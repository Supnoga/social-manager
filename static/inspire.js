// ================= INŠPIRÁCIA A KVALITA (1.16) =================
Object.assign(IC, {
  question: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  bookmark: '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  cloud: '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
});
const TPLN = { chyby: '3 chyby', mytus: 'Mýtus vs. fakt', cena: 'Koľko to stojí', ab: 'A vs. B', predpo: 'Pred / po', pov: 'POV', navod: 'Návod v 3 krokoch', odpoved: 'Odpoveď na otázku', novinka: 'Reakcia na novinku', pribeh: 'Príbeh zákazníka', kviz: 'Uhádneš?', zledobre: 'Zle vs. dobre', vysvetli: 'Za 30 sekúnd', top: 'Top 5', test: 'Experiment', zakulisie: 'Zákulisie', prestan: 'Prestaň robiť…', tajomstvo: 'Toto ti nikto nepovie' };

async function rInspire(b, p) {
  const lang = S.inspLang || p.source_lang;
  const d = await api(`/api/inspire/${p.id}?lang=${lang}`);
  const w = await api(`/api/weather/${p.id}`).catch(() => ({ alerts: [] }));
  const dm = x => x.slice(8, 10) + '.' + x.slice(5, 7) + '.';
  const wCard = `<div class="card"><h2>${I('cloud')}Počasie ako spúšťač</h2>
    <p class="small dim">Appka denne sleduje predpoveď vo všetkých tvojich krajinách. Keď niekam ide mráz, prudké ochladenie alebo horúčava, navrhne video práve pre tie krajiny a naplánuje ho na správny deň. Zadarmo, bez AI${w.at ? ' · naposledy ' + esc(w.at) : ''}.</p>
    ${w.alerts.length ? `<table>${w.alerts.map(a => `<tr><td style="width:70px"><b style="color:var(--acc);font-size:18px">${a.temp} °C</b></td><td><b>${esc(a.name)}</b> okolo ${dm(a.date)}${a.has_idea ? ' <span class="chip ok">nápad je</span>' : ''}<div class="small dim">${esc(a.countries.join(' '))}</div></td>
      <td style="text-align:right">${a.has_idea ? '' : `<button class="btn sm" onclick="wIdea(${p.id},'${a.key}')">${I('sparkles', 's')}Nápad</button>`}</td></tr>`).join('')}</table>` : '<p class="small muted">Teraz nič výnimočné. Keď sa niečo blíži, objaví sa to tu a v pondelkových nápadoch.</p>'}</div>`;
  const mixLine = d.mix && d.mix.n >= 6 ? `<div style="margin:10px 0 14px">${d.mix.mix.map(m => `<div class="row small" style="margin:5px 0"><span style="width:150px">${esc(m.name)}</span><div style="flex:1;height:8px;background:#222;border-radius:4px;overflow:hidden"><div style="width:${m.pct}%;height:100%;background:${d.mix.lack === m.key ? '#ff4d4d' : 'var(--acc)'}"></div></div><span class="dim" style="width:92px;text-align:right">${m.pct} % (cieľ ${m.target})</span></div>`).join('')}
    <div class="small ${d.mix.lack ? '' : 'dim'}">${d.mix.lack ? I('alert', 's') + ' Chýba ti typ „' + esc(d.mix.mix.find(m => m.key === d.mix.lack).name) + '“. Ďalšie nápady ho dostanú prednostne.' : 'Obsah je vyvážený.'}</div></div>` : `<p class="small dim">Pomer typov obsahu sa ukáže po prvých 6 videách. Appka stráži, aby sa striedali rady, dôkazy a aktuálne témy.</p>`;
  const qRow = q => `<tr><td style="width:28px">${I(q.source === 'comment' ? 'send' : 'question', 's')}</td><td>${esc(q.text)}<div class="small dim">${q.source === 'comment' ? 'pýtali sa v komentároch' : 'hľadajú na Googli'}${q.n > 1 ? ' · ' + q.n + '×' : ''} · ${esc((q.lang || '').toUpperCase())}</div></td>
    <td style="text-align:right;white-space:nowrap"><button class="btn sm" onclick="insItem(${p.id},'question',${q.id},'idea')">${I('sparkles', 's')}Nápad</button><button class="btn ghost sm" onclick="insItem(${p.id},'question',${q.id},'hide')">${I('x', 's')}</button></td></tr>`;
  const sRow = s => `<tr><td style="width:64px">${s.thumb ? `<img src="${esc(s.thumb)}" style="width:56px;height:56px;object-fit:cover;border-radius:8px">` : I(s.platform in PL ? s.platform : 'bookmark')}</td>
    <td>${s.url ? `<a href="${esc(s.url)}" target="_blank">${esc(s.title || s.url.slice(0, 70))}</a>` : ''}${s.note ? `<div class="small muted">${esc(s.note)}</div>` : ''}${s.status === 'used' ? '<div class="small dim">už použité na nápad</div>' : ''}</td>
    <td style="text-align:right;white-space:nowrap"><button class="btn sm" onclick="insItem(${p.id},'swipe',${s.id},'idea')">${I('sparkles', 's')}Nápad</button><button class="btn ghost sm" onclick="insItem(${p.id},'swipe',${s.id},'hide')">${I('trash', 's')}</button></td></tr>`;
  b.innerHTML = `<div class="g2" style="align-items:start"><div>
  <div class="card"><div class="row"><h2 style="margin:0;flex:1">${I('question')}Čo ľudia hľadajú a pýtajú sa</h2>
    <select style="max-width:160px" onchange="S.inspLang=this.value;render()">${d.langs.map(l => `<option value="${l}" ${l === d.lang ? 'selected' : ''}>${esc(langName(l))}</option>`).join('')}</select>
    <button class="btn sec sm" onclick="api('/api/inspire/questions/refresh',{method:'POST'}).then(()=>toast('Zisťujem otázky, o pár minút obnov stránku'))">${I('refresh', 's')}</button></div>
    <p class="small dim">Skutočné otázky: čo ľudia píšu do Googlu v danej krajine a čo sa pýtajú v komentároch pod tvojimi videami. Najlepšie témy na videá. Zbiera sa samé raz týždenne, zadarmo, bez AI${d.last ? ' · naposledy ' + esc(d.last) : ''}.</p>
    ${d.questions.length ? `<table>${d.questions.map(qRow).join('')}</table>` : empty('question', 'Zatiaľ žiadne otázky. Klikni na obnovenie vpravo hore (projekt potrebuje kľúčové slová v záložke Trendy).')}</div>
  ${wCard}
  </div><div>
  <div class="card"><h2>${I('bookmark')}Zásobník inšpirácie</h2>
    <p class="small dim">Videl si video, ktoré sa ti páči (TikTok, Reels, YouTube, čokoľvek)? Vlož sem odkaz, prípadne poznámku, čo sa ti na ňom páči. Claude z toho spraví nápad pre teba a v pondelok to dostane prednostne. Berie sa formát, nie obsah.</p>
    <textarea id="swU" placeholder="https://www.tiktok.com/@…/video/…" style="min-height:56px"></textarea>
    <input id="swN" placeholder="Poznámka (nepovinné): napr. páči sa mi rýchly strih a otázka na začiatku" style="margin-top:6px">
    <button class="btn sm" style="margin-top:8px" onclick="insSwipe(${p.id})">${I('plus', 's')}Pridať</button>
    ${d.swipes.length ? `<table style="margin-top:10px">${d.swipes.map(sRow).join('')}</table>` : ''}</div>
  <div class="card"><h2>${I('grid')}Overené formáty</h2>
    <p class="small dim">Claude pri každom nápade vyberie jeden overený formát. Appka si pamätá, ktoré ti fungujú (× = koľkokrát viac pozretí než bežne), a tie ponúka častejšie.</p>
    ${mixLine}
    <table>${d.templates.map(t => `<tr><td><b>${esc(t.name)}</b></td><td class="small dim">${t.used ? t.used + '× použité' : 'ešte nepoužité'}</td><td style="text-align:right">${t.ratio != null ? `<b style="color:${t.ratio >= 1.5 ? 'var(--acc)' : t.ratio < 0.8 ? 'var(--muted)' : '#fff'}">${t.ratio}×</b>` : '<span class="dim">–</span>'}</td></tr>`).join('')}</table></div>
  </div></div>`;
}
async function insItem(pid, kind, id, action) {
  const r = await api(`/api/inspire/${pid}/item`, { method: 'POST', body: { kind, id, action } }, action === 'idea' ? 'Claude vymýšľa…' : null);
  if (action === 'idea') { toast(`Nápady v schránke: ${r.created}`); S.meta = await api('/api/meta'); return go(`p/${pid}/radar/napady`); }
  render();
}
async function wIdea(pid, key) { const r = await api(`/api/weather/${pid}/idea`, { method: 'POST', body: { key } }, 'Claude vymýšľa…'); toast(`Nápady v schránke: ${r.created}`); S.meta = await api('/api/meta'); go(`p/${pid}/radar/napady`); }
async function insSwipe(pid) { const r = await api(`/api/inspire/${pid}/swipe`, { method: 'POST', body: { urls: $('#swU').value, note: $('#swN').value } }, 'Ukladám…'); toast(`Pridané: ${r.added}`); render(); }

// ---------- kontrola kvality scenára ----------
async function qualityCard(sid, iid) {
  const el = $('#qual'); if (!el) return;
  const d = await api(`/api/scripts/${sid}/quality`);
  const col = d.score >= 80 ? 'var(--ok, #3ecf8e)' : d.score >= 60 ? 'var(--acc)' : '#ff4d4d';
  const bad = d.items.filter(i => !i.ok), good = d.items.filter(i => i.ok);
  el.innerHTML = `<div class="card"><div class="row"><h2 style="margin:0;flex:1">${I('gauge')}Kvalita scenára</h2><b style="font-size:26px;color:${col}">${d.score}</b><span class="dim">/100</span></div>
    <p class="small dim" style="margin:4px 0 10px">Kontrola podľa pravidiel, ktoré fungujú na TikToku, Reels a Shorts. Bez AI, nič to nestojí. Video má ~${d.seconds} s.</p>
    ${bad.map(i => `<div class="small" style="margin:6px 0">${I('alert', 's')} ${esc(i.text)}</div>`).join('')}
    ${good.length ? `<details style="margin-top:6px"><summary class="small dim">V poriadku (${good.length})</summary>${good.map(i => `<div class="small muted" style="margin:4px 0">${I('check', 's')} ${esc(i.text)}</div>`).join('')}</details>` : ''}
    <div class="row" style="margin-top:12px">${bad.length ? `<button class="btn sm" onclick="improveScript(${sid})">${I('zap', 's')}Opraviť jedným klikom</button>` : ''}<button class="btn sec sm" onclick="hookIdeas(${iid},${sid})">${I('sparkles', 's')}Silnejší začiatok</button>
      ${S._improved === sid ? `<button class="btn ghost sm" onclick="improveUndo(${sid})">${I('refresh', 's')}Vrátiť pôvodný</button>` : ''}</div></div>`;
}
async function hookIdeas(iid, sid) {
  const d = await api(`/api/ideas/${iid}/hooks`, { method: 'POST' }, 'Claude hľadá silnejší začiatok…');
  S._hooks = d.hooks;
  modal(`<h2>${I('sparkles')}Silnejší začiatok videa</h2><p class="small dim">Teraz: „${esc(d.current)}“</p>
    ${d.hooks.map((h, k) => `<div class="card" style="margin:8px 0;cursor:pointer" onclick="useHook(${iid},${k})"><div class="row"><span style="flex:1">${esc(h)}</span>${I('check', 's')}</div></div>`).join('')}
    <p class="small dim">Klikni na ten, ktorý sa ti páči. Nahradí prvú vetu v texte pre hlas.</p>`);
}
async function useHook(iid, k) { await api(`/api/ideas/${iid}/use-hook`, { method: 'POST', body: { hook: S._hooks[k] } }); closeModal(); toast('Začiatok zmenený'); render(); }
async function improveScript(sid) {
  if ($('#sVo')) await saveScript(sid).catch(() => { });
  const r = await api(`/api/scripts/${sid}/improve`, { method: 'POST' }, 'Claude opravuje scenár…');
  if (r.changed) { S._improved = sid; toast(`Kvalita ${r.before} → ${r.after}` + (r.translations ? '. Preklady vyrob znova v kroku Text a hlas.' : '')); }
  render();
}
async function improveUndo(sid) { await api(`/api/scripts/${sid}/improve-undo`, { method: 'POST' }); S._improved = 0; toast('Vrátený pôvodný scenár'); render(); }
async function mkSeries(pid, iid) { const r = await api(`/api/ideas/${iid}/series`, { method: 'POST' }, 'Claude píše pokračovania…'); toast(`Séria „${r.series}“: ${r.created} pokračovania v schránke`); S.meta = await api('/api/meta'); go(`p/${pid}/radar/napady`); }
