"""Popisky a hashtagy pre každú sieť, krajinu a jazyk – skladajú sa pravidlami, bez AI.

Čo dnes funguje (overené 2026-11):
- TikTok: prvý riadok = háčik, kľúčové slová v texte (TikTok hľadá podľa textu), otázka do komentárov, 3-5 hashtagov.
- Instagram Reels: prvých ~125 znakov pred „viac“ musí niesť háčik aj kľúčové slovo, výzva uložiť/poslať ďalej, max 5 hashtagov.
- YouTube Shorts: názov krátky (prvých ~50 znakov vidno), kľúčové slovo na začiatku; prvé 3 hashtagy z popisu sa ukážu nad názvom.
- Facebook Reels: krátko (1-2 vety), otázka, 0-3 hashtagy.
- LinkedIn: háčik do ~140 znakov (potom „viac“), krátke odseky, vecný tón, otázka na konci, 3 hashtagy, bez emoji.

Hashtagy: značka + hlavné témy krajiny (banka hashtagov, ktoré ľudia v danej krajine naozaj používajú,
1 lacné AI volanie raz za projekt) + témy konkrétneho videa. Žiadne #fyp/#viral. Zakázané tvrdenia projektu sa vyhodia.
"""
import json
import re

from . import db, languages

RULES = {
    #            háčik max, text spolu max, hashtagov, otázka, výzva uložiť
    "tiktok":    {"hook": 100, "max": 2200, "tags": 5, "question": True, "save": True},
    "instagram": {"hook": 125, "max": 2200, "tags": 5, "question": True, "save": True},
    "facebook":  {"hook": 125, "max": 2000, "tags": 3, "question": True, "save": False},
    "linkedin":  {"hook": 140, "max": 3000, "tags": 3, "question": True, "save": False},
    "youtube":   {"hook": 100, "max": 4900, "tags": 4, "question": True, "save": False},
}
GENERIC = {"fyp", "foryou", "foryoupage", "viral", "trending", "explore", "fy", "reels", "tiktok", "shorts",
           "reelsinstagram", "instagood", "follow", "like", "likeforlikes", "xyzbca"}
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


# ---------- pomocné ----------
def _norm(s):
    return re.sub(r"[\W_]+", "", (s or "").lower(), flags=re.U)


def _tags(text):
    out = []
    for t in re.findall(r"#[\wÀ-￿]+", text or "", re.U):
        if _norm(t) and _norm(t) not in GENERIC:
            out.append(t)
    return out


def to_tag(words):
    words = (words or "").strip()
    if words.startswith("#"):
        return words if re.fullmatch(r"#[\w]+", words, re.U) else "#" + re.sub(r"\W+", "", words, flags=re.U)
    parts = re.findall(r"\w+", words, re.U)
    if not parts:
        return ""
    if len(parts) == 1:
        return "#" + parts[0].lower() if not parts[0].isupper() else "#" + parts[0]
    return "#" + "".join(p if (p.isupper() and len(p) <= 4) or any(c.isdigit() for c in p) else p[:1].upper() + p[1:].lower()
                         for p in parts)


def brand_tags(p):
    own = _tags(p.get("brand_tags") or "")
    if own:
        return own
    name = (p.get("name") or "").strip()
    return [to_tag(name)] if name else []


def _banned(p):
    from . import inspire
    return [b for b in inspire.banned_list(p) if b]


def _clean_banned(text, ban):
    """Vety so zakázaným tvrdením vyhodí."""
    if not ban or not text:
        return text
    low = lambda s: s.lower()
    out = []
    for line in text.split("\n"):
        sents = re.split(r"(?<=[.!?])\s+", line)
        keep = [s for s in sents if not any(low(b) in low(s) for b in ban)]
        out.append(" ".join(keep))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def _cut(s, n):
    s = (s or "").strip()
    if len(s) <= n:
        return s
    c = s[:n]
    cut = max(c.rfind(". "), c.rfind("! "), c.rfind("? "))
    if cut > n * 0.5:
        return c[:cut + 1]
    return c[:c.rfind(" ")].rstrip(",;:–-") + "…" if " " in c else c


def _first_sentence(s):
    s = (s or "").strip()
    m = re.match(r"(.+?[.!?])(\s|$)", s, re.S)
    return (m.group(1) if m else s).strip()


# ---------- banka hashtagov krajiny ----------
def bank_key(country, lang):
    return f"{(country or '').upper()}-{lang}"


def bank(project_id):
    p = db.one("SELECT hashtag_bank FROM projects WHERE id=?", (project_id,)) or {}
    try:
        return json.loads(p.get("hashtag_bank") or "{}") or {}
    except Exception:
        return {}


def bank_tags(project_id, country, lang):
    b = bank(project_id)
    tags = b.get(bank_key(country, lang)) or next((v for k, v in b.items() if k.endswith("-" + lang)), None)
    if tags:
        return [t for t in tags if _norm(t) not in GENERIC]
    kw = db.one("SELECT core FROM project_keywords WHERE project_id=? AND lang=?", (project_id, lang))
    if kw:  # záloha zadarmo: kľúčové slová z Inšpirácie (sú v jazyku krajiny)
        try:
            return [to_tag(w) for w in json.loads(kw["core"] or "[]")[:4] if w]
        except Exception:
            pass
    return []


def pairs(p):
    langs = p["languages"] if isinstance(p["languages"], list) else json.loads(p["languages"] or "[]")
    acc = db.q("SELECT DISTINCT country, lang FROM accounts WHERE project_id=? AND country!=''", (p["id"],))
    out = {bank_key(a["country"], a["lang"] or (languages.COUNTRY_LANGS.get(a["country"]) or [""])[0]) for a in acc}
    for c, ls in languages.COUNTRY_LANGS.items():
        for l in ls:
            if l in langs and c != "INT":
                out.add(bank_key(c, l))
    return sorted(k for k in out if not k.endswith("-"))


def _todo(project_id, force):
    from . import content
    p = content._project(project_id)
    have = bank(project_id)
    keys = pairs(p)
    return p, have, (keys if force else [k for k in keys if k not in have])


def bank_prompt(params):
    """1 lacné AI volanie raz za projekt: hashtagy, ktoré ľudia v každej krajine naozaj používajú pre tému projektu."""
    from . import content
    p, _, todo = _todo(params["project_id"], params.get("force"))
    params["todo"] = todo
    ban = _banned(p)
    return f"""{content._ctx(p)}
For each market (COUNTRY-language) list 6 hashtags that local people really use and search on TikTok/Instagram/YouTube
for this project's topic, in that language and local wording (e.g. Spain uses aerotermia, not a literal translation).
Order: most used first. Mix broad topic + specific niche + local (country/city only if commonly used). No brand names,
no generic tags (#fyp #viral #reels), no spaces, no banned claims.{(' Banned: ' + '; '.join(ban)) if ban else ''}
Markets: {', '.join(todo)}
Return JSON: {{"<COUNTRY-lang>":["#tag",...]}}"""


def bank_apply(params, data):
    p, have, todo = _todo(params["project_id"], params.get("force"))
    todo = params.get("todo") or todo
    ban = [_norm(b) for b in _banned(p) if _norm(b)]
    n = 0
    for k, v in (data or {}).items():
        if k in todo and isinstance(v, list):
            tags = [to_tag(str(x)) for x in v]
            tags = [t for t in dict.fromkeys(tags) if t and _norm(t) not in GENERIC and not any(b in _norm(t) for b in ban)]
            if tags:
                have[k] = tags[:8]
                n += 1
    db.run("UPDATE projects SET hashtag_bank=? WHERE id=?", (json.dumps(have, ensure_ascii=False), params["project_id"]))
    return {"countries": len(have), "new": n}


def build_bank(project_id, force=False):
    from . import content
    if not _todo(project_id, force)[2]:
        return {"countries": len(bank(project_id)), "new": 0}
    return content.run_task("hashtag_bank", {"project_id": project_id, "force": force})


def ensure_bank(project_id):
    """Doplní banku pre nové krajiny; ticho, keď AI nie je dostupná (popisky fungujú aj bez nej)."""
    try:
        p = db.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not p:
            return
        p["languages"] = json.loads(p["languages"] or "[]")
        have = bank(project_id)
        if any(k not in have for k in pairs(p)):
            build_bank(project_id)
    except Exception as e:
        print("banka hashtagov:", str(e)[:200])


# ---------- skladanie ----------
def kit(video):
    """Podklady k popisku: háčik, hodnota, otázka, výzva, kľúčové slová (zo scenára, inak z polí videa)."""
    post = {}
    src = None
    if video.get("script_id"):
        src = db.one("SELECT * FROM scripts WHERE id=?", (video["script_id"],))
    for raw in ((src or {}).get("post"), video.get("post")):
        try:
            d = json.loads(raw or "{}")
            if isinstance(d, dict) and d:
                post = d
        except Exception:
            pass
    desc = video.get("description") or ""
    hook = (video.get("caption") or "").strip() or (video.get("title") or "").strip()
    body = (post.get("body") or "").strip()
    if not body and desc:
        body = _first_sentence(desc) if _first_sentence(desc) != hook else ""
    kw = post.get("keywords") or []
    if isinstance(kw, str):
        kw = [x.strip() for x in re.split(r"[,;\n]", kw) if x.strip()]
    strip = lambda t: re.sub(r"\s{2,}", " ", re.sub(r"#[\w\u00C0-\uFFFF]+", "", t or "", flags=re.U)).strip()
    hook, body = strip(hook), strip(body)
    return {"hook": hook, "body": body, "question": (post.get("question") or "").strip(),
            "save": (post.get("save") or "").strip(), "keywords": kw, "desc": desc, "title": video.get("title") or ""}


def pick_tags(project, video, platform, country):
    """Značka + 1-2 témy krajiny (striedajú sa podľa videa) + témy videa; bez duplicít a zakázaných slov."""
    n = RULES[platform]["tags"]
    lang = video.get("lang") or project.get("source_lang") or ""
    vid_tags = _tags(video.get("hashtags"))
    local = bank_tags(project["id"], country, lang)
    brand = brand_tags(project)
    rot = []
    if local:
        rest = local[1:]
        k = (video.get("id") or 0) % len(rest) if rest else 0
        rot = [local[0]] + (rest[k:] + rest[:k])
    # poradie dôležitosti: hlavná téma krajiny, téma videa, značka, ďalšie
    order = rot[:1] + vid_tags[:1] + brand[:1] + rot[1:2] + vid_tags[1:2] + rot[2:3] + vid_tags[2:] + rot[3:] + brand[1:]
    ban = [_norm(b) for b in _banned(project) if _norm(b)]
    out, seen = [], set()
    for t in order:
        k = _norm(t)
        if not k or k in seen or k in GENERIC or any(b in k for b in ban):
            continue
        seen.add(k)
        out.append(t)
        if len(out) >= n:
            break
    if platform in ("tiktok", "instagram", "linkedin", "facebook") and brand and _norm(brand[0]) not in seen:
        out = out[:n - 1] + [brand[0]]  # značka vždy, aby sa dala nájsť
    return out


def _country_of(account, lang):
    c = (account or {}).get("country") or ""
    if c:
        return c
    return (languages.COUNTRIES.get(lang) or [""])[0]


def build(video, platform, account=None):
    """Vráti {"title", "text", "tags"} pre danú sieť. Bez AI."""
    pr = db.one("SELECT * FROM projects WHERE id=?", (video.get("project_id"),)) or {"id": 0, "name": ""}
    k = kit(video)
    r = RULES.get(platform, RULES["tiktok"])
    ban = _banned(pr)
    lang = video.get("lang") or pr.get("source_lang") or ""
    tags = pick_tags(pr, video, platform, _country_of(account, lang))
    hook = _cut(k["hook"], r["hook"])
    body = k["body"]
    if platform in ("facebook",):
        body = _cut(body, 160)
    q = k["question"] if r["question"] else ""
    save = k["save"] if r["save"] else ""
    title = None
    if platform == "youtube":
        title = _cut(re.sub(r"[<>]", "", k["title"] or hook or "Video"), 100)
        desc = k["desc"] or "\n\n".join(x for x in (hook, body) if x)
        parts = [desc]
        if q and q not in desc:
            parts.append(q)
        if k["keywords"]:
            low = desc.lower()
            miss = [w for w in k["keywords"] if w.lower() not in low]
            if miss:
                parts.append(" · ".join(miss[:4]))
        parts.append(" ".join(tags))
        text = "\n\n".join(p for p in parts if p)
    else:
        sep = "\n\n"
        parts = [hook]
        if body and body != hook:
            parts.append(body)
        if q:
            parts.append(q)
        if save:
            parts.append(save)
        text = sep.join(p for p in parts if p)
        if platform == "linkedin":
            text = _EMOJI.sub("", text)
        text = (text + sep + " ".join(tags)).strip() if tags else text
    text = _clean_banned(text, ban)
    if title:
        title = _clean_banned(title, ban) or _cut(k["hook"], 100)
    yt_tags = []
    if platform == "youtube":
        yt_tags = list(dict.fromkeys([w for w in k["keywords"]] + [t.lstrip("#") for t in tags]))
        while len(",".join(yt_tags)) > 480:
            yt_tags.pop()
    return {"title": title, "text": text[:r["max"]], "tags": yt_tags}


def preview(video, account=None):
    out = {}
    for pl in RULES:
        b = build(video, pl, account)
        out[pl] = {"title": b["title"], "text": b["text"], "len": len(b["text"]), "visible": RULES[pl]["hook"]}
    return out
