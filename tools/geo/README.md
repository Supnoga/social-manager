# Dáta pre mapy vo videách (app/geo)

Všetko zadarmo s licenciou vhodnou na komerčné videá:
- Natural Earth (verejná doména): hranice krajín 1:10m v pohľade „DEU“ (medzinárodne uznávané hranice), mestá, rieky a kanály 1:50m.
- i18n-iso-countries (MIT): názvy krajín v jazykoch appky.
- flag-icons (MIT): vlajky.
- d3-geo, d3-array, topojson-client (ISC): kreslenie máp v prehliadači.

Obnova dát: v prázdnom priečinku `npm i d3-geo d3-array topojson-client topojson-server topojson-simplify i18n-iso-countries flag-icons`,
stiahnuť z github.com/nvkelso/natural-earth-vector/geojson súbory ne_10m_admin_0_countries_deu (ako pov10_deu.geojson),
ne_10m_populated_places, ne_50m_rivers_lake_centerlines, potom `node build.js 0.002`, `node names.js <jazyky>`, `python3 places.py`.
