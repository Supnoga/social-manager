"""Dashboard (0 tokenov): čísla zverejnených príspevkov pre grafy a filtre.

Server vráti riadky po príspevkoch (dátum, sieť, účet, krajina, jazyk, projekt, čísla) a prehliadač z nich
sám počíta súčty, grafy a filtre. Len skutočné čísla stiahnuté zo sietí, nič vymyslené.
"""
import datetime as dt

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


@router.get("/api/dash")
def dash(days: int = 365):
    days = max(7, min(days, 800))
    since = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    real = _real(since)
    measured = sum(1 for r in real if r["m"])
    rows = [r for r in real if r["m"]]  # len príspevky so skutočne stiahnutými číslami
    last = db.one("SELECT MAX(fetched_at) t FROM post_stats WHERE error=''")
    return {"rows": rows, "real_posts": len(real), "real_measured": measured,
            "last": (last or {}).get("t"), "countries": languages.COUNTRY_NAMES,
            "langs": {k: v[0] for k, v in languages.LANGUAGES.items()}}
