"""Všetky programy, ktoré appka spúšťa (ffmpeg, prepis reči, lokálny hlas, sťahovanie videí…), bežia s nižšou prioritou.
Mac tak vždy dá prednosť samotnej appke: stránky a kliky odpovedajú hneď, aj keď sa popri tom skladajú videá a klipy."""
import os
import subprocess
import sys

_NICE = "/usr/bin/nice"


def _low_priority_children():
    if sys.platform == "win32" or not os.path.exists(_NICE) or getattr(subprocess.Popen, "_sm_nice", False):
        return
    try:
        if os.getpriority(os.PRIO_PROCESS, 0) > 0:   # tento proces už beží s nižšou prioritou (napr. skladanie videa)
            return
    except Exception:
        return
    base = subprocess.Popen

    class Popen(base):
        _sm_nice = True

        def __init__(self, args, *a, **kw):
            try:
                if not kw.get("shell") and not kw.get("executable") and not (len(a) >= 2 and a[1]) \
                        and os.environ.get("SM_NO_NICE") != "1":
                    if isinstance(args, (str, bytes, os.PathLike)):
                        args = [args]
                    if isinstance(args, (list, tuple)) and args and os.path.basename(str(args[0])) != "nice":
                        args = [_NICE, "-n", "10", *args]
            except Exception:
                pass
            super().__init__(args, *a, **kw)

    subprocess.Popen = Popen


_low_priority_children()
