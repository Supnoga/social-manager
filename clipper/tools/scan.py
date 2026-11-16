"""Kde sa vo videu niečo deje: hlasitosť, pohyb a strihy po sekundách. Všetko počíta tento počítač, bez AI.
    python scan.py <video> <výstup.json> <ffmpeg>
Výstup: {"dur","loud":[dB za sekundu],"motion":[pohyb za sekundu],"cuts":[sekundy strihov]}. Posledný riadok {"n"} alebo {"error"}."""
import json
import subprocess
import sys

FPS, W, H, RATE = 4, 96, 54, 8000


def _pipe(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)


def main():
    src, out, ff = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        import numpy as np
        # pohyb a strihy: malé čiernobiele snímky, 4 za sekundu
        p = _pipe([ff, "-v", "error", "-i", src, "-an", "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"])
        size, prev, diffs = W * H, None, []
        while True:
            buf = p.stdout.read(size)
            if len(buf) < size:
                break
            fr = np.frombuffer(buf, dtype=np.uint8).astype(np.int16)
            diffs.append(float(np.abs(fr - prev).mean()) if prev is not None else 0.0)
            prev = fr
        p.wait()
        if len(diffs) < FPS * 4:
            raise RuntimeError("video sa nedá prečítať alebo je príliš krátke")
        d = np.array(diffs)
        base = float(np.median(d)) + 1e-6
        cut_idx = [i for i in range(1, len(d)) if d[i] > max(22.0, base * 6) and d[i] > d[i - 1] * 2.5]
        cuts, last = [], -9.0
        for i in cut_idx:
            t = i / FPS
            if t - last >= 0.75:
                cuts.append(round(t, 2))
                last = t
        calm = np.minimum(d, max(22.0, base * 6))             # strih sám nie je pohyb
        n = len(d) // FPS
        motion = [round(float(calm[i * FPS:(i + 1) * FPS].mean()), 2) for i in range(n)]
        # hlasitosť: mono zvuk, priemerná sila za sekundu
        p = _pipe([ff, "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"])
        loud = []
        while True:
            buf = p.stdout.read(RATE * 2)
            if len(buf) < RATE:
                break
            a = np.frombuffer(buf[:len(buf) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768.0
            loud.append(round(float(20 * np.log10(np.sqrt((a * a).mean()) + 1e-5)), 1))
        p.wait()
        loud = (loud + [-100.0] * n)[:n]
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"dur": n, "loud": loud, "motion": motion, "cuts": cuts}, f)
        print(json.dumps({"n": n, "cuts": len(cuts)}))
    except Exception as e:
        print(json.dumps({"error": str(e)[:300]}))
        sys.exit(1)


if __name__ == "__main__":
    main()
