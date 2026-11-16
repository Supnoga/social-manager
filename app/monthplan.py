"""Mesačný plán (1.64, rytmus 1.65): každý kanál 1 krátke video denne, dlhé každý 3. deň (kanály sa striedajú).
Krátke patria k dlhému: jeho 3 krátke idú v jeho deň (po ňom) a 2 nasledujúce dni.

Bez AI, len z nápadov, ktoré už sú v appke:
- téma s presným modelom (auto_visual.topic) ide prvá; stroj bez modelu sa nepoužije (červená medzera).
- témy bez stroja: „overí sa pri skladaní“ – rozhodne kontrola obrazu (video, ktoré neprejde, ostane zadržané a plán vezme ďalšiu tému).
- krátke: najprv vlastné krátke nápady dlhého videa (parent), zvyšok sú výrezy z dlhého (jedno volanie AI až pri výrobe).
Plán sa ukladá do nastavenia month_plan, nič sa nevyrába ani nenahráva."""
import datetime as dt
import time

from . import auto_visual, db

LIVE = ("new", "approved", "scripted")


def _machine_project(pid):
    rows = db.q("SELECT title FROM ideas WHERE project_id=? ORDER BY id DESC LIMIT 60", (pid,))
    return bool(rows) and sum(1 for r in rows if auto_visual.find(r["title"] or "")) >= max(3, len(rows) * .2)


def _no_video(alias="i"):
    return f"NOT EXISTS (SELECT 1 FROM videos v JOIN scripts s2 ON s2.id=v.script_id WHERE s2.idea_id={alias}.id)"


def _longs(pid):
    return db.q(f"""SELECT i.id, i.title, COALESCE(i.score,0) score, COALESCE(i.ahead,0) ahead, i.status,
                   EXISTS (SELECT 1 FROM scripts s WHERE s.idea_id=i.id AND s.is_source=1) has_script
                   FROM ideas i WHERE i.project_id=? AND i.format='long' AND i.status IN {LIVE} AND {_no_video()}
                   ORDER BY has_script DESC, score DESC, i.id""", (pid,))


def _children(lid):
    return db.q(f"""SELECT i.id, i.title, EXISTS (SELECT 1 FROM scripts s WHERE s.idea_id=i.id AND s.is_source=1) has_script
                   FROM ideas i WHERE i.parent_id=? AND COALESCE(i.format,'short')='short' AND i.status IN {LIVE} AND {_no_video()}
                   ORDER BY has_script DESC, i.id LIMIT 3""", (lid,))


LONG_EVERY = 3   # Oliver 14.11.: každý kanál 1 krátke denne, dlhé každý 3. deň, kanály sa striedajú


def _cover(title):
    m = auto_visual.topic(title, title)
    if m:
        return "model", m
    return ("gap", auto_visual.find(title)[0]) if auto_visual.find(title) else ("verify", "")


def build_project(pid, start, days=30, offset=0):
    machine = _machine_project(pid)
    picked, rest, gaps = [], [], {}
    bad = set(db.get_setting("month_plan_bad", []) or [])   # neprešli kontrolou obrazu vopred
    for r in _longs(pid):
        if r["id"] in bad:
            continue
        c, m = _cover(r["title"] or "")
        if c == "gap":   # stroj, ku ktorému model ešte nie je: nepoužije sa
            gaps[m] = gaps.get(m, 0) + 1
            continue
        r["cover"], r["model"] = c, m
        (picked if c == "model" else rest).append(r)
    picked += rest
    d0 = dt.date.fromisoformat(start)
    dates = [d0 + dt.timedelta(days=n) for n in range(days)]
    longs = [d for d in dates if (d.toordinal() + offset) % LONG_EVERY == 0]
    made = {k.split(":")[1]: v for k, v in (db.get_setting("month_plan_made", {}) or {}).items() if k.split(":")[0] == str(pid)}
    made_rows = {}
    for dte, m in made.items():   # už vyrobené dlhé ostane vo svojom dni aj po prestavaní plánu
        r = db.one("SELECT id, title, COALESCE(score,0) score, status, 1 has_script FROM ideas WHERE id=?", (m.get("long"),))
        if r:
            r["cover"], r["model"] = _cover(r["title"] or "")
            if r["cover"] == "gap":
                r["cover"] = "verify"
            made_rows[dte] = r
    used = picked[:len([d for d in longs if d.isoformat() not in made_rows])]
    queue, cur, out = [], None, []
    kids_of = {r["id"]: _children(r["id"]) for r in used + list(made_rows.values())}
    li = 0
    for day in dates:
        rec = {"date": day.isoformat(), "long": None}
        if (day.toordinal() + offset) % LONG_EVERY == 0:
            if day.isoformat() in made_rows or li < len(used):
                r = made_rows.get(day.isoformat())
                if not r:
                    r = used[li]
                    li += 1
                cur = r
                rec["long"] = {"idea_id": r["id"], "title": r["title"], "script": bool(r["has_script"]), "status": r["status"],
                               "cover": r["cover"], "model": r["model"], "made": day.isoformat() in made_rows}
                ks = [{"idea_id": k["id"], "title": k["title"], "script": bool(k["has_script"])} for k in kids_of[r["id"]]]
                nd = int((made.get(day.isoformat()) or {}).get("shorts") or 0)
                ks = [{"done": True, "title": r["title"], "cut": 0} for _ in range(nd)] + ks
                queue = ks + [{"cut": len(ks) + i + 1, "title": r["title"]} for i in range(LONG_EVERY - len(ks))]
                queue = queue[:LONG_EVERY]
                for q in queue:
                    q.update(of=r["id"], cover=r["cover"], model=r["model"])
            else:
                rec["long_gap"] = True
                queue = []
        if queue:
            rec["short"] = queue.pop(0)
        else:   # kanál začína dlhým videom (Oliver 14.11.): pred prvým dlhým sa nič nezverejní
            rec["short"] = None
            if cur is None:
                rec["wait"] = True
        out.append(rec)
    nl = [d["long"] for d in out if d["long"]]
    return {"machine": machine, "offset": offset, "days": out, "spare": max(0, len(picked) - len(longs)),
            "summary": {"longs": len(nl), "long_slots": len(longs), "model": sum(1 for x in nl if x["cover"] == "model"),
                        "verify": sum(1 for x in nl if x["cover"] == "verify"),
                        "gap": sum(1 for d in out if d.get("long_gap")) + sum(1 for d in out if not d["short"] and not d.get("wait")),
                        "first": next((d["date"] for d in out if d["long"]), ""),
                        "shorts": sum(1 for d in out if d["short"]),
                        "scripts_ready": sum(1 for x in nl if x["script"]),
                        "missing": dict(sorted(gaps.items(), key=lambda kv: -kv[1])[:8])}}


def _set_rhythm(ids):
    """Rytmus do plánovača: krátke o 18:00, dlhé o 14:00 každý 3. deň; kanály rozdelené na tretiny."""
    pp = db.get_setting("plan_projects", {}) or {}
    for n, pid in enumerate(sorted({int(i) for i in ids} | {int(k) for k in pp})):   # posun podľa poradia všetkých kanálov
        cfg = pp.get(str(pid)) or {"days": [0, 1, 2, 3, 4, 5, 6]}
        cfg.update(hours=[18], long_hours=[14], long_every=LONG_EVERY, offset=n % LONG_EVERY)
        pp[str(pid)] = cfg
    db.set_setting("plan_projects", pp)
    return {str(pid): pp[str(pid)]["offset"] for pid in ids}


def build(project_ids=None, start=None, days=30):
    start = start or (dt.date.today() + dt.timedelta(days=1)).isoformat()
    days = max(1, min(62, int(days or 30)))
    plan = db.get_setting("month_plan", {}) or {}
    if not project_ids:   # celý plán: kanály, ktoré sa plánujú (plan_projects), inak všetky
        project_ids = [int(k) for k in (db.get_setting("plan_projects", {}) or {})] or [r["id"] for r in db.q("SELECT id FROM projects ORDER BY id")]
        plan["projects"] = {}
    ids = project_ids
    plan.setdefault("projects", {})
    plan.update(start=start, days=days, built=time.strftime("%Y-%m-%d %H:%M"))
    offs = _set_rhythm(ids)
    for pid in ids:
        plan["projects"][str(pid)] = build_project(int(pid), start, days, offs[str(pid)])
    db.set_setting("month_plan", plan)
    return plan


def get(project_id=0):
    plan = db.get_setting("month_plan", {}) or {}
    names = {str(r["id"]): r["name"] for r in db.q("SELECT id, name FROM projects")}
    projs = plan.get("projects", {})
    if project_id:
        projs = {k: v for k, v in projs.items() if k == str(project_id)}
    made_all = db.get_setting("month_plan_made", {}) or {}

    def live(k, v):
        """Plán sa ukladá pri zostavení; čo sa odvtedy vyrobilo, sa doplní tu (Oliver 16.11.: hotové video ukazovalo „scenár až pri výrobe“)."""
        v = dict(v)
        ids = {x["idea_id"] for r in v.get("days") or [] for x in (r.get("long"), r.get("short")) if x and x.get("idea_id")}
        scripted = {r["idea_id"] for r in db.q(f"SELECT DISTINCT idea_id FROM scripts WHERE is_source=1 AND idea_id IN ({','.join('?' * len(ids))})", tuple(ids))} if ids else set()
        days, cur, idx = [], None, 0
        for r in v.get("days") or []:
            r = dict(r)
            if r.get("short") and r["short"].get("idea_id"):
                r["short"] = dict(r["short"], script=r["short"]["idea_id"] in scripted)
            if r.get("long"):
                cur, idx = made_all.get(f"{k}:{r['date']}") or {}, 0
                mk = bool(cur.get("long"))
                r["long"] = dict(r["long"], made=mk, script=mk or r["long"]["idea_id"] in scripted, cover="model" if r["long"].get("cover") == "model" else ("done" if mk else r["long"].get("cover")))
            if r.get("short") and cur is not None:
                if cur.get("long") and r["short"].get("cover") == "verify":
                    r["short"] = dict(r["short"], cover="done")   # dlhé už prešlo kontrolou obrazu
                if idx < int(cur.get("shorts") or 0):
                    r["short"] = dict(r["short"], done=True)
                idx += 1
            days.append(r)
        v["days"] = days
        nl = [d["long"] for d in days if d.get("long")]
        v["summary"] = dict(v.get("summary") or {}, longs=len(nl), made=sum(1 for x in nl if x["made"]),
                            scripts_ready=sum(1 for x in nl if x["script"]),
                            model=sum(1 for x in nl if x.get("cover") == "model"), verify=sum(1 for x in nl if x.get("cover") == "verify"))
        return v
    return {"start": plan.get("start", ""), "days": plan.get("days", 30), "built": plan.get("built", ""),
            "projects": [dict(live(k, v), id=int(k), name=names.get(k, k), stock=stock_days(int(k))) for k, v in sorted(projs.items(), key=lambda kv: int(kv[0]))]}


def stock_days(pid, today=None):
    """Hlavná merná jednotka (Oliver 15.11.): koľko dní obsahu má kanál pripravených, počítané od dnes bez prerušenia.
    Deň je pokrytý, keď je hotové jeho krátke video (a v deň dlhého aj dlhé). Pred prvým dlhým videom kanál nič nezverejňuje."""
    today = today or dt.date.today()
    pp = (db.get_setting("plan_projects", {}) or {}).get(str(pid)) or {}
    offset = int(pp.get("offset", 0))
    made = {}
    for k, v in (db.get_setting("month_plan_made", {}) or {}).items():
        p, _, d = k.partition(":")
        if p == str(pid) and (v or {}).get("long"):
            made[d] = int((v or {}).get("shorts") or 0)
    if not made:
        return 0
    first = min(made)
    n, day = 0, today
    while n < 120:
        if day.isoformat() < first:   # kanál ešte nezačal: čaká na svoje prvé dlhé
            n += 1
            day += dt.timedelta(days=1)
            continue
        back = (day.toordinal() + offset) % LONG_EVERY   # koľko dní od posledného dňa dlhého videa
        ld = day - dt.timedelta(days=back)
        if ld.isoformat() not in made or made[ld.isoformat()] <= back:
            break
        n += 1
        day += dt.timedelta(days=1)
    return n


def stock_all():
    """Zásoba dní pre všetky kanály (aj tie, ktoré ešte nemajú plán: 0)."""
    return [{"id": r["id"], "name": r["name"], "days": stock_days(r["id"])} for r in db.q("SELECT id, name FROM projects ORDER BY id")]
