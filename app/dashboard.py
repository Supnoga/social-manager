"""Dashboard (0 tokenov): čísla zverejnených príspevkov pre grafy a filtre.

Server vráti riadky po príspevkoch (dátum, sieť, účet, krajina, jazyk, projekt, čísla) a prehliadač z nich
sám počíta súčty, grafy a filtre. Len skutočné čísla stiahnuté zo sietí, nič vymyslené.
"""
import datetime as dt

from fastapi import APIRouter

from fastapi import Body

from . import db, insights, languages

router = APIRouter()


def _country(acc_country, lang):
    c = (acc_country or "").upper()
    if c:
        return c
    cs = languages.COUNTRIES.get(lang or "", [])
    return cs[0] if len(cs) == 1 else ""


def _comment_counts():
    """Počet komentárov, ktoré appka sama stiahla, po videách (čerstvejšie ako čísla z Analytics)."""
    try:
        return {(r["platform"], r["post_ext"]): r["n"] for r in db.q(
            "SELECT platform, post_ext, COUNT(*) n FROM comments WHERE post_ext!='' GROUP BY platform, post_ext")}
    except Exception:
        return {}


def _real(since):
    cc = _comment_counts()
    rows = db.q("""SELECT p.id, p.scheduled_at, p.url, p.external_id ext, p.account_id, a.platform, a.name account, a.country acc_country,
                          a.lang acc_lang, v.lang vlang, v.title, v.project_id,
                          ps.views, ps.likes, ps.comments, ps.shares, ps.fetched_at, ps.watch_min, ps.avg_pct, ps.subs, v.duration
                   FROM posts p JOIN accounts a ON a.id=p.account_id JOIN videos v ON v.id=p.video_id
                   LEFT JOIN post_stats ps ON ps.post_id=p.id AND ps.fetched_at!='' AND (ps.error='' OR ps.views>0 OR ps.likes>0)
                   WHERE p.status='done' AND p.scheduled_at>=? ORDER BY p.scheduled_at""", (since,))
    out = []
    for r in rows:
        lang = r["acc_lang"] or r["vlang"] or ""
        out.append({"id": r["id"], "d": r["scheduled_at"][:16], "pl": r["platform"], "acc": r["account"] or r["platform"],
                    "aid": r["account_id"], "c": _country(r["acc_country"], lang), "l": lang, "p": r["project_id"],
                    "t": r["title"] or "", "u": r["url"] or "", "m": 1 if r["fetched_at"] else 0,
                    "v": r["views"] or 0, "lk": r["likes"] or 0, "cm": max(r["comments"] or 0, cc.get((r["platform"], r["ext"]), 0)), "sh": r["shares"] or 0,
                    "wm": round(r["watch_min"] or 0, 1), "ap": round(r["avg_pct"] or 0, 1), "sb": r["subs"] or 0,
                    "du": round(r["duration"] or 0)})
    return out


@router.get("/api/dash")
def dash(days: int = 365, pdays: int = 0):
    days = max(7, min(days, 800))
    psince = (dt.datetime.now() - dt.timedelta(days=pdays or days)).strftime("%Y-%m-%d %H:%M:%S")
    since = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    real = _real(since)
    measured = sum(1 for r in real if r["m"])
    rows = [r for r in real if r["m"]]  # len príspevky so skutočne stiahnutými číslami
    last = db.one("SELECT MAX(t) t FROM (SELECT MAX(fetched_at) t FROM post_stats WHERE error='' UNION ALL SELECT MAX(fetched_at) FROM account_stats)")
    accs, daily, aoff = insights.accounts_data(since[:10])
    pub = {}  # projekt: [zverejnené v období, z toho so stiahnutými číslami]
    for r in real:
        if r["d"] >= psince[:16]:
            x = pub.setdefault(str(r["p"]), [0, 0])
            x[0] += 1
            x[1] += r["m"]
    return {"rows": rows, "real_posts": len(real), "real_measured": measured,
            "last": (last or {}).get("t"), "countries": languages.COUNTRY_NAMES,
            "langs": {k: v[0] for k, v in languages.LANGUAGES.items()},
            "accounts": accs, "daily": daily, "analytics_off": aoff, "prod": insights.production(psince),
            "busy": insights._busy["on"], "pub": pub, "yt_limit": insights.limit_today(), "ypp_deadline": insights.YPP_DEADLINE}


@router.post("/api/dash/refresh")
def dash_refresh(data: dict = Body(default={})):
    return {"started": insights.refresh(force=True), "yt_limit": insights.limit_today()}
