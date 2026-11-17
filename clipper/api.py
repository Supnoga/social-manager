"""Stránka a API Clippera (/clip, /api/clip/...). Všetko je prístupné len z tohto počítača;
zvonku ide iba tajný odkaz na súbor klipu, ktorý si sťahuje TikTok (/pub/c/...)."""
import json
import re
import threading
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from starlette.concurrency import run_in_threadpool

from app import ai
from app import db as appdb

from . import env, publish, source, store, track, worker

router = APIRouter()
STATIC = Path(__file__).resolve().parent / "static"
NETS = ("youtube", "instagram", "tiktok", "facebook")
SITES = {"whop": "Whop", "clipping": "Clipping.net", "vyro": "Vyro", "vues": "Vues", "other": "Iná"}


@router.get("/clip")
def page():
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))


@router.get("/pub/c/{clip_id}/{fname}")
def public_clip(clip_id: int, fname: str):
    if Path(fname).stem != publish.clip_token(clip_id):
        raise HTTPException(404)
    c = store.one("SELECT path FROM clips WHERE id=?", (clip_id,))
    if not c or not Path(c["path"] or "").exists():
        raise HTTPException(404)
    return FileResponse(c["path"], media_type="video/mp4")


@router.get("/api/clip/file/{clip_id}")
def clip_file(clip_id: int):
    c = store.one("SELECT path FROM clips WHERE id=?", (clip_id,))
    if not c or not Path(c["path"] or "").exists():
        raise HTTPException(404)
    return FileResponse(c["path"], media_type="video/mp4")


# ---------- prehľad ----------
def _settings():
    return {"autopublish": bool(store.get("autopublish", False)), "paused": bool(store.get("paused", False)),
            "batches": ["%02d:%02d" % divmod(b, 60) for b in publish.batches()], "warmup": bool(store.get("warmup", True)),
            "ai_per_day": int(store.get("ai_per_day", 6)),
            "min_score": float(store.get("min_score", 6)), "per_day_default": int(store.get("per_day_default", 3))}


@router.get("/api/clip/state")
def state():
    totals = track.campaign_totals()
    camps = []
    for c in store.q("SELECT * FROM campaigns ORDER BY status='active' DESC, id DESC"):
        c["networks"] = json.loads(c["networks"] or "[]")
        c["site_name"] = SITES.get(c["site"], c["site"])
        c["totals"] = totals.get(c["id"], {"posted": 0, "queued": 0, "views": 0, "est": 0.0, "paid": 0.0, "todo": 0})
        n = {r["status"]: r["n"] for r in store.q("SELECT status, COUNT(*) n FROM clips WHERE campaign_id=? GROUP BY status", (c["id"],))}
        c["clips"] = n
        c["points"] = track.points(c)
        c["sources"] = store.one("SELECT COUNT(*) n FROM sources WHERE campaign_id=? AND status IN ('new','fetching','transcribing','ready')",
                                 (c["id"],))["n"]
        camps.append(c)
    names = {c["id"]: c["name"] for c in camps}
    accs = store.accounts()
    acc_name = {a["id"]: a["name"] for a in accs}
    sources = store.q("SELECT id, campaign_id, url, title, duration, status, error, created_at FROM sources ORDER BY id DESC LIMIT 100")
    for s in sources:
        s["campaign"] = names.get(s["campaign_id"], "")
        s["clips"] = store.one("SELECT COUNT(*) n FROM clips WHERE source_id=?", (s["id"],))["n"]
    clips = store.q("SELECT id, source_id, campaign_id, t0, t1, hook, title, caption, why, score, layout, duration, status, error, created_at "
                    "FROM clips ORDER BY CASE status WHEN 'ready' THEN 0 WHEN 'picked' THEN 1 WHEN 'approved' THEN 2 "
                    "WHEN 'failed' THEN 3 ELSE 4 END, id DESC LIMIT 300")
    posts = store.q("SELECT p.*, c.campaign_id, c.title clip_title, c.hook FROM posts p JOIN clips c ON c.id=p.clip_id "
                    "ORDER BY p.scheduled_at DESC LIMIT 600")
    camp_by = {c["id"]: c for c in camps}
    by_clip = {}
    for p in posts:
        p["account"] = acc_name.get(p["account_id"], "")
        p["campaign"] = names.get(p["campaign_id"], "")
        camp = camp_by.get(p["campaign_id"]) or {}
        p["est"] = track.earn(p["views"], camp) if p["status"] == "posted" and p["submit"] not in ("rejected", "missed") else 0
        p["deadline"] = track.deadline(p.get("posted_at"), camp.get("site")) if p["status"] == "posted" else ""
        by_clip.setdefault(p["clip_id"], []).append({"platform": p["platform"], "status": p["status"], "url": p["url"],
                                                     "views": p["views"], "when": p["scheduled_at"]})
    for c in clips:
        c["campaign"] = names.get(c["campaign_id"], "")
        c["posts"] = by_clip.get(c["id"], [])
    day = datetime.now().strftime("%Y-%m-%d")
    posted = [p for p in posts if p["status"] == "posted"]
    summary = {
        "views": sum(p["views"] or 0 for p in posted), "posted": len(posted),
        "today": sum(1 for p in posted if (p.get("posted_at") or p["updated_at"] or "")[:10] == day),
        "queued": sum(1 for p in posts if p["status"] in ("queued", "posting")),
        "est": round(sum(t["est"] for t in totals.values()), 2), "paid": round(sum(t["paid"] for t in totals.values()), 2),
        "todo": sum(1 for p in posted if p["submit"] == "todo" and p["url"]),
        "review": sum(1 for c in clips if c["status"] == "ready"),
        "failed": sum(1 for p in posts if p["status"] == "failed"),
        "ai_today": int((store.get("ai_calls", {}) or {}).get(day, 0)),
    }
    return {"settings": _settings(), "worker": dict(worker.STATE), "tools": {"ready": env.ready(), **env.STATE},
            "campaigns": camps, "sources": sources, "clips": clips, "posts": posts, "accounts": accs, "summary": summary,
            "sites": SITES, "now": store.now(), "project_id": store.project_id(), "public_ok": bool(_public_ok())}


def _public_ok():
    try:
        from app.platforms import tiktok_business
        return tiktok_business.public_base().startswith("https://")
    except Exception:
        return False


# ---------- kampane ----------
def _num(v, default=0.0):
    try:
        return float(str(v).replace(",", ".").replace("$", "").strip() or default)
    except Exception:
        return default


FIELDS = ("name", "site", "url", "rate", "min_views", "max_payout", "budget", "networks", "tags", "rules", "about", "lang",
          "per_day", "clip_min", "clip_max", "kind", "winners", "spent", "clippers", "age_days", "viral", "fit", "logo", "caption")


def _clean(d):
    out = {}
    if "name" in d:
        out["name"] = str(d["name"] or "").strip()[:120] or "Kampaň"
    if "site" in d:
        out["site"] = d["site"] if d["site"] in SITES else "other"
    for k in ("url", "tags", "rules", "about", "winners", "logo", "caption"):
        if k in d:
            out[k] = str(d[k] or "").strip()[:4000]
    for k in ("clippers", "age_days"):
        if k in d:
            out[k] = int(max(0, _num(d[k])))
    for k in ("viral", "fit"):                  # ručný odhad 1-10, 0 = nech to appka odhadne sama
        if k in d:
            out[k] = int(min(10, max(0, _num(d[k]))))
    for k in ("rate", "max_payout", "budget", "spent"):
        if k in d:
            out[k] = max(0.0, _num(d[k]))
    if "min_views" in d:
        out["min_views"] = int(max(0, _num(d["min_views"])))
    if "networks" in d:
        nets = d["networks"] if isinstance(d["networks"], list) else re.split(r"[,\s]+", str(d["networks"]))
        out["networks"] = json.dumps([n for n in NETS if n in [str(x).lower() for x in nets]] or ["youtube", "instagram", "tiktok"])
    if "lang" in d:
        out["lang"] = (str(d["lang"] or "en").strip().lower() or "en")[:2]
    if "kind" in d:
        out["kind"] = d["kind"] if d["kind"] in ("auto", "speech", "visual") else "auto"
    if "per_day" in d:
        out["per_day"] = int(min(60, max(1, _num(d["per_day"], 6))))
    if "clip_min" in d:
        out["clip_min"] = int(min(120, max(8, _num(d["clip_min"], 15))))
    if "clip_max" in d:
        out["clip_max"] = int(min(180, max(out.get("clip_min", 12) + 5, _num(d["clip_max"], 45))))
    return out


@router.post("/api/clip/campaign")
async def campaign_save(request: Request):
    d = await request.json()
    vals = _clean(d)
    cid = d.get("id")
    if cid:
        if vals:
            store.run("UPDATE campaigns SET " + ", ".join(f"{k}=?" for k in vals) + " WHERE id=?", list(vals.values()) + [int(cid)])
    else:
        vals.setdefault("name", "Kampaň")
        cid = store.run("INSERT INTO campaigns(" + ", ".join(vals) + ") VALUES(" + ", ".join("?" for _ in vals) + ")", list(vals.values()))
    for u in re.split(r"[\s,]+", str(d.get("sources") or "")):
        if u.strip():
            source.add(int(cid), u.strip())
    return {"ok": True, "id": int(cid)}


@router.post("/api/clip/campaign/{cid}/status")
async def campaign_status(cid: int, request: Request):
    st = (await request.json()).get("status")
    if st not in ("active", "paused", "ended"):
        raise HTTPException(400)
    store.run("UPDATE campaigns SET status=? WHERE id=?", (st, cid))
    return {"ok": True}


@router.post("/api/clip/brief")
async def brief(request: Request):
    """Z textu skopírovaného zo stránky kampane vytiahne pravidlá (lacné AI volanie)."""
    text = str((await request.json()).get("text") or "").strip()[:9000]
    if len(text) < 40:
        raise RuntimeError("Vlož text zo stránky kampane.")
    prompt = (
        "Below is text copied from a paid clipping campaign page (Whop Content Rewards, Clipping.net, Vyro or similar). "
        "Extract the campaign terms. Return JSON with keys: "
        '"name" (short campaign name), "rate" (USD per 1000 views, number), "min_views" (minimum views per clip to get paid, integer, 0 if none), '
        '"max_payout" (max USD per clip, 0 if none), "budget" (total USD budget, 0 if unknown), '
        '"networks" (array from: youtube, instagram, tiktok, facebook), '
        '"tags" (required hashtags, @mentions and disclosure tags such as #ad exactly as written, space separated, "" if none), '
        '"clip_min" and "clip_max" (required clip length in seconds, only if the text states it), '
        '"rules" (the content rules a clip editor must follow, max 600 characters, in English), '
        '"about" (who or what the source content is, max 200 characters), "lang" (2-letter language of the content), '
        '"winners" (headlines and view counts of the top / most viewed clips if the page lists them, max 400 characters, "" if none), '
        '"sources" (array of URLs of source videos or channels found in the text), '
        '"spent" (USD already paid out or used from the budget, 0 if not shown), "clippers" (number of creators who joined or submitted, 0 if not shown), '
        '"age_days" (how many days the campaign has been running, 0 if not shown), '
        '"viral" (1-10: how likely short clips of this content go viral on TikTok, Reels and Shorts: famous person, emotional or controversial '
        'topic, broad audience = high; niche product, ad-like footage, little to say = low), '
        '"kind" ("speech" if clips are cut from people talking: podcasts, interviews, talks, streamers; "visual" for trailers, gameplay, '
        'sport, music or product footage; "auto" if unclear), "gambling" (true if it promotes a casino, betting, poker or other gambling), '
        '"risk" ("" or one short Slovak sentence if the campaign is about gambling, betting, casino, crypto trading, adult content or looks like a scam).\n\n'
        "TEXT:\n" + text)
    try:
        data = await run_in_threadpool(lambda: ai.ask(prompt, "clip_brief", kind="cheap", timeout=300))
    except ai.NeedManual:
        raise RuntimeError("AI nie je dostupná (Claude nie je prihlásený na Macu). Vyplň kampaň ručne.")
    if not isinstance(data, dict):
        raise RuntimeError("Z textu sa nepodarilo vyčítať pravidlá, vyplň kampaň ručne.")
    out = _clean({k: data[k] for k in FIELDS if data.get(k) is not None})
    out["networks"] = json.loads(out.get("networks", '["youtube","instagram","tiktok"]'))
    out["sources"] = [u for u in (data.get("sources") or []) if isinstance(u, str) and u.startswith("http")][:20]
    out["risk"] = str(data.get("risk") or "")[:200]
    out["grade"], out["verdict"] = track.judge(out.get("rate"), out.get("budget"), _num(data.get("spent")), _num(data.get("clippers")),
                                               _num(data.get("age_days")))
    if data.get("gambling") is True:       # rozhodnutie Olivera 16.11.2026: kasína a stávkovanie nebrať
        out["grade"] = "bad"
        out["verdict"].insert(0, "Kasína a stávkovanie neberieme: platia najmenej a siete za ne mažú videá aj účty.")
    return out


# ---------- zdroje ----------
@router.post("/api/clip/source")
async def source_add(request: Request):
    d = await request.json()
    cid = int(d.get("campaign_id") or 0)
    if not store.campaign(cid):
        raise RuntimeError("Najprv vyber kampaň.")
    n = 0
    for u in re.split(r"[\s,]+", str(d.get("urls") or "")):
        if u.strip():
            source.add(cid, u.strip())
            n += 1
    if not n:
        raise RuntimeError("Vlož aspoň jeden odkaz na video.")
    return {"ok": True, "added": n}


@router.post("/api/clip/source/{sid}/retry")
def source_retry(sid: int):
    store.run("UPDATE sources SET status=CASE WHEN words_path!='' AND path!='' THEN 'ready' ELSE 'new' END, error='' WHERE id=?", (sid,))
    return {"ok": True}


# ---------- klipy ----------
@router.post("/api/clip/clip/{clip_id}")
async def clip_action(clip_id: int, request: Request):
    d = await request.json()
    c = store.one("SELECT * FROM clips WHERE id=?", (clip_id,))
    if not c:
        raise HTTPException(404)
    act = d.get("action")
    edits = {k: str(d[k]).strip()[:300] for k in ("hook", "title", "caption") if k in d}
    if edits:
        store.run("UPDATE clips SET " + ", ".join(f"{k}=?" for k in edits) + " WHERE id=?", list(edits.values()) + [clip_id])
    if act == "approve" and c["status"] == "ready":
        store.run("UPDATE clips SET status='approved' WHERE id=?", (clip_id,))
    elif act == "reject" and c["status"] in ("ready", "picked", "approved", "failed"):
        store.run("UPDATE clips SET status='rejected' WHERE id=?", (clip_id,))
    elif act == "redo" and c["status"] in ("ready", "failed", "rejected"):   # znova vystrihnúť (napr. po úprave titulku)
        store.run("UPDATE clips SET status='picked', error='' WHERE id=?", (clip_id,))
    return {"ok": True}


@router.post("/api/clip/approve_all")
def approve_all():
    n = store.one("SELECT COUNT(*) n FROM clips WHERE status='ready'")["n"]
    store.run("UPDATE clips SET status='approved' WHERE status='ready'")
    return {"ok": True, "approved": n}


# ---------- zverejnenia a odosielanie do kampane ----------
@router.post("/api/clip/post/{post_id}")
async def post_edit(post_id: int, request: Request):
    d = await request.json()
    p = store.one("SELECT * FROM posts WHERE id=?", (post_id,))
    if not p:
        raise HTTPException(404)
    if d.get("submit") in track.SUBMIT:
        store.run("UPDATE posts SET submit=?, submitted_at=CASE WHEN ?='submitted' THEN ? ELSE submitted_at END WHERE id=?",
                  (d["submit"], d["submit"], store.now(), post_id))
    if "paid" in d:
        store.run("UPDATE posts SET paid=?, submit='paid' WHERE id=?", (max(0.0, _num(d["paid"])), post_id))
    if "url" in d and str(d["url"]).startswith("http"):
        store.run("UPDATE posts SET url=? WHERE id=?", (str(d["url"]).strip()[:500], post_id))
    if d.get("now") and p["status"] == "queued":      # tento jeden klip zverejniť hneď (bez ostatných účtov)
        store.run("UPDATE posts SET scheduled_at=? WHERE id=?", (store.now(), post_id))
    if d.get("retry") and p["status"] == "failed":
        store.run("UPDATE posts SET status='queued', attempts=0, error='', scheduled_at=? WHERE id=?", (store.now(), post_id))
    return {"ok": True}


@router.post("/api/clip/submitted")
async def submitted(request: Request):
    ids = [int(x) for x in ((await request.json()).get("ids") or [])][:500]
    for i in ids:
        store.run("UPDATE posts SET submit='submitted', submitted_at=? WHERE id=? AND submit='todo'", (store.now(), i))
    return {"ok": True, "n": len(ids)}


@router.post("/api/clip/batch_now")
def batch_now():
    """Zverejní dávku hneď (z každého účtu jeden naplánovaný klip): keď je človek práve pri počítači a stihne vložiť odkazy."""
    return {"ok": True, "n": publish.batch_now()}


# ---------- účty a nastavenia ----------
@router.post("/api/clip/instagram")
async def instagram_connect(request: Request):
    """Klipový Instagram bez Facebook stránky: vloží sa token z Meta appky (priame prihlásenie cez Instagram)."""
    from app.platforms import meta
    from app.platforms.common import PlatformError
    d = await request.json()
    tok, ig_id = str(d.get("token") or "").strip(), re.sub(r"\D", "", str(d.get("ig_id") or "")) or None
    if len(tok) < 40:
        raise RuntimeError("Vlož celý token z Meta appky.")
    try:
        aid = await run_in_threadpool(lambda: meta.connect_instagram(tok, store.project_id(), "", ig_id))
    except PlatformError as e:
        raise RuntimeError(str(e)[:300])
    return {"ok": True, "id": aid}


@router.post("/api/clip/account/{account_id}")
async def account_edit(account_id: int, request: Request):
    d = await request.json()
    if not appdb.one("SELECT id FROM accounts WHERE id=? AND project_id=?", (account_id, store.project_id())):
        raise HTTPException(404)
    cur = store.one("SELECT * FROM clip_accounts WHERE account_id=?", (account_id,)) or {"active": 1, "per_day": store.get("per_day_default", 3)}
    active = int(bool(d.get("active", cur["active"])))
    per_day = int(min(6, max(1, _num(d.get("per_day", cur["per_day"]), 3))))
    store.run("INSERT INTO clip_accounts(account_id, active, per_day) VALUES(?,?,?) "
              "ON CONFLICT(account_id) DO UPDATE SET active=excluded.active, per_day=excluded.per_day", (account_id, active, per_day))
    return {"ok": True}


@router.post("/api/clip/settings")
async def settings_save(request: Request):
    d = await request.json()
    if "autopublish" in d:
        store.put("autopublish", bool(d["autopublish"]))
    if "paused" in d:
        store.put("paused", bool(d["paused"]))
    if "batches" in d:
        raw = d["batches"] if isinstance(d["batches"], list) else re.split(r"[,;\s]+", str(d["batches"]))
        ok = [x.strip().replace(".", ":") for x in raw if re.match(r"^\s*([01]?\d|2[0-3])[:.][0-5]\d\s*$", str(x))]
        if ok:
            store.put("batches", ok[:6])
    if "warmup" in d:
        store.put("warmup", bool(d["warmup"]))
    if "ai_per_day" in d:
        store.put("ai_per_day", int(min(40, max(0, _num(d["ai_per_day"], 6)))))
    if "min_score" in d:
        store.put("min_score", min(10.0, max(1.0, _num(d["min_score"], 6))))
    if d.get("replan"):
        publish.replan()
    if d.get("refresh_stats"):
        threading.Thread(target=track.tick, kwargs={"force": True}, daemon=True).start()
    return {"ok": True, "settings": _settings()}
