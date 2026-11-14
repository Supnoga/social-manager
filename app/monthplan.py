"""Mesačný plán (1.64): pre každý kanál na každý deň 1 dlhé video a jeho 3 krátke.

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


def build_project(pid, start, days=30):
    machine = _machine_project(pid)
    picked, rest, gaps = [], [], {}
    for r in _longs(pid):
        title = r["title"] or ""
        m = auto_visual.topic(title, title)
        if m:   # presný model: ide prvé
            r["cover"], r["model"] = "model", m
            picked.append(r)
            continue
        hit = auto_visual.find(title)
        if hit:   # stroj, ku ktorému model ešte nie je = medzera, nečaká sa na kontrolu
            gaps[hit[0]] = gaps.get(hit[0], 0) + 1
            continue
        r["cover"], r["model"] = "verify", ""   # téma bez stroja: rozhodne kontrola obrazu pri skladaní
        rest.append(r)
    picked += rest
    out = []
    d0 = dt.date.fromisoformat(start)
    for n in range(days):
        day = {"date": (d0 + dt.timedelta(days=n)).isoformat()}
        if n < len(picked):
            r = picked[n]
            kids = [{"idea_id": k["id"], "title": k["title"], "script": bool(k["has_script"])} for k in _children(r["id"])]
            kids += [{"cut": len(kids) + i + 1} for i in range(3 - len(kids))]
            day.update(long={"idea_id": r["id"], "title": r["title"], "script": bool(r["has_script"]), "status": r["status"]},
                       cover=r["cover"], model=r["model"], shorts=kids)
        else:
            day["cover"] = "gap"
        out.append(day)
    filled = sum(1 for d in out if d["cover"] != "gap")
    return {"machine": machine, "days": out, "spare": max(0, len(picked) - days),
            "summary": {"filled": filled, "model": sum(1 for d in out if d["cover"] == "model"),
                        "verify": sum(1 for d in out if d["cover"] == "verify"), "gap": days - filled,
                        "scripts_ready": sum(1 for d in out if d.get("long", {}).get("script")),
                        "missing": dict(sorted(gaps.items(), key=lambda kv: -kv[1])[:8])}}


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
    for pid in ids:
        plan["projects"][str(pid)] = build_project(int(pid), start, days)
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
