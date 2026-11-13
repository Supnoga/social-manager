"""YouTube Data API v3 - prihlásenie cez Google (OAuth 'Desktop app') a nahrávanie videí."""
import json
import os
import re
import time
import urllib.parse

from .. import db
from .common import BASE_URL, PlatformError, check, client, save_tokens, text_for, tokens

SCOPES = ("https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly "
          "https://www.googleapis.com/auth/youtube.force-ssl")  # force-ssl = čítanie a odpovedanie na komentáre
REDIRECT = BASE_URL + "/"


DAILY_UPLOADS = 95  # Google dáva ~100 nahratí denne na jeden Google Cloud projekt; rezerva


def clients():
    """Všetky Google projekty (OAuth klienti). Viac projektov = viac nahratí denne (každý má svoj limit)."""
    lst = db.get_setting("yt_clients") or []
    if not lst and db.get_setting("yt_client"):
        lst = [db.get_setting("yt_client")]
    return [x.get("installed") or x.get("web") or x for x in lst]


def add_client(data, replace=False):
    lst = db.get_setting("yt_clients") or ([db.get_setting("yt_client")] if db.get_setting("yt_client") else [])
    c = data.get("installed") or data.get("web") or data
    ids = [(x.get("installed") or x.get("web") or x).get("client_id") for x in lst]
    if c["client_id"] in ids:
        lst[ids.index(c["client_id"])] = data
    elif replace and lst:
        lst[0] = data
    else:
        lst.append(data)
    db.set_setting("yt_clients", lst)
    db.set_setting("yt_client", lst[0])
    return len(lst)


def creds(idx=0):
    cl = clients()
    if not cl:
        raise PlatformError("Najprv nahraj YouTube 'client_secret' JSON v časti Účty.")
    c = cl[idx] if 0 <= idx < len(cl) else cl[0]
    return c["client_id"], c["client_secret"]


def _client_idx(account):
    return int(tokens(account).get("client", 0) or 0)


def pick_client():
    """Pre nový kanál vyber Google projekt s najmenej kanálmi (rozloží denný limit nahratí)."""
    n = len(clients())
    if n <= 1:
        return 0
    cnt = [0] * n
    for a in db.q("SELECT tokens FROM accounts WHERE platform='youtube'"):
        i = int(json.loads(a["tokens"] or "{}").get("client", 0) or 0)
        if i < n:
            cnt[i] += 1
    return cnt.index(min(cnt))


def _uploads():
    u = db.get_setting("yt_uploads") or {}
    return u.get(time.strftime("%Y-%m-%d"), {})


def quota_ok(account):
    return _uploads().get(str(_client_idx(account)), 0) < DAILY_UPLOADS


def count_upload(account):
    day = time.strftime("%Y-%m-%d")
    u = db.get_setting("yt_uploads") or {}
    u = {day: u.get(day, {})}
    k = str(_client_idx(account))
    u[day][k] = u[day].get(k, 0) + 1
    db.set_setting("yt_uploads", u)


def usage():
    cl = clients()
    up = _uploads()
    chans = [0] * len(cl)
    for a in db.q("SELECT tokens FROM accounts WHERE platform='youtube'"):
        i = int(json.loads(a["tokens"] or "{}").get("client", 0) or 0)
        if i < len(chans):
            chans[i] += 1
    return [{"n": i + 1, "channels": chans[i], "today": up.get(str(i), 0), "limit": DAILY_UPLOADS} for i in range(len(cl))]


def auth_url(state, idx=0):
    cid, _ = creds(idx)
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent select_account", "state": state, "include_granted_scopes": "true"})


def _project_by_title(title):
    """Projekt s rovnakým názvom ako kanál (napr. kanál „Cash Xplained“ → projekt „Cash Xplained“)."""
    t = (title or "").strip().lower()
    for p in db.q("SELECT id, name FROM projects"):
        if (p["name"] or "").strip().lower() == t:
            return p["id"]
    return None


def callback(code, project_id=None, lang="", idx=0):
    guess = idx is None  # nevieme, z ktorého Google projektu prihlásenie prišlo: skús všetky
    with client() as c:
        r = None
        for i in (range(len(clients())) if guess else [idx]):
            cid, sec = creds(i)
            r = c.post("https://oauth2.googleapis.com/token", data={
                "code": code, "client_id": cid, "client_secret": sec, "redirect_uri": REDIRECT,
                "grant_type": "authorization_code"})
            if r.status_code < 400:
                idx = i
                break
        check(r, "Google token")
        t = r.json()
        t["expires_at"] = time.time() + t.get("expires_in", 3600) - 60
        t["client"] = idx
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
            pid = project_id or (_project_by_title(item["snippet"]["title"]) if guess else None)
            if guess and pid and not lang:
                lang = (db.one("SELECT COALESCE(source_lang,'') l FROM projects WHERE id=?", (pid,)) or {"l": ""})["l"]
            created.append(db.run("INSERT INTO accounts(platform,name,external_id,project_id,lang,tokens) VALUES(?,?,?,?,?,?)",
                                  ("youtube", item["snippet"]["title"], item["id"], pid, lang, json.dumps(t))))
    if not created:
        raise PlatformError("Tento Google účet nemá YouTube kanál. Najprv si ho vytvor na youtube.com.")
    return created


def access_token(account):
    t = tokens(account)
    if t.get("expires_at", 0) > time.time():
        return t["access_token"]
    if not t.get("refresh_token"):
        raise PlatformError("YouTube prihlásenie vypršalo, pripoj účet znova.")
    cid, sec = creds(_client_idx(account))
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


FULL = {"en": "Watch the full video", "sk": "Celé video", "cs": "Celé video", "de": "Das ganze Video", "fr": "La vidéo complète",
        "es": "El video completo", "it": "Il video completo", "pl": "Cały film", "pt": "O vídeo completo", "nl": "De volledige video"}


def full_video_line(video, account):
    """Short vyrobený z dlhého videa: prvý riadok popisu je odkaz na celé video (ak už je na tomto kanáli)."""
    try:
        r = db.one("""SELECT COALESCE(NULLIF(p.external_id,''), p.stash_id) external_id FROM scripts s JOIN ideas i ON i.id=s.idea_id JOIN scripts ps ON ps.idea_id=i.parent_id
                      JOIN videos pv ON pv.script_id=ps.id JOIN posts p ON p.video_id=pv.id
                      WHERE s.id=? AND i.parent_id>0 AND p.account_id=? AND (p.external_id!='' OR COALESCE(p.stash_id,'')!='') ORDER BY p.id DESC LIMIT 1""",
                   (video.get("script_id") or 0, account["id"]))
    except Exception:
        r = None
    if not r:
        return ""
    return f"{FULL.get(video.get('lang') or 'en', '▶')}: https://youtu.be/{r['external_id']}\n\n"


def category(video):
    """Kategória videa na YouTube. Vysvetľujúce videá patria do Vzdelávania (27), nie do predvolených Ľudí a blogov (22).
    Dá sa zmeniť nastavením yt_category = {"<id projektu>": "28"}."""
    m = db.get_setting("yt_category") or {}
    return str(m.get(str(video.get("project_id") or 0)) or m.get("*") or "27")


def _series(video):
    """Séria (pillar) dlhého videa; Shorts a videá bez série vrátia ''."""
    r = db.one("SELECT i.pillar, i.format FROM scripts s JOIN ideas i ON i.id=s.idea_id WHERE s.id=?", (video.get("script_id") or 0,))
    if not r or (r["format"] or "") != "long":
        return ""
    return re.sub(r"[<>]", "", (r["pillar"] or "").strip())[:120]


def add_to_series(account, video, yt_id):
    """Dlhé video zaradí do playlistu svojej série (playlist sa pri prvom videu založí sám).
    Diváci na televízore pozerajú sériu za sebou bez ďalšieho vyberania, čo pridáva hodiny pozerania.
    Nikdy nezhodí zverejnenie: každá chyba sa len vypíše."""
    try:
        name = _series(video)
        if not name or not yt_id:
            return ""
        key = name.lower()
        allp = db.get_setting("yt_playlists") or {}
        mine = allp.get(str(account["id"]), {})
        done = db.get_setting("yt_playlist_items") or {}
        if done.get(str(yt_id)):
            return mine.get(key, "")
        tok = access_token(account)
        h = {"Authorization": f"Bearer {tok}"}
        with client(timeout=60) as c:
            pl = mine.get(key)
            if not pl:
                r = check(c.post("https://www.googleapis.com/youtube/v3/playlists", params={"part": "snippet,status"}, headers=h,
                                 json={"snippet": {"title": name, "description": f"{name}: every episode from {account.get('name') or 'this channel'}.",
                                                   "defaultLanguage": video.get("lang") or "en"},
                                       "status": {"privacyStatus": "public"}}), "YouTube playlist")
                pl = r.json()["id"]
                mine[key] = pl
                allp[str(account["id"])] = mine
                db.set_setting("yt_playlists", allp)
            check(c.post("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "snippet"}, headers=h,
                         json={"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": yt_id}}}),
                  "YouTube zaradenie do playlistu")
        done[str(yt_id)] = pl
        if len(done) > 5000:
            done = dict(list(done.items())[-4000:])
        db.set_setting("yt_playlist_items", done)
        return pl
    except Exception as e:
        print("YouTube séria:", str(e)[:300])
        return ""


LOCALIZE_LANGS = ["de", "es", "pt", "fr", "it", "pl", "nl", "tr", "id", "hi"]


def _localizations(account, video, title, desc):
    """Preložené názvy (a pri dlhých videách prvý odsek popisu) cez bezplatný prekladač, bez AI a bez kvóty YouTube navyše:
    pošlú sa priamo pri nahratí. Len pre anglické Xplained kanály (alebo podľa nastavenia yt_localize) a len kým má
    prekladač voľné aspoň 40 % bezplatného limitu, aby zostalo na preklady iných projektov."""
    cfg = db.get_setting("yt_localize")
    name = account.get("name") or ""
    if cfg is None:
        on, langs = name.endswith("Xplained") and (video.get("lang") or "en") == "en", LOCALIZE_LANGS
    else:
        on = bool(cfg.get("on")) and (not cfg.get("projects") or video.get("project_id") in cfg["projects"])
        langs = cfg.get("langs") or LOCALIZE_LANGS
    if not on:
        return {}
    from .. import translate
    left = sum(v["left"] for v in translate.usage().values() if v["enabled"])
    free = sum(v["free"] for v in translate.usage().values() if v["enabled"])
    if not free or left < free * 0.4:
        return {}
    src = (video.get("lang") or "en")[:2]
    long_ = _series(video) != "" or bool(db.one("SELECT 1 FROM scripts s JOIN ideas i ON i.id=s.idea_id WHERE s.id=? AND i.format='long'",
                                               (video.get("script_id") or 0,)))
    first = (desc.split("\n\n")[0] if long_ else "").strip()[:300]
    glossary = [name, "YouTube", "Shorts"]
    out = {}
    for lg in langs:
        if lg == src:
            continue
        try:
            tr, _ = translate.translate_texts([title, first] if first else [title], src, lg, glossary)
        except Exception:
            break  # prekladač nemá voľný limit: zvyšok preskoč
        t = (tr[0] or "").strip()[:100]
        if not t:
            continue
        d = ((tr[1] + "\n\n") if first and len(tr) > 1 and tr[1] else "") + desc
        out[lg] = {"title": t, "description": d[:4900]}
    return out


def upload(account, video, privacy="public", publish_at=None):
    tok = access_token(account)
    title, desc = text_for(video, "youtube", account)
    from .. import captions
    tags = captions.build(video, "youtube", account)["tags"][:15]
    desc = (full_video_line(video, account) + desc)[:4900]
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at
    body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": category(video)}, "status": status}
    if video.get("lang"):
        body["snippet"]["defaultLanguage"] = video["lang"]
        body["snippet"]["defaultAudioLanguage"] = video["lang"]
    part = "snippet,status"
    try:
        loc = _localizations(account, video, title, desc)
    except Exception as e:
        print("YouTube preklady názvov:", e)
        loc = {}
    if loc:
        body["snippet"].setdefault("defaultLanguage", video.get("lang") or "en")
        body["localizations"] = loc
        part += ",localizations"
    size = os.path.getsize(video["file_path"])
    with client(timeout=3600) as c:
        r = check(c.post("https://www.googleapis.com/upload/youtube/v3/videos",
                         params={"uploadType": "resumable", "part": part},
                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                  "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/*"},
                         json=body), "YouTube štart nahrávania")
        loc = r.headers["Location"]
        from .common import file_chunks
        r = check(c.put(loc, headers={"Authorization": f"Bearer {tok}", "Content-Length": str(size),
                                      "Content-Type": "video/*"},
                        content=file_chunks(video["file_path"])), "YouTube nahrávanie")
        vid = r.json()["id"]
        thumb = os.path.splitext(video["file_path"])[0] + ".jpg"
        if os.path.exists(thumb):  # dlhé video: vlastný náhľad (ak ho kanál má povolený; inak YouTube vyberie sám)
            try:
                with open(thumb, "rb") as f:
                    c.post("https://www.googleapis.com/upload/youtube/v3/thumbnails/set", params={"videoId": vid},
                           headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"}, content=f.read())
            except Exception as e:
                print("YouTube náhľad:", e)
    count_upload(account)
    try:
        save_srt(video, vid)
    except Exception as e:
        print("YouTube titulky (príprava):", e)
    if status["privacyStatus"] == "public" or publish_at:
        add_to_series(account, video, vid)
    return vid, f"https://youtu.be/{vid}"


SRT_DIR = db.MEDIA_DIR / "srt"
CAPTION_COST = 4  # captions.insert = 400 jednotiek kvóty, teda ako 4 nahratia videa


def save_srt(video, yt_id):
    """Dlhé video: titulky z presného textu hlasu odloží bokom (hlas sa neskôr z Macu maže); nahrajú sa z voľnej kvóty."""
    if (db.get_setting("yt_captions", True) is False) or not video.get("script_id"):
        return
    from .. import crosslink, media
    if not crosslink.is_long(video):
        return
    s = db.one("SELECT voice_path, voiceover, lang FROM scripts WHERE id=?", (video["script_id"],))
    if not s or not s["voice_path"] or not os.path.exists(s["voice_path"]) or not (s["voiceover"] or "").strip():
        return
    body = media.srt(s["voice_path"], s["voiceover"])
    if body:
        SRT_DIR.mkdir(exist_ok=True)
        (SRT_DIR / f"{yt_id}.srt").write_text(body, encoding="utf-8")
        (SRT_DIR / f"{yt_id}.lang").write_text((s["lang"] or video.get("lang") or "en")[:2])


def caption_one():
    """Nahrá jedny čakajúce titulky, len z kvóty, ktorú nepotrebujú videá. Vráti True, ak niečo nahral."""
    if not SRT_DIR.exists():
        return False
    files = sorted(SRT_DIR.glob("*.srt"), key=lambda f: f.stat().st_mtime)
    for f in files[:20]:
        yt_id = f.stem
        post = db.one("""SELECT a.* FROM posts p JOIN accounts a ON a.id=p.account_id WHERE a.platform='youtube'
                         AND (p.external_id=? OR p.stash_id=?) LIMIT 1""", (yt_id, yt_id))
        if not post:
            if time.time() - f.stat().st_mtime > 7 * 86400:
                f.unlink(missing_ok=True)
            continue
        acc = dict(post)
        if _uploads().get(str(_client_idx(acc)), 0) + CAPTION_COST > DAILY_UPLOADS:
            continue
        lf = f.with_suffix(".lang")
        lang = lf.read_text().strip() if lf.exists() else "en"
        tok = access_token(acc)
        meta = json.dumps({"snippet": {"videoId": yt_id, "language": lang, "name": "", "isDraft": False}})
        boundary = "srtpart" + str(int(time.time()))
        data = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
                f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + f.read_bytes() + \
            f"\r\n--{boundary}--".encode()
        with client(timeout=120) as c:
            r = c.post("https://www.googleapis.com/upload/youtube/v3/captions",
                       params={"part": "snippet", "uploadType": "multipart"},
                       headers={"Authorization": f"Bearer {tok}", "Content-Type": f"multipart/related; boundary={boundary}"},
                       content=data)
        for _ in range(CAPTION_COST):
            count_upload(acc)
        if r.status_code < 300 or r.status_code in (404, 409) or "captionExists" in r.text:
            for x in (f, lf, f.with_suffix(".try")):
                x.unlink(missing_ok=True)
        elif r.status_code == 403 and "quota" in r.text.lower():
            return False
        else:
            print("YouTube titulky:", r.status_code, r.text[:300])
            tf = f.with_suffix(".try")
            n = int(tf.read_text() or 0) + 1 if tf.exists() else 1
            if n >= 3:  # po 3 neúspechoch to vzdá
                for x in (f, lf, tf):
                    x.unlink(missing_ok=True)
            else:
                tf.write_text(str(n))
                os.utime(f)  # skúsi neskôr, ostatné nebrzdí
        return True
    return False


def release(account, video_id, when=None):
    """Súkromne odložené video pustí von: v budúcom čase cez publishAt (YouTube ho zverejní sám), inak hneď."""
    tok = access_token(account)
    status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    if when:
        status = {"privacyStatus": "private", "publishAt": when, "selfDeclaredMadeForKids": False}
    with client(timeout=60) as c:
        check(c.put("https://www.googleapis.com/youtube/v3/videos", params={"part": "status"},
                    headers={"Authorization": f"Bearer {tok}"}, json={"id": video_id, "status": status}),
              "YouTube zverejnenie")
    return video_id, f"https://youtu.be/{video_id}"


def add_related(account, video_id, text):
    """Pridá riadok s odkazom na podobné video na koniec popisu a ten istý odkaz ako komentár kanála (pripnúť sa cez API nedá)."""
    if not text:
        return
    tok = access_token(account)
    h = {"Authorization": f"Bearer {tok}"}
    with client(timeout=60) as c:
        r = check(c.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet", "id": video_id}, headers=h),
                  "YouTube video")
        items = r.json().get("items") or []
        if not items:
            return
        sn = items[0]["snippet"]
        desc = sn.get("description") or ""
        if text not in desc:
            sn["description"] = (desc.rstrip() + "\n\n" + text)[:4900]
            body = {"id": video_id, "snippet": {k: sn[k] for k in ("title", "description", "tags", "categoryId",
                                                                   "defaultLanguage", "defaultAudioLanguage") if k in sn}}
            check(c.put("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet"}, headers=h, json=body),
                  "YouTube popis")
            c.post("https://www.googleapis.com/youtube/v3/commentThreads", params={"part": "snippet"}, headers=h,
                   json={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}})


def delete_video(account, video_id):
    tok = access_token(account)
    with client(timeout=60) as c:
        r = c.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": video_id},
                     headers={"Authorization": f"Bearer {tok}"})
        if r.status_code not in (204, 404):
            check(r, "YouTube zmazanie")

