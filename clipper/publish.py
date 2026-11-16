"""Zverejňovanie klipov: rozvrh po účtoch, nahratie cez hotové napojenia Social Managera, opakovanie pri chybe.

Jeden klip ide na každú sieť kampane raz (na jeden účet tej siete). Viac účtov na jednej sieti si klipy delí,
aby ten istý klip nebol na dvoch účtoch tej istej siete (siete to berú ako spam)."""
import hashlib
import hmac
import os
import random
import re
from datetime import datetime, timedelta

from app import db as appdb
from app.platforms import meta, tiktok, tiktok_business, youtube
from app.platforms.common import check, client, file_chunks, tokens

from . import store

FMT = "%Y-%m-%d %H:%M:%S"
MAX_TRIES = 4


# ---------- texty ----------
def _tags(camp):
    """Povinné značky kampane (hashtagy, označenia) tak, ako ich kampaň chce."""
    return " ".join(re.findall(r"[#@][\w.]+", camp.get("tags") or ""))


def texts(clip, camp, platform):
    title = re.sub(r"[<>]", "", (clip.get("title") or clip.get("hook") or "Clip")).strip()
    body = re.sub(r"[<>]", "", (clip.get("caption") or title)).strip()
    tags = _tags(camp)
    if platform == "youtube":
        t = title[:92]
        if tags and len(t) + len(tags) < 96 and "#" in tags:
            t = (t + " " + " ".join(x for x in tags.split() if x.startswith("#"))[:96 - len(t)]).strip()
        return t, (body + "\n\n" + (tags + " " if tags else "") + "#shorts").strip()
    return title, (body + ("\n\n" + tags if tags else "")).strip()[:2100]


# ---------- verejný odkaz na súbor klipu (TikTok si video sťahuje sám) ----------
def clip_token(clip_id):
    return hmac.new(tiktok_business._secret().encode(), f"c{clip_id}".encode(), hashlib.sha256).hexdigest()[:32]


def public_url(clip_id):
    return f"{tiktok_business.public_base()}/pub/c/{clip_id}/{clip_token(clip_id)}.mp4"


def _video(clip, camp, platform):
    title, text = texts(clip, camp, platform)
    v = {"id": clip["id"], "file_path": clip["path"], "duration": clip.get("duration") or 0, "title": title,
         "lang": camp.get("lang") or "en", "kind": "short", "fixed_text": (title, text)}
    if platform == "tiktok":
        v["public_url"] = public_url(clip["id"])
    return v


# ---------- YouTube (vlastné jednoduché nahratie: bez sérií, prekladov a titulkov Social Managera) ----------
def _yt_upload(acc, video):
    if not youtube.quota_ok(acc):
        raise RuntimeError("quota: dnešný limit nahratí YouTube je minutý")
    tok = youtube.access_token(acc)
    title, desc = video["fixed_text"]
    body = {"snippet": {"title": title[:100], "description": desc[:4900], "categoryId": "24",
                        "defaultLanguage": video["lang"], "defaultAudioLanguage": video["lang"]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(video["file_path"])
    with client(timeout=3600) as c:
        r = check(c.post("https://www.googleapis.com/upload/youtube/v3/videos",
                         params={"uploadType": "resumable", "part": "snippet,status"},
                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                  "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/*"},
                         json=body), "YouTube štart nahrávania")
        r = check(c.put(r.headers["Location"], headers={"Authorization": f"Bearer {tok}", "Content-Length": str(size),
                                                         "Content-Type": "video/*"},
                        content=file_chunks(video["file_path"])), "YouTube nahrávanie")
        vid = r.json()["id"]
    youtube.count_upload(acc)
    return vid, f"https://www.youtube.com/shorts/{vid}"


def _upload(acc, video):
    p = acc["platform"]
    if p == "youtube":
        return _yt_upload(acc, video)
    if p == "instagram":
        return meta.upload_instagram(acc, video)
    if p == "facebook":
        return meta.upload_facebook(acc, video)
    if p == "tiktok":
        return (tiktok_business.upload if tokens(acc).get("api") == "business" else tiktok.upload)(acc, video, "public")
    raise RuntimeError("Na túto sieť Clipper nezverejňuje: " + p)


# ---------- rozvrh ----------
def window():
    w = store.get("window", [10, 23])
    try:
        a, b = int(w[0]), int(w[1])
    except Exception:
        a, b = 10, 23
    return max(0, min(22, a)), max(a + 1, min(24, b))


def next_slot(account_id, per_day):
    """Najbližší voľný čas pre účet: klipy rovnomerne cez deň, s malou náhodou, najviac per_day denne."""
    h0, h1 = window()
    per_day = max(1, int(per_day))
    gap = (h1 - h0) * 3600 / per_day
    now = datetime.now()
    last = store.one("SELECT MAX(scheduled_at) m FROM posts WHERE account_id=? AND status IN ('queued','posting','posted')",
                     (account_id,))["m"]
    t = now + timedelta(minutes=4)
    if last:
        t = max(t, datetime.strptime(last, FMT) + timedelta(seconds=gap * random.uniform(0.85, 1.15)))
    for _ in range(60):
        start = t.replace(hour=h0, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=h1 - h0)
        if t < start:
            t = start + timedelta(minutes=random.uniform(1, 25))
        day = t.strftime("%Y-%m-%d")
        n = store.one("SELECT COUNT(*) n FROM posts WHERE account_id=? AND status IN ('queued','posting','posted') "
                      "AND substr(scheduled_at,1,10)=?", (account_id, day))["n"]
        if t <= end and n < per_day:
            break
        t = start + timedelta(days=1, minutes=random.uniform(1, 25))
    return t.strftime(FMT)


def plan(clip):
    """Schválený klip rozdelí na účty (jeden účet na každú sieť kampane). Vráti počet naplánovaných zverejnení."""
    camp = store.campaign(clip["campaign_id"]) or {}
    nets = camp.get("networks") or []
    accs = [a for a in store.accounts() if a["active"] and not a["broken"] and a["platform"] in nets]
    made = 0
    for net in nets:
        mine = [a for a in accs if a["platform"] == net]
        if not mine or store.one("SELECT id FROM posts WHERE clip_id=? AND platform=?", (clip["id"], net)):
            continue
        slots = sorted(((next_slot(a["id"], a["per_day"]), a) for a in mine), key=lambda x: x[0])
        when, acc = slots[0]
        store.run("INSERT INTO posts(clip_id, account_id, platform, scheduled_at) VALUES(?,?,?,?)", (clip["id"], acc["id"], net, when))
        made += 1
    if made or store.one("SELECT id FROM posts WHERE clip_id=?", (clip["id"],)):
        store.run("UPDATE clips SET status='planned' WHERE id=?", (clip["id"],))
    return made


# ---------- zverejnenie ----------
def due():
    return store.one("SELECT * FROM posts WHERE status='queued' AND scheduled_at<=? ORDER BY scheduled_at LIMIT 1", (store.now(),))


def publish(post):
    """Zverejní jeden príspevok. Chybu zapíše a skúsi neskôr (najviac 4-krát)."""
    clip = store.one("SELECT * FROM clips WHERE id=?", (post["clip_id"],))
    acc = appdb.one("SELECT * FROM accounts WHERE id=?", (post["account_id"],))
    if not clip or not acc or not os.path.exists(clip.get("path") or ""):
        store.run("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?",
                  ("Chýba súbor klipu alebo účet.", store.now(), post["id"]))
        return False
    camp = store.campaign(clip["campaign_id"]) or {}
    store.run("UPDATE posts SET status='posting', attempts=attempts+1, updated_at=? WHERE id=?", (store.now(), post["id"]))
    try:
        ext, url = _upload(acc, _video(clip, camp, acc["platform"]))
        url = url if str(url or "").startswith("http") else ""
        store.run("UPDATE posts SET status='posted', external_id=?, url=?, error='', updated_at=? WHERE id=?",
                  (str(ext), url, store.now(), post["id"]))
        return True
    except Exception as e:
        msg = str(e)[:500]
        tries = post["attempts"] + 1
        if "quota" in msg.lower() or "uploadLimitExceeded" in msg:
            when = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=random.randint(8, 40), second=0)
            store.run("UPDATE posts SET status='queued', attempts=attempts-1, scheduled_at=?, error=?, updated_at=? WHERE id=?",
                      (when.strftime(FMT), "YouTube má na dnes minutý limit, pôjde zajtra.", store.now(), post["id"]))
        elif tries >= MAX_TRIES:
            store.run("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?", (msg, store.now(), post["id"]))
        else:
            when = datetime.now() + timedelta(minutes=30 * tries)
            store.run("UPDATE posts SET status='queued', scheduled_at=?, error=?, updated_at=? WHERE id=?",
                      (when.strftime(FMT), msg, store.now(), post["id"]))
        return False


def recover():
    """Po reštarte: čo ostalo v stave „zverejňuje sa“, vráti do radu (o 10 minút, nech sa nezdvojí rozbehnuté)."""
    when = (datetime.now() + timedelta(minutes=10)).strftime(FMT)
    store.run("UPDATE posts SET status='queued', scheduled_at=MAX(scheduled_at, ?) WHERE status='posting'", (when,))
