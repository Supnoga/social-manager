"""Vzhľad účtov: profilová fotka, pozadie (banner) a popis (bio) hromadne pre viac účtov naraz.

- Popis sa napíše raz a do jazyka každého účtu ho preloží bezplatný prekladač (0 tokenov Claude).
- Obrázky sa orežú na presné rozmery každej siete.
- Samo sa zmení, kde to sieť cez oficiálne rozhranie dovolí: YouTube (popis + pozadie), Facebook (popis, titulná fotka,
  profilovka). Ostatné (Instagram, TikTok, LinkedIn, YouTube profilovka) appka pripraví na rýchle vloženie
  a povie, kde kliknúť.
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.parse

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile

from . import db, translate
from .platforms import meta, youtube
from .platforms.common import check, client, tokens

router = APIRouter()
DIR = db.DATA_DIR / "profiles"

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile_kits (project_id INTEGER PRIMARY KEY, avatar TEXT DEFAULT '', banner TEXT DEFAULT '',
  bio TEXT DEFAULT '', lang TEXT DEFAULT 'sk', updated_at TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS account_profiles (account_id INTEGER PRIMARY KEY, bio TEXT DEFAULT '', bio_src TEXT DEFAULT '',
  status TEXT DEFAULT '', note TEXT DEFAULT '', applied_at TEXT DEFAULT '');
"""
_ready = False

# limity popisu a rozmery obrázkov (2026)
BIO_MAX = {"youtube": 1000, "facebook": 255, "instagram": 150, "tiktok": 80, "linkedin": 2000}
AVATAR = (800, 800)
BANNER = {"youtube": (2560, 1440), "facebook": (1640, 624), "linkedin": (1584, 396)}
BANNER_ORG = (1128, 191)


def _db():
    global _ready
    if not _ready:
        with db._lock:
            db.con().executescript(SCHEMA)
            db.con().commit()
        _ready = True


def _now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _is_org(acc):
    return (acc.get("external_id") or "").startswith("urn:li:organization")


def _fit(src, size, out):
    """Oreže obrázok na presný pomer strán (stred) a zmenší na rozmer siete."""
    from PIL import Image, ImageOps
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("RGB")
    im = ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.5))
    im.save(out, "JPEG", quality=90, optimize=True)
    return out


def _cut(text, n):
    text = (text or "").strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(",.;:-–")
    return cut


def kit(pid):
    _db()
    k = db.one("SELECT * FROM profile_kits WHERE project_id=?", (pid,))
    if not k:
        p = db.one("SELECT source_lang FROM projects WHERE id=?", (pid,)) or {}
        k = {"project_id": pid, "avatar": "", "banner": "", "bio": "", "lang": p.get("source_lang") or "sk"}
    return k


def _accounts(pid):
    return db.q("SELECT * FROM accounts WHERE project_id=? ORDER BY platform, lang, name", (pid,))


def _files(acc, pid):
    """Cesty k pripraveným obrázkom pre účet."""
    d = DIR / str(pid) / "pripravene"
    out = {}
    if (d / "profilovka.jpg").exists():
        out["avatar"] = str(d / "profilovka.jpg")
    key = "linkedin-firma" if acc["platform"] == "linkedin" and _is_org(acc) else acc["platform"]
    f = d / f"pozadie-{key}.jpg"
    if f.exists():
        out["banner"] = str(f)
    return out


def _edit_link(acc):
    p, ext, name = acc["platform"], acc.get("external_id") or "", (acc.get("name") or "").lstrip("@")
    if p == "youtube":
        return f"https://studio.youtube.com/channel/{ext}/editing/profile"
    if p == "instagram":
        return "https://www.instagram.com/accounts/edit/"
    if p == "tiktok":
        return "https://www.tiktok.com/profile"
    if p == "facebook":
        return f"https://www.facebook.com/{ext}"
    if p == "linkedin":
        if _is_org(acc):
            return f"https://www.linkedin.com/company/{ext.split(':')[-1]}/admin/page-info/"
        return "https://www.linkedin.com/in/me/edit/intro/"
    return ""


def _manual_parts(acc, files, bio):
    """Čo musí Oliver kliknúť ručne (sieť zmenu cez rozhranie nedovolí)."""
    p = acc["platform"]
    parts = []
    if p == "youtube":
        if files.get("avatar"):
            parts.append("profilovka")
    elif p == "facebook":
        pass
    else:
        if files.get("avatar"):
            parts.append("profilovka")
        if files.get("banner"):
            parts.append("pozadie")
        if bio:
            parts.append("popis")
    return parts


# ---------- automatické zmeny ----------
def _yt_apply(acc, bio, banner):
    tok = youtube.access_token(acc)
    h = {"Authorization": f"Bearer {tok}"}
    with client(timeout=300) as c:
        r = check(c.get("https://www.googleapis.com/youtube/v3/channels", headers=h,
                        params={"part": "brandingSettings", "id": acc["external_id"]}), "YouTube kanál")
        items = r.json().get("items") or []
        if not items:
            raise RuntimeError("kanál sa nenašiel")
        bs = items[0].get("brandingSettings") or {}
        bs.setdefault("channel", {})
        if bio:
            bs["channel"]["description"] = bio
        if banner:
            with open(banner, "rb") as f:
                up = check(c.post("https://www.googleapis.com/upload/youtube/v3/channelBanners/insert",
                                  params={"uploadType": "media"}, headers={**h, "Content-Type": "image/jpeg"},
                                  content=f.read()), "YouTube pozadie")
            bs.setdefault("image", {})["bannerExternalUrl"] = up.json()["url"]
        r = c.put("https://www.googleapis.com/youtube/v3/channels", params={"part": "brandingSettings"}, headers=h,
                  json={"id": acc["external_id"], "brandingSettings": bs})
        if r.status_code == 403 and "insufficient" in r.text.lower():
            raise RuntimeError("chýba povolenie – pripoj kanál znova v Účtoch")
        check(r, "YouTube úprava kanála")


def _fb_apply(acc, bio, banner, avatar):
    t = tokens(acc)
    tok, page = t["page_token"], t["page_id"]
    done, failed = [], []
    with client(timeout=300) as c:
        if bio:
            r = c.post(meta.G(page), data={"access_token": tok, "about": bio})
            (done if r.status_code == 200 else failed).append("popis")
        if banner:
            try:
                with open(banner, "rb") as f:
                    ph = check(c.post(meta.G(f"{page}/photos"), data={"access_token": tok, "published": "false"},
                                      files={"source": ("cover.jpg", f, "image/jpeg")}), "Facebook foto").json()
                r = c.post(meta.G(page), data={"access_token": tok, "cover": ph["id"]})
                (done if r.status_code == 200 else failed).append("pozadie")
            except Exception:
                failed.append("pozadie")
        if avatar:
            try:
                with open(avatar, "rb") as f:
                    r = c.post(meta.G(f"{page}/picture"), data={"access_token": tok},
                               files={"source": ("avatar.jpg", f, "image/jpeg")})
                (done if r.status_code == 200 else failed).append("profilovka")
            except Exception:
                failed.append("profilovka")
    return done, failed


# ---------- API ----------
@router.get("/api/profiles/{pid}")
def get_profiles(pid: int):
    _db()
    k = kit(pid)
    rows = []
    for a in _accounts(pid):
        ap = db.one("SELECT * FROM account_profiles WHERE account_id=?", (a["id"],)) or {}
        files = _files(a, pid)
        rows.append({"id": a["id"], "platform": a["platform"], "name": a["name"], "lang": a["lang"], "org": _is_org(a),
                     "bio": ap.get("bio", ""), "max": BIO_MAX.get(a["platform"], 500), "status": ap.get("status", ""),
                     "note": ap.get("note", ""), "applied_at": ap.get("applied_at", ""), "files": files,
                     "link": _edit_link(a), "manual": _manual_parts(a, files, ap.get("bio", ""))})
    return {"kit": {**k, "avatar_ok": bool(k["avatar"] and os.path.exists(k["avatar"])),
                    "banner_ok": bool(k["banner"] and os.path.exists(k["banner"]))},
            "accounts": rows, "mt": translate.any_enabled(), "folder": str(DIR / str(pid) / "pripravene")}


@router.get("/api/profiles/{pid}/img/{which}")
def img(pid: int, which: str):
    from fastapi.responses import FileResponse
    k = kit(pid)
    path = DIR / str(pid) / "pripravene" / which if which not in ("avatar", "banner") else k.get(which)
    if not path or not os.path.exists(path) or ".." in which:
        raise HTTPException(404)
    return FileResponse(path)


@router.post("/api/profiles/{pid}/kit")
async def save_kit(pid: int, bio: str = Form(""), lang: str = Form(""), avatar: UploadFile = File(None),
                   banner: UploadFile = File(None)):
    """Uloží spoločnú profilovku, pozadie a popis projektu a pripraví obrázky pre každú sieť."""
    _db()
    k = kit(pid)
    d = DIR / str(pid)
    d.mkdir(parents=True, exist_ok=True)
    for name, up in (("avatar", avatar), ("banner", banner)):
        if up is not None and up.filename:
            ext = os.path.splitext(up.filename)[1].lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                raise HTTPException(400, "Obrázok musí byť JPG, PNG alebo WEBP")
            path = d / f"{name}{ext}"
            with open(path, "wb") as f:
                shutil.copyfileobj(up.file, f)
            k[name] = str(path)
    k["bio"], k["lang"] = bio, lang or k["lang"]
    db.run("""INSERT OR REPLACE INTO profile_kits(project_id, avatar, banner, bio, lang, updated_at) VALUES(?,?,?,?,?,?)""",
           (pid, k["avatar"], k["banner"], k["bio"], k["lang"], _now()))
    _prepare_images(pid, k)
    return {"ok": True}


def _prepare_images(pid, k):
    out = DIR / str(pid) / "pripravene"
    out.mkdir(parents=True, exist_ok=True)
    if k.get("avatar") and os.path.exists(k["avatar"]):
        _fit(k["avatar"], AVATAR, out / "profilovka.jpg")
    if k.get("banner") and os.path.exists(k["banner"]):
        for plat, size in BANNER.items():
            _fit(k["banner"], size, out / f"pozadie-{plat}.jpg")
        _fit(k["banner"], BANNER_ORG, out / "pozadie-linkedin-firma.jpg")


@router.post("/api/profiles/{pid}/texts")
def make_texts(pid: int, data: dict = Body(default={})):
    """Popis do jazyka každého účtu cez bezplatný prekladač. Kde chýba prekladač, nechá originál a povie to."""
    _db()
    k = kit(pid)
    if not (k.get("bio") or "").strip():
        raise HTTPException(400, "Najprv napíš popis")
    ids = set(data.get("account_ids") or [])
    accs = [a for a in _accounts(pid) if not ids or a["id"] in ids]
    proj = db.one("SELECT glossary FROM projects WHERE id=?", (pid,)) or {}
    import re
    gloss = [g.strip() for g in re.split(r"[\n,;]", proj.get("glossary") or "") if g.strip()]
    cache, errors, done = {}, [], 0
    for a in accs:
        lang = a["lang"] or k["lang"]
        if lang not in cache:
            if lang == k["lang"]:
                cache[lang] = k["bio"]
            else:
                try:
                    cache[lang] = translate.translate_texts([k["bio"]], k["lang"], lang, gloss)[0][0]
                except Exception as e:
                    cache[lang] = None
                    errors.append(f"{lang}: {str(e)[:80]}")
        txt = cache[lang]
        if txt is None:
            continue
        mx = BIO_MAX.get(a["platform"], 500)
        bio = _cut(txt, mx)
        note = f"skrátené na {mx} znakov" if len(bio) < len(txt.strip()) else ""
        db.run("""INSERT INTO account_profiles(account_id, bio, bio_src, status, note) VALUES(?,?,?,'ready',?)
                  ON CONFLICT(account_id) DO UPDATE SET bio=excluded.bio, bio_src=excluded.bio_src, status='ready', note=excluded.note""",
               (a["id"], bio, k["bio"], note))
        done += 1
    return {"done": done, "errors": errors}


@router.put("/api/profiles/account/{aid}")
def set_bio(aid: int, data: dict = Body(...)):
    _db()
    db.run("""INSERT INTO account_profiles(account_id, bio, status) VALUES(?,?,'ready')
              ON CONFLICT(account_id) DO UPDATE SET bio=excluded.bio, status='ready'""", (aid, data.get("bio", "")))
    return {"ok": True}


@router.post("/api/profiles/{pid}/apply")
def apply(pid: int, data: dict = Body(default={})):
    """Zmení, čo sieť dovolí. Vráti, čo je hotové a čo treba kliknúť ručne."""
    _db()
    ids = set(data.get("account_ids") or [])
    what = set(data.get("what") or ["bio", "avatar", "banner"])
    auto, manual, errors = 0, [], []
    for a in _accounts(pid):
        if ids and a["id"] not in ids:
            continue
        ap = db.one("SELECT * FROM account_profiles WHERE account_id=?", (a["id"],)) or {}
        bio = ap.get("bio", "") if "bio" in what else ""
        files = _files(a, pid)
        avatar = files.get("avatar") if "avatar" in what else None
        banner = files.get("banner") if "banner" in what else None
        done, left = [], []
        try:
            if a["platform"] == "youtube":
                if bio or banner:
                    _yt_apply(a, bio, banner)
                    done += (["popis"] if bio else []) + (["pozadie"] if banner else [])
                if avatar:
                    left.append("profilovka")
            elif a["platform"] == "facebook":
                d, f = _fb_apply(a, bio, banner, avatar)
                done += d
                left += f
            else:
                left += (["profilovka"] if avatar else []) + (["pozadie"] if banner and a["platform"] == "linkedin" else []) + \
                        (["popis"] if bio else [])
        except Exception as e:
            errors.append(f"{a['name']}: {str(e)[:120]}")
            left += (["popis"] if bio else []) + (["pozadie"] if banner else []) + (["profilovka"] if avatar else [])
            done = []
        st = "done" if done and not left else "manual" if left else ap.get("status", "")
        note = ("Hotovo: " + ", ".join(done) if done else "") + (" · Ručne: " + ", ".join(left) if left else "")
        db.run("""INSERT INTO account_profiles(account_id, status, note, applied_at) VALUES(?,?,?,?)
                  ON CONFLICT(account_id) DO UPDATE SET status=excluded.status, note=excluded.note, applied_at=excluded.applied_at""",
               (a["id"], st, note.strip(" ·"), _now()))
        if done:
            auto += 1
        if left:
            manual.append(a["name"])
    return {"auto": auto, "manual": manual, "errors": errors}


@router.post("/api/profiles/{pid}/manual-done/{aid}")
def manual_done(pid: int, aid: int):
    _db()
    db.run("UPDATE account_profiles SET status='done', note='Hotovo (ručne)', applied_at=? WHERE account_id=?", (_now(), aid))
    return {"ok": True}


@router.post("/api/profiles/{pid}/open")
def open_folder(pid: int):
    d = DIR / str(pid) / "pripravene"
    d.mkdir(parents=True, exist_ok=True)
    cmd = ["open", str(d)] if sys.platform == "darwin" else ["explorer", str(d)] if os.name == "nt" else ["xdg-open", str(d)]
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass
    return {"path": str(d)}
