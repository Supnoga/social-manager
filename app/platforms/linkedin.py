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
        _stamp(t)
        made = []
        if not org:
            me = check(c.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {t['access_token']}"}),
                       "LinkedIn profil").json()
            made.append(_upsert(f"urn:li:person:{me['sub']}", me.get("name", "Profil"), t, project_id, lang))
        else:
            try:
                acl = c.get(f"{REST}/organizationAcls", headers=headers(t["access_token"]),
                            params={"q": "roleAssignee", "role": "ADMINISTRATOR", "state": "APPROVED"}).json()
                for el in acl.get("elements", []):
                    org_urn = el.get("organization", "")
                    oid = org_urn.split(":")[-1]
                    name = oid
                    try:
                        o = c.get(f"{REST}/organizations/{oid}", headers=headers(t["access_token"])).json()
                        name = o.get("localizedName") or oid
                    except Exception:
                        pass
                    made.append(_upsert(org_urn, name, t, project_id, lang))
            except Exception as e:
                raise PlatformError("LinkedIn firemné stránky sa nepodarilo načítať: " + str(e))
            if not made:
                raise PlatformError("Nenašiel som firemnú stránku, kde si administrátor.")
    return made


def _stamp(t):
    now = time.time()
    t["expires_at"] = now + t.get("expires_in", 5184000) - 3600
    if t.get("refresh_token"):
        t["refresh_expires_at"] = now + t.get("refresh_token_expires_in", 31536000) - 3600


def expiry(t):
    """Kedy treba naozaj znova prihlásiť (pri obnoviteľnom tokene až keď vyprší refresh token)."""
    t = json.loads(t or "{}") if isinstance(t, str) else (t or {})
    return max(t.get("expires_at", 0), t.get("refresh_expires_at", 0) if t.get("refresh_token") else 0)


def is_org(account):
    return (account.get("external_id") or "").startswith("urn:li:organization")


def access_token(account):
    """Platný token; firemná stránka sa obnoví sama (refresh token platí rok), osobný profil treba po 60 dňoch prihlásiť znova."""
    t = tokens(account)
    if t.get("expires_at", 0) > time.time() + 86400 * 3:
        return t["access_token"]
    if t.get("refresh_token") and t.get("refresh_expires_at", 0) > time.time():
        cid, sec = creds(is_org(account))
        with client() as c:
            r = c.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                "grant_type": "refresh_token", "refresh_token": t["refresh_token"], "client_id": cid, "client_secret": sec})
        if r.status_code < 400:
            n = r.json()
            n.setdefault("refresh_token", t["refresh_token"])
            _stamp(n)
            if "refresh_token_expires_in" not in n:
                n["refresh_expires_at"] = t.get("refresh_expires_at", 0)
            save_tokens(account["id"], n)
            account["tokens"] = json.dumps(n)
            return n["access_token"]
    if t.get("expires_at", 0) > time.time():
        return t["access_token"]
    raise PlatformError("LinkedIn prihlásenie vypršalo, klikni pri účte na „Prihlásiť znova“.")


def refresh_all():
    """Spúšťa sa raz denne: obnoví tokeny firemných stránok skôr, než vypršia."""
    for a in db.q("SELECT * FROM accounts WHERE platform='linkedin'"):
        try:
            access_token(a)
        except Exception:
            pass


def followers(account):
    """Počet sledovateľov firemnej stránky (cielenie na krajinu/jazyk LinkedIn povolí od 300)."""
    if not is_org(account):
        return None
    urn = urllib.parse.quote(account["external_id"], safe="")
    with client() as c:
        r = c.get(f"{REST}/networkSizes/{urn}", headers=headers(access_token(account)),
                  params={"edgeType": "COMPANY_FOLLOWED_BY_MEMBER"})
    if r.status_code >= 400:
        return None
    return r.json().get("firstDegreeSize")


def page_langs():
    """Jazyky videí, ktoré idú na firemnú stránku (jedna stránka pre všetky krajiny)."""
    v = db.get_setting("li_page_langs", ["en"])
    return v if isinstance(v, list) else ["en"]


def _targeting(account, lang):
    """Cielenie príspevku na ľudí s LinkedInom v danom jazyku, len keď to stránka už smie (300+ sledovateľov)."""
    if not is_org(account) or not lang or not db.get_setting("li_target", True):
        return []
    n = db.get_setting("li_followers", 0) or 0
    if n < 300:
        return []
    return [{"interfaceLocales": [{"language": lang}]}]


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
    tok, owner = access_token(account), account["external_id"]
    h = headers(tok)
    size = os.path.getsize(video["file_path"])
    _, text = text_for(video, "linkedin", account)
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
        body = {
            "author": owner, "commentary": _escape(text)[:3000],
            "visibility": "PUBLIC" if privacy == "public" or is_org(account) else "CONNECTIONS",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": _targeting(account, video.get("lang")),
                             "thirdPartyDistributionChannels": []},
            "content": {"media": {"title": (video.get("title") or "")[:200], "id": urn}},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}
        r = c.post(f"{REST}/posts", headers=h, json=body)
        if r.status_code >= 400 and body["distribution"]["targetEntities"]:
            body["distribution"]["targetEntities"] = []  # cielenie odmietnuté -> zverejni pre všetkých
            r = c.post(f"{REST}/posts", headers=h, json=body)
        check(r, "LinkedIn príspevok")
        post = r.headers.get("x-restli-id", "")
    return post, f"https://www.linkedin.com/feed/update/{post}" if post else ""


def stats(account, posts):
    """Čísla k príspevkom firemnej stránky: zobrazenia, páči sa, komentáre, zdieľania (osobný profil ich nedáva)."""
    if not is_org(account):
        return {}
    tok = access_token(account)
    out = {}
    with client() as c:
        for i in range(0, len(posts), 20):
            part = posts[i:i + 20]
            shares = [p["external_id"] for p in part if ":share:" in p["external_id"]]
            ugc = [p["external_id"] for p in part if ":ugcPost:" in p["external_id"]]
            q = "q=organizationalEntity&organizationalEntity=" + urllib.parse.quote(account["external_id"], safe="")
            if shares:
                q += "&shares=List(" + ",".join(urllib.parse.quote(u, safe="") for u in shares) + ")"
            if ugc:
                q += "&ugcPosts=List(" + ",".join(urllib.parse.quote(u, safe="") for u in ugc) + ")"
            if not shares and not ugc:
                continue
            r = c.get(f"{REST}/organizationalEntityShareStatistics?{q}", headers=headers(tok))
            check(r, "LinkedIn čísla")
            for el in r.json().get("elements", []):
                key = el.get("share") or el.get("ugcPost")
                s = el.get("totalShareStatistics") or {}
                if key:
                    out[key] = (int(s.get("impressionCount", 0) or 0), int(s.get("likeCount", 0) or 0),
                                int(s.get("commentCount", 0) or 0), int(s.get("shareCount", 0) or 0))
        try:
            n = followers(account)
            if n is not None:
                db.set_setting("li_followers", n)
        except Exception:
            pass
    return out
