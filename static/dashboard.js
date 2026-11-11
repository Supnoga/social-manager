// ================= DASHBOARD: výsledky s filtrami a grafmi (bez AI, počíta prehliadač) =================
Object.assign(IC, {
  dash: '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  eye2: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  heart: '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7z"/>',
  pct: '<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
});

// farby sietí: pevné poradie (overená farebná paleta pre tmavé pozadie), farba patrí sieti, nie poradiu
const NET_C = { youtube: '#3987e5', tiktok: '#d95926', instagram: '#199e70', facebook: '#c98500', linkedin: '#d55181' };
const DM = { v: ['Zobrazenia', 'eye2'], r: ['Reakcie', 'heart'], er: ['Zapojenie', 'pct'], n: ['Príspevky', 'film'] };
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
  const key = `${want}`;
  if (!DD || DD.key !== key) {
    m.innerHTML = `<div class="top"><div>${pTitle('Dashboard')}</div></div><div class="card">${empty('dash', 'Načítavam čísla…')}</div>`;
    DD = await api(`/api/dash?days=${want}`); DD.key = key;
  }
  const now = Date.now(), dayMs = 864e5, cut = now - f.days * dayMs, cut0 = now - 2 * f.days * dayMs;
  const ts = x => new Date(x.d.replace(' ', 'T')).getTime();
  const proj = pid || +f.p || 0;
  const match = (x, skip) => (!proj || x.p === proj) && (skip === 'pl' || !f.pl || x.pl === f.pl) && (skip === 'c' || !f.c || x.c === f.c) && (skip === 'l' || !f.l || x.l === f.l);
  const all = DD.rows.map(x => ({ ...x, r: x.lk + x.cm + x.sh, ts: ts(x) }));
  const cur = all.filter(x => x.ts >= cut && match(x)), prev = all.filter(x => x.ts >= cut0 && x.ts < cut && match(x));
  const A = agg(cur), P = agg(prev);
  // možnosti filtrov (len to, čo v dátach je)
  const scope = all.filter(x => x.ts >= cut && (!proj || x.p === proj));
  const opts = k => [...new Set(scope.map(x => x[k]))].filter(Boolean);
  const nets = PLATS.filter(p => opts('pl').includes(p));
  const ctrs = opts('c').sort((a, b) => cName(a).localeCompare(cName(b), 'sk'));
  const lngs = opts('l').sort((a, b) => lName(a).localeCompare(lName(b), 'sk'));
  const sel = (k, label, list, nameFn) => `<label class="dsel"><span>${label}</span><select onchange="dSet('${k}',this.value)"><option value="">Všetky</option>${list.map(v => `<option value="${esc(String(v))}" ${String(f[k]) === String(v) ? 'selected' : ''}>${esc(nameFn(v))}</option>`).join('')}</select></label>`;
  const anyF = f.pl || f.c || f.l || (!pid && f.p);

  const delta = (a, b) => {
    if (!b) return '<span class="dd dim">bez porovnania</span>';
    const d = (a - b) / b, up = d >= 0;
    return `<span class="dd ${up ? 'up' : 'down'}">${up ? '▲' : '▼'} ${pf(Math.abs(d))}</span><span class="dim small"> oproti predtým</span>`;
  };
  const kpi = (k) => `<div class="card dk ${f.m === k ? 'on' : ''}" onclick="dSet('m','${k}')" title="Ukázať v grafoch">
    <div class="row" style="gap:8px">${I(DM[k][1], 's')}<span class="muted small">${DM[k][0]}</span></div>
    <b>${mfmt(k, mval(k, A))}</b><div class="small">${delta(mval(k, A), mval(k, P))}</div></div>`;

  m.innerHTML = `<div class="top"><div>${pTitle('Dashboard')}<p class="sub">Zobrazenia, reakcie a zapojenie zo všetkých sietí. Počíta sa z uložených čísel, nemíňa žiadne AI.</p></div></div>
  ${!all.some(x => !proj || x.p === proj) ? `<div class="dfilters"><div class="seg">${DAYS.map(([d, n]) => `<button class="${f.days === d ? 'on' : ''}" onclick="dSet('days',${d})">${n}</button>`).join('')}</div></div><div class="card">${empty('dash', 'Zatiaľ žiadne dáta. Skutočné čísla sa objavia samé, keď appka zverejní prvé videá na pripojené účty (sťahujú sa každých 6 hodín).')}</div>` : `
  <div class="dfilters">
    <div class="seg">${DAYS.map(([d, n]) => `<button class="${f.days === d ? 'on' : ''}" onclick="dSet('days',${d})">${n}</button>`).join('')}</div>
    ${pid ? '' : sel('p', 'Projekt', S.projects.map(p => p.id), v => S.projects.find(p => p.id === +v)?.name || v)}
    ${sel('pl', 'Sieť', nets, v => PL[v])}${sel('c', 'Krajina', ctrs, cName)}${sel('l', 'Jazyk', lngs, lName)}
    ${anyF ? `<button class="btn ghost sm" onclick="dReset()">${I('x', 's')}Zrušiť filtre</button>` : ''}
  </div>
  <div class="dkpis">${['v', 'r', 'er', 'n'].map(kpi).join('')}</div>
  ${cur.length ? `
  <div class="card"><div class="row"><h2 style="margin:0;flex:1">${DM[f.m][0]} v čase</h2>${legend([['var(--acc)', 'Toto obdobie'], ['#6b6b6b', 'Predchádzajúce obdobie', 1]])}</div><div id="dLine" class="dline"></div></div>
  <div class="g2 dg">
    <div class="card"><h2>Podľa siete</h2>${barList(groupBy(cur, x => x.pl).map(g => ({ ...g, label: PL[g.k] || g.k, color: NET_C[g.k], icon: g.k, click: `dSet('pl','${g.k}')` })), f.m, 10, f.pl)}</div>
    <div class="card"><h2>Podľa krajiny</h2>${barList(groupBy(cur, x => x.c).map(g => ({ ...g, label: cName(g.k), click: g.k ? `dSet('c','${g.k}')` : '' })), f.m, 12, f.c)}</div>
  </div>
  <div class="g2 dg">
    <div class="card"><h2>Kedy to funguje najlepšie</h2><p class="small dim" style="margin-top:-6px">${f.m === 'n' ? 'Počet príspevkov' : f.m === 'er' ? 'Zapojenie' : 'Priemer na jeden príspevok'} podľa dňa a hodiny zverejnenia (slovenský čas).</p>${heat(cur, f.m)}</div>
    <div class="card"><h2>Z čoho sú reakcie</h2>${react(A)}
      ${!pid && S.projects.length > 1 ? `<h2 style="margin-top:22px">Podľa projektu</h2>${barList(groupBy(cur, x => x.p).map(g => { const p = S.projects.find(y => y.id === +g.k); return { ...g, label: p?.name || 'Projekt', color: p?.color, click: `dSet('p','${g.k}')` }; }), f.m, 6, f.p)}` : ''}
      <h2 style="margin-top:22px">Podľa jazyka</h2>${barList(groupBy(cur, x => x.l).map(g => ({ ...g, label: lName(g.k), click: g.k ? `dSet('l','${g.k}')` : '' })), f.m, 6, f.l)}</div>
  </div>
  <div class="card"><h2>Najlepšie príspevky</h2>${topTable(cur, f.m)}</div>
  <div class="card"><h2>Účty</h2>${accTable(cur, f.m)}</div>`
    : `<div class="card">${empty('dash', anyF ? 'Pre tieto filtre zatiaľ nie sú žiadne čísla. Skús iné obdobie alebo zruš filtre.' : 'Zatiaľ žiadne dáta v tomto období.')}</div>`}`}
  <p class="small dim" style="margin-top:14px">Iba skutočné čísla zo sietí, nič vymyslené${DD.last ? ' · posledné stiahnutie ' + esc(DD.last.slice(8, 10) + '.' + DD.last.slice(5, 7) + '. ' + DD.last.slice(11, 16)) : ''} · Zapojenie = reakcie ÷ zobrazenia. LinkedIn ráta zobrazenia ako impresie, Instagram bez zobrazení ako dosah.</p>`;
  if (cur.length) lineChart($('#dLine'), cur, prev, f, cut, cut0);
}

function dSet(k, v) {
  const f = S.dash;
  if (k === 'days') v = +v;
  if (k !== 'm' && k !== 'days' && String(f[k]) === String(v)) v = ''; // druhý klik filter zruší
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
  return `<table class="dtab"><tr><th>Príspevok</th><th>Sieť</th><th>Krajina</th><th>Dátum</th><th>Zobrazenia</th><th>Reakcie</th><th>Zapojenie</th></tr>
    ${list.map(x => `<tr><td>${x.u ? `<a href="${esc(x.u)}" target="_blank">${esc(x.t || 'Bez názvu')}</a>` : esc(x.t || 'Bez názvu')}</td><td>${plat(x.pl)}</td><td>${esc(cName(x.c))}</td>
      <td class="dim">${x.d.slice(8, 10)}.${x.d.slice(5, 7)}.</td><td>${nf(x.v)}</td><td>${nf(x.r)}</td><td>${x.v ? pf(x.r / x.v) : '–'}</td></tr>`).join('')}</table>`;
}

function accTable(rows, m) {
  const g = groupBy(rows, x => x.aid).map(a => ({ ...a, x: a.rows[0], val: mval(m, a) })).sort((a, b) => b.val - a.val);
  const more = g.length > 15 && !S.dash.allAcc; if (more) g.length = 15;
  return `<table class="dtab"><tr><th>Účet</th><th>Sieť</th><th>Krajina</th><th>Príspevky</th><th>Zobrazenia</th><th>Reakcie</th><th>Zapojenie</th><th>Na príspevok</th></tr>
    ${g.map(a => `<tr><td>${esc(a.x.acc)}</td><td>${plat(a.x.pl)}</td><td>${esc(cName(a.x.c))}</td><td>${a.n}</td><td>${nf(a.v)}</td><td>${nf(a.r)}</td>
      <td>${a.v ? pf(a.r / a.v) : '–'}</td><td class="dim">${cf(a.v / a.n)} zobr.</td></tr>`).join('')}</table>
    ${more ? `<button class="btn ghost sm" style="margin-top:10px" onclick="S.dash.allAcc=1;pDash($('#main'))">${I('right', 's')}Ukázať všetky účty</button>` : ''}`;
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
