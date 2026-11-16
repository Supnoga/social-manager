"""Kde sú v zábere tváre a kde je strih: podklad pre orez videa na výšku.
    python faces.py <video> <t0> <t1> <výstup.json> [ffmpeg]
Výstup: {"w","h","samples":[{"t","diff","faces":[[cx,cy,šírka]]}]} (súradnice 0..1). Posledný riadok {"n"} alebo {"error"}."""
import json
import sys
from pathlib import Path


def frames_ffmpeg(ff, src, t0, t1, step, sw):
    """Snímky cez ffmpeg (vie každý kodek, aj AV1 bez hardvérovej podpory): (šírka, výška zdroja, zmenšené snímky BGR)."""
    import subprocess
    import numpy as np
    r = subprocess.run([ff, "-hide_banner", "-i", src], capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL)
    import re
    m = re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", r.stderr)
    if not m:
        return 0, 0, []
    w, h = int(m.group(1)), int(m.group(2))
    sh = max(2, int(h * sw / w) // 2 * 2)
    raw = subprocess.run([ff, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", src, "-an",
                          "-vf", f"fps={1 / step:.4f},scale={sw}:{sh}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, stdin=subprocess.DEVNULL).stdout
    n = len(raw) // (sw * sh * 3)
    return w, h, [np.frombuffer(raw, dtype=np.uint8, count=sw * sh * 3, offset=i * sw * sh * 3).reshape(sh, sw, 3) for i in range(n)]


def frames_cv(src, t0, t1, step, sw):
    import cv2
    cap = cv2.VideoCapture(src)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    out, t = [], t0
    if w and h:
        sh = max(1, int(h * sw / w))
        while t < t1:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, fr = cap.read()
            if not ok:
                break
            out.append(cv2.resize(fr, (sw, sh)))
            t += step
    cap.release()
    return w, h, out


def main():
    src, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    ff = sys.argv[5] if len(sys.argv) > 5 else ""
    try:
        import cv2
        import numpy as np
        step, sw = 0.25, 640
        w, h, frames = frames_ffmpeg(ff, src, t0, t1, step, sw) if ff else (0, 0, [])
        if not frames:
            w, h, frames = frames_cv(src, t0, t1, step, sw)
        if not w or not h or not frames:
            raise RuntimeError("video sa nedá prečítať")
        model = str(Path(__file__).with_name("face_yunet.onnx"))   # YuNet (OpenCV Zoo, licencia MIT)
        prev, samples = None, []
        sh = frames[0].shape[0]
        det = cv2.FaceDetectorYN.create(model, "", (sw, sh), 0.6, 0.3, 50)
        for k, small in enumerate(frames):
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            tiny = cv2.resize(gray, (64, 36)).astype("int16")
            diff = float(np.abs(tiny - prev).mean()) if prev is not None else 0.0
            prev = tiny
            _, found = det.detect(small)
            faces = []
            for f in (found if found is not None else []):
                x, y, fw, fh = (float(v) for v in f[:4])
                if fw >= sw * 0.03:
                    faces.append([round((x + fw / 2) / sw, 4), round((y + fh / 2) / sh, 4), round(fw / sw, 4)])
            samples.append({"t": round(k * step, 3), "diff": round(diff, 2), "faces": faces})
        with open(out, "w") as f:
            json.dump({"w": w, "h": h, "samples": samples}, f)
        print(json.dumps({"n": len(samples)}))
    except Exception as e:
        print(json.dumps({"error": str(e)[-300:]}))


if __name__ == "__main__":
    main()
