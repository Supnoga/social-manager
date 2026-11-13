"""Social Manager - hlavný server. Spúšťa sa cez start.bat / start.command."""
import json
import os
import random
import secrets
import shutil
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import ai, anim, brand, content, db, explainer, footage, languages, media, scheduler, nightly, tunnel, pronounce, updater, voices
from .platforms import linkedin, meta, tiktok, tiktok_business, youtube
from .platforms.common import PORT, PlatformError

STATIC = db.BASE_DIR / "static"
VIDEO_DIR = db.MEDIA_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}

app = FastAPI(title="Social Manager")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
_oauth_states = {}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


@app.middleware("http")
async def only_local(request: Request, call_next):
    """Ochrana: zvonka (cez tunel) je dostupné len /pub/ (tajné odkazy na videá), návrat z TikToku a overovací súbor."""
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host not in LOCAL_HOSTS or request.headers.get("cf-connecting-ip"):
        p = request.url.path
        if not (p.startswith("/pub/") or p.startswith("/oauth/ttb/callback") or (p.count("/") == 1 and p.endswith(".txt"))):
            return JSONResponse({"error": "forbidden"}, status_code=403)
    return await call_next(request)


@app.exception_handler(RuntimeError)
@app.exception_handler(ai.AIError)
@app.exception_handler(PlatformError)
async def _err(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=400)


@app.exception_handler(ai.NeedManual)
async def _manual(request, exc):
    return JSONResponse({"manual": True, "prompt": exc.prompt, "task": exc.purpose,
                         "params": getattr(exc, "params", {})})


@app.on_event("startup")
def _start():
    db.con()
    scheduler.start()
    tunnel.start()


def _page():
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))


# ---------------- OAuth návraty ----------------
@app.get("/")
def index(code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"/#/ucty?err={error}")
    if code and state.startswith("yt:"):
        info = _oauth_states.pop(state, {})
        try:
            youtube.callback(code, info.get("project_id"), info.get("lang", ""), info.get("client", 0))
            return RedirectResponse("/#/ucty?ok=youtube")
        except Exception as e:
            return RedirectResponse(f"/#/ucty?err={str(e)[:200]}")
    return _page()


@app.get("/oauth/tiktok/callback/")
def tiktok_cb(code: str = "", state: str = "", error: str = "", error_description: str = ""):
    if error:
        return RedirectResponse(f"/#/ucty?err=TikTok: {error_description or error}")
    info = _oauth_states.pop(state, {})
    try:
        tiktok.callback(code, state, info.get("project_id"), info.get("lang", ""))
        return RedirectResponse("/#/ucty?ok=tiktok")
    except Exception as e:
        return RedirectResponse(f"/#/ucty?err={str(e)[:200]}")


@app.get("/oauth/linkedin/callback")
def linkedin_cb(code: str = "", state: str = "", error: str = "", error_description: str = ""):
    if error:
        return RedirectResponse(f"/#/ucty?err=LinkedIn: {error_description or error}")
    info = _oauth_states.pop(state, {})
    try:
        linkedin.callback(code, info.get("project_id"), info.get("lang", ""), info.get("org", False))
        return RedirectResponse("/#/ucty?ok=linkedin")
    except Exception as e:
        return RedirectResponse(f"/#/ucty?err={str(e)[:200]}")


@app.get("/oauth/ttb/callback/")
def ttb_cb(auth_code: str = "", code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"/#/ucty?err=TikTok: {error}")
    info = _oauth_states.pop(state, {})
    try:
        tiktok_business.callback(auth_code or code, info.get("project_id"), info.get("lang", ""))
        return RedirectResponse("http://localhost:%d/#/ucty?ok=tiktok" % PORT)
    except Exception as e:
        return RedirectResponse(f"http://localhost:{PORT}/#/ucty?err={str(e)[:200]}")


@app.get("/pub/{vid}/{fname}")
def public_video(vid: int, fname: str):
    """Verejný (tajný) odkaz na video - odtiaľ si ho stiahne TikTok Business."""
    if Path(fname).stem != tiktok_business.video_token(vid):
        raise HTTPException(404)
    v = db.one("SELECT file_path FROM videos WHERE id=?", (vid,))
    if not v or not Path(v["file_path"]).exists():
        raise HTTPException(404)
    return FileResponse(v["file_path"], media_type="video/mp4")


@app.get("/{fname}.txt")
def verify_file(fname: str):
    """Overovací súbor pre TikTok (URL prefix) - obsah vložíš v Nastaveniach."""
    vf = db.get_setting("verify_files", {}) or {}
    if fname + ".txt" in vf:
        return HTMLResponse(vf[fname + ".txt"], media_type="text/plain")
    raise HTTPException(404)


# ---------------- Dlhé úlohy na pozadí (prehliadač sa len pýta na stav, spojenie sa nepreruší) ----------------
JOBS = {}


@app.post("/api/job")
def job_start(data: dict = Body(...)):
    import threading
    import httpx
    url = data.get("url", "")
    if not url.startswith("/api/") or url.startswith("/api/job"):
        raise HTTPException(400)
    jid = secrets.token_hex(8)
    JOBS[jid] = {"done": False}

    def run():
        try:
            r = httpx.request(data.get("method", "POST"), f"http://127.0.0.1:{PORT}{url}", json=data.get("body"),
                              timeout=3600)
            try:
                body = r.json()
            except Exception:
                body = {"error": r.text[:300]}
            JOBS[jid] = {"done": True, "status": r.status_code, "body": body}
        except Exception as e:
            JOBS[jid] = {"done": True, "status": 500, "body": {"error": f"Úloha zlyhala: {e}"}}

    threading.Thread(target=run, daemon=True).start()
    if len(JOBS) > 200:
        for k in [k for k, v in JOBS.items() if v.get("done")][:100]:
            JOBS.pop(k, None)
    return {"job": jid}


@app.get("/api/ping")
def ping():
    return {"ok": True, "version": updater.version()}


@app.post("/api/quit")
def quit_app():
    """Vypne appku (beží na pozadí bez okna)."""
    import threading
    threading.Timer(0.5, lambda: os._exit(0)).start()
    return {"ok": True}


@app.get("/api/job/{jid}")
def job_state(jid: str):
    j = JOBS.get(jid)
    if not j:
        raise HTTPException(404, "Úloha sa stratila (appka sa asi reštartovala) – skús znova")
    if j["done"]:
        JOBS.pop(jid, None)
    return j


# ---------------- Všeobecné ----------------
@app.get("/api/meta")
def api_meta():
    return {
        "languages": languages.as_list(),
        "countries": languages.countries_list(),
        "ai": ai.status(),
        "models": ai.models(),
        "settings": {k: db.get_setting(k, d) for k, d in [("ai_mode", "auto"), ("paused", False),
                                                          ("tt_mode", "inbox"), ("meta_api_version", "v25.0"),
                                                          ("claude_path", ""), ("public_base_url", ""), ("ttb_draft", False),
                                                          ("ttb_ai_label", False), ("cf_tunnel_token", ""),
                                                          ("jitter_min", 10), ("verify_files", {}),
                                                          ("mt_azure_region", ""), ("mt_google", False),
                                                          ("require_approval", True), ("plan_per_day", 1),
                                                          ("auto_plan_week", False), ("radar_enabled", True),
                                                          ("radar_weekly", True), ("plan_projects", {}), ("auto_produce", {})]},
        "inbox_count": db.one("SELECT COUNT(*) n FROM ideas WHERE status='inbox'")["n"],
        "yt_key": bool(db.get_setting("yt_api_key", "")),
        "ttb_redirect": tiktok_business.redirect_uri(), "ttb_redirect_local": tiktok_business.redirect_is_local(),
        "tunnel": tunnel.status(),
        "has": {"yt_client": bool(db.get_setting("yt_client")), "tt_creds": bool(db.get_setting("tt_client_key")),
                "ttb_creds": bool(db.get_setting("ttb_app_id")),
                "li_creds": bool(db.get_setting("li_client_id")), "li_org": bool(db.get_setting("li_org_client_id"))},
        "li": {"page_langs": linkedin.page_langs(), "target": db.get_setting("li_target", True),
               "followers": db.get_setting("li_followers", 0) or 0},
        "scheduler": scheduler.state,
        "yt_usage": youtube.usage(),
        "ffmpeg": bool(media.ffmpeg()),
        "google_tts": voices.google_usage(),
        "mt": __import__("app.translate", fromlist=["usage"]).usage(),
        "footage": footage.status(),
        "anim": __import__("app.anim", fromlist=["status"]).status(),
        "review_count": db.one("SELECT COUNT(*) n FROM posts WHERE status='review'")["n"],
        "night": nightly.status(),
    }


@app.post("/api/settings")
def api_settings(data: dict = Body(...)):
    allowed = {"ai_mode", "model_creative", "model_cheap", "paused", "claude_path", "meta_api_version", "tt_mode",
               "public_base_url", "ttb_draft", "ttb_ai_label", "cf_tunnel_token", "jitter_min", "ttb_redirect",
               "update_repo", "auto_update", "google_tts_key", "google_tts_budget", "update_token",
               "mt_deepl_key", "mt_azure_key", "mt_azure_region", "mt_google", "require_approval",
               "pexels_key", "pixabay_key", "cf_account", "cf_ai_token", "ai_images",
               "plan_per_day", "auto_plan_week", "radar_enabled", "radar_weekly", "li_page_langs", "li_target", "plan_projects", "auto_produce", "night"}
    if "verify_name" in data and data.get("verify_name"):
        vf = db.get_setting("verify_files", {}) or {}
        vf[data["verify_name"].strip().split("/")[-1]] = data.get("verify_content", "")
        db.set_setting("verify_files", vf)
    if "cf_tunnel_token" in data:  # Cloudflare kopíruje celý príkaz, vezmeme len token eyJ…
        import re as _re
        raw = str(data["cf_tunnel_token"] or "").strip()
        m = _re.search(r"eyJ[A-Za-z0-9_\-=.+/]+", raw)
        data["cf_tunnel_token"] = m.group(0) if m else raw
        restart = data["cf_tunnel_token"] != db.get_setting("cf_tunnel_token", "")
    else:
        restart = False
    for k, v in data.items():
        if k in allowed:
            db.set_setting(k, v)
    if restart:
        tunnel.stop()
        tunnel.start()
    return {"ok": True}


@app.get("/api/dashboard")
def dashboard():
    c = {r["status"]: r["n"] for r in db.q("SELECT status, COUNT(*) n FROM posts GROUP BY status")}
    import time as _t
    expiring = []
    for a in db.q("SELECT id, name, tokens, external_id FROM accounts WHERE platform='linkedin'"):
        exp = linkedin.expiry(a["tokens"])
        if exp and exp < _t.time() + 7 * 86400:
            expiring.append({"name": a["name"], "days": max(0, int((exp - _t.time()) / 86400)),
                             "org": (a["external_id"] or "").startswith("urn:li:organization")})
    return {
        "projects": db.one("SELECT COUNT(*) n FROM projects")["n"],
        "videos": db.one("SELECT COUNT(*) n FROM videos")["n"],
        "ideas": db.one("SELECT COUNT(*) n FROM ideas WHERE status IN ('new','approved')")["n"],
        "accounts": db.one("SELECT COUNT(*) n FROM accounts")["n"],
        "posts": c,
        "upcoming": _posts("p.status IN ('queued','uploading','review')", "p.scheduled_at", 12),
        "recent": _posts("p.status IN ('done','failed')", "p.updated_at DESC", 12),
        "ai": ai.usage_summary(),
        "scheduler": scheduler.state,
        "expiring": expiring,
    }


def _posts(where, order, limit, args=()):
    return db.q(f"""SELECT p.*, a.platform, a.name account_name, v.title, v.original_name, v.lang, v.project_id,
                   pr.name project_name, pr.color FROM posts p JOIN accounts a ON a.id=p.account_id
                   JOIN videos v ON v.id=p.video_id LEFT JOIN projects pr ON pr.id=v.project_id
                   WHERE {where} ORDER BY {order} LIMIT {int(limit)}""", args)


@app.get("/api/file")
def get_file(path: str):
    p = Path(path).resolve()
    if not p.exists():  # video už je na YouTube a z Macu zmazané: ukáž malý náhľad, ak ešte je
        v = db.one("SELECT COALESCE(preview_path,'') pv FROM videos WHERE file_path=?", (path,))
        if v and v["pv"]:
            p = Path(v["pv"]).resolve()
    allowed = [db.DATA_DIR.resolve()] + [Path(x).resolve() for x in db.get_setting("import_dirs", [])]
    if not any(str(p).startswith(str(a)) for a in allowed) or not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


@app.post("/api/videos/{vid}/save-copy")
def video_save_copy(vid: int, data: dict = Body(default={})):
    """Uloží kópiu videa do priečinka Stiahnuté (Downloads), aby sa dalo ľahko poslať alebo skontrolovať."""
    import re
    v = db.one("SELECT file_path, title FROM videos WHERE id=?", (vid,))
    if not v or not Path(v["file_path"]).exists():
        raise HTTPException(404)
    name = re.sub(r"[^\w.-]+", "-", str(data.get("name") or v["title"] or f"video-{vid}")).strip("-")[:80] or f"video-{vid}"
    if not name.lower().endswith(".mp4"):
        name += ".mp4"
    dest = Path.home() / "Downloads" / name
    shutil.copy2(v["file_path"], dest)
    return {"ok": True, "path": str(dest)}


# ---------------- Projekty ----------------
PROJECT_FIELDS = ["name", "description", "audience", "tone", "goals", "source_lang", "color", "voice_gender", "voice_rate", "glossary", "banned", "brand_tags"]


@app.get("/api/projects")
def projects():
    rows = db.q("""SELECT p.*, (SELECT COUNT(*) FROM videos v WHERE v.project_id=p.id) videos,
                   (SELECT COUNT(*) FROM ideas i WHERE i.project_id=p.id AND i.status NOT IN ('rejected','inbox','snoozed')) ideas,
                   (SELECT COUNT(*) FROM ideas i WHERE i.project_id=p.id AND i.status='inbox') inbox,
                   (SELECT COUNT(*) FROM posts po JOIN videos v ON v.id=po.video_id WHERE v.project_id=p.id AND po.status='review') review,
                   (SELECT COUNT(*) FROM posts po JOIN videos v ON v.id=po.video_id WHERE v.project_id=p.id AND po.status='failed') failed
                   FROM projects p ORDER BY p.id""")
    for r in rows:
        r["languages"] = json.loads(r["languages"] or "[]")
        r["strategy"] = json.loads(r["strategy"]) if r["strategy"] else None
        r["design_colors"] = json.loads(r.get("design_colors") or "[]")
        r["platforms"] = json.loads(r.get("platforms") or "[]")
        r["voices"] = json.loads(r.get("voices") or "{}")
        r["sources"] = [{"kind": x["kind"], "name": x["name"], "url": x.get("url", ""), "chars": len(x["text"])}
                        for x in json.loads(r.get("sources") or "[]")]
    return rows


@app.post("/api/projects")
def create_project(data: dict = Body(...)):
    if not data.get("name"):
        raise HTTPException(400, "Zadaj názov")
    pid = db.run("INSERT INTO projects(name) VALUES(?)", (data["name"],))
    return update_project(pid, data)


@app.put("/api/projects/{pid}")
def update_project(pid: int, data: dict = Body(...)):
    for f in PROJECT_FIELDS:
        if f in data:
            db.run(f"UPDATE projects SET {f}=? WHERE id=?", (data[f], pid))
    if "languages" in data:
        db.run("UPDATE projects SET languages=? WHERE id=?", (json.dumps(data["languages"]), pid))
    if isinstance(data.get("voices"), dict):
        db.run("UPDATE projects SET voices=? WHERE id=?", (json.dumps(data["voices"]), pid))
    if "platforms" in data:
        db.run("UPDATE projects SET platforms=? WHERE id=?", (json.dumps(data["platforms"]), pid))
    if "strategy" in data and isinstance(data["strategy"], dict):
        db.run("UPDATE projects SET strategy=?, strategy_short=? WHERE id=?",
               (json.dumps(data["strategy"], ensure_ascii=False), data["strategy"].get("summary", "")[:600], pid))
    return {"id": pid}


@app.delete("/api/projects/{pid}")
def delete_project(pid: int):
    for t in ("ideas", "scripts", "videos"):
        db.run(f"DELETE FROM {t} WHERE project_id=?", (pid,))
    db.run("DELETE FROM projects WHERE id=?", (pid,))
    return {"ok": True}


@app.post("/api/projects/{pid}/design")
async def project_design(pid: int, request: Request):
    """Vloženie MD dizajnu (súbory alebo text). Appka si z neho raz urobí krátky brand guide (šetrí tokeny)."""
    import re
    ct = request.headers.get("content-type", "")
    md_parts = []
    mode = "append"
    if ct.startswith("multipart"):
        form = await request.form()
        mode = form.get("mode", "append")
        for f in form.getlist("files"):
            md_parts.append(f"# {f.filename}\n" + (await f.read()).decode("utf-8", "ignore"))
        if form.get("text"):
            md_parts.append(str(form.get("text")))
    else:
        data = await request.json()
        mode = data.get("mode", "append")
        if data.get("text"):
            md_parts.append(data["text"])
    p = db.one("SELECT design_md FROM projects WHERE id=?", (pid,))
    md = "\n\n".join(md_parts)
    if mode == "append" and p and p["design_md"]:
        md = p["design_md"] + "\n\n" + md
    colors = list(dict.fromkeys(c.upper() for c in re.findall(r"#[0-9a-fA-F]{6}\b", md)))[:5]
    if not colors:  # dizajn bez farieb: nechať farby z loga
        logo = brand.main_asset(pid, "logo")
        colors = brand.logo_colors(logo["path"]) if logo else []
    db.run("UPDATE projects SET design_md=?, design_colors=?, design_summary='' WHERE id=?",
           (md, json.dumps(colors), pid))
    if not md.strip():
        return {"ok": True}
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(content.run_task, "design", {"project_id": pid})


def _html_text(html):
    import re
    import html as h
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    html = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header|form)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<(br|p|div|li|h[1-6]|tr)[^>]*>", "\n", html)
    txt = h.unescape(re.sub(r"<[^>]+>", " ", html))
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    txt = "\n".join(l.strip() for l in txt.splitlines() if len(l.strip()) > 2)
    return (h.unescape(title.group(1)).strip() if title else ""), txt


def _fetch_url(url):
    import httpx
    if not url.startswith("http"):
        url = "https://" + url
    r = httpx.get(url, follow_redirects=True, timeout=30, headers={"User-Agent": "Mozilla/5.0 (Macintosh) SocialManager"})
    r.raise_for_status()
    if "pdf" in r.headers.get("content-type", ""):
        return url, _pdf_text(r.content)
    title, txt = _html_text(r.text)
    return (title or url), txt


def _pdf_text(data):
    try:
        import io
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(data)).pages[:40])
    except Exception:
        return ""


@app.post("/api/projects/{pid}/sources")
async def project_sources(pid: int, request: Request):
    """Zdroje projektu: odkazy na weby, vložený text, súbory (txt, md, pdf, csv). AI z nich raz urobí výťah faktov."""
    p = db.one("SELECT sources FROM projects WHERE id=?", (pid,))
    if not p:
        raise HTTPException(404)
    items = json.loads(p["sources"] or "[]")
    from starlette.concurrency import run_in_threadpool
    errors = []
    ct = request.headers.get("content-type", "")
    if ct.startswith("multipart"):
        form = await request.form()
        for f in form.getlist("files"):
            raw = await f.read()
            txt = _pdf_text(raw) if f.filename.lower().endswith(".pdf") else raw.decode("utf-8", "ignore")
            if txt.strip():
                items.append({"kind": "file", "name": f.filename, "text": txt[:60000]})
            else:
                errors.append(f"{f.filename}: nenašiel som v ňom text")
    else:
        data = await request.json()
        if data.get("remove") is not None:
            idx = int(data["remove"])
            if 0 <= idx < len(items):
                items.pop(idx)
        for u in [x.strip() for x in (data.get("urls") or "").split() if x.strip()]:
            try:
                name, txt = await run_in_threadpool(_fetch_url, u)
                if len(txt) < 200:
                    errors.append(f"{u}: stránka nemá čitateľný text (skús text skopírovať a vložiť)")
                    continue
                items.append({"kind": "url", "name": name[:120], "url": u, "text": txt[:60000]})
            except Exception as e:
                errors.append(f"{u}: nedá sa otvoriť ({str(e)[:80]})")
        if (data.get("text") or "").strip():
            items.append({"kind": "text", "name": (data.get("title") or data["text"].strip()[:50]), "text": data["text"][:60000]})
    db.run("UPDATE projects SET sources=?, sources_summary='' WHERE id=?", (json.dumps(items, ensure_ascii=False), pid))
    res = {"ok": True, "errors": errors}
    if items:
        await run_in_threadpool(content.run_task, "sources", {"project_id": pid})
    return res


# ---------------- Tabuľa videí (postup) ----------------
STAGES = ["napad", "prototyp", "jazyky", "video", "siete"]


@app.get("/api/projects/{pid}/board")
def board(pid: int):
    rows = db.q("""SELECT i.*,
        (SELECT COUNT(*) FROM scripts s WHERE s.idea_id=i.id) langs,
        (SELECT COUNT(*) FROM scripts s WHERE s.idea_id=i.id AND s.voice_path!='') voices,
        (SELECT COUNT(*) FROM videos v JOIN scripts s ON s.id=v.script_id WHERE s.idea_id=i.id) videos,
        (SELECT COUNT(*) FROM posts p JOIN videos v ON v.id=p.video_id JOIN scripts s ON s.id=v.script_id
           WHERE s.idea_id=i.id AND p.status='done') posted,
        (SELECT COUNT(*) FROM posts p JOIN videos v ON v.id=p.video_id JOIN scripts s ON s.id=v.script_id
           WHERE s.idea_id=i.id AND p.status IN ('queued','uploading','review')) queued,
        (SELECT COUNT(*) FROM posts p JOIN videos v ON v.id=p.video_id JOIN scripts s ON s.id=v.script_id
           WHERE s.idea_id=i.id AND p.status='failed') failed
        FROM ideas i WHERE i.project_id=? AND i.status NOT IN ('rejected','inbox','snoozed') ORDER BY i.id DESC""", (pid,))
    for r in rows:
        if r["posted"] or r["queued"] or r["failed"]:
            r["stage"] = "siete"
        elif r["videos"]:
            r["stage"] = "video"
        elif r["langs"] > 1 or r["voices"]:
            r["stage"] = "jazyky"
        elif r["langs"]:
            r["stage"] = "prototyp"
        else:
            r["stage"] = "napad"
    return rows


@app.post("/api/ideas")
def idea_create(data: dict = Body(...)):
    """Vlastný nápad (napíšeš sám, AI ho potom rozpracuje)."""
    iid = db.run("INSERT INTO ideas(project_id,title,hook,angle,format,status,score) VALUES(?,?,?,?,?,?,?)",
                 (data["project_id"], data["title"], data.get("hook", ""), data.get("angle", ""),
                  data.get("format", "short"), "approved", 0))
    return {"id": iid}


@app.get("/api/ideas/{iid}/full")
def idea_full(iid: int):
    idea = db.one("SELECT * FROM ideas WHERE id=?", (iid,))
    if not idea:
        raise HTTPException(404)
    scripts = db.q("SELECT * FROM scripts WHERE idea_id=? ORDER BY is_source DESC, lang", (iid,))
    for s in scripts:
        s["scenes"] = json.loads(s["scenes"] or "[]")
        s["videos"] = db.q("SELECT id,file_path,title,duration,created_at FROM videos WHERE script_id=? ORDER BY id DESC", (s["id"],))
        vids = [v["id"] for v in s["videos"]]
        s["posts"] = db.q(f"""SELECT p.id,p.status,p.url,p.error,p.scheduled_at,a.platform,a.name account_name
                             FROM posts p JOIN accounts a ON a.id=p.account_id
                             WHERE p.video_id IN ({','.join('?' * len(vids)) or 'NULL'})""", vids) if vids else []
    return {"idea": idea, "scripts": scripts}


@app.post("/api/ideas/{iid}/publish")
def idea_publish(iid: int, data: dict = Body(...)):
    """Naplánuje najnovšie video každého vybraného jazyka na vybrané siete."""
    langs = set(data.get("langs") or [])
    vids = []
    for s in db.q("SELECT id, lang FROM scripts WHERE idea_id=?", (iid,)):
        if langs and s["lang"] not in langs:
            continue
        v = db.one("SELECT id FROM videos WHERE script_id=? ORDER BY id DESC LIMIT 1", (s["id"],))
        if v:
            vids.append(v["id"])
    if not vids:
        raise HTTPException(400, "Najprv vytvor videá (krok Video).")
    data = dict(data, video_ids=vids)
    return schedule(data)


# ---------------- AI ----------------
@app.post("/api/ai/{task}")
def ai_task(task: str, params: dict = Body(...)):
    if task not in content.TASKS:
        raise HTTPException(404)
    return content.run_task(task, params)


@app.post("/api/ai-manual")
def ai_manual(data: dict = Body(...)):
    return content.apply_manual(data["task"], data["params"], data["text"])


@app.get("/api/ai-usage")
def ai_usage():
    return ai.usage_summary()


# ---------------- Nápady a scenáre ----------------
@app.get("/api/ideas")
def ideas(project_id: int, status: str = ""):
    sql = """SELECT i.*, (SELECT COUNT(*) FROM scripts s WHERE s.idea_id=i.id) langs FROM ideas i WHERE project_id=?"""
    args = [project_id]
    if status:
        sql += " AND status=?"
        args.append(status)
    return db.q(sql + " ORDER BY CASE status WHEN 'approved' THEN 0 WHEN 'new' THEN 1 WHEN 'scripted' THEN 2 ELSE 3 END, score DESC, id DESC", args)


@app.patch("/api/ideas/{iid}")
def idea_update(iid: int, data: dict = Body(...)):
    for f in ("status", "title", "hook", "angle", "first_lang", "pillar", "format", "why", "score"):
        if f in data:
            db.run(f"UPDATE ideas SET {f}=? WHERE id=?", (data[f], iid))
    return {"ok": True}


@app.delete("/api/ideas/{iid}")
def idea_delete(iid: int):
    db.run("DELETE FROM scripts WHERE idea_id=?", (iid,))
    db.run("DELETE FROM ideas WHERE id=?", (iid,))
    return {"ok": True}


@app.post("/api/ideas/scripts")
def make_scripts(data: dict = Body(...)):
    """Scenáre pre viac nápadov - po 4 v jednom volaní (šetrí tokeny)."""
    ids = data["idea_ids"]
    total = 0
    for i in range(0, len(ids), 4):
        total += content.run_task("scripts", {"idea_ids": ids[i:i + 4]})["created"]
    return {"created": total}


@app.get("/api/scripts")
def scripts(idea_id: int):
    rows = db.q("SELECT * FROM scripts WHERE idea_id=? ORDER BY is_source DESC, lang", (idea_id,))
    for r in rows:
        r["scenes"] = json.loads(r["scenes"] or "[]")
    return rows


@app.put("/api/scripts/{sid}")
def script_update(sid: int, data: dict = Body(...)):
    old = db.one("SELECT voiceover FROM scripts WHERE id=?", (sid,)) or {}
    if "voiceover" in data and (data["voiceover"] or "").strip() != (old.get("voiceover") or "").strip():
        db.run("UPDATE scripts SET voice_path='' WHERE id=?", (sid,))  # zmenený text -> hlas sa urobí znova
    for f in ("title", "voiceover", "description", "hashtags", "caption"):
        if f in data:
            db.run(f"UPDATE scripts SET {f}=? WHERE id=?", (data[f], sid))
    return {"ok": True}


@app.post("/api/scripts/{sid}/translate")
def script_translate(sid: int, data: dict = Body(...)):
    langs = [l for l in data.get("langs", []) if l in languages.LANGUAGES]
    if not langs:
        raise HTTPException(400, "Vyber jazyky")
    from . import translate
    if (db.get_setting("ai_mode", "auto") == "manual" or not ai.find_claude()) and not translate.any_enabled():
        return content.run_task("translate", {"script_id": sid, "langs": langs})
    return content.translate_all(sid, langs)


@app.post("/api/scripts/{sid}/voice")
def script_voice(sid: int, data: dict = Body(default={})):
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    p = db.one("SELECT * FROM projects WHERE id=?", (s["project_id"],)) or {}
    path, engine, note = voices.synth(s["voiceover"], s["lang"], data.get("voice") or voices.project_voice(p, s["lang"]),
                                      data.get("gender") or p.get("voice_gender", "F"),
                                      float(data.get("rate") or voices.project_rate(p)), fresh=bool(data.get("fresh")))
    db.run("UPDATE scripts SET voice_path=?, voice_engine=? WHERE id=?", (path, engine, sid))
    return {"voice_path": path, "engine": engine, "note": note}


def _verbal_prefetch(iid):
    """Čísla nahlas pre všetky jazyky nápadu jednou požiadavkou na AI (len vety s číslom, čo ešte nie sú v pamäti)."""
    try:
        from . import verbal
        items = [(r["lang"], sent) for r in db.q("SELECT lang, voiceover FROM scripts WHERE idea_id=?", (iid,))
                 for sent in voices.split_sentences(r["voiceover"])]
        return verbal.ensure(items)
    except Exception as e:
        print("čísla nahlas:", e)
        return 0


@app.post("/api/ideas/{iid}/voice-all")
def idea_voice_all(iid: int, only_missing: int = 0):
    done, errors, notes = 0, [], set()
    _verbal_prefetch(iid)
    for s in db.q("SELECT id, lang FROM scripts WHERE idea_id=?" + (" AND voice_path=''" if only_missing else ""), (iid,)):
        try:
            r = script_voice(s["id"], {})
            done += 1
            if r["note"]:
                notes.add(r["note"][:160])
        except Exception as e:
            errors.append(f"{s['lang']}: {e}")
    return {"done": done, "errors": errors, "notes": sorted(notes)}


@app.get("/api/voices/{lang}")
def voice_list(lang: str):
    return {"voices": voices.catalog(lang), "google": voices.google_usage(), "sample": voices.sample(lang)}


@app.post("/api/voices/preview")
def voice_preview(data: dict = Body(...)):
    lang = data.get("lang", "sk")
    text = data.get("text") or voices.sample(lang)
    path, engine, note = voices.synth(text, lang, data.get("voice") or "auto",
                                      data.get("gender", "F"), float(data.get("rate") or 1.0))
    return {"voice_path": path, "engine": engine, "note": note, "spoken": voices.spoken_form(text, lang)[0]}


@app.get("/api/pronounce")
def pronounce_get():
    return {"custom": pronounce.custom(), "builtin": pronounce.builtin_list(), "demo": pronounce.demo("sk")}


@app.post("/api/pronounce")
def pronounce_save(data: dict = Body(...)):
    return {"custom": pronounce.save_custom(data.get("items") or [])}


@app.post("/api/voice/test")
def voice_test(data: dict = Body(...)):
    path = media.tts(data.get("text", "Ahoj"), data.get("lang", "sk"), data.get("gender", "F"))
    return {"voice_path": path}


def _shots_for(s):
    """Zábery sa vyberú raz pre originál a použijú vo všetkých jazykoch."""
    src = db.one("SELECT * FROM scripts WHERE idea_id=? AND is_source=1", (s["idea_id"],)) or s
    if src.get("shots"):
        return json.loads(src["shots"])
    scenes = json.loads(src["scenes"] or "[]")
    if any(not sc.get("q") for sc in scenes):
        try:
            scenes = content.scene_queries(scenes, src["title"])
            db.run("UPDATE scripts SET scenes=? WHERE id=?", (json.dumps(scenes, ensure_ascii=False), src["id"]))
        except Exception:
            for sc in scenes:
                sc.setdefault("q", src["title"])
    shots = footage.pick_for_scenes(scenes, pid=src["project_id"])
    db.run("UPDATE scripts SET shots=? WHERE id=?", (json.dumps(shots), src["id"]))
    return shots


def _scene_cuts(s, scenes, style):
    """Časy striedania scén (pre zvuk prechodu) – rovnaké, ako použil obraz."""
    try:
        total = media.duration(s["voice_path"]) or 0
        if style == "explainer":
            sc = json.loads(db.one("SELECT scenes FROM scripts WHERE id=?", (s["id"],))["scenes"] or "[]")
            return [t0 for t0, _ in explainer.timeline(sc, media.word_times(s["voice_path"], s["voiceover"]), total)][1:]
        if style == "broll" and scenes:
            return [total / len(scenes) * i for i in range(1, len(scenes))]
    except Exception:
        pass
    return []


def _thumb_opts(s):
    """Text a scéna náhľadového obrázka dlhého videa zo scenára (pole thumb)."""
    try:
        t = json.loads(s["thumb"] or "{}") if "thumb" in s.keys() else {}
    except Exception:
        t = {}
    return {"thumb_text": str(t.get("text") or ""), "thumb_scene": t.get("scene")}


def _broll_ready():
    st = footage.status()
    return st["pexels"] or st["pixabay"] or st["own"] > 0 or st["ai"]


@app.post("/api/scripts/{sid}/to-video")
def script_to_video(sid: int, data: dict = Body(default={})):
    """Vytvorí video: zábery z internetu/tvoje + titulky slovo po slove (predvolené), tvoje podkladové video, alebo farby dizajnu."""
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    if data.get("new_voice"):   # tlačidlo „Nový zvuk“: hlas sa nahrá nanovo a video sa zloží podľa neho
        script_voice(sid, {"fresh": True})
        s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    elif not s["voice_path"] or not Path(s["voice_path"]).exists() or voices.stale(s["voice_path"], s.get("voice_engine") or "", s["voiceover"], s["lang"]):
        script_voice(sid, {})   # aj starý hlas bez presných časov slov sa urobí nanovo (čistejší, titulky sedia)
        s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    want_music = data.get("music", True)
    data = dict(data, music=False)   # hudbu, efekty a hlasitosť rieši až audio.finish na hotovom videu
    out = VIDEO_DIR / f"script{sid}_{s['lang']}_{secrets.token_hex(3)}.mp4"
    base_id = data.get("base_video_id")
    proj = db.one("SELECT color, design_colors FROM projects WHERE id=?", (s["project_id"],)) or {}
    colors = json.loads(proj.get("design_colors") or "[]") or [proj.get("color") or "#FF6B00"]
    acc = brand.accent(colors, proj.get("color"))  # zvýrazňovacia farba značky (nikdy čierna/biela z manuálu)
    scenes = json.loads(s["scenes"] or "[]")
    base = db.one("SELECT * FROM videos WHERE id=?", (base_id,)) if base_id else None
    style = data.get("style") or ("base" if base else "explainer" if anim.available() else
                                  "broll" if _broll_ready() or brand.brand_footage(s["project_id"]) else "color")
    done = logo_in = False
    # font značky (ak má všetky písmená tohto jazyka)
    font_txt = (s["voiceover"] or "") + " " + " ".join(sc.get("onscreen", "") for sc in scenes)
    brand.use_font(s["project_id"], font_txt, letters_only=style == "explainer")
    if style == "explainer":
        try:
            pr = db.one("SELECT name FROM projects WHERE id=?", (s["project_id"],)) or {}
            sc2 = explainer.localized_scenes(s)
            bo, lg = brand.opts(s["project_id"]), brand.video_logo(s["project_id"], dark_bg=True)
            wide = ((db.one("SELECT format FROM ideas WHERE id=?", (s["idea_id"],)) or {}).get("format") == "long")  # dlhé video = na šírku
            explainer.make(sc2, s["voice_path"], out, acc, s["lang"], s["voiceover"], pr.get("name") or "",
                           footage.music_track(sid) if data.get("music", True) else None, brand.current_font(),
                           font_text=brand.current_text_font(),
                           logo=brand.logo_data_uri(lg, 680, 176) if lg and bo["logo_corner"] else None,
                           logo_end=brand.logo_data_uri(lg, 1320, 720) if lg and bo["logo_end"] else None,
                           products=brand.product_images(s["project_id"]), wide=wide,
                           thumb=out.with_suffix(".jpg") if wide else None, **_thumb_opts(s))
            done = logo_in = True
        except Exception as e:
            print("animované video:", e)
            brand.use_font(s["project_id"], font_txt)
            style = "broll" if _broll_ready() or brand.brand_footage(s["project_id"]) else "color"
    if style == "broll" and not done:
        try:
            media.broll_video(scenes, _shots_for(s), s["voice_path"], out, acc, s["lang"], s["voiceover"],
                              footage.music_track(sid) if data.get("music", True) else None)
            done = True
        except Exception as e:
            print("broll:", e)
    if not done:
        try:
            media.scene_video(scenes, s["voice_path"], out, colors, base["file_path"] if base else None)
        except Exception:
            # záloha: jednoduchšia verzia
            if base:
                media.merge_voice(base["file_path"], s["voice_path"], out)
            else:
                media.image_video(s["voice_path"], out)
    brand.clear_font()
    try:
        if not logo_in:  # animované video má logo priamo v obraze
            brand.decorate(s["project_id"], out)  # logo v rohu + záverečná karta s logom
    except Exception as e:
        print("logo vo videu:", e)
    try:  # zvuk: hudba pod hlasom, jemné prechody, hlasitosť ako na sieťach
        if not base:
            audio.finish(out, s["voice_path"], _scene_cuts(s, scenes, style if done else ""), s["idea_id"], want_music)
    except Exception as e:
        print("zvuk videa:", e)
    vid = _add_video(s["project_id"], str(out), out.name, s["lang"], s)
    return {"video_id": vid, "style": style if done or style != "broll" else "color"}


@app.get("/api/ideas/{iid}/shots")
def idea_shots(iid: int):
    src = db.one("SELECT * FROM scripts WHERE idea_id=? AND is_source=1", (iid,))
    if not src:
        return {"scenes": []}
    scenes = json.loads(src["scenes"] or "[]")
    shots = json.loads(src["shots"] or "[]") if src.get("shots") else []
    out = []
    for i, sc in enumerate(scenes):
        fs = [db.one("SELECT id, kind, path, source, license_url FROM footage WHERE id=?", (f,)) for f in (shots[i] if i < len(shots) else [])]
        out.append({"q": sc.get("q", ""), "onscreen": sc.get("onscreen", ""), "shots": [f for f in fs if f]})
    return {"scenes": out, "ready": _broll_ready(), "status": footage.status()}


@app.post("/api/ideas/{iid}/shots")
def idea_shots_change(iid: int, data: dict = Body(default={})):
    """Vyber zábery (ak ešte nie sú) alebo vymeň zábery jednej scény za ďalšie (bez AI)."""
    src = db.one("SELECT * FROM scripts WHERE idea_id=? AND is_source=1", (iid,))
    if not src:
        raise HTTPException(400, "Najprv sprav prototyp")
    if "scene" not in data:
        db.run("UPDATE scripts SET shots='' WHERE id=?", (src["id"],))
        _shots_for(src)
        return idea_shots(iid)
    i = int(data["scene"])
    scenes = json.loads(src["scenes"] or "[]")
    shots = json.loads(src["shots"] or "[]") if src.get("shots") else _shots_for(src)
    if data.get("q"):
        scenes[i]["q"] = data["q"]
        db.run("UPDATE scripts SET scenes=? WHERE id=?", (json.dumps(scenes, ensure_ascii=False), src["id"]))
    used = {f for sh in shots for f in sh}
    new = []
    for _ in range(2):
        r = footage.find(scenes[i].get("q", ""), scenes[i].get("alt", ""), used | set(new), pid=src["project_id"])
        if r:
            new.append(r["id"])
    if not new:
        raise HTTPException(400, "Nenašiel som iné zábery – skús iné slová")
    while len(shots) <= i:
        shots.append([])
    shots[i] = new
    db.run("UPDATE scripts SET shots=? WHERE id=?", (json.dumps(shots), src["id"]))
    return idea_shots(iid)


@app.post("/api/open-folder")
def open_folder(data: dict = Body(...)):
    """Otvorí priečinok Moje zábery / Hudba vo Finderi."""
    import subprocess
    import sys
    d = footage.OWN if data.get("which") == "own" else footage.MUSIC
    cmd = ["open", str(d)] if sys.platform == "darwin" else ["explorer", str(d)] if os.name == "nt" else ["xdg-open", str(d)]
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass
    return {"path": str(d)}


@app.post("/api/scripts/{sid}/attach-video")
async def script_attach(sid: int, file: UploadFile = File(...)):
    """Vlastné hotové video pre daný jazyk (napr. si ho strihaš sám)."""
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    ext = Path(file.filename).suffix.lower()
    if ext not in VIDEO_EXT:
        raise HTTPException(400, "Toto nie je video súbor.")
    dest = VIDEO_DIR / f"script{sid}_{s['lang']}_{secrets.token_hex(3)}{ext}"
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024 * 8):
            out.write(chunk)
    return {"video_id": _add_video(s["project_id"], str(dest), file.filename, s["lang"], s)}


def _first_lang(iid):
    idea = db.one("SELECT first_lang, project_id FROM ideas WHERE id=?", (iid,)) or {}
    p = db.one("SELECT source_lang FROM projects WHERE id=?", (idea.get("project_id"),)) or {}
    return idea.get("first_lang") or p.get("source_lang") or "sk"


def _vopts(data):
    return {k: data[k] for k in ("style", "base_video_id", "music", "new_voice") if k in data}


@app.post("/api/ideas/{iid}/produce-first")
def idea_produce_first(iid: int, data: dict = Body(default={})):
    """Prvá verzia: hlas + video len v jednom jazyku (predvolene jazyk scenára). Ostatné jazyky až po schválení."""
    src = db.one("SELECT * FROM scripts WHERE idea_id=? AND is_source=1", (iid,))
    if not src:
        raise HTTPException(400, "Najprv schváľ prototyp (scenár)")
    lang = data.get("lang") or _first_lang(iid)
    if lang not in languages.LANGUAGES:
        lang = src["lang"]
    db.run("UPDATE ideas SET first_lang=? WHERE id=?", (lang, iid))
    s = db.one("SELECT id FROM scripts WHERE idea_id=? AND lang=?", (iid, lang))
    out = {"lang": lang}
    if not s:
        out["translate"] = content.translate_all(src["id"], [lang])
        s = db.one("SELECT id FROM scripts WHERE idea_id=? AND lang=?", (iid, lang))
        if not s:
            raise HTTPException(400, "Preklad do tohto jazyka sa nepodaril")
    out.update(script_to_video(s["id"], _vopts(data)))
    return out


@app.post("/api/ideas/{iid}/teasers")
def idea_teasers(iid: int, data: dict = Body(default={})):
    """Shorts z dlhého videa: každý vysvetlí jeden kúsok a otvoreným koncom pozve na celé video. Jedno volanie AI."""
    idea = db.one("SELECT * FROM ideas WHERE id=?", (iid,))
    if not idea or idea["format"] != "long":
        raise HTTPException(400, "Toto ide len z dlhého videa")
    if not db.one("SELECT id FROM scripts WHERE idea_id=? AND is_source=1", (iid,)):
        raise HTTPException(400, "Dlhé video ešte nemá scenár")
    out = content.run_task("teasers", {"idea_id": iid, "count": max(1, min(6, int(data.get("count") or 3)))})
    if data.get("produce"):
        out["videos"] = 0
        for i in out["idea_ids"]:
            try:
                idea_produce_first(i, {})
                out["videos"] += 1
            except Exception as e:
                out.setdefault("errors", []).append(str(e)[:200])
    return out


@app.post("/api/ideas/{iid}/produce-all")
def idea_produce_all(iid: int, data: dict = Body(default={})):
    """Rozšírenie schválenej prvej verzie: preklad do ostatných jazykov -> hlasy -> videá.
    Zábery sú tie isté (vybrané raz), mení sa len text, titulky a hlas. Hotové videá sa nerobia znova."""
    src = db.one("SELECT * FROM scripts WHERE idea_id=? AND is_source=1", (iid,))
    if not src:
        raise HTTPException(400, "Najprv schváľ prototyp (scenár)")
    p = db.one("SELECT languages FROM projects WHERE id=?", (src["project_id"],))
    have = {r["lang"] for r in db.q("SELECT lang FROM scripts WHERE idea_id=?", (iid,))}
    missing = [l for l in json.loads(p["languages"] or "[]") if l not in have]
    out = {}
    if missing:
        out["translate"] = content.translate_all(src["id"], missing)
    out["voices"] = idea_voice_all(iid, only_missing=1)
    out["videos"] = idea_videos_all(iid, {**_vopts(data), "only_missing": 1})
    return out


@app.post("/api/ideas/{iid}/videos-all")
def idea_videos_all(iid: int, data: dict = Body(default={})):
    """Jedným klikom: pre všetky jazyky nápadu urobí hlas + video (s tvojím podkladovým videom, ak ho zvolíš)."""
    made, errors = [], []
    _verbal_prefetch(iid)
    for s in db.q("SELECT id, lang FROM scripts WHERE idea_id=?", (iid,)):
        if data.get("only_missing") and db.one("SELECT id FROM videos WHERE script_id=?", (s["id"],)):
            continue
        try:
            made.append(script_to_video(s["id"], _vopts(data))["video_id"])
        except Exception as e:
            errors.append(f"{s['lang']}: {e}")
    return {"created": len(made), "errors": errors}


# ---------------- Autopilot: celý postup naraz ----------------
AUTO = {"running": False, "step": "", "log": []}


def _autopilot(params):
    import threading
    pid = int(params["project_id"])
    take = int(params.get("take", 3))
    try:
        AUTO.update(running=True, log=[], step="Vymýšľam nápady")
        p = db.one("SELECT * FROM projects WHERE id=?", (pid,))
        if not p["strategy"]:
            AUTO["step"] = "Tvorím stratégiu"
            content.run_task("strategy", {"project_id": pid})
            AUTO["step"] = "Vymýšľam nápady"
        before = {r["id"] for r in db.q("SELECT id FROM ideas WHERE project_id=?", (pid,))}
        content.run_task("ideas", {"project_id": pid, "count": int(params.get("count", 10)),
                                   "format": params.get("format", "short"), "focus": params.get("focus", "")})
        new = [r for r in db.q("SELECT * FROM ideas WHERE project_id=? ORDER BY score DESC", (pid,)) if r["id"] not in before]
        best = [r["id"] for r in new[:take]]
        for i in best:
            db.run("UPDATE ideas SET status='approved' WHERE id=?", (i,))
        AUTO["log"].append(f"{len(new)} nápadov, vybral som {len(best)} najlepších")
        AUTO["step"] = "Píšem scenáre"
        make_scripts({"idea_ids": best})
        opts = {"base_video_id": params["base_video_id"], "style": "base"} if params.get("base_video_id") else {}
        for n, i in enumerate(best, 1):
            if not db.one("SELECT id FROM scripts WHERE idea_id=? AND is_source=1", (i,)):
                continue
            if params.get("all_langs"):
                AUTO["step"] = f"Robím všetky jazyky {n}/{len(best)}"
                r = idea_produce_all(i, opts)["videos"]
                AUTO["log"].append(f"Nápad {n}: {r['created']} videí" + (f", chyby: {'; '.join(r['errors'])}" if r["errors"] else ""))
            elif params.get("videos"):
                AUTO["step"] = f"Robím prvú verziu videa {n}/{len(best)}"
                try:
                    idea_produce_first(i, opts)
                    AUTO["log"].append(f"Nápad {n}: prvá verzia ({languages.name(_first_lang(i))}) hotová")
                except Exception as e:
                    AUTO["log"].append(f"Nápad {n}: chyba {e}")
        if params.get("videos") and not params.get("all_langs"):
            AUTO["log"].append("Pozri si videá a keď sú dobré, daj pri každom „Rozšíriť do všetkých jazykov“.")
        AUTO["step"] = "Hotovo ✅"
    except ai.NeedManual:
        AUTO["step"] = "Autopilot potrebuje Claude Code (v ručnom režime nefunguje)."
    except Exception as e:
        AUTO["step"] = f"Chyba: {e}"
    finally:
        AUTO["running"] = False


# ---------------- Denná výroba: appka si sama drží zásobu hotových videí podľa plánu projektu ----------------
PROD = {"running": False, "step": "", "log": [], "wait_until": 0, "resumed": set()}


def _prod_supply(pid, fmt):
    """Koľko hotových videí daného formátu ešte čaká na zverejnenie (nenaplánované + naplánované do budúcna)."""
    return db.one("""SELECT COUNT(DISTINCT s.idea_id) n FROM videos v JOIN scripts s ON s.id=v.script_id JOIN ideas i ON i.id=s.idea_id
                     WHERE v.project_id=? AND v.status='ready' AND COALESCE(i.format,'short')=?
                     AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.video_id=v.id AND p.status!='failed'
                                     AND (p.status='done' OR p.scheduled_at<=datetime('now','localtime')))""", (pid, fmt))["n"]


def _prod_pick(pid, fmt, n):
    """Najlepšie schválené nápady bez scenára; každý z inej série, kým sa dá."""
    rows = db.q("""SELECT i.id, COALESCE(i.pillar,'') pillar FROM ideas i WHERE i.project_id=? AND i.status='approved'
                   AND COALESCE(i.format,'short')=? AND (i.due_date IS NULL OR i.due_date='')
                   AND NOT EXISTS (SELECT 1 FROM scripts s WHERE s.idea_id=i.id) ORDER BY i.score DESC, i.id""", (pid, fmt))
    last = [r["pillar"] for r in db.q("""SELECT COALESCE(i.pillar,'') pillar FROM videos v JOIN scripts s ON s.id=v.script_id
                   JOIN ideas i ON i.id=s.idea_id WHERE v.project_id=? ORDER BY v.id DESC LIMIT 2""", (pid,))]
    out, used = [], set(x for x in last if x)
    for r in rows:  # najprv z každej série jeden
        if len(out) < n and r["pillar"] not in used:
            out.append(r["id"])
            if r["pillar"]:
                used.add(r["pillar"])
    for r in rows:  # keď inú sériu niet, ďalší najlepší
        if len(out) < n and r["id"] not in out:
            out.append(r["id"])
    return out, len(rows)


def _produce_once():
    import time as _t
    cfg = db.get_setting("auto_produce", {}) or {}
    if not cfg or PROD["running"] or AUTO["running"] or db.get_setting("paused", False) or _t.time() < PROD["wait_until"]:
        return
    if any(not j.get("done") for j in JOBS.values()):
        return  # používateľ práve niečo vyrába
    if not nightly.in_window():
        PROD["step"] = "Čakám na noc"
        return
    PROD["running"] = True
    nightly.keep_awake(True)
    try:
        _prod_resume(cfg)
        for pid_s, c in cfg.items():
            pid, ahead = int(pid_s), max(1, int(c.get("days_ahead") or 2))
            made = 0
            from_long = bool(c.get("from_long")) and int(c.get("long") or 0) > 0
            for fmt in (("long", "short") if from_long else ("short", "long")):
                per = int(c.get(fmt) or 0)
                if not per:
                    continue
                need = min(per, per * ahead - _prod_supply(pid, fmt))
                if need <= 0:
                    continue
                ids, left = _prod_pick(pid, fmt, need)
                if left < per * 3 and not c.get("no_ideas"):  # zásoba nápadov dochádza: doplň ju jedným volaním
                    PROD["step"] = "Dopĺňam nápady"
                    try:
                        before = {r["id"] for r in db.q("SELECT id FROM ideas WHERE project_id=?", (pid,))}
                        content.run_task("ideas", {"project_id": pid, "count": 20 if fmt == "short" else 8, "format": fmt})
                        for r in db.q("SELECT id, score FROM ideas WHERE project_id=?", (pid,)):
                            if r["id"] not in before and (r["score"] or 0) >= 7:
                                db.run("UPDATE ideas SET status='approved' WHERE id=?", (r["id"],))
                        ids, left = _prod_pick(pid, fmt, need)
                    except Exception as e:
                        PROD["log"].append(f"nápady: {e}")
                if ids and fmt == "short":
                    PROD["step"] = "Píšem scenáre krátkych videí"
                    make_scripts({"idea_ids": ids})
                for i in ids:
                    if fmt == "long":
                        PROD["step"] = "Píšem scenár dlhého videa"
                        make_scripts({"idea_ids": [i]})
                    if not db.one("SELECT id FROM scripts WHERE idea_id=? AND is_source=1", (i,)):
                        continue
                    PROD["step"] = f"Robím {'dlhé' if fmt == 'long' else 'krátke'} video"
                    try:
                        idea_produce_first(i, {})
                        made += 1
                        if fmt == "long" and from_long and int(c.get("short") or 0):
                            PROD["step"] = "Robím Shorts z dlhého videa"
                            k = max(1, round(int(c["short"]) / int(c["long"])))
                            made += idea_teasers(i, {"count": k, "produce": True}).get("videos", 0)
                    except Exception as e:
                        PROD["log"].append(f"nápad {i}: {e}")
                        db.run("UPDATE ideas SET status='new' WHERE id=?", (i,))  # nech sa na ňom výroba nezasekne
            if made:
                from . import planner
                r = planner.plan_week([pid])
                PROD["log"].append(f"{dt_now()} projekt {pid}: {made} nových videí, naplánovaných {r['created']}")
        PROD["step"] = ""
    except ai.NeedManual:
        PROD["step"] = "Denná výroba potrebuje Claude Code"
        PROD["wait_until"] = _t.time() + 3600
    except Exception as e:
        PROD["step"] = f"Chyba: {e}"
        PROD["wait_until"] = _t.time() + 1800
    finally:
        PROD["running"] = False
        PROD["log"] = PROD["log"][-30:]
        try:
            nightly.awake_tick()
        except Exception:
            pass


def _prod_resume(cfg):
    """Dokončí, čo prerušil spánok alebo reštart: scenár bez videa, dlhé video bez Shorts."""
    for pid_s, c in cfg.items():
        if not nightly.in_window():
            return
        for r in db.q("""SELECT i.id, COALESCE(i.format,'short') fmt FROM ideas i JOIN scripts s ON s.idea_id=i.id AND s.is_source=1
                         WHERE i.project_id=? AND s.created_at > datetime('now','localtime','-3 days')
                         AND NOT EXISTS (SELECT 1 FROM videos v JOIN scripts s2 ON s2.id=v.script_id WHERE s2.idea_id=i.id)
                         ORDER BY i.id""", (int(pid_s),)):
            if r["id"] in PROD["resumed"]:
                continue  # každé len raz za beh appky, nech sa chyba neopakuje dookola
            PROD["resumed"].add(r["id"])
            PROD["step"] = "Dokončujem prerušené video"
            try:
                idea_produce_first(r["id"], {})
            except Exception as e:
                PROD["log"].append(f"dokončenie {r['id']}: {e}")
                continue
        if bool(c.get("from_long")) and int(c.get("short") or 0) and int(c.get("long") or 0):
            k = max(1, round(int(c["short"]) / int(c["long"])))
            for r in db.q("""SELECT i.id FROM ideas i WHERE i.project_id=? AND i.format='long'
                             AND EXISTS (SELECT 1 FROM videos v JOIN scripts s ON s.id=v.script_id WHERE s.idea_id=i.id
                                         AND v.created_at > datetime('now','localtime','-3 days'))
                             AND NOT EXISTS (SELECT 1 FROM ideas t WHERE t.parent_id=i.id)""", (int(pid_s),)):
                if -r["id"] in PROD["resumed"]:
                    continue
                PROD["resumed"].add(-r["id"])
                PROD["step"] = "Dokončujem Shorts z dlhého videa"
                try:
                    idea_teasers(r["id"], {"count": k, "produce": True})
                except Exception as e:
                    PROD["log"].append(f"Shorts {r['id']}: {e}")


def dt_now():
    import datetime as _d
    return _d.datetime.now().strftime("%d.%m. %H:%M")


def _produce_loop():
    import time as _t
    _t.sleep(90)
    while True:
        try:
            _produce_once()
        except Exception as e:
            print("denná výroba:", e)
        _t.sleep(300)


@app.post("/api/storage/clean")
def storage_clean():
    """Ručné upratanie (inak beží samo každých 30 minút)."""
    nightly.clean()
    return nightly.status()


@app.get("/api/produce")
def produce_status():
    return dict({k: v for k, v in PROD.items() if k != "resumed"}, config=db.get_setting("auto_produce", {}) or {},
                night=nightly.status())


@app.post("/api/autopilot")
def autopilot(params: dict = Body(...)):
    import threading
    if AUTO["running"]:
        raise HTTPException(400, "Autopilot už beží")
    threading.Thread(target=_autopilot, args=(params,), daemon=True).start()
    return {"ok": True}


@app.get("/api/autopilot")
def autopilot_status():
    return AUTO


# ---------------- Videá ----------------
def _add_video(project_id, path, original, lang="", script=None):
    size = os.path.getsize(path)
    dur = media.duration(path)
    if not lang:
        lang = media.guess_lang(original)
    title = desc = tags = cap = ""
    sid = None
    if script:
        title, desc, tags, cap, sid = script["title"], script["description"], script["hashtags"], script["caption"], script["id"]
    else:
        title = Path(original).stem.replace("_", " ").replace("-", " ")[:90]
    return db.run("""INSERT INTO videos(project_id,lang,title,description,hashtags,caption,file_path,original_name,size,duration,script_id)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (project_id, lang, title, desc, tags, cap, path, original, size, dur, sid))


@app.post("/api/videos/upload")
async def videos_upload(project_id: int = Form(...), lang: str = Form(""), files: list[UploadFile] = File(...)):
    ids = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in VIDEO_EXT:
            continue
        dest = VIDEO_DIR / f"{datetime.now():%Y%m%d%H%M%S}_{secrets.token_hex(3)}{ext}"
        with open(dest, "wb") as out:
            while chunk := await f.read(1024 * 1024 * 8):
                out.write(chunk)
        ids.append(_add_video(project_id, str(dest), f.filename, lang))
    return {"created": len(ids)}


@app.post("/api/videos/import-folder")
def videos_import(data: dict = Body(...)):
    """Pridá všetky videá z priečinka (bez kopírovania - šetrí miesto). Jazyk uhádne z názvu, napr. video_de.mp4."""
    folder = Path(data["path"].strip().strip('"')).expanduser()
    if not folder.is_dir():
        raise HTTPException(400, "Priečinok neexistuje")
    dirs = set(db.get_setting("import_dirs", []))
    dirs.add(str(folder.resolve()))
    db.set_setting("import_dirs", sorted(dirs))
    existing = {r["file_path"] for r in db.q("SELECT file_path FROM videos")}
    n = 0
    for f in sorted(folder.rglob("*") if data.get("recursive", True) else folder.iterdir()):
        if f.suffix.lower() in VIDEO_EXT and str(f.resolve()) not in existing:
            # podpriečinok s názvom jazyka (napr. /de/) má prednosť
            lang = data.get("lang") or (f.parent.name.lower() if f.parent.name.lower() in languages.LANGUAGES else "")
            _add_video(int(data["project_id"]), str(f.resolve()), f.name, lang)
            n += 1
    return {"created": n}


@app.get("/api/videos")
def videos(project_id: int = 0, lang: str = "", status: str = ""):
    sql = """SELECT v.*, (SELECT GROUP_CONCAT(a.platform || ':' || p.status) FROM posts p JOIN accounts a ON a.id=p.account_id
             WHERE p.video_id=v.id) posts FROM videos v WHERE 1=1"""
    args = []
    if project_id:
        sql += " AND v.project_id=?"
        args.append(project_id)
    if lang:
        sql += " AND v.lang=?"
        args.append(lang)
    rows = db.q(sql + " ORDER BY v.id DESC", args)
    if status == "unposted":
        rows = [r for r in rows if not r["posts"]]
    return rows


# ---------- Popisky a hashtagy pre siete (bez AI) ----------
def _caption_preview(video):
    from . import captions
    out = {}
    for pl in captions.RULES:
        acc = db.one("SELECT * FROM accounts WHERE project_id=? AND platform=? AND lang=? AND country!='' ORDER BY id LIMIT 1",
                     (video.get("project_id"), pl, video.get("lang") or ""))
        b = captions.build(video, pl, acc)
        out[pl] = {"title": b["title"], "text": b["text"], "len": len(b["text"]), "visible": captions.RULES[pl]["hook"],
                   "country": (acc or {}).get("country") or ""}
    return out


@app.get("/api/videos/{vid}/captions")
def video_captions(vid: int):
    v = db.one("SELECT * FROM videos WHERE id=?", (vid,))
    if not v:
        raise HTTPException(404, "Video neexistuje")
    return _caption_preview(v)


@app.get("/api/scripts/{sid}/captions")
def script_captions(sid: int):
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    if not s:
        raise HTTPException(404, "Scenár neexistuje")
    v = {k: s[k] for k in ("project_id", "lang", "title", "description", "hashtags", "caption")}
    v.update({"id": s["idea_id"] or 0, "script_id": sid})
    return _caption_preview(v)


@app.get("/api/projects/{pid}/hashtags")
def project_hashtags(pid: int):
    from . import captions
    p = db.one("SELECT * FROM projects WHERE id=?", (pid,)) or {}
    return {"bank": captions.bank(pid), "brand": captions.brand_tags(p) if p else []}


@app.post("/api/projects/{pid}/hashtags")
def project_hashtags_build(pid: int):
    from . import captions
    r = captions.build_bank(pid, force=True)
    return {**r, "bank": captions.bank(pid)}


@app.put("/api/videos/{vid}")
def video_update(vid: int, data: dict = Body(...)):
    for f in ("title", "description", "hashtags", "caption", "lang", "project_id"):
        if f in data:
            db.run(f"UPDATE videos SET {f}=? WHERE id=?", (data[f], vid))
    return {"ok": True}


@app.post("/api/videos/bulk")
def videos_bulk(data: dict = Body(...)):
    ids = data.get("ids", [])
    if data.get("action") == "delete":
        for i in ids:
            v = db.one("SELECT file_path FROM videos WHERE id=?", (i,))
            if v and str(Path(v["file_path"]).resolve()).startswith(str(VIDEO_DIR.resolve())):
                Path(v["file_path"]).unlink(missing_ok=True)
            db.run("DELETE FROM posts WHERE video_id=? AND status!='done'", (i,))
            db.run("DELETE FROM videos WHERE id=?", (i,))
    elif data.get("action") == "set":
        for i in ids:
            video_update(i, data.get("fields", {}))
    elif data.get("action") == "ai-meta":
        n = 0
        for i in ids:
            content.run_task("meta", {"video_id": i, "about": data.get("about", "")})
            n += 1
        return {"done": n}
    return {"ok": True}


# ---------------- Účty ----------------
@app.get("/api/accounts")
def accounts():
    import time as _t
    rows = db.q("SELECT a.id, a.platform, a.name, a.external_id, a.project_id, a.lang, a.country, a.tokens, p.name project_name "
                "FROM accounts a LEFT JOIN projects p ON p.id=a.project_id ORDER BY a.platform, a.name")
    for r in rows:
        exp = linkedin.expiry(r.pop("tokens")) if r["platform"] == "linkedin" else 0
        r["days_left"] = max(0, int((exp - _t.time()) / 86400)) if exp else None
        r["org"] = (r["external_id"] or "").startswith("urn:li:organization")
    return rows


@app.post("/api/connect-project")
def connect_project(data: dict = Body(...)):
    """Projekt, do ktorého pôjdu novo pripojené účty (stránka Účty a siete v projekte)."""
    pid = int(data.get("project_id") or 0)
    if pid and db.one("SELECT id FROM projects WHERE id=?", (pid,)):
        db.set_setting("connect_project", pid)
    return {"ok": True}


@app.put("/api/accounts/{aid}")
def account_update(aid: int, data: dict = Body(...)):
    if data.get("name"):
        db.run("UPDATE accounts SET name=? WHERE id=?", (data["name"], aid))
    if "project_id" in data:
        if data.get("project_id"):  # účet vždy patrí pod konkrétny projekt
            db.run("UPDATE accounts SET project_id=? WHERE id=?", (data["project_id"], aid))
    if "country" in data:
        c = (data.get("country") or "").upper()
        db.run("UPDATE accounts SET country=? WHERE id=?", (c, aid))
        cl = languages.COUNTRY_LANGS.get(c, [])
        cur = (db.one("SELECT lang FROM accounts WHERE id=?", (aid,)) or {}).get("lang", "")
        if cl and "lang" not in data and cur not in cl:  # krajina určí jazyk videí
            db.run("UPDATE accounts SET lang=? WHERE id=?", (cl[0], aid))
    if "lang" in data:
        db.run("UPDATE accounts SET lang=? WHERE id=?", (data.get("lang") or "", aid))
    return {"ok": True}


@app.delete("/api/accounts/{aid}")
def account_delete(aid: int):
    db.run("DELETE FROM posts WHERE account_id=? AND status!='done'", (aid,))
    db.run("DELETE FROM accounts WHERE id=?", (aid,))
    return {"ok": True}


@app.post("/api/accounts/youtube/client")
async def yt_client(file: UploadFile = File(...)):
    try:
        data = json.loads((await file.read()).decode("utf-8"))
    except Exception:
        raise HTTPException(400, "Toto nie je JSON súbor z Google Cloud.")
    c = data.get("installed") or data.get("web")
    if not c or not c.get("client_id"):
        raise HTTPException(400, "V súbore chýba client_id - stiahni JSON OAuth klienta (typ Desktop app).")
    n = youtube.add_client(data)
    return {"ok": True, "projects": n}


@app.get("/api/accounts/youtube/connect")
def yt_connect(project_id: int = 0, lang: str = ""):
    st = "yt:" + secrets.token_urlsafe(12)
    idx = youtube.pick_client()
    _oauth_states[st] = {"project_id": project_id or None, "lang": lang, "client": idx}
    return RedirectResponse(youtube.auth_url(st, idx))


@app.post("/api/accounts/meta")
def meta_connect(data: dict = Body(...)):
    tok = (data.get("token") or "").strip()
    pid = data.get("project_id") or None
    if not tok:  # bez tokenu: použi uložený token a načítaj nové stránky a Instagramy
        for a in db.q("SELECT project_id, tokens FROM accounts WHERE platform='facebook' ORDER BY id"):
            tok = json.loads(a["tokens"] or "{}").get("user_token", "")
            if tok:
                pid = pid or a["project_id"]
                break
        if not tok:
            raise HTTPException(400, "Zatiaľ nie je uložený žiadny Meta token. Vlož ho do políčka.")
    ids = meta.connect(tok, pid, data.get("lang", ""))
    return {"created": len(ids)}


@app.post("/api/accounts/tiktok/creds")
def tt_creds(data: dict = Body(...)):
    db.set_setting("tt_client_key", data["client_key"].strip())
    db.set_setting("tt_client_secret", data["client_secret"].strip())
    if data.get("mode"):
        db.set_setting("tt_mode", data["mode"])
    return {"ok": True}


@app.post("/api/accounts/linkedin/creds")
def li_creds(data: dict = Body(...)):
    pre = "li_org_" if data.get("org") else "li_"
    db.set_setting(pre + "client_id", data["client_id"].strip())
    db.set_setting(pre + "client_secret", data["client_secret"].strip())
    return {"ok": True}


@app.get("/api/accounts/linkedin/connect")
def li_connect(project_id: int = 0, lang: str = "", org: int = 0):
    st = "li:" + secrets.token_urlsafe(12)
    _oauth_states[st] = {"project_id": project_id or None, "lang": lang, "org": bool(org)}
    return RedirectResponse(linkedin.auth_url(st, bool(org)))


@app.post("/api/accounts/ttb/creds")
def ttb_creds(data: dict = Body(...)):
    db.set_setting("ttb_app_id", data["app_id"].strip())
    db.set_setting("ttb_secret", data["secret"].strip())
    return {"ok": True}


@app.get("/api/accounts/ttb/connect")
def ttb_connect(project_id: int = 0, lang: str = ""):
    st = "ttb:" + secrets.token_urlsafe(12)
    _oauth_states[st] = {"project_id": project_id or None, "lang": lang}
    return RedirectResponse(tiktok_business.auth_url(st))


@app.post("/api/accounts/ttb/paste")
def ttb_paste(data: dict = Body(...)):
    """Ak presmerovanie nefunguje: vložíš adresu, na ktorej si skončil, a appka si z nej vezme kód."""
    import urllib.parse as up
    q = up.parse_qs(up.urlparse(data["url"].strip()).query)
    code = (q.get("auth_code") or q.get("code") or [""])[0]
    if not code:
        raise HTTPException(400, "V adrese nie je auth_code.")
    st = (q.get("state") or [""])[0]
    info = _oauth_states.pop(st, {})
    ids = tiktok_business.callback(code, info.get("project_id") or data.get("project_id"), info.get("lang", ""))
    return {"created": len(ids)}


@app.get("/api/accounts/tiktok/connect")
def tt_connect(project_id: int = 0, lang: str = ""):
    st = "tt:" + secrets.token_urlsafe(12)
    _oauth_states[st] = {"project_id": project_id or None, "lang": lang}
    return RedirectResponse(tiktok.auth_url(st))


# ---------------- Publikovanie ----------------
def _slots(start, times, per_day, days_skip=None):
    """Generuje časy publikovania: od 'start', v zadaných hodinách, max per_day za deň."""
    times = sorted(times)[:per_day] or ["18:00"]
    day = start.date()
    while True:
        for t in times:
            h, m = map(int, t.split(":"))
            dt = datetime.combine(day, datetime.min.time()).replace(hour=h, minute=m)
            if dt >= start:
                yield dt
        day += timedelta(days=1)


def _lang_ok(a, v):
    if a["platform"] == "linkedin" and linkedin.is_org(a) and not a["lang"]:
        # jedna firemná stránka pre všetky krajiny: idú len vybrané jazyky, nech sa stránka nezahltí
        return not v["lang"] or v["lang"] in linkedin.page_langs()
    return not a["lang"] or not v["lang"] or a["lang"] == v["lang"]


@app.post("/api/posts/schedule")
def schedule(data: dict = Body(...)):
    """Naplánuje veľa videí naraz. Každé video ide na účty svojho projektu a jazyka (alebo na vybrané účty)."""
    video_ids = data.get("video_ids", [])
    platforms = set(data.get("platforms") or ["youtube", "facebook", "instagram", "tiktok", "linkedin"])
    account_ids = data.get("account_ids") or []
    start = datetime.fromisoformat(data["start"]) if data.get("start") else datetime.now() + timedelta(minutes=1)
    times = data.get("times") or ["09:00", "13:00", "18:00"]
    per_day = int(data.get("per_day") or len(times))
    privacy = data.get("privacy", "public")
    immediately = data.get("now", False)
    status = "review" if db.get_setting("require_approval", True) and not data.get("approved") else "queued"
    all_acc = db.q("SELECT * FROM accounts")
    per_account = {}
    skipped = []
    for vid in video_ids:
        v = db.one("SELECT * FROM videos WHERE id=?", (vid,))
        if not v:
            continue
        if account_ids:
            targets = [a for a in all_acc if a["id"] in account_ids]
        else:
            targets = [a for a in all_acc if a["platform"] in platforms
                       and (not a["project_id"] or a["project_id"] == v["project_id"])
                       and _lang_ok(a, v)]
        if not targets:
            skipped.append(v["title"] or v["original_name"])
        for a in targets:
            per_account.setdefault(a["id"], []).append(vid)
    # pokračuj za posledným naplánovaným postom daného účtu, nech sa nenahromadia
    created = 0
    for aid, vids in per_account.items():
        last = db.one("SELECT MAX(scheduled_at) m FROM posts WHERE account_id=? AND status IN ('queued','review')", (aid,))["m"]
        st = start
        if last and not immediately and not data.get("start"):
            st = max(start, datetime.fromisoformat(last) + timedelta(minutes=1))
        gen = _slots(st, times, per_day)
        for vid in vids:
            jit = int(db.get_setting("jitter_min", 10) or 0)
            when = datetime.now() if immediately else next(gen) + timedelta(minutes=random.randint(0, jit) if jit else 0)
            db.run("INSERT INTO posts(video_id,account_id,scheduled_at,privacy,status) VALUES(?,?,?,?,?)",
                   (vid, aid, when.strftime("%Y-%m-%d %H:%M:%S"), privacy, status))
            created += 1
    return {"created": created, "skipped": skipped, "review": status == "review"}


# ---------------- Kontrola pred zverejnením ----------------
def _review_rows():
    return db.q("""SELECT p.id post_id, p.scheduled_at, a.platform, a.name account, v.id video_id, v.lang, v.title,
                          v.caption, v.hashtags, CASE WHEN COALESCE(v.removed,0)=1 THEN COALESCE(v.preview_path,'') ELSE v.file_path END file_path,
                          v.project_id, v.original_name, s.idea_id, s.is_source, COALESCE(p.stash_id,'') stash_id
                   FROM posts p JOIN videos v ON v.id=p.video_id JOIN accounts a ON a.id=p.account_id
                   LEFT JOIN scripts s ON s.id=v.script_id WHERE p.status='review' ORDER BY p.scheduled_at""")


@app.get("/api/review")
def review_list():
    """Na schválenie: zoskupené podľa nápadu (originál + všetky jazyky), aby sa schvaľovalo jedným klikom."""
    groups = {}
    for r in _review_rows():
        key = f"i{r['idea_id']}" if r["idea_id"] else f"v{r['video_id']}"
        g = groups.setdefault(key, {"key": key, "project_id": r["project_id"], "first": r["scheduled_at"],
                                    "langs": {}, "accounts": set(), "posts": 0, "platforms": set()})
        g["posts"] += 1
        g["accounts"].add(r["account"])
        g["platforms"].add(r["platform"])
        L = g["langs"].setdefault(r["lang"] or "-", {"lang": r["lang"], "video_id": r["video_id"], "title": r["title"] or r["original_name"],
                                                       "caption": r["caption"], "hashtags": r["hashtags"], "file": r["file_path"],
                                                       "source": bool(r["is_source"]), "posts": 0, "yt": ""})
        if r["stash_id"] and not L["yt"]:
            L["yt"] = f"https://studio.youtube.com/video/{r['stash_id']}/edit"
        L["posts"] += 1
    out = []
    for g in groups.values():
        langs = sorted(g["langs"].values(), key=lambda x: (not x["source"], x["lang"] or ""))
        out.append({"key": g["key"], "project_id": g["project_id"], "first": g["first"], "posts": g["posts"],
                    "accounts": len(g["accounts"]), "platforms": sorted(g["platforms"]), "langs": langs,
                    "title": langs[0]["title"]})
    return out


def _review_ids(keys):
    ids = []
    for r in _review_rows():
        key = f"i{r['idea_id']}" if r["idea_id"] else f"v{r['video_id']}"
        if keys == "all" or key in keys:
            ids.append(r["post_id"])
    return ids


@app.post("/api/review/approve")
def review_approve(data: dict = Body(...)):
    """Schváli a pustí von. Čo už malo byť zverejnené, pôjde hneď (rozložené po minútach)."""
    ids = _review_ids(data.get("keys") or "all")
    now = datetime.now()
    for i, pid in enumerate(ids):
        row = db.one("SELECT scheduled_at FROM posts WHERE id=?", (pid,))
        when = row["scheduled_at"]
        if datetime.fromisoformat(when) < now:
            when = (now + timedelta(minutes=i // 3, seconds=random.randint(0, 50))).strftime("%Y-%m-%d %H:%M:%S")
        db.run("UPDATE posts SET status='queued', scheduled_at=? WHERE id=?", (when, pid))
    return {"approved": len(ids)}


@app.post("/api/review/reject")
def review_reject(data: dict = Body(...)):
    """Vráti na úpravu: zruší naplánovanie (videá ostanú, po oprave ich naplánuješ znova)."""
    ids = _review_ids(data.get("keys") or [])
    for pid in ids:
        r = db.one("SELECT p.stash_id, p.account_id FROM posts p WHERE p.id=?", (pid,))
        if r and r["stash_id"]:  # súkromne odložené na YouTube: zmazať, nech tam nestraší
            try:
                acc = db.one("SELECT * FROM accounts WHERE id=?", (r["account_id"],))
                youtube.delete_video(acc, r["stash_id"])
            except Exception as e:
                print("YouTube zmazanie:", e)
        db.run("DELETE FROM posts WHERE id=?", (pid,))
    return {"rejected": len(ids)}


@app.get("/api/posts")
def posts(status: str = "", limit: int = 300):
    where = "1=1"
    args = ()
    if status:
        where = "p.status=?"
        args = (status,)
    return _posts(where, "p.scheduled_at DESC" if status in ("done", "failed") else "p.scheduled_at", limit, args)


@app.post("/api/posts/{pid}/retry")
def post_retry(pid: int):
    db.run("UPDATE posts SET status='queued', attempts=0, error='', scheduled_at=? WHERE id=?",
           (scheduler.now_str(), pid))
    return {"ok": True}


@app.post("/api/posts/{pid}/move")
def post_move(pid: int, data: dict = Body(...)):
    db.run("UPDATE posts SET scheduled_at=? WHERE id=? AND status='queued'",
           (datetime.fromisoformat(data["when"]).strftime("%Y-%m-%d %H:%M:%S"), pid))
    return {"ok": True}


@app.delete("/api/posts/{pid}")
def post_delete(pid: int):
    db.run("DELETE FROM posts WHERE id=? AND status!='uploading'", (pid,))
    return {"ok": True}


@app.get("/api/update")
def update_check():
    try:
        r = updater.check_github(apply=False)
    except Exception as e:
        r = {"error": str(e)}
    return dict(r, version=updater.version(), repo=db.get_setting("update_repo", "") or updater.DEFAULT_REPO)


@app.post("/api/update/github")
def update_github():
    r = updater.check_github(apply=True)
    if r.get("updated"):
        updater.restart()
    return r


@app.post("/api/update/zip")
async def update_zip(file: UploadFile = File(...)):
    try:
        ver = updater.apply_zip(await file.read())
    except Exception as e:
        raise HTTPException(400, str(e))
    updater.restart()
    return {"updated": ver}


# ---------------- Komentáre (samostatný modul) ----------------
from . import comments  # noqa: E402
app.include_router(comments.router)
from . import messages  # noqa: E402
app.include_router(messages.router)
from . import radar_api  # noqa: E402
app.include_router(radar_api.router)
from . import profiles  # noqa: E402
app.include_router(profiles.router)
from . import events  # noqa: E402
app.include_router(events.router)
from . import dashboard as dash_page  # noqa: E402
app.include_router(dash_page.router)
from . import inspire  # noqa: E402
app.include_router(inspire.router)
from . import weather  # noqa: E402
app.include_router(weather.router)
from . import audio  # noqa: E402
app.include_router(audio.router)
try:
    inspire.fix_refrigerant_name()   # „PROLINE R290“ nie je názov, R290 je chladivo (jednorazová oprava textov)
except Exception as _e:
    print("oprava R290:", _e)
app.include_router(brand.router)


def main():
    import sys
    import threading

    import faulthandler
    import logging
    import uvicorn
    log_path = db.DATA_DIR / "chyby.log"
    if log_path.exists() and log_path.stat().st_size > 2_000_000:
        log_path.write_text("")
    _crash = open(log_path, "a", buffering=1)
    faulthandler.enable(_crash)
    logging.basicConfig(filename=str(log_path), level=logging.WARNING, format="%(asctime)s %(name)s %(message)s")
    _default_hook = sys.excepthook

    def _hook(t, v, tb):
        logging.getLogger("app").error("Pád appky", exc_info=(t, v, tb))
        _default_hook(t, v, tb)
    sys.excepthook = _hook
    threading.excepthook = lambda a: logging.getLogger("app").error("Chyba vo vlákne", exc_info=(a.exc_type, a.exc_value, a.exc_traceback))
    # automatická aktualizácia pri spustení (ak je nastavený repozitár)
    if db.get_setting("auto_update", True) and os.environ.get("SM_SKIP_UPDATE") != "1":
        try:
            r = updater.check_github(apply=True)
            if r.get("updated"):
                print("Appka aktualizovaná na verziu", r["updated"], "- reštartujem…")
                sys.exit(3)
        except Exception as e:
            print("Aktualizáciu sa nepodarilo skontrolovať:", e)
    try:
        from . import anim
        anim.ensure_installed()  # animácie: Chromium sa stiahne raz na pozadí
    except Exception:
        pass
    try:
        inspire._db()
    except Exception:
        pass
    try:
        from . import radar
        radar.start()  # trendy, konkurencia, čísla našich videí (na pozadí, bez AI)
    except Exception:
        pass
    updater.background_checker(lambda: any(not j.get("done") for j in JOBS.values()) or bool(scheduler.state.get("current"))
                               or AUTO.get("running") or PROD.get("running"))
    threading.Thread(target=_produce_loop, daemon=True).start()
    if os.environ.get("SM_NO_BROWSER") != "1":
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning", log_config=None)
    except BaseException as e:
        logging.getLogger("app").error("Server skončil: %r", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
