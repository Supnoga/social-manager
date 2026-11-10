"""SQLite databáza - jeden súbor data/app.db, nič netreba inštalovať."""
import json
import sqlite3
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
DB_PATH = DATA_DIR / "app.db"
DATA_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)

_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  audience TEXT DEFAULT '',
  tone TEXT DEFAULT '',
  goals TEXT DEFAULT '',
  source_lang TEXT DEFAULT 'sk',
  languages TEXT DEFAULT '["sk"]',
  strategy TEXT DEFAULT '',
  strategy_short TEXT DEFAULT '',
  color TEXT DEFAULT '#6c5ce7',
  voice_gender TEXT DEFAULT 'F',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS ideas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  hook TEXT DEFAULT '',
  angle TEXT DEFAULT '',
  pillar TEXT DEFAULT '',
  format TEXT DEFAULT 'short',
  why TEXT DEFAULT '',
  score INTEGER DEFAULT 0,
  status TEXT DEFAULT 'new',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS scripts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  idea_id INTEGER,
  lang TEXT NOT NULL,
  is_source INTEGER DEFAULT 0,
  title TEXT DEFAULT '',
  voiceover TEXT DEFAULT '',
  scenes TEXT DEFAULT '[]',
  description TEXT DEFAULT '',
  hashtags TEXT DEFAULT '',
  caption TEXT DEFAULT '',
  voice_path TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now','localtime')),
  UNIQUE(idea_id, lang)
);
CREATE TABLE IF NOT EXISTS videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  lang TEXT DEFAULT '',
  title TEXT DEFAULT '',
  description TEXT DEFAULT '',
  hashtags TEXT DEFAULT '',
  caption TEXT DEFAULT '',
  file_path TEXT NOT NULL,
  original_name TEXT DEFAULT '',
  size INTEGER DEFAULT 0,
  duration REAL DEFAULT 0,
  script_id INTEGER,
  status TEXT DEFAULT 'ready',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  platform TEXT NOT NULL,
  name TEXT DEFAULT '',
  external_id TEXT DEFAULT '',
  project_id INTEGER,
  lang TEXT DEFAULT '',
  tokens TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL,
  account_id INTEGER NOT NULL,
  scheduled_at TEXT NOT NULL,
  privacy TEXT DEFAULT 'public',
  status TEXT DEFAULT 'queued',
  attempts INTEGER DEFAULT 0,
  external_id TEXT DEFAULT '',
  url TEXT DEFAULT '',
  error TEXT DEFAULT '',
  updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS ai_cache (hash TEXT PRIMARY KEY, response TEXT, created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS tm (h TEXT, lang TEXT, text TEXT, PRIMARY KEY(h, lang));
CREATE TABLE IF NOT EXISTS ai_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT DEFAULT (datetime('now','localtime')),
  purpose TEXT, model TEXT,
  input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0,
  cached INTEGER DEFAULT 0, ok INTEGER DEFAULT 1, note TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_videos_project ON videos(project_id, lang);
CREATE INDEX IF NOT EXISTS idx_ideas_project ON ideas(project_id, status);
"""


MIGRATIONS = [
    "ALTER TABLE projects ADD COLUMN design_md TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN design_summary TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN design_colors TEXT DEFAULT '[]'",
    "ALTER TABLE projects ADD COLUMN glossary TEXT DEFAULT ''",
    "ALTER TABLE scripts ADD COLUMN qa TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN sources TEXT DEFAULT '[]'",
    "ALTER TABLE projects ADD COLUMN sources_summary TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN voices TEXT DEFAULT '{}'",
    "ALTER TABLE projects ADD COLUMN voice_rate REAL DEFAULT 1.0",
    "ALTER TABLE scripts ADD COLUMN voice_engine TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN platforms TEXT DEFAULT '[\"youtube\",\"tiktok\",\"instagram\",\"facebook\"]'",
]


def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


_con = None


def con():
    global _con
    if _con is None:
        _con = connect()
        _con.executescript(SCHEMA)
        for sql in MIGRATIONS:
            try:
                _con.execute(sql)
            except sqlite3.OperationalError:
                pass  # stĺpec už existuje
        _con.commit()
    return _con


def q(sql, args=()):
    with _lock:
        return [dict(r) for r in con().execute(sql, args).fetchall()]


def one(sql, args=()):
    rows = q(sql, args)
    return rows[0] if rows else None


def run(sql, args=()):
    with _lock:
        cur = con().execute(sql, args)
        con().commit()
        return cur.lastrowid


def get_setting(key, default=None):
    r = one("SELECT value FROM settings WHERE key=?", (key,))
    if not r:
        return default
    try:
        return json.loads(r["value"])
    except Exception:
        return r["value"]


def set_setting(key, value):
    run("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value)))
