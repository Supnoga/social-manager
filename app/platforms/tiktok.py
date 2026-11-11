"""TikTok - Login Kit for Desktop (PKCE) + Content Posting API.

Režimy:
- inbox  (scope video.upload): video príde ako koncept do TikTok appky, ty ho jedným klikom zverejníš (funguje hneď).
- direct (scope video.publish): zverejní priamo. Bez auditu TikToku je však video iba súkromné (SELF_ONLY).
"""
import hashlib
import json
import os
import secrets
import time
import urllib.parse

from .. import db
from .common import BASE_URL, PlatformError, check, client, save_tokens, text_for, tokens

REDIRECT = BASE_URL + "/oauth/tiktok/callback/"
API = "https://open.tiktokapis.com/v2"
_pkce = {}


def creds():
    k, s = db.get_setting("tt_client_key", ""), db.get_setting("tt_client_secret", "")
    if not k or not s:
        raise PlatformError("Najprv vlož TikTok Client key a Client secret v časti Účty.")
    return k, s


def mode():
    return db.get_setting("tt_mode", "inbox")


def auth_url(state):
    key, _ = creds()
    verifier = secrets.token_urlsafe(64)[:96].replace("_", "-")
    _pkce[state] = verifier
    challenge = hashlib.sha256(verifier.encode()).hexdigest()  # TikTok desktop chce HEX
    scope = "user.info.basic,video.upload" + (",video.publish" if mode() == "direct" else "")
    return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": key, "scope": scope, "response_type": "code", "redirect_uri": REDIRECT,
        "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})


def callback(code, state, project_id=None, lang=""):
    key, sec = creds()
    verifier = _pkce.pop(state, "")
    with client() as c:
        r = check(c.post(f"{API}/oauth/token/", data={
            "client_key": key, "client_secret": sec, "code": code, "grant_type": "authorization_code",
            "redirect_uri": REDIRECT, "code_verifier": verifier},
            headers={"Content-Type": "application/x-www-form-urlencoded"}), "TikTok token")
        t = r.json()
        if "access_token" not in t:
            raise PlatformError("TikTok prihlásenie zlyhalo: " + json.dumps(t)[:300])
        t["expires_at"] = time.time() + t.get("expires_in", 86400) - 120
        name = t.get("open_id", "TikTok")
        try:
            u = c.get(f"{API}/user/info/", params={"fields": "open_id,display_name"},
                      headers={"Authorization": f"Bearer {t['access_token']}"}).json()
            name = u.get("data", {}).get("user", {}).get("display_name") or name
        except Exception:
            pass
    ex = db.one("SELECT id FROM accounts WHERE platform='tiktok' AND external_id=?", (t["open_id"],))
    if ex:
        save_tokens(ex["id"], t)
        return [ex["id"]]
    return [db.run("INSERT INTO accounts(platform,name,external_id,project_id,lang,tokens) VALUES(?,?,?,?,?,?)",
                   ("tiktok", name, t["open_id"], project_id, lang, json.dumps(t)))]


def access_token(account):
    t = tokens(account)
    if t.get("expires_at", 0) > time.time():
        return t["access_token"]
    key, sec = creds()
    with client() as c:
        r = c.post(f"{API}/oauth/token/", data={"client_key": key, "client_secret": sec,
                                                 "grant_type": "refresh_token", "refresh_token": t.get("refresh_token", "")},
                   headers={"Content-Type": "application/x-www-form-urlencoded"})
    n = r.json() if r.status_code < 400 else {}
    if "access_token" not in n:
        raise PlatformError("TikTok prihlásenie vypršalo, pripoj účet znova.")
    n["expires_at"] = time.time() + n.get("expires_in", 86400) - 120
    t.update(n)
    save_tokens(account["id"], t)
    return t["access_token"]


def _chunks(size):
    mb = 1024 * 1024
    if size <= 64 * mb:
        return size, 1
    chunk = 32 * mb
    return chunk, size // chunk  # posledný kúsok obsahuje aj zvyšok


def upload(account, video, privacy="public"):
    tok = access_token(account)
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    size = os.path.getsize(video["file_path"])
    chunk, count = _chunks(size)
    source = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": count}
    _, text = text_for(video, "tiktok", account)
    with client(timeout=3600) as c:
        if mode() == "direct":
            info = check(c.post(f"{API}/post/publish/creator_info/query/", headers=h, json={}), "TikTok info").json()
            opts = info.get("data", {}).get("privacy_level_options", ["SELF_ONLY"])
            want = "PUBLIC_TO_EVERYONE" if privacy == "public" else "SELF_ONLY"
            level = want if want in opts else opts[0]
            body = {"post_info": {"title": text, "privacy_level": level, "disable_duet": False,
                                  "disable_comment": False, "disable_stitch": False}, "source_info": source}
            r = check(c.post(f"{API}/post/publish/video/init/", headers=h, json=body), "TikTok štart")
        else:
            r = check(c.post(f"{API}/post/publish/inbox/video/init/", headers=h, json={"source_info": source}),
                      "TikTok štart")
        d = r.json()
        if d.get("error", {}).get("code", "ok") != "ok":
            raise PlatformError("TikTok: " + json.dumps(d["error"])[:300])
        pid, url = d["data"]["publish_id"], d["data"]["upload_url"]
        with open(video["file_path"], "rb") as f:
            for i in range(count):
                start = i * chunk
                end = size if i == count - 1 else start + chunk
                f.seek(start)
                data = f.read(end - start)
                check(c.put(url, content=data, headers={"Content-Type": "video/mp4", "Content-Length": str(len(data)),
                                                        "Content-Range": f"bytes {start}-{end - 1}/{size}"}),
                      "TikTok nahrávanie")
        status = ""
        for _ in range(60):
            s = c.post(f"{API}/post/publish/status/fetch/", headers=h, json={"publish_id": pid}).json()
            status = s.get("data", {}).get("status", "")
            if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
                break
            if status == "FAILED":
                raise PlatformError("TikTok odmietol video: " + str(s.get("data", {}).get("fail_reason")))
            time.sleep(10)
    note = "koncept v TikTok appke - otvor notifikácie a zverejni" if status == "SEND_TO_USER_INBOX" or mode() == "inbox" else ""
    return pid, note
