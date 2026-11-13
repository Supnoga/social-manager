"""Nočná výroba a šetrenie miesta na disku.

- Výroba ide len v nočnom okne (nastavenie night = {"on": true, "from": 22, "to": 8}).
- Mac počas okna (a 2 h pred ním) nezaspí, keď je na nabíjačke a appka má čo robiť (macOS caffeinate).
  Zatvorené veko bez monitora uspí Mac vždy, to sa obísť nedá.
- Video na schválenie sa hneď nahrá na YouTube ako SÚKROMNÉ (nikto ho nevidí). V appke ostane len malá
  náhľadová kópia na pozretie v Kontrole. Po schválení sa video na YouTube len prepne na verejné
  (v čase podľa plánu, YouTube to urobí sám aj keď Mac spí). Po vrátení na úpravu sa z YouTube zmaže.
- Upratovanie: plné video sa zmaže, keď je bezpečne na YouTube; náhľad po schválení; staré pomocné súbory.
"""
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from . import db

DEFAULT = {"on": True, "from": 22, "to": 8}
PREVIEW_DIR = db.MEDIA_DIR / "previews"
STATE = {"awake": False, "freed_mb": 0.0, "last_clean": "", "error": ""}
_caff = None
_lock = threading.Lock()
BUSY = lambda: False  # main.py sem dá: beží teraz nejaká dlhá úloha (ručná výroba)?


def cfg():
    c = dict(DEFAULT)
    c.update(db.get_setting("night", {}) or {})
    return c


def _in_window(h, a, b):
    return (a <= h < b) if a < b else (h >= a or h < b)


def in_window(now=None):
    """Smie teraz bežať výroba? Pri vypnutom nočnom režime vždy áno."""
    c = cfg()
    if not c.get("on"):
        return True
    h = (now or datetime.now()).hour
    return _in_window(h, int(c["from"]) % 24, int(c["to"]) % 24)


def _awake_hours(now=None):
    """Okno, kedy Mac drží hore: 2 h pred nočným oknom až do jeho konca."""
    c = cfg()
    h = (now or datetime.now()).hour
    return _in_window(h, (int(c["from"]) - 2) % 24, int(c["to"]) % 24)


def on_power():
    if sys.platform != "darwin":
        return False
    try:
        return "AC Power" in subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return False


def keep_awake(want):
    """Zapne/vypne zákaz spánku (len Mac). -i nečinnosť, -s systém na nabíjačke; obrazovka môže zhasnúť."""
    global _caff
    with _lock:
        alive = _caff is not None and _caff.poll() is None
        if want and not alive and sys.platform == "darwin":
            try:
                _caff = subprocess.Popen(["caffeinate", "-i", "-s", "-w", str(os.getpid())])
            except Exception as e:
                STATE["error"] = f"caffeinate: {e}"
        elif not want and alive:
            _caff.terminate()
            _caff = None
        STATE["awake"] = bool(_caff is not None and _caff.poll() is None)


def has_work():
    auto = db.get_setting("auto_produce", {}) or {}
    pending = db.one("""SELECT COUNT(*) n FROM posts p JOIN accounts a ON a.id=p.account_id
                        WHERE (p.status='review' AND a.platform='youtube' AND COALESCE(p.stash_id,'')='')
                           OR (p.status='queued' AND COALESCE(p.stash_id,'')!='')""")["n"]
    return bool(auto) or pending > 0


def awake_tick(busy=False):
    """Volá sa pravidelne: Mac drží hore počas výroby/nahrávania alebo v nočnom okne s prácou."""
    try:
        busy = busy or BUSY()
    except Exception:
        pass
    c = cfg()
    # nočný režim: drž hore 2 h pred oknom až do konca; výroba nonstop (nočný režim vypnutý): drž hore stále, keď je čo robiť
    want = busy or ((not c.get("on") or _awake_hours()) and has_work() and on_power())
    keep_awake(bool(want))


# ---------------- náhľady a upratovanie ----------------
def make_preview(src):
    """Malá kópia na pozretie v Kontrole (540p, nízky bitrate). Vráti cestu alebo ''."""
    from . import media
    ff = media.ffmpeg()
    if not ff or not src or not Path(src).exists():
        return ""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    out = PREVIEW_DIR / (Path(src).stem + "_nahlad.mp4")
    try:
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(src),
                        "-vf", "scale='if(gt(iw,ih),-2,540)':'if(gt(iw,ih),540,-2)'",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "32", "-c:a", "aac", "-b:a", "64k",
                        "-movflags", "+faststart", str(out)], check=True, timeout=1800)
        return str(out)
    except Exception as e:
        STATE["error"] = f"náhľad: {e}"
        out.unlink(missing_ok=True)
        return ""


def _free(path):
    try:
        p = Path(path)
        if p.exists() and str(p.resolve()).startswith(str(db.DATA_DIR.resolve())):
            STATE["freed_mb"] += p.stat().st_size / 1e6
            p.unlink()
    except Exception:
        pass


def video_safe_on_youtube(vid):
    """Všetky zverejnenia videa sú na YouTube (hotové alebo súkromne odložené) a iná sieť súbor nepotrebuje."""
    rows = db.q("""SELECT p.status, COALESCE(p.stash_id,'') stash, a.platform FROM posts p JOIN accounts a ON a.id=p.account_id
                   WHERE p.video_id=?""", (vid,))
    if not rows:
        return False
    for r in rows:
        if r["status"] == "done":
            continue
        if r["platform"] == "youtube" and r["stash"] and r["status"] in ("review", "queued", "uploading"):
            continue
        return False
    return True


def clean():
    """Zmaže, čo už netreba. Bezpečné spustiť kedykoľvek."""
    if not (db.get_setting("night", {}) or {}).get("clean", True):
        return
    for v in db.q("SELECT id, file_path, COALESCE(preview_path,'') preview, COALESCE(removed,0) removed FROM videos"):
        if not v["removed"] and v["file_path"] and Path(v["file_path"]).exists() and video_safe_on_youtube(v["id"]):
            in_review = db.one("SELECT 1 FROM posts WHERE video_id=? AND status='review'", (v["id"],))
            if in_review and not v["preview"]:
                pv = make_preview(v["file_path"])
                if not pv:
                    continue  # bez náhľadu nemaž, Oliver by nemal čo pozrieť
                db.run("UPDATE videos SET preview_path=? WHERE id=?", (pv, v["id"]))
            _free(v["file_path"])
            _free(os.path.splitext(v["file_path"])[0] + ".jpg")
            db.run("UPDATE videos SET removed=1 WHERE id=?", (v["id"],))
        if v["preview"] and not db.one("SELECT 1 FROM posts WHERE video_id=? AND status='review'", (v["id"],)):
            _free(v["preview"])
            db.run("UPDATE videos SET preview_path='' WHERE id=?", (v["id"],))
    # pomocné súbory, ktoré sa dajú kedykoľvek vyrobiť znova
    old = time.time() - 3 * 86400
    for d in (db.MEDIA_DIR / "anim",):
        if d.exists():
            for f in d.iterdir():
                try:
                    if f.is_file() and f.stat().st_mtime < old:
                        _free(f)
                except Exception:
                    pass
    # hlas videí, ktoré už sú celé na YouTube a nečakajú na schválenie
    for s in db.q("""SELECT s.id, s.voice_path FROM scripts s WHERE COALESCE(s.voice_path,'')!=''
                     AND EXISTS (SELECT 1 FROM videos v WHERE v.script_id=s.id)
                     AND NOT EXISTS (SELECT 1 FROM videos v WHERE v.script_id=s.id AND COALESCE(v.removed,0)=0)
                     AND NOT EXISTS (SELECT 1 FROM videos v JOIN posts p ON p.video_id=v.id WHERE v.script_id=s.id AND p.status!='done')"""):
        if Path(s["voice_path"]).exists() and Path(s["voice_path"]).stat().st_mtime < old:
            _free(s["voice_path"])
    STATE["last_clean"] = datetime.now().strftime("%d.%m. %H:%M")


def status():
    used = 0
    for root, _, files in os.walk(db.DATA_DIR):
        for f in files:
            try:
                used += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return dict(STATE, config=cfg(), in_window=in_window(), on_power=on_power(), data_mb=round(used / 1e6),
                freed_mb=round(STATE["freed_mb"]))
