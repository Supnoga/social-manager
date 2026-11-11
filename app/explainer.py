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

from . import db

W, H = 1080, 1920
KINDS = ("flow", "cycle", "bars", "calc", "compare", "count", "list", "icons", "temp", "house", "split", "text")
ICON_NAMES = ("house", "heatpump", "radiator", "floor", "thermo", "snow", "sun", "flame", "bolt", "drop", "coin",
              "leaf", "air", "phone", "tank", "sound", "clock", "plug", "check", "cross", "user", "tool", "chart", "shield")

# Stručný popis pre AI (pridá sa do promptu scenára, cca 200 tokenov)
SPEC = """"anim" = animated explainer diagram for the scene (N2N Academy style: black, thin line schematics drawn step by step). Pick ONE that explains the point visually:
{"t":"board","d":{"k":"flow","a":"input e.g. Electricity 1 kW","b":"device","c":"output e.g. Heat 4 kW","x":"optional extra input e.g. Air 3 kW"}} |
{"k":"cycle","l":["outdoor air","evaporator","compressor","condenser","home"]} (how a heat pump works) |
{"k":"bars","u":"unit","i":[["label",number],...max 4]} | {"k":"calc","r":[["1 600 m³ × 10,5","16 800 kWh"],...max 4]} |
{"k":"compare","a":["worse option","value"],"b":["better option","value"]} | {"k":"count","v":75,"pre":"","suf":" %","l":"label"} |
{"k":"list","i":["short point",...max 4]} | {"k":"icons","i":[["icon","label"],...2-4]} icons: """ + ",".join(ICON_NAMES) + """ |
{"k":"temp","a":["Outside",-10],"b":["Inside",21],"u":"°C"} | {"k":"house","i":[["Roof",25],["Walls",35],["Windows",15],["Floor",10]]} (heat losses %) |
{"k":"split","u":"%","i":[["from air",75],["electricity",25]]} | {"k":"text","w":"2-5 key words"}
Labels max 4 words, numbers as numbers."""


# ---------- texty na preklad (rovnaké poradie pre texts/with_texts) ----------
def _slots(d):
    """Zoznam (cesta) k textom v diagrame. Čísla sa neprekladajú."""
    k, out = d.get("k"), []
    for f in ("a", "b", "c", "x", "l", "w", "u", "pre", "suf"):
        v = d.get(f)
        if isinstance(v, str) and v.strip() and not (f in ("u", "pre", "suf") and not re.search(r"[^\W\d_]{4,}", v)):
            out.append((f,))
        elif isinstance(v, list) and f in ("a", "b") and v and isinstance(v[0], str):
            out.append((f, 0))
            if len(v) > 1 and isinstance(v[1], str) and re.search(r"[^\W\d_]{2,}", v[1]):
                out.append((f, 1))
        elif isinstance(v, list) and f == "l":
            out += [(f, i) for i, x in enumerate(v) if isinstance(x, str) and x.strip()]
    for f in ("i", "r"):
        for i, x in enumerate(d.get(f) or []):
            if isinstance(x, str):
                out.append((f, i))
            elif isinstance(x, list):
                for j, y in enumerate(x):
                    if isinstance(y, str) and y.strip() and not (k == "icons" and j == 0) and (
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
    (r"€|eur|úspor|ušetr|cena|cien|náklad|platí|faktúr|price|cost|kosten|spar", "coin"),
    (r"zim|mráz|chlad|-\s?\d+\s?°|winter|cold|frost|kalt", "snow"),
    (r"leto|slnk|solár|fotovolt|summer|sun|solar|sonne", "sun"),
    (r"plyn|gas|kotol|boiler|kessel|drev|pelet", "flame"),
    (r"elektr|prúd|kwh|strom|electric|power", "bolt"),
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


def guess(onscreen, visual=""):
    """Bez AI: z textu scény urobí jednoduchý diagram (ikony alebo číslo)."""
    txt = f"{onscreen} {visual}".lower()
    icons = []
    for rx, name in KEYWORDS:
        if re.search(rx, txt) and name not in icons:
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


def board_of(scene):
    a = scene.get("anim")
    d = from_old(a, scene.get("onscreen", "")) if isinstance(a, dict) else None
    if not d or d.get("k") not in KINDS:
        d = guess(scene.get("onscreen", ""), scene.get("visual", ""))
    return d


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
For each scene choose an animated diagram. {SPEC}
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
def timeline(scenes, words, total):
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


def caption_chunks(words, lang):
    maxc = 26 if lang in ("de", "fi", "hu", "nl", "et", "is") else 32
    out, cur = [], []
    for w in words:
        if cur and (len(" ".join(x["w"] for x in cur + [w])) > maxc or cur[-1]["w"][-1:] in ".!?…,;:"):
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
def page(data, font=None):
    fcss = ""
    if font:
        import base64
        from pathlib import Path
        if Path(font).exists():
            b64 = base64.b64encode(Path(font).read_bytes()).decode()
            fcss = (f"@font-face{{font-family:BrandF;src:url(data:font/{Path(font).suffix.lstrip('.').lower()};base64,{b64})}}"
                    ":root{--f:BrandF,var(--f0)}")
    return (TEMPLATE.replace("/*FONT*/", fcss)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{--f0:'Helvetica Neue','SF Pro Display',-apple-system,'Inter','Segoe UI',Arial,sans-serif;--f:var(--f0);--acc:#FF6B00;--g:#8a8a8a;--line:rgba(255,255,255,.85)}
/*FONT*/
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:#000;overflow:hidden;font-family:var(--f);color:#fff;-webkit-font-smoothing:antialiased}
#glow{position:absolute;width:1300px;height:1300px;border-radius:50%;background:radial-gradient(circle,var(--acc) 0%,transparent 62%);opacity:.0;left:420px;top:900px}
.sc{position:absolute;inset:0;display:none}
.kick{position:absolute;left:72px;top:318px;font-size:25px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:#cfcfcf;white-space:nowrap}
.kick b{color:var(--acc)}
.ttl{position:absolute;left:72px;top:362px;width:860px;font-size:82px;line-height:1.02;font-weight:800;text-transform:uppercase;letter-spacing:-1px;hyphens:auto;-webkit-hyphens:auto;overflow-wrap:break-word}
.ttl .w{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.08em;margin-bottom:-.08em}
.ttl .w>span{display:inline-block}
.viz{position:absolute;left:72px;top:690px;width:864px;height:560px}
.lab{position:absolute;font-size:26px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#bdbdbd;line-height:1.2}
.lab.a{color:var(--acc)}
.txt{position:absolute;font-size:38px;line-height:1.2;color:#fff}
.big{position:absolute;font-weight:800;letter-spacing:-1px;line-height:1}
.card{position:absolute;border:1.5px solid rgba(255,255,255,.16);background:#0d0d0d;border-radius:14px}
svg{position:absolute;left:0;top:0;overflow:visible}
svg .d{fill:none;stroke-linecap:round;stroke-linejoin:round}
#cap{position:absolute;left:72px;width:864px;top:1300px;text-align:center;font-size:56px;font-weight:700;line-height:1.18;color:#fff;text-shadow:0 4px 24px #000}
#cap span{color:rgba(255,255,255,.55)}#cap span.on{color:#fff}#cap span.k{color:var(--acc)}
#bar{position:absolute;left:0;top:1906px;height:14px;background:var(--acc);width:0}
</style></head><body><div id="glow"></div><div id="root"></div><div id="cap"></div><div id="bar"></div>
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
const ICONS={
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
shield:'<path d="M50 10 L82 22 V46 C82 68 68 82 50 90 C32 82 18 68 18 46 V22 Z"/><path d="M36 50 L46 60 L66 38"/>'};
function icon(name,size,col,sw){const s=svg(size,size,'');s.setAttribute('viewBox','0 0 100 100');s.innerHTML=(ICONS[name]||ICONS.check).replace(/<(path|rect|circle)/g,'<$1 class="d" pathLength="1"');s.style.color=col||'#fff';s.querySelectorAll('.d').forEach(p=>{p.setAttribute('stroke','currentColor');p.setAttribute('stroke-width',sw||3.2)});return s}
function draw(s,p){s.querySelectorAll('.d').forEach(d=>{d.style.strokeDasharray='1 1';d.style.strokeDashoffset=1-cl(p)})}
function show(e,p,dy){e.style.opacity=cl(p);e.style.transform=`translateY(${(1-E(p))*(dy==null?24:dy)}px)`}
// ---------- diagramy ----------
const V={};
V.flow=(v,d)=>{const X=432;const s=svg(864,560,`
<path class="d in" pathLength="1" d="M${X} 92 V184" stroke="#fff" stroke-width="3"/><path class="d ina" d="M${X-14} 168 L${X} 186 L${X+14} 168" stroke="#fff" stroke-width="3"/>
<rect class="d box" pathLength="1" x="${X-230}" y="196" width="460" height="128" rx="14" stroke="#fff" stroke-width="3"/>
<path class="d ex" pathLength="1" d="M846 260 H${X+246}" stroke="#7fc8ff" stroke-width="3"/><path class="d exa" d="M${X+262} 246 L${X+244} 260 L${X+262} 274" stroke="#7fc8ff" stroke-width="3"/>
<path class="d out" pathLength="1" d="M${X} 336 V452" stroke="var(--acc)" stroke-width="12"/><path class="d outa" d="M${X-34} 420 L${X} 460 L${X+34} 420" stroke="var(--acc)" stroke-width="12"/>`);v.append(s);
const a=el('div','txt',`left:132px;top:20px;width:600px;text-align:center;font-weight:700`,esc(d.a)),b=el('div','big',`left:${X-220}px;top:206px;width:440px;height:108px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:44px;text-transform:uppercase`,esc(d.b)),
c=el('div','big',`left:32px;top:478px;width:800px;text-align:center;color:var(--acc);font-size:64px`,esc(d.c)),x=el('div','lab',`left:${X+250}px;top:150px;width:200px;color:#7fc8ff;text-align:center`,esc(d.x||''));
v.append(a,b,c,x);fit(a,40,26,96,600);fit(b,46,26,108,430);fit(c,66,34,80,800);fit(x,26,18,96,200);
const ins=s.querySelector('.in'),ina=s.querySelector('.ina'),box=s.querySelector('.box'),ex=s.querySelector('.ex'),exa=s.querySelector('.exa'),out=s.querySelector('.out'),outa=s.querySelector('.outa');
[ina,exa,outa].forEach(p=>p.setAttribute('pathLength','1'));if(!d.x){ex.remove();exa.remove()}
return (t,st)=>{show(a,st(0,.5));ins.style.strokeDasharray='1 1';ins.style.strokeDashoffset=1-st(.25,.6);ina.style.strokeDasharray='1 1';ina.style.strokeDashoffset=1-st(.7,.3);
box.style.strokeDasharray='1 1';box.style.strokeDashoffset=1-st(1,.8);show(b,st(1.4,.5));
if(d.x){ex.style.strokeDasharray='1 1';ex.style.strokeDashoffset=1-st(2,.6);exa.style.strokeDasharray='1 1';exa.style.strokeDashoffset=1-st(2.5,.3);show(x,st(2,.5),0)}
const o=st(d.x?3:2,.6);out.style.strokeDasharray='1 1';out.style.strokeDashoffset=1-o;outa.style.strokeDasharray='1 1';outa.style.strokeDashoffset=1-st(d.x?3.4:2.4,.3);show(c,st(d.x?3.4:2.4,.6))}};
V.cycle=(v,d)=>{const L=d.l||[];const P='M210 300 V170 Q210 110 270 110 H594 Q654 110 654 170 V430 Q654 490 594 490 H270 Q210 490 210 430 Z';
const s=svg(864,560,`<path class="d loopc" pathLength="1" d="M210 300 V170 Q210 110 270 110 H432" stroke="#7fc8ff" stroke-width="5"/>
<path class="d looph" pathLength="1" d="M432 110 H594 Q654 110 654 170 V430 Q654 490 594 490 H432" stroke="var(--acc)" stroke-width="5"/>
<path class="d loopc2" pathLength="1" d="M432 490 H270 Q210 490 210 430 V300" stroke="#7fc8ff" stroke-width="5"/>
<g class="n1"><rect x="180" y="240" width="60" height="120" rx="8" fill="#000" stroke="#7fc8ff" stroke-width="4"/><path d="M190 256 H230 M190 276 H230 M190 296 H230 M190 316 H230 M190 336 H230" stroke="#7fc8ff" stroke-width="3"/></g>
<g class="n2"><circle cx="432" cy="110" r="40" fill="#000" stroke="#fff" stroke-width="4"/><path d="M412 124 L452 96 M420 100 L444 100 L444 122" stroke="#fff" stroke-width="4" fill="none"/></g>
<g class="n3"><rect x="624" y="240" width="60" height="120" rx="8" fill="#000" stroke="var(--acc)" stroke-width="4"/><path d="M634 256 H674 M634 276 H674 M634 296 H674 M634 316 H674 M634 336 H674" stroke="var(--acc)" stroke-width="3"/></g>
<g class="n4"><path d="M402 470 L462 510 V470 L402 510 Z" fill="#000" stroke="#fff" stroke-width="4"/></g>
<g class="air"><path d="M10 250 H150 M10 300 H170 M10 350 H150" stroke="#7fc8ff" stroke-width="3" stroke-dasharray="14 12" class="aird"/><path d="M156 286 L172 300 L156 314" stroke="#7fc8ff" stroke-width="3" fill="none"/></g>
<g class="heat"><path d="M694 300 H760" stroke="var(--acc)" stroke-width="6" stroke-dasharray="16 10" class="heatd"/></g>
<g class="dots"></g>`);v.append(s);
const hi=icon('house',96,'#fff',3.6);hi.style.left='768px';hi.style.top='252px';v.append(hi);
const path=document.createElementNS(SVGNS,'path');path.setAttribute('d',P);const len=path.getTotalLength?null:null;s.append(path);path.style.display='none';
const lab=(i,css,a)=>{const e=el('div','lab'+(a?' a':''),css,esc(L[i]||''));v.append(e);fit(e,24,14,96);return e};
const l0=lab(0,'left:0;top:180px;width:190px;color:#7fc8ff'),l1=lab(1,'left:252px;top:250px;width:170px;color:#7fc8ff'),l2=lab(2,'left:300px;top:20px;width:264px;text-align:center'),l3=lab(3,'left:442px;top:250px;width:170px;text-align:right',1),l4=lab(4,'left:720px;top:360px;width:144px;text-align:center',1);
const g=k=>s.querySelector(k);const dots=g('.dots');const NDOT=14;for(let i=0;i<NDOT;i++){const c=document.createElementNS(SVGNS,'circle');c.setAttribute('r',7);dots.append(c)}
const tot=path.getTotalLength();
return (t,st)=>{const a=st(0,1.2);['.loopc','.looph','.loopc2'].forEach((k,i)=>{const p=g(k);p.style.strokeDasharray='1 1';p.style.strokeDashoffset=1-cl(a*3-i)});
g('.air').style.opacity=st(.6,.5);g('.aird').style.strokeDashoffset=-t*60;show(l0,st(.6,.5),0);
g('.n1').style.opacity=st(1.2,.4);show(l1,st(1.2,.5),0);g('.n2').style.opacity=st(2,.4);show(l2,st(2,.5),0);
g('.n3').style.opacity=st(2.8,.4);show(l3,st(2.8,.5),0);g('.n4').style.opacity=st(2.8,.4);
g('.heat').style.opacity=st(3.4,.5);g('.heatd').style.strokeDashoffset=-t*70;hi.style.opacity=st(3.4,.5);draw(hi,st(3.4,1));show(l4,st(3.6,.5),0);
const on=st(1.2,.6);[...dots.children].forEach((c,i)=>{const u=((i/NDOT)+t*0.09)%1;const pt=path.getPointAtLength(u*tot);c.setAttribute('cx',pt.x);c.setAttribute('cy',pt.y);
const hot=pt.y<112&&pt.x>432||pt.x>640||pt.y>480&&pt.x>432;c.setAttribute('fill',hot?D.acc:'#7fc8ff');c.style.opacity=on})}};
V.bars=(v,d)=>{const I=(d.i||[]).slice(0,4);const n=I.length||1,max=Math.max(...I.map(x=>N(x[1])),1),bw=Math.min(170,680/n),gap=(864-bw*n)/(n+1);
const base=440,mh=360;const s=svg(864,560,`<path class="d ax" pathLength="1" d="M0 ${base} H864" stroke="#fff" stroke-width="3"/>`);v.append(s);
const it=I.map((x,i)=>{const L=gap+i*(bw+gap),last=i==n-1;const r=el('div','',`position:absolute;left:${L}px;width:${bw}px;bottom:${560-base}px;height:0;background:${last?'var(--acc)':i%2?'#e9e9e9':'#3b3b3b'}`);
const val=el('div','big',`left:${L-40}px;width:${bw+80}px;text-align:center;font-size:40px;${last?'color:var(--acc)':''}`);const lb=el('div','lab',`left:${L-30}px;width:${bw+60}px;top:${base+18}px;text-align:center`,esc(x[0]));
v.append(r,val,lb);fit(lb,24,15,62);return {r,val,lb,v:N(x[1]),h:N(x[1])/max*mh,dec:decs(x[1])}});
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
const n=el('div','big',`left:0;top:165px;width:864px;height:170px;display:flex;align-items:center;justify-content:center;font-size:150px`),l=el('div','lab',`left:182px;top:500px;width:500px;text-align:center;font-size:28px`,esc(d.l||''));v.append(n,l);fit(l,28,18,60);
const dec=decs(d.v);return (t,st)=>{const p=st(0,1.6);const r=s.querySelector('.ring');r.style.strokeDasharray='1 1';r.style.strokeDashoffset=1-(pct?Math.min(1,Math.abs(val)/100):1)*E(p);
n.innerHTML=esc(d.pre||'')+'<span style="color:var(--acc)">'+NF(val*E(p),dec)+'</span>'+esc(d.suf||'');fit(n,150,50,999,400);show(l,st(1,.6))}};
V.list=(v,d)=>{const I=(d.i||[]).slice(0,4);const rh=Math.min(130,540/Math.max(1,I.length));const rows=I.map((x,i)=>{const r=el('div','',`position:absolute;left:0;top:${i*rh}px;width:864px;height:${rh-16}px;display:flex;align-items:center;gap:28px`);
r.innerHTML=`<div style="flex:none;color:var(--acc);font-weight:800;font-size:54px;width:52px">${i+1}</div><div class="it" style="flex:none;width:780px;font-weight:800;text-transform:uppercase;font-size:44px;line-height:1.08">${esc(x)}</div>`;v.append(r);fit(r.querySelector('.it'),44,24,rh-16,780);return r});
return (t,st)=>rows.forEach((r,i)=>{const p=st(i*1,.6);r.style.opacity=p;r.style.transform=`translateX(${(1-E(p))*-50}px)`})};
V.icons=(v,d)=>{const I=(d.i||[]).slice(0,4);const n=I.length||1;const sz=n>3?150:190,step=864/n;const s=svg(864,560,'');v.append(s);
const items=I.map((x,i)=>{const cx=step*i+step/2;const ic=icon(x[0],sz,i==n-1?D.acc:'#fff',3);ic.style.left=(cx-sz/2)+'px';ic.style.top=(240-sz/2)+'px';v.append(ic);
const lb=el('div','lab',`left:${cx-step/2+6}px;width:${step-12}px;top:${250+sz/2+24}px;text-align:center;${i==n-1?'color:var(--acc)':''}`,esc(x[1]||''));v.append(lb);fit(lb,26,16,92);
let ar=null;if(i<n-1){ar=document.createElementNS(SVGNS,'path');ar.setAttribute('d',`M${cx+sz/2+10} 240 H${cx+step-sz/2-10}`);ar.setAttribute('stroke','#777');ar.setAttribute('stroke-width','3');ar.setAttribute('stroke-dasharray','10 9');s.append(ar)}return {ic,lb,ar}});
return (t,st)=>items.forEach((o,i)=>{const p=st(i*1.1,1);draw(o.ic,p);o.ic.style.opacity=p>0?1:0;show(o.lb,st(i*1.1+.4,.5),0);if(o.ar){o.ar.style.opacity=st(i*1.1+.8,.4);o.ar.style.strokeDashoffset=-t*40}})};
V.temp=(v,d)=>{const A=d.a||['',0],B=d.b||['',0],u=d.u||'°C';const va=N(A[1]),vb=N(B[1]);const lo=Math.min(va,vb,0)-5,hi=Math.max(va,vb)+5;const Y=v=>440-(v-lo)/(hi-lo)*380;
const th=(x,col)=>`<path d="M${x-22} 60 A22 22 0 0 1 ${x+22} 60 V430 A38 38 0 1 1 ${x-22} 430 Z" stroke="#fff" stroke-width="3" fill="none"/><circle cx="${x}" cy="462" r="26" fill="${col}"/>`;
const s=svg(864,560,th(220,'#7fc8ff')+th(644,'var(--acc)')+`<rect class="fa" x="208" width="24" fill="#7fc8ff"/><rect class="fb" x="632" width="24" fill="var(--acc)"/><path class="dt" d="" stroke="#fff" stroke-width="3" stroke-dasharray="8 8" fill="none"/>`);v.append(s);
const la=el('div','lab',`left:20px;top:0;width:180px;text-align:right`,esc(A[0])),lb=el('div','lab a',`left:684px;top:0;width:180px`,esc(B[0])),na=el('div','big',`left:0;top:${Y(va)-30}px;width:176px;text-align:right;font-size:48px;color:#7fc8ff`),nb=el('div','big',`left:684px;top:${Y(vb)-30}px;width:180px;font-size:48px;color:var(--acc)`),
dl=el('div','big',`left:270px;top:${(Y(va)+Y(vb))/2-34}px;width:324px;text-align:center;font-size:56px`);v.append(la,lb,na,nb,dl);fit(la,24,16,60);fit(lb,24,16,60);
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
V.text=(v,d)=>{const ws=String(d.w||'').split(/\s+/).filter(Boolean).slice(0,6);const box=el('div','',`position:absolute;left:0;top:40px;width:864px;height:480px;display:flex;flex-wrap:wrap;align-content:center;gap:0 22px;font-weight:900;text-transform:uppercase;line-height:1.02;font-size:118px;letter-spacing:-2px`);
const sp=ws.map((w,i)=>{const e=el('span','',i==ws.length-1?'color:var(--acc)':'',esc(w));box.append(e);return e});v.append(box);fit(box,118,48,480,864);
return (t,st)=>sp.forEach((e,i)=>{const p=st(i*.25,.45);e.style.opacity=p;e.style.display='inline-block';e.style.transform=`translateY(${(1-E(p))*50}px)`})};
// ---------- scény ----------
const root=document.getElementById('root');const SC=D.scenes.map((sc,i)=>{const w=el('div','sc');w.style.display='block';root.append(w);
const k=el('div','kick','',`<b>${String(i+1).padStart(2,'0')}</b>${D.kicker?' · '+esc(D.kicker):''} · ${i+1}/${D.scenes.length}`);
const tt=el('div','ttl');tt.lang=D.lang;tt.innerHTML=String(sc.h||'').split(/\s+/).filter(Boolean).map(x=>`<span class="w"><span>${esc(x)}</span></span>`).join(' ');w.append(k,tt);
const intro=i==0;fit(tt,intro?104:82,44,intro?330:270,860);const th=tt.offsetHeight;const vz=el('div','viz');vz.style.top=Math.max(690,362+th+90)+'px';w.append(vz);
let upd=()=>{};try{upd=(V[sc.v.k]||V.text)(vz,sc.v)||(()=>{})}catch(e){vz.textContent=''}
w.style.display='none';
return {w,k,tt,vz,upd,t0:sc.t0,t1:sc.t1,steps:sc.steps||0}});
const CAP=document.getElementById('cap'),BAR=document.getElementById('bar'),GLOW=document.getElementById('glow');let lastCap=-1;
function renderAt(t){let cur=SC.length-1;for(let i=0;i<SC.length;i++){if(t<SC[i].t1){cur=i;break}}
SC.forEach((s,i)=>{const lt=t-s.t0,dur=s.t1-s.t0;const vis=i==cur||(i==cur-1&&t-SC[cur].t0<.35);s.w.style.display=vis?'block':'none';if(!vis)return;
if(i<cur){const o=cl((t-SC[cur].t0)/.35);s.w.style.opacity=1-o;s.w.style.transform=`translateY(${-60*E(o)}px)`;return}
s.w.style.opacity=1;s.w.style.transform='';s.k.style.opacity=E(lt/.4);
s.tt.querySelectorAll('.w>span').forEach((e,j)=>{const p=E((lt-.08-j*.07)/.5);e.style.transform=`translateY(${(1-p)*105}%)`});
const span=Math.max(.6,Math.min(1.35,(dur*.72-.6)/Math.max(1,s.steps)));const st=(a,b)=>E((lt-.6-a*span)/(b*Math.max(.7,span)));
s.vz.style.opacity=i==0?1:E((lt-.25)/.4);try{s.upd(lt,st)}catch(e){}});
GLOW.style.opacity=cur==0?.22*E(t/1.5):.07;GLOW.style.transform=`translate(${Math.sin(t*.3)*40}px,${Math.cos(t*.25)*40}px)`;
BAR.style.width=(1080*cl(t/D.total))+'px';
let ci=-1;for(let i=0;i<D.caps.length;i++){if(t>=D.caps[i].s-.05&&t<D.caps[i].e){ci=i;break}}
if(ci<0){CAP.innerHTML='';return}const c=D.caps[ci];
CAP.innerHTML=c.w.map(w=>`<span class="${t>=w.s?'on':''}">${esc(w.t)}</span>`).join(' ');
const on=[...CAP.children].filter(x=>x.classList.contains('on'));if(on.length)on[on.length-1].className='on k';if(ci!==lastCap){fit(CAP,56,36,140,864);lastCap=ci}}
window.READY=true;
</script></body></html>"""

STEPS = {"flow": lambda d: 4 if d.get("x") else 3, "cycle": lambda d: 4, "bars": lambda d: len(d.get("i") or []) + 1,
         "calc": lambda d: len(d.get("r") or []) + .5, "compare": lambda d: 2.5, "count": lambda d: 2, "list": lambda d: len(d.get("i") or []),
         "icons": lambda d: len(d.get("i") or []) + .5, "temp": lambda d: 3.5, "house": lambda d: len(d.get("i") or []) + 1.5,
         "split": lambda d: len(d.get("i") or []) + .5, "text": lambda d: 1.5}

_lock = threading.Lock()


def make(scenes, voice, out, accent="#FF6B00", lang="sk", text="", kicker="", music=None, font=None, fps=30):
    """Vyrenderuje celé video: animované scény + titulky + hlas (+ hudba potichu)."""
    from . import anim, media
    if not anim.available():
        raise RuntimeError("Animácie sa ešte pripravujú (Chromium sa sťahuje)")
    total = media.duration(voice) or 10
    words = media.word_times(voice, text)
    times = timeline(scenes, words, total)
    sc_data = []
    for sc, (t0, t1) in zip(scenes, times):
        v = board_of(sc)
        h = (sc.get("onscreen") or "").strip()
        if v.get("k") == "text" and re.sub(r"\W", "", str(v.get("w", "")).lower()) == re.sub(r"\W", "", h.lower()):
            h = ""  # rovnaký text ako nadpis: ukáž ho len raz, veľkým
        sc_data.append({"h": h, "v": v, "t0": round(t0, 3), "t1": round(t1, 3),
                        "steps": STEPS.get(v.get("k"), lambda d: 2)(v)})
    data = {"acc": accent, "lang": lang, "kicker": kicker, "total": total, "scenes": sc_data, "caps": caption_chunks(words, lang)}
    html = page(data, font)
    if total > 90:
        fps = 25
    n = int((total + 0.3) * fps)
    ff = media.ffmpeg()
    cmd = [ff, "-y", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-", "-i", str(voice)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        af = ["-filter_complex", "[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]", "-map", "0:v", "-map", "[a]"]
    else:
        af = ["-map", "0:v", "-map", "1:a"]
    cmd += af + ["-t", f"{total + 0.3:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
                 "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    import os
    from playwright.sync_api import sync_playwright
    with _lock, sync_playwright() as pw:
        exe = os.environ.get("SM_CHROMIUM")
        b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        try:
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.set_content(html)
            pg.wait_for_function("window.READY===true", timeout=20000)
            for i in range(n):
                pg.evaluate(f"renderAt({i / fps:.4f})")
                proc.stdin.write(pg.screenshot(type="jpeg", quality=90))
            proc.stdin.close()
            err = proc.stderr.read().decode(errors="ignore")
            if proc.wait() != 0:
                raise RuntimeError("ffmpeg: " + err[-400:])
        finally:
            if proc.poll() is None:
                proc.kill()
            b.close()
    return str(out)


def preview(d, out_png, accent="#FF6B00", lang="sk", title="Ukážka", at=6.0):
    """Jeden obrázok diagramu (na test/náhľad)."""
    data = {"acc": accent, "lang": lang, "kicker": "", "total": 10, "caps": [],
            "scenes": [{"h": title, "v": d, "t0": 0, "t1": 10, "steps": STEPS.get(d.get("k"), lambda x: 2)(d)}]}
    import os
    from playwright.sync_api import sync_playwright
    with _lock, sync_playwright() as pw:
        exe = os.environ.get("SM_CHROMIUM")
        b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": W, "height": H})
            pg.set_content(page(data))
            pg.wait_for_function("window.READY===true", timeout=20000)
            pg.evaluate(f"renderAt({at})")
            pg.screenshot(path=str(out_png))
        finally:
            b.close()
    return str(out_png)
