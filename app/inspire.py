"""Inšpirácia a kvalita obsahu (1.16).

- Otázky ľudí: čo ľudia hľadajú na Googli (našepkávač, zadarmo, bez AI) + otázky z komentárov pod tvojimi videami.
- Zásobník: videá a nápady, ktoré sa ti páčia (odkaz z akejkoľvek siete + poznámka).
- Overené formáty a háčiky: knižnica šablón; appka si pamätá, ktoré ti fungujú, a tie dáva Claudovi častejšie.
- Kontrola kvality scenára: skóre a rady bez AI (0 tokenov). Lepší háčik = 1 malé lacné volanie.
"""
import datetime as dt
import json
import random
import re
import statistics
import time

import httpx
from fastapi import APIRouter, Body, HTTPException

from . import ai, db, languages

router = APIRouter()

SCHEMA = """
CREATE TABLE IF NOT EXISTS swipes (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, url TEXT DEFAULT '', platform TEXT DEFAULT '',
  title TEXT DEFAULT '', thumb TEXT DEFAULT '', note TEXT DEFAULT '', status TEXT DEFAULT 'new', created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, lang TEXT, text TEXT, source TEXT,
  n INTEGER DEFAULT 1, status TEXT DEFAULT 'new', seen_at TEXT DEFAULT (datetime('now','localtime')), UNIQUE(project_id, lang, text));
"""
_ready = False


def _db():
    global _ready
    if _ready:
        return
    db.con().executescript(SCHEMA)
    # N2N: nikdy netvrdiť výrobu na Slovensku (prednastavené raz, dá sa zmeniť v projekte)
    if not db.get_setting("banned_n2n_done"):
        db.run("""UPDATE projects SET banned='made in Slovakia; vyrobené na Slovensku; slovenská výroba; slovenský výrobca'
                  WHERE (name LIKE '%N2N%' OR name LIKE '%n2n%') AND COALESCE(banned,'')=''""")
        db.set_setting("banned_n2n_done", True)
    db.con().commit()
    _ready = True


# ---------- knižnica overených formátov a háčikov ----------
FORMATS = [
    ("chyby", "3 chyby, ktoré…", "3 mistakes people make with X, each fixed fast"),
    ("mytus", "Mýtus vs. fakt", "common myth stated, then busted with one hard fact"),
    ("cena", "Koľko to naozaj stojí", "real cost breakdown with concrete numbers, then how to pay less"),
    ("ab", "A vs. B", "side-by-side comparison, clear winner for a specific situation"),
    ("predpo", "Pred / po", "before state vs after state, the change shown visually"),
    ("pov", "POV", "first-person situation the viewer recognizes, twist at the end"),
    ("navod", "Návod v 3 krokoch", "do this in 3 quick steps, each one visual"),
    ("odpoved", "Odpoveď na otázku", "answer one real viewer/customer question directly"),
    ("novinka", "Reakcia na novinku", "react to a current news/change and what it means for the viewer"),
    ("pribeh", "Príbeh zákazníka", "one customer's problem -> solution -> result with numbers"),
    ("kviz", "Uhádneš?", "quiz question first, viewer guesses, reveal at the end"),
    ("zledobre", "Zle vs. dobre", "wrong way vs right way shown back to back"),
    ("vysvetli", "Vysvetlím za 30 sekúnd", "explain one confusing thing simply with an analogy"),
    ("top", "Top 5 / rebríček", "countdown list, best one last"),
    ("test", "Experiment / test", "we tested X so you don't have to, result with numbers"),
    ("zakulisie", "Zákulisie", "behind the scenes: how it is made/installed/checked"),
    ("prestan", "Prestaň robiť…", "call out a common habit, show the better alternative"),
    ("tajomstvo", "Toto ti nikto nepovie", "insider tip the industry rarely says out loud"),
]
HOOKS = [
    "Stop doing {X} until you see this",
    "{N}% of people don't know that…",
    "Nobody tells you this about {X}",
    "If you have {problem}, watch this",
    "{X} vs {Y}: the difference will surprise you",
    "I was doing {X} wrong for {N} years",
    "This {thing} costs you {N} € every year",
    "Here's what {N} € really buys you",
    "Don't buy {X} before you know these 3 things",
    "The real reason your {X} {fails}",
    "You've been told {myth}. It's wrong.",
    "Watch what happens when…",
]
FMT = {f[0]: f for f in FORMATS}


def template_stats(pid):
    """Priemerný výsledok (× nad normál účtu) pre každý formát, ktorý už bol použitý."""
    _db()
    from . import stats
    tpl = {r["id"]: r["template"] for r in db.q("SELECT id, template FROM ideas WHERE project_id=? AND COALESCE(template,'')!=''", (pid,))}
    agg = {}
    for x in stats.ideas_perf(pid):
        t = tpl.get(x["idea_id"])
        if t:
            agg.setdefault(t, []).append(x["ratio"])
    used = {}
    for r in db.q("SELECT template, COUNT(*) n FROM ideas WHERE project_id=? AND COALESCE(template,'')!='' GROUP BY template", (pid,)):
        used[r["template"]] = r["n"]
    out = []
    for k, name, en in FORMATS:
        rs = agg.get(k, [])
        out.append({"key": k, "name": name, "en": en, "used": used.get(k, 0), "measured": len(rs),
                    "ratio": round(statistics.median(rs), 2) if rs else None})
    return out


GROUPS = {"rady": ["chyby", "mytus", "navod", "vysvetli", "odpoved", "prestan", "tajomstvo", "zledobre"],
          "dokazy": ["pribeh", "test", "predpo", "zakulisie", "cena", "ab"],
          "zabava": ["novinka", "pov", "kviz", "top"]}
GROUP_NAMES = {"rady": "Rady a vysvetlenia", "dokazy": "Dôkazy a čísla", "zabava": "Aktuálne a zábavné"}
TARGET = {"rady": 50, "dokazy": 30, "zabava": 20}
GROUP_OF = {k: g for g, ks in GROUPS.items() for k in ks}


def content_mix(pid, last=20):
    """Pomer typov obsahu v posledných nápadoch (bez AI). Stráži, aby sa obsah striedal."""
    rows = db.q("""SELECT template FROM ideas WHERE project_id=? AND COALESCE(template,'')!='' AND status NOT IN ('rejected','inbox','snoozed')
                   ORDER BY id DESC LIMIT ?""", (pid, last))
    n = len(rows)
    cnt = {g: 0 for g in GROUPS}
    for r in rows:
        g = GROUP_OF.get(r["template"])
        if g:
            cnt[g] += 1
    mix = [{"key": g, "name": GROUP_NAMES[g], "pct": round(100 * cnt[g] / n) if n else 0, "target": TARGET[g]} for g in GROUPS]
    lack = None
    if n >= 6:
        worst = min(mix, key=lambda m: m["pct"] - m["target"])
        if worst["pct"] - worst["target"] <= -12:
            lack = worst["key"]
    return {"n": n, "mix": mix, "lack": lack}


def pick_templates(pid, n=5):
    """70 % najlepšie fungujúce, zvyšok málo vyskúšané / náhodné (učiaci sa výber, bez AI).
    Ak niektorý typ obsahu chýba (content_mix), dostane aspoň 2 miesta."""
    st = template_stats(pid)
    lack = content_mix(pid)["lack"]
    if lack:
        first = [s for s in st if s["key"] in GROUPS[lack] and not (s["ratio"] is not None and s["ratio"] < 0.7 and s["measured"] >= 3)]
        first.sort(key=lambda s: (-(s["ratio"] or 1.0), s["used"], random.random()))
        forced = first[:2]
        rest_pick = _pick(st, n - len(forced), exclude=forced)
        return forced + rest_pick
    return _pick(st, n)


def _pick(st, n, exclude=()):
    st = [s for s in st if s not in exclude]
    good = sorted([s for s in st if s["ratio"] is not None and s["measured"] >= 2], key=lambda s: -s["ratio"])
    good = [s for s in good if s["ratio"] >= 1.0]
    k_best = min(len(good), round(n * 0.7))
    chosen = good[:k_best]
    rest = [s for s in st if s not in chosen and not (s["ratio"] is not None and s["ratio"] < 0.7 and s["measured"] >= 3)]
    rest.sort(key=lambda s: (s["used"], random.random()))
    chosen += rest[:n - len(chosen)]
    return chosen


def templates_prompt(pid, n=5):
    ch = pick_templates(pid, n)
    hooks = random.sample(HOOKS, 4)
    t = "Proven formats (pick one per idea, return its key in \"template\"): " + "; ".join(
        f'{s["key"]}={s["en"]}' + (f' (ours {s["ratio"]}x)' if s["ratio"] else "") for s in ch)
    t += "\nProven hook patterns (adapt, don't copy literally): " + " | ".join(hooks)
    return t


# ---------- R290 je chladivo, nie názov produktu ----------
_R290 = re.compile(r"(PROLINE)[\s\-–]+R[\s\-]?290\b", re.I)


def fix_refrigerant_name():
    """Jednorazová oprava: AI si zo zhrnutia projektu odvodila názov „PROLINE R290“. R290 je len chladivo radu PROLINE.
    Opraví zhrnutia projektu (z nich AI píše), hotové scenáre a nápady, a pridá „PROLINE R290“ medzi zakázané výrazy."""
    if db.get_setting("fix_r290_done"):
        return 0
    n = 0
    for p in db.q("SELECT * FROM projects"):
        upd = {}
        for f, rep in (("strategy_short", r"\1 (refrigerant R290)"), ("design_summary", r"\1 (refrigerant R290)"),
                       ("sources_summary", r"\1 (refrigerant R290)"), ("strategy", r"\1 (chladivo R290)")):
            v = p.get(f) or ""
            v2 = _R290.sub(rep, v)
            if "n2n" in (p.get("name") or "").lower():   # N2N sa nemá prezentovať ako slovenský výrobca
                v2 = v2.replace("Slovak heat pump manufacturer", "European HVAC manufacturer").replace("Slovak-made", "European engineering")
            if v2 != v:
                upd[f] = v2
        hit = bool(upd) or any(_R290.search(str(r.get("voiceover") or "") + str(r.get("scenes") or ""))
                               for r in db.q("SELECT voiceover, scenes FROM scripts WHERE project_id=?", (p["id"],)))
        ban = banned_list(p)
        if hit and not any(b.lower() == "proline r290" for b in ban):
            upd["banned"] = "; ".join(ban + ["PROLINE R290"])
        if upd:
            db.run(f"UPDATE projects SET {', '.join(k + '=?' for k in upd)} WHERE id=?", (*upd.values(), p["id"]))
            n += 1
    for r in db.q("SELECT id, title, voiceover, scenes, description, caption FROM scripts"):
        new = {f: _R290.sub(r"\1", r.get(f) or "") for f in ("title", "voiceover", "scenes", "description", "caption")}
        if any(new[f] != (r.get(f) or "") for f in new):
            extra = ", voice_path=''" if new["voiceover"] != (r.get("voiceover") or "") else ""
            db.run(f"UPDATE scripts SET title=?, voiceover=?, scenes=?, description=?, caption=?{extra} WHERE id=?",
                   (new["title"], new["voiceover"], new["scenes"], new["description"], new["caption"], r["id"]))
            n += 1
    for r in db.q("SELECT id, title, hook, angle FROM ideas"):
        new = {f: _R290.sub(r"\1", r.get(f) or "") for f in ("title", "hook", "angle")}
        if any(new[f] != (r.get(f) or "") for f in new):
            db.run("UPDATE ideas SET title=?, hook=?, angle=? WHERE id=?", (new["title"], new["hook"], new["angle"], r["id"]))
            n += 1
    db.set_setting("fix_r290_done", True)
    return n


# ---------- zakázané tvrdenia ----------
def banned_list(p):
    return [b.strip() for b in re.split(r"[;\n]", p.get("banned") or "") if b.strip()]


def banned_ctx(p):
    b = banned_list(p)
    return ("NEVER claim or say (forbidden): " + "; ".join(b)) if b else ""


# ---------- otázky ľudí ----------
QW = {  # slová, ktorými ľudia začínajú otázky (koľko stojí / ako / prečo)
    "sk": ["koľko stojí", "ako", "prečo"], "cs": ["kolik stojí", "jak", "proč"], "de": ["was kostet", "wie", "warum"],
    "pl": ["ile kosztuje", "jak", "dlaczego"], "hu": ["mennyibe kerül", "hogyan", "miért"], "fr": ["combien coûte", "comment", "pourquoi"],
    "nl": ["wat kost", "hoe", "waarom"], "it": ["quanto costa", "come", "perché"], "es": ["cuánto cuesta", "cómo", "por qué"],
    "pt": ["quanto custa", "como", "porque"], "en": ["how much does", "how to", "why"], "da": ["hvad koster", "hvordan", "hvorfor"],
    "sv": ["vad kostar", "hur", "varför"], "no": ["hva koster", "hvordan", "hvorfor"], "fi": ["paljonko maksaa", "miten", "miksi"],
    "is": ["hvað kostar", "hvernig", "af hverju"], "et": ["kui palju maksab", "kuidas", "miks"], "lv": ["cik maksā", "kā", "kāpēc"],
    "lt": ["kiek kainuoja", "kaip", "kodėl"], "el": ["πόσο κοστίζει", "πώς", "γιατί"], "bg": ["колко струва", "как", "защо"],
    "ro": ["cât costă", "cum", "de ce"], "hr": ["koliko košta", "kako", "zašto"], "sl": ["koliko stane", "kako", "zakaj"],
    "sr": ["koliko košta", "kako", "zašto"], "bs": ["koliko košta", "kako", "zašto"], "mk": ["колку чини", "како", "зошто"],
    "sq": ["sa kushton", "si", "pse"],
}
Q_RE = re.compile(r"\?|^(ako|koľko|prečo|kde|kedy|čo|jak|kolik|proč|wie|was|warum|wo|wann|how|why|what|where|when|which|can|is|does|"
                  r"ile|jak|czy|mennyi|hogy|combien|comment|pourquoi|hoe|wat|waarom|quanto|come|perché|cuánto|cómo|por qué|cât|cum)\b", re.I)


def _suggest(q, lang, country):
    r = httpx.get("https://suggestqueries.google.com/complete/search",
                  params={"client": "firefox", "hl": lang, "gl": country.lower() if country else lang, "q": q},
                  headers={"User-Agent": "Mozilla/5.0 SocialManager"}, timeout=15)
    r.raise_for_status()
    try:
        data = json.loads(r.content.decode(r.encoding or "utf-8", "ignore"))
    except Exception:
        data = json.loads(r.content.decode("latin-1"))
    return [s for s in (data[1] if len(data) > 1 else []) if isinstance(s, str) and s.lower().strip() != q.lower().strip()]


def _save_q(pid, lang, text, source):
    text = text.strip()[:220]
    if len(text) < 6:
        return
    db.run("""INSERT INTO questions(project_id, lang, text, source) VALUES(?,?,?,?)
              ON CONFLICT(project_id, lang, text) DO UPDATE SET n=n+1, seen_at=datetime('now','localtime')""", (pid, lang, text, source))


def job_questions():
    """Raz týždenne: našepkávač Googlu pre kľúčové slová projektu v každom jazyku (zadarmo, bez AI)."""
    _db()
    from . import radar
    for p in radar._projects():
        kws = {r["lang"]: json.loads(r["core"] or "[]") for r in db.q("SELECT lang, core FROM project_keywords WHERE project_id=?", (p["id"],))}
        for lang in p["languages"]:
            words = kws.get(lang, [])[:3]
            if not words:
                continue
            ctry = (radar.LANG_COUNTRIES.get(lang) or [""])[0]
            for w in words:
                qs = [w + " "] + [f"{qw} {w}" for qw in QW.get(lang, [])]
                for q in qs:
                    try:
                        for s in _suggest(q, lang, ctry)[:8]:
                            _save_q(p["id"], lang, s, "search")
                    except Exception as e:
                        radar._log("suggest", f"{lang}:{q}", False, note=str(e))
                    time.sleep(0.7)
    _comment_questions()
    db.set_setting("questions_last", dt.datetime.now().strftime("%Y-%m-%d %H:%M"))


def _comment_questions(days=60):
    """Otázky z komentárov pod tvojimi videami (bez AI)."""
    try:
        rows = db.q("""SELECT c.text, c.text_sk, a.project_id, a.lang FROM comments c JOIN accounts a ON a.id=c.account_id
                       WHERE c.fetched_at >= datetime('now','localtime',?)""", (f"-{days} day",))
    except Exception:
        return
    for r in rows:
        t = (r["text"] or "").strip()
        if r["project_id"] and 8 <= len(t) <= 300 and Q_RE.search(t):
            _save_q(r["project_id"], r["lang"] or "", t, "comment")


def questions(pid, lang=None, limit=60):
    _db()
    sql = "SELECT * FROM questions WHERE project_id=? AND status='new'"
    args = [pid]
    if lang:
        sql += " AND (lang=? OR source='comment')"
        args.append(lang)
    rows = db.q(sql + " ORDER BY (source='comment') DESC, n DESC, id DESC LIMIT ?", (*args, limit))
    return rows


def signals(pid, n_q=4, n_s=4):
    """Pre týždennú dávku Radaru: otázky ľudí (O) a zásobník (Z). Pár desiatok tokenov."""
    _db()
    out = []
    p = db.one("SELECT source_lang FROM projects WHERE id=?", (pid,))
    src = p["source_lang"] if p else "sk"
    qs = db.q("""SELECT * FROM questions WHERE project_id=? AND status='new' ORDER BY (source='comment') DESC,
                 (lang=?) DESC, n DESC, id DESC LIMIT ?""", (pid, src, n_q))
    for i, q in enumerate(qs):
        out.append({"id": f"O{i + 1}", "mk": [q["lang"]] if q["lang"] and q["source"] == "search" else "all",
                    "txt": f'people {"asked in our comments" if q["source"] == "comment" else "search on Google"}: "{q["text"][:120]}"',
                    "ref": {"question": q["id"], "label": q["text"][:80]}})
    for i, s in enumerate(db.q("SELECT * FROM swipes WHERE project_id=? AND status='new' ORDER BY id DESC LIMIT ?", (pid, n_s))):
        out.append({"id": f"Z{i + 1}", "mk": "all",
                    "txt": f'owner saved this as inspiration ({s["platform"] or "web"}): "{(s["title"] or s["url"])[:100]}"'
                           + (f'; note: {s["note"][:120]}' if s["note"] else ""),
                    "ref": {"swipe": s["id"], "label": (s["title"] or s["note"] or s["url"])[:80]}})
    try:
        from . import weather
        out += weather.signals(pid)
    except Exception:
        pass
    return out


def mark_used(ref):
    if ref.get("question"):
        db.run("UPDATE questions SET status='used' WHERE id=?", (ref["question"],))
    if ref.get("swipe"):
        db.run("UPDATE swipes SET status='used' WHERE id=?", (ref["swipe"],))


# ---------- zásobník ----------
def _platform(url):
    u = url.lower()
    for k, v in (("tiktok", "tiktok"), ("youtu", "youtube"), ("instagram", "instagram"), ("facebook", "facebook"),
                 ("fb.watch", "facebook"), ("linkedin", "linkedin")):
        if k in u:
            return v
    return "web" if u.startswith("http") else ""


def _oembed(url, platform):
    ep = {"youtube": "https://www.youtube.com/oembed", "tiktok": "https://www.tiktok.com/oembed"}.get(platform)
    if not ep:
        return "", ""
    try:
        r = httpx.get(ep, params={"url": url, "format": "json"}, timeout=12, follow_redirects=True)
        d = r.json()
        return (d.get("title") or "")[:200], d.get("thumbnail_url") or ""
    except Exception:
        return "", ""


@router.get("/api/inspire/{pid}")
def api_overview(pid: int, lang: str = ""):
    _db()
    p = db.one("SELECT source_lang, languages FROM projects WHERE id=?", (pid,))
    if not p:
        raise HTTPException(404)
    lang = lang or p["source_lang"]
    last = db.get_setting("questions_last", "")
    return {"questions": questions(pid, lang), "lang": lang, "last": last, "mix": content_mix(pid),
            "langs": json.loads(p["languages"] or "[]"),
            "swipes": db.q("SELECT * FROM swipes WHERE project_id=? AND status!='hidden' ORDER BY status='used', id DESC LIMIT 60", (pid,)),
            "templates": template_stats(pid)}


@router.post("/api/inspire/{pid}/swipe")
def api_swipe_add(pid: int, data: dict = Body(...)):
    _db()
    added = 0
    lines = [l.strip() for l in (data.get("urls") or "").split("\n") if l.strip()][:20]
    note = (data.get("note") or "").strip()
    if not lines and note:
        db.run("INSERT INTO swipes(project_id, note) VALUES(?,?)", (pid, note[:1000]))
        return {"added": 1}
    for url in lines:
        pl = _platform(url)
        title, thumb = _oembed(url, pl)
        db.run("INSERT INTO swipes(project_id, url, platform, title, thumb, note) VALUES(?,?,?,?,?,?)",
               (pid, url[:500], pl, title, thumb, note[:1000]))
        added += 1
    return {"added": added}


@router.post("/api/inspire/{pid}/item")
def api_item(pid: int, data: dict = Body(...)):
    """Akcie: idea (Nápad z tohto), hide (skryť). kind: question|swipe."""
    _db()
    kind, iid, act = data.get("kind"), int(data.get("id") or 0), data.get("action")
    table = {"question": "questions", "swipe": "swipes"}.get(kind)
    if not table:
        raise HTTPException(400)
    if act == "hide":
        db.run(f"UPDATE {table} SET status='hidden' WHERE id=? AND project_id=?", (iid, pid))
        return {"ok": True}
    from . import content
    return content.radar_quick(pid, {kind: iid})


@router.post("/api/inspire/questions/refresh")
def api_q_refresh():
    import threading

    def go():
        try:
            job_questions()
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()
    return {"ok": True}


# ---------- kontrola kvality scenára (bez AI) ----------
GREET = re.compile(r"^(ahoj|čau|dobrý deň|zdravím|vitajte|hi|hello|hey|hallo|servus|cześć|dzień dobry|bonjour|ciao|hola|hej|moi)\b", re.I)
CTA = re.compile(r"sleduj|ulož|napíš|koment|zdieľaj|klikni|odkaz|link|zavolaj|kontakt|partner|follow|save|comment|share|subscribe|"
                 r"sledujte|uložte|napište|folg|speicher|kommentier|abonn|obserwuj|zapisz|napisz|kövess|mentsd|abonne|enregistre|"
                 r"volg|bewaar|segui|salva|sigue|guarda|segue|følg|gem|följ|spara|seuraa|tallenna", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def _sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", (t or "").strip()) if s.strip()]


def check_script(s, p=None, fmt="short"):
    vo = s.get("voiceover") or ""
    scenes = s.get("scenes") or []
    if isinstance(scenes, str):
        scenes = json.loads(scenes or "[]")
    sents = _sentences(vo)
    words = len(vo.split())
    first = sents[0] if sents else ""
    fw = len(first.split())
    items = []

    def add(ok, w, good, bad):
        items.append({"ok": bool(ok), "w": w, "text": good if ok else bad})

    add(first and fw <= 14, 3, f"Háčik je krátky ({fw} slov).", f"Prvá veta má {fw} slov. Skráť ju pod 14, ľudia sa rozhodnú za 2 sekundy.")
    add(first and not GREET.search(first), 2, "Nezačína pozdravom.", "Nezačínaj pozdravom ani predstavovaním, hneď prvou vetou povedz to najzaujímavejšie.")
    lo, hi = (70, 170) if fmt == "short" else (600, 1300)
    add(lo <= words <= hi, 2, f"Dĺžka sedí (~{round(words / 2.6)} s).",
        f"Text má {words} slov (~{round(words / 2.6)} s). Pre {'krátke video' if fmt == 'short' else 'dlhé video'} je ideál {lo}–{hi} slov.")
    avg = words / max(1, len(sents))
    add(avg <= 16, 1, "Vety sú krátke, dobre sa počúvajú.", f"Vety majú v priemere {round(avg)} slov. Krátke vety sa lepšie počúvajú aj prekladajú.")
    add(re.search(r"\d", vo), 2, "Obsahuje konkrétne číslo.", "Pridaj konkrétne číslo (cena, úspora, percento). Čísla zvyšujú dôveru aj pozretia.")
    tail = " ".join(sents[-2:]) + " " + (s.get("caption") or "")
    add(CTA.search(tail), 2, "Na konci je výzva (sleduj, ulož, napíš…).", "Na konci chýba výzva. Pridaj napr. „Ulož si to“ alebo „Napíš do komentára…“.")
    add(not EMOJI.search(vo), 1, "Bez emoji v texte pre hlas.", "V texte pre hlas sú emoji, hlas ich nevie prečítať. Daj ich len do textu príspevku.")
    add(4 <= len(scenes) <= 9, 1, f"{len(scenes)} scén, video bude mať tempo.", f"Scén je {len(scenes)}. Ideál je 4–8, aby sa obraz často menil.")
    s1 = (scenes[0].get("onscreen") if scenes else "") or ""
    add(s1 and len(s1.split()) <= 7, 2, "Prvý text na obrazovke je krátky a výrazný.",
        "Prvý text na obrazovke chýba alebo je dlhý. Daj max. 7 slov, veľa ľudí pozerá bez zvuku.")
    add(all((c.get("onscreen") or "").strip() for c in scenes) if scenes else False, 1, "Každá scéna má text na obrazovke.",
        "Niektoré scény nemajú text na obrazovke. Video bez zvuku by bolo nejasné.")
    cap = s.get("caption") or ""
    tags = len(re.findall(r"#\w", s.get("hashtags") or ""))
    add(len(cap) <= 150 and 3 <= tags <= 10, 1, "Text príspevku a hashtagy sú v poriadku.",
        f"Text príspevku má {len(cap)} znakov a {tags} hashtagov. Ideál je do 150 znakov a 3–8 hashtagov.")
    bad = []
    if p:
        full = " ".join([vo, s.get("title") or "", cap, s.get("description") or ""] + [c.get("onscreen") or "" for c in scenes]).lower()
        bad = [b for b in banned_list(p) if b.lower() in full]
        add(not bad, 4, "Žiadne zakázané tvrdenia.", "Pozor, text obsahuje zakázané tvrdenie: " + ", ".join(bad) + ". Prepíš to.")
    tot = sum(i["w"] for i in items)
    score = round(100 * sum(i["w"] for i in items if i["ok"]) / max(1, tot))
    if bad:
        score = min(score, 40)
    items.sort(key=lambda i: (i["ok"], -i["w"]))
    return {"score": score, "items": items, "words": words, "seconds": round(words / 2.6)}


@router.get("/api/scripts/{sid}/quality")
def api_quality(sid: int):
    _db()
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    if not s:
        raise HTTPException(404)
    p = db.one("SELECT * FROM projects WHERE id=?", (s["project_id"],))
    i = db.one("SELECT format FROM ideas WHERE id=?", (s["idea_id"],)) or {}
    return check_script(s, p, i.get("format") or "short")


@router.post("/api/ideas/{iid}/hooks")
def api_hooks(iid: int):
    """5 silnejších háčikov k nápadu (1 malé volanie lacného modelu, ~600 tokenov)."""
    _db()
    idea = db.one("SELECT * FROM ideas WHERE id=?", (iid,))
    if not idea:
        raise HTTPException(404)
    p = db.one("SELECT * FROM projects WHERE id=?", (idea["project_id"],))
    s = db.one("SELECT voiceover FROM scripts WHERE idea_id=? AND is_source=1", (iid,))
    first = (_sentences(s["voiceover"])[:1] or [""])[0] if s else ""
    try:
        data = ai.ask(f"""Short video for {p['name']}. Topic: {idea['title']}. Angle: {idea['angle'][:200]}
Current first sentence: "{first or idea['hook']}"
{banned_ctx(p)}
Write 5 much stronger opening sentences (max 12 words each) that stop scrolling in 2 seconds: curiosity gap, concrete number,
bold claim that the video proves, or direct call-out of the viewer's problem. Patterns: {' | '.join(random.sample(HOOKS, 5))}
Must be true to the topic, no clickbait lies, no greetings. Language: {languages.english(p['source_lang'])}.
Return JSON: {{"hooks":["","","","",""]}}""", "hooks", "cheap", use_cache=False)
    except ai.NeedManual:
        raise HTTPException(400, "Na návrh háčikov treba Claude Code (v ručnom režime nefunguje).")
    return {"hooks": [h for h in (data or {}).get("hooks", []) if isinstance(h, str)][:5], "current": first or idea["hook"]}


@router.post("/api/ideas/{iid}/use-hook")
def api_use_hook(iid: int, data: dict = Body(...)):
    """Nahradí háčik nápadu aj prvú vetu textu pre hlas (v hlavnom jazyku)."""
    hook = (data.get("hook") or "").strip()
    if not hook:
        raise HTTPException(400)
    db.run("UPDATE ideas SET hook=? WHERE id=?", (hook, iid))
    s = db.one("SELECT id, voiceover, scenes FROM scripts WHERE idea_id=? AND is_source=1", (iid,))
    if s:
        sents = _sentences(s["voiceover"])
        vo = " ".join([hook] + sents[1:]) if sents else hook
        db.run("UPDATE scripts SET voiceover=? WHERE id=?", (vo, s["id"]))
    return {"ok": True}


# ---------- opraviť scenár jedným klikom (1 volanie) ----------
@router.post("/api/scripts/{sid}/improve")
def api_improve(sid: int):
    """Claude opraví presne to, čo našla kontrola kvality. Pôvodná verzia sa odloží, dá sa vrátiť."""
    _db()
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    if not s:
        raise HTTPException(404)
    p = db.one("SELECT * FROM projects WHERE id=?", (s["project_id"],))
    idea = db.one("SELECT format FROM ideas WHERE id=?", (s["idea_id"],)) or {}
    fmt = idea.get("format") or "short"
    before = check_script(s, p, fmt)
    tips = [i["text"] for i in before["items"] if not i["ok"]]
    if not tips:
        return {"before": before["score"], "after": before["score"], "changed": False}
    scenes = json.loads(s["scenes"] or "[]")
    payload = {"voiceover": s["voiceover"], "onscreen": [c.get("onscreen", "") for c in scenes], "caption": s["caption"], "hashtags": s["hashtags"]}
    from . import content
    try:
        data = ai.ask(f"""{content._ctx(content._project(p["id"]))}
Improve this {"short (110-150 spoken words)" if fmt == "short" else "long"} video script. Fix exactly these problems found by our checker (in Slovak):
{chr(10).join("- " + t for t in tips)}
Keep the topic, meaning, facts and numbers (never invent facts), the language ({languages.english(s["lang"])}) and exactly {len(scenes)} on-screen texts
(one per scene, same order, max 7 words each). Voiceover: no greeting, first sentence max 14 words, short sentences, natural for text-to-speech.
Script: {json.dumps(payload, ensure_ascii=False)}
Return JSON with the same shape: {{"voiceover":"","onscreen":[""],"caption":"","hashtags":""}}""", "improve", "creative", use_cache=False)
    except ai.NeedManual:
        raise HTTPException(400, "Na opravu scenára treba Claude Code (v ručnom režime nefunguje).")
    if not isinstance(data, dict) or not (data.get("voiceover") or "").strip():
        raise HTTPException(400, "Claude nevrátil opravený text, skús znova.")
    db.set_setting(f"script_backup_{sid}", {"voiceover": s["voiceover"], "scenes": s["scenes"], "caption": s["caption"], "hashtags": s["hashtags"]})
    for i, t in enumerate(data.get("onscreen") or []):
        if i < len(scenes) and isinstance(t, str) and t.strip():
            scenes[i]["onscreen"] = t
    db.run("UPDATE scripts SET voiceover=?, scenes=?, caption=?, hashtags=? WHERE id=?",
           (data["voiceover"].strip(), json.dumps(scenes, ensure_ascii=False), data.get("caption") or s["caption"],
            data.get("hashtags") or s["hashtags"], sid))
    after = check_script(db.one("SELECT * FROM scripts WHERE id=?", (sid,)), p, fmt)
    others = db.one("SELECT COUNT(*) n FROM scripts WHERE idea_id=? AND id!=?", (s["idea_id"], sid))["n"]
    return {"before": before["score"], "after": after["score"], "changed": True, "translations": others}


@router.post("/api/scripts/{sid}/improve-undo")
def api_improve_undo(sid: int):
    b = db.get_setting(f"script_backup_{sid}")
    if not b:
        raise HTTPException(400, "Pôvodná verzia už nie je uložená.")
    db.run("UPDATE scripts SET voiceover=?, scenes=?, caption=?, hashtags=? WHERE id=?", (b["voiceover"], b["scenes"], b["caption"], b["hashtags"], sid))
    db.set_setting(f"script_backup_{sid}", None)
    return {"ok": True}


# ---------- séria z jedného videa (1 volanie) ----------
@router.post("/api/ideas/{iid}/series")
def api_series(iid: int):
    """Z nápadu spraví 5-dielnu sériu: 4 pokračovania pribudnú do schránky nápadov."""
    _db()
    idea = db.one("SELECT * FROM ideas WHERE id=?", (iid,))
    if not idea:
        raise HTTPException(404)
    if db.one("SELECT id FROM ideas WHERE source='series' AND source_ref=?", (str(iid),)):
        raise HTTPException(400, "Séria k tomuto videu už existuje (pozri Radar → Nápady).")
    from . import content
    p = content._project(idea["project_id"])
    try:
        data = ai.ask(f"""{content._ctx(p)}
Turn this video into a 5-part series; it is part 1: "{idea['title']}" | hook: {idea['hook']} | angle: {idea['angle'][:300]}
Write parts 2-5. Each must work alone for a new viewer, but together they form a clear journey that makes people follow for the next part.
Each hook: exact first spoken sentence, max 14 words, no greeting. Don't repeat part 1.
Return JSON: {{"series":"series name, max 5 words","ideas":[{{"title":"","hook":"","angle":"","why":"what this part adds"}}]}}
Write in {languages.english(p['source_lang'])}.""", "series", "creative", use_cache=False)
    except ai.NeedManual:
        raise HTTPException(400, "Na sériu treba Claude Code (v ručnom režime nefunguje).")
    name = str((data or {}).get("series") or idea["title"])[:60]
    made = 0
    for k, it in enumerate((data or {}).get("ideas", [])[:4]):
        if not isinstance(it, dict) or not it.get("title"):
            continue
        db.run("""INSERT INTO ideas(project_id,title,hook,angle,pillar,format,why,score,status,source,source_ref,template)
                  VALUES(?,?,?,?,?,?,?,?,'inbox','series',?,?)""",
               (idea["project_id"], str(it["title"])[:300], it.get("hook", ""), it.get("angle", ""), idea["pillar"], idea["format"],
                f"Séria „{name}“, časť {k + 2}/5. {it.get('why', '')}", max(7, int(idea["score"] or 0)), str(iid), idea.get("template") or ""))
        made += 1
    return {"created": made, "series": name}
