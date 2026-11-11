"""Obrázky a súbory značky v dizajne projektu: logá, fotky, videá, fonty, PDF brand manuál.

Bez AI (0 tokenov):
- Logo: samo sa dá do rohu každého videa a na koniec videa, farby z loga sa použijú vo videách,
  z loga sa pripraví profilovka účtov (ak tam ešte nie je iná).
- Fotky a videá značky: idú do záberov vo videách tohto projektu (prednostne pred zábermi z internetu).
- Font: titulky, texty a animácie vo videách sú vo fonte značky (ak font má všetky písmená jazyka,
  inak sa pre ten jazyk použije bežný font).
- PDF brand manuál a .md: text sa pridá do dizajnu (rovnako ako MD dizajn), farby sa z neho vytiahnu.
Formáty: PNG, JPG, WebP, GIF, BMP, TIFF, HEIC/HEIF (iPhone), AVIF, SVG, MP4/MOV/M4V/WebM, TTF/OTF/WOFF/WOFF2, PDF, MD/TXT.
"""
import colorsys
import datetime as dt
import json
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import FileResponse

from . import db

router = APIRouter()
DIR = db.DATA_DIR / "brand"

SCHEMA = """
CREATE TABLE IF NOT EXISTS brand_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, kind TEXT, name TEXT,
  path TEXT, orig TEXT DEFAULT '', w INTEGER DEFAULT 0, h INTEGER DEFAULT 0, dur REAL DEFAULT 0, note TEXT DEFAULT '',
  footage_id INTEGER DEFAULT 0, main INTEGER DEFAULT 0, created_at TEXT DEFAULT '');
"""
_ready = False

IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
CONVERT = {".heic", ".heif", ".avif"}
VIDEO = {".mp4", ".mov", ".m4v", ".webm"}
FONT = {".ttf", ".otf", ".woff", ".woff2"}
TEXT = {".md", ".markdown", ".txt"}
DEFAULT_OPTS = {"logo_corner": True, "logo_end": True, "photos_often": True}
_local = threading.local()


def _db():
    global _ready
    if not _ready:
        with db._lock:
            db.con().executescript(SCHEMA)
            db.con().commit()
        _ready = True


def _now():
    return dt.datetime.now().isoformat(timespec="seconds")


def opts(pid):
    o = dict(DEFAULT_OPTS)
    o.update(db.get_setting(f"brand_opts_{pid}", {}) or {})
    return o


def assets(pid, kind=None):
    _db()
    sql, args = "SELECT * FROM brand_assets WHERE project_id=?", [pid]
    if kind:
        sql += " AND kind=?"
        args.append(kind)
    return [a for a in db.q(sql + " ORDER BY main DESC, id", args) if Path(a["path"]).exists()]


def main_asset(pid, kind):
    a = assets(pid, kind)
    return a[0] if a else None


# ---------- obrázky ----------
def _convert_other(src, out_jpg):
    """HEIC/AVIF: na Macu cez vstavaný nástroj sips, inak cez Pillow (ak to vie)."""
    if shutil.which("sips"):
        r = subprocess.run(["sips", "-s", "format", "jpeg", str(src), "--out", str(out_jpg)],
                           capture_output=True, stdin=subprocess.DEVNULL)
        if r.returncode == 0 and Path(out_jpg).exists():
            return True
    try:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:
            pass
        from PIL import Image
        Image.open(src).convert("RGB").save(out_jpg, "JPEG", quality=92)
        return True
    except Exception:
        return False


def _svg_to_png(src, out_png):
    """Záloha, keď SVG neprevedie prehliadač: Mac Quick Look, potom Chromium (ak je stiahnuté)."""
    if shutil.which("qlmanage"):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["qlmanage", "-t", "-s", "1600", "-o", tmp, str(src)], capture_output=True, stdin=subprocess.DEVNULL)
            got = list(Path(tmp).glob("*.png"))
            if got:
                shutil.move(str(got[0]), out_png)
                return True
    try:
        from . import anim
        if anim.available():
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                b = pw.chromium.launch()
                try:
                    pg = b.new_page(viewport={"width": 1600, "height": 1600})
                    pg.goto(Path(src).resolve().as_uri())
                    pg.locator("svg").first.screenshot(path=str(out_png), omit_background=True)
                finally:
                    b.close()
            return Path(out_png).exists()
    except Exception:
        pass
    return False


def _looks_like_logo(im, name):
    if "logo" in name.lower() or "znak" in name.lower():
        return True
    if im.mode in ("RGBA", "LA", "P"):
        a = im.convert("RGBA").getchannel("A")
        small = a.resize((64, 64))
        transparent = sum(1 for v in small.getdata() if v < 30)
        return transparent > 64 * 64 * 0.15
    return False


def _store_image(pid, src, name, d, orig=""):
    from PIL import Image, ImageOps
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)
    is_logo = bool(orig) or _looks_like_logo(im, name)
    stem = re.sub(r"[^\w\-]+", "_", Path(name).stem)[:60] or "obrazok"
    if is_logo:
        im = im.convert("RGBA")
        box = im.getchannel("A").getbbox()
        if box:
            im = im.crop(box)
        im.thumbnail((2400, 2400))
        out = d / f"{stem}.png"
        im.save(out, "PNG", optimize=True)
    else:
        im = im.convert("RGB")
        im.thumbnail((3840, 3840))
        out = d / f"{stem}.jpg"
        im.save(out, "JPEG", quality=92)
    return out, ("logo" if is_logo else "photo"), im.size


def _lum(rgb):
    r, g, b = rgb[:3]
    return 0.299 * r + 0.587 * g + 0.114 * b


def logo_colors(path, n=3):
    """Výrazné farby z loga (bez bielej, čiernej a sivej)."""
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    im.thumbnail((160, 160))
    px = [p[:3] for p in im.getdata() if p[3] > 128]
    if not px:
        return []
    counts = {}
    for r, g, b in px:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s < 0.3 or l < 0.12 or l > 0.92:
            continue
        key = (r // 24, g // 24, b // 24)
        c = counts.setdefault(key, [0, 0, 0, 0])
        c[0] += r
        c[1] += g
        c[2] += b
        c[3] += 1
    top = sorted(counts.values(), key=lambda c: -c[3])
    out = []
    for r, g, b, k in top:
        if k < len(px) * 0.02:
            break
        hx = "#%02X%02X%02X" % (r // k, g // k, b // k)
        if all(sum(abs(int(hx[i:i + 2], 16) - int(o[i:i + 2], 16)) for i in (1, 3, 5)) > 90 for o in out):
            out.append(hx)
        if len(out) >= n:
            break
    return out


def _logo_dark(im):
    px = [p for p in im.convert("RGBA").resize((80, 80)).getdata() if p[3] > 128]
    return bool(px) and sum(_lum(p) for p in px) / len(px) < 85


def _logo_layer(logo_path, max_w, max_h, plate=None):
    """Logo zmenšené do rámčeka; tmavé logo dostane bielu podložku, aby bolo vidieť na tmavom zábere."""
    from PIL import Image, ImageDraw
    im = Image.open(logo_path).convert("RGBA")
    r = min(max_w / im.size[0], max_h / im.size[1])
    im = im.resize((max(1, int(im.size[0] * r)), max(1, int(im.size[1] * r))), Image.LANCZOS)
    dark = _logo_dark(im) if plate is None else plate
    if not dark:
        return im
    pad = max(12, im.size[1] // 5)
    bg = Image.new("RGBA", (im.size[0] + pad * 2, im.size[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, bg.size[0] - 1, bg.size[1] - 1], radius=pad, fill=(255, 255, 255, 235))
    bg.alpha_composite(im, (pad, pad))
    return bg


# ---------- font ----------
def _missing_glyph_mask(font):
    m = font.getmask("")
    return m.size, bytes(m)


def font_covers(path, text):
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(str(path), 48)
        miss = _missing_glyph_mask(f)
        for ch in {c for c in (text or "") + (text or "").upper() if not c.isspace()}:
            m = f.getmask(ch)
            if (m.size, bytes(m)) == miss:
                return False
        return True
    except Exception:
        return False


def use_font(pid, text):
    """Nastaví font značky pre práve vytvárané video (ak má všetky písmená textu). Vráti cestu alebo None."""
    f = main_asset(pid, "font")
    path = f["path"] if f and font_covers(f["path"], text) else None
    _local.font = path
    return path


def current_font():
    return getattr(_local, "font", None)


def clear_font():
    _local.font = None


def _font_preview(path, out):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (640, 220), (17, 17, 17))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(path), 96)
    d.text((30, 30), "Aa Žž 123", font=f, fill=(255, 255, 255))
    im.save(out, "PNG")


# ---------- PDF / text do dizajnu ----------
def _pdf_text(path):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    return "\n".join((p.extract_text() or "") for p in r.pages[:40])[:60000]


def _add_design_text(pid, title, text):
    p = db.one("SELECT design_md, design_colors FROM projects WHERE id=?", (pid,)) or {}
    md = ((p.get("design_md") or "") + f"\n\n# {title}\n" + text).strip()
    colors = list(dict.fromkeys(c.upper() for c in re.findall(r"#[0-9a-fA-F]{6}\b", md)))[:5]
    if not colors:
        colors = json.loads(p.get("design_colors") or "[]")
    db.run("UPDATE projects SET design_md=?, design_colors=?, design_summary='' WHERE id=?", (md, json.dumps(colors), pid))


# ---------- zábery ----------
def _tags(pid, name, note):
    from . import footage
    words = (Path(name).stem.replace("_", " ").replace("-", " ") + " " + (note or "")).strip()
    en = ""
    try:
        from . import translate
        src = (db.one("SELECT source_lang FROM projects WHERE id=?", (pid,)) or {}).get("source_lang") or "sk"
        if words and src != "en" and translate.any_enabled():
            en = translate.translate_texts([words], src, "en")[0][0] or ""
    except Exception:
        en = ""
    return " ".join(sorted(footage._words(words + " " + en) | {"brand"}))


def _sync_footage(a):
    if a["kind"] not in ("photo", "video"):
        if a.get("footage_id"):
            db.run("DELETE FROM footage WHERE id=?", (a["footage_id"],))
            db.run("UPDATE brand_assets SET footage_id=0 WHERE id=?", (a["id"],))
        return
    tags = _tags(a["project_id"], a["name"], a.get("note"))
    if a.get("footage_id") and db.one("SELECT id FROM footage WHERE id=?", (a["footage_id"],)):
        db.run("UPDATE footage SET tags=?, path=? WHERE id=?", (tags, a["path"], a["footage_id"]))
    else:
        fid = db.run("INSERT INTO footage(source, source_id, path, tags, kind, w, h, dur) VALUES('brand',?,?,?,?,?,?,?)",
                     (f"{a['project_id']}-{a['id']}", a["path"], tags, a["kind"], a["w"], a["h"], a["dur"]))
        db.run("UPDATE brand_assets SET footage_id=? WHERE id=?", (fid, a["id"]))


def brand_footage(pid):
    """Zábery značky tohto projektu (riadky z footage)."""
    return [r for r in db.q("SELECT * FROM footage WHERE source='brand' AND source_id LIKE ?", (f"{pid}-%",))
            if Path(r["path"]).exists()]


# ---------- logo vo videu ----------
def _video_size(path):
    from . import media
    r = subprocess.run([media.ffmpeg(), "-i", str(path)], capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL)
    m = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", r.stderr)
    return (int(m.group(1)), int(m.group(2))) if m else (1080, 1920)


def decorate(pid, video):
    """Pridá logo do rohu a krátku záverečnú kartu s logom. Bez AI, len ffmpeg."""
    from PIL import Image
    from . import media
    o = opts(pid)
    logo = main_asset(pid, "logo")
    if not logo or not (o["logo_corner"] or o["logo_end"]):
        return False
    total = media.duration(video) or 0
    if total < 2:
        return False
    W, H = _video_size(video)
    k = W / 1080
    end_len = 1.6 if (o["logo_end"] and total > 6) else 0
    t0 = total - end_len
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        inputs, chain, last = [], "", "[0:v]"
        if o["logo_corner"]:
            lay = _logo_layer(logo["path"], int(230 * k), int(110 * k))
            fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.92)))
            fr.alpha_composite(lay, (int(56 * k), int(190 * H / 1920)))
            fr.save(tmp / "corner.png")
            inputs += ["-loop", "1", "-i", str(tmp / "corner.png")]
            n = len(inputs) // 4
            en = f":enable='lt(t,{t0:.2f})'" if end_len else ""
            chain += f"{last}[{n}:v]overlay=0:0{en}[c];"
            last = "[c]"
        if end_len:
            fr = Image.new("RGBA", (W, H), (0, 0, 0, 200))
            lay = _logo_layer(logo["path"], int(620 * k), int(340 * k))
            fr.alpha_composite(lay, ((W - lay.size[0]) // 2, (H - lay.size[1]) // 2))
            fr.save(tmp / "end.png")
            inputs += ["-loop", "1", "-i", str(tmp / "end.png")]
            n = len(inputs) // 4
            chain += (f"[{n}:v]format=rgba,fade=in:st={t0:.2f}:d=0.35:alpha=1[e];"
                      f"{last}[e]overlay=0:0:enable='gte(t,{t0:.2f})'[c2];")
            last = "[c2]"
        chain += f"{last}format=yuv420p[v]"
        out = tmp / ("out" + Path(video).suffix)
        media._run_ff([media.ffmpeg(), "-y", "-i", str(video), *inputs, "-filter_complex", chain, "-map", "[v]", "-map", "0:a?",
                       "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy",
                       "-movflags", "+faststart", str(out)])
        shutil.move(str(out), str(video))
    return True


# ---------- profilovka z loga ----------
def logo_avatar(pid):
    from PIL import Image
    logo = main_asset(pid, "logo")
    if not logo:
        return None
    im = Image.open(logo["path"]).convert("RGBA")
    dark = _logo_dark(im)
    bg = Image.new("RGBA", (800, 800), (255, 255, 255, 255) if dark else (0, 0, 0, 255))
    im.thumbnail((560, 560), Image.LANCZOS)
    bg.alpha_composite(im, ((800 - im.size[0]) // 2, (800 - im.size[1]) // 2))
    out = DIR / str(pid) / "profilovka-z-loga.jpg"
    bg.convert("RGB").save(out, "JPEG", quality=92)
    return str(out)


def _after_logo_change(pid):
    """Farby z loga do dizajnu (ak dizajn nemá vlastné) + profilovka z loga pre Vzhľad účtov."""
    logo = main_asset(pid, "logo")
    p = db.one("SELECT design_colors FROM projects WHERE id=?", (pid,)) or {}
    have = json.loads(p.get("design_colors") or "[]")
    if logo and not have:
        cols = logo_colors(logo["path"])
        if cols:
            db.run("UPDATE projects SET design_colors=? WHERE id=?", (json.dumps(cols), pid))
    try:
        if logo:
            logo_avatar(pid)
        else:
            (DIR / str(pid) / "profilovka-z-loga.jpg").unlink(missing_ok=True)
        from . import profiles
        profiles._prepare_images(pid, profiles.kit(pid))
    except Exception as e:
        print("profilovka z loga:", e)


def _ensure_main(pid, kind):
    if kind in ("logo", "font") and not db.one("SELECT id FROM brand_assets WHERE project_id=? AND kind=? AND main=1", (pid, kind)):
        a = db.one("SELECT id FROM brand_assets WHERE project_id=? AND kind=? ORDER BY id", (pid, kind))
        if a:
            db.run("UPDATE brand_assets SET main=1 WHERE id=?", (a["id"],))


# ---------- API ----------
def _public(a):
    return {k: a[k] for k in ("id", "kind", "name", "w", "h", "dur", "note", "main")} | {"orig": bool(a.get("orig"))}


@router.get("/api/brand/{pid}")
def get_brand(pid: int):
    return {"assets": [_public(a) for a in assets(pid)], "opts": opts(pid)}


@router.put("/api/brand/{pid}/opts")
def set_opts(pid: int, data: dict = Body(...)):
    o = opts(pid)
    o.update({k: bool(v) for k, v in data.items() if k in DEFAULT_OPTS})
    db.set_setting(f"brand_opts_{pid}", o)
    return o


@router.post("/api/brand/{pid}/upload")
async def upload(pid: int, request: Request):
    from . import media
    _db()
    form = await request.form()
    d = DIR / str(pid)
    (d / "originaly").mkdir(parents=True, exist_ok=True)
    files = form.getlist("files")
    svgs = {}
    added, errors, texts = [], [], 0
    # najprv uložiť SVG originály, aby sa dali spárovať s PNG, ktoré z nich spravil prehliadač
    for f in files:
        if Path(f.filename or "").suffix.lower() == ".svg":
            p = d / "originaly" / Path(f.filename).name
            p.write_bytes(await f.read())
            svgs[Path(f.filename).stem.lower()] = p
    png_twins = {Path(f.filename).name[:-8].lower() for f in files if (f.filename or "").lower().endswith(".svg.png")}
    for f in files:
        name = Path(f.filename or "subor").name
        ext = Path(name).suffix.lower()
        try:
            if ext == ".svg":
                if Path(name).stem.lower() in png_twins:
                    continue
                png = d / "originaly" / (Path(name).stem + ".svg.png")
                if not _svg_to_png(svgs[Path(name).stem.lower()], png):
                    raise ValueError("SVG sa nepodarilo previesť – ulož logo aj ako PNG")
                src, orig, name = png, str(svgs[Path(name).stem.lower()]), Path(name).stem + ".svg"
                ext = ".png"
            else:
                raw = await f.read()
                src = d / "originaly" / name
                src.write_bytes(raw)
                orig = ""
                if name.lower().endswith(".svg.png"):
                    orig = str(svgs.get(name[:-8].lower(), ""))
                    name = name[:-4]
            if ext in CONVERT:
                jpg = d / "originaly" / (Path(name).stem + ".jpg")
                if not _convert_other(src, jpg):
                    raise ValueError("tento formát sa nedá otvoriť – ulož ho ako JPG alebo PNG")
                src, ext = jpg, ".jpg"
            if ext in IMG:
                out, kind, (w, h) = _store_image(pid, src, name, d, orig)
                aid = db.run("INSERT INTO brand_assets(project_id, kind, name, path, orig, w, h, created_at) VALUES(?,?,?,?,?,?,?,?)",
                             (pid, kind, name, str(out), orig, w, h, _now()))
            elif ext in VIDEO:
                out = d / name
                shutil.move(str(src), out)
                dur = media.duration(out) or 0
                w, h = _video_size(out)
                aid = db.run("INSERT INTO brand_assets(project_id, kind, name, path, w, h, dur, created_at) VALUES(?,?,?,?,?,?,?,?)",
                             (pid, "video", name, str(out), w, h, dur, _now()))
            elif ext in FONT:
                from PIL import ImageFont
                ImageFont.truetype(str(src), 40)  # overí, že sa font dá použiť
                out = d / name
                shutil.move(str(src), out)
                aid = db.run("INSERT INTO brand_assets(project_id, kind, name, path, created_at) VALUES(?,?,?,?,?)",
                             (pid, "font", name, str(out), _now()))
            elif ext == ".pdf":
                out = d / name
                shutil.move(str(src), out)
                text = _pdf_text(out)
                if text.strip():
                    _add_design_text(pid, name, text)
                    texts += 1
                aid = db.run("INSERT INTO brand_assets(project_id, kind, name, path, note, created_at) VALUES(?,?,?,?,?,?)",
                             (pid, "pdf", name, str(out), f"{len(text)} znakov textu" if text.strip() else "bez textu (len obrázky)", _now()))
            elif ext in TEXT:
                _add_design_text(pid, name, src.read_text("utf-8", "ignore"))
                texts += 1
                continue
            else:
                raise ValueError("tento typ súboru appka nepoužije")
            a = db.one("SELECT * FROM brand_assets WHERE id=?", (aid,))
            _ensure_main(pid, a["kind"])
            _sync_footage(a)
            added.append(name)
        except Exception as e:
            errors.append(f"{name}: {str(e)[:120]}")
    _after_logo_change(pid)
    summary = None
    if texts:
        try:
            from starlette.concurrency import run_in_threadpool
            from . import content
            summary = await run_in_threadpool(content.run_task, "design", {"project_id": pid})
        except Exception as e:
            print("zhrnutie dizajnu:", e)
    res = {"added": added, "errors": errors, "texts": texts}
    if isinstance(summary, dict) and summary.get("manual"):
        res.update(summary)
    return res


@router.put("/api/brand/asset/{aid}")
def edit_asset(aid: int, data: dict = Body(...)):
    _db()
    a = db.one("SELECT * FROM brand_assets WHERE id=?", (aid,))
    if not a:
        raise HTTPException(404, "Nenašiel som súbor")
    pid = a["project_id"]
    if "note" in data:
        db.run("UPDATE brand_assets SET note=? WHERE id=?", (str(data["note"])[:300], aid))
    if data.get("kind") in ("logo", "photo") and a["kind"] in ("logo", "photo") and data["kind"] != a["kind"]:
        from PIL import Image
        im = Image.open(a["path"])
        if data["kind"] == "photo" and Path(a["path"]).suffix.lower() == ".png":
            bg = Image.new("RGB", im.size, (0, 0, 0))
            bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").getchannel("A"))
            newp = str(Path(a["path"]).with_suffix(".jpg"))
            bg.save(newp, "JPEG", quality=92)
            Path(a["path"]).unlink(missing_ok=True)
            db.run("UPDATE brand_assets SET path=? WHERE id=?", (newp, aid))
        db.run("UPDATE brand_assets SET kind=?, main=0 WHERE id=?", (data["kind"], aid))
        _ensure_main(pid, "logo")
    if data.get("main"):
        b = db.one("SELECT kind FROM brand_assets WHERE id=?", (aid,))
        db.run("UPDATE brand_assets SET main=0 WHERE project_id=? AND kind=?", (pid, b["kind"]))
        db.run("UPDATE brand_assets SET main=1 WHERE id=?", (aid,))
    _sync_footage(db.one("SELECT * FROM brand_assets WHERE id=?", (aid,)))
    if a["kind"] == "logo" or data.get("kind"):
        _after_logo_change(pid)
    return get_brand(pid)


@router.delete("/api/brand/asset/{aid}")
def delete_asset(aid: int):
    _db()
    a = db.one("SELECT * FROM brand_assets WHERE id=?", (aid,))
    if not a:
        return {"ok": True}
    if a.get("footage_id"):
        db.run("DELETE FROM footage WHERE id=?", (a["footage_id"],))
    db.run("DELETE FROM brand_assets WHERE id=?", (aid,))
    pp = Path(a["path"])
    for p in (pp, a.get("orig"), pp.with_suffix(".nahlad.png"), pp.with_name(pp.stem + ".nahlad.png")):
        if p:
            Path(p).unlink(missing_ok=True)
    _ensure_main(a["project_id"], a["kind"])
    if a["kind"] == "logo":
        _after_logo_change(a["project_id"])
    return get_brand(a["project_id"])


@router.get("/api/brand/file/{aid}")
def asset_file(aid: int, preview: int = 0):
    _db()
    a = db.one("SELECT * FROM brand_assets WHERE id=?", (aid,))
    if not a or not Path(a["path"]).exists():
        raise HTTPException(404, "Nenašiel som súbor")
    if preview and a["kind"] == "font":
        pv = Path(a["path"]).with_suffix(".nahlad.png")
        if not pv.exists():
            _font_preview(a["path"], pv)
        return FileResponse(pv)
    if preview and a["kind"] in ("photo", "logo"):
        pv = Path(a["path"]).with_name(Path(a["path"]).stem + ".nahlad.png")
        if not pv.exists():
            from PIL import Image
            im = Image.open(a["path"])
            im.thumbnail((480, 480))
            im.save(pv, "PNG")
        return FileResponse(pv)
    return FileResponse(a["path"])
