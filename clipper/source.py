"""Zdrojové video kampane: stiahnutie a prepis reči s časmi slov."""
import json
import re
import shutil
import subprocess
from pathlib import Path

from app import media

from . import env, store

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
NOISE = re.compile(r"\[[^\]]*\]|\([^)]*\)")        # [Music], (Laughter), (Audience applauds): zvuky, nie reč
REACT = re.compile(r"laugh|applau|cheer|chuckl|smiech|potlesk|lach|rire|risa", re.I)   # reakcia publika: do titulkov nie, ale klip ju má nechať dobehnúť


def _sec(v):
    """'1:06:07', '45:50', '1h6m7s', '3967s' alebo '3967' -> sekundy."""
    v = (v or "").strip().lower()
    if not v:
        return None
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", v)
    if m and any(m.groups()):
        h, mi, se = (int(x or 0) for x in m.groups())
        return h * 3600 + mi * 60 + se
    if re.fullmatch(r"\d+(?::\d{1,2}){0,2}", v):
        t = 0
        for x in v.split(":"):
            t = t * 60 + int(x)
        return t
    return None


def span(url):
    """Ktorú časť zdroja kampaň dovoľuje strihať. Za odkazom môže byť @od-do (napr. @1:06:07-3:03:10 alebo @45:50-);
    inak sa berie začiatok z odkazu (?t=10589s). Vráti (čistý odkaz, od, do), do = None znamená po koniec."""
    url = (url or "").strip()
    a, b = 0.0, None
    m = re.search(r"@([\dhms:]*)-([\dhms:]*)$", url)
    if m and not Path(url).expanduser().exists():
        url = url[:m.start()]
        a, b = float(_sec(m.group(1)) or 0), _sec(m.group(2))
    else:
        t = re.search(r"[?&#]t=([\dhms:]+)", url)
        if t:
            a = float(_sec(t.group(1)) or 0)
    if t := re.search(r"[?&]t=[\dhms:]+", url):
        url = (url[:t.start()] + ("?" if t.group(0)[0] == "?" else "") + url[t.end():].lstrip("&")).rstrip("?&")
    return url, a, (float(b) if b else None)


def add(campaign_id, url):
    url = (url or "").strip()
    if not url:
        raise RuntimeError("Chýba odkaz na zdrojové video.")
    ex = store.one("SELECT id FROM sources WHERE campaign_id=? AND url=?", (campaign_id, url))
    if ex:
        return ex["id"]
    return store.run("INSERT INTO sources(campaign_id, url) VALUES(?,?)", (campaign_id, url))


def _from_json3(path):
    """Titulky YouTube (json3) -> slová s časmi. Automatické titulky majú čas pri každom slove."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []
    words = []
    for ev in data.get("events", []):
        segs = [dict(s, utf8=NOISE.sub(lambda m: " (laughter) " if REACT.search(m.group(0)) else " ", s.get("utf8") or ""))
                for s in (ev.get("segs") or [])]
        segs = [s for s in segs if s["utf8"].strip()]
        if not segs:
            continue
        t0 = (ev.get("tStartMs") or 0) / 1000
        dur = (ev.get("dDurationMs") or 0) / 1000
        timed = any("tOffsetMs" in s for s in segs) or len(segs) > 1
        if timed:
            for i, s in enumerate(segs):
                st = t0 + (s.get("tOffsetMs") or 0) / 1000
                for tok in s["utf8"].split():
                    words.append({"w": tok, "s": round(st, 3), "e": 0})
        else:   # ručné titulky: čas len na celý riadok, slová sa rozložia rovnomerne podľa dĺžky
            toks = segs[0]["utf8"].replace("\n", " ").split()
            total = sum(len(x) + 1 for x in toks) or 1
            st = t0
            for tok in toks:
                d = max(0.08, dur * (len(tok) + 1) / total)
                words.append({"w": tok, "s": round(st, 3), "e": round(st + d * 0.9, 3)})
                st += d
    words.sort(key=lambda w: w["s"])
    out = []
    for i, w in enumerate(words):
        if w["w"].startswith("[") and w["w"].endswith("]"):   # [Music], [Applause]
            continue
        if not w["e"]:
            nxt = words[i + 1]["s"] if i + 1 < len(words) else w["s"] + 0.4
            w["e"] = round(min(nxt, w["s"] + 0.9) if nxt > w["s"] else w["s"] + 0.3, 3)
        out.append(w)
    return out


def _probe(path):
    return media.duration(path) or 0


def fetch(src):
    """Stiahne video (alebo vezme súbor z disku) a pripraví slová s časmi. Vráti aktualizovaný riadok zdroja."""
    camp = store.campaign(src["campaign_id"]) or {}
    lang = (camp.get("lang") or "en")[:2]
    out_dir = store.DIR / "src" / str(src["id"])
    out_dir.mkdir(parents=True, exist_ok=True)
    url = span(src["url"])[0]
    subs = ""
    if Path(url).expanduser().exists() and Path(url).suffix.lower() in VIDEO_EXT:
        path = Path(url).expanduser()
        title, dur = path.stem, _probe(path)
    else:
        r = env.tool("fetch", [url, out_dir, media.ffmpeg() or "ffmpeg", lang, store.get("max_height", 1080)], timeout=3 * 3600)
        path, title, dur, subs = Path(r["path"]), r.get("title") or "", float(r.get("duration") or 0), r.get("subs") or ""
        dur = dur or _probe(path)
    store.run("UPDATE sources SET path=?, title=?, duration=?, status='transcribing', error='' WHERE id=?",
              (str(path), title[:300], dur, src["id"]))
    words = _from_json3(subs) if subs else []
    want = camp.get("kind") or "auto"
    holes = len(words) < max(30, dur / 6)                    # titulky chýbajú alebo sú deravé
    from .moments import punctuated
    blind = len(words) >= 60 and not punctuated(words)       # automatické titulky bez bodiek: nevidno, kde sa veta končí
    if want != "visual" and (holes or blind):                # prepis reči na tomto počítači (zadarmo)
        wav = out_dir / "audio.wav"
        try:
            media._run_ff([media.ffmpeg(), "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
            wj = out_dir / "stt.json"
            r = env.tool("stt", [wav, wj, lang or "auto", store.get("stt_model", "small")], timeout=6 * 3600)
            words = json.loads(wj.read_text(encoding="utf-8"))
            lang = (r.get("lang") or lang)[:2]
        except Exception:
            if holes:
                raise
        finally:
            wav.unlink(missing_ok=True)
    per_min = len(words) / max(1.0, dur / 60)
    kind = "visual" if want == "visual" or (want == "auto" and per_min < 60) else "speech"   # rozhovor má 130 až 180 slov za minútu
    if kind == "speech" and len(words) < 20:
        raise RuntimeError("Vo videu som nenašiel reč. Ak je to trailer, hra alebo šport, nastav v kampani zdroj „obraz“.")
    wp = out_dir / "words.json"
    wp.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    store.run("UPDATE sources SET words_path=?, lang=?, kind=?, status='ready', error='' WHERE id=?", (str(wp), lang, kind, src["id"]))
    return store.one("SELECT * FROM sources WHERE id=?", (src["id"],))


def _raw(src):
    try:
        return json.loads(Path(src["words_path"]).read_text(encoding="utf-8"))
    except Exception:
        return []


def _split(ws):
    """Rozdelí prepis na reč a na poznámky v zátvorkách ([Music], (Laughter), [text na plátne], aj cez viac slov).
    Vráti (slová reči, [(začiatok, koniec, je to reakcia publika)])."""
    speech, notes, i = [], [], 0
    while i < len(ws):
        tok = ws[i]["w"]
        close = {"[": "]", "(": ")"}.get(tok[:1])
        if close:
            j = i
            while j < len(ws) - 1 and j - i < 25 and close not in ws[j]["w"]:
                j += 1
            if close in ws[j]["w"]:
                notes.append((" ".join(w["w"] for w in ws[i:j + 1]), ws[i]["s"], ws[j]["e"]))
                i = j + 1
                continue
        speech.append(ws[i])
        i += 1
    return speech, [(a, b, bool(REACT.search(text))) for text, a, b in notes]


def _inside(src, a, b):
    _, x, y = span(src.get("url"))
    return a >= x - 0.01 and (y is None or b <= y + 0.01)


def words(src):
    return [w for w in _split(_raw(src))[0] if _inside(src, w["s"], w["e"])]


def notes(src):
    """Poznámky v prepise mimo reči: [(začiatok, koniec, je to reakcia publika)]. Smiech a potlesk, ale aj hudba či text na plátne."""
    return [n for n in _split(_raw(src))[1] if _inside(src, n[0], n[1])]


def reactions(src):
    """Kde sa publikum smeje alebo tlieska (podľa titulkov): [(začiatok, koniec)], susedné spojené."""
    out = []
    for a, b, react in notes(src):
        if react:
            if out and a - out[-1][1] < 1.5:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
    return out


def heat(src):
    """Najviac prehrávané časti videa podľa YouTube: [(začiatok, koniec, sila 0-1)]. Prázdne, ak ich video nemá."""
    try:
        rows = json.loads((store.DIR / "src" / str(src["id"]) / "heat.json").read_text(encoding="utf-8"))
        return [tuple(x) for x in rows if _inside(src, x[0], x[1])]
    except Exception:
        return []


def drop_files(src):
    """Zdroj je vyťažený: veľké video sa z disku zmaže, prepis ostáva."""
    d = store.DIR / "src" / str(src["id"])
    p = Path(src.get("path") or "")
    try:
        if p.exists() and d in p.parents:
            p.unlink()
    except Exception:
        pass
