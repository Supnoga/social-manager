"""Zábery do videí zadarmo: tvoje vlastné zábery -> Pexels -> Pixabay -> fotky -> AI obrázok (Cloudflare, zadarmo denne).

Všetko stiahnuté sa ukladá lokálne s tagmi, takže sa to isté nesťahuje znova. Výber bez AI (skóre podľa tagov).
Licencie: Pexels a Pixabay dovoľujú komerčné použitie bez uvedenia autora; zábery s logami/osobami
nepoužívať tak, akoby značka alebo osoba odporúčala produkt.
"""
import base64
import datetime
import hashlib
import json
import random
import re
import time
from pathlib import Path

import httpx

from . import db

DIR = db.DATA_DIR / "footage"
OWN = DIR / "moje"          # sem si Oliver hodí vlastné zábery (tagy z názvu súboru)
MUSIC = DIR / "hudba"       # hudba do pozadia (mp3), voliteľné
for d in (DIR, OWN, MUSIC):
    d.mkdir(parents=True, exist_ok=True)

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
STOP = {"the", "a", "an", "of", "and", "in", "on", "with", "at", "to", "for", "video", "clip"}


def _words(t):
    return {w for w in re.findall(r"[a-z0-9]+", (t or "").lower()) if w not in STOP and len(w) > 1}


def _setting(k):
    return (db.get_setting(k, "") or "").strip()


def status():
    return {"pexels": bool(_setting("pexels_key")), "pixabay": bool(_setting("pixabay_key")),
            "ai": bool(_setting("cf_account") and _setting("cf_ai_token")) and bool(db.get_setting("ai_images", True)),
            "own": sum(1 for f in OWN.rglob("*") if f.suffix.lower() in VIDEO_EXT | IMG_EXT),
            "music": sum(1 for f in MUSIC.rglob("*") if f.suffix.lower() in {".mp3", ".m4a", ".wav"}),
            "own_dir": str(OWN), "music_dir": str(MUSIC), "library": db.one("SELECT COUNT(*) n FROM footage")["n"]}


# ---------- lokálna knižnica ----------
def _index_own():
    have = {r["path"] for r in db.q("SELECT path FROM footage WHERE source='own'")}
    for f in OWN.rglob("*"):
        ext = f.suffix.lower()
        if str(f) in have or ext not in VIDEO_EXT | IMG_EXT:
            continue
        tags = " ".join(_words(f.stem.replace("_", " ").replace("-", " ") + " " + f.parent.name))
        db.run("INSERT INTO footage(source, source_id, path, tags, kind) VALUES('own',?,?,?,?)",
               (f.name, str(f), tags, "video" if ext in VIDEO_EXT else "photo"))


def _local(q, exclude):
    want = _words(q)
    best, score = None, 0
    for r in db.q("SELECT * FROM footage"):
        if r["id"] in exclude or not Path(r["path"]).exists():
            continue
        hit = len(want & set(r["tags"].split()))
        if not hit:
            continue
        s = hit * 3 + (4 if r["source"] == "own" else 0) + (1 if r["kind"] == "video" else 0) + (1 if r["h"] >= r["w"] else 0) - r["used"] * 0.5
        if s > score and hit >= max(1, len(want) // 2):
            best, score = r, s
    return best


def _save(source, sid, url, tags, kind, w, h, dur, page, ext):
    path = DIR / source / f"{sid}{ext}"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for ch in r.iter_bytes(1 << 20):
                    f.write(ch)
    ex = db.one("SELECT id FROM footage WHERE source=? AND source_id=?", (source, str(sid)))
    if ex:
        return ex["id"]
    return db.run("INSERT INTO footage(source, source_id, path, tags, kind, w, h, dur, license_url) VALUES(?,?,?,?,?,?,?,?,?)",
                  (source, str(sid), str(path), " ".join(_words(tags)), kind, w, h, dur, page))


def _cached_get(url, params, headers=None):
    key = hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    c = db.one("SELECT response, created_at FROM ai_cache WHERE hash=?", ("fs" + key,))
    if c and c["created_at"] > (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"):
        return json.loads(c["response"])
    r = httpx.get(url, params=params, headers=headers or {}, timeout=30)
    r.raise_for_status()
    data = r.json()
    db.run("INSERT OR REPLACE INTO ai_cache(hash, response, created_at) VALUES(?,?,datetime('now','localtime'))",
           ("fs" + key, json.dumps(data)))
    return data


# ---------- online zdroje ----------
def _pexels_video(q, exclude_src):
    key = _setting("pexels_key")
    if not key:
        return None
    d = _cached_get("https://api.pexels.com/videos/search", {"query": q, "orientation": "portrait", "per_page": 15},
                    {"Authorization": key})
    for v in d.get("videos", []):
        if f"pexels:{v['id']}" in exclude_src or v.get("duration", 0) < 3:
            continue
        files = sorted([f for f in v["video_files"] if f.get("height") and f["height"] >= 1080 and f.get("file_type") == "video/mp4"],
                       key=lambda f: f["height"])
        if not files:
            continue
        f = files[0]
        tags = q + " " + re.sub(r"[-/]", " ", v.get("url", ""))
        return _save("pexels", v["id"], f["link"], tags, "video", f["width"], f["height"], v["duration"], v["url"], ".mp4")
    return None


def _pixabay_video(q, exclude_src):
    key = _setting("pixabay_key")
    if not key:
        return None
    d = _cached_get("https://pixabay.com/api/videos/", {"key": key, "q": q[:100], "per_page": 20, "safesearch": "true"})
    for v in d.get("hits", []):
        if f"pixabay:{v['id']}" in exclude_src or v.get("duration", 0) < 3:
            continue
        cand = [x for x in v["videos"].values() if x.get("url") and x.get("height", 0) >= 1080] or \
               [x for x in v["videos"].values() if x.get("url")]
        if not cand:
            continue
        f = min(cand, key=lambda x: x.get("height", 0))
        return _save("pixabay", v["id"], f["url"], q + " " + v.get("tags", ""), "video", f.get("width", 0), f.get("height", 0),
                     v["duration"], v.get("pageURL", ""), ".mp4")
    return None


def _pexels_photo(q, exclude_src):
    key = _setting("pexels_key")
    if not key:
        return None
    d = _cached_get("https://api.pexels.com/v1/search", {"query": q, "orientation": "portrait", "per_page": 15},
                    {"Authorization": key})
    for p in d.get("photos", []):
        if f"pexels-photo:{p['id']}" in exclude_src:
            continue
        return _save("pexels-photo", p["id"], p["src"]["portrait"], q + " " + (p.get("alt") or ""), "photo",
                     p["width"], p["height"], 0, p["url"], ".jpg")
    return None


def _pixabay_photo(q, exclude_src):
    key = _setting("pixabay_key")
    if not key:
        return None
    d = _cached_get("https://pixabay.com/api/", {"key": key, "q": q[:100], "orientation": "vertical", "per_page": 20,
                                                 "image_type": "photo", "safesearch": "true"})
    for p in d.get("hits", []):
        if f"pixabay-photo:{p['id']}" in exclude_src:
            continue
        return _save("pixabay-photo", p["id"], p["largeImageURL"], q + " " + p.get("tags", ""), "photo",
                     p["imageWidth"], p["imageHeight"], 0, p.get("pageURL", ""), ".jpg")
    return None


def _ai_image(q, style=""):
    acc, tok = _setting("cf_account"), _setting("cf_ai_token")
    if not (acc and tok) or not db.get_setting("ai_images", True):
        return None
    prompt = f"vertical photo, {q}, cinematic, natural light, high detail, no text, no logo{', ' + style if style else ''}"
    r = httpx.post(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell",
                   headers={"Authorization": f"Bearer {tok}"}, json={"prompt": prompt, "steps": 4,
                                                                     "width": 768, "height": 1344}, timeout=120)
    if r.status_code != 200:
        return None
    img = r.json().get("result", {}).get("image")
    if not img:
        return None
    sid = hashlib.sha1((prompt + str(time.time())).encode()).hexdigest()[:12]
    path = DIR / "ai" / f"{sid}.jpg"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(base64.b64decode(img))
    return db.run("INSERT INTO footage(source, source_id, path, tags, kind, w, h) VALUES('ai',?,?,?,?,?,?)",
                  (sid, str(path), " ".join(_words(q)), "photo", 768, 1344))


def find(q, alt="", exclude=(), online=True):
    """Nájde jeden záber pre hľadaný výraz. Vráti riadok z tabuľky footage alebo None."""
    _index_own()
    exclude = set(exclude)
    ex_src = {f"{r['source']}:{r['source_id']}" for r in db.q("SELECT id, source, source_id FROM footage") if r["id"] in exclude}
    for query in [q, alt]:
        if not query:
            continue
        r = _local(query, exclude)
        if r and (r["source"] == "own" or random.random() < 0.6):
            return r
        if not online:
            continue
        for fn in (_pexels_video, _pixabay_video):
            try:
                fid = fn(query, ex_src)
            except Exception:
                fid = None
            if fid and fid not in exclude:
                return db.one("SELECT * FROM footage WHERE id=?", (fid,))
        if r:
            return r
    for query in [q, alt]:
        for fn in (_pexels_photo, _pixabay_photo):
            try:
                fid = fn(query, ex_src) if query else None
            except Exception:
                fid = None
            if fid and fid not in exclude:
                return db.one("SELECT * FROM footage WHERE id=?", (fid,))
    try:
        fid = _ai_image(q or alt)
        if fid:
            return db.one("SELECT * FROM footage WHERE id=?", (fid,))
    except Exception:
        pass
    return None


def pick_for_scenes(scenes, shots_per_scene=None, seed=None):
    """Pre každú scénu vyberie zábery (2-3 na scénu). Výsledok sa uloží k scenáru a použije pre všetky jazyky."""
    rnd = random.Random(seed)
    used, out = set(), []
    for i, sc in enumerate(scenes):
        q = sc.get("q") or sc.get("visual", "")
        q = q if isinstance(q, str) else (q or {}).get("q", "")
        q = " ".join(list(_words(q))[:6]) if len(q) > 60 else q
        n = shots_per_scene or 2
        ids = []
        for _ in range(n):
            r = find(q, sc.get("alt", ""), used)
            if not r:
                break
            used.add(r["id"])
            ids.append(r["id"])
            db.run("UPDATE footage SET used=used+1 WHERE id=?", (r["id"],))
        rnd.shuffle(ids)
        out.append(ids)
    return out


def music_track(seed=None):
    tracks = [f for f in MUSIC.rglob("*") if f.suffix.lower() in {".mp3", ".m4a", ".wav"}]
    return str(random.Random(seed).choice(tracks)) if tracks else None
