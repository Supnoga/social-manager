"""AI cez Claude Code CLI = používa tvoj Claude Max plán (nie platené API).

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
        "premium": db.get_setting("model_premium", "opus"),  # len scenáre dlhých videí (nesú najviac)
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

    path = find_claude()
    mode = db.get_setting("ai_mode", "auto")
    if mode == "manual" or not path:
        raise NeedManual(SYSTEM + "\n\n" + prompt, purpose)

    env = dict(os.environ)
    # Dôležité: bez API kľúča -> Claude Code použije prihlásenie do Max plánu, nič sa neplatí navyše.
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    # Premýšľanie modelu sa ráta do limitu Max plánu a pri scenári tvorilo ~80 % spotreby: stačí stredné (lacné úlohy nízke).
    env["CLAUDE_CODE_EFFORT_LEVEL"] = "low" if kind == "cheap" else (db.get_setting("ai_effort", "medium") or "medium")
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
    # poznámka: koľko znakov má viditeľná odpoveď (rozdiel oproti výstupným tokenom = premýšľanie modelu) a použité úsilie
    _log(purpose, model, it, ot, note=f"chars={len(str(meta.get('result', '')))} effort={env.get('CLAUDE_CODE_EFFORT_LEVEL', '')}")
    db.run("INSERT OR REPLACE INTO ai_cache(hash,response) VALUES(?,?)", (h, json.dumps(data, ensure_ascii=False)))
    return data


def usage_summary():
    tot = db.one("SELECT COUNT(*) calls, COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp, "
                 "COALESCE(SUM(cached),0) cached FROM ai_log WHERE ts >= datetime('now','localtime','-1 day')")
    week = db.one("SELECT COUNT(*) calls, COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp "
                  "FROM ai_log WHERE ts >= datetime('now','localtime','-7 day')")
    last = db.q("SELECT ts,purpose,model,input_tokens,output_tokens,cached,ok,note FROM ai_log ORDER BY id DESC LIMIT 30")
    by = db.q("SELECT purpose, model, COUNT(*) calls, COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp "
              "FROM ai_log WHERE ok=1 AND cached=0 AND ts >= datetime('now','localtime','-7 day') GROUP BY purpose, model ORDER BY outp DESC")
    return {"day": tot, "week": week, "last": last, "by": by}
