"""Vyrobí zabudovanú hudbu a zvukové efekty appky (app/sound). Spúšťa sa len pri vývoji, nie v appke.
Všetko je vypočítané (syntetizátor v numpy), takže zvuky sú naše vlastné a bez licencií.
Použitie: python tools/make_sounds.py  (treba numpy a ffmpeg)."""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "app" / "sound"
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


class Track:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.dry = np.zeros((2, self.n))    # priamo
        self.wet = np.zeros((2, self.n))    # do dozvuku
        self.dly = np.zeros((2, self.n))    # do ozveny

    def add(self, buf, t, sig, pan=0.0, gain=1.0):
        """Pridá mono signál na čas t (s), koniec sa pretočí na začiatok (slučka bez švu)."""
        i = int(t * SR) % self.n
        idx = (i + np.arange(len(sig))) % self.n
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        np.add.at(buf[0], idx, sig * gain * l)
        np.add.at(buf[1], idx, sig * gain * r)


def env(n, a, r):
    e = np.ones(n)
    a, r = int(a * SR), int(r * SR)
    if a:
        e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if r:
        e[-r:] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def pad_note(m, dur, cutoff=1400.0, detune=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m) * 2 ** (detune / 1200)
    s = np.zeros(n)
    k = 1
    while k * f < 6000:
        s += np.sin(2 * np.pi * k * f * t + rng.uniform(0, 6.28)) / k / (1 + (k * f / cutoff) ** 2)
        k += 1
    vib = 1 + 0.04 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6.28))
    return s * vib * env(n, min(0.9, dur * 0.3), min(1.4, dur * 0.4))


def pluck(m, dur=0.7, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.zeros(n)
    for k in range(1, 9):
        if k * f > 9000:
            break
        s += np.sin(2 * np.pi * k * f * t) / k ** (1.5 / bright) * np.exp(-t * (5 + 3.2 * k))
    s[:96] *= np.linspace(0, 1, 96)
    return s


def bell(m, dur=2.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t + 1.2 * np.exp(-4 * t) * np.sin(2 * np.pi * 3.0 * f * t)) * np.exp(-2.4 * t)
    s += 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-4 * t)
    s[:144] *= np.linspace(0, 1, 144)
    return s


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-6 * t)
    return s * env(n, 0.012, min(0.12, dur * 0.4)) * np.exp(-1.2 * t / max(dur, 0.1))


def kick(soft=1.0):
    n = int(0.26 * SR)
    t = np.arange(n) / SR
    f = 46 + 70 * np.exp(-t * 34)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 15 / soft)


def noise_hit(dur, lo, hi, decay):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= np.exp(-0.5 * ((np.log(fr + 1) - np.log((lo * hi) ** 0.5)) / (np.log(hi / lo) / 2.2)) ** 2)
    y = np.fft.irfft(X, n)
    y /= np.abs(y).max() + 1e-9
    t = np.arange(n) / SR
    y *= np.exp(-t * decay)
    y[:48] *= np.linspace(0, 1, 48)
    return y


def reverb(x, secs=2.2, damp=3500.0, pre=0.018):
    """Dozvuk: kruhová konvolúcia s umelou ozvenou miestnosti (chvost sa pretočí na začiatok)."""
    n = x.shape[1]
    out = np.zeros_like(x)
    for c in range(2):
        m = int(secs * SR)
        t = np.arange(m) / SR
        ir = rng.standard_normal(m) * np.exp(-t * 6.9 / secs)
        I = np.fft.rfft(ir)
        fr = np.fft.rfftfreq(m, 1 / SR)
        I *= 1 / (1 + (fr / damp) ** 2) * (fr > 180)
        ir = np.fft.irfft(I, m)
        ir = np.concatenate([np.zeros(int(pre * SR)), ir])
        ir /= np.sqrt((ir ** 2).sum())
        h = np.zeros(n)
        h[:len(ir)] = ir[:n]
        out[c] = np.fft.irfft(np.fft.rfft(x[c]) * np.fft.rfft(h), n)
    return out


def pingpong(x, delay, fb=0.42, n_taps=6):
    out = np.zeros_like(x)
    mono = x.mean(axis=0)
    d = int(delay * SR)
    for k in range(1, n_taps + 1):
        out[k % 2] += np.roll(mono, d * k) * fb ** (k - 1)
    return out


def lowpass(x, fc):
    X = np.fft.rfft(x, axis=-1)
    fr = np.fft.rfftfreq(x.shape[-1], 1 / SR)
    return np.fft.irfft(X / (1 + (fr / fc) ** 4), x.shape[-1], axis=-1)


def highpass(x, fc):
    X = np.fft.rfft(x, axis=-1)
    fr = np.fft.rfftfreq(x.shape[-1], 1 / SR)
    return np.fft.irfft(X * (fr / fc) ** 2 / (1 + (fr / fc) ** 2), x.shape[-1], axis=-1)


def finish(tr, delay, rev=0.5, dl=0.35):
    mix = tr.dry + dl * pingpong(tr.dly, delay) + rev * reverb(tr.wet + 0.5 * dl * pingpong(tr.dly, delay))
    mix = highpass(mix, 32)
    mix /= np.abs(mix).max() + 1e-9
    mix = np.tanh(mix * 1.4) / np.tanh(1.4)
    return mix * 0.7


def save(name, x, loud=-16.0, fmt="ogg"):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / (name + ".tmp.wav")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x.T, -1, 1) * 32767).astype("<i2").tobytes())
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(tmp), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    cur = float(r.stderr.split("I:")[-1].split("LUFS")[0])
    gain = loud - cur
    codec = ["-c:a", "libvorbis", "-q:a", "3"] if fmt == "ogg" else ["-c:a", "pcm_s16le"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false", *codec,
                    str(OUT / f"{name}.{fmt}")], check=True)
    tmp.unlink()
    print(name, f"{x.shape[1] / SR:.1f}s", f"{cur:.1f} LUFS -> {loud}")


# ---------- skladby ----------
def chords_pad(tr, prog, bar, bars_per, passes, gain=0.16, cutoff=1300):
    T = 0.0
    for _ in range(passes):
        for ch in prog:
            d = bar * bars_per
            for j, m in enumerate(ch):
                for det, pan in ((-7, -0.6), (7, 0.6)):
                    s = pad_note(m, d + 1.2, cutoff, det)
                    tr.add(tr.dry, T - 0.25, s, pan * (0.5 + 0.5 * (j % 2)), gain * 0.6)
                    tr.add(tr.wet, T - 0.25, s, pan, gain * 0.5)
            T += d


def calm():
    """Pokojná technická: 92 BPM, a mol. Podklad + jemné arpeggio, od druhého kola tichý rytmus."""
    bpm, bars_per = 92, 2
    beat = 60 / bpm
    bar = beat * 4
    prog = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 69], [48, 55, 60, 64, 71], [55, 59, 62, 64, 69]]  # Am9 Fmaj7 Cmaj7 G6
    passes = 4
    tr = Track(bar * bars_per * len(prog) * passes)
    chords_pad(tr, prog, bar, bars_per, passes)
    T = 0.0
    for p in range(passes):
        for ci, ch in enumerate(prog):
            tones = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[2] + 24, ch[4] + 12, ch[3] + 12, ch[2] + 12]
            for b in range(bars_per):
                for e in range(8):
                    t = T + b * bar + e * beat / 2
                    vel = (1.0 if e % 4 == 0 else 0.6 if e % 2 == 0 else 0.42) * (0.75 if p == 0 else 1.0)
                    if p == 3 and ci < 2 and e % 2:
                        continue
                    s = pluck(tones[(e + b * 3) % 8], 0.8, 0.9)
                    tr.add(tr.dry, t, s, 0.25 * (-1) ** e, 0.11 * vel)
                    tr.add(tr.dly, t, s, 0, 0.07 * vel)
                    tr.add(tr.wet, t, s, 0, 0.05 * vel)
                if p >= 1 and not (p == 3 and ci < 2):
                    for q in (0, 2):
                        tr.add(tr.dry, T + b * bar + q * beat, kick(1.0), 0, 0.30)
                    tr.add(tr.dry, T + b * bar + 2.5 * beat, kick(0.8), 0, 0.14)
                    for q in range(4):
                        tr.add(tr.dry, T + b * bar + (q + 0.5) * beat, noise_hit(0.07, 6000, 12000, 70), 0.3, 0.035)
                    tr.add(tr.dry, T + b * bar, bass(ch[0] - 24, beat * 1.8), 0, 0.26)
                    tr.add(tr.dry, T + b * bar + 2.5 * beat, bass(ch[0] - 24, beat * 1.2), 0, 0.2)
            if p >= 2:
                mel = [ch[4] + 12, ch[3] + 12] if ci % 2 == 0 else [ch[2] + 24, ch[4] + 12]
                for k, m in enumerate(mel):
                    s = bell(m)
                    tr.add(tr.wet, T + k * bar + beat * 1.5, s, 0.4 * (-1) ** k, 0.08)
                    tr.add(tr.dly, T + k * bar + beat * 1.5, s, 0, 0.05)
            T += bar * bars_per
    return finish(tr, beat * 0.75)


def drive():
    """Energickejšia: 114 BPM, C dur. Krátke tóny v rytme, basa, jemný rytmus."""
    bpm, bars_per = 114, 2
    beat = 60 / bpm
    bar = beat * 4
    prog = [[48, 55, 60, 64, 67], [43, 55, 59, 62, 67], [45, 57, 60, 64, 67], [41, 53, 57, 60, 67]]  # C G Am F (spoločný tón g)
    passes = 5
    tr = Track(bar * bars_per * len(prog) * passes)
    chords_pad(tr, prog, bar, bars_per, passes, gain=0.10, cutoff=1700)
    pat = [1, 0, 0.5, 1, 0, 0.6, 1, 0.45]
    T = 0.0
    for p in range(passes):
        full = p >= 1 and p != 3
        for ci, ch in enumerate(prog):
            for b in range(bars_per):
                for e in range(8):
                    t = T + b * bar + e * beat / 2
                    if pat[e]:
                        for m in ch[2:5]:
                            s = pluck(m + 12, 0.32, 1.25)
                            tr.add(tr.dry, t, s, 0.35 * (-1) ** e, 0.055 * pat[e])
                            tr.add(tr.wet, t, s, 0, 0.02 * pat[e])
                    if e in (0, 3, 6) or (full and e == 7):
                        s = pluck(ch[4] + 12 + (0 if e != 6 else -3 if ci in (0, 2) else -5), 0.6, 1.0)
                        tr.add(tr.dly, t, s, 0, 0.05)
                    if full:
                        tr.add(tr.dry, t, bass(ch[0] - 12, beat * 0.42), 0, 0.2 if e % 2 == 0 else 0.13)
                if p >= 1:
                    for q in range(4):
                        if full or q in (0, 2):
                            tr.add(tr.dry, T + b * bar + q * beat, kick(0.9), 0, 0.33)
                        if full:
                            tr.add(tr.dry, T + b * bar + (q + 0.5) * beat, noise_hit(0.06, 7000, 13000, 80), -0.3, 0.04)
                    if full:
                        for q in (1, 3):
                            c = noise_hit(0.16, 900, 3500, 32)
                            tr.add(tr.dry, T + b * bar + q * beat, c, 0.1, 0.075)
                            tr.add(tr.wet, T + b * bar + q * beat, c, 0, 0.05)
            T += bar * bars_per
    return finish(tr, beat * 0.75, rev=0.4, dl=0.4)


def ambient():
    """Ambientná bez rytmu: 66 BPM, D dur. Podklad a riedke zvonivé tóny."""
    bpm, bars_per = 66, 2
    beat = 60 / bpm
    bar = beat * 4
    prog = [[50, 57, 61, 64, 66], [47, 54, 57, 62, 66], [43, 55, 59, 62, 66], [45, 57, 61, 64, 69]]  # Dmaj9 Bm7 Gmaj7 A6
    passes = 3
    tr = Track(bar * bars_per * len(prog) * passes)
    chords_pad(tr, prog, bar, bars_per, passes, gain=0.2, cutoff=1100)
    T = 0.0
    for p in range(passes):
        for ci, ch in enumerate(prog):
            tr.add(tr.dry, T, bass(ch[0] - 12, bar * 1.6) * 0.8, 0, 0.16)
            seq = [(0.0, ch[4] + 12), (1.5, ch[2] + 12), (3.0, ch[3] + 12), (4.5, ch[4] + 12), (6.0, ch[1] + 12), (7.0, ch[3] + 24)]
            for k, (bt, m) in enumerate(seq):
                if p == 0 and k % 2:
                    continue
                s = bell(m, 3.0)
                tr.add(tr.wet, T + bt * beat, s, 0.5 * (-1) ** k, 0.085)
                tr.add(tr.dly, T + bt * beat, s, 0, 0.06)
                tr.add(tr.dry, T + bt * beat, s, 0.3 * (-1) ** k, 0.03)
            T += bar * bars_per
    return finish(tr, beat * 1.5, rev=0.75, dl=0.4)


# ---------- efekty ----------
def whoosh(dur=0.5, up=True, seed=1):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = r.standard_normal(n)
    out = np.zeros(n)
    # pásmový filter s pohyblivým stredom: po krátkych oknách
    win = 2048
    hop = 256
    w = np.hanning(win)
    xp = np.concatenate([np.zeros(win), x, np.zeros(win)])
    acc = np.zeros(len(xp))
    for i in range(0, len(xp) - win, hop):
        pos = np.clip((i - win / 2) / n, 0, 1)
        k = pos if up else 1 - pos
        fc = 350 * (5200 / 350) ** (np.sin(k * np.pi / 2) ** 1.3)
        X = np.fft.rfft(xp[i:i + win] * w)
        fr = np.fft.rfftfreq(win, 1 / SR)
        X *= np.exp(-0.5 * ((np.log(fr + 1) - np.log(fc)) / 0.45) ** 2)
        acc[i:i + win] += np.fft.irfft(X, win) * w
    out = acc[win:win + n]
    peak = 0.62 if up else 0.3
    e = np.where(t < dur * peak, (t / (dur * peak)) ** 2.2, np.exp(-(t - dur * peak) * 14))
    out = out / (np.abs(out).max() + 1e-9) * e
    pan = np.linspace(-0.6, 0.6, n) * (1 if seed % 2 else -1)
    st = np.stack([out * np.cos((pan + 1) * np.pi / 4), out * np.sin((pan + 1) * np.pi / 4)])
    tail = np.concatenate([st, np.zeros((2, int(0.5 * SR)))], axis=1)
    return (tail + 0.35 * reverb(tail, 0.6, 5000)) * 0.8


def hit():
    """Jemný úder na začiatok: hlboký tón + krátky šum s dozvukom."""
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 52 + 60 * np.exp(-t * 26)
    low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5)
    air = np.zeros(n)
    a = noise_hit(0.5, 1500, 7000, 9)
    air[:len(a)] = a
    st = np.stack([low * 0.9 + air * 0.16, low * 0.9 + air * 0.16])
    wet = reverb(np.stack([air, air]), 1.2, 4500)
    out = st + 0.4 * wet
    out[:, -4800:] *= np.linspace(1, 0, 4800)
    return out / np.abs(out).max() * 0.8


if __name__ == "__main__":
    only = set(sys.argv[1:])
    jobs = {"hudba-pokojna": calm, "hudba-energicka": drive, "hudba-ambient": ambient}
    for name, fn in jobs.items():
        if not only or name in only:
            save(name, fn(), -16.0, "ogg")
    fx = {"fx-prechod-1": lambda: whoosh(0.5, True, 1), "fx-prechod-2": lambda: whoosh(0.42, True, 2),
          "fx-uder": hit}
    for name, fn in fx.items():
        if not only or name in only:
            save(name, fn(), -20.0, "ogg")
