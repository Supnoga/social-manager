"""Kde sú v zábere tváre a kde je strih: podklad pre orez videa na výšku.
    python faces.py <video> <t0> <t1> <výstup.json>
Výstup: {"w","h","samples":[{"t","diff","faces":[[cx,cy,šírka]]}]} (súradnice 0..1). Posledný riadok {"n"} alebo {"error"}."""
import json
import sys
from pathlib import Path


def main():
    src, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    try:
        import cv2
        import numpy as np
        cap = cv2.VideoCapture(src)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if not w or not h:
            raise RuntimeError("video sa nedá otvoriť")
        model = str(Path(__file__).with_name("face_yunet.onnx"))   # YuNet (OpenCV Zoo, licencia MIT)
        step, t, prev, samples, det = 0.25, t0, None, [], None
        sw = 640
        sh = max(1, int(h * sw / w))
        while t < t1:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, fr = cap.read()
            if not ok:
                break
            small = cv2.resize(fr, (sw, sh))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            tiny = cv2.resize(gray, (64, 36)).astype("int16")
            diff = float(np.abs(tiny - prev).mean()) if prev is not None else 0.0
            prev = tiny
            if det is None:
                det = cv2.FaceDetectorYN.create(model, "", (sw, sh), 0.6, 0.3, 50)
            _, found = det.detect(small)
            faces = []
            for f in (found if found is not None else []):
                x, y, fw, fh = (float(v) for v in f[:4])
                if fw >= sw * 0.03:
                    faces.append([round((x + fw / 2) / sw, 4), round((y + fh / 2) / sh, 4), round(fw / sw, 4)])
            samples.append({"t": round(t - t0, 3), "diff": round(diff, 2), "faces": faces})
            t += step
        cap.release()
        with open(out, "w") as f:
            json.dump({"w": w, "h": h, "samples": samples}, f)
        print(json.dumps({"n": len(samples)}))
    except Exception as e:
        print(json.dumps({"error": str(e)[-300:]}))


if __name__ == "__main__":
    main()
