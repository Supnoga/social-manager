"""Aktualizácie bez preinštalovania. Dáta (priečinok data) a nastavenia ostávajú.

Spôsoby:
1) automaticky pri spustení z GitHubu (ak je v Nastaveniach zadaný repozitár, napr. 'meno/social-manager'),
2) ručne: v Nastaveniach pretiahneš nový zip.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import httpx

from . import db

BASE = db.BASE_DIR
KEEP = {"data", "venv", ".git"}
DEFAULT_REPO = "Supnoga/social-manager"  # odtiaľ si appka sama sťahuje nové verzie


def version():
    f = BASE / "VERSION"
    return f.read_text().strip() if f.exists() else "0"


def _vt(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0,)


def apply_zip(data: bytes):
    """Rozbalí nový zip a prepíše kód appky. Dáta nechá tak."""
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(io.BytesIO(data)).extractall(tmp)
        roots = [p.parent for p in Path(tmp).rglob("app/main.py")]
        if not roots:
            raise ValueError("Toto nie je zip so Social Manager appkou.")
        src = roots[0].parent
        new_ver = (src / "VERSION").read_text().strip() if (src / "VERSION").exists() else "?"
        for item in src.iterdir():
            if item.name in KEEP:
                continue
            dest = BASE / item.name
            if item.is_dir():
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    # doinštaluje nové knižnice, ak pribudli
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(BASE / "requirements.txt")],
                   capture_output=True)
    return new_ver


def check_github(apply=True):
    repo = (db.get_setting("update_repo", "") or DEFAULT_REPO).strip().strip("/")
    if not repo:
        return {"configured": False}
    if repo.startswith("https://github.com/"):
        repo = repo[len("https://github.com/"):]
    branch = db.get_setting("update_branch", "main")
    token = (db.get_setting("update_token", "") or "").strip()
    with httpx.Client(timeout=60, follow_redirects=True) as c:
        if token:  # súkromný repozitár: cez GitHub API s kľúčom len na čítanie
            h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw"}
            r = c.get(f"https://api.github.com/repos/{repo}/contents/VERSION", params={"ref": branch}, headers=h)
        else:
            r = c.get(f"https://raw.githubusercontent.com/{repo}/{branch}/VERSION")
        if r.status_code != 200:
            return {"configured": True, "error": "Repozitár sa nedá prečítať (je súkromný? vlož kľúč v Pokročilých)."}
        remote = r.text.strip()
        if _vt(remote) <= _vt(version()):
            return {"configured": True, "latest": True, "version": version()}
        if not apply:
            return {"configured": True, "available": remote}
        if token:
            z = c.get(f"https://api.github.com/repos/{repo}/zipball/{branch}", headers={"Authorization": f"Bearer {token}"})
        else:
            z = c.get(f"https://github.com/{repo}/archive/refs/heads/{branch}.zip")
        z.raise_for_status()
    return {"configured": True, "updated": apply_zip(z.content)}


def restart():
    """Ukončí appku s kódom 3 - spúšťací skript ju hneď znova zapne už s novým kódom."""
    import threading
    threading.Timer(1.0, lambda: os._exit(3)).start()


def background_checker(is_busy, every_hours=4):
    """Každých pár hodín pozrie, či je nová verzia. Keď appka práve nič nerobí, aktualizuje sa a reštartuje."""
    import threading
    import time

    def loop():
        while True:
            time.sleep(every_hours * 3600)
            try:
                if not db.get_setting("auto_update", True):
                    continue
                if check_github(apply=False).get("available"):
                    for _ in range(60):
                        if not is_busy():
                            break
                        time.sleep(60)
                    if not is_busy() and check_github(apply=True).get("updated"):
                        restart()
            except Exception:
                pass
    threading.Thread(target=loop, daemon=True).start()
