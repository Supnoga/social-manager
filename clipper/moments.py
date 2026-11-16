"""Výber momentov: Claude (cez tvoj Max) číta iba text prepisu a vráti časy najsilnejších momentov.
Obraz ani zvuk sa do AI neposiela, takže je to lacné: hodina videa je jedno až dve krátke volania."""
import re

from app import ai

from . import source, store

END = ".!?…"


def _lines(words, t_from=0, t_to=1e9):
    """Prepis po riadkoch [sekunda] text; nový riadok po konci vety alebo po ~9 sekundách."""
    out, cur, start = [], [], None
    for w in words:
        if w["s"] < t_from or w["s"] >= t_to:
            continue
        if start is None:
            start = w["s"]
        cur.append(w["w"])
        if w["w"][-1:] in END or w["s"] - start > 9:
            out.append(f"[{int(start)}] " + " ".join(cur))
            cur, start = [], None
    if cur:
        out.append(f"[{int(start)}] " + " ".join(cur))
    return out


def _is_end(words, i):
    """Koniec vety: bodka, otáznik, výkričník; pri titulkoch bez interpunkcie dlhšia pauza v reči."""
    if words[i]["w"][-1:] in END:
        return True
    return i + 1 < len(words) and words[i + 1]["s"] - words[i]["e"] > 0.5


def _snap(words, t0, t1, lo, hi):
    """Začiatok na prvé slovo vety, koniec na koniec vety; dĺžka v medziach kampane."""
    idx = [i for i, w in enumerate(words) if w["s"] >= t0 - 0.6]
    if not idx:
        return None
    i0 = idx[0]
    for k in range(i0, max(-1, i0 - 12), -1):     # o pár slov späť na začiatok vety
        if k == 0 or _is_end(words, k - 1):
            if words[i0]["s"] - words[k]["s"] <= 4:
                i0 = k
            break
    start = words[i0]["s"]
    i1 = i0
    while i1 + 1 < len(words) and words[i1 + 1]["e"] <= max(t1, start + lo):
        i1 += 1
    j = i1
    while j + 1 < len(words) and not _is_end(words, j) and words[j + 1]["e"] - start <= hi:   # dokonči vetu
        j += 1
    if _is_end(words, j):
        i1 = j
    if words[i1]["e"] - start > hi:   # príliš dlhé: skráť na poslednú celú vetu, ktorá sa zmestí
        k = i1
        while k > i0 and (words[k]["e"] - start > hi or not _is_end(words, k)):
            k -= 1
        if words[k]["e"] - start >= lo * 0.7:
            i1 = k
        else:                          # veta sa nezmestí: tvrdý strih na hornej hranici
            while i1 > i0 and words[i1]["e"] - start > hi:
                i1 -= 1
    end = words[i1]["e"]
    if end - start < min(lo, 12):
        return None
    return max(0.0, start - 0.15), end + 0.3


def _caption(m):
    tags = " ".join(re.findall(r"#\w+", str(m.get("hashtags") or "")))[:80]
    return (str(m.get("caption") or "").strip()[:300] + (" " + tags if tags else "")).strip()


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0)) / max(1e-6, min(a1 - a0, b1 - b0))


def pick(src, want):
    """Vyberie až `want` nových momentov zo zdroja a uloží ich ako klipy na strih. Vráti počet."""
    camp = store.campaign(src["campaign_id"])
    words = source.words(src)
    if not words or want <= 0:
        return 0
    lo, hi = int(camp.get("clip_min") or 20), int(camp.get("clip_max") or 55)
    taken = [(c["t0"], c["t1"]) for c in store.q("SELECT t0, t1 FROM clips WHERE source_id=?", (src["id"],))]
    total = words[-1]["e"]
    window = 40 * 60
    made = 0
    parts = max(1, round(total / window))
    for p in range(parts):
        if made >= want:
            break
        a, b = p * total / parts, (p + 1) * total / parts
        n = max(1, round((want - made) / (parts - p)))
        lines = _lines(words, a, b)
        if len(lines) < 5:
            continue
        used = "; ".join(f"{int(x)}-{int(y)}" for x, y in taken if x < b and y > a) or "none"
        prompt = (
            f"Below is a transcript of part of a long video. Each line starts with [second]. "
            f"Pick the {n + 2} strongest moments to cut out as standalone vertical short clips ({lo}-{hi} seconds each).\n"
            "A good moment: starts at the beginning of a thought with a strong first sentence, makes sense with zero context, "
            "holds one idea (surprising claim, strong opinion, concrete story, number, joke, emotional peak) and ends on a finished "
            "sentence or punchline. Skip intros, greetings, sponsor reads, housekeeping and anything that needs earlier context.\n"
            + (f"About the source / campaign rules: {(camp.get('about') or '')[:400]} {(camp.get('rules') or '')[:600]}\n" if (camp.get("about") or camp.get("rules")) else "")
            + f"Already used second ranges (do not overlap them): {used}.\n"
            f"Write hook, title and caption in the language of the transcript ({src.get('lang') or camp.get('lang') or 'en'}).\n"
            'Return JSON: {"moments":[{"start":<second where it starts>,"end":<second where it ends>,'
            '"hook":"on-screen headline, max 7 words, creates curiosity, no clickbait lies",'
            '"title":"post title, max 70 characters","caption":"one sentence that makes people comment","hashtags":"3 short topical hashtags",'
            '"why":"max 12 words","score":<1-10>}]}\n\nTRANSCRIPT:\n' + "\n".join(lines))
        try:
            data = ai.ask(prompt, "clip_moments", kind="creative", timeout=900)
        except ai.NeedManual:
            raise RuntimeError("AI nie je dostupná (Claude nie je prihlásený na Macu).")
        items = data.get("moments") if isinstance(data, dict) else data
        items = sorted([m for m in (items or []) if isinstance(m, dict)], key=lambda m: -float(m.get("score") or 0))
        got = 0
        for m in items:
            if got >= n or made >= want:
                break
            try:
                s, e = float(m["start"]), float(m["end"])
            except Exception:
                continue
            if float(m.get("score") or 0) < float(store.get("min_score", 6)):
                continue                 # slabý moment radšej nevydať: zdroj je vyťažený
            sn = _snap(words, s, e, lo, hi)
            if not sn:
                continue
            t0, t1 = sn
            if any(_overlap(t0, t1, x, y) > 0.25 for x, y in taken):
                continue
            hook = re.sub(r"\s+", " ", str(m.get("hook") or "")).strip(" .")[:80]
            store.run("INSERT INTO clips(source_id, campaign_id, t0, t1, hook, title, caption, why, score) VALUES(?,?,?,?,?,?,?,?,?)",
                      (src["id"], src["campaign_id"], round(t0, 2), round(t1, 2), hook, str(m.get("title") or hook)[:100],
                       _caption(m), str(m.get("why") or "")[:200], float(m.get("score") or 0)))
            taken.append((t0, t1))
            got += 1
            made += 1
    if made == 0:
        store.run("UPDATE sources SET status='used' WHERE id=?", (src["id"],))   # už z neho nič nové nevyjde
    return made
