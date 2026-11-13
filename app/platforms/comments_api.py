"""Čítanie komentárov a odpovedanie cez oficiálne API sietí (zadarmo).

Každá sieť vráti zoznam {id, post, post_url, post_title, author, text, created, likes, answered}.
- YouTube: commentThreads (1 jednotka z 10 000 denne), odpoveď 50 jednotiek. Treba právo youtube.force-ssl.
- Facebook / Instagram: Graph API, token potrebuje pages_read_engagement, pages_read_user_content,
  pages_manage_engagement a instagram_manage_comments.
- TikTok: len cez TikTok API for Business (práva comment.list a comment.list.manage).
- LinkedIn: len firemné stránky (Community Management API). Osobný profil čítanie komentárov nedovolí.
"""
import re
import urllib.parse

from .common import PlatformError, check, client, tokens
from . import linkedin, meta, tiktok_business, youtube


def _yt_item(acc, it, by_id):
    s = it["snippet"]["topLevelComment"]["snippet"]
    if (s.get("authorChannelId") or {}).get("value") == acc["external_id"]:
        return None
    vid = it["snippet"].get("videoId") or s.get("videoId") or ""
    p = by_id.get(vid, {})
    return {"id": it["id"], "post": vid, "post_url": p.get("url", "") or (f"https://www.youtube.com/watch?v={vid}" if vid else ""),
            "post_title": p.get("title") or "", "author": s.get("authorDisplayName", ""),
            "text": s.get("textDisplay") or s.get("textOriginal", ""), "created": s.get("publishedAt", ""),
            "likes": s.get("likeCount", 0), "answered": it["snippet"].get("totalReplyCount", 0) > 0}


# ---------- YouTube bez kvóty (keď je denný limit Googlu minutý) ----------
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def _yti(c, body):
    """Verejné rozhranie stránky youtube.com (to isté, čo používa prehliadač), nečerpá kvótu Google API."""
    r = c.post("https://www.youtube.com/youtubei/v1/next", params={"prettyPrint": "false"},
               headers={"User-Agent": _UA, "Content-Type": "application/json"},
               json={"context": {"client": {"clientName": "WEB", "clientVersion": "2.20241101.00.00", "hl": "en", "gl": "US"}}, **body})
    r.raise_for_status()
    return r.json()


def _walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                yield v
            yield from _walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v, key)


def _ago_iso(t):
    """„3 hours ago“ → približný čas (presný čas YouTube stránka nedáva)."""
    from datetime import datetime, timedelta, timezone
    m = re.match(r"(\d+)\s+(second|minute|hour|day|week|month|year)", t or "")
    n, u = (int(m.group(1)), m.group(2)) if m else (0, "second")
    sec = {"second": 1, "minute": 60, "hour": 3600, "day": 86400, "week": 604800, "month": 2592000, "year": 31536000}[u]
    return (datetime.now(timezone.utc) - timedelta(seconds=n * sec)).strftime("%Y-%m-%dT%H:%M:%SZ")


def yt_page_comments(acc, video_id, title="", url=""):
    """Komentáre jedného videa z verejnej stránky (prvá strana, ~20 najnovších/najlepších). Bez kvóty."""
    out = []
    with client(timeout=30) as c:
        d = _yti(c, {"videoId": video_id})
        tok = None
        for sec in _walk(d, "itemSectionRenderer"):
            if sec.get("sectionIdentifier") == "comment-item-section":
                tok = next(_walk(sec, "token"), None)
                break
        if not tok:
            return out  # komentáre vypnuté alebo žiadne
        d = _yti(c, {"continuation": tok})
        mine = set()  # komentáre, na ktoré už odpovedal sám kanál
        for th in _walk(d, "commentThreadRenderer"):
            rtok = next(_walk(th.get("replies") or {}, "token"), None)
            cid = next(_walk(th.get("commentViewModel") or th, "commentId"), None)
            if not rtok or not cid:
                continue
            try:
                rd = _yti(c, {"continuation": rtok})
                if any((x.get("author") or {}).get("channelId") == acc["external_id"] for x in _walk(rd, "commentEntityPayload")):
                    mine.add(cid)
            except Exception:
                pass
    for p in _walk(d, "commentEntityPayload"):
        pr, au, tb = p.get("properties") or {}, p.get("author") or {}, p.get("toolbar") or {}
        if not pr.get("commentId") or au.get("channelId") == acc["external_id"] or "." in pr["commentId"]:
            continue  # vlastné komentáre kanála a odpovede vynechá
        likes = re.sub(r"\D", "", tb.get("likeCountNotliked") or "") or "0"
        out.append({"id": pr["commentId"], "post": video_id, "post_url": url or f"https://www.youtube.com/watch?v={video_id}",
                    "post_title": title or "", "author": au.get("displayName", ""),
                    "text": (pr.get("content") or {}).get("content", ""), "created": _ago_iso(pr.get("publishedTime")),
                    "likes": int(likes), "answered": pr["commentId"] in mine})
    return out


def _yt_pages(acc, posts):
    import time
    out = []
    for p in posts[:40]:
        try:
            out += yt_page_comments(acc, p["external_id"], p.get("title") or "", p.get("url") or "")
        except Exception as e:
            print("YouTube komentáre zo stránky:", p["external_id"], e)
        time.sleep(1)
    return out


def _yt(acc, posts):
    """Všetky nové komentáre kanála jedným volaním (1 jednotka kvóty na kanál, nie 1 na každé video).
    Číta sa z malej pevnej dennej rezervy pre komentáre (insights.READ_RESERVE), nahrávanie má svoj limit zvlášť."""
    from ..insights import _read_ok, block_today
    if not _read_ok(acc, kind="comments"):
        return _yt_pages(acc, posts)  # limit minutý: komentáre z verejnej stránky videí
    tok = youtube.access_token(acc)
    by_id = {p["external_id"]: p for p in posts}
    out = []
    with client() as c:
        r = c.get("https://www.googleapis.com/youtube/v3/commentThreads", headers={"Authorization": f"Bearer {tok}"},
                  params={"part": "snippet", "allThreadsRelatedToChannelId": acc["external_id"], "maxResults": 100,
                          "order": "time", "textFormat": "plainText"})
        if r.status_code == 403 and "insufficient" in r.text.lower():
            raise PlatformError("YouTube: chýba povolenie na komentáre. Pripoj kanál znova (Účty → YouTube).")
        if r.status_code == 403 and "quota" in r.text.lower():
            block_today(acc)
            return _yt_pages(acc, posts)
        if r.status_code == 403 and "commentsDisabled" in r.text:
            return out
        check(r, "YouTube komentáre")
        for it in r.json().get("items", []):
            x = _yt_item(acc, it, by_id)
            if x:
                out.append(x)
    return out


def _fb(acc, posts):
    t = tokens(acc)
    out = []
    with client() as c:
        for p in posts:
            r = c.get(meta.G(f"{p['external_id']}/comments"), params={
                "access_token": t["page_token"], "filter": "toplevel", "order": "reverse_chronological", "limit": 50,
                "fields": "id,from{id,name},message,created_time,like_count,comment_count"})
            if r.status_code in (400, 403) and "permission" in r.text.lower():
                raise PlatformError("Facebook: token nemá právo na komentáre (pages_read_engagement, "
                                    "pages_read_user_content, pages_manage_engagement). Vytvor nový token a vlož ho v Účtoch.")
            check(r, "Facebook komentáre")
            for it in r.json().get("data", []):
                if (it.get("from") or {}).get("id") == t.get("page_id"):
                    continue
                out.append({"id": it["id"], "post": p["external_id"], "post_url": p.get("url", ""),
                            "post_title": p.get("title") or "", "author": (it.get("from") or {}).get("name", ""),
                            "text": it.get("message", ""), "created": it.get("created_time", ""),
                            "likes": it.get("like_count", 0), "answered": False})
    return out


def _ig(acc, posts):
    t = tokens(acc)
    me = acc["name"].lstrip("@")
    out = []
    with client() as c:
        for p in posts:
            r = c.get(meta.G(f"{p['external_id']}/comments"), params={
                "access_token": t["page_token"], "limit": 50,
                "fields": "id,text,username,timestamp,like_count,replies{username}"})
            if r.status_code in (400, 403) and "permission" in r.text.lower():
                raise PlatformError("Instagram: token nemá právo instagram_manage_comments. Vytvor nový token a vlož ho v Účtoch.")
            check(r, "Instagram komentáre")
            for it in r.json().get("data", []):
                if it.get("username") == me:
                    continue
                replied = any(x.get("username") == me for x in (it.get("replies") or {}).get("data", []))
                out.append({"id": it["id"], "post": p["external_id"], "post_url": p.get("url", ""),
                            "post_title": p.get("title") or "", "author": "@" + it.get("username", ""),
                            "text": it.get("text", ""), "created": it.get("timestamp", ""),
                            "likes": it.get("like_count", 0), "answered": replied})
    return out


def _tt_video(p):
    m = re.search(r"/video/(\d+)", p.get("url") or "")
    return m.group(1) if m else ""


def _tt(acc, posts):
    if tokens(acc).get("api") != "business":
        raise PlatformError("TikTok komentáre idú len cez TikTok API for Business (tento účet je pripojený inak).")
    tok = tiktok_business.access_token(acc)
    out = []
    with client() as c:
        for p in posts:
            vid = _tt_video(p)
            if not vid:
                continue
            r = c.get(f"{tiktok_business.API}/business/comment/list/", headers={"Access-Token": tok}, params={
                "business_id": acc["external_id"], "video_id": vid, "max_count": 30,
                "sort_field": "create_time", "sort_order": "desc"})
            check(r, "TikTok komentáre")
            d = r.json()
            if d.get("code") not in (0, "0"):
                msg = str(d.get("message", ""))
                if "scope" in msg.lower() or "permission" in msg.lower():
                    raise PlatformError("TikTok: appka nemá právo na komentáre (comment.list, comment.list.manage). "
                                        "Pridaj ich v TikTok Business portáli a pripoj účet znova.")
                raise PlatformError(f"TikTok komentáre: {msg}")
            for it in (d.get("data") or {}).get("comments", []):
                if it.get("owner") or it.get("parent_comment_id") not in (None, "", "0", it.get("comment_id")):
                    continue
                out.append({"id": str(it["comment_id"]), "post": vid, "post_url": p.get("url", ""),
                            "post_title": p.get("title") or "",
                            "author": "@" + (it.get("username") or it.get("display_name") or ""),
                            "text": it.get("text", ""), "created": str(it.get("create_time", "")),
                            "likes": it.get("likes", 0), "answered": bool(it.get("replies"))})
    return out


def _li(acc, posts):
    owner = acc["external_id"]
    if not owner.startswith("urn:li:organization"):
        return []  # osobný profil: LinkedIn čítanie komentárov nedovolí
    tok = linkedin.access_token(acc)
    out = []
    with client() as c:
        for p in posts:
            urn = urllib.parse.quote(p["external_id"], safe="")
            r = c.get(f"{linkedin.REST}/socialActions/{urn}/comments", headers=linkedin.headers(tok), params={"count": 50})
            check(r, "LinkedIn komentáre")
            for it in r.json().get("elements", []):
                if it.get("actor") == owner or it.get("parentComment"):
                    continue
                cid = it.get("commentUrn") or it.get("$URN") or str(it.get("id", ""))
                out.append({"id": cid, "post": p["external_id"], "post_url": p.get("url", ""),
                            "post_title": p.get("title") or "", "author": "",
                            "text": (it.get("message") or {}).get("text", ""),
                            "created": str((it.get("created") or {}).get("time", "")), "likes": 0, "answered": False})
    return out


LISTERS = {"youtube": _yt, "facebook": _fb, "instagram": _ig, "tiktok": _tt, "linkedin": _li}


def list_comments(acc, posts):
    fn = LISTERS.get(acc["platform"])
    return fn(acc, posts) if fn else []


def reply(acc, com, text):
    p = acc["platform"]
    with client() as c:
        if p == "youtube":
            tok = youtube.access_token(acc)
            check(c.post("https://www.googleapis.com/youtube/v3/comments", params={"part": "snippet"},
                         headers={"Authorization": f"Bearer {tok}"},
                         json={"snippet": {"parentId": com["external_id"], "textOriginal": text}}), "YouTube odpoveď")
        elif p == "facebook":
            check(c.post(meta.G(f"{com['external_id']}/comments"),
                         data={"access_token": tokens(acc)["page_token"], "message": text}), "Facebook odpoveď")
        elif p == "instagram":
            check(c.post(meta.G(f"{com['external_id']}/replies"),
                         data={"access_token": tokens(acc)["page_token"], "message": text}), "Instagram odpoveď")
        elif p == "tiktok":
            tok = tiktok_business.access_token(acc)
            tiktok_business._env(c.post(f"{tiktok_business.API}/business/comment/reply/create/",
                                        headers={"Access-Token": tok, "Content-Type": "application/json"},
                                        json={"business_id": acc["external_id"], "video_id": com["post_ext"],
                                              "comment_id": com["external_id"], "text": text}), "TikTok odpoveď")
        elif p == "linkedin":
            post = com["post_ext"]
            check(c.post(f"{linkedin.REST}/socialActions/{urllib.parse.quote(post, safe='')}/comments",
                         headers=linkedin.headers(linkedin.access_token(acc)),
                         json={"actor": acc["external_id"], "object": post, "parentComment": com["external_id"],
                               "message": {"text": text}}), "LinkedIn odpoveď")
        else:
            raise PlatformError("Táto sieť odpovede nepodporuje.")
