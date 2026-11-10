import json
import os
import types

import pytest

from app import ai, content, db, planner, redakcia, scheduler, translate


# ---------- pomocníci ----------
class FakeMT:
    """Falošný DeepL: preloží slovo po slove podľa slovníčka, chránené <span> nechá tak, a ráta volania."""

    def __init__(self, words=None):
        self.calls = 0
        self.chars = 0
        self.words = words or {}

    def __call__(self, p, texts, src, tgt):
        import re
        self.calls += 1
        self.chars += sum(len(t) for t in texts)
        out = []
        for t in texts:
            parts = re.split(r"(<span[^>]*>.*?</span>)", t)
            res = []
            for part in parts:
                if part.startswith("<span"):
                    res.append(part)
                else:
                    for a, b in self.words.items():
                        part = part.replace(a, b)
                    res.append(part)
            out.append(f"[{tgt}]" + "".join(res))
        return out


@pytest.fixture
def mt(monkeypatch):
    f = FakeMT()
    monkeypatch.setattr(translate, "_key", lambda p: "k:fx" if p == "deepl" else "")
    monkeypatch.setattr(translate, "supports", lambda p, lang: True)
    monkeypatch.setattr(translate, "_call", f)
    return f


def make_project(**kw):
    pid = db.run("INSERT INTO projects(name, source_lang, languages, glossary) VALUES(?,?,?,?)",
                 (kw.get("name", "N2N"), "sk", json.dumps(["sk", "cs", "de"]), kw.get("glossary", "N2N")))
    return pid


def make_source(pid, idea=1, title="Tepelné čerpadlo N2N šetrí 40 % nákladov", approved=True):
    iid = db.run("INSERT INTO ideas(project_id, title) VALUES(?,?)", (pid, title))
    sid = db.run("""INSERT INTO scripts(project_id, idea_id, lang, is_source, title, voiceover, description, caption, scenes)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                 (pid, iid, "sk", 1, title, "Prečo tepelné čerpadlo?", "Popis videa", "Príspevok o úspore",
                  json.dumps([{"onscreen": "Úspora 40 %"}])))
    if approved:
        redakcia.approve_source(sid)
    return sid


# ---------- slovník pojmov ----------
def test_term_is_forced_in_target_language(mt):
    pid = make_project()
    redakcia.set_term(pid, "tepelné čerpadlo", "de", "Wärmepumpe")
    sid = make_source(pid)
    redakcia.translate_new(pid, ["de"])
    t = db.one("SELECT * FROM scripts WHERE lang='de'")
    assert "Wärmepumpe" in t["title"]
    assert "Wärmepumpe" in t["voiceover"]  # aj s veľkým písmenom na začiatku vety
    assert "N2N" in t["title"]


def test_check_flags_missing_term():
    why = translate.check("Tepelné čerpadlo je super a šetrí veľa peňazí", "Das Gerät ist super und spart viel Geld",
                          [], {"tepelné čerpadlo": "Wärmepumpe"})
    assert "Wärmepumpe" in why


def test_import_terms_from_table():
    pid = make_project()
    n = redakcia.import_terms(pid, [{"src": "tepelné čerpadlo", "de": "Wärmepumpe", "cs": "tepelné čerpadlo", "xx": "?"}])
    assert n == 2
    assert translate.terms_for(pid, "de") == {"tepelné čerpadlo": "Wärmepumpe"}


# ---------- schválenie a „len nové“ ----------
def test_only_approved_sources_are_translated(mt):
    pid = make_project()
    make_source(pid, approved=False)
    rep = redakcia.translate_new(pid, ["de"])
    assert rep["sources"] == 0 and mt.calls == 0


def test_second_run_costs_nothing_and_change_retranslates(mt):
    pid = make_project()
    sid = make_source(pid)
    r1 = redakcia.translate_new(pid, ["de", "cs"])
    assert r1["translated"] == 2 and mt.calls == 2
    r2 = redakcia.translate_new(pid, ["de", "cs"])
    assert r2["unchanged"] == 2 and r2["translated"] == 0 and mt.calls == 2  # nič nové = žiadne volanie
    before = mt.chars
    db.run("UPDATE scripts SET caption='Nový príspevok' WHERE id=?", (sid,))
    r3 = redakcia.translate_new(pid, ["de"])
    assert r3["translated"] == 1
    # zmenil sa len jeden text; zvyšok ide z pamäte prekladov, takže sa platí len za nový text
    assert mt.chars - before == len("Nový príspevok")


def test_retranslation_resets_review(mt):
    pid = make_project()
    sid = make_source(pid)
    redakcia.translate_new(pid, ["de"])
    t = db.one("SELECT id FROM scripts WHERE lang='de'")
    redakcia.review(t["id"], True)
    db.run("UPDATE scripts SET title='Iný názov' WHERE id=?", (sid,))
    redakcia.translate_new(pid, ["de"])
    assert db.one("SELECT review FROM scripts WHERE lang='de'")["review"] == ""


def test_default_langs_come_from_countries():
    assert redakcia.langs_for(["CZ", "AT", "PL", "HU", "SK"]) == ["cs", "de", "pl", "hu"]


# ---------- oprava označeného jednou dávkou ----------
def test_flagged_go_to_one_batch_on_api(mt, monkeypatch):
    monkeypatch.setenv("SM_AI_BACKEND", "api")
    mt.words = {"40": "41"}  # pokazí čísla -> kontrola to označí
    sent = {}

    def fake_submit(prompts, purpose, kind="cheap", meta=None):
        sent.update(prompts=prompts, kind=kind, meta=meta)
        return "batch_1"
    monkeypatch.setattr(ai, "submit_batch", fake_submit)
    pid = make_project()
    make_source(pid)
    make_source(pid, title="Druhé video so 40 % úsporou")
    rep = redakcia.translate_new(pid, ["de", "cs"])
    assert rep["batch"] == "batch_1"
    assert len(sent["prompts"]) == 2 and sent["kind"] == "cheap"  # jedna dávka, lacný model


def test_collect_fixes_applies_results(mt, monkeypatch):
    pid = make_project()
    sid = make_source(pid)
    redakcia.translate_new(pid, ["de"])
    flags = {"de": {"title": "čísla"}}
    db.run("INSERT INTO ai_batches(id,purpose,meta) VALUES(?,?,?)", ("b1", "fix", json.dumps({"flags": {str(sid): flags}})))
    monkeypatch.setattr(ai, "batch_results", lambda bid: {f"fix-{sid}": {"de": {"title": "Opravený názov 40 %"}}})
    assert redakcia.collect_fixes() == {"fixed": 1}
    assert db.one("SELECT title FROM scripts WHERE lang='de'")["title"] == "Opravený názov 40 %"


def test_api_params_are_cheap():
    p = ai._api_params("claude-haiku-5-5", "ahoj")
    assert p["thinking"] == {"type": "disabled"} and p["output_config"]["effort"] == "low"
    assert p["system"][0]["cache_control"]["type"] == "ephemeral"
    assert ai.api_model("haiku") == "claude-haiku-5-5"


def test_daily_cap_stops_ai(monkeypatch):
    monkeypatch.setenv("SM_AI_BACKEND", "api")
    db.set_setting("ai_daily_token_cap", 1000)
    db.run("INSERT INTO ai_log(purpose,model,input_tokens,output_tokens) VALUES('x','m',900,200)")
    with pytest.raises(ai.AIError):
        ai.ask("nový prompt", "test", "cheap")


def test_api_backend_uses_api_not_cli(monkeypatch):
    monkeypatch.setenv("SM_AI_BACKEND", "api")
    calls = []
    monkeypatch.setattr(ai, "_ask_api", lambda prompt, purpose, model: calls.append(model) or {"ok": 1})
    monkeypatch.setattr(ai, "find_claude", lambda: (_ for _ in ()).throw(AssertionError("CLI sa nesmie použiť")))
    assert ai.ask("p", "t", "cheap") == {"ok": 1}
    assert ai.ask("p", "t", "cheap") == {"ok": 1}  # druhýkrát z cache
    assert calls == ["claude-haiku-5-5"]


# ---------- vzorka ----------
def test_sample_has_all_flagged_and_some_per_lang(mt):
    pid = make_project()
    for i in range(5):
        make_source(pid, title=f"Video {i} o úspore")
    redakcia.translate_new(pid, ["de", "cs"])
    t = db.one("SELECT id FROM scripts WHERE lang='cs'")
    db.run("UPDATE scripts SET qa='{\"title\":\"čísla\"}' WHERE id=?", (t["id"],))
    items = redakcia.sample(pid, per_lang=2, seed=1)
    langs = [i["lang"] for i in items]
    assert t["id"] in [i["id"] for i in items]
    assert langs.count("de") == 2
    assert all(i["countries"] for i in items)


def test_lang_released_only_after_good_sample(mt):
    pid = make_project()
    make_source(pid)
    redakcia.translate_new(pid, ["de"])
    assert not redakcia.lang_status(pid)["de"]["ready"]
    t = db.one("SELECT id FROM scripts WHERE lang='de'")
    redakcia.review(t["id"], True)
    assert redakcia.lang_status(pid)["de"]["ready"]
    redakcia.review(t["id"], False, "zlý tón")
    assert not redakcia.lang_status(pid)["de"]["ready"]


# ---------- plán nasucho a režim nasucho ----------
def _video_and_account(pid, lang):
    sc = db.one("SELECT id FROM scripts WHERE lang=?", (lang,))
    vid = db.run("INSERT INTO videos(project_id, lang, title, file_path, script_id) VALUES(?,?,?,?,?)",
                 (pid, lang, "Video DE", "/tmp/x.mp4", sc["id"]))
    acc = db.run("INSERT INTO accounts(platform, name, project_id, lang, country) VALUES(?,?,?,?,?)",
                 ("youtube", "N2N Deutschland", pid, lang, "AT"))
    return vid, acc


def test_dry_plan_writes_nothing(mt, monkeypatch):
    from app import stats
    monkeypatch.setattr(stats, "best_hours", lambda a, n: ([10, 18], "test"))
    monkeypatch.setattr(stats, "winners", lambda pid: [])
    pid = make_project()
    make_source(pid)
    redakcia.translate_new(pid, ["de"])
    _video_and_account(pid, "de")
    res = redakcia.dry_plan(pid, days=3)
    assert res["items"] and res["dry"]
    assert db.one("SELECT COUNT(*) n FROM posts")["n"] == 0
    assert all(i["blocked"] for i in res["items"])  # preklad ešte neprešiel vzorkou
    text = redakcia.plan_text(res)
    assert "nič sa nezapísalo" in text and "čaká na kontrolu" in text


def test_dry_run_never_uploads(monkeypatch):
    monkeypatch.setenv("SM_DRY_RUN", "1")
    pid = make_project()
    vid = db.run("INSERT INTO videos(project_id, lang, title, file_path) VALUES(?,?,?,?)", (pid, "de", "V", "/tmp/x.mp4"))
    acc = db.run("INSERT INTO accounts(platform, name) VALUES('youtube','A')")
    db.run("INSERT INTO posts(video_id, account_id, scheduled_at, status) VALUES(?,?,'2000-01-01 00:00:00','queued')", (vid, acc))
    monkeypatch.setitem(scheduler.UPLOADERS, "youtube", lambda *a: (_ for _ in ()).throw(AssertionError("nahrávanie!")))
    scheduler.tick()
    scheduler.process_one(db.one("SELECT * FROM posts"))
    assert db.one("SELECT status FROM posts")["status"] == "queued"


def test_dry_run_blocks_comment_and_dm_replies(monkeypatch):
    monkeypatch.setenv("SM_DRY_RUN", "1")
    from app import comments, messages
    with pytest.raises(RuntimeError):
        comments.send([1])
    with pytest.raises(RuntimeError):
        messages.send([1])


# ---------- schvaľovacia schránka ----------
def test_inbox_off_without_key(monkeypatch):
    monkeypatch.delenv("OS_INBOX_KEY", raising=False)
    pid = make_project()
    make_source(pid, approved=False)
    assert redakcia.send_for_approval(pid)["sent"] == 0


def test_inbox_roundtrip_with_edit(monkeypatch):
    pid = make_project()
    sid = make_source(pid, approved=False)
    calls = []

    def fake(payload):
        calls.append(payload)
        if payload["action"] == "add":
            return {"ok": True, "approval": {"id": "apr_1", "status": "pending"}}
        edited = payload and calls[0]["body"].replace("Popis videa", "Upravený popis")
        return {"ok": True, "approvals": [{"id": "apr_1", "status": "approved", "text": edited}]}
    monkeypatch.setattr(redakcia, "_inbox", fake)
    assert redakcia.send_for_approval(pid)["sent"] == 1
    assert redakcia.send_for_approval(pid)["sent"] == 0  # už čaká, neposiela dvojičku
    assert calls[0]["kind"] == "post" and calls[0]["dedupeKey"].startswith("social-manager:script:")
    assert redakcia.sync_approvals() == {"approved": 1, "rejected": 0}
    s = db.one("SELECT * FROM scripts WHERE id=?", (sid,))
    assert s["approved_at"] and s["description"] == "Upravený popis"
