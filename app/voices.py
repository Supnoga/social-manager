"""Hlasy: Google Chirp 3 HD (najprirodzenejšie, 1 mil. znakov/mesiac zadarmo s poistkou limitu),
Microsoft Edge neural (zadarmo bez registrácie) a Google gTTS ako posledná záloha.

ID hlasu: "google:sk-SK-Chirp3-HD-Aoede", "edge:sk-SK-ViktoriaNeural", "auto" (najlepší dostupný)."""
import asyncio
import base64
import datetime
import hashlib
import json
import re
import threading
from pathlib import Path

import httpx

from . import db, languages, pronounce

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


def _google_tts(text, voice_name, out_path, rate=1.0):
    key = google_key()
    if not key:
        raise RuntimeError("Google hlas nemá zadaný kľúč (Nastavenia → Hlas)")
    if google_usage()["left"] < len(text):
        raise RuntimeError("Google hlas: mesačný bezplatný limit je vyčerpaný, používam bezplatný Microsoft hlas")
    locale = "-".join(voice_name.split("-")[:2])
    chunks, cur = [], ""
    for sent in re.split(r"(?<=[.!?…])\s+", text):  # Google berie max ~5000 bajtov naraz
        if len((cur + " " + sent).encode()) > 4000 and cur:
            chunks.append(cur)
            cur = sent
        else:
            cur = (cur + " " + sent).strip()
    if cur:
        chunks.append(cur)
    audio = b""
    for ch in chunks:
        body = {"input": {"text": ch}, "voice": {"languageCode": locale, "name": voice_name},
                "audioConfig": {"audioEncoding": "MP3"}}
        if rate and abs(rate - 1.0) > 0.01:
            body["audioConfig"]["speakingRate"] = rate
        r = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", params={"key": key}, json=body, timeout=120)
        if r.status_code != 200:
            try:
                msg = r.json()["error"]["message"]
            except Exception:
                msg = r.text[:300]
            raise RuntimeError("Google hlas: " + msg)
        audio += base64.b64decode(r.json()["audioContent"])
        _google_add(len(ch))
    Path(out_path).write_bytes(audio)


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


def _edge_tts(text, voice, out_path, rate=1.0, spans=None):
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
        words = pronounce.remap(words, text, spans)   # titulky v pôvodnom zápise (PROLINE, nie „prolajn")
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
                        "label": f"{n} · {desc}", "best": True})
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


def synth(text, lang, voice_id="auto", gender="F", rate=1.0, out_path=None):
    """Vytvorí hlas. Vráti (cesta, engine, poznámka). Keď vybraný hlas nejde, skúsi ďalší a povie to.
    Text sa pred hlasom upraví podľa výslovnosti (pronounce); titulky ostanú v pôvodnom zápise."""
    if not re.sub(r"\s+", " ", text or "").strip():
        raise RuntimeError("Prázdny text pre hlas")
    text, spans = pronounce.speak(text, lang)
    if not text:
        raise RuntimeError("Prázdny text pre hlas")
    if not voice_id or voice_id == "auto":
        voice_id = default_voice(lang, gender)
    chain = [voice_id]
    if not voice_id.startswith("edge:"):
        chain.append("edge:" + languages.voice(lang, gender))
    chain.append("gtts")
    errors = []
    for vid in chain:
        path = Path(out_path or VOICE_DIR / f"{lang}_{hashlib.md5((vid + str(rate) + text).encode()).hexdigest()[:12]}.mp3")
        if path.exists() and path.stat().st_size > 1000 and not out_path:
            return str(path), vid.split(":")[0], "; ".join(errors)
        try:
            Path(str(path) + ".words.json").unlink(missing_ok=True)
            if vid.startswith("google:"):
                _google_tts(text, vid[7:], path, rate)
            elif vid.startswith("edge:"):
                _edge_tts(text, vid[5:], path, rate, spans)
            else:
                from gtts import gTTS
                gTTS(text, lang={"no": "no"}.get(lang, lang)).save(str(path))
            return str(path), vid.split(":")[0], "; ".join(errors)
        except Exception as e:
            errors.append(str(e)[:200])
    raise RuntimeError("Hlas sa nepodarilo vytvoriť (skontroluj internet): " + " / ".join(errors))


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
