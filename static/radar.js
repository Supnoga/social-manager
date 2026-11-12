// ================= RADAR, VÝSLEDKY, PLÁNOVANIE NA TÝŽDEŇ =================
Object.assign(IC, {
  radar: '<path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"/><path d="M4 6h.01"/><path d="M2.29 9.62A10 10 0 1 0 21.31 8.35"/><path d="M16.24 7.76A6 6 0 1 0 8.23 16.67"/><path d="M12 18h.01"/><path d="M17.99 11.66A6 6 0 0 1 15.77 16.67"/><circle cx="12" cy="12" r="2"/><path d="m13.41 10.59 5.66-5.66"/>',
  trend: '<path d="M22 7 13.5 15.5 8.5 10.5 2 17"/><path d="M16 7h6v6"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
  repeat: '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
});

const STAGE = { rastie: ['rastie', 'ok'], vrchol: ['vrchol', 'acc'], slabne: ['slabne', ''] };
const SRC = { gtrends: 'Google Trendy', news: 'Správy', wiki: 'Wikipédia', yt_pop: 'YouTube' };

async function pRadar(m) {
  const r = R(), tab = (S.pf ? r[3] : r[2]) || 'napady';
  if (!S.projects.length) { m.innerHTML = `<div class="card">${empty('radar', 'Najprv vytvor projekt.')}</div>`; return; }
  const pid = S.pf || +r[1] || S.radarP || S.projects[0].id; S.radarP = pid;
  const p = S.projects.find(x => x.id === pid) || S.projects[0];
  const tabs = [['napady', 'inbox', 'Nápady'], ['inspiracia', 'bookmark', 'Inšpirácia'], ['udalosti', 'calendar', 'Udalosti'], ['trendy', 'trend', 'Trendy'], ['konkurencia', 'users', 'Konkurencia'], ['vysledky', 'chart', 'Výsledky']];
  m.innerHTML = `<div class="top"><div>${pTitle('Radar')}<p class="sub">Appka sama sleduje trendy, konkurenciu a čísla tvojich videí. Claude z toho raz týždenne navrhne nápady.</p></div><span class="sp"></span>
    ${S.pf ? '' : `<select onchange="go('p/'+this.value+'/radar/${tab}')" style="max-width:240px">${S.projects.map(x => `<option value="${x.id}" ${x.id === p.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>`}</div>
  <div class="tabs">${tabs.map(([k, ic, n]) => `<a href="#/p/${p.id}/radar/${k}" class="${tab === k ? 'on' : ''}">${I(ic, 's')}${n}</a>`).join('')}</div><div id="rbody"></div>`;
  const b = $('#rbody');
  if (tab === 'napady') await rInbox(b, p);
  else if (tab === 'inspiracia') await rInspire(b, p);
  else if (tab === 'udalosti') await rEvents(b, p);
  else if (tab === 'trendy') await rTrends(b, p);
  else if (tab === 'konkurencia') await rComp(b, p);
  else await rResults(b, p);
}

async function rInbox(b, p) {
  const d = await api(`/api/radar/${p.id}/inbox`);
  const card = (i, snoozed) => `<div class="card" style="margin-bottom:10px"><div class="row" style="align-items:flex-start">
    <div style="flex:1"><div class="row" style="gap:6px;margin-bottom:4px">${i.source === 'repeat' ? `<span class="chip ok">${I('repeat', 's')}variácia úspešného</span>` : i.source === 'series' ? `<span class="chip ok">${I('layers', 's')}séria</span>` : i.source === 'event' ? `<span class="chip acc">${I('calendar', 's')}udalosť ${esc((i.due_date || '').slice(8, 10) + '.' + (i.due_date || '').slice(5, 7) + '.')}</span>` : `<span class="chip acc">${I('radar', 's')}Radar</span>`}<span class="chip">skóre ${i.score}</span>${i.template && TPLN[i.template] ? `<span class="chip">${esc(TPLN[i.template])}</span>` : ''}${i.ref?.label ? `<span class="small dim">z: ${esc(i.ref.label)}</span>` : ''}</div>
      <h2 style="margin:4px 0">${esc(i.title)}</h2><div class="muted">„${esc(i.hook)}“</div>
      ${i.why_now ? `<div class="small" style="margin-top:6px">${I('clock', 's')} ${esc(i.why_now)}</div>` : ''}${i.why ? `<div class="small dim" style="margin-top:4px">${esc(i.why)}</div>` : ''}</div>
    <div class="row" style="flex-direction:column;gap:6px"><button class="btn sm" onclick="rIdea(${i.id},'accept')">${I('check', 's')}Beriem</button>
      ${snoozed ? '' : `<button class="btn sec sm" onclick="rIdea(${i.id},'snooze')">${I('clock', 's')}Neskôr</button>`}
      <button class="btn ghost sm" onclick="rIdea(${i.id},'reject')">${I('x', 's')}Nie</button></div></div></div>`;
  b.innerHTML = `<div class="row" style="margin-bottom:12px"><p class="muted small" style="flex:1;margin:0">Nové nápady chodia samé každý pondelok (1 volanie Claude na projekt). „Beriem“ ich presunie medzi tvoje videá.</p>
    <button class="btn sec sm" onclick="rWeekly(${p.id})">${I('sparkles', 's')}Navrhnúť teraz</button></div>
    ${d.inbox.length ? d.inbox.map(i => card(i)).join('') : `<div class="card">${empty('inbox', 'Schránka je prázdna. Nápady pribudnú v pondelok, alebo klikni Navrhnúť teraz.')}</div>`}
    ${d.snoozed.length ? `<h2 style="margin-top:20px">${I('clock')}Odložené</h2>${d.snoozed.map(i => card(i, true)).join('')}` : ''}`;
}
async function rIdea(id, action) { await api('/api/radar/idea/' + id, { method: 'POST', body: { action } }); if (action === 'accept') toast('Pridané medzi videá projektu'); S.meta = await api('/api/meta'); sidebar(); render(); }
async function rWeekly(pid) { const r = await api(`/api/radar/${pid}/weekly`, { method: 'POST', body: {} }, 'Claude pozerá trendy a výsledky…'); toast(r.created ? `Nových nápadov: ${r.created}` : (r.note || 'Nič nové'), !r.created); S.meta = await api('/api/meta'); render(); }

async function rTrends(b, p) {
  const d = await api(`/api/radar/${p.id}/trends`);
  const kw = Object.entries(d.keywords);
  b.innerHTML = `<div class="card" style="margin-bottom:14px"><div class="row"><div style="flex:1"><b>Čo sleduje:</b> <span class="small muted">${kw.length ? esc((d.keywords[p.source_lang] || kw[0][1]).join(', ')) : 'kľúčové slová sa ešte len pripravia'}</span>
    <div class="small dim">Zdroje: Google Trendy, Google Správy, Wikipédia${S.meta.yt_key ? ', YouTube' : ''} · ${d.items} tém za posledné dni · zadarmo, bez AI</div></div>
    <button class="btn sec sm" onclick="rKw(${p.id})">${I('refresh', 's')}Obnoviť slová</button><button class="btn sec sm" onclick="rRun()">${I('radar', 's')}Skontrolovať teraz</button></div></div>
  ${d.trends.length ? `<div class="card"><table>${d.trends.map(t => `<tr><td style="width:56px"><b style="font-size:18px;color:${t.heat >= 60 ? 'var(--acc)' : '#fff'}">${t.heat}</b></td>
    <td><div><b>${esc(t.label)}</b> <span class="chip ${STAGE[t.stage][1]}">${STAGE[t.stage][0]}</span>${t.pinned ? ' <span class="chip acc">pripnuté</span>' : ''}</div>
      <div class="small dim">${t.sources.map(s => SRC[s] || s).join(', ')} · ${(t.countries.length ? t.countries : t.langs).join(' ').toUpperCase()}${t.ctx ? ' · ' + esc(t.ctx.slice(0, 140)) : ''}</div></td>
    <td style="text-align:right;white-space:nowrap">${t.urls[0] ? `<a class="btn ghost sm" target="_blank" href="${esc(t.urls[0])}">${I('ext', 's')}</a>` : ''}
      <button class="btn sm" onclick="rTrend(${p.id},'${t.key}','idea')">${I('sparkles', 's')}Nápad z tohto</button>
      <button class="btn ghost sm" title="${t.pinned ? 'Odopnúť' : 'Pripnúť'}" onclick="rTrend(${p.id},'${t.key}','${t.pinned ? 'unpin' : 'pinned'}')">${I(t.pinned ? 'x' : 'target', 's')}</button>
      <button class="btn ghost sm" title="Nezaujíma ma" onclick="rTrend(${p.id},'${t.key}','ignored')">${I('trash', 's')}</button></td></tr>`).join('')}</table></div>`
    : `<div class="card">${empty('trend', 'Zatiaľ žiadne trendy k tomuto projektu. Radar zbiera dáta na pozadí – prvé výsledky do hodiny. Ak projekt nemá popis, doplň ho, nech appka vie, čo hľadať.')}</div>`}`;
}
async function rTrend(pid, key, action) { const r = await api(`/api/radar/${pid}/trend`, { method: 'POST', body: { key, action } }, action === 'idea' ? 'Claude vymýšľa…' : null); if (action === 'idea') { toast(`Nápady v schránke: ${r.created}`); S.meta = await api('/api/meta'); return go(`p/${pid}/radar/napady`); } render(); }
async function rKw(pid) { const r = await api(`/api/radar/${pid}/keywords`, { method: 'POST', body: {} }, 'Pripravujem kľúčové slová…'); toast(`Slová pre ${r.langs} jazykov`); render(); }
async function rRun() { await api('/api/radar/run', { method: 'POST' }); toast('Radar beží na pozadí, o pár minút obnov stránku'); }

async function rComp(b, p) {
  const d = await api(`/api/radar/${p.id}/competitors`);
  b.innerHTML = `${d.yt_key ? '' : `<div class="hint" style="margin-bottom:14px">${I('alert')}<div>Na sledovanie YouTube kanálov treba bezplatný YouTube kľúč. <a href="#/nastavenia">Nastavenia → Radar</a></div></div>`}
  <div class="g2" style="align-items:start"><div class="card"><h2>${I('users')}Sledované účty</h2>
    <label class="l">Odkazy na kanály (jeden na riadok)</label><textarea id="cUrls" placeholder="https://www.youtube.com/@kanal"></textarea>
    <button class="btn sm" style="margin-top:8px" onclick="rCompAdd(${p.id})">${I('plus', 's')}Pridať</button>
    <p class="small dim">YouTube sa sleduje automaticky. TikTok a Instagram oficiálne čítať nedovolia, tie si appka len zapamätá ako odkaz.</p>
    ${d.competitors.length ? `<table>${d.competitors.map(c => `<tr><td>${I(c.platform === 'youtube' ? 'youtube' : c.platform in PL ? c.platform : 'link', 's')}</td><td><a href="${esc(c.url)}" target="_blank">${esc(c.name)}</a><div class="small dim">${c.mode === 'auto' ? `${c.posts} videí · ${(c.followers || 0).toLocaleString('sk')} odberateľov` : 'len odkaz'}${c.last_error ? ' · <span class="bad-t">' + esc(c.last_error.slice(0, 80)) + '</span>' : ''}</div></td>
      <td style="text-align:right"><button class="btn ghost sm" onclick="api('/api/radar/competitors/${c.id}',{method:'DELETE'}).then(render)">${I('trash', 's')}</button></td></tr>`).join('')}</table>` : ''}</div>
  <div class="card"><h2>${I('zap')}Videá, ktoré im ušli nad normál</h2><p class="small dim">Video, ktoré má aspoň 3× viac pozretí ako je u daného kanála bežné. Z nich sa berie formát, nie obsah.</p>
    ${d.outliers.length ? `<table>${d.outliers.map(o => `<tr><td style="width:56px"><b style="color:var(--acc)">${o.ratio}×</b></td><td><a href="${esc(o.url)}" target="_blank">${esc(o.title)}</a><div class="small dim">${esc(o.channel)} · ${(o.views || 0).toLocaleString('sk')} pozretí · ${esc(o.published_at.slice(0, 10))}</div></td>
      <td style="text-align:right;white-space:nowrap"><button class="btn sm" onclick="rCompIdea(${p.id},${o.id})">${I('sparkles', 's')}Nápad</button><button class="btn ghost sm" onclick="api('/api/radar/${p.id}/comp-post/${o.id}',{method:'POST',body:{action:'hide'}}).then(render)">${I('x', 's')}</button></td></tr>`).join('')}</table>` : empty('zap', 'Zatiaľ nič výnimočné.')}</div></div>`;
}
async function rCompAdd(pid) { const r = await api(`/api/radar/${pid}/competitors`, { method: 'POST', body: { urls: $('#cUrls').value } }, 'Pridávam…'); toast(`Pridané: ${r.added.length}` + (r.errors.length ? ' · ' + r.errors.join('; ') : ''), !!r.errors.length); render(); }
async function rCompIdea(pid, id) { const r = await api(`/api/radar/${pid}/comp-post/${id}`, { method: 'POST', body: { action: 'idea' } }, 'Claude vymýšľa…'); toast(`Nápady v schránke: ${r.created}`); S.meta = await api('/api/meta'); go(`p/${pid}/radar/napady`); }

async function rResults(b, p) {
  const d = await api(`/api/results/${p.id}`);
  const hr = h => String(h).padStart(2, '0') + ':00';
  b.innerHTML = `<div class="g2" style="align-items:start"><div>
  <div class="card"><h2>${I('chart')}Ako sa darí videám</h2>
    <p class="small dim">Čísla sa sťahujú samé každých 6 hodín (YouTube, Facebook, Instagram, TikTok Business). „2×“ = video malo 2× viac pozretí, ako je na tom účte bežné. Zmerané: ${d.measured} zverejnení${d.last ? ' · naposledy ' + esc(d.last.slice(5, 16)) : ''}.</p>
    ${d.ideas.length ? `<table>${d.ideas.map(x => `<tr><td style="width:56px"><b style="color:${x.ratio >= 1.8 ? 'var(--acc)' : x.ratio < 0.7 ? 'var(--muted)' : '#fff'}">${x.ratio}×</b></td><td><a href="#/p/${p.id}/v/${x.idea_id}">${esc(x.title || '')}</a><div class="small dim">${x.views.toLocaleString('sk')} pozretí · ${x.likes} páči sa · ${x.comments} komentárov · ${x.posts} účtov</div></td></tr>`).join('')}</table>`
      : empty('chart', 'Zatiaľ žiadne čísla. Objavia sa pár hodín po prvých zverejneniach.')}
    <button class="btn sec sm" style="margin-top:10px" onclick="api('/api/results/refresh',{method:'POST'},'Sťahujem čísla…').then(render)">${I('refresh', 's')}Stiahnuť čísla teraz</button></div>
  <div class="card"><h2>${I('repeat')}Zopakovať úspešné</h2>
    <p class="small muted">Úspešné videá (aspoň 1,8× nad normál) appka pri plánovaní dáva na účty, kde ešte neboli, ako prvé. Tu k nim Claude navrhne nové variácie s iným začiatkom (1 malé volanie).</p>
    ${d.winners.length ? `<ul class="small">${d.winners.map(w => `<li>${esc(w.title)} <b style="color:var(--acc)">${w.ratio}×</b></li>`).join('')}</ul><button class="btn sm" onclick="rRepeat(${p.id})">${I('repeat', 's')}Vytvoriť variácie</button>` : '<p class="small dim">Zatiaľ žiadny výrazný úspech.</p>'}</div>
  </div><div>
  <div class="card"><h2>${I('clock')}Najlepšie časy</h2><p class="small dim">Keď má účet dosť čísel, časy sa učia z neho. Dovtedy štandardné časy pre danú sieť a krajinu.</p>
    ${d.times.length ? `<table>${d.times.map(t => `<tr><td>${plat(t.platform, false)}</td><td>${esc(t.account)} <span class="small dim">${esc((t.lang || '').toUpperCase())}</span></td><td>${t.hours.map(hr).join(', ')}</td><td class="small dim">${esc(t.how)}</td></tr>`).join('')}</table>` : empty('clock', 'Žiadne účty.')}</div>
  ${d.learnings ? `<div class="card"><h2>${I('bulb')}Čo appka posiela Claudovi</h2><p class="small dim">Pri vymýšľaní nápadov dostane Claude tento krátky výťah, aby staval na tom, čo funguje:</p><p class="small muted">${esc(d.learnings)}</p></div>` : ''}
  </div></div>`;
}
async function rRepeat(pid) { const r = await api(`/api/results/${pid}/repeat`, { method: 'POST' }, 'Claude vymýšľa variácie…'); toast(`Nových variácií v schránke: ${r.ideas}`); S.meta = await api('/api/meta'); go(`p/${pid}/radar/napady`); }

// ---------- Naplánovať týždeň ----------
function planDialog() {
  const st = S.meta.settings;
  modal(`<h2>${I('calendar')}Naplánovať týždeň</h2>
  <p class="muted small">Appka rozdelí hotové videá na všetky účty na 7 dní dopredu: každý účet dostane videá svojho projektu a jazyka, ktoré na ňom ešte neboli, v najlepšie časy pre ten účet. Úspešné videá idú prvé.</p>
  <label class="l">Projekty</label><div class="pick">${S.projects.map(p => `<label><input type="checkbox" name="pwp" value="${p.id}" ${!S.pf || S.pf === p.id ? 'checked' : ''}><span class="dot" style="background:${p.color}"></span>${esc(p.name)}</label>`).join('')}</div>
  <label class="l">Koľko videí denne na jeden účet</label><select id="pwN">${[1, 2, 3].map(n => `<option ${n === +st.plan_per_day ? 'selected' : ''}>${n}</option>`).join('')}</select>
  ${planOwn(st)}
  <label class="row" style="margin-top:12px"><input type="checkbox" id="pwAuto" ${st.auto_plan_week ? 'checked' : ''}> Každú nedeľu večer naplánovať ďalší týždeň samé</label>
  ${st.require_approval !== false ? `<p class="small dim">${I('eye', 's')} Videá najprv čakajú v Kontrole na tvoje schválenie.</p>` : ''}
  <div class="row" style="margin-top:16px"><button class="btn" onclick="planRun()">${I('calendar')}Naplánovať</button></div>`);
}
function planOwn(st) {
  const pp = st.plan_projects || {}, dn = ['Po', 'Ut', 'St', 'Št', 'Pi', 'So', 'Ne'];
  const rows = S.projects.filter(p => pp[p.id] && (pp[p.id].days || []).length).map(p => `<b>${esc(p.name)}</b>: ${pp[p.id].days.length === 7 ? 'každý deň' : pp[p.id].days.map(d => dn[d]).join(', ')}${(pp[p.id].hours || []).length ? ', krátke o ' + pp[p.id].hours.map(h => h + ':00').join(', ') : ''}${(pp[p.id].long_hours || []).length ? ', dlhé o ' + pp[p.id].long_hours.map(h => h + ':00').join(', ') : ''}`);
  const ap = st.auto_produce || {};
  const auto = S.projects.filter(p => ap[p.id]).map(p => `<b>${esc(p.name)}</b>: ${ap[p.id].short || 0} krátke a ${ap[p.id].long || 0} dlhé denne${ap[p.id].from_long ? ' (Shorts sa robia z dlhého videa a idú von až po ňom)' : ''}`);
  return (rows.length ? `<p class="small dim">${I('clock', 's')} Vlastný rytmus podľa stratégie: ${rows.join(' · ')}</p>` : '')
    + (auto.length ? `<p class="small dim">${I('sparkles', 's')} Videá si appka vyrába a plánuje sama: ${auto.join(' · ')}</p>` : '');
}
async function planRun() {
  const ids = $$('[name=pwp]:checked').map(c => +c.value), per = +$('#pwN').value, auto = $('#pwAuto').checked;
  await api('/api/settings', { method: 'POST', body: { auto_plan_week: auto, plan_per_day: per } });
  const r = await api('/api/plan/week', { method: 'POST', body: { project_ids: ids.length === S.projects.length ? null : ids, per_day: per } }, 'Plánujem týždeň…');
  closeModal(); S.meta = await api('/api/meta');
  const full = r.accounts.length - r.empty.length - r.short.length;
  modal(`<h2>${I('check')}Naplánovaných ${r.created} videí</h2>
    <p class="muted">${full} účtov má plný týždeň${r.short.length ? `, ${r.short.length} len čiastočne` : ''}${r.empty.length ? `, ${r.empty.length} nemá žiadne nové video` : ''}.</p>
    ${r.empty.length || r.short.length ? `<p class="small dim">Chýbajúce videá: ${esc([...r.empty, ...r.short].slice(0, 20).join(', '))}${r.empty.length + r.short.length > 20 ? '…' : ''}. Vyrob ďalšie videá a klikni znova – doplní sa len to, čo chýba.</p>` : ''}
    ${r.review ? `<a class="btn" href="#/${S.pf ? 'p/' + S.pf + '/' : ''}kontrola" onclick="closeModal()">${I('eye')}Otvoriť Kontrolu</a>` : `<button class="btn" onclick="closeModal();render()">${I('check')}OK</button>`}`);
}

// ---------- Udalosti a sviatky ----------
const EVK = { 'sviatok': ['štátny sviatok', ''], 'prianie': ['na prianie', 'acc'], 'deň': ['bežný deň', ''], 'sezóna': ['sezóna', ''], 'téma': ['téma projektu', 'ok'] };
async function rEvents(b, p) {
  const d = await api(`/api/events/${p.id}?days=75`);
  const dn = x => new Date(x + 'T12:00').toLocaleDateString('sk', { weekday: 'short', day: 'numeric', month: 'long' });
  b.innerHTML = `<div class="g2" style="align-items:start;grid-template-columns:2fr 1fr"><div class="card"><h2>${I('calendar')}Blíži sa (75 dní)</h2>
    <p class="small dim">Štátne sviatky krajín tvojich jazykov, bežné dni (Vianoce, Halloween…) a tematické dni projektu. Nápady k udalostiam o 1–3 týždne pribudnú v pondelok samé. Video k udalosti sa pri plánovaní dá presne na jej deň a len na účty krajín, kde sa oslavuje.</p>
    ${d.events.length ? `<table>${d.events.map(e => `<tr><td style="width:120px"><b>${dn(e.date)}</b><div class="small ${e.days_left <= 7 ? 'bad-t' : 'dim'}">${e.days_left ? 'o ' + e.days_left + ' dní' : 'dnes'}</div></td>
      <td><b>${esc(e.name)}</b> <span class="chip ${EVK[e.kind]?.[1] || ''}">${EVK[e.kind]?.[0] || e.kind}</span>${e.has_idea ? ' <span class="chip ok">nápad je</span>' : ''}
        <div class="small dim">${e.all ? 'všetky jazyky' : (e.countries.length ? e.countries.join(' ') : e.langs.join(' ').toUpperCase())}${e.why && e.why !== e.name ? ' · ' + esc(e.why) : ''}</div></td>
      <td style="text-align:right;white-space:nowrap"><button class="btn sm" onclick="evIdea(${p.id},'${esc(e.key)}','video')">${I('sparkles', 's')}Video</button>
        <button class="btn sec sm" onclick="evIdea(${p.id},'${esc(e.key)}','greeting')">${I('send', 's')}Prianie</button>
        <button class="btn ghost sm" title="Nezaujíma ma" onclick="api('/api/events/${p.id}/ignore',{method:'POST',body:{key:'${esc(e.key)}'}}).then(render)">${I('x', 's')}</button></td></tr>`).join('')}</table>`
      : empty('calendar', 'Nič v najbližších týždňoch.')}</div>
  <div class="card"><h2>${I('target')}Tematické dni projektu</h2>
    <p class="small dim">Dni, ktoré zaujímajú tvoje publikum (napr. Deň Zeme, Deň tepelných čerpadiel). Claude ich navrhne raz podľa popisu projektu, môžeš pridať aj vlastné. Dátumy over, či sedia.</p>
    ${d.custom.length ? `<table>${d.custom.map(c => `<tr><td><b>${esc(c.name)}</b><div class="small dim">${esc(c.rule)}${c.why ? ' · ' + esc(c.why) : ''}</div></td><td style="text-align:right"><button class="btn ghost sm" onclick="api('/api/events/custom/${c.id}',{method:'DELETE'}).then(render)">${I('trash', 's')}</button></td></tr>`).join('')}</table>` : ''}
    <div class="row" style="margin-top:10px"><input id="evN" placeholder="Názov dňa" style="flex:2"><input id="evD" placeholder="22.4." style="flex:1;max-width:90px"><button class="btn sec sm" onclick="evAdd(${p.id})">${I('plus', 's')}</button></div>
    <button class="btn sec sm" style="margin-top:10px" onclick="evSuggest(${p.id})">${I('sparkles', 's')}Navrhnúť dni pre projekt</button></div></div>`;
}
async function evIdea(pid, key, kind) { const r = await api(`/api/events/${pid}/idea`, { method: 'POST', body: { key, kind } }, kind === 'greeting' ? 'Claude píše prianie…' : 'Claude vymýšľa…'); toast(`Nápady v schránke: ${r.created}`); S.meta = await api('/api/meta'); go(`p/${pid}/radar/napady`); }
async function evAdd(pid) { await api(`/api/events/${pid}/custom`, { method: 'POST', body: { name: $('#evN').value, rule: $('#evD').value } }); render(); }
async function evSuggest(pid) { const r = await api(`/api/events/${pid}/suggest`, { method: 'POST' }, 'Claude hľadá dni pre projekt…'); toast(`Pridaných dní: ${r.added}`); render(); }
