"""Výsledky účtov pre Dashboard (0 tokenov): odberatelia a sledovatelia v čase, čas sledovania na YouTube
a cesta k zárobku (YouTube Partner Program).

Zdroje (len oficiálne API, ktoré appka už má pripojené, nič sa neplatí):
- YouTube Data API: počet odberateľov, zobrazení a videí kanála (1 jednotka kvóty na kanál, max pár desiatok denne,
  nahrávanie videí to nebrzdí: čítanie má vlastný strop READ_CAP a pri minutej kvóte sa len preskočí).
- YouTube Analytics API: denné zobrazenia, čas sledovania, noví odberatelia, a pri videách čas sledovania a koľko
  z videa ľudia pozrú. Má vlastnú kvótu, s nahrávaním sa nedelí. Treba ho mať zapnuté v Google projekte.
- Facebook / Instagram: počet sledovateľov stránky a účtu.
- TikTok (len účty cez TikTok Business) a LinkedIn (len firemná stránka): počet sledovateľov.
"""
import datetime as dt
import json
import time

from . import db
from .platforms import linkedin, meta, tiktok_business, youtube
from .platforms.common import client, tokens

YTA = "https://youtubeanalytics.googleapis.com/v2/reports"
READ_CAP = 150  # max. jednotiek YouTube Data API denne na Google projekt pre štatistiky (nahratie ich má tisíce)
YPP_DEADLINE = "2027-01-31"


def _now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ago(days):
    return (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return dt.date.today().isoformat()


# ---------- strop čítania z YouTube Data API ----------
def _cli(acc):
    return str(int(tokens(acc).get("client", 0) or 0))


def yt_blocked(acc=None):
    """Google projekty, ktoré dnes vyčerpali kvótu (čítanie sa už neskúša, nech nič neberie nahrávaniu)."""
    b = (db.get_setting("yt_read_block") or {}).get(_today(), [])
    return b if acc is None else _cli(acc) in b


def limit_today():
    """Je dnes niektorý Google projekt bez kvóty (vyčerpaná alebo minutá nahrávaním)?"""
    if yt_blocked():
        return True
    return any(not youtube.quota_ok(a) for a in db.q("SELECT tokens FROM accounts WHERE platform='youtube'"))


def block_today(acc):
    day = _today()
    b = (db.get_setting("yt_read_block") or {}).get(day, [])
    if _cli(acc) not in b:
        db.set_setting("yt_read_block", {day: b + [_cli(acc)]})


def _read_ok(acc, units=1):
    """Čítanie štatistík z YouTube Data API len z rezervy: nie pri vyčerpanej kvóte a nie keď sa blíži limit nahratí."""
    if yt_blocked(acc) or not youtube.quota_ok(acc):
        return False
    day = _today()
    u = db.get_setting("yt_read_units") or {}
    u = {day: u.get(day, {})}
    k = str(int(tokens(acc).get("client", 0) or 0))
    if u[day].get(k, 0) + units > READ_CAP:
        return False
    u[day][k] = u[day].get(k, 0) + units
    db.set_setting("yt_read_units", u)
    return True


def _ins(aid, **kw):
    db.run("INSERT OR IGNORE INTO acc_insight(account_id) VALUES(?)", (aid,))
    if kw:
        db.run(f"UPDATE acc_insight SET {', '.join(k + '=?' for k in kw)} WHERE account_id=?", (*kw.values(), aid))


def _snap(aid, followers, views_total=None, media=None):
    db.run("""INSERT INTO account_stats(account_id, day, followers, views_total, media_count, fetched_at) VALUES(?,?,?,?,?,?)
              ON CONFLICT(account_id, day) DO UPDATE SET followers=excluded.followers, views_total=excluded.views_total,
              media_count=excluded.media_count, fetched_at=excluded.fetched_at""",
           (aid, _today(), followers, views_total, media, _now()))


# ---------- YouTube ----------
def _yt_channel(acc):
    items = None
    if _read_ok(acc):
        tok = youtube.access_token(acc)
        with client() as c:
            r = c.get("https://www.googleapis.com/youtube/v3/channels", headers={"Authorization": f"Bearer {tok}"},
                      params={"part": "statistics", "id": acc["external_id"]} if acc["external_id"] else {"part": "statistics", "mine": "true"})
        if r.status_code == 200:
            items = r.json().get("items") or []
        elif "quota" in r.text.lower():
            block_today(acc)
        else:
            raise RuntimeError(_gerr(r))
    if items is None:
        raise RuntimeError("quota: dnes vyčerpaný limit YouTube, čísla prídu zajtra")
    if not items:
        raise RuntimeError("Kanál sa nenašiel")
    s = items[0].get("statistics", {})
    subs = None if s.get("hiddenSubscriberCount") else int(s.get("subscriberCount", 0) or 0)
    _snap(acc["id"], subs, int(s.get("viewCount", 0) or 0), int(s.get("videoCount", 0) or 0))


def _gerr(r):
    try:
        e = r.json()["error"]
        reason = ((e.get("errors") or [{}])[0]).get("reason", "") or e.get("status", "")
        return f"{reason}: {e.get('message', '')}"[:300]
    except Exception:
        return f"HTTP {r.status_code}: {r.text[:200]}"


def _report(c, tok, **params):
    r = c.get(YTA, headers={"Authorization": f"Bearer {tok}"}, params={"ids": "channel==MINE", **params})
    if r.status_code != 200:
        raise RuntimeError(_gerr(r))
    d = r.json()
    cols = [h["name"] for h in d.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in d.get("rows") or []]


def _yt_analytics(acc):
    """Raz denne na kanál: denné čísla za 90 dní, podmienky zárobku a čísla jednotlivých videí."""
    tok = youtube.access_token(acc)
    today = dt.date.today()
    d90, d365 = (today - dt.timedelta(days=89)).isoformat(), (today - dt.timedelta(days=364)).isoformat()
    with client() as c:
        rows = _report(c, tok, startDate=d90, endDate=today.isoformat(), dimensions="day", sort="day",
                       metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes,comments,shares")
        for x in rows:
            db.run("""INSERT OR REPLACE INTO yt_daily(account_id, day, views, watch_min, subs_gained, subs_lost, likes, comments, shares)
                      VALUES(?,?,?,?,?,?,?,?,?)""", (acc["id"], x["day"], int(x.get("views") or 0), float(x.get("estimatedMinutesWatched") or 0),
                                                     int(x.get("subscribersGained") or 0), int(x.get("subscribersLost") or 0),
                                                     int(x.get("likes") or 0), int(x.get("comments") or 0), int(x.get("shares") or 0)))
        ypp = {"split": True}
        try:  # rozdelenie na Shorts a dlhé videá (YouTube ráta zárobok zvlášť)
            y = _report(c, tok, startDate=d365, endDate=today.isoformat(), dimensions="creatorContentType",
                        metrics="views,estimatedMinutesWatched")
            q = _report(c, tok, startDate=d90, endDate=today.isoformat(), dimensions="creatorContentType", metrics="views")
            long_min = sum(float(x.get("estimatedMinutesWatched") or 0) for x in y if x.get("creatorContentType") not in ("SHORTS", "STORY"))
            ypp.update(long_hours=round(long_min / 60, 1),
                       shorts_views_90=sum(int(x.get("views") or 0) for x in q if x.get("creatorContentType") == "SHORTS"),
                       all_views_365=sum(int(x.get("views") or 0) for x in y))
        except RuntimeError:
            y = _report(c, tok, startDate=d365, endDate=today.isoformat(), metrics="views,estimatedMinutesWatched")
            ypp.update(split=False, long_hours=round(sum(float(x.get("estimatedMinutesWatched") or 0) for x in y) / 60, 1),
                       shorts_views_90=None, all_views_365=sum(int(x.get("views") or 0) for x in y))
        # čísla videí (posledných 200 podľa zobrazení, za celý čas)
        vids = _report(c, tok, startDate="2015-01-01", endDate=today.isoformat(), dimensions="video", sort="-views", maxResults=200,
                       metrics="views,estimatedMinutesWatched,averageViewPercentage,subscribersGained,likes,comments")
    posts = {p["external_id"]: p["id"] for p in db.q("SELECT id, external_id FROM posts WHERE account_id=? AND external_id!=''", (acc["id"],))}
    for x in vids:
        pid = posts.get(x.get("video"))
        if pid:
            db.run("INSERT OR IGNORE INTO post_stats(post_id, fetched_at) VALUES(?, '')", (pid,))
            db.run("UPDATE post_stats SET watch_min=?, avg_pct=?, subs=? WHERE post_id=?",
                   (float(x.get("estimatedMinutesWatched") or 0), float(x.get("averageViewPercentage") or 0),
                    int(x.get("subscribersGained") or 0), pid))
            _merge(pid, int(x.get("views") or 0), int(x.get("likes") or 0), int(x.get("comments") or 0))
    ypp["at"] = _now()
    _ins(acc["id"], ypp=json.dumps(ypp), analytics_at=_now(), analytics_error="")


def _merge(pid, views, likes, comments=None):
    """Zapíše čísla videa; berie vyššie z oboch zdrojov (feed je čerstvejší, Analytics má komentáre)."""
    db.run("INSERT OR IGNORE INTO post_stats(post_id, fetched_at) VALUES(?, '')", (pid,))
    db.run("""UPDATE post_stats SET views=MAX(views, ?), likes=MAX(likes, ?), comments=MAX(comments, COALESCE(?, comments)),
              fetched_at=?, error='' WHERE post_id=?""", (views, likes, comments, _now(), pid))


def rss_job():
    """Každú hodinu, zadarmo a bez kvóty: verejný feed kanála (posledných 15 videí) s pozretiami a lajkami."""
    import re
    for acc in db.q("SELECT id, external_id FROM accounts WHERE platform='youtube' AND external_id LIKE 'UC%'"):
        posts = {p["external_id"]: p["id"] for p in db.q("SELECT id, external_id FROM posts WHERE account_id=? AND status='done' AND external_id!=''",
                                                         (acc["id"],))}
        if not posts:
            continue
        try:
            with client() as c:
                r = c.get("https://www.youtube.com/feeds/videos.xml", params={"channel_id": acc["external_id"]})
            if r.status_code != 200:
                continue
            for e in r.text.split("<entry>")[1:]:
                vid = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", e)
                if not vid or vid.group(1) not in posts:
                    continue
                v = re.search(r'<media:statistics views="(\d+)"', e)
                lk = re.search(r'<media:starRating count="(\d+)"', e)
                _merge(posts[vid.group(1)], int(v.group(1)) if v else 0, int(lk.group(1)) if lk else 0)
        except Exception as ex:
            print("YouTube feed:", ex)
        time.sleep(0.5)


# ---------- ostatné siete: len počet sledovateľov ----------
def _fb(acc):
    t = tokens(acc)
    with client() as c:
        r = c.get(meta.G(acc["external_id"]), params={"access_token": t["page_token"], "fields": "followers_count,fan_count"})
    if r.status_code != 200:
        raise RuntimeError(_gerr(r))
    d = r.json()
    _snap(acc["id"], d.get("followers_count", d.get("fan_count")))


def _ig(acc):
    t = tokens(acc)
    with client() as c:
        r = c.get(meta.G(acc["external_id"]), params={"access_token": t["page_token"], "fields": "followers_count,media_count"})
    if r.status_code != 200:
        raise RuntimeError(_gerr(r))
    d = r.json()
    _snap(acc["id"], d.get("followers_count"), None, d.get("media_count"))


def _tt(acc):
    if tokens(acc).get("api") != "business":
        raise RuntimeError("nobusiness")
    tok = tiktok_business.access_token(acc)
    with client() as c:
        r = c.get(f"{tiktok_business.API}/business/get/", headers={"Access-Token": tok},
                  params={"business_id": acc["external_id"], "fields": json.dumps(["followers_count"])})
    d = r.json() if r.status_code == 200 else {}
    if d.get("code") not in (0, None) or "data" not in d:
        raise RuntimeError((d.get("message") or f"HTTP {r.status_code}")[:200])
    data = d.get("data") or {}
    f = data.get("followers_count")
    if f is None and data.get("metrics"):
        f = (data["metrics"][-1] or {}).get("followers_count")
    _snap(acc["id"], f)


def _li(acc):
    if not linkedin.is_org(acc):
        raise RuntimeError("noorg")
    f = linkedin.followers(acc)
    if f is None:
        raise RuntimeError("LinkedIn nedal počet sledovateľov")
    _snap(acc["id"], f)


SNAP = {"youtube": _yt_channel, "facebook": _fb, "instagram": _ig, "tiktok": _tt, "linkedin": _li}


_busy = {"on": False}


def refresh(force=False):
    """Ručné „Stiahnuť čísla teraz“ (v pozadí, nič nečaká). Analytics najviac raz za 2 h."""
    if _busy["on"]:
        return False
    if force:
        db.run("UPDATE acc_insight SET stats_at='' WHERE stats_at<?", (_ago(1 / 144),))
        db.run("UPDATE acc_insight SET analytics_at='' WHERE analytics_at<?", (_ago(1 / 12),))
        db.run("UPDATE post_stats SET fetched_at='' WHERE fetched_at<?", (_ago(1 / 144),))

    def go():
        _busy["on"] = True
        try:
            from . import stats
            try:
                rss_job()
            except Exception as e:
                print("YouTube feed:", e)
            try:
                stats.job()
            except Exception as e:
                print("Štatistiky príspevkov:", e)
            job()
        finally:
            _busy["on"] = False
    import threading
    threading.Thread(target=go, daemon=True).start()
    return True


def job():
    """Každých 6 h počty sledovateľov, raz denne YouTube Analytics. Chyba jedného účtu nezastaví ostatné."""
    for acc in db.q("SELECT * FROM accounts"):
        fn = SNAP.get(acc["platform"])
        if not fn:
            continue
        st = db.one("SELECT * FROM acc_insight WHERE account_id=?", (acc["id"],)) or {}
        if (st.get("stats_at") or "") < _ago(0.24):
            try:
                fn(acc)
                _ins(acc["id"], stats_at=_now(), error="")
            except Exception as e:
                _ins(acc["id"], stats_at=_now(), error=str(e)[:300])
            time.sleep(0.3)
        if acc["platform"] == "youtube" and (st.get("analytics_at") or "") < _ago(0.125):  # každé 3 h (vlastná kvóta Analytics)
            try:
                _yt_analytics(acc)
            except Exception as e:
                _ins(acc["id"], analytics_at=_now(), analytics_error=str(e)[:300])
            time.sleep(0.3)
    db.run("DELETE FROM yt_daily WHERE day<?", ((dt.date.today() - dt.timedelta(days=800)).isoformat(),))


# ---------- dáta pre Dashboard ----------
def _gproject(acc):
    """Google Cloud projekt kanála (na priamy odkaz, kde sa zapína YouTube Analytics)."""
    try:
        cl = youtube.clients()
        i = int(tokens(acc).get("client", 0) or 0)
        return (cl[i] if i < len(cl) else cl[0]).get("project_id", "")
    except Exception:
        return ""


def _human(acc, err, analytics=False):
    e = (err or "").lower()
    if not e or e in ("nobusiness", "noorg"):
        return ""
    if any(k in e for k in ("accessnotconfigured", "has not been used", "is disabled", "service_disabled")):
        return "analytics_off"
    if "insufficient" in e or "scope" in e:
        return "Chýba povolenie na čítanie štatistík, pripoj účet znova."
    if "quota" in e:
        return "Dnes minutá kvóta YouTube, skúsi sa zajtra."
    if any(k in e for k in ("vypršalo", "invalid_grant", "expired", "unauthenticated", "invalid_token", "oauthexception")):
        return "Prihlásenie vypršalo, pripoj účet znova."
    return err[:160]


def accounts_data(since_day):
    """Účty s posledným a starším počtom sledovateľov, denné čísla YouTube a podmienky zárobku."""
    accs = db.q("SELECT id, platform, name, project_id, country, lang, tokens, external_id FROM accounts")
    ins = {r["account_id"]: r for r in db.q("SELECT * FROM acc_insight")}
    snaps = {}
    for r in db.q("SELECT account_id, day, followers, views_total, media_count FROM account_stats WHERE followers IS NOT NULL ORDER BY day"):
        snaps.setdefault(r["account_id"], []).append(r)
    out, off_projects = [], {}
    for a in accs:
        s = snaps.get(a["id"], [])
        last = s[-1] if s else None
        before = [x for x in s if x["day"] <= since_day]
        base = before[-1] if before else (s[0] if s else None)
        i = ins.get(a["id"]) or {}
        tt_note = a["platform"] == "tiktok" and json.loads(a["tokens"] or "{}").get("api") != "business"
        err = _human(a, i.get("error"))
        aerr = _human(a, i.get("analytics_error"), True) if a["platform"] == "youtube" else ""
        if aerr == "analytics_off":
            gp = _gproject(a)
            off_projects[gp] = off_projects.get(gp, 0) + 1
        out.append({"id": a["id"], "pl": a["platform"], "name": a["name"], "p": a["project_id"], "c": (a["country"] or "").upper(),
                    "l": a["lang"] or "", "f": last["followers"] if last else None, "f0": base["followers"] if base else None,
                    "f0d": base["day"] if base else None, "vt": last["views_total"] if last else None,
                    "mc": last["media_count"] if last else None, "first": s[0]["day"] if s else None,
                    "ypp": json.loads(i.get("ypp") or "{}") if a["platform"] == "youtube" else None,
                    "err": err, "aerr": "" if aerr == "analytics_off" else aerr, "aoff": aerr == "analytics_off",
                    "tt_draft": tt_note, "li_personal": a["platform"] == "linkedin" and not linkedin.is_org(a)})
    daily = db.q("SELECT account_id a, day d, views v, watch_min w, subs_gained sg, subs_lost sl, likes lk, comments cm FROM yt_daily WHERE day>=?",
                 (since_day,))
    return out, daily, [{"project": k, "channels": v} for k, v in off_projects.items()]


def production(since):
    """Koľko je vymyslené, napísané, vyrobené, na schválenie, naplánované a zverejnené (po projektoch)."""
    out = {}

    def add(sql, key, args=()):
        for r in db.q(sql, args):
            out.setdefault(r["p"], {})[key] = r["n"]
    add("SELECT project_id p, COUNT(*) n FROM ideas WHERE status IN ('new','approved','inbox') GROUP BY project_id", "ideas")
    add("SELECT project_id p, COUNT(*) n FROM scripts WHERE is_source=1 AND created_at>=? GROUP BY project_id", "scripts", (since,))
    add("SELECT project_id p, COUNT(*) n FROM videos WHERE created_at>=? GROUP BY project_id", "made", (since,))
    for st, key in (("review", "review"), ("queued", "queued"), ("uploading", "queued"), ("failed", "failed")):
        for r in db.q("""SELECT v.project_id p, COUNT(*) n FROM posts p JOIN videos v ON v.id=p.video_id WHERE p.status=? GROUP BY v.project_id""", (st,)):
            out.setdefault(r["p"], {})[key] = out.get(r["p"], {}).get(key, 0) + r["n"]
    add("""SELECT v.project_id p, COUNT(*) n FROM posts p JOIN videos v ON v.id=p.video_id
           WHERE p.status='done' AND p.updated_at>=? GROUP BY v.project_id""", "done", (since,))
    nxt = db.q("""SELECT v.project_id p, MIN(p.scheduled_at) t FROM posts p JOIN videos v ON v.id=p.video_id
                  WHERE p.status='queued' AND p.scheduled_at>=? GROUP BY v.project_id""", (_now(),))
    for r in nxt:
        out.setdefault(r["p"], {})["next"] = r["t"]
    return {str(k): v for k, v in out.items() if k is not None}
