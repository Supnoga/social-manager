"""Dashboard (0 tokenov): čísla zverejnených príspevkov pre grafy a filtre.

Server vráti riadky po príspevkoch (dátum, sieť, účet, krajina, jazyk, projekt, čísla) a prehliadač z nich
sám počíta súčty, grafy a filtre. Bez skutočných čísel vie vrátiť ukážkové dáta, aby bolo vidno, ako to bude vyzerať.
"""
import datetime as dt
import random

from fastapi import APIRouter

from . import db, languages

router = APIRouter()


def _country(acc_country, lang):
    c = (acc_country or "").upper()
    if c:
        return c
    cs = languages.COUNTRIES.get(lang or "", [])
    return cs[0] if len(cs) == 1 else ""


def _real(since):
    rows = db.q("""SELECT p.id, p.scheduled_at, p.url, p.account_id, a.platform, a.name account, a.country acc_country,
                          a.lang acc_lang, v.lang vlang, v.title, v.project_id,
                          ps.views, ps.likes, ps.comments, ps.shares, ps.fetched_at
                   FROM posts p JOIN accounts a ON a.id=p.account_id JOIN videos v ON v.id=p.video_id
                   LEFT JOIN post_stats ps ON ps.post_id=p.id AND ps.error=''
                   WHERE p.status='done' AND p.scheduled_at>=? ORDER BY p.scheduled_at""", (since,))
    out = []
    for r in rows:
        lang = r["acc_lang"] or r["vlang"] or ""
        out.append({"id": r["id"], "d": r["scheduled_at"][:16], "pl": r["platform"], "acc": r["account"] or r["platform"],
                    "aid": r["account_id"], "c": _country(r["acc_country"], lang), "l": lang, "p": r["project_id"],
                    "t": r["title"] or "", "u": r["url"] or "", "m": 1 if r["fetched_at"] else 0,
                    "v": r["views"] or 0, "lk": r["likes"] or 0, "cm": r["comments"] or 0, "sh": r["shares"] or 0})
    return out


# typický výkon sietí pre ukážku (zobrazenia na video, podiel reakcií)
_DEMO_NET = {"tiktok": (2600, .07), "instagram": (1300, .06), "youtube": (900, .045), "facebook": (700, .035), "linkedin": (450, .05)}
_DEMO_TITLES = ["Koľko ušetrí tepelné čerpadlo za rok", "3 chyby pri výbere tepelného čerpadla", "Ako ticho je PROLINE v noci",
                "Rekuperácia: čerstvý vzduch bez strát", "Montáž za jeden deň", "Čo znamená SCOP 5,14", "Zima −20 °C a stále teplo",
                "N2N Home: kúrenie z mobilu", "Prečo chladivo R290", "Starý kotol vs. tepelné čerpadlo",
                "Ako vybrať správny výkon", "Dotácie na tepelné čerpadlo"]


def _demo(since_days):
    """Ukážkové dáta: skutočné projekty a krajiny, vymyslené čísla (stále rovnaké, aby graf neskákal)."""
    rnd = random.Random(42)
    projects = [p["id"] for p in db.q("SELECT id FROM projects")] or [0]
    countries = [(c, ls[0]) for c, ls in languages.COUNTRY_LANGS.items() if c != "INT"]
    weight = {c: rnd.uniform(.3, 1.6) for c, _ in countries}
    for big in ("SK", "CZ", "DE", "PL", "AT", "HU"):
        weight[big] = weight.get(big, 1) * 2.2
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    out, pid = [], 1
    for day in range(since_days, -1, -1):
        base = now - dt.timedelta(days=day)
        growth = 0.55 + 0.45 * (1 - day / max(since_days, 1))  # účty rastú
        for _ in range(rnd.randint(3, 7)):
            c, lang = rnd.choice(countries)
            pl = rnd.choices(list(_DEMO_NET), weights=[5, 4, 3, 3, 1])[0]
            hour = rnd.choice([7, 8, 9, 11, 12, 13, 16, 17, 18, 19, 20, 21])
            when = base.replace(hour=hour)
            if when > now:
                continue
            views0, er = _DEMO_NET[pl]
            hour_boost = 1.35 if hour in (12, 18, 19, 20) else 1.0
            wk_boost = 1.2 if when.weekday() in (5, 6) else 1.0
            v = int(views0 * weight[c] * growth * hour_boost * wk_boost * rnd.lognormvariate(0, .6))
            react = v * er * rnd.uniform(.6, 1.5)
            out.append({"id": pid, "d": when.strftime("%Y-%m-%d %H:%M"), "pl": pl,
                        "acc": f"N2N TECHNOLOGY {languages.COUNTRY_NAMES.get(c, c)}", "aid": f"{pl}-{c}",
                        "c": c, "l": lang, "p": rnd.choice(projects), "t": rnd.choice(_DEMO_TITLES), "u": "", "m": 1,
                        "v": v, "lk": int(react * .78), "cm": int(react * .12), "sh": int(react * .10)})
            pid += 1
    return out


@router.get("/api/dash")
def dash(days: int = 365, demo: int = 0):
    days = max(7, min(days, 800))
    since = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    real = _real(since)
    measured = sum(1 for r in real if r["m"])
    use_demo = bool(demo)
    rows = _demo(days) if use_demo else real
    last = db.one("SELECT MAX(fetched_at) t FROM post_stats WHERE error=''")
    return {"rows": rows, "demo": use_demo, "real_posts": len(real), "real_measured": measured,
            "last": (last or {}).get("t"), "countries": languages.COUNTRY_NAMES,
            "langs": {k: v[0] for k, v in languages.LANGUAGES.items()}}
