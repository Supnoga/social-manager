"""Facebook stránky + Instagram (cez Meta Graph API). Jeden token -> všetky stránky aj prepojené IG účty."""
import json
import os
import time

from .. import db
from .common import PlatformError, check, client, file_chunks, text_for, tokens


def ver():
    return db.get_setting("meta_api_version", "v25.0")


def G(path):
    return f"https://graph.facebook.com/{ver()}/{path.lstrip('/')}"


def connect(user_token, project_id=None, lang=""):
    """Z tokenu (System User alebo používateľský) načíta stránky a ich Instagram účty."""
    user_token = user_token.strip()
    with client() as c:
        r = check(c.get(G("me/accounts"), params={
            "access_token": user_token, "limit": 100,
            "fields": "id,name,access_token,instagram_business_account{id,username}"}), "Meta stránky")
        pages = r.json().get("data", [])
    if not pages:
        raise PlatformError("Token nevidí žiadnu Facebook stránku. Skontroluj, či má System User priradené stránky "
                            "a práva pages_show_list, pages_manage_posts.")
    made = []
    for p in pages:
        t = {"page_token": p["access_token"], "page_id": p["id"], "user_token": user_token}
        made.append(_upsert("facebook", p["name"], p["id"], t, project_id, lang))
        ig = p.get("instagram_business_account")
        if ig:
            made.append(_upsert("instagram", "@" + ig.get("username", ig["id"]), ig["id"],
                                 dict(t, ig_id=ig["id"]), project_id, lang))
    return made


def _upsert(platform, name, ext, t, project_id, lang):
    ex = db.one("SELECT id FROM accounts WHERE platform=? AND external_id=?", (platform, ext))
    if ex:
        db.run("UPDATE accounts SET tokens=?, name=? WHERE id=?", (json.dumps(t), name, ex["id"]))
        return ex["id"]
    return db.run("INSERT INTO accounts(platform,name,external_id,project_id,lang,tokens) VALUES(?,?,?,?,?,?)",
                  (platform, name, ext, project_id, lang, json.dumps(t)))


def upload_facebook(account, video, privacy="public"):
    t = tokens(account)
    tok, page = t["page_token"], t["page_id"]
    _, text = text_for(video, "facebook")
    size = os.path.getsize(video["file_path"])
    dur = video.get("duration") or 0
    with client(timeout=3600) as c:
        if dur and dur > 90:
            # dlhšie video -> klasické video na stránke
            with open(video["file_path"], "rb") as f:
                r = check(c.post(f"https://graph-video.facebook.com/{ver()}/{page}/videos",
                                 data={"access_token": tok, "description": text, "title": (video.get("title") or "")[:250]},
                                 files={"source": (os.path.basename(video["file_path"]), f, "video/mp4")}), "FB video")
            vid = r.json()["id"]
            return vid, f"https://www.facebook.com/{vid}"
        # krátke video -> Reel (3 fázy)
        r = check(c.post(G(f"{page}/video_reels"), json={"upload_phase": "start", "access_token": tok}), "FB reel štart")
        vid = r.json()["video_id"]
        check(c.post(f"https://rupload.facebook.com/video-upload/{ver()}/{vid}",
                     headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)},
                     content=file_chunks(video["file_path"])), "FB reel nahrávanie")
        check(c.post(G(f"{page}/video_reels"), params={
            "access_token": tok, "video_id": vid, "upload_phase": "finish", "video_state": "PUBLISHED",
            "description": text}), "FB reel publikovanie")
    return vid, f"https://www.facebook.com/reel/{vid}"


def upload_instagram(account, video, privacy="public"):
    t = tokens(account)
    tok, ig = t["page_token"], t["ig_id"]
    _, text = text_for(video, "instagram")
    size = os.path.getsize(video["file_path"])
    auth = {"Authorization": f"OAuth {tok}"}
    with client(timeout=3600) as c:
        r = check(c.post(G(f"{ig}/media"), headers=auth, json={
            "media_type": "REELS", "upload_type": "resumable", "caption": text, "share_to_feed": True}), "IG kontajner")
        cont = r.json()
        cid = cont["id"]
        uri = cont.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{ver()}/{cid}"
        check(c.post(uri, headers=dict(auth, offset="0", file_size=str(size)),
                     content=file_chunks(video["file_path"])), "IG nahrávanie")
        # čakanie na spracovanie
        for _ in range(120):
            s = check(c.get(G(cid), headers=auth, params={"fields": "status_code,status"}), "IG stav").json()
            code = s.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                raise PlatformError("Instagram video odmietol: " + str(s.get("status")))
            time.sleep(10)
        else:
            raise PlatformError("Instagram spracováva video príliš dlho, skúsim neskôr.")
        r = check(c.post(G(f"{ig}/media_publish"), headers=auth, data={"creation_id": cid}), "IG publikovanie")
        mid = r.json()["id"]
        link = ""
        try:
            link = c.get(G(mid), headers=auth, params={"fields": "permalink"}).json().get("permalink", "")
        except Exception:
            pass
    return mid, link
