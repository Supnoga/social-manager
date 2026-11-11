"""Vymýšľač obsahu: stratégia -> nápady -> scenáre -> lokalizácia do jazykov.

Každá úloha má 2 časti: vytvorenie promptu a uloženie výsledku. Vďaka tomu funguje aj
"ručný režim" (skopíruješ prompt do claude.ai a vložíš odpoveď späť), ak by CLI nebežalo.
"""
import json

from . import ai, db, languages


def _project(pid):
    p = db.one("SELECT * FROM projects WHERE id=?", (pid,))
    if not p:
        raise ai.AIError("Projekt neexistuje")
    p["languages"] = json.loads(p["languages"] or "[]")
    return p


def _ctx(p):
    """Krátky kontext projektu - posiela sa v každej požiadavke, preto je stručný (šetrí tokeny)."""
    parts = [f"Project: {p['name']}"]
    if p.get("design_summary"):
        parts.append(f"Brand/design guide: {p['design_summary']}")
    if p.get("sources_summary"):
        parts.append(f"Facts from project sources (use them, don't invent facts): {p['sources_summary']}")
    if p["strategy_short"]:
        parts.append(f"Strategy: {p['strategy_short']}")
    else:
        for k in ("description", "audience", "tone", "goals"):
            if p[k]:
                parts.append(f"{k.capitalize()}: {p[k][:400]}")
    from . import inspire
    if inspire.banned_ctx(p):
        parts.append(inspire.banned_ctx(p))
    parts.append(f"Source language: {languages.english(p['source_lang'])}")
    return "\n".join(parts)


# ---------- 1. STRATÉGIA ----------
def strategy_prompt(params):
    p = _project(params["project_id"])
    return f"""Create a sharp short-form video content strategy (TikTok, Reels, Shorts, Facebook) for this project.
Name: {p['name']}
About: {p['description']}
Target audience: {p['audience']}
Tone/brand voice: {p['tone']}
Goals: {p['goals']}
Markets: {', '.join(languages.english(l) for l in p['languages'])}
{('Facts from project sources: ' + p['sources_summary']) if p.get('sources_summary') else ''}
Think like a top creator-strategist: specific audience pains/desires, what makes people stop scrolling, save, share and follow.
Return JSON:
{{"positioning":"1-2 sentences","audience":[{{"persona":"","pains":"","desires":""}}] (2-3),
"pillars":[{{"name":"","why":"","examples":["",""]}}] (4-6),
"hooks":["proven hook patterns adapted to this niche"] (8),
"formats":[{{"name":"","structure":""}}] (4-5),
"cadence":"recommended posting frequency per platform",
"do":[""],"dont":[""],
"summary":"max 450 characters, dense English summary of the strategy used as context for future prompts"}}
Write all values in {languages.english(p['source_lang'])} except "summary" (English)."""


def strategy_apply(params, data):
    db.run("UPDATE projects SET strategy=?, strategy_short=? WHERE id=?",
           (json.dumps(data, ensure_ascii=False), (data.get("summary") or "")[:600], params["project_id"]))
    return data


# ---------- 2. NÁPADY ----------
def ideas_prompt(params):
    p = _project(params["project_id"])
    n = max(1, min(int(params.get("count", 10)), 30))
    prev = db.q("SELECT title FROM ideas WHERE project_id=? ORDER BY id DESC LIMIT 60", (p["id"],))
    prev_txt = "; ".join(r["title"][:60] for r in prev)
    pillars = ""
    if p["strategy"]:
        try:
            pillars = ", ".join(x["name"] for x in json.loads(p["strategy"]).get("pillars", []))
        except Exception:
            pass
    focus = params.get("focus", "").strip()
    fmt = params.get("format", "short")
    from . import inspire
    tpl = inspire.templates_prompt(p["id"], 6)
    qs = inspire.questions(p["id"], p["source_lang"], 5)
    qtxt = ("Real questions people ask (great topics): " + "; ".join(q["text"][:90] for q in qs)) if qs else ""
    return f"""{_ctx(p)}
{tpl}
{qtxt}
Pillars: {pillars or 'choose yourself'}
{('Focus for this batch: ' + focus) if focus else ''}
{('Our real results so far (build on what worked, avoid what flopped): ' + p['learnings']) if p.get('learnings') else ''}
Video format: {'short vertical 20-60s' if fmt == 'short' else 'long-form 5-12 min YouTube'}
Already used (do NOT repeat or paraphrase): {prev_txt or 'none'}

Brainstorm 3x more ideas than needed internally, then return only the {n} strongest.
Each must have a scroll-stopping hook for the first 2 seconds, a clear payoff, and work in any European country (avoid local-only references unless focus asks).
Score 1-10 = realistic viral/save/share potential, be strict.
Return JSON: {{"ideas":[{{"title":"","hook":"exact first sentence spoken","angle":"what makes it unique","pillar":"","template":"format key","why":"why it performs","score":7}}]}}
Write in {languages.english(p['source_lang'])}."""


def ideas_apply(params, data):
    pid = params["project_id"]
    fmt = params.get("format", "short")
    out = []
    for i in data.get("ideas", []):
        iid = db.run("INSERT INTO ideas(project_id,title,hook,angle,pillar,format,why,score,template) VALUES(?,?,?,?,?,?,?,?,?)",
                     (pid, i.get("title", "")[:300], i.get("hook", ""), i.get("angle", ""), i.get("pillar", ""),
                      fmt, i.get("why", ""), int(i.get("score") or 0), _tpl(i.get("template"))))
        out.append(iid)
    return {"created": len(out)}


def _tpl(k):
    from . import inspire
    k = str(k or "").strip().lower()
    return k if k in inspire.FMT else ""


# ---------- 3. SCENÁRE (dávkovo viac nápadov naraz) ----------
def scripts_prompt(params):
    ideas = [db.one("SELECT * FROM ideas WHERE id=?", (i,)) for i in params["idea_ids"]]
    ideas = [i for i in ideas if i]
    p = _project(ideas[0]["project_id"])
    from . import inspire
    items = "\n".join(f'- id {i["id"]} [{i["format"]}]: {i["title"]} | hook: {i["hook"]} | angle: {i["angle"]}'
                      + (f' | format: {inspire.FMT[i["template"]][2]}' if i.get("template") in inspire.FMT else "") for i in ideas)
    return f"""{_ctx(p)}
Write production-ready video scripts for these ideas:
{items}

Rules: short = 110-150 spoken words (~45s), long = 700-1100 words. Start with the hook verbatim (max 14 words, no greeting), deliver value fast,
at least one concrete number, short sentences, a new visual every 2-4 s, pattern interrupts, end with a natural CTA (follow/save/comment). Spoken text must sound natural for voice-over (TTS),
no emojis or symbols in voiceover. It will be machine-translated to many languages: short clear sentences, no puns or rhymes
tied to one language, numbers as digits, brand/product names exact. Captions/hashtags optimized for TikTok/Reels/Shorts.
Return JSON: {{"scripts":[{{"idea_id":0,"title":"max 90 chars, curiosity-driven","voiceover":"full spoken text",
"scenes":[{{"visual":"what to show","onscreen":"short on-screen text","q":"2-5 English words to search stock footage","anim":null}}] (4-7 scenes; scene 1 = hook: strongest, moving, concrete shot;
for 1-2 scenes with numbers/lists/comparisons set "anim" to an animated graphic: {{"t":"counter","d":{{"value":2,"prefix":"","suffix":" €","label":""}}}} |
{{"t":"bars","d":{{"title":"","suffix":"","items":[{{"label":"","value":0}}]}}}} | {{"t":"list","d":{{"title":"","items":[""]}}}} |
{{"t":"compare","d":{{"left":{{"label":"","value":""}},"right":{{"label":"","value":""}}}}}} | {{"t":"kinetic","d":{{"words":["2-4 punchy words"]}}}}),
"description":"YouTube description 2-4 sentences + CTA","caption":"social caption max 150 chars","hashtags":"#a #b (5-8)"}}]}}
Write in {languages.english(p['source_lang'])}."""


def scripts_apply(params, data):
    n = 0
    for s in data.get("scripts", []):
        idea = db.one("SELECT * FROM ideas WHERE id=?", (int(s.get("idea_id") or 0),))
        if not idea:
            continue
        p = _project(idea["project_id"])
        db.run("""INSERT INTO scripts(project_id,idea_id,lang,is_source,title,voiceover,scenes,description,hashtags,caption)
                  VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(idea_id,lang) DO UPDATE SET title=excluded.title,
                  voiceover=excluded.voiceover, scenes=excluded.scenes, description=excluded.description,
                  hashtags=excluded.hashtags, caption=excluded.caption""",
               (p["id"], idea["id"], p["source_lang"], 1, s.get("title", ""), s.get("voiceover", ""),
                json.dumps(s.get("scenes", []), ensure_ascii=False), s.get("description", ""),
                s.get("hashtags", ""), s.get("caption", "")))
        db.run("UPDATE ideas SET status='scripted' WHERE id=?", (idea["id"],))
        n += 1
    return {"created": n}


# ---------- 4. LOKALIZÁCIA (lacný model, viac jazykov v 1 volaní) ----------
def translate_prompt(params):
    src = db.one("SELECT * FROM scripts WHERE id=?", (params["script_id"],))
    langs = params["langs"]
    scenes = [s.get("onscreen", "") for s in json.loads(src["scenes"] or "[]")]
    from . import anim
    anims = {str(i): anim.texts(s.get("anim")) for i, s in enumerate(json.loads(src["scenes"] or "[]")) if s.get("anim")}
    payload = {"title": src["title"], "voiceover": src["voiceover"], "onscreen": scenes, **({"anim_texts": anims} if anims else {}),
               "description": src["description"], "caption": src["caption"], "hashtags": src["hashtags"]}
    names = ", ".join(f"{c}={languages.english(c)}" for c in langs)
    return f"""Localize (not literal translation) this short video script for native speakers. Keep meaning, punch and length
(voiceover must take about the same time to speak). Use natural idioms, local-relevant hashtags (mix of local + international).
Languages: {names}
Source: {json.dumps(payload, ensure_ascii=False)}
Return JSON: {{"<lang code>":{{"title":"","voiceover":"","onscreen":[""],"description":"","caption":"","hashtags":""{', "anim_texts":{"<scene>":[""]}' if anims else ''}}}}}"""


def translate_apply(params, data):
    src = db.one("SELECT * FROM scripts WHERE id=?", (params["script_id"],))
    scenes = json.loads(src["scenes"] or "[]")
    n = 0
    for lang, t in data.items():
        if lang not in params["langs"] or not isinstance(t, dict):
            continue
        sc = [dict(s) for s in scenes]
        for i, txt in enumerate(t.get("onscreen", []) or []):
            if i < len(sc):
                sc[i]["onscreen"] = txt
        from . import anim
        for k, tr in (t.get("anim_texts") or {}).items():
            if str(k).isdigit() and int(k) < len(sc) and sc[int(k)].get("anim") and isinstance(tr, list):
                sc[int(k)]["anim"] = anim.with_texts(sc[int(k)]["anim"], tr)
        db.run("""INSERT INTO scripts(project_id,idea_id,lang,is_source,title,voiceover,scenes,description,hashtags,caption)
                  VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(idea_id,lang) DO UPDATE SET title=excluded.title,
                  voiceover=excluded.voiceover, scenes=excluded.scenes, description=excluded.description,
                  hashtags=excluded.hashtags, caption=excluded.caption""",
               (src["project_id"], src["idea_id"], lang, 0, t.get("title", ""), t.get("voiceover", ""),
                json.dumps(sc, ensure_ascii=False), t.get("description", ""), t.get("hashtags", ""), t.get("caption", "")))
        n += 1
    return {"created": n}


# ---------- 5. POPIS K HOTOVÉMU VIDEU (keď máš vlastné video bez scenára) ----------
def meta_prompt(params):
    v = db.one("SELECT * FROM videos WHERE id=?", (params["video_id"],))
    p = _project(v["project_id"])
    lang = v["lang"] or p["source_lang"]
    return f"""{_ctx(p)}
Write publishing metadata for a short video. What the video is about: {params.get('about') or v['original_name']}
Language: {languages.english(lang)}
Return JSON: {{"title":"max 90 chars","description":"2-4 sentences + CTA","hashtags":"#a #b (5-8)"}}"""


def meta_apply(params, data):
    db.run("UPDATE videos SET title=?, description=?, hashtags=? WHERE id=?",
           (data.get("title", ""), data.get("description", ""), data.get("hashtags", ""), params["video_id"]))
    return data


# ---------- 6. DIZAJN (MD súbory -> krátky brand guide, robí sa len raz) ----------
def design_prompt(params):
    p = _project(params["project_id"])
    md = (p.get("design_md") or "")[:12000]
    return f"""Summarize this brand/design document into a compact guide used as context for video content creation.
Document:
{md}
Return JSON: {{"summary":"max 500 chars, English: visual style, tone of voice, audience, key do/don't","colors":["#hex"] (main brand colors, max 5),"font":"main font name or empty"}}"""


def design_apply(params, data):
    db.run("UPDATE projects SET design_summary=?, design_colors=? WHERE id=?",
           ((data.get("summary") or "")[:600], json.dumps((data.get("colors") or [])[:5]), params["project_id"]))
    return data


# ---------- 7. ZDROJE (weby, texty, súbory -> krátky výťah faktov, robí sa len raz) ----------
def sources_prompt(params):
    p = _project(params["project_id"])
    items = json.loads(p.get("sources") or "[]")
    per = max(2000, 36000 // max(1, len(items)))
    doc = "\n\n".join(f"### {it['name']}\n{it['text'][:per]}" for it in items)
    return f"""Extract the most useful facts for creating social media videos for project "{p['name']}" from these sources.
Keep: concrete facts, numbers, products/services, prices, USPs, stories, customer problems, FAQs, claims that can be made.
Sources:
{doc}
Return JSON: {{"summary":"max 1500 chars, dense English bullet-style facts (use ; as separator)"}}"""


def sources_apply(params, data):
    db.run("UPDATE projects SET sources_summary=? WHERE id=?", ((data.get("summary") or "")[:1800], params["project_id"]))
    return data


# ---------- RADAR (trendy, konkurencia, schránka nápadov) ----------
import datetime as _dt


def radar_keywords(pid):
    """Kľúčové slová projektu pre každý jazyk (1 lacné volanie, raz za projekt / po zmene popisu)."""
    p = _project(pid)
    langs = p["languages"][:40]
    data = ai.ask(f"""{_ctx(p)}
About: {(p['description'] or '')[:500]}
For trend monitoring, give search keywords for this project in each language: {', '.join(langs)}.
core = 4-8 exact topic words people search, related = 4-8 adjacent topics, negative = 2-5 words that look related but are off-topic,
entities = 0-5 brands/people/places relevant. Single words or short phrases, lowercase, in that language.
Return JSON: {{"<lang code>":{{"core":[],"related":[],"negative":[],"entities":[]}}}}""", "radar_keywords", "cheap")
    n = 0
    for lang, kw in (data or {}).items():
        if lang in langs and isinstance(kw, dict):
            db.run("""INSERT OR REPLACE INTO project_keywords(project_id, lang, core, related, negative, entities, updated_at)
                      VALUES(?,?,?,?,?,?,datetime('now','localtime'))""",
                   (pid, lang, *(json.dumps([str(x) for x in kw.get(k, [])][:10], ensure_ascii=False)
                                 for k in ("core", "related", "negative", "entities"))))
            n += 1
    return {"langs": n}


def _radar_ideas(p, sig, n, purpose, kind, extra=""):
    from . import inspire
    prev = db.q("SELECT title FROM ideas WHERE project_id=? ORDER BY id DESC LIMIT 40", (p["id"],))
    lines = "\n".join(f'{s["id"]} [{",".join(s["mk"]) if isinstance(s["mk"], list) else s["mk"]}] {s["txt"]}' for s in sig)
    data = ai.ask(f"""{_ctx(p)}
{('Our results: ' + p['learnings']) if p.get('learnings') else ''}
Signals this week (T = trend, K = competitor video far above its normal views, E = upcoming event/holiday: video must be ready for that date,
O = real question people ask: answer it, Z = inspiration the owner saved: prefer these):
{lines or 'none'}
{extra}
{inspire.templates_prompt(p["id"], 5)}
Already have (don't repeat): {'; '.join(r['title'][:50] for r in prev) or 'none'}
Propose the {n} best short-video ideas for this project. Use a signal only if it truly fits the project; it's fine to ignore weak ones.
For K signals copy the format/angle, never the content. Score 1-10 strictly.
Return JSON: {{"ideas":[{{"title":"","hook":"exact first sentence","angle":"","template":"format key","why":"","why_now":"1 short sentence, which signal and why now","signal":"T1|K2|O1|Z1|none","markets":"all|list of lang codes","score":7}}]}}
Write in {languages.english(p['source_lang'])}.""", purpose, kind)
    refs = {s["id"]: s["ref"] for s in sig}
    exp = (_dt.datetime.now() + _dt.timedelta(days=14)).strftime("%Y-%m-%d")
    made = 0
    for i in (data or {}).get("ideas", [])[:n]:
        if not i.get("title"):
            continue
        ref = refs.get(str(i.get("signal", "")).strip(), {})
        if ref.get("event"):
            from . import events
            events._db()
            db.run("""INSERT INTO ideas(project_id,title,hook,angle,pillar,format,why,score,status,source,source_ref,why_now,
                      expires_at,due_date,markets,template) VALUES(?,?,?,?,'','short',?,?,'inbox','event',?,?,?,?,?,?)""",
                   (p["id"], i["title"][:300], i.get("hook", ""), i.get("angle", ""), i.get("why", ""), int(i.get("score") or 0),
                    ref["event"], i.get("why_now", ""), ref["date"], ref["date"],
                    ",".join(ref.get("langs") or []), _tpl(i.get("template"))))
            made += 1
            continue
        db.run("""INSERT INTO ideas(project_id,title,hook,angle,pillar,format,why,score,status,source,source_ref,why_now,expires_at,template)
                  VALUES(?,?,?,?,'','short',?,?,'inbox','radar',?,?,?,?)""",
               (p["id"], i["title"][:300], i.get("hook", ""), i.get("angle", ""), i.get("why", ""), int(i.get("score") or 0),
                json.dumps(ref, ensure_ascii=False), i.get("why_now", ""), exp, _tpl(i.get("template"))))
        inspire.mark_used(ref)
        made += 1
    return made


def radar_weekly(pid, n=5):
    """Raz týždenne: výťah trendov a konkurencie + naše výsledky -> 5 nápadov do schránky (1 volanie)."""
    from . import radar
    p = _project(pid)
    sig = radar.signals(pid)
    if not sig and not p.get("learnings"):
        return {"created": 0, "note": "zatiaľ nič nové"}
    return {"created": _radar_ideas(p, sig, n, "radar_weekly", "creative")}


def radar_quick(pid, ref):
    """„Nápad z tohto“: 2 nápady z jedného trendu alebo videa konkurencie (malé volanie)."""
    p = _project(pid)
    if ref.get("trend"):
        from . import radar
        t = next((x for x in radar.project_trends(pid, 80) if x["key"] == ref["trend"]), None)
        if not t:
            raise ai.AIError("Trend už nie je aktuálny")
        sig = [{"id": "T1", "mk": t["langs"] or "all", "txt": f'"{t["label"]}" {t["stage"]}; ctx: {t["ctx"][:200]}',
                "ref": {"trend": t["key"], "label": t["label"]}}]
    elif ref.get("question") or ref.get("swipe"):
        from . import inspire
        if ref.get("question"):
            q = db.one("SELECT * FROM questions WHERE id=?", (int(ref["question"]),))
            if not q:
                raise ai.AIError("Otázka už neexistuje")
            sig = [{"id": "O1", "mk": [q["lang"]] if q["source"] == "search" and q["lang"] else "all",
                    "txt": f'people ask: "{q["text"]}" (language {q["lang"]})', "ref": {"question": q["id"], "label": q["text"][:80]}}]
        else:
            w = db.one("SELECT * FROM swipes WHERE id=?", (int(ref["swipe"]),))
            if not w:
                raise ai.AIError("Položka už neexistuje")
            sig = [{"id": "Z1", "mk": "all", "txt": f'owner likes this ({w["platform"] or "note"}): "{w["title"] or w["url"]}"'
                    + (f'; note: {w["note"][:300]}' if w["note"] else "") + ". Copy the format/idea, never the content.",
                    "ref": {"swipe": w["id"], "label": (w["title"] or w["note"] or w["url"])[:80]}}]
    else:
        c = db.one("SELECT * FROM comp_posts WHERE id=?", (int(ref["comp_post"]),))
        sig = [{"id": "K1", "mk": "all", "txt": f'competitor video "{c["title"]}" {c["ratio"]}x its normal, {c["views"]} views',
                "ref": {"comp_post": c["id"], "label": c["title"][:80]}}]
    return {"created": _radar_ideas(p, sig, 2, "radar_quick", "cheap", "Make both ideas about this signal.")}


TASKS = {
    "sources": (sources_prompt, sources_apply, "cheap"),
    "design": (design_prompt, design_apply, "cheap"),
    "strategy": (strategy_prompt, strategy_apply, "creative"),
    "ideas": (ideas_prompt, ideas_apply, "creative"),
    "scripts": (scripts_prompt, scripts_apply, "creative"),
    "translate": (translate_prompt, translate_apply, "cheap"),
    "meta": (meta_prompt, meta_apply, "cheap"),
}


def run_task(name, params):
    prompt_fn, apply_fn, kind = TASKS[name]
    prompt = prompt_fn(params)
    try:
        data = ai.ask(prompt, name, kind)
    except ai.NeedManual as e:
        e.params = params
        raise
    return apply_fn(params, data)


def apply_manual(name, params, text):
    prompt_fn, apply_fn, kind = TASKS[name]
    data = ai.extract_json(text)
    return apply_fn(params, data)


def translate_all(script_id, langs, chunk=6):
    """Preklad: najprv bezplatné strojové prekladače (0 tokenov), Claude len pre zvyšok a na opravu označených kúskov."""
    from . import translate
    done, rest, flags, used = ([], list(langs), {}, [])
    if translate.any_enabled():
        done, rest, flags, used = translate.machine_translate(script_id, langs)
    if flags:
        try:
            fix_flagged(script_id, flags)
            flags = {}
        except ai.NeedManual:
            pass
        except Exception:
            pass
    for l, why in flags.items():
        db.run("UPDATE scripts SET qa=? WHERE idea_id=(SELECT idea_id FROM scripts WHERE id=?) AND lang=?",
               (json.dumps(why, ensure_ascii=False), script_id, l))
    total = len(done)
    for i in range(0, len(rest), chunk):
        total += run_task("translate", {"script_id": script_id, "langs": rest[i:i + chunk]})["created"]
    return {"created": total, "machine": len(done), "ai": len(rest), "by": used, "check": flags}


def scene_queries(scenes, title=""):
    """Pre staršie scenáre bez 'q': krátke anglické výrazy na hľadanie záberov (1 malé lacné volanie)."""
    need = [i for i, sc in enumerate(scenes) if not sc.get("q")]
    if not need:
        return scenes
    items = {str(i): (scenes[i].get("visual") or scenes[i].get("onscreen") or "")[:160] for i in need}
    data = ai.ask(f"""Video: {title}. For each scene give 2-5 English words to search stock video (concrete, visual, no text).
Scenes: {json.dumps(items, ensure_ascii=False)}
Return JSON: {{"<scene number>":"words"}}""", "queries", "cheap")
    for k, v in (data or {}).items():
        if k.isdigit() and int(k) < len(scenes) and isinstance(v, str):
            scenes[int(k)]["q"] = v
    return scenes


def fix_flagged(script_id, flags):
    """Malé AI volanie: opraví len polia, ktoré neprešli automatickou kontrolou (všetky jazyky naraz)."""
    src = db.one("SELECT * FROM scripts WHERE id=?", (script_id,))
    items = {}
    for lang, fields in flags.items():
        t = db.one("SELECT * FROM scripts WHERE idea_id=? AND lang=?", (src["idea_id"], lang))
        items[lang] = {f: t[f] for f in fields}
    prompt = f"""Fix these machine translations of a short video script (problems: {json.dumps(flags, ensure_ascii=False)}).
Keep numbers and brand names, natural native style, similar length to source.
Source ({languages.english(src['lang'])}): {json.dumps({f: src[f] for fs in flags.values() for f in fs}, ensure_ascii=False)}
Translations: {json.dumps(items, ensure_ascii=False)}
Return JSON with the same shape: {{"<lang>":{{"<field>":"fixed text"}}}}"""
    data = ai.ask(prompt, "fix", "cheap")
    for lang, fields in (data or {}).items():
        if lang in flags and isinstance(fields, dict):
            for f, v in fields.items():
                if f in ("title", "voiceover", "description", "caption") and isinstance(v, str) and v.strip():
                    db.run(f"UPDATE scripts SET {f}=?, qa='' WHERE idea_id=? AND lang=?", (v, src["idea_id"], lang))
