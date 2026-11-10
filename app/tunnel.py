"""Bezplatný Cloudflare Tunnel - sprístupní appku na tvojej doméne (potrebné len pre TikTok Business).
Navonok sú dostupné LEN tajné odkazy na videá a overovací súbor, nič iné (stráži to main.py)."""
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import threading
import urllib.request

from . import db

BIN_DIR = db.DATA_DIR / "bin"
_proc = None
_state = {"running": False, "error": ""}


def _binary():
    p = shutil.which("cloudflared")
    if p:
        return p
    name = "cloudflared.exe" if os.name == "nt" else "cloudflared"
    local = BIN_DIR / name
    if local.exists():
        return str(local)
    # stiahnutie (zadarmo, oficiálne vydanie Cloudflare)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    sysname, arch = platform.system().lower(), platform.machine().lower()
    arm = arch in ("arm64", "aarch64")
    base = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    if sysname == "windows":
        urllib.request.urlretrieve(base + "cloudflared-windows-amd64.exe", local)
    elif sysname == "darwin":
        tgz = BIN_DIR / "cf.tgz"
        urllib.request.urlretrieve(base + ("cloudflared-darwin-arm64.tgz" if arm else "cloudflared-darwin-amd64.tgz"), tgz)
        with tarfile.open(tgz) as t:
            t.extractall(BIN_DIR)
        tgz.unlink()
    else:
        urllib.request.urlretrieve(base + ("cloudflared-linux-arm64" if arm else "cloudflared-linux-amd64"), local)
    if os.name != "nt":
        local.chmod(local.stat().st_mode | stat.S_IEXEC)
    return str(local)


def _run(token):
    global _proc
    try:
        b = _binary()
        _proc = subprocess.Popen([b, "tunnel", "--no-autoupdate", "run", "--token", token],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        _state.update(running=True, error="")
        err = _proc.stderr.read()
        _proc.wait()
        _state.update(running=False, error=(err or "")[-300:])
    except Exception as e:
        _state.update(running=False, error=str(e))


def start():
    token = (db.get_setting("cf_tunnel_token", "") or "").strip()
    if token and not _state["running"]:
        threading.Thread(target=_run, args=(token,), daemon=True).start()


def stop():
    if _proc and _proc.poll() is None:
        _proc.terminate()


def status():
    return dict(_state, configured=bool(db.get_setting("cf_tunnel_token", "")))
