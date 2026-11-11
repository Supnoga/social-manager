"""Výslovnosť: úprava textu tesne pred hlasom, bez AI (iba pravidlá a slovník).

Hlasové služby (Google Chirp 3 HD aj Microsoft) nedovoľujú vo väčšine našich jazykov vlastnú výslovnosť
ani značky pre pauzy, preto sa text pre hlas prepíše „ako sa číta" v pravopise daného jazyka:
  PROLINE -> prolajn (sk) / prolaïne (fr) / προλάιν (el), 36 dB(A) -> 36 decibelov A, A+++ -> A plus plus plus.
Titulky ostávajú v pôvodnom zápise: speak() vracia aj zoznam úsekov, podľa ktorých remap() vráti
do časovania slov pôvodný text.

Čítanie v slovníku sa píše po slovensky tak, ako to znie (napr. „prolajn"); do ostatných jazykov sa prevedie samo."""
import re

from . import db

# ---------- slovník značky a skratiek ----------
# (slovo, čítanie po slovensky | None = nechať tak, len presne takto veľkými?, {jazyk: vlastné čítanie})
BUILTIN = [
    ("N2N TECHNOLOGY", "en tu en teknolodži", False, {"en": "N to N Technology"}),
    ("N2N HOME", "en tu en houm", False, {"en": "N to N Home"}),
    ("N2N", "en tu en", False, {"en": "N to N"}),
    ("PROLINE", "prolajn", False, {"en": "Pro Line"}),
    ("TOWER", "tauer", False, {"en": "Tower", "de": "Tower", "nl": "Tower", "fr": "taoueur"}),
    ("REGULATION", "regjulejšn", True, {"en": "Regulation", "fr": "Regulation", "de": "Regulation"}),
    ("TECHNOLOGY", "teknolodži", True, {"en": "Technology"}),
    ("HOME", "houm", True, {"en": "Home"}),
    ("SCOP", "skop", True, {}),
    ("COP", "kop", True, {"en": "C O P"}),
    ("SEER", "sír", True, {"en": "seer"}),
    ("HVAC", None, True, {"en": "H vac"}),
]
# skratky, ktoré sa majú hláskovať (hlas to pri veľkých písmenách robí sám) – nemeniť na bežné slovo
ACRONYMS = {"HVAC", "LED", "USB", "GPS", "SMS", "PDF", "FAQ", "DIY", "CEO", "USA", "DPH", "PVC", "LCD", "WLAN", "HDMI",
            "ERP", "TÜV", "ISO", "IP", "EU", "EÚ", "OK", "TV", "AC", "DC", "UV", "PV", "FV", "TČ", "TUV", "CO"}

# ---------- jednotky a slová podľa jazyka ----------
# kW, kWh, W, dB, °C, m², m³, plus, a (&), až (5–10)
_T = {
    "sk": ("kilowattov", "kilowatthodín", "wattov", "decibelov", "stupňov Celzia", "metrov štvorcových", "metrov kubických", "plus", "a", "až"),
    "cs": ("kilowattů", "kilowatthodin", "wattů", "decibelů", "stupňů Celsia", "metrů čtverečních", "metrů krychlových", "plus", "a", "až"),
    "en": ("kilowatts", "kilowatt hours", "watts", "decibels", "degrees Celsius", "square metres", "cubic metres", "plus", "and", "to"),
    "de": ("Kilowatt", "Kilowattstunden", "Watt", "Dezibel", "Grad Celsius", "Quadratmeter", "Kubikmeter", "plus", "und", "bis"),
    "fr": ("kilowatts", "kilowattheures", "watts", "décibels", "degrés Celsius", "mètres carrés", "mètres cubes", "plus", "et", "à"),
    "es": ("kilovatios", "kilovatios hora", "vatios", "decibelios", "grados Celsius", "metros cuadrados", "metros cúbicos", "más", "y", "a"),
    "it": ("chilowatt", "chilowattora", "watt", "decibel", "gradi Celsius", "metri quadrati", "metri cubi", "più", "e", "a"),
    "pt": ("quilowatts", "quilowatts-hora", "watts", "decibéis", "graus Celsius", "metros quadrados", "metros cúbicos", "mais", "e", "a"),
    "pl": ("kilowatów", "kilowatogodzin", "watów", "decybeli", "stopni Celsjusza", "metrów kwadratowych", "metrów sześciennych", "plus", "i", "do"),
    "nl": ("kilowatt", "kilowattuur", "watt", "decibel", "graden Celsius", "vierkante meter", "kubieke meter", "plus", "en", "tot"),
    "hu": ("kilowatt", "kilowattóra", "watt", "decibel", "Celsius-fok", "négyzetméter", "köbméter", "plusz", "és", None),
    "ro": ("kilowați", "kilowați-oră", "wați", "decibeli", "grade Celsius", "metri pătrați", "metri cubi", "plus", "și", "până la"),
    "bg": ("киловата", "киловатчаса", "вата", "децибела", "градуса по Целзий", "квадратни метра", "кубически метра", "плюс", "и", "до"),
    "hr": ("kilovata", "kilovatsati", "vata", "decibela", "stupnjeva Celzija", "četvornih metara", "kubnih metara", "plus", "i", "do"),
    "sl": ("kilovatov", "kilovatnih ur", "vatov", "decibelov", "stopinj Celzija", "kvadratnih metrov", "kubičnih metrov", "plus", "in", "do"),
    "sr": ("kilovata", "kilovat-časova", "vati", "decibela", "stepeni Celzijusa", "kvadratnih metara", "kubnih metara", "plus", "i", "do"),
    "bs": ("kilovata", "kilovat-sati", "vati", "decibela", "stepeni Celzijusa", "kvadratnih metara", "kubnih metara", "plus", "i", "do"),
    "mk": ("киловати", "киловат-часови", "вати", "децибели", "Целзиусови степени", "квадратни метри", "кубни метри", "плус", "и", "до"),
    "sq": ("kilovat", "kilovat-orë", "vat", "decibel", "gradë Celsius", "metra katrorë", "metra kub", "plus", "dhe", "deri në"),
    "el": ("κιλοβάτ", "κιλοβατώρες", "βατ", "ντεσιμπέλ", "βαθμούς Κελσίου", "τετραγωνικά μέτρα", "κυβικά μέτρα", "συν", "και", "έως"),
    "da": ("kilowatt", "kilowatt-timer", "watt", "decibel", "grader celsius", "kvadratmeter", "kubikmeter", "plus", "og", "til"),
    "sv": ("kilowatt", "kilowattimmar", "watt", "decibel", "grader Celsius", "kvadratmeter", "kubikmeter", "plus", "och", "till"),
    "no": ("kilowatt", "kilowattimer", "watt", "desibel", "grader celsius", "kvadratmeter", "kubikkmeter", "pluss", "og", "til"),
    "fi": ("kilowattia", "kilowattituntia", "wattia", "desibeliä", "celsiusastetta", "neliömetriä", "kuutiometriä", "plus", "ja", None),
    "is": ("kílóvött", "kílóvattstundir", "vött", "desíbel", "gráður á Celsíus", "fermetrar", "rúmmetrar", "plús", "og", "til"),
    "et": ("kilovatti", "kilovatt-tundi", "vatti", "detsibelli", "kraadi Celsiuse järgi", "ruutmeetrit", "kuupmeetrit", "pluss", "ja", "kuni"),
    "lv": ("kilovati", "kilovatstundas", "vati", "decibeli", "grādi pēc Celsija", "kvadrātmetri", "kubikmetri", "plus", "un", "līdz"),
    "lt": ("kilovatų", "kilovatvalandžių", "vatų", "decibelų", "laipsnių Celsijaus", "kvadratinių metrų", "kubinių metrų", "plius", "ir", "iki"),
}
_KEYS = ("kW", "kWh", "W", "dB", "C", "m2", "m3", "plus", "and", "to")
_KILO = (("kilo", "mega"), ("chilo", "mega"), ("quilo", "mega"), ("kíló", "mega"), ("кило", "мега"), ("κιλο", "μεγα"))


def _words(lang, cyr=False):
    t = dict(zip(_KEYS, _T.get(lang) or _T["en"]))
    for a, b in _KILO:
        if t["kW"].lower().startswith(a):
            cap = t["kW"][0].isupper()
            t["MW"] = (b.capitalize() if cap else b) + t["kW"][len(a):]
            t["MWh"] = (b.capitalize() if cap else b) + t["kWh"][len(a):]
            break
    if lang == "sr" and cyr:
        t = {k: _sr_cyr(v) if v else v for k, v in t.items()}
    return t


# ---------- prevod „slovenského čítania" do pravopisu jazyka ----------
_NORM = str.maketrans({"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ý": "i", "y": "i", "ä": "e", "ľ": "l", "ĺ": "l",
                       "ŕ": "r", "ť": "t", "ď": "d", "ň": "n", "ě": "e", "ř": "r", "ů": "u", "w": "v"})
_UNIT = re.compile(r"dž|ch|aj|ej|oj|au|ou|ks|.", re.S)
_AI = {"aj": "ai", "ej": "ei", "oj": "oi"}
_MAPS = {
    "pl": {"v": "w", "š": "sz", "ž": "ż", "č": "cz", "dž": "dż", "ou": "oł", "au": "ał"},
    "hu": {"s": "sz", "š": "s", "ž": "zs", "č": "cs", "dž": "dzs", "a": "á", "aj": "áj", "au": "áu", "ou": "ó", "ej": "éj", "ks": "ksz", "ch": "h"},
    "de": {"v": "w", "š": "sch", "ž": "sch", "č": "tsch", "dž": "dsch", "c": "z", "aj": "ai", "ej": "eh", "oj": "eu", "ou": "oh", "ks": "x"},
    "nl": {"aj": "ai", "ej": "ee", "oj": "oi", "ou": "oo", "u": "oe", "š": "sj", "ž": "zj", "č": "tsj", "dž": "dzj", "c": "ts"},
    "da": {"oj": "øj", "š": "sj", "ž": "sj", "č": "tj", "dž": "dj", "c": "ts"},
    "sv": {"o": "å", "u": "o", "oj": "åj", "ou": "å", "š": "sj", "ž": "sj", "č": "tj", "dž": "dj", "c": "ts"},
    "no": {"o": "å", "u": "o", "oj": "åj", "ou": "å", "š": "sj", "ž": "sj", "č": "tsj", "dž": "dsj", "c": "ts"},
    "fi": {**_AI, "č": "tš", "c": "ts", "ch": "h"},
    "et": {**_AI, "č": "tš", "c": "ts", "ch": "h"},
    "is": {"aj": "æ", "ej": "ei", "au": "á", "ou": "ó", "u": "ú", "i": "í", "š": "sj", "ž": "sj", "č": "tsj", "dž": "dj", "c": "ts", "ch": "h"},
    "lv": {**_AI, "ch": "h"},
    "lt": {**_AI},
    "hr": {"ch": "h"}, "bs": {"ch": "h"}, "sl": {"ch": "h"}, "sr": {"ch": "h"},
    "sq": {"š": "sh", "ž": "zh", "č": "ç", "dž": "xh", "ch": "h"},
    "ro": {**_AI, "j": "i", "š": "ș", "ž": "j", "c": "ț", "ch": "h", "ks": "x"},
    "it": {**_AI, "j": "i", "c": "z", "ks": "x", "ch": "c"},
    "es": {**_AI, "j": "y", "š": "sh", "ž": "y", "č": "ch", "dž": "y", "c": "ts", "ch": "j", "h": "j", "z": "s", "ks": "x"},
    "pt": {**_AI, "j": "i", "š": "ch", "ž": "j", "č": "tch", "dž": "dj", "c": "ts", "ch": "r"},
    "fr": {"aj": "aï", "ej": "eï", "oj": "oï", "au": "ao", "ou": "ô", "u": "ou", "j": "y", "š": "ch", "ž": "j", "č": "tch", "dž": "dj",
           "c": "ts", "ch": "kh", "e": "è"},
    "el": {"a": "α", "b": "μπ", "c": "τσ", "d": "ντ", "e": "ε", "f": "φ", "g": "γκ", "h": "χ", "i": "ι", "j": "γι", "k": "κ", "l": "λ",
           "m": "μ", "n": "ν", "o": "ο", "p": "π", "r": "ρ", "s": "σ", "t": "τ", "u": "ου", "v": "β", "z": "ζ", "š": "σ", "ž": "ζ",
           "č": "τσ", "dž": "τζ", "ch": "χ", "ks": "ξ", "aj": "άι", "ej": "έι", "oj": "όι", "au": "άου", "ou": "όου"},
    "bg": {"a": "а", "b": "б", "c": "ц", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "х", "i": "и", "j": "й", "k": "к", "l": "л",
           "m": "м", "n": "н", "o": "о", "p": "п", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "z": "з", "š": "ш", "ž": "ж",
           "č": "ч", "dž": "дж", "ch": "х", "ks": "кс", "aj": "ай", "ej": "ей", "oj": "ой", "au": "ау", "ou": "оу"},
}
_MAPS["mk"] = {**_MAPS["bg"], "j": "ј", "aj": "ај", "ej": "еј", "oj": "ој", "dž": "џ"}
_MAPS["sr-cyr"] = dict(_MAPS["mk"])
_SOFT = {"it": ("c", "ci", "g", "gi", "sc", "sci", "gh"), "ro": ("c", "ci", "g", "gi", None, None, "gh")}
_VOW = "aeiouyáéíóúýäôěůöüőűàèìòùâêîôûãõåæøœαεηιουωάέήίόύώаеиоуъюяыэєії"


def phon(say, lang, cyr=False):
    """„prolajn" (slovenské čítanie) -> pravopis jazyka, v ktorom to hlas prečíta rovnako."""
    if lang in ("sk", "cs"):
        return say
    m = _MAPS.get("sr-cyr" if lang == "sr" and cyr else lang, {})
    out = []
    for word in say.split():
        units = _UNIT.findall(word.lower().translate(_NORM).replace("ô", "uo").replace("x", "ks").replace("q", "kv"))
        res = []
        for i, u in enumerate(units):
            front = i + 1 < len(units) and units[i + 1][0] in "ei"
            soft = _SOFT.get(lang)
            if soft and u in ("č", "dž", "š", "g"):
                if u == "g":
                    res.append(soft[6] if front else "g")
                    continue
                a, b = {"č": soft[0:2], "dž": soft[2:4], "š": soft[4:6]}[u]
                if a:
                    res.append(a if front else b)
                    continue
            if u == "g" and front and lang in ("es", "pt", "fr"):
                res.append("gu")
                continue
            res.append(m.get(u, u))
        w = "".join(res)
        if lang == "fr" and re.search(r"[aeiouèôï][nm]$", w):
            w += "e"    # inak by z toho bola nosovka
        if lang == "nl" and w.endswith("i") and len(w) > 2:
            w += "e"
        if lang == "el" and w.endswith("σ"):
            w = w[:-1] + "ς"
        out.append(w)
    return " ".join(out)


_SRC = (("dž", "џ"), ("lj", "љ"), ("nj", "њ"), ("a", "а"), ("b", "б"), ("c", "ц"), ("č", "ч"), ("ć", "ћ"), ("d", "д"), ("đ", "ђ"),
        ("e", "е"), ("f", "ф"), ("g", "г"), ("h", "х"), ("i", "и"), ("j", "ј"), ("k", "к"), ("l", "л"), ("m", "м"), ("n", "н"),
        ("o", "о"), ("p", "п"), ("r", "р"), ("s", "с"), ("š", "ш"), ("t", "т"), ("u", "у"), ("v", "в"), ("z", "з"), ("ž", "ж"))


def _sr_cyr(s):
    for a, b in _SRC:
        s = s.replace(a, b).replace(a.capitalize(), b.capitalize())
    return s


# ---------- vlastné slová (Nastavenia → Hlas → Výslovnosť) ----------
def custom():
    return [x for x in (db.get_setting("pronounce", []) or []) if isinstance(x, dict) and (x.get("w") or "").strip() and (x.get("say") or "").strip()]


def save_custom(items):
    out, seen = [], set()
    for x in items or []:
        w, say, lang = (x.get("w") or "").strip()[:60], (x.get("say") or "").strip()[:120], (x.get("lang") or "*").strip() or "*"
        if not w or not say or (w.lower(), lang) in seen:
            continue
        seen.add((w.lower(), lang))
        out.append({"w": w, "say": say, "lang": lang})
    db.set_setting("pronounce", out)
    return out


def builtin_list():
    return [{"w": w, "say": say} for w, say, _, _ in BUILTIN if say]


def _entries(lang, cyr):
    """[(slovo, čítanie v jazyku | None, presne veľkými?)] – vlastné slová majú prednosť pred zabudovanými."""
    ent = {}
    for w, say, exact, over in BUILTIN:
        if lang in over:
            r = over[lang]
        elif say is None:
            r = None
        else:
            r = phon(say, lang, cyr)
        ent[w.lower()] = (w, r, exact)
    cu = custom()
    for x in [c for c in cu if c["lang"] == "*"] + [c for c in cu if c["lang"] == lang]:
        w = x["w"]
        if x["lang"] == lang:
            r = x["say"]
        elif lang == "en" and re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", w):
            r = w if not w.isupper() else w.title()    # anglické slovo prečíta anglický hlas sám
        else:
            r = phon(x["say"], lang, cyr)
        ent[w.lower()] = (w, r, False)
    return sorted(ent.values(), key=lambda e: -len(e[0]))


# ---------- hlavná úprava ----------
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍⃣]+")
_NUM = r"\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?"
_UNITS = r"kWh|MWh|kW|MW|KW|W|dB\s?\(A\)|dBA|dB|°\s?C|℃|m²|m2|m³|m3"
_cache = {}


def _pre(text, lang):
    """Čistenie, ktoré sa netýka titulkov: emoji, odrážky, riadky a pomlčky ako pauzy."""
    t = _EMOJI.sub(" ", text or "")
    t = re.sub(r"https?://", "", t)
    t = re.sub(r"(?m)^\s*[•\-–—*·▪►]+\s+", "", t)
    t = re.sub(r"(?<=[^\s.!?…:;,])[ \t]*\n+\s*", ". ", t)      # nový riadok bez bodky = koniec vety (pauza)
    t = re.sub(r"\s+[–—-]{1,2}\s+", ", ", t)                    # pomlčka medzi slovami = krátka pauza
    t = t.replace("—", ", ").replace("#", " ").replace("*", "").replace("_", " ")
    t = re.sub(r"(?<![\w.,])[−–](?=\d)", "-", t)                # mínus pred číslom
    t = re.sub(r"([!?])[!?]+", r"\1", t)
    t = re.sub(r"\.{4,}", "…", t)
    t = re.sub(r"\s+([,.!?;:])", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    if lang == "en":
        t = re.sub(r"(?<![\d,.])(\d+),(\d{1,2})(?![\d,])", r"\1.\2", t)   # 5,14 -> 5.14
    return t


def _num(s):
    return re.sub(r"(?<=\d)[   ](?=\d{3})", "", s)


def _readable(w, lang):
    """Slovo veľkými písmenami, ktoré sa dá prečítať ako slovo (PROLINE áno, HVAC nie)."""
    lw = w.lower()
    v = sum(1 for c in lw if c in _VOW)
    if not v or v / len(lw) < 0.25:
        return False
    run = mx = 0
    for c in lw:
        run = 0 if c in _VOW else run + 1
        mx = max(mx, run)
    return mx <= (4 if lang in ("sk", "cs", "pl", "hr", "sr", "bs", "sl", "mk", "bg", "de") else 3)


def _compile(lang, cyr, sig):
    key = (lang, cyr, sig)
    if key in _cache:
        return _cache[key]
    ent = _entries(lang, cyr)
    parts = []
    for i, (w, _, exact) in enumerate(ent):
        pat = r"\s+".join(re.escape(x) for x in w.split())
        parts.append(f"(?P<d{i}>(?<!\\w){pat if exact else '(?i:' + pat + ')'}(?!\\w))")
    parts += [
        r"(?P<ref>(?<!\w)R[-‑ ]?(?P<refn>\d{2,4}[a-zA-Z]?)(?!\w))",
        r"(?P<cls>(?<!\w)(?P<clsl>[A-G])(?P<clsp>\+{1,3})(?!\w))",
        rf"(?P<nu>(?<![\w.,])(?P<nun>-?(?:{_NUM}))(?P<nus>\s?)(?P<nuu>{_UNITS})(?![\w²³]))",
        rf"(?P<rng>(?<![\w.,/\-–])(?P<ra>{_NUM})\s?[–-]\s?(?P<rb>{_NUM})(?![\d/\-–]|[.,]\d))",
        r"(?P<grp>(?<![\w.,])(?<!\d[   ])[1-9]\d{0,2}(?:[   ]\d{3})+(?!\d)(?![   ]\d))",
        r"(?P<amp>(?<=\s)&(?=\s))",
        r"(?P<caps>(?<![\w'’])[^\W\d_]{2,}(?![\w'’]))",
    ]
    _cache.clear()
    _cache[key] = (re.compile("|".join(parts)), ent)
    return _cache[key]


def speak(text, lang, on=None):
    """Vráti (text pre hlas, úseky). Úsek = (začiatok, koniec, pôvodný text) v texte pre hlas."""
    if on is None:
        on = db.get_setting("pronounce_on", True)
    raw = re.sub(r"\s+", " ", text or "").strip()
    if not on:
        return raw, []
    t = _pre(text, lang)
    cyr = bool(re.search("[Ѐ-ӿ]", t))
    rx, ent = _compile(lang, cyr, repr(custom()))
    T = _words(lang, cyr)
    letters = [c for c in t if c.isalpha()]
    shout = len(letters) > 12 and sum(c.isupper() for c in letters) / len(letters) > 0.7
    out, spans, pos, n = [], [], 0, 0

    def add(spoken, orig):
        nonlocal n
        if spoken != orig:
            spans.append((n, n + len(spoken), orig))
        out.append(spoken)
        n += len(spoken)

    for m in rx.finditer(t):
        add(t[pos:m.start()], t[pos:m.start()])
        pos, g, s = m.end(), m.lastgroup, m.group(0)
        d = next((k for k in m.groupdict() if k[0] == "d" and k[1:].isdigit() and m.group(k) is not None), None)
        if d:
            r = ent[int(d[1:])][1]
            add(s if r is None else r, s)
        elif m.group("ref"):
            add("R " + m.group("refn"), s)
        elif m.group("cls"):
            add(m.group("clsl") + (" " + T["plus"]) * len(m.group("clsp")), s)
        elif m.group("nu"):
            u = re.sub(r"\s", "", m.group("nuu"))
            word = {"kW": T["kW"], "KW": T["kW"], "kWh": T["kWh"], "MW": T.get("MW"), "MWh": T.get("MWh"), "W": T["W"], "dB": T["dB"],
                    "dB(A)": T["dB"] + " A", "dBA": T["dB"] + " A", "°C": T["C"], "℃": T["C"], "m²": T["m2"], "m2": T["m2"],
                    "m³": T["m3"], "m3": T["m3"]}.get(u)
            num = m.group("nun")
            add(_num(num), num)
            if word:
                add(" ", m.group("nus"))
                add(word, m.group("nuu"))
            else:
                add(m.group("nus") + m.group("nuu"), m.group("nus") + m.group("nuu"))
        elif m.group("rng"):
            add(f"{_num(m.group('ra'))} {T['to']} {_num(m.group('rb'))}" if T["to"] else s, s)
        elif m.group("grp"):
            add(_num(s), s)
        elif m.group("amp"):
            add(T["and"], s)
        else:  # slovo
            if s.isupper() and s not in ACRONYMS:
                if shout:
                    add(s.lower() if len(s) > 1 else s, s)
                elif len(s) >= 4 and _readable(s, lang):
                    add(s.capitalize(), s)
                else:
                    add(s, s)
            else:
                add(s, s)
    add(t[pos:], t[pos:])
    return "".join(out), spans


def remap(words, spoken, spans):
    """Časovanie slov z hlasu (čo naozaj povedal) -> titulky v pôvodnom zápise."""
    if not spans or not words:
        return words
    out, pos, last, low = [], 0, None, spoken.lower()
    for w in words:
        i = low.find((w.get("w") or "").lower(), pos)
        if i < 0 or i - pos > 80:
            out.append(w)
            last = None
            continue
        pos = i + len(w["w"])
        sp = next((x for x in spans if x[0] <= i < x[1]), None)
        if not sp:
            out.append(w)
            last = None
        elif sp is last:
            if out and out[-1].get("_sp") is sp:
                out[-1]["e"] = w["e"]
        else:
            last = sp
            if sp[2].strip():
                out.append({"w": sp[2].strip(), "s": w["s"], "e": w["e"], "_sp": sp})
    for w in out:
        w.pop("_sp", None)
    return out


def demo(lang):
    """Ukážková veta na vyskúšanie (značka + skratky + jednotky)."""
    return "PROLINE od N2N: SCOP 5,14, chladivo R290, trieda A+++, hlučnosť od 36 dB(A), výkon 8 kW."
