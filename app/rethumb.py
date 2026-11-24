"""Spätné vylepšenie už vyrobených videí podľa stratégie náhľadov (18.11.2026). Bez zásahu do výroby:
beží na pozadí, náhľady sa nahrávajú len z voľnej YouTube kvóty a nové texty náhľadov stoja jedno lacné volanie AI na 25 videí.

1. Dlhé videá: nový náhľad (veľký presný model, farebné pozadie, líška, krátky text s témou). Hotovým videám sa nahrá
   na YouTube, ešte nenahratým sa len prepíše obrázok vedľa videa (nahrá sa pri zverejnení).
2. Staršie Shorts: odkaz na dlhé video toho istého kanála do popisu a ako komentár.
Hotové sa pamätá v nastaveniach thumb2_done (id videí), thumb2_up (YouTube id) a short_link_done (id príspevkov)."""
import json
import os
import threading
import traceback
from datetime import datetime

from . import db

_busy = threading.Lock()
PER_RUN = 8          # toľko náhľadov na jedno spustenie (každý ~5–20 s na Macu)
SHORTS_PER_RUN = 10


def _long_rows():
    """Dlhé videá vyrobené pred touto verziou (novšie už majú nový náhľad z výroby)."""
    mx = db.get_setting("thumb2_max_vid")
    if mx is None:
        mx = (db.one("SELECT MAX(id) m FROM videos") or {}).get("m") or 0
        db.set_setting("thumb2_max_vid", mx)
    return db.q("""SELECT v.id vid, v.file_path, p.id pid, p.status, p.account_id, COALESCE(NULLIF(p.external_id,''), p.stash_id, '') yt,
                          s.id sid, s.title, s.thumb, s.lang
                   FROM videos v JOIN scripts s ON s.id=v.script_id JOIN ideas i ON i.id=s.idea_id
                   LEFT JOIN posts p ON p.video_id=v.id
                   WHERE i.format='long' AND v.id<=? AND COALESCE(v.removed,0)=0 AND (p.id IS NULL OR p.status IN ('done','queued','review','hold'))
                   ORDER BY (p.status='done') DESC, p.scheduled_at DESC""", (mx,))


def _old_text(row):
    try:
        return str((json.loads(row["thumb"] or "{}") or {}).get("text") or "")
    except Exception:
        return ""


def new_texts(rows):
    """Nové texty náhľadov pre viac videí naraz (jedno lacné volanie AI). Vráti {sid: text}."""
    from . import ai
    items = {str(r["sid"]): {"title": r["title"], "old": _old_text(r)} for r in rows}
    if not items:
        return {}
    prompt = ("Write YouTube thumbnail hook text for these animated explainer videos (the picture shows the main object). Rules: 2-5 words, "
              "max 28 characters, UPPERCASE, never repeats the title; a short dramatic claim, reaction or question the viewer reacts to. "
              "Styles that won 3-100x on top explainer channels: 'THEY REMOVED THE HILL', 'THEY'RE BACK??', 'IT'S HAPPENING!', "
              "'DOES ANYONE WIN?', 'HE ACTUALLY HAS A PLAN', 'THIS CAN'T MOVE!'. Clickbait is fine, lies are not; no emoji. "
              "Write in the language of the title.\n"
              f"Videos (id: title, old text): {json.dumps(items, ensure_ascii=False)}\n"
              'Return JSON: {"<id>": "TEXT"}')
    try:
        r = ai.ask(prompt, "thumb_text", "cheap") or {}
    except Exception as e:
        print("náhľady, text:", e)
        return {}
    return {int(k): str(v).strip()[:28] for k, v in r.items() if str(k).isdigit() and str(v).strip()}


def _save_text(sid, text):
    s = db.one("SELECT thumb FROM scripts WHERE id=?", (sid,)) or {}
    try:
        t = json.loads(s.get("thumb") or "{}") or {}
    except Exception:
        t = {}
    t["text"] = text
    db.run("UPDATE scripts SET thumb=? WHERE id=?", (json.dumps(t, ensure_ascii=False), sid))


def _done_long():
    """1.104.0: všetky zverejnené dlhé videá na YouTube (aj tie, ktorých súbor sa už z Macu zmazal)."""
    return db.q("""SELECT v.id vid, v.file_path, p.account_id, COALESCE(NULLIF(p.external_id,''), p.stash_id, '') yt, s.id sid
                   FROM videos v JOIN scripts s ON s.id=v.script_id JOIN ideas i ON i.id=s.idea_id
                   JOIN posts p ON p.video_id=v.id JOIN accounts a ON a.id=p.account_id
                   WHERE i.format='long' AND a.platform='youtube' AND p.status='done'
                   AND COALESCE(NULLIF(p.external_id,''), p.stash_id, '')!='' ORDER BY p.scheduled_at DESC""")


def _thumb_file(r, done):
    """Obrázok náhľadu pre video: hotový, alebo ho nanovo vyrobí (bez AI, len zo scenára)."""
    from . import main
    for f in (db.get_setting(f"thumb2_path_{r['vid']}") or "", os.path.splitext(r["file_path"] or "")[0] + ".jpg"):
        if f and os.path.exists(f):
            return f
    out = str(db.MEDIA_DIR / f"thumb_v{r['vid']}.jpg")
    s = db.one("SELECT * FROM scripts WHERE id=?", (r["sid"],))
    if not s:
        return ""
    try:
        if not main.render_thumb(s, out) or not os.path.exists(out):
            return ""
    except Exception:
        traceback.print_exc()
        return ""
    done.add(str(r["vid"]))
    db.set_setting("thumb2_done", sorted(done))
    db.set_setting(f"thumb2_path_{r['vid']}", out)
    return out


def thumbs_run(limit=PER_RUN):
    from . import main
    from .platforms import youtube
    done = set(db.get_setting("thumb2_done", []) or [])
    up = set(db.get_setting("thumb2_up", []) or [])
    rows = _long_rows()
    todo = [r for r in rows if str(r["vid"]) not in done][:limit]           # nový vzhľad náhľadu pre staršie videá
    texts = new_texts(todo)
    n = 0
    for r in todo:
        if r["sid"] in texts:
            _save_text(r["sid"], texts[r["sid"]])
        s = db.one("SELECT * FROM scripts WHERE id=?", (r["sid"],))
        out = os.path.splitext(r["file_path"] or "")[0] + ".jpg" if r["file_path"] else str(db.MEDIA_DIR / f"thumb_v{r['vid']}.jpg")
        if not os.path.isdir(os.path.dirname(out) or "."):
            out = str(db.MEDIA_DIR / f"thumb_v{r['vid']}.jpg")
        try:
            if not main.render_thumb(s, out):
                continue
        except Exception:
            traceback.print_exc()
            continue
        done.add(str(r["vid"]))
        db.set_setting("thumb2_done", sorted(done))
        db.set_setting(f"thumb2_path_{r['vid']}", out)
        n += 1
    # 1.104.0: nahratie náhľadu všetkým zverejneným dlhým videám, ktoré ho na YouTube ešte nemajú. Kanál, ktorý náhľad
    # odmietne (nie je overený), sa skúša znova raz za deň, takže po overení sa náhľady doplnia samy.
    renders = 0
    for r in _done_long():
        if r["yt"] in up:
            continue
        acc = db.one("SELECT * FROM accounts WHERE id=?", (r["account_id"],))
        if not acc or youtube.thumb_blocked(acc) or not youtube.spare_ok(acc, youtube.U_THUMB):
            continue
        path = _thumb_file(r, done) if renders < limit else ""
        if not path:
            continue
        renders += 1
        if youtube.set_thumb(acc, r["yt"], path):
            up.add(r["yt"])
            n += 1
    return n


def shorts_run(limit=SHORTS_PER_RUN):
    from . import crosslink
    from .platforms import youtube
    done = set(db.get_setting("short_link_done", []) or [])
    now = datetime.now().isoformat(timespec="minutes")
    rows = db.q("""SELECT p.id pid, p.external_id, p.account_id, v.* FROM posts p JOIN videos v ON v.id=p.video_id
                   JOIN accounts a ON a.id=p.account_id JOIN scripts s ON s.id=v.script_id JOIN ideas i ON i.id=s.idea_id
                   WHERE a.platform='youtube' AND i.format!='long' AND p.status='done' AND COALESCE(p.external_id,'')!=''
                   AND p.scheduled_at<=? ORDER BY p.scheduled_at DESC LIMIT 2000""", (now,))
    n = 0
    for r in rows:
        if n >= limit:
            break
        if r["pid"] in done:
            continue
        acc = db.one("SELECT * FROM accounts WHERE id=?", (r["account_id"],))
        if not acc:
            continue
        vid = {k: r[k] for k in r.keys() if k not in ("pid", "external_id", "account_id")}
        line = crosslink.line(acc, vid, now)
        if not line:
            continue   # kanál ešte nemá verejné dlhé video: skúsi sa neskôr
        if not youtube.spare_ok(acc, youtube.U_UPDATE + youtube.U_COMMENT + 1):
            continue
        try:
            youtube.add_related(acc, r["external_id"], line)
        except Exception as e:
            print("odkaz zo Shortu:", e)
            continue
        done.add(r["pid"])
        db.set_setting("short_link_done", sorted(done))
        n += 1
    return n


def kick():
    """Spustí jedno kolo na pozadí, ak ešte nebeží. Nastavenie rethumb=false ho vypne."""
    if db.get_setting("rethumb", True) is False or _busy.locked():
        return

    def go():
        with _busy:
            try:
                thumbs_run()
            except Exception:
                traceback.print_exc()
            try:
                shorts_run()
            except Exception:
                traceback.print_exc()
    threading.Thread(target=go, daemon=True).start()
