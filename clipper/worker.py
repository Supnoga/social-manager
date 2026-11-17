"""Výrobná linka Clippera: jedna slučka na pozadí, vždy jedna ťažká vec naraz.

zdroj -> stiahnuť a prepísať -> vybrať momenty (AI, len text) -> strih -> schválenie -> rozvrh -> zverejnenie -> čísla.
Všetko je zapísané v databáze, takže po reštarte alebo aktualizácii pokračuje tam, kde skončila."""
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta

from . import env, moments, publish, render, source, store, track

STATE = {"step": "", "busy": False, "drain": False, "error": "", "last": "", "started": False}
_lock = threading.Lock()


def busy():
    """Robí sa práve niečo, čo sa nemá prerušiť aktualizáciou (strih, nahrávanie)?"""
    return bool(STATE["busy"])


def _work(step):
    STATE.update(step=step, busy=True)


def _idle():
    STATE.update(step="", busy=False, last=store.now())


def _ai_left():
    """Koľko výberov momentov ešte dnes smie ísť (šetrenie limitu Max)."""
    day = datetime.now().strftime("%Y-%m-%d")
    used = store.get("ai_calls", {}) or {}
    return int(store.get("ai_per_day", 6)) - int(used.get(day, 0))


def _ai_count():
    day = datetime.now().strftime("%Y-%m-%d")
    used = store.get("ai_calls", {}) or {}
    store.put("ai_calls", {day: int(used.get(day, 0)) + 1})


def _fetch_one():
    src = store.one("SELECT s.* FROM sources s JOIN campaigns c ON c.id=s.campaign_id WHERE s.status='new' AND c.status='active' "
                    "ORDER BY s.id LIMIT 1")
    if not src:
        return False
    _work("Sťahujem a prepisujem zdrojové video")
    store.run("UPDATE sources SET status='fetching' WHERE id=?", (src["id"],))
    try:
        source.fetch(src)
    except Exception as e:
        store.run("UPDATE sources SET status='failed', error=? WHERE id=?", (str(e)[-400:], src["id"]))
    return True


def _pick_one():
    """Kampani, ktorej dochádza zásoba klipov, vyberie nové momenty z ďalšieho zdroja."""
    if _ai_left() <= 0:
        return False
    for camp in store.q("SELECT * FROM campaigns WHERE status='active' ORDER BY id"):
        stock = store.one("SELECT COUNT(*) n FROM clips WHERE campaign_id=? AND status IN ('picked','ready','approved')",
                          (camp["id"],))["n"]
        per_day = int(camp["per_day"] or 6)
        if stock >= per_day:             # zásoba na deň je: AI netreba volať
            continue
        want = per_day * 2 - stock
        src = store.one("SELECT * FROM sources WHERE campaign_id=? AND status='ready' ORDER BY id LIMIT 1", (camp["id"],))
        if not src:
            continue
        _work("Vyberám najsilnejšie momenty")
        _ai_count()
        try:
            moments.pick(src, min(want, 12))
        except Exception as e:
            store.run("UPDATE sources SET error=? WHERE id=?", (str(e)[-300:], src["id"]))
            STATE["error"] = str(e)[-200:]
        return True
    return False


def _render_one():
    clip = store.one("SELECT c.* FROM clips c JOIN campaigns k ON k.id=c.campaign_id WHERE c.status='picked' AND k.status='active' "
                     "ORDER BY c.score DESC, c.id LIMIT 1")
    if not clip:
        return False
    _work("Striham klip")
    try:
        path, dur, layout = render.render(clip)
        status = "approved" if store.get("autopublish", False) else "ready"
        store.run("UPDATE clips SET path=?, duration=?, layout=?, status=?, error='' WHERE id=?", (path, dur, layout, status, clip["id"]))
    except Exception as e:
        store.run("UPDATE clips SET status='failed', error=? WHERE id=?", (str(e)[-400:], clip["id"]))
    return True


def _plan():
    for clip in store.q("SELECT * FROM clips WHERE status='approved' ORDER BY score DESC, id"):
        publish.plan(clip)


def _publish_one():
    post = publish.due()
    if not post:
        return False
    STATE["publishing"] = True
    try:
        if publish.publish(post):
            _notify()
    finally:
        STATE["publishing"] = False
    return True


def _pub_loop():
    """Zverejňovanie beží samo, popri sťahovaní a strihu: dlhé stiahnutie (3-hodinový stream) nesmie zdržať dávku,
    lebo kampane berú odkaz len 30 minút od zverejnenia."""
    time.sleep(30)
    while True:
        wait = 15
        try:
            if not store.get("paused", False):
                _plan()
                if _publish_one():
                    wait = 1
                elif time.time() - STATE.get("links_at", 0) > 60:
                    STATE["links_at"] = time.time()
                    publish.fill_links()
        except Exception:
            traceback.print_exc()
            wait = 60
        time.sleep(wait)


def _notify():
    """Upozornenie na Macu, že sú vonku nové odkazy s termínom (Whop berie odkaz len 30 minút od zverejnenia).
    Ozve sa na konci dávky, pri dlhej dávke priebežne každých 10 minút."""
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        last = store.get("notified_at", "") or ""
        new = [p for p in store.q("SELECT p.posted_at, k.site FROM posts p JOIN clips c ON c.id=p.clip_id JOIN campaigns k ON k.id=c.campaign_id "
                                  "WHERE p.status='posted' AND p.submit='todo' AND p.url!='' AND p.posted_at>?", (last,))
               if track.deadline(p["posted_at"], p["site"]) > store.now()]
        if not new:
            return
        soon = (datetime.now() + timedelta(minutes=3)).strftime(fmt)
        more = store.one("SELECT COUNT(*) n FROM posts WHERE status='queued' AND scheduled_at<=?", (soon,))["n"]
        oldest = min(p["posted_at"] for p in new)
        if more and (datetime.now() - datetime.strptime(oldest, fmt)).total_seconds() < 600:
            return
        store.put("notified_at", store.now())
        until = min(track.deadline(p["posted_at"], p["site"]) for p in new)[11:16]
        text = f"Nové klipy vonku: {len(new)}. Odkazy vlož do kampane do {until}."
        STATE["last_note"] = text
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e", f'display notification "{text}" with title "Clipper" sound name "Glass"'],
                           timeout=10, capture_output=True, stdin=subprocess.DEVNULL)
    except Exception:
        traceback.print_exc()


def _cleanup():
    """Vyťažené zdroje: veľké video preč z disku (prepis ostáva). Raz za hodinu."""
    if time.time() - float(store.get("cleanup_at", 0) or 0) < 3600:
        return
    store.put("cleanup_at", time.time())
    for src in store.q("SELECT * FROM sources WHERE status='used' AND path!=''"):
        if not store.one("SELECT id FROM clips WHERE source_id=? AND status='picked'", (src["id"],)):
            source.drop_files(src)
            store.run("UPDATE sources SET path='' WHERE id=?", (src["id"],))


def tick():
    """Jeden krok linky. Vráti True, keď niečo urobil (ďalší krok môže ísť hneď)."""
    if store.get("paused", False):
        track.tick()
        return False
    if store.one("SELECT COUNT(*) n FROM campaigns")["n"]:
        env.ensure()                         # nástroje sa pripravia až vtedy, keď Clipper niekto naozaj používa
    did = False
    try:
        if not STATE["drain"] and env.ready():    # zverejňovanie má vlastné vlákno (_pub_loop)
            did = _fetch_one() or _render_one() or _pick_one()
        track.tick()
        _cleanup()
    finally:
        _idle()
    return did


def _loop():
    time.sleep(20)
    try:
        publish.recover()
        store.run("UPDATE sources SET status='new' WHERE status IN ('fetching','transcribing')")
        moments.fix_ends()
    except Exception:
        traceback.print_exc()
    while True:
        wait = 20
        try:
            with _lock:
                if tick():
                    wait = 2
        except Exception as e:
            STATE.update(error=str(e)[-300:], busy=False, step="")
            traceback.print_exc()
            wait = 60
        time.sleep(wait)


def start():
    if STATE["started"]:
        return
    STATE["started"] = True
    threading.Thread(target=_loop, daemon=True, name="clipper").start()
    threading.Thread(target=_pub_loop, daemon=True, name="clipper-publish").start()
