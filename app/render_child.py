"""Samostatný proces na skladanie jedného videa (snímky z prehliadača do ffmpeg).

Beží s nižšou prioritou, takže Mac dá prednosť appke (stránky sa načítajú hneď) a skladanie ide popri tom.
Vstup: úloha (pickle) na stdin. Výsledok (pickle) do súboru, ktorého cestu dostane ako argument."""
import os
import pickle
import sys


def main():
    out = sys.argv[1]
    try:
        os.nice(10)
    except Exception:
        pass
    job = pickle.loads(sys.stdin.buffer.read())
    try:
        from app import explainer
        cover, over = explainer._capture(job)
        res = {"cover": cover, "over": over}
    except Exception as e:
        res = {"error": str(e)[:1000] or e.__class__.__name__}
    with open(out, "wb") as f:
        pickle.dump(res, f)


if __name__ == "__main__":
    main()
