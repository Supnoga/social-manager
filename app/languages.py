"""Európske jazyky + bezplatné hlasy (Microsoft Edge neural hlasy cez edge-tts)."""

# kód: (názov po slovensky, anglický názov pre AI, ženský hlas, mužský hlas)
LANGUAGES = {
    "sk": ("Slovenčina", "Slovak", "sk-SK-ViktoriaNeural", "sk-SK-LukasNeural"),
    "cs": ("Čeština", "Czech", "cs-CZ-VlastaNeural", "cs-CZ-AntoninNeural"),
    "en": ("Angličtina", "English", "en-GB-SoniaNeural", "en-GB-RyanNeural"),
    "de": ("Nemčina", "German", "de-DE-KatjaNeural", "de-DE-ConradNeural"),
    "fr": ("Francúzština", "French", "fr-FR-DeniseNeural", "fr-FR-HenriNeural"),
    "es": ("Španielčina", "Spanish", "es-ES-ElviraNeural", "es-ES-AlvaroNeural"),
    "it": ("Taliančina", "Italian", "it-IT-ElsaNeural", "it-IT-DiegoNeural"),
    "pl": ("Poľština", "Polish", "pl-PL-ZofiaNeural", "pl-PL-MarekNeural"),
    "pt": ("Portugalčina", "Portuguese (Portugal)", "pt-PT-RaquelNeural", "pt-PT-DuarteNeural"),
    "nl": ("Holandčina", "Dutch", "nl-NL-ColetteNeural", "nl-NL-MaartenNeural"),
    "hu": ("Maďarčina", "Hungarian", "hu-HU-NoemiNeural", "hu-HU-TamasNeural"),
    "ro": ("Rumunčina", "Romanian", "ro-RO-AlinaNeural", "ro-RO-EmilNeural"),
    "bg": ("Bulharčina", "Bulgarian", "bg-BG-KalinaNeural", "bg-BG-BorislavNeural"),
    "hr": ("Chorvátčina", "Croatian", "hr-HR-GabrijelaNeural", "hr-HR-SreckoNeural"),
    "sl": ("Slovinčina", "Slovenian", "sl-SI-PetraNeural", "sl-SI-RokNeural"),
    "sr": ("Srbčina", "Serbian", "sr-RS-SophieNeural", "sr-RS-NicholasNeural"),
    "bs": ("Bosniačtina", "Bosnian", "bs-BA-VesnaNeural", "bs-BA-GoranNeural"),
    "mk": ("Macedónčina", "Macedonian", "mk-MK-MarijaNeural", "mk-MK-AleksandarNeural"),
    "sq": ("Albánčina", "Albanian", "sq-AL-AnilaNeural", "sq-AL-IlirNeural"),
    "el": ("Gréčtina", "Greek", "el-GR-AthinaNeural", "el-GR-NestorasNeural"),
    "da": ("Dánčina", "Danish", "da-DK-ChristelNeural", "da-DK-JeppeNeural"),
    "sv": ("Švédčina", "Swedish", "sv-SE-SofieNeural", "sv-SE-MattiasNeural"),
    "no": ("Nórčina", "Norwegian (Bokmål)", "nb-NO-PernilleNeural", "nb-NO-FinnNeural"),
    "fi": ("Fínčina", "Finnish", "fi-FI-NooraNeural", "fi-FI-HarriNeural"),
    "is": ("Islandčina", "Icelandic", "is-IS-GudrunNeural", "is-IS-GunnarNeural"),
    "et": ("Estónčina", "Estonian", "et-EE-AnuNeural", "et-EE-KertNeural"),
    "lv": ("Lotyština", "Latvian", "lv-LV-EveritaNeural", "lv-LV-NilsNeural"),
    "lt": ("Litovčina", "Lithuanian", "lt-LT-OnaNeural", "lt-LT-LeonasNeural"),
    "uk": ("Ukrajinčina", "Ukrainian", "uk-UA-PolinaNeural", "uk-UA-OstapNeural"),
    "ga": ("Írčina", "Irish", "ga-IE-OrlaNeural", "ga-IE-ColmNeural"),
    "mt": ("Maltčina", "Maltese", "mt-MT-GraceNeural", "mt-MT-JosephNeural"),
    "ca": ("Katalánčina", "Catalan", "ca-ES-JoanaNeural", "ca-ES-EnricNeural"),
    "gl": ("Galícijčina", "Galician", "gl-ES-SabelaNeural", "gl-ES-RoiNeural"),
    "cy": ("Waleština", "Welsh", "cy-GB-NiaNeural", "cy-GB-AledNeural"),
    "ru": ("Ruština", "Russian", "ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"),
    "tr": ("Turečtina", "Turkish", "tr-TR-EmelNeural", "tr-TR-AhmetNeural"),
}


# Jazyky, ktoré appka ponúka (Oliverov zoznam 2026-11-10, slovenčina ako východisková) a krajiny, kde sa použijú
COUNTRIES = {
    "sk": ["SK"], "cs": ["CZ"], "de": ["DE", "AT", "CH", "LU"], "pl": ["PL"], "hu": ["HU"], "fr": ["FR", "BE", "CH", "LU"],
    "nl": ["NL", "BE"], "it": ["IT", "CH"], "es": ["ES"], "pt": ["PT"], "en": ["GB", "IE", "MT"], "da": ["DK"], "sv": ["SE"],
    "no": ["NO"], "fi": ["FI"], "is": ["IS"], "et": ["EE"], "lv": ["LV"], "lt": ["LT"], "el": ["GR", "CY"], "bg": ["BG"],
    "ro": ["RO"], "hr": ["HR"], "sl": ["SI"], "sr": ["RS", "ME"], "bs": ["BA"], "mk": ["MK"], "sq": ["AL", "XK"],
}
COUNTRY_NAMES = {
    "SK": "Slovensko", "CZ": "Česko", "DE": "Nemecko", "AT": "Rakúsko", "CH": "Švajčiarsko", "LU": "Luxembursko", "PL": "Poľsko",
    "HU": "Maďarsko", "FR": "Francúzsko", "BE": "Belgicko", "NL": "Holandsko", "IT": "Taliansko", "ES": "Španielsko",
    "PT": "Portugalsko", "GB": "Spojené kráľovstvo", "IE": "Írsko", "MT": "Malta", "DK": "Dánsko", "SE": "Švédsko", "NO": "Nórsko",
    "FI": "Fínsko", "IS": "Island", "EE": "Estónsko", "LV": "Lotyšsko", "LT": "Litva", "GR": "Grécko", "CY": "Cyprus",
    "BG": "Bulharsko", "RO": "Rumunsko", "HR": "Chorvátsko", "SI": "Slovinsko", "RS": "Srbsko", "ME": "Čierna Hora",
    "BA": "Bosna a Hercegovina", "MK": "Severné Macedónsko", "AL": "Albánsko", "XK": "Kosovo",
}
EXTRA = {"en": "medzinárodná verzia"}


def name(code):
    return LANGUAGES.get(code, (code,))[0]


def english(code):
    return LANGUAGES.get(code, (code, code))[1]


def voice(code, gender="F"):
    v = LANGUAGES.get(code)
    if not v:
        return "en-GB-SoniaNeural"
    return v[2] if gender.upper().startswith("F") else v[3]


def countries_text(code):
    t = ", ".join(COUNTRY_NAMES.get(c, c) for c in COUNTRIES.get(code, []))
    return t + (" a " + EXTRA[code] if code in EXTRA else "")


def as_list():
    return [{"code": k, "name": LANGUAGES[k][0], "female": LANGUAGES[k][2], "male": LANGUAGES[k][3],
             "countries": countries_text(k)} for k in COUNTRIES]
