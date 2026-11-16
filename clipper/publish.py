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
DISCLOSE = {"#ad", "#sponsored", "#advertisement", "#paidpartnership", "#paid", "#promo", "#partner", "#collab"}
MAX_HASH = 5       # viac hashtagov dosah znižuje a Instagram ich viac neberie


def _tags(camp, platform=None):
    """Povinné značky kampane: (označenie spolupráce, hashtagy, označenia účtov) tak, ako ich kampaň chce.
    Značka môže platiť len pre jednu sieť: „instagram:@sega youtube:@sega_west“."""
    found = []
    for net, t in re.findall(r"(?:\b(youtube|instagram|tiktok|facebook):)?([#@][\w.]+)", camp.get("tags") or "", re.I):
        if not net or platform is None or net.lower() == platform:
            found.append(t)
    found = list(dict.fromkeys(found))
    disc = [t for t in found if t.lower() in DISCLOSE]
    return disc, [t for t in found if t.startswith("#") and t not in disc], [t for t in found if t.startswith("@")]


def texts(clip, camp, platform):
    """Popis: text klipu (alebo presný text, ktorý kampaň predpisuje) a označenia účtov v prvom riadku,
    označenie spolupráce (#Ad) na vlastnom riadku ako prvý hashtag, za ním ostatné hashtagy."""
    title = re.sub(r"[<>]", "", (clip.get("title") or clip.get("hook") or "Clip")).strip()
    fixed = (camp.get("caption") or "").strip()
    disc, req, mentions = _tags(camp, platform)
    if fixed:                                     # kampaň chce presne svoj text: nič v ňom nemeniť
        body, own = fixed, []
        low = fixed.lower()
        disc = [t for t in disc if t.lower() not in low]
        req = [t for t in req if t.lower() not in low]
        mentions = [t for t in mentions if t.lower() not in low]
    else:
        body = re.sub(r"[<>]", "", (clip.get("caption") or title)).strip()
        own = re.findall(r"#\w+", body)
        body = re.sub(r"\s+", " ", re.sub(r"#\w+", "", body)).strip() or title
    have = {t.lower() for t in disc + req}
    room = MAX_HASH - len(disc) - len(req) - (1 if platform == "youtube" else 0)
    if disc:                                      # značkové kampane: za #Ad najviac 3 ďalšie hashtagy
        room = min(room, 3 - len(req) - (1 if platform == "youtube" else 0))
    extra = [t for t in dict.fromkeys(own) if t.lower() not in have][:max(0, min(3, room))]
    first = (body + (" " + " ".join(mentions) if mentions else "")).strip()
    tail = " ".join(disc + req + extra + (["#shorts"] if platform == "youtube" else []))
    text = (first + ("\n" + tail if tail else "")).strip()
    if platform == "youtube":
        t = title[:92]
        if req and len(t) + len(" ".join(req)) < 96:
            t = (t + " " + " ".join(req)).strip()
        return t, text
    return title, text[:2100]


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
DEFAULT_BATCHES = ["14:00", "18:00", "21:30"]    # slovenský čas; v Amerike je vtedy ráno, obed a popoludnie
ACTIVE = "('queued','posting','posted')"


def batches():
    """Časy dávok cez deň (minúty od polnoci). Všetky účty zverejňujú v tých istých časoch, aby odkazy prišli naraz
    a dali sa do kampane vložiť včas (Whop berie odkaz len 30 minút od zverejnenia)."""
    out = set()
    for x in store.get("batches", None) or DEFAULT_BATCHES:
        m = re.match(r"^\s*(\d{1,2})[:.](\d{2})\s*$", str(x))
        if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
            out.add(int(m.group(1)) * 60 + int(m.group(2)))
    return sorted(out)[:6] or [840, 1080, 1290]


def day_cap(account_id, per_day, day):
    """Koľko klipov smie účet v daný deň zverejniť. Nový účet sa rozbieha pomaly (1, 1, 2, 2, potom plný počet),
    lebo siete nový účet s veľa videami naraz berú ako spam a nepustia ho k ľuďom."""
    lim = min(max(1, int(per_day)), len(batches()))
    if not store.get("warmup", True):
        return lim
    first = store.one(f"SELECT MIN(scheduled_at) m FROM posts WHERE account_id=? AND status IN {ACTIVE}", (account_id,))["m"]
    age = (day - datetime.strptime(first[:10], "%Y-%m-%d").date()).days if first else 0
    return min(lim, 1 if age < 2 else 2 if age < 4 else lim)


def next_slot(account_id, per_day):
    """Najbližšia voľná dávka pre účet: v jednej dávke jeden klip, denne najviac toľko, koľko účet smie."""
    now = datetime.now() + timedelta(minutes=4)
    day0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    taken = [datetime.strptime(r["scheduled_at"], FMT) for r in
             store.q(f"SELECT scheduled_at FROM posts WHERE account_id=? AND status IN {ACTIVE} AND scheduled_at>=?",
                     (account_id, day0.strftime(FMT)))]
    for d in range(120):
        day = day0 + timedelta(days=d)
        mine = [t for t in taken if t.date() == day.date()]
        if len(mine) >= day_cap(account_id, per_day, day.date()):
            continue
        for b in batches():
            t = day + timedelta(minutes=b)
            if t >= now and not any(abs((x - t).total_seconds()) < 1500 for x in mine):
                return (t + timedelta(seconds=random.randint(0, 300))).strftime(FMT)
    return (now + timedelta(days=120)).strftime(FMT)


def batch_now():
    """Zverejní dávku hneď: z každého účtu jeho najbližší naplánovaný klip. Vráti počet."""
    n = 0
    for r in store.q("SELECT account_id, MIN(scheduled_at) m FROM posts WHERE status='queued' GROUP BY account_id"):
        p = store.one("SELECT id FROM posts WHERE status='queued' AND account_id=? AND scheduled_at=? LIMIT 1", (r["account_id"], r["m"]))
        if p:
            store.run("UPDATE posts SET scheduled_at=? WHERE id=?", (store.now(), p["id"]))
            n += 1
    return n


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
        store.run("UPDATE posts SET status='posted', external_id=?, url=?, error='', updated_at=?, posted_at=? WHERE id=?",
                  (str(ext), url, store.now(), store.now(), post["id"]))
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
