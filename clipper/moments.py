"""Výber momentov: Claude (cez tvoj Max) číta iba text prepisu a vráti časy najsilnejších momentov.
Obraz ani zvuk sa do AI neposiela, takže je to lacné: hodina videa je jedno až dve krátke volania."""
import re
from datetime import datetime, timedelta

from app import ai

from . import source, store

END = ".!?…"
CLOSE = "\"'”’»)]"      # veta môže končiť úvodzovkou: „…best one we've ever seen."
OPENQ, CLOSEQ = "\"“„«", "\"”»"       # priama reč
LOOSE = {"it", "it's", "its", "that", "that's", "this", "these", "those", "he", "he's", "she", "she's", "they", "they're",
         "which", "because", "or", "who", "there", "there's"}     # takto sa klip začínať nemá: ukazuje na niečo, čo divák nepočul
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


def _first(words, k, punct):
    """Slovo k začína vetu (alebo to, čo nasleduje po dvojbodke: „I did the only thing I could: I wrote 90 pages“)."""
    return k == 0 or _is_end(words, k - 1, punct) or (punct and words[k - 1]["w"][-1:] == ":" and words[k]["w"][:1].isupper())


def _sent_end(words, i, punct, max_s=15):
    """Koniec vety, ktorá sa začína slovom i (index posledného slova), alebo None, ak sa do max_s sekúnd neskončí."""
    j = i
    while j + 1 < len(words) and not _is_end(words, j, punct) and words[j + 1]["e"] - words[i]["s"] <= max_s:
        j += 1
    return j if _is_end(words, j, punct) else None


def _open_quote(words, i0, i1):
    """Ostala v klipe otvorená priama reč? („… and he says, "Actually, let's …“ bez konca citátu)"""
    state = False
    for w in words[i0:i1 + 1]:
        tok = w["w"]
        if tok[:1] in OPENQ:
            state = True
        if len(tok) > 1 and tok.rstrip(".,!?…;:")[-1:] in CLOSEQ:
            state = False
    return state


def _complete(words, i0, i1, punct, limit):
    """Dokončenie myšlienky: klip nekončí otázkou, na ktorú odpoveď zaznie hneď potom, ani uprostred priamej reči."""
    if not punct:
        return i1
    for _ in range(4):
        nxt = i1 + 1
        if nxt >= len(words) or words[nxt]["s"] - words[i1]["e"] >= MAX_GAP:
            break
        j = None
        if words[i1]["w"].rstrip(CLOSE)[-1:] == "?":
            j = _sent_end(words, nxt, punct)
        elif _open_quote(words, i0, i1):
            j = nxt
            while j + 1 < len(words) and words[j]["w"].rstrip(".,!?…;:")[-1:] not in CLOSEQ and words[j + 1]["e"] - words[i1]["e"] <= 15:
                j += 1
            if words[j]["w"].rstrip(".,!?…;:")[-1:] not in CLOSEQ:
                j = None
            elif not _is_end(words, j, punct):
                j = _sent_end(words, j, punct)
        if j is None or words[j]["e"] - words[i0]["s"] > limit + 10:
            break
        i1 = j
    return i1


def _bounds(words, t0, t1, lo, hi, punct):
    """Hranice klipu ako indexy slov (prvé, posledné): začiatok na prvé slovo vety, koniec na koniec vety a dokončenej myšlienky.
    Klip nikdy nekončí uprostred vety: ak sa pointa do dĺžky nezmestí, radšej sa posunie začiatok alebo sa moment nevydá."""
    idx = [i for i, w in enumerate(words) if w["s"] >= t0 - 0.6]
    if not idx:
        return None
    i0 = idx[0]
    if not _first(words, i0, punct):
        back = next((k for k in range(i0 - 1, max(-1, i0 - 14), -1) if _first(words, k, punct)), None)
        if back is not None and words[i0]["s"] - words[back]["s"] <= 4:
            i0 = back                  # o pár slov späť na začiatok vety
        else:                          # veta sa začala dávno: začni až ďalšou
            fwd = next((k for k in range(i0 + 1, min(len(words), i0 + 30))
                        if _first(words, k, punct) and words[k]["s"] - words[i0]["s"] <= 6), None)
            if fwd is not None:
                i0 = fwd
            elif punct:
                return None
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
    done = _complete(words, i0, i1, punct, hi)
    return _fit(words, i0, done, lo, hi if done == i1 else _soft(hi), punct)


def _soft(hi):
    """Dokončenie myšlienky smie klip trochu predĺžiť nad dĺžku z kampane (o 15 %, najviac o 8 sekúnd)."""
    return min(hi * 1.15, hi + 8)


def _fit(words, i0, i1, lo, limit, punct):
    """Dĺžka v medziach: keď je klip pridlhý, začne o vetu či dve neskôr (najviac o 10 sekúnd), koniec ostáva."""
    if words[i1]["e"] - words[i0]["s"] > limit:
        later = next((k for k in range(i0 + 1, i1) if _first(words, k, punct)
                      and words[k]["s"] - words[i0]["s"] <= 10 and words[i1]["e"] - words[k]["s"] <= limit
                      and words[k]["w"].strip("\"“'").lower() not in LOOSE), None)
        if later is not None:
            i0 = later
        elif punct:
            return None                # radšej žiadny klip než klip bez pointy
        else:                          # prepis bez interpunkcie: strih na poslednej pauze, ktorá sa zmestí
            k = i1
            while k > i0 and (words[k]["e"] - words[i0]["s"] > limit or not _is_end(words, k, punct)):
                k -= 1
            if words[k]["e"] - words[i0]["s"] >= lo * 0.7:
                i1 = k
            else:
                while i1 > i0 and words[i1]["e"] - words[i0]["s"] > limit:
                    i1 -= 1
    if words[i1]["e"] - words[i0]["s"] < min(lo, 12):
        return None
    return i0, i1


def _times(words, i0, i1, react=()):
    """Časy strihu. Dozvuk: po pointe nechaj dobehnúť smiech či potlesk (do 3 s), inak krátky nádych, nikdy nie do ďalšej vety."""
    start, end = words[i0]["s"], words[i1]["e"]
    gap = (words[i1 + 1]["s"] - end) if i1 + 1 < len(words) else 3.0
    if any(a < end + 1.0 and b > end + 0.2 for a, b in react):
        tail = min(3.0, gap - 0.15)
    elif gap >= 1.0:
        tail = min(gap - 0.2, 1.2)
    else:
        tail = min(0.3, gap - 0.04)        # reč pokračuje hneď: strih tesne pred ďalším slovom (presne ho doladí zvuk pri strihu)
    return max(0.0, start - 0.15), end + max(0.05, tail)


def _snap(words, t0, t1, lo, hi, react=()):
    """Časy klipu (začiatok, koniec) pre moment, ktorý vybrala AI, alebo None, keď z neho čistý klip nevyjde."""
    b = _bounds(words, t0, t1, lo, hi, punctuated(words))
    return _times(words, b[0], b[1], react) if b else None


def _text(words, a, b):
    return " ".join(w["w"] for w in words[a:b + 1])


def _after(words, i1, punct, n=3):
    """Konce najbližších viet za klipom (indexy), najviac n a najviac 25 sekúnd."""
    out, i = [], i1 + 1
    while len(out) < n and i < len(words) and words[i]["s"] - words[i1]["e"] < 25:
        j = _sent_end(words, i, punct)
        if j is None:
            break
        out.append(j)
        i = j + 1
    return out


def _review(cands, words, camp, lo, hi, punct):
    """Druhé čítanie hotového strihu: AI dostane presný text každého klipu, vetu pred ním a vety po ňom
    a povie, či sa klip začína zrozumiteľne a či je myšlienka dokončená. Malé volanie (len text klipov).
    Vráti kandidátov, ktorí prešli, s upravenými hranicami."""
    if not cands or not punct or not store.get("review", True):
        return cands
    blocks = []
    for n, c in enumerate(cands, 1):
        i0, i1 = c["i0"], c["i1"]
        prev = next((k for k in range(i0 - 1, max(-1, i0 - 40), -1) if _first(words, k, punct)), i0)
        c["after"] = _after(words, i1, punct)
        ends, a = [], i1 + 1
        for j in c["after"]:
            ends.append(f"A{len(ends) + 1}: {_text(words, a, j)}")
            a = j + 1
        blocks.append(f"CLIP {n}\nheadline: {c['m'].get('hook') or ''}\nBEFORE (not in clip): {_text(words, prev, i0 - 1) if prev < i0 else '-'}\n"
                      f"CLIP TEXT: {_text(words, i0, i1)}\nAFTER (not in clip): {' | '.join(ends) or '-'}")
    prompt = (
        "You are the final editor of short vertical clips cut from a long video. Check each clip strictly as a viewer "
        "who has never seen the source and hears only CLIP TEXT.\n"
        "- Start: the first sentence must make sense with zero context (no 'it/that/he' pointing outside the clip, no answer to an unheard "
        "question, no leftover of a previous thought). If dropping the first sentence fixes it, set drop_first to 1.\n"
        "- End: the thought, story, joke, quote or list must be finished and the last sentence must feel like an ending. If the payoff, "
        "punchline or answer only comes in AFTER, set add_after to how many AFTER sentences (1-3) are needed. "
        "If the clip keeps going after its payoff into a new topic, set cut_last to how many trailing sentences to remove.\n"
        "- Never keep a clip that would change what the speaker meant, or that has no real payoff.\n"
        "- Headline: must be true to the clip and must not give the payoff away. If it is not, put a better one (max 7 words) in hook, else leave hook empty.\n"
        + (f"- Campaign rules (a clip that breaks them is not ok): {(camp.get('rules') or '')[:600]}\n" if camp.get("rules") else "")
        + 'Return JSON: {"clips":[{"id":<clip number>,"ok":true,"drop_first":0,"add_after":0,"cut_last":0,"hook":"","problem":"max 10 words, empty if fine"}]}. '
        "Set ok to false only when these changes cannot save the clip.\n\n" + "\n\n".join(blocks))
    try:
        data = ai.ask(prompt, "clip_review", kind="creative", timeout=600)
    except ai.NeedManual:
        raise
    except Exception as e:
        print("Clipper kontrola strihu:", str(e)[:200])
        return cands
    rows = {}
    for r in (data.get("clips") if isinstance(data, dict) else data) or []:
        try:
            rows[int(r["id"])] = r
        except Exception:
            pass
    out = []
    num = lambda r, k: max(0, min(3, int(float(r.get(k) or 0))))
    for n, c in enumerate(cands, 1):
        r = rows.get(n)
        if not r:
            out.append(c)
            continue
        if r.get("ok") is False:
            continue
        i0, i1 = c["i0"], c["i1"]
        try:
            add, cut, drop = num(r, "add_after"), num(r, "cut_last"), num(r, "drop_first")
        except Exception:
            add = cut = drop = 0
        if add and c["after"]:
            i1 = c["after"][min(add, len(c["after"])) - 1]
        elif cut:
            for _ in range(cut):
                k = next((k for k in range(i1 - 1, i0, -1) if _is_end(words, k, punct)), None)
                if k is None:
                    break
                i1 = k
        if drop:
            k = next((k for k in range(i0 + 1, i1) if _first(words, k, punct)), None)
            if k is not None:
                i0 = k
        if (i0, i1) != (c["i0"], c["i1"]):
            b = _fit(words, i0, i1, lo, _soft(hi), punct)
            if not b:
                continue               # myšlienka sa do dĺžky nezmestí: radšej nevydať
            c["i0"], c["i1"] = b
        hook = re.sub(r"\s+", " ", str(r.get("hook") or "")).strip(" .")
        if hook:
            c["m"]["hook"] = hook
        out.append(c)
    return out


def _caption(m):
    tags = " ".join(re.findall(r"#\w+", str(m.get("hashtags") or ""))[:3])
    return (str(m.get("caption") or "").strip()[:300] + (" " + tags if tags else "")).strip()


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0)) / max(1e-6, min(a1 - a0, b1 - b0))


def _max_gap(words, t0, t1, notes=()):
    """Najdlhšie ticho medzi slovami klipu. Pauza, v ktorej sa publikum smeje alebo tlieska, tichom nie je (do 6 s);
    kratšia pauza, pri ktorej prepis hlási hudbu alebo text na plátne, tiež nie (do 4 s)."""
    inside = [w for w in words if w["s"] >= t0 - 0.2 and w["s"] < t1 - 0.25]
    worst = 0.0
    for a, b in zip(inside, inside[1:]):
        g = b["s"] - a["e"]
        if g > MAX_GAP and any(x < b["s"] and y > a["e"] and g <= (6 if r else 4) for x, y, r in notes):
            continue
        worst = max(worst, g)
    return worst


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
    if store.get("fix_ends_2", False):
        return
    for c in store.q("SELECT c.* FROM clips c WHERE c.status IN ('picked','ready','approved') "
                     "AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.clip_id=c.id)"):
        src = store.one("SELECT * FROM sources WHERE id=?", (c["source_id"],))
        if not src or (src.get("kind") or "speech") == "visual":
            continue
        words, camp = source.words(src), store.campaign(c["campaign_id"]) or {}
        if not words:
            continue
        sn = _snap(words, c["t0"] + 0.15, c["t1"] - 0.3, int(camp.get("clip_min") or 15), int(camp.get("clip_max") or 45),
                   source.reactions(src))
        if not sn:
            store.run("UPDATE clips SET status='rejected', error='Koniec klipu vychádzal doprostred vety.' WHERE id=?", (c["id"],))
        elif abs(sn[0] - c["t0"]) > 0.2 or abs(sn[1] - c["t1"]) > 0.2:
            store.run("UPDATE clips SET t0=?, t1=?, status='picked', error='' WHERE id=?", (round(sn[0], 2), round(sn[1], 2), c["id"]))
    store.put("fix_ends_2", True)


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
    react, notes = source.reactions(src), source.notes(src)
    punct = punctuated(words)
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
            "Never end on a set-up ('and they say', 'and then') or on a question whose answer comes next: include the answer, "
            "the thought must be finished. If the audience laughs or reacts right after the punchline, that is a great ending. "
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
        cands = []
        for m in items:
            try:
                s, e = float(m["start"]), float(m["end"])
            except Exception:
                continue
            if float(m.get("score") or 0) < float(store.get("min_score", 6)):
                continue                 # slabý moment radšej nevydať: zdroj je vyťažený
            bd = _bounds(words, s, e, lo, hi, punct)
            if bd:
                cands.append({"m": m, "i0": bd[0], "i1": bd[1]})
        got = 0
        for c in _review(cands, words, camp, lo, hi, punct):
            if got >= n or made >= want:
                break
            m = c["m"]
            t0, t1 = _times(words, c["i0"], c["i1"], react)
            if _max_gap(words, t0, t1, notes) > MAX_GAP:
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
