"""Sledovanie klipov: pozretia zo sietí (hotové čítanie Social Managera) a odhad zárobku podľa pravidiel kampane.

Odhad je len orientačný. Platí číslo, ktoré ukáže stránka kampane po schválení klipu."""
import time
from datetime import datetime, timedelta

from app import db as appdb
from app import stats as appstats

from . import store

EVERY = 3 * 3600
SUBMIT = ("todo", "submitted", "approved", "rejected", "paid", "missed")
# Do koľkých minút od zverejnenia berie platforma odkaz (Whop / Content Rewards 30 minút, Clipping.net 72 hodín).
WINDOW = {"whop": 30, "clipping": 72 * 60}


def deadline(posted_at, site):
    """Dokedy treba odkaz vložiť do kampane ('' = bez termínu)."""
    w = WINDOW.get(site or "")
    if not w or not posted_at:
        return ""
    try:
        return (datetime.strptime(posted_at, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=w)).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""


def tick(force=False):
    """Raz za 3 hodiny načíta pozretia všetkých klipov za posledných 45 dní."""
    if not force and time.time() - float(store.get("stats_at", 0) or 0) < EVERY:
        return 0
    store.put("stats_at", time.time())
    since = (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S")
    rows = store.q("SELECT id, account_id, platform, external_id, url FROM posts WHERE status='posted' AND external_id!='' "
                   "AND updated_at>=?", (since,))
    done = 0
    by_acc = {}
    for r in rows:
        by_acc.setdefault(r["account_id"], []).append(r)
    for aid, posts in by_acc.items():
        acc = appdb.one("SELECT * FROM accounts WHERE id=?", (aid,))
        fn = appstats.FETCHERS.get(acc["platform"]) if acc else None
        if not fn:
            continue
        try:
            got = fn(acc, posts) or {}
        except Exception as e:
            print("Clipper čísla:", acc["platform"], str(e)[:200])
            continue
        for p in posts:
            v = got.get(p["external_id"])
            if v:
                store.run("UPDATE posts SET views=?, likes=?, comments=?, stats_at=? WHERE id=?",
                          (int(v[0] or 0), int(v[1] or 0), int(v[2] or 0), store.now(), p["id"]))
                done += 1
    return done


def earn(views, camp):
    """Odhad zárobku jedného príspevku v dolároch (pred poplatkom platformy)."""
    views = int(views or 0)
    if views < int(camp.get("min_views") or 0):
        return 0.0
    e = views / 1000.0 * float(camp.get("rate") or 0)
    cap = float(camp.get("max_payout") or 0)
    return round(min(e, cap) if cap > 0 else e, 2)


def _usd(x):
    return f"{x:,.0f}".replace(",", " ") + " $"


def judge(rate, budget, spent=0, clippers=0, age_days=0):
    """Hodnotenie kampane pred vstupom: ('good' | 'ok' | 'bad', krátke vety po slovensky).
    Vychádza z toho, čo ukazujú otvorené kampane (11/2026): bežná kampaň míňa 500 až 1 500 $ denne a vydrží 1 až 4 týždne,
    na jedného klipera vychádza 30 až 200 $; najlepšie sú vyššia sadzba, dosť rozpočtu a málo kliperov."""
    rate, budget, spent = float(rate or 0), float(budget or 0), max(0.0, float(spent or 0))
    clippers, age = int(clippers or 0), float(age_days or 0)
    bad, good, out = 0, 0, []
    r = f"{rate:g}".replace(".", ",")
    if rate >= 2:
        good += 1
        out.append(f"Sadzba {r} $ za 1 000 pozretí je nadpriemerná.")
    elif rate >= 1:
        out.append(f"Sadzba {r} $ za 1 000 pozretí je bežná.")
    elif rate > 0:
        bad += 1
        out.append(f"Sadzba {r} $ za 1 000 pozretí je nízka.")
    if rate > 0:
        out.append("Na 100 $ treba " + f"{int(round(100 / rate * 1000, -3)):,}".replace(",", " ") + " pozretí.")
    if budget > 0:
        left = max(0.0, budget - spent)
        days = left / (spent / age) if spent > 0 and age >= 1 else None
        out.append(f"Ostáva {_usd(left)} z {_usd(budget)}.")
        if days is not None:
            n = round(days)
            word = "deň" if n == 1 else "dni" if 2 <= n <= 4 else "dní"
            out.append(f"Míňa sa asi {_usd(spent / age)} denne, rozpočet vystačí " + (f"asi na {n} {word}." if n <= 60 else "na viac ako 60 dní."))
        if left < 1000 or (days is not None and days < 3) or (spent / budget > 0.7 and (days is None or days < 7)):
            bad += 2
            out.append("Peniaze sa čoskoro minú, klipy sa nemusia stihnúť zaplatiť.")
        elif budget >= 5000 and spent / budget < 0.5:
            good += 1
    else:
        out.append("Rozpočet nie je uvedený, over ho na stránke kampane.")
    if clippers > 0:
        if clippers > 300:
            bad += 1
            out.append(f"Je tam veľa kliperov ({clippers}), peniaze sa delia na drobné.")
        elif clippers <= 50:
            good += 1
            out.append(f"Kliperov je málo ({clippers}), to je dobre.")
        if spent > 0:
            out.append(f"Na jedného klipera zatiaľ vyšlo asi {_usd(spent / clippers)}.")
    return ("bad" if bad >= 2 else "good" if good >= 2 and not bad else "ok"), out


def campaign_totals():
    """Súčty po kampaniach: klipy, zverejnenia, pozretia, odhad zárobku, vyplatené."""
    out = {}
    camps = {c["id"]: c for c in store.q("SELECT * FROM campaigns")}
    for r in store.q("SELECT p.views, p.submit, p.paid, p.status, c.campaign_id FROM posts p JOIN clips c ON c.id=p.clip_id"):
        t = out.setdefault(r["campaign_id"], {"posted": 0, "queued": 0, "views": 0, "est": 0.0, "paid": 0.0, "todo": 0})
        if r["status"] == "posted":
            t["posted"] += 1
            t["views"] += r["views"] or 0
            if r["submit"] not in ("rejected", "missed"):
                t["est"] += earn(r["views"], camps.get(r["campaign_id"]) or {})
            if r["submit"] == "todo":
                t["todo"] += 1
        elif r["status"] in ("queued", "posting"):
            t["queued"] += 1
        t["paid"] += float(r["paid"] or 0)
    for cid, t in out.items():
        b = float((camps.get(cid) or {}).get("budget") or 0)
        t["est"] = round(min(t["est"], b) if b > 0 else t["est"], 2)
        t["paid"] = round(t["paid"], 2)
    return out
