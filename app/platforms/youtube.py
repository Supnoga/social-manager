"""YouTube Data API v3 - prihlásenie cez Google (OAuth 'Desktop app') a nahrávanie videí."""
import json
import os
import time
import urllib.parse

from .. import db
from .common import BASE_URL, PlatformError, check, client, save_tokens, text_for, tokens

SCOPES = ("https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly "
          "https://www.googleapis.com/auth/youtube.force-ssl")  # force-ssl = čítanie a odpovedanie na komentáre
REDIRECT = BASE_URL + "/"


def creds():
    c = db.get_setting("yt_client") or {}
    c = c.get("installed") or c.get("web") or c
    if not c.get("client_id"):
        raise PlatformError("Najprv nahraj YouTube 'client_secret' JSON v časti Účty.")
    return c["client_id"], c["client_secret"]


def auth_url(state):
    cid, _ = creds()
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent select_account", "state": state, "include_granted_scopes": "true"})


def callback(code, project_id=None, lang=""):
    cid, sec = creds()
    with client() as c:
        r = check(c.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": cid, "client_secret": sec, "redirect_uri": REDIRECT,
            "grant_type": "authorization_code"}), "Google token")
        t = r.json()
        t["expires_at"] = time.time() + t.get("expires_in", 3600) - 60
        ch = check(c.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true"},
                         headers={"Authorization": f"Bearer {t['access_token']}"}), "YouTube kanál").json()
    created = []
    for item in ch.get("items", []):
        ex = db.one("SELECT id FROM accounts WHERE platform='youtube' AND external_id=?", (item["id"],))
        if ex:
            old = tokens(db.one("SELECT * FROM accounts WHERE id=?", (ex["id"],)))
            if not t.get("refresh_token"):
                t["refresh_token"] = old.get("refresh_token")
            save_tokens(ex["id"], t)
            created.append(ex["id"])
        else:
            created.append(db.run("INSERT INTO accounts(platform,name,external_id,project_id,lang,tokens) VALUES(?,?,?,?,?,?)",
                                  ("youtube", item["snippet"]["title"], item["id"], project_id, lang, json.dumps(t))))
    if not created:
        raise PlatformError("Tento Google účet nemá YouTube kanál. Najprv si ho vytvor na youtube.com.")
    return created


def access_token(account):
    t = tokens(account)
    if t.get("expires_at", 0) > time.time():
        return t["access_token"]
    if not t.get("refresh_token"):
        raise PlatformError("YouTube prihlásenie vypršalo, pripoj účet znova.")
    cid, sec = creds()
    with client() as c:
        r = c.post("https://oauth2.googleapis.com/token", data={
            "client_id": cid, "client_secret": sec, "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
        if r.status_code >= 400:
            raise PlatformError("YouTube prihlásenie vypršalo (ak je Google appka v režime 'Testing', prepni ju na "
                                "'In production'). Pripoj účet znova.")
        n = r.json()
    t["access_token"] = n["access_token"]
    t["expires_at"] = time.time() + n.get("expires_in", 3600) - 60
    save_tokens(account["id"], t)
    return t["access_token"]


def upload(account, video, privacy="public", publish_at=None):
    tok = access_token(account)
    title, desc = text_for(video, "youtube")
    tags = [x.strip("#") for x in (video.get("hashtags") or "").split() if x.startswith("#")][:15]
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at
    body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "22"}, "status": status}
    if video.get("lang"):
        body["snippet"]["defaultLanguage"] = video["lang"]
        body["snippet"]["defaultAudioLanguage"] = video["lang"]
    size = os.path.getsize(video["file_path"])
    with client(timeout=3600) as c:
        r = check(c.post("https://www.googleapis.com/upload/youtube/v3/videos",
                         params={"uploadType": "resumable", "part": "snippet,status"},
                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                  "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/*"},
                         json=body), "YouTube štart nahrávania")
        loc = r.headers["Location"]
        from .common import file_chunks
        r = check(c.put(loc, headers={"Authorization": f"Bearer {tok}", "Content-Length": str(size),
                                      "Content-Type": "video/*"},
                        content=file_chunks(video["file_path"])), "YouTube nahrávanie")
        vid = r.json()["id"]
    return vid, f"https://youtu.be/{vid}"
