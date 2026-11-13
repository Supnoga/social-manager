"""Odkaz na podobné video z príbuzného kanála (napr. Machines ↔ Engines, Cash ↔ Wallet). Bez AI.

Dlhé video dostane do popisu jeden riadok „Related: … https://youtu.be/…“ a ten istý odkaz ako komentár kanála.
Odkazuje len na video, ktoré je už verejné (alebo zverejnené skôr než toto), a len medzi kanálmi s blízkou témou.
Pripnúť komentár ani nastaviť koncové obrazovky YouTube API nedovoľuje.
Mapu kanálov sa dá zmeniť nastavením related_channels = {"Cash Xplained": ["Wallet Xplained", ...]}.
"""
from . import db

GROUPS = [
    ["Cash", "Wallet", "Stocks", "Company", "Brands"],
    ["Machines", "Engines", "Inventions", "Forces", "Industry"],
    ["Engines", "Flight", "Logistics"],
    ["Mega", "House", "Underground", "Industry"],
    ["Maps", "Nations", "Arsenal"],
    ["Digital", "Logic", "Inventions"],
    ["Energy", "House", "Machines"],
]
LABEL = {"en": "Related", "de": "Passend dazu", "fr": "À voir aussi", "es": "Relacionado", "it": "Correlato",
         "pl": "Zobacz też", "cs": "Podobné video", "sk": "Podobné video", "hu": "Kapcsolódó", "nl": "Gerelateerd",
         "pt": "Relacionado"}


def _short(name):
    return (name or "").replace(" Xplained", "").strip().lower()


def related_names(channel_name):
    """Názvy príbuzných kanálov, v poradí podľa blízkosti (z nastavenia alebo zo skupín)."""
    custom = db.get_setting("related_channels") or {}
    if channel_name in custom:
        return [_short(x) for x in custom[channel_name]]
    me, out = _short(channel_name), []
    for g in GROUPS:
        gl = [x.lower() for x in g]
        if me in gl:
            out += [x for x in gl if x != me and x not in out]
    return out


def is_long(video):
    r = db.one("SELECT i.format FROM scripts s JOIN ideas i ON i.id=s.idea_id WHERE s.id=?", (video.get("script_id") or 0,))
    return bool(r and (r["format"] or "") == "long")


def pick(account, video, before, seed=0):
    """Jedno verejné dlhé video z príbuzného kanála, zverejnené najneskôr v čase `before`. Vráti (názov, yt_id) alebo None."""
    if not account or account.get("platform") != "youtube" or not is_long(video):
        return None
    names = related_names(account.get("name") or "")
    if not names:
        return None
    accs = {_short(a["name"]): a["id"] for a in db.q("SELECT id, name FROM accounts WHERE platform='youtube'")}
    ids = [accs[n] for n in names if n in accs and accs[n] != account.get("id")]
    if not ids:
        return None
    k = seed % len(ids)
    for aid in ids[k:] + ids[:k]:  # striedanie kanálov, nech neodkazujeme stále na ten istý
        r = db.one("""SELECT v.title, p.external_id FROM posts p JOIN videos v ON v.id=p.video_id JOIN scripts s ON s.id=v.script_id
                      JOIN ideas i ON i.id=s.idea_id WHERE p.account_id=? AND p.status='done' AND COALESCE(p.external_id,'')!=''
                      AND i.format='long' AND p.scheduled_at<=? ORDER BY p.scheduled_at DESC LIMIT 1""", (aid, before))
        if r:
            return (r["title"] or "").strip(), r["external_id"]
    return None


def line(account, video, before, seed=0):
    r = pick(account, video, before, seed)
    if not r:
        return ""
    lab = LABEL.get((video.get("lang") or "en")[:2], LABEL["en"])
    return f"{lab}: {r[0]} https://youtu.be/{r[1]}" if r[0] else f"{lab}: https://youtu.be/{r[1]}"
