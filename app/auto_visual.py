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
    (r"lithium[- ]ion|li-ion|\blithium batter|batter(y|ies) (wears?|wear out|degrad\w*|health|life|cells?|chemistry|ages?|aging)|phone batter\w*|how (a |the )?batter(y|ies) works?|\banodes?\b|\bcathodes?\b|charge cycles?",
     "battery", ["Anode", "Cathode", "Separator", "Electrons"]),
    (r"electric motors?|e-?motors?|ev motors?|traction motors?|induction motors?|brushless|permanent[- ]magnet motors?|synchronous motors?|servo ?motors?|\bstator\b|regenerative braking|motor (spins|turns)", "emotor",
     ["Stator coils", "Rotor magnets", "Magnetic field", "Shaft"]),
    (r"hurricanes?|typhoons?|tropical cyclones?|cyclones? forms?|\beye of the storm|\beyewall|category 5|saffir", "hurricane",
     ["Warm ocean", "Eyewall", "Eye", "Outflow"]),
    (r"touch ?screens?|touch[- ]sensitive|capacitive|multi-?touch|how (your |a |the )?(phone|smartphone) (screen )?(knows|senses|feels|detects) (your )?(touch|finger)|pinch to zoom|screen (knows|senses|feels) (your )?finger|knows where you (touch|tap)", "touchscreen",
     ["Electrode grid", "Finger", "Controller", "Glass"]),
    (r"\bneurons?\b|nerve cells?|nerve signals?|synaps\w+|neurotransmitter|how (the |your )?brain (works|sends|thinks|learns|remembers|signals)|\baxons?\b|myelin", "neuron",
     ["Dendrites", "Cell body", "Axon", "Synapse"]),
    (r"robot(ic)? arms?|industrial robots?|factory robots?|welding robots?|robots? (in|on) (the |a )?(factory|assembly|car plant)|pick[- ]and[- ]place|cobots?|\brobotics?\b|robots? (build|weld|assemble|make)", "robot_arm",
     ["Base", "Shoulder", "Elbow", "Gripper"]),
    (r"transistors?\b|mosfet", "transistor", ["Source", "Gate", "Drain", "Channel"]),
    (r"circuit breakers?|breaker trips?|\bfuses?\b|\bmcb\b", "breaker", ["Contacts", "Bimetal strip", "Solenoid", "Arc chute"]),
    (r"hard ?disks?|hard ?drives?|\bhdds?\b|read/write heads?|\bplatters?\b", "harddrive",
     ["Platter", "Head", "Spindle"]),
    (r"transformer|high voltage|substation", "transformer", ["Primary coil", "Iron core", "Secondary coil"]),
    (r"\bzipp?ers?\b|zip fasteners?|\bzips\b", "zipper", ["Teeth", "Slider"]),
    (r"tower cranes?|construction cranes?|\bjibs?\b|\bcranes?\b", "crane", ["Counterweight", "Trolley", "Hook"]),
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
    "circuit": [("battery", r"battery|cell|volt|power source"), ("switch", r"switch|open|closed|break|loop"), ("bulb", r"bulb|lamp|light|glow")],
    "wave": [("crest", r"crest|peak|top|hump"), ("particle", r"particles?|bob|move up|moves? up|rope|wave"), ("wave", r"wave|travel|energy|wavelength")],
    "cpu": [("clock", r"clock|hz|ghz|pace|tick|frequency"), ("bus", r"bus|wires?|signal|lines?|transfer"), ("cores", r"cores?|processor|chip|transistors?|cpu")],
    "parachute": [("canopy", r"canopy|parachute|dome|cloth|fabric"), ("lines", r"lines?|cords?|strings?|ropes?"), ("load", r"load|person|jumper|harness|body|weight")],
    "trajectory": [("peak", r"peak|highest|top of|apex|halfway"), ("landing", r"land|hits? the ground|falls? back|lands"), ("launch", r"launch|throw|fired?|shot|angle|kick")],
    "escalator": [("steps", r"step|stair|tread"), ("drive", r"motor|drive|chain|top|pulls?")],
    "conveyor": [("rollers", r"roller|drum|pulley|spin|turn"), ("load", r"load|box|boxes|package|parcel|cargo|goods|items?")],
    "pulley": [("wheel", r"pulley|wheel|sheave|axle"), ("rope", r"rope|cable|\bline\b|pull"), ("load", r"load|lift|hoist|weight|box")],
    "lever": [("load", r"load|weight|lift|heavy|rock|boulder"), ("effort", r"effort|push|press|pull|\bforce\b"), ("fulcrum", r"fulcrum|pivot|balance point|support")],
    "rocket": [("nose", r"nose|payload|capsule|upper stage|second stage"), ("booster", r"booster|first stage|lower stage|stages?|separat"), ("nozzle", r"nozzle|engines?|thrust|exhaust|burn")],
    "zipper": [("teeth", r"teeth|tooth|interlock|rows?"), ("slider", r"slider|\bpulls?\b|\btab\b|zip(per)? (up|down)")],
    "drill": [("motor", r"motor|chuck|body|trigger|battery"), ("bit", r"\bbit\b|drill|hole|spiral|twist|rotat"), ("chips", r"chips?|dust|debris|shavings|cut")],
    "generator": [("turbine", r"turbine|blades?|water|steam|wind|spin"), ("stator", r"stator|coils?|copper|wires?|induc"), ("bulb", r"bulb|light|lamp|output|electric|power")],
    "fission": [("fuel", r"fuel|uranium|rods?|atoms?|split|nucle"), ("control", r"control|absorb|boron|cadmium|slow"), ("steam", r"steam|turbine|water|heat|cool")],
    "rotor": [("rotor", r"rotor|blades?|lift|propeller|spin"), ("tail", r"tail|torque|yaw"), ("air", r"air|push|downwash|wind")],
    "aircon": [("indoor", r"indoor|inside|room|fan"), ("outdoor", r"outdoor|outside|compressor|condenser"), ("pipe", r"pipe|refrigerant|coolant|gas|loop")],
    "pendulum": [("pivot", r"pivot|hinge|hang|suspend|support"), ("rod", r"rod|arm|length|rope|string"), ("bob", r"bob|weight|mass|swing|period")],
    "transformer": [("secondary", r"secondary|output|\blow voltage|\b23 ?V\b|\blamp\b|bulb|\bload\b"), ("primary", r"primary|input|\b230 ?V\b|\bplug\b|mains"), ("core", r"\bcore\b|iron|steel|\bflux\b|magnetic|\blaminat")],
    "crane": [("trolley", r"trolley|\bjib\b|\barm\b|\bboom\b|moves? (along|out|in)"), ("hook", r"\bhook\b|\bcable\b|\brope\b|\bload\b|lift|lower"), ("counterweight", r"counterweight|\bbalance\b|\bmast\b|\btower\b|\bweight\b")],
    "harddrive": [("head", r"\bhead\b|flies|flying|\bnm\b|air cushion|hover|gap|reads?\b|writes?\b"), ("spindle", r"spindle|\bmotor\b|\bspins?\b|\brpm\b|\bhub\b|rotates?"), ("platter", r"platter|\bdisks?\b|tracks?|sectors?|\bbits?\b|magnetic")],
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
    "battery": [("wear", r"wears? out|degrad|aging|ages|capacity (drops|falls|loss)|\bSEI\b|trapped|lose|80 ?%|cycles?"),
                ("charge", r"\bcharg(e|es|ing|er)\b|plug(ged)? in|fast charg|recharg"),
                ("separator", r"separator|short circuit|\bfire\b|thermal runaway|puncture"),
                ("anode", r"anode|graphite|negative (side|electrode)"),
                ("cathode", r"cathode|cobalt|nickel|metal oxide|\bLFP\b|\biron phosphate|positive (side|electrode)"),
                ("circuit", r"electrons?|\bwires?\b|current|power(s)? (your|the) (phone|car)|circuit")],
    "hurricane": [("landfall", r"landfall|hits? (land|the coast)|makes landfall|over land|weakens|dies (out|down)|inland|storm surge"),
                  ("eye", r"\beye\b|calm|clear sky|sinking|blue sky|quiet center"),
                  ("ocean", r"ocean|warm water|sea surface|26|27|evaporat|\bfuel\b|moisture|\bheat\b"),
                  ("outflow", r"outflow|\btop\b|spreads? out|exhaust|upper|altitude|chimney"),
                  ("eyewall", r"eyewall|wall|rising|rises|towers?|thunderstorms?|rain|winds?|condens|spin|rotat|coriolis")],
    "touchscreen": [("pinch", r"pinch|two fingers|multi-?touch|zoom|several fingers|ten fingers"),
                    ("glass", r"\bglass\b|layers?|gorilla|\bthin\b|beneath|under the (glass|screen)|gloves?|water|wet"),
                    ("controller", r"controller|chip|measures?|calculat|coordinates|times a second|\bHz\b|scan|position"),
                    ("finger", r"finger|skin|conduct|\bbody\b|charge|stylus|steals?|borrow"),
                    ("grid", r"\bgrid\b|electrodes?|rows?|columns?|lines|transparent|\bITO\b|indium")],
    "neuron": [("synapse", r"synaps|neurotransmitter|dopamine|serotonin|\bgap\b|chemical|receptor|vesicle"),
               ("axon", r"\baxons?\b|myelin|\bjumps?\b|speed|fast|\bm/s\b|insulat|travels?|signal moves"),
               ("soma", r"cell body|threshold|\bfires?\b|firing|millivolt|\bmV\b|all[- ]or[- ]nothing|spike|action potential|voltage"),
               ("dendrites", r"dendrit|branches|inputs?|receives?|listens?|connections?")],
    "robot_arm": [("weld", r"\bweld|spark|\bseams?\b|car bod(y|ies)|spot weld"),
                  ("gripper", r"gripp|grab|\bpicks?\b|\bhand\b|finger|\bplace\b|\bholds?\b|suction"),
                  ("elbow", r"elbow|\breach|forearm|inverse kinematics|\bpath\b|precis"),
                  ("shoulder", r"shoulder|\bmotors?\b|servo|\bjoints?\b|\baxis|\baxes|gearbox|torque"),
                  ("base", r"\bbase\b|rotat|bolted|\bfloor\b|\bcages?\b|safety")],
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
RUNS = ("piston", "wankel", "rotary", "turbo", "camshaft", "gearbox", "heatpump", "wind_turbine", "emotor", "robot_arm")
# zábery, ktoré len posunú kameru (stav stroja nemenia): v rámci jednej scény môže kamera prejsť z jedného na druhý
CAM_ONLY = {"harddrive": {"platter", "head", "spindle"}, "circuit": {"battery", "switch", "bulb"}, "wave": {"wave", "particle", "crest"}, "cpu": {"cores", "bus", "clock"}, "parachute": {"canopy", "lines", "load"}, "trajectory": {"launch", "peak", "landing"}, "escalator": {"steps", "drive"}, "conveyor": {"rollers", "load"}, "pulley": {"wheel", "rope", "load"}, "lever": {"load", "effort", "fulcrum"}, "rocket": {"nose", "booster", "nozzle"}, "zipper": {"teeth", "slider"}, "drill": {"motor", "bit", "chips"}, "generator": {"turbine", "stator", "bulb"}, "fission": {"fuel", "control", "steam"}, "rotor": {"rotor", "tail", "air"}, "aircon": {"indoor", "outdoor", "pipe"}, "pendulum": {"pivot", "rod", "bob"}, "transformer": {"core", "primary", "secondary"}, "crane": {"trolley", "hook", "counterweight"}, "turbo": {"turbine", "shaft", "compressor"}, "camshaft": {"cam", "valve", "belt"}, "car_brake": {"caliper", "disc"},
            "gearbox": {"input", "gears", "collar", "output"}, "differential": {"pinion", "spider"},
            "heatpump": {"evap", "comp", "cond", "valve"}, "wind_turbine": {"rotor", "gearbox", "generator"},
            "solar": {"light", "junction", "circuit"}, "tunnel": {"cutter", "jacks", "rings", "conveyor"},
            "radar": {"antenna", "pulse", "target", "screen"}, "bridge": {"deck", "hangers", "cable", "towers", "anchor"},
            "wing": {"flow", "pressure", "lift"}, "dam": {"reservoir", "wall", "penstock", "turbine", "generator"},
            "submarine": {"tanks", "air", "hull", "propeller", "planes"}, "hydraulic": {"small", "big", "oil", "valves"},
            "elevator": {"car", "counterweight", "sheave", "brake"}, "fridge": {"compressor", "condenser", "valve", "evaporator"},
            "jet": {"fan", "compressor", "combustor", "turbine", "nozzle"},
            "wall": {"inside", "masonry", "insulation", "outside"}, "pinlock": {"keypins", "drivers", "shear", "plug"}, "canal_lock": {"gates", "valves", "chamber", "ship"}, "orbit": {"gravity", "speed", "path"},
            "transistor": {"source", "gate", "drain", "channel"}, "emotor": {"coils", "magnets", "field", "shaft"}, "battery": {"anode", "cathode", "separator", "circuit"}, "robot_arm": {"base", "shoulder", "elbow", "gripper"}, "neuron": {"dendrites", "soma", "axon", "synapse"}, "touchscreen": {"grid", "finger", "controller", "glass"}, "hurricane": {"ocean", "eyewall", "eye", "outflow"}, "breaker": {"contacts", "bimetal", "coil", "arc"}}
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
_SUPPORT = {"circuit": r"circuits?|battery|switch|bulbs?|current|electrons?", "wave": r"waves?|crests?|troughs?|wavelength|energy|oscillat", "cpu": r"processors?|cpus?|chips?|cores?|transistors?|clock|bus", "parachute": r"parachutes?|canopy|drag|lines?|jumper|skydiv", "trajectory": r"trajector\w*|parabola|projectile|launch|gravity|arc", "escalator": r"steps?|stairs?|treads?|handrails?|chains?|motor|escalator", "conveyor": r"rollers?|belts?|conveyor|loads?|boxes|drums?", "pulley": r"pulleys?|wheels?|ropes?|cables?|sheaves?|loads?|lift", "lever": r"levers?|fulcrum|pivot|effort|load|arms?", "rocket": r"rockets?|stages?|boosters?|thrust|nozzles?|fuel", "zipper": r"zippers?|teeth|slider|interlock", "drill": r"drills?|bits?|chips?|spiral|rotat|hole", "generator": r"generators?|turbines?|coils?|magnets?|rotors?|stators?", "fission": r"fission|uranium|neutrons?|reactors?|fuel|control rods?", "rotor": r"rotors?|blades?|helicopter|tail|lift", "aircon": r"air conditioner|indoor|outdoor|refrigerant|compressor|condenser", "pendulum": r"pendulums?|swings?|bob|period|clock", "transformer": r"primary|secondary|\bcoils?\b|\bcore\b|\bflux\b|windings?|turns", "crane": r"trolley|\bjib\b|counterweight|\bhook\b|\bmast\b|\bcables?\b|\bropes?\b", "harddrive": r"platter|\bhead\b|spindle|\bbits?\b|magnetic|tracks?|sectors?|actuator|flies|\bnm\b", "wankel": r"\brotors?\b|\bpockets?\b|\brotary\b|housing", "piston": r"crankshaft|\bstrokes?\b|\bvalves?\b|connecting rod",
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
            "battery": r"\bions?\b|anode|cathode|electrolyte|separator|lithium|electrons?|graphite|cobalt|charge cycles?|capacity",
            "hurricane": r"\beye\b|eyewall|warm|ocean|winds?|rain|clouds?|evaporat|condens|rising|spin|storm|category|km/h|mph",
            "touchscreen": r"finger|electrodes?|\bgrid\b|capacit|charge|glass|controller|touch|coordinates|pinch|layers?|conduct",
            "neuron": r"neurons?|synaps|axons?|dendrit|myelin|signal|electric|voltage|chemical|fires?|firing|brain|nerve|neurotransmitter|threshold",
            "robot_arm": r"\bjoints?\b|\bmotors?\b|servo|gripp|\bweld|\barms?\b|elbow|shoulder|precis|\baxis|\baxes|repeat|\bcars?\b|factory|assembly|program",
            "emotor": r"\bcoils?\b|\bstator\b|\brotor\b|\bmagnets?\b|magnetic field|copper|windings?|torque|\binverter\b|\bphases?\b|\bshaft\b|\bRPM\b",
            "heatpump": r"compressor|evaporat|condens|expansion valve|\bCOP\b|outdoor unit|kompres|výparn|kondenz|verdicht|verdampf"}
# model vo videu len vtedy, keď text hovorí o tom, ako stroj funguje (reklamné video o tepelnom čerpadle nemá byť celé na reze okruhu)
_NEEDS = {"circuit": 3, "wave": 3, "cpu": 3, "parachute": 3, "trajectory": 3, "escalator": 3, "conveyor": 3, "pulley": 3, "lever": 3, "rocket": 3, "zipper": 3, "drill": 3, "generator": 3, "fission": 3, "rotor": 3, "aircon": 3, "pendulum": 3, "transformer": 3, "crane": 3, "harddrive": 3, "heatpump": 2, "wind_turbine": 3, "solar": 3, "tunnel": 3, "radar": 3, "bridge": 3, "wing": 3, "dam": 3, "submarine": 3, "hydraulic": 3, "elevator": 3, "fridge": 3, "jet": 3, "transistor": 3, "breaker": 3, "canal_lock": 3, "orbit": 3, "pinlock": 3, "wall": 3, "emotor": 3, "battery": 3, "robot_arm": 3, "neuron": 3, "touchscreen": 3, "hurricane": 3}


def topic(full, title="", strict=False):
    """Stroj s presným modelom, o ktorom je celé video. Rozhoduje názov videa; bez neho musí stroj v texte jasne prevládať. Inak None.
    strict (hotový scenár): pri strojoch z _NEEDS musí text hovoriť aj o ich častiach, inak video nie je o tom, ako stroj funguje."""
    m = _topic(full, title)
    if strict and m in _NEEDS and len(re.findall(_SUPPORT.get(m, r"$^"), full or "", re.I)) < _NEEDS[m]:
        return None
    return m


# názov menuje stroj, ale video je o jeho inej podobe, ktorú model neukazuje (rekuperačné brzdenie nie je kotúčová brzda): radšej žiadny model
_AVOID = {"trajectory": r"\bquiz\b|rocket|orbit", "rocket": r"\bquiz\b|rocket (league|science|salad)|arugula", "zipper": r"zip (file|code)|zipcode|\bquiz\b|zip it", "transformer": r"\bquiz\b|transformers? (movie|film|toy|robot)|optimus|megatron|autobot|decepticon|voltage (spike|drop)|\bbatter", "crane": r"\bquiz\b|\bbirds?\b|crane fl|sandhill|whooping|origami|crane game|claw machine|\bdiving\b", "harddrive": r"\bssd\b|solid[- ]state|\bflash\b|floppy|\btapes?\b|\bquiz\b", "car_brake": r"regenerat|single[- ]pedal|elevator|safety gear|engine brak|air brake",
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
          "battery": r"\bquiz\b|solid[- ]state|sodium|lead[- ]acid|flow batter|artillery|battery of|grid (storage|batter)|power ?wall|nuclear batter|potato|lemon",
          "hurricane": r"\bquiz\b|cyclone (vacuum|separator|dust)|dyson|hurricane lamp|desert storm|brainstorm|perfect storm|storm(trooper|s? of)|tornado|hail",
          "touchscreen": r"\bquiz\b|resistive|e-?ink|foldable|oled vs|burn[- ]in|refresh rate|screen time|touch grass|touchdown",
          "neuron": r"\bquiz\b|neural network|\bAI\b|chatgpt|deep learning|machine learning|computer|chip|neuralink",
          "robot_arm": r"\bquiz\b|humanoid|robot (dog|vacuum|lawn)|surg|chatbot|\bAI\b|android|terminator|mars|rover|\bbot\b|walking robot",
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


NAMES = {"circuit": "Electric circuit", "wave": "Wave", "cpu": "Processor chip", "parachute": "Parachute", "trajectory": "Projectile path", "escalator": "Escalator", "conveyor": "Conveyor belt", "pulley": "Pulley", "lever": "Lever", "rocket": "Rocket", "zipper": "Zipper", "drill": "Drill", "generator": "Generator", "fission": "Nuclear reactor", "rotor": "Helicopter rotor", "aircon": "Air conditioner", "pendulum": "Pendulum", "transformer": "Transformer", "crane": "Tower crane", "harddrive": "Hard disk drive", "hurricane": "Hurricane", "touchscreen": "Touchscreen", "neuron": "Nerve cell", "robot_arm": "Robot arm", "battery": "Battery cell", "emotor": "Electric motor", "piston": "Piston engine", "wankel": "Rotary engine", "rotary": "Rotary engine", "gears": "Gears", "turbo": "Turbocharger", "camshaft": "Camshaft", "car_brake": "Disc brake", "gearbox": "Gearbox", "differential": "Differential", "heatpump": "Heat pump", "wind_turbine": "Wind turbine", "solar": "Solar panel", "tunnel": "Tunnel boring machine", "radar": "Radar", "bridge": "Suspension bridge", "wing": "Wing", "dam": "Hydroelectric dam", "submarine": "Submarine", "hydraulic": "Hydraulic jack", "elevator": "Elevator", "fridge": "Refrigerator", "jet": "Jet engine", "wall": "Wall cross-section", "pinlock": "Pin tumbler lock", "canal_lock": "Canal lock", "orbit": "Orbit", "transistor": "Transistor", "breaker": "Circuit breaker"}
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


# ---------- ikona musí ukazovať to, o čom scéna hovorí (16.11.: turbo nakreslené ako veterná turbína, výfuk ako dažďový mrak) ----------
# Značky bez vlastného predmetu (človek, áno/nie, čas, peniaze, dokument, graf): môžu stáť pri čomkoľvek.
_SYMBOL = set("""user users people family boss person crowd team group audience customer worker check cross warning warning_sign idea bulb target star heart
trophy thumbs_up search pin location clock hourglass calendar eye key lock shield flag document contract clipboard receipt invoice mail chat share megaphone
chart chart_down growth pie graph percent calculator scale ruler coin coins banknote money moneybag wallet piggybank card pricetag gift handshake play puzzle
dice infinity speed gauge meter thermo thermometer_up sound sound_wave wave network code bell power globe globe_pin map compass signpost dot stamp crown
candles briefcase dollar euro cart hand_coin barrier brain""".split())
# Ikona s menom, ktoré znie všeobecne, ale kreslí jednu konkrétnu vec: smie sa ukázať, len keď scéna hovorí o tej veci.
_ICON_ONLY = {"turbine": r"\bwind|breez|\bgust|veter", "cloud": r"cloud|\brain|weather|storm|\bsk(?:y|ies)|\bfog|overcast|vapou?r|steam|humid",
              "fan": r"\bfans?\b|ventilat|\bblow|cooling fan", "heatpump": r"heat ?pump", "panel": r"solar|photovolt|\bpv\b",
              "tank": r"\btanks?\b|reservoir|\bstor(?:e|ed|age)|ballast", "pylon": r"pylon|power line|grid|transmission|electric|pole|telegraph|wire",
              "boiler": r"boiler|furnace|water heater", "radiator": r"radiator|heater|heating", "fridge": r"fridge|refrigerat|freezer|cool",
              "battletank": r"battle|army|armou?r|military|soldier|\bwar\b|panzer", "fighter": r"fighter|warplane|air force|dogfight|military"}
# Slová navyše k bežným ikonám (k menu ikony a jej synonymám z knižnice).
_ICON_MORE = {"phone": "app apps mobile screen call text device swipe tap taps message scan", "wifi": "network hotspot router internet signal online connect",
              "store": "shop shops grocer retail supermarket aldi buy sell customer mall company bakery baker cafe café pharmacy market", "house": "home apartment flat rent landlord owner own roof room live mortgage property door",
              "bank": "loan lend account deposit mortgage payment money credit fund treasury mint finance", "ship": "boat vessel hull sea port cargo sail ocean harbor harbour captain",
              "plane": "flight fly flying aircraft airliner airline pilot airport landing jet crew passenger", "city": "town capital urban street delhi rome london",
              "server": "data database company cloud storage copy stored account", "drop": "water oil liquid drain leak sea ocean river rain fuel wet pond flood",
              "truck": "lorry delivery freight haul road trailer driver", "car": "drive driving driver vehicle road traffic ride pedal cart bus", "flame": "fire burn hot heat gas combust",
              "bolt": "electric electricity power energy volt charge charging current lightning spark", "plug": "socket charger charging outlet power electric cable",
              "sun": "solar sunlight day summer shadow light", "snow": "cold ice freeze frozen frost winter chill", "leaf": "plant green eco nature organic algae environment",
              "air": "wind breeze breath oxygen atmosphere pressure sky", "battery": "charge charging cell lithium energy", "gear": "gears cog settings setting mechanism machine config",
              "tool": "repair fix wrench maintenance service mechanic install", "tree": "forest wood trees plant farm", "engine": "motor cylinder piston combustion",
              "laptop": "computer desk pc software types typing", "tv": "television screen show shows movie episode", "camera": "photo photos picture image lens",
              "package": "parcel box boxes order shipment", "warehouse": "hub depot storage stock sorting", "container": "box boxes steel stack", "factory": "plant production assembly line made makes mill mills works furnace industry industrial manufacture employer",
              "chip": "processor silicon semiconductor cpu", "virus": "bacteria germ microbe", "conveyor": "belt", "trash": "recycling waste garbage bin", "robot": "ai automation bot",
              "barcode": "scan scanner label tracking tracker", "fish": "larvae marine", "flap": "flaps", "office": "company business corporate headquarters firm startup", "van": "vehicle vehicles shipping delivery courier", "mountain": "hill peak slope", "village": "town province settlement", "satellite": "orbit space gps", "road": "street route highway lane path", "window": "glass view pane"}
_ICON_STOP = set("the and for with from into over under old new big small real fake hot cold cool your our one two all any".split())
_ICON_WORDS = {}


def _icon_words(canon):
    """Slová, ktoré ikona znázorňuje: jej meno, synonymá z knižnice ikon a ručné doplnky."""
    if canon not in _ICON_WORDS:
        from . import explainer
        ws = set(canon.split("_")) | set(_ICON_MORE.get(canon, "").split())
        for k, v in explainer.ICON_ALIAS.items():
            if v == canon:
                ws |= set(k.split("_"))
        _ICON_WORDS[canon] = {re.sub(r"(?:ies|es|s|ing|e)$", "", w) if len(w) > 5 else w for w in ws if len(w) > 1 and w not in _ICON_STOP}
    return _ICON_WORDS[canon]


def icon_fit(icon, label, ctx):
    """Sedí ikona k scéne? ctx = popis pod ikonou, nadpis, opis a hlas scény. Značky (_SYMBOL) sedia vždy."""
    from . import explainer
    canon = explainer.icon_name(icon) or ""
    if not canon:
        return False   # neznáme meno by sa nakreslilo ako fajka
    if canon in _ICON_ONLY:
        return bool(re.search(_ICON_ONLY[canon], ctx or "", re.I))
    if canon in _SYMBOL:
        return True
    low = (ctx or "").lower()
    return any(re.search(r"(?<![a-z])" + re.escape(w) + (r"(?![a-z])" if len(w) < 4 else ""), low) for w in _icon_words(canon))


_LEAD = r"^(?:the|a|an|your|our|his|her|their|my|old|new|hot|cold|cool|cooler|big|small|real|fake|fresh|dirty|clean|same|whole|full|empty)\s+"
_ICON_KINDS = ("scene", "icons", "draw", "hero")


def _icon_for(label, ctx):
    """Ikona, ktorú popis pomenúva celý („Turbo“ → turbocharger, „Hot exhaust“ → exhaust). None, keď knižnica takú nemá."""
    from . import explainer
    l = re.sub(r"[^a-z0-9 ]+", " ", (label or "").lower()).strip()
    for cand in dict.fromkeys((l, re.sub(_LEAD, "", l))):
        if not cand or len(cand.split()) > 3:
            continue
        n = cand.replace(" ", "_")
        for c in (n, re.sub(r"ies$", "y", n), re.sub(r"es$", "", n), re.sub(r"s$", "", n)):
            c = c if c in explainer._ICON_SET else explainer.ICON_ALIAS.get(c)
            if c in explainer._ICON_SET and icon_fit(c, label, ctx):
                return c
    return None


def _nodes(d):
    """[(ikona, popis)] diagramu s ikonami."""
    k = d.get("k")
    try:
        if k == "scene":
            return [(str(q[0]), str(q[1]) if len(q) > 1 else "") for q in d.get("n") or [] if isinstance(q, list) and q]
        if k == "icons":
            return [(str(q[0]), str(q[1]) if len(q) > 1 else "") if isinstance(q, list) and q else (str(q), "") for q in d.get("i") or [] if q]
        if k == "draw":
            return [(str(e.get("i") or "") if e.get("s") == "icon" else "turbine", str(e.get("l") or ""))
                    for e in d.get("e") or [] if isinstance(e, dict) and e.get("s") in ("icon", "turbine")]
        if k == "hero" and d.get("i"):
            return [(str(d["i"]), f"{d.get('w') or ''} {d.get('s') or ''}".strip())]
    except (TypeError, IndexError):
        pass
    return []


def bad_icons(d, ctx):
    """Počet ikon diagramu, ktoré nesedia k scéne."""
    return sum(1 for i, l in _nodes(d) if not icon_fit(i, l, f"{l} . {ctx}")) if d.get("k") in _ICON_KINDS else 0


def fix_icons(d, ctx):
    """Ikona, ktorá nesedí k scéne, sa vymení za tú, ktorú popis pomenúva; keď taká nie je, ostane neutrálna značka s popisom.
    Vráti (diagram, počet nesediacich ikon)."""
    if d.get("k") not in _ICON_KINDS:
        return d, 0
    bad = 0

    def pick(i, l):
        nonlocal bad
        if icon_fit(i, l, f"{l} . {ctx}"):
            return i
        bad += 1
        return (_icon_for(l, ctx) if l.strip() else None) or "dot"
    try:
        k = d["k"]
        if k == "scene":
            out = dict(d, n=[[pick(str(q[0]), str(q[1]) if len(q) > 1 else "")] + list(q[1:]) for q in d.get("n") or [] if isinstance(q, list) and q])
        elif k == "icons":
            it = []
            for q in d.get("i") or []:
                i, l = (str(q[0]), str(q[1]) if len(q) > 1 else "") if isinstance(q, list) and q else (str(q), "")
                n = pick(i, l)
                if n != "dot" or l.strip():   # ikona bez popisu, ktorá nesedí, nemá čo ukázať
                    it.append([n, l])
            out = dict(d, i=it) if it else {"k": "text", "w": ""}
        elif k == "draw":
            el = []
            for e in d.get("e") or []:
                if isinstance(e, dict) and e.get("s") == "icon":
                    e = dict(e, i=pick(str(e.get("i") or ""), str(e.get("l") or "")))
                elif isinstance(e, dict) and e.get("s") == "turbine":
                    n = pick("turbine", str(e.get("l") or ""))
                    if n != "turbine":
                        p = (list(e.get("p") or []) + [216, 240, 150])[:3]
                        e = {**{x: y for x, y in e.items() if x not in ("s", "n", "p")}, "s": "icon", "i": n, "p": [p[0], p[1] - p[2] / 2, 90]}
                el.append(e)
            out = dict(d, e=el)
        else:
            n = pick(str(d.get("i") or ""), f"{d.get('w') or ''} {d.get('s') or ''}".strip()) if d.get("i") else None
            out = d if n in (None, d.get("i")) else (dict(d, i=n) if n != "dot" else {"k": "text", "w": str(d.get("w") or "")})
    except (TypeError, ValueError, IndexError):
        return d, 0
    return out, bad


def _own(topic, d):
    """Hovorí diagram s ikonami o stroji videa alebo jeho častiach (ikonou či popisom)? Vtedy ho má ukázať presný model, nie ikona."""
    rx = [r for r, m, _ in _RX if m == topic] + [re.compile(r, re.I) for r in [_SUPPORT.get(topic)] + [p[1] for p in _PARTS.get(topic, ())] if r]
    return any(r.search(f"{i.replace('_', ' ')} . {l}") for i, l in _nodes(d) for r in rx)


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
    # najprv časť, o ktorej scéna hovorí, potom stroj v behu alebo celok (ten sedí vždy), až nakoniec iná časť
    said = focuses(topic, scene.get("onscreen") or "", scene.get("visual") or "", scene.get("_spoken") or "")
    rest = sorted(p for p in CAM_ONLY.get(topic, ()) if p not in said)
    if rest:
        rest = rest[used.get("_fill", 0) % len(rest):] + rest[:used.get("_fill", 0) % len(rest)]
    for f in said + (["run"] if topic in RUNS else []) + [""] + rest:
        if (topic, f) != used.get("_last"):
            if f in rest:
                used["_fill"] = used.get("_fill", 0) + 1
            used["_last"] = (topic, f)
            return _state(dict({"k": "mech", "m": topic}, **({"f": f} if f else {}), **({"l": _LABELS[topic]} if _LABELS.get(topic) and lang == "en" else {})), used)
    return {"k": "text", "w": str(scene.get("onscreen") or "")}


def upgrade(d, scene, spoken, used, lang="en", prev=None, long=False, full="", topic=None, last=False):
    """d = diagram scény. Vráti diagram, ktorý sa naozaj ukáže.
    topic = stroj, o ktorom je celé video: slabé scény (ikony, text) vtedy ukazujú jeho presný model a kamera ide
    na to, o čom scéna hovorí. Mimo témy videa sa model doplní, len keď scéna sama hovorí o stroji s presným modelom."""
    d = calm_draw(d)
    texts = (scene.get("onscreen") or "", scene.get("visual") or "", spoken or "")
    if d.get("k") in _ICON_KINDS:   # ikona musí sedieť k scéne; vo videu o stroji jeho časti ukazuje len presný model
        fixed, bad = fix_icons(d, " . ".join(texts)) if lang == "en" else (d, 0)
        d = {"k": "text"} if topic and (bad or _own(topic, d)) else fixed
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
                return _fill(d, topic, used, dict(scene, _spoken=spoken), lang)   # v dlhom videu nie dva celkové pohľady po sebe
            f = "run" if topic in RUNS and used.get("_ov", 0) % 2 else ""
            used["_ov"] = used.get("_ov", 0) + 1
        if prev == topic and used.get("_last") == (topic, f):   # nikdy ten istý záber dvakrát po sebe: iná časť, beh naplno alebo celok
            alt = [g for g in focuses(topic, *texts) + (["run"] if topic in RUNS else []) + [""] if (topic, g) != used.get("_last")]
            if long or not alt:
                return _fill(d, topic, used, dict(scene, _spoken=spoken), lang)
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
    if used.get(m, 0) >= (4 if long else 3) or prev == m:
        return actors(d) or d
    used[m] = used.get(m, 0) + 1
    used["_last"] = (m, "")
    out = {"k": "mech", "m": m}
    if labels and lang == "en":
        out["l"] = labels
    return out
