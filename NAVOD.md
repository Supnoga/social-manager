# Social Manager – návod

Appka beží na tvojom počítači, je zadarmo a dáta ostávajú u teba (priečinok `data`).

## 1. Inštalácia na Mac (iba raz)

1. **Python** – ak ho ešte nemáš: https://www.python.org/downloads/ → stiahni a nainštaluj.
2. **Claude Code** (AI ide z tvojho Max plánu) – ak ho ešte nemáš: v Termináli `curl -fsSL https://claude.ai/install.sh | bash`, potom `claude` a prihlás sa.
3. Rozbaľ **Social-Manager-Mac.zip** a ikonku **Social Manager** presuň na **Plochu** (alebo do Aplikácií).
4. Prvé otvorenie: dvojklik → Mac povie, že appku nevie overiť → **Systémové nastavenia → Súkromie a bezpečnosť** → dole **„Aj tak otvoriť“** → heslo. Toto je len raz.
5. Prvé spustenie trvá 1–2 minúty (pripravuje sa). Potom sa otvorí prehliadač.

Odvtedy stačí **dvojklik na ikonku**. Appka beží na pozadí bez čierneho okna, vypneš ju vľavo dole „Vypnúť appku“.
**Aktualizácie prichádzajú samé** (pri zapnutí a každé 4 hodiny). Projekty a nastavenia zo starej verzie appka prenesie sama.

> Appka publikuje len keď beží. Počítač teda musí byť zapnutý v čase, keď sú videá naplánované.

## 2. Ako sa s ňou pracuje

1. **Nový projekt** (vľavo „+“). Popíš o čom je, pre koho, vyber jazyky a siete.
   V záložke **Popis a dizajn** môžeš vložiť **MD dizajn** (napr. z Claude Design) – farby a štýl sa potom použijú vo videách aj v textoch.
2. V projekte, záložka **Videá**, je tabuľa s 5 krokmi:
   1. **Nápad** – „Vymyslieť nápady“ (AI), „Vlastný nápad“ alebo **Autopilot** (všetko naraz).
   2. **Prototyp** – scenár + náhľad videa v telefóne (scény, texty na obrazovke, hlas). Uprav a schváľ.
   3. **Text a hlas** – preklad do všetkých jazykov projektu a hlasy jedným klikom.
   4. **Video** – appka urobí videá s textami a hlasom (aj cez tvoje podkladové zábery), alebo nahráš vlastné video ku každému jazyku.
   5. **Siete** – tabuľka jazyky × siete, naplánuješ alebo zverejníš hneď.
3. **Knižnica** – hromadné videá: pretiahni ich alebo pridaj celý priečinok (jazyk sa spozná z názvu `recept_de.mp4` alebo z priečinka `/de/`).
4. **Účty a siete** – pripoj kanály a pri každom nastav **projekt a jazyk**.
5. **Publikovanie** – kalendár po dňoch, chyby sa dajú zopakovať jedným klikom.

## 3. Pripojenie platforiem

Podrobný návod na registrácie je v samostatnom návode „Registrácie na platformy". Do appky potom vložíš:

| Platforma | Čo vložíš v časti Účty |
|---|---|
| YouTube | JSON súbor OAuth klienta (typ *Desktop app*) → Pripojiť kanál (pre každý kanál zvlášť) |
| Facebook + Instagram | System User token → appka sama nájde všetky stránky aj IG účty |
| TikTok (veľa účtov, verejne) | App ID + Secret z business-api.tiktok.com → Pripojiť každý účet. Potrebuje verejnú adresu (nižšie) |
| TikTok (záloha) | Client key + Secret → videá prídu ako koncept do TikTok appky |
| LinkedIn | 2 appky: profil (Client ID + Secret, funguje hneď) a firemné stránky (druhé Client ID + Secret, po schválení LinkedInom) |

### Verejná adresa (len pre TikTok Business)
TikTok Business si videá **sťahuje z internetu**, nevie ich prijať priamo. Riešenie:
1. Vyber si jednu zo svojich domén (takú, na ktorej nemáš dôležitý e-mail ani web) a pridaj ju do Cloudflare (bezplatný plán).
2. Cloudflare → Zero Trust → Networks → Tunnels → vytvor tunel (Cloudflared). Public hostname napr. `videa.tvojadomena.sk` → service `http://localhost:8765`.
3. Skopíruj token tunela a vlož ho v appke: **Nastavenia → Verejná adresa** spolu s adresou `https://videa.tvojadomena.sk`.
4. Overovací súbor z TikTok portálu (napr. `tiktokXXXX.txt`) vlož tam isto – appka ho sprístupní.

Zvonka je viditeľné **len** video pod tajným odkazom a overovací súbor, nič iné z appky.

## 3b. Preklady zadarmo (bez tokenov)
V **Nastavenia → Preklady zadarmo** vlož kľúč Microsoft Translator (Free F0, 2 mil. znakov mesačne) – návod je priamo tam. Voliteľne DeepL Free (500 tis.) a Google (500 tis.). Potom preklady nestoja žiadne Claude tokeny; Claude len opraví sporné kúsky. V projekte vyplň **Neprekladať** (názov značky, produktov). V kroku **Text a hlas** tlačidlo **Vyrobiť všetky jazyky** spraví preklad, hlasy aj videá naraz.

## 4. AI a spotreba

- AI ide cez **Claude Code s tvojím Max plánom** – nič sa neplatí navyše. Ak Claude Code nie je, appka ponúkne **ručný režim** (skopíruješ text do claude.ai a odpoveď vložíš späť).
- Šetrenie je zabudované: krátke zadania, viac vecí v jednom volaní, lacnejší model (haiku) na preklady, a čo už raz bolo vypočítané, sa neopakuje.
- Orientačne: 1 nápad so scenárom v 9 jazykoch ≈ 40–50 tisíc tokenov. Prehľad spotreby je v **Nastaveniach**.
- **Háčik:** spotreba ide z rovnakého limitu ako tvoj bežný chat s Claudom. Keď limit dôjde, appka povie a treba pár hodín počkať. Max plán je osobný, appku používaj pre seba (nie ako službu pre iných).

## 5. Limity platforiem (na rovinu)

- **YouTube:** denný limit nahrávania na jeden Google Cloud projekt (podľa aktuálnych pravidiel cca 100 videí/deň). Consent screen prepni na „In production", inak prihlásenie vyprší po 7 dňoch.
- **Instagram:** max 100 príspevkov za 24 h na účet. **Facebook Reels:** 30 za 24 h na stránku, 3–90 s.
- **TikTok Business:** potrebuje schválenie appky TikTokom (pár dní). Pri veľmi podobných videách hlási „spam" – appka preto náhodne posúva čas publikovania; dávaj videám rôzne texty.
- **LinkedIn:** prihlásenie platí 60 dní, potom ho v Účtoch obnovíš jedným klikom. Firemné stránky až po schválení „Community Management API".
- **TikTok záloha (koncepty):** bez schválenia ide len koncept do appky alebo súkromné video.

## 6. Hlas

- **Google hlasy (Chirp 3 HD)** – najprirodzenejšie, majú slovenčinu, češtinu, maďarčinu, poľštinu a väčšinu európskych jazykov. **1 milión znakov mesačne zadarmo** (cca 1 000 minút). Kľúč vložíš v **Nastavenia → Hlas** (návod je tam). Google chce v projekte kartu; appka počíta znaky a pri 0 € navyše sa pred limitom sama prepne na bezplatný hlas. Ak chceš, nastavíš strop v € (napr. 5 € ≈ ďalších 180 minút).
- **Microsoft hlasy** – zadarmo bez registrácie, použijú sa, keď Google kľúč nie je alebo je limit minutý. Pre portugalčinu, bosniačtinu, macedónčinu, albánčinu, islandčinu, írčinu, maltčinu, katalánčinu, galícijčinu a waleštinu Google HD hlas nemá, tam ide vždy Microsoft.
- **Výber hlasu:** v projekte → Popis a dizajn → **Hlasy pre jazyky**: pri každom jazyku vyberieš hlas, tlačidlom ▶ si vypočuješ ukážku, nastavíš rýchlosť reči.
- Ak vybraný hlas nejde, appka použije náhradný a **povie ti to**.

## 6b. Zdroje projektu
V projekte → Popis a dizajn → **Zdroje**: vlož odkazy na svoj web, text alebo súbory (PDF, TXT, MD). AI si z nich raz urobí výťah faktov a stratégia, nápady aj scenáre z nich vychádzajú.

## 7. Aktualizácie
Prichádzajú samé, nič nerobíš. Dáta ostávajú v priečinku *Knižnica → Application Support → SocialManager → data*.

## 8. Keď niečo nejde

- *Claude: ručný režim* → v Termináli/PowerShell spusti `claude` a prihlás sa. Prípadne v Nastaveniach vlož cestu ku Claude Code.
- *„prihlásenie vypršalo"* → v Účtoch účet pripoj znova.
- Záloha dát = skopíruj priečinok `data` (v Application Support/SocialManager).
- Keď appka spadne, sama sa znova zapne. Ak nie, pošli Claudovi súbor `data/chyby.log`.
