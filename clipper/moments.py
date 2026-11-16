"""Výber momentov: Claude (cez tvoj Max) číta iba text prepisu a vráti časy najsilnejších momentov.
Obraz ani zvuk sa do AI neposiela, takže je to lacné: hodina videa je jedno až dve krátke volania."""
import re
from datetime import datetime, timedelta

from app import ai

from . import source, store

END = ".!?…"
CLOSE = "\"'”’»)]"      # veta môže končiť úvodzovkou: „…best one we've ever seen."
PAUSE = 1.5        # dlhšie ticho sa v prepise označí
MAX_GAP = 2.5      # klip s dlhším tichom vnútri sa neberie (ľudia pri tichu odchádzajú)


def _lines(words, t_from=0, t_to=1e9):
    """Prepis po riadkoch [sekunda] text; nový riadok po konci vety alebo po ~9 sekundách."""
    out, cur, start, prev = [], [], None, None
    for w in words:
        if w["s"] < t_from or w["s"] >= t_to:
            continue
        if prev is not None and w["s"] - prev > PAUSE:      # ticho: AI vie, že tadiaľ klip viesť nemá
            if cur:
                out.append(f"[{int(start)}] " + " ".join(cur))
                cur, start = [], None
            out.append(f"(pause {int(w['s'] - prev)}s)")
        prev = w["e"]
        if start is None:
            start = w["s"]
        cur.append(w["w"])
        if _stop(w["w"]) or w["s"] - start > 9:
            out.append(f"[{int(start)}] " + " ".join(cur))
            cur, start = [], None
    if cur:
        out.append(f"[{int(start)}] " + " ".join(cur))
    return out


def _stop(tok):
    """Slovo končí vetu (bodka, otáznik, výkričník, aj keď je za nimi úvodzovka)."""
    return tok.rstrip(CLOSE)[-1:] in END


def punctuated(words):
    """Má prepis interpunkciu? Automatické titulky ju nemajú a konce viet sa potom dajú len odhadnúť z páuz."""
    return sum(1 for w in words if _stop(w["w"])) >= max(3, len(words) / 40)


def _is_end(words, i, punct=True):
    """Koniec vety. Pri prepise bez interpunkcie odhad: dlhšia pauza v reči, nie však po čiarke či dvojbodke."""
    if _stop(words[i]["w"]):
        return True
    if punct or words[i]["w"][-1:] in ",:;-–":
        return False
    return i + 1 < len(words) and words[i + 1]["s"] - words[i]["e"] > 0.5


def _snap(words, t0, t1, lo, hi):
    """Začiatok na prvé slovo vety, koniec na koniec vety; dĺžka v medziach kampane.
    Klip nikdy nekončí uprostred vety: ak sa pointa do dĺžky nezmestí, radšej sa posunie začiatok alebo sa moment nevydá."""
    punct = punctuated(words)
    idx = [i for i, w in enumerate(words) if w["s"] >= t0 - 0.6]
    if not idx:
        return None
    i0 = idx[0]
    for k in range(i0, max(-1, i0 - 12), -1):     # o pár slov späť na začiatok vety
        if k == 0 or _is_end(words, k - 1, punct):
            if words[i0]["s"] - words[k]["s"] <= 4:
                i0 = k
            break
    i1 = i0
    while i1 + 1 < len(words) and words[i1 + 1]["e"] <= max(t1, words[i0]["s"] + lo):
        i1 += 1
    if not _is_end(words, i1, punct):
        back = next((k for k in range(i1 - 1, max(i0, i1 - 4), -1)
                     if _is_end(words, k, punct) and words[i1]["e"] - words[k]["e"] <= 1.5), None)
        if back is not None:           # AI trafila tesne za koniec vety: vráť sa naň
            i1 = back
        else:                          # inak vetu dokonči
            j = i1
            while j + 1 < len(words) and not _is_end(words, j, punct) and words[j + 1]["e"] - words[i1]["e"] <= 12:
                j += 1
            if _is_end(words, j, punct):
                i1 = j
            elif punct:
                return None            # veta sa nekončí ani o 12 sekúnd ďalej: z toho dobrý koniec nebude
    if words[i1]["e"] - words[i0]["s"] > hi:
        # pointa sa nezmestí: skús začať o vetu či dve neskôr (najviac o 10 sekúnd)
        later = next((k for k in range(i0 + 1, i1) if _is_end(words, k - 1, punct)
                      and words[k]["s"] - words[i0]["s"] <= 10 and words[i1]["e"] - words[k]["s"] <= hi), None)
        if later is not None:
            i0 = later
        elif punct:
            return None                # radšej žiadny klip než klip bez pointy
        else:                          # prepis bez interpunkcie: strih na poslednej pauze, ktorá sa zmestí
            k = i1
            while k > i0 and (words[k]["e"] - words[i0]["s"] > hi or not _is_end(words, k, punct)):
                k -= 1
            if words[k]["e"] - words[i0]["s"] >= lo * 0.7:
                i1 = k
            else:
                while i1 > i0 and words[i1]["e"] - words[i0]["s"] > hi:
                    i1 -= 1
    start, end = words[i0]["s"], words[i1]["e"]
    if end - start < min(lo, 12):
        return None
    return max(0.0, start - 0.15), end + 0.3


def _caption(m):
    tags = " ".join(re.findall(r"#\w+", str(m.get("hashtags") or ""))[:3])
    return (str(m.get("caption") or "").strip()[:300] + (" " + tags if tags else "")).strip()


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0)) / max(1e-6, min(a1 - a0, b1 - b0))


def _max_gap(words, t0, t1):
    inside = [w for w in words if w["s"] >= t0 and w["e"] <= t1 + 0.4]
    return max((b["s"] - a["e"] for a, b in zip(inside, inside[1:])), default=0.0)


def hot(src, a=0, b=1e9, n=6):
    """Časti, ktoré si diváci na YouTube púšťajú najviac dookola: [(začiatok, koniec, sila 0-1)] od najsilnejšej.
    Úvod videa sa neráta (ten má vysoké číslo vždy)."""
    rows = [h for h in source.heat(src) if h[0] >= 20 and h[0] < b and h[1] > a]
    if len(rows) < 5:
        return []
    top = max(h[2] for h in rows) or 1.0
    out = []
    for s0, e0, v in sorted(rows):
        if v < 0.5 * top:
            continue
        if out and s0 - out[-1][1] <= 1:
            out[-1] = (out[-1][0], e0, max(out[-1][2], v))
        else:
            out.append((s0, e0, v))
    return sorted(out, key=lambda h: -h[2])[:n]


def proven(src, camp, a=0, b=1e9):
    """Čo už pri tomto obsahu naozaj fungovalo: top klipy kampane (píše Oliver) a najviac prehrávané časti zdroja."""
    out = ""
    win = (camp.get("winners") or "").strip()
    if win:
        out += ("Clips that already got the most views in this campaign (headline, views): " + win[:500] + "\n"
                "This is proven demand: prefer moments about the same topics and write headlines in the same style, "
                "but make our own cut and our own wording, never a copy.\n")
    parts = hot(src, a, b)
    if parts:
        out += ("Most replayed parts of this video on YouTube (viewers rewatch them, a strong signal; prefer moments that contain one): "
                + "; ".join(f"{int(s0)}-{int(e0)}s ({int(v * 100)}%)" for s0, e0, v in parts) + ".\n")
    return out


def fix_ends():
    """Jednorazová oprava: klipy, ktoré ešte nie sú vonku, sa prepočítajú, aby nekončili uprostred vety."""
    if store.get("fix_ends_1", False):
        return
    for c in store.q("SELECT c.* FROM clips c WHERE c.status IN ('picked','ready','approved') "
                     "AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.clip_id=c.id)"):
        src = store.one("SELECT * FROM sources WHERE id=?", (c["source_id"],))
        if not src or (src.get("kind") or "speech") == "visual":
            continue
        words, camp = source.words(src), store.campaign(c["campaign_id"]) or {}
        if not words:
            continue
        sn = _snap(words, c["t0"] + 0.15, c["t1"] - 0.3, int(camp.get("clip_min") or 15), int(camp.get("clip_max") or 45))
        if not sn:
            store.run("UPDATE clips SET status='rejected', error='Koniec klipu vychádzal doprostred vety.' WHERE id=?", (c["id"],))
        elif abs(sn[0] - c["t0"]) > 0.2 or abs(sn[1] - c["t1"]) > 0.2:
            store.run("UPDATE clips SET t0=?, t1=?, status='picked', error='' WHERE id=?", (round(sn[0], 2), round(sn[1], 2), c["id"]))
    store.put("fix_ends_1", True)


def _learned():
    """Čo na našich účtoch naozaj fungovalo: titulky klipov s najviac a najmenej pozretiami (až keď je z čoho)."""
    since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    rows = store.q("SELECT c.hook, MAX(p.views) v FROM posts p JOIN clips c ON c.id=p.clip_id "
                   "WHERE p.status='posted' AND p.scheduled_at<=? AND c.hook!='' GROUP BY c.id ORDER BY v DESC", (since,))
    if len(rows) < 8:
        return ""
    best = "; ".join(f'"{r["hook"]}" ({int(r["v"])} views)' for r in rows[:4])
    worst = "; ".join(f'"{r["hook"]}" ({int(r["v"])})' for r in rows[-3:])
    return (f"Results from our own accounts. Most viewed clips: {best}. Least viewed: {worst}. "
            "Prefer moments and headlines like the first group.\n")


def pick(src, want):
    """Vyberie až `want` nových momentov zo zdroja a uloží ich ako klipy na strih. Vráti počet."""
    if (src.get("kind") or "speech") == "visual":
        from . import vision
        return vision.pick(src, want)
    camp = store.campaign(src["campaign_id"])
    words = source.words(src)
    if not words or want <= 0:
        return 0
    lo, hi = int(camp.get("clip_min") or 15), int(camp.get("clip_max") or 45)
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
            f"Below is a transcript of part of a long video. Each line starts with [second]; (pause Ns) marks silence. "
            f"Pick the {n + 2} moments most likely to go viral as standalone vertical short clips ({lo}-{hi} seconds each).\n"
            "Viewers decide in the first 1-2 seconds whether to swipe away, so the FIRST SENTENCE of the clip decides everything.\n"
            "Rules for a strong moment:\n"
            "1. Cold open: 'start' is the second where the single strongest sentence begins (bold claim, number, confession, conflict, "
            "high stakes, unusual statement). No warm-up, no filler opener, no host question unless the question itself is the hook.\n"
            "2. It opens a loop the viewer wants closed (what happened, why, how much, who was right) and closes it inside the clip.\n"
            "3. Zero context needed: no 'as I said', no unexplained names, nothing pointing outside the clip.\n"
            "4. One idea only. Stories, emotions, disagreements and an expert explaining something surprising beat general talk.\n"
            "5. 'end' is the second where the line AFTER the payoff or punchline starts, so the last sentence is heard to its very end. "
            "Never end on a set-up ('and they say', 'and then') whose answer comes next: include the answer. "
            f"Start to end of the payoff must fit in {hi} seconds; if it does not, start later or pick another moment. "
            "Prefer the shortest version that still delivers; dense 18-35 second clips usually win.\n"
            "6. Skip stretches with pauses, cross-talk, intros, greetings, sponsor reads and housekeeping.\n"
            "7. Never cut or headline a moment so that it changes what the speaker meant.\n"
            + (f"About the source / campaign rules (they override the rules above): {(camp.get('about') or '')[:400]} {(camp.get('rules') or '')[:600]}\n" if (camp.get("about") or camp.get("rules")) else "")
            + proven(src, camp, a, b)
            + _learned()
            + f"Already used second ranges (do not overlap them): {used}.\n"
            f"Write hook, title and caption in the language of the transcript ({src.get('lang') or camp.get('lang') or 'en'}).\n"
            'Return JSON: {"moments":[{"start":<second where it starts>,"end":<second where it ends>,'
            '"hook":"on-screen headline shown from the first frame, max 7 words, a statement not a question, makes people need the payoff '
            'without giving it away, true to what is said",'
            '"title":"post title, max 70 characters","caption":"40-80 characters, an opinion or statement that makes people comment",'
            '"hashtags":"3 short topical hashtags",'
            '"why":"max 12 words","score":<1-10: how hard it is to swipe away in the first 2 seconds and how satisfying the payoff is>}]}'
            "\n\nTRANSCRIPT:\n" + "\n".join(lines))
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
            if _max_gap(words, t0, t1) > MAX_GAP:
                continue                 # dlhé ticho vnútri: taký klip ľudia nedopozerajú
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
