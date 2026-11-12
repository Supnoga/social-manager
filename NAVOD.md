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
   3. **Text a hlas** – hlas pre prvú verziu v jednom jazyku (predvolene jazyk scenára, dá sa zmeniť).
   4. **Video** – najprv sa urobí video len v tomto jednom jazyku. Pozrieš si ho, a keď je dobré, tlačidlo **Rozšíriť do všetkých jazykov** ho preloží do ostatných jazykov s tým istým obrazom (mení sa len text, titulky a hlas). Môžeš aj nahrať vlastné video.
   5. **Siete** – tabuľka jazyky × siete, naplánuješ alebo zverejníš hneď.
3. **Knižnica** – hromadné videá: pretiahni ich alebo pridaj celý priečinok (jazyk sa spozná z názvu `recept_de.mp4` alebo z priečinka `/de/`).
4. **Účty a siete** (v menu pod projektom) – pripoj kanály, pridajú sa do tohto projektu; pri každom nastav **krajinu**.
5. **Kontrola** – všetko naplánované najprv čaká tu. Pozrieš video (prepínaš jazyky), a **Schváliť a pustiť** ho pošle vo všetkých jazykoch na všetky účty naraz. **Vrátiť na úpravu** zruší naplánovanie. Vypnúť sa dá v Nastaveniach → Ostatné.
6. **Publikovanie** – kalendár po dňoch, chyby sa dajú zopakovať jedným klikom.

## 3. Pripojenie platforiem

Podrobný návod na registrácie je v samostatnom návode „Registrácie na platformy". Do appky potom vložíš:

| Platforma | Čo vložíš v časti Účty |
|---|---|
| YouTube | JSON súbor OAuth klienta (typ *Desktop app*) → Pripojiť kanál (pre každý kanál zvlášť) |
| Facebook + Instagram | System User token → appka sama nájde všetky stránky aj IG účty |
| TikTok (veľa účtov, verejne) | App ID + Secret z business-api.tiktok.com → Pripojiť každý účet. Potrebuje verejnú adresu (nižšie) |
| TikTok (záloha) | Client key + Secret → videá prídu ako koncept do TikTok appky |
| LinkedIn | 2 appky: profil (Client ID + Secret, funguje hneď) a firemné stránky (druhé Client ID + Secret, po schválení LinkedInom) |

### Veľa kanálov a účtov (napr. 40 YouTube kanálov v jednom projekte)

- **Viac YouTube kanálov pod jedným Google účtom**: klikni *Pripojiť kanál*, v okne Google vyber kanál. Pre ďalší kanál klikni znova a vyber ďalší. Každý kanál je v appke samostatný účet.
- **Projekt a jazyk**: v zozname účtov zaškrtni viac účtov naraz a hore nastav projekt alebo jazyk jedným klikom. Zoznam sa dá filtrovať podľa siete, projektu a mena.
- **Limit YouTube**: jeden Google projekt zvládne cca 100 nahratí denne (všetky kanály spolu). Pri 40 kanáloch × 1–2 videá denne to stačí. Pri viac vytvor v Google Cloud ďalší projekt (rovnaký postup) a nahraj jeho JSON tlačidlom *Pridať ďalší Google projekt* – nové kanály sa rozložia samé. Keď sa denný limit minie, video nezlyhá, len počká do rána.

### Verejná adresa (len pre TikTok Business)
TikTok Business si videá **sťahuje z internetu**, nevie ich prijať priamo. Riešenie:
1. Vyber si jednu zo svojich domén (takú, na ktorej nemáš dôležitý e-mail ani web) a pridaj ju do Cloudflare (bezplatný plán).
2. Cloudflare → Zero Trust → Networks → Tunnels → vytvor tunel (Cloudflared). Public hostname napr. `videa.tvojadomena.sk` → service `http://localhost:8765`.
3. Skopíruj token tunela a vlož ho v appke: **Nastavenia → Verejná adresa** spolu s adresou `https://videa.tvojadomena.sk`.
4. Overovací súbor z TikTok portálu (napr. `tiktokXXXX.txt`) vlož tam isto – appka ho sprístupní.

Zvonka je viditeľné **len** video pod tajným odkazom a overovací súbor, nič iné z appky.

## 3b. Preklady zadarmo (bez tokenov)
V **Nastavenia → Preklady zadarmo** vlož kľúč Microsoft Translator (Free F0, 2 mil. znakov mesačne) – návod je priamo tam. Voliteľne DeepL Free (500 tis.) a Google (500 tis.). Potom preklady nestoja žiadne Claude tokeny; Claude len opraví sporné kúsky. V projekte vyplň **Neprekladať** (názov značky, produktov). Keď je prvá verzia videa dobrá, v kroku **Video** tlačidlo **Rozšíriť do všetkých jazykov** spraví preklad, hlasy aj videá naraz.

## 3c. Obraz videí: animované schémy ako N2N Akadémia (predvolené)
Videá sa robia ako vysvetľujúce animácie v štýle videí N2N Akadémie: čierne pozadie, veľký nadpis scény, tenké schémy, ktoré sa postupne kreslia (tok energie cez tepelné čerpadlo, ako funguje cyklus čerpadla, stĺpce, výpočty, správne/nesprávne, ikony, teplomery, tepelné straty domu, počítadlá), titulky so zvýrazneným slovom a lišta priebehu dole. Farba je farba projektu, písmo je písmo značky.
Claude navrhne schému ku každej scéne rovno pri písaní scenára (staršie scenáre dostanú schémy samé pri ďalšom „Vytvoriť znova“, jedno malé lacné volanie). Pri rozšírení do ďalších jazykov sa obraz nemení, preložia sa len texty v schémach. Všetko zadarmo, renderuje sa u teba na Macu.
Ak chceš radšej zábery z internetu, v kroku **Video** vyber štýl *Zábery z internetu + titulky*.

### Zábery z internetu (voliteľné)
V **Nastavenia → Zábery a hudba** vlož bezplatný kľúč **Pexels** (a voliteľne Pixabay). Svoje vlastné zábery daj do priečinka **Moje zábery** (tlačidlo ho otvorí) a pomenuj ich podľa obsahu, napr. `varenie-cestoviny.mp4` – appka ich uprednostní. Hudbu (mp3) daj do priečinka **Hudba**.
Video potom vyzerá takto: nový záber každé 2–3 s, fotky sa pohybujú, titulky slovo po slove (aktuálne slovo vo farbe projektu), text scény hore. Zábery sa vyberú raz a platia pre všetky jazyky; v kroku **Video** ich vidíš po scénach a môžeš ich vymeniť.

## 3c2. Vzhľad účtov (profilovka, pozadie, popis)

V menu *Vzhľad účtov*: nahraj raz profilovú fotku, pozadie a napíš popis. Appka obrázky oreže pre každú sieť a popis preloží do jazyka každého účtu (bezplatný prekladač). Tlačidlo *Nastaviť označeným* zmení samo YouTube (popis, pozadie) a Facebook (popis, pozadie, profilovka). Instagram, TikTok a LinkedIn zmenu zvonka nedovolia: pri nich je tlačidlo na skopírovanie popisu, odkaz rovno na úpravu profilu a obrázky v priečinku. Po vložení klikni *Hotovo*. YouTube profilovku tiež treba nahrať ručne (Google to nedovolí).

## 3d. Radar, výsledky a plánovanie na týždeň

- **Radar** (v menu): appka sama sleduje trendy (Google Trendy, Google Správy, Wikipédia, YouTube), videá konkurencie (YouTube kanály, ktoré pridáš v karte Konkurencia) a čísla tvojich videí. Všetko zadarmo a bez AI.
- **Nápady**: každý pondelok Claude z krátkeho výťahu navrhne 5 nápadov na projekt (1 volanie). Klikneš *Beriem*, *Neskôr* alebo *Nie*. Pri trende alebo videe konkurencie je aj tlačidlo *Nápad z tohto*.
- **YouTube kľúč** na sledovanie konkurencie: Nastavenia → Radar a plánovanie (návod je tam, 3 minúty, zadarmo).
- **Udalosti** (Radar → Udalosti): štátne sviatky krajín tvojich jazykov, bežné dni (Vianoce, Nový rok, Halloween, Valentín…) a tematické dni projektu (napr. Deň Zeme). Pri každej je tlačidlo *Video* a *Prianie*. Nápady k udalostiam o 1–3 týždne pribudnú v pondelok samé. Video k udalosti sa naplánuje presne na jej deň a len na účty krajín, kde sa oslavuje.
- **Výsledky**: čísla zo sietí sa sťahujú každých 6 hodín. Appka vie, ktoré videá sa darili, a posiela to Claudovi pri vymýšľaní, aby staval na tom, čo funguje.
- **Naplánovať týždeň** (Publikovanie): jedným klikom rozdelí hotové videá na všetky účty na 7 dní, v najlepšie časy pre každý účet. Kým nie sú vlastné čísla, používa štandardné časy podľa siete a krajiny. Dá sa zapnúť, aby to robila sama každú nedeľu večer. Projekt môže mať vlastný rytmus (od 1.27): napríklad Energy Xplained vydáva 5 Shorts týždenne, pondelok až piatok o 18:00; okno plánovania to ukáže. Od 1.28 vie appka aj **dlhé videá na šírku** (pri nápade zvoľ formát „Dlhé YouTube video“): scenár má 6 až 8 minút, video sa vyrobí v rozmere 1920×1080 s náhľadovým obrázkom a v pláne projektu môže mať vlastnú hodinu (napr. každý deň o 15:00). V jeden deň appka nedá dve videá z tej istej série. **Denná výroba (od 1.29):** projekt môže mať zapnuté, že si appka sama drží zásobu hotových videí na 2 dni dopredu (napr. 3 krátke a 1 dlhé denne): vyberie najlepšie schválené nápady, napíše scenáre, vyrobí videá a naplánuje ich. Ty ich len schváliš v Kontrole. Keď dochádzajú nápady, doplní ich. **Od 1.30:** videá držia odstup od krajov a na Shorts nechávajú voľné miesto tam, kde siete zobrazujú tlačidlá, popis a názov kanála (platí pre všetky projekty). Scenáre rozprávajú jednoducho a pútavo ako príbeh, bez technického žargónu. Animácie majú pozadie v pohybe, jemné približovanie, nové obrázky (solárny panel, veterná turbína, batéria, auto, stožiar, žiarovka a ďalšie) a veľké animované obrázky pri rozprávaní. **Od 1.31:** celé video je jedna veľká kresliaca plocha: scény ležia vedľa seba, kamera sa medzi nimi plynule presúva a na konci sa oddiali, aby ukázala všetko naraz. **Od 1.32:** **Shorts z dlhého videa**: pri dlhom videu je tlačidlo „Urobiť z neho 3 Shorts“. Každý Short vysvetlí jeden kúsok a otvoreným koncom pozve na celé video. Pri dennej výrobe to appka robí sama, Shorts idú von až po dlhom videu a v popise majú odkaz naň. Appka vie aj **vlastné kresby**: keď treba vec ukázať (napríklad turbínu s 2, 3 a 4 lopatkami vedľa seba), nakreslí ju a rozhýbe. Na konci videa rohové logo zmizne, aby sa neprekrývalo s prehľadom.
- **Zopakovať úspešné** (Radar → Výsledky): úspešné videá idú pri plánovaní prvé na účty, kde ešte neboli, a Claude k nim navrhne nové variácie. Rovnaké video na ten istý účet znova nedávame, siete to trestajú.

## 3c1. Logo, fotky a súbory značky
V projekte → Popis a dizajn → **Obrázky, logá a súbory značky**: pretiahni sem logo, fotky produktov, videá, fonty alebo PDF brand manuál (PNG, JPG, SVG, WebP, HEIC z iPhonu, GIF, MP4, MOV, TTF, OTF, WOFF, PDF, MD). Bez AI, zadarmo.
- **Logo** sa samo dá do rohu každého nového videa a na záverečnú kartu po dohovorení hlasu. Keď nahráš viac súborov, appka sama spozná skutočné logo (podľa názvu, napr. `logo-...`), nie ikonu, a na čierne video vyberie svetlý variant. Tmavé logo dostane bielu podložku. Z loga sa urobí aj profilovka účtov (ak nenahráš inú).
- **Fotky a videá** sa použijú ako zábery vo videách tohto projektu (pred zábermi z internetu). Ku každej napíš, čo je na nej, appka ju dá k scéne, ktorá o tom hovorí. Navyše sa jedna dostane do každého videa.
- **Fonty**: nadpisový font (napr. Display, Bold) ide na nadpisy a čísla, textový (Text, Light) na titulky. Font bez diakritiky sa vynechá. Pri jazykoch, pre ktoré font nemá písmená (napr. azbuka), ostane bežný font.
- **PDF / MD** sa pridá k dizajnu značky.
- **Farby z manuálu**: zvýrazňovacia farba videí je prvá sýta farba z dizajnu (pri N2N červená). Čierna, biela a sivé sa za ňu nikdy neberú. Iné farby sa vo videách nepoužívajú.
- **Produkty**: obrázok produktu s priehľadným pozadím pomenovaný podľa produktu (napr. `hydrobox.png`) sa ukáže v scéne, ktorá produkt spomína, so svetlom vo farbe značky.
- Všetko sa dá vypnúť zaškrtávačmi nad súbormi. Hviezdička = hlavné logo alebo font.

## 3d1. Inšpirácia a kvalita obsahu
- **Radar → Inšpirácia → Čo ľudia hľadajú a pýtajú sa:** čo ľudia píšu do Googlu v každej krajine (napr. „koľko stojí tepelné čerpadlo“) a otázky z komentárov pod tvojimi videami. Zbiera sa samé raz týždenne, zadarmo, bez AI. Tlačidlo „Nápad“ z otázky urobí video.
- **Zásobník inšpirácie:** vlož odkaz na video, ktoré sa ti páči (TikTok, Reels, YouTube…), prípadne poznámku. Claude z neho vezme formát (nie obsah) a v pondelok ho použije prednostne.
- **Overené formáty:** 18 osvedčených typov videí (3 chyby, Mýtus vs. fakt, Koľko to stojí…). Claude ku každému nápadu jeden vyberie, appka si pamätá, ktoré ti fungujú, a tie ponúka častejšie.
- **Kvalita scenára:** pri prototype vidíš skóre 0–100 a konkrétne rady (krátky začiatok, číslo, výzva na konci, text na obrazovke…). Bez AI. „Silnejší začiatok“ navrhne 5 lepších prvých viet (1 malé lacné volanie).
- **Opraviť jedným klikom:** pri kvalite scenára; Claude opraví presne to, čo kontrola našla (1 volanie). Dá sa vrátiť späť.
- **Séria:** pri nápade tlačidlo „Urobiť z toho sériu“ pridá 4 pokračovania (časť 2 až 5) do schránky nápadov.
- **Počasie ako spúšťač:** appka denne sleduje predpoveď v krajinách projektu. Keď ide mráz, prudké ochladenie alebo horúčava, navrhne video pre tie krajiny na správny deň. Zadarmo, bez AI.
- **Vyvážený obsah:** appka stráži pomer rád, dôkazov a aktuálnych tém (cieľ 50/30/20) a chýbajúci typ ponúka prednostne.
- **Nikdy netvrdiť:** v nastavení projektu zapíš zakázané tvrdenia (pri N2N je prednastavené „made in Slovakia“ a podobné). Claude ich nepoužije a kontrola kvality ich odhalí.

## 3d2. Dashboard (výsledky v grafoch)

- **Dashboard** (v menu pod projektom): iba skutočné zobrazenia, reakcie a zapojenie zo sietí, kým nie sú, ukáže „Zatiaľ žiadne dáta“. Filtre: obdobie, sieť, krajina, jazyk. Klik na riadok v grafe (napr. krajinu) ju vyfiltruje, druhý klik filter zruší.
- Grafy: vývoj v čase (oproti predchádzajúcemu obdobiu), podľa siete, krajiny, jazyka a projektu, kedy to funguje najlepšie (deň a hodina), z čoho sú reakcie, najlepšie príspevky a účty.
- Nemíňa žiadne AI. Kým nie sú skutočné čísla, ukazuje ukážkové (je to pri nich napísané).

## 3e. Súkromné správy (Facebook a Instagram)
V menu **Správy** (pod každým projektom aj pre všetky projekty naraz) sú súkromné správy zo všetkých Facebook stránok a Instagram účtov. Appka ich načíta sama každú hodinu (zadarmo, bez AI). Klikni **Navrhnúť odpovede**, AI napíše odpoveď v jazyku zákazníka, pod ňou vidíš preklad do slovenčiny. Nič sa neodošle bez tvojho kliknutia.

Čo treba nastaviť raz:
- Meta token s právami pages_messaging, pages_manage_metadata a instagram_manage_messages (vlož ho znova v Účtoch).
- V appke Instagram: Nastavenia → Správy → Pripojené nástroje → Povoliť prístup k správam (na každom účte).
- Správy od bežných ľudí Meta pustí až po jednorazovom schválení appky (App Review) a overení firmy. Je to zadarmo. Dovtedy vidíš len správy od ľudí, ktorí spravujú stránku.

Pravidlá sietí: odpísať sa dá do 24 hodín od poslednej správy človeka (karta ukazuje, koľko času ostáva). Keď Meta schváli povolenie „Human Agent“, zapni v nastavení správ odpisovanie do 7 dní.
TikTok v Európe správy cez appky nepovoľuje a LinkedIn ich povoľuje len svojim partnerom, tam sa odpisuje priamo v ich appkách.

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
- **Výslovnosť:** hlas pred čítaním sám opraví názvy (PROLINE, TOWER, N2N…), skratky (SCOP, R290, A+++), jednotky (kW, dB(A), °C) a slová písané VEĽKÝMI písmenami, vo všetkých jazykoch a bez AI. Titulky ostanú napísané pôvodne. Vlastné slovo pridáš v **Nastavenia → Výslovnosť**: napíšeš slovo a po slovensky to, ako má znieť (napr. *prolajn*), tlačidlom ▶ si ho vypočuješ. Staršie videá majú starý hlas, stačí im hlas vyrobiť znova.

- **Zvuk videí (od 1.24):** Google hlas sa vyrába po vetách v plnej kvalite (čistejší, nie „telefónny“), pauzy medzi vetami sú krátke a titulky aj striedanie scén idú presne podľa hlasu. Každé video dostane tichú **hudbu pod hlas** (pri reči sa sama stíši), jemný zvuk pri zmene scény a hlasitosť ako ostatné videá na sieťach. Hudba je zabudovaná a zadarmo (3 nálady); vlastná v priečinku Hudba má prednosť. Nastavíš v **Nastavenia → Zvuk videí** (nálada, hlasitosť hudby, efekty, alebo bez hudby). Staršie videá stačí vyrobiť znova, hlas sa urobí nanovo sám.
- **Čísla podľa gramatiky (od 1.25):** hlas číta čísla, desatinné čísla, percentá a jednotky v správnom rode a páde každého jazyka (2 percentá → „dve percentá“, 2 kW → „dva kilowatty“, SCOP 5,14 → „päť celých štrnásť“). Robí to Claude z tvojho plánu: posiela len vety s číslom, všetky jazyky naraz, a každú vetu si zapamätá, takže spotreba je malá. Titulky ostávajú číslicami. Vypneš v **Nastavenia → Zvuk videí**.
- **Nový zvuk (od 1.25.1):** v kroku Video je pri videu tlačidlo „Nový zvuk“ (pri ostatných jazykoch ikonka mikrofónu). Hlas sa nahrá úplne nanovo, povie to trochu inak, a video sa podľa neho zloží znova; obraz ostáva rovnaký. Tlačidlo „Nový hlas“ v kroku Text a hlas tiež nahrá hlas naozaj nanovo. Keď sa zmení spôsob čítania (čísla, výslovnosť), stačí „Vytvoriť znova“ a appka hlas vymení sama.
- **R290 je chladivo, nie názov:** appka už nepíše „PROLINE R290“, ale PROLINE (s chladivom R290).

## 6b. Zdroje projektu
V projekte → Popis a dizajn → **Zdroje**: vlož odkazy na svoj web, text alebo súbory (PDF, TXT, MD). AI si z nich raz urobí výťah faktov a stratégia, nápady aj scenáre z nich vychádzajú.

## 7. Aktualizácie
Prichádzajú samé, nič nerobíš. Dáta ostávajú v priečinku *Knižnica → Application Support → SocialManager → data*.

## 8. Keď niečo nejde

- *Claude: ručný režim* → v Termináli/PowerShell spusti `claude` a prihlás sa. Prípadne v Nastaveniach vlož cestu ku Claude Code.
- *„prihlásenie vypršalo"* → v Účtoch účet pripoj znova.
- Záloha dát = skopíruj priečinok `data` (v Application Support/SocialManager).
- Keď appka spadne, sama sa znova zapne. Ak nie, pošli Claudovi súbor `data/chyby.log`.
- **Popisky a hashtagy (od 1.26):** appka ku každému videu sama poskladá popisok pre každú sieť, krajinu a jazyk podľa toho, čo dnes funguje: prvý riadok je háčik s hľadaným slovom, potom krátka hodnota, otázka do komentárov a na TikToku/Instagrame výzva uložiť si to. Hashtagy: TikTok a Instagram 5 (Instagram viac nedovolí), YouTube 4 (prvé 3 sa ukážu nad názvom), Facebook a LinkedIn 3. Vždy značka, hlavná téma krajiny (striedajú sa) a téma videa, nikdy #fyp či #viral. Zakázané tvrdenia projektu sa z popiskov vyhodia. Ukážku pre každú sieť vidíš v kroku Prototyp (karta „Popisky pre siete“) aj v Kontrole (tlačidlo „Popisky pre siete“).
- **Hashtagy krajín:** v projekte → Popis a dizajn → „Hashtagy krajín“. Sú to hashtagy, ktoré ľudia v danej krajine naozaj používajú (napr. v Španielsku #aerotermia, nie doslovný preklad). Pripravia sa samé pri prvom rozšírení videa do jazykov jedným lacným AI volaním za celý projekt, potom už nič nestoja. Vlastné hashtagy značky nastavíš v poli „Hashtagy značky“.
