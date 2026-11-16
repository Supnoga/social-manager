"""Automatický strih klipu: orez na výšku podľa tvárí, titulky slovo po slove, úvodný titulok hore.

Rozloženia (vyberá sa pre každý záber zvlášť):
  full = zdroj je už na výšku;  crop = jedna tvár, orez na ňu (pri pohybe ju sleduje);
  duo  = dvaja ľudia vedľa seba, každý dostane polovicu obrazu;  fit = nič isté, celý záber na rozmazanom pozadí.
Texty sú mimo zón tlačidiel sietí: vpravo 180 px voľných, hore 300 px, dole 560 px."""
import array
import json
import math
import re
import statistics
import subprocess
import tempfile
from pathlib import Path

from app import media

from . import env, source, store

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_RIGHT = 300, 180
CAP_Y = {"crop": 1180, "full": 1180, "fit": 1200, "duo": 925, "wide": 1230}
WIDE_KEEP, WIDE_Y = 0.7, 560     # klip podľa obrazu: stredných 70 % šírky, väčší obraz než pri celom zábere
HOOK_SEC = 4.0
FIT_Y = 570
ACCENT = (255, 107, 0)


# ---------- zábery a tváre ----------
def _scene_cuts(src, t0, dur):
    """Presné časy strihov v zdroji (sekundy od začiatku klipu)."""
    r = subprocess.run([media.ffmpeg(), "-hide_banner", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(src), "-an",
                        "-vf", "scale=320:-2,select='gt(scene,0.33)',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    cuts = sorted(float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr))
    out = []
    for c in cuts:
        if 0.8 < c < dur - 0.8 and (not out or c - out[-1] > 1.0):
            out.append(round(round(c * FPS) / FPS, 4))
    return out


def _people(samples):
    """Kto je v zábere: ("crop", body polohy tváre) | ("duo", [ľavý, pravý]) | ("fit", None)."""
    allf = [sorted(s["faces"], key=lambda f: -f[2]) for s in samples]
    hit = [f for f in allf if f]
    if len(hit) < max(2, len(samples) * 0.5):
        return "fit", None
    crowd = [f for f in hit if len(f) >= 3 and f[0][2] < f[2][2] * 1.7]
    if len(crowd) > len(hit) * 0.4:
        return "fit", None              # veľa podobne veľkých tvárí (publikum, skupina, záber spoza rečníka): orez by ukázal náhodného človeka
    two = [f[:2] for f in hit if len(f) >= 2]
    if len(two) > len(hit) / 2:
        left = [min(f, key=lambda x: x[0]) for f in two]
        right = [max(f, key=lambda x: x[0]) for f in two]
        med = lambda fs: {"cx": statistics.median(f[0] for f in fs), "cy": statistics.median(f[1] for f in fs),
                          "w": statistics.median(f[2] for f in fs)}
        a, b = med(left), med(right)
        big, small = max(a["w"], b["w"]), min(a["w"], b["w"])
        if b["cx"] - a["cx"] >= 0.26 and big <= small * 2.0:
            return "duo", [a, b]
        if big <= small * 1.6:
            return "fit", None          # dvaja blízko seba: orez by jedného odrezal
    top, prev = [], None
    for s, fs in zip(samples, allf):    # drž sa tej istej osoby, nie vždy práve najväčšej tváre
        if not fs:
            continue
        f = fs[0]
        if prev is not None and abs(f[0] - prev[0]) > 0.12:
            near = min(fs, key=lambda x: abs(x[0] - prev[0]))
            if near[2] >= f[2] * 0.6 and abs(near[0] - prev[0]) < 0.08:
                f = near
        top.append((s["t"], f))
        prev = f
    jumps = sum(1 for (ta, fa), (tb, fb) in zip(top, top[1:]) if tb - ta <= 0.6 and abs(fb[0] - fa[0]) > 0.18)
    if jumps > max(1, len(top) * 0.12):
        return "fit", None              # tvár preskakuje z miesta na miesto: nie je to jeden človek, orez by skákal
    face = {"cy": statistics.median(f[1] for _, f in top), "w": statistics.median(f[2] for _, f in top)}
    return "crop", {"pts": [(t, f[0]) for t, f in top], "face": face}


def _track(pts, t_start):
    """Poloha tváre v čase: keď sa hýbe málo, jedna pevná poloha; inak kľúčové body po pol sekunde (plynulý posun).
    Rečník, ktorý chodí po pódiu, nesmie z obrazu vyjsť: krátke okno a len ľahké vyhladenie, aby orez nemeškal."""
    pts = [(t - t_start, x) for t, x in pts]
    xs = sorted(p[1] for p in pts)
    mid = statistics.median(xs)
    if len(pts) < 6 or xs[int(len(xs) * 0.9)] - xs[int(len(xs) * 0.1)] < 0.07:
        return [(0, mid)]
    keys, t = [], 0.0
    end = pts[-1][0]
    while t <= end + 0.5:
        win = [x for (tt, x) in pts if abs(tt - t) <= 0.5]
        if win:
            keys.append((round(t, 2), statistics.median(win)))
        t += 0.5
    sm = []
    for i, (t, x) in enumerate(keys):   # ľahké vyhladenie (1-2-1), aby obraz neposkakoval
        a, b = keys[max(0, i - 1)][1], keys[min(len(keys) - 1, i + 1)][1]
        sm.append((t, (a + 2 * x + b) / 4))
    out = [sm[0]]
    for t, x in sm[1:]:                 # drobné chvenie sa neprenáša
        out.append((t, out[-1][1] if abs(x - out[-1][1]) < 0.012 else x))
    return out or [(0, mid)]


def _x_expr(keys, sw, cw):
    """ffmpeg výraz pre x orezu: lineárne medzi kľúčovými bodmi, v medziach obrazu."""
    def px(x):
        return max(0, min(sw - cw, round(x * sw - cw / 2)))
    if len(keys) == 1:
        return str(px(keys[0][1]))
    expr = str(px(keys[-1][1]))
    for (ta, xa), (tb, xb) in reversed(list(zip(keys, keys[1:]))):
        a, b = px(xa), px(xb)
        expr = f"if(lt(t,{tb}),{a}+({b}-{a})*(t-{ta})/{max(0.01, tb - ta):.2f},{expr})"
    return f"if(lt(t,{keys[0][0]}),{px(keys[0][1])},{expr})"


def _no_face_edges(samples, a, b):
    """Začiatok alebo koniec záberu, kde tvár nevidno (rečník sa otočil chrbtom alebo odchádza): tam orez nemá čoho sa držať.
    Vráti časy, kde sa má záber rozdeliť; časť bez tváre sa potom ukáže celá."""
    has = [s["t"] for s in samples if a <= s["t"] < b and s["faces"]]
    if len(has) < 4 or has[-1] - has[0] < 1.0:
        return []
    out = []
    if has[0] - a >= 1.25:
        out.append(has[0])
    if b - (has[-1] + 0.25) >= 1.25:
        out.append(has[-1] + 0.25)
    return [round(round(x * FPS) / FPS, 4) for x in out]


def plan(src_path, t0, dur, work, whole=False):
    """Rozdelí klip na zábery a pre každý vyberie rozloženie. Vráti (zoznam záberov, šírka, výška zdroja)."""
    fj = Path(work) / "faces.json"
    try:
        if whole:        # klip podľa obrazu (trailer, hra, šport): neorezáva sa na tvár, ukáže sa celý záber
            raise LookupError
        env.tool("faces", [src_path, f"{t0:.3f}", f"{t0 + dur:.3f}", fj, media.ffmpeg() or "ffmpeg"], timeout=900)
        data = json.loads(fj.read_text())
    except LookupError:
        data = {"w": 0, "h": 0, "samples": []}
    except Exception as e:
        print("Clipper tváre:", str(e)[:200])
        data = {"w": 0, "h": 0, "samples": []}
    sw, sh = data.get("w") or 0, data.get("h") or 0
    if not sw:
        r = subprocess.run([media.ffmpeg(), "-i", str(src_path)], capture_output=True, text=True, errors="ignore",
                           stdin=subprocess.DEVNULL, start_new_session=True)
        m = re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", r.stderr)
        sw, sh = (int(m.group(1)), int(m.group(2))) if m else (1920, 1080)
    bounds = [0.0] + ([] if whole else _scene_cuts(src_path, t0, dur)) + [dur]
    if sh < sw * 1.2:
        bounds = sorted(set(bounds) | {x for a, b in zip(bounds, bounds[1:]) for x in _no_face_edges(data["samples"], a, b)})
    shots = []
    for a, b in zip(bounds, bounds[1:]):
        sm = [s for s in data["samples"] if a <= s["t"] < b]
        shot = {"a": a, "b": b, "layout": "wide" if whole else "fit"}
        if sh >= sw * 1.2:
            shot["layout"] = "full"
        elif len(sm) >= 2:
            kind, who = _people(sm)
            if kind == "crop":
                shot.update(layout="crop", keys=_track(who["pts"], a), face=who["face"])
            elif kind == "duo":
                shot.update(layout="duo", people=who)
        shots.append(shot)
    return shots, sw, sh


def _vf(shot, sw, sh):
    lay = shot["layout"]
    tail = f"fps={FPS},setsar=1,format=yuv420p"
    if lay == "full":
        return f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{tail}[v]"
    if lay == "crop":
        cw = min(sw, int(sh * 9 / 16) // 2 * 2)
        return f"[0:v]crop={cw}:{sh}:'{_x_expr(shot['keys'], sw, cw)}':0,scale={W}:{H}:flags=lanczos,unsharp=5:5:0.5:5:5:0,{tail}[v]"
    if lay == "duo":
        ch = int(sh * 0.74) // 2 * 2
        cw = min(sw, int(ch * W / (H / 2)) // 2 * 2)
        parts = []
        for i, p in enumerate(shot["people"]):
            x = max(0, min(sw - cw, round(p["cx"] * sw - cw / 2)))
            y = max(0, min(sh - ch, round(p["cy"] * sh - ch * 0.42)))
            parts.append(f"[s{i}]crop={cw}:{ch}:{x}:{y},scale={W}:{H // 2}:flags=lanczos,unsharp=5:5:0.5:5:5:0[p{i}]")
        return f"[0:v]split=2[s0][s1];{parts[0]};{parts[1]};[p0][p1]vstack=inputs=2,{tail}[v]"
    if lay == "wide":
        cw = int(sw * WIDE_KEEP) // 2 * 2
        fh = min(H - WIDE_Y - 300, int(W * sh / cw) // 2 * 2)
        return (f"[0:v]split=2[b0][f0];[b0]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=26:3,eq=brightness=-0.22[bg];[f0]crop={cw}:{sh},scale={W}:{fh}[fg];[bg][fg]overlay=0:{WIDE_Y},{tail}[v]")
    fh = int(W * sh / sw) // 2 * 2
    return (f"[0:v]split=2[b0][f0];[b0]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=26:3,eq=brightness=-0.22[bg];[f0]scale={W}:{fh}[fg];[bg][fg]overlay=0:{min(FIT_Y, (H - fh) // 2)},{tail}[v]")


# ---------- zvuk: strih presne do ticha ----------
def _levels(src, a, b, step=0.02):
    """Hlasitosť zvuku medzi a..b po 20 ms (dB, vyhladené)."""
    r = subprocess.run([media.ffmpeg(), "-v", "error", "-ss", f"{max(0.0, a):.3f}", "-t", f"{b - a:.3f}", "-i", str(src), "-vn",
                        "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, stdin=subprocess.DEVNULL,
                       start_new_session=True)
    x = array.array("h")
    x.frombytes(r.stdout[:len(r.stdout) // 2 * 2])
    n = int(8000 * step)
    raw = [10 * math.log10(max(1.0, sum(v * v for v in x[i:i + n]) / n)) - 90.3 for i in range(0, len(x) - n + 1, n)]
    return [max(raw[max(0, i - 1):i + 2]) for i in range(len(raw))]


def _dip(src, a, b, near):
    """Pauza v reči medzi a..b najbližšie k času `near`: (koniec reči pred ňou, začiatok reči po nej); None tam, kde reč v okne nie je.
    Vráti None, keď v okne zreteľná pauza nie je (hudba, potlesk, súvislá reč)."""
    lv = _levels(src, a, b)
    if len(lv) < 10 or max(lv) - min(lv) < 15:
        return None
    lim, loud = min(lv) + 6, min(lv) + 14
    runs, start = [], None
    for i, v in enumerate(lv + [0.0]):
        if v <= lim and start is None:
            start = i
        elif v > lim and start is not None:
            runs.append((start, i))
            start = None
    if not runs:
        return None
    at = lambda i: a + i * 0.02
    i0, i1 = min(runs, key=lambda r: 0.0 if at(r[0]) <= near <= at(r[1]) else min(abs(at(r[0]) - near), abs(at(r[1]) - near)))
    before = next((k + 1 for k in range(i0 - 1, -1, -1) if lv[k] >= loud), None)
    after = next((k for k in range(i1, len(lv)) if lv[k] >= loud), None)
    return (at(before) if before is not None else None), (at(after) if after is not None else None), at(i0), at(i1)


def tighten(src_path, t0, t1, words):
    """Doladí strih podľa zvuku, aby sa nezačínal ani nekončil uprostred slova (časy slov z titulkov sú len približné).
    Posun je najviac o pár desatín sekundy; dlhší dozvuk (smiech, nádych) na konci sa nemení."""
    inside = [w for w in words if w["s"] >= t0 - 0.05 and w["s"] < t1 - 0.04]
    if not inside:
        return t0, t1
    ws, we = inside[0]["s"], inside[-1]["e"]
    try:
        d = _dip(src_path, ws - 0.6, ws + 0.3, ws - 0.05)
        if d:                          # tesne pred prvé slovo
            t0 = max(0.0, d[2], (d[1] - 0.12) if d[1] is not None else d[3] - 0.14)
        elif ws - t0 > 1.0:
            t0 = ws - 0.15
        if t1 - we <= 0.6:             # krátky koniec: tesne za posledné slovo, nie do ďalšieho
            d = _dip(src_path, we - 0.4, we + 0.7, we + 0.05)
            if d:
                end = d[0] if d[0] is not None else d[2]
                t1 = max(end + 0.08, min(end + 0.3, (d[1] if d[1] is not None else d[3]) - 0.06))
    except Exception as e:
        print("Clipper zvuk:", str(e)[:200])
    return round(t0, 3), round(t1, 3)


def _check(out, dur):
    """Posledná kontrola hotového súboru: čierny začiatok, čierny obraz, hluchý zvuk. Pri chybe vyhodí výnimku s dôvodom."""
    r = subprocess.run([media.ffmpeg(), "-hide_banner", "-i", str(out), "-vf", "scale=320:-2,blackdetect=d=0.4:pix_th=0.08",
                        "-af", "silencedetect=n=-50dB:d=4.5,volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    if any(a < 0.3 for a, _ in black):
        raise RuntimeError("Klip sa začína čiernym obrazom.")
    if sum(b - a for a, b in black) > dur * 0.25:
        raise RuntimeError("Veľká časť klipu je čierny obraz.")
    m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    if not m or float(m.group(1)) < -45:
        raise RuntimeError("Klip nemá zvuk.")
    if re.search(r"silence_start", r.stderr):
        raise RuntimeError("V klipe je dlhé ticho.")


# ---------- titulky a úvodný titulok ----------
def _clean(tok):
    t = tok.replace(">>", "").strip().strip('"“”„«»')      # úvodzovky priamej reči do titulkov nepatria
    return t if re.search(r"\w", t) and not (t.startswith("[") or t.endswith("]")) else ""


def clip_words(words, t0, t1):
    out = []
    for w in words:
        if w["s"] < t0 - 0.05 or w["s"] >= t1 - 0.1:
            continue
        t = _clean(w["w"])
        if t:
            out.append({"w": t, "s": max(0.0, w["s"] - t0), "e": max(0.05, min(w["e"], t1) - t0)})
    return out


def _frame(path, chunk, active, hook, cap_y, hook_bottom=None, avoid=None):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    safe = W - SAFE_RIGHT - 80
    if hook:
        size = 64
        font = media._font(size)
        lines = media._wrap(d, hook, font, safe - 40)
        while len(lines) > 3 and size > 38:
            size -= 6
            font = media._font(size)
            lines = media._wrap(d, hook, font, safe - 40)
        if len(lines) > 3:              # ani najmenšie písmo nestačí: radšej tri bodky než veta useknutá bez varovania
            lines = lines[:3]
            lines[2] = lines[2].rstrip(" ,.;:") + "…"
        lh = int(size * 1.32)
        bw = max(d.textlength(ln, font=font) for ln in lines) + 56
        x0 = (W - bw) / 2
        bh = lh * len(lines) + 14
        if hook_bottom is not None:
            top = hook_bottom - bh
        elif avoid and avoid[0] < SAFE_TOP + bh + 20:      # hore by zakryl tvár: dať ho pod ňu, nad titulky
            top = max(SAFE_TOP, min(avoid[1] + 50, cap_y - 40 - bh))
        else:
            top = SAFE_TOP
        d.rounded_rectangle([x0, top - 18, x0 + bw, top + lh * len(lines) + 14], 22, fill=ACCENT + (255,))
        y = top
        for ln in lines:
            d.text(((W - d.textlength(ln, font=font)) / 2, y), ln, font=font, fill=(0, 0, 0, 255))
            y += lh
    if chunk:
        words = [w["w"].upper() for w in chunk]
        size = 92
        font = media._font(size)
        while d.textlength(" ".join(words), font=font) > safe and size > 50:
            size -= 6
            font = media._font(size)
        space = d.textlength(" ", font=font)
        total = sum(d.textlength(w, font=font) for w in words) + space * (len(words) - 1)
        x = (W - SAFE_RIGHT - total) / 2 + 50
        for i, w in enumerate(words):
            col = ACCENT if i == active else (255, 255, 255)
            d.text((x, cap_y), w, font=font, fill=col + (255,), stroke_width=8, stroke_fill=(0, 0, 0, 255))
            x += d.textlength(w, font=font) + space
    img.save(path)


def _captions(words, hook, lang, dur, shots, sw, sh, tmp):
    """Priehľadná video vrstva s titulkami slovo po slove a s úvodným titulkom.
    Poloha textov sa riadi záberom, ktorý práve beží, aby nikdy nezakryli tvár.
    Titulok ostáva celý čas len vtedy, keď je celý klip na rozmazanom pozadí; inak prvé 4 sekundy."""
    hook_until = dur + 9 if all(s["layout"] in ("fit", "wide") for s in shots) else HOOK_SEC

    def place(t):
        s = next((x for x in shots if x["a"] <= t < x["b"]), shots[-1])
        lay, avoid = s["layout"], None
        if lay == "crop" and s.get("face"):
            fh = s["face"]["w"] * sw * 1.35 * H / sh
            cy = s["face"]["cy"] * H
            avoid = (cy - fh * 0.8, cy + fh * 0.55)
        return shots.index(s), CAP_Y[lay], (880 if lay == "duo" else None), avoid

    segs, cur = [], 0.0          # (začiatok, koniec, skupina slov, aktívne slovo)
    for ch in media._chunks(words, lang):
        for j, w in enumerate(ch):
            s0 = max(cur, w["s"])
            e0 = ch[j + 1]["s"] if j + 1 < len(ch) else min(w["e"] + 0.2, s0 + 1.2)
            if s0 > cur + 0.03:
                segs.append((cur, s0, None, -1))
            e0 = max(s0 + 0.05, e0)
            segs.append((s0, e0, ch, j))
            cur = e0
    segs.append((cur, max(cur + 0.1, dur + 0.5), None, -1))
    cuts = sorted({hook_until} | {s["a"] for s in shots[1:]})
    frames, cache = [], {}
    for n, (a, b, ch, j) in enumerate(segs):
        edges = [a] + [c for c in cuts if a + 0.02 < c < b - 0.02] + [b]
        for pa, pb in zip(edges, edges[1:]):
            si, cap_y, hook_bottom, avoid = place(pa)
            with_hook = bool(hook) and pa < hook_until
            key = (n if ch else -1, with_hook, si)
            if key not in cache:
                cache[key] = tmp / f"c{len(cache):04d}.png"
                _frame(cache[key], ch, j, hook if with_hook else None, cap_y, hook_bottom, avoid)
            frames.append((cache[key], pb - pa))
    lst = tmp / "caps.txt"
    lst.write_text("".join(f"file '{p}'\nduration {d:.3f}\n" for p, d in frames) + f"file '{frames[-1][0]}'\n")
    caps = tmp / "caps.mov"
    media._run_ff([media.ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", f"fps={FPS},format=rgba",
                   "-c:v", "png", str(caps)])
    return caps


# ---------- celý klip ----------
def render(clip):
    """Vystrihne a zloží klip. Vráti (cesta, dĺžka, rozloženie). Pri chybe vyhodí výnimku s dôvodom."""
    src = store.one("SELECT * FROM sources WHERE id=?", (clip["source_id"],))
    if not src or not Path(src["path"] or "").exists():
        raise RuntimeError("Zdrojové video už nie je na disku.")
    ff = media.ffmpeg()
    visual = (src.get("kind") or "speech") == "visual"
    t0, t1 = float(clip["t0"]), float(clip["t1"])
    spoken = source.words(src)
    if not visual:
        n0, n1 = tighten(src["path"], t0, t1, spoken)
        if (n0, n1) != (t0, t1):
            t0, t1 = n0, n1
            store.run("UPDATE clips SET t0=?, t1=? WHERE id=?", (t0, t1, clip["id"]))
    dur = t1 - t0
    out = store.DIR / "clips" / f"klip-{clip['id']}.mp4"
    with tempfile.TemporaryDirectory(dir=store.DIR / "work") as tmp:
        tmp = Path(tmp)
        shots, sw, sh = plan(src["path"], t0, dur, tmp, whole=visual)
        parts, done = [], 0
        total_frames = round(dur * FPS)
        for i, s in enumerate(shots):
            n = (total_frames - done) if i == len(shots) - 1 else round(s["b"] * FPS) - done
            if n <= 0:
                continue
            part = tmp / f"s{i:03d}.mp4"
            media._run_ff([ff, "-y", "-ss", f"{t0 + done / FPS:.4f}", "-i", src["path"], "-filter_complex", _vf(s, sw, sh),
                           "-map", "[v]", "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                           "-pix_fmt", "yuv420p", str(part)])
            parts.append(part)
            done += n
        lst = tmp / "parts.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        body = tmp / "body.mp4"
        media._run_ff([ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(body)])
        time_by = {}
        for s in shots:
            time_by[s["layout"]] = time_by.get(s["layout"], 0) + s["b"] - s["a"]
        layout = max(time_by, key=time_by.get)
        words = clip_words(spoken, t0, t0 + dur)
        caps = _captions(words, (clip.get("hook") or "").strip(), src.get("lang") or "en", dur, shots, sw, sh, tmp)
        out_d = 0.4 if words and dur - words[-1]["e"] > 0.8 else 0.12      # smiech či potlesk na konci doznie plynulo
        fade = max(0.0, dur - out_d)
        media._run_ff([ff, "-y", "-i", str(body), "-i", str(caps), "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", src["path"],
                       "-filter_complex",
                       f"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
                       f"[2:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:d=0.06,afade=t=out:st={fade:.2f}:d={out_d},aresample=48000[a]",
                       "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)])
    real = media.duration(out)
    if not out.exists() or out.stat().st_size < 50_000 or abs(real - dur) > 1.0:
        raise RuntimeError(f"Klip nevyšiel správne (dĺžka {real:.1f} s namiesto {dur:.1f} s).")
    if not words and not visual:
        raise RuntimeError("V klipe nie je žiadna reč.")
    _check(out, dur)
    return str(out), real, layout
