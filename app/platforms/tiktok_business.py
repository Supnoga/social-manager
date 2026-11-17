"""TikTok API for Business (Accounts API) - verejné zverejnenie na VLASTNÉ TikTok účty, aj na desiatky účtov.

Háčik: TikTok si video STIAHNE z verejnej adresy (video_url) na doméne overenej v TikTok portáli.
Appka preto vie videá sprístupniť cez verejnú adresu (napr. Cloudflare Tunnel na tvojej doméne),
a to len pod tajným odkazom, ktorý sa nedá uhádnuť.
"""
import hashlib
import hmac
import json
import secrets
import threading
import time
import urllib.parse
from pathlib import Path

from .. import db
from .common import PlatformError, check, client, save_tokens, text_for, tokens

API = "https://business-api.tiktok.com/open_api/v1.3"


def creds():
    a, s = db.get_setting("ttb_app_id", ""), db.get_setting("ttb_secret", "")
    if not a or not s:
        raise PlatformError("Najprv vlož TikTok Business App ID a Secret v časti Účty.")
    return a, s


def public_base():
    b = (db.get_setting("public_base_url", "") or "").rstrip("/")
    if not b.startswith("https://"):
        raise PlatformError("TikTok Business potrebuje verejnú https adresu (Nastavenia → Verejná adresa).")
    return b


APPROVED_REDIRECT = "https://videa.n2ntechnology.com/oauth/ttb/callback/"


def redirect_uri():
    """Musí sedieť presne s adresou v schválenej TikTok appke. Nezávisí od verejnej adresy (tunela):
    ak presmerovanie nikam nevedie, adresu z prehliadača vložíš do appky (Pripojiť z adresy)."""
    return (db.get_setting("ttb_redirect", "") or "").strip() or APPROVED_REDIRECT


def redirect_is_local():
    b = (db.get_setting("public_base_url", "") or "").rstrip("/")
    return bool(b) and redirect_uri().startswith(b + "/")


def _secret():
    s = db.get_setting("pub_secret")
    if not s:
        s = secrets.token_hex(16)
        db.set_setting("pub_secret", s)
    return s


def video_token(video_id):
    return hmac.new(_secret().encode(), f"v{video_id}".encode(), hashlib.sha256).hexdigest()[:32]


def public_url(video):
    if video.get("public_url"):   # Clipper: klip má vlastný tajný odkaz (/pub/c/...)
        return video["public_url"]
    ext = Path(video["file_path"]).suffix.lower() or ".mp4"
    return f"{public_base()}/pub/{video['id']}/{video_token(video['id'])}{ext}"


def verify_property():
    """Overí vlastníctvo verejnej adresy (URL prefix https://<tunel>/) cez API: TikTok dá podpis a meno súboru,
    appka ten súbor sama vystaví na koreni adresy (/<meno>.txt) a dá TikToku overiť. Bez DNS a bez klikania."""
    app_id, sec = creds()
    meta = {"property_type": 2, "url": public_base() + "/"}
    body = {"app_id": app_id, "secret": sec, "url_property_meta": meta}
    out = {}
    with client(timeout=60) as c:
        r = c.post(f"{API}/business/property/add/", json=body).json()
        info = (r.get("data") or {}).get("url_property_info") or {}
        out["add"] = {"code": r.get("code"), "message": r.get("message"), "status": info.get("property_status")}
        if info.get("file_name") and info.get("signature"):
            vf = db.get_setting("verify_files", {}) or {}
            name = info["file_name"] if info["file_name"].endswith(".txt") else info["file_name"] + ".txt"
            vf[name] = info["signature"]
            db.set_setting("verify_files", vf)
            out["file"] = name
        time.sleep(3)
        r = c.post(f"{API}/business/property/verify/", json=body).json()
        info = (r.get("data") or {}).get("url_property_info") or r.get("data") or {}
        out["verify"] = {"code": r.get("code"), "message": r.get("message"), "status": info.get("property_status")}
    return out


def auth_url(state):
    app_id, _ = creds()
    scope = db.get_setting("ttb_scopes", "user.info.basic,user.info.username,video.upload,video.publish")
    return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": app_id, "redirect_uri": redirect_uri(), "state": state, "response_type": "code",
        "disable_auto_auth": "1", "scope": scope})


def _env(r, what):
    check(r, what)
    d = r.json()
    if d.get("code") not in (0, "0"):
        raise PlatformError(f"{what}: {d.get('message')} (kód {d.get('code')})")
    return d.get("data") or {}


def callback(code, project_id=None, lang=""):
    app_id, sec = creds()
    with client() as c:
        d = _env(c.post(f"{API}/tt_user/oauth2/token/", json={
            "client_id": app_id, "client_secret": sec, "grant_type": "authorization_code",
            "auth_code": code, "redirect_uri": redirect_uri()}), "TikTok Business prihlásenie")
        d["expires_at"] = time.time() + int(d.get("expires_in") or 82800) - 300
        oid = d["open_id"]
        name = "TikTok " + oid[:8]
        try:
            info = c.get(f"{API}/business/get/", headers={"Access-Token": d["access_token"]},
                         params={"business_id": oid, "fields": json.dumps(["username", "display_name"])}).json()
            u = info.get("data") or {}
            name = "@" + u["username"] if u.get("username") else (u.get("display_name") or name)
        except Exception:
            pass
    ex = db.one("SELECT id FROM accounts WHERE platform='tiktok' AND external_id=?", (oid,))
    d["api"] = "business"
    if ex:
        save_tokens(ex["id"], d)
        return [ex["id"]]
    return [db.run("INSERT INTO accounts(platform,name,external_id,project_id,lang,tokens) VALUES(?,?,?,?,?,?)",
                   ("tiktok", name, oid, project_id, lang, json.dumps(d)))]


_REFRESH = threading.Lock()


def access_token(account):
    """Platný token účtu. Obnova len v jednom vlákne naraz a vždy s najnovším uloženým tokenom:
    TikTok pri obnove vydá nový refresh token a starý zneplatní, takže dve súbežné obnovy by účet odpojili."""
    with _REFRESH:
        row = db.one("SELECT * FROM accounts WHERE id=?", (account["id"],)) or account
        t = tokens(row)
        if t.get("expires_at", 0) > time.time():
            return t["access_token"]
        app_id, sec = creds()
        with client() as c:
            try:
                n = _env(c.post(f"{API}/tt_user/oauth2/refresh_token/", json={
                    "client_id": app_id, "client_secret": sec, "grant_type": "refresh_token",
                    "refresh_token": t.get("refresh_token", "")}), "TikTok obnovenie")
            except PlatformError as e:
                raise PlatformError(f"TikTok prihlásenie vypršalo, pripoj účet znova. ({e})")
        n["expires_at"] = time.time() + int(n.get("expires_in") or 82800) - 300
        t.update(n)
        save_tokens(account["id"], t)
        return t["access_token"]


def upload(account, video, privacy="public"):
    tok = access_token(account)
    oid = account["external_id"]
    _, text = text_for(video, "tiktok", account)
    post_info = {"caption": text, "disable_comment": False, "disable_duet": False, "disable_stitch": False,
                 "is_brand_organic": False, "is_branded_content": False,
                 "is_ai_generated": bool(db.get_setting("ttb_ai_label", False))}
    if db.get_setting("ttb_draft", False) or privacy == "private":
        post_info = {"upload_to_draft": True}
    h = {"Access-Token": tok, "Content-Type": "application/json"}
    with client(timeout=300) as c:
        d = _env(c.post(f"{API}/business/video/publish/", headers=h, json={
            "business_id": oid, "video_url": public_url(video), "post_info": post_info}), "TikTok zverejnenie")
        pid = d.get("share_id") or d.get("publish_id")
        status, reason, post_ids = "", "", []
        for _ in range(60):
            time.sleep(10)
            s = c.get(f"{API}/business/publish/status/", headers={"Access-Token": tok},
                      params={"business_id": oid, "publish_id": pid}).json().get("data") or {}
            status, reason, post_ids = s.get("status", ""), s.get("reason", ""), s.get("post_ids") or []
            if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
                break
            if status == "FAILED":
                if "spam" in str(reason).lower():
                    raise PlatformError("TikTok to označil ako spam (príliš podobné videá alebo veľa naraz). "
                                        "Daj medzi videá viac času a líšiace sa texty.")
                raise PlatformError("TikTok odmietol video: " + str(reason))
    if post_ids:
        return pid, f"https://www.tiktok.com/video/{post_ids[0]}"
    return pid, "koncept v TikTok appke" if status == "SEND_TO_USER_INBOX" else ""


def post_link(account, pid):
    """Odkaz na už zverejnené video: TikTok dá číslo príspevku často až chvíľu po zverejnení. "" keď ešte nie je."""
    tok = access_token(account)
    with client(timeout=30) as c:
        s = c.get(f"{API}/business/publish/status/", headers={"Access-Token": tok},
                  params={"business_id": account["external_id"], "publish_id": pid}).json().get("data") or {}
    ids = s.get("post_ids") or []
    if not ids:
        return ""
    return _link(account, ids[0])


def _link(account, item_id):
    ids = [item_id]
    who = (account.get("name") or "").strip().lstrip("@")
    return f"https://www.tiktok.com/@{who}/video/{ids[0]}" if who and " " not in who else f"https://www.tiktok.com/video/{ids[0]}"


def recent_videos(account, n=20):
    """Posledné videá účtu: [(item_id, čas vytvorenia v sekundách, odkaz)]. Záloha, keď stav zverejnenia nedá číslo príspevku."""
    tok = access_token(account)
    with client(timeout=30) as c:
        r = c.get(f"{API}/business/video/list/", headers={"Access-Token": tok}, params={
            "business_id": account["external_id"], "max_count": n,
            "fields": json.dumps(["item_id", "create_time"])})
    vids = ((r.json() if r.status_code == 200 else {}).get("data") or {}).get("videos") or []
    return [(str(v.get("item_id")), int(v.get("create_time") or 0), _link(account, str(v.get("item_id"))))
            for v in vids if v.get("item_id")]
