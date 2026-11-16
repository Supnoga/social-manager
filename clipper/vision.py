"""Výber momentov podľa obrazu a zvuku: pre videá bez reči (trailery, hry, šport, zábery produktov).

Lacno: miesta, kde sa niečo deje, nájde tento počítač sám (hlasitosť, pohyb, strihy). Claude potom dostane jediný
malý obrázok so zábermi z tých miest a vyberie najlepšie. Celé video sa do AI nikdy neposiela."""
import json
import re
import subprocess
from pathlib import Path

from app import ai, media

from . import env, source, store

MAX_CAND = 12
TW, TH = 256, 144        # jeden záber na obrázku


def scan(src):
    """Hlasitosť, pohyb a strihy po sekundách. Počíta sa raz, výsledok ostáva pri zdroji."""
    p = Path(src["path"])
    out = store.DIR / "src" / str(src["id"]) / "scan.json"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        env.tool("scan", [p, out, media.ffmpeg() or "ffmpeg"], timeout=3 * 3600)
    return json.loads(out.read_text(encoding="utf-8"))


def _z(xs):
    n = len(xs) or 1
    m = sum(xs) / n
    sd = (sum((x - m) ** 2 for x in xs) / n) ** 0.5 or 1.0
    return [max(-2.0, min(3.0, (x - m) / sd)) for x in xs]


def _snap(t, cuts, slack):
    """Najbližší strih k času t (do `slack` sekúnd), aby klip nezačínal ani nekončil uprostred záberu."""
    near = [c for c in cuts if abs(c - t) <= slack]
    return min(near, key=lambda c: abs(c - t)) if near else t


def candidates(sig, lo, hi, taken, n=MAX_CAND):
    """Najživšie úseky videa: zoznam (začiatok, koniec, sila), bez prekrývania a mimo už použitých miest."""
    dur = int(sig.get("dur") or 0)
    loud = [x if x > -90 else -60.0 for x in sig.get("loud") or []][:dur]
    if dur < max(8, lo) or len(loud) < dur:
        return []
    score = [a + b for a, b in zip(_z(loud), _z((sig.get("motion") or [0.0] * dur)[:dur]))]
    length = int(max(lo, min(hi, (lo + hi) / 2, dur)))
    sums, acc = [], sum(score[:length])
    for s in range(0, dur - length + 1):
        if s:
            acc += score[s + length - 1] - score[s - 1]
        sums.append((acc / length, s))
    cuts = sig.get("cuts") or []
    out, used = [], [(a, b) for a, b in taken]
    for val, s in sorted(sums, reverse=True):
        if len(out) >= n:
            break
        t0 = max(0.0, _snap(s, cuts, 3))
        t1 = min(float(dur), _snap(s + length, cuts, 3))
        if t1 - t0 < lo * 0.8:
            t1 = min(float(dur), t0 + length)
        if t1 - t0 > hi:
            t1 = t0 + hi
        if any(min(t1, b) - max(t0, a) > 0.25 * min(t1 - t0, b - a) for a, b in used):
            continue
        used.append((t0, t1))
        out.append((round(t0, 2), round(t1, 2), round(val, 2)))
    return sorted(out)


def sheet(src_path, cands, out):
    """Jeden obrázok: každý úsek má číslo a tri zábery (začiatok, stred, koniec)."""
    from PIL import Image, ImageDraw
    ff = media.ffmpeg()
    tmp = Path(out).parent
    cols = 2 if len(cands) > 4 else 1
    rows = (len(cands) + cols - 1) // cols
    cw, chh = TW * 3 + 8, TH + 8
    img = Image.new("RGB", (cols * cw, rows * chh), (0, 0, 0))
    d = ImageDraw.Draw(img)
    font = media._font(40)
    for i, (t0, t1, _) in enumerate(cands):
        x0, y0 = (i % cols) * cw, (i // cols) * chh
        for k, f in enumerate((0.12, 0.5, 0.88)):
            fp = tmp / f"f{i}_{k}.jpg"
            subprocess.run([ff, "-v", "error", "-y", "-ss", f"{t0 + (t1 - t0) * f:.2f}", "-i", str(src_path), "-frames:v", "1",
                            "-vf", f"scale={TW}:{TH}:force_original_aspect_ratio=decrease,pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2",
                            str(fp)], capture_output=True, stdin=subprocess.DEVNULL, start_new_session=True, timeout=120)
            if fp.exists():
                try:
                    img.paste(Image.open(fp).convert("RGB"), (x0 + k * TW, y0))
                except Exception:
                    pass
                fp.unlink(missing_ok=True)
        d.rectangle([x0, y0, x0 + 58, y0 + 50], fill=(255, 107, 0))
        d.text((x0 + 8, y0 + 2), str(i + 1), font=font, fill=(0, 0, 0))
    img.save(out, quality=82)
    return out


def _said(words, t0, t1):
    return " ".join(w["w"] for w in words if t0 <= w["s"] < t1)[:160]


def pick(src, want):
    """Vyberie až `want` momentov podľa obrazu a uloží ich ako klipy na strih. Vráti počet."""
    camp = store.campaign(src["campaign_id"])
    if want <= 0 or not Path(src.get("path") or "").exists():
        return 0
    lo, hi = int(camp.get("clip_min") or 15), int(camp.get("clip_max") or 45)
    taken = [(c["t0"], c["t1"]) for c in store.q("SELECT t0, t1 FROM clips WHERE source_id=?", (src["id"],))]
    seen_key = f"vision_seen_{src['id']}"          # úseky, ktoré už Claude videl a nevybral, sa neukazujú znova
    taken += [tuple(x) for x in (store.get(seen_key, []) or [])]
    cands = candidates(scan(src), lo, hi, taken, min(MAX_CAND, want + 4))
    if not cands:
        store.run("UPDATE sources SET status='used' WHERE id=?", (src["id"],))
        return 0
    work = store.DIR / "work" / f"sheet-{src['id']}"
    work.mkdir(parents=True, exist_ok=True)
    img = sheet(src["path"], cands, work / "sheet.jpg")
    words = source.words(src)
    rows = []
    for i, (t0, t1, val) in enumerate(cands):
        said = _said(words, t0, t1)
        rows.append(f"{i + 1}: {int(t0)}-{int(t1)}s, energy {val:+.1f}" + (f', spoken: "{said}"' if said else ""))
    lang = src.get("lang") or camp.get("lang") or "en"
    prompt = (
        "The image sheet.jpg is a contact sheet from one long video. Each numbered row shows three frames of one segment "
        "(start, middle, end). The segments are the loudest and most eventful parts of the video, found automatically.\n"
        f"Pick the {min(want, len(cands))} segments most likely to go viral as standalone vertical short clips and write their texts.\n"
        "Prefer segments where something visibly happens (action, reveal, reaction, a striking image, a result) and that make sense "
        "with zero context. Skip logos, title cards, credits, menus, loading screens and near-duplicate segments.\n"
        + (f"About the source / campaign rules: {(camp.get('about') or '')[:400]} {(camp.get('rules') or '')[:600]}\n" if (camp.get("about") or camp.get("rules")) else "")
        + "Segments:\n" + "\n".join(rows) + "\n"
        f"Write hook, title and caption in this language: {lang}. Describe only what is really visible; never invent facts.\n"
        'Return JSON: {"moments":[{"n":<segment number>,"hook":"on-screen headline, max 7 words, a statement not a question, makes people '
        'need to see what happens","title":"post title, max 70 characters","caption":"40-80 characters, an opinion or statement that makes '
        'people comment","hashtags":"3 short topical hashtags","why":"max 12 words","score":<1-10>}]}')
    try:
        data = ai.ask(prompt, "clip_vision", kind="creative", timeout=900, image=str(img))
    except ai.NeedManual:
        raise RuntimeError("AI nie je dostupná (Claude nie je prihlásený na Macu).")
    finally:
        Path(img).unlink(missing_ok=True)
    store.put(seen_key, (store.get(seen_key, []) or []) + [[a, b] for a, b, _ in cands])
    items = data.get("moments") if isinstance(data, dict) else data
    items = sorted([m for m in (items or []) if isinstance(m, dict)], key=lambda m: -float(m.get("score") or 0))
    made, seen = 0, set()
    for m in items:
        if made >= want:
            break
        try:
            i = int(m["n"]) - 1
        except Exception:
            continue
        if i in seen or not 0 <= i < len(cands) or float(m.get("score") or 0) < float(store.get("min_score", 6)):
            continue
        seen.add(i)
        t0, t1, _ = cands[i]
        hook = re.sub(r"\s+", " ", str(m.get("hook") or "")).strip(" .")[:80]
        tags = " ".join(re.findall(r"#\w+", str(m.get("hashtags") or ""))[:3])
        caption = (str(m.get("caption") or "").strip()[:300] + (" " + tags if tags else "")).strip()
        store.run("INSERT INTO clips(source_id, campaign_id, t0, t1, hook, title, caption, why, score) VALUES(?,?,?,?,?,?,?,?,?)",
                  (src["id"], src["campaign_id"], t0, t1, hook, str(m.get("title") or hook)[:100], caption,
                   str(m.get("why") or "")[:200], float(m.get("score") or 0)))
        made += 1
    if made == 0:
        store.run("UPDATE sources SET status='used' WHERE id=?", (src["id"],))   # už z neho nič nové nevyjde
    return made
