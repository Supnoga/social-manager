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


def _singles(pid, skip):
    """Samostatné krátke nápady (bez dlhého) na dni pred prvým dlhým videom kanála."""
    rows = db.q(f"""SELECT i.id, i.title, EXISTS (SELECT 1 FROM scripts s WHERE s.idea_id=i.id AND s.is_source=1) has_script
                   FROM ideas i WHERE i.project_id=? AND COALESCE(i.format,'short')='short' AND i.status IN {LIVE} AND {_no_video()}
                   ORDER BY has_script DESC, COALESCE(i.score,0) DESC, i.id""", (pid,))
    out = []
    for r in rows:
        if r["id"] in skip:
            continue
        c, m = _cover(r["title"] or "")
        if c != "gap":
            out.append(dict(r, cover=c, model=m))
    out.sort(key=lambda r: r["cover"] != "model")
    return out


def build_project(pid, start, days=30, offset=0):
    machine = _machine_project(pid)
    picked, rest, gaps = [], [], {}
    for r in _longs(pid):
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
    used = picked[:len(longs)]
    queue, cur, out = [], None, []
    kids_of = {r["id"]: _children(r["id"]) for r in used}
    singles = _singles(pid, {k["id"] for ks in kids_of.values() for k in ks})
    li = 0
    for day in dates:
        rec = {"date": day.isoformat(), "long": None}
        if (day.toordinal() + offset) % LONG_EVERY == 0:
            if li < len(used):
                r = used[li]
                li += 1
                cur = r
                rec["long"] = {"idea_id": r["id"], "title": r["title"], "script": bool(r["has_script"]), "status": r["status"],
                               "cover": r["cover"], "model": r["model"]}
                ks = [{"idea_id": k["id"], "title": k["title"], "script": bool(k["has_script"])} for k in kids_of[r["id"]]]
                queue = ks + [{"cut": len(ks) + i + 1, "title": r["title"]} for i in range(LONG_EVERY - len(ks))]
                for q in queue:
                    q.update(of=r["id"], cover=r["cover"], model=r["model"])
            else:
                rec["long_gap"] = True
                queue = []
        if queue:
            rec["short"] = queue.pop(0)
        elif singles:
            x = singles.pop(0)
            rec["short"] = {"idea_id": x["id"], "title": x["title"], "script": bool(x["has_script"]), "cover": x["cover"], "model": x["model"]}
        else:
            rec["short"] = None
        out.append(rec)
    nl = [d["long"] for d in out if d["long"]]
    return {"machine": machine, "offset": offset, "days": out, "spare": max(0, len(picked) - len(longs)),
            "summary": {"longs": len(nl), "long_slots": len(longs), "model": sum(1 for x in nl if x["cover"] == "model"),
                        "verify": sum(1 for x in nl if x["cover"] == "verify"),
                        "gap": sum(1 for d in out if d.get("long_gap")) + sum(1 for d in out if not d["short"]),
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
    return {"start": plan.get("start", ""), "days": plan.get("days", 30), "built": plan.get("built", ""),
            "projects": [dict(v, id=int(k), name=names.get(k, k)) for k, v in sorted(projs.items(), key=lambda kv: int(kv[0]))]}
