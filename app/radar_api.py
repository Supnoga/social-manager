"""API pre Radar (trendy, konkurencia, schránka nápadov), Výsledky a plánovanie na týždeň."""
import datetime as dt
import json
import threading

from fastapi import APIRouter, Body, HTTPException

from . import ai, content, db, planner, radar, stats

router = APIRouter()


def _ideas(pid, status):
    rows = db.q("SELECT * FROM ideas WHERE project_id=? AND status=? ORDER BY score DESC, id DESC", (pid, status))
    for r in rows:
        try:
            r["ref"] = json.loads(r.get("source_ref") or "{}") if r.get("source") == "radar" else {}
        except Exception:
            r["ref"] = {}
    return rows


@router.get("/api/radar/{pid}/inbox")
def inbox(pid: int):
    return {"inbox": _ideas(pid, "inbox"), "snoozed": _ideas(pid, "snoozed")}


@router.post("/api/radar/idea/{iid}")
def idea_action(iid: int, data: dict = Body(...)):
    st = {"accept": "new", "snooze": "snoozed", "reject": "rejected"}.get(data.get("action"))
    if not st:
        raise HTTPException(400, "Neznáma akcia")
    db.run("UPDATE ideas SET status=? WHERE id=?", (st, iid))
    if st == "snoozed":
        db.run("UPDATE ideas SET expires_at=? WHERE id=?", ((dt.date.today() + dt.timedelta(days=30)).isoformat(), iid))
    return {"ok": True}


@router.get("/api/radar/{pid}/trends")
def trends(pid: int):
    kw = db.q("SELECT lang, core FROM project_keywords WHERE project_id=?", (pid,))
    return {"trends": radar.project_trends(pid), "keywords": {r["lang"]: json.loads(r["core"] or "[]") for r in kw},
            "items": db.one("SELECT COUNT(*) n FROM trend_items")["n"]}


@router.post("/api/radar/{pid}/trend")
def trend_action(pid: int, data: dict = Body(...)):
    act, key = data.get("action"), data.get("key", "")
    if act == "idea":
        return content.radar_quick(pid, {"trend": key})
    if act in ("ignored", "pinned"):
        db.run("INSERT OR REPLACE INTO trend_status(project_id, cluster_key, status, label) VALUES(?,?,?,?)",
               (pid, key, act, data.get("label", "")))
    elif act == "unpin":
        db.run("DELETE FROM trend_status WHERE project_id=? AND cluster_key=?", (pid, key))
    return {"ok": True}


@router.post("/api/radar/{pid}/keywords")
def keywords(pid: int):
    return content.radar_keywords(pid)


@router.post("/api/radar/{pid}/weekly")
def weekly(pid: int):
    return content.radar_weekly(pid)


@router.get("/api/radar/{pid}/competitors")
def competitors(pid: int):
    return {"competitors": db.q("""SELECT c.*, (SELECT COUNT(*) FROM comp_posts cp WHERE cp.competitor_id=c.id) posts
                                   FROM competitors c WHERE project_id=? ORDER BY id""", (pid,)),
            "outliers": radar.outliers(pid)[:30], "yt_key": bool(radar.yt_key()),
            "proven": radar.proven(pid, "long", 25), "patterns": radar.title_patterns(pid, "long")}


@router.post("/api/radar/{pid}/competitors")
def comp_add(pid: int, data: dict = Body(...)):
    added, errors = [], []
    for url in [u.strip() for u in (data.get("urls") or "").replace(",", "\n").split("\n") if u.strip()][:30]:
        try:
            added.append(radar.resolve_competitor(pid, url))
        except Exception as e:
            errors.append(f"{url}: {e}")
    return {"added": added, "errors": errors}


@router.delete("/api/radar/competitors/{cid}")
def comp_del(cid: int):
    db.run("DELETE FROM comp_posts WHERE competitor_id=?", (cid,))
    db.run("DELETE FROM competitors WHERE id=?", (cid,))
    return {"ok": True}


@router.post("/api/radar/{pid}/comp-post/{cpid}")
def comp_post(pid: int, cpid: int, data: dict = Body(...)):
    if data.get("action") == "idea":
        return content.radar_quick(pid, {"comp_post": cpid})
    db.run("UPDATE comp_posts SET status='hidden' WHERE id=?", (cpid,))
    return {"ok": True}


@router.get("/api/radar/status")
def status():
    return radar.status()


@router.post("/api/radar/run")
def run_now():
    if radar.STATE["running"]:
        return {"ok": True, "running": True}

    def go():
        for name in radar.JOBS:
            radar.run_job(name)
    threading.Thread(target=go, daemon=True).start()
    return {"ok": True}


@router.post("/api/radar/yt-key")
def yt_key(data: dict = Body(...)):
    key = (data.get("key") or "").strip()
    old = db.get_setting("yt_api_key", "")
    db.set_setting("yt_api_key", key)
    try:
        radar._yt("videos", part="id", chart="mostPopular", regionCode="SK", maxResults=1)
    except Exception as e:
        db.set_setting("yt_api_key", old)
        raise HTTPException(400, f"Kľúč nefunguje: {e}")
    return {"ok": True}


# ---------- Výsledky a opakovanie úspešných ----------
@router.get("/api/results/{pid}")
def results(pid: int):
    return stats.overview(pid)


@router.post("/api/results/refresh")
def results_refresh():
    stats.job()
    return {"ok": True}


@router.post("/api/results/{pid}/repeat")
def repeat(pid: int):
    try:
        return planner.repeat_winners(pid)
    except ai.NeedManual:
        raise HTTPException(400, "Na variácie treba Claude Code (v ručnom režime nefunguje).")


# ---------- Plánovanie na týždeň ----------
@router.post("/api/plan/week")
def plan_week(data: dict = Body(default={})):
    if data.get("per_day"):
        db.set_setting("plan_per_day", int(data["per_day"]))
    return planner.plan_week(data.get("project_ids") or None, int(data.get("days") or 7), data.get("per_day"),
                             bool(data.get("dry")))
