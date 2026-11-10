"""Súkromné správy: zber z Facebook stránok a Instagram účtov na jedno miesto, návrh odpovede od AI, odoslanie po schválení.

Čo siete dovoľujú (november 2026):
- Facebook stránky a Instagram (profesionálne účty): áno, zadarmo cez Meta API.
  Odpísať sa dá do 24 hodín od poslednej správy človeka, s povolením „Human Agent“ do 7 dní.
- TikTok: API na správy je v EÚ/EHP, Švajčiarsku a UK zakázané -> odpisuje sa v appke TikTok.
- LinkedIn: API na správy majú len schválení partneri LinkedInu -> odpisuje sa na LinkedIne.

Šetrenie:
- zber je zadarmo (žiadna AI), beží sám každú hodinu (kvôli 24-hodinovému oknu),
- AI (lacný model) píše návrhy len na kliknutie alebo po zapnutí, po dávkach (15 konverzácií v jednom volaní),
  s krátkym kontextom (posledné 4 správy, každá skrátená),
- preklad do slovenčiny robí bezplatný prekladač, nie Claude.
"""
import json
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body

from . import ai, content, db
from .platforms import meta
from .platforms.common import PlatformError, check, client, tokens

router = APIRouter()
state = {"last_fetch": None, "running": False}
_lock = threading.Lock()
PLATFORMS = ("facebook", "instagram")

SCHEMA = """
CREATE TABLE IF NOT EXISTS dms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL,
  platform TEXT NOT NULL,
  conv_id TEXT NOT NULL,
  user_id TEXT DEFAULT '',
  author TEXT DEFAULT '',
  last_msg_id TEXT DEFAULT '',
  history TEXT DEFAULT '[]',
  text TEXT DEFAULT '',
  text_sk TEXT DEFAULT '',
  last_in TEXT DEFAULT '',
  status TEXT DEFAULT 'new',
  reply TEXT DEFAULT '',
  reply_sk TEXT DEFAULT '',
  error TEXT DEFAULT '',
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  UNIQUE(platform, conv_id)
);
CREATE INDEX IF NOT EXISTS idx_dms_status ON dms(status, account_id);
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
    return {"auto_fetch": db.get_setting("dm_auto_fetch", True),
            "auto_draft": db.get_setting("dm_auto_draft", False),
            "human_agent": db.get_setting("dm_human_agent", False)}


def _ts(s):
    """Čas z Meta (2026-11-10T10:00:00+0000) -> datetime v UTC."""
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        return None


def hours_left(last_in, human_agent=False):
    t = _ts(last_in or "")
    if not t:
        return None
    limit = 7 * 24 if human_agent else 24
    return limit - (datetime.now(timezone.utc) - t).total_seconds() / 3600


# ---------------- zber ----------------
def _list(acc):
    """Konverzácie jedného účtu: [{conv, user, author, last_id, last_in, history, incoming, answered}]."""
    t = tokens(acc)
    page, tok = t.get("page_id"), t.get("page_token")
    if not page or not tok:
        return []
    ig = acc["platform"] == "instagram"
    me = {page, t.get("ig_id") or "", acc["external_id"]}
    me_name = acc["name"].lstrip("@")
    since = datetime.now(timezone.utc) - timedelta(days=7)
    out = []
    with client() as c:
        r = c.get(meta.G(f"{page}/conversations"), params={
            "access_token": tok, "platform": "instagram" if ig else "messenger", "limit": 50,
            "fields": "id,updated_time,participants,messages.limit(6){id,message,from,created_time}"})
        if r.status_code in (400, 403) and ("permission" in r.text.lower() or "(#200)" in r.text or "(#10)" in r.text):
            perm = "instagram_manage_messages" if ig else "pages_messaging"
            raise PlatformError(f"{'Instagram' if ig else 'Facebook'}: token nemá právo na správy ({perm}). "
                                "Vytvor nový token a vlož ho v Účtoch (postup je dole na tejto stránke).")
        check(r, "Instagram správy" if ig else "Facebook správy")
        for cv in r.json().get("data", []):
            upd = _ts(cv.get("updated_time", ""))
            if upd and upd < since:
                continue
            msgs = (cv.get("messages") or {}).get("data", [])  # najnovšia prvá
            if not msgs:
                continue

            def mine(m):
                f = m.get("from") or {}
                return f.get("id") in me or (ig and f.get("username") == me_name)

            other = next((p for p in (cv.get("participants") or {}).get("data", [])
                          if p.get("id") not in me and p.get("username") != me_name), {})
            incoming = []
            for m in msgs:
                if mine(m):
                    break
                incoming.append(m)
            last_in = next((m.get("created_time", "") for m in msgs if not mine(m)), "")
            hist = [{"me": 1 if mine(m) else 0, "t": (m.get("message") or "")[:200]}
                    for m in reversed(msgs[len(incoming):len(incoming) + 3])]  # staršie správy pred novými
            out.append({"conv": cv["id"], "user": other.get("id", ""),
                        "author": ("@" + other["username"]) if other.get("username") else other.get("name", ""),
                        "last_id": msgs[0].get("id", ""), "last_in": last_in, "history": hist,
                        "incoming": "\n".join((m.get("message") or "[príloha]") for m in reversed(incoming)),
                        "answered": not incoming})
    return out


def fetch_all():
    """Stiahne nové správy zo všetkých FB/IG účtov. Žiadna AI."""
    _db()
    if not _lock.acquire(blocking=False):
        return {"new": 0, "busy": True}
    state["running"] = True
    new, errors = 0, {}
    try:
        for acc in db.q("SELECT * FROM accounts WHERE platform IN ('facebook','instagram')"):
            try:
                items = _list(acc)
            except Exception as e:
                errors[str(acc["id"])] = {"name": acc["name"], "platform": acc["platform"], "error": str(e)[:300]}
                continue
            for it in items:
                ex = db.one("SELECT id, last_msg_id, status FROM dms WHERE platform=? AND conv_id=?",
                            (acc["platform"], it["conv"]))
                if ex and ex["last_msg_id"] == it["last_id"]:
                    continue
                st = "answered" if it["answered"] else "new"
                if ex:
                    if it["answered"]:
                        db.run("UPDATE dms SET last_msg_id=?, history=?, status=CASE WHEN status IN ('sent','skip') "
                               "THEN status ELSE 'answered' END, updated_at=datetime('now','localtime') WHERE id=?",
                               (it["last_id"], json.dumps(it["history"], ensure_ascii=False), ex["id"]))
                        continue
                    db.run("UPDATE dms SET last_msg_id=?, history=?, text=?, text_sk='', last_in=?, status='new', "
                           "reply='', reply_sk='', error='', author=?, user_id=?, updated_at=datetime('now','localtime') "
                           "WHERE id=?", (it["last_id"], json.dumps(it["history"], ensure_ascii=False), it["incoming"],
                                          it["last_in"], it["author"], it["user"], ex["id"]))
                else:
                    db.run("INSERT INTO dms(account_id,platform,conv_id,user_id,author,last_msg_id,history,text,last_in,status) "
                           "VALUES(?,?,?,?,?,?,?,?,?,?)",
                           (acc["id"], acc["platform"], it["conv"], it["user"], it["author"], it["last_id"],
                            json.dumps(it["history"], ensure_ascii=False), it["incoming"], it["last_in"], st))
                if st == "new":
                    new += 1
        db.set_setting("dm_errors", errors)
        state["last_fetch"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if new:
            _translate("text", "text_sk", "('new','draft')")
            if settings()["auto_draft"]:
                try:
                    draft()
                except Exception:
                    traceback.print_exc()
    finally:
        state["running"] = False
        _lock.release()
    return {"new": new, "errors": len(errors)}


def _translate(src, dst, statuses):
    """Preklad do slovenčiny bezplatným prekladačom (žiadne Claude tokeny)."""
    try:
        from . import translate
        if not translate.any_enabled():
            return
    except Exception:
        return
    rows = db.q(f"SELECT d.id, d.{src} s, a.lang FROM dms d JOIN accounts a ON a.id=d.account_id "
                f"WHERE d.{dst}='' AND d.{src}!='' AND d.status IN {statuses} AND a.lang!='' AND a.lang!='sk' LIMIT 300")
    by_lang = {}
    for r in rows:
        by_lang.setdefault(r["lang"], []).append(r)
    for lang, group in by_lang.items():
        try:
            out, _ = translate.translate_texts([g["s"][:600] for g in group], lang, "sk")
            for g, t in zip(group, out):
                db.run(f"UPDATE dms SET {dst}=? WHERE id=?", (t or "", g["id"]))
        except Exception:
            pass


# ---------------- AI návrhy ----------------
def _prompt(project, items):
    brand = (project or {}).get("name") or "the brand"
    info = ((project or {}).get("strategy_short") or (project or {}).get("description") or "")[:500]
    tone = ((project or {}).get("tone") or "friendly, warm")[:120]
    return (f"Write replies to private messages (DMs) sent to the social media account of '{brand}'. About: {info}\n"
            f"Tone: {tone}.\nRules: reply in the SAME language as the customer; 1-3 short sentences; natural, human, "
            "polite; max 1 emoji; never invent facts, prices, availability, dates or promises; never ask for passwords "
            "or payment data; if you cannot answer, thank them and say a colleague will get back soon. "
            "Set s=1 (skip) for spam, scams, bots, hate or messages needing no reply.\n"
            'Return JSON {"r":[{"i":<id>,"t":"<reply>","s":0}]}\n'
            "Conversations (h=earlier messages [me,text], me=1 is us; m=new message to answer):\n"
            + json.dumps(items, ensure_ascii=False, separators=(",", ":")))


def draft(ids=None):
    _db()
    base = "SELECT d.*, a.project_id FROM dms d JOIN accounts a ON a.id=d.account_id "
    if ids:
        rows = db.q(base + f"WHERE d.id IN ({','.join('?' * len(ids))})", tuple(ids))
    else:
        rows = db.q(base + "WHERE d.status='new' ORDER BY d.id DESC LIMIT 150")
    if not ids:  # na správy po čase už odpísať nejde -> na ne nemíňame AI
        ha = settings()["human_agent"]
        rows = [r for r in rows if (hours_left(r["last_in"], ha) or 1) > 0]
    by_proj = {}
    for r in rows:
        by_proj.setdefault(r["project_id"], []).append(r)
    done = skipped = 0
    for pid, group in by_proj.items():
        project = db.one("SELECT name, strategy_short, description, tone FROM projects WHERE id=?", (pid,)) if pid else None
        for i in range(0, len(group), 15):
            items = []
            for r in group[i:i + 15]:
                try:
                    h = json.loads(r["history"] or "[]")[-3:]
                except Exception:
                    h = []
                it = {"i": r["id"], "m": (r["text"] or "")[:400]}
                if h:
                    it["h"] = [[x["me"], x["t"][:120]] for x in h]
                items.append(it)
            res = ai.ask(_prompt(project, items), "správy", kind="cheap")
            d, k = _apply(res)
            done += d
            skipped += k
    _translate("reply", "reply_sk", "('draft')")
    return {"drafted": done, "skipped": skipped}


def _apply(res):
    done = skipped = 0
    for x in (res.get("r") if isinstance(res, dict) else res) or []:
        try:
            did = int(x.get("i"))
        except Exception:
            continue
        if x.get("s") in (1, "1", True):
            db.run("UPDATE dms SET status='skip', reply='' WHERE id=? AND status IN ('new','draft')", (did,))
            skipped += 1
        elif (x.get("t") or "").strip():
            db.run("UPDATE dms SET status='draft', reply=?, reply_sk='' WHERE id=? AND status IN ('new','draft','skip')",
                   (x["t"].strip(), did))
            done += 1
    return done, skipped


def _manual_apply(params, data):
    d, k = _apply(data)
    _translate("reply", "reply_sk", "('draft')")
    return {"drafted": d, "skipped": k}


content.TASKS["správy"] = (None, _manual_apply, "cheap")


# ---------------- odoslanie ----------------
def _send_one(acc, dm, text):
    t = tokens(acc)
    body = {"recipient": {"id": dm["user_id"]}, "message": {"text": text}, "messaging_type": "RESPONSE"}
    left = hours_left(dm["last_in"])
    if left is not None and left <= 0:
        if not settings()["human_agent"] or hours_left(dm["last_in"], True) <= 0:
            raise PlatformError("Čas na odpoveď vypršal (siete dovoľujú odpísať do 24 hodín od správy). "
                                "Odpíš priamo v appke Facebook/Instagram.")
        body.update(messaging_type="MESSAGE_TAG", tag="HUMAN_AGENT")
    if not dm["user_id"]:
        raise PlatformError("Neviem, komu odpovedať (chýba príjemca). Načítaj správy znova.")
    with client() as c:
        r = c.post(meta.G(f"{t['page_id']}/messages"), params={"access_token": t["page_token"]}, json=body)
        if r.status_code >= 400 and "outside of allowed window" in r.text.lower():
            raise PlatformError("Čas na odpoveď vypršal. Odpíš priamo v appke Facebook/Instagram.")
        check(r, ("Instagram" if acc["platform"] == "instagram" else "Facebook") + " správa")


def send(ids):
    from .scheduler import dry_run
    if dry_run():
        raise RuntimeError("Režim nasucho: nič sa neodosiela ani nepublikuje.")
    _db()
    ok = fail = 0
    for did in ids:
        d = db.one("SELECT * FROM dms WHERE id=?", (did,))
        if not d or not (d["reply"] or "").strip() or d["status"] == "sent":
            continue
        acc = db.one("SELECT * FROM accounts WHERE id=?", (d["account_id"],))
        try:
            if not acc:
                raise PlatformError("Účet už neexistuje")
            _send_one(acc, d, d["reply"].strip())
            db.run("UPDATE dms SET status='sent', error='' WHERE id=?", (did,))
            ok += 1
        except Exception as e:
            db.run("UPDATE dms SET status='failed', error=? WHERE id=?", (str(e)[:500], did))
            fail += 1
        time.sleep(1.5)
    return {"sent": ok, "failed": fail}


# ---------------- automatický zber ----------------
def _loop():
    time.sleep(90)
    while True:
        try:
            if settings()["auto_fetch"] and not db.get_setting("paused", False):
                fetch_all()
        except Exception:
            traceback.print_exc()
        time.sleep(3600)


_started = False


@router.on_event("startup")
def _start():
    global _started
    if not _started:
        _started = True
        _db()
        threading.Thread(target=_loop, daemon=True).start()


# ---------------- API ----------------
@router.get("/api/dms")
def api_list(status: str = "new", project_id: int = 0, platform: str = ""):
    _db()
    where, args = [], []
    if status == "new":
        where.append("d.status IN ('new','draft','failed')")
    elif status:
        where.append("d.status=?")
        args.append(status)
    if project_id:
        where.append("a.project_id=?")
        args.append(project_id)
    if platform:
        where.append("d.platform=?")
        args.append(platform)
    rows = db.q("SELECT d.*, a.name account_name, a.lang, a.project_id FROM dms d JOIN accounts a ON a.id=d.account_id "
                + ("WHERE " + " AND ".join(where) if where else "") + " ORDER BY d.last_in DESC, d.id DESC LIMIT 300",
                tuple(args))
    ha = settings()["human_agent"]
    for r in rows:
        left = hours_left(r["last_in"], ha)
        r["hours_left"] = None if left is None else round(left, 1)
        try:
            r["history"] = json.loads(r["history"] or "[]")
        except Exception:
            r["history"] = []
    pj = "AND a.project_id=?" if project_id else ""
    counts = {r["status"]: r["n"] for r in db.q(
        f"SELECT d.status, COUNT(*) n FROM dms d JOIN accounts a ON a.id=d.account_id WHERE 1=1 {pj} GROUP BY d.status",
        (project_id,) if project_id else ())}
    return {"items": rows, "counts": counts, "state": state, "settings": settings(),
            "errors": db.get_setting("dm_errors", {}) or {}}


@router.get("/api/dms/count")
def api_count():
    _db()
    return {"n": db.one("SELECT COUNT(*) n FROM dms WHERE status IN ('new','draft')")["n"]}


@router.post("/api/dms/fetch")
def api_fetch():
    return fetch_all()


@router.post("/api/dms/draft")
def api_draft(data: dict = Body(default={})):
    return draft(data.get("ids") or None)


@router.post("/api/dms/send")
def api_send(data: dict = Body(...)):
    ids = data.get("ids") or []
    if data.get("all_drafts"):
        pj = "AND account_id IN (SELECT id FROM accounts WHERE project_id=?)" if data.get("project_id") else ""
        ids = [r["id"] for r in db.q(f"SELECT id FROM dms WHERE status='draft' AND reply!='' {pj}",
                                     (data["project_id"],) if pj else ())]
    return send(ids)


@router.put("/api/dms/{did}")
def api_update(did: int, data: dict = Body(...)):
    _db()
    if "reply" in data:
        r = data["reply"].strip()
        db.run("UPDATE dms SET reply=?, reply_sk='', status=CASE WHEN ?='' THEN 'new' ELSE 'draft' END WHERE id=?",
               (r, r, did))
    if data.get("status") in ("new", "skip", "draft"):
        db.run("UPDATE dms SET status=? WHERE id=?", (data["status"], did))
    return {"ok": True}


@router.post("/api/dms/settings")
def api_settings(data: dict = Body(...)):
    for k in ("auto_fetch", "auto_draft", "human_agent"):
        if k in data:
            db.set_setting("dm_" + k, bool(data[k]))
    return {"ok": True}
