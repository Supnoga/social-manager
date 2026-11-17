"""Stiahne zdrojové video (odkaz z kampane) a titulky s časmi slov, ak ich zdroj má.
    python fetch.py <url> <priečinok> <ffmpeg> <jazyk> <max výška>
Výsledok (posledný riadok): {"path","title","duration","subs","lang","id"} alebo {"error"}.
Ak YouTube pri videu ukazuje „najviac prehrávané“, uloží ich do heat.json: [[začiatok, koniec, sila 0-1], ...]."""
import json
import sys
from pathlib import Path


VIDEO = (".mp4", ".mov", ".m4v", ".webm", ".mkv")


def drive(url, out):
    """Google Drive: priečinok (stiahne všetky videá) alebo jeden súbor. Kampane tam často dávajú zábery."""
    import gdown
    out.mkdir(parents=True, exist_ok=True)
    if "/folders/" in url:
        try:
            got = gdown.download_folder(url, output=str(out), quiet=True, remaining_ok=True) or []
        except TypeError:        # novší gdown tento parameter nemá
            got = gdown.download_folder(url, output=str(out), quiet=True) or []
    else:
        got = [gdown.download(url, output=str(out) + "/", quiet=True, fuzzy=True)]
    files = sorted(str(Path(f)) for f in got if f and Path(f).suffix.lower() in VIDEO and Path(f).exists())
    if not files:
        print(json.dumps({"error": "na Google Drive som nenašiel video (alebo priečinok nie je zdieľaný odkazom)"}))
        return
    p = Path(files[0])
    print(json.dumps({"path": str(p), "title": p.stem, "duration": 0, "subs": "", "lang": "", "id": p.stem, "files": files}))


def main():
    url, out, ff, lang, height = sys.argv[1:6]
    if "drive.google.com" in url:
        return drive(url, Path(out))
    import yt_dlp
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(out / "%(id)s.%(ext)s"),
        # H.264 má prednosť: prečíta ho každý nástroj, strihá sa rýchlo a nikdy nie je HDR (vyblednuté farby); AV1 až keď H.264 nie je
        "format": (f"bv*[height<={height}][vcodec^=avc1]+ba[ext=m4a]/bv*[height<={height}][ext=mp4]+ba[ext=m4a]/"
                   f"bv*[height<={height}]+ba/b[height<={height}]/b"),
        "merge_output_format": "mp4",
        "ffmpeg_location": ff,
        "noplaylist": True,
        "quiet": True, "no_warnings": True, "noprogress": True,
        "writesubtitles": True, "writeautomaticsub": True,
        "subtitleslangs": [lang, f"{lang}-orig", f"{lang}.*"],
        "subtitlesformat": "json3",
        "retries": 5, "fragment_retries": 5,
        "ignoreerrors": False,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(url, download=True)
            if info.get("_type") == "playlist" and info.get("entries"):
                info = info["entries"][0]
            path = Path(y.prepare_filename(info)).with_suffix(".mp4")
    except Exception as e:
        # titulky občas zlyhajú (limit): video je dôležitejšie, skús ešte raz bez nich
        try:
            opts.update(writesubtitles=False, writeautomaticsub=False)
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(url, download=True)
                if info.get("_type") == "playlist" and info.get("entries"):
                    info = info["entries"][0]
                path = Path(y.prepare_filename(info)).with_suffix(".mp4")
        except Exception as e2:
            print(json.dumps({"error": str(e2)[-300:] or str(e)[-300:]}))
            return
    if not path.exists():
        cand = sorted(out.glob(f"{info.get('id')}.*"), key=lambda p: p.stat().st_size, reverse=True)
        cand = [c for c in cand if c.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")]
        if not cand:
            print(json.dumps({"error": "video sa nestiahlo"}))
            return
        path = cand[0]
    try:
        heat = [[round(float(h["start_time"]), 1), round(float(h["end_time"]), 1), round(float(h["value"]), 3)]
                for h in (info.get("heatmap") or [])]
        if heat:
            (out / "heat.json").write_text(json.dumps(heat), encoding="utf-8")
    except Exception:
        pass
    subs = ""
    for s in sorted(out.glob(f"{info.get('id')}.*.json3")):
        subs = str(s)
        if f".{lang}." in s.name:
            break
    print(json.dumps({"path": str(path), "title": info.get("title") or "", "duration": float(info.get("duration") or 0),
                      "subs": subs, "lang": (info.get("language") or lang or "")[:2], "id": str(info.get("id") or "")}))


if __name__ == "__main__":
    main()
