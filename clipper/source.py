"""Zdrojové video kampane: stiahnutie a prepis reči s časmi slov."""
import json
import shutil
import subprocess
from pathlib import Path

from app import media

from . import env, store

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


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
        segs = [s for s in (ev.get("segs") or []) if (s.get("utf8") or "").strip()]
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
    url = src["url"]
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
    if want != "visual" and len(words) < max(30, dur / 6):   # titulky chýbajú alebo sú deravé: prepis reči na tomto počítači
        wav = out_dir / "audio.wav"
        media._run_ff([media.ffmpeg(), "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
        wj = out_dir / "stt.json"
        r = env.tool("stt", [wav, wj, lang or "auto", store.get("stt_model", "small")], timeout=6 * 3600)
        words = json.loads(wj.read_text(encoding="utf-8"))
        wav.unlink(missing_ok=True)
        lang = (r.get("lang") or lang)[:2]
    per_min = len(words) / max(1.0, dur / 60)
    kind = "visual" if want == "visual" or (want == "auto" and per_min < 60) else "speech"   # rozhovor má 130 až 180 slov za minútu
    if kind == "speech" and len(words) < 20:
        raise RuntimeError("Vo videu som nenašiel reč. Ak je to trailer, hra alebo šport, nastav v kampani zdroj „obraz“.")
    wp = out_dir / "words.json"
    wp.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    store.run("UPDATE sources SET words_path=?, lang=?, kind=?, status='ready', error='' WHERE id=?", (str(wp), lang, kind, src["id"]))
    return store.one("SELECT * FROM sources WHERE id=?", (src["id"],))


def words(src):
    try:
        return json.loads(Path(src["words_path"]).read_text(encoding="utf-8"))
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
