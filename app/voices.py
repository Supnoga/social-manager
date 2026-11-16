"""Hlasy: Google Chirp 3 HD (najprirodzenejšie, 1 mil. znakov/mesiac zadarmo s poistkou limitu),
lokálny hlas Kokoro (angličtina, beží na tomto počítači, zadarmo bez limitu), Microsoft Edge neural (zadarmo bez registrácie) a Google gTTS ako posledná záloha.

ID hlasu: "google:sk-SK-Chirp3-HD-Aoede", "local:af_heart", "edge:sk-SK-ViktoriaNeural", "auto" (najlepší dostupný)."""
import asyncio
import base64
import datetime
import hashlib
import io
import json
import re
import subprocess
import sys
import threading
import time
import wave
from array import array
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from . import db, languages, pronounce, verbal

VOICE_DIR = db.MEDIA_DIR / "voice"
VOICE_DIR.mkdir(parents=True, exist_ok=True)
EDGE_CACHE = db.DATA_DIR / "edge_voices.json"
_lock = threading.Lock()

# Jazyky, pre ktoré má Google Chirp 3 HD hlasy (európske)
GOOGLE_LOCALES = {
    "sk": "sk-SK", "cs": "cs-CZ", "en": "en-GB", "de": "de-DE", "fr": "fr-FR", "es": "es-ES", "it": "it-IT",
    "pl": "pl-PL", "nl": "nl-NL", "hu": "hu-HU", "ro": "ro-RO", "bg": "bg-BG", "hr": "hr-HR", "sl": "sl-SI",
    "sr": "sr-RS", "el": "el-GR", "da": "da-DK", "sv": "sv-SE", "no": "nb-NO", "fi": "fi-FI", "et": "et-EE",
    "lv": "lv-LV", "lt": "lt-LT", "uk": "uk-UA", "ru": "ru-RU", "tr": "tr-TR",
}
# Ďalšie prízvuky toho istého jazyka (angličtina: americká popri britskej)
GOOGLE_MORE = {"en": [("en-US", "americký")]}
# (meno, pohlavie, krátky popis)
CHIRP = [
    ("Aoede", "F", "jasný, prirodzený"), ("Kore", "F", "pevný, istý"), ("Leda", "F", "mladistvý"),
    ("Zephyr", "F", "svieži, energický"), ("Callirrhoe", "F", "pokojný"), ("Despina", "F", "jemný, plynulý"),
    ("Sulafat", "F", "teplý"), ("Achernar", "F", "mäkký"), ("Autonoe", "F", "jasný"), ("Erinome", "F", "čistý"),
    ("Gacrux", "F", "zrelý"), ("Laomedeia", "F", "veselý"), ("Pulcherrima", "F", "priamy"), ("Vindemiatrix", "F", "jemný"),
    ("Charon", "M", "informatívny"), ("Puck", "M", "veselý, energický"), ("Fenrir", "M", "nadšený"),
    ("Orus", "M", "pevný"), ("Enceladus", "M", "dychový, pokojný"), ("Iapetus", "M", "čistý"),
    ("Algieba", "M", "hladký"), ("Schedar", "M", "vyrovnaný"), ("Achird", "M", "priateľský"),
    ("Algenib", "M", "chrapľavý"), ("Alnilam", "M", "pevný"), ("Rasalgethi", "M", "informatívny"),
    ("Sadachbia", "M", "živý"), ("Sadaltager", "M", "znalý"), ("Umbriel", "M", "pohodový"), ("Zubenelgenubi", "M", "uvoľnený"),
]
# Viacjazyčné Edge hlasy – výrazne prirodzenejšie, hovoria aj inými jazykmi (môžu mať jemný prízvuk)
EDGE_MULTI = [
    ("en-US-AvaMultilingualNeural", "F"), ("en-US-EmmaMultilingualNeural", "F"), ("de-DE-SeraphinaMultilingualNeural", "F"),
    ("fr-FR-VivienneMultilingualNeural", "F"), ("en-US-AndrewMultilingualNeural", "M"), ("en-US-BrianMultilingualNeural", "M"),
    ("de-DE-FlorianMultilingualNeural", "M"), ("fr-FR-RemyMultilingualNeural", "M"),
]
SAMPLE = {
    "sk": "Ahoj! Toto je ukážka môjho hlasu. Takto budú znieť tvoje videá.",
    "cs": "Ahoj! Tohle je ukázka mého hlasu. Takhle budou znít tvoje videa.",
    "en": "Hi there! This is a sample of my voice. This is how your videos will sound.",
    "de": "Hallo! Das ist eine Hörprobe meiner Stimme. So werden deine Videos klingen.",
    "fr": "Salut ! Voici un extrait de ma voix. Voilà comment sonneront tes vidéos.",
    "es": "¡Hola! Esta es una muestra de mi voz. Así sonarán tus vídeos.",
    "it": "Ciao! Questo è un esempio della mia voce. Ecco come suoneranno i tuoi video.",
    "pl": "Cześć! To jest próbka mojego głosu. Tak będą brzmieć twoje filmy.",
    "hu": "Szia! Ez a hangom mintája. Így fognak szólni a videóid.",
    "nl": "Hoi! Dit is een voorbeeld van mijn stem. Zo gaan je video's klinken.",
    "pt": "Olá! Esta é uma amostra da minha voz. É assim que os teus vídeos vão soar.",
    "ro": "Salut! Aceasta este o mostră a vocii mele. Așa vor suna videoclipurile tale.",
    "uk": "Привіт! Це зразок мого голосу. Ось так звучатимуть твої відео.",
    "ru": "Привет! Это образец моего голоса. Так будут звучать твои видео.",
    "hr": "Bok! Ovo je uzorak mog glasa. Ovako će zvučati tvoji videozapisi.",
    "sl": "Živjo! To je vzorec mojega glasu. Tako bodo zveneli tvoji videi.",
    "bg": "Здравей! Това е мостра от моя глас. Така ще звучат твоите видеа.",
    "el": "Γεια σου! Αυτό είναι ένα δείγμα της φωνής μου. Έτσι θα ακούγονται τα βίντεό σου.",
    "sv": "Hej! Det här är ett prov på min röst. Så här kommer dina videor att låta.",
    "da": "Hej! Dette er en prøve på min stemme. Sådan kommer dine videoer til at lyde.",
    "no": "Hei! Dette er en prøve på stemmen min. Slik kommer videoene dine til å høres ut.",
    "fi": "Hei! Tämä on näyte äänestäni. Tältä videosi tulevat kuulostamaan.",
    "tr": "Merhaba! Bu benim sesimden bir örnek. Videoların böyle duyulacak.",
    "et": "Tere! See on minu hääle näidis. Nii hakkavad sinu videod kõlama.",
    "lv": "Sveiki! Šis ir mana balss paraugs. Tā skanēs tavi video.",
    "lt": "Labas! Tai mano balso pavyzdys. Taip skambės tavo vaizdo įrašai.",
    "is": "Halló! Þetta er sýnishorn af röddinni minni. Svona munu myndböndin þín hljóma.",
    "sr": "Здраво! Ово је пример мог гласа. Овако ће звучати твоји видео снимци.",
    "bs": "Zdravo! Ovo je primjer mog glasa. Ovako će zvučati tvoji videi.",
    "mk": "Здраво! Ова е пример за мојот глас. Вака ќе звучат твоите видеа.",
    "sq": "Përshëndetje! Ky është një shembull i zërit tim. Kështu do të tingëllojnë videot e tua.",
}


def sample(lang):
    return SAMPLE.get(lang) or SAMPLE["en"]


# ---------- Google: kľúč, počítadlo znakov, poistka ----------
FREE_CHARS = 1_000_000   # Chirp 3 HD zadarmo mesačne
PRICE_PER_M = 30.0       # cena za 1 mil. znakov nad limit (USD, cca €)


def google_key():
    return (db.get_setting("google_tts_key", "") or "").strip()


def _month():
    return datetime.date.today().strftime("%Y-%m")


def google_usage():
    u = db.get_setting("google_tts_usage", {}) or {}
    used = u.get(_month(), 0)
    budget = float(db.get_setting("google_tts_budget", 0) or 0)  # koľko € mesačne smie minúť nad bezplatný limit
    limit = FREE_CHARS - 50000 + int(budget / PRICE_PER_M * 1_000_000)
    paid = max(0, used - FREE_CHARS) * PRICE_PER_M / 1_000_000
    return {"month": _month(), "used": used, "limit": limit, "left": max(0, limit - used), "free": FREE_CHARS,
            "budget": budget, "spent": round(paid, 2), "minutes": used // 900, "enabled": bool(google_key())}


def _google_add(n):
    with _lock:
        u = db.get_setting("google_tts_usage", {}) or {}
        u = {k: v for k, v in u.items() if k >= (datetime.date.today() - datetime.timedelta(days=100)).strftime("%Y-%m")}
        u[_month()] = u.get(_month(), 0) + n
        db.set_setting("google_tts_usage", u)


VOICE_VER = "z2"   # zmena spôsobu výroby hlasu = nové súbory (staré sa nepoužijú)
SR = 24000
PUNCT = ".!?…,;:"
ABBR = set("dr mr mrs ms nr no st ing mgr prof doc napr tzv resp tj cca str obr tel max min art fig vs sv ul bzw ca usw etc vgl inkl zzgl ggf evtl "
           "sog bsp jr sr mag dipl ev pol kpt např apod atd atď pozn odst nám př tj tzn mj np tzw itd itp ok godz zob wg m.in ex env av bd".split())


def spoken_form(text, lang):
    """Text tak, ako ho hlas povie: čísla slovom podľa gramatiky (verbal), potom názvy a skratky (pronounce).
    Vráti (text pre hlas, mapy späť na pôvodný zápis pre titulky)."""
    s1, sp1 = verbal.say_all(split_sentences(text), lang)
    s2, sp2 = pronounce.speak(s1, lang)
    return s2, (sp2, s1, sp1)


def unmap(words, spoken, maps, orig):
    """Časy slov z hlasu -> slová v pôvodnom zápise (titulky ukážu „2 kW“, hlas povie „dva kilowatty“)."""
    if not isinstance(maps, tuple):          # staré volanie len s úsekmi výslovnosti
        return punctuate(pronounce.remap(punctuate(words, spoken), spoken, maps), orig)
    sp2, s1, sp1 = maps
    w = pronounce.remap(punctuate(words, spoken), spoken, sp2)
    if sp1:
        w = pronounce.remap(punctuate(w, s1), s1, sp1)
    return punctuate(w, orig)


def split_sentences(text):
    """Rozdelí text na vety. Pri pochybnosti radšej nedelí (skratky „napr.“, „z. B.“, „Dr.“, „3. mája“)
    a kratučké vety spojí so susednou, aby zneli prirodzene."""
    raw = [x for x in re.split(r"(?<=[.!?…])\s+", re.sub(r"\s+", " ", text or "").strip()) if x]
    parts = []
    for x in raw:
        first = next((c for c in x if c.isalpha()), "")
        prev = parts[-1] if parts else ""
        last = re.sub(r"[^\w]", "", prev.split()[-1]) if prev.split() else ""
        abbr = prev.endswith(".") and not prev.endswith("..") and (
            (len(last) == 1 and last.isalpha()) or (last.isdigit() and len(last) <= 2 and len(prev) > 3) or last.lower() in ABBR)
        if parts and (first.islower() or abbr):
            parts[-1] += " " + x
        else:
            parts.append(x)
    out = []
    for x in parts:
        if out and len(out[-1]) < 12 and len(out[-1]) + len(x) < 320:
            out[-1] += " " + x
        else:
            out.append(x)
    if len(out) > 1 and len(out[-1]) < 12:
        tail = out.pop()
        out[-1] += " " + tail
    return out


def _pcm(wav):
    """WAV z Googlu -> vzorky (mono, 16 bit)."""
    try:
        with wave.open(io.BytesIO(wav)) as w:
            sr, ch, data = w.getframerate(), w.getnchannels(), w.readframes(w.getnframes())
    except Exception:
        sr, ch, data = SR, 1, wav[44:]
    a = array("h")
    a.frombytes(data[:len(data) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    if ch == 2:
        a = a[::2]
    return a, sr


def _levels(a, win):
    return [max(max(seg), -min(seg)) for seg in (a[i:i + win] for i in range(0, len(a), win)) if len(seg)]


def _fade(a, n):
    n = min(n, len(a) // 2)
    for i in range(n):
        k = i / n
        a[i] = int(a[i] * k)
        a[-1 - i] = int(a[-1 - i] * k)


def _tidy(a, sr):
    """Oreže ticho na začiatku a konci vety, dlhé pauzy vnútri skráti. Vráti (vzorky, pauzy vnútri [(od, do) v s])."""
    win = sr // 100
    lv = _levels(a, win)
    if not lv or max(lv) < 200:
        return array("h"), []
    thr = max(160, max(lv) * 0.02)
    loud = [i for i, v in enumerate(lv) if v > thr]
    i0, i1 = max(0, loud[0] - 2), min(len(lv), loud[-1] + 7)
    a, lv = a[i0 * win:i1 * win], lv[i0:i1]
    runs, start = [], None
    for i, v in enumerate(lv + [thr + 1]):
        if v <= thr and start is None:
            start = i
        elif v > thr and start is not None:
            if i - start >= 13 and start > 2:
                runs.append((start, i))
            start = None
    keep, out, gaps, pos = 30, array("h"), [], 0      # pauza vnútri vety najviac 0,3 s
    for s0, s1 in runs:
        out.extend(a[pos * win:s0 * win])
        n = min(s1 - s0, keep)
        g0 = len(out) / sr
        out.extend(array("h", bytes(2 * n * win)))
        gaps.append((g0, len(out) / sr))
        pos = s1
    out.extend(a[pos * win:])
    _fade(out, sr // 200)
    return out, gaps


def _spoken_weight(tok):
    core = tok.strip(PUNCT + "()\"'„“”«»")
    n = sum(4 if c.isdigit() else 1 for c in core)
    return max(1.0, n + 1.5)


def _times(tokens, dur, gaps):
    """Časy slov vo vete: rozdelí hovorený čas podľa dĺžky slov a pauzy (čiarky) priradí k interpunkcii."""
    if not tokens:
        return []
    voiced, last = [], 0.0
    for g0, g1 in gaps:
        voiced.append((last, g0))
        last = g1
    voiced.append((last, dur))
    cuts = [i for i, t in enumerate(tokens[:-1]) if t[-1:] in PUNCT or t in ("–", "—", "-")]
    if gaps and len(cuts) == len(gaps):
        groups, prev = [], 0
        for c in cuts:
            groups.append(tokens[prev:c + 1])
            prev = c + 1
        groups.append(tokens[prev:])
        out = []
        for grp, (v0, v1) in zip(groups, voiced):
            w = [_spoken_weight(t) for t in grp]
            unit, t = (v1 - v0) / sum(w), v0
            for tok, x in zip(grp, w):
                out.append((t, t + x * unit))
                t += x * unit
        return out
    # inak: plynule cez hovorený čas, pauzy sa preskočia
    w = [_spoken_weight(t) for t in tokens]
    total_v = sum(v1 - v0 for v0, v1 in voiced) or dur
    unit, acc, out = total_v / sum(w), 0.0, []

    def real(x):
        for v0, v1 in voiced:
            if x <= v1 - v0 + 1e-6:
                return v0 + x
            x -= v1 - v0
        return dur
    for x in w:
        out.append((real(acc), real(acc + x * unit)))
        acc += x * unit
    return out


def punctuate(words, text):
    """Doplní k slovám interpunkciu z textu (Microsoft hlas ju v časovaní nevracia) – titulky a strih podľa viet."""
    low, pos = (text or "").lower(), 0
    for w in words:
        x = (w.get("w") or "").strip()
        if not x or x[-1:] in PUNCT:
            continue
        i = low.find(x.lower(), pos)
        if i < 0 or i - pos > 60:
            continue
        pos = i + len(x)
        m = re.match(r"[^\s\w]*", low[pos:])
        tail = "".join(c for c in (m.group(0) if m else "") if c in PUNCT)
        if tail:
            w["w"] = x + tail[0]
    return words


def _google_call(body, key):
    last = ""
    for attempt in range(4):
        try:
            r = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", params={"key": key}, json=body, timeout=120)
        except httpx.HTTPError as e:
            last = str(e)[:200]
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code == 200:
            return base64.b64decode(r.json()["audioContent"])
        try:
            last = r.json()["error"]["message"]
        except Exception:
            last = r.text[:300]
        if r.status_code not in (429, 500, 502, 503, 504):
            break
        time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("Google hlas: " + last)


def _save_voice(pcm, sr, out_path):
    """Vyrovná hlasitosť a uloží (MP3 vo vysokej kvalite)."""
    import math
    lv = sorted(v for v in _levels(pcm, sr // 100) if v > 300)
    gain = max(-6.0, min(14.0, 20 * math.log10(18000 / max(lv[int(len(lv) * 0.9)], 1)))) if lv else 0.0
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        data = array("h", pcm)
        if sys.byteorder == "big":
            data.byteswap()
        w.writeframes(data.tobytes())
    from . import media
    ff = media.ffmpeg()
    if ff:
        r = subprocess.run([ff, "-y", "-f", "wav", "-i", "-", "-af", f"volume={gain:.2f}dB,alimiter=limit=0.9:level=false",
                            "-ar", str(sr), "-c:a", "libmp3lame", "-b:a", "128k", "-f", "mp3", str(out_path)],
                           input=buf.getvalue(), capture_output=True, start_new_session=True)
        if r.returncode == 0 and Path(out_path).stat().st_size > 1000:
            return
    Path(out_path).write_bytes(buf.getvalue())


def _google_tts(text, voice_name, out_path, rate=1.0, lang=""):
    """Google Chirp 3 HD po vetách, v plnej kvalite (bez stratovej kompresie od Googlu).
    Vďaka tomu poznáme presný čas každej vety -> titulky a obraz sedia s hlasom; pauzy medzi vetami sú krátke a rovnaké."""
    key = google_key()
    if not key:
        raise RuntimeError("Google hlas nemá zadaný kľúč (Nastavenia → Hlas)")
    parts = split_sentences(text)
    verbal.ensure([(lang, p) for p in parts])          # čísla podľa gramatiky jazyka (len vety s číslom, z pamäte zadarmo)
    spoken = []
    for p in parts:
        sp, maps = spoken_form(p, lang)
        if sp.strip():
            spoken.append((p, sp, maps))
    if not spoken:
        raise RuntimeError("Prázdny text pre hlas")
    if google_usage()["left"] < sum(len(sp) for _, sp, _ in spoken):
        raise RuntimeError("Google hlas: mesačný bezplatný limit je vyčerpaný, používam bezplatný Microsoft hlas")
    locale = "-".join(voice_name.split("-")[:2])

    def one(sp):
        body = {"input": {"text": sp}, "voice": {"languageCode": locale, "name": voice_name},
                "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SR}}
        if rate and abs(rate - 1.0) > 0.01:
            body["audioConfig"]["speakingRate"] = rate
        wav = _google_call(body, key)
        _google_add(len(sp))
        return _pcm(wav)

    with ThreadPoolExecutor(max_workers=4) as ex:
        clips = list(ex.map(one, [sp for _, sp, _ in spoken]))
    sr = clips[0][1]
    pause = 1 / max(0.8, rate or 1.0) ** 0.5
    pcm, words = array("h", bytes(2 * int(sr * 0.04))), []
    for (orig, sp, spans), (a, _) in zip(spoken, clips):
        a, gaps = _tidy(a, sr)
        if not len(a):
            continue
        t0, dur = len(pcm) / sr, len(a) / sr
        toks = sp.split()
        ws = [{"w": t, "s": round(t0 + s, 3), "e": round(t0 + e, 3)} for t, (s, e) in zip(toks, _times(toks, dur, gaps))]
        words += unmap(ws, sp, spans, orig)
        pcm.extend(a)
        end = sp.rstrip()[-1:]
        gap = (0.36 if end in "?!" else 0.42 if end == "…" else 0.30) * pause
        pcm.extend(array("h", bytes(2 * int(sr * gap))))
    if not words:
        raise RuntimeError("Google hlas nevrátil zvuk")
    _save_voice(pcm, sr, out_path)
    Path(str(out_path) + ".words.json").write_text(json.dumps(words, ensure_ascii=False))


# ---------- Lokálny hlas (Kokoro): beží na tomto počítači, zadarmo a bez limitu; kvalitný len v angličtine ----------
LOCAL_DIR = db.DATA_DIR / "kokoro"
LOCAL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
LOCAL_FILES = {"kokoro-v1.0.onnx": 300_000_000, "voices-v1.0.bin": 20_000_000}   # názov: najmenšia veľkosť hotového súboru
LOCAL_VOICES = [("af_heart", "F", "teplý, prirodzený", "en-us"), ("af_bella", "F", "živý, energický", "en-us"),
                ("am_michael", "M", "pokojný rozprávač", "en-us"), ("am_fenrir", "M", "hlbší, rázny", "en-us"),
                ("am_puck", "M", "mladší, svižný", "en-us"), ("bf_emma", "F", "britský, jemný", "en-gb"),
                ("bm_george", "M", "britský rozprávač", "en-gb")]
LOCAL = {"installing": False, "error": ""}
_local_lock = threading.Lock()


def _local_py():
    v = LOCAL_DIR / "venv"
    return v / "Scripts" / "python.exe" if sys.platform == "win32" else v / "bin" / "python"


def local_ready():
    return ((LOCAL_DIR / ".ok").exists() and _local_py().exists()
            and all((LOCAL_DIR / f).exists() and (LOCAL_DIR / f).stat().st_size >= n for f, n in LOCAL_FILES.items()))


def _sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", stdin=subprocess.DEVNULL, start_new_session=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "chyba").strip()[-300:])
    return r.stdout


def local_ensure(wait=False):
    """Raz na pozadí pripraví lokálny hlas: vlastný Python 3.12 (appka môže bežať na staršom), balík hlasu a model (asi 350 MB).
    Všetko zadarmo a bez klikania; chyba ostane v LOCAL["error"]."""
    if local_ready() or LOCAL["installing"]:
        return

    def go():
        LOCAL["installing"] = True
        step = "príprava"
        try:
            LOCAL_DIR.mkdir(parents=True, exist_ok=True)
            py = _local_py()
            if not (LOCAL_DIR / ".ok").exists() or not py.exists():
                step = "inštalácia uv"
                _sh([sys.executable, "-m", "pip", "install", "-q", "uv"])
                step = "Python 3.12 pre hlas"
                _sh([sys.executable, "-m", "uv", "venv", "--python", "3.12", "--clear", str(LOCAL_DIR / "venv")])
                step = "balík hlasu"
                _sh([sys.executable, "-m", "uv", "pip", "install", "--python", str(py), "kokoro-onnx>=0.4.9", "numpy"])
                step = "skúška balíka"
                _sh([str(py), "-c", "import kokoro_onnx, numpy"], 300)
                (LOCAL_DIR / ".ok").write_text("ok")
            for f, n in LOCAL_FILES.items():
                step = "sťahovanie modelu " + f
                dest = LOCAL_DIR / f
                if dest.exists() and dest.stat().st_size >= n:
                    continue
                part = dest.with_suffix(dest.suffix + ".part")
                with httpx.stream("GET", LOCAL_URL + f, follow_redirects=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(part, "wb") as out:
                        for chunk in r.iter_bytes(1 << 20):
                            out.write(chunk)
                if part.stat().st_size < n:
                    raise RuntimeError("model sa nestiahol celý")
                part.replace(dest)
            LOCAL["error"] = ""
        except Exception as e:
            LOCAL["error"] = f"{step}: {str(e)[-300:]}"
            print("lokálny hlas:", LOCAL["error"])
        finally:
            LOCAL["installing"] = False
    if wait:
        go()
    else:
        threading.Thread(target=go, daemon=True).start()


def local_status():
    return {"ready": local_ready(), "installing": LOCAL["installing"], "error": LOCAL["error"]}


def _local_tts(text, voice, out_path, rate=1.0, lang="en"):
    """Lokálny hlas po vetách (rovnako ako Google): poznáme čas každej vety, titulky a obraz sedia s hlasom."""
    if lang != "en":
        raise RuntimeError("Lokálny hlas vie dobre len po anglicky")
    if not local_ready():
        local_ensure()
        raise RuntimeError("Lokálny hlas sa ešte pripravuje (sťahuje sa raz, asi 350 MB)" + (": " + LOCAL["error"] if LOCAL["error"] else ""))
    loc = {v: l for v, _, _, l in LOCAL_VOICES}.get(voice)
    if not loc:
        raise RuntimeError("Neznámy lokálny hlas " + voice)
    parts = split_sentences(text)
    verbal.ensure([(lang, p) for p in parts])
    spoken = []
    for p in parts:
        sp, maps = spoken_form(p, lang)
        if sp.strip():
            spoken.append((p, sp, maps))
    if not spoken:
        raise RuntimeError("Prázdny text pre hlas")
    import tempfile
    with _local_lock, tempfile.TemporaryDirectory() as tmp:   # hovorí vždy len jedno video naraz (šetrí procesor pre skladanie obrazu)
        src = Path(tmp) / "vety.json"
        src.write_text(json.dumps([sp for _, sp, _ in spoken], ensure_ascii=False), encoding="utf-8")
        _sh([str(_local_py()), str(Path(__file__).with_name("tts_local.py")), str(LOCAL_DIR), voice, loc,
             f"{max(0.7, min(1.4, rate or 1.0)):.2f}", str(src), tmp], timeout=600 + 20 * len(spoken))
        clips = [_pcm((Path(tmp) / f"{i}.wav").read_bytes()) for i in range(len(spoken))]
    sr = clips[0][1]
    pause = 1 / max(0.8, rate or 1.0) ** 0.5
    pcm, words = array("h", bytes(2 * int(sr * 0.04))), []
    for (orig, sp, spans), (a, _) in zip(spoken, clips):
        a, gaps = _tidy(a, sr)
        if not len(a):
            continue
        t0, dur = len(pcm) / sr, len(a) / sr
        toks = sp.split()
        ws = [{"w": t, "s": round(t0 + s, 3), "e": round(t0 + e, 3)} for t, (s, e) in zip(toks, _times(toks, dur, gaps))]
        words += unmap(ws, sp, spans, orig)
        pcm.extend(a)
        end = sp.rstrip()[-1:]
        gap = (0.36 if end in "?!" else 0.42 if end == "…" else 0.30) * pause
        pcm.extend(array("h", bytes(2 * int(sr * gap))))
    if not words:
        raise RuntimeError("Lokálny hlas nevrátil zvuk")
    _save_voice(pcm, sr, out_path)
    Path(str(out_path) + ".words.json").write_text(json.dumps(words, ensure_ascii=False))


# ---------- Microsoft Edge ----------
def _run(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        if "event loop" not in str(e):
            raise
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _edge_tts(text, voice, out_path, rate=1.0, spans=None, orig=None):
    import edge_tts
    pct = f"{int(round((rate - 1) * 100)):+d}%"
    words = []

    async def go():
        com = edge_tts.Communicate(text, voice, rate=pct, boundary="WordBoundary")
        with open(out_path, "wb") as f:
            async for ch in com.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":  # časovanie slov pre titulky (zadarmo)
                    words.append({"w": ch["text"], "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
    try:
        _run(go())
    except TypeError:  # staršie edge-tts bez parametra boundary
        _run(edge_tts.Communicate(text, voice, rate=pct).save(str(out_path)))
    if not Path(out_path).exists() or Path(out_path).stat().st_size < 1000:
        raise RuntimeError("Microsoft hlas nevrátil zvuk")
    if words:
        words = unmap(words, text, spans, orig or text)   # titulky v pôvodnom zápise (PROLINE, nie „prolajn"; 2, nie „dve")
        Path(str(out_path) + ".words.json").write_text(json.dumps(words, ensure_ascii=False))


def edge_voices():
    """Zoznam všetkých Edge hlasov (raz stiahne a uloží)."""
    if EDGE_CACHE.exists():
        try:
            return json.loads(EDGE_CACHE.read_text())
        except Exception:
            pass
    try:
        import edge_tts
        v = _run(edge_tts.list_voices())
        v = [{"name": x["ShortName"], "locale": x["Locale"], "gender": "F" if x["Gender"] == "Female" else "M"} for x in v]
        EDGE_CACHE.write_text(json.dumps(v))
        return v
    except Exception:
        return []


def _pretty(voice_name):
    n = voice_name.split("-")[-1].replace("MultilingualNeural", "").replace("Neural", "")
    return n


# ---------- katalóg ----------
def catalog(lang):
    out = []
    loc = GOOGLE_LOCALES.get(lang)
    if loc:
        for n, g, desc in CHIRP:
            out.append({"id": f"google:{loc}-Chirp3-HD-{n}", "name": n, "gender": g, "engine": "google",
                        "label": f"{n} · {desc}" + (" · britský" if lang == "en" else ""), "best": True})
        for loc2, tag in GOOGLE_MORE.get(lang, []):
            for n, g, desc in CHIRP:
                out.append({"id": f"google:{loc2}-Chirp3-HD-{n}", "name": n, "gender": g, "engine": "google",
                            "label": f"{n} · {desc} · {tag}", "best": True})
    if lang == "en":
        for n, g, desc, loc2 in LOCAL_VOICES:
            out.append({"id": "local:" + n, "name": n, "gender": g, "engine": "local", "label": f"{n.split('_')[1].title()} · {desc}"})
    seen = set()
    f, m = languages.voice(lang, "F"), languages.voice(lang, "M")
    prefix = {"no": "nb-"}.get(lang, lang + "-")
    for v in [{"name": f, "gender": "F"}, {"name": m, "gender": "M"}] + [
            x for x in edge_voices() if x["locale"].lower().startswith(prefix.lower()) and "Multilingual" not in x["name"]]:
        if v["name"] in seen:
            continue
        seen.add(v["name"])
        out.append({"id": "edge:" + v["name"], "name": _pretty(v["name"]), "gender": v["gender"], "engine": "edge",
                    "label": f"{_pretty(v['name'])} · {v['name'].split('-')[1]}"})
    for n, g in EDGE_MULTI:
        out.append({"id": "edge:" + n, "name": _pretty(n), "gender": g, "engine": "edge",
                    "label": f"{_pretty(n)} · viacjazyčný (môže mať prízvuk)"})
    return out


def default_voice(lang, gender="F"):
    loc = GOOGLE_LOCALES.get(lang)
    if loc and google_key() and google_usage()["left"] > 2000:
        name = "Aoede" if gender.upper().startswith("F") else "Charon"
        return f"google:{loc}-Chirp3-HD-{name}"
    return "edge:" + languages.voice(lang, gender)


def _said(path, text):
    """Vedľa hlasu si zapíše, čo presne povedal (podľa toho sa pozná, že ho treba urobiť nanovo)."""
    try:
        Path(str(path) + ".say.txt").write_text(text, encoding="utf-8")
    except Exception:
        pass


def synth(text, lang, voice_id="auto", gender="F", rate=1.0, out_path=None, fresh=False):
    """Vytvorí hlas. Vráti (cesta, engine, poznámka). Keď vybraný hlas nejde, skúsi ďalší a povie to.
    Text sa pred hlasom upraví podľa výslovnosti (pronounce); titulky ostanú v pôvodnom zápise.
    Vedľa hlasu uloží časy slov (.words.json), podľa ktorých idú titulky a striedanie scén.
    fresh=True: hotový hlas z pamäte sa nepoužije, nahrá sa nanovo (Google hlas ho zakaždým povie trochu inak)."""
    orig = re.sub(r"\s+", " ", text or "").strip()
    if not orig:
        raise RuntimeError("Prázdny text pre hlas")
    text, spans = spoken_form(orig, lang)
    if not text:
        raise RuntimeError("Prázdny text pre hlas")
    if not voice_id or voice_id == "auto":
        voice_id = default_voice(lang, gender)
    chain = [voice_id]
    if not voice_id.startswith("local:"):   # lokálny hlas nemá náhradu: Oliver nechce videá s iným hlasom (radšej počkať)
        if not voice_id.startswith("edge:"):
            chain.append("edge:" + languages.voice(lang, gender))
        chain.append("gtts")
    errors = []
    for vid in chain:
        path = Path(out_path or VOICE_DIR / f"{lang}_{hashlib.md5((VOICE_VER + vid + str(rate) + text).encode()).hexdigest()[:12]}.mp3")
        if path.exists() and path.stat().st_size > 1000 and not out_path and not fresh:
            _said(path, text)
            return str(path), vid.split(":")[0], "; ".join(errors)
        try:
            Path(str(path) + ".words.json").unlink(missing_ok=True)
            if vid.startswith("google:"):
                _google_tts(orig, vid[7:], path, rate, lang)
            elif vid.startswith("local:"):
                _local_tts(orig, vid[6:], path, rate, lang)
            elif vid.startswith("edge:"):
                _edge_tts(text, vid[5:], path, rate, spans, orig)
            else:
                from gtts import gTTS
                gTTS(text, lang={"no": "no"}.get(lang, lang)).save(str(path))
            _said(path, text)
            return str(path), vid.split(":")[0], "; ".join(errors)
        except Exception as e:
            errors.append(str(e)[:200])
    raise RuntimeError("Hlas sa nepodarilo vytvoriť (skontroluj internet): " + " / ".join(errors))


def stale(voice_path, engine="", text=None, lang=None):
    """Hlas vyrobený starým spôsobom – pri ďalšom videu sa urobí nanovo:
    Google bez časov slov, alebo hlas, ktorý ešte čítal čísla po starom (bez gramatiky jazyka)."""
    if engine == "google" and not Path(str(voice_path) + ".words.json").exists():
        return True
    if text and lang and verbal.enabled():
        said = Path(str(voice_path) + ".say.txt")
        try:
            if said.exists():
                return said.read_text(encoding="utf-8") != spoken_form(re.sub(r"\s+", " ", text).strip(), lang)[0]
            return any(verbal.need(x) for x in split_sentences(text))
        except Exception:
            return False
    return False


def project_voice(project, lang):
    try:
        v = json.loads((project or {}).get("voices") or "{}")
    except Exception:
        v = {}
    return v.get(lang) or "auto"


def project_rate(project):
    try:
        return float((project or {}).get("voice_rate") or 1.0)
    except Exception:
        return 1.0
