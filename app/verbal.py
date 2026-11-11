"""Čísla, jednotky a značky nahlas podľa gramatiky jazyka („2 percentá“ → „dve percentá“, „2 kW“ → „dva kilowatty“).

Prečo AI a nie knižnica: správny tvar závisí od rodu a pádu okolitých slov, a to v každom jazyku inak. Knižnice
(num2words a pod.) vedia len základný tvar, nepoznajú vetu a 7 z 28 jazykov appky im chýba. Samotný hlas si rod tipuje.
Claude to vie vo všetkých jazykoch naraz.

Úspora tokenov: posielajú sa LEN vety, v ktorých je číslo alebo značka, všetky jazyky v jednej požiadavke,
a každá veta sa zapamätá (druhýkrát je zadarmo). Výsledok sa kontroluje: nesmie zmeniť nič okrem čísel,
inak sa použije pôvodná veta. Titulky ostávajú napísané pôvodne (číslicami)."""
import difflib
import hashlib
import re

from . import db

VER = "1"
BATCH = 70
NEED = re.compile(r"\d|[%‰€$£°±×÷=§]|(?<=\s)[+/](?=\s)")
_ready = False


def _db():
    global _ready
    if not _ready:
        db.con().executescript("CREATE TABLE IF NOT EXISTS spoken_cache (hash TEXT PRIMARY KEY, lang TEXT, src TEXT, spoken TEXT);")
        db.con().commit()
        _ready = True


def enabled():
    return bool(db.get_setting("verbal_on", True))


def _h(sentence, lang):
    return hashlib.sha1(f"{VER}|{lang}|{sentence}".encode()).hexdigest()


def need(sentence):
    return bool(NEED.search(sentence or ""))


def _norm(tok):
    return re.sub(r"[^\w%°€$£+]", "", tok.lower())


def _coded(tok):
    """Označenie s písmenami aj číslicami (R290, N2N, A+++, CO2) – to sa neprepisuje, rieši ho Výslovnosť."""
    t = tok.strip(".,!?:;()\"'„“”«»")
    return bool(re.search(r"[^\W\d_]", t) and re.search(r"\d", t)) or bool(re.fullmatch(r"[A-G]\+{1,3}", t))


def valid(src, out):
    """Poistka: AI smela prepísať len čísla a značky. Ostatné slová musia ostať, číslice nesmú zvýšiť."""
    if not isinstance(out, str) or not out.strip() or len(out) > len(src) * 4 + 60:
        return False
    codes = {_norm(t) for t in src.split() if _coded(t)}
    for t in out.split():
        if re.search(r"\d", t) and _norm(t) not in codes:
            return False
    toks = src.split()
    keep = [_norm(t) for k, t in enumerate(toks) if not NEED.search(t) and len(_norm(t)) > 2
            and not (k and re.search(r"\d", toks[k - 1]))]          # slovo hneď za číslom je často jednotka (kW, dB)
    if not keep:
        return True
    have = [_norm(t) for t in out.split()]
    m = difflib.SequenceMatcher(None, keep, have, autojunk=False)
    same = sum(b.size for b in m.get_matching_blocks())
    return same / len(keep) >= 0.8


def _ask(items):
    """items = [(lang, veta)] -> [prepis alebo None]. Jedna požiadavka pre všetky jazyky."""
    import json
    from . import ai, languages
    payload = {str(i): [languages.english(l), s] for i, (l, s) in enumerate(items)}
    prompt = (
        "Prepare sentences for a text-to-speech voice. For each item [language, sentence] rewrite the sentence in the SAME language "
        "so that every number, decimal, percentage, ordinal, date, time, range, price, unit of measure and math symbol is written out "
        "in words exactly as an educated native speaker reads it aloud, with correct grammatical gender, case and number agreement "
        "with the surrounding words (Slovak \"2 percentá\" -> \"dve percentá\", \"2 kW\" -> \"dva kilowatty\", \"o 2 stupne\" -> \"o dva stupne\", "
        "\"SCOP 5.14\" -> \"SCOP päť celých štrnásť\"; German \"1 Minute\" -> \"eine Minute\"; Portuguese \"2 casas\" -> \"duas casas\"). "
        "Units become words too (kW, kWh, °C, dB, m², %, €). Use the script of the sentence (Cyrillic stays Cyrillic, Greek stays Greek). "
        "Change NOTHING else: keep every other word, the word order, punctuation and capitalisation identical. Do not translate, "
        "do not add or drop words. Leave product names and codes that mix letters and digits untouched (R290, N2N, A+++, CO2, R32). "
        "Return JSON object: same keys, value = rewritten sentence.\n" + json.dumps(payload, ensure_ascii=False))
    data = ai.ask(prompt, "verbal", "creative")
    return [data.get(str(i)) if isinstance(data, dict) else None for i in range(len(items))]


def ensure(items):
    """Pripraví prepis pre vety (lang, veta), ktoré ho potrebujú a ešte nie sú v pamäti. Vráti počet poslaných viet.
    Keď AI nie je dostupná, nič sa nestane (hlas prečíta číslice po svojom)."""
    if not enabled():
        return 0
    _db()
    todo, seen = [], set()
    for lang, s in items:
        s = (s or "").strip()
        h = _h(s, lang)
        if not s or not need(s) or h in seen:
            continue
        seen.add(h)
        if not db.one("SELECT 1 x FROM spoken_cache WHERE hash=?", (h,)):
            todo.append((lang, s))
    sent = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        try:
            res = _ask(chunk)
        except Exception as e:   # bez Claude (ručný režim, limit, chyba): nezdržuj výrobu hlasu
            print("čísla nahlas:", str(e)[:200])
            break
        sent += len(chunk)
        for (lang, s), out in zip(chunk, res):
            ok = valid(s, out)
            db.run("INSERT OR REPLACE INTO spoken_cache(hash,lang,src,spoken) VALUES(?,?,?,?)",
                   (_h(s, lang), lang, s, re.sub(r"\s+", " ", out).strip() if ok else ""))
    return sent


def spans(src, out):
    """Úseky v prepise, ktoré sa líšia od pôvodnej vety: [(od, do, pôvodný text)] – pre titulky v pôvodnom zápise."""
    a, b = src.split(), out.split()
    pos, starts = 0, []
    for t in b:
        i = out.index(t, pos)
        starts.append((i, i + len(t)))
        pos = i + len(t)
    res = []
    m = difflib.SequenceMatcher(None, [_norm(t) for t in a], [_norm(t) for t in b], autojunk=False)
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        if tag == "equal" or j1 == j2:
            continue
        res.append((starts[j1][0], starts[j2 - 1][1], " ".join(a[i1:i2])))
    return res


def say(sentence, lang):
    """Vráti (veta pre hlas, úseky). Bez prepisu v pamäti vráti pôvodnú vetu."""
    s = (sentence or "").strip()
    if not s or not enabled() or not need(s):
        return s, []
    _db()
    r = db.one("SELECT spoken FROM spoken_cache WHERE hash=?", (_h(s, lang),))
    out = (r or {}).get("spoken") or ""
    if not out or out == s:
        return s, []
    return out, spans(s, out)


def say_all(sentences, lang):
    """Celý text po vetách: (text pre hlas, úseky v ňom)."""
    ensure([(lang, s) for s in sentences])
    parts, sp, n = [], [], 0
    for s in sentences:
        out, ss = say(s, lang)
        sp += [(a + n, b + n, o) for a, b, o in ss]
        parts.append(out)
        n += len(out) + 1
    return " ".join(parts), sp


def stats():
    _db()
    r = db.one("SELECT COUNT(*) n, SUM(CASE WHEN spoken='' THEN 1 ELSE 0 END) bad FROM spoken_cache") or {}
    return {"on": enabled(), "sentences": r.get("n") or 0, "rejected": r.get("bad") or 0}
