"""Zvuk videí: hudba v pozadí, jemné zvukové efekty, čistý a dosť hlasný hlas, obraz zosúladený s hlasom.

Bez AI a zadarmo – všetko robí ffmpeg. Hudba a efekty sú zabudované (app/sound, vlastné, bez licencií);
keď si používateľ dá vlastnú hudbu do priečinka Hudba, má prednosť.

- scene_times(): scény sa striedajú podľa toho, o čom hlas práve hovorí (porovná texty scény s vetami).
- finish(): do hotového videa namieša hlas + hudbu (pod hlasom sa stíši) + efekty a vyrovná hlasitosť
  na úroveň bežnú na sieťach (-14 LUFS, stereo 48 kHz)."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse

from . import db

router = APIRouter()

SOUND = Path(__file__).resolve().parent / "sound"
MOODS = {"calm": "hudba-pokojna.ogg", "drive": "hudba-energicka.ogg", "ambient": "hudba-ambient.ogg"}
MOOD_NAMES = {"auto": "Automaticky", "calm": "Pokojná", "drive": "Energickejšia", "ambient": "Ambientná (bez rytmu)",
              "own": "Len moja hudba (priečinok Hudba)", "off": "Bez hudby"}
LEVELS = {"low": -5.0, "mid": 0.0, "high": 4.0}
TARGET = -14.0      # hlasitosť hotového videa (LUFS) – tak to majú TikTok, Reels aj Shorts
VOICE_LUFS = -16.0


def opts():
    o = db.get_setting("sound", {}) or {}
    return {"music": o.get("music") if o.get("music") in MOOD_NAMES else "auto",
            "level": o.get("level") if o.get("level") in LEVELS else "mid",
            "fx": bool(o.get("fx", True))}


def save_opts(data):
    o = opts()
    for k in ("music", "level"):
        if k in data:
            o[k] = data[k]
    if "fx" in data:
        o["fx"] = bool(data["fx"])
    db.set_setting("sound", o)
    return opts()


def info():
    return {**opts(), "moods": MOOD_NAMES, "samples": {k: str(SOUND / v) for k, v in MOODS.items()}}


def pick_music(seed=0):
    """Hudba pre video: vlastná z priečinka Hudba má prednosť, inak zabudovaná. Rovnaká pre všetky jazyky nápadu."""
    o = opts()
    if o["music"] == "off":
        return None
    if o["music"] in ("auto", "own"):
        try:
            from . import footage
            own = footage.music_track(seed)
            if own:
                return own
        except Exception:
            pass
        if o["music"] == "own":
            return None
    mood = o["music"] if o["music"] in MOODS else ("calm", "drive", "calm", "ambient")[int(seed or 0) % 4]
    f = SOUND / MOODS[mood]
    return str(f) if f.exists() else None


# ---------- obraz podľa hlasu ----------
def _tokens(text):
    out = set()
    for w in re.findall(r"[^\W_]+", (text or "").lower()):
        if w.isdigit():
            out.add(w)
        elif len(w) >= 4:
            out.add(w[:5])
    return out


def _strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield str(int(x)) if float(x).is_integer() else str(x).replace(".", " ")
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in ("k", "t"):
                yield from _strings(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _strings(v)


def sentences(words):
    """Vety s časmi z časovania slov: [{'s','e','t'}]."""
    out, cur = [], []
    for w in words or []:
        cur.append(w)
        if (w.get("w") or "")[-1:] in ".!?…":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"s": c[0]["s"], "e": c[-1]["e"], "t": " ".join(x["w"] for x in c)} for c in out]


def scene_times(scenes, words, total):
    """Kedy má ísť ktorá scéna: zoskupí vety k scénam podľa spoločných slov (poradie ostáva), inak približne rovnomerne.
    Vráti [(od, do)] alebo None, keď sa to nedá určiť (málo viet)."""
    n = len(scenes or [])
    sents = sentences(words)
    m = len(sents)
    if n < 2 or m < n:
        return None
    stoks = [_tokens(s["t"]) for s in sents]
    df = {}
    for t in stoks:
        for x in t:
            df[x] = df.get(x, 0) + 1
    sim = []
    for sc in scenes:
        a = sc.get("anim") if isinstance(sc.get("anim"), dict) else {}
        tk = _tokens(" ".join([sc.get("onscreen") or ""] + list(_strings(a.get("d")))))
        sim.append([sum(1.0 / df[x] for x in tk & st) for st in stoks])
    ideal = total / n
    NEG = -1e9
    # best[i][j] = najlepšie skóre, keď prvých i scén pokrýva prvých j viet
    best = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, m - (n - i) + 1):
            for k in range(i - 1, j):
                if best[i - 1][k] <= NEG:
                    continue
                dur = sents[j - 1]["e"] - sents[k]["s"]
                sc = sum(sim[i - 1][k:j]) - 0.7 * abs(dur - ideal) / ideal - (4.0 if dur < 1.3 else 0.0)
                if best[i - 1][k] + sc > best[i][j]:
                    best[i][j], back[i][j] = best[i - 1][k] + sc, k
    if best[n][m] <= NEG:
        return None
    cuts, j = [], m
    for i in range(n, 0, -1):
        k = back[i][j]
        cuts.append(k)
        j = k
    cuts = cuts[::-1]          # index prvej vety každej scény
    edges = [0.0]
    for c in cuts[1:]:
        edges.append(round((sents[c - 1]["e"] + sents[c]["s"]) / 2, 3))   # strih v pauze medzi vetami
    edges.append(total + 0.3)
    return [(edges[i], edges[i + 1]) for i in range(n)]


# ---------- miešanie ----------
def _ff():
    from . import media
    return media.ffmpeg()


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-500:])
    return r.stderr


def loudness(path):
    """Hlasitosť súboru v LUFS (None, keď sa nedá zmerať alebo je ticho)."""
    try:
        err = _run([_ff(), "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"])
        m = re.findall(r"I:\s*(-?[\d.]+) LUFS", err)
        v = float(m[-1]) if m else None
        return v if v is not None and v > -60 else None
    except Exception:
        return None


def finish(video, voice, cuts=None, seed=0, music=True, end_at=None):
    """Nahradí zvuk hotového videa: hlas (vyčistený, vyrovnaný) + hudba + efekty, nahlas ako iné videá na sieťach.
    cuts = časy striedania scén (pre zvuk prechodu). Obraz sa nemení (kopíruje sa), trvá to pár sekúnd."""
    from . import media
    ff = _ff()
    video, voice = Path(video), Path(voice)
    if not ff or not video.exists() or not voice.exists():
        return False
    total = media.duration(video)
    vdur = media.duration(voice)
    if total < 1 or vdur < 0.5:
        return False
    o = opts()
    track = pick_music(seed) if music else None
    vl = loudness(voice)
    vgain = max(-12.0, min(16.0, VOICE_LUFS - vl)) if vl is not None else 0.0
    cmd = [ff, "-y", "-hide_banner", "-i", str(voice)]
    # hlas: odreže dunenie, trochu zrozumiteľnosti a „vzduchu“, jemne vyrovná hlasné a tiché miesta
    fc = [f"[0:a]aresample=48000,volume={vgain:.2f}dB,highpass=f=75,equalizer=f=250:t=q:w=1.2:g=-1.5,"
          "equalizer=f=4200:t=q:w=1.4:g=2,treble=g=1.5:f=8500,"
          "acompressor=threshold=-18dB:ratio=2.5:attack=6:release=140:makeup=2dB,"
          "aformat=channel_layouts=stereo,asplit=2[v][key]"]
    mix, idx = ["[v]"], 1
    if track:
        cmd += ["-stream_loop", "-1", "-i", str(track)]
        ml = loudness(track) if not str(track).startswith(str(SOUND)) else -16.0
        mgain = (-16.0 - (ml if ml is not None else -16.0)) - 16.0 + LEVELS[o["level"]]
        tail = max(0.0, total - vdur)
        fade = min(1.6, max(0.7, tail if tail > 0.5 else 0.9))
        fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},volume={mgain:.2f}dB,"
                  f"highpass=f=90,equalizer=f=2600:t=q:w=1.2:g=-3,afade=t=in:d=0.35,"
                  f"afade=t=out:st={max(0.0, total - fade):.3f}:d={fade:.3f}[m0];"
                  f"[m0][key]sidechaincompress=threshold=0.035:ratio=5:attack=25:release=450:makeup=1[m]")
        mix.append("[m]")
        idx += 1
    else:
        fc.append("[key]anullsink")
    if o["fx"] and music:
        fx = []
        hitf = SOUND / "fx-uder.ogg"
        if hitf.exists():
            fx.append((hitf, 0.0, -9.0))
        wh = [f for f in (SOUND / "fx-prechod-1.ogg", SOUND / "fx-prechod-2.ogg") if f.exists()]
        last = -9.0
        marks = sorted(set(round(float(t), 2) for t in (cuts or []) if 1.0 < float(t) < vdur - 0.8))
        if end_at is None and total - vdur > 1.0:
            end_at = vdur + 0.1                      # záverečná karta po skončení hlasu
        if end_at:
            marks.append(float(end_at))
        for k, t in enumerate(marks):
            if wh and t - last >= 1.6:
                fx.append((wh[k % len(wh)], max(0.0, t - 0.30), -10.0))
                last = t
        for f, t, g in fx[:40]:
            cmd += ["-i", str(f)]
            ms = int(t * 1000)
            fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g:.1f}dB,adelay={ms}|{ms}[f{idx}]")
            mix.append(f"[f{idx}]")
            idx += 1
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:dropout_transition=0:normalize=0,"
              f"apad,atrim=0:{total:.3f},alimiter=limit=0.9:attack=4:release=80:level=false[a]")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "mix.wav"
        _run(cmd + ["-filter_complex", ";".join(fc), "-map", "[a]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav)])
        cur = loudness(wav)
        gain = max(-10.0, min(10.0, TARGET - cur)) if cur is not None else 0.0
        out = Path(tmp) / ("out" + video.suffix)
        _run([ff, "-y", "-hide_banner", "-i", str(video), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
              "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89:attack=3:release=60:level=false",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
              "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)])
        shutil.move(str(out), str(video))
    return True


# ---------- nastavenia (Nastavenia → Zvuk videí) ----------
@router.get("/api/sound")
def sound_get():
    from . import footage
    try:
        own = footage.status().get("music", 0)
    except Exception:
        own = 0
    from . import verbal
    return {**opts(), "moods": MOOD_NAMES, "own": own, "numbers": verbal.stats()}


@router.post("/api/sound")
def sound_save(data: dict = Body(...)):
    if "numbers" in data:
        db.set_setting("verbal_on", bool(data["numbers"]))
    return save_opts(data)


@router.get("/api/sound/sample/{mood}")
def sound_sample(mood: str):
    f = SOUND / MOODS.get(mood, "")
    if mood not in MOODS or not f.exists():
        raise HTTPException(404)
    return FileResponse(f, media_type="audio/ogg")
