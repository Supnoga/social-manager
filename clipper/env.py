"""Vlastné nástroje Clippera vo vlastnom Pythone (data/clipper/venv): sťahovanie zdrojov, prepis reči, hľadanie tvárí.
Nič z toho sa neinštaluje do Social Managera, takže ho to nemôže rozbiť. Všetko je zadarmo a beží na tomto počítači."""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import store

VENV = store.DIR / "venv"
TOOLS = Path(__file__).resolve().parent / "tools"
PKGS = ["yt-dlp", "opencv-python-headless", "numpy", "faster-whisper"]
STATE = {"installing": False, "error": "", "step": ""}


def py():
    return VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def ready():
    return (VENV / ".ok").exists() and py().exists()


def _sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL,
                       start_new_session=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "chyba").strip()[-400:])
    return r.stdout


def ensure(wait=False):
    """Raz na pozadí pripraví nástroje (asi 400 MB). Raz za týždeň obnoví sťahovač, lebo siete sa často menia."""
    if STATE["installing"]:
        return
    if ready():
        if time.time() - float(store.get("ytdlp_at", 0) or 0) > 7 * 86400:
            store.put("ytdlp_at", time.time())
            threading.Thread(target=_refresh, daemon=True).start()
        return

    def go():
        STATE.update(installing=True, error="")
        try:
            STATE["step"] = "inštalátor"
            _sh([sys.executable, "-m", "pip", "install", "-q", "uv"])
            STATE["step"] = "vlastný Python"
            _sh([sys.executable, "-m", "uv", "venv", "--python", "3.12", "--clear", str(VENV)])
            STATE["step"] = "nástroje na strih"
            _sh([sys.executable, "-m", "uv", "pip", "install", "--python", str(py())] + PKGS, 3600)
            STATE["step"] = "skúška"
            _sh([str(py()), "-c", "import yt_dlp, cv2, numpy, faster_whisper"], 300)
            (VENV / ".ok").write_text("ok")
            store.put("ytdlp_at", time.time())
            STATE["step"] = ""
        except Exception as e:
            STATE["error"] = f"{STATE['step']}: {str(e)[-300:]}"
            print("Clipper nástroje:", STATE["error"])
        finally:
            STATE["installing"] = False
    if wait:
        go()
    else:
        threading.Thread(target=go, daemon=True).start()


def _refresh():
    try:
        _sh([sys.executable, "-m", "uv", "pip", "install", "--python", str(py()), "-U", "yt-dlp"], 900)
    except Exception as e:
        print("Clipper: obnova sťahovača:", str(e)[-200:])


def tool(name, args, timeout=3600):
    """Spustí nástroj (clipper/tools/<name>.py) vo vlastnom Pythone a vráti jeho JSON výsledok (posledný riadok výstupu)."""
    if not ready():
        raise RuntimeError("Nástroje Clippera sa ešte pripravujú" + (": " + STATE["error"] if STATE["error"] else "."))
    r = subprocess.run([str(py()), str(TOOLS / f"{name}.py")] + [str(a) for a in args], capture_output=True, text=True,
                       errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True, timeout=timeout)
    lines = [ln for ln in (r.stdout or "").strip().splitlines() if ln.strip()]
    if r.returncode != 0 or not lines:
        raise RuntimeError(f"{name}: " + ((r.stderr or r.stdout or "bez výstupu").strip()[-400:]))
    try:
        out = json.loads(lines[-1])
    except Exception:
        raise RuntimeError(f"{name}: nečitateľný výsledok: {lines[-1][:200]}")
    if isinstance(out, dict) and out.get("error"):
        raise RuntimeError(f"{name}: {out['error']}")
    return out
