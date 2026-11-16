"""Plánovač: každých 30 s pozrie frontu a nahrá videá, ktorým nastal čas. Pri chybe skúsi znova (max 3x)."""
import os
import random
import threading
import time
import json
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
    from . import brand
    if brand.unlogo_blocked(vid["id"]):   # ešte so starým logom: počká na opravu
        return
    if acc["platform"] == "youtube" and not youtube.quota_ok(acc):
        nxt = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=random.randint(0, 59), second=0)
        db.run("UPDATE posts SET scheduled_at=?, error=? WHERE id=?", (nxt.strftime("%Y-%m-%d %H:%M:%S"),
               "Dnešný limit YouTube je minutý. Nahrá sa samo zajtra ráno, netreba nič robiť.", post["id"]))
        return
    db.run("UPDATE posts SET status='uploading', attempts=attempts+1, updated_at=? WHERE id=?", (now_str(), post["id"]))
    state["current"] = f"{acc['platform']}: {vid['title'] or vid['original_name']}"
    try:
        ext_id = url = None
        if acc["platform"] == "youtube" and post["attempts"] > 0:  # predošlý pokus sa prerušil: nie je už video na kanáli?
            found = youtube.find_interrupted(acc, vid)
            if found:
                ext_id, url = youtube.release(acc, found) if post["privacy"] == "public" else (found, f"https://youtu.be/{found}")
        if not ext_id:
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
        temporary = any(w in msg for w in ("HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504", "dočasne"))
        if acc["platform"] == "youtube" and ("quotaExceeded" in msg or "uploadLimitExceeded" in msg or "quota" in msg.lower()):
            nxt = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=random.randint(0, 59), second=0)
            db.run("UPDATE posts SET status='queued', attempts=attempts-1, scheduled_at=?, error=?, updated_at=? WHERE id=?",
                   (nxt.strftime("%Y-%m-%d %H:%M:%S"), "Dnešný limit YouTube je minutý. Nahrá sa samo zajtra ráno, netreba nič robiť.", now_str(), post["id"]))
            return
        attempts = post["attempts"] + 1
        if (temporary and attempts < 12) or (attempts < 3 and "vypršalo" not in msg and "Najprv" not in msg):
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
    if youtube.units_blocked(acc):  # Google dnes už odmietol pre limit: skúsi sa až po obnovení o 9:00
        return
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
        elif "quota" in msg.lower():  # denný limit: počká na ďalší deň, nepočíta sa ako neúspešný pokus
            youtube.units_block(acc)
            db.run("UPDATE posts SET error=?, updated_at=? WHERE id=?",
                   ("Dnešný limit YouTube je minutý, zverejní sa po jeho obnovení.", now_str(), post["id"]))
        elif post["attempts"] >= 5:
            db.run("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?", (msg, now_str(), post["id"]))
        else:
            db.run("UPDATE posts SET attempts=attempts+1, error=?, updated_at=? WHERE id=?", ("Skúsim znova: " + msg, now_str(), post["id"]))
        traceback.print_exc()


def stash_one(post):
    """Video čakajúce na schválenie nahrá na YouTube ako súkromné, aby sa mohlo z Macu zmazať."""
    acc = db.one("SELECT * FROM accounts WHERE id=?", (post["account_id"],))
    vid = db.one("SELECT * FROM videos WHERE id=?", (post["video_id"],))
    if not acc or not vid or not vid["file_path"] or not os.path.exists(vid["file_path"]) or not youtube.quota_ok(acc, reserve=youtube.RELEASE_RESERVE):
        return False
    from . import brand
    if brand.unlogo_blocked(vid["id"]):
        return False
    state["current"] = f"YouTube (súkromne): {vid['title'] or vid['original_name']}"
    retry = (post.get("error") or "").startswith("Súkromné nahratie:")
    try:
        # značka pre prípad pádu appky uprostred nahrávania: ďalší pokus najprv pozrie, či video na kanáli už nie je
        db.run("UPDATE posts SET error='Súkromné nahratie: prebieha', updated_at=? WHERE id=?", (now_str(), post["id"]))
        ext_id = youtube.find_interrupted(acc, vid) if retry else ""
        if not ext_id:
            ext_id, _ = youtube.upload(acc, vid, "private")
        db.run("UPDATE posts SET stash_id=?, error='', updated_at=? WHERE id=?", (str(ext_id), now_str(), post["id"]))
        # projekty, ktoré Oliver pustil bez Kontroly: po súkromnom nahratí rovno naplánovať (YouTube ich zverejní sám)
        if vid["project_id"] in {int(x) for x in (db.get_setting("auto_approve_projects", []) or [])}:
            db.run("UPDATE posts SET status='queued' WHERE id=? AND status='review'", (post["id"],))
        return True
    except Exception as e:
        m = str(e)
        if "quota" in m.lower() or "uploadLimitExceeded" in m:
            m = "Dnešný limit YouTube je minutý. Nahrá sa samo zajtra ráno, netreba nič robiť."
        db.run("UPDATE posts SET error=?, updated_at=? WHERE id=?", ("Súkromné nahratie: " + m[:600], now_str(), post["id"]))
        traceback.print_exc()
        return False
    finally:
        state["current"] = None


def _next_reset():
    """Kedy sa obnoví denný limit YouTube (polnoc v Kalifornii), v našom miestnom čase."""
    try:
        from zoneinfo import ZoneInfo
        la = ZoneInfo("America/Los_Angeles")
        d = datetime.now(la).date() + timedelta(days=1)
        return datetime(d.year, d.month, d.day, tzinfo=la).astimezone().replace(tzinfo=None)
    except Exception:
        return datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=1 if datetime.now().hour >= 9 else 0)


def ahead_one():
    """Oliver 15.11.: voľný zvyšok denného limitu nahrávania využiť na videá na ďalšie dni. Video sa nahrá súkromne
    s časom zverejnenia (publishAt), YouTube ho zverejní sám v jeho deň. Prednosť majú všetky videá, ktoré majú ísť
    von pred obnovením limitu (+ RELEASE_RESERVE), najbližšie dni idú prvé a v rámci dňa dlhé pred krátkymi.
    Krátke sa dopredu nahrá, len keď dlhé video toho kanála v ten deň už nahraté je (bez dlhého nič nevyjde)."""
    if not db.get_setting("ahead_upload", True):
        return False
    reset = _next_reset().strftime("%Y-%m-%d %H:%M:%S")
    # 16.11.: aj dnešné videá (o 15+ minút) sa nahrajú vopred s časom zverejnenia, aby vyšli presne načas
    # a nečakali v rade na nahrávanie až v ich čas (napr. 15 dlhých o 14:00 naraz)
    soon = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    rows = db.q("""SELECT p.*, COALESCE(i.format,'short') fmt, substr(p.scheduled_at,1,10) day FROM posts p
                   JOIN accounts a ON a.id=p.account_id LEFT JOIN videos v ON v.id=p.video_id
                   LEFT JOIN scripts s ON s.id=v.script_id LEFT JOIN ideas i ON i.id=s.idea_id
                   WHERE p.status='queued' AND a.platform='youtube' AND COALESCE(p.stash_id,'')='' AND p.scheduled_at>=?
                   ORDER BY substr(p.scheduled_at,1,10), COALESCE(i.format,'short')!='long', p.scheduled_at LIMIT 60""",
                (soon,))
    for p in rows:
        acc = db.one("SELECT * FROM accounts WHERE id=?", (p["account_id"],))
        vid = db.one("SELECT * FROM videos WHERE id=?", (p["video_id"],))
        from . import brand
        if not acc or not vid or not vid["file_path"] or not os.path.exists(vid["file_path"]) or brand.unlogo_blocked(vid["id"]):
            continue
        k = youtube._client_idx(acc)
        need = 0
        for r in db.q("""SELECT a.tokens FROM posts p JOIN accounts a ON a.id=p.account_id WHERE a.platform='youtube'
                         AND p.status IN ('queued','uploading') AND COALESCE(p.stash_id,'')='' AND p.scheduled_at<?""", (reset,)):
            try:
                if int(json.loads(r["tokens"] or "{}").get("client", 0) or 0) == k:
                    need += 1
            except Exception:
                pass
        if p["scheduled_at"] < reset:
            need = max(0, need - 1)  # samo patrí medzi videá pred obnovením limitu, nahratie teraz nič navyše nestojí
        if not youtube.quota_ok(acc, reserve=need + youtube.RELEASE_RESERVE) or youtube.units_blocked(acc) \
                or youtube.units_used(acc) + 150 + (need + youtube.RELEASE_RESERVE) * 110 > youtube.UNITS_LIMIT:
            continue
        if (p.get("error") or "").startswith("Nahratie dopredu:") and (p.get("updated_at") or "") > (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"):
            continue
        if p["fmt"] != "long" and db.one("""SELECT 1 FROM posts p2 JOIN videos v2 ON v2.id=p2.video_id
                   JOIN scripts s2 ON s2.id=v2.script_id JOIN ideas i2 ON i2.id=s2.idea_id
                   WHERE p2.account_id=? AND substr(p2.scheduled_at,1,10)=? AND i2.format='long' AND p2.status!='done'""",
                                         (p["account_id"], p["day"])):
            continue
        state["current"] = f"YouTube (dopredu na {p['day']}): {vid['title'] or vid['original_name']}"
        try:
            db.run("UPDATE posts SET status='uploading', attempts=attempts+1, updated_at=? WHERE id=?", (now_str(), p["id"]))
            ext_id, url = youtube.upload(acc, vid, "private", publish_at=_utc(p["scheduled_at"]))
            db.run("UPDATE posts SET status='done', external_id=?, url=?, error='', updated_at=? WHERE id=?",
                   (str(ext_id), url or f"https://youtu.be/{ext_id}", now_str(), p["id"]))
            return True
        except Exception as e:
            m = str(e)
            if "quota" in m.lower() or "uploadLimitExceeded" in m:
                youtube.units_block(acc)
                m = "Dnešný limit YouTube je minutý, nahrá sa v jeho deň."
            db.run("UPDATE posts SET status='queued', error=?, updated_at=? WHERE id=?", ("Nahratie dopredu: " + m[:600], now_str(), p["id"]))
            traceback.print_exc()
            return False
        finally:
            state["current"] = None
    return False


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
    if not due:
        try:
            ahead_one()
        except Exception:
            traceback.print_exc()
    if stash_on():
        # poradie: najbližší deň prvý a v rámci dňa dlhé videá pred krátkymi (bez dlhého videa krátke v ten deň nevyjdú)
        rows = db.q("""SELECT p.* FROM posts p JOIN accounts a ON a.id=p.account_id
                       LEFT JOIN videos v ON v.id=p.video_id LEFT JOIN scripts s ON s.id=v.script_id
                       LEFT JOIN ideas i ON i.id=s.idea_id WHERE p.status='review'
                       AND a.platform='youtube' AND COALESCE(p.stash_id,'')=''
                       AND NOT (COALESCE(p.error,'') LIKE 'Súkromné nahratie:%' AND p.updated_at > ?)
                       ORDER BY substr(p.scheduled_at,1,10), COALESCE(i.format,'short')!='long', p.scheduled_at LIMIT 10""", ((datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),))
        done = 0
        for p in rows:
            if done < 2 and stash_one(p):
                done += 1
        if rows or (datetime.now().minute % 30 == 0 and datetime.now().second < 30):
            try:
                nightly.clean()
            except Exception:
                traceback.print_exc()
    # titulky dlhých videí: len z kvóty, ktorú práve nepotrebujú videá (stoja ako 4 nahratia)
    if not due and not db.one("""SELECT 1 FROM posts p JOIN accounts a ON a.id=p.account_id WHERE a.platform='youtube'
                                 AND ((p.status='review' AND COALESCE(p.stash_id,'')='') OR p.status='uploading') LIMIT 1"""):
        try:
            youtube.localize_one() or youtube.caption_one()  # najprv preklady názvov (lacné), potom titulky
        except Exception:
            traceback.print_exc()
    try:
        if datetime.now().hour >= 3:
            backup_db()
    except Exception:
        traceback.print_exc()
    try:
        nightly.awake_tick(busy=bool(state["current"]))
    except Exception:
        traceback.print_exc()


BACKUP_DIR = db.DATA_DIR / "zalohy"


def backup_db(keep=5):
    """Raz denne bezpečná kópia databázy (pripojenia kanálov, plány, nastavenia) do data/zalohy, posledných 5 dní.
    Vyrovnávacia pamäť AI odpovedí sa nezálohuje (dá sa kedykoľvek vytvoriť znova a zaberá najviac)."""
    import sqlite3
    day = datetime.now().strftime("%Y-%m-%d")
    if db.get_setting("backup_day", "") == day:
        return
    db.set_setting("backup_day", day)
    BACKUP_DIR.mkdir(exist_ok=True)
    out = BACKUP_DIR / f"app-{day}.db"
    src = sqlite3.connect(f"file:{db.DB_PATH}?mode=ro", uri=True, timeout=30)
    dst = sqlite3.connect(out)
    try:
        src.backup(dst)
        try:
            dst.execute("DELETE FROM ai_cache")
            dst.commit()
            dst.execute("VACUUM")
        except Exception:
            pass
    finally:
        dst.close()
        src.close()
    for f in sorted(BACKUP_DIR.glob("app-*.db"))[:-keep]:
        f.unlink(missing_ok=True)


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
