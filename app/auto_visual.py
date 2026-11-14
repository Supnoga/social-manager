"""Bez AI: keď hlas alebo nadpis scény hovorí o stroji či deji, ktorý má knižnica ako animovanú schému (rez motora,
prevodovka, priehrada, raketa...), dá ju tam namiesto všeobecnej ikony. Funguje aj pre staré scenáre pri novom skladaní."""
import re

# (regex, mechanizmus, popisky po anglicky) – poradie = priorita (konkrétne pred všeobecnými)
RULES = [
    (r"jet engine|turbofan|turbojet|jet turbine", "jet", ["Intake", "Compressor", "Combustion", "Exhaust"]),
    (r"rotary engine|wankel|rotor housing|apex seal|triangular rotor", "wankel", ["Intake", "Compression", "Power", "Exhaust"]),
    (r"turbo(charger|charged|charging)?s?\b|turbo lag|wastegate|boost pressure", "turbo", ["Exhaust in", "Turbine", "Compressor", "Air to engine"]),
    (r"four[- ]stroke|piston|cylinder|combustion engine|intake stroke|compression stroke|power stroke|exhaust stroke|how (an? )?(car )?engine",
     "piston", ["Intake", "Compression", "Power", "Exhaust"]),
    (r"camshaft|valve timing|valves? open|valve ?train|timing (belt|chain)|cam lobe", "camshaft", ["Camshaft", "Valve", "Timing belt"]),
    (r"differential", "differential", ["Inner wheel", "Differential", "Outer wheel"]),
    (r"gearbox|transmission|gear ratio|shift(ing)? gears?", "gearbox", ["Engine", "Wheels"]),
    (r"\bbrake|braking|brake disc|brake pad", "car_brake", ["Brake disc", "Caliper", "Brake pads"]),
    (r"helicopter|main rotor|tail rotor", "rotor", ["Main rotor", "Tail rotor", "Torque"]),
    (r"\bwing|airfoil|aerofoil|\blift\b(?! shaft)|how planes? fl", "wing", ["Lift", "Airflow"]),
    (r"parachut|skydiv|terminal velocity", "parachute", ["Drag", "Weight"]),
    (r"rocket|booster|launch vehicle|liftoff|stage separation", "rocket", ["Payload", "Second stage", "First stage"]),
    (r"satellite|\bgps\b|orbit", "orbit", ["Earth", "Satellites"]),
    (r"\bradar|stealth", "radar", []),
    (r"submarine|ballast", "submarine", ["Ballast tank", "Sea water"]),
    (r"projectile|trajectory|ballistic|cannon|artillery|howitzer", "trajectory", []),
    (r"nuclear|fission|reactor|uranium|chain reaction", "fission", ["Neutron", "Uranium-235", "Energy"]),
    (r"hydraulic|pascal", "hydraulic", ["Small piston", "Big piston", "Hydraulic oil"]),
    (r"\blever|fulcrum", "lever", ["Load", "Effort", "Pivot"]),
    (r"pulley|block and tackle", "pulley", ["Pulley", "Load", "Pull"]),
    (r"tower crane|\bcranes?\b", "crane", ["Counterweight", "Load"]),
    (r"escalator", "escalator", ["Handrail", "Drive"]),
    (r"elevator|lift shaft|counterweight", "elevator", ["Car", "Counterweight"]),
    (r"suspension bridge|bridge", "bridge", ["Deck", "Hangers", "Main cable", "Towers", "Anchorage"]),
    (r"tunnel boring|\btbm\b|tunnel", "tunnel", ["Cutterhead", "Lining rings", "Conveyor"]),
    (r"oil well|drilling|drill rig|derrick|fracking", "drill", ["Derrick", "Drill bit", "Oil reservoir"]),
    (r"canal lock|lock chamber|panama canal", "canal_lock", ["Upper water", "Lock chamber", "Lower water"]),
    (r"\bdams?\b|hydroelectric|hydropower|reservoir", "dam", ["Reservoir", "Turbine", "Grid"]),
    (r"wind turbine|wind power|wind farm|wind energy", "wind_turbine", ["Wind", "Power"]),
    (r"solar (panel|cell|power|energy)|photovoltaic", "solar", ["Sunlight", "Solar cell", "Load"]),
    (r"heat pump|wärmepumpe|tepeln\w+ čerpad|tepeln\w+ čerpad|pompa ciepła|hőszivattyú|refrigerant", "heatpump",
     ["Outdoor air", "Compressor", "Heat", "Expansion valve"]),
    (r"air ?condition|\bac unit", "aircon", ["Compressor", "Cooling", "Heat outside"]),
    (r"fridge|refrigerator", "fridge", ["Compressor", "Cold", "Heat"]),
    (r"generator|dynamo|alternator", "generator", ["Turbine", "Generator", "Bulb"]),
    (r"electric motor|e-motor|ev motor", "motor", ["Magnet", "Coil", "Battery"]),
    (r"transformer|high voltage|substation", "transformer", ["Primary coil", "Iron core", "Secondary coil"]),
    (r"circuit|electric current|\bohm|voltage", "circuit", ["Battery", "Switch", "Bulb"]),
    (r"conveyor|assembly line|production line|factory line|mass production", "conveyor", ["Weld", "Paint", "Check"]),
    (r"\bcpu\b|processor|microchip|transistor", "cpu", ["RAM", "Cache", "Cores"]),
    (r"hard drive|\bhdd\b|\bssd\b|storage drive", "hdd", ["Hard drive", "SSD"]),
    (r"fib(er|re) optic|undersea cable|internet cable", "fiber", ["Core", "Cladding", "Laser"]),
    (r"bicycle|\bbikes?\b|chain drive", "bicycle", ["Sprocket", "Chainring"]),
    (r"sound wave|frequenc|radio wave|wavelength", "wave", []),
    (r"pendulum|clock mechanism|grandfather clock", "pendulum", []),
    (r"\bgears?\b|cogs?\b", "gears", ["Driver gear", "Driven gear"]),
]
_RX = [(re.compile(r, re.I), m, l) for r, m, l in RULES]
_LABELS = {}
for _r, _m, _l in RULES:
    _LABELS.setdefault(_m, _l)


def _precise():
    """Stroje s presným spočítaným modelom = tie, ktoré má zz_mech_pro.js (zoznam sa číta priamo z neho)."""
    try:
        from pathlib import Path
        js = "\n".join(f.read_text(encoding="utf-8") for f in sorted((Path(__file__).parent / "boards").glob("zz_mech_pro*.js")))
        return set(re.findall(r"^PRO\.(\w+)=", js, re.M)) or {"piston", "wankel", "gears"}
    except Exception:
        return {"piston", "wankel", "gears"}


PRECISE = _precise()
# záber na jednu dobu motora: podľa toho, o čom scéna hovorí (nadpis, opis, hlas)
_STROKES = [("intake", r"intake|air (and fuel )?(in\b|enters|rushes)|(pulls?|sucks?|draws?|drawn|sucked|pulled) in\b"),
            ("compression", r"compress|squeez|squash"),
            ("power", r"power stroke|\bpower\b|spark|ignit|\bburn|combust|explo|expand|bang\b|pushes? the (piston|rotor)"),
            ("exhaust", r"exhaust|used gas|burnt gas|burned gas|swept out|pushed out")]
_PARTS = {   # zábery na časti ďalších modelov (názvy záberov sú v zz_mech_pro_b.js)
    "camshaft": [("cam", r"cam lobe|\blobes?\b|camshaft|\bcams?\b|egg[- ]shaped"), ("valve", r"valve|spring|\bport\b|air and fuel|mixture"),
                 ("belt", r"timing (belt|chain)|\bbelt\b|\bchain\b|crankshaft|half (the )?speed|twice|in sync")],
    "turbo": [("turbine", r"turbine|exhaust (gas|gases|side)|hot side|waste energy"), ("shaft", r"\bshaft|bearing|\boil\b"),
              ("compressor", r"compressor|compress|fresh air|more air|cold side|\bboost|pack(s|ed)? (more )?air|intake")],
    "car_brake": [("caliper", r"caliper|brake pads?|\bpads?\b|\bpistons?\b|brake fluid|hydraulic|squeez|clamp|pedal"),
                  ("disc", r"\bdis[ck]s?\b|\brotors?\b|\bheat|degrees|glow|friction|\bfade")],
}
FOCUS = {m: [(f, re.compile(r, re.I)) for f, r in _STROKES] for m in ("piston", "wankel", "rotary")}
FOCUS.update({m: [(f, re.compile(r, re.I)) for f, r in v] for m, v in _PARTS.items()})
RUNS = ("piston", "wankel", "rotary", "turbo", "camshaft")   # modely, ktoré vedia záber „beží naplno“
WEAK = ("hero", "icons", "scene", "draw", "text", "list")
# ikony, ktoré sa naozaj točia; ostatné sa nemajú otáčať (otáčajúca sa značka motora pôsobí lacno)
SPINS = set("gear wheel tyre saw_blade flywheel impeller propeller ship_propeller sprocket ball_bearing roller_bearing brake_disc vinyl film_reel roulette ship_wheel".split())


def find(text):
    for rx, m, labels in _RX:
        if rx.search(text or ""):
            return m, labels
    return None


# slová, ktoré tému len podporujú (samy model nespustia): pomáhajú spoznať, o ktorom stroji je celé video
_SUPPORT = {"wankel": r"\brotors?\b|\bpockets?\b|\brotary\b|housing", "piston": r"crankshaft|\bstrokes?\b|\bvalves?\b|connecting rod",
            "gears": r"\bteeth\b|\btooth\b|\bmesh|\bratio", "turbo": r"turbine|compressor|\bboost|exhaust gas|intercooler|\bspool",
            "camshaft": r"\blobes?\b|\bvalves?\b|timing|\bcams?\b", "car_brake": r"caliper|\bpads?\b|\bdis[ck]s?\b|friction|brake fluid|pedal"}


def topic(full, title=""):
    """Stroj s presným modelom, o ktorom je celé video. Rozhoduje názov videa; bez neho musí stroj v texte jasne prevládať. Inak None."""
    hit = find(title or "")
    if hit:
        return hit[0] if hit[0] in PRECISE else None   # video je o inom stroji: jeho model nesmie zabrať celé video
    score = {}
    for m in dict.fromkeys(m for _, m, _ in _RX):
        strong = sum(len(rx.findall(full or "")) for rx, mm, _ in _RX if mm == m)
        if strong:
            score[m] = 2 * strong + len(re.findall(_SUPPORT.get(m, r"$^"), full or "", re.I))
    best = sorted(score.items(), key=lambda kv: -kv[1])
    if not best or best[0][0] not in PRECISE or best[0][1] < (10 if (title or "").strip() else 6):
        return None   # názov, ktorý stroj nemenuje, je slabší dôkaz: stroj musí v texte prevládať výrazne
    if len(best) > 1 and best[0][1] < 1.5 * best[1][1]:
        return None   # dva stroje sú v texte zhruba rovnako: bez názvu videa sa nedá povedať, o ktorom je
    return best[0][0]


NAMES = {"piston": "Piston engine", "wankel": "Rotary engine", "rotary": "Rotary engine", "gears": "Gears", "turbo": "Turbocharger", "camshaft": "Camshaft", "car_brake": "Disc brake"}
_CMP = re.compile(r"\bvs\.?\b|versus|compared|unlike|instead of|rather than|difference|\bthan an?\b|side by side|normal engine|regular engine|conventional", re.I)


def other(topic, *texts):
    """Iný stroj s presným modelom, s ktorým scéna porovnáva (napr. piestový motor vo videu o rotačnom). Inak None."""
    same = {"wankel": "rotary", "rotary": "wankel"}.get(topic)
    for t in texts:
        if not t or not _CMP.search(t):
            continue
        for rx, m, _ in _RX:
            if m in ("piston", "wankel") and topic in ("piston", "wankel", "rotary") and m in PRECISE and m not in (topic, same) and rx.search(t):
                return m
    return None


def focuses(m, *texts):
    """Všetky časti stroja, o ktorých scéna hovorí (v poradí, ako zaznejú), bez opakovania."""
    out = []
    for t in texts:
        for _, f in sorted((mt.start(), f) for f, rx in FOCUS.get(m, ()) for mt in [rx.search(t or "")] if mt):
            if f not in out:
                out.append(f)
    return out


def focus(m, *texts):
    """Ktorú dobu scéna ukazuje: prvý text (nadpis, opis, hlas), ktorý hovorí o jednej až dvoch dobách. Viac dôb = celkový pohľad."""
    for t in texts:
        hits = sorted((mt.start(), f) for f, rx in FOCUS.get(m, ()) for mt in [rx.search(t or "")] if mt)
        if len(hits) > 2:
            return None
        if hits:
            return hits[0][1]
    return None


_UNIT = {"rpm": "RPM", "percent": "%", "%": "%", "degrees": "°", "times": "×", "bar": "bar", "psi": "psi", "horsepower": "hp", "hp": "hp",
         "kilowatts": "kW", "kw": "kW", "volts": "V", "liters": "L", "litres": "L", "km/h": "km/h", "mph": "mph", "tons": "t", "tonnes": "t",
         "meters": "m", "metres": "m", "kilometers": "km", "kilometres": "km", "seconds": "s", "celsius": "°C"}
_NUM = re.compile(r"^[^\d]{0,2}(\d[\d,.]*(?:/\d+)?)(%|x|×)?[^\w%]*$")


def callout(onscreen, words, t0):
    """Číslo, ktoré hlas v scéne povie (s jednotkou), a kedy: {"w": "9,000 RPM", "t": čas od začiatku scény}.
    Keď hlas číslo povie slovom, vezme sa z nadpisu scény. Inak None."""
    for i, w in enumerate(words):
        m = _NUM.match(str(w.get("w") or ""))
        if not m:
            continue
        num, suf = m.group(1).rstrip(".,"), m.group(2) or ""
        nxt = re.sub(r"[^\w/%°]", "", str(words[i + 1]["w"]).lower()) if i + 1 < len(words) else ""
        unit = "" if suf else _UNIT.get(nxt, "")
        if not (suf or unit) and len(re.sub(r"\D", "", num)) < 2:
            continue   # samotná malá číslica bez jednotky nie je zaujímavé číslo
        txt = num + ("×" if suf in ("x", "×") else suf) + (unit if unit in ("%", "°", "×") else " " + unit if unit else "")
        return {"w": txt.strip(), "t": round(max(0.0, float(w.get("s") or 0) - t0), 2)}
    m = re.search(r"(?<![\w.])(\d[\d,.]*(?:/\d+)?\s?(?:%|×|x\b|rpm\b|bar\b|hp\b|kw\b|°c?)?)", re.sub(r"^\s*\d+[.):]\s*", "", onscreen or ""), re.I)
    if m and (len(re.sub(r"\D", "", m.group(1))) > 1 or re.search(r"[%×x/°a-z]", m.group(1), re.I)):
        return {"w": m.group(1).strip().replace("x", "×").upper().replace("KW", "kW").replace("BAR", "bar").replace("HP", "hp"), "t": None}
    return None


def sound_events(sc_data):
    """Zvuky k obrazu presných modelov: [(druh, čas vo videu)]. Časy sú spočítané rovnako ako pohyb v zz_mech_pro.js."""
    ev = []
    for s in sc_data:
        v, t0, t1 = s.get("v") or {}, s["t0"], s["t1"]
        if v.get("k") != "mech" or v.get("m") not in PRECISE:
            continue
        dur, f, m, sh = t1 - t0, v.get("f") or "", v.get("m"), 0.0
        if v.get("_in"):
            IN = max(1.7, min(2.8, dur * .3))
            sh = IN * .78
            ev.append(("zoom", t0 + IN * .55))
        if (v.get("c") or {}).get("t") is not None:
            ev.append(("num", t0 + v["c"]["t"]))
        end, hits, kind = t1 - .25, [], "bang"
        if m == "piston":
            T1, PF = max(4.6, min(7.6, dur * .66)), max(3.2, min(5.5, dur * .8))
            if f in ("intake", "compression", "power", "exhaust"):
                kind = {"intake": "air", "exhaust": "hiss", "power": "bang"}.get(f)
                hits = [n * PF for n in range(int(dur / PF) + 1)] if kind else []
            else:
                ph = (lambda t: 2 + t * 4.2 / T1) if f == "run" else (lambda t: t / T1 if t <= T1 else 1 + (
                    (t - T1) + 3.2 * (1.6 * ((min(1, (t - T1) / 1.6)) ** 3 - (min(1, (t - T1) / 1.6)) ** 4 / 2)
                                      if t - T1 < 1.6 else .8 + (t - T1 - 1.6))) / T1)
                t, last = 0.0, ph(0.0)
                while t < dur:
                    t += .01
                    p = ph(t)
                    if int(p + .5) > int(last + .5):   # zážih = polovica cyklu
                        hits.append(t)
                    last = p
        elif m in ("wankel", "rotary"):
            w = 1.9 if f == "run" else .72
            if f in ("", "run", "power"):
                hits = [(0.5236 + j * 2.0944) / w for j in range(60)]
            elif f in ("intake", "exhaust"):
                kind, hits = {"intake": "air", "exhaust": "hiss"}[f], [.5]
        hits = [h for h in hits if 0 <= h and t0 + sh + h < end]
        if len(hits) > 5:   # pri behu naplno stačí pár úderov, nie každý zážih
            hits = hits[::-(-len(hits) // 5)]
        for h in hits:
            if True:
                ev.append((kind, t0 + sh + h))
    return sorted(ev, key=lambda e: e[1])


def calm_draw(d):
    """Kresba: točiť sa smú len veci, ktoré sa naozaj točia; ostatné len jemne pulzujú."""
    if d.get("k") != "draw":
        return d
    els = []
    for e in d.get("e") or []:
        if isinstance(e, dict) and e.get("s") == "icon" and "spin" in str(e.get("a") or "") and str(e.get("i") or "") not in SPINS:
            e = dict(e, a=str(e.get("a")).replace("spin", "pulse"))
        els.append(e)
    return dict(d, e=els)


def upgrade(d, scene, spoken, used, lang="en", prev=None, long=False, full="", topic=None, last=False):
    """d = diagram scény. Vráti diagram, ktorý sa naozaj ukáže.
    topic = stroj, o ktorom je celé video: slabé scény (ikony, text) vtedy ukazujú jeho presný model a kamera ide
    na to, o čom scéna hovorí. Mimo témy videa sa model doplní, len keď scéna sama hovorí o stroji s presným modelom."""
    d = calm_draw(d)
    texts = (scene.get("onscreen") or "", scene.get("visual") or "", spoken or "")
    if d.get("k") == "mech":
        if d.get("m") in FOCUS and not d.get("f"):
            f = focus(d["m"], *texts)
            if f and used.get("_last") != (d["m"], f):
                d = dict(d, f=f)
        used["_last"] = (d.get("m"), d.get("f") or "")
        return d
    if d.get("k") not in WEAK:
        return d
    if topic and last:   # záverečná výzva: stroj beží ďalej, text výzvy je v nadpise scény
        f = "run" if topic in RUNS and used.get("_last") != (topic, "run") else ""
        used["_last"] = (topic, f)
        return dict({"k": "mech", "m": topic}, **({"f": f} if f else {}), **({"l": _LABELS[topic]} if _LABELS.get(topic) and lang == "en" else {}))
    if topic:
        o = other(topic, *texts)
        if o and not used.get("_vs"):   # scéna porovnáva s iným strojom: oba bežia vedľa seba (raz za video)
            used["_vs"] = 1
            used["_last"] = ("versus", "")
            out = {"k": "mech", "m": "versus", "a": o, "b": topic}
            if lang == "en":
                out["l"] = [NAMES.get(o, o), NAMES.get(topic, topic)]
            return out
        f = focus(topic, *texts)
        if f is None:
            if long and prev == topic:
                return d   # v dlhom videu nie dva celkové pohľady po sebe
            f = "run" if topic in RUNS and used.get("_ov", 0) % 2 else ""
            used["_ov"] = used.get("_ov", 0) + 1
        if prev == topic and used.get("_last") == (topic, f):   # nikdy ten istý záber dvakrát po sebe: iná časť, beh naplno alebo celok
            alt = [g for g in focuses(topic, *texts) + (["run"] if topic in RUNS else []) + [""] if (topic, g) != used.get("_last")]
            if long or not alt:
                return d
            f = alt[0]
        used["_last"] = (topic, f)
        out = {"k": "mech", "m": topic}
        if f:
            out["f"] = f
        if _LABELS.get(topic) and lang == "en":
            out["l"] = _LABELS[topic]
        return out
    # radšej žiadny model než nesúvisiaci: stroj musí byť v nadpise/opise scény, alebo ho hlas spomína a video je o ňom
    hit = find(f"{texts[0]} . {texts[1]}")
    if not hit:
        hit = find(spoken)
        if hit and sum(len(rx.findall(full or "")) for rx, m, _ in _RX if m == hit[0]) < 3:
            hit = None
    if not hit or hit[0] not in PRECISE:   # len stroje s presným modelom; staré hrubé schémy sa samy nedopĺňajú
        return d
    m, labels = hit
    if used.get(m, 0) >= (3 if long else 2) or prev == m:
        return d
    used[m] = used.get(m, 0) + 1
    used["_last"] = (m, "")
    out = {"k": "mech", "m": m}
    if labels and lang == "en":
        out["l"] = labels
    return out
