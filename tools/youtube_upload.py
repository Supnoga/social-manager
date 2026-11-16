#!/usr/bin/env python3
"""Complete, working upload script used by Social Manager (standalone version of app/platforms/youtube.py).

What it does (same flow as the app):
  1. OAuth 2.0 sign-in of the channel owner (installed-app flow, local redirect),
     scopes: youtube.upload, youtube.force-ssl, youtube.readonly
  2. videos.insert as PRIVATE with resumable upload (title, description, tags, language,
     title/description localizations, containsSyntheticMedia flag)
  3. thumbnails.set (optional), captions.insert from an .srt (optional), playlistItems.insert (optional)
  4. videos.update -> status.publishAt = planned time, so YouTube publishes the video itself

Usage:
  pip install requests
  python youtube_upload.py --client client_secret.json --video video.mp4 --title "Title" \
      --description "Text" --publish-at 2026-11-20T17:00:00Z [--thumb t.jpg] [--srt subs.srt --srt-lang en] [--playlist PLxxxx]

Source: https://github.com/Supnoga/social-manager  ·  Privacy: PRIVACY.md  ·  Terms: TERMS.md
"""
import argparse
import http.server
import json
import os
import secrets
import threading
import urllib.parse
import webbrowser

import requests

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtube.readonly"]
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
TOKEN_FILE = "token.json"


def oauth(client_file):
    c = json.load(open(client_file))
    c = c.get("installed") or c.get("web")
    if os.path.exists(TOKEN_FILE):
        t = json.load(open(TOKEN_FILE))
        r = requests.post(TOKEN, data={"client_id": c["client_id"], "client_secret": c["client_secret"],
                                       "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
        if r.ok:
            return r.json()["access_token"]
    port, state, got = 8765, secrets.token_urlsafe(16), {}
    redirect = f"http://localhost:{port}/oauth"

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                got["code"] = q.get("code", [""])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Channel connected. You can close this window.")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("localhost", port), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    url = AUTH + "?" + urllib.parse.urlencode({"client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code",
                                               "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent",
                                               "state": state})
    print("Open and approve:", url)
    webbrowser.open(url)
    while "code" not in got:
        threading.Event().wait(0.5)
    srv.server_close()
    r = requests.post(TOKEN, data={"code": got["code"], "client_id": c["client_id"], "client_secret": c["client_secret"],
                                   "redirect_uri": redirect, "grant_type": "authorization_code"})
    r.raise_for_status()
    json.dump({"refresh_token": r.json()["refresh_token"]}, open(TOKEN_FILE, "w"))
    return r.json()["access_token"]


def upload(tok, a):
    h = {"Authorization": f"Bearer {tok}"}
    body = {"snippet": {"title": a.title[:100], "description": a.description[:5000], "tags": a.tags or [],
                        "categoryId": "27", "defaultLanguage": a.lang, "defaultAudioLanguage": a.lang},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
    size = os.path.getsize(a.video)
    r = requests.post(f"{UPLOAD}/videos?uploadType=resumable&part=snippet,status", json=body,
                      headers={**h, "X-Upload-Content-Type": "video/*", "X-Upload-Content-Length": str(size)})
    r.raise_for_status()
    with open(a.video, "rb") as f:
        r = requests.put(r.headers["Location"], data=f, headers={**h, "Content-Type": "video/*", "Content-Length": str(size)})
    r.raise_for_status()
    vid = r.json()["id"]
    print("Uploaded as private:", vid)
    if a.thumb:
        with open(a.thumb, "rb") as f:
            requests.post(f"{UPLOAD}/thumbnails/set?videoId={vid}", data=f, headers={**h, "Content-Type": "image/jpeg"}).raise_for_status()
    if a.srt:
        meta = {"snippet": {"videoId": vid, "language": a.srt_lang, "name": ""}}
        files = {"m": (None, json.dumps(meta), "application/json"), "f": ("c.srt", open(a.srt, "rb"), "application/octet-stream")}
        requests.post(f"{UPLOAD}/captions?part=snippet&uploadType=multipart", files=files, headers=h).raise_for_status()
    if a.playlist:
        requests.post(f"{API}/playlistItems?part=snippet", headers=h,
                      json={"snippet": {"playlistId": a.playlist, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).raise_for_status()
    if a.publish_at:
        requests.put(f"{API}/videos?part=status", headers=h,
                     json={"id": vid, "status": {"privacyStatus": "private", "publishAt": a.publish_at,
                                                 "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}).raise_for_status()
        print("Scheduled, YouTube publishes it at", a.publish_at)
    print("https://youtu.be/" + vid)
    return vid


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--client", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--tags", nargs="*")
    p.add_argument("--lang", default="en")
    p.add_argument("--publish-at")
    p.add_argument("--thumb")
    p.add_argument("--srt")
    p.add_argument("--srt-lang", default="en")
    p.add_argument("--playlist")
    a = p.parse_args()
    upload(oauth(a.client), a)
