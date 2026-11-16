"""Lokálny hlas (Kokoro) ako samostatný program vo vlastnom Pythone (data/kokoro/venv).

Appka môže bežať na staršom Pythone, než aký hlas potrebuje, preto ho nevolá priamo:
    python tts_local.py <priečinok s modelom> <hlas> <jazyk en-us|en-gb> <rýchlosť> <vety.json> <výstupný priečinok>
vety.json = zoznam viet; do výstupného priečinka uloží 0.wav, 1.wav, ... (mono, 16 bit)."""
import json
import sys
import wave
from pathlib import Path


def main():
    model, voice, lang, speed, src, out = sys.argv[1:7]
    import numpy as np
    from kokoro_onnx import Kokoro
    k = Kokoro(str(Path(model) / "kokoro-v1.0.onnx"), str(Path(model) / "voices-v1.0.bin"))
    for i, text in enumerate(json.loads(Path(src).read_text(encoding="utf-8"))):
        smp, sr = k.create(text, voice=voice, speed=float(speed), lang=lang)
        pcm = (np.clip(smp, -1, 1) * 32767).astype("<i2").tobytes()
        with wave.open(str(Path(out) / f"{i}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(int(sr))
            w.writeframes(pcm)
    print("OK")


if __name__ == "__main__":
    main()
