"""Hlas zadarmo (Microsoft Edge neural hlasy cez edge-tts) a práca s videom (ffmpeg, pribalené zadarmo)."""
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import db, languages

VOICE_DIR = db.MEDIA_DIR / "voice"
VOICE_DIR.mkdir(parents=True, exist_ok=True)


def ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def tts(text, lang, gender="F", out_path=None, voice=None, rate=1.0):
    """Starší vstup – používa nový výber hlasov (voices.synth)."""
    from . import voices
    if isinstance(rate, str):
        rate = 1 + int(rate.strip("%+") or 0) / 100 * (-1 if rate.startswith("-") else 1)
    if voice and ":" not in voice:
        voice = "edge:" + voice
    return voices.synth(text, lang, voice or "auto", gender, rate, out_path)[0]


def duration(path):
    ff = ffmpeg()
    if not ff:
        return 0
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        return 0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def merge_voice(video, voice, out, keep_original=0.15):
    """Dá hlas do videa. Pôvodný zvuk stíši (hudba v pozadí ostane potichu)."""
    ff = ffmpeg()
    if not ff:
        raise RuntimeError("Chýba ffmpeg")
    cmd = [ff, "-y", "-i", str(video), "-i", str(voice), "-filter_complex",
           f"[0:a]volume={keep_original}[a0];[a0][1:a]amix=inputs=2:duration=first:dropout_transition=0[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    if r.returncode != 0:
        # video bez zvukovej stopy
        cmd = [ff, "-y", "-i", str(video), "-i", str(voice), "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
        if r.returncode != 0:
            raise RuntimeError("ffmpeg: " + r.stderr[-400:])
    return str(out)


def image_video(voice, out, bg_color="0x111111", image=None, size="1080x1920"):
    """Z hlasu urobí jednoduché vertikálne video (obrázok/farba + hlas) - na rýchle testy alebo podcast-štýl."""
    ff = ffmpeg()
    if image:
        cmd = [ff, "-y", "-loop", "1", "-i", str(image), "-i", str(voice), "-vf",
               f"scale={size.replace('x', ':')}:force_original_aspect_ratio=increase,crop={size.replace('x', ':')}",
               "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)]
    else:
        cmd = [ff, "-y", "-f", "lavfi", "-i", f"color=c={bg_color}:s={size}:r=30", "-i", str(voice),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-400:])
    return str(out)


LANG_RE = re.compile(r"(?:^|[_\-. \[(])(" + "|".join(languages.LANGUAGES) + r")(?:$|[_\-. \])])", re.I)


def guess_lang(filename):
    """Z názvu súboru uhádne jazyk, napr. 'recept_de.mp4' -> de."""
    stem = Path(filename).stem
    m = None
    for m in LANG_RE.finditer(stem):
        pass
    return m.group(1).lower() if m else ""


# ---------- Videá so scénami (texty na obrazovke ako v náhľade) ----------
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size):
    from PIL import ImageFont
    from . import brand
    for f in ([brand.current_font()] if brand.current_font() else []) + FONT_CANDIDATES:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default(size)


def _hex(c, default=(255, 107, 0)):
    c = (c or "").lstrip("#")
    try:
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return default


def _wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def scene_frame(text, out, color="#FF6B00", size=(1080, 1920), transparent=False):
    """Jeden obrázok scény: farebný prechod + veľký biely text (alebo priehľadná vrstva s textom)."""
    from PIL import Image, ImageDraw
    W, H = size
    if transparent:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
    else:
        r, g, b = _hex(color)
        img = Image.new("RGB", size, (0, 0, 0))
        px = img.load()
        grad = Image.new("RGB", (1, H))
        for y in range(H):
            k = max(0.0, 1 - y / (H * 0.85))
            grad.putpixel((0, y), (int(r * k * 0.9), int(g * k * 0.9), int(b * k * 0.9)))
        img = grad.resize(size)
    d = ImageDraw.Draw(img)
    text = (text or "").strip()
    if text:
        fs = 96 if len(text) < 40 else 78 if len(text) < 80 else 62
        font = _font(fs)
        lines = _wrap(d, text, font, W - 160)
        lh = int(fs * 1.18)
        y = int(H * 0.42) - len(lines) * lh // 2
        if transparent:  # podklad pod text, aby bol čitateľný na videu
            box_w = max(d.textlength(l, font=font) for l in lines) + 70
            d.rounded_rectangle([(W - box_w) / 2, y - 30, (W + box_w) / 2, y + len(lines) * lh + 20], 28, fill=(0, 0, 0, 150))
        for line in lines:
            w = d.textlength(line, font=font)
            d.text(((W - w) / 2 + 3, y + 4), line, font=font, fill=(0, 0, 0, 120) if transparent else (0, 0, 0))
            d.text(((W - w) / 2, y), line, font=font, fill=(255, 255, 255))
            y += lh
    img.save(out)
    return out


def scene_video(scenes, voice, out, colors=None, base_video=None):
    """Video zo scén: texty na obrazovke sa striedajú podľa dĺžky hlasu. S podkladom ich dá cez tvoje video."""
    import tempfile
    ff = ffmpeg()
    colors = colors or ["#FF6B00"]
    scenes = [s for s in scenes if (s.get("onscreen") or "").strip()] or [{"onscreen": ""}]
    total = duration(voice) or 10
    per = total / len(scenes)
    with tempfile.TemporaryDirectory() as tmp:
        frames = []
        for i, s in enumerate(scenes):
            f = str(Path(tmp) / f"s{i:03d}.png")
            scene_frame(s.get("onscreen", ""), f, colors[i % len(colors)], transparent=bool(base_video))
            frames.append(f)
        if base_video:
            cmd = [ff, "-y", "-stream_loop", "-1", "-i", str(base_video), "-i", str(voice)]
            for f in frames:
                cmd += ["-i", f]
            chain = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v0]"
            for i in range(len(frames)):
                a, b = i * per, (i + 1) * per
                chain += f";[v{i}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{i + 1}]"
            cmd += ["-filter_complex", chain, "-map", f"[v{len(frames)}]", "-map", "1:a", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(out)]
        else:
            lst = Path(tmp) / "list.txt"
            lst.write_text("".join(f"file '{f}'\nduration {per:.3f}\n" for f in frames) + f"file '{frames[-1]}'\n")
            cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(voice),
                   "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
                   "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
        if r.returncode != 0:
            raise RuntimeError("ffmpeg: " + r.stderr[-500:])
    return str(out)


# ---------- Video zo záberov (B-roll) + titulky slovo po slove ----------
W, H = 1080, 1920
SAFE_TOP, CAP_Y = 300, 1180   # bezpečná zóna: mimo horných ikon, spodného popisu a pravých tlačidiel
LONG_WORD_LANGS = {"de", "fi", "hu", "nl", "et", "is"}


def _run_ff(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-500:])


def word_times(voice, text):
    """Časy slov: z Microsoft hlasu (presné) alebo odhad podľa dĺžky slov (Google hlas)."""
    wj = Path(str(voice) + ".words.json")
    if wj.exists():
        try:
            w = json.loads(wj.read_text())
            if w:
                return w
        except Exception:
            pass
    total = duration(voice) or 10
    words = (text or "").split()
    if not words:
        return []
    weights = [len(x) + 2 + (6 if x[-1:] in ".!?…" else 2 if x[-1:] in ",;:" else 0) for x in words]
    unit, t, out = total * 0.97 / sum(weights), 0.12, []
    for x, wt in zip(words, weights):
        d = wt * unit
        out.append({"w": x, "s": t, "e": t + d * 0.85})
        t += d
    return out


def _chunks(words, lang):
    maxc = 14 if lang in LONG_WORD_LANGS else 20
    out, cur = [], []
    for w in words:
        if cur and (len(" ".join(x["w"] for x in cur + [w])) > maxc or len(cur) >= 3 or cur[-1]["w"][-1:] in ".!?…,"):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def _caption_frame(path, chunk, active, accent, banner=""):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if banner:
        bf = _font(56)
        lines = _wrap(d, banner, bf, W - 260)[:3]
        y = SAFE_TOP
        for ln in lines:
            tw = d.textlength(ln, font=bf)
            x = (W - 180 - tw) / 2 + 40
            d.rounded_rectangle([x - 22, y - 10, x + tw + 22, y + 66], 16, fill=(0, 0, 0, 170))
            d.text((x, y), ln, font=bf, fill=(255, 255, 255, 255))
            y += 82
    if chunk:
        text = " ".join(w["w"] for w in chunk)
        size = 92
        font = _font(size)
        while d.textlength(text.upper(), font=font) > W - 260 and size > 50:
            size -= 6
            font = _font(size)
        words = [w["w"].upper() for w in chunk]
        space = d.textlength(" ", font=font)
        total = sum(d.textlength(w, font=font) for w in words) + space * (len(words) - 1)
        x = (W - 180 - total) / 2 + 40
        for i, w in enumerate(words):
            col = accent if i == active else (255, 255, 255)
            d.text((x, CAP_Y), w, font=font, fill=col + (255,), stroke_width=7, stroke_fill=(0, 0, 0, 255))
            x += d.textlength(w, font=font) + space
    img.save(path)


def broll_video(scenes, shots, voice, out, accent="#FF6B00", lang="", text="", music=None):
    """Obal: pridá animácie (ak sú v scenári a Chromium je pripravené)."""
    from . import anim, brand
    total = duration(voice) or 10
    n = max(1, len(scenes))
    per = total / n
    anims = []
    for i, sc in enumerate(scenes):
        a = sc.get("anim")
        if isinstance(a, dict) and a.get("t") in anim.TYPES and anim.available():
            d = dict(a.get("d") or {})
            d.setdefault("comma", lang not in ("en", "ga", "mt", "cy"))
            try:
                mov = anim.render(a["t"], d, accent, min(per, 4.0), font=brand.current_font())
                if mov:
                    anims.append((i * per, min(per, 4.0), mov, i))
            except Exception as e:
                print("animácia:", e)
    return _broll(scenes, shots, voice, out, accent, lang, text, music, anims)


def _broll(scenes, shots, voice, out, accent, lang, text, music, anims):
    """Strih zo záberov: každé 2-3 s nový záber, fotky v pohybe (Ken Burns), titulky slovo po slove, hudba potichu."""
    import random
    import tempfile
    ff = ffmpeg()
    total = duration(voice) or 10
    acc = _hex(accent)
    pool = [[db.one("SELECT * FROM footage WHERE id=?", (fid,)) for fid in ids] for ids in shots]
    pool = [[f for f in p if f and Path(f["path"]).exists()] for p in pool]
    flat = [f for p in pool for f in p]
    if not flat:
        raise RuntimeError("Nenašiel som žiadne zábery (zadaj kľúč Pexels/Pixabay alebo pridaj vlastné zábery)")
    n = max(1, len(scenes))
    per = total / n
    rnd = random.Random(str(out))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clips, t, k = [], 0.0, 0
        for i in range(n):
            cand = pool[i] if i < len(pool) and pool[i] else flat
            cuts = max(1, round(per / 2.6))
            for c in range(cuts):
                dur = per / cuts
                if i == n - 1 and c == cuts - 1:
                    dur = total - t + 0.3
                f = cand[c % len(cand)]
                cp = tmp / f"c{k:03d}.mp4"
                if f["kind"] == "photo":
                    frames = max(1, int(dur * 30))
                    zin = rnd.choice(["min(zoom+0.0011,1.15)", "if(eq(on,0),1.15,max(zoom-0.0011,1.0))"])
                    vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
                          f"zoompan=z='{zin}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,setsar=1")
                    _run_ff([ff, "-y", "-i", f["path"], "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "23", "-pix_fmt", "yuv420p", "-an", str(cp)])
                else:
                    fd = f["dur"] or duration(f["path"]) or dur
                    start = 0.5 if (i == 0 and c == 0) else max(0.0, rnd.uniform(0, max(0.0, fd - dur - 0.2)))
                    _run_ff([ff, "-y", "-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", f["path"], "-t", f"{dur:.3f}",
                             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-an", str(cp)])
                clips.append(cp)
                t += dur
                k += 1
        lst = tmp / "clips.txt"
        lst.write_text("".join(f"file '{c}'\n" for c in clips))
        body = tmp / "body.mp4"
        _run_ff([ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(body)])
        # titulky: jeden priehľadný obrázok na každé slovo, poskladané do priehľadnej video vrstvy
        words = word_times(voice, text)
        frames, cur = [], 0.0
        blank = tmp / "blank.png"
        anim_scenes = {a[3] for a in anims}
        banner_at = lambda tt: "" if not scenes or min(n - 1, int(tt / per)) in anim_scenes else (scenes[min(n - 1, int(tt / per))].get("onscreen") or "").strip()
        idx = 0
        for ch in _chunks(words, lang):
            for j, w in enumerate(ch):
                s0 = w["s"]
                e0 = ch[j + 1]["s"] if j + 1 < len(ch) else w["e"] + 0.15
                if s0 > cur + 0.02:
                    p = tmp / f"g{idx:04d}.png"
                    _caption_frame(p, None, -1, acc, banner_at(cur))
                    frames.append((p, s0 - cur))
                    idx += 1
                p = tmp / f"w{idx:04d}.png"
                _caption_frame(p, ch, j, acc, banner_at(s0))
                frames.append((p, max(0.04, e0 - s0)))
                cur = s0 + max(0.04, e0 - s0)
                idx += 1
        _caption_frame(blank, None, -1, acc, "")
        frames.append((blank, max(0.1, total - cur + 0.5)))
        cl = tmp / "caps.txt"
        cl.write_text("".join(f"file '{p}'\nduration {d:.3f}\n" for p, d in frames) + f"file '{blank}'\n")
        caps = tmp / "caps.mov"
        _run_ff([ff, "-y", "-f", "concat", "-safe", "0", "-i", str(cl), "-vf", "fps=30,format=rgba", "-c:v", "png", str(caps)])
        cmd = [ff, "-y", "-i", str(body), "-i", str(caps), "-i", str(voice)]
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            afil = "[3:a]volume=0.12[m];[2:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        else:
            afil = "[2:a]anull[a]"
        vchain, last, idx0 = "", "[0:v]", 4 if music else 3
        for j, (st, du, mov, _) in enumerate(anims):
            cmd += ["-itsoffset", f"{st:.3f}", "-i", mov]
            vchain += f"{last}[{idx0 + j}:v]overlay=0:0:format=auto:eof_action=pass:enable='between(t,{st:.2f},{st + du:.2f})'[a{j}];"
            last = f"[a{j}]"
        vchain += f"{last}[1:v]overlay=0:0:format=auto,format=yuv420p[v]"
        cmd += ["-filter_complex", f"{vchain};{afil}", "-map", "[v]", "-map", "[a]",
                "-t", f"{total + 0.2:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", "30",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
        _run_ff(cmd)
    return str(out)


def _ts(t):
    ms = int(round(max(0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(voice, text):
    """Titulky (SRT) z presného textu hlasu a časov slov: po vetách, max. 2 riadky po ~42 znakov a 7 s."""
    words = word_times(voice, text)
    cues, cur = [], []
    for w in words:
        if cur and (len(" ".join(x["w"] for x in cur + [w])) > 84 or w["e"] - cur[0]["s"] > 7):
            cues.append(cur)
            cur = []
        cur.append(w)
        if w["w"][-1:] in ".!?…" and len(" ".join(x["w"] for x in cur)) > 20:
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    out = []
    for i, c in enumerate(cues, 1):
        line = " ".join(x["w"] for x in c)
        if len(line) > 42:  # rozdeliť na dva riadky pri medzere najbližšie stredu
            mid = len(line) // 2
            sp = min((k for k, ch in enumerate(line) if ch == " "), key=lambda k: abs(k - mid), default=-1)
            if sp > 0:
                line = line[:sp] + "\n" + line[sp + 1:]
        end = c[-1]["e"] + 0.3
        if i < len(cues):
            end = min(end, cues[i][0]["s"])
        out.append(f"{i}\n{_ts(c[0]['s'])} --> {_ts(end)}\n{line}\n")
    return "\n".join(out)
