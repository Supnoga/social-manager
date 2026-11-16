"""Facebook stránky + Instagram (cez Meta Graph API). Jeden token -> všetky stránky aj prepojené IG účty."""
import json
import os
import time

from .. import db
from .common import PlatformError, check, client, file_chunks, save_tokens, text_for, tokens


def ver():
    return db.get_setting("meta_api_version", "v25.0")


def G(path):
    return f"https://graph.facebook.com/{ver()}/{path.lstrip('/')}"


def IGH(path):
    """Adresa pre Instagram účet pripojený priamym prihlásením cez Instagram (bez Facebook stránky)."""
    return f"https://graph.instagram.com/{ver()}/{path.lstrip('/')}"


def connect_instagram(token, project_id=None, lang="", ig_id=None):
    """Instagram bez Facebook stránky: token z Meta appky (Instagram, „API setup with Instagram login“).
    Účet musí byť firemný alebo tvorca a mať v appke rolu testera. Token platí 60 dní a appka si ho predlžuje sama."""
    token = (token or "").strip()
    if token.startswith("EAA"):
        return _connect_instagram_fb(token, project_id, lang, ig_id)
    with client() as c:
        r = c.get(IGH("me"), params={"fields": "user_id,username,account_type", "access_token": token})
    if r.status_code >= 400:
        raise PlatformError("Instagram token neprijal. Skontroluj, či je celý a či je účet firemný. " + r.text[:200])
    d = r.json()
    ig_id = str(d.get("user_id") or d.get("id") or "")
    if not ig_id:
        raise PlatformError("Instagram nevrátil účet k tomuto tokenu.")
    t = {"ig_login": True, "ig_token": token, "ig_id": ig_id, "ig_at": time.time()}
    return _upsert("instagram", "@" + (d.get("username") or ig_id), ig_id, t, project_id, lang)


def _connect_instagram_fb(token, project_id=None, lang="", ig_id=None):
    """Novšie Meta appky dávajú pri Instagrame token cez „Unified login“ (začína EAA, nevyprší): volá sa graph.facebook.com
    s číslom Instagram účtu, Facebook stránka netreba. Číslo účtu sa zistí z tokenu (debug_token)."""
    with client() as c:
        r = c.get(G("debug_token"), params={"input_token": token, "access_token": token})
        ids = []
        if r.status_code == 200:
            for sc in (r.json().get("data") or {}).get("granular_scopes") or []:
                if str(sc.get("scope", "")).startswith("instagram"):
                    ids += [str(x) for x in sc.get("target_ids") or []]
        if ig_id:                      # token systémového používateľa debug_token nedovolí: číslo účtu príde zvonku
            ids.insert(0, str(ig_id))
        if not ids:                    # alebo cez stránky, ku ktorým token patrí
            r = c.get(G("me/accounts"), params={"fields": "instagram_business_account", "access_token": token})
            if r.status_code == 200:
                ids += [str(p["instagram_business_account"]["id"]) for p in r.json().get("data") or []
                        if p.get("instagram_business_account")]
        ids = list(dict.fromkeys(ids))
        if not ids:
            raise PlatformError("Z tokenu sa nedá zistiť Instagram účet. Vygeneruj token znova pri účte v Meta appke.")
        r = c.get(G(ids[0]), params={"fields": "id,username", "access_token": token})
    if r.status_code >= 400:
        raise PlatformError("Instagram token neprijal. " + r.text[:200])
    d = r.json()
    t = {"ig_login": True, "ig_fb": True, "ig_token": token, "ig_id": str(d["id"]), "ig_at": time.time()}
    return _upsert("instagram", "@" + (d.get("username") or d["id"]), str(d["id"]), t, project_id, lang)


def ig_ctx(account):
    """Kadiaľ sa volá Instagram pre tento účet: (funkcia na adresu, token, účet v adrese).
    Cez Facebook stránku (firemné účty) alebo priamym prihlásením (klipové účty)."""
    t = tokens(account)
    if not t.get("ig_login"):
        return G, t["page_token"], t["ig_id"]
    if t.get("ig_fb"):                    # token z „Unified login“: graph.facebook.com, nevyprší
        return G, t["ig_token"], t["ig_id"]
    if time.time() - float(t.get("ig_at") or 0) > 7 * 86400:       # token žije 60 dní, predĺž ho raz za týždeň
        try:
            with client() as c:
                r = c.get("https://graph.instagram.com/refresh_access_token",
                          params={"grant_type": "ig_refresh_token", "access_token": t["ig_token"]})
            if r.status_code == 200 and r.json().get("access_token"):
                t["ig_token"] = r.json()["access_token"]
            t["ig_at"] = time.time()
            save_tokens(account["id"], t)
        except Exception:
            pass
    return IGH, t["ig_token"], "me"


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
    _, text = text_for(video, "facebook", account)
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
    U, tok, ig = ig_ctx(account)
    _, text = text_for(video, "instagram", account)
    size = os.path.getsize(video["file_path"])
    auth = {"Authorization": f"OAuth {tok}"}
    q = {"access_token": tok}
    with client(timeout=3600) as c:
        r = check(c.post(U(f"{ig}/media"), headers=auth, params=q, json={
            "media_type": "REELS", "upload_type": "resumable", "caption": text, "share_to_feed": True}), "IG kontajner")
        cont = r.json()
        cid = cont["id"]
        uri = cont.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{ver()}/{cid}"
        check(c.post(uri, headers=dict(auth, offset="0", file_size=str(size)),
                     content=file_chunks(video["file_path"])), "IG nahrávanie")
        # čakanie na spracovanie
        for _ in range(120):
            s = check(c.get(U(cid), headers=auth, params=dict(q, fields="status_code,status")), "IG stav").json()
            code = s.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                raise PlatformError("Instagram video odmietol: " + str(s.get("status")))
            time.sleep(10)
        else:
            raise PlatformError("Instagram spracováva video príliš dlho, skúsim neskôr.")
        r = check(c.post(U(f"{ig}/media_publish"), headers=auth, params=q, data={"creation_id": cid}), "IG publikovanie")
        mid = r.json()["id"]
        link = ""
        try:
            link = c.get(U(mid), headers=auth, params=dict(q, fields="permalink")).json().get("permalink", "")
        except Exception:
            pass
    return mid, link
