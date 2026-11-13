"""Radar: trendy (Google Trendy, Wikipédia, Google Správy, YouTube), konkurencia (YouTube) a schránka nápadov.

Zber, počítanie a triedenie robí program (0 tokenov). Claude dostane len krátky výťah raz týždenne,
alebo keď klikneš „Nápad z tohto“. Všetko zadarmo a cez oficiálne zdroje (žiadne scrapovanie sietí).
"""
import datetime as dt
import hashlib
import json
import math
import re
import statistics
import threading
import time
import unicodedata
import xml.etree.ElementTree as ET

import httpx

from . import db, languages

UA = "SocialManager/1.9 (personal use; social media planning) httpx"
STATE = {"running": False, "job": "", "last_error": ""}

LANG_COUNTRIES = {**{k: [] for k in languages.LANGUAGES}, **{k: [c for c in v if c != 'XK'] for k, v in languages.COUNTRIES.items()}}
WIKI = {"no": "no", "bs": "bs"}  # inak kód jazyka = wiki

STOP = set("""a aj ako ale alebo and ani are as at be bol by by co do for from had has have i in is it je jej ju k ked
ktory ktora kde ma na nie od of on ona or pre pri s sa si so su ta the to too u v vo z za ze že der die das und mit von
den dem des ein eine ist im zu le la les de du des et en un une est pour il el los las y con por del al lo para
il di che e per un una gli della dei i w z na do sie się nie jak ze jest to o od za po te que um uma os as no da
do em för och att det som på en ett med av har ik het een van op met voor ze zijn niet aan""".split())


# ---------- text ----------
def normalize(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9Ͱ-ϿЀ-ӿ]+", s) if t not in STOP and len(t) > 1]


def stems(s):
    return sorted({t[:5] if len(t) >= 6 else t for t in normalize(s)})


def jaccard(a, b):
    A, B = set(a), set(b)
    return len(A & B) / max(1, len(A | B))


def _now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get(url, **kw):
    r = httpx.get(url, headers={"User-Agent": UA}, timeout=25, follow_redirects=True, **kw)
    r.raise_for_status()
    return r


def _log(source, key, ok, units=0, note=""):
    db.run("INSERT INTO fetch_log(source, key, ok, units, note) VALUES(?,?,?,?,?)", (source, key, int(ok), units, note[:300]))


# ---------- projekty, jazyky, krajiny ----------
def _projects():
    rows = db.q("SELECT * FROM projects")
    for p in rows:
        p["languages"] = json.loads(p["languages"] or "[]")
    return rows


def _countries():
    out = set()
    for p in _projects():
        for l in p["languages"]:
            out.update(LANG_COUNTRIES.get(l, [])[:2])
    return sorted(out)


def _country_lang(c):
    for l, cs in LANG_COUNTRIES.items():
        if c in cs:
            return l
    return ""


def _upsert(source, country, lang, term, context="", volume=0, url="", extra=None):
    norm = " ".join(stems(term))
    if not norm:
        return
    ex = db.one("SELECT id FROM trend_items WHERE source=? AND country=? AND norm=?", (source, country, norm))
    if ex:
        db.run("UPDATE trend_items SET last_seen=?, seen_count=seen_count+1, volume=MAX(volume,?), context=? WHERE id=?",
               (_now(), volume, context[:300], ex["id"]))
    else:
        db.run("""INSERT INTO trend_items(source,country,lang,term,norm,context,volume,url,extra,first_seen,last_seen)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (source, country, lang, term[:200], norm, context[:300], volume, url,
                                                     json.dumps(extra or {}), _now(), _now()))


# ---------- zdroje trendov ----------
def job_gtrends():
    for c in _countries():
        try:
            r = _get("https://trends.google.com/trending/rss", params={"geo": c})
            root = ET.fromstring(r.content)
            ns = {"ht": "https://trends.google.com/trending/rss"}
            for it in root.iter("item"):
                title = (it.findtext("title") or "").strip()
                traffic = it.findtext("ht:approx_traffic", default="", namespaces=ns) or ""
                vol = float(re.sub(r"[^\d]", "", traffic) or 0)
                news = [n.findtext("ht:news_item_title", default="", namespaces=ns) for n in it.findall("ht:news_item", ns)]
                _upsert("gtrends", c, _country_lang(c), title, " | ".join(x for x in news if x)[:300], vol,
                        f"https://trends.google.com/trends/explore?geo={c}&q={title}")
            _log("gtrends", c, 1)
        except Exception as e:
            _log("gtrends", c, 0, note=str(e))
        time.sleep(1)


def job_news():
    for p in _projects():
        for l in p["languages"][:6]:
            cs = LANG_COUNTRIES.get(l) or []
            if not cs:
                continue
            kw = db.one("SELECT core FROM project_keywords WHERE project_id=? AND lang=?", (p["id"], l))
            core = json.loads(kw["core"]) if kw else []
            if not core:
                continue
            q = " OR ".join(f'"{x}"' if " " in x else x for x in core[:6]) + " when:2d"
            c = cs[0]
            try:
                r = _get("https://news.google.com/rss/search", params={"q": q, "hl": l, "gl": c, "ceid": f"{c}:{l}"})
                root = ET.fromstring(r.content)
                for it in list(root.iter("item"))[:20]:
                    title = re.sub(r"\s+-\s+[^-]+$", "", it.findtext("title") or "")
                    _upsert("news", c, l, title, it.findtext("source") or "", 0, it.findtext("link") or "")
                _log("news", f"{p['id']}:{l}", 1)
            except Exception as e:
                _log("news", f"{p['id']}:{l}", 0, note=str(e))
            time.sleep(1)


def job_wiki():
    day = dt.date.today() - dt.timedelta(days=1)
    langs = sorted({l for p in _projects() for l in p["languages"]})
    for l in langs:
        w = WIKI.get(l, l)
        try:
            r = _get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{w}.wikipedia/all-access/{day:%Y/%m/%d}")
            arts = r.json()["items"][0]["articles"]
            for a in arts[:200]:
                t = a["article"]
                if ":" in t or a["rank"] <= 1 or t.startswith("-"):
                    continue
                _upsert("wiki", "", l, t.replace("_", " "), "", a["views"], f"https://{w}.wikipedia.org/wiki/{t}")
            _log("wiki", l, 1)
        except Exception as e:
            _log("wiki", l, 0, note=str(e))
        time.sleep(1)


# ---------- YouTube (kľúč zadarmo) ----------
def yt_key():
    return (db.get_setting("yt_api_key", "") or "").strip()


def yt_units_today():
    return db.one("SELECT COALESCE(SUM(units),0) n FROM fetch_log WHERE source LIKE 'yt%' AND ts>=?",
                  (dt.date.today().strftime("%Y-%m-%d"),))["n"]


def _yt(path, units=1, **params):
    if not yt_key():
        raise RuntimeError("Chýba YouTube API kľúč (Nastavenia → Radar)")
    if yt_units_today() > 8000:
        raise RuntimeError("Dnešná YouTube kvóta je takmer minutá")
    r = httpx.get(f"https://www.googleapis.com/youtube/v3/{path}", params={**params, "key": yt_key()}, timeout=25)
    _log("yt_" + path.split("/")[0], json.dumps(params)[:100], r.status_code == 200, units)
    if r.status_code != 200:
        try:
            raise RuntimeError("YouTube: " + r.json()["error"]["message"])
        except (KeyError, ValueError):
            raise RuntimeError("YouTube: " + r.text[:200])
    return r.json()


def _iso_dur(s):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    d, h, mi, se = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def job_yt_popular():
    if not yt_key():
        return
    for c in _countries()[:12]:
        try:
            d = _yt("videos", part="snippet,statistics", chart="mostPopular", regionCode=c, maxResults=50)
            for v in d.get("items", []):
                sn = v["snippet"]
                _upsert("yt_pop", c, _country_lang(c), sn["title"], sn.get("channelTitle", ""),
                        float(v.get("statistics", {}).get("viewCount", 0)), f"https://youtu.be/{v['id']}")
        except Exception as e:
            STATE["last_error"] = str(e)
            break


# ---------- konkurencia ----------
def resolve_competitor(pid, url):
    url = url.strip()
    m = re.search(r"youtube\.com/(@[\w.\-]+)", url) or re.search(r"^(@[\w.\-]+)$", url)
    params = None
    if m:
        params = {"forHandle": m.group(1)}
    elif re.search(r"youtube\.com/channel/(UC[\w-]+)", url):
        params = {"id": re.search(r"channel/(UC[\w-]+)", url).group(1)}
    elif re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url):
        vid = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url).group(1)
        d = _yt("videos", part="snippet", id=vid)
        if not d.get("items"):
            raise RuntimeError("video sa nenašlo")
        params = {"id": d["items"][0]["snippet"]["channelId"]}
    else:
        plat = "tiktok" if "tiktok" in url else "instagram" if "instagram" in url else "facebook" if "facebook" in url else "web"
        db.run("INSERT OR IGNORE INTO competitors(project_id, platform, mode, url, name, external_id) VALUES(?,?,?,?,?,?)",
               (pid, plat, "manual", url, url.rstrip("/").split("/")[-1], url))
        return "manual"
    d = _yt("channels", part="snippet,statistics,contentDetails", **params)
    if not d.get("items"):
        raise RuntimeError("kanál sa nenašiel")
    ch = d["items"][0]
    db.run("""INSERT OR IGNORE INTO competitors(project_id, platform, mode, url, handle, external_id, uploads_playlist, name, followers, lang)
              VALUES(?,?,?,?,?,?,?,?,?,?)""",
           (pid, "youtube", "auto", url, ch["snippet"].get("customUrl", ""), ch["id"],
            ch["contentDetails"]["relatedPlaylists"]["uploads"], ch["snippet"]["title"],
            int(ch["statistics"].get("subscriberCount", 0) or 0), (ch["snippet"].get("defaultLanguage") or "")[:2]))
    c = db.one("SELECT id FROM competitors WHERE project_id=? AND platform='youtube' AND external_id=?", (pid, ch["id"]))
    comp_backlog(c["id"])
    return ch["snippet"]["title"]


def comp_uploads(cid, n=10):
    c = db.one("SELECT * FROM competitors WHERE id=?", (cid,))
    if not c or c["platform"] != "youtube":
        return
    d = _yt("playlistItems", part="contentDetails", playlistId=c["uploads_playlist"], maxResults=n)
    ids = [x["contentDetails"]["videoId"] for x in d.get("items", [])]
    _update_videos(c, ids)
    db.run("UPDATE competitors SET last_checked=?, last_error='' WHERE id=?", (_now(), cid))


def _update_videos(c, ids):
    for i in range(0, len(ids), 50):
        d = _yt("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        for v in d.get("items", []):
            st, sn = v.get("statistics", {}), v["snippet"]
            dur = _iso_dur(v["contentDetails"].get("duration"))
            db.run("""INSERT INTO comp_posts(competitor_id, external_id, url, title, thumb, published_at, duration, is_short,
                      views, likes, comments, last_checked) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                      ON CONFLICT(competitor_id, external_id) DO UPDATE SET views=excluded.views, likes=excluded.likes,
                      comments=excluded.comments, last_checked=excluded.last_checked""",
                   (c["id"], v["id"], f"https://youtu.be/{v['id']}", sn["title"], (sn.get("thumbnails", {}).get("medium") or {}).get("url", ""),
                    sn["publishedAt"].replace("T", " ").replace("Z", ""), dur, int(dur <= 180), int(st.get("viewCount", 0) or 0),
                    int(st.get("likeCount", 0) or 0), int(st.get("commentCount", 0) or 0), _now()))
    _rescore(c["id"])


def _hours_since(ts):
    try:
        return max(1.0, (dt.datetime.utcnow() - dt.datetime.fromisoformat(ts)).total_seconds() / 3600)
    except Exception:
        return 168.0


def _rescore(cid):
    c = db.one("SELECT * FROM competitors WHERE id=?", (cid,))
    posts = db.q("SELECT * FROM comp_posts WHERE competitor_id=?", (cid,))
    for short in (1, 0):
        old = [p["views"] for p in posts if p["is_short"] == short and _hours_since(p["published_at"]) >= 168]
        base = statistics.median(old) if len(old) >= 3 else 0
        db.run(f"UPDATE competitors SET {'baseline_short' if short else 'baseline_long'}=? WHERE id=?", (base, cid))
        if not base:
            base = 0.1 * (c["followers"] or 0)
        for p in posts:
            if p["is_short"] != short:
                continue
            h = _hours_since(p["published_at"])
            expected = max(1.0, base * min(1.0, (h / 168) ** 0.6))
            ratio = p["views"] / expected if base else 0
            db.run("UPDATE comp_posts SET ratio=? WHERE id=?", (round(ratio, 2), p["id"]))
        # overené témy: staršie video oproti 30 susedným videám toho istého kanála (rovnaký formát)
        ps = sorted([p for p in posts if p["is_short"] == short], key=lambda x: x["published_at"] or "")
        vals = [p["views"] for p in ps]
        for k, p in enumerate(ps):
            nb = vals[max(0, k - 15):k] + vals[k + 1:k + 16]
            ra = 0.0
            if len(nb) >= 6 and _hours_since(p["published_at"]) >= 14 * 24:
                ra = round(p["views"] / max(1.0, statistics.median(nb)), 2)
            if ra != (p["ratio_all"] if "ratio_all" in p.keys() else 0):
                db.run("UPDATE comp_posts SET ratio_all=? WHERE id=?", (ra, p["id"]))


def comp_backlog(cid, max_n=200):
    """Celá história kanála (do 200 videí) – z nej sa počítajú overené témy. ~8 jednotiek kvóty na kanál."""
    c = db.one("SELECT * FROM competitors WHERE id=?", (cid,))
    if not c or c["platform"] != "youtube" or not c["uploads_playlist"]:
        return
    ids, tok = [], None
    while len(ids) < max_n:
        prm = {"part": "contentDetails", "playlistId": c["uploads_playlist"], "maxResults": 50}
        if tok:
            prm["pageToken"] = tok
        d = _yt("playlistItems", **prm)
        ids += [x["contentDetails"]["videoId"] for x in d.get("items", [])]
        tok = d.get("nextPageToken")
        if not tok:
            break
    _update_videos(c, ids[:max_n])  # obnoví aj čísla starších videí
    db.run("UPDATE competitors SET backlog_at=?, last_checked=?, last_error='' WHERE id=?", (_now(), _now(), cid))


def job_comp_backlog():
    """Raz za mesiac prejde celú históriu každého sledovaného kanála (najviac 25 kanálov za beh)."""
    old = (dt.datetime.now() - dt.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    done = 0
    for c in db.q("SELECT id, backlog_at FROM competitors WHERE platform='youtube' AND active=1 ORDER BY backlog_at"):
        if c["backlog_at"] and c["backlog_at"] > old:
            continue
        try:
            comp_backlog(c["id"])
            done += 1
        except Exception as e:
            db.run("UPDATE competitors SET last_error=? WHERE id=?", (str(e)[:200], c["id"]))
            if "kvóta" in str(e) or "Chýba" in str(e):
                break
        if done >= 25:
            break


def job_comp_uploads():
    for c in db.q("SELECT id FROM competitors WHERE platform='youtube' AND active=1"):
        try:
            comp_uploads(c["id"])
        except Exception as e:
            db.run("UPDATE competitors SET last_error=? WHERE id=?", (str(e)[:200], c["id"]))
            if "kvóta" in str(e) or "Chýba" in str(e):
                break


def job_comp_stats():
    for c in db.q("SELECT * FROM competitors WHERE platform='youtube' AND active=1"):
        ids = [r["external_id"] for r in db.q("SELECT external_id, published_at FROM comp_posts WHERE competitor_id=?", (c["id"],))
               if _hours_since(r["published_at"]) <= 14 * 24]
        if ids:
            try:
                _update_videos(c, ids)
            except Exception:
                break


# ---------- kľúčové slová a relevancia ----------
def keywords(pid):
    out = {"core": set(), "related": set(), "negative": set(), "entities": set()}
    for r in db.q("SELECT * FROM project_keywords WHERE project_id=?", (pid,)):
        for k in out:
            for w in json.loads(r[k] or "[]"):
                out[k].update(stems(w))
    return out


def relevance(kw, text_stems):
    t = set(text_stems)
    if t & kw["negative"]:
        return 0.0
    hits = 2 * len(t & kw["core"]) + len(t & kw["related"]) + 2 * len(t & kw["entities"])
    return min(1.0, hits / 3)


def clusters(hours=72):
    """Zlúči rovnaké témy (bez AI) a spočíta teplotu."""
    since = (dt.datetime.now() - dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    items = db.q("SELECT * FROM trend_items WHERE last_seen>=? ORDER BY volume DESC LIMIT 4000", (since,))
    maxvol = {}
    for it in items:
        k = (it["source"], it["country"] or it["lang"])
        maxvol[k] = max(maxvol.get(k, 0), it["volume"] or 0)
    cl = []
    for it in items:
        st = it["norm"].split()
        best = None
        for c in cl:
            if jaccard(st, c["stems"]) >= 0.5:
                best = c
                break
        if not best:
            best = {"label": it["term"], "stems": st, "items": [], "sources": set(), "countries": set(), "langs": set(),
                    "first": it["first_seen"], "V": 0.0, "ctx": ""}
            cl.append(best)
        best["items"].append(it)
        best["sources"].add(it["source"])
        if it["country"]:
            best["countries"].add(it["country"])
        if it["lang"]:
            best["langs"].add(it["lang"])
        best["first"] = min(best["first"], it["first_seen"])
        mv = maxvol.get((it["source"], it["country"] or it["lang"]), 0)
        if mv > 1 and it["volume"]:
            best["V"] = max(best["V"], math.log10(it["volume"] + 1) / math.log10(mv + 1))
        if it["context"] and len(best["ctx"]) < 200:
            best["ctx"] += " " + it["context"]
    for c in cl:
        age = (dt.datetime.now() - dt.datetime.fromisoformat(c["first"])).total_seconds() / 3600
        F = math.exp(-age / 36)
        X = (len(c["sources"]) - 1) / 3
        G = min(1, len(c["countries"]) / 5)
        S = 1.0 if age < 24 else 0.6 if age < 48 else 0.3
        c["base"] = 0.35 * c["V"] + 0.30 * S + 0.20 * X + 0.15 * G
        c["F"] = F
        c["stage"] = "rastie" if age < 24 and S >= 0.5 else "slabne" if F < 0.3 else "vrchol"
        c["key"] = hashlib.sha1(" ".join(c["stems"]).encode()).hexdigest()[:10]
        c["text_stems"] = set(c["stems"]) | set(stems(c["ctx"]))
    return cl


def project_trends(pid, limit=40):
    p = db.one("SELECT * FROM projects WHERE id=?", (pid,))
    langs = set(json.loads(p["languages"] or "[]"))
    countries = {c for l in langs for c in LANG_COUNTRIES.get(l, [])}
    kw = keywords(pid)
    hidden = {r["cluster_key"] for r in db.q("SELECT cluster_key FROM trend_status WHERE project_id=? AND status='ignored'", (pid,))}
    pinned = {r["cluster_key"] for r in db.q("SELECT cluster_key FROM trend_status WHERE project_id=? AND status='pinned'", (pid,))}
    wide = (p.get("radar_scope") or "narrow") == "wide"
    out = []
    for c in clusters():
        if c["key"] in hidden:
            continue
        if not (c["countries"] & countries or c["langs"] & langs):
            continue
        R = relevance(kw, c["text_stems"]) if any(kw.values()) else 0.0
        heat = 100 * (R ** 0.7) * c["F"] * c["base"]
        if wide and R < 0.34 and 100 * c["F"] * c["base"] >= 60:
            R = max(R, 0.1)
            heat = 100 * (R ** 0.7) * c["F"] * c["base"]
        if heat < 15 and c["key"] not in pinned:
            continue
        out.append({"key": c["key"], "label": c["label"], "heat": round(heat), "stage": c["stage"], "relevance": round(R, 2),
                    "countries": sorted(c["countries"]), "langs": sorted(c["langs"]), "sources": sorted(c["sources"]),
                    "ctx": c["ctx"].strip()[:220], "urls": [i["url"] for i in c["items"][:3] if i["url"]],
                    "pinned": c["key"] in pinned})
    out.sort(key=lambda x: (-x["pinned"], -x["heat"]))
    return out[:limit]


def outliers(pid, min_ratio=3.0, days=14):
    rows = db.q("""SELECT cp.*, c.name channel, c.followers FROM comp_posts cp JOIN competitors c ON c.id=cp.competitor_id
                   WHERE c.project_id=? AND cp.ratio>=? AND cp.status!='hidden' ORDER BY cp.ratio DESC LIMIT 60""", (pid, min_ratio))
    return [r for r in rows if _hours_since(r["published_at"]) <= days * 24]


# ---------- overené témy a vzory názvov (0 tokenov) ----------
TITLE_PATTERNS = [
    ("why", "Why …?", r"^why\b"),
    ("how", "How …", r"^how\b"),
    ("what_if", "What happens if / when …", r"\bwhat (happens|if|would|really)\b"),
    ("question", "Otázka (…?)", r"\?\s*$"),
    ("number", "Konkrétne číslo", r"\d"),
    ("money", "Peniaze / veľké sumy", r"[$€£]|\b(billion|million|trillion|cost|price|cheap|expensive|money)\b"),
    ("superlative", "Najväčší / jediný / najhorší", r"\b(biggest|largest|most|worst|best|fastest|deadliest|richest|smallest|longest|only|strongest|first|last)\b"),
    ("secret", "Skryté / skutočný dôvod", r"\b(secret|hidden|nobody|no one|real reason|truth|actually|really|insane|genius|strange|weird)\b"),
    ("problem", "Problém / zlyhanie / kríza", r"\b(problem|fail|failed|failure|mistake|collapse|crisis|disaster|dying|dead|broke|bankrupt|wrong|ruin)"),
    ("versus", "Porovnanie (vs)", r"\b(vs\.?|versus)\b"),
    ("the_x", "The … (príbeh)", r"^the\b"),
    ("explained", "Explained / in X minutes", r"\b(explained|in \d+ minutes?)\b"),
]


PATTERN_EN = {"why": "'Why ...'", "how": "'How ...'", "what_if": "'What happens if/when ...'", "question": "question title",
              "number": "concrete number", "money": "money/big sums", "superlative": "superlative (biggest/only/worst)",
              "secret": "hidden truth/real reason", "problem": "problem/failure/crisis", "versus": "X vs Y",
              "the_x": "'The ...' story", "explained": "'... Explained'"}


def proven(pid, fmt="long", limit=30, min_ratio=2.5):
    """Overené témy: staršie videá konkurencie s min. 2,5× viac pozretiami než je na ich kanáli bežné."""
    short = 1 if fmt == "short" else 0
    rows = db.q("""SELECT cp.*, c.name channel FROM comp_posts cp JOIN competitors c ON c.id=cp.competitor_id
                   WHERE c.project_id=? AND c.active=1 AND cp.is_short=? AND cp.ratio_all>=? AND cp.status NOT IN ('hidden','used')
                   AND (cp.is_short=1 OR cp.duration>=240) AND cp.views>=? ORDER BY cp.ratio_all DESC LIMIT 300""",
                (pid, short, min_ratio, 50000 if short else 20000))
    rows.sort(key=lambda r: -(min(r["ratio_all"], 30) * math.log10(r["views"] + 10)))
    out, seen = [], []
    for r in rows:
        st = stems(r["title"])
        if any(jaccard(st, x) > 0.5 for x in seen):
            continue
        seen.append(st)
        out.append(r)
        if len(out) >= limit:
            break
    return out


def title_patterns(pid, fmt="long"):
    """Ktoré typy názvov majú medzi hitmi konkurencie výrazne väčšie zastúpenie než bežne (bez AI)."""
    short = 1 if fmt == "short" else 0
    rows = db.q("""SELECT cp.title, cp.ratio_all FROM comp_posts cp JOIN competitors c ON c.id=cp.competitor_id
                   WHERE c.project_id=? AND c.active=1 AND cp.is_short=? AND cp.ratio_all>0 AND (cp.is_short=1 OR cp.duration>=240)""", (pid, short))
    hits = [r for r in rows if r["ratio_all"] >= 2.5]
    if len(rows) < 40 or len(hits) < 8:
        return {"patterns": [], "n": len(rows), "hits": len(hits), "len_hits": 0}
    out = []
    for key, label, rx in TITLE_PATTERNS:
        f = lambda t: bool(re.search(rx, t or "", re.I))
        a = sum(f(r["title"]) for r in hits) / len(hits)
        b = sum(f(r["title"]) for r in rows) / len(rows)
        if a >= 0.08 and b > 0:
            out.append({"key": key, "label": label, "share": round(a * 100), "lift": round(a / b, 2)})
    out.sort(key=lambda x: -x["lift"])
    return {"patterns": out, "n": len(rows), "hits": len(hits),
            "len_hits": round(statistics.median([len(r["title"]) for r in hits]))}


def proven_prompt(pid, fmt="long", n=6):
    """Krátky výťah pre Claude (~150 tokenov): overené témy + typy názvov, ktoré v nike fungujú."""
    import random
    top = proven(pid, fmt, 14)
    if not top:
        return ""
    pick = top[:3] + random.sample(top[3:], min(max(0, n - 3), len(top) - 3))
    lines = "; ".join(f'"{r["title"][:80]}" ({r["ratio_all"]:.0f}x)' for r in pick)
    tp = title_patterns(pid, fmt)
    pat = ", ".join([f'{PATTERN_EN[p["key"]]} {p["lift"]}x' for p in tp["patterns"] if p["lift"] >= 1.15][:4])
    return ("PROVEN IN THIS NICHE (competitor videos with 2.5x+ the views of their neighbouring uploads = topics viewers demonstrably want): "
            + lines + ". Prefer ideas that hit the SAME viewer desire with our own angle and our own story; never copy a title."
            + (f" Title styles that over-perform here: {pat}; typical hit title {tp['len_hits']} chars." if pat else ""))


def _own_stats():
    from . import stats
    stats.job()


def _housekeeping():
    from . import content, planner
    db.run("UPDATE ideas SET status='rejected' WHERE status='inbox' AND expires_at!='' AND expires_at<?", (dt.date.today().isoformat(),))
    db.run("DELETE FROM trend_items WHERE last_seen<?", ((dt.datetime.now() - dt.timedelta(days=10)).strftime("%Y-%m-%d"),))
    db.run("DELETE FROM fetch_log WHERE ts<?", ((dt.datetime.now() - dt.timedelta(days=14)).strftime("%Y-%m-%d"),))
    for p in _projects():  # kľúčové slová raz pre projekt (1 lacné volanie), potrebné pre správy a relevanciu
        tried = db.get_setting("kw_tried", {}) or {}
        if (not db.one("SELECT 1 x FROM project_keywords WHERE project_id=?", (p["id"],)) and (p["description"] or p["strategy_short"])
                and tried.get(str(p["id"]), "") < (dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y-%m-%d %H")):
            tried[str(p["id"])] = dt.datetime.now().strftime("%Y-%m-%d %H")
            db.set_setting("kw_tried", tried)
            try:
                content.radar_keywords(p["id"])
            except Exception as e:
                STATE["last_error"] = f"Kľúčové slová: {e}"[:300]
    from . import events
    for p in _projects():  # tematické dni projektu: raz (1 lacné volanie)
        if not db.get_setting(f"events_suggested_{p['id']}") and (p["description"] or p["strategy_short"]):
            db.set_setting(f"events_suggested_{p['id']}", "trying")
            try:
                events.suggest(p["id"])
            except Exception as e:
                STATE["last_error"] = f"Udalosti: {e}"[:300]
    try:
        planner.weekly_auto()
    except Exception as e:
        STATE["last_error"] = f"Plánovanie: {e}"[:300]


# ---------- plánovač Radaru (samostatné vlákno, nezasahuje do publikovania) ----------
JOBS = {"gtrends": (2, job_gtrends), "news": (3, job_news), "wiki": (24, job_wiki), "yt_popular": (24, job_yt_popular),
        "comp_uploads": (6, job_comp_uploads), "comp_backlog": (12, job_comp_backlog), "comp_stats": (3, job_comp_stats), "own_stats": (6, _own_stats),
        "weather": (24, lambda: __import__("app.weather", fromlist=["job"]).job()),
        "questions": (168, lambda: __import__("app.inspire", fromlist=["job_questions"]).job_questions())}


def run_job(name):
    hours, fn = JOBS[name]
    STATE.update(running=True, job=name)
    try:
        fn()
        db.run("INSERT OR REPLACE INTO intel_jobs(name, last_run, next_run, last_ok, last_error) VALUES(?,?,?,1,'')",
               (name, _now(), (dt.datetime.now() + dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")))
    except Exception as e:
        db.run("INSERT OR REPLACE INTO intel_jobs(name, last_run, next_run, last_ok, last_error) VALUES(?,?,?,0,?)",
               (name, _now(), (dt.datetime.now() + dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"), str(e)[:300]))
    finally:
        STATE.update(running=False, job="")


def _weekly_due():
    day = int(db.get_setting("radar_weekly_day", 0) or 0)  # 0 = pondelok
    now = dt.datetime.now()
    last = db.get_setting("radar_weekly_last", "")
    this_week = (now - dt.timedelta(days=(now.weekday() - day) % 7)).strftime("%Y-%m-%d")
    return now.hour >= 7 and last < this_week and now.weekday() >= day


def loop():
    time.sleep(30)
    last_hk = 0
    while True:
        try:
            if not db.get_setting("paused", False):
                on = db.get_setting("radar_enabled", True)
                if time.time() - last_hk > 3600:
                    last_hk = time.time()
                    _housekeeping()
                for name in JOBS:
                    if not on and name != "own_stats":
                        continue
                    j = db.one("SELECT next_run FROM intel_jobs WHERE name=?", (name,))
                    if not j or j["next_run"] <= _now():
                        run_job(name)
                        time.sleep(5)
                if on and db.get_setting("radar_weekly", True) and _weekly_due():
                    db.set_setting("radar_weekly_last", dt.date.today().strftime("%Y-%m-%d"))
                    from . import content
                    for p in _projects():
                        try:
                            content.radar_weekly(p["id"])
                        except Exception as e:
                            STATE["last_error"] = f"Týždenná dávka: {e}"[:300]
        except Exception as e:
            STATE["last_error"] = str(e)[:300]
        time.sleep(60)


def start():
    threading.Thread(target=loop, daemon=True).start()


def status():
    return {"yt_key": bool(yt_key()), "yt_units_today": yt_units_today(), "running": STATE["running"], "job": STATE["job"],
            "last_error": STATE["last_error"], "jobs": db.q("SELECT * FROM intel_jobs"),
            "tokens_week": db.one("SELECT COALESCE(SUM(input_tokens+output_tokens),0) n FROM ai_log WHERE purpose LIKE 'radar%' AND ts>=?",
                                  ((dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d"),))["n"]}


def signals(pid, n_trends=6, n_comp=4):
    """Kompaktný výťah pre AI (pár stoviek tokenov)."""
    out = []
    for i, t in enumerate(project_trends(pid, n_trends)):
        out.append({"id": f"T{i + 1}", "mk": t["langs"] or "all", "txt": f'"{t["label"]}" heat {t["heat"]} {t["stage"]}, {len(t["sources"])} sources'
                    + (f'; ctx: {t["ctx"][:90]}' if t["ctx"] else ""), "ref": {"trend": t["key"], "label": t["label"]}})
    try:
        from . import events
        out += events.signals(pid)
    except Exception:
        pass
    try:
        from . import inspire
        out += inspire.signals(pid)
    except Exception:
        pass
    for i, o in enumerate(proven(pid, "long", 3)):
        out.append({"id": f"P{i + 1}", "mk": "all", "txt": f'proven competitor long video "{o["title"][:90]}" {o["ratio_all"]}x its channel normal, {o["views"]} views',
                    "ref": {"comp_post": o["id"], "label": o["title"][:80]}})
    for i, o in enumerate(outliers(pid)[:n_comp]):
        out.append({"id": f"K{i + 1}", "mk": "all", "txt": f'competitor {"short" if o["is_short"] else "video"} "{o["title"][:90]}" {o["ratio"]}x channel normal, {o["views"]} views',
                    "ref": {"comp_post": o["id"], "label": o["title"][:80]}})
    return out
