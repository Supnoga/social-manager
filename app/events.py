"""Kalendár udalostí: sviatky podľa krajín (zadarmo, bez AI), bežné dni (Valentín, Halloween, Vianoce…)
a tematické dni podľa zamerania projektu (Claude ich navrhne raz a uložia sa).

Appka s predstihom ukáže blížiace sa udalosti, ponúkne nápad na video alebo prianie a týždenná dávka Radaru
ich berie do úvahy (bez volania navyše). Videá k udalosti plánovanie dá presne na jej deň.
"""
import datetime as dt
import json

import httpx
from fastapi import APIRouter, Body, HTTPException

from . import ai, db, languages

router = APIRouter()
SCHEMA = """
CREATE TABLE IF NOT EXISTS holidays_cache (country TEXT, year INTEGER, data TEXT, fetched_at TEXT, PRIMARY KEY(country, year));
CREATE TABLE IF NOT EXISTS project_events (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, name TEXT, rule TEXT,
  why TEXT DEFAULT '', langs TEXT DEFAULT 'all', source TEXT DEFAULT 'ai', active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS event_status (project_id INTEGER, key TEXT, status TEXT, PRIMARY KEY(project_id, key));
"""
_ready = False
ORTHODOX = {"el", "bg", "ro", "sr", "mk"}
LEAD_DAYS = 21  # koľko dní vopred ukazovať

# bežné dni, ktoré sa hodia skoro každému projektu (pravidlo: MM-DD, easter±N, N-dow-MM, last-dow-MM)
COMMON = [
    ("Nový rok", "01-01", "prianie"), ("Valentín", "02-14", "deň"), ("Medzinárodný deň žien", "03-08", "deň"),
    ("Veľká noc", "easter+0", "prianie"), ("Deň matiek", "2-sun-05", "prianie"), ("Halloween", "10-31", "deň"),
    ("Black Friday", "last-fri-11", "deň"), ("Vianoce", "12-24", "prianie"), ("Silvester", "12-31", "prianie"),
    ("Začiatok leta / prázdnin", "06-21", "sezóna"), ("Návrat do škôl", "09-01", "sezóna"),
]
DOW = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _db():
    global _ready
    if not _ready:
        with db._lock:
            db.con().executescript(SCHEMA)
            for sql in ("ALTER TABLE ideas ADD COLUMN due_date TEXT DEFAULT ''", "ALTER TABLE ideas ADD COLUMN markets TEXT DEFAULT ''"):
                try:
                    db.con().execute(sql)
                except Exception:
                    pass
            db.con().commit()
        _ready = True


# ---------- dátumy ----------
def easter(year, orthodox=False):
    if orthodox:
        a, b, c = year % 4, year % 7, year % 19
        d = (19 * c + 15) % 30
        e = (2 * a + 4 * b - d + 34) % 7
        month, day = divmod(d + e + 114, 31)
        return dt.date(year, month, day + 1) + dt.timedelta(days=13)
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(year, month, day + 1)


def resolve(rule, year, orthodox=False):
    """Pravidlo -> dátum v danom roku (alebo None)."""
    try:
        rule = (rule or "").strip().lower()
        if rule.startswith("easter"):
            return easter(year, orthodox) + dt.timedelta(days=int(rule[6:] or 0))
        parts = rule.split("-")
        if len(parts) == 2:
            return dt.date(year, int(parts[0]), int(parts[1]))
        n, dow, mon = parts
        mon = int(mon)
        if n == "last":
            d = dt.date(year + (mon == 12), mon % 12 + 1, 1) - dt.timedelta(days=1)
            while d.weekday() != DOW[dow]:
                d -= dt.timedelta(days=1)
            return d
        d = dt.date(year, mon, 1)
        while d.weekday() != DOW[dow]:
            d += dt.timedelta(days=1)
        return d + dt.timedelta(weeks=int(n) - 1)
    except Exception:
        return None


def next_date(rule, today, orthodox=False):
    for y in (today.year, today.year + 1):
        d = resolve(rule, y, orthodox)
        if d and d >= today:
            return d
    return None


# ---------- štátne sviatky (Nager.Date, zadarmo, bez kľúča) ----------
def holidays(country, year):
    _db()
    c = db.one("SELECT data, fetched_at FROM holidays_cache WHERE country=? AND year=?", (country, year))
    if c and json.loads(c["data"]):
        return json.loads(c["data"])
    if c and c["fetched_at"] > (dt.datetime.now() - dt.timedelta(days=2)).strftime("%Y-%m-%d"):
        return []
    data = []
    try:
        r = httpx.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}", timeout=20)
        if r.status_code == 200:
            data = [{"date": h["date"], "name": h.get("localName") or h["name"], "en": h["name"]}
                    for h in r.json() if h.get("global", True)]
    except Exception:
        pass
    db.run("INSERT OR REPLACE INTO holidays_cache(country, year, data, fetched_at) VALUES(?,?,?,?)",
           (country, year, json.dumps(data, ensure_ascii=False), dt.date.today().isoformat()))
    return data


def _project(pid):
    p = db.one("SELECT * FROM projects WHERE id=?", (pid,))
    if not p:
        raise HTTPException(404, "Projekt neexistuje")
    p["languages"] = json.loads(p["languages"] or "[]")
    return p


def upcoming(pid, days=60):
    """Blížiace sa udalosti pre projekt: sviatky krajín jeho jazykov, bežné dni a tematické dni projektu."""
    _db()
    p = _project(pid)
    today = dt.date.today()
    end = today + dt.timedelta(days=days)
    langs = p["languages"]
    ev = {}

    def add(date, name, kind, lang, country="", why=""):
        if not date or not (today <= date <= end):
            return
        key = f"{date.isoformat()}|{name}"
        e = ev.setdefault(key, {"key": key, "date": date.isoformat(), "name": name, "kind": kind, "langs": set(),
                                "countries": set(), "why": why, "local": set()})
        if kind == "sviatok" and why:
            e["local"].add(why)
        if lang:
            e["langs"].add(lang)
        if country:
            e["countries"].add(country)

    for name, rule, kind in COMMON:
        for l in langs:
            add(next_date(rule, today, l in ORTHODOX and rule.startswith("easter")), name, kind, l)
    for r in db.q("SELECT * FROM project_events WHERE project_id=? AND active=1", (pid,)):
        targets = langs if r["langs"] in ("", "all") else [x for x in r["langs"].split(",") if x in langs]
        for l in targets:
            add(next_date(r["rule"], today), r["name"], "téma", l, why=r["why"])
    for l in langs:
        for c in languages.COUNTRIES.get(l, []):
            if c == "XK":
                continue
            for y in {today.year, end.year}:
                for h in holidays(c, y):
                    d = dt.date.fromisoformat(h["date"])
                    # rovnaký sviatok vo viacerých krajinách zlúčiť pod anglický názov
                    add(d, h["en"], "sviatok", l, c, why=h["name"])
    st = {r["key"]: r["status"] for r in db.q("SELECT key, status FROM event_status WHERE project_id=?", (pid,))}
    have = {r["source_ref"] for r in db.q("SELECT source_ref FROM ideas WHERE project_id=? AND source='event'", (pid,))}
    out = []
    for e in ev.values():
        if st.get(e["key"]) == "ignored":
            continue
        e["langs"], e["countries"] = sorted(e["langs"]), sorted(e["countries"])
        loc = e.pop("local")
        if len(loc) == 1:  # sviatok len v jednej krajine/jazyku: miestny názov
            e["name"], e["why"] = loc.pop(), ""
        e["all"] = set(e["langs"]) >= set(langs)
        e["days_left"] = (dt.date.fromisoformat(e["date"]) - today).days
        e["has_idea"] = e["key"] in have
        out.append(e)
    out.sort(key=lambda x: (x["date"], x["kind"] != "téma"))
    return out


def signals(pid, n=4):
    """Pre týždennú dávku Radaru: udalosti o 7-25 dní, ku ktorým ešte nie je nápad (pár desiatok tokenov)."""
    out = []
    for e in upcoming(pid, 25):
        if e["days_left"] < 7 or e["has_idea"]:
            continue
        out.append({"id": f"E{len(out) + 1}", "mk": "all" if e["all"] else e["langs"],
                    "txt": f'event "{e["name"]}" on {e["date"]} ({e["kind"]}{", " + e["why"][:60] if e["why"] else ""})',
                    "ref": {"event": e["key"], "label": e["name"], "date": e["date"], "langs": e["langs"]}})
        if len(out) >= n:
            break
    return out


def suggest(pid):
    """Raz pre projekt: Claude (lacný model) navrhne tematické dni podľa zamerania projektu."""
    _db()
    p = _project(pid)
    data = ai.ask(f"""Project: {p['name']}. {(p.get('strategy_short') or p.get('description') or '')[:500]}
Markets: {', '.join(languages.english(l) for l in p['languages'])}.
List 10-20 real recurring awareness days, international days, industry/trade days and seasonal moments that this project's
audience cares about (e.g. a heat pump company: World Heat Pump Day, Earth Day, start of heating season). Only real, verifiable
recurring days with correct dates. Skip general holidays (Christmas, New Year, Easter, Halloween, Valentine, Black Friday).
rule format: "MM-DD" for fixed dates, "2-sun-05" = 2nd Sunday of May, "last-fri-11" = last Friday of November.
Return JSON: {{"events":[{{"name":"name in {languages.english(p['source_lang'])}","rule":"","why":"1 short reason","langs":"all or comma list of codes"}}]}}""",
                  "events", "cheap")
    n = 0
    for e in (data or {}).get("events", [])[:25]:
        if not e.get("name") or not resolve(e.get("rule"), 2026):
            continue
        if db.one("SELECT 1 x FROM project_events WHERE project_id=? AND lower(name)=lower(?)", (pid, e["name"])):
            continue
        db.run("INSERT INTO project_events(project_id, name, rule, why, langs, source) VALUES(?,?,?,?,?,'ai')",
               (pid, e["name"][:120], e["rule"].lower(), (e.get("why") or "")[:200], e.get("langs") or "all"))
        n += 1
    db.set_setting(f"events_suggested_{pid}", dt.date.today().isoformat())
    return {"added": n}


def idea_for(pid, key, kind="video"):
    """1 malé volanie: nápad na video alebo prianie k udalosti -> schránka Nápadov, naplánuje sa presne na ten deň."""
    _db()
    p = _project(pid)
    e = next((x for x in upcoming(pid, 400) if x["key"] == key), None)
    if not e:
        raise HTTPException(400, "Udalosť sa nenašla")
    want = ("a short greeting video (wish) for the audience, warm and on-brand, 15-25 s, clear wish at the end"
            if kind == "greeting" else "a short video tied to this day that fits the project (useful/entertaining, not generic)")
    data = ai.ask(f"""Project: {p['name']}. {(p.get('strategy_short') or p.get('description') or '')[:400]}
Event: "{e['name']}" on {e['date']}{(' (' + e['why'] + ')') if e['why'] else ''}. Markets: {', '.join(e['langs'])}.
Write 2 ideas for {want}. Keep it universal across these countries unless the event is national.
Return JSON: {{"ideas":[{{"title":"","hook":"exact first sentence","angle":"","why":"","score":7}}]}}
Write in {languages.english(p['source_lang'])}.""", "event_idea", "cheap")
    made = 0
    for i in (data or {}).get("ideas", [])[:2]:
        if not i.get("title"):
            continue
        db.run("""INSERT INTO ideas(project_id,title,hook,angle,pillar,format,why,score,status,source,source_ref,why_now,expires_at,
                  due_date,markets) VALUES(?,?,?,?,'','short',?,?,'inbox','event',?,?,?,?,?)""",
               (pid, i["title"][:300], i.get("hook", ""), i.get("angle", ""), i.get("why", ""), int(i.get("score") or 7), key,
                f"{e['name']} – {dt.date.fromisoformat(e['date']).strftime('%d.%m.')}", e["date"], e["date"],
                "" if e["all"] else ",".join(e["langs"])))
        made += 1
    return {"created": made}


# ---------- API ----------
@router.get("/api/events/{pid}")
def api_upcoming(pid: int, days: int = 60):
    _db()
    return {"events": upcoming(pid, days),
            "custom": db.q("SELECT * FROM project_events WHERE project_id=? ORDER BY name", (pid,)),
            "lead": LEAD_DAYS}


@router.post("/api/events/{pid}/suggest")
def api_suggest(pid: int):
    return suggest(pid)


@router.post("/api/events/{pid}/idea")
def api_idea(pid: int, data: dict = Body(...)):
    return idea_for(pid, data["key"], data.get("kind", "video"))


@router.post("/api/events/{pid}/ignore")
def api_ignore(pid: int, data: dict = Body(...)):
    _db()
    db.run("INSERT OR REPLACE INTO event_status(project_id, key, status) VALUES(?,?,'ignored')", (pid, data["key"]))
    return {"ok": True}


@router.post("/api/events/{pid}/custom")
def api_custom(pid: int, data: dict = Body(...)):
    _db()
    rule = (data.get("rule") or "").strip()
    if "." in rule:  # 22.4. -> 04-22
        d, m = [x for x in rule.split(".") if x][:2]
        rule = f"{int(m):02d}-{int(d):02d}"
    if not data.get("name") or not resolve(rule, 2026):
        raise HTTPException(400, "Zadaj názov a dátum (napr. 22.4.)")
    db.run("INSERT INTO project_events(project_id, name, rule, why, langs, source) VALUES(?,?,?,?,'all','manual')",
           (pid, data["name"][:120], rule, data.get("why", "")))
    return {"ok": True}


@router.delete("/api/events/custom/{eid}")
def api_del(eid: int):
    _db()
    db.run("DELETE FROM project_events WHERE id=?", (eid,))
    return {"ok": True}
