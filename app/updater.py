"""Aktualizácie bez preinštalovania. Dáta (priečinok data) a nastavenia ostávajú.

Spôsoby:
1) automaticky pri spustení z GitHubu (ak je v Nastaveniach zadaný repozitár, napr. 'meno/social-manager'),
2) ručne: v Nastaveniach pretiahneš nový zip.
"""
import io
import os
import shutil
import time
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


PREV = db.DATA_DIR / "prev_code"      # kópia kódu pred poslednou aktualizáciou (na návrat späť)
SKIP_FILE = db.DATA_DIR / "skip_version"  # verzia, po ktorej appka nenabehla (zapisuje aj mac/run.sh)


def bad_versions():
    bad = set(db.get_setting("update_bad", []) or [])
    try:
        if SKIP_FILE.exists():
            bad |= {x.strip() for x in SKIP_FILE.read_text().split() if x.strip()}
    except Exception:
        pass
    return bad


def _backup(names):
    """Odloží terajší kód (len to, čo nová verzia prepíše), aby sa dalo vrátiť späť."""
    shutil.rmtree(PREV, ignore_errors=True)
    PREV.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = BASE / name
        if name in KEEP or not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, PREV / name)
        else:
            shutil.copy2(src, PREV / name)


def _copy_dir(src, dest):
    """Prepíše priečinok kódu. Keď sa kopírovanie raz nepodarí (súbor práve číta iný proces),
    skúsi to znova a prepisuje na mieste, aby appka neostala s polovičným kódom (17.11.)."""
    shutil.rmtree(dest, ignore_errors=True)
    for i in range(3):
        try:
            shutil.copytree(src, dest, dirs_exist_ok=True)
            return
        except shutil.Error:
            if i == 2:
                raise
            time.sleep(2)


def restore_prev():
    """Vráti kód spred poslednej aktualizácie. Vráti verziu, na ktorú sa vrátil, alebo ''."""
    if not (PREV / "app" / "main.py").exists():
        return ""
    for item in PREV.iterdir():
        dest = BASE / item.name
        if item.is_dir():
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    for f in list(BASE.glob("*.command")) + list(BASE.glob("*.sh")) + list((BASE / "mac").glob("*.sh")):
        try:
            f.chmod(0o755)
        except Exception:
            pass
    return version()


def _starts():
    """Skúška novej verzie ešte pred reštartom: dá sa appka vôbec načítať? Vráti '' alebo text chyby."""
    try:
        r = subprocess.run([sys.executable, "-c", "import app.main"], cwd=str(BASE), capture_output=True, text=True,
                           timeout=300, stdin=subprocess.DEVNULL, env=dict(os.environ, SM_VERIFY="1"))
    except Exception:
        return ""  # skúška sa nedala urobiť (napr. pomalý Mac): verziu nezahadzuj, poistkou ostáva mac/run.sh
    return "" if r.returncode == 0 else (r.stderr or r.stdout or "neznáma chyba").strip()[-300:]


def apply_zip(data: bytes):
    """Rozbalí nový zip a prepíše kód appky. Dáta nechá tak. Starý kód si odloží; keď sa nová verzia nedá
    spustiť, hneď ho vráti späť a tú verziu už neskúša."""
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(io.BytesIO(data)).extractall(tmp)
        roots = [p.parent for p in Path(tmp).rglob("app/main.py")]
        if not roots:
            raise ValueError("Toto nie je zip so Social Manager appkou.")
        src = roots[0].parent
        new_ver = (src / "VERSION").read_text().strip() if (src / "VERSION").exists() else "?"
        try:
            _backup([i.name for i in src.iterdir()])
            have_prev = True
        except Exception:
            have_prev = False
        for item in src.iterdir():
            if item.name in KEEP:
                continue
            dest = BASE / item.name
            if item.is_dir():
                _copy_dir(item, dest)
            else:
                shutil.copy2(item, dest)
    for f in list(BASE.glob("*.command")) + list(BASE.glob("*.sh")):  # zip nenesie práva na spustenie
        try:
            f.chmod(0o755)
        except Exception:
            pass
    # doinštaluje nové knižnice, ak pribudli
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(BASE / "requirements.txt")],
                       capture_output=True, timeout=900, stdin=subprocess.DEVNULL)
    except Exception:
        pass  # run.sh pri reštarte skúsi knižnice doinštalovať znova
    err = _starts() if have_prev else ""
    if err:
        back = restore_prev()
        db.set_setting("update_bad", sorted(bad_versions() | {new_ver}))
        raise ValueError(f"Verzia {new_ver} sa nedá spustiť, ostáva {back}: {err}")
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
        if _vt(remote) <= _vt(version()) or remote in bad_versions():
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


def background_checker(is_busy, every_minutes=15, drain=None):
    """Každých 15 minút (podľa hodín, nie spánku Macu) pozrie, či je nová verzia. Keď appka práve nič nerobí,
    aktualizuje sa a reštartuje sama. Prehliadač sa potom obnoví sám."""
    import logging
    import threading
    import time

    def loop():
        time.sleep(90)
        last = 0
        while True:
            try:
                if time.time() - last >= every_minutes * 60 and db.get_setting("auto_update", True):
                    last = time.time()
                    r = check_github(apply=False)
                    db.set_setting("update_last", {"ts": time.strftime("%Y-%m-%d %H:%M"), "result": r.get("error") or
                                                   (f"nová verzia {r['available']}" if r.get("available") else "aktuálna")})
                    if r.get("available"):
                        # výroba dokončí rozrobené video a nové nezačne; po reštarte pokračuje sama (drain(False) = pustiť ďalej)
                        if drain:
                            drain(True)
                        updated = False
                        try:
                            for _ in range(90):
                                if not is_busy():
                                    break
                                time.sleep(60)
                            if not is_busy():
                                res = check_github(apply=True)
                                if res.get("updated"):
                                    logging.getLogger("app").warning("Aktualizované na %s, reštartujem", res["updated"])
                                    updated = True
                                    restart()
                                    return
                        finally:
                            if drain and not updated:
                                drain(False)
            except Exception as e:
                logging.getLogger("app").warning("Aktualizácia zlyhala: %r", e)
                db.set_setting("update_last", {"ts": time.strftime("%Y-%m-%d %H:%M"), "result": f"chyba: {e}"[:200]})
            time.sleep(60)
    threading.Thread(target=loop, daemon=True).start()
