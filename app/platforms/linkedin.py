"""LinkedIn - videá na osobný profil (hneď) a na firemné stránky (po schválení 'Community Management API')."""
import json
import os
import re
import secrets
import time
import urllib.parse
from datetime import date

from .. import db
from .common import BASE_URL, PlatformError, check, client, save_tokens, text_for, tokens

REDIRECT = BASE_URL + "/oauth/linkedin/callback"
REST = "https://api.linkedin.com/rest"


def creds(org=False):
    pre = "li_org_" if org else "li_"
    i, s = db.get_setting(pre + "client_id", ""), db.get_setting(pre + "client_secret", "")
    if not i or not s:
        raise PlatformError("Najprv vlož LinkedIn Client ID a Client Secret " +
                            ("druhej appky (firemné stránky) " if org else "") + "v časti Účty.")
    return i, s


def li_version():
    v = db.get_setting("li_version", "")
    if v:
        return v
    d = date.today()
    m = d.month - 3
    y = d.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y}{m:02d}"


def headers(tok):
    return {"Authorization": f"Bearer {tok}", "LinkedIn-Version": li_version(),
            "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"}


def auth_url(state, org=False):
    cid, _ = creds(org)
    scope = ("w_organization_social r_organization_social rw_organization_admin" if org
             else "openid profile w_member_social")
    return "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": REDIRECT, "state": state, "scope": scope})


def callback(code, project_id=None, lang="", org=False):
    cid, sec = creds(org)
    with client() as c:
        t = check(c.post("https://www.linkedin.com/oauth/v2/accessToken", data={
            "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
            "client_id": cid, "client_secret": sec}), "LinkedIn prihlásenie").json()
        t["expires_at"] = time.time() + t.get("expires_in", 5184000) - 3600
        made = []
        if not org:
            me = check(c.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {t['access_token']}"}),
                       "LinkedIn profil").json()
            made.append(_upsert(f"urn:li:person:{me['sub']}", "👤 " + me.get("name", "Profil"), t, project_id, lang))
        else:
            try:
                acl = c.get(f"{REST}/organizationAcls", headers=headers(t["access_token"]),
                            params={"q": "roleAssignee", "role": "ADMINISTRATOR", "state": "APPROVED"}).json()
                for el in acl.get("elements", []):
                    org = el.get("organization", "")
                    oid = org.split(":")[-1]
                    name = "🏢 " + oid
                    try:
                        o = c.get(f"{REST}/organizations/{oid}", headers=headers(t["access_token"])).json()
                        name = "🏢 " + (o.get("localizedName") or oid)
                    except Exception:
                        pass
                    made.append(_upsert(org, name, t, project_id, lang))
            except Exception as e:
                raise PlatformError("LinkedIn firemné stránky sa nepodarilo načítať: " + str(e))
            if not made:
                raise PlatformError("Nenašiel som firemnú stránku, kde si administrátor.")
    return made


def _upsert(urn, name, t, project_id, lang):
    ex = db.one("SELECT id FROM accounts WHERE platform='linkedin' AND external_id=?", (urn,))
    if ex:
        save_tokens(ex["id"], t)
        return ex["id"]
    return db.run("INSERT INTO accounts(platform,name,external_id,project_id,lang,tokens) VALUES(?,?,?,?,?,?)",
                  ("linkedin", name, urn, project_id, lang, json.dumps(t)))


def _escape(text):
    # LinkedIn "little text" formát vyžaduje escapovanie špeciálnych znakov
    return re.sub(r"([\\|{}@\[\]()<>#*_~])", r"\\\1", text)


def upload(account, video, privacy="public"):
    t = tokens(account)
    if t.get("expires_at", 0) < time.time():
        raise PlatformError("LinkedIn prihlásenie vypršalo (platí 60 dní), pripoj účet znova.")
    tok, owner = t["access_token"], account["external_id"]
    h = headers(tok)
    size = os.path.getsize(video["file_path"])
    _, text = text_for(video, "linkedin")
    with client(timeout=3600) as c:
        init = check(c.post(f"{REST}/videos", params={"action": "initializeUpload"}, headers=h, json={
            "initializeUploadRequest": {"owner": owner, "fileSizeBytes": size,
                                        "uploadCaptions": False, "uploadThumbnail": False}}), "LinkedIn štart").json()["value"]
        urn, etags = init["video"], []
        with open(video["file_path"], "rb") as f:
            for ins in init["uploadInstructions"]:
                f.seek(ins["firstByte"])
                part = f.read(ins["lastByte"] - ins["firstByte"] + 1)
                r = check(c.put(ins["uploadUrl"], content=part, headers={"Content-Type": "application/octet-stream"}),
                          "LinkedIn nahrávanie")
                etags.append(r.headers.get("etag", "").strip('"') or r.headers.get("ETag", ""))
        check(c.post(f"{REST}/videos", params={"action": "finalizeUpload"}, headers=h, json={
            "finalizeUploadRequest": {"video": urn, "uploadToken": init.get("uploadToken", ""),
                                      "uploadedPartIds": etags}}), "LinkedIn dokončenie")
        for _ in range(60):
            s = c.get(f"{REST}/videos/{urllib.parse.quote(urn, safe='')}", headers=h).json()
            if s.get("status") == "AVAILABLE":
                break
            if s.get("status") == "PROCESSING_FAILED":
                raise PlatformError("LinkedIn video nespracoval: " + str(s.get("processingFailureReason")))
            time.sleep(10)
        r = check(c.post(f"{REST}/posts", headers=h, json={
            "author": owner, "commentary": _escape(text),
            "visibility": "PUBLIC" if privacy == "public" else "CONNECTIONS",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": {"title": (video.get("title") or "")[:200], "id": urn}},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}), "LinkedIn príspevok")
        post = r.headers.get("x-restli-id", "")
    return post, f"https://www.linkedin.com/feed/update/{post}" if post else ""
