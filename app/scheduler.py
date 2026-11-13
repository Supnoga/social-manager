"""Plánovač: každých 30 s pozrie frontu a nahrá videá, ktorým nastal čas. Pri chybe skúsi znova (max 3x)."""
import os
import random
import threading
import time
import traceback
from datetime import datetime, timedelta

from . import db, nightly
from .platforms import linkedin, meta, tiktok, tiktok_business, youtube
from .platforms.common import tokens

UPLOADERS = {
    "youtube": youtube.upload,
    "facebook": meta.upload_facebook,
    "instagram": meta.upload_instagram,
    "linkedin": linkedin.upload,
    "tiktok": lambda acc, vid, priv: (tiktok_business.upload if tokens(acc).get("api") == "business"
                                      else tiktok.upload)(acc, vid, priv),
}

_running = False
state = {"last_tick": None, "current": None}


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def process_one(post):
    acc = db.one("SELECT * FROM accounts WHERE id=?", (post["account_id"],))
    vid = db.one("SELECT * FROM videos WHERE id=?", (post["video_id"],))
    if not acc or not vid:
        db.run("UPDATE posts SET status='failed', error='Účet alebo video už neexistuje' WHERE id=?", (post["id"],))
        return
    if acc["platform"] == "youtube" and not youtube.quota_ok(acc):
        nxt = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=random.randint(0, 59), second=0)
        db.run("UPDATE posts SET scheduled_at=?, error=? WHERE id=?", (nxt.strftime("%Y-%m-%d %H:%M:%S"),
               "Dnešný limit YouTube nahratí je vyčerpaný, presunuté na zajtra (pridaj ďalší Google projekt v Účtoch).", post["id"]))
        return
    db.run("UPDATE posts SET status='uploading', attempts=attempts+1, updated_at=? WHERE id=?", (now_str(), post["id"]))
    state["current"] = f"{acc['platform']}: {vid['title'] or vid['original_name']}"
    try:
        ext_id, url = UPLOADERS[acc["platform"]](acc, vid, post["privacy"])
        db.run("UPDATE posts SET status='done', external_id=?, url=?, error='', updated_at=? WHERE id=?",
               (str(ext_id), url or "", now_str(), post["id"]))
        if acc["platform"] == "youtube":
            try:  # odkaz na podobné video z príbuzného kanála (len dlhé videá)
                from . import crosslink
                youtube.add_related(acc, str(ext_id), crosslink.line(acc, vid, post["scheduled_at"], post["id"]))
            except Exception as e2:
                print("Odkaz na podobné video:", e2)
    except Exception as e:
        msg = str(e)[:800]
        if acc["platform"] == "youtube" and ("quotaExceeded" in msg or "uploadLimitExceeded" in msg or "quota" in msg.lower()):
            nxt = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=random.randint(0, 59), second=0)
            db.run("UPDATE posts SET status='queued', attempts=attempts-1, scheduled_at=?, error=?, updated_at=? WHERE id=?",
                   (nxt.strftime("%Y-%m-%d %H:%M:%S"), "YouTube denný limit, presunuté na zajtra.", now_str(), post["id"]))
            return
        attempts = post["attempts"] + 1
        if attempts < 3 and "vypršalo" not in msg and "Najprv" not in msg:
            retry = (datetime.now() + timedelta(minutes=15 * attempts)).strftime("%Y-%m-%d %H:%M:%S")
            db.run("UPDATE posts SET status='queued', scheduled_at=?, error=?, updated_at=? WHERE id=?",
                   (retry, "Skúsim znova: " + msg, now_str(), post["id"]))
        else:
            db.run("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?", (msg, now_str(), post["id"]))
        traceback.print_exc()
    finally:
        state["current"] = None


def _utc(local_str):
    from datetime import timezone
    return datetime.fromisoformat(local_str).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def release_one(post):
    """Schválené video, ktoré už leží súkromne na YouTube: len sa prepne na verejné (alebo naplánuje cez publishAt)."""
    acc = db.one("SELECT * FROM accounts WHERE id=?", (post["account_id"],))
    if not acc:
        db.run("UPDATE posts SET status='failed', error='Účet už neexistuje' WHERE id=?", (post["id"],))
        return
    when = post["scheduled_at"]
    future = datetime.fromisoformat(when) > datetime.now() + timedelta(minutes=10)
    try:
        ext_id, url = youtube.release(acc, post["stash_id"], _utc(when) if future else None)
        db.run("UPDATE posts SET status='done', external_id=?, url=?, error='', updated_at=? WHERE id=?",
               (ext_id, url, now_str(), post["id"]))
        vrow = db.one("SELECT * FROM videos WHERE id=?", (post["video_id"],)) or {}
        youtube.add_to_series(acc, vrow, ext_id)
        try:  # odkaz na podobné video z príbuzného kanála (len dlhé videá)
            from . import crosslink
            youtube.add_related(acc, ext_id, crosslink.line(acc, vrow, when, post["id"]))
        except Exception as e:
            print("Odkaz na podobné video:", e)
    except Exception as e:
        msg = str(e)[:800]
        if "notFound" in msg or "404" in msg:  # niekto video na YouTube zmazal: nahrá sa nanovo, ak je súbor
            db.run("UPDATE posts SET stash_id='', error=? WHERE id=?", ("Súkromné video na YouTube chýba, nahrá sa znova", post["id"]))
        elif post["attempts"] >= 5:
            db.run("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?", (msg, now_str(), post["id"]))
        else:
            db.run("UPDATE posts SET attempts=attempts+1, error=?, updated_at=? WHERE id=?", ("Skúsim znova: " + msg, now_str(), post["id"]))
        traceback.print_exc()


def stash_one(post):
    """Video čakajúce na schválenie nahrá na YouTube ako súkromné, aby sa mohlo z Macu zmazať."""
    acc = db.one("SELECT * FROM accounts WHERE id=?", (post["account_id"],))
    vid = db.one("SELECT * FROM videos WHERE id=?", (post["video_id"],))
    if not acc or not vid or not vid["file_path"] or not os.path.exists(vid["file_path"]) or not youtube.quota_ok(acc):
        return False
    state["current"] = f"YouTube (súkromne): {vid['title'] or vid['original_name']}"
    try:
        ext_id, _ = youtube.upload(acc, vid, "private")
        db.run("UPDATE posts SET stash_id=?, error='', updated_at=? WHERE id=?", (str(ext_id), now_str(), post["id"]))
        return True
    except Exception as e:
        db.run("UPDATE posts SET error=?, updated_at=? WHERE id=?", ("Súkromné nahratie: " + str(e)[:600], now_str(), post["id"]))
        traceback.print_exc()
        return False
    finally:
        state["current"] = None


def stash_on():
    return (db.get_setting("night", {}) or {}).get("stash", True)


def tick():
    state["last_tick"] = now_str()
    if db.get_setting("paused", False):
        return
    for p in db.q("SELECT * FROM posts WHERE status='queued' AND COALESCE(stash_id,'')!='' ORDER BY scheduled_at LIMIT 20"):
        release_one(p)
    due = db.q("""SELECT * FROM posts WHERE status='queued' AND COALESCE(stash_id,'')='' AND scheduled_at<=?
                  ORDER BY scheduled_at LIMIT 5""", (now_str(),))
    for p in due:
        process_one(p)
    if stash_on():
        rows = db.q("""SELECT p.* FROM posts p JOIN accounts a ON a.id=p.account_id WHERE p.status='review'
                       AND a.platform='youtube' AND COALESCE(p.stash_id,'')=''
                       AND NOT (COALESCE(p.error,'') LIKE 'Súkromné nahratie:%' AND p.updated_at > ?)
                       ORDER BY p.video_id LIMIT 10""", ((datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),))
        done = 0
        for p in rows:
            if done < 2 and stash_one(p):
                done += 1
        if rows or (datetime.now().minute % 30 == 0 and datetime.now().second < 30):
            try:
                nightly.clean()
            except Exception:
                traceback.print_exc()
    try:
        nightly.awake_tick(busy=bool(state["current"]))
    except Exception:
        traceback.print_exc()


def loop():
    # po reštarte: čo ostalo 'uploading', vráť do fronty
    db.run("UPDATE posts SET status='queued' WHERE status='uploading'")
    while True:
        try:
            tick()
        except Exception:
            traceback.print_exc()
        time.sleep(30)


def start():
    global _running
    if _running:
        return
    _running = True
    threading.Thread(target=loop, daemon=True).start()
