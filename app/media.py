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
    for f in FONT_CANDIDATES:
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
