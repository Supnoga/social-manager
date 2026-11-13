"""Mapy do videí: krajiny, mestá, trasy, rieky a vlajky. Bez AI, zadarmo, offline.

Dáta (priečinok app/geo, vyrobené cez tools/geo):
- world.json   hranice krajín, Natural Earth 1:10m (verejná doména), pohľad „DEU“ = medzinárodne uznávané hranice
               (Krym = Ukrajina, Kosovo samostatne), zjednodušené na ~800 kB
- places.json  krajiny (svetadiel, oblasť, bod pre popisok, názvy v jazykoch appky), aliasy názvov, skupiny (EÚ, Pobaltie...)
- cities.json  ~5 800 miest (Natural Earth populated places, verejná doména)
- rivers.json  ~330 riek a kanálov (Natural Earth 1:50m, verejná doména)
- flags/       vlajky krajín (flag-icons, licencia MIT)
- js/          d3-geo, d3-array (ISC), topojson-client (ISC) na vykreslenie v prehliadači

Scéna v scenári: {"k":"map","c":["EG","SD"],"p":["Cairo"],"r":[["Cairo","Aswan"]],"v":"Nile"}
Server tu vyhľadá mestá/rieky/vlajky (resolve) a do stránky pošle len to, čo scéna potrebuje.
Čo sa nedá nájsť, sa radšej vynechá: žiadne vymyslené miesta.
"""
import base64
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DIR = Path(__file__).parent / "geo"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


@lru_cache(maxsize=1)
def places():
    return json.loads((DIR / "places.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def cities():
    return json.loads((DIR / "cities.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _city_index():
    idx = {}
    for i, c in enumerate(cities()):
        for k in c[6]:
            idx.setdefault(k, []).append(i)
    return idx


@lru_cache(maxsize=1)
def rivers():
    return json.loads((DIR / "rivers.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def world_json():
    return (DIR / "world.json").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def libs_js():
    return "\n".join((DIR / "js" / f).read_text(encoding="utf-8") for f in ("d3-array.min.js", "d3-geo.min.js", "topojson-client.min.js"))


@lru_cache(maxsize=300)
def flag_uri(cc):
    p = DIR / "flags" / f"{str(cc).lower()}.svg"
    if not re.fullmatch(r"[A-Za-z]{2}", str(cc)) or not p.exists():
        return ""
    return "data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode()


def country(x):
    """ISO kód alebo názov krajiny -> ISO kód (alebo None)."""
    P = places()
    s = str(x or "").strip()
    if not s:
        return None
    if s.upper() in P["countries"]:
        return s.upper()
    return P["alias"].get(norm(s))


def countries_of(x):
    """Krajina alebo skupina (EU, Middle East, Africa...) -> zoznam kódov."""
    c = country(x)
    if c:
        return [c]
    return list(places()["groups"].get(norm(x), []))


def country_name(cc, lang="en"):
    c = places()["countries"].get(cc) or {}
    n = c.get("n") or {}
    return n.get(lang) or n.get("en") or cc


def city(name, hint=()):
    """Mesto podľa názvu ("Cairo" alebo "Cairo, EG"); pri zhode viacerých vyhrá to v spomenutej krajine, potom väčšie."""
    s = str(name or "")
    cc = None
    if "," in s:
        s, rest = s.split(",", 1)
        cc = country(rest)
    ids = _city_index().get(norm(s)) or []
    if not ids:
        return None
    C = cities()
    pick = [i for i in ids if cc and C[i][1] == cc] or [i for i in ids if C[i][1] in hint] or ids
    return C[min(pick)]  # zoradené podľa počtu obyvateľov


def river(name):
    R = rivers()
    k = norm(name)
    for nm, r in R.items():
        if k in r["k"]:
            return nm, r["l"]
    k2 = norm(re.sub(r"(?i)\b(river|canal|the)\b", "", str(name)))
    for nm, r in R.items():
        if k2 and (k2 in r["k"] or k2 + " canal" in r["k"]):
            return nm, r["l"]
    return None, None


# námorné body (prielivy, kanály, mysy) na lodné trasy, aby čiara išla po mori a nie cez pevninu
SEA = {"strait of malacca": (2.5, 101.2), "singapore strait": (1.2, 104.0), "bab el mandeb": (12.6, 43.4), "gulf of aden": (12.5, 47.5),
       "suez canal": (30.5, 32.35), "port said": (31.3, 32.4), "red sea": (20.0, 38.5), "strait of gibraltar": (35.95, -5.6),
       "english channel": (50.2, -1.0), "dover strait": (51.0, 1.45), "north sea": (55.5, 3.5), "strait of hormuz": (26.6, 56.4),
       "bosporus": (41.1, 29.05), "panama canal": (9.1, -79.7), "cape of good hope": (-34.6, 18.4), "cape horn": (-56.2, -67.3),
       "arabian sea": (15.0, 63.0), "bay of bengal": (13.0, 88.0), "south china sea": (13.0, 113.0), "sri lanka south": (5.5, 80.6),
       "mediterranean": (35.5, 18.0), "sicily channel": (37.2, 11.5), "crete south": (34.4, 25.0), "atlantic": (35.0, -40.0),
       "bay of biscay": (45.5, -6.0), "cape finisterre": (43.2, -10.0), "caribbean": (15.0, -75.0), "pacific": (20.0, -150.0),
       "taiwan strait": (24.5, 119.5), "danish straits": (55.6, 10.9), "baltic sea": (56.5, 19.0), "drake passage": (-58.5, -65.0),
       "mozambique channel": (-17.0, 41.5), "strait of magellan": (-53.5, -70.5), "black sea": (43.3, 34.0), "persian gulf": (27.0, 51.5)}


def sea_point(name):
    k = norm(re.sub(r"(?i)^the ", "", str(name or "")))
    c = SEA.get(k)
    return [c[1], c[0]] if c else None


def _list(v):
    if isinstance(v, str):
        return [v]
    return [x for x in (v or []) if isinstance(x, (str, list))]


def resolve(d, lang="en"):
    """Diagram mapy -> údaje pre stránku (len overené miesta). None, keď sa nenašlo nič."""
    P = places()
    ccs = []
    for x in _list(d.get("c")):
        for c in countries_of(x if isinstance(x, str) else ""):
            if c not in ccs:
                ccs.append(c)
    ccs = ccs[:40]
    pts, seen = [], set()

    def add_city(n):
        c = city(n, ccs)
        if not c:
            return None
        key = (c[2], c[3])
        if key not in seen:
            seen.add(key)
            pts.append({"n": (c[7] or {}).get(lang) or c[0], "lat": c[2], "lon": c[3], "cap": c[5], "cc": c[1]})
        return [c[3], c[2]]

    for n in _list(d.get("p"))[:6]:
        if isinstance(n, str):
            add_city(n)
    routes = []
    for r in _list(d.get("r"))[:4]:
        if not (isinstance(r, list) and len(r) >= 2):
            continue
        ends = []
        r = r[:18]
        for j, e in enumerate(r):
            if not isinstance(e, str):
                continue
            if 0 < j < len(r) - 1:  # medzibody: najprv more, potom mesto bez popisku
                c = city(e, ccs)
                ll = sea_point(e) or (c and [c[3], c[2]])
            else:  # začiatok a koniec: mesto s popiskom
                ll = add_city(e) or sea_point(e)
            if not ll and country(e):
                cx = P["countries"][country(e)]
                ll = [cx["x"], cx["y"]]
            if ll:
                ends.append(ll)
        if len(ends) >= 2:
            routes.append(ends)
    riv = []
    for v in _list(d.get("v"))[:2]:
        if isinstance(v, str):
            nm, lines = river(v)
            if lines:
                riv.append({"n": str(v).strip(), "l": lines})
    if not (ccs or pts or riv):
        return None
    main = ccs[0] if ccs else (pts[0]["cc"] if pts else None)
    group = len(ccs) > 4
    out = {"k": "map", "c": ccs, "main": main, "pts": pts, "r": routes, "v": riv, "group": group,
           "names": {c: country_name(c, lang) for c in ccs},
           "lp": {c: [P["countries"][c]["x"], P["countries"][c]["y"]] for c in ccs if c in P["countries"]},
           "flags": {c: flag_uri(c) for c in ccs[:4] if not group and flag_uri(c)}}
    if d.get("l"):
        out["l"] = str(d["l"])[:60]
    return out


# ---------- bez AI: nájsť krajiny, mestá a rieky v texte scény ----------
@lru_cache(maxsize=1)
def _finder():
    P = places()
    keys = {}
    for a, c in P["alias"].items():
        if len(a) >= 4 and not a.isdigit() and not re.fullmatch(r"[a-z]{3}", a):
            keys[a] = ("c", c)
    for g in ("european union", "middle east", "scandinavia", "baltics", "balkans", "africa", "europe", "asia",
              "south america", "north america", "southeast asia", "central asia", "caucasus", "gulf states"):
        keys.setdefault(g, ("g", g))
    for nm, r in rivers().items():
        for k in r["k"]:
            if len(k) >= 4 and k not in keys:
                keys[k + " river"] = ("v", nm)
                if k in ("nile", "danube", "amazon", "amazonas", "mississippi", "yangtze", "mekong", "volga", "rhine", "thames", "ganges",
                         "euphrates", "tigris", "suez canal", "panama canal", "zambezi", "congo", "niger", "indus", "seine", "elbe"):
                    keys.setdefault(k, ("v", nm))
    pat = re.compile(r"\b(" + "|".join(sorted(map(re.escape, keys), key=len, reverse=True)) + r")\b")
    return keys, pat


def find_places(text, with_cities=True):
    """Z textu (anglický/ľubovoľný s latinkou) vytiahne krajiny, skupiny, rieky a veľké mestá. Bez AI."""
    keys, pat = _finder()
    t = norm(text)
    c, g, v, p = [], [], [], []
    for m in pat.finditer(t):
        kind, val = keys[m.group(1)]
        if kind == "c" and val not in c:
            c.append(val)
        elif kind == "g" and val not in g:
            g.append(val)
        elif kind == "v" and val not in v:
            v.append(val)
    if with_cities:
        idx, C = _city_index(), cities()
        words = t.split()
        for n in (1, 2, 3):
            for i in range(len(words) - n + 1):
                k = " ".join(words[i:i + n])
                if len(k) < 4 or k in keys:
                    continue
                ids = idx.get(k)
                if not ids:
                    continue
                cc = C[ids[0]]
                # len známe mestá (hlavné mestá alebo nad 1 milión), aby bežné slovo nebolo „mestom“
                if (cc[5] or cc[4] >= 1_000_000) and cc[0] not in p and not _common_word(k):
                    p.append(cc[0])
    return {"c": c, "g": g, "v": v, "p": p[:4]}


_COMMON = set("""after also before both can could dallas date even fine gross hope ideal male man mobile most nice none
normal ocean only page park parks police rich round sale same split sunny union victoria wells york""".split())


def _common_word(k):
    return k in _COMMON


def guess_map(text):
    """Návrh diagramu mapy z textu scény, alebo None."""
    f = find_places(text)
    c = f["c"] + [x for x in f["g"]]
    if not (c or f["v"] or f["p"]):
        return None
    d = {"k": "map", "c": c[:6]}
    if f["p"]:
        d["p"] = f["p"]
    if f["v"]:
        d["v"] = f["v"][0]
    return d
