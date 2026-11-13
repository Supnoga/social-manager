"""Komentáre: zber zo všetkých účtov na jedno miesto, návrh odpovede od AI, odoslanie po schválení.

Šetrenie:
- zber komentárov je zadarmo (oficiálne API sietí, žiadna AI), beží sám každé 3 hodiny,
- AI (lacný model) píše návrhy len na kliknutie, po dávkach (do 25 komentárov v jednom volaní),
- preklad do slovenčiny pre teba robí bezplatný prekladač (ak je zapnutý), nie Claude,
- spam a komentáre bez potreby odpovede AI označí na preskočenie.
"""
import json
import threading
import time
import traceback
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, HTTPException

from . import ai, content, db
from .platforms import comments_api

router = APIRouter()
state = {"last_fetch": None, "running": False}
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL,
  platform TEXT NOT NULL,
  external_id TEXT NOT NULL,
  post_ext TEXT DEFAULT '',
  post_url TEXT DEFAULT '',
  post_title TEXT DEFAULT '',
  author TEXT DEFAULT '',
  text TEXT DEFAULT '',
  text_sk TEXT DEFAULT '',
  created TEXT DEFAULT '',
  likes INTEGER DEFAULT 0,
  status TEXT DEFAULT 'new',
  reply TEXT DEFAULT '',
  reply_sk TEXT DEFAULT '',
  error TEXT DEFAULT '',
  fetched_at TEXT DEFAULT (datetime('now','localtime')),
  UNIQUE(platform, external_id)
);
CREATE INDEX IF NOT EXISTS idx_comments_status ON comments(status, account_id);
"""
_ready = False


def _db():
    global _ready
    if not _ready:
        with db._lock:
            db.con().executescript(SCHEMA)
            db.con().commit()
        _ready = True


def settings():
    return {"auto_fetch": db.get_setting("comments_auto_fetch", True),
            "days": int(db.get_setting("comments_days", 14) or 14),
            "auto_draft": db.get_setting("comments_auto_draft", False),
            "tiktok": db.get_setting("comments_tiktok", False)}


# ---------------- zber ----------------
def _posts_for(account, days):
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    return db.q("SELECT p.external_id, p.url, v.title FROM posts p LEFT JOIN videos v ON v.id=p.video_id "
                "WHERE p.account_id=? AND p.status='done' AND p.updated_at>=? AND p.external_id!='' "
                "ORDER BY p.updated_at DESC LIMIT 40", (account["id"], since))


def fetch_all():
    """Stiahne nové komentáre zo všetkých účtov. Vráti počet nových."""
    _db()
    if not _lock.acquire(blocking=False):
        return {"new": 0, "busy": True}
    state["running"] = True
    new, errors = 0, {}
    try:
        days = settings()["days"]
        for acc in db.q("SELECT * FROM accounts"):
            posts = _posts_for(acc, days)
            if not posts and acc["platform"] != "youtube":  # YouTube číta celý kanál naraz
                continue
            try:
                items = comments_api.list_comments(acc, posts)
            except Exception as e:
                errors[str(acc["id"])] = {"name": acc["name"], "platform": acc["platform"], "error": str(e)[:300]}
                continue
            for it in items:
                ex = db.one("SELECT id FROM comments WHERE platform=? AND external_id=?", (acc["platform"], it["id"]))
                if ex:
                    continue
                db.run("INSERT INTO comments(account_id,platform,external_id,post_ext,post_url,post_title,author,text,created,likes,status) "
                       "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (acc["id"], acc["platform"], it["id"], it.get("post", ""), it.get("post_url", ""),
                        it.get("post_title", ""), it.get("author", ""), it.get("text", ""), it.get("created", ""),
                        int(it.get("likes") or 0), "answered" if it.get("answered") else "new"))
                new += 1
        db.set_setting("comments_errors", errors)
        state["last_fetch"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if new:
            _translate_new()
            if settings()["auto_draft"]:
                try:
                    draft()
                except Exception:
                    traceback.print_exc()
    finally:
        state["running"] = False
        _lock.release()
    return {"new": new, "errors": len(errors)}


def _translate_new():
    """Preklad komentárov do slovenčiny bezplatným prekladačom (žiadne Claude tokeny)."""
    try:
        from . import translate
        if not translate.any_enabled():
            return
    except Exception:
        return
    rows = db.q("SELECT c.id, c.text, a.lang FROM comments c JOIN accounts a ON a.id=c.account_id "
                "WHERE c.text_sk='' AND c.status IN ('new','draft') AND a.lang!='' AND a.lang!='sk' LIMIT 300")
    by_lang = {}
    for r in rows:
        by_lang.setdefault(r["lang"], []).append(r)
    for lang, group in by_lang.items():
        try:
            out, _ = translate.translate_texts([g["text"][:500] for g in group], lang, "sk")
            for g, t in zip(group, out):
                db.run("UPDATE comments SET text_sk=? WHERE id=?", (t or "", g["id"]))
        except Exception:
            pass


# ---------------- AI návrhy ----------------
def _prompt(project, items):
    brand = (project or {}).get("name") or "the brand"
    info = ((project or {}).get("strategy_short") or (project or {}).get("description") or "")[:500]
    tone = ((project or {}).get("tone") or "friendly, warm")[:120]
    return (f"Write replies to social media comments as the creator of '{brand}'. About: {info}\nTone: {tone}.\n"
            "Rules: reply in the SAME language as the comment; 1-2 short sentences; natural, human, no hashtags, "
            "max 1 emoji; never invent facts, prices or promises; questions you cannot answer -> invite to follow/DM. "
            "Set s=1 (skip) for spam, hate, bots, single emoji or comments needing no reply.\n"
            'Return JSON {"r":[{"i":<id>,"t":"<reply>","s":0}]}\nComments (v=video title):\n'
            + json.dumps(items, ensure_ascii=False, separators=(",", ":")))


def draft(ids=None):
    """Pripraví návrhy odpovedí pre nové komentáre (alebo vybrané). Po dávkach, lacný model."""
    _db()
    if ids:
        rows = db.q(f"SELECT c.*, a.project_id, a.lang acc_lang FROM comments c JOIN accounts a ON a.id=c.account_id "
                    f"WHERE c.id IN ({','.join('?' * len(ids))})", tuple(ids))
    else:
        rows = db.q("SELECT c.*, a.project_id, a.lang acc_lang FROM comments c JOIN accounts a ON a.id=c.account_id "
                    "WHERE c.status='new' ORDER BY c.id DESC LIMIT 200")
    by_proj = {}
    for r in rows:
        by_proj.setdefault(r["project_id"], []).append(r)
    done = skipped = 0
    for pid, group in by_proj.items():
        project = db.one("SELECT name, strategy_short, description, tone FROM projects WHERE id=?", (pid,)) if pid else None
        for i in range(0, len(group), 25):
            batch = group[i:i + 25]
            items = [{"i": r["id"], "c": (r["text"] or "")[:300], "v": (r["post_title"] or "")[:60]} for r in batch]
            res = ai.ask(_prompt(project, items), "komentáre", kind="cheap")
            d, k = _apply(res)
            done += d
            skipped += k
    _translate_replies()
    return {"drafted": done, "skipped": skipped}


def _apply(res):
    done = skipped = 0
    for x in (res.get("r") if isinstance(res, dict) else res) or []:
        try:
            cid = int(x.get("i"))
        except Exception:
            continue
        if x.get("s") in (1, "1", True):
            db.run("UPDATE comments SET status='skip', reply='' WHERE id=? AND status IN ('new','draft')", (cid,))
            skipped += 1
        elif (x.get("t") or "").strip():
            db.run("UPDATE comments SET status='draft', reply=?, reply_sk='' WHERE id=? AND status IN ('new','draft','skip')",
                   (x["t"].strip(), cid))
            done += 1
    return done, skipped


def _manual_apply(params, data):
    """Ručný režim AI (bez Claude Code): odpoveď vložená z claude.ai."""
    d, k = _apply(data)
    _translate_replies()
    return {"drafted": d, "skipped": k}


content.TASKS["komentáre"] = (None, _manual_apply, "cheap")


def _translate_replies():
    try:
        from . import translate
        if not translate.any_enabled():
            return
    except Exception:
        return
    rows = db.q("SELECT c.id, c.reply, a.lang FROM comments c JOIN accounts a ON a.id=c.account_id "
                "WHERE c.status='draft' AND c.reply!='' AND c.reply_sk='' AND a.lang!='' AND a.lang!='sk' LIMIT 300")
    by_lang = {}
    for r in rows:
        by_lang.setdefault(r["lang"], []).append(r)
    for lang, group in by_lang.items():
        try:
            out, _ = translate.translate_texts([g["reply"] for g in group], lang, "sk")
            for g, t in zip(group, out):
                db.run("UPDATE comments SET reply_sk=? WHERE id=?", (t or "", g["id"]))
        except Exception:
            pass


# ---------------- odoslanie ----------------
def send(ids):
    _db()
    ok = fail = 0
    for cid in ids:
        c = db.one("SELECT * FROM comments WHERE id=?", (cid,))
        if not c or not (c["reply"] or "").strip() or c["status"] == "sent":
            continue
        acc = db.one("SELECT * FROM accounts WHERE id=?", (c["account_id"],))
        try:
            if not acc:
                raise RuntimeError("Účet už neexistuje")
            comments_api.reply(acc, c, c["reply"].strip())
            db.run("UPDATE comments SET status='sent', error='' WHERE id=?", (cid,))
            ok += 1
        except Exception as e:
            db.run("UPDATE comments SET status='failed', error=? WHERE id=?", (str(e)[:500], cid))
            fail += 1
        time.sleep(1.5)  # nech to siete neberú ako spam
    return {"sent": ok, "failed": fail}


# ---------------- automatický zber na pozadí ----------------
def _loop():
    time.sleep(60)
    while True:
        try:
            if settings()["auto_fetch"] and not db.get_setting("paused", False):
                fetch_all()
        except Exception:
            traceback.print_exc()
        time.sleep(2 * 3600)


_started = False


@router.on_event("startup")
def _start():
    global _started
    if not _started:
        _started = True
        _db()
        threading.Thread(target=_loop, daemon=True).start()


# ---------------- API ----------------
@router.get("/api/comments")
def api_list(status: str = "new", project_id: int = 0, platform: str = ""):
    _db()
    where, args = [], []
    if status == "new":
        where.append("c.status IN ('new','draft','failed')")
    elif status:
        where.append("c.status=?")
        args.append(status)
    if project_id:
        where.append("a.project_id=?")
        args.append(project_id)
    if platform:
        where.append("c.platform=?")
        args.append(platform)
    rows = db.q("SELECT c.*, a.name account_name, a.lang, a.project_id, pr.name project_name, pr.color project_color FROM comments c "
                "JOIN accounts a ON a.id=c.account_id LEFT JOIN projects pr ON pr.id=a.project_id "
                + ("WHERE " + " AND ".join(where) if where else "") + " ORDER BY COALESCE(NULLIF(c.created,''), c.fetched_at) DESC, c.id DESC LIMIT 300", tuple(args))
    cw, ca = ("WHERE a.project_id=?", (project_id,)) if project_id else ("", ())
    counts = {r["status"]: r["n"] for r in db.q("SELECT c.status, COUNT(*) n FROM comments c JOIN accounts a ON a.id=c.account_id "
                                                + cw + " GROUP BY c.status", ca)}
    return {"items": rows, "counts": counts, "state": state, "settings": settings(),
            "errors": db.get_setting("comments_errors", {}) or {}}


@router.get("/api/comments/count")
def api_count():
    _db()
    return {"n": db.one("SELECT COUNT(*) n FROM comments WHERE status IN ('new','draft')")["n"]}


@router.get("/api/comments/summary")
def api_summary():
    """Pre hlavnú stránku: počet nezodpovedaných, nové za 24 h, po projektoch a 6 najnovších."""
    _db()
    since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    by_p = db.q("""SELECT a.project_id p, COUNT(*) n FROM comments c JOIN accounts a ON a.id=c.account_id
                   WHERE c.status IN ('new','draft','failed') GROUP BY a.project_id ORDER BY n DESC""")
    latest = db.q("""SELECT c.id, c.platform, c.external_id, c.post_ext, c.post_url, c.post_title, c.author, c.text, c.text_sk, c.created,
                            c.status, a.name account_name, a.project_id, pr.name project_name, pr.color project_color
                     FROM comments c JOIN accounts a ON a.id=c.account_id LEFT JOIN projects pr ON pr.id=a.project_id
                     WHERE c.status IN ('new','draft','failed') ORDER BY COALESCE(NULLIF(c.created,''), c.fetched_at) DESC LIMIT 6""")
    return {"open": sum(r["n"] for r in by_p), "day": db.one("SELECT COUNT(*) n FROM comments WHERE created>=?", (since,))["n"],
            "by_project": by_p, "latest": latest, "last": state["last_fetch"], "running": state["running"]}


@router.post("/api/comments/fetch")
def api_fetch():
    return fetch_all()


@router.post("/api/comments/draft")
def api_draft(data: dict = Body(default={})):
    return draft(data.get("ids") or None)


@router.post("/api/comments/send")
def api_send(data: dict = Body(...)):
    ids = data.get("ids") or []
    if data.get("all_drafts"):
        ids = [r["id"] for r in db.q("SELECT id FROM comments WHERE status='draft' AND reply!=''")]
    return send(ids)


@router.put("/api/comments/{cid}")
def api_update(cid: int, data: dict = Body(...)):
    _db()
    if "reply" in data:
        db.run("UPDATE comments SET reply=?, reply_sk='', status=CASE WHEN ?='' THEN 'new' ELSE 'draft' END WHERE id=?",
               (data["reply"].strip(), data["reply"].strip(), cid))
    if data.get("status") in ("new", "skip", "draft"):
        db.run("UPDATE comments SET status=? WHERE id=?", (data["status"], cid))
    return {"ok": True}


@router.post("/api/comments/settings")
def api_settings(data: dict = Body(...)):
    for k in ("auto_fetch", "days", "auto_draft", "tiktok"):
        if k in data:
            db.set_setting("comments_" + k, data[k])
    if "tiktok" in data:
        # TikTok práva na komentáre pýtame až keď ich máš v TikTok portáli schválené (inak by zlyhalo prihlásenie)
        base = "user.info.basic,user.info.username,video.upload,video.publish"
        db.set_setting("ttb_scopes", base + (",comment.list,comment.list.manage" if data["tiktok"] else ""))
    return {"ok": True}
