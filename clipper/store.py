"""Dáta Clippera: vlastný súbor data/clipper/clipper.db, oddelený od databázy Social Managera."""
import json
import sqlite3
import threading
from datetime import datetime

from app import db as appdb

DIR = appdb.DATA_DIR / "clipper"
DIR.mkdir(parents=True, exist_ok=True)
for _d in ("src", "clips", "work"):
    (DIR / _d).mkdir(exist_ok=True)
DB_PATH = DIR / "clipper.db"
_lock = threading.RLock()
_con = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  site TEXT DEFAULT 'whop',
  url TEXT DEFAULT '',
  rate REAL DEFAULT 1.0,
  min_views INTEGER DEFAULT 0,
  max_payout REAL DEFAULT 0,
  budget REAL DEFAULT 0,
  networks TEXT DEFAULT '["youtube","instagram","tiktok"]',
  tags TEXT DEFAULT '',
  rules TEXT DEFAULT '',
  about TEXT DEFAULT '',
  lang TEXT DEFAULT 'en',
  per_day INTEGER DEFAULT 6,
  clip_min INTEGER DEFAULT 20,
  clip_max INTEGER DEFAULT 55,
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_id INTEGER NOT NULL,
  url TEXT DEFAULT '',
  title TEXT DEFAULT '',
  duration REAL DEFAULT 0,
  path TEXT DEFAULT '',
  words_path TEXT DEFAULT '',
  lang TEXT DEFAULT '',
  status TEXT DEFAULT 'new',
  error TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS clips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL,
  campaign_id INTEGER NOT NULL,
  t0 REAL, t1 REAL,
  hook TEXT DEFAULT '',
  title TEXT DEFAULT '',
  caption TEXT DEFAULT '',
  why TEXT DEFAULT '',
  score REAL DEFAULT 0,
  layout TEXT DEFAULT '',
  path TEXT DEFAULT '',
  duration REAL DEFAULT 0,
  status TEXT DEFAULT 'picked',
  error TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  clip_id INTEGER NOT NULL,
  account_id INTEGER NOT NULL,
  platform TEXT DEFAULT '',
  scheduled_at TEXT NOT NULL,
  status TEXT DEFAULT 'queued',
  attempts INTEGER DEFAULT 0,
  external_id TEXT DEFAULT '',
  url TEXT DEFAULT '',
  error TEXT DEFAULT '',
  views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0,
  stats_at TEXT DEFAULT '',
  submit TEXT DEFAULT 'todo',
  submitted_at TEXT DEFAULT '',
  paid REAL DEFAULT 0,
  updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS clip_accounts (account_id INTEGER PRIMARY KEY, active INTEGER DEFAULT 1, per_day INTEGER DEFAULT 6);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX IF NOT EXISTS idx_cposts ON posts(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_cclips ON clips(campaign_id, status);
"""


def con():
    global _con
    if _con is None:
        _con = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
        _con.row_factory = sqlite3.Row
        _con.execute("PRAGMA journal_mode=WAL")
        _con.executescript(SCHEMA)
        _con.commit()
    return _con


def q(sql, args=()):
    with _lock:
        return [dict(r) for r in con().execute(sql, args).fetchall()]


def one(sql, args=()):
    r = q(sql, args)
    return r[0] if r else None


def run(sql, args=()):
    with _lock:
        cur = con().execute(sql, args)
        con().commit()
        return cur.lastrowid


def get(key, default=None):
    r = one("SELECT value FROM kv WHERE key=?", (key,))
    if not r:
        return default
    try:
        return json.loads(r["value"])
    except Exception:
        return default


def put(key, value):
    run("INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def campaign(cid):
    c = one("SELECT * FROM campaigns WHERE id=?", (cid,))
    if c:
        try:
            c["networks"] = json.loads(c["networks"] or "[]")
        except Exception:
            c["networks"] = []
    return c


def project_id():
    """Projekt „Clipper“ v Social Manageri: drží len účty na sieťach (pripájajú sa cez hotové prihlásenie appky).
    Nevyrába sa v ňom nič a do zásoby dní ani plánov sa neráta."""
    pid = appdb.get_setting("clip_project_id")
    if pid and appdb.one("SELECT id FROM projects WHERE id=?", (pid,)):
        return int(pid)
    pid = appdb.run("INSERT INTO projects(name, description, source_lang, languages, color) VALUES(?,?,?,?,?)",
                    ("Clipper", "Účty pre platený clipping. Výroba a zverejňovanie beží v Clipperi (/clip).", "en", '["en"]', "#FF6B00"))
    appdb.set_setting("clip_project_id", pid)
    return int(pid)


def accounts():
    """Účty Clippera = účty projektu Clipper v Social Manageri + ich nastavenie (koľko klipov denne)."""
    pid = project_id()
    rows = appdb.q("SELECT id, platform, name, external_id, tokens FROM accounts WHERE project_id=? ORDER BY platform, id", (pid,))
    conf = {r["account_id"]: r for r in q("SELECT * FROM clip_accounts")}
    out = []
    for a in rows:
        c = conf.get(a["id"]) or {"active": 1, "per_day": get("per_day_default", 6)}
        try:
            broken = bool(json.loads(a["tokens"] or "{}").get("broken"))
        except Exception:
            broken = False
        out.append({"id": a["id"], "platform": a["platform"], "name": a["name"], "external_id": a["external_id"],
                    "active": int(c["active"]), "per_day": int(c["per_day"]), "broken": broken})
    return out
