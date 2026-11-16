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
        if not db.get_setting("brand_main_v2", 0):
            db.set_setting("brand_main_v2", 1)
            try:
                for r in db.q("SELECT DISTINCT project_id FROM brand_assets"):
                    _ensure_main(r["project_id"], "logo")
                    _ensure_main(r["project_id"], "font")
                    _after_logo_change(r["project_id"])
            except Exception as e:
                print("oprava hlavného loga:", e)


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


def _needs_plate(logo_path):
    """Biela podložka len pre priehľadné tmavé logo (inak by na čiernom nebolo vidieť); logo s vlastným pozadím ju nedostane."""
    from PIL import Image
    im = Image.open(logo_path).convert("RGBA")
    transparent = im.getchannel("A").getextrema()[0] < 200
    return transparent and _logo_dark(im)


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


def font_covers(path, text, letters_only=False):
    """Má font všetky znaky textu? letters_only: stačia písmená (symboly ako ², × či € si prehliadač doplní z bežného fontu)."""
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(str(path), 48)
        miss = _missing_glyph_mask(f)
        for ch in {c for c in (text or "") + (text or "").upper() if not c.isspace() and (c.isalpha() or not letters_only)}:
            m = f.getmask(ch)
            if (m.size, bytes(m)) == miss:
                return False
        return True
    except Exception:
        return False


def use_font(pid, text, letters_only=False):
    """Nastaví fonty značky pre práve vytvárané video: nadpisový a textový (len také, čo majú všetky písmená textu)."""
    ok = [a for a in assets(pid, "font") if font_covers(a["path"], text, letters_only)]
    disp = max(ok, key=lambda a: (_font_score(a, "display"), a["main"], -a["id"]))["path"] if ok else None
    rest = [a for a in ok if a["path"] != disp and Path(a["path"]).stem != Path(disp).stem]
    txt = max(rest, key=lambda a: (_font_score(a, "text"), -a["id"])) if rest else None
    _local.font = disp
    _local.font_text = txt["path"] if txt and _font_score(txt, "text") > _font_score(txt, "display") else None
    return disp


def current_font():
    return getattr(_local, "font", None)


def current_text_font():
    return getattr(_local, "font_text", None)


def clear_font():
    _local.font = None
    _local.font_text = None


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
    logo = video_logo(pid, dark_bg=True)
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
            # rovnaké miesto a veľkosť ako logo v animovanom videe (explainer #lg), aby nikdy nezakrylo nadpis
            if W > H:   # na šírku: 280x64 vľavo hore nad nadpisom
                s = H / 1080
                box, pos = (int(280 * s), int(64 * s)), (int(150 * s), int(72 * s))
            else:       # na výšku: 313x81 nad nadpisom, v bezpečnej zóne Shorts
                box, pos = (int(313 * k), int(81 * k)), (int(96 * k), int(270 * H / 1920))
            lay = _logo_layer(logo["path"], *box, plate=_needs_plate(logo["path"]))
            fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.92)))
            fr.alpha_composite(lay, pos)
            fr.save(tmp / "corner.png")
            inputs += ["-loop", "1", "-i", str(tmp / "corner.png")]
            n = len(inputs) // 4
            en = f":enable='lt(t,{t0:.2f})'" if end_len else ""
            chain += f"{last}[{n}:v]overlay=0:0{en}[c];"
            last = "[c]"
        if end_len:
            fr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            lay = _logo_layer(logo["path"], int(620 * min(k, H / 1080)), int(340 * min(k, H / 1080)), plate=_needs_plate(logo["path"]))
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


LOGO_RX = r"logo|znak|znack|brand|wordmark|\bmark\b"


def _is_logo_name(name):
    return bool(re.search(LOGO_RX, re.sub(r"[_\-.]+", " ", (name or "").lower())))


def _dark_cached(a):
    try:
        from PIL import Image
        return _logo_dark(Image.open(a["path"]))
    except Exception:
        return False


def _logo_score(a, dark_bg=None):
    """Čím viac, tým skôr je to skutočné logo značky (nie ikona ani výrez produktu)."""
    n = re.sub(r"[_\-.]+", " ", (a.get("name") or "").lower())
    sc = 0
    if _is_logo_name(n):
        sc += 10
    if re.search(r"icon|ikon|favicon|app\b", n):
        sc -= 3
    if re.search(r"basic|main|primary|hlavn|zaklad", n):
        sc += 1
    w, h = a.get("w") or 0, a.get("h") or 0
    if h and w / h >= 1.8:
        sc += 3  # nápis (wordmark) má prednosť pred samotným znakom
    if dark_bg is not None:
        dark = _dark_cached(a)
        sc += 4 if dark != dark_bg else -6
        if re.search(r"white|biel|light|negat|invert" if dark_bg else r"black|ciern|dark", n):
            sc += 2
    return sc


def _font_score(a, role="display"):
    n = (a.get("name") or "").lower()
    sc = 0
    if Path(a["path"]).suffix.lower() in (".otf", ".ttf"):
        sc += 4  # s týmito vie pracovať aj kreslenie titulkov mimo prehliadača
    heavy = bool(re.search(r"display|bold|black|heavy|headline|title|nadpis", n))
    light = bool(re.search(r"text|light|thin|regular|book|body", n))
    if role == "display":
        sc += 3 * heavy - 2 * (light and not heavy)
    else:
        sc += 3 * (light and not re.search(r"display|black|heavy", n)) - 2 * heavy
    if font_covers(a["path"], "Čučoriedka ľúbi žaby, ÁÉÍÓÚ ßäöü"):
        sc += 5  # font bez diakritiky sa hodí len na názvy produktov
    return sc


def _manual_main(pid, kind):
    return db.get_setting(f"brand_main_manual_{pid}_{kind}", 0)


def _ensure_main(pid, kind):
    """Hlavné logo/font: to, čo vybral používateľ; inak to, čo najviac vyzerá ako logo (font: nadpisový s diakritikou)."""
    if kind not in ("logo", "font"):
        return
    items = [a for a in db.q("SELECT * FROM brand_assets WHERE project_id=? AND kind=? ORDER BY id", (pid, kind)) if Path(a["path"]).exists()]
    if not items:
        return
    man = _manual_main(pid, kind)
    if man and any(a["id"] == man for a in items):
        best = man
    else:
        best = max(items, key=lambda a: (_logo_score(a) if kind == "logo" else _font_score(a), -a["id"]))["id"]
    db.run("UPDATE brand_assets SET main=0 WHERE project_id=? AND kind=? AND id<>?", (pid, kind, best))
    db.run("UPDATE brand_assets SET main=1 WHERE id=?", (best,))


def video_logo(pid, dark_bg=True):
    """Logo do videa: ručne zvolené hlavné logo, inak variant, ktorý je na danom pozadí najlepšie vidieť (na čiernej biely)."""
    logos = assets(pid, "logo")
    if not logos:
        return None
    man = _manual_main(pid, "logo")
    for a in logos:
        if man and a["id"] == man:
            return a
    named = [a for a in logos if _is_logo_name(a["name"])] or logos
    return max(named, key=lambda a: (_logo_score(a, dark_bg), -a["id"]))


def logo_data_uri(a, max_w, max_h, dark_bg=True):
    """Logo ako obrázok do animácie. Tmavé logo na tmavom pozadí dostane svetlú podložku."""
    import base64
    import io
    lay = _logo_layer(a["path"], max_w, max_h, plate=None if dark_bg else False)
    buf = io.BytesIO()
    lay.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def product_images(pid):
    """Výrezy produktov s priehľadným pozadím (nie logá): {slovo v názve: cesta}. Použijú sa v scéne, ktorá produkt spomína."""
    out = {}
    for a in assets(pid, "logo"):
        if _is_logo_name(a["name"]) or max(a.get("w") or 0, a.get("h") or 0) < 400:
            continue
        key = re.sub(r"[^a-z0-9]+", " ", Path(a["name"]).stem.lower()).strip()
        if len(key) >= 4:
            out[key] = a["path"]
    return out


def _vivid(hx):
    try:
        r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    except Exception:
        return False
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return s >= 0.35 and 0.18 <= l <= 0.85


def accent(colors, project_color=None, fallback="#FF6B00"):
    """Hlavná (zvýrazňovacia) farba značky: prvá sýta farba z dizajnu. Čierna, biela a sivé ňou nikdy nie sú."""
    for c in list(colors or []) + [project_color]:
        if c and re.fullmatch(r"#[0-9a-fA-F]{6}", c) and _vivid(c):
            return c
    return fallback


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
        db.set_setting(f"brand_main_manual_{pid}_{b['kind']}", aid)
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


# ---------- dodatočné logo do hotových, ešte nenahratých videí ----------
_relogo_busy = threading.Lock()


def _relogo_pending(pid):
    """Videá projektu bez loga: vznikli pred nahratím loga a ešte nie sú na YouTube (ani súkromne)."""
    lg = video_logo(pid, dark_bg=True)
    if not lg:
        return []
    since = (db.one("SELECT created_at FROM brand_assets WHERE id=?", (lg["id"],)) or {}).get("created_at") or ""
    done = set(db.get_setting(f"relogo_done_{pid}", []) or [])
    rows = db.q("""SELECT v.* FROM videos v WHERE v.project_id=? AND v.created_at < ?
                   AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.video_id=v.id AND (COALESCE(p.stash_id,'')!=''
                        OR COALESCE(p.external_id,'')!='' OR p.status IN ('done','uploading')))""", (pid, since))
    return [r for r in rows if r["id"] not in done and r["file_path"] and Path(r["file_path"]).exists()]


def relogo(pids):
    """Bez AI: dá logo do rohu (a záverečnú kartu) videám, ktoré vznikli pred nahratím loga. Po jednom, na pozadí."""
    import os

    def run():
        if not _relogo_busy.acquire(blocking=False):
            return
        try:
            for pid in pids:
                for v in _relogo_pending(pid):
                    busy = db.one("SELECT 1 FROM posts WHERE video_id=? AND (status='uploading' OR COALESCE(stash_id,'')!='')", (v["id"],))
                    if busy:
                        continue
                    src = Path(v["file_path"])
                    tmp = src.with_name(src.stem + ".logo" + src.suffix)
                    try:
                        shutil.copyfile(src, tmp)
                        if decorate(pid, tmp):
                            os.replace(tmp, src)
                    except Exception as e:
                        print("dodatočné logo:", e)
                    finally:
                        if tmp.exists():
                            tmp.unlink()
                    done = db.get_setting(f"relogo_done_{pid}", []) or []
                    db.set_setting(f"relogo_done_{pid}", done + [v["id"]])
        finally:
            _relogo_busy.release()

    threading.Thread(target=run, daemon=True).start()


@router.post("/api/brand/relogo")
def relogo_api(data: dict = Body(default={})):
    pids = [int(p) for p in data.get("project_ids", [])]
    left = {p: len(_relogo_pending(p)) for p in pids}
    relogo(pids)
    return {"pending": left}


# ---------- oprava videí so zlým dodatočným logom (1.53.8) ----------
# Do 1.53.7 dávalo dodatočné logo (relogo) aj do dlhých videí rozloženie pre výšku: obrovské logo cez nadpis.
# Tu sa také videá, ktoré ešte nie sú verejné, podržia, zložia nanovo (len Mac, bez AI) a nahrajú znova.
_fix_busy = threading.Lock()
_fix_state = {"running": False, "done": [], "errors": [], "current": None}


def _relogoed_ids():
    ids = set()
    for r in db.q("SELECT key, value FROM settings WHERE key LIKE 'relogo_done_%'"):
        try:
            ids |= {int(x) for x in json.loads(r["value"] or "[]")}
        except Exception:
            pass
    return ids


def _is_public(p):
    return p["status"] == "done" and (p.get("scheduled_at") or "") <= dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fixlogo_report():
    pub, todo, fixed = [], [], set(db.get_setting("fixlogo_done", []) or [])
    for vid in sorted(_relogoed_ids()):
        v = db.one("SELECT id, project_id, title, script_id FROM videos WHERE id=?", (vid,))
        if not v or vid in fixed:
            continue
        posts = db.q("""SELECT p.*, a.platform FROM posts p JOIN accounts a ON a.id=p.account_id WHERE p.video_id=?""", (vid,))
        row = {"video_id": vid, "project_id": v["project_id"], "title": v["title"], "fmt": (db.one(
            f"SELECT {db.fmt_sql('v')} f FROM videos v WHERE v.id=?", (vid,)) or {}).get("f"),
            "posts": [{"id": p["id"], "status": p["status"], "at": p["scheduled_at"], "url": p.get("url") or "",
                       "yt": p.get("external_id") or p.get("stash_id") or ""} for p in posts]}
        (pub if any(_is_public(p) for p in posts) else todo).append(row)
    todo.sort(key=lambda r: min([p["at"] or "9" for p in r["posts"]] or ["9"]))  # najbližšie zverejnenie prvé
    return {"public": pub, "todo": todo, "fixed": sorted(fixed), "state": _fix_state}


RENDER = None  # main.script_to_video (main beží ako __main__, preto ho main sem dá sám)


def _fix_one(vid):
    from .platforms import youtube
    v = db.one("SELECT * FROM videos WHERE id=?", (vid,))
    if not v or not v["script_id"]:
        raise RuntimeError("video bez scenára")
    keep = db.get_setting("fixlogo_hold", {}) or {}
    if any(_is_public(p) for p in db.q("SELECT * FROM posts WHERE video_id=?", (vid,))):
        raise RuntimeError("medzitým sa zverejnilo")
    # 1) najprv zložiť nanovo (hlas aj scenár ostávajú); keď sa to nepodarí, na YouTube sa nič nezmaže
    r = RENDER(int(v["script_id"]), {})
    # 2) až teraz súkromné/naplánované kópie na YouTube zmazať (ešte nie sú verejné)
    for p in db.q("SELECT p.*, a.platform FROM posts p JOIN accounts a ON a.id=p.account_id WHERE p.video_id=?", (vid,)):
        if _is_public(p):
            raise RuntimeError("medzitým sa zverejnilo")
        yid = p.get("external_id") or p.get("stash_id") or ""
        if yid and p["platform"] == "youtube":
            acc = db.one("SELECT * FROM accounts WHERE id=?", (p["account_id"],))
            youtube.delete_video(acc, yid)
            db.run("UPDATE posts SET stash_id='', external_id='', url='' WHERE id=?", (p["id"],))
    new = db.one("SELECT * FROM videos WHERE id=?", (r["video_id"],))
    old = Path(v["file_path"] or "")
    db.run("UPDATE videos SET file_path=?, size=?, duration=?, preview_path='', removed=0 WHERE id=?",
           (new["file_path"], new["size"], new["duration"], vid))
    db.run("DELETE FROM videos WHERE id=?", (new["id"],))
    for f in (old, old.with_suffix(".jpg")):
        if str(f) and f != Path(new["file_path"]) and f.exists():
            try:
                f.unlink()
            except Exception:
                pass
    # 3) posty späť do pôvodného stavu (verejné hneď neboli, takže 'done' = naplánované → znova nahrať)
    for p in db.q("SELECT id FROM posts WHERE video_id=? AND status='hold'", (vid,)):
        st = keep.get(str(p["id"]), "queued")
        db.run("UPDATE posts SET status=?, error='', attempts=0 WHERE id=?", ("review" if st == "review" else "queued", p["id"]))


def fixlogo(apply=True):
    rep = fixlogo_report()
    if not apply:
        return rep
    keep = db.get_setting("fixlogo_hold", {}) or {}
    for row in rep["todo"]:  # hneď podržať, nech sa nič nenahrá ani nezverejní, kým nie je nové video
        for p in row["posts"]:
            if p["status"] != "hold":
                keep[str(p["id"])] = p["status"]
        db.run("UPDATE posts SET status='hold' WHERE video_id=? AND status IN ('review','queued','done','failed')", (row["video_id"],))
    db.set_setting("fixlogo_hold", keep)

    def run():
        if not _fix_busy.acquire(blocking=False):
            return
        _fix_state["running"] = True
        try:
            for row in rep["todo"]:
                _fix_state["current"] = row["video_id"]
                try:
                    _fix_one(row["video_id"])
                    db.set_setting("fixlogo_done", (db.get_setting("fixlogo_done", []) or []) + [row["video_id"]])
                    _fix_state["done"].append(row["video_id"])
                except Exception as e:
                    _fix_state["errors"].append([row["video_id"], str(e)[:300]])
                    print("oprava loga:", row["video_id"], e)
        finally:
            _fix_state["running"] = False
            _fix_state["current"] = None
            _fix_busy.release()

    threading.Thread(target=run, daemon=True).start()
    return dict(rep, started=len(rep["todo"]))


@router.get("/api/brand/fixlogo")
def fixlogo_get():
    return fixlogo_report()


@router.post("/api/brand/fixlogo")
def fixlogo_post(data: dict = Body(default={})):
    return fixlogo(bool(data.get("apply", True)))


# ---------- odstránenie starého loga z hotových videí (1.76.0) ----------
# Oliver 15.11.: staré logo kanála (spred líšky) hore vo videu je škaredé. Líška je vo videu ako sprievodca, logo v rohu
# netreba. Nové videá ho už nemajú (logo_corner/logo_end vypnuté), hotové neuverejnené sa opravia bez AI aj bez
# skladania nanovo: ffmpeg delogo zahladí roh (pozadie je tmavé), dlhým videám sa odstrihne záverečná karta s logom.
_unlogo_busy = threading.Lock()
_unlogo_state = {"running": False, "done": 0, "errors": [], "current": None}
UNLOGO_TAIL = 1.8   # explainer.TAIL: záverečná karta s logom na konci dlhého videa


def _logo_box(pid, wide):
    """Kde presne je logo v rohu (rovnaký výpočet ako v explainer: data URI 680×176 → CSS rámček, stage posun)."""
    lg = video_logo(pid, dark_bg=True)
    if not lg:
        return None
    try:
        lay = _logo_layer(lg["path"], 680, 176)
        w0, h0 = lay.size
    except Exception:
        w0, h0 = 600, 600
    if wide:
        r = min(280 / w0, 64 / h0, 1)
        x, y, w, h = 150, 72, w0 * r, h0 * r
    else:
        r = min(340 / w0, 88 / h0, 1)
        s = .97   # #stage: transform-origin 72px 196px; translate(8px,-56px) scale(.97)
        x, y, w, h = 72 + 8, 196 - 56, w0 * r * s, h0 * r * s
    pad = 14
    return int(x - pad), int(y - pad), int(w + 2 * pad), int(h + 2 * pad)


def unlogo_pending(pids):
    done = set(db.get_setting("unlogo_done", []) or [])
    out = []
    for pid in pids:
        rows = db.q(f"""SELECT v.*, {db.fmt_sql('v')} fmt FROM videos v WHERE v.project_id=?
                       AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.video_id=v.id AND (COALESCE(p.stash_id,'')!=''
                            OR COALESCE(p.external_id,'')!='' OR p.status='uploading'))""", (pid,))
        out += [r for r in rows if r["id"] not in done and r["file_path"] and Path(r["file_path"]).exists()]
    # najprv videá, ktoré idú von najskôr
    def first(r):
        p = db.one("SELECT MIN(scheduled_at) t FROM posts WHERE video_id=? AND status IN ('queued','review')", (r["id"],))
        return (p or {}).get("t") or "9999"
    return sorted(out, key=first)


def unlogo_blocked(video_id):
    """Video ešte čaká na odstránenie starého loga alebo na nové zloženie: nenahrávať ho."""
    vid = int(video_id or 0)
    return vid in set(db.get_setting("unlogo_todo", []) or []) or vid in set(db.get_setting("rerender_todo", []) or [])


def unlogo_now(video_id):
    """16.11.: video na rade čakalo v rade na odstránenie loga za preskladaním máp a nevyšlo načas.
    Video, ktoré má ísť von, sa skontroluje (a ak treba, opraví) hneď. True = môže ísť von."""
    vid = int(video_id or 0)
    if not unlogo_blocked(vid):
        return True
    if vid in set(db.get_setting("rerender_todo", []) or []):
        return False   # skladá sa nanovo (oprava obrazu): počká na nové video
    if vid in set(db.get_setting("remap_todo", []) or []) and vid not in set(db.get_setting("remap_done", []) or []):
        return False   # čaká na opravu mapy: staré video by nemalo ísť von
    v = db.one(f"SELECT v.*, {db.fmt_sql('v')} fmt FROM videos v WHERE v.id=?", (vid,))
    try:
        if v and v.get("file_path") and Path(v["file_path"]).exists():
            _unlogo_one(v)
        db.set_setting("unlogo_done", (db.get_setting("unlogo_done", []) or []) + [vid])
        db.set_setting("unlogo_todo", [i for i in (db.get_setting("unlogo_todo", []) or []) if i != vid])
        return True
    except Exception as e:
        print("odstránenie loga (hneď):", vid, e)
        return False


def _has_logo(ff, src, box):
    """Je v rohu naozaj logo? (pozadie je tmavé, logo/podložka svetlé) Nové videá ho už nemajú: tie sa nechajú tak."""
    x, y, w, h = box
    r = subprocess.run([ff, "-v", "error", "-ss", "3", "-i", str(src), "-frames:v", "1", "-vf", f"crop={w}:{h}:{x}:{y}",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, stdin=subprocess.DEVNULL)
    px = r.stdout or b""
    if not px:
        return True   # nevieme: radšej opraviť
    return sum(1 for c in px if c > 150) > len(px) * .03


def _unlogo_one(v):
    from . import media
    ff = media.ffmpeg()
    src = Path(v["file_path"])
    wide = (v.get("fmt") or "") == "long"
    box = _logo_box(v["project_id"], wide)
    if not box or not _has_logo(ff, src, box):
        return False
    tmp = src.with_name(src.stem + ".unlogo.mp4")
    vf = []
    if box:
        x, y, w, h = box
        vf.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
    dur = None
    if wide:
        r = subprocess.run([ff, "-i", str(src)], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr or "")
        if m:
            dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    cmd = [ff, "-y", "-i", str(src)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    if dur and dur > 30:
        cmd += ["-t", f"{dur - UNLOGO_TAIL:.2f}"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)]
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 10000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError((r.stderr or "ffmpeg")[-300:])
    import os
    os.replace(tmp, src)
    try:
        db.run("UPDATE videos SET size=? WHERE id=?", (src.stat().st_size, v["id"]))
        if dur and dur > 30:
            db.run("UPDATE videos SET duration=? WHERE id=?", (round(dur - UNLOGO_TAIL, 2), v["id"]))
    except Exception:
        pass


def unlogo(pids):
    for pid in pids:   # nové videá už bez starého loga
        o = opts(pid)
        o.update(logo_corner=False, logo_end=False)
        db.set_setting(f"brand_opts_{pid}", o)
    todo = unlogo_pending(pids)
    db.set_setting("unlogo_todo", sorted(set(db.get_setting("unlogo_todo", []) or []) | {r["id"] for r in todo}))

    def run():
        _unlogo_busy.acquire()   # počká, kým dobehne preskladanie máp (predtým tu skončil a videá ostali zablokované)
        _unlogo_state["running"] = True
        try:
            for v in todo:
                if not unlogo_blocked(v["id"]):
                    continue
                _unlogo_state["current"] = v["id"]
                try:
                    _unlogo_one(v)
                    db.set_setting("unlogo_done", (db.get_setting("unlogo_done", []) or []) + [v["id"]])
                    _unlogo_state["done"] += 1
                    db.set_setting("unlogo_todo", [i for i in (db.get_setting("unlogo_todo", []) or []) if i != v["id"]])
                except Exception as e:   # ostáva zablokované (nenahrá sa so starým logom)
                    _unlogo_state["errors"].append([v["id"], str(e)[:300]])
                    print("odstránenie loga:", v["id"], e)
        finally:
            _unlogo_state["running"] = False
            _unlogo_state["current"] = None
            _unlogo_busy.release()

    threading.Thread(target=run, daemon=True).start()
    return {"started": len(todo)}


@router.post("/api/brand/unlogo")
def unlogo_api(data: dict = Body(default={})):
    return unlogo([int(p) for p in data.get("project_ids", [])])


@router.get("/api/unlogo")
def unlogo_status():
    return dict(_unlogo_state, todo=len(db.get_setting("unlogo_todo", []) or []))


# ---------- mapy: kamera netrafila krajiny na severe (1.76.1) ----------
# Do 1.76.0 mala mapa strop zemepisnej šírky stredu záberu 60°, takže Island, Nórsko, Fínsko, Grónsko… pri
# priblížení ušli hore z obrazu. Tu sa nájdu hotové neuverejnené videá s takou mapou a zložia sa nanovo (len Mac, bez AI).
_LAT = {"IS": (63.3, 66.6), "NO": (58.0, 71.2), "FI": (59.8, 70.1), "SE": (55.3, 69.1), "GL": (59.8, 83.6),
        "RU": (41.2, 81.9), "CA": (41.7, 83.1), "SJ": (76.4, 80.8), "FO": (61.4, 62.4), "AX": (59.9, 60.5)}


def _north_map(scenes):
    for sc in scenes or []:
        d = ((sc.get("anim") or {}).get("d") or {}) if isinstance(sc, dict) else {}
        if d.get("k") != "map":
            continue
        cs = [str(c).upper() for c in (d.get("c") or [])] + ([str(d["onto"]).upper()] if d.get("onto") else [])
        if not any(c in _LAT for c in cs):
            continue
        lo = min(_LAT.get(c, (45, 45))[0] for c in cs)
        hi = max(_LAT.get(c, (45, 45))[1] for c in cs)
        if (lo + hi) / 2 > 59:
            return True
    return False


def remap_pending(pids):
    out = []
    for pid in pids:
        for v in db.q("""SELECT v.*, s.scenes sc FROM videos v JOIN scripts s ON s.id=v.script_id WHERE v.project_id=?
                         AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.video_id=v.id AND (COALESCE(p.stash_id,'')!=''
                              OR COALESCE(p.external_id,'')!='' OR p.status='uploading'))""", (pid,)):
            if v["id"] in set(db.get_setting("remap_done", []) or []) or not v["file_path"] or not Path(v["file_path"]).exists():
                continue
            try:
                if _north_map(json.loads(v["sc"] or "[]")):
                    out.append(v)
            except Exception:
                pass
    return out


def remap(pids):
    todo = remap_pending(pids)
    db.set_setting("remap_todo", sorted(set(db.get_setting("remap_todo", []) or []) | {r["id"] for r in todo}))
    db.set_setting("unlogo_todo", sorted(set(db.get_setting("unlogo_todo", []) or []) | {r["id"] for r in todo}))

    def run():
        with _unlogo_busy:   # po jednom, nie súčasne s odstraňovaním loga
            for v in todo:
                if v["id"] in set(db.get_setting("remap_done", []) or []):
                    continue
                _unlogo_state["current"] = "mapa %s" % v["id"]
                try:
                    r = RENDER(int(v["script_id"]), {})
                    new = db.one("SELECT * FROM videos WHERE id=?", (r["video_id"],))
                    old = Path(v["file_path"])
                    db.run("UPDATE videos SET file_path=?, size=?, duration=?, preview_path='', removed=0 WHERE id=?",
                           (new["file_path"], new["size"], new["duration"], v["id"]))
                    db.run("DELETE FROM videos WHERE id=?", (new["id"],))
                    for f in (old, old.with_suffix(".jpg")):
                        if f != Path(new["file_path"]) and f.exists():
                            f.unlink(missing_ok=True)
                    db.set_setting("remap_done", (db.get_setting("remap_done", []) or []) + [v["id"]])
                    _unlogo_state["remapped"] = _unlogo_state.get("remapped", 0) + 1
                    db.set_setting("unlogo_done", (db.get_setting("unlogo_done", []) or []) + [v["id"]])
                    db.set_setting("unlogo_todo", [i for i in (db.get_setting("unlogo_todo", []) or []) if i != v["id"]])
                except Exception as e:
                    _unlogo_state["errors"].append([v["id"], "mapa: " + str(e)[:300]])
                    print("mapa nanovo:", v["id"], e)

    threading.Thread(target=run, daemon=True).start()
    return {"started": len(todo), "ids": [v["id"] for v in todo]}


@router.post("/api/brand/remap")
def remap_api(data: dict = Body(default={})):
    return remap([int(p) for p in data.get("project_ids", [])])
