"""Preklady bez Claude tokenov: bezplatné strojové prekladače (DeepL Free, Microsoft Azure F0, Google).

Každý má mesačné počítadlo znakov a appka sa tvrdo zastaví pred bezplatným limitom (nič sa neplatí).
Ochrana kvality: glosár „neprekladať“, prekladová pamäť (čo raz preložíš, už nič nestojí),
automatické kontroly a AI (haiku) opraví len označené kúsky. Claude preklad ostáva ako záloha.
"""
import datetime
import hashlib
import html
import json
import re
import threading

import httpx

from . import db, languages

_lock = threading.Lock()

# bezplatné mesačné limity (overené 2026-11): DeepL API Free 500k, Azure Translator F0 2M, Google Translation 500k
PROVIDERS = {
    "deepl": {"name": "DeepL", "free": 500_000},
    "azure": {"name": "Microsoft", "free": 2_000_000},
    "google": {"name": "Google", "free": 500_000},
}
MARGIN = 0.97  # rezerva, aby sa nikdy neprešiel limit
INTL_TAGS = {"fyp", "foryou", "foryoupage", "viral", "shorts", "reels", "tiktok", "trending", "explore", "fy"}



# ---------- nastavenia a počítadlá ----------
def _key(p):
    if p == "google":
        return (db.get_setting("google_tts_key", "") or "").strip() if db.get_setting("mt_google", False) else ""
    return (db.get_setting(f"mt_{p}_key", "") or "").strip()


def _month():
    return datetime.date.today().strftime("%Y-%m")


def usage():
    u = db.get_setting("mt_usage", {}) or {}
    out = {}
    for p, info in PROVIDERS.items():
        used = (u.get(p) or {}).get(_month(), 0)
        out[p] = {"name": info["name"], "enabled": bool(_key(p)), "used": used, "free": info["free"],
                  "left": max(0, int(info["free"] * MARGIN) - used)}
    return out


def _add(p, n):
    with _lock:
        u = db.get_setting("mt_usage", {}) or {}
        u.setdefault(p, {})
        u[p][_month()] = u[p].get(_month(), 0) + n
        db.set_setting("mt_usage", u)


def any_enabled():
    return any(_key(p) for p in PROVIDERS)


# ---------- jazykové kódy ----------
def _code(p, lang):
    if p == "deepl":
        return {"en": "EN-GB", "pt": "PT-PT", "no": "NB"}.get(lang, lang.upper())
    if p == "azure":
        return {"no": "nb", "sr": "sr-Cyrl"}.get(lang, lang)
    return lang


def _src_code(p, lang):
    if p == "deepl":
        return {"no": "NB"}.get(lang, lang.upper())
    if p == "azure":
        return {"no": "nb", "sr": "sr-Cyrl"}.get(lang, lang)
    return lang


def _deepl_targets(key):
    cache = db.get_setting("deepl_targets", {}) or {}
    if cache.get("day") == str(datetime.date.today()) and cache.get("list"):
        return set(cache["list"])
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    r = httpx.get(f"https://{host}/v2/languages", params={"type": "target"},
                  headers={"Authorization": f"DeepL-Auth-Key {key}"}, timeout=30)
    r.raise_for_status()
    lst = [x["language"].upper() for x in r.json()]
    db.set_setting("deepl_targets", {"day": str(datetime.date.today()), "list": lst})
    return set(lst)


def supports(p, lang):
    if p == "deepl":
        try:
            return _code(p, lang) in _deepl_targets(_key(p))
        except Exception:
            return False
    return lang in languages.LANGUAGES  # Azure aj Google majú všetky jazyky appky


# ---------- glosár (neprekladať) ----------
def _protect(text, glossary):
    t = html.escape(text or "", quote=False).replace("\n", "<br>")
    for g in sorted(glossary, key=len, reverse=True):
        ge = html.escape(g, quote=False)
        t = re.sub(r"(?<![\w>])" + re.escape(ge) + r"(?![\w<])", f'<span translate="no" class="notranslate">{ge}</span>', t)
    return t


def _unprotect(t):
    t = re.sub(r"<br\s*/?>", "\n", t or "")
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).replace(" ", " ").strip()


# ---------- volania poskytovateľov ----------
def _call(p, texts, src, tgt):
    key = _key(p)
    if p == "deepl":
        host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
        body = {"text": texts, "source_lang": _src_code(p, src).split("-")[0], "target_lang": _code(p, tgt),
                "tag_handling": "html", "formality": "prefer_less"}
        r = httpx.post(f"https://{host}/v2/translate", json=body, headers={"Authorization": f"DeepL-Auth-Key {key}"}, timeout=60)
        if r.status_code == 456:
            raise RuntimeError("DeepL: mesačný limit vyčerpaný")
        r.raise_for_status()
        return [x["text"] for x in r.json()["translations"]]
    if p == "azure":
        h = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}
        region = (db.get_setting("mt_azure_region", "") or "").strip()
        if region:
            h["Ocp-Apim-Subscription-Region"] = region
        r = httpx.post("https://api.cognitive.microsofttranslator.com/translate",
                       params={"api-version": "3.0", "from": _src_code(p, src), "to": _code(p, tgt), "textType": "html"},
                       json=[{"Text": t} for t in texts], headers=h, timeout=60)
        if r.status_code != 200:
            raise RuntimeError("Microsoft prekladač: " + r.text[:200])
        return [x["translations"][0]["text"] for x in r.json()]
    r = httpx.post("https://translation.googleapis.com/language/translate/v2", params={"key": key},
                   json={"q": texts, "source": src, "target": tgt, "format": "html"}, timeout=60)
    if r.status_code != 200:
        try:
            msg = r.json()["error"]["message"]
        except Exception:
            msg = r.text[:200]
        raise RuntimeError("Google prekladač: " + msg)
    return [x["translatedText"] for x in r.json()["data"]["translations"]]


def translate_texts(texts, src, tgt, glossary=()):
    """Preloží zoznam textov. Vráti (preklady, poskytovateľ) alebo vyhodí chybu, ak nie je voľný poskytovateľ."""
    out = [None] * len(texts)
    todo, hashes = [], []
    for i, t in enumerate(texts):
        if not (t or "").strip():
            out[i] = t or ""
            continue
        h = hashlib.sha1(f"{src}|{'|'.join(sorted(glossary))}|{t}".encode()).hexdigest()
        c = db.one("SELECT text FROM tm WHERE h=? AND lang=?", (h, tgt))
        if c:
            out[i] = c["text"]
        else:
            todo.append(i)
            hashes.append(h)
    if not todo:
        return out, "pamäť"
    payload = [_protect(texts[i], glossary) for i in todo]
    need = sum(len(x) for x in payload)
    errors = []
    for p in ("deepl", "azure", "google"):
        if not _key(p) or usage()[p]["left"] < need or not supports(p, tgt):
            continue
        try:
            res = _call(p, payload, src, tgt)
            _add(p, need)
            for i, h, r in zip(todo, hashes, res):
                out[i] = _unprotect(r)
                db.run("INSERT OR REPLACE INTO tm(h, lang, text) VALUES(?,?,?)", (h, tgt, out[i]))
            return out, PROVIDERS[p]["name"]
        except Exception as e:
            errors.append(str(e)[:150])
    raise RuntimeError("; ".join(errors) or "žiadny prekladač nemá voľný limit")


# ---------- hashtagy ----------
def _tag_words(tag):
    t = tag.lstrip("#")
    t = re.sub(r"([a-záäčďéíĺľňóôŕšťúýž])([A-ZÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ])", r"\1 \2", t)
    return t.replace("_", " ")


def _to_tag(words):
    parts = re.findall(r"\w+", words, re.U)
    if not parts:
        return ""
    return "#" + parts[0].lower() + "".join(w[:1].upper() + w[1:].lower() for w in parts[1:])


# ---------- kontroly bez AI ----------
def check(src, tgt, glossary):
    if not (src or "").strip():
        return ""
    if not (tgt or "").strip():
        return "prázdne"
    if tgt.strip() == src.strip() and len(src) > 25:
        return "nepreložené"
    ratio = len(tgt) / max(1, len(src))
    if len(src) > 30 and not 0.6 <= ratio <= 1.5:
        return f"dĺžka {ratio:.1f}×"
    if sorted(re.findall(r"\d+", src)) != sorted(re.findall(r"\d+", tgt)):
        return "čísla"
    for g in glossary:
        if g in src and g not in tgt:
            return f"chýba „{g}“"
    return ""


FIELDS = ("title", "voiceover", "description", "caption")


def machine_translate(script_id, langs):
    """Preloží scenár do jazykov strojovo. Vráti (hotové jazyky, jazyky pre AI zálohu, na kontrolu, poznámky)."""
    src = db.one("SELECT * FROM scripts WHERE id=?", (script_id,))
    proj = db.one("SELECT * FROM projects WHERE id=?", (src["project_id"],))
    glossary = [g.strip() for g in re.split(r"[\n,;]", (proj or {}).get("glossary") or "") if g.strip()]
    scenes = json.loads(src["scenes"] or "[]")
    tags = (src["hashtags"] or "").split()
    keep_tags = [t for t in tags if t.lstrip("#").lower() in INTL_TAGS]
    tr_tags = [t for t in tags if t not in keep_tags][:6]
    from . import anim
    anim_txt = [(i, anim.texts(s.get("anim"))) for i, s in enumerate(scenes) if s.get("anim")]
    anim_flat = [x for _, xs in anim_txt for x in xs]
    texts = [src[f] or "" for f in FIELDS] + [s.get("onscreen", "") for s in scenes] + [_tag_words(t) for t in tr_tags] + anim_flat
    done, rest, flags, used = [], [], {}, set()
    for lang in langs:
        if lang == src["lang"]:
            continue
        try:
            res, prov = translate_texts(texts, src["lang"], lang, glossary)
        except RuntimeError as e:
            rest.append(lang)
            used.add(str(e)[:120])
            continue
        used.add(prov)
        t = dict(zip(FIELDS, res[:len(FIELDS)]))
        sc = [dict(s) for s in scenes]
        for i, s in enumerate(sc):
            s["onscreen"] = res[len(FIELDS) + i]
        base = len(FIELDS) + len(scenes)
        new_tags = [_to_tag(w) for w in res[base:base + len(tr_tags)]]
        pos = base + len(tr_tags)
        for i, xs in anim_txt:
            sc[i]["anim"] = anim.with_texts(scenes[i]["anim"], res[pos:pos + len(xs)])
            pos += len(xs)
        hashtags = " ".join(dict.fromkeys([x for x in new_tags if x] + keep_tags))
        bad = {f: check(src[f], t[f], glossary) for f in FIELDS}
        bad = {f: why for f, why in bad.items() if why}
        db.run("""INSERT INTO scripts(project_id,idea_id,lang,is_source,title,voiceover,scenes,description,hashtags,caption)
                  VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(idea_id,lang) DO UPDATE SET title=excluded.title,
                  voiceover=excluded.voiceover, scenes=excluded.scenes, description=excluded.description,
                  hashtags=excluded.hashtags, caption=excluded.caption, voice_path=''""",
               (src["project_id"], src["idea_id"], lang, 0, t["title"], t["voiceover"], json.dumps(sc, ensure_ascii=False),
                t["description"], hashtags, t["caption"]))
        if bad:
            flags[lang] = bad
        done.append(lang)
    return done, rest, flags, sorted(used)
