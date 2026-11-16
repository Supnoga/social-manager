"""Sledovanie klipov: pozretia zo sietí (hotové čítanie Social Managera) a odhad zárobku podľa pravidiel kampane.

Odhad je len orientačný. Platí číslo, ktoré ukáže stránka kampane po schválení klipu."""
import time
from datetime import datetime, timedelta

from app import db as appdb
from app import stats as appstats

from . import store

EVERY = 3 * 3600
SUBMIT = ("todo", "submitted", "approved", "rejected", "paid")


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


def campaign_totals():
    """Súčty po kampaniach: klipy, zverejnenia, pozretia, odhad zárobku, vyplatené."""
    out = {}
    camps = {c["id"]: c for c in store.q("SELECT * FROM campaigns")}
    for r in store.q("SELECT p.views, p.submit, p.paid, p.status, c.campaign_id FROM posts p JOIN clips c ON c.id=p.clip_id"):
        t = out.setdefault(r["campaign_id"], {"posted": 0, "queued": 0, "views": 0, "est": 0.0, "paid": 0.0, "todo": 0})
        if r["status"] == "posted":
            t["posted"] += 1
            t["views"] += r["views"] or 0
            if r["submit"] != "rejected":
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
