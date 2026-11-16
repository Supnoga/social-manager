"""Prepis reči s časmi slov priamo na tomto počítači (zadarmo, bez AI limitu).
    python stt.py <zvuk alebo video> <výstup.json> <jazyk alebo auto> <model>
Výstup: [{"w","s","e"}, ...]. Posledný riadok: {"words": počet, "lang"} alebo {"error"}."""
import json
import sys


def _load(src):
    """16 kHz mono WAV (pripravený ffmpegom) -> pole čísel; bez PyAV, ktorého novšie verzie faster-whisper nevedia otvoriť."""
    import wave
    import numpy as np
    if not src.lower().endswith(".wav"):
        return src
    with wave.open(src, "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1 or w.getframerate() != 16000:
            return src
        data = w.readframes(w.getnframes())
    return np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0


def main():
    src, out, lang, model = sys.argv[1:5]
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel(model, device="cpu", compute_type="int8")
        segs, info = m.transcribe(_load(src), language=None if lang in ("", "auto") else lang, word_timestamps=True,
                                  vad_filter=True, beam_size=1, condition_on_previous_text=False)
        words = []
        for s in segs:
            for w in (s.words or []):
                t = (w.word or "").strip()
                if t:
                    words.append({"w": t, "s": round(float(w.start), 3), "e": round(float(w.end), 3)})
        with open(out, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False)
        print(json.dumps({"words": len(words), "lang": info.language}))
    except Exception as e:
        print(json.dumps({"error": str(e)[-300:]}))


if __name__ == "__main__":
    main()
