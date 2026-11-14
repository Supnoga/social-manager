"""Bez AI: keď hlas alebo nadpis scény hovorí o stroji či deji, ktorý má knižnica ako animovanú schému (rez motora,
prevodovka, priehrada, raketa...), dá ju tam namiesto všeobecnej ikony. Funguje aj pre staré scenáre pri novom skladaní."""
import re

# (regex, mechanizmus, popisky po anglicky) – poradie = priorita (konkrétne pred všeobecnými)
RULES = [
    (r"jet engine|turbofan|turbojet|jet turbine", "jet", ["Intake", "Compressor", "Combustion", "Exhaust"]),
    (r"rotary engine|wankel|rotor housing|apex seal", "wankel", ["Intake", "Compression", "Power", "Exhaust"]),
    (r"four[- ]stroke|piston|cylinder|combustion engine|intake stroke|compression stroke|power stroke|exhaust stroke|how (an? )?(car )?engine",
     "piston", ["Intake", "Compression", "Power", "Exhaust"]),
    (r"camshaft|valve timing|valves? open", "camshaft", ["Camshaft", "Valve spring", "Valve"]),
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
WEAK = ("hero", "icons", "scene", "draw", "text", "list")
# ikony, ktoré sa naozaj točia; ostatné sa nemajú otáčať (otáčajúca sa značka motora pôsobí lacno)
SPINS = set("gear wheel tyre saw_blade flywheel impeller propeller ship_propeller sprocket ball_bearing roller_bearing brake_disc vinyl film_reel roulette ship_wheel".split())


def find(text):
    for rx, m, labels in _RX:
        if rx.search(text or ""):
            return m, labels
    return None


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


def upgrade(d, scene, spoken, used, lang="en", prev=None, long=False, full=""):
    """d = diagram scény. Ak je slabý (ikona, text) a scéna hovorí o mechanizme z knižnice, vráti animovanú schému."""
    d = calm_draw(d)
    if d.get("k") not in WEAK:
        return d
    # radšej žiadny model než nesúvisiaci: stroj musí byť v nadpise/opise scény, alebo ho hlas spomína a video je o ňom
    hit = find(f"{scene.get('onscreen') or ''} . {scene.get('visual') or ''}")
    if not hit:
        hit = find(spoken)
        if hit and sum(len(rx.findall(full or "")) for rx, m, _ in _RX if m == hit[0]) < 3:
            hit = None
    if not hit:
        return d
    m, labels = hit
    if used.get(m, 0) >= (3 if long else 2) or prev == m:
        return d
    used[m] = used.get(m, 0) + 1
    out = {"k": "mech", "m": m}
    if labels and lang == "en":
        out["l"] = labels
    return out
