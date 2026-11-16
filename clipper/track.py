"""Sledovanie klipov: pozretia zo sietí (hotové čítanie Social Managera) a odhad zárobku podľa pravidiel kampane.

Odhad je len orientačný. Platí číslo, ktoré ukáže stránka kampane po schválení klipu."""
import math
import re
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


def _pts(x):
    return int(max(1, min(10, math.floor(x + 0.5))))


def _top_views(text):
    """Najvyšší počet pozretí spomenutý v poli „Čo tu funguje“ (403K, 1.2M, 42 000)."""
    best = 0.0
    for num, unit in re.findall(r"(\d[\d ,.]*)\s*([kKmM]|tis|mil)?", text or ""):
        try:
            v = float(num.replace(" ", "").replace(",", "." if unit else ""))
        except ValueError:
            continue
        v *= {"k": 1e3, "t": 1e3, "m": 1e6}.get((unit or "")[:1].lower(), 1)
        if v >= 1000:
            best = max(best, v)
    return best


def points(c):
    """Bodovanie kampane (partnerstva) 1 až 10 v piatich veciach, spolu najviac 50. Vráti aj krátke vysvetlenia.
    cena = sadzba; viralita = koľko pozretí tam klipy naozaj robia (alebo odhad, kým čísla nie sú); konkurencia = počet kliperov;
    rozpočet = koľko peňazí ostáva a na ako dlho; hodí sa = či to appka vie strihať sama."""
    rate, budget, spent = float(c.get("rate") or 0), float(c.get("budget") or 0), max(0.0, float(c.get("spent") or 0))
    clippers = int(c.get("clippers") or 0)
    age = float(c.get("age_days") or 0)
    try:
        age += max(0, (datetime.now() - datetime.strptime((c.get("created_at") or "")[:10], "%Y-%m-%d")).days)
    except Exception:
        pass
    out, why = {}, {}
    out["cena"] = _pts(rate * 3 + 1) if rate > 0 else 1
    why["cena"] = f"{rate:g} $ za 1 000 pozretí".replace(".", ",")
    # viralita: zaplatené pozretia na jedného klipera a najlepší klip kampane
    parts = []
    if rate > 0 and spent >= 200 and clippers > 0:
        vpc = spent / rate * 1000 / clippers
        parts.append((0.6, 2.5 * math.log10(max(vpc, 10)) - 4.5))
        why["viral"] = f"na klipera {_short(vpc)} zaplatených pozretí"
    top = _top_views(c.get("winners"))
    if top:
        parts.append((0.4, 2.5 * math.log10(top) - 5.5))
        why["viral"] = (why.get("viral", "") + ", " if why.get("viral") else "") + f"najlepší klip {_short(top)}"
    if parts:
        out["viral"] = _pts(sum(w * v for w, v in parts) / sum(w for w, _ in parts))
    elif int(c.get("viral") or 0) > 0:
        out["viral"] = _pts(int(c["viral"]))
        why["viral"] = "odhad, kampaň ešte nemá vlastné čísla"
    else:
        out["viral"] = 5
        why["viral"] = "bez údajov, stred"
    out["konk"] = _pts(11 - 3.2 * math.log10(clippers + 1))
    why["konk"] = f"{clippers} kliperov" if clippers else "zatiaľ nikto alebo neuvedené"
    if budget > 0:
        left = max(0.0, budget - spent)
        p = 3 * math.log10(max(left, 10)) - 5.5
        why["rozp"] = f"ostáva {_usd(left)} z {_usd(budget)}"
        if spent > 0 and age >= 1:
            days = left / (spent / age)
            p -= 4 if days < 3 else 2 if days < 7 else 0
            if days < 60:
                why["rozp"] += f", asi na {int(round(days))} dní"
        out["rozp"] = _pts(p)
    else:
        out["rozp"] = 5
        why["rozp"] = "rozpočet neuvedený"
    if int(c.get("fit") or 0) > 0:
        out["fit"] = _pts(int(c["fit"]))
    else:
        out["fit"] = {"speech": 9, "visual": 6}.get(c.get("kind") or "auto", 7)
    why["fit"] = {9: "reč: appka strihá sama", 6: "obraz: appka vie, ale horšie"}.get(out["fit"], "ako dobre to appka zvládne sama")
    out["total"] = sum(out[k] for k in ("cena", "viral", "konk", "rozp", "fit"))
    out["why"] = why
    return out


def _short(v):
    return f"{v / 1e6:.1f} mil.".replace(".", ",", 1) if v >= 1e6 else f"{int(round(v / 1000))} tis." if v >= 1000 else str(int(v))


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
