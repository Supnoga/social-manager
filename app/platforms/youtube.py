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


DAILY_UPLOADS = 99  # Google dáva 100 nahratí denne na jeden Google Cloud projekt; 16.11.: rezerva 5 by posunula 4 krátke na ďalší deň


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


def pick_client(project_id=None):
    """Google projekt (prístup) pre nový kanál. Každá značka môže mať vlastný prístup (nastavenie yt_project_client,
    napr. {"2": 1} = projekt Dupie cez druhý Google projekt); inak hlavný. Kanály jednej značky sa medzi viac
    Google projektov nedelia, to by YouTube považoval za obchádzanie limitu."""
    n = len(clients())
    m = db.get_setting("yt_project_client", {}) or {}
    idx = int(m.get(str(project_id), 0) or 0) if project_id else 0
    return idx if 0 <= idx < max(n, 1) else 0


def gday():
    """Dátum "Google dňa": kvóta YouTube sa obnovuje o polnoci v Kalifornii (u nás 9:00, v lete tiež 9:00)."""
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    except Exception:
        return (dt.datetime.utcnow() - dt.timedelta(hours=8)).date().isoformat()


def _uploads():
    u = db.get_setting("yt_uploads") or {}
    return u.get(gday(), {})


RELEASE_RESERVE = 10  # nahrávanie dopredu nechá 10 nahratí na videá, ktoré majú ísť von hneď


# Google má dva oddelené denné limity na jeden Google projekt:
#  1) nahratia videí (videos.insert): 100 denne, stráži ho DAILY_UPLOADS a count_upload,
#  2) všetko ostatné spolu 10 000 jednotiek: zverejnenie/úprava videa 50, náhľad 50, playlist 50, komentár 50, titulky 400.
# Druhý limit sa predtým nepočítal vôbec a titulky sa mylne rátali ako nahratia (15.11. tak zastavili videá).
UNITS_LIMIT = 9000  # z 10 000; zvyšok ostáva na čítanie čísel, komentárov a Radar
U_UPDATE, U_THUMB, U_PLAYLIST, U_COMMENT, U_DELETE = 50, 50, 50, 50, 50


def _units():
    return (db.get_setting("yt_units") or {}).get(gday(), {})


def units_used(account):
    return _units().get(str(_client_idx(account)), 0)


def count_units(account, n):
    day = gday()
    u = db.get_setting("yt_units") or {}
    u = {day: u.get(day, {})}
    k = str(_client_idx(account))
    u[day][k] = u[day].get(k, 0) + int(n)
    db.set_setting("yt_units", u)


def units_block(account):
    """Google odmietol požiadavku pre minutý limit jednotiek: do obnovenia (9:00) už nič navyše neskúšať."""
    day = gday()
    b = (db.get_setting("yt_units_block") or {}).get(day, [])
    k = str(_client_idx(account))
    if k not in b:
        db.set_setting("yt_units_block", {day: b + [k]})


def units_blocked(account):
    return str(_client_idx(account)) in ((db.get_setting("yt_units_block") or {}).get(gday(), []))


def _release_reserve(account):
    """Jednotky, ktoré dnes ešte budú treba na zverejnenie videí (majú prednosť pred titulkami, prekladmi a odkazmi):
    videá už súkromne nahraté a čakajúce na zverejnenie + videá, ktoré sa dnes ešte stihnú nahrať."""
    k = _client_idx(account)
    stashed = fresh = 0
    for r in db.q("""SELECT a.tokens, COALESCE(p.stash_id,'') stash FROM posts p JOIN accounts a ON a.id=p.account_id
                     WHERE a.platform='youtube' AND p.status IN ('queued','review')"""):
        try:
            if int(json.loads(r["tokens"] or "{}").get("client", 0) or 0) != k:
                continue
        except Exception:
            continue
        if r["stash"]:
            stashed += 1
        else:
            fresh += 1
    left = max(0, DAILY_UPLOADS - _uploads().get(str(k), 0))
    return (stashed + min(fresh, left)) * (U_UPDATE + 60)  # zverejnenie + priemerný podiel náhľadu a playlistu


def spare_ok(account, cost=50):
    """Sú voľné jednotky na veci navyše (titulky, preklady názvov, odkaz na podobné video) aj po odrátaní toho,
    čo dnes ešte potrebujú videá? cost je v jednotkách kvóty."""
    if units_blocked(account):
        return False
    return units_used(account) + cost + _release_reserve(account) <= UNITS_LIMIT


def is_quota_error(text):
    t = (text or "").lower()
    return "quotaexceeded" in t or "quota" in t or "ratelimitexceeded" in t


def quota_ok(account, reserve=0):
    return _uploads().get(str(_client_idx(account)), 0) < DAILY_UPLOADS - reserve


def count_upload(account):
    day = gday()
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
    un = _units()
    return [{"n": i + 1, "channels": chans[i], "today": up.get(str(i), 0), "limit": DAILY_UPLOADS,
             "units": un.get(str(i), 0), "units_limit": UNITS_LIMIT,
             "project": cl[i].get("project_id", ""), "number": (cl[i].get("client_id") or "").split("-")[0]}
            for i in range(len(cl))]


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
        if r.status_code >= 500 or r.status_code == 429:
            raise PlatformError(f"Google dočasne neodpovedá (HTTP {r.status_code}), skúsim neskôr.")
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
                count_units(account, U_PLAYLIST)
                pl = r.json()["id"]
                mine[key] = pl
                allp[str(account["id"])] = mine
                db.set_setting("yt_playlists", allp)
            check(c.post("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "snippet"}, headers=h,
                         json={"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": yt_id}}}),
                  "YouTube zaradenie do playlistu")
            count_units(account, U_PLAYLIST)
        done[str(yt_id)] = pl
        if len(done) > 5000:
            done = dict(list(done.items())[-4000:])
        db.set_setting("yt_playlist_items", done)
        return pl
    except Exception as e:
        print("YouTube séria:", str(e)[:300])
        return ""


LOCALIZE_LANGS = ["de", "es", "pt", "fr", "it", "pl", "nl", "tr", "id", "hi"]


def _loc_log(msg):
    log = (db.get_setting("yt_loc_log", []) or [])[-19:]
    log.append(time.strftime("%d.%m. %H:%M ") + str(msg)[:200])
    db.set_setting("yt_loc_log", log)


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
        tr = None
        for attempt in range(3):
            try:
                tr, _ = translate.translate_texts([title, first] if first else [title], src, lg, glossary)
                break
            except Exception as e:
                _loc_log(f"{lg}: {e}")
                if "limit" in str(e).lower() and "rate" not in str(e).lower():
                    return out  # mesačný limit prekladača: zvyšok preskoč
                time.sleep(2 + attempt * 3)  # krátke pribrzdenie prekladača, skúsiť znova
        if not tr:
            continue
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
                count_units(account, U_THUMB)
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


def find_uploaded(account, title, duration=0, hours=12):
    """Poistka proti dvojitému nahratiu: keď sa predošlý pokus prerušil (výpadok internetu, reštart appky), video už
    na kanáli môže byť. Pozrie posledné nahraté videá kanála (pár jednotiek kvóty) a vráti id videa, ktoré má rovnaký
    názov aj dĺžku (na sekundu), je z posledných hodín a ešte nepatrí žiadnemu príspevku v appke. Rovnaký názov sám
    nestačí: staršia verzia toho istého videa nesmie nahradiť novú. Pri akejkoľvek chybe vráti '' (nahrá sa ako doteraz)."""
    try:
        import datetime as dt
        title = (title or "").strip()
        if not title:
            return ""
        tok = access_token(account)
        h = {"Authorization": f"Bearer {tok}"}
        with client(timeout=30) as c:
            ch = c.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "contentDetails", "mine": "true"}, headers=h)
            count_units(account, 1)
            if ch.status_code != 200:
                return ""
            items = ch.json().get("items") or []
            pl = next((i["contentDetails"]["relatedPlaylists"]["uploads"] for i in items
                       if i.get("id") == account.get("external_id")), None) or (items and items[0]["contentDetails"]["relatedPlaylists"]["uploads"])
            if not pl:
                return ""
            r = c.get("https://www.googleapis.com/youtube/v3/playlistItems",
                      params={"part": "snippet", "playlistId": pl, "maxResults": 25}, headers=h)
            count_units(account, 1)
            if r.status_code != 200:
                return ""
        limit = (dt.datetime.utcnow() - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
        for it in r.json().get("items") or []:
            sn = it.get("snippet") or {}
            yid = (sn.get("resourceId") or {}).get("videoId") or ""
            if not yid or (sn.get("title") or "").strip() != title or (sn.get("publishedAt") or "") < limit:
                continue
            if db.one("SELECT 1 FROM posts WHERE external_id=? OR stash_id=?", (yid, yid)):
                continue  # toto video už appka pozná (iný príspevok)
            with client(timeout=30) as c:
                d = c.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "contentDetails", "id": yid}, headers=h)
            count_units(account, 1)
            m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", ((d.json().get("items") or [{}])[0].get("contentDetails") or {}).get("duration") or "") if d.status_code == 200 else None
            secs = sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0
            if secs and duration and abs(secs - float(duration)) <= 1.5:
                return yid
    except Exception as e:
        print("YouTube kontrola dvojitého nahratia:", str(e)[:200])
    return ""


def find_interrupted(account, video):
    return find_uploaded(account, text_for(video, "youtube", account)[0], video.get("duration") or 0)


SRT_DIR = db.MEDIA_DIR / "srt"
CAPTION_COST = 400  # captions.insert = 400 jednotiek z limitu 10 000 (nie z limitu nahratí)


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
        if not spare_ok(acc, CAPTION_COST):
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
        count_units(acc, CAPTION_COST)
        if r.status_code < 300 or r.status_code in (404, 409) or "captionExists" in r.text:
            for x in (f, lf, f.with_suffix(".try")):
                x.unlink(missing_ok=True)
        elif r.status_code == 403 and "quota" in r.text.lower():
            units_block(acc)
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
    count_units(account, U_UPDATE)
    return video_id, f"https://youtu.be/{video_id}"


def unschedule(account, video_id):
    """Zruší naplánované zverejnenie (publishAt): video ostane na YouTube súkromné."""
    tok = access_token(account)
    with client(timeout=60) as c:
        check(c.put("https://www.googleapis.com/youtube/v3/videos", params={"part": "status"},
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"id": video_id, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}),
              "YouTube zrušenie plánu")
    count_units(account, U_UPDATE)


def add_related(account, video_id, text):
    """Pridá riadok s odkazom na podobné video na koniec popisu a ten istý odkaz ako komentár kanála (pripnúť sa cez API nedá)."""
    if not text or not spare_ok(account, U_UPDATE + U_COMMENT + 1):  # vec navyše: len z jednotiek, ktoré nepotrebujú videá
        return
    tok = access_token(account)
    h = {"Authorization": f"Bearer {tok}"}
    with client(timeout=60) as c:
        count_units(account, 1)
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
            count_units(account, U_UPDATE + U_COMMENT)
            c.post("https://www.googleapis.com/youtube/v3/commentThreads", params={"part": "snippet"}, headers=h,
                   json={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}})


def delete_video(account, video_id):
    tok = access_token(account)
    with client(timeout=60) as c:
        r = c.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": video_id},
                     headers={"Authorization": f"Bearer {tok}"})
        if r.status_code not in (204, 404):
            check(r, "YouTube zmazanie")
    count_units(account, U_DELETE)




def localize_one():
    """Doplní preložené názvy a popisy už nahratým Xplained videám, ktorým chýbajú. Len z voľnej kvóty. True = niečo spravil."""
    done = set(db.get_setting("yt_loc_done", []) or [])
    rows = db.q("""SELECT p.id pid, COALESCE(NULLIF(p.external_id,''), p.stash_id) yt, a.*, v.id vid FROM posts p
                   JOIN accounts a ON a.id=p.account_id JOIN videos v ON v.id=p.video_id
                   WHERE a.platform='youtube' AND a.name LIKE '%Xplained' AND p.status IN ('done','queued','review')
                   AND COALESCE(NULLIF(p.external_id,''), p.stash_id, '')!='' ORDER BY p.scheduled_at LIMIT 400""")
    for r in rows:
        if r["yt"] in done:
            continue
        acc = {k: r[k] for k in r.keys() if k not in ("pid", "yt", "vid")}
        acc["id"] = r["account_id"] if "account_id" in r.keys() else acc.get("id")
        if not spare_ok(acc):
            continue
        video = db.one("SELECT * FROM videos WHERE id=?", (r["vid"],))
        tok = access_token(acc)
        h = {"Authorization": f"Bearer {tok}"}
        with client(timeout=60) as c:
            g = c.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet,localizations", "id": r["yt"]}, headers=h)
            items = g.json().get("items") or [] if g.status_code == 200 else None
            if items is None:
                _loc_log(f"spätne {r['yt']}: {g.status_code} {g.text[:120]}")
                return False
            if not items or len(items[0].get("localizations") or {}) >= 5:
                done.add(r["yt"])
                db.set_setting("yt_loc_done", sorted(done))
                continue
            sn = items[0]["snippet"]
            loc = _localizations(acc, video, sn.get("title") or "", sn.get("description") or "")
            if not loc:
                return False  # prekladač nemá limit alebo je vypnutý
            body = {"id": r["yt"], "localizations": loc,
                    "snippet": {k: sn[k] for k in ("title", "description", "tags", "categoryId", "defaultAudioLanguage") if k in sn}}
            body["snippet"]["defaultLanguage"] = sn.get("defaultLanguage") or (video.get("lang") or "en")
            u = c.put("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet,localizations"}, headers=h, json=body)
        count_units(acc, U_UPDATE + 1)
        if u.status_code < 300:
            done.add(r["yt"])
            db.set_setting("yt_loc_done", sorted(done))
        else:
            _loc_log(f"spätne {r['yt']}: {u.status_code} {u.text[:160]}")
            if u.status_code == 403:
                if is_quota_error(u.text):
                    units_block(acc)
                return False
            done.add(r["yt"])  # nevracať sa k nemu dookola
            db.set_setting("yt_loc_done", sorted(done))
        return True
    return False
