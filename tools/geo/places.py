import json, re, unicodedata
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
names = json.load(open("names.json"))
en = names["en"]
fix = {"GB": "United Kingdom", "CD": "DR Congo", "CG": "Congo", "US": "United States", "KR": "South Korea", "KP": "North Korea", "CZ": "Czechia", "MK": "North Macedonia"}
for l, m in names.items():
    if l != "en" and m.get("CD") == m.get("CG"):
        a = json.load(open("node_modules/i18n-iso-countries/langs/%s.json" % ("nb" if l == "no" else l)))["countries"]["CD"]
        m["CD"] = (a if isinstance(a, list) else [a])[0]
g = json.load(open("pov10_deu.geojson"))
countries, alias = {}, {}
for f in g["features"]:
    p = f["properties"]; cid = p["ISO_A2_EH"] if p["ISO_A2_EH"] != "-99" else p["ADM0_A3"]
    if cid in countries: continue
    nm = {l: m[cid] for l, m in names.items() if cid in m and not cid.startswith("_")}
    nm["en"] = fix.get(cid) or (en.get(cid) if cid in en else p["NAME_EN"] or p["NAME"])
    countries[cid] = {"ct": p["CONTINENT"], "sr": p["SUBREGION"], "x": round(p["LABEL_X"], 2), "y": round(p["LABEL_Y"], 2), "n": nm}
    for a in [p["NAME"], p["NAME_EN"], p["NAME_LONG"], p["ADMIN"], p["FORMAL_EN"], p["ISO_A3_EH"], p["ADM0_A3"], nm["en"]] + en.get("_all_" + cid, []):
        if a and a != "-99": alias.setdefault(norm(a), cid)
for c in countries: alias.setdefault(norm(c), c)
for a, c in {"holland": "NL", "america": "US", "usa": "US", "uk": "GB", "britain": "GB", "england": "GB", "scotland": "GB", "wales": "GB",
             "ivory coast": "CI", "burma": "MM", "east timor": "TL", "swaziland": "SZ", "turkiye": "TR", "czech republic": "CZ", "macedonia": "MK",
             "congo kinshasa": "CD", "drc": "CD", "dr congo": "CD", "congo brazzaville": "CG", "uae": "AE", "vatican": "VA", "vatican city": "VA"}.items():
    alias[a] = c
# mesta
d = json.load(open("ne_10m_populated_places.geojson"))
cities = []
LN = ["de", "es", "fr", "pt", "hu", "it", "nl", "pl", "sv", "el", "tr", "uk", "ru"]
for f in d["features"]:
    p = f["properties"]
    if not (p["POP_MAX"] >= 20000 or p["ADM0CAP"] or p["FEATURECLA"] == "Admin-1 capital"): continue
    cc = p["ISO_A2"] if p["ISO_A2"] not in ("-99", None) else ""
    loc = {l: p["NAME_" + l.upper()] for l in LN if p.get("NAME_" + l.upper()) and p["NAME_" + l.upper()] != (p["NAME_EN"] or p["NAME"])}
    keys = sorted({norm(x) for x in [p["NAME"], p["NAMEASCII"], p["NAME_EN"]] + (p["NAMEALT"] or "").split("|") if x and norm(x)})
    cities.append([p["NAME_EN"] or p["NAME"], cc, round(p["LATITUDE"], 3), round(p["LONGITUDE"], 3), int(p["POP_MAX"]), 1 if p["ADM0CAP"] else 0, keys, loc])
cities.sort(key=lambda c: -c[4])
# rieky a kanály
r = json.load(open("ne_50m_rivers_lake_centerlines.geojson"))
rivers = {}
for f in r["features"]:
    p = f["properties"]; nm = (p.get("name_en") or p.get("name") or "").strip()
    if not nm: continue
    nm = re.sub(r"\s+", " ", nm)
    geo = f["geometry"]; lines = geo["coordinates"] if geo["type"] == "MultiLineString" else [geo["coordinates"]]
    for ln in lines:
        pts = [[round(x, 2), round(y, 2)] for x, y in ln]
        rivers.setdefault(nm, {"k": sorted({norm(nm)} | {norm(a) for a in (p.get("name_alt") or "").split("|") if a}), "l": []})["l"].append(pts)
EU = "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split()
groups = {"european union": EU, "eu": EU, "middle east": "BH CY EG IR IQ IL JO KW LB OM PS QA SA SY TR AE YE".split(),
          "nordic": "DK FI IS NO SE".split(), "scandinavia": "DK NO SE".split(), "baltics": "EE LV LT".split(), "benelux": "BE NL LU".split(),
          "balkans": "AL BA BG HR XK ME MK RO RS SI GR".split(), "gulf states": "BH KW OM QA SA AE".split(), "g7": "CA FR DE IT JP GB US".split(),
          "dach": "DE AT CH".split(), "iberia": "ES PT".split(), "british isles": "GB IE".split(), "visegrad": "CZ HU PL SK".split(),
          "horn of africa": "DJ ER ET SO".split(), "caucasus": "AM AZ GE".split(),
          "central asia": "KZ KG TJ TM UZ".split(), "southeast asia": "BN KH ID LA MY MM PH SG TH TL VN".split(), "nato": "AL BE BG CA HR CZ DK EE FI FR DE GR HU IS IT LV LT LU ME NL MK NO PL PT RO SK SI ES SE TR GB US".split()}
for c, v in countries.items():
    for k in (v["ct"], v["sr"]):
        if k and k not in ("Seven seas (open ocean)",):
            groups.setdefault(norm(k), []).append(c)
json.dump({"countries": countries, "alias": alias, "groups": groups}, open("places.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(cities, open("cities.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(rivers, open("rivers.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(countries), len(alias), len(cities), len(rivers), sorted(groups)[:40])
