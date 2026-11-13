"""Učenie z výsledkov (0 tokenov): čísla našich zverejnených videí zo sietí, porovnanie s bežným výkonom účtu,
najlepšie hodiny na zverejnenie a krátky výťah „čo funguje“ pre vymýšľanie nápadov.

Čísla sa sťahujú cez oficiálne API sietí, ktoré appka už má pripojené (nič navyše sa neplatí).
LinkedIn dáva čísla len firemnej stránke (osobný profil sa preskakuje).
"""
import datetime as dt
import json
import statistics

from . import db
from .platforms import linkedin, meta, tiktok_business, youtube
from .platforms.common import client, tokens

# štandardné časy (slovenský čas), kým appka nemá vlastné čísla; zdroj: verejné prehľady sietí 2025-2026
DEFAULT_HOURS = {"tiktok": [19, 12, 21, 16], "instagram": [18, 11, 20, 13], "youtube": [17, 12, 20, 15],
                 "facebook": [13, 9, 19, 16], "linkedin": [8, 12, 17, 10]}
# posun voči slovenskému času podľa jazyka účtu (aby ľudia v cieľovej krajine videli video v ich dobrý čas)
TZ_SHIFT = {"en": -1, "pt": -1, "ga": -1, "is": -1, "el": 1, "fi": 1, "et": 1, "lv": 1, "lt": 1, "ro": 1, "bg": 1, "uk": 1,
            "tr": 2, "ru": 2}


def _now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ago(days):
    return (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


# ---------- sťahovanie čísel ----------
def _yt(acc, posts):
    from .insights import _read_ok
    tok = youtube.access_token(acc)
    out = {}
    with client() as c:
        for i in range(0, len(posts), 50):
            if not _read_ok(acc):  # strop čítania: nahrávanie videí má prednosť
                break
            ids = [p["external_id"] for p in posts[i:i + 50]]
            r = c.get("https://www.googleapis.com/youtube/v3/videos", headers={"Authorization": f"Bearer {tok}"},
                      params={"part": "statistics", "id": ",".join(ids)})
            if r.status_code == 403 and "quota" in r.text.lower():
                from .insights import block_today
                block_today(acc)
                break
            r.raise_for_status()
            for v in r.json().get("items", []):
                s = v.get("statistics", {})
                out[v["id"]] = (int(s.get("viewCount", 0) or 0), int(s.get("likeCount", 0) or 0), int(s.get("commentCount", 0) or 0), 0)
    return out


def _fb(acc, posts):
    t = tokens(acc)
    out = {}
    with client() as c:
        for p in posts:
            views = likes = comments = 0
            r = c.get(meta.G(f"{p['external_id']}/video_insights"), params={"access_token": t["page_token"],
                                                                          "metric": "total_video_views,blue_reels_play_count"})
            if r.status_code == 200:
                for m in r.json().get("data", []):
                    views = max(views, int(((m.get("values") or [{}])[0]).get("value") or 0))
            r = c.get(meta.G(p["external_id"]), params={"access_token": t["page_token"],
                                                       "fields": "likes.summary(true).limit(0),comments.summary(true).limit(0)"})
            if r.status_code == 200:
                d = r.json()
                likes = ((d.get("likes") or {}).get("summary") or {}).get("total_count", 0)
                comments = ((d.get("comments") or {}).get("summary") or {}).get("total_count", 0)
            out[p["external_id"]] = (views, likes, comments, 0)
    return out


def _ig(acc, posts):
    t = tokens(acc)
    out = {}
    with client() as c:
        for p in posts:
            vals = {}
            for metric in ("views,likes,comments,shares", "reach,likes,comments,shares"):
                r = c.get(meta.G(f"{p['external_id']}/insights"), params={"access_token": t["page_token"], "metric": metric})
                if r.status_code == 200:
                    vals = {m["name"]: int(((m.get("values") or [{}])[0]).get("value") or 0) for m in r.json().get("data", [])}
                    break
            if vals:
                out[p["external_id"]] = (vals.get("views") or vals.get("reach", 0), vals.get("likes", 0), vals.get("comments", 0),
                                         vals.get("shares", 0))
    return out


def _tt(acc, posts):
    if tokens(acc).get("api") != "business":
        return {}
    import re
    tok = tiktok_business.access_token(acc)
    ids = {}
    for p in posts:
        m = re.search(r"/video/(\d+)", p.get("url") or "")
        if m:
            ids[m.group(1)] = p["external_id"]
    out = {}
    if not ids:
        return out
    with client() as c:
        keys = list(ids)
        for i in range(0, len(keys), 20):
            r = c.get(f"{tiktok_business.API}/business/video/list/", headers={"Access-Token": tok}, params={
                "business_id": acc["external_id"],
                "fields": json.dumps(["item_id", "video_views", "likes", "comments", "shares"]),
                "filters": json.dumps({"video_ids": keys[i:i + 20]})})
            d = r.json() if r.status_code == 200 else {}
            for v in (d.get("data") or {}).get("videos", []):
                ext = ids.get(str(v.get("item_id")))
                if ext:
                    out[ext] = (int(v.get("video_views", 0) or 0), int(v.get("likes", 0) or 0), int(v.get("comments", 0) or 0),
                                int(v.get("shares", 0) or 0))
    return out


FETCHERS = {"youtube": _yt, "facebook": _fb, "instagram": _ig, "tiktok": _tt, "linkedin": linkedin.stats}


def job():
    """Raz za 6 h: čísla k videám zverejneným za posledných 90 dní (nové max raz za 12 h, staršie ako 14 dní raz za 2 dni)."""
    linkedin.refresh_all()
    rows = db.q("""SELECT p.*, ps.fetched_at FROM posts p LEFT JOIN post_stats ps ON ps.post_id=p.id
                   WHERE p.status='done' AND p.external_id!='' AND p.updated_at>=?""", (_ago(90),))
    by_acc = {}
    for r in rows:
        if r["fetched_at"] and r["fetched_at"] > _ago(0.5 if r["updated_at"] > _ago(14) else 2):
            continue
        by_acc.setdefault(r["account_id"], []).append(r)
    for aid, posts in by_acc.items():
        acc = db.one("SELECT * FROM accounts WHERE id=?", (aid,))
        fn = FETCHERS.get((acc or {}).get("platform"))
        if not fn:
            continue
        try:
            res = fn(acc, posts)
            err = ""
        except Exception as e:
            res, err = {}, str(e)[:200]
        for p in posts:
            v = res.get(p["external_id"])
            if v:
                db.run("""INSERT INTO post_stats(post_id, views, likes, comments, shares, fetched_at, error) VALUES(?,?,?,?,?,?,'')
                          ON CONFLICT(post_id) DO UPDATE SET views=excluded.views, likes=excluded.likes, comments=excluded.comments,
                          shares=excluded.shares, fetched_at=excluded.fetched_at, error=''""", (p["id"], *v, _now()))
            else:
                db.run("""INSERT INTO post_stats(post_id, fetched_at, error) VALUES(?,?,?)
                          ON CONFLICT(post_id) DO UPDATE SET fetched_at=excluded.fetched_at, error=excluded.error""",
                       (p["id"], _now(), err or "bez čísel"))
        _rescore(aid)
    for p in db.q("SELECT id FROM projects"):
        db.run("UPDATE projects SET learnings=? WHERE id=?", (learnings(p["id"]), p["id"]))


def _rescore(aid):
    """Pomer k bežnému výkonu účtu (medián), aby sa dali porovnať malé aj veľké účty."""
    rows = db.q("""SELECT ps.post_id, ps.views FROM post_stats ps JOIN posts p ON p.id=ps.post_id
                   WHERE p.account_id=? AND ps.error='' ORDER BY p.scheduled_at DESC LIMIT 60""", (aid,))
    vals = [r["views"] for r in rows if r["views"]]
    base = statistics.median(vals) if len(vals) >= 3 else 0
    for r in rows:
        db.run("UPDATE post_stats SET ratio=? WHERE post_id=?", (round(r["views"] / base, 2) if base else 0, r["post_id"]))


# ---------- vyhodnotenie ----------
def _rows(pid=None, days=90):
    return db.q(f"""SELECT ps.*, p.account_id, p.scheduled_at, a.platform, a.name account, a.lang acc_lang, v.lang, v.title,
                          s.idea_id, i.title idea_title, i.hook, i.pillar, i.project_id
                   FROM post_stats ps JOIN posts p ON p.id=ps.post_id JOIN accounts a ON a.id=p.account_id
                   JOIN videos v ON v.id=p.video_id LEFT JOIN scripts s ON s.id=v.script_id LEFT JOIN ideas i ON i.id=s.idea_id
                   WHERE ps.error='' AND p.scheduled_at>=? {'AND v.project_id=?' if pid else ''}""",
                (_ago(days), pid) if pid else (_ago(days),))


def ideas_perf(pid, days=90):
    """Výkon nápadov (všetky jazyky a účty spolu): priemerný pomer k bežnému výkonu účtov."""
    agg = {}
    for r in _rows(pid, days):
        if not r["idea_id"] or not r["ratio"]:
            continue
        a = agg.setdefault(r["idea_id"], {"idea_id": r["idea_id"], "title": r["idea_title"], "hook": r["hook"], "pillar": r["pillar"],
                                          "ratios": [], "views": 0, "likes": 0, "comments": 0, "posts": 0})
        a["ratios"].append(r["ratio"])
        a["views"] += r["views"]
        a["likes"] += r["likes"]
        a["comments"] += r["comments"]
        a["posts"] += 1
    out = []
    for a in agg.values():
        a["ratio"] = round(statistics.median(a.pop("ratios")), 2)
        out.append(a)
    out.sort(key=lambda x: -x["ratio"])
    return out


def winners(pid, min_ratio=1.8):
    return [x for x in ideas_perf(pid) if x["ratio"] >= min_ratio and x["posts"] >= 1]


def learnings(pid):
    """Krátky výťah pre AI (~100-150 tokenov). Bez čísel = prázdny reťazec (nič sa neposiela)."""
    perf = ideas_perf(pid)
    if len(perf) < 4:
        return ""
    top = [x for x in perf[:4] if x["ratio"] >= 1.0] or perf[:2]
    low = [x for x in perf[len(top):][-3:] if x["ratio"] < 0.8]
    pil = {}
    for x in perf:
        if x["pillar"]:
            pil.setdefault(x["pillar"], []).append(x["ratio"])
    pil_txt = ", ".join(f"{k} {statistics.median(v):.1f}x" for k, v in sorted(pil.items(), key=lambda kv: -statistics.median(kv[1]))[:4])
    t = "WORKED (x = vs normal): " + "; ".join(f'"{x["title"][:60]}" {x["ratio"]}x' for x in top)
    if low:
        t += " | FLOPPED: " + "; ".join(f'"{x["title"][:50]}" {x["ratio"]}x' for x in low)
    if pil_txt:
        t += " | pillars: " + pil_txt
    return t[:700]


def best_hours(account, n=3):
    """Najlepšie hodiny pre účet: z vlastných čísel (účet, potom celá sieť), inak štandardné časy pre krajinu."""
    rows = db.q("""SELECT ps.ratio, p.scheduled_at, p.account_id FROM post_stats ps JOIN posts p ON p.id=ps.post_id
                   JOIN accounts a ON a.id=p.account_id WHERE a.platform=? AND ps.error='' AND ps.ratio>0 AND p.scheduled_at>=?""",
                (account["platform"], _ago(120)))
    from . import languages
    c = (account.get("country") or "").upper()
    shift = languages.COUNTRY_TZ.get(c, 0) if c else TZ_SHIFT.get(account.get("lang") or "", 0)
    for scope in ([r for r in rows if r["account_id"] == account["id"]], rows):
        if len(scope) < 12:
            continue
        hrs = {}
        for r in scope:
            hrs.setdefault(int(r["scheduled_at"][11:13]), []).append(r["ratio"])
        good = sorted([(statistics.median(v), h) for h, v in hrs.items() if len(v) >= 3], reverse=True)
        if len(good) >= n:
            return [h for _, h in good[:n]], "z tvojich čísel"
    base = DEFAULT_HOURS.get(account["platform"], [18, 12, 9])
    return [(h - shift) % 24 for h in base[:n]] if shift else base[:n], "štandardné časy"


def overview(pid):
    perf = ideas_perf(pid)
    accs = db.q("SELECT * FROM accounts WHERE project_id=? OR project_id IS NULL", (pid,))
    times = []
    for a in accs[:60]:
        h, how = best_hours(a)
        times.append({"account": a["name"], "platform": a["platform"], "lang": a.get("country") or a["lang"], "hours": sorted(h), "how": how})
    st = db.one("""SELECT COUNT(*) n, MAX(ps.fetched_at) last FROM post_stats ps JOIN posts p ON p.id=ps.post_id
                   JOIN videos v ON v.id=p.video_id WHERE v.project_id=? AND ps.error=''""", (pid,))
    return {"ideas": perf[:30], "winners": [x for x in perf if x["ratio"] >= 1.8][:10], "times": times,
            "measured": st["n"], "last": st["last"], "learnings": learnings(pid)}
