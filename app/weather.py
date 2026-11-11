"""Počasie ako spúšťač nápadov (1.18): mráz, prudké ochladenie alebo horúčava v krajinách projektu.

Predpoveď z Open-Meteo (zadarmo, bez kľúča, 1 požiadavka denne pre všetky krajiny). Vyhodnotenie robí program, bez AI.
Výstraha sa správa ako udalosť: nápad dostane dátum a pôjde len na účty krajín, ktorých sa týka.
"""
import datetime as dt
import json

import httpx
from fastapi import APIRouter, Body, HTTPException

from . import db, languages

router = APIRouter()
CAPITALS = {
    "SK": (48.15, 17.11), "CZ": (50.08, 14.44), "DE": (52.52, 13.40), "AT": (48.21, 16.37), "CH": (46.95, 7.45), "LU": (49.61, 6.13),
    "PL": (52.23, 21.01), "HU": (47.50, 19.04), "FR": (48.86, 2.35), "BE": (50.85, 4.35), "NL": (52.37, 4.90), "IT": (41.90, 12.50),
    "ES": (40.42, -3.70), "PT": (38.72, -9.14), "GB": (51.51, -0.13), "IE": (53.35, -6.26), "MT": (35.90, 14.51), "DK": (55.68, 12.57),
    "SE": (59.33, 18.07), "NO": (59.91, 10.75), "FI": (60.17, 24.94), "IS": (64.15, -21.94), "EE": (59.44, 24.75), "LV": (56.95, 24.11),
    "LT": (54.69, 25.28), "GR": (37.98, 23.73), "CY": (35.17, 33.36), "BG": (42.70, 23.32), "RO": (44.43, 26.10), "HR": (45.81, 15.98),
    "SI": (46.06, 14.51), "RS": (44.79, 20.45), "ME": (42.44, 19.26), "BA": (43.86, 18.41), "MK": (42.00, 21.43), "AL": (41.33, 19.82),
    "XK": (42.66, 21.17),
}
KINDS = {"first_frost": ("Prvý mráz", "first frost of the season"), "cold": ("Prudké ochladenie", "sudden cold snap"),
         "freeze": ("Silný mráz", "deep freeze"), "heat": ("Horúčava", "heat wave")}


def evaluate(times, tmin, tmax, today):
    """Z radu denných teplôt (minulých 14 dní + predpoveď) vráti najviac jednu výstrahu: (druh, dátum, teplota)."""
    past = [(a, b) for t, a, b in zip(times, tmin, tmax) if t < today and a is not None and b is not None]
    fut = [(t, a, b) for t, a, b in zip(times, tmin, tmax) if t >= today + dt.timedelta(days=2) and a is not None and b is not None]
    if len(past) < 5 or not fut:
        return None
    p_min = min(a for a, _ in past)
    p_avg_min = sum(a for a, _ in past) / len(past)
    p_avg_max = sum(b for _, b in past) / len(past)
    d_cold, t_cold, _ = min(fut, key=lambda x: x[1])
    d_hot, _, t_hot = max(fut, key=lambda x: x[2])
    if t_cold <= -12:
        return "freeze", d_cold, t_cold
    if p_min > 0.5 and t_cold <= -1:
        return "first_frost", d_cold, t_cold
    if t_cold <= p_avg_min - 7 and t_cold <= -3:
        return "cold", d_cold, t_cold
    if t_hot >= 32 and t_hot >= p_avg_max + 3:
        return "heat", d_hot, t_hot
    return None


def job():
    """Raz denne: predpoveď pre hlavné mestá všetkých krajín (1 požiadavka)."""
    cs = list(CAPITALS)
    r = httpx.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": ",".join(str(CAPITALS[c][0]) for c in cs), "longitude": ",".join(str(CAPITALS[c][1]) for c in cs),
        "daily": "temperature_2m_min,temperature_2m_max", "forecast_days": 10, "past_days": 14, "timezone": "auto"}, timeout=40)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        data = [data]
    today = dt.date.today()
    alerts = []
    for c, d in zip(cs, data):
        dd = d.get("daily") or {}
        try:
            res = evaluate([dt.date.fromisoformat(t) for t in dd.get("time", [])], dd.get("temperature_2m_min", []),
                           dd.get("temperature_2m_max", []), today)
        except Exception:
            res = None
        if res:
            alerts.append({"country": c, "kind": res[0], "date": res[1].isoformat(), "temp": round(res[2])})
    db.set_setting("weather_alerts", {"at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "alerts": alerts})


def _countries(pid):
    p = db.one("SELECT languages FROM projects WHERE id=?", (pid,))
    langs = json.loads((p or {}).get("languages") or "[]")
    acc = {r["country"] for r in db.q("SELECT DISTINCT country FROM accounts WHERE project_id=? AND country!=''", (pid,))}
    return acc or {c for l in langs for c in languages.COUNTRIES.get(l, [])}


def alerts(pid):
    """Výstrahy pre krajiny projektu, zoskupené podľa druhu. Kľúč je stabilný v rámci týždňa (bez duplicít nápadov)."""
    st = db.get_setting("weather_alerts", {}) or {}
    mine = _countries(pid)
    today = dt.date.today().isoformat()
    groups = {}
    for a in st.get("alerts", []):
        if a["country"] in mine and a["date"] >= today:
            groups.setdefault(a["kind"], []).append(a)
    out = []
    for kind, items in groups.items():
        items.sort(key=lambda a: a["date"])
        date = items[0]["date"]
        y, w, _ = dt.date.fromisoformat(date).isocalendar()
        key = f"w|{kind}|{y}-{w}"
        temp = min(a["temp"] for a in items) if kind != "heat" else max(a["temp"] for a in items)
        out.append({"key": key, "kind": kind, "name": KINDS[kind][0], "en": KINDS[kind][1], "date": date, "temp": temp,
                    "countries": [a["country"] for a in items],
                    "has_idea": bool(db.one("SELECT id FROM ideas WHERE project_id=? AND source_ref=?", (pid, key)))})
    out.sort(key=lambda a: a["date"])
    return {"at": st.get("at", ""), "alerts": out}


def _signal(a, n):
    return {"id": f"W{n}", "mk": a["countries"],
            "txt": f'weather: {a["en"]} forecast around {a["date"]} in {", ".join(a["countries"])} (down/up to {a["temp"]} °C); '
                   f'only use if weather matters for this project',
            "ref": {"event": a["key"], "label": f'{a["name"]} ({", ".join(a["countries"][:6])})', "date": a["date"], "langs": a["countries"]}}


def signals(pid, n=2):
    return [_signal(a, i + 1) for i, a in enumerate([a for a in alerts(pid)["alerts"] if not a["has_idea"]][:n])]


def signal_for(pid, key):
    a = next((a for a in alerts(pid)["alerts"] if a["key"] == key), None)
    return _signal(a, 1) if a else None


@router.get("/api/weather/{pid}")
def api_alerts(pid: int):
    return alerts(pid)


@router.post("/api/weather/{pid}/idea")
def api_idea(pid: int, data: dict = Body(...)):
    from . import content
    if not signal_for(pid, data.get("key", "")):
        raise HTTPException(400, "Výstraha už nie je aktuálna")
    return content.radar_quick(pid, {"weather": data["key"]})
