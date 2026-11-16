"""Bez AI: keď hlas alebo nadpis scény hovorí o stroji či deji, ktorý má knižnica ako animovanú schému (rez motora,
prevodovka, priehrada, raketa...), dá ju tam namiesto všeobecnej ikony. Funguje aj pre staré scenáre pri novom skladaní."""
import re

# (regex, mechanizmus, popisky po anglicky) – poradie = priorita (konkrétne pred všeobecnými)
RULES = [
    (r"jet engine|turbofan|turbojet|jet turbine", "jet", ["Fan", "Compressor", "Combustion", "Turbine", "Nozzle"]),
    (r"rotary engine|wankel|rotor housing|apex seal|triangular rotor", "wankel", ["Intake", "Compression", "Power", "Exhaust"]),
    (r"turbo(charger|charged|charging)?s?\b|turbo lag|wastegate|boost pressure", "turbo", ["Exhaust in", "Turbine", "Compressor", "Air to engine"]),
    (r"four[- ]stroke|piston|(?<!lock )cylinder|combustion engine|intake stroke|compression stroke|power stroke|exhaust stroke|how (an? )?(car )?engines?\b"
     r"|(petrol|gasoline|inline[- ]?(four|six|4|6)|straight[- ](four|six)|boxer) engines?|\bv(6|8|10|12)\b|crankshaft|spark plugs?|engine knock",
     "piston", ["Intake", "Compression", "Power", "Exhaust"]),
    (r"camshaft|valve timing|valves? open|valve ?train|timing (belt|chain)|cam lobe", "camshaft", ["Camshaft", "Valve", "Timing belt"]),
    (r"differential|\bdiffs?\b|spider gears?|ring gear", "differential", ["Drive pinion", "Ring gear", "Spider gears", "Axle shaft"]),
    (r"gearbox|transmission|gear ratio|shift(ing|s)? gears?|\bsynchro|layshaft|first gear|top gear", "gearbox", ["Input shaft", "Gear pairs", "Selector", "Output shaft"]),
    (r"\bbrake|braking|brake disc|brake pad", "car_brake", ["Brake disc", "Caliper", "Brake pads"]),
    (r"helicopter|main rotor|tail rotor", "rotor", ["Main rotor", "Tail rotor", "Torque"]),
    (r"\bwing|airfoil|aerofoil|lift force|lift and drag|generat\w+ lift|\blift, not|how planes? fl", "wing", ["Airflow", "Low pressure", "High pressure", "Lift"]),
    (r"parachut|skydiv|terminal velocity", "parachute", ["Drag", "Weight"]),
    (r"\borbit(s|al)?\b|satellites? (do not|don't|never) fall|floating astronauts", "orbit", ["Gravity", "Sideways speed", "Orbit", "Low orbit", "Medium orbit", "Geostationary"]),
    (r"rocket|booster|launch vehicle|liftoff|stage separation", "rocket", ["Payload", "Second stage", "First stage"]),
    (r"satellite|\bgps\b|orbit", "orbit", ["Gravity", "Sideways speed", "Orbit", "Low orbit", "Medium orbit", "Geostationary"]),
    (r"\bradar|stealth", "radar", ["Antenna", "Pulse", "Target", "Screen"]),
    (r"submarine|ballast", "submarine", ["Ballast tanks", "Compressed air", "Pressure hull", "Propeller", "Dive planes"]),
    (r"projectile|trajectory|ballistic|cannon|artillery|howitzer", "trajectory", []),
    (r"nuclear|fission|reactor|uranium|chain reaction", "fission", ["Neutron", "Uranium-235", "Energy"]),
    (r"hydraulic|pascal", "hydraulic", ["Small piston", "Big piston", "Hydraulic oil", "Check valves"]),
    (r"\blever|fulcrum", "lever", ["Load", "Effort", "Pivot"]),
    (r"pulley|block and tackle", "pulley", ["Pulley", "Load", "Pull"]),
    (r"tower crane|\bcranes?\b", "crane", ["Counterweight", "Load"]),
    (r"escalator", "escalator", ["Handrail", "Drive"]),
    (r"elevator|lift shaft|counterweight", "elevator", ["Car", "Counterweight", "Traction sheave", "Safety brake"]),
    (r"suspension bridge|bridge", "bridge", ["Deck", "Hangers", "Main cable", "Towers", "Anchorage"]),
    (r"tunnel boring|\btbm\b|tunnel", "tunnel", ["Cutterhead", "Thrust jacks", "Lining rings", "Conveyor"]),
    (r"oil well|drilling|drill rig|derrick|fracking", "drill", ["Derrick", "Drill bit", "Oil reservoir"]),
    (r"inside your wall|wall insulation|vapou?r barrier|wall dries|sip panels?|insulat(e|ing) (a |the |your )?walls?|cavity wall|wall cut open", "wall",
     ["Inside", "Masonry", "Insulation", "Outside", "Dew point", "Vapor barrier"]),
    (r"pin tumbler|lock ?pick|locksmith|lock cylinder|door lock pins|mechanical lock|key opens a lock", "pinlock", ["Key pins", "Driver pins", "Shear line", "Plug"]),
    (r"canal lock|ship lock|lock chamber|panama canal|inside a lock", "canal_lock", ["Gates", "Valves", "Chamber", "Ship"]),
    (r"\bdams?\b|hydroelectric|hydropower|reservoir", "dam", ["Reservoir", "Dam wall", "Penstock", "Turbine", "Generator"]),
    (r"wind turbine|wind power|wind farm|wind energy", "wind_turbine", ["Rotor", "Gearbox", "Generator", "Tower"]),
    (r"solar (panel|cell|power|energy)|photovoltaic", "solar", ["Sunlight", "P-N junction", "Current"]),
    (r"heat pump|wärmepumpe|tepeln\w+ čerpad|tepeln\w+ čerpad|pompa ciepła|hőszivattyú|refrigerant", "heatpump",
     ["Evaporator", "Compressor", "Condenser", "Expansion valve"]),
    (r"air ?condition|\bac unit", "aircon", ["Compressor", "Cooling", "Heat outside"]),
    (r"fridge|refrigerator", "fridge", ["Compressor", "Condenser", "Expansion", "Evaporator"]),
    (r"generator|dynamo|alternator", "generator", ["Turbine", "Generator", "Bulb"]),
    (r"electric motors?|e-?motors?|ev motors?|traction motors?|induction motors?|brushless|permanent[- ]magnet motors?|synchronous motors?|servo ?motors?|\bstator\b|regenerative braking|motor (spins|turns)", "emotor",
     ["Stator coils", "Rotor magnets", "Magnetic field", "Shaft"]),
    (r"transistors?\b|mosfet", "transistor", ["Source", "Gate", "Drain", "Channel"]),
    (r"circuit breakers?|breaker trips?|\bfuses?\b|\bmcb\b", "breaker", ["Contacts", "Bimetal strip", "Solenoid", "Arc chute"]),
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
    "gearbox": [("collar", r"selector|synchro|collar|\bdog\b|\bfork|\block(s|ed)?\b|shift|gear (stick|lever)|engage"),
                ("input", r"input shaft|clutch|from the engine|engine (turns|spins|drives)|crankshaft"),
                ("output", r"output shaft|to the wheels|wheels|driveshaft|prop ?shaft"),
                ("gears", r"gear pairs?|\bratio|layshaft|countershaft|big(ger)? gear|small(er)? gear|\bteeth"),
                ("g1", r"first gear|1st gear|low(est)? gear|pull(ing)? away|from a stop"), ("g2", r"second gear|2nd gear"),
                ("g3", r"top gear|high(er|est)? gear|(third|fourth|fifth|sixth) gear|motorway|highway|cruis")],
    "differential": [("pinion", r"pinion|ring gear|crown wheel|driveshaft|prop ?shaft|from the (engine|gearbox)|ninety|90"),
                     ("spider", r"spider|small gears|side gears?|\bcage\b|carrier|\binside\b|planet"),
                     ("hold", r"hold(s|ing)? one wheel|\bheld\b|one wheel (is )?(stopped|stuck|locked|stops)|stand(s|ing)? still|twice as fast|\bice\b|\bmud\b|wheel ?spin|(loses?|no|without) grip|spins? freely|open diff"),
                     ("straight", r"straight|same speed|turn together|as one (block|piece|unit)|do(es)? not spin|nothing spins"),
                     ("turn", r"corner|\bbend|inner wheel|outer wheel|inside wheel|outside wheel|different speeds?|faster|slower|speeds up|slows down")],
    "heatpump": [("valve", r"expansion|\bvalve|pressure drops?|throttl|expanz|škrtiac|drossel|rozpręż"),   # aj v jazykoch N2N
                 ("comp", r"compress|squeez|kompres|verdicht|sprężark"),
                 ("cond", r"condens|gives? (up |off )?its heat|hands? (over )?its heat|releases? (its |the )?heat|back into (a )?liquid|kondenz|verflüssig|skraplacz|heat exchanger|plate|to the water|heats? (the |your )?water|radiator|underfloor|floor heating|hot water"),
                 ("evap", r"evaporat|výparn|verdampf|parownik|outdoor (air|coil)|outside air|from the air|\bfan\b|\bcoil\b|absorb|boil")],
    "wind_turbine": [("gearbox", r"gearbox|\bgears?\b|speeds? (it )?up|\bratio|times faster"),
                     ("generator", r"generator|magnet|\bcoils?\b|copper|electric|current|\bgrid\b|volt|megawatt"),
                     ("rotor", r"\bblades?\b|\brotor\b|\bhub\b|\blift\b|main shaft|sweep|the wind (hits|pushes|turns)")],
    "solar": [("junction", r"junction|silicon|knock|electric field|n-type|p-type|\blayers?\b|\bholes?\b|free electrons?"),
              ("circuit", r"circuit|\bwires?\b|current|\bflows?\b|\bload\b|bulb|lamp|inverter|\bgrid\b|battery|\bvolts?\b|power your"),
              ("light", r"sunlight|photons?|\bsun\b|light (hits|strikes)|\brays?\b")],
    "tunnel": [("jacks", r"\bjacks?\b|hydraulic|thrust|pushes? (itself|forward|off)|rams?\b|cylinders?"),
               ("rings", r"lining|\brings?\b|segments?|concrete|erector|\bwalls?\b|waterproof|gasket|grout"),
               ("conveyor", r"conveyor|\bbelt\b|\bscrew\b|\bmuck\b|spoil|debris|rubble|carr(y|ies) (it |the )?(away|out)|out of the tunnel"),
               ("cutter", r"cutter ?head|cutting (head|wheel|discs?)|\bdis[ck] cutters?|\bcutters?\b|\bface\b|grinds?|chews?|\brock\b|\bteeth\b|rotat")],
    "radar": [("chaff", r"chaff|alumini?um|\bstrips\b|decoys?|\bfoil\b"), ("clutter", r"clutter|\bbirds?\b|flock|false (targets?|echoes?|alarms?)"),
              ("doppler", r"doppler|frequency shift|closing speed|how fast|velocity|moving targets?"),
              ("stealth", r"stealth|invisible|deflect|scatter|absorb|angled|radar cross|\bRCS\b|faceted|coating"),
              ("screen", r"\bscreen\b|\bdisplay\b|\bblip|\bscope\b|operator|measures? the (time|delay)|microseconds?|round trip|time it takes"),
              ("target", r"\becho|bounces?|reflect|\btarget\b|aircraft|\bplanes?\b|\bjet\b|missile|\bhull\b|metal"),
              ("pulse", r"\bpulses?\b|radio waves?|microwaves?|speed of light|\bbeam\b|sends? out|transmit|\bsignal"),
              ("antenna", r"antenna|\bdish\b|\barray\b|transmitter|receiver|rotat|\bsweeps?\b")],
    "bridge": [("gap", r"expansion (joint|gap)|\bgaps?\b|expands?|contracts?|thermal|summer|winter|temperature"),
               ("wind", r"\bwind\b|resonan|flutter|twist|oscillat|\bsway|gallop|tacoma|wobbl|vibrat"),
               ("anchor", r"anchor|bedrock|concrete block|buried"), ("towers", r"\btowers?\b|pylons?|compress|foundation|caisson|\bpiers?\b"),
               ("hangers", r"hangers?|suspenders?|vertical (cables|ropes)|hang(s|ing)? from"),
               ("cable", r"main cable|\bcables?\b|\bwires?\b|strands?|tension|\bspun\b|spinning"),
               ("deck", r"\bdeck\b|roadway|\broad\b|traffic|trucks?|\bcars?\b|\blanes?\b|girder|truss")],
    "wing": [("stall", r"\bstall|separat|too steep|critical angle|loses? (its )?lift"), ("flap", r"\bflaps?\b|\bslats?\b|landing|take[- ]?off"),
             ("pressure", r"pressure|suction|bernoulli|faster over|speeds? up over|\bsucks?"),
             ("lift", r"\blift\b|upward force|newton|pushes? (the )?air down|downwash|deflect"),
             ("flow", r"airflow|air flows?|streamlines?|leading edge|air (splits|hits|meets)")],
    "dam": [("arch", r"curved|\barch|canyon walls?|abutments?"), ("spill", r"spillway|overflow|flood ?gates?|overtop|\bslides?\b"),
            ("pressure", r"pressure|thicker|weight of (the )?water|pushes? (on|against)|\bdepth\b|deeper"),
            ("generator", r"generator|electricit|\bgrid\b|megawatts?|\bcoils?\b|magnets?|power lines?|transformer"),
            ("turbine", r"turbine|runner|\bblades?\b|\bspins?\b|spinning"), ("penstock", r"penstock|\bpipes?\b|intake|rush(es|ing)?"),
            ("wall", r"\bwall\b|concrete|gravity dam|foundation|bedrock|\bcrest\b"), ("reservoir", r"reservoir|\blake\b|stored? water|water level|upstream")],
    "submarine": [("sonar", r"sonar|\bpings?\b|hydrophone"), ("dive", r"\bdives?\b|diving|submerge|\bsinks?\b|flood"),
                  ("surface", r"\bsurfac(e|es|ing)\b|blow(s|ing)? (the )?(tanks|ballast)|\brises?\b"), ("air", r"compressed air|high[- ]pressure air|air flasks?"),
                  ("tanks", r"ballast|\btanks?\b|buoyan|\bvents?\b"), ("hull", r"pressure hull|\bhull\b|crush|water pressure|\bsteel\b|titanium|\bdepth"),
                  ("propeller", r"propeller|pump[- ]?jet|\bshaft\b|reactor|electric motor"), ("planes", r"dive planes?|hydroplanes?|\bplanes\b|\bfins?\b|rudder|steer")],
    "hydraulic": [("valves", r"check valves?|one[- ]way valves?|\bvalves?\b|release"), ("oil", r"\boil\b|\bfluid\b|incompressible|pressure|pascal"),
                  ("big", r"big(ger)? piston|large piston|wide piston|\bram\b|lifts? (the|a|your) car|\bload\b"),
                  ("small", r"small piston|narrow piston|handle|\blever\b|pump(s|ing)?\b|\bstrokes?\b|push(es)? down|your (hand|arm)")],
    "elevator": [("snap", r"\bsnaps?\b|(cable|rope) (breaks|fails)|free ?fall|plummet|cut the (cable|rope)"),
                 ("brake", r"safety (gear|brake)|\bbrakes?\b|governor|wedge|clamp|\bgrips?\b|otis"), ("sheave", r"sheave|pulley|\bmotor\b|traction|machine room|friction"),
                 ("counterweight", r"counterweight|balanc"), ("car", r"\bcar\b|\bcab(in)?\b|passengers?|\bdoors?\b|\bfloors?\b")],
    "fridge": [("dirty", r"\bdust|dirty|clogged|clean(ing)? the coils"), ("evaporator", r"evaporat|freez|absorbs? (the )?heat|\bboils?\b|inside the (fridge|box)|\bcold\b"),
               ("valve", r"capillary|expansion|throttl|pressure drops?|narrow tube"),
               ("condenser", r"condens|\bcoils?\b|back of the fridge|out the back|releases? (the )?heat|dumps? (the )?heat|kitchen"),
               ("compressor", r"compressor|\bhum|squeez|\bpump\b|\bmotor\b|\bclick")],
    "transistor": [("off", r"switch(es|ed)? off|turns? off|no current|blocks?|\boff\b"), ("on", r"switch(es|ed)? on|turns? on|current flows|conducts"),
                   ("channel", r"channel|bridge|path|electrons? (gather|collect|line)"), ("gate", r"\bgate\b|voltage|electric field|insulat|oxide"),
                   ("source", r"\bsource\b"), ("drain", r"\bdrain\b")],
    "breaker": [("fuse", r"\bfuses?\b|melts?|wire burns"), ("short", r"short circuit|shorts?\b|thousands? of amps|instant|millisecond|magnet"),
                ("overload", r"overload|too many|too much|kettle|heater|slowly|minutes"), ("arc", r"\barc\b|spark|plasma|chute|plates"),
                ("coil", r"\bcoil\b|solenoid|electromagnet|plunger"), ("bimetal", r"bimetal|\bstrip\b|bends?|two metals|heats? up"),
                ("contacts", r"contacts?|\bsnap|springs?|\bopens?\b|latch")],
    "wall": [("wet", r"condens|\bwet\b|mou?ld|\bdamp|trapped|droplets?|\brots?\b"), ("interior", r"vapou?r barrier|membrane|insulat\w* (on|from) the inside|internal insulation|warm side"),
             ("bare", r"no insulation|uninsulated|bare (brick|wall)|solid (brick|wall)|without insulation"), ("sip", r"\bsips?\b|\bosb\b|sandwich|\bpanels?\b"),
             ("insulation", r"insulation|\bfoam\b|polystyrene|\beps\b|mineral wool"), ("masonry", r"bricks?|blocks?|masonry|concrete|\bstone\b"),
             ("outside", r"outside|outdoor|render|fa[cç]ade|frost|cold air"), ("inside", r"inside|\brooms?\b|plaster|indoor|warm air|surface")],
    "pinlock": [("pick", r"\bpicks?\b|picking|locksmith|tension|wrench|without (the|a) key|one (pin )?at a time|\bbinds?\b"),
                ("wrong", r"wrong key|different key|wrong cut|too (high|low|deep|shallow)|won't turn|will not turn|refuses|\bjams?\b"),
                ("shear", r"shear line|\bgap\b|lines? up|align"), ("drivers", r"driver pins?|top pins?|upper pins?|springs?"),
                ("keypins", r"key pins?|bottom pins?|lower pins?|\bcuts?\b|notch|ridges|different lengths"), ("plug", r"\bplug\b|cylinder|rotat|\bturns?\b|\bcam\b|\bbolt\b")],
    "canal_lock": [("fill", r"fills?\b|filling|water (rushes|flows|pours) in|floods? in"), ("drain", r"drains?|empt(y|ies|ied)|water (rushes|flows|pours) out|is lowered|goes down"),
                   ("valves", r"valves?|culverts?|tunnels?|\bpipes?\b"), ("gates", r"\bgates?\b|\bdoors?\b|mitre|miter|\bseals?\b"),
                   ("chamber", r"chamber|\bfloor\b|\bwalls?\b|concrete"), ("ship", r"\bships?\b|vessel|\bhull\b|tonnes|containers?")],
    "orbit": [("decay", r"decay|\bdrag\b|re-?entr|burns? up|thin air|atmosphere|debris|comes? down"), ("transfer", r"transfer|hohmann|\bburns?\b|higher orbit|rendezvous|change orbit"),
              ("launch", r"launch|rockets?|lift-?off|pitch|gravity turn|reach(es)? orbit|climbs?"), ("types", r"geostationary|low earth|medium earth|\bleo\b|\bgeo\b|\bmeo\b|altitudes?|orbit types"),
              ("fall", r"cannon|newton|thought experiment|throw|fired?|keeps? missing|\bmiss(es)?\b"), ("gravity", r"gravity|\bpulls?\b|falling|weightless"),
              ("speed", r"sideways|speed|kilomet|\bfast|velocity"), ("path", r"orbit|circle|\blaps?\b|around")],
    "jet": [("nozzle", r"nozzle|exhaust|thrust|newton"), ("turbine", r"turbine"), ("combustor", r"combust|\bfuel\b|\bburn|flame|ignit|kerosene"),
            ("compressor", r"compress|squeez|\bstages?\b"), ("fan", r"\bfan\b|bypass|intake|\bblades?\b|\bsucks?")],
    "emotor": [("regen", r"regenerat|recuperat|braking (charges|recharges|puts)|back into the battery|motor becomes a generator|acts as a generator"),
               ("field", r"magnetic field|rotating field|\bfield\b|phases?|three[- ]phase|alternating|\bAC\b|inverter|frequency"),
               ("magnets", r"\bmagnets?\b|\brotor\b|neodymium|rare earth|\bpoles?\b|north|south|attract|repel"),
               ("coils", r"\bcoils?\b|\bstator\b|copper|windings?|electromagnet|current"),
               ("shaft", r"\bshaft\b|torque|\bwheels?\b|axle|gear|output")],
    "car_brake": [("caliper", r"caliper|brake pads?|\bpads?\b|\bpistons?\b|brake fluid|hydraulic|squeez|clamp|pedal"),
                  ("disc", r"\bdis[ck]s?\b|\brotors?\b|\bheat|degrees|glow|friction|\bfade")],
}
FOCUS = {m: [(f, re.compile(r, re.I)) for f, r in _STROKES] for m in ("piston", "wankel", "rotary")}
FOCUS.update({m: [(f, re.compile(r, re.I)) for f, r in v] for m, v in _PARTS.items()})
RUNS = ("piston", "wankel", "rotary", "turbo", "camshaft", "gearbox", "heatpump", "wind_turbine", "emotor")
# zábery, ktoré len posunú kameru (stav stroja nemenia): v rámci jednej scény môže kamera prejsť z jedného na druhý
CAM_ONLY = {"turbo": {"turbine", "shaft", "compressor"}, "camshaft": {"cam", "valve", "belt"}, "car_brake": {"caliper", "disc"},
            "gearbox": {"input", "gears", "collar", "output"}, "differential": {"pinion", "spider"},
            "heatpump": {"evap", "comp", "cond", "valve"}, "wind_turbine": {"rotor", "gearbox", "generator"},
            "solar": {"light", "junction", "circuit"}, "tunnel": {"cutter", "jacks", "rings", "conveyor"},
            "radar": {"antenna", "pulse", "target", "screen"}, "bridge": {"deck", "hangers", "cable", "towers", "anchor"},
            "wing": {"flow", "pressure", "lift"}, "dam": {"reservoir", "wall", "penstock", "turbine", "generator"},
            "submarine": {"tanks", "air", "hull", "propeller", "planes"}, "hydraulic": {"small", "big", "oil", "valves"},
            "elevator": {"car", "counterweight", "sheave", "brake"}, "fridge": {"compressor", "condenser", "valve", "evaporator"},
            "jet": {"fan", "compressor", "combustor", "turbine", "nozzle"},
            "wall": {"inside", "masonry", "insulation", "outside"}, "pinlock": {"keypins", "drivers", "shear", "plug"}, "canal_lock": {"gates", "valves", "chamber", "ship"}, "orbit": {"gravity", "speed", "path"},
            "transistor": {"source", "gate", "drain", "channel"}, "emotor": {"coils", "magnets", "field", "shaft"}, "breaker": {"contacts", "bimetal", "coil", "arc"}}
# tenké schémy, ktoré v krátkom videu o stroji nahradí model (grafy s číslami ostávajú)
SOFT = {"flow", "cycle", "steps", "network", "tree", "layers", "split", "stack", "level", "zoom", "size", "sim", "forces", "myth", "dots",
        "funnel", "venn", "house", "crack", "clock", "matrix"}   # modely, ktoré vedia záber „beží naplno“
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
            "camshaft": r"\blobes?\b|\bvalves?\b|timing|\bcams?\b", "car_brake": r"caliper|\bpads?\b|\bdis[ck]s?\b|friction|brake fluid|pedal",
            "gearbox": r"\bgears?\b|\bshift|clutch|\bratio|synchro|\bshafts?\b", "differential": r"\bwheels?\b|corner|axle|spider|pinion|ring gear|\bturns?\b",
            "solar": r"photons?|electrons?|silicon|junction|sunlight|\bcells?\b|inverter|\bvolts?\b|current",
            "wind_turbine": r"\bblades?\b|nacelle|\brotor\b|gearbox|generator|\byaw|\bpitch|megawatt|\bMW\b|\btower",
            "tunnel": r"cutter ?head|\bcutters?\b|lining|segments?|\brings?\b|\bjacks?\b|conveyor|\bshield\b|\bmuck\b|boring machine|\btbm\b",
            "radar": r"\bpulses?\b|\becho|antenna|\bdish\b|radio waves?|reflect|bounces?|\bblip|\bscreen\b|stealth|microwaves?",
            "bridge": r"\bcables?\b|hangers?|suspenders?|\btowers?\b|anchor|\bdeck\b|suspension|\bspan\b|strands?",
            "wing": r"\blift\b|airflow|air ?foil|angle of attack|\bstall|pressure|\bflaps?\b|leading edge|trailing edge|\bdrag\b",
            "dam": r"reservoir|turbine|penstock|spillway|generator|concrete|\bwall\b|water pressure|megawatt|hydro",
            "submarine": r"ballast|\btanks?\b|pressure hull|\bhull\b|\bdives?\b|surfac|compressed air|buoyan|propeller",
            "hydraulic": r"pistons?|\boil\b|\bfluid\b|pressure|cylinders?|\bvalves?\b|pascal|\blever\b|\bjack\b",
            "elevator": r"counterweight|\bropes?\b|\bcables?\b|sheave|pulley|safety (gear|brake)|governor|\bshaft\b|\brails?\b",
            "fridge": r"compressor|refrigerant|condens|evaporat|\bcoils?\b|\bheat\b|capillary|thermostat",
            "jet": r"\bfan\b|compressor|combust|turbine|nozzle|bypass|thrust|\bblades?\b|\bfuel\b",
            "wall": r"insulat|\blayers?\b|vapou?r|condens|dew point|bricks?|plaster|heat (loss|flows?|escapes?)|u-?value|moisture|\bdamp|membrane",
            "pinlock": r"\bpins?\b|shear line|springs?|\bplug\b|cylinder|\bkeys?\b|\bcuts?\b|\bpicks?\b|tension",
            "canal_lock": r"\bgates?\b|chamber|valves?|culvert|water level|\blifts?\b|gravity|\bfills?\b|drains?|\blocks?\b",
            "orbit": r"gravity|orbit|sideways|speed|\bfalls?\b|falling|altitude|\bburns?\b|\bdrag\b|kilomet",
            "transistor": r"\bgate\b|\bsource\b|\bdrain\b|channel|silicon|electrons?|voltage|switch|current",
            "breaker": r"contacts?|bimetal|\bstrip\b|\bcoil\b|solenoid|\barc\b|\btrips?\b|overload|short circuit|\bamps?\b|\bfuses?\b",
            "emotor": r"\bcoils?\b|\bstator\b|\brotor\b|\bmagnets?\b|magnetic field|copper|windings?|torque|\binverter\b|\bphases?\b|\bshaft\b|\bRPM\b",
            "heatpump": r"compressor|evaporat|condens|expansion valve|\bCOP\b|outdoor unit|kompres|výparn|kondenz|verdicht|verdampf"}
# model vo videu len vtedy, keď text hovorí o tom, ako stroj funguje (reklamné video o tepelnom čerpadle nemá byť celé na reze okruhu)
_NEEDS = {"heatpump": 2, "wind_turbine": 3, "solar": 3, "tunnel": 3, "radar": 3, "bridge": 3, "wing": 3, "dam": 3, "submarine": 3, "hydraulic": 3, "elevator": 3, "fridge": 3, "jet": 3, "transistor": 3, "breaker": 3, "canal_lock": 3, "orbit": 3, "pinlock": 3, "wall": 3, "emotor": 3}


def topic(full, title="", strict=False):
    """Stroj s presným modelom, o ktorom je celé video. Rozhoduje názov videa; bez neho musí stroj v texte jasne prevládať. Inak None.
    strict (hotový scenár): pri strojoch z _NEEDS musí text hovoriť aj o ich častiach, inak video nie je o tom, ako stroj funguje."""
    m = _topic(full, title)
    if strict and m in _NEEDS and len(re.findall(_SUPPORT.get(m, r"$^"), full or "", re.I)) < _NEEDS[m]:
        return None
    return m


# názov menuje stroj, ale video je o jeho inej podobe, ktorú model neukazuje (rekuperačné brzdenie nie je kotúčová brzda): radšej žiadny model
_AVOID = {"car_brake": r"regenerat|single[- ]pedal|elevator|safety gear|engine brak|air brake",
          "gearbox": r"\bcvt\b|no gears|hybrid|direct[- ]drive|cycloidal|dual[- ]mass|dual[- ]clutch|automatic|planetary",
          "gears": r"\bcvt\b|no gears", "wankel": r"[1-9][- ]stroke|one[- ]stroke|rival", "heatpump": r"brushless|\bmotors?\b|\bcost\b",
          "piston": r"opposed|two[- ]stroke|2[- ]stroke|deactivat|diesel|spark plug makes|\bquiz\b|lasts longer",
          "camshaft": r"rotary valve|camless|phaser", "turbo": r"supercharger",
          "wind_turbine": r"\bweld|steel plates|\b1 piece|floats|floating", "solar": r"solar (thermal|water)",
          "tunnel": r"sewer|flood|immersed|float|wind tunnel|drill and blast|\bblast|dynamite|by hand|\bmines?\b|mining|quantum|carpal|\bvpn\b|\bquiz\b|\bsink|riverbed|underwater|breathe|chimney|\bair\b|\bfire\b|\brain\b|drain|pump|stream|\bpipes?\b|never (came|dry)|stay cool|poured|below it all|cross passages|alive|future",
          "bridge": r"paint|holes in|americas|\bships?\b|too low|\barch|truss bridge|draw ?bridge|bascule|cable[- ]stayed|pontoon|float|covered|beam bridge|\brope|land bridge|rectifier|cantilever|viaduct|aqueduct|\bstone|roman|lift bridge|swing|movable|\bopens?\b|\bquiz\b|\bship'?s? bridge|dental|card game",
          "wing": r"holds itself|wobble|crosswind|wing low|grounded|winglet|swept|sweep|\bflex|\bbend|fold|\bbirds?\b|insect|wingtip|vortex|vortices|turbulence|\bice\b|icing|fuel|wingspan|delta|flying wing|\bquiz\b|buffalo|chicken|right[- ]wing|left[- ]wing|rivet|\bspar\b",
          "dam": r"beaver|drained itself|moved sideways|tailings|landslide|ice dam|pumped|tidal|\bdike|\bquiz\b|rain reservoir",
          "submarine": r"\bships? dump|cargo|container ships?|invasive|species|torpedo|sound layer|layers of sound|silent|silence|quiet|nois|signature|\bhunt|aircraft|find(ing)? submarines|vanish|\bhides?\b|detection|sonar|cable|\bquiz\b",
          "hydraulic": r"brak|excavator|fracking|fractur|hydraulic jump|elevator|\bquiz\b",
          "elevator": r"space elevator|never stops|paternoster|puzzle|wrong one|grain|\bquiz\b",
          "fridge": r"magnet|smart fridge|door seal|absorption|gas fridge|\bquiz\b|ice ?maker|defrost",
          "wall": r"\bdrill|\bquiz\b|\broof|\bloft|attic|noise|sound|great wall|firewall|wall street|\bpaint|cracks?|shel(f|ves)|wall plug",
          "pinlock": r"smart lock|electronic|\bquiz\b|padlock|seat ?belt|canal|67 years",
          "canal_lock": r"\bquiz\b|suez|pay by|too wide",
          "emotor": r"\bquiz\b|stepper|linear motor|maglev|motor ?(oil|cycle|way|home|boat|racing|sport)|motorist|motor vehicle|motor neurons?|motor skills|motor cortex",
          "orbit": r"\bgps\b|submarine|\bspot|\bsees?\b|see through|\bjam|millimet|early warning|\bpings?\b|without gps|\bimages?\b|camera|\bspy|\bquiz\b|navigation|indoors|internet",
          "transistor": r"vacuum tube|from sand|\d+ steps|wafer|\bquiz\b|shortage",
          "breaker": r"\brcd\b|\bgfci\b|shock|multimeter|blown? your|\bquiz\b|fuse box|fused? (together|into)|fusion",
          "jet": r"jet stream|jet lag|jet ski|jet ?pack|water ?jet|inkjet|ramjet|scramjet|\bquiz\b",
          "radar": r"sonar|lidar|speed (camera|trap|gun)|weather|\bquiz\b|microwave oven|candy|chocolate|passive|never transmits|phased|from space|\bimages?\b|mapping|sensor fusion|hopping|beamforming|signal processing|whisper|reveals its own|turn off|horizon|bomber|warning receivers?|locked on|lost fights"}


# Video o lietadle hovorí o prúdovom motore len „engine“ (vták v motore): ráta sa, keď text pozná aspoň 4 jeho časti.
_ALIAS = {"jet": (r"\b(?:air)?planes?\b|aircraft|airliner|\bpilots?\b|cockpit", r"\bengines?\b", 4, 12)}


def _alias(m, full):
    a = _ALIAS.get(m)
    if not a or len(re.findall(a[0], full, re.I)) < 3:
        return 0
    sup = re.findall(_SUPPORT.get(m, r"$^"), full, re.I)
    if len({w.lower().rstrip("s") for w in sup if isinstance(w, str)}) < a[2] or len(sup) < a[3]:
        return 0
    return len(re.findall(a[1], full, re.I)) // 4


def _topic(full, title=""):
    hit = find(title or "")
    if hit:
        if hit[0] in _AVOID and re.search(_AVOID[hit[0]], title, re.I):
            return None
        return hit[0] if hit[0] in PRECISE else None   # video je o inom stroji: jeho model nesmie zabrať celé video
    score, named = {}, {}
    for m in dict.fromkeys(m for _, m, _ in _RX):
        strong = sum(len(rx.findall(full or "")) for rx, mm, _ in _RX if mm == m) + _alias(m, full or "")
        if strong:
            named[m] = strong
            score[m] = 2 * strong + len(re.findall(_SUPPORT.get(m, r"$^"), full or "", re.I))
    best = sorted(score.items(), key=lambda kv: -kv[1])
    if not best or best[0][0] not in PRECISE or best[0][1] < (10 if (title or "").strip() else 6):
        return None   # názov, ktorý stroj nemenuje, je slabší dôkaz: stroj musí v texte prevládať výrazne
    if (title or "").strip() and (named[best[0][0]] < 3 or len({w.lower() if isinstance(w, str) else "".join(w).lower()
                                                               for w in re.findall(_SUPPORT.get(best[0][0], r"$^"), full or "", re.I)}) < 3):
        return None   # stroj padne v texte raz či dvakrát (hra „Radar Scope“) alebo slovo znamená iné (hotelové „wing“) a z jeho častí text pozná len jedno bežné slovo: video o ňom nie je
    if len(best) > 1 and best[0][1] < 1.5 * best[1][1]:
        return None   # dva stroje sú v texte zhruba rovnako: bez názvu videa sa nedá povedať, o ktorom je
    return best[0][0]


NAMES = {"emotor": "Electric motor", "piston": "Piston engine", "wankel": "Rotary engine", "rotary": "Rotary engine", "gears": "Gears", "turbo": "Turbocharger", "camshaft": "Camshaft", "car_brake": "Disc brake", "gearbox": "Gearbox", "differential": "Differential", "heatpump": "Heat pump", "wind_turbine": "Wind turbine", "solar": "Solar panel", "tunnel": "Tunnel boring machine", "radar": "Radar", "bridge": "Suspension bridge", "wing": "Wing", "dam": "Hydroelectric dam", "submarine": "Submarine", "hydraulic": "Hydraulic jack", "elevator": "Elevator", "fridge": "Refrigerator", "jet": "Jet engine", "wall": "Wall cross-section", "pinlock": "Pin tumbler lock", "canal_lock": "Canal lock", "orbit": "Orbit", "transistor": "Transistor", "breaker": "Circuit breaker"}
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
            IN = 1.15 if v.get("_first") else max(1.7, min(2.8, dur * .3))
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
        elif m == "wind_turbine":
            if f in ("", "rotor", "run"):
                kind, hits = "air", [.5]
        elif m == "heatpump":   # ventilátor ženie vzduch, za ventilom chladivo zasyčí
            if f in ("", "evap", "valve"):
                kind, hits = ("hiss" if f == "valve" else "air"), [.5]
        hits = [h for h in hits if 0 <= h and t0 + sh + h < end]
        if len(hits) > 5:   # pri behu naplno stačí pár úderov, nie každý zážih
            hits = hits[::-(-len(hits) // 5)]
        for h in hits:
            if True:
                ev.append((kind, t0 + sh + h))
    return sorted(ev, key=lambda e: e[1])


def shots(v, words, t0):
    """Kamera za hlasom: [[časť, čas od začiatku scény], …], keď hlas v jednej scéne hovorí postupne o viacerých častiach. Inak None.
    Berú sa len zábery, ktoré menia iba kameru (CAM_ONLY); na jednej časti kamera ostane aspoň 2 s."""
    m, f0 = v.get("m"), v.get("f") or ""
    cam = CAM_ONLY.get(m)
    if v.get("k") != "mech" or not cam or (f0 and f0 not in cam):
        return None
    text, starts = "", []
    for w in words:
        starts.append((len(text), float(w.get("s") or 0)))
        text += str(w.get("w") or "") + " "
    ev = []
    for f, rx in FOCUS.get(m, ()):
        if f in cam:
            for mt in rx.finditer(text):
                at = [s for o, s in starts if o <= mt.start()]
                ev.append((round(max(0.0, (at[-1] if at else t0) - t0), 2), f))
    ev.sort()
    # poradie určuje hlas; záber z nadpisu (f0) ide prvý len vtedy, keď hlas o prvej časti prehovorí až neskôr
    seq = [[f0, 0.0]] if f0 and (not ev or ev[0][0] > 2.4) else []
    for t, f in ev:
        if not seq:
            seq.append([f, 0.0 if t <= 2.4 else t])
        elif seq[-1][0] != f and t - seq[-1][1] >= 2.0:
            seq.append([f, t])
    return seq if len(seq) >= 2 or (seq and not f0) else None


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


def _state(out, used):
    """Diferenciál: keď video drží jedno koleso, drží ho aj v ďalších záberoch (kým nepríde jazda rovno alebo zákruta)."""
    if out.get("m") == "differential":
        f = out.get("f") or ""
        if f == "hold":
            used["_hold"] = 1
        elif f in ("straight", "turn"):
            used["_hold"] = 0
        elif used.get("_hold"):
            out = dict(out, h=1)
    return out


# ---------- „kto komu“: scéna z ikon sa ukáže ako nakreslení účastníci, medzi ktorými naozaj niečo putuje (PRO.actors) ----------
_SPRITE = {n: k for k, v in {
    "person": "user boss soldier worker customer man woman person employee driver investor", "crowd": "people users family team group audience community",
    "phone": "phone smartphone mobile", "screen": "tv play video monitor", "laptop": "laptop computer online_shop", "router": "wifi router antenna",
    "house": "house home village", "city": "city office skyscraper building town", "shop": "store shop supermarket", "bank": "bank capitol government",
    "factory": "factory", "server": "server database", "cloud": "cloud cloud_upload", "doc": "document contract receipt invoice clipboard", "mail": "mail",
    "calendar": "calendar", "wallet": "wallet", "coins": "coins moneybag money gold", "coin": "coin dollar euro", "cash": "banknote", "piggy": "piggybank",
    "tag": "pricetag percent", "lock": "lock", "shield": "shield", "key": "key", "chart": "chart", "chart_down": "chart_down", "growth": "growth",
    "box": "box package gift pallet crate parcel boxes", "bag": "shopping_bag cart", "truck": "truck forklift van lorry", "warehouse": "warehouse depot hub storage", "container": "container", "plane": "plane", "ship": "ship", "globe": "globe map globe_pin",
    "check": "check", "cross": "cross", "clock": "clock hourglass", "bulb": "idea bulb", "chip": "chip", "drop": "drop water tap", "bolt": "bolt electricity lightning power",
    "flame": "flame fire", "snow": "snow snowflake cold", "leaf": "leaf plant", "car": "car taxi", "tank": "tank barrel", "pump": "pump", "battery": "battery",
    "card": "card credit_card", "air": "air wind", "camera": "camera photo image", "pin": "pin location marker", "search": "search magnifier",
    "tree": "tree forest", "robot": "robot", "satellite": "satellite", "gear": "gear cog settings", "eye": "eye", "sun": "sun", "flag": "flag", "plug": "plug charger socket", "tool": "tool wrench repair", "touch": "touch tap finger"}.items() for n in v.split()}
_TOKEN = [(k, re.compile(r, re.I)) for k, r in (
    ("coin", r"[$€£¥]|\b(pay|pays|paid|payments?|prices?|fees?|profits?|margins?|money|cash|rent|salary|wages?|costs?|tax|taxes|interest|loans?|lends?|funds?|"
             r"revenue|income|dividends?|invest\w*|buys?|sales?|sells?|spends?|debt|refunds?|deposits?|bills?|charges?|subsid\w*|premiums?|tips?|coins?|"
             r"savings?|earn\w*|budget|credit|returned|cashback|discount)\b"),
    ("box", r"\b(box|boxes|goods|products?|ships?|shipping|deliver\w*|stock|cargo|parcels?|orders?|supply|supplies|unload\w*|imports?|exports?|food|parts|items?)\b"),
    ("person", r"\b(crowds?|customers?|visitors?|shoppers?|fans?|viewers?|users?|people|workers?|travell?ers?|passengers?|tourists?|migra\w*|joins?|hires?|"
               r"subscribers?|players?|families|soldiers?|troops)\b"),
    ("doc", r"\b(contracts?|copy|copies|papers?|invoices?|reports?|receipts?|letters?|tickets?|licen[cs]es?|patents?|laws?|rules?|plans?|forms?|permits?|deal|agreements?|results?)\b"),
    ("data", r"\b(data|links?|signals?|connect\w*|sends?|passwords?|log ?in|requests?|stream\w*|cast|click\w*|messages?|upload\w*|download\w*|track\w*|traffic|"
             r"code|wi-?fi|app|notif\w*|info\w*|search\w*|scan\w*|sync\w*|posts?|watch\w*|shares?|invites?|ads?|email|texts?|calls?|updates?|play|power)\b"))]
_TOKEN_SRC = {"coin": "wallet coins coin cash piggy bank", "box": "truck box ship factory bag warehouse container", "data": "phone router server cloud laptop screen chip", "drop": "drop tank pump"}
_STOP = re.compile(r"(?i)\b(block\w*|denied|reject\w*|fail\w*|stopp?\w*|banned|can'?t|cannot|refus\w*|no access|cut off|locked out)\b")


def actors(d):
    """Scéna, rad ikon alebo jednoduchá kresba (ikona, šípka, ikona) → presný blok „kto komu“. None, keď účastníkov nevieme nakresliť:
    každý musí mať vlastnú kresbu, pri troch a viac smie jeden ostať čiarovou ikonou na tabuľke."""
    k, nodes, edges = d.get("k"), [], []
    try:
        if k == "scene":
            nodes = [[str(q[0]), str(q[1] if len(q) > 1 else "")] for q in d.get("n") or [] if isinstance(q, list) and q]
            edges = [[int(e[0]), int(e[1]), str(e[2] if len(e) > 2 else ""), 1 if len(e) > 3 and e[3] else 0] for e in d.get("l") or [] if isinstance(e, list) and len(e) > 1]
        elif k == "icons":
            nodes = [[str(q[0]), str(q[1] if len(q) > 1 else "")] if isinstance(q, list) else [str(q), ""] for q in d.get("i") or [] if q]
        elif k == "draw":
            el = [e for e in d.get("e") or [] if isinstance(e, dict)]
            note = [str(e.get("t") or "").strip() for e in el if e.get("s") == "text"]
            el = [e for e in el if e.get("s") != "text"]
            if len(note) > 1 or any(e.get("s") not in ("icon", "arrow") for e in el):
                return None
            arrow = None
            for e in el:
                if e.get("s") == "icon":
                    nodes.append([str(e.get("i") or ""), str(e.get("l") or "")])
                    if arrow is not None and len(nodes) > 1:
                        edges.append([len(nodes) - 2, len(nodes) - 1, arrow, 1 if e.get("c") else 0])
                    arrow = None
                elif nodes:
                    arrow = str(e.get("l") or "")
            if note and len(edges) == 1 and not edges[0][2] and len(note[0]) <= 26:
                edges[0][2] = note[0]   # jediný popis pod kresbou patrí k jej jedinej šípke
        else:
            return None
    except (TypeError, ValueError):
        return None
    n = len(nodes)
    if not 2 <= n <= 4 or len(edges) > 4 or any(not (0 <= a < n and 0 <= b < n and a != b) for a, b, *_ in edges):
        return None
    nd = [[_SPRITE.get(i.lower().strip()) or "ico:" + i, l] for i, l in nodes]
    if sum(1 for q in nd if q[0].startswith("ico:")) > (1 if n >= 3 else 0):
        return None
    ed = []
    for a, b, l, hl in edges:
        tok = next((t for t, rx in _TOKEN if rx.search(l)), None) or next((t for t, src in _TOKEN_SRC.items() if nd[a][0] in src.split()), "dot")
        ed.append([a, b, l, hl, tok, 1 if _STOP.search(l) else 0])
    return {"k": "mech", "m": "actors", "nd": nd, "ed": ed}


def _fill(d, topic, used, scene, lang):
    """Slabá scéna, ktorá v dlhom videu ostáva bez modelu. Bola tam kresba od AI (prázdna náhrada)? Ukáže sa ďalší záber na inú časť modelu,
    inak aspoň nadpis scény: prázdna scéna nesmie vzniknúť nikdy."""
    if d.get("k") != "text" or str(d.get("w") or "").strip():
        return actors(d) or d
    parts = sorted(p for p in CAM_ONLY.get(topic, ()) if (topic, p) != used.get("_last"))
    if parts:
        f = parts[used.get("_fill", 0) % len(parts)]
        used["_fill"] = used.get("_fill", 0) + 1
        used["_last"] = (topic, f)
        return _state(dict({"k": "mech", "m": topic, "f": f}, **({"l": _LABELS[topic]} if _LABELS.get(topic) and lang == "en" else {})), used)
    return {"k": "text", "w": str(scene.get("onscreen") or "")}


def upgrade(d, scene, spoken, used, lang="en", prev=None, long=False, full="", topic=None, last=False):
    """d = diagram scény. Vráti diagram, ktorý sa naozaj ukáže.
    topic = stroj, o ktorom je celé video: slabé scény (ikony, text) vtedy ukazujú jeho presný model a kamera ide
    na to, o čom scéna hovorí. Mimo témy videa sa model doplní, len keď scéna sama hovorí o stroji s presným modelom."""
    d = calm_draw(d)
    texts = (scene.get("onscreen") or "", scene.get("visual") or "", spoken or "")
    if topic and (d.get("k") == "svg" or (not long and d.get("k") in SOFT | {"count"}) or (d.get("k") == "mech" and d.get("m") not in PRECISE)):
        d = {"k": "text"}   # kresba od AI, stará hrubá schéma alebo (v krátkom videu) samotné číslo: ukáže sa presný model, číslo naskočí pri ňom
    if d.get("k") == "mech":
        if d.get("m") in FOCUS and not d.get("f"):
            f = focus(d["m"], *texts)
            if f and used.get("_last") != (d["m"], f):
                d = dict(d, f=f)
        used["_last"] = (d.get("m"), d.get("f") or "")
        return _state(d, used)
    if d.get("k") not in WEAK:
        return d
    if topic and last:   # záverečná výzva: stroj beží ďalej, text výzvy je v nadpise scény
        f = "run" if topic in RUNS and used.get("_last") != (topic, "run") else ""
        used["_last"] = (topic, f)
        return _state(dict({"k": "mech", "m": topic}, **({"f": f} if f else {}), **({"l": _LABELS[topic]} if _LABELS.get(topic) and lang == "en" else {})), used)
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
                return _fill(d, topic, used, scene, lang)   # v dlhom videu nie dva celkové pohľady po sebe
            f = "run" if topic in RUNS and used.get("_ov", 0) % 2 else ""
            used["_ov"] = used.get("_ov", 0) + 1
        if prev == topic and used.get("_last") == (topic, f):   # nikdy ten istý záber dvakrát po sebe: iná časť, beh naplno alebo celok
            alt = [g for g in focuses(topic, *texts) + (["run"] if topic in RUNS else []) + [""] if (topic, g) != used.get("_last")]
            if long or not alt:
                return _fill(d, topic, used, scene, lang)
            f = alt[0]
        used["_last"] = (topic, f)
        out = {"k": "mech", "m": topic}
        if f:
            out["f"] = f
        if _LABELS.get(topic) and lang == "en":
            out["l"] = _LABELS[topic]
        return _state(out, used)
    # radšej žiadny model než nesúvisiaci: stroj musí byť v nadpise/opise scény, alebo ho hlas spomína a video je o ňom
    hit = find(f"{texts[0]} . {texts[1]}")
    if not hit:
        hit = find(spoken)
        if hit and sum(len(rx.findall(full or "")) for rx, m, _ in _RX if m == hit[0]) < 3:
            hit = None
    if hit and (re.search(_AVOID.get(hit[0], r"$^"), (full or "") + " . " + " . ".join(texts), re.I)
                or sum(len(rx.findall(full or "")) for rx, mm, _ in _RX if mm == hit[0]) < 3
                or len(re.findall(_SUPPORT.get("wankel" if hit[0] == "rotary" else hit[0], r"$^"), full or "", re.I)) < _NEEDS.get(hit[0], 2)):
        hit = None   # video nie je o stroji: jeho model sa ukáže, len keď o ňom text naozaj hovorí (aspoň 3×, aj o jeho častiach) a slovo nemá iný význam (VPN „tunnel“, „brake“ na úvery, balastné nádrže nákladnej lode)
    if not hit or hit[0] not in PRECISE or hit[0] == "actors":   # len stroje s presným modelom; inak účastníci scény nakreslení („kto komu“)
        return actors(d) or d
    m, labels = hit
    if used.get(m, 0) >= (3 if long else 2) or prev == m:
        return actors(d) or d
    used[m] = used.get(m, 0) + 1
    used["_last"] = (m, "")
    out = {"k": "mech", "m": m}
    if labels and lang == "en":
        out["l"] = labels
    return out
