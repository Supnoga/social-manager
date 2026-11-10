"""AI: na Macu cez Claude Code CLI (osobný Max plán), na serveri cez firemné API (SM_AI_BACKEND=api).

Firemná automatika nemá bežať na osobnom Max pláne. Na serveri preto ide AI cez API kľúč firmy:
- najlacnejší model (Haiku 5.5) na preklady a opravy, Sonnet 5.5 len na tvorbu,
- dávky (Batch API) za polovičnú cenu, kde sa nečaká na odpoveď,
- denný strop tokenov (ai_daily_token_cap), po ňom AI stojí do ďalšieho dňa.

Šetrenie tokenov:
- vlastný krátky systémový prompt (namiesto veľkého predvoleného), žiadne nástroje, žiadne MCP
  -> réžia cca 2-3 tisíc tokenov na volanie namiesto desiatok tisíc,
- dávkovanie (veľa nápadov / jazykov v jednom volaní),
- lacnejší model (haiku) na preklady, silnejší (sonnet) na vymýšľanie,
- cache: rovnaká požiadavka sa druhýkrát neplatí vôbec,
- krátke zhrnutie projektu namiesto celej stratégie v každej požiadavke.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import db

SYSTEM = ("You are a senior social media strategist and short-form video scriptwriter. "
          "Answer ONLY with valid minified JSON matching the requested shape. No markdown, no comments.")


class NeedManual(Exception):
    """AI nie je dostupná cez CLI -> appka ukáže prompt na skopírovanie do claude.ai."""

    def __init__(self, prompt, purpose):
        super().__init__("manual")
        self.prompt = prompt
        self.purpose = purpose


class AIError(Exception):
    pass


# skratky z nastavení -> presné modely API
API_MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
DEFAULT_DAILY_CAP = 300_000  # tokenov denne (vstup + výstup) pre API; pri Haiku je to rádovo pár centov


def backend():
    """'api' = firemné API (server), 'cli' = Claude Code s Max plánom (Mac)."""
    return (os.environ.get("SM_AI_BACKEND") or db.get_setting("ai_backend", "cli") or "cli").strip().lower()


def api_model(short):
    return API_MODELS.get(short, short)


def _api_params(model, prompt, max_tokens=4000):
    """Krátke, lacné volanie: bez premýšľania (Haiku) alebo s nízkym úsilím, systémový prompt sa cache-uje."""
    p = {"model": model, "max_tokens": max_tokens,
         "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
         "messages": [{"role": "user", "content": prompt}],
         "output_config": {"effort": "low"}}
    if model.startswith("claude-haiku"):
        p["thinking"] = {"type": "disabled"}
    return p


def tokens_today():
    r = db.one("SELECT COALESCE(SUM(input_tokens),0)+COALESCE(SUM(output_tokens),0) n FROM ai_log "
               "WHERE cached=0 AND ts >= datetime('now','localtime','start of day')")
    return (r or {}).get("n", 0) or 0


def _check_cap(extra=0):
    cap = int(db.get_setting("ai_daily_token_cap", DEFAULT_DAILY_CAP) or DEFAULT_DAILY_CAP)
    if tokens_today() + extra > cap:
        raise AIError(f"Denný strop AI ({cap:,} tokenov) je minutý, AI pokračuje zajtra.".replace(",", " "))


def _client():
    try:
        import anthropic
    except ImportError:
        raise AIError("Chýba knižnica anthropic (pip install anthropic).")
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise AIError("Na serveri chýba ANTHROPIC_API_KEY (patrí do súboru s nastaveniami servera, nie do kódu).")
    return anthropic.Anthropic()


def _text(msg):
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _ask_api(prompt, purpose, model):
    _check_cap()
    import anthropic
    try:
        msg = _client().messages.create(**_api_params(model, prompt))
    except anthropic.APIStatusError as e:
        _log(purpose, model, ok=0, note=str(e)[:400])
        raise AIError(f"Claude API ({e.status_code}): {str(e)[:300]}")
    except anthropic.APIConnectionError as e:
        _log(purpose, model, ok=0, note=str(e)[:400])
        raise AIError("Claude API nie je dostupné, skús neskôr.")
    u = msg.usage
    it = (u.input_tokens or 0) + (getattr(u, "cache_creation_input_tokens", 0) or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0)
    _log(purpose, model, it, u.output_tokens or 0)
    if msg.stop_reason == "refusal":
        raise AIError("Claude túto požiadavku odmietol.")
    return extract_json(_text(msg))


# ---------- dávky (Batch API, polovičná cena) ----------
def submit_batch(prompts, purpose, kind="cheap", meta=None):
    """prompts: {id: prompt}. Pošle všetko naraz ako jednu dávku. Vráti id dávky (alebo None, ak nič netreba)."""
    if not prompts:
        return None
    if backend() != "api":
        raise AIError("Dávky idú len cez firemné API (server).")
    _check_cap()
    model = api_model(models()[kind])
    reqs = [{"custom_id": str(cid)[:64], "params": _api_params(model, pr)} for cid, pr in prompts.items()]
    b = _client().messages.batches.create(requests=reqs)
    db.run("INSERT INTO ai_batches(id,purpose,meta) VALUES(?,?,?)",
           (b.id, purpose, json.dumps({**(meta or {}), "model": model}, ensure_ascii=False)))
    return b.id


def batch_results(batch_id):
    """Ak je dávka hotová, vráti {id: JSON odpoveď alebo None}. Ak ešte beží, vráti None."""
    c = _client()
    b = c.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        return None
    row = db.one("SELECT * FROM ai_batches WHERE id=?", (batch_id,)) or {}
    model = json.loads(row.get("meta") or "{}").get("model", "")
    out = {}
    for r in c.messages.batches.results(batch_id):
        if r.result.type != "succeeded":
            out[r.custom_id] = None
            continue
        m = r.result.message
        u = m.usage
        _log(row.get("purpose", "batch"), model, (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0),
             u.output_tokens or 0, note="dávka")
        try:
            out[r.custom_id] = extract_json(_text(m))
        except Exception:
            out[r.custom_id] = None
    db.run("UPDATE ai_batches SET status='done', done_at=datetime('now','localtime') WHERE id=?", (batch_id,))
    return out


def find_claude():
    custom = db.get_setting("claude_path", "")
    if custom and Path(custom).exists():
        return custom
    p = shutil.which("claude")
    if p:
        return p
    home = Path.home()
    for c in [home / ".local/bin/claude", home / ".local/bin/claude.exe", home / ".claude/local/claude",
              home / "AppData/Roaming/npm/claude.cmd", home / ".npm-global/bin/claude",
              Path("/usr/local/bin/claude"), Path("/opt/homebrew/bin/claude")]:
        if c.exists():
            return str(c)
    return None


def status():
    path = find_claude()
    info = {"cli_found": bool(path), "path": path, "mode": db.get_setting("ai_mode", "auto"),
            "logged_in": None, "version": None}
    if path:
        try:
            out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL, start_new_session=True)
            info["version"] = out.stdout.strip()
        except Exception as e:
            info["version"] = f"chyba: {e}"
    return info


def models():
    return {
        "creative": db.get_setting("model_creative", "sonnet"),
        "cheap": db.get_setting("model_cheap", "haiku"),
    }


def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        raise AIError("AI nevrátila JSON: " + text[:300])
    s = min(starts)
    end_char = "}" if text[s] == "{" else "]"
    e = text.rfind(end_char)
    return json.loads(text[s:e + 1])


def _log(purpose, model, it=0, ot=0, cached=0, ok=1, note=""):
    db.run("INSERT INTO ai_log(purpose,model,input_tokens,output_tokens,cached,ok,note) VALUES(?,?,?,?,?,?,?)",
           (purpose, model, it, ot, cached, ok, note[:500]))


def ask(prompt, purpose, kind="creative", use_cache=True, timeout=600):
    """Pošle prompt Claudovi a vráti JSON. kind: creative|cheap."""
    model = models()[kind]
    h = hashlib.sha256(f"{model}|{SYSTEM}|{prompt}".encode()).hexdigest()
    if use_cache:
        c = db.one("SELECT response FROM ai_cache WHERE hash=?", (h,))
        if c:
            _log(purpose, model, cached=1)
            return json.loads(c["response"])

    if backend() == "api":
        data = _ask_api(prompt, purpose, api_model(model))
        db.run("INSERT OR REPLACE INTO ai_cache(hash,response) VALUES(?,?)", (h, json.dumps(data, ensure_ascii=False)))
        return data

    path = find_claude()
    mode = db.get_setting("ai_mode", "auto")
    if mode == "manual" or not path:
        raise NeedManual(SYSTEM + "\n\n" + prompt, purpose)

    env = dict(os.environ)
    # Dôležité: bez API kľúča -> Claude Code použije prihlásenie do Max plánu, nič sa neplatí navyše.
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    cmd = [path, "-p", "--model", model, "--system-prompt", SYSTEM, "--tools", "",
           "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence",
           "--output-format", "json"]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout,
                           env=env, cwd=str(db.DATA_DIR), encoding="utf-8", start_new_session=True)
    except subprocess.TimeoutExpired:
        _log(purpose, model, ok=0, note="timeout")
        raise AIError("Claude neodpovedal včas, skús znova.")
    out = (r.stdout or "").strip()
    try:
        meta = json.loads(out)
    except Exception:
        _log(purpose, model, ok=0, note=(r.stderr or out)[:400])
        msg = (r.stderr or out or "").strip()
        if "login" in msg.lower() or "auth" in msg.lower():
            raise AIError("Claude Code nie je prihlásený. Otvor terminál a spusti: claude  (a prihlás sa Max účtom).")
        raise AIError("Chyba Claude CLI: " + msg[:400])
    if meta.get("is_error"):
        _log(purpose, model, ok=0, note=str(meta.get("result"))[:400])
        res = str(meta.get("result", ""))
        if "limit" in res.lower():
            raise AIError("Dosiahnutý limit Max plánu. Počkaj na obnovenie limitu (zvyčajne pár hodín).")
        raise AIError("Claude: " + res[:400])
    u = meta.get("usage", {}) or {}
    it = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
    ot = u.get("output_tokens", 0)
    data = extract_json(meta.get("result", ""))
    _log(purpose, model, it, ot)
    db.run("INSERT OR REPLACE INTO ai_cache(hash,response) VALUES(?,?)", (h, json.dumps(data, ensure_ascii=False)))
    return data


def usage_summary():
    tot = db.one("SELECT COUNT(*) calls, COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp, "
                 "COALESCE(SUM(cached),0) cached FROM ai_log WHERE ts >= datetime('now','localtime','-1 day')")
    week = db.one("SELECT COUNT(*) calls, COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp "
                  "FROM ai_log WHERE ts >= datetime('now','localtime','-7 day')")
    last = db.q("SELECT ts,purpose,model,input_tokens,output_tokens,cached,ok,note FROM ai_log ORDER BY id DESC LIMIT 30")
    return {"day": tot, "week": week, "last": last}
