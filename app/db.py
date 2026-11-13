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
CREATE TABLE IF NOT EXISTS footage (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, source_id TEXT, path TEXT, tags TEXT DEFAULT '', kind TEXT DEFAULT 'video', w INTEGER DEFAULT 0, h INTEGER DEFAULT 0, dur REAL DEFAULT 0, license_url TEXT DEFAULT '', used INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS competitors (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, platform TEXT, mode TEXT DEFAULT 'auto',
  url TEXT DEFAULT '', handle TEXT DEFAULT '', external_id TEXT DEFAULT '', uploads_playlist TEXT DEFAULT '', name TEXT DEFAULT '',
  followers INTEGER DEFAULT 0, lang TEXT DEFAULT '', active INTEGER DEFAULT 1, baseline_short REAL DEFAULT 0, baseline_long REAL DEFAULT 0,
  last_checked TEXT DEFAULT '', last_error TEXT DEFAULT '', UNIQUE(project_id, platform, external_id));
CREATE TABLE IF NOT EXISTS comp_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, competitor_id INTEGER, external_id TEXT, url TEXT DEFAULT '',
  title TEXT DEFAULT '', thumb TEXT DEFAULT '', published_at TEXT DEFAULT '', duration INTEGER DEFAULT 0, is_short INTEGER DEFAULT 1,
  views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0, ratio REAL DEFAULT 0, status TEXT DEFAULT '',
  last_checked TEXT DEFAULT '', UNIQUE(competitor_id, external_id));
CREATE TABLE IF NOT EXISTS trend_items (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, country TEXT DEFAULT '', lang TEXT DEFAULT '',
  term TEXT, norm TEXT, context TEXT DEFAULT '', volume REAL DEFAULT 0, url TEXT DEFAULT '', extra TEXT DEFAULT '{}',
  first_seen TEXT, last_seen TEXT, seen_count INTEGER DEFAULT 1);
CREATE INDEX IF NOT EXISTS idx_trend_seen ON trend_items(last_seen);
CREATE INDEX IF NOT EXISTS idx_trend_norm ON trend_items(source, country, norm);
CREATE TABLE IF NOT EXISTS project_keywords (project_id INTEGER, lang TEXT, core TEXT DEFAULT '[]', related TEXT DEFAULT '[]',
  negative TEXT DEFAULT '[]', entities TEXT DEFAULT '[]', updated_at TEXT DEFAULT (datetime('now','localtime')), PRIMARY KEY(project_id, lang));
CREATE TABLE IF NOT EXISTS trend_status (project_id INTEGER, cluster_key TEXT, status TEXT, label TEXT DEFAULT '',
  PRIMARY KEY(project_id, cluster_key));
CREATE TABLE IF NOT EXISTS intel_jobs (name TEXT PRIMARY KEY, last_run TEXT, next_run TEXT, last_ok INTEGER DEFAULT 1, last_error TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS fetch_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')), source TEXT,
  key TEXT DEFAULT '', ok INTEGER DEFAULT 1, units INTEGER DEFAULT 0, note TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS post_stats (post_id INTEGER PRIMARY KEY, views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0, shares INTEGER DEFAULT 0, ratio REAL DEFAULT 0, error TEXT DEFAULT '', fetched_at TEXT DEFAULT '');
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
    "ALTER TABLE scripts ADD COLUMN shots TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN glossary TEXT DEFAULT ''",
    "ALTER TABLE scripts ADD COLUMN qa TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN sources TEXT DEFAULT '[]'",
    "ALTER TABLE projects ADD COLUMN sources_summary TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN voices TEXT DEFAULT '{}'",
    "ALTER TABLE projects ADD COLUMN voice_rate REAL DEFAULT 1.0",
    "ALTER TABLE scripts ADD COLUMN voice_engine TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN source TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN ahead INTEGER DEFAULT 0",
    "ALTER TABLE ideas ADD COLUMN due_date TEXT DEFAULT ''",
    "ALTER TABLE accounts ADD COLUMN country TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN markets TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN source_ref TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN why_now TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN expires_at TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN radar_scope TEXT DEFAULT 'narrow'",
    "ALTER TABLE projects ADD COLUMN learnings TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN platforms TEXT DEFAULT '[\"youtube\",\"tiktok\",\"instagram\",\"facebook\"]'",
    "ALTER TABLE ideas ADD COLUMN template TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN banned TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN first_lang TEXT DEFAULT ''",
    "ALTER TABLE scripts ADD COLUMN post TEXT DEFAULT ''",
    "ALTER TABLE videos ADD COLUMN post TEXT DEFAULT ''",
    "ALTER TABLE projects ADD COLUMN hashtag_bank TEXT DEFAULT '{}'",
    "ALTER TABLE projects ADD COLUMN brand_tags TEXT DEFAULT ''",
    "ALTER TABLE ideas ADD COLUMN parent_id INTEGER DEFAULT 0",
    "ALTER TABLE comp_posts ADD COLUMN ratio_all REAL DEFAULT 0",
    "ALTER TABLE competitors ADD COLUMN backlog_at TEXT DEFAULT ''",
    "ALTER TABLE scripts ADD COLUMN thumb TEXT DEFAULT ''",
    "ALTER TABLE posts ADD COLUMN stash_id TEXT DEFAULT ''",
    "ALTER TABLE videos ADD COLUMN removed INTEGER DEFAULT 0",
    "ALTER TABLE videos ADD COLUMN preview_path TEXT DEFAULT ''",
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
        _accounts_to_projects(_con)
        _con.commit()
    return _con


def _accounts_to_projects(c):
    """Každý účet patrí pod konkrétny projekt (žiadne spoločné účty).
    Účty bez projektu (alebo po zmazanom projekte) dostanú projekt N2N, inak prvý projekt. Nič sa neodpája.
    Nový pripojený účet bez projektu dostane projekt, v ktorom bola naposledy otvorená stránka Účty a siete."""
    try:
        r = c.execute("SELECT id FROM projects WHERE upper(name) LIKE '%N2N%' ORDER BY id LIMIT 1").fetchone() \
            or c.execute("SELECT MIN(id) id FROM projects").fetchone()
        if r and r["id"]:
            c.execute("UPDATE accounts SET project_id=? WHERE project_id IS NULL OR project_id NOT IN (SELECT id FROM projects)", (r["id"],))
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('connect_project',?)", (json.dumps(r["id"]),))
        c.execute("""CREATE TRIGGER IF NOT EXISTS acc_default_project AFTER INSERT ON accounts WHEN NEW.project_id IS NULL BEGIN
            UPDATE accounts SET project_id = COALESCE(
              (SELECT id FROM projects WHERE id = (SELECT CAST(value AS INTEGER) FROM settings WHERE key='connect_project')),
              (SELECT MIN(id) FROM projects)) WHERE id = NEW.id;
            END""")
    except sqlite3.Error:
        pass


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
