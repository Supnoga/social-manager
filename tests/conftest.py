import os
import sys
import tempfile
from pathlib import Path

import pytest

# testy nikdy nesiahnu na skutočné dáta ani na siete
os.environ["SM_DATA_DIR"] = tempfile.mkdtemp(prefix="sm-test-")
os.environ.pop("SM_AI_BACKEND", None)
os.environ.pop("SM_DRY_RUN", None)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr(db, "_con", None)
    yield
    if db._con is not None:
        db._con.close()
