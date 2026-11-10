# Social Manager na serveri

Cieľ: redakcia beží stále, aj keď je Mac vypnutý. Na serveri je **režim nasucho** (`SM_DRY_RUN=1`):
nič sa nenahráva na siete, neodpovedá na komentáre ani správy a nemenia sa profily. Ostré publikovanie sa zapína až po súhlase.

## Spustenie (Docker)
1. Na serveri: `git clone https://github.com/Supnoga/social-manager /opt/social-manager && cd /opt/social-manager`
2. `cp deploy/server.env.example deploy/server.env` a doplniť kľúče (súbor ostáva len na serveri, je v `.gitignore`).
3. `docker compose -f deploy/docker-compose.yml up -d --build`
4. Appka sa otvára cez SSH tunel: `ssh -L 8765:127.0.0.1:8765 server`, potom v prehliadači `http://localhost:8765`.
   Zvonka je appka zavretá (port je len na 127.0.0.1 a appka pustí iba lokálne požiadavky).

Bez Dockeru: `deploy/social-manager.service` (systemd).
Prenesenie dát z Macu: obsah priečinka `data/` skopírovať do zväzku `sm-data` (alebo nastaviť `SM_DATA_DIR`).

## AI a náklady
- Na serveri AI ide cez firemný API kľúč (`SM_AI_BACKEND=api`), nie cez osobný Max plán.
- Preklady robí najprv bezplatný DeepL / Microsoft / Google so slovníkom pojmov a pamäťou prekladov (0 tokenov).
- Prekladá sa len schválený a nový alebo zmenený text; nezmenené preklady sa preskočia.
- AI (Claude Haiku 5.5, bez premýšľania) len opraví preklady, ktoré neprešli kontrolou, a to jednou dávkou (Batch API, polovičná cena).
- Denný strop: nastavenie `ai_daily_token_cap` (predvolene 300 000 tokenov). Po ňom AI stojí do ďalšieho dňa.

## Redakcia z príkazového riadku
```
python -m app.redakcia kolo --projekt 1            # celé kolo: schválenia, preklad nového, opravy, plán nasucho
python -m app.redakcia preklad --projekt 1 --jazyky cs,de,pl,hu
python -m app.redakcia vzorka --projekt 1          # čo má človek skontrolovať
python -m app.redakcia plan --projekt 1 --dni 7    # plán nasucho, nič nezapíše
```
Rozhranie pre appku: `/api/redakcia/...` (slovník pojmov, schválenie zdroja, preklad, vzorka, posudok, plán nasucho).
