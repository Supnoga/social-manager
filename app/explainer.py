"""Vysvetľujúce animované videá v štýle N2N Akadémie.

Čierne pozadie, veľký nadpis, tenké čiarové schémy, ktoré sa postupne kreslia a odkrývajú
(tok energie, cyklus tepelného čerpadla, stĺpce, výpočty, porovnanie správne/nesprávne, ikony...),
titulky s aktuálnym slovom a tenká lišta priebehu. Bez AI pri renderi, zadarmo (Chromium cez Playwright).

Každá scéna má v scenári "anim": {"t":"board","d":{"k":"<druh>", ...}}. Texty v ňom sa prekladajú
spolu so scenárom (anim.texts / anim.with_texts), obraz ostáva vo všetkých jazykoch rovnaký.
"""
import json
import re
import subprocess
import threading

from pathlib import Path

from . import db, icons_extra

W, H = 1080, 1920
KINDS = ("flow", "cycle", "bars", "calc", "compare", "count", "list", "icons", "temp", "house", "split", "text", "hero", "draw", "scene",
         "map", "timeline", "line", "growth", "pie", "stack", "dots", "size", "layers", "mech",
         "forces", "waterfall", "funnel", "loan", "inflation", "crack", "sim", "lines")
ICON_NAMES = ("house", "heatpump", "radiator", "floor", "thermo", "snow", "sun", "flame", "bolt", "drop", "coin",
              "leaf", "air", "phone", "tank", "sound", "clock", "plug", "check", "cross", "user", "tool", "chart", "shield",
              "panel", "turbine", "battery", "car", "pylon", "bulb", "meter", "globe", "window", "factory", "cloud", "city", "compressor", "fridge", "fan", "boiler", "dot")
ICON_NAMES += tuple(n for n in icons_extra.NAMES if n not in ICON_NAMES)
BASE_ICONS = ICON_NAMES[:40]  # tieto vidí AI vždy, ďalšie len podľa kanála (app/icons/*.json channels)

# ---------- rozšírenia knižnice: app/icons/*.json a app/boards/*.js + *.json (nahrávajú sa samy) ----------
_EXT = Path(__file__).parent
ICON_PACKS, ICON_ALIAS, ICON_CHANNELS = {}, {}, {}
for _f in sorted((_EXT / "icons").glob("*.json")):
    try:
        _j = json.loads(_f.read_text(encoding="utf-8"))
    except Exception:
        continue
    ICON_PACKS.update({k: v for k, v in (_j.get("icons") or {}).items() if k not in ICON_NAMES})
    ICON_ALIAS.update(_j.get("aliases") or {})
    for _c, _names in (_j.get("channels") or {}).items():
        ICON_CHANNELS.setdefault(_c, []).extend(_names)
ICON_NAMES += tuple(ICON_PACKS)
_ICON_SET = set(ICON_NAMES)
ICON_ALIAS = {k: v for k, v in ICON_ALIAS.items() if v in ICON_NAMES and k not in ICON_NAMES}
BOARD_META = {}
for _f in sorted((_EXT / "boards").glob("*.json")):
    try:
        BOARD_META[_f.stem] = json.loads(_f.read_text(encoding="utf-8"))
    except Exception:
        pass

# Stručný popis pre AI (pridá sa do promptu scenára, cca 200 tokenov)
SPEC = """"anim" = animated explainer diagram for the scene (N2N Academy style: black, thin line schematics drawn step by step). Pick ONE that explains the point visually:
{"t":"board","d":{"k":"flow","a":"input e.g. Electricity 1 kW","b":"device","c":"output e.g. Heat 4 kW","x":"optional extra input e.g. Air 3 kW"}} |
{"k":"cycle","l":["outdoor air","evaporator","compressor","condenser","home"]} (how a heat pump works) |
{"k":"bars","u":"unit","i":[["label",number,"optional ISO country code = flag"],...max 4]} | {"k":"calc","r":[["1 600 m³ × 10,5","16 800 kWh"],...max 4]} |
{"k":"compare","a":["worse option","value"],"b":["better option","value"]} | {"k":"count","v":75,"pre":"","suf":" %","l":"label"} |
{"k":"list","i":["short point",...max 4]} | {"k":"icons","i":[["icon","label"],...2-4]} icons (any simple English noun works, the app has 1000+ line icons; e.g.): %ICONS%. An icon must BE the thing its label names (turbo = "turbocharger", exhaust gas = "exhaust"; "turbine" is a WIND turbine, "cloud" is a rain cloud): never a look-alike; if no icon shows the thing, write "dot" |
{"k":"temp","a":["Outside",-10],"b":["Inside",21],"u":"°C"} | {"k":"house","i":[["Roof",25],["Walls",35],["Windows",15],["Floor",10]]} (heat losses %) |
{"k":"split","u":"%","i":[["from air",75],["electricity",25]]} | {"k":"text","w":"2-5 key words"} |
{"k":"svg","svg":"<g>...</g>"} = CUTAWAY MADE FOR THIS SCENE: inline SVG (viewBox 864x560, no <svg> tag) that shows the inside of the thing and how it moves: real shapes (housing, rotor, piston, valves, pipes, layers, fluid), moving with SMIL <animate>/<animateTransform>/<animateMotion> (dur 2-4s, repeatCount="indefinite"; gas/fluid as dots moving along a path; heat as colour change). Style: black background, white strokes 3-4 px, fills #111/#222, ONE accent colour written as ACC for the moving/important part, 2-4 labels <text font-size="26"> in CAPS inside the frame, parts sized and placed like the real machine (moving parts touch what they push), colour only the part that is working right now, fill 70% of the frame, no gradients/filters/images, max 2500 chars. Use it for the 1-3 key "how it works" scenes when no ready "mech" fits |
{"k":"hero","i":"icon","w":"2-4 words","s":"optional short second line"} (one big animated picture of the thing we talk about; use it for story, everyday comparisons and scenes without numbers)
{"k":"draw","e":[...max 14 elements]} = your own animated line drawing on a 432x280 canvas (x right, y down). Use it when the viewer should SEE the thing happen instead of reading about it (example: a 2-blade, a 3-blade and a 4-blade wind turbine side by side, the 2-blade one shaking). Elements:
{"s":"turbine","p":[xCenter,yGround,height],"n":blades,"l":"label"} | {"s":"line","p":[x1,y1,x2,y2]} | {"s":"arrow","p":[x1,y1,x2,y2]} | {"s":"circle","p":[cx,cy,r]} | {"s":"rect","p":[x,y,w,h]} | {"s":"text","p":[x,y],"t":"1-3 words"} | {"s":"icon","i":"icon name","p":[xCenter,yCenter,size]}.
Optional on every element: "c":1 (red highlight) or 2 (grey), "a":"spin" / "shake" / "pulse" / "float" / "flow" (moving dots along a line or arrow; may combine like "spin shake"; a turbine always spins), "at":0,1,2.. (step when it appears, so the drawing builds up while the voice explains), "l":"label under it".
A drawing MUST be built from real objects (turbine, icons); lines, arrows, circles, rectangles and texts are only helpers (ground line, frame, highlight ring, pointer). Never let a bare circle, rectangle or line stand for a real thing: if there is no icon for the thing, use "scene", "hero" or a number diagram instead. Objects are big (icons 70-110 px, turbines 130-180 px high), 2-4 objects per drawing.
Keep drawings simple and big, leave 20 px margin, labels inside the canvas. Never put a text on top of a line, arrow or shape or on another text: place it beside with a clear gap (texts are centered on their x). Something must MOVE in every drawing (spin, shake, flow, pulse) and it must show the exact thing the voice is describing at that moment: the machine, the part, the before and after, what goes in and what comes out.
{"k":"scene","n":[["icon","label","optional: spin / shake / pulse / float"],...2-6 things],"l":[[fromIndex,toIndex,"what flows (1-2 words)",1 if this is the highlighted red flow else 0],...]} = ready-made pictures connected by moving arrows; the app arranges everything neatly by itself (no coordinates). Best with 2-4 of these, which are drawn as real figures and buildings with coins, data or goods travelling between them: user, people, phone, tv, laptop, wifi, house, city, store, bank, factory, server, cloud, document, mail, calendar, wallet, coins, banknote, piggybank, pricetag, lock, shield, key, chart, growth, package, truck, plane, ship, globe, clock, idea, chip, check, cross; say in each arrow label what moves (pays rent, sends data, ships goods). Use it whenever things give something to each other (example: n=[["air","Outdoor air"],["bolt","Electricity"],["heatpump","Heat pump"],["house","Home"]], l=[[0,2,"3 kW",0],[1,2,"1 kW",0],[2,3,"4 kW heat",1]]). Every thing has a label. Only icons from the list. Keep it simple: at most 5 things and 5 arrows, an arrow should go to a neighbouring thing and not jump over another one.
{"k":"map","c":["EG","SD"],"p":["Cairo"],"r":[["Cairo","Aswan"]],"v":"Nile","l":"optional 1-3 word tag"} = real animated map: the globe turns and zooms in, countries light up with their flags. c = ISO 2-letter codes (first = main) or a region (EU, Middle East, Africa, Balkans...), p = max 4 real cities, r = routes: ["Cairo","London"] is a straight flight line; a ship route lists sea waypoints between the ports, e.g. ["Shanghai","South China Sea","Singapore Strait","Sri Lanka South","Bab el Mandeb","Red Sea","Suez Canal","Crete South","Sicily Channel","Strait of Gibraltar","Cape Finisterre","English Channel","Rotterdam"] (other points: Strait of Malacca, Hormuz, Persian Gulf, Cape of Good Hope, Panama Canal, Caribbean, Atlantic, Pacific, Bosporus, Black Sea, Danish Straits, Baltic Sea, North Sea, Taiwan Strait), v = river or canal. Only real places, all fields except c optional. Use "map" EVERY time the voice names a country, region, city, river, sea route or border: it beats all other rules.
{"k":"timeline","i":[["1869","Suez Canal opens"],...max 5]} (history, dates) | {"k":"line","u":"unit","i":[["2000",12],["2010",30],...max 10]} (change over time)
PRIORITY: the picture must SHOW what the voice says at that moment. A machine, device or process being explained -> "mech" (ready animated cutaway) when one fits, otherwise "svg" (a cutaway you draw for this scene); a place -> "map"; a spoken number -> a number diagram; things passing something to each other -> "scene"; "draw" only to compare objects side by side; "hero"/"text" only for the hook or the closing line. Never just a spinning icon of the thing.
Labels max 4 words, numbers as numbers."""



# Vizuály na mieru téme kanála: do zadania pre AI idú len riadky, ktoré kanál potrebuje (šetrí tokeny)
PACK = {
    "growth": '{"k":"growth","p":1000,"r":7,"y":30,"m":0,"u":"€","l":"after 30 years","a":"paid in","b":"interest","x":"years"} = compound growth the app CALCULATES itself (p start sum, r % per year, y years, m monthly addition): savings, investing, loans and debt',
    "pie": '{"k":"pie","u":"%","c":"centre text","i":[["Needs",50],["Wants",30],["Savings",20]]} = shares of a whole (budget, where the money goes, market share), max 5',
    "stack": '{"k":"stack","u":"$","i":[["1 million",1000000],["1 billion",1000000000]]} = huge numbers shown as squares in true proportion, max 3',
    "dots": '{"k":"dots","n":100,"h":23,"l":"of people ..."} = 100 dots, h of them light up (probability, percent of people, 1 in N)',
    "size": '{"k":"size","u":"m","d":"v or h","i":[["Burj Khalifa",828,"skyscraper"],["Eiffel Tower",330],["Person",1.8,"user"]]} = real sizes side by side in true scale (heights v, lengths h), optional icon, max 4',
    "layers": '{"k":"layers","u":"cm","z":0,"i":[["Plaster",2],["Brick",30],["Insulation",15,1]]} = cross-section layer by layer, top to bottom, real thickness (third value 1 = highlighted layer; "z":1 adds a depth ruler, for ground and underground)',
    "forces": '{"k":"forces","i":"plane","f":[["Lift","up",3],["Weight","down",3],["Thrust","right",2],["Drag","left",1]]} = force arrows on one object (icon), arrow length = size of the force, first arrow highlighted',
    "waterfall": '{"k":"waterfall","t":5,"u":"€","l":"Coffee","i":[["Rent",1.2],["Staff",1.5],["Beans",0.4],["Profit",0.5,1]]} = what a price is made of (third value 1 = highlight)',
    "funnel": '{"k":"funnel","i":[["See the ad",10000],["Visit",800],["Buy",40]]} = how many people are left at each step',
    "loan": '{"k":"loan","p":200000,"r":4,"y":30,"u":"€"} = loan or mortgage: the app CALCULATES the monthly payment, total paid and interest',
    "inflation": '{"k":"inflation","v":100,"r":3,"y":20,"u":"€","i":"cart"} = what the same money buys after y years of r % inflation (the app calculates)',
    "crack": '{"k":"crack","l":[6,8,10,12,16],"set":"lower|mixed|all"} = time to guess a password by length (the app calculates at 10 billion guesses per second)',
    "sim": '{"k":"sim","m":"doors|coin|dice","n":1000,"l":["stay","switch"]} = the experiment played 1000 times live, result in % (doors = the three doors puzzle, dice = chance of sum 7)',
    "lines": '{"k":"lines","x":["6:00","9:00","12:00","15:00","18:00"],"s":[["Solar",[0,30,80,50,5]],["Demand",[40,60,55,60,90]]]} = 2-3 lines over the same time (supply vs demand, two brands)',
    "hist": '{"k":"map","y":[-200,-1,117],"h":["Roman Empire"],"l":"optional tag"} = HISTORICAL map: approximate borders in that year (1-4 years show growth or fall over time), h = empire or state names as in history books',
    "truesize": '{"k":"map","c":["RU"],"t":"US"} = true size: the first country slides onto country t at the same real size',
    "mech": '{"k":"mech","m":"piston|wankel|gears|wing|wave|radar|orbit|pendulum|jet","n":[12,24],"l":["label 1","label 2","label 3","label 4"]} = ready animated mechanism: piston = 4-stroke engine cutaway (l = the 4 strokes), wankel = rotary engine cutaway (l = intake, compression, power, exhaust); piston and wankel take "f":"intake|compression|power|exhaust" (camera close-up on the stroke the voice talks about) or "f":"run" (running at full speed), and {"k":"mech","m":"versus","a":"piston","b":"wankel","l":["name A","name B"]} runs two of them side by side to compare; gears (n = teeth, l = the 2 gears), wing = airflow and lift (l = lift, airflow), wave (n = 1-2 frequencies, l = their names: sound, light, radio), radar sweep, orbit (n satellites sending to one point: GPS, l = Earth, satellites), pendulum',
}
CHANNEL_PACKS = {
    "cash": ("growth", "inflation", "pie", "stack", "dots", "lines"), "wallet": ("loan", "growth", "pie", "waterfall", "inflation", "stack"),
    "stocks": ("growth", "lines", "pie", "stack", "dots", "sim"), "company": ("waterfall", "funnel", "pie", "stack", "dots", "growth"),
    "brands": ("lines", "pie", "funnel", "waterfall", "stack"),
    "machines": ("mech", "forces", "size", "layers"), "engines": ("mech", "forces", "size", "lines", "pie"), "flight": ("forces", "mech", "size", "dots"),
    "mega": ("size", "forces", "layers", "mech"), "house": ("layers", "size", "pie", "waterfall"), "underground": ("layers", "size", "mech"),
    "industry": ("size", "stack", "layers", "mech", "waterfall"), "inventions": ("mech", "size", "lines"), "arsenal": ("mech", "forces", "size", "layers"),
    "forces": ("forces", "mech", "dots", "size", "sim"), "digital": ("crack", "mech", "dots", "stack", "funnel"), "logic": ("sim", "dots", "pie", "stack", "growth"),
    "logistics": ("size", "stack", "funnel", "waterfall"), "maps": ("hist", "truesize", "dots", "size", "stack"), "nations": ("truesize", "hist", "dots", "pie", "size", "stack"),
    "energy": ("lines", "mech", "size", "pie", "stack", "waterfall"), "n2n": ("layers", "pie", "waterfall"),
}



for _m in BOARD_META.values():
    KINDS += tuple(k for k in (_m.get("kinds") or {}) if k not in KINDS)
    PACK.update(_m.get("pack") or {})
    for _c, _ks in (_m.get("channels") or {}).items():
        CHANNEL_PACKS[_c] = tuple(CHANNEL_PACKS.get(_c, ())) + tuple(k for k in _ks if k not in CHANNEL_PACKS.get(_c, ()))
_ALL_PACK = ("default",)


def icon_name(name):
    """Kanonické meno ikony aj zo synonyma, množného čísla alebo časti mena (rovnako ako IR v stránke); None = nič."""
    def one(n):
        for c in (n, re.sub(r"ies$", "y", n), re.sub(r"es$", "", n), re.sub(r"s$", "", n)):
            if c in _ICON_SET:
                return c
            if ICON_ALIAS.get(c) in _ICON_SET:
                return ICON_ALIAS[c]
        return None
    if not isinstance(name, str) or len(name) > 40:
        return None
    n = re.sub(r"[\s-]+", "_", name.lower().strip())
    r = one(n)
    if r:
        return r
    for x in reversed([x for x in n.split("_") if x]):
        r = one(x)
        if r:
            return r
    return None


def icon_ok(name):
    return icon_name(name) is not None


def _icons_js(data):
    """Do stránky len ikony z balíkov, ktoré video naozaj používa (stránka ostane malá aj pri tisícoch ikon)."""
    seen, alias = set(), {}

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            c = icon_name(x)
            if c:
                seen.add(c)
                k = re.sub(r"[\s-]+", "_", x.lower().strip())
                if k != c:
                    alias[k] = c
    walk(data)
    body = "".join(json.dumps(k) + ":" + json.dumps(ICON_PACKS[k]) + "," for k in sorted(seen) if k in ICON_PACKS)
    return body, json.dumps(alias)


def _chan(project=None):
    name = str((project or {}).get("name") or "").lower()
    return next((key for key in CHANNEL_PACKS if key in name), None)


def icons_for(project=None):
    """Ikony, ktoré AI uvidí: základné + tie, ktoré sa hodia kanálu (šetrí tokeny)."""
    c = _chan(project)
    extra = [n for n in ICON_CHANNELS.get(c or "default", ICON_CHANNELS.get("default", [])) if n in ICON_NAMES and n not in BASE_ICONS]
    return ",".join(dict.fromkeys(list(BASE_ICONS) + extra))


def packs_for(project=None):
    name = str((project or {}).get("name") or "").lower()
    for key, kinds in CHANNEL_PACKS.items():
        if key in name:
            return kinds
    return ("pie", "dots", "size")


def spec(project=None):
    """SPEC + vizuály na mieru kanálu (len tie, ktoré jeho témy potrebujú)."""
    extra = " |\n".join(PACK[k] for k in packs_for(project) if k in PACK)
    return SPEC.replace("%ICONS%", icons_for(project)) + "\nMore diagrams for this channel (use them whenever they fit the spoken point better than the defaults):\n" + extra


_SKIP = {}
for _m in BOARD_META.values():
    for _k, _v in (_m.get("kinds") or {}).items():
        _SKIP[_k] = {f: tuple(c) for f, c in (_v.get("skip") or {}).items()}


# ---------- texty na preklad (rovnaké poradie pre texts/with_texts) ----------
def _slots(d):
    """Zoznam (cesta) k textom v diagrame. Čísla sa neprekladajú."""
    k, out = d.get("k"), []
    for f in ("a", "b", "c", "x", "l", "w", "s", "u", "pre", "suf"):
        v = d.get(f)
        if isinstance(v, str) and v.strip() and not (f in ("u", "pre", "suf") and not re.search(r"[^\W\d_]{4,}", v)):
            out.append((f,))
        elif isinstance(v, list) and f in ("a", "b") and v and isinstance(v[0], str):
            out.append((f, 0))
            if len(v) > 1 and isinstance(v[1], str) and re.search(r"[^\W\d_]{2,}", v[1]):
                out.append((f, 1))
        elif isinstance(v, list) and f == "l":
            out += [(f, i) for i, x in enumerate(v) if isinstance(x, str) and x.strip()]
    for i, x in enumerate(d.get("e") or [] if k == "draw" else []):
        for f in ("t", "l"):
            if isinstance(x, dict) and isinstance(x.get(f), str) and re.search(r"[^\W\d_]{2,}", x[f]):
                out.append(("e", i, f))
    for f, j in (("n", 1), ("l", 2)) if k == "scene" else ():
        for i, x in enumerate(d.get(f) or []):
            if isinstance(x, list) and len(x) > j and isinstance(x[j], str) and re.search(r"[^\W\d_]{2,}", x[j]):
                out.append((f, i, j))
    for f in ("i", "r", "f") if k != "map" else ():
        for i, x in enumerate(d.get(f) if isinstance(d.get(f), list) else []):
            if isinstance(x, str):
                out.append((f, i))
            elif isinstance(x, list):
                for j, y in enumerate(x):
                    if isinstance(y, str) and y.strip() and not (k == "icons" and j == 0) and j not in _SKIP.get(k, {}).get(f, ()) and not (k in ("bars", "size") and j == 2) and not (k == "forces" and j == 1) and (
                            k == "calc" or re.search(r"[^\W\d_]{2,}", y)):
                        out.append((f, i, j))
    return out


def _get(d, p):
    v = d
    for x in p:
        v = v[x]
    return v


def _set(d, p, val):
    v = d
    for x in p[:-1]:
        v = v[x]
    v[p[-1]] = val


def texts(d):
    try:
        return [str(_get(d, p)) for p in _slots(d or {})]
    except Exception:
        return []


def with_texts(d, tr):
    d = json.loads(json.dumps(d or {}))
    try:
        for p, t in zip(_slots(d), tr):
            if isinstance(t, str) and t.strip():
                _set(d, p, t)
    except Exception:
        pass
    return d


# ---------- staré typy animácií a scény bez diagramu ----------
KEYWORDS = [
    (r"čerpadl|čerpadel|heat ?pump|wärmepumpe|pompa|pompe|pump|tepelk", "heatpump"),
    (r"\bdom|domov|house|home|haus|bývan|byt", "house"),
    (r"radiátor|radiator|heizkörper|vykurov", "radiator"),
    (r"podlah|floor|fußboden", "floor"),
    (r"€|eur|euros?|úspor|ušetr|cena|cien|náklad|platí|faktúr|price|cost|kosten|spar", "coin"),
    (r"zim|mráz|chlad|-\s?\d+\s?°|winter|cold|frost|kalt", "snow"),
    (r"solár|fotovolt|solar panel|panel|photovolt", "panel"),
    (r"veter|turbín|wind|turbine", "turbine"),
    (r"batéri|battery|batterie|akumul", "battery"),
    (r"elektromobil|auto\b|\bcar\b|\bev\b", "car"),
    (r"sieť|grid|netz|vedenie|blackout", "pylon"),
    (r"leto|slnk|summer|sun|sonne", "sun"),
    (r"plyn|gas|kotol|boiler|kessel|drev|pelet", "flame"),
    (r"elektr|prúd|kwh|strom|electric|electricity", "bolt"),
    (r"teplá voda|voda|water|wasser|bojler|zásobník", "drop"),
    (r"hluk|tich|db|noise|quiet|leise", "sound"),
    (r"aplik|app|mobil|telefón|phone", "phone"),
    (r"vzduch|air|luft", "air"),
    (r"ekolog|co2|emisi|príroda|green|klima", "leaf"),
    (r"montáž|inštal|servis|install|montage", "tool"),
    (r"záruk|garanc|bezpeč|warranty|garantie", "shield"),
    (r"teplot|°c|thermo|temperatur", "thermo"),
    (r"rok|rokov|hod|minút|čas|year|time|zeit", "clock"),
]


KEYWORDS += icons_extra.KEYWORDS


def _num(s):
    m = re.search(r"(-?\d[\d\s.,]*)", s or "")
    if not m:
        return None
    raw = m.group(1).strip().replace(" ", "").replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}([.,]\d{3})+", raw):
        raw = re.sub(r"[.,]", "", raw)
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def guess(onscreen, visual="", lang="en"):
    """Bez AI: z textu scény urobí jednoduchý diagram (ikony alebo číslo).
    Po anglicky sa slovo hľadá celé („happens“ nie je app, „important“ nie je port) a ikona musí sedieť k scéne (auto_visual.icon_fit)."""
    from . import auto_visual
    txt = f"{onscreen} {visual}".lower()
    icons = []
    for rx, name in KEYWORDS:
        if name in icons:
            continue
        if lang == "en":
            if re.search(r"(?<![a-zà-ž])(?:" + rx + r")(?:s|es|e|ed|ing)?(?![a-zà-ž])", txt) and auto_visual.icon_fit(name, "", txt):
                icons.append(name)
        elif re.search(rx, txt):
            icons.append(name)
    if "=" in (onscreen or "") and re.search(r"\d", onscreen):
        l, r = onscreen.split("=", 1)
        return {"k": "calc", "r": [[l.strip(), r.strip()]]}
    n = _num(onscreen)
    if n is not None and n == int(n):
        n = int(n)
    if n is not None and re.search(r"%|€|kw|°|x|×|rok", (onscreen or "").lower()):
        m = re.search(r"-?\d[\d\s.,]*\s*(%|€|kWh|kW|°C|×|x)?", onscreen)
        suf = (m.group(1) or "") if m else ""
        return {"k": "count", "v": n, "pre": "", "suf": (" " + suf) if suf and suf not in "%×x" else suf, "l": ""}
    if len(icons) == 1:
        return {"k": "hero", "i": icons[0], "w": ""}
    if icons:
        return {"k": "icons", "i": [[i, ""] for i in icons[:3]]}
    return {"k": "text", "w": onscreen or ""}


def from_old(a, onscreen=""):
    """Prevod starších animácií (counter, bars, list, compare, kinetic) na diagram."""
    t, d = (a or {}).get("t"), (a or {}).get("d") or {}
    if t == "board":
        return d
    if t == "counter":
        return {"k": "count", "v": d.get("value", 0), "pre": d.get("prefix", ""), "suf": d.get("suffix", ""), "l": d.get("label", "")}
    if t == "bars":
        return {"k": "bars", "u": (d.get("suffix") or "").strip(), "i": [[x.get("label", ""), x.get("value", 0)] for x in d.get("items", [])][:4]}
    if t == "list":
        return {"k": "list", "i": list(d.get("items", []))[:4]}
    if t == "compare":
        l, r = d.get("left") or {}, d.get("right") or {}
        return {"k": "compare", "a": [l.get("label", ""), str(l.get("value", ""))], "b": [r.get("label", ""), str(r.get("value", ""))]}
    if t == "kinetic":
        return {"k": "text", "w": " ".join(d.get("words", []))}
    return None


def board_of(scene, lang="en"):
    a = scene.get("anim")
    d = from_old(a, scene.get("onscreen", "")) if isinstance(a, dict) else None
    if not d or d.get("k") not in KINDS:
        d = guess(scene.get("onscreen", ""), scene.get("visual", ""), lang)
    if d.get("k") == "svg" and not clean_svg(d.get("svg")):
        d = guess(scene.get("onscreen", ""), scene.get("visual", ""), lang)
    if d.get("k") == "draw":
        # voľná kresba len z hotových dielov: bez krivých čiar od AI a aspoň jeden skutočný objekt, inak radšej jednoduchý diagram
        els = [e for e in (d.get("e") or []) if isinstance(e, dict) and e.get("s") != "path"]
        if not any(e.get("s") in ("turbine", "icon") for e in els):
            return guess(scene.get("onscreen", ""), scene.get("visual", ""), lang)
        d = dict(d, e=els)
    if d.get("k") == "scene":
        ok = [x for x in (d.get("n") or []) if isinstance(x, list) and x and icon_ok(x[0])]
        if len(ok) < 2 or len(ok) != len(d.get("n") or []):
            d = guess(scene.get("onscreen", ""), scene.get("visual", ""), lang)
    return auto_map(scene, d)


_MAP_WORD = re.compile(r"(?i)\b(map|maps|mapa|mapy|mape|karte|carte|mappa|kaart|mapie|térkép|harta|border|borders|route|routes)\b")


def auto_map(scene, d):
    """Bez AI: keď scéna hovorí o krajine, meste alebo rieke a obraz ju neukazuje, dá tam mapu.
    Číselné grafy (stĺpce, výpočty, porovnania) nechá tak, mapa nahradí len všeobecný obrázok alebo text."""
    if d.get("k") == "map":
        return d
    vis, ons = str(scene.get("visual") or ""), str(scene.get("onscreen") or "")
    weak = d.get("k") in ("hero", "text", "icons", "list", "scene", "draw")
    if not (weak or _MAP_WORD.search(vis)):
        return d
    try:
        from . import geo
        m = geo.guess_map(ons + " . " + vis) if (_MAP_WORD.search(vis) or d.get("k") in ("hero", "text")) else geo.guess_map(ons)
    except Exception as e:
        print("mapa:", e)
        return d
    return m or d


_SVG_BAD = re.compile(r"(?is)<\s*(script|foreignObject|iframe|image|use|style)\b.*?(</\s*\1\s*>|/>)|\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')|(xlink:)?href\s*=\s*[\"'](?!#)[^\"']*[\"']|javascript:|url\((?!#)[^)]*\)")


def clean_svg(src):
    """Rez na mieru od AI: len čisté SVG tvary a animácie (bez skriptov, odkazov, obrázkov); pokazené = None."""
    s = str(src or "").strip()
    if not (40 < len(s) < 9000):
        return None
    s = re.sub(r"(?is)^\s*<svg[^>]*>|</svg>\s*$", "", s)
    s = _SVG_BAD.sub("", s)
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">' + s + "</svg>")
    except Exception:
        return None
    if len(list(root.iter())) < 4 or not any(e.tag.split("}")[-1].startswith("animate") for e in root.iter()):
        return None  # bez pohybu to nie je animácia, radšej iný obraz
    return s


def prepare(v, lang="en"):
    """Pred renderom: mapa dostane overené súradnice a vlajky, stĺpce vlajky krajín. Čo sa nenájde, ostane bez mapy."""
    if v.get("k") == "svg":
        c = clean_svg(v.get("svg"))
        return dict(v, svg=c) if c else {"k": "text", "w": str(v.get("w") or v.get("l") or "")}
    if v.get("k") == "map":
        from . import geo
        r = geo.resolve(v, lang)
        return r or {"k": "text", "w": str(v.get("l") or "")}
    if v.get("k") in ("bars", "rank") and any(isinstance(x, list) and len(x) > 2 for x in v.get("i") or []):
        from . import geo
        fl = {}
        for i, x in enumerate((v.get("i") or [])[:6]):
            c = geo.country(x[2]) if isinstance(x, list) and len(x) > 2 and isinstance(x[2], str) and (
                v["k"] == "bars" or re.fullmatch(r"[A-Za-z]{2}", x[2].strip())) else None
            if c and geo.flag_uri(c):
                fl[i] = geo.flag_uri(c)
        if fl:
            return dict(v, fl=fl)
    return v


def needs_boards(scenes):
    return any(not (isinstance(s.get("anim"), dict) and s["anim"].get("t") == "board") for s in scenes)


def ensure_boards(script_id):
    """Pre scenár bez diagramov: 1 malé lacné AI volanie navrhne diagramy (raz, uloží sa). Bez AI: odhad z textu."""
    from . import ai, languages
    s = db.one("SELECT * FROM scripts WHERE id=?", (script_id,))
    if not s:
        return []
    scenes = json.loads(s["scenes"] or "[]")
    if not scenes or not needs_boards(scenes):
        return scenes
    need = [i for i, sc in enumerate(scenes) if not (isinstance(sc.get("anim"), dict) and sc["anim"].get("t") == "board")]
    data = None
    try:
        items = {str(i): {"onscreen": scenes[i].get("onscreen", ""), "visual": (scenes[i].get("visual") or "")[:140]} for i in need}
        data = ai.ask(f"""Short explainer video "{s['title']}". Voiceover: {s['voiceover'][:1500]}
For each scene choose an animated diagram. {spec(db.one("SELECT name FROM projects WHERE id=?", (s["project_id"],)))}
Write labels in {languages.english(s['lang'])}. Scenes: {json.dumps(items, ensure_ascii=False)}
Return JSON: {{"<scene number>":{{"k":"..."}}}}""", "boards", "cheap")
    except Exception as e:
        print("diagramy cez AI:", e)
    for i in need:
        d = (data or {}).get(str(i)) if isinstance(data, dict) else None
        if isinstance(d, dict) and isinstance(d.get("d"), dict):
            d = d["d"]
        if not (isinstance(d, dict) and d.get("k") in KINDS):
            d = board_of(scenes[i])
        scenes[i]["anim"] = {"t": "board", "d": d}
    db.run("UPDATE scripts SET scenes=? WHERE id=?", (json.dumps(scenes, ensure_ascii=False), script_id))
    return scenes


_STRONG = ("map", "timeline", "line", "bars", "compare", "count", "calc", "split", "temp", "scene")


def _bad_scenes(scenes, why=""):
    """Indexy scén, ktoré by kontrola označila: slabé (ikony, text, zoznam, kresba), hrubá kresba, prázdne alebo prekrývajúce sa."""
    from . import auto_visual
    body = scenes[:-1] if len(scenes) > 2 else scenes
    out = set()
    for i, sc in enumerate(body):
        a = sc.get("anim") or {}
        d = a.get("d") if isinstance(a, dict) and a.get("t") == "board" else a
        k = d.get("k") if isinstance(d, dict) else None
        if k in auto_visual.WEAK and not auto_visual.actors(d):
            out.add(i)
        elif k == "svg" or (k == "mech" and d.get("m") not in auto_visual.PRECISE):
            out.add(i)
    for m in re.finditer(r"Prázdna scéna: ([\d, ]+)", why or ""):
        out |= {int(x) - 1 for x in re.findall(r"\d+", m.group(1))}
    out |= {int(x) - 1 for x in re.findall(r"Prekrývanie v scéne (\d+)", why or "")}
    return sorted(i for i in out if 0 <= i < len(body))


def strengthen(script_id, why=""):
    """Slabé scény (len ikony či text), prázdne a prekrývajúce sa scény dostanú nový obraz: mapu, graf, časovú os alebo blok „kto komu“.
    Jedno malé lacné AI volanie len pre tieto scény (scenár ani hlas sa nemenia). Vráti počet vymenených scén (16.11.)."""
    from . import ai, auto_visual, languages
    s = db.one("SELECT * FROM scripts WHERE id=?", (script_id,))
    if not s:
        return 0
    scenes = ensure_boards(script_id)
    bad = _bad_scenes(scenes, why)
    if not bad:
        return 0
    p = db.one("SELECT * FROM projects WHERE id=?", (s["project_id"],)) or {}
    packs = [k for k in packs_for(p) if k in PACK]
    allowed = set(_STRONG) | {PACK[k].split('"k":"')[1].split('"')[0] for k in packs if '"k":"' in PACK[k]}
    items = {str(i): {"onscreen": scenes[i].get("onscreen", ""), "visual": (scenes[i].get("visual") or "")[:160]} for i in bad}
    sprites = "user, people, phone, tv, laptop, wifi, house, city, store, bank, factory, server, cloud, document, mail, calendar, wallet, coins, " \
              "banknote, piggybank, pricetag, lock, shield, key, chart, growth, package, truck, warehouse, container, plane, ship, globe, clock, idea, " \
              "chip, check, cross, drop, bolt, flame, snow, leaf, car, battery, card, robot, satellite, gear, sun, flag, plug, tool"
    lines = [x for x in SPEC.split("\n") if any(f'"k":"{k}"' in x for k in ("bars", "compare", "temp", "split", "scene", "map", "timeline"))]
    try:
        data = ai.ask(f"""Video "{s['title']}". These scenes now show only icons or text, or their picture is empty or crowded.
Give each scene a NEW diagram that SHOWS what the scene says. Allowed diagrams ONLY:
{chr(10).join(lines)}
{chr(10).join(PACK[k] for k in packs)}
Rules: a place, country, city or route -> "map"; years or history -> "timeline"; a number -> "bars", "count", "compare", "line" or "calc" with real numbers;
people, companies or things giving something to each other -> "scene" with 2-4 things ONLY from this list: {sprites} (every thing labelled, every arrow says what moves).
Never "hero", "text", "list", "icons", "draw", "svg" or "mech". Labels max 3 words. Write labels in {languages.english(s['lang'])}.
Scenes: {json.dumps(items, ensure_ascii=False)}
Return JSON: {{"<scene number>":{{"k":"..."}}}}""", "strengthen", "cheap")
    except Exception as e:
        print("silnejší obraz:", e)
        return 0
    n = 0
    for i in bad:
        d = (data or {}).get(str(i)) if isinstance(data, dict) else None
        if isinstance(d, dict) and isinstance(d.get("d"), dict):
            d = d["d"]
        if not (isinstance(d, dict) and d.get("k") in allowed):
            continue
        if d["k"] == "scene" and not auto_visual.actors(d):
            continue   # účastníci, ktorých nevieme nakresliť: ostal by len rad ikon
        scenes[i]["anim"] = {"t": "board", "d": d}
        n += 1
    if n:
        db.run("UPDATE scripts SET scenes=? WHERE id=?", (json.dumps(scenes, ensure_ascii=False), script_id))
    return n


def localized_scenes(s):
    """Scény pre video v jazyku skriptu. Starší preklad bez diagramov: vezme diagramy z originálu a preloží ich texty zadarmo."""
    scenes = json.loads(s["scenes"] or "[]")
    if not needs_boards(scenes):
        return scenes
    src = db.one("SELECT * FROM scripts WHERE idea_id=? AND is_source=1", (s["idea_id"],))
    if not src or src["id"] == s["id"]:
        return ensure_boards(s["id"])
    src_sc = ensure_boards(src["id"])
    for i, sc in enumerate(scenes):
        if i < len(src_sc) and not (isinstance(sc.get("anim"), dict) and sc["anim"].get("t") == "board"):
            d = src_sc[i]["anim"]["d"]
            tx = texts(d)
            if tx:
                try:
                    from . import translate
                    tr, _ = translate.translate_texts(tx, src["lang"], s["lang"])
                    d = with_texts(d, tr)
                except Exception:
                    pass
            sc["anim"] = {"t": "board", "d": d}
    db.run("UPDATE scripts SET scenes=? WHERE id=?", (json.dumps(scenes, ensure_ascii=False), s["id"]))
    return scenes


# ---------- časovanie scén podľa viet ----------
FOX_MOODS = ("surprised", "thinking", "worried", "happy", "no", "point")
_FX_NO = re.compile(r"\b(myth|wrong|not|never|mistake|lie|lies|false|actually|isn't|doesn't|don't|can't|fails?)\b", re.I)
_FX_WOR = re.compile(r"\b(danger\w*|explo\w+|crash\w*|fire|burn\w*|die[sd]?|death|deadly|risk\w*|collaps\w*|toxic|poison\w*|disaster|fail\w*|broke|breaks?|melt\w*|war|attack\w*|kill\w*)\b", re.I)
_FX_NUM = re.compile(r"\d")


def fox_moods(scenes, sc_data, words):
    """Emócie líšky po scénach (pravidlá z rozboru úspešných kanálov, 19.11.): 1–3 s reakcia, 4–6 za krátke video, nikdy dve rovnaké po sebe.
    AI môže dať do scény pole "fox"; inak sa emócia odhadne z textu bez ďalšieho volania AI."""
    n, prev = len(sc_data), ""
    cap = 6 if n <= 12 else max(6, n // 2)
    used = 0
    for i, (sc, d) in enumerate(zip(scenes, sc_data)):
        spoken = " ".join(w["w"] for w in words if d["t0"] - .05 <= w["s"] < d["t1"])
        k = (d.get("v") or {}).get("k")
        m = str(sc.get("fox") or "").strip().lower()
        if m not in FOX_MOODS:
            m = ""
            if i == 0:
                m = "thinking" if "?" in spoken else "surprised"
            elif i == n - 1 and n > 2:
                m = "happy"
            elif _FX_WOR.search(spoken):
                m = "worried"
            elif _FX_NO.search(spoken):
                m = "no"
            elif "?" in spoken:
                m = "thinking"
            elif _FX_NUM.search(spoken) and k in ("count", "bars", "calc", "compare", "pie", "hero", "waterfall", "dots"):
                m = "surprised"
            elif k == "mech" and i % 2 == 0:
                m = "point"
        if m and (m == prev or (used >= cap and i not in (0, n - 1))):
            m = ""
        if m:
            d["fx"] = m
            used += 1
        prev = m


def timeline(scenes, words, total):
    try:  # scény podľa toho, o čom hlas práve hovorí (audio.scene_times); inak rovnomerne po vetách
        from . import audio
        t = audio.scene_times(scenes, words, total)
        if t:
            return t
    except Exception as e:
        print("časovanie scén:", e)
    n = max(1, len(scenes))
    ends = [w["e"] for w in words if w["w"][-1:] in ".!?…"] if words else []
    bounds, last = [], 0.0
    for k in range(1, n):
        target = total * k / n
        cand = [e for e in ends if e > last + 1.2 and e < total - 1.0 * (n - k)]
        b = min(cand, key=lambda e: abs(e - target)) if cand else target
        if abs(b - target) > total / n * 0.6:
            b = target
        bounds.append(max(b, last + 0.8))
        last = bounds[-1]
    edges = [0.0] + bounds + [total + 0.3]
    return [(edges[i], edges[i + 1]) for i in range(n)]


def caption_chunks(words, lang, wide=False):
    # úspešné kanály: 1–3 slová naraz, menia sa každých 0,5–1 s (rozbor 19.11.); na šírku najviac 4 slová
    maxc = 16 if lang in ("de", "fi", "hu", "nl", "et", "is") else 18
    maxw = 3
    if wide:
        maxc, maxw = maxc + 12, 4
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(x["w"] for x in cur + [w])) > maxc or cur[-1]["w"][-1:] in ".!?…,;:"):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    res = []
    for i, ch in enumerate(out):
        nxt = out[i + 1][0]["s"] if i + 1 < len(out) else ch[-1]["e"] + 0.6
        res.append({"s": ch[0]["s"], "e": min(nxt, ch[-1]["e"] + 0.6),
                    "w": [{"t": x["w"], "s": x["s"]} for x in ch]})
    return res


# ---------- HTML ----------
def _font_face(family, path):
    import base64
    from pathlib import Path
    if not path or not Path(path).exists():
        return ""
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    ext = Path(path).suffix.lstrip(".").lower()
    # rozsah hrúbok 1-1000: prehliadač font umelo nezhrubne (značka má presne daný rez)
    return f"@font-face{{font-family:{family};font-weight:1 1000;src:url(data:font/{ext};base64,{b64})}}"


def page(data, font=None, font_text=None):
    fcss = _font_face("BrandF", font)
    if fcss:
        fcss += ":root{--f:BrandF,var(--f0);--ft:BrandF,var(--f0)}"
        tcss = _font_face("BrandT", font_text)
        if tcss:
            fcss += tcss + ":root{--ft:BrandT,var(--f0)}"
    geo_js = ""
    if any((sc.get("v") or {}).get("k") == "map" for sc in data.get("scenes", [])):
        from . import geo
        hist = {}
        for sc in data.get("scenes", []):
            for f in (sc.get("v") or {}).get("hist") or []:
                hist[str(f["y"])] = geo.hist_json(f["y"])
        geo_js = (geo.libs_js() + "\nwindow.TOPO=" + geo.world_json() + ";\nwindow.HIST={"
                  + ",".join(json.dumps(k) + ":" + v for k, v in hist.items()) + "};").replace("</", "<\\/")
    ic, al = _icons_js(data)
    return (TEMPLATE.replace("/*FONT*/", fcss).replace("/*GEOLIBS*/", geo_js, 1)
            .replace("/*PACK_ICONS*/", ic.replace("</", "<\\/"), 1).replace("/*ICON_ALIAS*/{}", al.replace("</", "<\\/"), 1)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{--f0:'Helvetica Neue','SF Pro Display',-apple-system,'Inter','Segoe UI',Arial,sans-serif;--f:var(--f0);--ft:var(--f0);--acc:#FF6B00;--g:#8a8a8a;--line:rgba(255,255,255,.85)}
/*FONT*/
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:#000;overflow:hidden;font-family:var(--f);color:#fff;-webkit-font-smoothing:antialiased}
#glow{position:absolute;width:1300px;height:1300px;border-radius:50%;background:radial-gradient(circle,var(--acc) 0%,transparent 62%);opacity:.0;left:420px;top:900px}
.sc{position:absolute;left:0;top:0;display:none}
#root{position:absolute;left:0;top:0;transform-origin:0 0}
.fr{position:absolute;inset:26px;border:2px solid rgba(255,255,255,.22);border-radius:36px;opacity:0}
.kick{display:none;position:absolute;left:72px;top:318px;font-size:25px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:#cfcfcf;white-space:nowrap}
.kick b{color:var(--acc)}
.ttl{position:absolute;left:72px;top:318px;width:860px;z-index:3;text-shadow:0 4px 26px #000,0 0 8px rgba(0,0,0,.8);font-size:82px;line-height:1.02;font-weight:800;text-transform:uppercase;letter-spacing:-1px;hyphens:auto;-webkit-hyphens:auto;overflow-wrap:break-word}
.ttl .w{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.08em;margin-bottom:-.08em}
.ttl .w>span{display:inline-block}
.viz{position:absolute;left:72px;top:719px;width:864px;height:560px}
.lab{position:absolute;font-size:26px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#bdbdbd;line-height:1.2}
.lab.a{color:var(--acc)}
.txt{position:absolute;font-family:var(--ft);font-size:38px;line-height:1.2;color:#fff}
.big{position:absolute;font-weight:800;letter-spacing:-1px;line-height:1}
.card{position:absolute;border:1.5px solid rgba(255,255,255,.16);background:#0d0d0d;border-radius:14px}
svg{position:absolute;left:0;top:0;overflow:visible}
svg .d{fill:none;stroke-linecap:round;stroke-linejoin:round}
#cap{position:absolute;left:72px;width:864px;top:1480px;text-align:center;font-family:var(--ft);font-size:60px;font-weight:700;line-height:1.2;color:#fff;text-shadow:0 4px 24px #000;text-wrap:balance}
#cap span{color:rgba(255,255,255,.6)}#cap span.on{color:#fff}#cap span.k{color:var(--acc)}
#lg{position:absolute;left:72px;top:196px;max-width:340px;max-height:88px;display:none}
#end{position:absolute;inset:0;display:none;background:#000}
#end .gl{position:absolute;left:-110px;top:310px;width:1300px;height:1300px;border-radius:50%;background:radial-gradient(circle,var(--acc) 0%,transparent 60%)}
#end img{position:absolute;left:50%;top:50%;max-width:660px;max-height:360px}
#end .ln{position:absolute;left:50%;top:1180px;width:160px;height:6px;margin-left:-80px;background:var(--acc)}
#bar{position:absolute;left:0;top:1906px;height:14px;background:var(--acc);width:0}
#bg{position:absolute;left:0;top:0}
/* bezpečná zóna na výšku: vpravo tlačidlá, dole popis a názov kanála, hore lišta aplikácie */
.notext .ttl,.notext .kick,.notext #cap,.notext #lg,.notext #gdc,.notext #bg{visibility:hidden!important}
#stage{position:absolute;inset:0;transform-origin:72px 196px;transform:translate(8px,-56px) scale(.97)}
.viz{transform-origin:center}
body.wide,html.wide{width:1920px;height:1080px}
.wide #stage{transform:none}
.wide #glow{left:310px;top:-110px}
.wide #lg{left:150px;top:72px;max-width:280px;max-height:64px}
.wide .kick{display:block;left:150px;top:166px;font-size:22px}
.wide .ttl{left:150px;top:200px;width:1620px}
.wide .viz{left:528px;top:345px}
.wide #cap{left:260px;width:1400px;top:975px;font-size:44px}
.wide #end .gl{left:310px;top:-110px}
.wide #end .ln{top:760px}
.wide #bar{top:1068px;height:12px}
</style></head><body><canvas id="bg"></canvas><div id="glow"></div><div id="stage"><div id="root"></div><img id="lg"><div id="cap"></div></div><div id="end"><div class="gl"></div><img><div class="ln"></div></div><div id="bar"></div>
<script>/*GEOLIBS*/</script>
<script>
const D=__DATA__;
document.documentElement.style.setProperty('--acc',D.acc);document.documentElement.lang=D.lang||'en';
const cl=x=>Math.max(0,Math.min(1,x)),E=x=>1-Math.pow(1-cl(x),3),EI=x=>{x=cl(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2};
const NF=(v,dec)=>{try{return new Intl.NumberFormat(D.lang||'en',{minimumFractionDigits:dec,maximumFractionDigits:dec}).format(v)}catch(e){return v.toFixed(dec)}};
const decs=v=>{const s=String(v);return s.includes('.')?Math.min(2,s.split('.')[1].length):0};
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const N=v=>{const x=parseFloat(String(v).replace(/\s/g,'').replace(',','.'));return isNaN(x)?0:x};
function el(tag,cls,css,html){const e=document.createElement(tag);if(cls)e.className=cls;if(css)e.style.cssText=css;if(html!=null)e.innerHTML=html;return e}
function fit(e,max,min,h,w){let s=max;e.style.fontSize=s+'px';const W=w||e.clientWidth;const cw=()=>{const r=document.createRange();r.selectNodeContents(e);return r.getBoundingClientRect().width};while(s>min&&(e.scrollHeight>h+2||cw()>W+2)){s-=2;e.style.fontSize=s+'px'}return s}
const SVGNS='http://www.w3.org/2000/svg';
function svg(w,h,inner){const s=document.createElementNS(SVGNS,'svg');s.setAttribute('width',w);s.setAttribute('height',h);s.setAttribute('viewBox',`0 0 ${w} ${h}`);s.innerHTML=inner;return s}
const ICONS={/*EXTRA_ICONS*/
house:'<path d="M14 48 L50 17 L86 48"/><path d="M24 41 V85 H76 V41"/><path d="M42 85 V62 H58 V85"/>',
heatpump:'<rect x="8" y="22" width="84" height="56" rx="6"/><circle cx="36" cy="50" r="18"/><path d="M36 32 C44 42 28 58 36 68 M18 50 C28 42 44 58 54 50"/><path d="M66 36 H84 M66 44 H84 M66 52 H84 M66 60 H84"/><path d="M18 78 V86 M82 78 V86"/>',
radiator:'<rect x="14" y="24" width="12" height="54" rx="6"/><rect x="30" y="24" width="12" height="54" rx="6"/><rect x="46" y="24" width="12" height="54" rx="6"/><rect x="62" y="24" width="12" height="54" rx="6"/><path d="M8 70 H14 M74 70 H92"/>',
floor:'<path d="M10 78 H90"/><path d="M14 66 C22 58 30 74 38 66 S54 58 62 66 S78 74 86 66"/><path d="M32 48 C28 42 36 36 32 28 M50 48 C46 42 54 36 50 28 M68 48 C64 42 72 36 68 28"/>',
thermo:'<path d="M43 20 A7 7 0 0 1 57 20 V60 A15 15 0 1 1 43 60 Z"/><path d="M50 34 V70"/><path d="M62 28 H70 M62 40 H70 M62 52 H70"/>',
snow:'<path d="M50 12 V88 M17 31 L83 69 M83 31 L17 69"/><path d="M41 18 L50 26 L59 18 M41 82 L50 74 L59 82"/>',
sun:'<circle cx="50" cy="50" r="16"/><path d="M50 12 V22 M50 78 V88 M12 50 H22 M78 50 H88 M23 23 L30 30 M70 70 L77 77 M77 23 L70 30 M30 70 L23 77"/>',
flame:'<path d="M50 12 C62 30 74 42 74 60 A24 24 0 0 1 26 60 C26 48 33 40 38 33 C40 43 44 47 48 50 C47 36 47 24 50 12 Z"/>',
bolt:'<path d="M57 10 L26 56 H48 L42 90 L75 42 H53 Z"/>',
drop:'<path d="M50 12 C64 32 74 46 74 62 A24 24 0 0 1 26 62 C26 46 36 32 50 12 Z"/><path d="M38 64 A12 12 0 0 0 50 76"/>',
coin:'<circle cx="50" cy="50" r="36"/><path d="M62 36 A17 17 0 1 0 62 64 M32 46 H56 M32 55 H56"/>',
leaf:'<path d="M20 80 C20 42 44 20 84 18 C84 56 62 80 20 80 Z"/><path d="M20 80 L60 40"/>',
air:'<path d="M12 38 H58 A10 10 0 1 0 48 28"/><path d="M12 54 H72 A11 11 0 1 1 61 65"/><path d="M12 70 H40"/>',
phone:'<rect x="30" y="10" width="40" height="80" rx="8"/><path d="M45 80 H55"/><path d="M38 34 H62 M38 44 H56"/>',
tank:'<rect x="30" y="10" width="40" height="76" rx="18"/><path d="M30 38 H70"/><path d="M42 86 V92 M58 86 V92"/><path d="M50 54 V70"/>',
sound:'<path d="M16 40 H30 L48 24 V76 L30 60 H16 Z"/><path d="M60 38 C66 44 66 56 60 62 M70 28 C82 40 82 60 70 72"/>',
clock:'<circle cx="50" cy="50" r="36"/><path d="M50 28 V50 L64 60"/>',
plug:'<path d="M38 12 V30 M62 12 V30"/><path d="M28 30 H72 V44 A22 22 0 0 1 28 44 Z"/><path d="M50 66 V90"/>',
check:'<circle cx="50" cy="50" r="36"/><path d="M33 51 L45 63 L68 38"/>',
cross:'<circle cx="50" cy="50" r="36"/><path d="M36 36 L64 64 M64 36 L36 64"/>',
user:'<circle cx="50" cy="34" r="16"/><path d="M18 88 C18 64 32 56 50 56 C68 56 82 64 82 88"/>',
tool:'<path d="M64 12 A20 20 0 0 0 46 40 L14 72 A8 8 0 0 0 26 84 L58 52 A20 20 0 0 0 86 34 L74 40 L64 30 L70 18 Z"/>',
chart:'<path d="M14 14 V86 H88"/><path d="M24 70 L44 50 L58 60 L84 28"/><path d="M72 28 H84 V40"/>',
shield:'<path d="M50 10 L82 22 V46 C82 68 68 82 50 90 C32 82 18 68 18 46 V22 Z"/><path d="M36 50 L46 60 L66 38"/>',
panel:'<path d="M22 30 H78 L90 76 H10 Z"/><path d="M41 30 L36 76 M59 30 L64 76 M18 46 H82 M14 61 H86"/><path d="M50 76 V90 M36 90 H64"/>',
turbine:'<path d="M50 44 L46 92 H54 Z"/><g class="spin"><circle cx="50" cy="40" r="4"/><path d="M50 36 C54 26 54 14 50 6 C46 14 46 26 50 36 Z"/><path d="M53.5 42 C60 50 70 56 79 57 C74 49 64 43 53.5 42 Z"/><path d="M46.5 42 C36 43 26 49 21 57 C30 56 40 50 46.5 42 Z"/></g>',
battery:'<rect x="24" y="20" width="52" height="70" rx="8"/><path d="M40 20 V12 H60 V20"/><path d="M34 76 H66 M34 62 H66 M34 48 H66"/>',
car:'<path d="M12 62 V50 L24 46 L34 30 H66 L78 46 L88 50 V62 Z"/><path d="M34 46 H68"/><circle cx="30" cy="66" r="8"/><circle cx="70" cy="66" r="8"/><path d="M52 12 L46 22 H54 L48 30"/>',
pylon:'<path d="M40 90 L46 14 H54 L60 90"/><path d="M22 30 H78 M30 48 H70"/><path d="M44 30 L57 48 M56 30 L43 48 M42 66 L58 80 M58 66 L42 80"/><path d="M22 30 V36 M78 30 V36 M30 48 V54 M70 48 V54"/>',
bulb:'<path d="M36 62 C26 54 22 44 24 34 A26 26 0 0 1 76 34 C78 44 74 54 64 62 V72 H36 Z"/><path d="M40 80 H60 M44 88 H56"/><path d="M44 62 V48 L50 42 L56 48 V62"/>',
meter:'<rect x="18" y="14" width="64" height="72" rx="8"/><path d="M28 28 H72 V46 H28 Z"/><path d="M36 37 H44 M50 37 H64"/><circle cx="50" cy="66" r="10"/><path d="M50 66 L56 60"/>',
globe:'<circle cx="50" cy="50" r="36"/><path d="M14 50 H86"/><path d="M50 14 C34 26 34 74 50 86 C66 74 66 26 50 14 Z"/><path d="M22 30 C38 38 62 38 78 30 M22 70 C38 62 62 62 78 70"/>',
window:'<rect x="20" y="14" width="60" height="72" rx="3"/><path d="M50 14 V86 M20 50 H80"/><path d="M28 24 L38 34 M60 60 L70 70"/>',
factory:'<path d="M10 88 V48 L34 60 V48 L58 60 V48 L70 54 V18 H84 V88 Z"/><path d="M22 74 H30 M44 74 H52 M64 74 H72"/><path d="M72 10 C76 6 82 8 84 4"/>',
cloud:'<path d="M28 70 A16 16 0 0 1 30 38 A22 22 0 0 1 72 42 A14 14 0 0 1 72 70 Z"/><path d="M36 80 L32 90 M52 80 L48 90 M68 80 L64 90"/>',
dot:'<circle cx="50" cy="50" r="30"/><circle cx="50" cy="50" r="9"/>',
compressor:'<circle cx="50" cy="50" r="34"/><path d="M26 26 L82 40 M26 74 L82 60"/><path d="M4 50 H16 M84 50 H96"/>',
fridge:'<rect x="26" y="8" width="48" height="84" rx="6"/><path d="M26 38 H74"/><path d="M36 18 V28 M36 48 V64"/>',
fan:'<circle cx="50" cy="40" r="32"/><g class="spin"><circle cx="50" cy="40" r="4"/><path d="M50 36 C58 30 58 18 50 12 C46 20 46 30 50 36 Z"/><path d="M53.5 42 C63 44 72 52 74 58 C64 58 56 50 53.5 42 Z"/><path d="M46.5 42 C44 50 36 58 26 58 C28 50 37 44 46.5 42 Z"/></g><path d="M38 70 L32 90 H68 L62 70"/>',
boiler:'<rect x="24" y="8" width="52" height="70" rx="6"/><path d="M50 60 C40 52 44 42 50 34 C56 42 60 52 50 60 Z"/><path d="M34 20 H66"/><path d="M36 78 V92 M64 78 V92"/>',
city:'<path d="M8 88 H92"/><rect x="14" y="40" width="20" height="48"/><rect x="40" y="18" width="22" height="70"/><rect x="68" y="50" width="18" height="38"/><path d="M20 50 H28 M20 62 H28 M46 30 H56 M46 44 H56 M46 58 H56 M73 60 H81 M73 72 H81"/>'};
const WSPIN=new Set('gear wheel tyre saw_blade flywheel impeller propeller ship_propeller sprocket ball_bearing roller_bearing brake_disc vinyl film_reel roulette ship_wheel'.split(' '));const canSpin=n=>WSPIN.has(IR(String(n||'')));
function IR(name){const ok=n=>ICONS[n]?n:(ICON_ALIAS[n]&&ICONS[ICON_ALIAS[n]]?ICON_ALIAS[n]:null);const one=n=>ok(n)||ok(n.replace(/ies$/,'y'))||ok(n.replace(/es$/,''))||ok(n.replace(/s$/,''));
let n=String(name||'').toLowerCase().trim().replace(/[\s-]+/g,'_');let r=one(n);if(r)return r;const p=n.split('_').filter(Boolean);for(let i=p.length-1;i>=0;i--){r=one(p[i]);if(r)return r}return 'check'}
function icon(name,size,col,sw){const s=svg(size,size,'');s.setAttribute('viewBox','0 0 100 100');s.innerHTML=(ICONS[IR(name)]||ICONS.check).replace(/<(path|rect|circle)/g,'<$1 class="d" pathLength="1"');s.style.color=col||'#fff';s.querySelectorAll('.d').forEach(p=>{p.setAttribute('stroke','currentColor');p.setAttribute('stroke-width',sw||3.2)});s.querySelectorAll('.spin').forEach(g=>SPIN.push(g));return s}
const SPIN=[];
function draw(s,p){s.querySelectorAll('.d').forEach(d=>{d.style.strokeDasharray='1 1';d.style.strokeDashoffset=1-cl(p)})}
function show(e,p,dy){e.style.opacity=cl(p);e.style.transform=`translateY(${(1-E(p))*(dy==null?24:dy)}px)`}
// ---------- diagramy ----------
const V={};
V.flow=(v,d)=>{const X=432;const s=svg(864,560,`
<path class="d in" pathLength="1" d="M${X} 92 V184" stroke="#fff" stroke-width="3"/><path class="d ina" d="M${X-14} 168 L${X} 186 L${X+14} 168" stroke="#fff" stroke-width="3"/>
<rect class="d box" pathLength="1" x="${X-230}" y="196" width="460" height="128" rx="14" stroke="#fff" stroke-width="3"/>
<path class="d ex" pathLength="1" d="M846 260 H${X+246}" stroke="#a9a9a9" stroke-width="3"/><path class="d exa" d="M${X+262} 246 L${X+244} 260 L${X+262} 274" stroke="#a9a9a9" stroke-width="3"/>
<path class="d out" pathLength="1" d="M${X} 336 V452" stroke="var(--acc)" stroke-width="12"/><path class="d outa" d="M${X-34} 420 L${X} 460 L${X+34} 420" stroke="var(--acc)" stroke-width="12"/>`);v.append(s);
const a=el('div','txt',`left:132px;top:20px;width:600px;text-align:center;font-weight:700`,esc(d.a)),b=el('div','big',`left:${X-220}px;top:206px;width:440px;height:108px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:44px;text-transform:uppercase`,esc(d.b)),
c=el('div','big',`left:32px;top:478px;width:800px;text-align:center;color:var(--acc);font-size:64px`,esc(d.c)),x=el('div','lab',`left:${X+250}px;top:150px;width:200px;color:#a9a9a9;text-align:center`,esc(d.x||''));
v.append(a,b,c,x);fit(a,40,26,96,600);fit(b,46,26,108,430);fit(c,66,34,80,800);fit(x,26,18,96,200);
const ins=s.querySelector('.in'),ina=s.querySelector('.ina'),box=s.querySelector('.box'),ex=s.querySelector('.ex'),exa=s.querySelector('.exa'),out=s.querySelector('.out'),outa=s.querySelector('.outa');
[ina,exa,outa].forEach(p=>p.setAttribute('pathLength','1'));if(!d.x){ex.remove();exa.remove()}
return (t,st)=>{show(a,st(0,.5));ins.style.strokeDasharray='1 1';ins.style.strokeDashoffset=1-st(.25,.6);ina.style.strokeDasharray='1 1';ina.style.strokeDashoffset=1-st(.7,.3);
box.style.strokeDasharray='1 1';box.style.strokeDashoffset=1-st(1,.8);show(b,st(1.4,.5));
if(d.x){ex.style.strokeDasharray='1 1';ex.style.strokeDashoffset=1-st(2,.6);exa.style.strokeDasharray='1 1';exa.style.strokeDashoffset=1-st(2.5,.3);show(x,st(2,.5),0)}
const o=st(d.x?3:2,.6);out.style.strokeDasharray='1 1';out.style.strokeDashoffset=1-o;outa.style.strokeDasharray='1 1';outa.style.strokeDashoffset=1-st(d.x?3.4:2.4,.3);show(c,st(d.x?3.4:2.4,.6))}};
V.cycle=(v,d)=>{const L=d.l||[];const P='M210 300 V170 Q210 110 270 110 H594 Q654 110 654 170 V430 Q654 490 594 490 H270 Q210 490 210 430 Z';
const s=svg(864,560,`<path class="d loopc" pathLength="1" d="M210 300 V170 Q210 110 270 110 H432" stroke="#a9a9a9" stroke-width="5"/>
<path class="d looph" pathLength="1" d="M432 110 H594 Q654 110 654 170 V430 Q654 490 594 490 H432" stroke="var(--acc)" stroke-width="5"/>
<path class="d loopc2" pathLength="1" d="M432 490 H270 Q210 490 210 430 V300" stroke="#a9a9a9" stroke-width="5"/>
<g class="n1"><rect x="180" y="240" width="60" height="120" rx="8" fill="#000" stroke="#a9a9a9" stroke-width="4"/><path d="M190 256 H230 M190 276 H230 M190 296 H230 M190 316 H230 M190 336 H230" stroke="#a9a9a9" stroke-width="3"/></g>
<g class="n2"><circle cx="432" cy="110" r="40" fill="#000" stroke="#fff" stroke-width="4"/><path d="M404 82 L470 98 M404 138 L470 122" stroke="#fff" stroke-width="4" fill="none"/></g>
<g class="n3"><rect x="624" y="240" width="60" height="120" rx="8" fill="#000" stroke="var(--acc)" stroke-width="4"/><path d="M634 256 H674 M634 276 H674 M634 296 H674 M634 316 H674 M634 336 H674" stroke="var(--acc)" stroke-width="3"/></g>
<g class="n4"><path d="M402 470 L462 510 V470 L402 510 Z" fill="#000" stroke="#fff" stroke-width="4"/></g>
<g class="air"><path d="M10 250 H150 M10 300 H170 M10 350 H150" stroke="#a9a9a9" stroke-width="3" stroke-dasharray="14 12" class="aird"/><path d="M156 286 L172 300 L156 314" stroke="#a9a9a9" stroke-width="3" fill="none"/></g>
<g class="heat"><path d="M694 300 H760" stroke="var(--acc)" stroke-width="6" stroke-dasharray="16 10" class="heatd"/></g>
<g class="dots"></g>`);v.append(s);
const hi=icon('house',96,'#fff',3.6);hi.style.left='768px';hi.style.top='252px';v.append(hi);
const path=document.createElementNS(SVGNS,'path');path.setAttribute('d',P);const len=path.getTotalLength?null:null;s.append(path);path.style.display='none';
const lab=(i,css,a)=>{const e=el('div','lab'+(a?' a':''),css,esc(L[i]||''));v.append(e);fit(e,24,14,96);return e};
const l0=lab(0,'left:0;top:180px;width:190px;color:#a9a9a9'),l1=lab(1,'left:252px;top:250px;width:170px;color:#a9a9a9'),l2=lab(2,'left:300px;top:20px;width:264px;text-align:center'),l3=lab(3,'left:442px;top:250px;width:170px;text-align:right',1),l4=lab(4,'left:720px;top:360px;width:144px;text-align:center',1);
const g=k=>s.querySelector(k);const dots=g('.dots');const NDOT=14;for(let i=0;i<NDOT;i++){const c=document.createElementNS(SVGNS,'circle');c.setAttribute('r',7);dots.append(c)}
const tot=path.getTotalLength();
return (t,st)=>{const a=st(0,1.2);['.loopc','.looph','.loopc2'].forEach((k,i)=>{const p=g(k);p.style.strokeDasharray='1 1';p.style.strokeDashoffset=1-cl(a*3-i)});
g('.air').style.opacity=st(.6,.5);g('.aird').style.strokeDashoffset=-t*60;show(l0,st(.6,.5),0);
g('.n1').style.opacity=st(1.2,.4);show(l1,st(1.2,.5),0);g('.n2').style.opacity=st(2,.4);show(l2,st(2,.5),0);
g('.n3').style.opacity=st(2.8,.4);show(l3,st(2.8,.5),0);g('.n4').style.opacity=st(2.8,.4);
g('.heat').style.opacity=st(3.4,.5);g('.heatd').style.strokeDashoffset=-t*70;hi.style.opacity=st(3.4,.5);draw(hi,st(3.4,1));show(l4,st(3.6,.5),0);
const on=st(1.2,.6);[...dots.children].forEach((c,i)=>{const u=((i/NDOT)+t*0.09)%1;const pt=path.getPointAtLength(u*tot);c.setAttribute('cx',pt.x);c.setAttribute('cy',pt.y);
const hot=pt.y<112&&pt.x>432||pt.x>640||pt.y>480&&pt.x>432;c.setAttribute('fill',hot?D.acc:'#a9a9a9');c.style.opacity=on})}};
V.bars=(v,d)=>{const I=(d.i||[]).slice(0,4);const n=I.length||1,max=Math.max(...I.map(x=>N(x[1])),1),bw=Math.min(170,680/n),gap=(864-bw*n)/(n+1);
const base=440,mh=360;const s=svg(864,560,`<path class="d ax" pathLength="1" d="M0 ${base} H864" stroke="#fff" stroke-width="3"/>`);v.append(s);
const it=I.map((x,i)=>{const L=gap+i*(bw+gap),last=i==n-1;const r=el('div','',`position:absolute;left:${L}px;width:${bw}px;bottom:${560-base}px;height:0;background:${last?'var(--acc)':i%2?'#e9e9e9':'#3b3b3b'}`);
const vw=Math.min(bw+80,bw+gap-10),lw=Math.min(bw+60,bw+gap-12);const val=el('div','big',`left:${L+bw/2-vw/2}px;width:${vw}px;text-align:center;white-space:nowrap;font-size:40px;${last?'color:var(--acc)':''}`,esc(NF(N(x[1]),decs(x[1]))+(d.u?' '+d.u:'')));const lb=el('div','lab',`left:${L+bw/2-lw/2}px;width:${lw}px;top:${base+18}px;text-align:center`,esc(x[0]));
const fu=d.fl&&d.fl[i];if(fu){const f=el('img','',`position:absolute;left:${L+bw/2-33}px;top:${base+16}px;width:66px;height:49px;border-radius:4px;object-fit:cover;box-shadow:0 2px 10px rgba(0,0,0,.6)`);f.src=fu;v.append(f);lb.style.top=(base+76)+'px'}
v.append(r,val,lb);fit(lb,28,13,fu?44:70);fit(val,40,18,60);return {r,val,lb,v:N(x[1]),h:N(x[1])/max*mh,dec:decs(x[1])}});
return (t,st)=>{const ax=s.querySelector('.ax');ax.style.strokeDasharray='1 1';ax.style.strokeDashoffset=1-st(0,.6);
it.forEach((o,i)=>{const p=st(.4+i*.9,.9);o.r.style.height=(E(p)*o.h)+'px';o.val.style.top=(base-E(p)*o.h-52)+'px';o.val.textContent=NF(o.v*E(p),o.dec)+(d.u?' '+d.u:'');o.val.style.opacity=cl(p*3);show(o.lb,st(.4+i*.9,.5),0)})}};
V.calc=(v,d)=>{const R=(d.r||[]).slice(0,4);const rh=Math.min(130,540/Math.max(1,R.length));
const rows=R.map((r,i)=>{const y=i*rh;const ln=el('div','',`position:absolute;left:0;top:${y+rh-8}px;height:2px;width:864px;background:rgba(255,255,255,.14);transform-origin:left`);
const a=el('div','lab',`left:0;top:${y+6}px;width:864px`,''),ex=el('div','txt',`left:0;top:${y+38}px;width:520px;color:#d0d0d0`,esc(r[0])),res=el('div','big',`right:0;top:${y+30}px;width:400px;text-align:right;font-size:50px;color:${i==R.length-1?'var(--acc)':'#fff'}`);
v.append(ln,a,ex,res);fit(ex,36,20,rh-46,520);const num=N(String(r[1]||'').match(/-?[\d\s.,]+/)?.[0]||'');return {ln,a,ex,res,txt:String(r[1]||''),num}});
return (t,st)=>{rows.forEach((o,i)=>{const p=st(i*1.1,.6);show(o.ex,p,16);o.a.style.opacity=p;o.ln.style.transform=`scaleX(${E(p)})`;const q=st(i*1.1+.5,.7);o.res.style.opacity=cl(q*2);
o.res.textContent=q<1&&/\d/.test(o.txt)?o.txt.replace(/-?\d[\d\s.,]*\d|\d/,m=>{const v=N(m.replace(/\s/g,''));return Math.abs(v)>=1000||q<1?NF(Math.round(v*E(q)),0):m}):o.txt;fit(o.res,52,28,64,400)})}};
V.compare=(v,d)=>{const A=d.a||['',''],B=d.b||['',''];const mk=(y,o,good)=>{const c=el('div','card',`left:0;top:${y}px;width:864px;height:236px;${good?'border-color:var(--acc)':''}`);
const ic=icon(good?'check':'cross',84,good?D.acc:'#777',5);ic.style.left='38px';ic.style.top='76px';const l=el('div','txt',`left:152px;top:44px;width:670px;font-weight:600;color:${good?'#fff':'#aaa'}`,esc(o[0]));
const val=el('div','big',`left:152px;top:116px;width:670px;font-size:84px;${good?'color:var(--acc)':'color:#888;text-decoration:line-through;text-decoration-thickness:4px'}`,esc(o[1]));c.append(ic,l,val);v.append(c);fit(l,38,22,60,670);fit(val,84,34,96,670);return {c,ic}};
const a=mk(10,A,0),b=mk(300,B,1);return (t,st)=>{show(a.c,st(0,.6),40);draw(a.ic,st(.3,.7));show(b.c,st(1.3,.6),40);draw(b.ic,st(1.6,.7));b.c.style.transform+=` scale(${1+.03*Math.sin(cl(st(2.2,.5))*Math.PI)})`}};
V.count=(v,d)=>{const val=N(d.v);const pct=/%/.test(d.suf||'');const s=svg(864,560,`<circle cx="432" cy="250" r="220" stroke="rgba(255,255,255,.12)" stroke-width="10" fill="none"/><circle class="d ring" pathLength="1" cx="432" cy="250" r="220" stroke="var(--acc)" stroke-width="10" transform="rotate(-90 432 250)"/>`);v.append(s);
const n=el('div','big',`left:0;top:165px;width:864px;height:170px;display:flex;align-items:center;justify-content:center;white-space:pre;font-size:150px`),l=el('div','lab',`left:182px;top:500px;width:500px;text-align:center;font-size:28px`,esc(d.l||''));v.append(n,l);fit(l,28,18,60);
const dec=decs(d.v);return (t,st)=>{const p=st(0,1.6);const r=s.querySelector('.ring');r.style.strokeDasharray='1 1';r.style.strokeDashoffset=1-(pct?Math.min(1,Math.abs(val)/100):1)*E(p);
n.innerHTML=esc(d.pre||'')+'<span style="color:var(--acc)">'+NF(val*E(p),dec)+'</span>'+esc(d.suf||'');fit(n,150,50,999,400);show(l,st(1,.6))}};
V.list=(v,d)=>{const I=(d.i||[]).slice(0,4);const rh=Math.min(130,540/Math.max(1,I.length));const rows=I.map((x,i)=>{const r=el('div','',`position:absolute;left:0;top:${i*rh}px;width:864px;height:${rh-16}px;display:flex;align-items:center;gap:28px`);
r.innerHTML=`<div style="flex:none;color:var(--acc);font-weight:800;font-size:54px;width:52px">${i+1}</div><div class="it" style="flex:none;width:780px;font-weight:800;text-transform:uppercase;font-size:44px;line-height:1.08">${esc(x)}</div>`;v.append(r);fit(r.querySelector('.it'),44,24,rh-16,780);return r});
return (t,st)=>rows.forEach((r,i)=>{const p=st(i*1,.6);r.style.opacity=p;r.style.transform=`translateX(${(1-E(p))*-50}px)`})};
V.icons=(v,d)=>{const I=(d.i||[]).slice(0,4);const n=I.length||1;const sz=n>3?150:190,step=864/n;const s=svg(864,560,'');v.append(s);
const items=I.map((x,i)=>{const cx=step*i+step/2;const ic=icon(x[0],sz,i==n-1?D.acc:'#fff',3);ic.style.left=(cx-sz/2)+'px';ic.style.top=(240-sz/2)+'px';v.append(ic);
const lb=el('div','lab',`left:${cx-step/2+6}px;width:${step-12}px;top:${250+sz/2+24}px;text-align:center;${i==n-1?'color:var(--acc)':''}`,esc(x[1]||''));v.append(lb);fit(lb,26,14,92,step-44);
let ar=null;if(i<n-1){ar=document.createElementNS(SVGNS,'path');ar.setAttribute('d',`M${cx+sz/2+10} 240 H${cx+step-sz/2-10}`);ar.setAttribute('stroke','#777');ar.setAttribute('stroke-width','3');ar.setAttribute('stroke-dasharray','10 9');s.append(ar)}return {ic,lb,ar}});
return (t,st)=>items.forEach((o,i)=>{const p=st(i*1.1,1);draw(o.ic,p);o.ic.style.opacity=p>0?1:0;show(o.lb,st(i*1.1+.4,.5),0);if(o.ar){o.ar.style.opacity=st(i*1.1+.8,.4);o.ar.style.strokeDashoffset=-t*40}})};
V.temp=(v,d)=>{const A=d.a||['',0],B=d.b||['',0],u=d.u||'°C';const va=N(A[1]),vb=N(B[1]);const lo=Math.min(va,vb,0)-5,hi=Math.max(va,vb)+5;const Y=v=>440-(v-lo)/(hi-lo)*380;
const th=(x,col)=>`<path d="M${x-22} 60 A22 22 0 0 1 ${x+22} 60 V430 A38 38 0 1 1 ${x-22} 430 Z" stroke="#fff" stroke-width="3" fill="none"/><circle cx="${x}" cy="462" r="26" fill="${col}"/>`;
const s=svg(864,560,th(220,'#a9a9a9')+th(644,'var(--acc)')+`<rect class="fa" x="208" width="24" fill="#a9a9a9"/><rect class="fb" x="632" width="24" fill="var(--acc)"/><path class="dt" d="" stroke="#fff" stroke-width="3" stroke-dasharray="8 8" fill="none"/>`);v.append(s);
const la=el('div','lab',`left:20px;top:0;width:180px;text-align:right`,esc(A[0])),lb=el('div','lab a',`left:684px;top:0;width:180px`,esc(B[0])),na=el('div','big',`left:0;top:${Y(va)-30}px;width:176px;text-align:right;font-size:48px;color:#a9a9a9`),nb=el('div','big',`left:684px;top:${Y(vb)-30}px;width:180px;font-size:48px;color:var(--acc)`),
dl=el('div','big',`left:270px;top:${(Y(va)+Y(vb))/2-34}px;width:324px;text-align:center;font-size:56px`);v.append(la,lb,na,nb,dl);fit(la,24,16,60);fit(lb,24,16,60);na.style.top=Math.max(Y(va)-30,la.offsetHeight+6)+'px';nb.style.top=Math.max(Y(vb)-30,lb.offsetHeight+6)+'px';   // číslo nikdy neleží cez názov nad ním

return (t,st)=>{const p=E(st(.2,1.2)),q=E(st(1,1.2));const ya=440+(Y(va)-440)*p,yb=440+(Y(vb)-440)*q;const fa=s.querySelector('.fa'),fb=s.querySelector('.fb');
fa.setAttribute('y',ya);fa.setAttribute('height',Math.max(0,462-ya));fb.setAttribute('y',yb);fb.setAttribute('height',Math.max(0,462-yb));
show(la,st(0,.5),0);show(lb,st(.8,.5),0);na.textContent=NF(va*p,0)+' '+u;nb.textContent=NF(vb*q,0)+' '+u;na.style.opacity=st(.2,.3);nb.style.opacity=st(1,.3);
const r=st(2.4,.6);const dt=s.querySelector('.dt');dt.setAttribute('d',`M250 ${Y(va)} H${250+(614-250)*r} M250 ${Y(vb)} H${250+(614-250)*r}`);dl.textContent='Δ '+NF(Math.abs(vb-va),0)+(u=='°C'?' K':' '+u);show(dl,st(2.8,.5))}};
V.house=(v,d)=>{const I=(d.i||[]).slice(0,4);const hi=icon('house',380,'#fff',1.6);hi.style.left='252px';hi.style.top='96px';v.append(hi);
const pos=[[0,0,'M442 150 V62',[462,0,300,'left']],[0,0,'M310 330 H180',[0,276,170,'right']],[0,0,'M574 330 H694',[704,276,160,'left']],[0,0,'M442 470 V548',[462,476,300,'left']]];
const s=svg(864,560,'');v.append(s);const items=I.map((x,i)=>{const P=pos[i];const a=document.createElementNS(SVGNS,'path');a.setAttribute('d',P[2]);a.setAttribute('stroke',D.acc);a.setAttribute('stroke-width','8');a.setAttribute('stroke-dasharray','14 10');a.setAttribute('fill','none');s.append(a);
const L=P[3];const lb=el('div','',`position:absolute;left:${L[0]}px;top:${L[1]}px;width:${L[2]}px;text-align:${L[3]}`,`<div class="lab a" style="position:static">${esc(x[0])}</div><div class="big" style="position:static;font-size:46px">${x[1]!==''&&x[1]!=null?esc(x[1])+(typeof x[1]=='number'||/^\d+$/.test(x[1])?' %':''):''}</div>`);v.append(lb);return {a,lb}});
return (t,st)=>{draw(hi,st(0,1.2));items.forEach((o,i)=>{const p=st(1+i*.8,.5);o.a.style.opacity=p;o.a.style.strokeDashoffset=t*40;show(o.lb,p,0)})}};
V.split=(v,d)=>{const I=(d.i||[]).slice(0,3);const tot=I.reduce((s,x)=>s+N(x[1]),0)||1;const cols=['var(--acc)','#e9e9e9','#555'];let x0=0;
const segs=I.map((x,i)=>{const w=N(x[1])/tot*864;const r=el('div','',`position:absolute;left:${x0}px;top:170px;height:120px;width:0;background:${cols[i]}`);
const n=el('div','big',`left:${x0}px;top:${i%2?330:40}px;width:${Math.max(w,300)}px;font-size:72px;color:${i==0?'var(--acc)':'#fff'}`);const lb=el('div','lab',`left:${x0}px;top:${i%2?412:122}px;width:${Math.max(w,300)}px`,esc(x[0]));v.append(r,n,lb);fit(lb,24,16,40);
const o={r,n,lb,w,v:N(x[1])};x0+=w;return o});return (t,st)=>segs.forEach((o,i)=>{const p=st(i*1.1,.9);o.r.style.width=(E(p)*o.w)+'px';o.n.textContent=NF(o.v*E(p),decs(o.v))+(d.u?' '+d.u:'');show(o.n,p,0);show(o.lb,p,0)})};
V.hero=(v,d)=>{const has=!!(d.w||d.s);const sz=has?330:400,cx=432,cy=has?200:270;
const rings=[0,1,2].map(i=>{const r=el('div','',`position:absolute;left:${cx-sz*.5}px;top:${cy-sz*.5}px;width:${sz}px;height:${sz}px;border-radius:50%;border:2px solid var(--acc);opacity:0`);v.append(r);return r});
const halo=el('div','',`position:absolute;left:${cx-sz*.95}px;top:${cy-sz*.95}px;width:${sz*1.9}px;height:${sz*1.9}px;border-radius:50%;background:radial-gradient(circle,var(--acc) 0%,transparent 62%);opacity:0`);v.append(halo);
const ic=icon(d.i||'bolt',sz,'#fff',2.2);ic.style.left=(cx-sz/2)+'px';ic.style.top=(cy-sz/2)+'px';v.append(ic);
const w=el('div','big',`left:0;top:${cy+sz/2+26}px;width:864px;text-align:center;font-size:70px;text-transform:uppercase`,esc(d.w||'')),s2=el('div','lab a',`left:82px;top:${cy+sz/2+112}px;width:700px;text-align:center;font-size:30px`,esc(d.s||''));v.append(w,s2);fit(w,70,34,84,840);fit(s2,30,18,70,700);
return (t,st)=>{const p=st(0,1.4);draw(ic,p);ic.style.opacity=p>0?1:0;ic.style.transform=`translateY(${Math.sin(t*1.1)*8}px) scale(${.9+.1*E(p)})`;halo.style.opacity=.22*E(st(.3,1.2))*(1+.12*Math.sin(t*1.6));
rings.forEach((r,i)=>{const q=((t*.32+i/3)%1);const on=cl(st(.8,.6));r.style.transform=`scale(${.72+q*.56})`;r.style.opacity=on*(1-q)*.55});show(w,st(1,.6),30);show(s2,st(1.5,.6),20)}};
// zložená scéna: hotové obrázky + šípky s pohybom, rozloženie robí appka (AI nedáva súradnice)
V.scene=(v,d)=>{const NN=(Array.isArray(d.n)?d.n:[]).filter(x=>Array.isArray(x)).slice(0,6),n=NN.length;if(!n)return;
const LL=(Array.isArray(d.l)?d.l:[]).filter(x=>Array.isArray(x)&&x[0]!=x[1]&&NN[x[0]]&&NN[x[1]]).slice(0,8);
const lay=NN.map(()=>0);if(LL.length){for(let k=0;k<n;k++)LL.forEach(e=>{if(lay[e[1]]<lay[e[0]]+1&&lay[e[0]]+1<n)lay[e[1]]=lay[e[0]]+1})}else NN.forEach((x,i)=>lay[i]=i);
const used=[...new Set(lay)].sort((a,b)=>a-b);lay.forEach((x,i)=>lay[i]=used.indexOf(x));const C=used.length,cols=Array.from({length:C},()=>[]);lay.forEach((c,i)=>cols[c].push(i));
const R=Math.max(...cols.map(c=>c.length)),cw=864/C,rh=Math.min(250,500/R),sz=Math.round(Math.max(84,Math.min(180,cw*.5,rh*.58)));
const pos=NN.map(()=>[0,0]);cols.forEach((c,ci)=>c.forEach((i,ri)=>{pos[i]=[cw*ci+cw/2,250+(ri-(c.length-1)/2)*rh-18]}));
const s=svg(864,560,'');s.style.position='absolute';s.style.left='0';s.style.top='0';v.append(s);
const nodes=NN.map((x,i)=>{const hot=LL.some(e=>e[1]==i&&e[3])&&!LL.some(e=>e[0]==i);const ic=icon(x[0],sz,hot?D.acc:'#fff',2.8);ic.style.left=(pos[i][0]-sz/2)+'px';ic.style.top=(pos[i][1]-sz/2)+'px';v.append(ic);
const lb=el('div','lab',`left:${pos[i][0]-cw/2+8}px;width:${cw-16}px;top:${pos[i][1]+sz/2+10}px;text-align:center;font-size:22px;letter-spacing:2px;${hot?'color:var(--acc)':''}`,esc(x[1]||''));v.append(lb);fit(lb,22,13,58,cw-40);
return {ic,lb,n:x[0],a:String(x[2]||''),at:lay[i],ph:i*1.7}});
const mk=(tag,at)=>{const e=document.createElementNS(SVGNS,tag);for(const k in at)e.setAttribute(k,at[k]);return e};
const links=LL.map((e,k)=>{const a=pos[e[0]],b=pos[e[1]],col=e[3]?D.acc:'#9a9a9a',g=sz/2+16;let dstr;
if(lay[e[1]]>lay[e[0]]){const x1=a[0]+g,x2=b[0]-g;dstr=a[1]==b[1]?`M${x1} ${a[1]} H${x2}`:`M${x1} ${a[1]} C${(x1+x2)/2} ${a[1]} ${(x1+x2)/2} ${b[1]} ${x2} ${b[1]}`}
else{const yb=Math.max(a[1],b[1])+sz/2+92;dstr=`M${a[0]} ${a[1]+sz/2+70} V${yb-20} Q${a[0]} ${yb} ${a[0]-20} ${yb} H${b[0]+20} Q${b[0]} ${yb} ${b[0]} ${yb-20} V${b[1]+sz/2+70}`}
const pa=mk('path',{d:dstr,stroke:col,'stroke-width':3.2,class:'d',pathLength:1});s.append(pa);const L=pa.getTotalLength(),q=pa.getPointAtLength(L),q0=pa.getPointAtLength(Math.max(0,L-6)),an=Math.atan2(q.y-q0.y,q.x-q0.x),H=15;
const hd=mk('path',{d:`M${q.x-H*Math.cos(an-.5)} ${q.y-H*Math.sin(an-.5)} L${q.x} ${q.y} L${q.x-H*Math.cos(an+.5)} ${q.y-H*Math.sin(an+.5)}`,stroke:col,'stroke-width':3.2,fill:'none','stroke-linecap':'round','stroke-linejoin':'round',opacity:0});s.append(hd);
const dots=[0,1].map(()=>{const c=mk('circle',{r:5.5,fill:e[3]?D.acc:'#fff',opacity:0});s.append(c);return c});
const flat=a[1]==b[1]||lay[e[1]]<=lay[e[0]],skip=lay[e[1]]-lay[e[0]]>1;const m=pa.getPointAtLength(L*(flat&&skip?.2:.5));const lb=el('div','lab',flat?`left:${m.x-120}px;width:240px;top:${m.y-(skip?-12:44)}px;text-align:center;`:`left:${m.x+16}px;width:200px;top:${m.y-13}px;text-align:left;`);lb.style.cssText+=`font-size:20px;letter-spacing:1.5px;color:${e[3]?'var(--acc)':'#d0d0d0'};text-shadow:0 0 10px #000,0 0 10px #000`;lb.innerHTML=esc(e[2]||'');v.append(lb);fit(lb,20,13,30,flat?Math.max(90,(skip?.4:1)*(Math.abs(b[0]-a[0])-sz-20)):Math.max(70,(b[0]-a[0])/2-sz/2));
return {pa,hd,dots,lb,L,at:Math.max(lay[e[0]],lay[e[1]]-1)+.6}});
return (t,st)=>{nodes.forEach(o=>{const p=st(o.at*1.2,.9);draw(o.ic,p);o.ic.style.opacity=p>0?1:0;let tr=`scale(${.9+.1*E(p)})`;if(/shake/.test(o.a))tr+=` translate(${Math.sin(t*31+o.ph)*4}px,${Math.cos(t*27+o.ph)*2}px)`;if(/float/.test(o.a))tr+=` translateY(${Math.sin(t*1.4+o.ph)*7}px)`;if(/pulse/.test(o.a))tr+=` scale(${1+.06*Math.sin(t*3.2+o.ph)})`;if(/spin/.test(o.a)&&canSpin(o.n))tr+=` rotate(${(t*80)%360}deg)`;o.ic.style.transform=tr;show(o.lb,st(o.at*1.2+.4,.5),0)});
links.forEach((o,k)=>{const p=st(o.at*1.2,.8);o.pa.style.strokeDasharray='1 1';o.pa.style.strokeDashoffset=1-cl(p);o.hd.setAttribute('opacity',p>=1?1:0);show(o.lb,st(o.at*1.2+.5,.5),0);
o.dots.forEach((c,i)=>{const q=((t*.5+i/2+k*.17)%1);if(p<1){c.setAttribute('opacity',0);return}const pt=o.pa.getPointAtLength(q*o.L);c.setAttribute('cx',pt.x);c.setAttribute('cy',pt.y);c.setAttribute('opacity',Math.sin(q*Math.PI))})})}};
// vlastná kresba: AI opíše jednoduché tvary, appka ich nakreslí a rozhýbe (ukázať, nie len povedať)
V.draw=(v,d)=>{const s=svg(864,560,'');s.setAttribute('viewBox','0 0 432 280');s.style.position='absolute';s.style.left='0';s.style.top='0';s.style.overflow='visible';v.append(s);
const COL=c=>c==1?D.acc:c==2?'#8f8f8f':'#fff',n=x=>{const y=parseFloat(x);return isFinite(y)?y:0},okd=x=>/^[MmLlHhVvCcSsQqTtAaZz0-9\s,.\-eE]+$/.test(String(x||''))?String(x):'';
const mk=(tag,at)=>{const e=document.createElementNS(SVGNS,tag);for(const k in at)e.setAttribute(k,at[k]);return e};
const els=(Array.isArray(d.e)?d.e:[]).slice(0,14).map(o=>{if(!o||typeof o!='object')return null;const p=(Array.isArray(o.p)?o.p:[]).map(n),col=COL(o.c),g=mk('g',{}),A=String(o.a||''),st={stroke:col,'stroke-width':2.4,class:'d',pathLength:1};
let cx=0,cy=0,ly=0,rot=null,flow=null;
if(o.s=='turbine'){const x=p[0]||216,y=p[1]||240,h=Math.max(60,p[2]||150),nb=Math.max(1,Math.min(6,Math.round(n(o.n))||3)),R=h*.42,hy=y-h;cx=x;cy=y-h/2;ly=y+16;
g.append(mk('path',Object.assign({d:`M${x-4} ${y} L${x-1.6} ${hy} H${x+1.6} L${x+4} ${y} Z`},st)));rot=mk('g',{});for(let i=0;i<nb;i++){const a=i*360/nb;rot.append(mk('path',Object.assign({d:`M${x} ${hy} C${x+R*.11} ${hy-R*.3} ${x+R*.1} ${hy-R*.7} ${x} ${hy-R} C${x-R*.06} ${hy-R*.7} ${x-R*.05} ${hy-R*.3} ${x} ${hy} Z`,transform:`rotate(${a} ${x} ${hy})`},st)))}
rot.append(mk('circle',Object.assign({cx:x,cy:hy,r:3.2},st)));g.append(rot);rot._c=[x,hy];rot._v=nb==2?150:nb>3?70:95}
else if(o.s=='path'){const e=mk('path',Object.assign({d:okd(o.d)||'M0 0'},st));g.append(e);flow=e}
else if(o.s=='line'||o.s=='arrow'){const e=mk('path',Object.assign({d:`M${p[0]} ${p[1]} L${p[2]} ${p[3]}`},st));g.append(e);flow=e;cx=(p[0]+p[2])/2;cy=(p[1]+p[3])/2;ly=Math.max(p[1],p[3])+16;
if(o.s=='arrow'){const a=Math.atan2(p[3]-p[1],p[2]-p[0]),L=9;g.append(mk('path',Object.assign({d:`M${p[2]-L*Math.cos(a-.5)} ${p[3]-L*Math.sin(a-.5)} L${p[2]} ${p[3]} L${p[2]-L*Math.cos(a+.5)} ${p[3]-L*Math.sin(a+.5)}`},st)))}}
else if(o.s=='circle'){g.append(mk('circle',Object.assign({cx:p[0],cy:p[1],r:Math.max(1,p[2]||10)},st)));cx=p[0];cy=p[1];ly=p[1]+(p[2]||10)+16}
else if(o.s=='rect'){g.append(mk('rect',Object.assign({x:p[0],y:p[1],width:Math.max(1,p[2]),height:Math.max(1,p[3]),rx:4},st)));cx=p[0]+p[2]/2;cy=p[1]+p[3]/2;ly=p[1]+p[3]+16}
else if(o.s=='text'){const e=mk('text',{x:p[0],y:p[1],fill:col,'font-size':Math.max(9,Math.min(26,n(o.z)||15)),'font-weight':800,'text-anchor':'middle','letter-spacing':.6,stroke:'#000','stroke-width':3,'paint-order':'stroke'});e.textContent=String(o.t||'').toUpperCase();g.append(e);cx=p[0];cy=p[1]}
else if(o.s=='icon'){const z=Math.max(20,p[2]||60),ic=icon(o.i,z,col,3);ic.setAttribute('x',p[0]-z/2);ic.setAttribute('y',p[1]-z/2);g.append(ic);cx=p[0];cy=p[1];ly=p[1]+z/2+16}
else return null;
if(o.s=='path'&&flow){try{const b=flow.getBBox();cx=b.x+b.width/2;cy=b.y+b.height/2;ly=b.y+b.height+16}catch(e){}}
let lb=null;if(o.l&&o.s!='text'){lb=mk('text',{x:cx,y:Math.min(274,ly),fill:o.c==1?D.acc:'#bdbdbd','font-size':Math.max(7.5,Math.min(12,150/Math.max(1,String(o.l).length))),'font-weight':700,'text-anchor':'middle','letter-spacing':.8});lb.textContent=String(o.l).toUpperCase();s.append(lb)}
s.append(g);const dots=/flow/.test(A)&&flow?[0,1,2].map(()=>{const c=mk('circle',{r:3.2,fill:D.acc,opacity:0});s.append(c);return c}):[];
const pts=[];if(o.s=='turbine'){const x=p[0]||216,y=p[1]||240,h=Math.max(60,p[2]||150),R=h*.42;for(let k=0;k<=10;k++)pts.push([x,y-h*k/10]);[1,.6,.25].forEach(f=>{for(let k=0;k<20;k++)pts.push([x+R*f*Math.cos(k*.314),y-h+R*f*Math.sin(k*.314)])})}
else if(o.s=='icon'){const z=Math.max(20,p[2]||60);for(let a=0;a<=4;a++)for(let b=0;b<=4;b++)pts.push([p[0]-z/2+z*a/4,p[1]-z/2+z*b/4])}
else if(o.s!='text')g.querySelectorAll('.d').forEach(e=>{try{const L=e.getTotalLength(),m=Math.max(8,Math.min(60,Math.round(L/5)));for(let k=0;k<=m;k++){const q=e.getPointAtLength(L*k/m);pts.push([q.x,q.y])}}catch(_){}});
return {g,lb,rot,cx,cy,A,at:Math.max(0,n(o.at)),dots,flow,ph:cx*.05+cy*.03,spin:/spin/.test(A)&&!rot&&(o.s!='icon'||canSpin(o.i)),pts,tx:o.s=='text'?g.firstChild:null}}).filter(Boolean);
// texty a popisy nesmú ležať na čiarach ani na sebe: nájdi najbližšie voľné miesto
const placed=[];const P=els.reduce((a,e)=>a.concat(e.pts),[]);
const bb=e=>{try{const b=e.getBBox();return [b.x-3,b.y-2,b.x+b.width+3,b.y+b.height+2]}catch(_){return null}};
const bad=(b)=>b[0]<4||b[2]>428||b[1]<2||b[3]>278||P.some(q=>q[0]>b[0]&&q[0]<b[2]&&q[1]>b[1]&&q[1]<b[3])||placed.some(c=>b[0]<c[2]&&b[2]>c[0]&&b[1]<c[3]&&b[3]>c[1]);
const CAND=[[0,0]];for(let r=1;r<=9;r++){const d=r*9;[[0,d],[0,-d],[d,0],[-d,0],[d,d*.6],[-d,d*.6],[d,-d*.6],[-d,-d*.6]].forEach(c=>CAND.push(c))}
const settle=e=>{if(!e||!e.textContent)return;const b=bb(e);if(!b)return;let best=null;for(const c of CAND){const t=[b[0]+c[0],b[1]+c[1],b[2]+c[0],b[3]+c[1]];if(!bad(t)){best=[c,t];break}}
if(!best){const c=[Math.max(4-b[0],Math.min(428-b[2],0)),Math.max(2-b[1],Math.min(278-b[3],0))];best=[c,[b[0]+c[0],b[1]+c[1],b[2]+c[0],b[3]+c[1]]]}
e.setAttribute('x',n(e.getAttribute('x'))+best[0][0]);e.setAttribute('y',n(e.getAttribute('y'))+best[0][1]);placed.push(best[1])};
els.forEach(o=>settle(o.tx));els.forEach(o=>settle(o.lb));
return (t,stf)=>els.forEach(o=>{const p=stf(o.at,.9);o.g.style.opacity=p>0?1:0;o.g.querySelectorAll('.d').forEach(e=>{e.style.strokeDasharray='1 1';e.style.strokeDashoffset=1-cl(p)});o.g.querySelectorAll('text').forEach(e=>e.style.opacity=cl(p));if(o.lb)o.lb.style.opacity=E(stf(o.at+.5,.5));
let tr='';if(/shake/.test(o.A)){const k=cl(p)*2.6;tr+=`translate(${Math.sin(t*31+o.ph)*k} ${Math.cos(t*27+o.ph)*k*.5}) rotate(${Math.sin(t*23+o.ph)*1.6*cl(p)} ${o.cx} ${o.cy+60}) `}
if(/float/.test(o.A))tr+=`translate(0 ${Math.sin(t*1.4+o.ph)*5}) `;if(/pulse/.test(o.A)){const k=1+.07*Math.sin(t*3.2+o.ph);tr+=`translate(${o.cx} ${o.cy}) scale(${k}) translate(${-o.cx} ${-o.cy}) `}
if(o.spin)tr+=`rotate(${(t*80)%360} ${o.cx} ${o.cy}) `;o.g.setAttribute('transform',tr);
if(o.rot)o.rot.setAttribute('transform',`rotate(${(t*o.rot._v*cl(p*1.5))%360} ${o.rot._c[0]} ${o.rot._c[1]})`);
if(o.dots.length){let L=0;try{L=o.flow.getTotalLength()}catch(e){}o.dots.forEach((c,i)=>{const q=((t*.45+i/3)%1);if(!L||p<1){c.setAttribute('opacity',0);return}const pt=o.flow.getPointAtLength(q*L);c.setAttribute('cx',pt.x);c.setAttribute('cy',pt.y);c.setAttribute('opacity',Math.sin(q*Math.PI))})}})};
/*EXTRA_BOARDS*/
V.text=(v,d)=>{const ws=String(d.w||'').split(/\s+/).filter(Boolean).slice(0,6);const box=el('div','',`position:absolute;left:0;top:40px;width:864px;height:480px;display:flex;flex-wrap:wrap;align-content:center;gap:0 22px;font-weight:900;text-transform:uppercase;line-height:1.02;font-size:118px;letter-spacing:-2px`);
const sp=ws.map((w,i)=>{const e=el('span','',i==ws.length-1?'color:var(--acc)':'',esc(w));box.append(e);return e});v.append(box);fit(box,118,48,480,864);
return (t,st)=>sp.forEach((e,i)=>{const p=st(i*.25,.45);e.style.opacity=p;e.style.display='inline-block';e.style.transform=`translateY(${(1-E(p))*50}px)`})};
V.product=(v,d)=>{const I=(d.i||[]).filter(Boolean).slice(0,3);const solo=!I.length;const bw=solo?864:400,bh=560,cx=bw/2,cy=270;
const halo=el('div','',`position:absolute;left:${cx-(solo?430:330)}px;top:${cy-(solo?430:330)}px;width:${solo?860:660}px;height:${solo?860:660}px;border-radius:50%;background:radial-gradient(circle,var(--acc) 0%,transparent 64%)`);
const fl=el('div','',`position:absolute;left:${cx-(solo?260:180)}px;top:${bh-34}px;width:${solo?520:360}px;height:44px;border-radius:50%;background:radial-gradient(ellipse,var(--acc) 0%,transparent 70%)`);
const im=el('img','',`position:absolute;left:0;top:0;width:${bw}px;height:${bh}px;object-fit:contain`);im.src=d.img;v.append(halo,fl,im);
const rh=Math.min(170,bh/Math.max(1,I.length)),y0=(bh-rh*I.length)/2;const rows=I.map((x,i)=>{const r=el('div','',`position:absolute;left:452px;top:${y0+i*rh}px;width:412px;height:${rh}px`);
r.innerHTML=`<div class="ln" style="width:56px;height:5px;background:var(--acc);margin:${rh/2-58}px 0 18px;transform-origin:left"></div><div class="it" style="font-weight:800;text-transform:uppercase;font-size:44px;line-height:1.06;overflow-wrap:break-word">${esc(x)}</div>`;v.append(r);fit(r.querySelector('.it'),44,24,96,412);return r});
return (t,st)=>{const p=st(.1,1);halo.style.opacity=(solo?.5:.42)*st(0,1.2)*(1+.08*Math.sin(t*1.3));fl.style.opacity=.55*st(.3,1);im.style.opacity=cl(p*1.4);im.style.transform=`translateY(${(1-p)*36+Math.sin(t*.9)*5}px) scale(${.93+.07*p})`;
rows.forEach((r,i)=>{const q=st(1.1+i*.9,.6);r.style.opacity=q;r.style.transform=`translateX(${(1-q)*40}px)`;r.querySelector('.ln').style.transform=`scaleX(${q})`})}};
// ---------- scény ----------
const WIDE=!!D.wide;if(WIDE){document.documentElement.classList.add('wide');document.body.classList.add('wide')}
const PW=WIDE?1920:1080,PH=WIDE?1080:1920,GAP=90;
// jedno veľké plátno: scény ležia vedľa seba (had), kamera sa medzi nimi presúva a na konci ukáže celý obraz
const NS=D.scenes.length,COLS=Math.max(1,WIDE?Math.ceil(Math.sqrt(NS)):Math.min(NS,Math.ceil(Math.sqrt(NS*1.7)))),ROWS=Math.ceil(NS/COLS),WW=COLS*PW+(COLS-1)*GAP,WH=ROWS*PH+(ROWS-1)*GAP;
const root=document.getElementById('root');const SC=D.scenes.map((sc,i)=>{const w=el('div','sc');w.style.display='block';root.append(w);
const row=Math.floor(i/COLS),kk=i%COLS,col=row%2?COLS-1-kk:kk;const X0=col*(PW+GAP),Y0=row*(PH+GAP);w.style.left=X0+'px';w.style.top=Y0+'px';w.style.width=PW+'px';w.style.height=PH+'px';const fr=el('div','fr');w.append(fr);
const k=el('div','kick','',`<b>${String(i+1).padStart(2,'0')}</b>${D.kicker?' · '+esc(D.kicker):''} · ${i+1}/${D.scenes.length}`);
const tt=el('div','ttl');tt.lang=D.lang;tt.innerHTML=String(sc.h||'').split(/\s+/).filter(Boolean).map(x=>`<span class="w"><span>${esc(x)}</span></span>`).join(' ');w.append(k,tt);
const intro=i==0;if(WIDE)fit(tt,intro?66:58,30,76,1620);else fit(tt,intro?104:82,36,212,860);const vz=el('div','viz');w.append(vz);
let upd=()=>{};try{upd=(V[sc.v.k]||V.text)(vz,sc.v)||(()=>{})}catch(e){vz.textContent=''}
w.style.display='none';
const pro=sc.v.k=='mech'&&!!(window.MECHPRO&&MECHPRO[sc.v.m]);return {w,k,tt,vz,upd,fr,c:[X0+PW/2,Y0+PH/2],t0:sc.t0,t1:sc.t1,steps:sc.steps||0,pro,fast:i==0&&pro}});
const CAP=document.getElementById('cap'),BAR=document.getElementById('bar'),GLOW=document.getElementById('glow'),LG=document.getElementById('lg'),END=document.getElementById('end');let lastCap=-1;
const EIMG=END.querySelector('img'),ELN=END.querySelector('.ln'),EGL=END.querySelector('.gl');const TAIL=D.tail||0;
// sprievodca: líška (maskot) pri titulkoch – „hovorí“ ich, ukazuje hore na stroj a reaguje na čísla (keď je D.guide; na výšku vľavo od titulkov, na šírku v ľavom dolnom rohu pod číslami)
const GD=(()=>{if(!D.guide)return null;const R=2,w=210,h=290,c=el('canvas','',WIDE?'position:absolute;left:150px;top:846px;width:210px;height:290px;z-index:4;transform-origin:0 0;transform:scale(.73)':'position:absolute;left:30px;top:1367px;width:210px;height:290px;z-index:4;transform-origin:0 0;transform:scale(1.42)');c.id='gdc';c.width=w*R;c.height=h*R;document.getElementById('stage').append(c);
if(WIDE){CAP.style.left='380px';CAP.style.width='1160px'}else{CAP.style.left='350px';CAP.style.width='600px'}return {x:c.getContext('2d',{willReadFrequently:true}),R,w,h}})();
// líška žije: v scéne s emóciou (sc.fx) vyskočí, 1–3 s reaguje (prekvapenie, zamyslenie, strach, radosť, nesúhlas, ukazovanie) a zase odíde; na začiatku je hneď v akcii, na konci sa vráti do úvodnej pózy (slučka)
function foxState(t,cur,force){const sc=D.scenes[cur]||{},lt=t-(sc.t0||0),WIN=WIDE?4.2:2.8,LST=D.scenes.length-1;let m=sc.fx||'',l=lt,vis=0;
if(D.loop&&t>D.total-.9){m=(D.scenes[0]||{}).fx||'surprised';l=t-(D.total-.9);vis=E(l/.3)}
else if(m){vis=E((lt-.05)/.3)*(1-E((lt-WIN+.35)/.35))}
if(force){vis=1;l=Math.max(l,.9);if(!m)m='happy'}return {m,l,vis}}
function drawGuide(t,cur,talk,ending,force){const {x,R,w,h}=GD,A=D.acc,T2=Math.PI*2;x.setTransform(R,0,0,R,0,0);x.clearRect(0,0,w,h);x.translate(0,40);const sc=D.scenes[cur]||{},v=sc.v||{},lt=t-(sc.t0||0);
const F=foxState(t,cur,force),M=F.m,ml=F.l,on=k=>M==k?1:0,pk=E((ml-.1)/.35)*(1-E((ml-2.6)/.4)),
pt=Math.max(v.k=='mech'?E((lt-.45)/.4):0,on('point')*pk),sur=on('surprised')*pk,thk=on('thinking')*pk,wor=on('worried')*pk,hap=on('happy')*pk,no=on('no')*pk;
let ex=0,ek=0;if(v.c&&v.c.t!=null){ek=lt-v.c.t;if(ek>=0&&ek<1.3)ex=Math.exp(-ek*3.2)}ex=Math.max(ex,sur*Math.exp(-Math.max(0,ml-.1)*1.6));
const a=F.vis*(ending?0:1);if(a<=.01)return;talk=talk&&!sur&&!hap;const amp=talk?.5+.5*Math.sin(t*23)*Math.sin(t*7.7+1):0,
hop=(sur+hap)*Math.abs(Math.sin(ml*9))*Math.exp(-ml*1.3)*30,bob=Math.sin(t*2.1)*5-ex*24*Math.abs(Math.sin(ek*12))-hop,shk=wor*Math.sin(t*41)*2.2,blink=((t+.7)%3.3)<.11&&ex<.2&&!hap;
x.globalAlpha=a;x.lineJoin='round';x.lineCap='round';x.fillStyle='rgba(0,0,0,.55)';x.beginPath();x.ellipse(92,240,44+bob*.4,6,0,0,T2);x.fill();
x.save();x.translate(shk,(1-a)*90+bob);const box=(X,Y,W,H,r,f,st,lw)=>{x.beginPath();x.roundRect(X,Y,W,H,r);x.fillStyle=f;x.fill();if(st){x.strokeStyle=st;x.lineWidth=lw||5;x.stroke()}};
const DK='#16181b',WH='#fff',CR='#e9e3d8',pth=(P,f,st,lw)=>{x.beginPath();P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.closePath();if(f){x.fillStyle=f;x.fill()}if(st){x.strokeStyle=st;x.lineWidth=lw||5;x.stroke()}},
ell=(X,Y,rx,ry,f)=>{x.beginPath();x.ellipse(X,Y,rx,ry,0,0,T2);x.fillStyle=f;x.fill()},arm=(P,col)=>{x.strokeStyle=WH;x.lineWidth=7;x.beginPath();P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();const Q=P[P.length-1];x.fillStyle=col||WH;x.beginPath();x.arc(Q[0],Q[1],col?8:5.6,0,T2);x.fill();if(col){x.strokeStyle=WH;x.lineWidth=2;x.stroke()}};
// chvost (pri radosti sa kýve rýchlejšie)
x.save();x.translate(66,204);x.rotate(.7+Math.sin(t*(2.4+hap*8))*(.12+hap*.15));x.beginPath();x.moveTo(0,0);x.bezierCurveTo(-29.6,-18,-59.2,-30,-74,-8);x.bezierCurveTo(-59.2,10,-29.6,14,0,12);x.closePath();x.fillStyle=A;x.fill();x.strokeStyle=WH;x.lineWidth=4;x.stroke();
x.beginPath();x.moveTo(-57.7,-24);x.bezierCurveTo(-66.6,-20,-74,-12,-74,-8);x.bezierCurveTo(-66.6,4,-60.7,6,-54.8,6);x.closePath();x.fillStyle=CR;x.fill();x.restore();
// ľavá ruka: v pokoji dole, pri zamyslení pri brade, pri radosti hore
const lArm=()=>{const EX=54+Math.sin(t*2.1)*3,up=Math.max(hap,sur*.6),ch=thk;const hx=EX*(1-up-ch)+40*up+76*ch,hy=188*(1-up-ch)+118*up+140*ch;arm([[66,162],[hx,hy]],ch>.3?A:null)};if(thk<.3)lArm();
box(62,146,60,70,24,A,WH);ell(92,186,20,26,CR);
// hlava: pri nesúhlase krúti, pri zamyslení nakloní
x.save();x.translate(92,140);x.rotate(no*Math.sin(ml*13)*.2+thk*.12);x.translate(-92,-140);
{const eu=sur*8;pth([[52,80],[58-eu*.3,36-eu],[84,64]],A,WH);pth([[132,80],[126+eu*.3,36-eu],[100,64]],A,WH);pth([[59,72],[62-eu*.3,46-eu],[76,64]],DK);pth([[125,72],[122+eu*.3,46-eu],[108,64]],DK)}
pth([[44,72],[140,72],[136,102],[92,138],[48,102]],A,WH);pth([[48,98],[86,110],[92,138],[98,110],[136,98],[92,138]],CR);
{const dx=4*pt+6*thk,dy=-3*pt-2*ex-6*thk;[72,112].forEach((X,j)=>{if(hap>.4){x.strokeStyle=DK;x.lineWidth=4.5;x.beginPath();x.arc(X,90,8,Math.PI*1.15,Math.PI*1.85);x.stroke()}
else if(blink){x.strokeStyle=DK;x.lineWidth=4;x.beginPath();x.moveTo(X-8,86);x.lineTo(X+8,86);x.stroke()}else{x.fillStyle=DK;x.beginPath();x.arc(X+dx,86+dy,8*(1+.25*ex),0,T2);x.fill();x.fillStyle='rgba(255,255,255,.9)';x.beginPath();x.arc(X+dx+2.8,86+dy-2.8,2.24,0,T2);x.fill()}
const bw=Math.max(wor,no);if(bw>.05){x.strokeStyle=DK;x.lineWidth=4;x.globalAlpha=a*bw;x.beginPath();const s=j?-1:1;if(wor>no){x.moveTo(X-9*s,74);x.lineTo(X+7*s,70)}else{x.moveTo(X-9*s,70);x.lineTo(X+7*s,76)}x.stroke();x.globalAlpha=a}})}
ell(92,115,7,5,DK);
if(hap>.3){x.strokeStyle=DK;x.lineWidth=4;x.beginPath();x.arc(92,121,9,Math.PI*.15,Math.PI*.85);x.stroke()}
else if(wor>.3){x.strokeStyle=DK;x.lineWidth=3.5;x.beginPath();x.moveTo(82,129);x.quadraticCurveTo(87,124,92,129);x.quadraticCurveTo(97,134,102,129);x.stroke()}
else{const ry=1.6+4.4*Math.min(1,amp+.6*ex+.8*sur);ell(92,127,5.5,ry,DK)}
x.restore();if(thk>=.3)lArm();
// pravá ruka: ukazuje hore na to, o čom sa hovorí (šípka), pri radosti hore
{const an=1.2-2.32*pt+Math.sin(t*4.6)*.07*pt-2.0*hap*(1-pt),S0=[122,160],EL=[S0[0]+Math.cos(an+.4*pt)*30,S0[1]+Math.sin(an+.4*pt)*30],HD=[EL[0]+Math.cos(an-.25*pt)*34,EL[1]+Math.sin(an-.25*pt)*34];
arm([S0,EL,HD],A);
if(pt>.5){const b=an-.25,k=E((pt-.5)/.4),w=3*Math.sin(t*5),TX=HD[0]+Math.cos(b)*(27+w),TY=HD[1]+Math.sin(b)*(27+w);x.globalAlpha=a*k;x.strokeStyle=A;x.lineWidth=6;x.beginPath();x.moveTo(TX-Math.cos(b-.75)*14,TY-Math.sin(b-.75)*14);x.lineTo(TX,TY);x.lineTo(TX-Math.cos(b+.75)*14,TY-Math.sin(b+.75)*14);x.stroke();x.globalAlpha=a}}
// znak nad hlavou: ! prekvapenie, ? zamyslenie, kvapka strach, hviezdičky radosť, X nesúhlas
{const sy=E((ml-.15)/.3),k=Math.max(sur,thk,wor,hap,no);if(k>.1&&sy>0){x.globalAlpha=a*Math.min(1,k*1.4)*sy;x.save();x.translate(170,34-6*sy);x.lineWidth=5;x.strokeStyle=WH;x.fillStyle=A;
if(sur>.1||thk>.1){x.font='900 44px Helvetica,Arial,sans-serif';x.textAlign='center';x.textBaseline='middle';x.strokeText(sur>.1?'!':'?',0,0);x.fillText(sur>.1?'!':'?',0,0)}
else if(wor>.1){x.beginPath();x.moveTo(0,-16);x.quadraticCurveTo(12,4,0,10);x.quadraticCurveTo(-12,4,0,-16);x.fillStyle='#8fd3ff';x.fill();x.stroke()}
else if(hap>.1){[[-14,-6,9],[10,-14,7],[12,10,6]].forEach(([X,Y,r])=>{x.beginPath();for(let i=0;i<8;i++){const q=i*Math.PI/4+t*2,rr=i%2?r*.4:r;x.lineTo(X+Math.cos(q)*rr,Y+Math.sin(q)*rr)}x.closePath();x.fill()})}
else{x.lineWidth=7;x.strokeStyle=A;x.beginPath();x.moveTo(-11,-11);x.lineTo(11,11);x.moveTo(11,-11);x.lineTo(-11,11);x.stroke()}
x.restore();x.globalAlpha=a}}
x.restore();x.globalAlpha=1}

if(D.logo){LG.src=D.logo;LG.style.display='block'}if(D.logoEnd||D.logo)EIMG.src=D.logoEnd||D.logo;
const XF=.22;
// pozadie v pohybe: jemná mriežka a čiastočky energie, ktoré pomaly stúpajú
const BG=document.getElementById('bg');BG.width=PW;BG.height=PH;const CX=BG.getContext('2d');
let _sd=7;const rnd=()=>{_sd=(_sd*16807)%2147483647;return _sd/2147483647};
const PT=Array.from({length:WIDE?46:38},()=>({x:rnd(),y:rnd(),r:1.2+rnd()*2.6,v:.012+rnd()*.03,ph:rnd()*6.28,a:rnd()<.3}));
function drawBg(t,ending){CX.clearRect(0,0,PW,PH);if(ending)return;const g=120,off=(t*9)%g;CX.strokeStyle='rgba(255,255,255,.035)';CX.lineWidth=1;CX.beginPath();
for(let x=-g+off;x<PW+g;x+=g){CX.moveTo(x,0);CX.lineTo(x,PH)}for(let y=-g+off*.6;y<PH+g;y+=g){CX.moveTo(0,y);CX.lineTo(PW,y)}CX.stroke();
PT.forEach(p=>{const y=((p.y-t*p.v)%1+1)%1*PH,x=p.x*PW+Math.sin(t*.5+p.ph)*26;const al=(.10+.10*Math.sin(t*.9+p.ph))*(p.a?1.9:1);CX.fillStyle=p.a?D.acc:'#fff';CX.globalAlpha=Math.max(0,al);CX.beginPath();CX.arc(x,y,p.r,0,6.3);CX.fill()});CX.globalAlpha=1}
function renderAt(t){let cur=SC.length-1;for(let i=0;i<SC.length;i++){if(t<SC[i].t1){cur=i;break}}window._cur=cur;
const ending=TAIL>0&&t>=D.total,et=t-D.total;
const MV=.8,LD=SC.length?SC[SC.length-1].t1-SC[SC.length-1].t0:0,ZO=NS>2&&!D.loop?Math.min(3.2,Math.max(1.8,LD*.5)):0;const zo=ZO?EI((t-(D.total-ZO))/(ZO*.75)):0;
// prechod: stará scéna odíde doľava a nová príde sprava – vždy vodorovne, takže obraz ani nadpis nikdy neprejdú cez titulky
let cx=SC[cur].c[0],cy=SC[cur].c[1],zs=1,tr=null;if(cur>0){const p=EI((t-SC[cur].t0)/MV);if(p<1){tr=[cur-1,cur,p];zs=1-.14*Math.sin(Math.PI*p)}}
// slučka: na konci krátkeho videa kamera preletí späť na prvú scénu v jej úvodnom stave, takže koniec plynulo nadviaže na začiatok
const lp=D.loop&&NS>1&&cur>0?EI((t-(D.len-.6))/.5):0;if(lp>0){tr=[cur,0,lp];zs=1-.14*Math.sin(Math.PI*lp)}
let sx=PW/2,sy=PH/2;if(zo>0){const AW=WIDE?1700:864,AH=WIDE?790:1150,fs=Math.min(AW/WW,AH/WH);cx+=(WW/2-cx)*zo;cy+=(WH/2-cy)*zo;zs=1+(fs-1)*zo;sx+=((WIDE?960:504)-sx)*zo;sy+=((WIDE?465:750)-sy)*zo}
root.style.transform=`translate(${sx-cx*zs}px,${sy-cy*zs}px) scale(${zs})`;root.style.opacity=ending?1-cl(et/.3):1;
SC.forEach((s,i)=>{const home=lp>0&&i==0,lt=home?0:t-s.t0,dur=s.t1-s.t0;const vis=home||(!(ending&&et>.3)&&(zo>0?i<=cur:(i==cur||(i==cur-1&&t-SC[cur].t0<MV))));s.w.style.display=vis?'block':'none';if(!vis)return;
s.w.style.transform=tr&&!zo&&(i==tr[0]||i==tr[1])?`translate(${SC[cur].c[0]-s.c[0]+(i==tr[1]?1-tr[2]:-tr[2])*(PW+GAP)}px,${SC[cur].c[1]-s.c[1]}px)`:'';
s.fr.style.opacity=zo;if(i!=cur&&!home)return;
const l2=i==0?lt:lt-.12;s.k.style.opacity=E(l2/.4);
s.tt.querySelectorAll('.w>span').forEach((e,j)=>{const p=E((l2-.05-j*.07)/.5);e.style.transform=`translateY(${(1-p)*105}%)`});
const span=Math.max(.6,Math.min(1.35,(dur*.72-.6)/Math.max(1,s.steps)));const st=(a,b)=>s.fast?1:E((lt-.6-a*span)/(b*Math.max(.7,span)));
s.vz.style.opacity=s.fast?1:E((l2-.2)/.4);s.vz.style.transform=s.pro?`scale(${WIDE?1.28:1.1})`:(WIDE?`translate(${Math.sin(lt*.55)*10}px,${(1-E((l2-.15)/.6))*34}px) scale(${1.16*(1+.02*cl(lt/Math.max(1,dur)))*(1+.015*((Math.floor(lt/2.6)%2)?E((lt%2.6)/.6):1-E((lt%2.6)/.6)))})`:`translate(${Math.sin(lt*.55)*14}px,${(1-E((l2-.15)/.6))*34+Math.cos(lt*.4)*8}px) scale(${1.16*(1+.05*cl(lt/Math.max(1,dur)))*(1+.04*((Math.floor(lt/2.6)%2)?E((lt%2.6)/.6):1-E((lt%2.6)/.6)))})`);try{s.upd(lt,st)}catch(e){}});
SPIN.forEach(g=>g.setAttribute('transform',`rotate(${(t*70)%360} 50 40)`));drawBg(t,ending);
GLOW.style.opacity=ending?0:(cur==0?.24*E(t/1.5):.10);GLOW.style.transform=`translate(${Math.sin(t*.3)*40}px,${Math.cos(t*.25)*40}px)`;
BAR.style.width=((WIDE?1920:1080)*cl(t/D.total))+'px';
if(ending){CAP.innerHTML='';if(GD)drawGuide(t,cur,false,true);LG.style.opacity=1-cl(et/.3);END.style.display='block';const p=E((et-.25)/.6);END.style.opacity=cl(et/.3);
EIMG.style.opacity=p;EIMG.style.transform=`translate(-50%,-50%) scale(${.94+.06*p})`;EGL.style.opacity=.30*E((et-.2)/1);ELN.style.transform=`scaleX(${E((et-.6)/.6)})`;
ELN.style.top=((WIDE?540:960)+EIMG.offsetHeight/2+(WIDE?50:70))+'px';return}
END.style.display='none';LG.style.opacity=.96*(1-cl(zo*1.6));
let ci=-1;for(let i=0;i<D.caps.length;i++){if(t>=D.caps[i].s-.05&&t<D.caps[i].e){ci=i;break}}
if(GD)drawGuide(t,cur,ci>=0,ending);
if(ci<0){CAP.innerHTML='';lastCap=-1;return}const c=D.caps[ci];
CAP.innerHTML=c.w.map(w=>`<span class="${t>=w.s?'on':''}">${esc(w.t)}</span>`).join(' ');
const on=[...CAP.children].filter(x=>x.classList.contains('on'));if(on.length)on[on.length-1].className='on k';if(ci!==lastCap){if(WIDE)fit(CAP,48,24,58,GD?1160:1400);else fit(CAP,GD?72:76,30,150,GD?600:864);lastCap=ci}}
// náhľadový obrázok dlhého videa: veľký text vľavo, hlavný obraz vpravo, bez titulkov a lišty
window.thumbMode=function(i,txt){i=Math.max(0,Math.min(SC.length-1,i|0));const s=SC[i];renderAt(window.THT!=null?Math.min(s.t1-.2,s.t0+window.THT*(s.t1-s.t0)):Math.max(s.t0+.1,s.t1-.2));
CAP.innerHTML='';BAR.style.width=0;LG.style.display='none';s.k.style.display='none';s.fr.style.opacity=0;
const words=String(txt||'').trim().split(/\s+/).filter(Boolean);if(!words.length)return;s.tt.style.display='none';s.vz.querySelectorAll('.phud').forEach(e=>e.style.display='none');
GLOW.style.opacity=.36;GLOW.style.transform=WIDE?'translate(520px,240px)':'translate(0,0)';document.getElementById('bg').style.opacity=.35;
const T=el('div','',`position:absolute;left:${WIDE?96:72}px;top:${WIDE?150:300}px;width:${WIDE?720:936}px;font-weight:800;text-transform:uppercase;line-height:.98;letter-spacing:-2px;text-shadow:0 6px 30px #000;-webkit-text-stroke:12px #000;paint-order:stroke fill;overflow-wrap:normal;word-break:keep-all;hyphens:none`);
// posledné slovo na plnom pruhu vo farbe kanála (tak to robia najúspešnejšie náhľady konkurencie, analýza 18.11.)
T.lang=D.lang;T.innerHTML=words.map((w,j)=>j==words.length-1?`<span style="display:inline-block;background:var(--acc);color:#fff;-webkit-text-stroke:0;text-shadow:none;padding:0 .14em .04em;margin-top:.06em;border-radius:.06em;box-shadow:0 8px 30px rgba(0,0,0,.5)">${esc(w)}</span>`:`<span style="color:#fff">${esc(w)}</span>`).join(' ');s.w.append(T);
fit(T,WIDE?190:200,70,WIDE?(GD?640:780):620,WIDE?720:936);if(WIDE){T.style.top=Math.max(70,((GD?900:1080)-T.offsetHeight)/2-10)+'px'}
// obraz dostane miesto, ktoré ostalo vedľa textu (na šírku) alebo pod ním (na výšku), a zmenší sa tak, aby sa doň zmestil celý
const Z=s.pro&&window.KIT?KIT.ZN:{l:0,t:0,w:864,h:560},rg=document.createRange();rg.selectNodeContents(T);const tr=rg.getBoundingClientRect(),wr=s.w.getBoundingClientRect(),kx=wr.width/PW;
const x0=WIDE?(tr.right-wr.left)/kx+44:60,x1=WIDE?1860:1020,y0=WIDE?90:(tr.bottom-wr.top)/kx+40,y1=WIDE?990:1790;
// náhľad sa pozerá v malom: obraz sa zväčší podľa toho, čo v ňom naozaj je (nie podľa celej zóny), aby nebol malý v prázdnej tme
let C=Z;try{s.vz.style.transform='none';const vr=s.vz.getBoundingClientRect();let a=1e9,b=1e9,c=-1e9,d=-1e9;
s.vz.querySelectorAll('path,rect,circle,ellipse,polygon,polyline,line,text,image,use,img,canvas').forEach(e=>{if(e.closest('.phud,defs,clipPath,mask,pattern'))return;const r=e.getBoundingClientRect();if(r.width<2&&r.height<2)return;const cs=getComputedStyle(e);if(cs.visibility=='hidden'||cs.display=='none')return;
let L=(r.left-vr.left)/kx,T2=(r.top-vr.top)/kx,W=r.width/kx,H=r.height/kx;
if(e.tagName=='CANVAS'&&e.width>8&&e.height>8){try{const g=e.getContext('2d'),q=g&&g.getImageData(0,0,e.width,e.height).data;if(q){let p=1e9,o=1e9,u=-1,n=-1;const st=3;
for(let y=0;y<e.height;y+=st)for(let x=0;x<e.width;x+=st){const k=(y*e.width+x)*4;if(q[k+3]>40&&q[k]+q[k+1]+q[k+2]>90){if(x<p)p=x;if(x>u)u=x;if(y<o)o=y;if(y>n)n=y}}
if(u<0)return;const fx=W/e.width,fy=H/e.height;L+=p*fx;T2+=o*fy;W=(u-p+st)*fx;H=(n-o+st)*fy}}catch(_){}}
if(W>1500||H>1000)return;a=Math.min(a,L);b=Math.min(b,T2);c=Math.max(c,L+W);d=Math.max(d,T2+H)});
if(c-a>40&&d-b>40){const m=16;C={l:a-m,t:b-m,w:c-a+2*m,h:d-b+2*m}}}catch(e){C=Z}
const sc=Math.min(C===Z?(WIDE?1.42:1.25):(WIDE?2.6:2.2),(x1-x0)/C.w,(y1-y0)/C.h);
s.vz.style.opacity=1;s.vz.style.transform=`scale(${sc})`;s.vz.style.left=((x0+x1)/2-432-(C.l+C.w/2-432)*sc)+'px';s.vz.style.top=((y0+y1)/2-280-(C.t+C.h/2-280)*sc)+'px';
// pozadie nie čisto čierne (v tmavom režime YouTube by splynulo): farba kanála za predmetom, k okrajom tmavne
GLOW.style.opacity=0;document.getElementById('bg').style.opacity=.25;document.body.style.background=`radial-gradient(ellipse ${WIDE?'62% 80% at 66% 50%':'90% 55% at 50% 66%'},color-mix(in srgb,var(--acc) 62%,#000) 0%,color-mix(in srgb,var(--acc) 26%,#000) 48%,#050505 100%)`;
// líška (maskot kanála) dole vľavo pod textom: tvár upúta oko a kanál je na prvý pohľad rozpoznateľný
// šípka od textu k predmetu (asi pätina víťazných náhľadov ukazuje šípkou na to podstatné)
if(WIDE&&words.length){try{const tb=T.getBoundingClientRect(),sx=(tb.right-wr.left)/kx+18,sy=(tb.top-wr.top)/kx+tb.height/kx*.62,ex=x0+(x1-x0)*.2,ey=(y0+y1)/2+40;
if(ex-sx>60){const A=document.createElementNS('http://www.w3.org/2000/svg','svg');A.setAttribute('width',1920);A.setAttribute('height',1080);A.style.cssText='position:absolute;left:0;top:0;z-index:6;overflow:visible';
const mx=(sx+ex)/2,my=Math.max(sy,ey)+90,d=`M${sx},${sy} Q${mx},${my} ${ex},${ey}`,ang=Math.atan2(ey-my,ex-mx),hl=46,h=(a)=>`${ex-hl*Math.cos(ang+a)},${ey-hl*Math.sin(ang+a)}`;
A.innerHTML=`<path d="${d}" fill="none" stroke="#000" stroke-width="26" stroke-linecap="round"/><path d="M${h(.5)} L${ex},${ey} L${h(-.5)}" fill="none" stroke="#000" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>
<path d="${d}" fill="none" stroke="var(--acc)" stroke-width="14" stroke-linecap="round"/><path d="M${h(.5)} L${ex},${ey} L${h(-.5)}" fill="none" stroke="var(--acc)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>`;s.w.append(A)}}catch(e){}}
if(GD&&WIDE){const c=GD.x.canvas;drawGuide(s.t0+.6,i,false,false,true);c.style.display='block';c.style.left='70px';c.style.top='720px';c.style.transform='scale(1.25)';c.style.zIndex=5}};
// kontrola prekrývania (bez AI) pre práve vykreslenú snímku: čo leží cez čo, hoci nemá. Vráti aj miesta textov, aby sa dalo overiť, že pod nimi nie je obraz.
window.ovl=function(){const s=SC[window._cur||0],bad=new Set(),B=e=>{const b=e.getBoundingClientRect();return [b.left,b.top,b.right,b.bottom]},U=q=>q.length?[Math.min(...q.map(b=>b.left)),Math.min(...q.map(b=>b.top)),Math.max(...q.map(b=>b.right)),Math.max(...q.map(b=>b.bottom))]:null,
TX=e=>{const r=document.createRange();r.selectNodeContents(e);return U([...r.getClientRects()].filter(b=>b.width>1&&b.height>1))},
hit=(a,b,m)=>!!a&&!!b&&Math.min(a[2],b[2])-Math.max(a[0],b[0])>m&&Math.min(a[3],b[3])-Math.max(a[1],b[1])>m,
op=e=>{let o=1;for(;e&&e.style;e=e.parentElement){const c=getComputedStyle(e);if(c.display=='none'||c.visibility=='hidden')return 0;o*=+c.opacity}return o};
const T={},cb=CAP.getBoundingClientRect(),k=cb.width/(CAP.offsetWidth||1);T.titulky=[cb.left,cb.top,cb.right,cb.top+(WIDE?58:150)*k];
T.nadpis=U([...s.tt.querySelectorAll('.w')].map(e=>e.getBoundingClientRect()));if(LG.offsetWidth&&op(LG)>.3)T.logo=B(LG);if(WIDE&&op(s.k)>.3)T['číslo scény']=TX(s.k);
const G=GD&&op(GD.x.canvas)>.3?B(GD.x.canvas):null;if(G)T.sprievodca=G;const ks=Object.keys(T);
ks.forEach((a,i)=>ks.slice(i+1).forEach(b=>{if(hit(T[a],T[b],2))bad.add(a+' × '+b)}));
s.vz.querySelectorAll('canvas.pmod,canvas.phud').forEach(c=>{if(op(c)<.3)return;const r=B(c),nm=c.classList.contains('pmod')?'obraz stroja':'čísla pri stroji';ks.forEach(a=>{if(hit(T[a],r,3))bad.add(a+' × '+nm)});
const S=c._S;if(!S)return;if(c.classList.contains('pmod')){const hc=[...s.vz.querySelectorAll('canvas.phud')].find(h=>h._S===S);if(hc&&hit(r,B(hc),2))bad.add('čísla pri stroji × obraz stroja');
const tg=S.tags.filter(u=>u[4]>.5);tg.forEach((a,i)=>tg.slice(i+1).forEach(b=>{if(hit(a,b,2))bad.add('názvy v modeli cez seba')}))}
else{const hd=S.hud.filter(u=>u[5]>.5).map(u=>[u[1],u[2],u[1]+u[3],u[2]+u[4]]);hd.forEach((a,i)=>hd.slice(i+1).forEach(b=>{if(hit(a,b,2))bad.add('čísla pri stroji cez seba')}))}});
const lv=[...s.vz.querySelectorAll('*')].filter(e=>[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())&&op(e)>.5).map(e=>[e,TX(e)]).filter(q=>q[1]);
lv.forEach((a,i)=>{ks.forEach(b=>{if(hit(T[b],a[1],3))bad.add(b+' × popis v obraze')});lv.slice(i+1).forEach(b=>{if(!a[0].contains(b[0])&&!b[0].contains(a[0])&&hit(a[1],b[1],4)&&Math.min(a[1][3],b[1][3])-Math.max(a[1][1],b[1][1])>.3*Math.min(a[1][3]-a[1][1],b[1][3]-b[1][1]))bad.add('popisy v obraze cez seba')})});   // riadky textu sa smú dotýkať, nie ležať cez seba

return {bad:[...bad],zones:T}};
window.READY=true;
</script></body></html>"""

TEMPLATE = TEMPLATE.replace("/*EXTRA_ICONS*/", icons_extra.js() + ",/*PACK_ICONS*/", 1)
TEMPLATE = TEMPLATE.replace("const ICONS={", "const ICON_ALIAS=/*ICON_ALIAS*/{};const ICONS={", 1)
_HERE = Path(__file__).parent
TEMPLATE = TEMPLATE.replace("/*EXTRA_BOARDS*/", (_HERE / "boards_extra.js").read_text(encoding="utf-8") + "\n"
                            + (_HERE / "boards_pack.js").read_text(encoding="utf-8") + "\n"
                            + (_HERE / "geo" / "map.js").read_text(encoding="utf-8") + "\n"
                            + "\n".join(f.read_text(encoding="utf-8") for f in sorted((_HERE / "boards").glob("*.js"))), 1)

STEPS = {"flow": lambda d: 4 if d.get("x") else 3, "cycle": lambda d: 4, "bars": lambda d: len(d.get("i") or []) + 1,
         "calc": lambda d: len(d.get("r") or []) + .5, "compare": lambda d: 2.5, "count": lambda d: 2, "list": lambda d: len(d.get("i") or []),
         "icons": lambda d: len(d.get("i") or []) + .5, "temp": lambda d: 3.5, "house": lambda d: len(d.get("i") or []) + 1.5,
         "split": lambda d: len(d.get("i") or []) + .5, "text": lambda d: 1.5, "hero": lambda d: 2.5, "scene": lambda d: len(d.get("n") or []) + 1.5,
         "draw": lambda d: max([int(x.get("at") or 0) for x in (d.get("e") or []) if isinstance(x, dict)] or [0]) + 1.5,
         "product": lambda d: len(d.get("i") or []) + 1.5,
         "map": lambda d: 2.2 + .6 * len(d.get("r") or []) + .4 * len(d.get("pts") or []) + .5 * len(d.get("v") or [])
                          + 1.25 * max(0, len(d.get("hist") or []) - 1) + (1.6 if d.get("onto") else 0),
         "timeline": lambda d: len(d.get("i") or []) * .8 + .8, "line": lambda d: 3,
         "growth": lambda d: 3.2, "pie": lambda d: len(d.get("i") or []) * .55 + .6, "stack": lambda d: len(d.get("i") or []) * .9 + .6,
         "dots": lambda d: 2.4, "size": lambda d: len(d.get("i") or []) * .7 + .6, "layers": lambda d: len(d.get("i") or []) * .45 + .6,
         "mech": lambda d: 2, "forces": lambda d: len(d.get("f") or []) * .5 + 1, "waterfall": lambda d: len(d.get("i") or []) * .5 + .8,
         "funnel": lambda d: len(d.get("i") or []) * .55 + .4, "loan": lambda d: 2.7, "inflation": lambda d: 2.2,
         "crack": lambda d: len(d.get("l") or [1] * 5) * .45 + .5, "sim": lambda d: 3.2, "lines": lambda d: 2.6}

for _m in BOARD_META.values():
    for _k, _v in (_m.get("kinds") or {}).items():
        _st = _v.get("steps") or [2]
        STEPS.setdefault(_k, lambda d, _st=_st: float(_st[0]) + (float(_st[1]) * len(d.get(_st[2]) or []) if len(_st) > 2 else 0))

class _Slots:
    """Koľko videí sa smie skladať naraz (nastavenie render_parallel, 1–8, predvolene 4). Každé má vlastný prehliadač.
    Nastavenie sa číta pri každom skladaní, takže sa dá meniť bez reštartu appky."""

    def __init__(self):
        self._c = threading.Condition()
        self.active = 0

    @staticmethod
    def limit():
        try:
            return max(1, min(8, int(db.get_setting("render_parallel", 4) or 4)))
        except Exception:
            return 4

    def __enter__(self):
        with self._c:
            while self.active >= self.limit():
                self._c.wait(timeout=15)
            self.active += 1
        return self

    def __exit__(self, *a):
        with self._c:
            self.active -= 1
            self._c.notify_all()


_lock = _Slots()
# plátna sa kreslia bez grafickej karty: na Macu sa inak plátno samo vynulovalo a model ostal malý v rohu
CANVAS_ARGS = ["--disable-accelerated-2d-canvas"]


TAIL = 1.8  # záverečná karta s logom po dohovorení hlasu


def _img_uri(path, box=760):
    import base64
    import io
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    im.thumbnail((box, box))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def with_product(h, v, products, cache):
    """Scéna, ktorá spomína produkt značky (napr. HYDROBOX) a nemá vlastnú schému s číslami, ukáže obrázok produktu."""
    if not products or v.get("k") not in ("icons", "text", "list"):
        return v
    txt = " " + re.sub(r"[^a-z0-9]+", " ", (h + " " + " ".join(texts(v))).lower()) + " "
    hit = max((k for k in products if f" {k} " in txt), key=len, default=None)
    if not hit:
        return v
    try:
        if hit not in cache:
            cache[hit] = _img_uri(products[hit])
    except Exception:
        return v
    k = v.get("k")
    items = [x[1] for x in v.get("i") or [] if len(x) > 1 and x[1]] if k == "icons" else list(v.get("i") or []) if k == "list" else []
    return {"k": "product", "img": cache[hit], "i": [str(x) for x in items][:3]}


VISUAL_KINDS = ("scene", "draw", "product", "hero", "house", "cycle", "flow", "icons", "compare")


THUMB_SCORE = {"map": 80, "product": 70, "house": 45, "cycle": 40, "scene": 40, "draw": 30, "flow": 20, "compare": 15, "icons": 8, "hero": 4}


def thumb_index(scenes, sc_data, want=None):
    """Scéna pre náhľad (stratégia náhľadov 18.11.): jeden veľký konkrétny predmet. Najprv presný model stroja,
    potom mapa či produkt, schémy až potom; samotná ikona (hero), čísla a zoznamy len keď nič iné nie je.
    Scéna, ktorú vybral scenár, dostane prednosť medzi rovnako dobrými. Nie posledná scéna (tá je oddialená)."""
    from . import auto_visual
    last = max(0, len(sc_data) - 2)
    try:
        want = int(want)
    except (TypeError, ValueError):
        want = -1
    best, bi = -1, 0
    for i, d in enumerate(sc_data[:last + 1]):
        v = d.get("v") or {}
        k = v.get("k")
        sc = 100 if k == "mech" and v.get("m") in auto_visual.PRECISE else 25 if k == "mech" else THUMB_SCORE.get(k, 0)
        if sc and i == want:
            sc += 12
        sc -= i * 4 / max(1, last)   # pri zhode skôr scéna zo začiatku (hlavný predmet videa)
        if sc > best:
            best, bi = sc, i
    return bi


EVENTS = {}   # cesta videa -> [(druh zvuku, čas)] z posledného skladania
QA = {}       # cesta videa -> výsledok kontroly pred zverejnením
WEAK_MAX = 0.4    # najviac toľko scén smie byť „slabých“ (ikony, text, zoznam)
EMPTY_MIN = 0.006   # prázdna scéna má 0 až 0,3 %; riedka tabuľka s dvoma riadkami textu okolo 1 % (pri 1,2 % padali dobré videá na hrane merania)


def _coverage(jpg, wide):
    """Koľko z plochy obrazu scény (bez nadpisu a titulkov) naozaj niečo ukazuje (0–1)."""
    try:
        import io
        from PIL import Image, ImageChops
        box = (400, 290, 1520, 960) if wide else (30, 560, 1050, 1290)
        r, g, bl = Image.open(io.BytesIO(jpg)).convert("RGB").crop(box).resize((204, 140)).split()
        # najsvetlejšia zložka farby, nie jas: červená či modrá farba kanála má nízky jas a obraz v nej by sa nerátal
        h = ImageChops.lighter(ImageChops.lighter(r, g), bl).histogram()
        return sum(h[71:]) / max(1, sum(h))
    except Exception:
        return 1.0


OVER_MAX = 0.002   # v mieste nadpisu či titulkov smie byť (po skrytí textu a pozadia) najviac toľko „hrán“ obrazu; prázdne miesto má 0


def _overlap(pg, over, k):
    """Kontrola jednej snímky bez AI: (1) miesta textov a obrazu sa nesmú pretínať, (2) po skrytí textov musí byť pod nimi prázdno."""
    try:
        import io
        from PIL import Image, ImageFilter
        info = pg.evaluate("window.ovl()")
        bad = set(info.get("bad") or [])
        pg.evaluate("document.body.classList.add('notext')")
        try:
            im = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("L")
        finally:
            pg.evaluate("document.body.classList.remove('notext')")
        for name, r in (info.get("zones") or {}).items():
            if not r:
                continue
            box = (max(0, int(r[0]) - 4), max(0, int(r[1]) - 4), min(im.width, int(r[2]) + 4), min(im.height, int(r[3]) + 4))
            if box[2] - box[0] < 8 or box[3] - box[1] < 8:
                continue
            px = im.crop(box).filter(ImageFilter.FIND_EDGES).crop((1, 1, box[2] - box[0] - 1, box[3] - box[1] - 1)).getdata()
            if sum(1 for v in px if v > 40) > max(80, OVER_MAX * len(px)):
                bad.add(name + " × obraz")
        if bad:
            over.setdefault(k, set()).update(bad)
    except Exception as e:
        print("kontrola prekrývania:", e)


def check(sc_data, cover, over=None, badic=None):
    """Kontrola pred zverejnením. Vráti {"ok", "why": [dôvody po slovensky], ...}.
    Neprejde: prázdna scéna, stroj bez presného modelu, priveľa scén len s ikonami či textom."""
    from . import auto_visual
    body = sc_data[:-1] if len(sc_data) > 2 else sc_data   # posledná scéna je výzva „pozri celé video“
    weak = [i + 1 for i, s in enumerate(body) if (s["v"] or {}).get("k") in auto_visual.WEAK]
    crude = sorted({str(s["v"].get("m") or "kresba") for s in body
                    if (s["v"].get("k") == "mech" and s["v"].get("m") not in auto_visual.PRECISE) or s["v"].get("k") == "svg"})
    empty = [i + 1 for i, c in sorted(cover.items()) if c < EMPTY_MIN]
    why = []
    if empty:
        why.append("Prázdna scéna: " + ", ".join(map(str, empty)))
    if crude:
        why.append("Stroj bez presného modelu: " + ", ".join(crude))
    for k, bad in sorted((over or {}).items()):
        why.append(f"Prekrývanie v scéne {k + 1}: " + ", ".join(sorted(bad)))
    if badic:
        why.append("Ikona nesedí k scéne: " + ", ".join(map(str, badic)))
    # krátke video má len 4–5 scén: jedna slabá scéna navyše (2 zo 4) ešte neznamená „len ikony“ (16.11.)
    if body and len(weak) / len(body) > (WEAK_MAX if len(body) > 8 else 0.5):
        why.append(f"Slabý obraz (len ikony alebo text) v {len(weak)} z {len(body)} scén")
    return {"ok": not why, "why": why, "scenes": len(sc_data), "weak": len(weak),
            "precise": sum(1 for s in body if s["v"].get("k") == "map" or (s["v"].get("k") == "mech" and s["v"].get("m") in auto_visual.PRECISE))}


def make(scenes, voice, out, accent="#FF6B00", lang="sk", text="", kicker="", music=None, font=None, fps=30,
         font_text=None, logo=None, logo_end=None, products=None, wide=False, thumb=None, thumb_text="", thumb_scene=None, loop=True, title="", guide=False, detail=1, check_only=False, thumb_only=False):
    """Vyrenderuje celé video: animované scény + titulky + hlas (+ hudba potichu).

    logo / logo_end = obrázky (data URI) do rohu a na záverečnú kartu; s logom sa video predĺži o TAIL sekúnd.
    products = {slovo: cesta k obrázku produktu s priehľadným pozadím}."""
    from . import anim, media
    if not anim.available():
        raise RuntimeError("Animácie sa ešte pripravujú (Chromium sa sťahuje)")
    if thumb_only:   # len náhľadový obrázok (napr. nový vzhľad pre už nahraté video): bez hlasu, bez skladania videa
        check_only = True
    if check_only and not voice:   # rýchla kontrola scenára bez hlasu a bez skladania videa: len kontrolné snímky, vráti výsledok kontroly
        ws = (text or "").split() or ["."]
        total = max(10.0, len(ws) / 2.7)
        words = [{"w": w, "s": i * total / len(ws), "e": (i + .8) * total / len(ws)} for i, w in enumerate(ws)]
    else:
        total = media.duration(voice) or 10
        words = media.word_times(voice, text)
    times = timeline(scenes, words, total)
    sc_data, pcache, used, prev, badic = [], {}, {}, None, []
    seen_mech = set()
    from . import auto_visual
    # stroj, o ktorom je celé video (ak má presný model): podľa názvu videa, inak podľa toho, čo v texte prevláda
    topic = auto_visual.topic(" . ".join([text] + [f"{sc.get('onscreen') or ''} . {sc.get('visual') or ''}" for sc in scenes]), title, strict=True)
    for i, (sc, (t0, t1)) in enumerate(zip(scenes, times)):
        spoken = " ".join(w["w"] for w in words if t0 - .05 <= w["s"] < t1)
        b0 = board_of(sc, lang)
        if not topic and (b0.get("k") == "svg" or (b0.get("k") == "mech" and b0.get("m") not in auto_visual.PRECISE)):
            # kresba od AI či stará hrubá schéma sa neukazuje: video nie je o stroji s presným modelom, scéna dostane obraz odhadnutý z textu
            b0 = guess(sc.get("onscreen") or "", sc.get("visual") or "", lang)
        v = auto_visual.upgrade(b0, sc, spoken, used, lang, prev, long=len(scenes) > 12, full=text,
                                topic=topic, last=i == len(scenes) - 1 and len(scenes) > 2)
        prev = v.get("m") if v.get("k") == "mech" else None
        v = prepare(v, lang)
        if v.get("k") == "text" and not str(v.get("w") or "").strip():   # mapa, ktorú sa nepodarilo nájsť, či iný obraz bez obsahu: nikdy prázdna scéna
            v = prepare(guess(sc.get("onscreen") or "", "", lang), lang)
            if v.get("k") == "text" and not str(v.get("w") or "").strip():
                v = {"k": "text", "w": str(sc.get("onscreen") or sc.get("visual") or "")[:60]}
        if v.get("k") == "mech":  # réžia: dĺžka scény a úvodný záber „kde to je“ len pri prvom výskyte stroja
            v = dict(v, _dur=round(t1 - t0, 2), **({} if v.get("m") in seen_mech else {"_in": 1}), **({"_first": 1} if i == 0 else {}))
            seen_mech.add(v.get("m"))
            fs = auto_visual.shots(v, [w for w in words if t0 - .05 <= w["s"] < t1], t0)
            if fs:   # hlas v scéne prejde cez viac častí: kamera ide za ním
                v = dict(v, fs=fs)
            if v.get("m") in auto_visual.PRECISE and not v.get("c"):   # číslo, ktoré hlas povie, naskočí pri modeli
                c = auto_visual.callout(sc.get("onscreen"), [w for w in words if t0 - .05 <= w["s"] < t1], t0)
                if c:
                    if c["t"] is None:
                        c["t"] = round((t1 - t0) * .45, 2)
                    v = dict(v, c=c)
        h = (sc.get("onscreen") or "").strip()
        v = with_product(h, v, products, pcache)
        if v.get("k") == "text" and re.sub(r"\W", "", str(v.get("w", "")).lower()) == re.sub(r"\W", "", h.lower()):
            h = ""  # rovnaký text ako nadpis: ukáž ho len raz, veľkým
        sc_data.append({"h": h, "v": v, "t0": round(t0, 3), "t1": round(t1, 3),
                        "steps": STEPS.get(v.get("k"), lambda d: 2)(v)})
        if lang == "en" and auto_visual.bad_icons(v, f"{sc.get('onscreen') or ''} . {sc.get('visual') or ''} . {spoken}"):
            badic.append(i + 1)   # poistka: ikona, ktorá nesedí k scéne, sa nesmie dostať von (kontrola video nepustí)
    if guide:
        fox_moods(scenes, sc_data, words)
    loop = bool(loop and not wide and len(sc_data) > 2)   # krátke video: koniec nadviaže na začiatok (bez záverečnej karty, logo ostáva v rohu)
    tail = 0 if loop else TAIL if (logo_end or logo) else 0
    data = {"acc": accent, "lang": lang, "kicker": kicker, "total": total, "scenes": sc_data, "caps": caption_chunks(words, lang, wide),
            "logo": logo or "", "logoEnd": "" if loop else logo_end or "", "tail": tail, "wide": bool(wide), "guide": bool(guide), "detail": int(detail or 1),
            "loop": loop, "len": round(total + (0.6 if loop else tail or 0.3), 3)}
    vw, vh = (H, W) if wide else (W, H)
    html = page(data, font, font_text)
    if total > 90:
        fps = 25
    length = data["len"]
    n = int(length * fps)
    ff = media.ffmpeg()
    cmd = [ff, "-y", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-", "-i", str(voice)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        af = ["-filter_complex", f"[1:a]apad[v];[2:a]volume=0.10,afade=t=out:st={max(0, length - 1.2):.2f}:d=1.2[m];"
              "[v][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]", "-map", "0:v", "-map", "[a]"]
    else:
        af = ["-map", "0:v", "-map", "1:a", "-af", "apad"]
    cmd += af + ["-t", f"{length:.2f}", *media.h264(20), "-pix_fmt", "yuv420p", "-r", str(fps),
                 "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    probe = {min(n - 1, int((d["t0"] + (min(d["t1"], total) - d["t0"]) * .7) * fps)): k for k, d in enumerate(sc_data)}
    probe2 = {min(n - 1, int((d["t0"] + (min(d["t1"], total) - d["t0"]) * .32) * fps)): k for k, d in enumerate(sc_data)}
    # záverečný odjazd kamery (prehľad všetkých scén naraz) je zámerný: počas neho sa prekrývanie nemeria, inak padne skoro každé dlhé video na poslednej scéne
    ld = sc_data[-1]["t1"] - sc_data[-1]["t0"] if sc_data else 0
    zo0 = total - min(3.2, max(1.8, ld * .5)) if len(sc_data) > 2 and not loop else 1e9
    job = {"html": html, "vw": vw, "vh": vh, "cmd": cmd, "n": n, "fps": fps, "check_only": bool(check_only), "wide": bool(wide),
           "probe": probe, "probe2": probe2, "zo0": zo0, "thumb": str(thumb) if thumb and (thumb_only or not check_only) else "", "thumb_only": bool(thumb_only),
           "thumb_text": (thumb_text or "").strip(), "thumb_i": thumb_index(scenes, sc_data, thumb_scene) if (thumb_text or "").strip() and sc_data else None,
           "thumb_t": min(2.6, max(0.5, sc_data[0]["t1"] - 0.3) if sc_data else 2.6)}
    if job["thumb"] and job["thumb_i"] is not None:   # náhľad: stroj celý, bez jazdy kamery po detailoch (scéna inak končí na detaile)
        ti = job["thumb_i"]
        sd2 = [dict(d, v={k: x for k, x in (d.get("v") or {}).items() if k not in ("fs", "_in", "c")}) if n == ti else d for n, d in enumerate(sc_data)]
        job["thumb_html"] = page(dict(data, scenes=sd2), font, font_text)
    with _lock:
        cover, over = capture_job(job)
    if thumb_only:
        return str(thumb) if thumb and Path(str(thumb)).exists() else None
    if check_only:
        return check(sc_data, cover, over, badic)
    EVENTS[str(out)] = auto_visual.sound_events(sc_data)   # zvuky k obrazu (domieša audio.finish)
    QA[str(out)] = check(sc_data, cover, over, badic)
    if _all_black(out, length):
        raise RuntimeError("Video vyšlo celé čierne, skús ho vyrobiť znova")
    return str(out)


def _capture(job):
    """Snímky z prehliadača do ffmpeg + kontrolné snímky. Vráti (cover, over).
    Beží v samostatnom procese s nižšou prioritou (render_child), aby skladanie videí nebrzdilo appku."""
    import os
    from playwright.sync_api import sync_playwright
    cmd, n, fps, check_only, wide = job["cmd"], job["n"], job["fps"], job["check_only"], job["wide"]
    vw, vh, html, thumb = job["vw"], job["vh"], job["html"], job["thumb"]
    probe, probe2, zo0 = job["probe"], job["probe2"], job["zo0"]
    cover, over = {}, {}
    with sync_playwright() as pw:
        exe = os.environ.get("SM_CHROMIUM")
        b = pw.chromium.launch(executable_path=exe, args=CANVAS_ARGS) if exe else pw.chromium.launch(args=CANVAS_ARGS)
        proc = None if check_only else subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        try:
            if thumb:  # náhľadový obrázok: veľký krátky text + najsilnejší obraz (bez neho úvodná scéna s názvom)
                tp = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1)  # vlastná stránka, video ostane čisté
                try:
                    tp.set_content(job.get("thumb_html") or html)
                    tp.wait_for_function("window.READY===true", timeout=20000)
                    if job["thumb_i"] is not None:
                        tp.evaluate("([i,t])=>thumbMode(i,t)", [job["thumb_i"], job["thumb_text"]])
                    else:
                        tp.evaluate("renderAt(%.2f);document.getElementById('cap').innerHTML='';document.getElementById('bar').style.width=0"
                                    % job["thumb_t"])
                    tp.screenshot(path=thumb, type="jpeg", quality=92)
                except Exception as e:
                    print("náhľad:", e)
                finally:
                    tp.close()
            if job.get("thumb_only"):
                return cover, over
            pg = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1)
            pg.set_content(html)
            pg.wait_for_function("window.READY===true", timeout=20000)
            for i in range(n):
                if check_only and i not in probe and i not in probe2:
                    continue
                pg.evaluate(f"renderAt({i / fps:.4f})")
                shot = pg.screenshot(type="jpeg", quality=90)
                if i in probe:   # jedna snímka z každej scény na kontrolu pred zverejnením
                    cover[probe[i]] = _coverage(shot, wide)
                if (i in probe or i in probe2) and i / fps < zo0:   # dve snímky z každej scény: neleží niečo cez seba?
                    _overlap(pg, over, probe.get(i, probe2.get(i)))
                if proc:
                    proc.stdin.write(shot)
            if proc:
                proc.stdin.close()
                err = proc.stderr.read().decode(errors="ignore")
                if proc.wait() != 0:
                    raise RuntimeError("ffmpeg: " + err[-400:])
        finally:
            if proc and proc.poll() is None:
                proc.kill()
            b.close()
    return cover, over


def _render_dir():
    d = Path(db.DATA_DIR) / "render_jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _job_key(job):
    """Rovnaké video = rovnaký kľúč (bez ciest výstupu), aby appka po reštarte našla rozrobené skladanie."""
    import hashlib
    import pickle
    j = dict(job, cmd=list(job["cmd"][:-1]), thumb=bool(job.get("thumb")))
    return hashlib.sha1(pickle.dumps(sorted(j.items(), key=lambda kv: kv[0]), protocol=4)).hexdigest()[:20]


def _alive(pid):
    import os
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def capture_job(job):
    """Skladanie v samostatnom procese s nižšou prioritou: appka (stránky, plánovač) ostane svižná aj pri 4 videách naraz.
    17.11.: proces beží nezávisle od appky. Keď sa appka reštartuje (aktualizácia), skladanie pokračuje
    a nová appka si hotové video prevezme (rovnaký kľúč úlohy), nič sa neskladá znova.
    Keď sa samostatný proces nedá spustiť (nečakaná chyba prostredia), poskladá sa to postaru priamo v appke."""
    import os
    import pickle
    import shutil
    import sys
    import time as _t
    if db.get_setting("render_inproc", False):
        return _capture(job)
    if job.get("check_only"):
        return _capture_child(job)
    d = _render_dir() / _job_key(job)
    d.mkdir(exist_ok=True)
    (d / "claimed").write_text(str(os.getpid()))
    res_path, vid, th = d / "res.pkl", d / "video.mp4", d / "thumb.jpg"
    out, thumb = job["cmd"][-1], job.get("thumb") or ""

    def take():
        res = pickle.loads(res_path.read_bytes())
        if isinstance(res, dict) and "error" in res:
            raise RuntimeError(res["error"])
        if not (isinstance(res, dict) and "cover" in res and vid.exists()):
            return None
        shutil.move(str(vid), out)
        if thumb and th.exists():
            shutil.move(str(th), thumb)
        shutil.rmtree(d, ignore_errors=True)
        return res["cover"], res["over"]

    try:
        pid = int((d / "pid").read_text()) if (d / "pid").exists() else 0
    except Exception:
        pid = 0
    if not res_path.exists() and not (pid and _alive(pid)):
        for f in (res_path, vid, th):
            try:
                f.unlink()
            except OSError:
                pass
        job2 = dict(job, cmd=list(job["cmd"][:-1]) + [str(vid)], thumb=str(th) if thumb else "")
        proc = subprocess.Popen([sys.executable, "-m", "app.render_child", str(res_path)], stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(db.BASE_DIR), start_new_session=True)
        (d / "pid").write_text(str(proc.pid))
        proc.stdin.write(pickle.dumps(job2))
        proc.stdin.close()
        pid = proc.pid
        t0 = _t.time()
        while proc.poll() is None and _t.time() - t0 < 4 * 3600:
            _t.sleep(3)
    else:   # skladanie začala predošlá appka a ešte beží: počkaj naň
        t0 = _t.time()
        while not res_path.exists() and pid and _alive(pid) and _t.time() - t0 < 4 * 3600:
            (d / "claimed").write_text(str(os.getpid()))
            _t.sleep(5)
        _t.sleep(1)
    try:
        r = take() if res_path.exists() else None
    except RuntimeError:
        shutil.rmtree(d, ignore_errors=True)
        raise
    except Exception:
        r = None
    if r:
        return r
    shutil.rmtree(d, ignore_errors=True)
    print("samostatné skladanie nefungovalo, skladám v appke")
    return _capture(job)


def _capture_child(job):
    """Kontrola vopred (len pár snímok): krátka, beží ako dieťa appky."""
    import os
    import pickle
    import sys
    import tempfile
    fd, res_path = tempfile.mkstemp(suffix=".render")
    os.close(fd)
    try:
        r = subprocess.run([sys.executable, "-m", "app.render_child", res_path], input=pickle.dumps(job),
                           cwd=str(db.BASE_DIR), capture_output=True, timeout=4 * 3600)
        try:
            res = pickle.loads(Path(res_path).read_bytes())
        except Exception:
            res = None
        if isinstance(res, dict) and "error" in res:
            raise RuntimeError(res["error"])
        if isinstance(res, dict) and "cover" in res:
            return res["cover"], res["over"]
        print("samostatné skladanie nefungovalo, skladám v appke:", (r.stderr or b"").decode(errors="ignore")[-600:])
    finally:
        try:
            os.unlink(res_path)
        except OSError:
            pass
    return _capture(job)


def render_jobs_cleanup(started):
    """Po štarte appky: rozrobené skladanie, ktoré si nová appka do 20 minút neprevzala (video už nikto nechce),
    sa zastaví; staré zvyšky sa zmažú."""
    import os
    import shutil
    import signal
    import time as _t
    try:
        base = _render_dir()
    except Exception:
        return
    for d in base.iterdir():
        try:
            cl = d / "claimed"
            claimed_now = cl.exists() and cl.stat().st_mtime >= started
            pid = int((d / "pid").read_text()) if (d / "pid").exists() else 0
            if pid and _alive(pid) and not claimed_now:
                try:
                    os.killpg(pid, signal.SIGTERM)
                except Exception:
                    os.kill(pid, signal.SIGTERM)
                shutil.rmtree(d, ignore_errors=True)
            elif not (pid and _alive(pid)) and _t.time() - d.stat().st_mtime > 6 * 3600:
                shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass


def _all_black(path, length):
    """Poistka: pár snímok z hotového videa; keď sú všetky čierne, video je pokazené."""
    from . import media
    ff = media.ffmpeg()
    if not ff:
        return False
    try:
        mx = 0
        for t in (length * 0.2, length * 0.5, length * 0.8):
            r = subprocess.run([ff, "-ss", f"{t:.1f}", "-i", str(path), "-frames:v", "1", "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YMAX",
                                "-f", "null", "-"], capture_output=True, text=True, errors="ignore", timeout=60, stdin=subprocess.DEVNULL)
            m = re.findall(r"YMAX=(\d+)", r.stderr + r.stdout)
            if not m:
                return False
            mx = max(mx, int(m[-1]))
        return mx < 40
    except Exception:
        return False


def preview(d, out_png, accent="#FF6B00", lang="sk", title="Ukážka", at=6.0):
    """Jeden obrázok diagramu (na test/náhľad)."""
    d = prepare(d, lang)
    data = {"acc": accent, "lang": lang, "kicker": "", "total": 10, "caps": [],
            "scenes": [{"h": title, "v": d, "t0": 0, "t1": 10, "steps": STEPS.get(d.get("k"), lambda x: 2)(d)}]}
    import os
    from playwright.sync_api import sync_playwright
    with _lock, sync_playwright() as pw:
        exe = os.environ.get("SM_CHROMIUM")
        b = pw.chromium.launch(executable_path=exe, args=CANVAS_ARGS) if exe else pw.chromium.launch(args=CANVAS_ARGS)
        try:
            pg = b.new_page(viewport={"width": W, "height": H})
            pg.set_content(page(data))
            pg.wait_for_function("window.READY===true", timeout=20000)
            pg.evaluate(f"renderAt({at})")
            pg.screenshot(path=str(out_png))
        finally:
            b.close()
    return str(out_png)
