"""Marketingová redakcia: schválený zdroj -> verzie pre krajiny -> kontrola vzorky -> plán publikovania nasucho.

Postup (všetko beží na serveri, nie na Macu):
1. Zdroj (slovenský scenár) sa schváli: ručne v appke alebo v schvaľovacej schránke N2N OS (ASAP › Na schválenie).
2. Preklad len schválených zdrojov a len toho, čo je nové. Najprv bezplatný strojový prekladač (DeepL a spol.)
   so slovníkom pojmov pre krajinu a pamäťou prekladov; čo už raz bolo preložené, nič nestojí.
3. Čo neprejde automatickou kontrolou (čísla, dĺžka, chýbajúci pojem), opraví AI: najlacnejší model, jednou dávkou
   (Batch API, polovičná cena). Bez API ostane označené na ručnú kontrolu.
4. Kontrola vzorky: z každého jazyka pár náhodných prekladov + všetko označené. Človek dá „dobré“ / „zlé“.
5. Plán publikovania nasucho: ukáže, čo by kam a kedy išlo, nič nezapíše a nič nepublikuje.

Ostré publikovanie táto časť nerobí. Na serveri je navyše zapnutý režim nasucho (SM_DRY_RUN=1),
v ktorom plánovač nič nenahráva.
"""
import argparse
import json
import os
import random
import sys

import httpx

from . import ai, db, languages, translate

# predvolené cieľové krajiny pre prvé kolo (Oliverove hlavné trhy v okolí; dá sa zmeniť nastavením redakcia_countries)
DEFAULT_COUNTRIES = ["CZ", "AT", "PL", "HU"]
INBOX_URL = "https://europe-west1-asapn2n.cloudfunctions.net/osInbox"


# ---------- nastavenie ----------
def countries():
    v = db.get_setting("redakcia_countries", None) or os.environ.get("SM_COUNTRIES", "")
    if isinstance(v, str):
        v = [x.strip().upper() for x in v.split(",") if x.strip()]
    return v or list(DEFAULT_COUNTRIES)


def langs_for(country_codes, source_lang="sk"):
    out = []
    for c in country_codes:
        for l in languages.COUNTRY_LANGS.get(c, [])[:1]:  # prvý jazyk krajiny
            if l != source_lang and l not in out:
                out.append(l)
    return out


# ---------- slovník pojmov ----------
def set_term(project_id, src, lang, target, note=""):
    src, target = (src or "").strip(), (target or "").strip()
    if not src or not lang:
        raise ValueError("Pojem aj jazyk sú povinné.")
    if not target:
        db.run("DELETE FROM terms WHERE project_id=? AND src=? AND lang=?", (project_id, src, lang))
        return
    db.run("""INSERT INTO terms(project_id,src,lang,target,note) VALUES(?,?,?,?,?)
              ON CONFLICT(project_id,src,lang) DO UPDATE SET target=excluded.target, note=excluded.note""",
           (project_id, src, lang, target, note))


def list_terms(project_id):
    return db.q("SELECT src, lang, target, note FROM terms WHERE project_id=? ORDER BY src, lang", (project_id,))


def import_terms(project_id, rows):
    """rows: [{"src": "tepelné čerpadlo", "de": "Wärmepumpe", "cs": "tepelné čerpadlo", ...}] (napr. z tabuľky)."""
    n = 0
    for r in rows:
        src = (r.get("src") or "").strip()
        for lang, target in r.items():
            if lang in ("src", "note") or lang not in languages.LANGUAGES:
                continue
            set_term(project_id, src, lang, target, r.get("note", ""))
            n += 1
    return n


# ---------- 1. schválenie zdroja ----------
def approve_source(script_id, approved=True):
    s = db.one("SELECT id, is_source FROM scripts WHERE id=?", (script_id,))
    if not s or not s["is_source"]:
        raise ValueError("Schváliť sa dá len zdrojový scenár.")
    db.run("UPDATE scripts SET approved_at=CASE WHEN ? THEN datetime('now','localtime') ELSE '' END WHERE id=?",
           (1 if approved else 0, script_id))


def _inbox_body(s):
    return f"Názov:\n{s['title']}\n\nText k videu:\n{s['voiceover']}\n\nPopis:\n{s['description']}\n\nPríspevok:\n{s['caption']}"


def _inbox(payload):
    key = os.environ.get("OS_INBOX_KEY", "").strip()
    if not key:
        return None
    r = httpx.post(os.environ.get("OS_INBOX_URL", INBOX_URL), json=payload, headers={"x-os-key": key}, timeout=30)
    r.raise_for_status()
    return r.json()


def send_for_approval(project_id):
    """Neschválené zdroje pošle do schvaľovacej schránky N2N OS (len ak je na serveri kľúč OS_INBOX_KEY).
    Schránka nič neodosiela, len zbiera Oliverove rozhodnutia."""
    pend = db.get_setting("redakcia_inbox", {}) or {}
    sent = 0
    for s in db.q("SELECT * FROM scripts WHERE project_id=? AND is_source=1 AND COALESCE(approved_at,'')=''", (project_id,)):
        h = translate.source_hash(s)
        if pend.get(str(s["id"]), {}).get("h") == h:
            continue
        res = _inbox({"action": "add", "kind": "post", "title": f"Video na preklad: {s['title']}"[:140],
                      "body": _inbox_body(s), "summary": "Po schválení sa pripravia verzie pre ďalšie krajiny.",
                      "dedupeKey": f"social-manager:script:{s['id']}:{h[:12]}", "level": "B"})
        if not res:
            return {"sent": 0, "note": "Schránka nie je napojená (chýba OS_INBOX_KEY) – schváľ zdroj v appke."}
        pend[str(s["id"])] = {"id": res["approval"]["id"], "h": h}
        sent += 1
    db.set_setting("redakcia_inbox", pend)
    return {"sent": sent}


def sync_approvals():
    """Prečíta rozhodnutia zo schránky: schválené zdroje označí, úpravy textu prevezme, zamietnuté nechá tak."""
    pend = db.get_setting("redakcia_inbox", {}) or {}
    if not pend:
        return {"approved": 0, "rejected": 0}
    res = _inbox({"action": "get", "ids": [v["id"] for v in pend.values()]})
    if not res:
        return {"approved": 0, "rejected": 0}
    by_id = {a["id"]: a for a in res.get("approvals", [])}
    ok = bad = 0
    for sid, v in list(pend.items()):
        a = by_id.get(v["id"])
        if not a or a.get("status") == "pending":
            continue
        if a.get("status") == "approved":
            if a.get("text"):
                _apply_edited(int(sid), a["text"])
            approve_source(int(sid))
            ok += 1
        else:
            bad += 1
        pend.pop(sid)
    db.set_setting("redakcia_inbox", pend)
    return {"approved": ok, "rejected": bad}


def _apply_edited(script_id, text):
    labels = {"Názov:": "title", "Text k videu:": "voiceover", "Popis:": "description", "Príspevok:": "caption"}
    cur, parts = None, {}
    for line in text.splitlines():
        if line.strip() in labels:
            cur = labels[line.strip()]
            parts[cur] = []
        elif cur:
            parts[cur].append(line)
    for f, lines in parts.items():
        db.run(f"UPDATE scripts SET {f}=? WHERE id=?", ("\n".join(lines).strip(), script_id))


# ---------- 2. + 3. preklad nového a oprava označeného ----------
def translate_new(project_id, langs=None):
    """Preloží všetky schválené zdroje projektu do jazykov krajín. Prekladá len nové alebo zmenené."""
    if not translate.any_enabled():
        raise RuntimeError("Nie je nastavený žiadny bezplatný prekladač (DeepL Free a pod.).")
    proj = db.one("SELECT * FROM projects WHERE id=?", (project_id,))
    if not proj:
        raise ValueError("Projekt neexistuje.")
    langs = langs or langs_for(countries(), proj.get("source_lang") or "sk")
    report = {"project": proj["name"], "langs": langs, "sources": 0, "translated": 0, "unchanged": 0,
              "missing": {}, "flagged": {}, "batch": None}
    for s in db.q("SELECT id, title FROM scripts WHERE project_id=? AND is_source=1 AND COALESCE(approved_at,'')!=''",
                  (project_id,)):
        report["sources"] += 1
        before = {r["lang"]: r["src_hash"] for r in db.q(
            "SELECT lang, src_hash FROM scripts WHERE idea_id=(SELECT idea_id FROM scripts WHERE id=?)", (s["id"],))}
        done, rest, flags, _ = translate.machine_translate(s["id"], langs, skip_unchanged=True)
        h = translate.source_hash(db.one("SELECT * FROM scripts WHERE id=?", (s["id"],)))
        for l in done:
            if before.get(l) == h:
                report["unchanged"] += 1
            else:
                report["translated"] += 1
        if rest:
            report["missing"][s["id"]] = rest
        for l, why in flags.items():
            db.run("UPDATE scripts SET qa=? WHERE idea_id=(SELECT idea_id FROM scripts WHERE id=?) AND lang=?",
                   (json.dumps(why, ensure_ascii=False), s["id"], l))
        if flags:
            report["flagged"][s["id"]] = flags
    if report["flagged"] and ai.backend() == "api":
        report["batch"] = submit_fixes(report["flagged"])
    return report


def submit_fixes(flagged):
    """Všetky označené preklady jednou dávkou (Batch API = polovičná cena, výsledok do pár hodín)."""
    from . import content
    prompts = {f"fix-{sid}": content.fix_prompt(sid, fl) for sid, fl in flagged.items()}
    return ai.submit_batch(prompts, "fix", "cheap", meta={"flags": {str(k): v for k, v in flagged.items()}})


def collect_fixes():
    """Vyzdvihne hotové dávky a opravy zapíše. Bezpečné spúšťať často (napr. každých 15 minút)."""
    from . import content
    fixed = 0
    for b in db.q("SELECT * FROM ai_batches WHERE status='pending' AND purpose='fix'"):
        res = ai.batch_results(b["id"])
        if res is None:
            continue
        flags = json.loads(b["meta"] or "{}").get("flags", {})
        for cid, data in res.items():
            sid = cid.split("-", 1)[1]
            if data and sid in flags:
                fixed += content.apply_fix(int(sid), flags[sid], data)
    return {"fixed": fixed}


# ---------- 4. kontrola vzorky ----------
def sample(project_id, per_lang=2, seed=None):
    """Na kontrolu: všetko označené automatickou kontrolou + pár náhodných prekladov z každého jazyka."""
    rows = db.q("""SELECT t.id, t.lang, t.title, t.caption, t.description, t.qa, t.review, s.id src_id, s.title src_title,
                   s.caption src_caption, s.description src_description FROM scripts t
                   JOIN scripts s ON s.idea_id=t.idea_id AND s.is_source=1
                   WHERE t.project_id=? AND t.is_source=0 AND COALESCE(t.review,'')=''""", (project_id,))
    rnd = random.Random(seed)
    out, by_lang = [], {}
    for r in rows:
        (out if r["qa"] else by_lang.setdefault(r["lang"], [])).append(r)
    for lang, items in sorted(by_lang.items()):
        out.extend(rnd.sample(items, min(per_lang, len(items))))
    for r in out:
        r["lang_name"] = languages.name(r["lang"])
        r["countries"] = [languages.COUNTRY_NAMES.get(c, c) for c, ls in languages.COUNTRY_LANGS.items() if ls[:1] == [r["lang"]]]
    return out


def review(script_id, ok, note=""):
    t = db.one("SELECT id, is_source FROM scripts WHERE id=?", (script_id,))
    if not t or t["is_source"]:
        raise ValueError("Posúdiť sa dá len preklad.")
    db.run("UPDATE scripts SET review=?, review_note=? WHERE id=?", ("ok" if ok else "bad", note or "", script_id))


def lang_status(project_id):
    """Pre každý jazyk: koľko prekladov je, koľko prešlo vzorkou, koľko je zlých. Jazyk je pustený, keď má
    aspoň jeden dobrý posudok, žiadny zlý a nič označené automatickou kontrolou."""
    out = {}
    for r in db.q("""SELECT lang, COUNT(*) n, SUM(review='ok') ok, SUM(review='bad') bad, SUM(COALESCE(qa,'')!='') flagged
                     FROM scripts WHERE project_id=? AND is_source=0 GROUP BY lang""", (project_id,)):
        r["ready"] = bool(r["ok"]) and not r["bad"] and not r["flagged"]
        out[r["lang"]] = r
    return out


# ---------- 5. plán publikovania nasucho ----------
def dry_plan(project_id, days=7):
    from . import planner
    res = planner.plan_week([project_id], days=days, dry=True)
    st = lang_status(project_id)
    for it in res.get("items", []):
        s = st.get(it.get("lang") or "")
        it["blocked"] = bool(it.get("lang")) and it["lang"] != (db.one("SELECT source_lang FROM projects WHERE id=?",
                                                                        (project_id,)) or {}).get("source_lang") \
            and not (s and s["ready"])
    res["lang_status"] = st
    return res


# ---------- výstup pre ľudí ----------
def report_text(rep):
    lines = [f"Projekt {rep['project']}: {rep['sources']} schválených videí, jazyky {', '.join(rep['langs'])}.",
             f"Preložené nanovo: {rep['translated']}, bez zmeny (zadarmo): {rep['unchanged']}."]
    if rep["flagged"]:
        n = sum(len(v) for v in rep["flagged"].values())
        lines.append(f"Na opravu označených prekladov: {n}" + (" (poslané AI jednou dávkou)." if rep["batch"] else " (čakajú na ručnú kontrolu)."))
    if rep["missing"]:
        lines.append("Nepreložené (prekladač nemal voľný limit alebo jazyk): " +
                     "; ".join(f"video {k}: {', '.join(v)}" for k, v in rep["missing"].items()))
    return "\n".join(lines)


def plan_text(res):
    lines = [f"Plán nasucho: {len(res.get('items', []))} príspevkov (nič sa nezapísalo ani nepublikovalo)."]
    for it in res.get("items", [])[:200]:
        mark = "  [čaká na kontrolu prekladu]" if it.get("blocked") else ""
        lines.append(f"{it['when'][:16]}  {it['platform']:<9} {it['account']}  ({it.get('lang') or '-'})  {it['title']}{mark}")
    if res.get("empty"):
        lines.append("Bez obsahu: " + ", ".join(res["empty"]))
    return "\n".join(lines)


# ---------- rozhranie pre appku ----------
from fastapi import APIRouter, Body  # noqa: E402

router = APIRouter()


@router.get("/api/redakcia/{pid}/terms")
def api_terms(pid: int):
    return {"terms": list_terms(pid), "countries": countries()}


@router.post("/api/redakcia/{pid}/terms")
def api_set_terms(pid: int, data: dict = Body(...)):
    if "rows" in data:
        return {"saved": import_terms(pid, data["rows"])}
    set_term(pid, data.get("src"), data.get("lang"), data.get("target"), data.get("note", ""))
    return {"ok": True}


@router.post("/api/redakcia/source/{sid}/approve")
def api_approve(sid: int, data: dict = Body(default={})):
    approve_source(sid, data.get("approved", True))
    return {"ok": True}


@router.post("/api/redakcia/{pid}/translate")
def api_translate(pid: int, data: dict = Body(default={})):
    rep = translate_new(pid, data.get("langs") or None)
    return {**rep, "text": report_text(rep)}


@router.get("/api/redakcia/{pid}/sample")
def api_sample(pid: int, per_lang: int = 2):
    return {"items": sample(pid, per_lang), "status": lang_status(pid)}


@router.post("/api/redakcia/review/{tid}")
def api_review(tid: int, data: dict = Body(...)):
    review(tid, bool(data.get("ok")), data.get("note", ""))
    return {"ok": True}


@router.get("/api/redakcia/{pid}/plan")
def api_plan(pid: int, days: int = 7):
    res = dry_plan(pid, days)
    return {**res, "text": plan_text(res)}


def background():
    """Na serveri: každých 15 minút vyzdvihne hotové AI dávky (opravy prekladov). Nič nepublikuje."""
    import threading
    import time
    import traceback

    def loop():
        while True:
            try:
                if ai.backend() == "api" and db.one("SELECT 1 FROM ai_batches WHERE status='pending'"):
                    collect_fixes()
            except Exception:
                traceback.print_exc()
            time.sleep(900)
    threading.Thread(target=loop, daemon=True).start()


# ---------- spúšťanie na serveri ----------
def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m app.redakcia", description="Marketingová redakcia (beh na serveri)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("schvalenie", "preklad", "opravy", "vzorka", "plan", "kolo"):
        sp = sub.add_parser(name)
        sp.add_argument("--projekt", type=int, required=name not in ("opravy",))
        sp.add_argument("--jazyky", default="")
        sp.add_argument("--dni", type=int, default=7)
    a = p.parse_args(argv)
    langs = [x.strip() for x in a.jazyky.split(",") if x.strip()] or None
    if a.cmd == "schvalenie":
        print(json.dumps({**sync_approvals(), **send_for_approval(a.projekt)}, ensure_ascii=False))
    elif a.cmd == "preklad":
        print(report_text(translate_new(a.projekt, langs)))
    elif a.cmd == "opravy":
        print(json.dumps(collect_fixes(), ensure_ascii=False))
    elif a.cmd == "vzorka":
        for r in sample(a.projekt):
            print(f"[{r['id']}] {r['lang_name']} ({', '.join(r['countries'])}){'  !' + r['qa'] if r['qa'] else ''}\n"
                  f"   SK: {r['src_title']}\n   →  {r['title']}")
    elif a.cmd == "plan":
        print(plan_text(dry_plan(a.projekt, a.dni)))
    elif a.cmd == "kolo":  # celé kolo naraz, napr. z cronu každú hodinu
        print(json.dumps(sync_approvals(), ensure_ascii=False))
        print(json.dumps(send_for_approval(a.projekt), ensure_ascii=False))
        print(json.dumps(collect_fixes(), ensure_ascii=False) if ai.backend() == "api" else "")
        print(report_text(translate_new(a.projekt, langs)))
        print(plan_text(dry_plan(a.projekt, a.dni)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
