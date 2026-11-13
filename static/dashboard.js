// ================= DASHBOARD: výsledky s filtrami a grafmi (bez AI, počíta prehliadač) =================
Object.assign(IC, {
  dash: '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  eye2: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  heart: '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7z"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  pct: '<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
});

// farby sietí: pevné poradie (overená farebná paleta pre tmavé pozadie), farba patrí sieti, nie poradiu
const NET_C = { youtube: '#3987e5', tiktok: '#d95926', instagram: '#199e70', facebook: '#c98500', linkedin: '#d55181' };
const DM = { v: ['Pozretia', 'eye2'], lk: ['Páči sa mi', 'thumbUp'], cm: ['Komentáre', 'message'], r: ['Reakcie', 'heart'], er: ['Zapojenie', 'pct'], n: ['Príspevky', 'film'] };
const DAYS = [[7, '7 dní'], [30, '30 dní'], [90, '3 mesiace'], [365, 'Rok']];
const WD = ['Po', 'Ut', 'St', 'Št', 'Pi', 'So', 'Ne'];
S.dash = S.dash || { days: 30, pl: '', c: '', l: '', p: '', m: 'v' };
let DD = null; // načítané dáta { key, ... }

const nf = n => Math.round(n).toLocaleString('sk-SK');
const cf = n => n >= 1e6 ? (n / 1e6).toLocaleString('sk-SK', { maximumFractionDigits: 1 }) + ' mil.' : n >= 1e4 ? (n / 1e3).toLocaleString('sk-SK', { maximumFractionDigits: n >= 1e5 ? 0 : 1 }) + ' tis.' : nf(n);
const pf = x => (x * 100).toLocaleString('sk-SK', { maximumFractionDigits: 1, minimumFractionDigits: 1 }) + ' %';
const mval = (m, a) => m === 'er' ? (a.v ? a.r / a.v : 0) : a[m];
const mfmt = (m, x) => m === 'er' ? pf(x) : cf(x);
const cName = c => c ? (DD?.countries?.[c] || c) : 'Bez krajiny';
const lName = l => l ? (DD?.langs?.[l] || l) : '–';

function agg(rows) {
  const a = { v: 0, r: 0, lk: 0, cm: 0, sh: 0, n: 0 };
  for (const x of rows) { a.v += x.v; a.lk += x.lk; a.cm += x.cm; a.sh += x.sh; a.n++; }
  a.r = a.lk + a.cm + a.sh; return a;
}
function groupBy(rows, key) {
  const g = {};
  for (const x of rows) { const k = key(x); (g[k] = g[k] || []).push(x); }
  return Object.entries(g).map(([k, rs]) => ({ k, ...agg(rs), rows: rs }));
}

// ---------- tooltip ----------
function dTip(e, html) {
  let t = $('#dtip');
  if (!t) { t = document.createElement('div'); t.id = 'dtip'; t.className = 'dtip'; document.body.appendChild(t); }
  if (!html) { t.style.display = 'none'; return; }
  t.innerHTML = html; t.style.display = 'block';
  const w = t.offsetWidth, h = t.offsetHeight;
  t.style.left = Math.min(e.clientX + 14, innerWidth - w - 8) + 'px';
  t.style.top = (e.clientY + 14 + h > innerHeight ? e.clientY - h - 10 : e.clientY + 14) + 'px';
}
document.addEventListener('mousemove', e => {
  const el = e.target.closest && e.target.closest('[data-tip]');
  if (el) dTip(e, el.dataset.tip); else if ($('#dtip')?.style.display === 'block' && !e.target.closest('.dline')) dTip(e, '');
});

async function pDash(m) {
  const f = S.dash, pid = S.pf || 0;
  const want = f.days * 2;
  const key = `${want}-${f.days}`;
  if (!DD || DD.key !== key) {
    m.innerHTML = `<div class="top"><div>${pTitle('Dashboard')}</div></div><div class="card">${empty('dash', 'Načítavam čísla…')}</div>`;
    DD = await api(`/api/dash?days=${want}&pdays=${f.days}`); DD.key = key;
  }
  const now = Date.now(), dayMs = 864e5, cut = now - f.days * dayMs, cut0 = now - 2 * f.days * dayMs;
  const dstr = t => { const d = new Date(t); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  const cutD = dstr(cut), cut0D = dstr(cut0);
  const ts = x => new Date(x.d.replace(' ', 'T')).getTime();
  const all1 = pid && f.all;
  const proj = pid && !f.all ? pid : +f.p || 0;
  const match = (x, skip) => (!proj || x.p === proj) && (skip === 'pl' || !f.pl || x.pl === f.pl) && (skip === 'c' || !f.c || x.c === f.c) && (skip === 'l' || !f.l || x.l === f.l);
  const all = DD.rows.map(x => ({ ...x, r: x.lk + x.cm + x.sh, ts: ts(x) }));
  const cur = all.filter(x => x.ts >= cut && match(x)), prev = all.filter(x => x.ts >= cut0 && x.ts < cut && match(x));
  const A = agg(cur), P = agg(prev);
  // účty v rozsahu filtrov (aj tie bez príspevkov)
  const accs = (DD.accounts || []).filter(a => match(a));
  const accIds = new Set(accs.map(a => a.id));
  const daily = (DD.daily || []).filter(x => accIds.has(x.a));
  const dCur = daily.filter(x => x.d >= cutD), dPrev = daily.filter(x => x.d >= cut0D && x.d < cutD);
  const sumd = (rs, k) => rs.reduce((s, x) => s + (k === 'sn' ? x.sg - x.sl : x[k]), 0);
  const ytAcc = accs.filter(a => a.pl === 'youtube');
  // sledovatelia: YouTube z denných čísel (presne), ostatné siete z vlastných meraní (od prvého merania)
  const ytDailyIds = new Set(dCur.map(x => x.a));
  const withF = accs.filter(a => a.f != null);
  const F = withF.reduce((s, a) => s + a.f, 0);
  const growthOf = a => a.pl === 'youtube' && ytDailyIds.has(a.id) ? sumd(dCur.filter(x => x.a === a.id), 'sn') : (a.f != null && a.f0 != null ? a.f - a.f0 : 0);
  const FG = withF.reduce((s, a) => s + growthOf(a), 0);
  const fSince = withF.filter(a => !(a.pl === 'youtube' && ytDailyIds.has(a.id)) && a.f0d && a.f0d > cutD).map(a => a.f0d).sort()[0];
  const W = sumd(dCur, 'w') / 60, WP = sumd(dPrev, 'w') / 60;
  // možnosti filtrov (z príspevkov aj účtov)
  const scope = [...all.filter(x => x.ts >= cut && (!proj || x.p === proj)), ...(DD.accounts || []).filter(a => !proj || a.p === proj)];
  const opts = k => [...new Set(scope.map(x => x[k]))].filter(Boolean);
  const nets = PLATS.filter(p => opts('pl').includes(p));
  const ctrs = opts('c').sort((a, b) => cName(a).localeCompare(cName(b), 'sk'));
  const lngs = opts('l').sort((a, b) => lName(a).localeCompare(lName(b), 'sk'));
  const sel = (k, label, list, nameFn) => `<label class="dsel"><span>${label}</span><select onchange="dSet('${k}',this.value)"><option value="">Všetky</option>${list.map(v => `<option value="${esc(String(v))}" ${String(f[k]) === String(v) ? 'selected' : ''}>${esc(nameFn(v))}</option>`).join('')}</select></label>`;
  const anyF = f.pl || f.c || f.l || ((!pid || all1) && f.p);

  const delta = (a, b) => {
    if (!b) return '<span class="dd dim">bez porovnania</span>';
    const d = (a - b) / b, up = d >= 0;
    return `<span class="dd ${up ? 'up' : 'down'}">${up ? '▲' : '▼'} ${pf(Math.abs(d))}</span><span class="dim small"> oproti predtým</span>`;
  };
  const kpi = (k) => `<div class="card dk ${f.m === k ? 'on' : ''}" onclick="dSet('m','${k}')" title="Ukázať v grafoch">
    <div class="row" style="gap:8px">${I(DM[k][1], 's')}<span class="muted small">${DM[k][0]}</span></div>
    <b>${mfmt(k, mval(k, A))}</b><div class="small">${delta(mval(k, A), mval(k, P))}</div></div>`;
  const kpiF = `<div class="card dk nc"><div class="row" style="gap:8px">${I('users', 's')}<span class="muted small">Odberatelia a sledovatelia</span></div>
    <b>${withF.length ? cf(F) : '–'}</b><div class="small">${withF.length ? `<span class="dd ${FG >= 0 ? 'up' : 'down'}">${FG >= 0 ? '+' : ''}${nf(FG)}</span><span class="dim small"> ${fSince ? 'od ' + fSince.slice(8, 10) + '.' + fSince.slice(5, 7) + '.' : 'za obdobie'}</span>` : '<span class="dim">zatiaľ nezmerané</span>'}</div></div>`;
  const kpiW = `<div class="card dk nc"><div class="row" style="gap:8px">${I('clock', 's')}<span class="muted small">Čas sledovania (YouTube)</span></div>
    <b>${dCur.length ? nf(W) + ' h' : '–'}</b><div class="small">${dCur.length ? delta(W, WP) : `<span class="dim">${ytAcc.length ? 'čaká na YouTube Analytics' : 'len YouTube'}</span>`}</div></div>`;

  const seg = `<div class="seg">${DAYS.map(([d, n]) => `<button class="${f.days === d ? 'on' : ''}" onclick="dSet('days',${d})">${n}</button>`).join('')}</div>`;
  const scopeSeg = pid ? `<div class="seg"><button class="${!f.all ? 'on' : ''}" onclick="dScope(0)">Tento projekt</button><button class="${f.all ? 'on' : ''}" onclick="dScope(1)">Všetky projekty</button></div>` : '';
  const nothing = !cur.length && !accs.length;

  m.innerHTML = `<div class="top"><div>${pTitle('Dashboard')}<p class="sub">Pozretia, lajky, komentáre, odberatelia a výroba videí. Čísla sa sťahujú samé zo sietí, nemíňa žiadne AI.</p></div>
    <button class="btn sec" onclick="dRefresh(this)" ${DD.busy ? 'disabled' : ''}>${I('refresh', 's')}${DD.busy ? 'Sťahujem…' : 'Stiahnuť čísla teraz'}</button></div>
  <div class="dfilters">${scopeSeg}${seg}
    ${pid && !f.all ? '' : sel('p', 'Projekt', S.projects.map(p => p.id), v => S.projects.find(p => p.id === +v)?.name || v)}
    ${sel('pl', 'Sieť', nets, v => PL[v])}${sel('c', 'Krajina', ctrs, cName)}${sel('l', 'Jazyk', lngs, lName)}
    ${anyF ? `<button class="btn ghost sm" onclick="dReset()">${I('x', 's')}Zrušiť filtre</button>` : ''}
  </div>
  <div class="dkpis d6">${['v', 'lk', 'cm'].map(kpi).join('')}${kpiF}${kpiW}${kpi('er')}</div>
  ${prodCard(proj, f.days)}
  ${nothing ? `<div class="card">${empty('dash', anyF ? 'Pre tieto filtre zatiaľ nie sú žiadne čísla. Skús iné obdobie alebo zruš filtre.' : 'Zatiaľ žiadne dáta. Čísla sa objavia samé po prvých zverejnených videách (sťahujú sa každých 6 hodín).')}</div>` : ''}
  ${cur.length ? `<div class="card"><div class="row"><h2 style="margin:0;flex:1">${DM[f.m][0]} podľa dňa zverejnenia</h2>${legend([['var(--acc)', 'Toto obdobie'], ['#6b6b6b', 'Predchádzajúce obdobie', 1]])}</div><div id="dLine" class="dline"></div></div>` : ''}
  ${dCur.length ? `<div class="card"><div class="row" style="flex-wrap:wrap;gap:10px"><h2 style="margin:0;flex:1">YouTube deň po dni</h2>
      <div class="seg">${YM.map(([k, n]) => `<button class="${f.ym === k ? 'on' : ''}" onclick="dSet('ym','${k}')">${n}</button>`).join('')}</div></div>
      <p class="small dim" style="margin:6px 0 0">Skutočné denné čísla všetkých videí kanálov z YouTube Analytics (YouTube ich dopĺňa s oneskorením 2 až 3 dni).</p><div id="dYt" class="dline"></div></div>` : ''}
  ${yppCard(ytAcc, f)}
  ${(!proj && S.projects.length > 1) ? `<div class="card"><h2>Porovnanie projektov</h2>${projTable(cur, accs, dCur, growthOf)}</div>` : ''}
  ${accs.length || cur.length ? `<div class="card"><div class="row"><h2 style="margin:0;flex:1">Kanály a účty</h2><span class="small dim">kliknutím na stĺpec zoradíš</span></div>${accTable2(cur, accs, dCur, growthOf)}</div>` : ''}
  ${cur.length ? `
  <div class="g2 dg">
    <div class="card"><h2>Podľa siete</h2>${barList(groupBy(cur, x => x.pl).map(g => ({ ...g, label: PL[g.k] || g.k, color: NET_C[g.k], icon: g.k, click: `dSet('pl','${g.k}')` })), f.m, 10, f.pl)}</div>
    <div class="card"><h2>Podľa krajiny</h2>${barList(groupBy(cur, x => x.c).map(g => ({ ...g, label: cName(g.k), click: g.k ? `dSet('c','${g.k}')` : '' })), f.m, 12, f.c)}</div>
  </div>
  <div class="card"><h2>Najlepšie videá</h2>${topTable(cur, f.m)}</div>
  ${worstTable(cur, f.m)}
  <div class="g2 dg">
    <div class="card"><h2>Kedy to funguje najlepšie</h2><p class="small dim" style="margin-top:-6px">${f.m === 'n' ? 'Počet príspevkov' : f.m === 'er' ? 'Zapojenie' : 'Priemer na jeden príspevok'} podľa dňa a hodiny zverejnenia (slovenský čas).</p>${heat(cur, f.m)}</div>
    <div class="card"><h2>Z čoho sú reakcie</h2>${react(A)}
      <h2 style="margin-top:22px">Podľa jazyka</h2>${barList(groupBy(cur, x => x.l).map(g => ({ ...g, label: lName(g.k), click: g.k ? `dSet('l','${g.k}')` : '' })), f.m, 6, f.l)}</div>
  </div>` : ''}
  ${gapsCard(accs, DD)}
  <p class="small dim" style="margin-top:14px">Iba skutočné čísla zo sietí, nič vymyslené${DD.last ? ' · posledné stiahnutie ' + esc(DD.last.slice(8, 10) + '.' + DD.last.slice(5, 7) + '. ' + DD.last.slice(11, 16)) : ''} · Zapojenie = (lajky + komentáre + zdieľania) ÷ zobrazenia. LinkedIn ráta zobrazenia ako impresie, Instagram bez zobrazení ako dosah.</p>`;
  if (cur.length) lineChart($('#dLine'), cur, prev, f, cut, cut0);
  if (dCur.length) ytChart($('#dYt'), daily, f, cut, cut0);
}

const YM = [['v', 'Pozretia'], ['w', 'Hodiny sledovania'], ['sn', 'Noví odberatelia'], ['lk', 'Lajky']];
S.dash.ym = S.dash.ym || 'v';
function dScope(v) { S.dash.all = v ? 1 : 0; S.dash.p = ''; pDash($('#main')); }
async function dRefresh(b) {
  b.disabled = true;
  const r = await api('/api/dash/refresh', { method: 'POST', body: {} });
  toast((r.started ? 'Sťahujem čísla zo sietí, o pár minút sa doplnia samé.' : 'Čísla sa už práve sťahujú.') + (r.yt_limit ? ' YouTube má dnes vyčerpaný denný limit, preto sa pozretia jednotlivých YouTube videí doplnia zajtra (odberatelia a čas sledovania idú normálne).' : ''));
  DD.busy = true; b.innerHTML = I('refresh', 's') + 'Sťahujem…';
  let n = 0; const t = setInterval(async () => {
    n++; if (!location.hash.includes('dashboard') || n > 20) return clearInterval(t);
    const d = await api(`/api/dash?days=${S.dash.days * 2}&pdays=${S.dash.days}`);
    if (!d.busy || n % 4 === 0) { d.key = DD.key; DD = d; pDash($('#main')); }
    if (!d.busy) clearInterval(t);
  }, 15000);
}

function prodCard(proj, days) {
  const P = DD.prod || {}, keys = proj ? [String(proj)] : Object.keys(P);
  const s = k => keys.reduce((t, p) => t + ((P[p] || {})[k] || 0), 0);
  const nx = keys.map(p => (P[p] || {}).next).filter(Boolean).sort()[0];
  const per = DAYS.find(d => d[0] === days)?.[1] || days + ' dní';
  const t = (ic, n, label, cls = '', hint = '') => `<div class="dp ${cls}" ${hint ? `data-tip="${esc(hint)}"` : ''}>${I(ic, 's')}<b>${nf(n)}</b><span>${label}</span></div>`;
  return `<div class="card"><div class="row"><h2 style="margin:0;flex:1">Výroba videí</h2><span class="small dim">${nx ? 'najbližšie zverejnenie ' + nx.slice(8, 10) + '.' + nx.slice(5, 7) + '. ' + nx.slice(11, 16) : ''}</span></div>
    <div class="dprod">${t('bulb', s('ideas'), 'nápadov v zásobníku')}${t('pencil', s('scripts'), 'scenárov za ' + per)}${t('film', s('made'), 'vyrobených videí za ' + per, '', 'Každá jazyková verzia sa ráta zvlášť.')}
    ${t('eye', s('review'), 'čaká na schválenie', s('review') ? 'warn' : '')}${t('calendar', s('queued'), 'naplánovaných')}${t('send', s('done'), 'zverejnených za ' + per, 'ok')}
    ${s('failed') ? t('alert', s('failed'), 's chybou', 'bad', 'Pozri Publikovanie.') : ''}</div></div>`;
}

function yppCard(yt, f) {
  if (!yt.length || (f.pl && f.pl !== 'youtube')) return '';
  const dl = DD.ypp_deadline || '2027-01-31', left = Math.max(0, Math.ceil((new Date(dl + 'T23:59') - Date.now()) / 864e5));
  const rows = yt.map(a => {
    const y = a.ypp || {}, subs = a.f, h = y.long_hours, sv = y.shorts_views_90;
    const ps = subs != null ? Math.min(1, subs / 1000) : 0, pw = Math.max(h != null ? h / 4000 : 0, sv != null ? sv / 1e7 : 0);
    const ok = subs >= 1000 && (h >= 4000 || sv >= 1e7);
    return { a, subs, h, sv, ok, score: ps * 0.5 + Math.min(1, pw) * 0.5, has: y.at };
  }).sort((x, y) => y.ok - x.ok || y.score - x.score || (y.subs || 0) - (x.subs || 0));
  const many = rows.length > 8 && !S.dash.allYpp, list = many ? rows.slice(0, 8) : rows;
  const bar = (v, max, label, val) => v == null ? `<div class="yb"><span class="dim">${label}</span><div class="dt"><i style="width:0"></i></div><span class="dim">nezmerané</span></div>`
    : `<div class="yb" data-tip="${esc(`${label}: ${val} z ${cf(max)}`)}"><span class="dim">${label}</span><div class="dt"><i style="width:${Math.max(1.5, Math.min(100, v / max * 100))}%;background:${v >= max ? 'var(--ok)' : 'var(--acc)'}"></i></div><span>${val}</span></div>`;
  const okN = rows.filter(r => r.ok).length;
  return `<div class="card"><div class="row" style="flex-wrap:wrap;gap:8px"><h2 style="margin:0;flex:1">Cesta k zárobku na YouTube</h2>
      <span class="chip ${okN ? 'ok' : ''}">${okN} z ${rows.length} kanálov spĺňa</span><span class="chip acc">do ${dl.slice(8, 10)}.${dl.slice(5, 7)}.${dl.slice(0, 4)} ostáva ${left} dní</span></div>
    <p class="small dim" style="margin:6px 0 12px">Reklamy zapne YouTube pri 1 000 odberateľoch a k tomu 4 000 hodinách sledovania dlhých videí za rok alebo 10 mil. pozretí Shorts za 90 dní.</p>
    <div class="ypp">${list.map(r => {
      const need = r.subs != null && r.subs < 1000 && left ? Math.ceil((1000 - r.subs) / left) : 0;
      return `<div class="yr"><div class="yn">${I('youtube', 's')}<span>${esc(r.a.name)}</span>${r.ok ? '<span class="chip ok">spĺňa, môžeš požiadať</span>' : need ? `<span class="small dim">treba +${nf(need)} odberateľov denne</span>` : ''}</div>
        ${bar(r.subs, 1000, 'Odberatelia', r.subs == null ? '' : nf(r.subs))}${bar(r.h, 4000, 'Hodiny (dlhé, 12 mes.)', r.h == null ? '' : nf(r.h))}${bar(r.sv, 1e7, 'Shorts pozretia (90 dní)', r.sv == null ? '' : cf(r.sv))}</div>`;
    }).join('')}</div>
    ${many ? `<button class="btn ghost sm" style="margin-top:10px" onclick="S.dash.allYpp=1;pDash($('#main'))">${I('right', 's')}Ukázať všetkých ${rows.length} kanálov</button>` : ''}</div>`;
}

function projTable(cur, accs, dCur, growthOf) {
  const g = S.projects.map(p => {
    const rs = cur.filter(x => x.p === p.id), ac = accs.filter(a => a.p === p.id), ids = new Set(ac.map(a => a.id)), a = agg(rs);
    return { p, ...a, f: ac.reduce((s, x) => s + (x.f || 0), 0), fg: ac.reduce((s, x) => s + growthOf(x), 0), w: dCur.filter(x => ids.has(x.a)).reduce((s, x) => s + x.w, 0) / 60, nacc: ac.length };
  }).filter(x => x.n || x.nacc).sort((a, b) => b.v - a.v || b.f - a.f);
  return `<table class="dtab"><tr><th>Projekt</th><th>Účty</th><th>Sledovatelia</th><th>Rast</th><th>Videá</th><th>Pozretia</th><th>Lajky</th><th>Komentáre</th><th>Hodiny</th></tr>
    ${g.map(x => `<tr class="cl" onclick="S.dash.p='${x.p.id}';pDash($('#main'))"><td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${x.p.color};margin-right:6px"></span>${esc(x.p.name)}</td>
      <td>${x.nacc}</td><td>${nf(x.f)}</td><td class="${x.fg > 0 ? 'up' : ''}">${x.fg > 0 ? '+' : ''}${nf(x.fg)}</td><td>${x.n}</td><td>${nf(x.v)}</td><td>${nf(x.lk)}</td><td>${nf(x.cm)}</td><td>${x.w ? nf(x.w) : '–'}</td></tr>`).join('')}</table>`;
}

const ACOLS = [['name', 'Účet'], ['pl', 'Sieť'], ['c', 'Krajina'], ['f', 'Sledovatelia'], ['fg', 'Rast'], ['n', 'Videá'], ['v', 'Pozretia'], ['lk', 'Lajky'], ['cm', 'Komentáre'], ['avg', 'Na video'], ['w', 'Hodiny']];
function accTable2(cur, accs, dCur, growthOf) {
  const byA = {}; for (const x of cur) (byA[x.aid] = byA[x.aid] || []).push(x);
  const list = accs.map(a => { const g = agg(byA[a.id] || []); return { ...a, ...g, name: a.name, f: a.f, fg: growthOf(a), avg: g.n ? g.v / g.n : 0, w: dCur.filter(x => x.a === a.id).reduce((s, x) => s + x.w, 0) / 60 }; });
  const sk = S.dash.as || 'v', dir = S.dash.ad || -1;
  list.sort((a, b) => { const x = a[sk] ?? -1, y = b[sk] ?? -1; return (typeof x === 'string' ? x.localeCompare(y, 'sk') : x - y) * dir || (b.f || 0) - (a.f || 0); });
  const more = list.length > 15 && !S.dash.allAcc; const show = more ? list.slice(0, 15) : list;
  return `<table class="dtab"><tr>${ACOLS.map(([k, n]) => `<th class="cl" onclick="dSort('${k}')">${n}${sk === k ? (dir < 0 ? ' ↓' : ' ↑') : ''}</th>`).join('')}</tr>
    ${show.map(a => `<tr><td>${esc(a.name)}${a.err ? ` <span class="chip bad" data-tip="${esc(a.err)}">${I('alert', 's')}</span>` : ''}</td><td>${plat(a.pl, false)}</td><td>${esc(cName(a.c))}</td>
      <td>${a.f == null ? '<span class="dim">–</span>' : nf(a.f)}</td><td class="${a.fg > 0 ? 'up' : a.fg < 0 ? 'down' : 'dim'}">${a.f == null ? '' : (a.fg > 0 ? '+' : '') + nf(a.fg)}</td>
      <td>${a.n}</td><td>${nf(a.v)}</td><td>${nf(a.lk)}</td><td>${nf(a.cm)}</td><td class="dim">${a.n ? cf(a.avg) : '–'}</td><td>${a.pl === 'youtube' && a.w ? nf(a.w) : '<span class="dim">–</span>'}</td></tr>`).join('')}</table>
    ${more ? `<button class="btn ghost sm" style="margin-top:10px" onclick="S.dash.allAcc=1;pDash($('#main'))">${I('right', 's')}Ukázať všetkých ${list.length} účtov</button>` : ''}`;
}
function dSort(k) { const f = S.dash; if (f.as === k) f.ad = -(f.ad || -1); else { f.as = k; f.ad = ['name', 'pl', 'c'].includes(k) ? 1 : -1; } pDash($('#main')); }

function worstTable(rows, m) {
  const old = rows.filter(x => Date.now() - x.ts > 2 * 864e5);
  if (old.length < 6) return '';
  const k = m === 'n' ? 'v' : m, list = [...old].sort((a, b) => mval(k, a) - mval(k, b) || a.v - b.v).slice(0, 5);
  return `<div class="card"><h2>Najslabšie videá</h2><p class="small dim" style="margin-top:-6px">Len videá staršie ako 2 dni, aby mali čas sa rozbehnúť.</p>${vidTable(list)}</div>`;
}

function gapsCard(accs, D) {
  const out = [];
  for (const o of D.analytics_off || []) out.push(`YouTube Analytics nie je zapnuté v Google projekte${o.project ? ' <b>' + esc(o.project) + '</b>' : ''} (${o.channels} kanálov), preto chýba čas sledovania a denné čísla. <a href="https://console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com${o.project ? '?project=' + encodeURIComponent(o.project) : ''}" target="_blank">Zapnúť jedným klikom ${I('ext', 's')}</a>`);
  const errs = accs.filter(a => a.err || a.aerr);
  if (errs.length) out.push(`${errs.length} ${errs.length === 1 ? 'účet má' : errs.length < 5 ? 'účty majú' : 'účtov má'} problém so sťahovaním čísel: ${errs.slice(0, 6).map(a => `${esc(a.name)} (${esc(a.err || a.aerr)})`).join(', ')}${errs.length > 6 ? ' …' : ''}`);
  const tt = accs.filter(a => a.tt_draft).length;
  if (tt) out.push(`${tt} TikTok ${tt === 1 ? 'účet je' : 'účtov je'} pripojených bez TikTok Business, tie čísla nedávajú (videá idú ako koncepty).`);
  if (accs.some(a => a.li_personal)) out.push('Osobný LinkedIn profil čísla nedáva, merať sa dá len firemná stránka.');
  if (accs.some(a => a.pl !== 'youtube' && a.f != null)) out.push('Rast sledovateľov na Facebooku, Instagrame, TikToku a LinkedIne appka meria sama od dňa, keď ich začala sťahovať (siete históriu nedávajú).');
  if (accs.some(a => a.pl === 'youtube')) out.push('YouTube zaokrúhľuje počet odberateľov nad 1 000 (napr. 1 230 → 1,23 tis.) a čísla z Analytics dopĺňa o 2 až 3 dni neskôr.');
  return out.length ? `<div class="card"><h2>Čo sa zatiaľ nedá zmerať</h2><ul class="dgaps">${out.map(x => `<li>${x}</li>`).join('')}</ul></div>` : '';
}

// ---------- YouTube deň po dni (stĺpce za deň, predchádzajúce obdobie prerušovanou čiarou) ----------
function ytChart(el, daily, f, cut, cut0) {
  const W = Math.max(320, el.clientWidth), H = 220, L = 54, R = 12, T = 12, B = 28, day = 864e5;
  const nb = f.days <= 120 ? f.days : Math.ceil(f.days / 7), step = f.days <= 120 ? day : 7 * day;
  const k = f.ym, val = x => k === 'sn' ? x.sg - x.sl : k === 'w' ? x.w / 60 : x[k];
  const by = (start) => { const b = new Array(nb).fill(0); for (const x of daily) { const t = new Date(x.d + 'T12:00').getTime(), i = Math.floor((t - start) / step); if (i >= 0 && i < nb) b[i] += val(x); } return b; };
  const c = by(cut), p = by(cut0);
  const top = Math.max(...c, ...p, 1e-9), nice = (() => { const e = Math.pow(10, Math.floor(Math.log10(top))), r = top / e; return (r <= 1 ? 1 : r <= 2 ? 2 : r <= 5 ? 5 : 10) * e; })();
  const bw = (W - L - R) / nb, X = i => L + i * bw, Y = v => T + (H - T - B) * (1 - Math.max(0, v) / nice);
  const fmt = v => k === 'w' ? nf(v) + ' h' : cf(v);
  const dlab = i => { const d = new Date(cut + i * step); return `${d.getDate()}.${d.getMonth() + 1}.`; };
  const every = Math.max(1, Math.ceil(nb / Math.floor((W - L) / 70)));
  const grid = [0, .5, 1].map(t => `<line x1="${L}" x2="${W - R}" y1="${Y(nice * t)}" y2="${Y(nice * t)}" stroke="#262626"/><text x="${L - 8}" y="${Y(nice * t) + 4}" text-anchor="end">${fmt(nice * t)}</text>`).join('');
  const bars = c.map((v, i) => `<rect x="${(X(i) + bw * .15).toFixed(1)}" y="${Y(v).toFixed(1)}" width="${Math.max(1, bw * .7).toFixed(1)}" height="${Math.max(0, Y(0) - Y(v)).toFixed(1)}" rx="2" fill="#FF6B00" data-tip="${esc(`<b>${dlab(i)}</b><br>${fmt(v)}<br><span class='dim'>predtým: ${fmt(p[i])}</span>`)}"/>`).join('');
  const pl = p.map((v, i) => `${i ? 'L' : 'M'}${(X(i) + bw / 2).toFixed(1)},${Y(v).toFixed(1)}`).join('');
  const xl = c.map((_, i) => i % every === 0 ? `<text x="${X(i) + bw / 2}" y="${H - 8}" text-anchor="middle">${dlab(i)}</text>` : '').join('');
  el.innerHTML = `<svg width="${W}" height="${H}" class="dsvg">${grid}${xl}${bars}<path d="${pl}" fill="none" stroke="#6b6b6b" stroke-width="1.5" stroke-dasharray="4 4"/></svg>`;
}

function dSet(k, v) {
  const f = S.dash;
  if (k === 'days') v = +v;
  if (k !== 'm' && k !== 'ym' && k !== 'days' && String(f[k]) === String(v)) v = ''; // druhý klik filter zruší
  f[k] = v; pDash($('#main'));
}
function dReset() { Object.assign(S.dash, { pl: '', c: '', l: '', p: '' }); pDash($('#main')); }

const legend = items => `<div class="dleg">${items.map(([c, n, dash]) => `<span><i style="${dash ? `border-top:2px dashed ${c};background:none;height:0` : `background:${c}`}"></i>${n}</span>`).join('')}</div>`;

function barList(groups, m, max, active) {
  groups.forEach(g => g.val = mval(m, g));
  groups.sort((a, b) => b.val - a.val);
  let list = groups;
  if (groups.length > max) {
    const rest = groups.slice(max - 1), o = agg(rest.flatMap(g => g.rows));
    list = [...groups.slice(0, max - 1), { ...o, label: `Ďalšie (${rest.length})`, val: mval(m, o), other: 1 }];
  }
  const top = Math.max(...list.map(g => g.val), 1e-9), tot = m === 'er' ? 0 : list.reduce((s, g) => s + g.val, 0);
  return `<div class="dbars">${list.map(g => `<div class="dbar ${g.click ? 'cl' : ''} ${active && String(active) === String(g.k) ? 'on' : ''}" ${g.click ? `onclick="${g.click}"` : ''}
    data-tip="${esc(`<b>${esc(g.label)}</b><br>Zobrazenia ${nf(g.v)}<br>Reakcie ${nf(g.r)}<br>Zapojenie ${g.v ? pf(g.r / g.v) : '–'}<br>Príspevky ${g.n}`)}">
    <div class="dl">${g.icon ? I(g.icon, 's') : ''}<span>${esc(g.label)}</span></div>
    <div class="dt"><i style="width:${Math.max(1.5, g.val / top * 100)}%;background:${g.other ? '#555' : g.color || 'var(--acc)'}"></i></div>
    <div class="dv">${mfmt(m, g.val)}${tot ? `<span class="dim"> ${Math.round(g.val / tot * 100)} %</span>` : ''}</div></div>`).join('')}</div>`;
}

function react(A) {
  const parts = [['Páči sa mi', A.lk], ['Komentáre', A.cm], ['Zdieľania', A.sh]], t = A.r || 1;
  return `<div class="dbars">${parts.map(([n, v]) => `<div class="dbar" data-tip="${esc(`<b>${n}</b><br>${nf(v)} (${Math.round(v / t * 100)} % reakcií)`)}"><div class="dl"><span>${n}</span></div>
    <div class="dt"><i style="width:${Math.max(1.5, v / t * 100)}%;background:var(--acc)"></i></div><div class="dv">${cf(v)}<span class="dim"> ${Math.round(v / t * 100)} %</span></div></div>`).join('')}</div>`;
}

function heat(rows, m) {
  const cell = {};
  for (const x of rows) { const d = new Date(x.ts), k = ((d.getDay() + 6) % 7) + '-' + d.getHours(); (cell[k] = cell[k] || []).push(x); }
  const val = rs => { if (!rs) return null; const a = agg(rs); return m === 'n' ? a.n : m === 'er' ? (a.v ? a.r / a.v : 0) : a[m] / a.n; };
  const hours = []; for (let h = 6; h < 24; h++) hours.push(h);
  const vals = Object.values(cell).map(val), top = Math.max(...vals, 1e-9);
  const lab = m === 'n' ? 'príspevkov' : m === 'er' ? 'zapojenie' : (m === 'v' ? 'zobrazení' : 'reakcií') + ' na príspevok';
  return `<div class="dheat"><div></div>${hours.map(h => `<div class="hh">${h % 3 === 0 ? h : ''}</div>`).join('')}
    ${WD.map((w, wi) => `<div class="hw">${w}</div>${hours.map(h => { const rs = cell[wi + '-' + h], v = val(rs);
      return v === null ? `<div class="hc"></div>` : `<div class="hc" style="background:color-mix(in srgb, var(--acc) ${Math.round(15 + 85 * v / top)}%, #1a1a1a)" data-tip="${esc(`<b>${w} ${h}:00</b><br>${m === 'er' ? pf(v) : nf(v)} ${lab}<br>${rs.length} príspevkov`)}"></div>`; }).join('')}`).join('')}</div>
    <div class="row small dim" style="margin-top:8px;gap:6px">menej<span class="hscale"></span>viac</div>`;
}

function topTable(rows, m) {
  const k = m === 'n' ? 'v' : m, list = [...rows].sort((a, b) => mval(k, b) - mval(k, a) || b.v - a.v).slice(0, 10);
  return vidTable(list);
}

function vidTable(list) {
  const yt = list.some(x => x.wm || x.ap);
  return `<table class="dtab"><tr><th>Video</th><th>Sieť</th><th>Účet</th><th>Dátum</th><th>Pozretia</th><th>Lajky</th><th>Komentáre</th>${yt ? '<th>Hodiny</th><th>Pozreté z videa</th>' : ''}<th>Zapojenie</th></tr>
    ${list.map(x => `<tr><td>${x.u ? `<a href="${esc(x.u)}" target="_blank">${esc(x.t || 'Bez názvu')}</a>` : esc(x.t || 'Bez názvu')}</td><td>${plat(x.pl, false)}</td><td class="dim">${esc(x.acc)}</td>
      <td class="dim">${x.d.slice(8, 10)}.${x.d.slice(5, 7)}.</td><td>${nf(x.v)}</td><td>${nf(x.lk)}</td><td>${nf(x.cm)}</td>
      ${yt ? `<td>${x.wm ? nf(x.wm / 60) : '–'}</td><td>${x.ap ? Math.round(x.ap) + ' %' : '–'}</td>` : ''}<td>${x.v ? pf(x.r / x.v) : '–'}</td></tr>`).join('')}</table>`;
}

// ---------- čiarový graf (toto obdobie + predchádzajúce prerušovane) ----------
function lineChart(el, cur, prev, f, cut, cut0) {
  const W = Math.max(320, el.clientWidth), H = 240, L = 54, R = 12, T = 12, B = 28;
  const day = 864e5, step = f.days <= 31 ? day : f.days <= 120 ? 7 * day : 30.4 * day;
  const nb = Math.ceil(f.days * day / step);
  const bucket = (rows, start) => { const b = Array.from({ length: nb }, () => []); for (const x of rows) { const i = Math.min(nb - 1, Math.floor((x.ts - start) / step)); if (i >= 0) b[i].push(x); } return b.map(rs => { const a = agg(rs); return { ...a, val: mval(f.m, a) }; }); };
  const c = bucket(cur, cut), p = bucket(prev, cut0);
  const top = Math.max(...c.map(x => x.val), ...p.map(x => x.val), 1e-9);
  const nice = (() => { const e = Math.pow(10, Math.floor(Math.log10(top))), r = top / e; return (r <= 1 ? 1 : r <= 2 ? 2 : r <= 5 ? 5 : 10) * e; })();
  const X = i => L + (nb === 1 ? (W - L - R) / 2 : i * (W - L - R) / (nb - 1)), Y = v => T + (H - T - B) * (1 - v / nice);
  const path = arr => arr.map((x, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(x.val).toFixed(1)}`).join('');
  const dlab = i => { const d = new Date(cut + i * step); return step >= 30 * day ? ['jan', 'feb', 'mar', 'apr', 'máj', 'jún', 'júl', 'aug', 'sep', 'okt', 'nov', 'dec'][d.getMonth()] : `${d.getDate()}.${d.getMonth() + 1}.`; };
  const every = Math.max(1, Math.ceil(nb / Math.floor((W - L) / 70)));
  const grid = [0, .25, .5, .75, 1].map(t => `<line x1="${L}" x2="${W - R}" y1="${Y(nice * t)}" y2="${Y(nice * t)}" stroke="#262626"/><text x="${L - 8}" y="${Y(nice * t) + 4}" text-anchor="end">${mfmt(f.m, nice * t)}</text>`).join('');
  const xl = c.map((_, i) => i % every === 0 ? `<text x="${X(i)}" y="${H - 8}" text-anchor="middle">${dlab(i)}</text>` : '').join('');
  el.innerHTML = `<svg width="${W}" height="${H}" class="dsvg">
    <defs><linearGradient id="dgr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF6B00" stop-opacity=".28"/><stop offset="1" stop-color="#FF6B00" stop-opacity="0"/></linearGradient></defs>
    ${grid}${xl}
    <path d="${path(p)}" fill="none" stroke="#6b6b6b" stroke-width="2" stroke-dasharray="5 5"/>
    <path d="${path(c)}L${X(nb - 1)},${Y(0)}L${X(0)},${Y(0)}Z" fill="url(#dgr)"/>
    <path d="${path(c)}" fill="none" stroke="#FF6B00" stroke-width="2" stroke-linejoin="round"/>
    <line id="dX" y1="${T}" y2="${H - B}" stroke="#555" style="display:none"/><circle id="dO" r="5" fill="#FF6B00" stroke="#121212" stroke-width="2" style="display:none"/>
    <rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="transparent" id="dHit"/></svg>`;
  const hit = el.querySelector('#dHit'), xL = el.querySelector('#dX'), o = el.querySelector('#dO');
  hit.onmousemove = e => {
    const bx = e.clientX - el.querySelector('svg').getBoundingClientRect().left;
    const i = Math.max(0, Math.min(nb - 1, Math.round((bx - L) / ((W - L - R) / Math.max(1, nb - 1)))));
    xL.setAttribute('x1', X(i)); xL.setAttribute('x2', X(i)); xL.style.display = ''; o.setAttribute('cx', X(i)); o.setAttribute('cy', Y(c[i].val)); o.style.display = '';
    const per = step === day ? dlab(i) : `od ${dlab(i)}`;
    dTip(e, `<b>${per}</b><br>${DM[f.m][0]}: ${mfmt(f.m, c[i].val)}<br><span class="dim">predtým: ${mfmt(f.m, p[i].val)}</span><br><span class="dim">${c[i].n} príspevkov</span>`);
  };
  hit.onmouseleave = e => { xL.style.display = 'none'; o.style.display = 'none'; dTip(e, ''); };
}
let _dRs; addEventListener('resize', () => { clearTimeout(_dRs); _dRs = setTimeout(() => { if ($('#dLine')) pDash($('#main')); }, 250); });

// ---------- Prehľad (hlavná stránka): poradie projektov ----------
S.hp = S.hp || { days: 7, k: 'v' };
const HPK = [['v', 'Pozretia'], ['fg', 'Rast odberateľov'], ['lk', 'Lajky'], ['done', 'Zverejnené videá']];
async function homeProjects(el) {
  if (!el) return;
  const f = S.hp;
  let D;
  try { D = await api(`/api/dash?days=${f.days * 2}&pdays=${f.days}`); } catch (e) { el.innerHTML = `<h2>${I('chart')}Ako sa darí projektom</h2>${empty('chart', 'Čísla sa nepodarilo načítať.')}`; return; }
  if (!el.isConnected) return;
  const day = 864e5, now = Date.now(), cut = now - f.days * day, cut0 = now - 2 * f.days * day;
  const ds = t => new Date(t).toISOString().slice(0, 10), cutD = ds(cut), cut0D = ds(cut0);
  const rows = D.rows.map(x => ({ ...x, ts: new Date(x.d.replace(' ', 'T')).getTime() }));
  const list = S.projects.map(p => {
    const cur = agg(rows.filter(x => x.p === p.id && x.ts >= cut)), prev = agg(rows.filter(x => x.p === p.id && x.ts >= cut0 && x.ts < cut));
    const ac = (D.accounts || []).filter(a => a.p === p.id), ids = new Set(ac.map(a => a.id));
    const dl = (D.daily || []).filter(x => ids.has(x.a)), ytIds = new Set(dl.filter(x => x.d >= cutD).map(x => x.a));
    const fg = ac.reduce((s, a) => s + (a.pl === 'youtube' && ytIds.has(a.id) ? dl.filter(x => x.a === a.id && x.d >= cutD).reduce((t, x) => t + x.sg - x.sl, 0) : (a.f != null && a.f0 != null ? a.f - a.f0 : 0)), 0);
    const fgp = dl.filter(x => x.d >= cut0D && x.d < cutD).reduce((t, x) => t + x.sg - x.sl, 0);
    const fl = ac.filter(a => a.f != null);
    return { p, v: cur.v, vp: prev.v, lk: cur.lk, lkp: prev.lk, cm: cur.cm, n: cur.n, fg, fgp, f: fl.reduce((s, a) => s + a.f, 0), hasF: fl.length,
      w: dl.filter(x => x.d >= cutD).reduce((t, x) => t + x.w, 0) / 60, done: ((D.prod || {})[p.id] || {}).done || 0, nacc: ac.length };
  });
  const k = f.k; list.sort((a, b) => b[k] - a[k] || b.v - a.v || b.f - a.f);
  const top = Math.max(...list.map(x => x[k]), 1e-9), any = list.some(x => x.v || x.f || x.done);
  const tr = (a, b) => !b ? (a ? '<span class="dd up">nové</span>' : '<span class="dim">–</span>') : `<span class="dd ${a >= b ? 'up' : 'down'}">${a >= b ? '▲' : '▼'} ${Math.round(Math.abs(a - b) / b * 100)} %</span>`;
  const fmtK = (x) => k === 'fg' ? (x.fg > 0 ? '+' : '') + nf(x.fg) : k === 'done' ? nf(x.done) : cf(x[k]);
  el.innerHTML = `<div class="row" style="flex-wrap:wrap;gap:10px;margin-bottom:10px"><h2 style="margin:0;flex:1">${I('chart')}Ako sa darí projektom</h2>
    <div class="seg">${HPK.map(([kk, n]) => `<button class="${k === kk ? 'on' : ''}" onclick="S.hp.k='${kk}';homeProjects($('#hProj'))">${n}</button>`).join('')}</div>
    <div class="seg">${[[7, '7 dní'], [30, '30 dní'], [90, '3 mesiace']].map(([d, n]) => `<button class="${f.days === d ? 'on' : ''}" onclick="S.hp.days=${d};homeProjects($('#hProj'))">${n}</button>`).join('')}</div>
    <span class="small dim">${D.last ? 'stiahnuté ' + esc(D.last.slice(8, 10) + '.' + D.last.slice(5, 7) + '. ' + D.last.slice(11, 16)) : 'zatiaľ nestiahnuté'}</span>
    <button class="btn sec sm" onclick="hRefresh(this)" ${D.busy || S.hp.busy ? 'disabled' : ''}>${I('refresh', 's')}${D.busy || S.hp.busy ? 'Sťahujem…' : 'Stiahnuť čísla teraz'}</button></div>
  ${!any ? empty('chart', 'Zatiaľ žiadne čísla. Objavia sa samé po prvých zverejnených videách (sťahujú sa každých 6 hodín).') : `
  <table class="dtab hrank"><tr><th>#</th><th>Projekt</th><th></th><th>Pozretia</th><th>oproti predtým</th><th>Lajky</th><th>Komentáre</th><th>Odberatelia</th><th>Rast</th><th>Hodiny</th><th>Zverejnené</th></tr>
  ${list.map((x, i) => `<tr class="cl" onclick="S.dash.all=0;location.hash='#/p/${x.p.id}/dashboard'">
    <td class="${i === 0 && x[k] > 0 ? 'lead' : 'dim'}">${i + 1}</td>
    <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${x.p.color};margin-right:6px"></span>${esc(x.p.name)}${i === 0 && x[k] > 0 ? ' <span class="chip acc">vedie</span>' : ''}${i === list.length - 1 && list.length > 2 && x[k] < top * 0.2 ? ' <span class="chip">zaostáva</span>' : ''}</td>
    <td style="width:22%"><div class="hbar"><i style="width:${Math.max(1, x[k] / top * 100)}%;background:${x.p.color || 'var(--acc)'}"></i></div><span class="small dim">${fmtK(x)}</span></td>
    <td>${nf(x.v)}</td><td>${tr(x.v, x.vp)}</td><td>${nf(x.lk)}</td><td>${nf(x.cm)}</td>
    <td>${x.hasF ? nf(x.f) : '<span class="dim">–</span>'}</td><td class="${x.fg > 0 ? 'up' : x.fg < 0 ? 'down' : 'dim'}">${x.hasF ? (x.fg > 0 ? '+' : '') + nf(x.fg) : ''}</td>
    <td>${x.w ? nf(x.w) : '<span class="dim">–</span>'}</td><td>${nf(x.done)}</td></tr>`).join('')}</table>
  <p class="small dim" style="margin:8px 0 0">Klikni na projekt pre celý dashboard. Len skutočné čísla zo sietí, sťahujú sa samé každých 6 hodín.</p>`}`;
  if (D.busy && !S.hp.t) { S.hp.t = setTimeout(() => { S.hp.t = 0; homeProjects($('#hProj')); }, 15000); }
}
async function hRefresh(b) {
  b.disabled = true;
  const r = await api('/api/dash/refresh', { method: 'POST', body: {} });
  toast((r.started ? 'Sťahujem čísla zo sietí, o pár minút sa doplnia samé.' : 'Čísla sa už práve sťahujú.') + (r.yt_limit ? ' YouTube má dnes vyčerpaný denný limit, preto sa pozretia jednotlivých YouTube videí doplnia zajtra (odberatelia a čas sledovania idú normálne).' : ''));
  S.hp.busy = 1; b.innerHTML = I('refresh', 's') + 'Sťahujem…';
  setTimeout(() => { S.hp.busy = 0; homeProjects($('#hProj')); }, 15000);
}
