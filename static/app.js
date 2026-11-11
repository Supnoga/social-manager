// Social Manager - rozhranie (bez frameworkov)
const S = { meta: null, projects: [] };
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------- ikonky (Lucide, MIT) ----------
const IC = {
  home: '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  settings: '<path d="M21 4h-7M10 4H3M21 12h-9M8 12H3M21 20h-5M12 20H3M14 2v4M8 10v4M16 18v4"/>',
  plus: '<path d="M5 12h14M12 5v14"/>',
  sparkles: '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.13-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.13a.5.5 0 0 1 .96 0L14.06 8.5A2 2 0 0 0 15.5 9.94l6.13 1.58a.5.5 0 0 1 0 .96L15.5 14.06a2 2 0 0 0-1.44 1.44l-1.58 6.13a.5.5 0 0 1-.96 0z"/><path d="M20 3v4M22 5h-4"/>',
  bulb: '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6M10 22h4"/>',
  phone: '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
  mic: '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3"/>',
  film: '<rect x="2" y="2" width="20" height="20" rx="2.18"/><path d="M7 2v20M17 2v20M2 12h20M2 7h5M2 17h5M17 17h5M17 7h5"/>',
  send: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/>',
  trash: '<path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  play: '<polygon points="6 3 20 12 6 21 6 3"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20M2 12h20"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8M21 3v5h-5M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16M8 16H3v5"/>',
  right: '<path d="m9 18 6-6-6-6"/>', left: '<path d="m15 18-6-6 6-6"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4M10 9H8M16 13H8M16 17H8"/>',
  palette: '<path d="M12 22a10 10 0 1 1 10-10c0 2.5-2 4-4.5 4H15a2 2 0 0 0-1.5 3.3c.4.5.5 1.1.2 1.7-.3.6-1 1-1.7 1Z"/><circle cx="13.5" cy="6.5" r="1"/><circle cx="17.5" cy="10.5" r="1"/><circle cx="8.5" cy="7.5" r="1"/><circle cx="6.5" cy="12.5" r="1"/>',
  youtube: '<path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"/><path d="m10 15 5-3-5-3z"/>',
  facebook: '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
  instagram: '<rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37zM17.5 6.5h.01"/>',
  linkedin: '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
  tiktok: '<path d="M9 12a4 4 0 1 0 4 4V2c.5 2.5 2.5 4.5 5 5"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  pencil: '<path d="M21.17 6.81a1 1 0 0 0-3.99-3.99L3.84 16.17a2 2 0 0 0-.5.83l-1.32 4.35a.5.5 0 0 0 .62.62l4.35-1.32a2 2 0 0 0 .83-.5z"/><path d="m15 5 4 4"/>',
  rocket: '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
  layers: '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65M22 12.65l-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  copy: '<rect x="8" y="8" width="14" height="14" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  ext: '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  bot: '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 16h.01M16 16h.01"/>',
  library: '<path d="m16 6 4 14M12 6v14M8 8v12M4 4v16"/>',
  folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  volume: '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14"/>',
  type: '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
  thumbUp: '<path d="M7 10v12M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
  chart: '<path d="M3 3v18h18M18 17V9M13 17V5M8 17v-3"/>',
};
const I = (n, c = '') => `<svg class="i ${c}" viewBox="0 0 24 24">${IC[n] || ''}</svg>`;
const PL = { youtube: 'YouTube', tiktok: 'TikTok', instagram: 'Instagram', facebook: 'Facebook', linkedin: 'LinkedIn' };
const PLATS = Object.keys(PL);
const plat = (p, withName = true) => `<span class="plat-ic">${I(p)}${withName ? PL[p] : ''}</span>`;
const ST = { review: ['Na schválenie', 'warn'], queued: ['Naplánované', 'acc'], uploading: ['Nahráva sa', 'warn'], done: ['Zverejnené', 'ok'], failed: ['Chyba', 'bad'] };
const langName = c => (S.meta?.languages.find(l => l.code === c) || {}).name || (c || '—').toUpperCase();
const STAGES = [
  ['napad', 'Nápad', 'bulb', 'Čo natočiť'],
  ['prototyp', 'Prototyp', 'phone', 'Scenár a náhľad'],
  ['jazyky', 'Text a hlas', 'mic', 'Hlas prvej verzie'],
  ['video', 'Video', 'film', 'Prvá verzia + jazyky'],
  ['siete', 'Siete', 'send', 'Publikovanie'],
];

// ---------- pomocníci ----------
function toast(msg, err) { const t = $('#toast'); t.textContent = msg; t.className = 'toast' + (err ? ' err' : ''); clearTimeout(t._h); t._h = setTimeout(() => t.classList.add('hidden'), err ? 9000 : 3200); }
function busy(on, text) { $('#busy').classList.toggle('hidden', !on); $('#busyText').textContent = text || 'Pracujem…'; }
function modal(html) { $('#modalBody').innerHTML = html; $('#modal').classList.remove('hidden'); }
function closeModal() { $('#modal').classList.add('hidden'); }
const empty = (icon, text) => `<div class="empty">${I(icon)}<div>${text}</div></div>`;

async function api(url, opts = {}, busyText) {
  if (opts.body && !(opts.body instanceof FormData)) { opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(opts.body); }
  if (busyText) busy(true, busyText);
  try {
    let r, d;
    if (busyText && !(opts.body instanceof FormData) && (opts.method || 'GET') !== 'GET') {
      // dlhá úloha: beží na pozadí, prehliadač sa len pýta na stav
      const j = await (await fetch('/api/job', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url, method: opts.method, body: opts.body ? JSON.parse(opts.body) : null }) })).json();
      let st;
      for (let miss = 0; ;) {
        await new Promise(res => setTimeout(res, 1500));
        try { const x = await fetch('/api/job/' + j.job); st = await x.json(); miss = 0; if (!x.ok) throw new Error(st.detail || 'Chyba'); if (st.done) break; }
        catch (e) { if (e.message && e.message !== 'Failed to fetch' && e.message !== 'Load failed') throw e; if (++miss > 20) throw new Error('Appka neodpovedá – je otvorené čierne okno (Terminál)?'); }
      }
      r = { ok: st.status < 400, status: st.status }; d = st.body || {};
    } else {
      r = await fetch(url, opts);
      d = await r.json().catch(() => ({}));
    }
    if (d.manual) { busy(false); return await manualAI(d); }
    if (!r.ok) throw new Error(d.error || d.detail || 'Chyba ' + r.status);
    return d;
  } catch (e) { if (e.message !== 'Zrušené') toast(/fetch|Load failed/i.test(e.message) ? 'Appka neodpovedá – skontroluj, či je otvorené čierne okno (Terminál), a skús znova.' : e.message, true); throw e; }
  finally { if (busyText) busy(false); }
}

// Ručný režim AI: keď Claude Code nie je dostupný
function manualAI(d) {
  return new Promise((resolve, reject) => {
    modal(`<h2>${I('bot')} Pošli toto Claudovi</h2>
      <p class="muted small">Claude Code nie je zapnutý, tak to spravíme ručne: skopíruj text, vlož ho na claude.ai a odpoveď vlož sem.</p>
      <pre>${esc(d.prompt)}</pre>
      <div class="row"><button class="btn sec" id="mcopy">${I('copy')}Kopírovať</button><a class="btn sec" href="https://claude.ai/new" target="_blank">${I('ext')}Otvoriť claude.ai</a></div>
      <label class="l">Odpoveď od Clauda</label><textarea id="mans" style="min-height:140px"></textarea>
      <div class="row" style="margin-top:12px"><button class="btn" id="mok">${I('check')}Uložiť</button></div>`);
    $('#mcopy').onclick = () => { navigator.clipboard.writeText(d.prompt); toast('Skopírované'); };
    $('#mok').onclick = async () => { try { const res = await api('/api/ai-manual', { method: 'POST', body: { task: d.task, params: d.params, text: $('#mans').value } }); closeModal(); resolve(res); } catch (e) { } };
    $('#modal .x').onclick = () => { closeModal(); reject(new Error('Zrušené')); };
  });
}

// ---------- routing ----------
// #/  #/p/ID/(videa|kontrola|kalendar|radar/TAB|komentare|profily|brief|kniznica|strategia)  #/p/ID/v/IDEA/STEP  #/kontrola #/kalendar #/komentare (všetky projekty)
const R = () => location.hash.replace(/^#\/?/, '').split('?')[0].split('/').filter(Boolean);
const go = h => { location.hash = '#/' + h; };
window.addEventListener('hashchange', render);
$('#modal').addEventListener('click', e => { if (e.target.id === 'modal') closeModal(); });

async function loadBase() {
  [S.meta, S.projects] = await Promise.all([api('/api/meta'), api('/api/projects')]);
}

function sidebar() {
  const r = R(), cur = r[0] || '', inP = cur === 'p' ? +r[1] : 0, sec = inP ? (r[2] || 'videa') : '';
  const nav = (h, icon, label, on, cnt) => `<a class="nav ${on ? 'on' : ''}" href="#/${h}">${I(icon)}${label}${cnt ? `<span class="cnt" style="color:var(--acc);font-weight:700">${cnt}</span>` : ''}</a>`;
  const sub = (p, k, icon, label, cnt) => `<a class="nav sub ${inP === p.id && (sec === k || (k === 'videa' && ['videa', 'v', 'kniznica', 'strategia'].includes(sec))) ? 'on' : ''}" href="#/p/${p.id}/${k}">${I(icon, 's')}${label}${cnt ? `<span class="cnt" style="color:var(--acc);font-weight:700">${cnt}</span>` : ''}</a>`;
  const ai = S.meta.ai;
  $('#side').innerHTML = `
    <div class="logo"><div class="mark">${I('play')}</div>Social Manager</div>
    ${nav('', 'home', 'Prehľad', !cur)}
    <div class="sec-t">Projekty <a href="#/novy" title="Nový projekt">${I('plus', 's')}</a></div>
    ${S.projects.map(p => `<a class="nav ${inP === p.id ? 'on' : ''}" href="#/p/${p.id}/videa"><span class="dot" style="background:${p.color}"></span>${esc(p.name)}<span class="cnt" ${p.review + p.inbox ? 'style="color:var(--acc);font-weight:700"' : ''}>${inP === p.id ? '' : (p.review + p.inbox || '')}</span></a>
      ${inP === p.id ? `<div class="subnav">${sub(p, 'videa', 'layers', 'Videá')}${sub(p, 'kontrola', 'eye', 'Kontrola', p.review)}${sub(p, 'kalendar', 'calendar', 'Publikovanie', p.failed ? '!' : '')}${sub(p, 'dashboard', 'chart', 'Dashboard')}${sub(p, 'radar', 'radar', 'Radar', p.inbox)}${sub(p, 'komentare', 'message', 'Komentáre')}${sub(p, 'spravy', 'inbox', 'Správy')}${sub(p, 'ucty', 'link', 'Účty a siete')}${sub(p, 'profily', 'user', 'Vzhľad účtov')}${sub(p, 'brief', 'palette', 'Popis a dizajn')}</div>` : ''}`).join('') || `<a class="nav" href="#/novy">${I('plus')}Nový projekt</a>`}
    <div class="sec-t">Nastavenie</div>
    ${nav('nastavenia', 'settings', 'Nastavenia', cur === 'nastavenia')}
    <div class="side-foot">
      <div class="status"><i class="${ai.cli_found ? '' : 'w'}"></i>Claude ${ai.cli_found ? 'pripojený' : 'v ručnom režime'}</div>
      <div class="status"><i class="${S.meta.settings.paused ? 'w' : ''}"></i>Plánovač ${S.meta.settings.paused ? 'pozastavený' : 'beží'}</div>
      <a class="small dim" style="display:block;margin-top:8px;cursor:pointer" onclick="quitApp()">Vypnúť appku</a>
    </div>`;
}
// aktuálny projekt (ak je stránka otvorená v projekte) – pre filtre a nadpisy
const PF = () => S.pf ? S.projects.find(x => x.id === S.pf) : null;
const here = () => location.hash.split('?')[0];
const pTitle = t => { const p = PF(); return p ? `<div class="crumb"><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${p.color};margin-right:6px"></span>${esc(p.name)}</div><h1>${t}</h1>` : `<h1>${t}</h1>`; };

const PROJ_SECS = ['kalendar', 'kontrola', 'komentare', 'spravy', 'radar', 'dashboard', 'profily', 'ucty'];
async function render() {
  await loadBase();
  sidebar();
  const r = R(), m = $('#main');
  window.scrollTo(0, 0);
  S.pf = r[0] === 'p' ? +r[1] : 0;
  if (S.pf) try { localStorage.setItem('lastP', S.pf); } catch (e) { }
  // všetko patrí pod projekt: staré spoločné adresy (aj návrat z pripájania účtu) otvoria posledný projekt
  if (PROJ_SECS.includes(r[0])) {
    let lp = 0; try { lp = +localStorage.getItem('lastP'); } catch (e) { }
    const p = S.projects.find(x => x.id === lp) || S.projects[0];
    const qs = location.hash.includes('?') ? '?' + location.hash.split('?')[1] : '';
    return location.replace(p ? `#/p/${p.id}/${r.join('/')}${qs}` : '#/novy');
  }
  try {
    if (!r[0]) await pHome(m);
    else if (r[0] === 'nastavenia') await pSettings(m);
    else if (r[0] === 'novy') pProjectForm(m, null);
    else if (r[0] === 'p') {
      const p = S.projects.find(x => x.id === +r[1]);
      if (!p) return go('');
      const sec = r[2] || 'videa';
      if (sec === 'v') await pIdea(m, p, +r[3], r[4] || null);
      else if (sec === 'kontrola') await pReview(m);
      else if (sec === 'kalendar') await pCalendar(m);
      else if (sec === 'radar') await pRadar(m);
      else if (sec === 'dashboard') await pDash(m);
      else if (sec === 'komentare') await pComments(m);
      else if (sec === 'spravy') await pMessages(m);
      else if (sec === 'profily') await pProfiles(m);
      else if (sec === 'ucty') await pAccounts(m);
      else await pProject(m, p, sec);
    }
  } catch (e) { console.error(e); }
  const q = new URLSearchParams(location.hash.split('?')[1] || '');
  if (q.get('ok')) { toast('Účet pripojený: ' + q.get('ok')); history.replaceState(null, '', location.hash.split('?')[0]); }
  if (q.get('err')) { toast('Chyba: ' + q.get('err'), true); history.replaceState(null, '', location.hash.split('?')[0]); }
}


async function pHome(m) {
  const d = await api('/api/dashboard');
  const ai = S.meta.ai;
  const steps = [
    [ai.cli_found, 'Claude prepojený s Max plánom', 'nastavenia'],
    [d.projects > 0, 'Vytvoriť prvý projekt', 'novy'],
    [d.accounts > 0, 'Pripojiť siete', 'ucty'],
    [(d.posts.queued || 0) + (d.posts.done || 0) > 0, 'Naplánovať prvé video', d.projects ? `p/${S.projects[0]?.id}/videa` : 'novy'],
  ];
  const tile = (icon, n, label) => `<div class="card stat"><div class="ic">${I(icon)}</div><div><b>${n}</b><span>${label}</span></div></div>`;
  m.innerHTML = `<div class="top"><div><h1>Prehľad</h1><p class="sub">Všetky projekty a publikovanie na jednom mieste.</p></div><div class="sp"></div>
    <a class="btn" href="#/novy">${I('plus')}Nový projekt</a></div>
  <div class="grid" style="margin-bottom:14px;grid-template-columns:repeat(auto-fill,minmax(170px,1fr))">
    ${tile('folder', d.projects, 'projektov')}${tile('bulb', d.ideas, 'nápadov v práci')}${tile('film', d.videos, 'videí')}
    ${tile('clock', d.posts.queued || 0, 'naplánovaných')}${tile('check', d.posts.done || 0, 'zverejnených')}
    ${tile('bot', ((d.ai.day.inp + d.ai.day.outp) / 1000).toFixed(1) + 'k', 'AI tokenov za 24 h')}
  </div>
  ${d.expiring.length ? `<div class="hint" style="margin-bottom:14px">${I('alert')}<div>LinkedIn prihlásenie čoskoro vyprší: ${d.expiring.map(e => `<b>${esc(e.name)}</b> (${e.days} dní)`).join(', ')}. <a class="btn sm" href="/api/accounts/linkedin/connect${d.expiring.some(e => e.org) ? '?org=1' : ''}">Prihlásiť znova</a></div></div>` : ''}
  ${(d.posts.failed || 0) ? `<div class="hint" style="margin-bottom:14px;border-color:rgba(240,68,56,.4);background:var(--badSoft);color:#ffc9c4">${I('alert')}<div>${d.posts.failed} publikovaní skončilo chybou. <a href="#/kalendar?f=failed">Pozrieť</a></div></div>` : ''}
  <div class="g2">
    <div class="card"><h2>${I('folder')}Projekty</h2>${S.projects.length ? S.projects.map(p => `<a class="nav" href="#/p/${p.id}/videa"><span class="dot" style="background:${p.color}"></span><div><div style="color:#fff">${esc(p.name)}</div><div class="small dim">${p.languages.length} jazykov · ${p.ideas} nápadov · ${p.videos} videí</div></div><span class="sp"></span>${I('right', 's')}</a>`).join('') : empty('folder', 'Zatiaľ žiadny projekt.')}</div>
    ${steps.some(s => !s[0]) ? `<div class="card"><h2>${I('target')}Prvé kroky</h2><ul class="check-list">${steps.map(s => `<li><span class="b ${s[0] ? 'ok' : ''}">${I(s[0] ? 'check' : 'right', 's')}</span><a href="#/${s[2]}" style="color:${s[0] ? 'var(--muted)' : '#fff'}">${s[1]}</a></li>`).join('')}</ul></div>`
      : `<div class="card"><h2>${I('check')}Posledné výsledky</h2>${postList(d.recent.slice(0, 6))}</div>`}
  </div>
  <div class="g2" style="margin-top:14px">
    <div class="card"><h2>${I('clock')}Naplánované</h2>${postList(d.upcoming)}</div>
    ${steps.some(s => !s[0]) ? `<div class="card"><h2>${I('check')}Posledné výsledky</h2>${postList(d.recent)}</div>` : `<div class="card"><h2>${I('chart')}AI za 24 h</h2><p class="muted">${d.ai.day.calls} volaní · ${((d.ai.day.inp + d.ai.day.outp) / 1000).toFixed(1)}k tokenov · ${d.ai.day.cached} zadarmo z pamäte</p><a href="#/nastavenia">Detail spotreby</a></div>`}
  </div>`;
}
function postList(list) {
  if (!list.length) return empty('calendar', 'Nič tu nie je.');
  return `<table>${list.map(p => `<tr><td style="width:120px" class="small muted">${esc(p.scheduled_at.slice(5, 16))}</td><td>${plat(p.platform, false)}</td>
    <td><div style="max-width:260px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(p.title || p.original_name)}</div><div class="small dim">${esc(p.project_name || '')} · ${langName(p.lang)}</div></td>
    <td style="text-align:right"><span class="chip ${ST[p.status][1]}">${ST[p.status][0]}</span>${p.url && p.url.startsWith('http') ? ` <a href="${esc(p.url)}" target="_blank" class="btn ghost sm">${I('ext', 's')}</a>` : ''}</td></tr>`).join('')}</table>`;
}

// ================= PROJEKT =================
async function pProject(m, p, tab) {
  const tabs = [['videa', 'layers', 'Videá'], ['brief', 'palette', 'Popis a dizajn'], ['kniznica', 'library', 'Knižnica'], ['strategia', 'target', 'Stratégia']];
  m.innerHTML = `<div class="top"><div><div class="crumb"><a href="#/">Prehľad</a>${I('right', 's')}Projekt</div>
    <h1 class="row"><span class="dot" style="width:12px;height:12px;border-radius:4px;background:${p.color}"></span>${esc(p.name)}</h1>
    <div class="row" style="margin-top:8px">${p.languages.slice(0, 12).map(l => `<span class="chip">${esc(l.toUpperCase())}</span>`).join('')}${p.languages.length > 12 ? `<span class="chip">+${p.languages.length - 12}</span>` : ''}
    <span class="dim">·</span>${p.platforms.map(x => `<span class="chip">${I(x, 's')}</span>`).join('')}</div></div></div>
  <div class="tabs">${tabs.map(([k, ic, n]) => `<a href="#/p/${p.id}/${k}" class="${tab === k ? 'on' : ''}">${I(ic, 's')}${n}</a>`).join('')}</div>
  <div id="pbody"></div>`;
  const b = $('#pbody');
  if (tab === 'videa') await tBoard(b, p);
  else if (tab === 'brief') pProjectForm(b, p);
  else if (tab === 'kniznica') await tLibrary(b, p);
  else if (tab === 'strategia') tStrategy(b, p);
}

async function tBoard(b, p) {
  const ideas = await api(`/api/projects/${p.id}/board`);
  const by = k => ideas.filter(i => i.stage === k);
  const nL = p.languages.length;
  b.innerHTML = `<div class="row" style="margin-bottom:16px">
      <button class="btn" onclick="ideasDialog(${p.id})">${I('sparkles')}Vymyslieť nápady</button>
      <button class="btn sec" onclick="ownIdea(${p.id})">${I('pencil')}Vlastný nápad</button>
      <button class="btn sec" onclick="autoDialog(${p.id})">${I('rocket')}Autopilot</button>
      <span class="sp"></span>${p.strategy ? '' : `<button class="btn ghost" onclick="makeStrategy(${p.id})">${I('target')}Odporúčam najprv stratégiu</button>`}
    </div><div id="autoBox"></div>
    <div class="board">${STAGES.map(([k, n, ic], idx) => `<div class="lane"><div class="lane-h"><span class="n">${idx + 1}</span>${n}<span class="c">${by(k).length}</span></div>
      ${by(k).map(i => `<div class="vc" onclick="go('p/${p.id}/v/${i.id}')">
        <div class="row" style="justify-content:space-between;margin-bottom:6px"><span class="score ${i.score >= 8 ? 'hi' : ''}">${i.score || '–'}</span>${i.status === 'new' ? '<span class="chip">nový</span>' : ''}${i.failed ? `<span class="chip bad">${I('alert', 's')}${i.failed}</span>` : ''}</div>
        <div class="t">${esc(i.title)}</div><div class="h">${esc(i.hook)}</div>
        <div class="m">${i.langs ? `<span title="jazyky">${I('globe', 's')}${i.langs}/${nL}</span>` : ''}${i.voices ? `<span title="hlasy">${I('mic', 's')}${i.voices}</span>` : ''}${i.videos ? `<span title="videá">${I('film', 's')}${i.videos}</span>` : ''}${i.queued ? `<span title="naplánované">${I('clock', 's')}${i.queued}</span>` : ''}${i.posted ? `<span title="zverejnené" class="ok-t">${I('check', 's')}${i.posted}</span>` : ''}</div>
      </div>`).join('') || (idx === 0 ? empty('bulb', 'Klikni na „Vymyslieť nápady“') : '')}</div>`).join('')}</div>`;
  pollAuto();
}

function ideasDialog(pid) {
  modal(`<h2>${I('sparkles')}Vymyslieť nápady</h2><p class="muted small">Claude vymyslí viac nápadov, sám ich ohodnotí a dá ti len tie najsilnejšie.</p>
  <div class="g2"><div><label class="l">Počet</label><select id="iCount"><option>5</option><option selected>10</option><option>20</option></select></div>
  <div><label class="l">Formát</label><select id="iFmt"><option value="short">Krátke video (TikTok, Reels, Shorts)</option><option value="long">Dlhé YouTube video</option></select></div></div>
  <label class="l">Na čo sa zamerať (nepovinné)</label><input id="iFocus" placeholder="napr. Vianoce, chyby začiatočníkov…">
  <div class="row" style="margin-top:16px"><button class="btn" onclick="genIdeas(${pid})">${I('sparkles')}Vymyslieť</button></div>`);
}
async function genIdeas(pid) { const body = { project_id: pid, count: +$('#iCount').value, format: $('#iFmt').value, focus: $('#iFocus').value }; closeModal(); const r = await api('/api/ai/ideas', { method: 'POST', body }, 'Claude vymýšľa nápady…'); toast(`Pridaných ${r.created} nápadov`); render(); }
function ownIdea(pid) {
  modal(`<h2>${I('pencil')}Vlastný nápad</h2><label class="l">O čom bude video</label><input id="oT" placeholder="napr. 3 chyby pri varení cestovín">
  <label class="l">Úvodná veta (háčik) – nepovinné</label><input id="oH"><label class="l">Poznámka pre AI – nepovinné</label><textarea id="oA"></textarea>
  <div class="row" style="margin-top:16px"><button class="btn" onclick="saveOwnIdea(${pid})">${I('check')}Pridať</button></div>`);
}
async function saveOwnIdea(pid) { const r = await api('/api/ideas', { method: 'POST', body: { project_id: pid, title: $('#oT').value, hook: $('#oH').value, angle: $('#oA').value } }); closeModal(); go(`p/${pid}/v/${r.id}`); }
async function makeStrategy(id) { await api('/api/ai/strategy', { method: 'POST', body: { project_id: id } }, 'Claude premýšľa nad stratégiou… (cca 1 min)'); toast('Stratégia hotová'); go(`p/${id}/strategia`); }

function autoDialog(pid) {
  modal(`<h2>${I('rocket')}Autopilot</h2><p class="muted small">Claude vymyslí nápady, vyberie najlepšie, napíše scenáre a urobí prvú verziu videa v jednom jazyku. Keď sa ti video páči, jedným tlačidlom ho rozšíriš do ostatných jazykov.</p>
  <div class="g2"><div><label class="l">Koľko nápadov vymyslieť</label><input id="aC" type="number" value="10"></div><div><label class="l">Koľko najlepších spracovať</label><input id="aT" type="number" value="3"></div></div>
  <label class="l">Na čo sa zamerať (nepovinné)</label><input id="aF">
  <label class="row" style="margin-top:12px"><input type="checkbox" id="aV" checked> Urobiť aj prvú verziu videa (hlas + video v jednom jazyku)</label>
  <label class="row" style="margin-top:6px"><input type="checkbox" id="aA"> Rovno aj všetky ostatné jazyky (bez kontroly)</label>
  <button class="btn" onclick="runAuto(${pid})">${I('rocket')}Spustiť</button>`);
}
async function runAuto(pid) { await api('/api/autopilot', { method: 'POST', body: { project_id: pid, count: +$('#aC').value, take: +$('#aT').value, videos: $('#aV').checked || $('#aA').checked, all_langs: $('#aA').checked, focus: $('#aF').value } }); closeModal(); pollAuto(); }
async function pollAuto() {
  const a = await api('/api/autopilot'); const box = $('#autoBox'); if (!box || (!a.running && !a.step)) return;
  box.innerHTML = `<div class="hint" style="margin-bottom:14px">${a.running ? '<span class="spinner spin-s"></span>' : I('check')}<div><b>Autopilot:</b> ${esc(a.step)}<div class="small">${a.log.map(esc).join('<br>')}</div></div></div>`;
  if (a.running) setTimeout(pollAuto, 4000); else if (a.step.startsWith('Hotovo') && box.dataset.was) render();
  box.dataset.was = a.running ? '1' : '';
}

function tStrategy(b, p) {
  const s = p.strategy;
  if (!s) { b.innerHTML = `<div class="card">${empty('target', 'Stratégia ešte nie je.')}<div class="row" style="justify-content:center"><button class="btn" onclick="makeStrategy(${p.id})">${I('sparkles')}Vytvoriť stratégiu</button></div></div>`; return; }
  const list = a => (a || []).map(x => `<li style="margin:6px 0">${typeof x === 'string' ? esc(x) : Object.values(x).map(v => esc(Array.isArray(v) ? v.join(', ') : v)).join(' — ')}</li>`).join('');
  b.innerHTML = `<div class="card"><div class="row"><h2 style="margin:0">${I('target')}Pozicionovanie</h2><span class="sp"></span><button class="btn sec sm" onclick="makeStrategy(${p.id})">${I('refresh', 's')}Prerobiť</button></div><p style="font-size:16px">${esc(s.positioning)}</p></div>
  <div class="g2" style="margin-top:14px"><div class="card"><h2>Publikum</h2><ul>${list(s.audience)}</ul></div><div class="card"><h2>Piliere obsahu</h2><ul>${list(s.pillars)}</ul></div>
  <div class="card"><h2>Háčiky na prvé 2 sekundy</h2><ul>${list(s.hooks)}</ul></div><div class="card"><h2>Formáty</h2><ul>${list(s.formats)}</ul><p class="muted"><b>Frekvencia:</b> ${esc(s.cadence)}</p></div>
  <div class="card"><h2 class="ok-t">Rob</h2><ul>${list(s.do)}</ul></div><div class="card"><h2 class="bad-t">Nerob</h2><ul>${list(s.dont)}</ul></div></div>`;
}

// ---------- popis + dizajn projektu ----------
function pProjectForm(m, p) {
  const isNew = !p;
  p = p || { name: '', description: '', audience: '', tone: '', goals: '', source_lang: 'sk', languages: ['sk', 'cs', 'en', 'de'], color: '#FF6B00', voice_gender: 'F', platforms: ['youtube', 'tiktok', 'instagram', 'facebook'], design_colors: [] };
  m.innerHTML = `${isNew ? `<div class="top"><div><div class="crumb"><a href="#/">Prehľad</a>${I('right', 's')}Nový projekt</div><h1>Nový projekt</h1><p class="sub">Každý projekt = jedna značka. Má svoje jazyky, siete, štýl a videá.</p></div></div>` : ''}
  <div class="g2" style="align-items:start">
  <div class="card"><h2>${I('file')}Popis projektu</h2>
    <div class="g2"><div><label class="l">Názov</label><input id="pName" value="${esc(p.name)}"></div><div><label class="l">Farba v appke</label><input id="pColor" type="color" value="${p.color}"></div></div>
    <label class="l">O čom je projekt (čím viac detailov, tým lepšie nápady)</label><textarea id="pDesc" style="min-height:120px">${esc(p.description)}</textarea>
    <label class="l">Pre koho (publikum)</label><textarea id="pAud" style="min-height:70px">${esc(p.audience)}</textarea>
    <div class="g2"><div><label class="l">Štýl / tón</label><input id="pTone" value="${esc(p.tone)}" placeholder="vtipný, odborný…"></div><div><label class="l">Cieľ</label><input id="pGoals" value="${esc(p.goals)}" placeholder="sledovatelia, predaj…"></div></div>
    <div class="g2"><div><label class="l">Hlavný jazyk (v ňom vymýšľame)</label><select id="pSrc">${S.meta.languages.map(l => `<option value="${l.code}" ${l.code === p.source_lang ? 'selected' : ''}>${l.name}</option>`).join('')}</select></div>
    <div><label class="l">Hlas</label><select id="pVoice"><option value="F" ${p.voice_gender === 'F' ? 'selected' : ''}>Ženský</option><option value="M" ${p.voice_gender === 'M' ? 'selected' : ''}>Mužský</option></select></div></div>
    <label class="l">Neprekladať (názvy značky, produktov, mená – oddeľ čiarkou)</label><input id="pGloss" value="${esc(p.glossary || '')}" placeholder="Zdravé recepty, FitBox, Oliver">
    <label class="l">Nikdy netvrdiť (zakázané slová a tvrdenia, oddeľ bodkočiarkou)</label><input id="pBan" value="${esc(p.banned || '')}" placeholder="made in Slovakia; najlacnejší na trhu">
    <label class="l">Siete</label><div class="pick">${PLATS.map(x => `<label><input type="checkbox" name="pl" value="${x}" ${p.platforms.includes(x) ? 'checked' : ''}>${I(x, 's')}${PL[x]}</label>`).join('')}</div>
    <label class="l">Jazyky <a class="small" onclick="$$('[name=lang]').forEach(c=>c.checked=true)">vybrať všetky</a> · <a class="small" onclick="$$('[name=lang]').forEach(c=>c.checked=false)">zrušiť</a></label>
    <div class="pick">${S.meta.languages.map(l => `<label title="${esc(l.countries || '')}"><input type="checkbox" name="lang" value="${l.code}" ${p.languages.includes(l.code) ? 'checked' : ''}>${l.name}</label>`).join('')}</div>
    <p class="small dim">Podrž myš na jazyku a uvidíš krajiny, pre ktoré je.</p>
    <div class="row" style="margin-top:18px"><button class="btn" onclick="saveProject(${p.id || 0})">${I('check')}${isNew ? 'Vytvoriť projekt' : 'Uložiť'}</button>
    ${isNew ? '' : `<span class="sp"></span><button class="btn bad sm" onclick="delProject(${p.id})">${I('trash', 's')}Zmazať projekt</button>`}</div></div>
  ${isNew ? `<div class="card"><h2>${I('palette')}Dizajn</h2><p class="muted">Po vytvorení projektu sem môžeš vložiť MD dizajn (napr. z Claude Design), logo, fotky, fonty a PDF brand manuál. Appka ich potom použije vo všetkých videách.</p></div>` : `
  <div class="card"><h2>${I('palette')}Dizajn značky (MD)</h2>
    <p class="muted small">Vlož .md súbory s dizajnom (napr. export z Claude Design, brand manuál). Appka si z nich raz urobí krátke zhrnutie, takže to nemíňa veľa tokenov.</p>
    ${p.design_colors.length ? `<div class="row" style="margin:10px 0">${p.design_colors.map(c => `<div class="col" style="align-items:center;gap:4px"><div class="swatch" style="background:${c}"></div><span class="small dim">${c}</span></div>`).join('')}</div>` : ''}
    ${p.design_summary ? `<div class="hint" style="margin:10px 0">${I('sparkles')}<div>${esc(p.design_summary)}</div></div>` : ''}
    <div class="drop" id="mdDrop">${I('upload', 'l')}<div style="margin-top:6px">Pretiahni sem súbory alebo klikni</div><input type="file" id="mdIn" multiple accept=".md,.markdown,.txt,.pdf" class="hidden"></div>
    <label class="l">…alebo vlož text</label><textarea id="mdText" placeholder="# Brand&#10;Farby: #FF6B00 …"></textarea>
    <div class="row" style="margin-top:10px"><button class="btn sm" onclick="saveDesign(${p.id},'append')">${I('plus', 's')}Pridať</button><button class="btn sec sm" onclick="saveDesign(${p.id},'replace')">${I('refresh', 's')}Nahradiť všetko</button></div>
    ${p.design_md ? `<details style="margin-top:14px"><summary>Zobraziť vložený dizajn (${p.design_md.length.toLocaleString('sk')} znakov)</summary><pre>${esc(p.design_md.slice(0, 20000))}</pre></details>` : ''}
  </div>
  <div class="card" id="brandCard"></div>
  <div class="card"><h2>${I('library')}Zdroje (odkiaľ má AI čerpať)</h2>
    <p class="muted small">Pridaj odkazy na tvoj web, produkty, články, alebo vlož text či súbory (PDF, TXT, MD). Appka ich prečíta a AI si z nich raz urobí výťah faktov – stratégia, nápady aj scenáre z nich potom vychádzajú. Šetrí to tokeny.</p>
    ${p.sources.length ? `<div class="vlist">${p.sources.map((x, i) => `<div class="vrow">${I(x.kind === 'url' ? 'globe' : 'file', 's')}<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(x.url || x.name)}">${esc(x.name)}</span><span class="small dim">${x.chars < 1000 ? x.chars + " znakov" : Math.round(x.chars / 1000) + "k znakov"}</span><button class="btn ghost sm ic" title="Odstrániť" onclick="srcRemove(${p.id},${i})">${I('trash', 's')}</button></div>`).join('')}</div>` : ''}
    ${p.sources_summary ? `<details style="margin-top:10px"><summary class="small">Čo si AI zo zdrojov zapamätala</summary><p class="small muted">${esc(p.sources_summary)}</p></details>` : ''}
    <label class="l">Odkazy (každý na nový riadok)</label><textarea id="srcUrls" style="min-height:70px" placeholder="https://mojweb.sk&#10;https://mojweb.sk/produkty"></textarea>
    <label class="l">…alebo vlož text</label><textarea id="srcText" style="min-height:70px" placeholder="Popis produktov, cenník, časté otázky zákazníkov…"></textarea>
    <div class="row" style="margin-top:10px"><button class="btn sm" onclick="srcAdd(${p.id})">${I('plus', 's')}Pridať</button><label class="btn sec sm">${I('upload', 's')}Pridať súbory<input type="file" multiple accept=".pdf,.txt,.md,.csv" class="hidden" onchange="srcFiles(${p.id},this.files)"></label></div>
  </div>
  <div class="card"><h2>${I('mic')}Hlasy pre jazyky</h2>
    <p class="muted small">Pri každom jazyku si vyber hlas a vypočuj ukážku. „Automaticky“ = najlepší dostupný hlas. Potom klikni Uložiť.</p>
    <label class="l">Rýchlosť reči <span class="dim" id="rateV">${(+p.voice_rate || 1).toFixed(2)}×</span></label><input type="range" id="pRate" min="0.8" max="1.3" step="0.05" value="${p.voice_rate || 1}" oninput="$('#rateV').textContent=(+this.value).toFixed(2)+'×'">
    <div id="pVoices" class="vlist">${p.languages.map(l => `<div class="vrow"><span style="min-width:110px">${esc(S.meta.languages.find(x => x.code === l)?.name || l)}</span><select data-vl="${l}" style="flex:1"><option value="auto">Automaticky</option></select><button class="btn sec sm ic" title="Ukážka" onclick="playVoice('${l}',$('[data-vl=${l}]').value,this)">${I('play', 's')}</button></div>`).join('')}</div>
    <div class="row" style="margin-top:12px"><button class="btn sm" onclick="saveProject(${p.id})">${I('check', 's')}Uložiť hlasy</button></div>
  </div>`}</div>`;
  if (p.id) p.languages.forEach(async l => {
    const d = await voicesFor(l), sel = $(`[data-vl=${l}]`); if (!sel) return;
    const cur = (p.voices || {})[l] || 'auto';
    const grp = (t, list) => list.length ? `<optgroup label="${t}">${list.map(v => `<option value="${v.id}" ${v.id === cur ? 'selected' : ''}>${esc(v.label)} (${v.gender === 'F' ? 'žena' : 'muž'})</option>`).join('')}</optgroup>` : '';
    sel.innerHTML = `<option value="auto">Automaticky (najlepší dostupný)</option>` + grp('Google HD – najprirodzenejšie', d.voices.filter(v => v.engine === 'google')) + grp('Microsoft – zadarmo bez kľúča', d.voices.filter(v => v.engine === 'edge'));
  });
  if (p.id && typeof brandCard === 'function') brandCard(p.id);
  const drop = $('#mdDrop');
  if (drop) {
    const fin = $('#mdIn');
    drop.onclick = () => fin.click();
    drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
    drop.ondragleave = () => drop.classList.remove('over');
    drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over'); uploadMd(p.id, e.dataTransfer.files); };
    fin.onchange = () => uploadMd(p.id, fin.files);
  }
}
async function srcDone(r) { toast('Zdroje uložené' + (r.errors && r.errors.length ? ' · ' + r.errors.join('; ') : ''), !!(r.errors && r.errors.length)); render(); }
async function srcAdd(pid) { const urls = $('#srcUrls').value, text = $('#srcText').value; if (!urls.trim() && !text.trim()) return toast('Vlož odkaz alebo text', true); srcDone(await api(`/api/projects/${pid}/sources`, { method: 'POST', body: { urls, text } }, 'Čítam zdroje…')); }
async function srcFiles(pid, files) { const fd = new FormData(); [...files].forEach(f => fd.append('files', f)); srcDone(await api(`/api/projects/${pid}/sources`, { method: 'POST', body: fd }, 'Čítam súbory…')); }
async function srcRemove(pid, i) { if (!confirm('Odstrániť tento zdroj?')) return; srcDone(await api(`/api/projects/${pid}/sources`, { method: 'POST', body: { remove: i } }, 'Aktualizujem…')); }
async function saveProject(id) {
  const body = { name: $('#pName').value, color: $('#pColor').value, description: $('#pDesc').value, audience: $('#pAud').value, tone: $('#pTone').value, goals: $('#pGoals').value, source_lang: $('#pSrc').value, voice_gender: $('#pVoice').value, glossary: $('#pGloss').value, banned: $('#pBan') ? $('#pBan').value : '', ...($('#pRate') ? { voice_rate: +$('#pRate').value, voices: Object.fromEntries($$('[data-vl]').map(x => [x.dataset.vl, x.value])) } : {}), languages: $$('[name=lang]:checked').map(c => c.value), platforms: $$('[name=pl]:checked').map(c => c.value) };
  if (!body.name) return toast('Zadaj názov projektu', true);
  if (!body.languages.includes(body.source_lang)) body.languages.unshift(body.source_lang);
  const r = await api(id ? '/api/projects/' + id : '/api/projects', { method: id ? 'PUT' : 'POST', body });
  toast('Uložené'); if (!id) go(`p/${r.id}/brief`); else render();
}
async function delProject(id) { if (!confirm('Naozaj zmazať projekt aj s jeho nápadmi a videami?')) return; await api('/api/projects/' + id, { method: 'DELETE' }); go(''); }
async function uploadMd(pid, files) { if ([...files].some(f => !/\.(md|markdown|txt)$/i.test(f.name)) && typeof brandUpload === 'function') return brandUpload(pid, files); const fd = new FormData(); [...files].forEach(f => fd.append('files', f)); fd.append('mode', 'append'); await api(`/api/projects/${pid}/design`, { method: 'POST', body: fd }, 'Čítam dizajn…'); toast('Dizajn uložený'); render(); }
async function saveDesign(pid, mode) { const text = $('#mdText').value; if (!text && mode === 'append') return toast('Vlož text alebo súbor', true); if (mode === 'replace' && !confirm('Nahradiť celý doterajší dizajn?')) return; await api(`/api/projects/${pid}/design`, { method: 'POST', body: { text, mode } }, 'Čítam dizajn…'); toast('Dizajn uložený'); render(); }

// ================= DETAIL VIDEA (5 krokov) =================
async function pIdea(m, p, iid, step) {
  const d = await api(`/api/ideas/${iid}/full`);
  const { idea, scripts } = d;
  const src = scripts.find(s => s.is_source) || scripts[0];
  const hasVideo = scripts.some(s => s.videos.length), hasPosts = scripts.some(s => s.posts.length);
  const autoStep = hasPosts ? 'siete' : hasVideo ? 'video' : scripts.length > 1 || scripts.some(s => s.voice_path) ? 'jazyky' : src ? 'prototyp' : 'napad';
  step = step || autoStep;
  const doneIdx = STAGES.findIndex(s => s[0] === autoStep);
  m.innerHTML = `<div class="top"><div style="min-width:0;flex:1"><div class="crumb"><a href="#/p/${p.id}/videa">${esc(p.name)}</a>${I('right', 's')}Video</div>
    <h1>${esc(src?.title || idea.title)}</h1></div>
    <button class="btn ghost" onclick="if(confirm('Zmazať tento nápad aj s jeho jazykmi?'))api('/api/ideas/${iid}',{method:'DELETE'}).then(()=>go('p/${p.id}/videa'))">${I('trash')}</button></div>
  <div class="steps">${STAGES.map(([k, n, ic, sub], i) => `<div class="step ${k === step ? 'on' : i < doneIdx || (i === doneIdx && k !== step) ? 'done' : ''}" onclick="go('p/${p.id}/v/${iid}/${k}')"><span class="b">${i < doneIdx && k !== step ? I('check', 's') : i + 1}</span><div>${n}<small>${sub}</small></div></div>`).join('')}</div>
  <div id="sbody"></div>`;
  const b = $('#sbody');
  const ctx = { p, idea, scripts, src, iid };
  ({ napad: sIdea, prototyp: sProto, jazyky: sLangs, video: sVideo, siete: sSocial })[step](b, ctx);
}

function sIdea(b, { p, idea, src, iid }) {
  b.innerHTML = `<div class="g2" style="align-items:start"><div class="card"><h2>${I('bulb')}Nápad</h2>
    <label class="l">Názov</label><input id="eT" value="${esc(idea.title)}">
    <label class="l">Háčik (prvá veta)</label><input id="eH" value="${esc(idea.hook)}">
    <label class="l">Uhol / čím je to iné</label><textarea id="eA">${esc(idea.angle)}</textarea>
    ${idea.why ? `<p class="small muted">${I('chart', 's')} ${esc(idea.why)}</p>` : ''}
    <div class="row" style="margin-top:14px"><button class="btn sec" onclick="saveIdea(${iid})">${I('check')}Uložiť</button><span class="sp"></span>
      <button class="btn sec" title="Claude napíše 4 pokračovania (časť 2 až 5). Série najlepšie naberajú sledovateľov." onclick="mkSeries(${p.id},${iid})">${I('layers')}Urobiť z toho sériu</button></div></div>
  <div class="card"><h2>${I('phone')}Ďalší krok: prototyp</h2>
    <p class="muted">Claude napíše scenár: text pre hlas, scény, texty na obrazovku, popis a hashtagy. Potom si to pozrieš ako náhľad videa.</p>
    ${src ? `<div class="hint">${I('check')}<div>Prototyp už existuje.</div></div><div class="row" style="margin-top:12px"><button class="btn" onclick="go('p/${p.id}/v/${iid}/prototyp')">Otvoriť prototyp${I('right')}</button><button class="btn sec" onclick="mkProto(${p.id},${iid})">${I('refresh')}Napísať znova</button></div>`
      : `<button class="btn" onclick="mkProto(${p.id},${iid})">${I('sparkles')}Vytvoriť prototyp</button>`}</div></div>`;
}
async function saveIdea(iid) { await api('/api/ideas/' + iid, { method: 'PATCH', body: { title: $('#eT').value, hook: $('#eH').value, angle: $('#eA').value } }); toast('Uložené'); }
async function mkProto(pid, iid) { await saveIdea(iid).catch(() => { }); await api('/api/ideas/' + iid, { method: 'PATCH', body: { status: 'approved' } }); await api('/api/ideas/scripts', { method: 'POST', body: { idea_ids: [iid] } }, 'Claude píše scenár…'); go(`p/${pid}/v/${iid}/prototyp`); }

function sProto(b, { p, src, iid }) {
  if (!src) { b.innerHTML = `<div class="card">${empty('phone', 'Prototyp ešte nie je.')}<div class="row" style="justify-content:center"><button class="btn" onclick="mkProto(${p.id},${iid})">${I('sparkles')}Vytvoriť prototyp</button></div></div>`; return; }
  b.innerHTML = `<div class="proto"><div class="col" style="align-items:center">${phoneHTML()}<div class="row" style="margin-top:10px"><button class="btn sec sm" onclick="voiceOne(${src.id},true)">${I('mic', 's')}${src.voice_path ? 'Nový hlas' : 'Vytvoriť hlas'}</button></div></div>
    <div><div class="card"><h2>${I('type')}Scenár <span class="chip">${langName(src.lang)}</span></h2>
      <label class="l">Názov videa</label><input id="sTitle" value="${esc(src.title)}">
      <label class="l">Text pre hlas</label><textarea id="sVo" style="min-height:150px">${esc(src.voiceover)}</textarea>
      <label class="l">Scény</label><div id="scenes">${src.scenes.map((c, i) => `<div class="scene"><span class="n">${i + 1}</span><textarea class="scV" style="min-height:56px" placeholder="Čo je v zábere">${esc(c.visual)}</textarea><textarea class="scO" style="min-height:56px;font-weight:600" placeholder="Text na obrazovke">${esc(c.onscreen)}</textarea></div>`).join('')}</div>
      <div class="g2"><div><label class="l">Text príspevku</label><input id="sCap" value="${esc(src.caption)}"></div><div><label class="l">Hashtagy</label><input id="sTags" value="${esc(src.hashtags)}"></div></div>
      <label class="l">Popis (YouTube)</label><textarea id="sDesc">${esc(src.description)}</textarea>
      <div class="row" style="margin-top:14px"><button class="btn sec" onclick="saveScript(${src.id})">${I('check')}Uložiť</button><span class="sp"></span>
      <button class="btn" onclick="saveScript(${src.id}).then(()=>go('p/${p.id}/v/${iid}/jazyky'))">Schváliť a ďalej: hlas${I('right')}</button></div></div><div id="qual"></div></div></div>`;
  setupPhone(src, p);
  if (typeof qualityCard === 'function') qualityCard(src.id, iid).catch(() => { });
}
function phoneHTML() { return `<div class="phone" id="phone"><div class="bg"></div><div class="bars"></div><div class="txt"></div><div class="vis"></div><div class="cap"></div><div class="play" id="pplay"><span>${I('play')}</span></div></div>`; }
function setupPhone(s, p) {
  const ph = $('#phone'); if (!ph) return;
  const scenes = s.scenes.length ? s.scenes : [{ onscreen: s.title, visual: '' }];
  const cols = (p.design_colors && p.design_colors.length ? p.design_colors : [p.color || '#FF6B00']);
  $('.bars', ph).innerHTML = scenes.map(() => '<i><b></b></i>').join('');
  $('.cap', ph).textContent = (s.caption || '') + ' ' + (s.hashtags || '');
  let audio = s.voice_path ? new Audio('/api/file?path=' + encodeURIComponent(s.voice_path)) : null, timer, idx = 0, playing = false;
  if (audio) audio.onerror = () => { audio = null; };
  const show = i => {
    const c = cols[i % cols.length];
    $('.bg', ph).style.background = `radial-gradient(120% 80% at 20% 10%, ${c}cc 0%, ${c}33 45%, #000 100%)`;
    const t = $('.txt', ph); t.textContent = scenes[i].onscreen || ''; t.style.animation = 'none'; t.offsetHeight; t.style.animation = '';
    $('.vis', ph).textContent = scenes[i].visual ? 'Záber: ' + scenes[i].visual : ''; $('.vis', ph).style.display = scenes[i].visual ? '' : 'none';
    $$('.bars b', ph).forEach((b, k) => { b.style.transition = 'none'; b.style.width = k < i ? '100%' : '0'; });
  };
  show(0);
  const play = () => {
    const total = (audio && audio.duration) || Math.max(8, (s.voiceover || '').split(/\s+/).length / 2.6);
    const per = total / scenes.length * 1000;
    idx = 0; playing = true; $('#pplay').style.display = 'none';
    if (audio) { audio.currentTime = 0; audio.play(); }
    const stepF = () => {
      if (idx >= scenes.length) { playing = false; $('#pplay').style.display = ''; return; }
      show(idx); const bar = $$('.bars b', ph)[idx]; bar.offsetHeight; bar.style.transition = `width ${per}ms linear`; bar.style.width = '100%';
      idx++; timer = setTimeout(stepF, per);
    };
    stepF();
  };
  $('#pplay').onclick = () => { if (audio && !audio.duration) { const t = setTimeout(() => { audio = null; play(); }, 2500); audio.addEventListener('loadedmetadata', () => { clearTimeout(t); play(); }, { once: true }); audio.load(); } else play(); };
  ph.onclick = e => { if (playing && e.target.closest('#phone') && !e.target.closest('#pplay')) { clearTimeout(timer); audio && audio.pause(); playing = false; $('#pplay').style.display = ''; } };
  window._stopPhone = () => { clearTimeout(timer); audio && audio.pause(); };
}
async function saveScript(id) {
  const body = { title: $('#sTitle').value, voiceover: $('#sVo').value, description: $('#sDesc').value, caption: $('#sCap').value, hashtags: $('#sTags').value };
  await api('/api/scripts/' + id, { method: 'PUT', body }); toast('Uložené');
  if ($('#qual') && typeof qualityCard === 'function') qualityCard(id, R()[3] ? +R()[3] : 0).catch(() => { });
}
async function voiceOne(id, rerender) { const r = await api(`/api/scripts/${id}/voice`, { method: 'POST', body: { fresh: true } }, 'Vytváram hlas…'); toast('Hlas hotový'); voiceNote(r); if (rerender) render(); }

function firstLangOf(p, idea, src) { return idea.first_lang || p.source_lang || src.lang; }
function firstLangSelect(p, idea, src, iid) {
  const cur = firstLangOf(p, idea, src), opts = [...new Set([src.lang, cur, ...p.languages])];
  return `<select style="width:auto" onchange="setFirstLang(${iid},this.value)" title="V akom jazyku urobiť prvú verziu na kontrolu">${opts.map(l => `<option value="${l}" ${l === cur ? 'selected' : ''}>${langName(l)}</option>`).join('')}</select>`;
}
async function setFirstLang(iid, lang) { await api('/api/ideas/' + iid, { method: 'PATCH', body: { first_lang: lang } }); render(); }
function isExpanded(scripts, first) { return scripts.some(s => !s.is_source && s.lang !== first); }
function sLangs(b, { p, scripts, src, iid, idea }) {
  if (!src) return sProto(b, { p, src, iid });
  const first = firstLangOf(p, idea, src);
  if (!isExpanded(scripts, first)) {
    const s = scripts.find(x => x.lang === first), rest = p.languages.filter(l => l !== first).length;
    b.innerHTML = `<div class="card"><div class="row"><h2 style="margin:0">${I('mic')}Prvá verzia</h2><span class="sp"></span>${firstLangSelect(p, idea, src, iid)}</div>
      <p class="small dim" style="margin:6px 0 12px">Najprv dokončíš video v jednom jazyku. Ostatné jazyky${rest ? ` (${rest})` : ''} sa vyrobia až keď budeš spokojný, jedným tlačidlom v kroku Video. Šetrí to čas, preklady aj hlas.</p>
      ${s ? `<div class="lang-row"><div><b>${langName(s.lang)}</b>${s.is_source ? ' <span class="chip acc">originál</span>' : ''}</div>
        <div class="small" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.title)}</div>
        <div class="row">${s.voice_path ? `<audio controls preload="none" src="/api/file?path=${encodeURIComponent(s.voice_path)}"></audio><button class="btn sec sm" onclick="voiceOne(${s.id},true)">${I('refresh', 's')}Nový hlas</button>` : `<button class="btn sm" onclick="voiceOne(${s.id},true)">${I('mic', 's')}Vytvoriť hlas</button>`}
        <button class="btn ghost sm" onclick="editLang(${s.id})" title="Upraviť text">${I('pencil', 's')}</button></div></div>`
      : `<div class="row"><span class="small muted">Scenár je v jazyku ${langName(src.lang)}. Pre ${langName(first)} ho najprv preložím (zadarmo).</span><span class="sp"></span><button class="btn sm" onclick="translateMissing(${src.id},'${first}')">${I('globe', 's')}Preložiť</button></div>`}</div>
    <div class="row" style="margin-top:14px;justify-content:flex-end"><button class="btn" onclick="go('p/${p.id}/v/${iid}/video')">Ďalej: video${I('right')}</button></div>`;
    window._scripts = scripts;
    return;
  }
  const have = Object.fromEntries(scripts.map(s => [s.lang, s]));
  const missing = p.languages.filter(l => !have[l]);
  const noVoice = scripts.filter(s => !s.voice_path).length;
  b.innerHTML = `<div class="card"><div class="row"><h2 style="margin:0">${I('globe')}Jazyky <span class="chip">${p.languages.filter(l => have[l]).length}/${p.languages.length}</span></h2><span class="sp"></span>
    ${missing.length ? `<button class="btn" onclick="produceAll(${iid})">${I('zap')}Dorobiť chýbajúce jazyky (${missing.length})</button>` : ''}
    ${missing.length ? `<button class="btn sec" onclick="translateMissing(${src.id},'${missing.join(',')}')">${I('globe')}Len preložiť (${missing.length})</button>` : ''}
    <button class="btn sec" onclick="voiceAll(${iid})" ${noVoice ? '' : 'disabled'}>${I('mic')}Hlasy pre všetky (${noVoice})</button></div>
    <p class="small dim" style="margin:6px 0 10px">${Object.values(S.meta.mt || {}).some(x => x.enabled) ? 'Preklad robí bezplatný prekladač (0 tokenov), Claude len opraví sporné kúsky.' : 'Preklad robí Claude (lacnejší model). Bezplatný prekladač bez tokenov zapneš v Nastaveniach → Preklady zadarmo.'}</p>
    ${p.languages.map(l => { const s = have[l]; return `<div class="lang-row"><div><b>${langName(l)}</b>${s && s.is_source ? ' <span class="chip acc">originál</span>' : ''}${s && s.qa ? ` <span class="chip" style="color:var(--warn,#f5b000)" title="${esc(Object.entries(JSON.parse(s.qa)).map(([k, v]) => k + ': ' + v).join(', '))}">skontroluj</span>` : ''}</div>
      <div class="small ${s ? '' : 'dim'}" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${s ? esc(s.title) : 'chýba preklad'}</div>
      <div class="row">${s ? `${s.voice_path ? `<audio controls preload="none" src="/api/file?path=${encodeURIComponent(s.voice_path)}"></audio>` : `<button class="btn sec sm" onclick="voiceOne(${s.id},true)">${I('mic', 's')}Hlas</button>`}
        <button class="btn ghost sm" onclick="editLang(${s.id})">${I('pencil', 's')}</button>` : ''}</div></div>`; }).join('')}</div>
  <div class="row" style="margin-top:14px;justify-content:flex-end"><button class="btn" onclick="go('p/${p.id}/v/${iid}/video')">Ďalej: video${I('right')}</button></div>`;
  window._scripts = scripts;
}
function trMsg(r) { if (!r) return ''; let m = `Preložené: ${r.created}`; if (r.machine) m += ` (zadarmo prekladačom: ${r.machine}${r.ai ? `, cez Claude: ${r.ai}` : ''})`; const c = Object.keys(r.check || {}); if (c.length) m += ` · skontroluj: ${c.map(langName).join(', ')}`; return m; }
async function translateMissing(sid, langs) { const r = await api(`/api/scripts/${sid}/translate`, { method: 'POST', body: { script_id: sid, langs: langs.split(',') } }, `Prekladám do ${langs.split(',').length} jazykov…`); toast(trMsg(r)); render(); }
async function produceAll(iid) { const r = await api(`/api/ideas/${iid}/produce-all`, { method: 'POST', body: vOpts() }, 'Rozširujem do ostatných jazykov: preklad → hlas → video… Obraz ostáva rovnaký. (môže to trvať pár minút)'); const e = [...(r.voices?.errors || []), ...(r.videos?.errors || [])]; toast(`${r.translate ? trMsg(r.translate) + ' · ' : ''}Videí: ${r.videos?.created || 0}` + (e.length ? ' · chyby: ' + e.join('; ') : ''), !!e.length); const h = location.hash.slice(2); if (/\/video$/.test(h)) render(); else go(h.replace(/\/(napad|prototyp|jazyky|siete)$/, '') + '/video'); }
async function produceFirst(iid) { const r = await api(`/api/ideas/${iid}/produce-first`, { method: 'POST', body: vOpts() }, 'Robím prvú verziu: hlas → video…'); toast(`Prvá verzia (${langName(r.lang)}) je hotová – pozri si ju`); render(); }
async function voiceAll(iid) { const r = await api(`/api/ideas/${iid}/voice-all?only_missing=1`, { method: 'POST' }, 'Vytváram hlasy…'); toast(`Hlasov: ${r.done}` + (r.errors.length ? ' · chyby: ' + r.errors.join('; ') : ''), !!r.errors.length); voiceNote(r); render(); }
function editLang(sid) {
  const s = window._scripts.find(x => x.id === sid);
  modal(`<h2>${I('pencil')}${langName(s.lang)}</h2>
  <label class="l">Názov</label><input id="sTitle" value="${esc(s.title)}">
  <label class="l">Text pre hlas</label><textarea id="sVo" style="min-height:150px">${esc(s.voiceover)}</textarea>
  <div class="g2"><div><label class="l">Text príspevku</label><input id="sCap" value="${esc(s.caption)}"></div><div><label class="l">Hashtagy</label><input id="sTags" value="${esc(s.hashtags)}"></div></div>
  <label class="l">Popis (YouTube)</label><textarea id="sDesc">${esc(s.description)}</textarea>
  <div class="row" style="margin-top:14px"><button class="btn" onclick="saveScript(${sid}).then(()=>{closeModal();render()})">${I('check')}Uložiť</button><button class="btn sec" onclick="saveScript(${sid}).then(()=>voiceOne(${sid})).then(()=>{closeModal();render()})">${I('mic')}Uložiť a urobiť nový hlas</button></div>`);
}

async function sVideo(b, { p, scripts, src, iid, idea }) {
  if (!src) return sProto(b, { p, src, iid });
  const lib = (await api(`/api/videos?project_id=${p.id}`)).filter(v => !v.script_id);
  const fs = S.meta.footage || {}, ready = fs.pexels || fs.pixabay || fs.own || fs.ai, an = S.meta.anim?.ready;
  const first = firstLangOf(p, idea, src), fsc = scripts.find(s => s.lang === first), fv = fsc && fsc.videos[0];
  const expanded = isExpanded(scripts, first);
  const toDo = p.languages.filter(l => l !== first && !scripts.some(s => s.lang === l && s.videos.length)).length;
  const rowsHTML = scripts.map(s => { const v = s.videos[0]; return `<div class="lang-row" style="grid-template-columns:150px 1fr auto"><div><b>${langName(s.lang)}</b>${s.lang === first ? ' <span class="chip acc">prvá verzia</span>' : ''}</div>
      <div class="row">${v ? `<video src="/api/file?path=${encodeURIComponent(v.file_path)}" preload="metadata" style="height:90px;aspect-ratio:9/16;object-fit:cover" controls></video><span class="small muted">${v.duration ? Math.round(v.duration) + ' s' : ''}${s.videos.length > 1 ? ` · ${s.videos.length} verzie` : ''}</span>` : '<span class="small dim">bez videa</span>'}</div>
      <div class="row"><label class="btn sec sm" style="cursor:pointer">${I('upload', 's')}Vlastné<input type="file" accept="video/*" class="hidden" onchange="attachVid(${s.id},this.files[0])"></label>
      <button class="btn ghost sm" onclick="newSound(${s.id})" title="Nový zvuk: hlas sa nahrá nanovo a video sa zloží znova">${I('mic', 's')}</button>
      <button class="btn ghost sm" onclick="oneVideo(${s.id})" title="Vytvoriť znova">${I('refresh', 's')}</button></div></div>`; }).join('');
  b.innerHTML = `<div class="card"><div class="row"><h2 style="margin:0">${I('film')}1. Prvá verzia</h2><span class="sp"></span>${expanded ? `<span class="chip">${langName(first)}</span>` : firstLangSelect(p, idea, src, iid)}</div>
    <div class="g2" style="align-items:end;margin-top:10px"><div><label class="l">Štýl videa</label><select id="vStyle" onchange="$('#baseWrap').style.display=this.value==='base'?'':'none';$('#shotsWrap').style.display=this.value==='broll'?'':'none'">
      <option value="explainer" ${an ? 'selected' : ''}>Animované schémy ako N2N Akadémia (odporúčam)</option>
      <option value="broll" ${!an && ready ? 'selected' : ''}>Zábery z internetu + titulky</option><option value="color" ${!an && !ready ? 'selected' : ''}>Farby dizajnu + texty</option><option value="base">Moje podkladové video + hlas</option></select></div>
    <div id="baseWrap" style="display:none"><label class="l">Podkladové video</label><select id="baseVid"><option value="">—</option>${lib.map(v => `<option value="${v.id}">${esc(v.title || v.original_name)}</option>`).join('')}</select></div></div>
    ${an ? '' : `<div class="hint" style="margin-top:12px">${I('alert')}<div>Animácie sa pripravujú na pozadí (stiahne sa raz, pár minút). Potom daj „Vytvoriť znova“.</div></div>`}
    ${ready || an ? '' : `<div class="hint" style="margin-top:12px">${I('alert')}<div>Na zábery zadaj bezplatný kľúč Pexels v <a href="#/nastavenia">Nastaveniach → Zábery a hudba</a>, alebo daj svoje zábery do priečinka Moje zábery.</div></div>`}
    ${fv ? `<div class="row" style="margin-top:14px;align-items:flex-start"><video src="/api/file?path=${encodeURIComponent(fv.file_path)}" preload="metadata" controls style="height:420px;max-height:70vh;aspect-ratio:9/16;object-fit:cover;border-radius:12px;background:#000"></video>
      <div class="col" style="gap:8px"><span class="small muted">${langName(first)}${fv.duration ? ' · ' + Math.round(fv.duration) + ' s' : ''}</span>
      <button class="btn sec sm" onclick="produceFirst(${iid})">${I('refresh', 's')}Vytvoriť znova</button>
      ${fsc ? `<button class="btn sec sm" onclick="newSound(${fsc.id})" title="Hlas sa nahrá nanovo (povie to trochu inak) a video sa zloží znova. Obraz ostáva rovnaký.">${I('mic', 's')}Nový zvuk</button>` : ''}
      <button class="btn ghost sm" onclick="go('p/${p.id}/v/${iid}/prototyp')">${I('pencil', 's')}Upraviť scenár</button>
      ${fsc ? `<label class="btn ghost sm" style="cursor:pointer">${I('upload', 's')}Nahrať vlastné<input type="file" accept="video/*" class="hidden" onchange="attachVid(${fsc.id},this.files[0])"></label>` : ''}</div></div>`
      : `<div class="row" style="margin-top:14px"><button class="btn" onclick="produceFirst(${iid})">${I('film')}Vytvoriť video (${langName(first)})</button><span class="small dim">Urobí hlas a video len v tomto jazyku, aby si si ho mohol pozrieť.</span></div>`}</div>
  <div class="card" id="shotsWrap" style="${ready && !an ? '' : 'display:none'}"><div class="row"><h2 style="margin:0">${I('film')}Zábery po scénach</h2><span class="sp"></span><button class="btn sec sm" onclick="shotsPick(${iid})">${I('refresh', 's')}Vybrať zábery</button></div>
    <p class="small dim">Rovnaké zábery sa použijú vo všetkých jazykoch. Nepáči sa ti záber? Zmeň slová, daj „Vymeniť“ a potom „Vytvoriť znova“.</p><div id="shotsBox" class="small dim">Načítavam…</div></div>
  <div class="card"><h2>${I('globe')}2. Rozšíriť do ostatných jazykov</h2>
    ${toDo ? `<p class="muted">${fv ? 'Páči sa ti video? Appka ho preloží' : 'Najprv si pozri prvú verziu. Potom ju appka preloží'} do ďalších ${toDo} jazykov a použije ten istý obraz. Mení sa len text, titulky a hlas.</p>
      <button class="btn" onclick="produceAll(${iid})" ${fv ? '' : 'disabled'}>${I('zap')}Rozšíriť do všetkých jazykov (${toDo})</button>`
      : `<p class="muted">${p.languages.length > 1 || expanded ? 'Všetky jazyky projektu majú video.' : 'Projekt nemá ďalšie jazyky.'}</p>`}
    ${expanded ? `<div style="margin-top:14px">${rowsHTML}</div><div class="row" style="margin-top:10px"><button class="btn ghost sm" onclick="if(confirm('Vytvoriť znova videá vo všetkých jazykoch?'))videosAll(${iid})">${I('refresh', 's')}Vytvoriť znova všetky</button></div>` : ''}</div>
  <div class="row" style="margin-top:14px;justify-content:flex-end"><button class="btn" onclick="go('p/${p.id}/v/${iid}/siete')">Ďalej: siete${I('right')}</button></div>`;
  loadShots(iid);
}
function vOpts() { if (!$('#vStyle')) return {}; const st = $('#vStyle').value, base = $('#baseVid')?.value; return st === 'base' && base ? { style: 'base', base_video_id: +base } : { style: st === 'base' ? 'color' : st }; }
async function loadShots(iid) {
  const box = $('#shotsBox'); if (!box) return;
  const d = await api(`/api/ideas/${iid}/shots`);
  if (!d.scenes.some(sc => sc.shots.length)) { box.innerHTML = 'Zábery ešte nie sú vybrané – vyberú sa samé pri vytvorení videa, alebo klikni „Vybrať zábery“.'; return; }
  box.innerHTML = d.scenes.map((sc, i) => `<div class="vrow" style="align-items:center;flex-wrap:wrap"><b style="min-width:22px">${i + 1}.</b>
    ${sc.shots.map(f => f.kind === 'photo' ? `<img src="/api/file?path=${encodeURIComponent(f.path)}" style="height:96px;aspect-ratio:9/16;object-fit:cover;border-radius:8px">` : `<video src="/api/file?path=${encodeURIComponent(f.path)}#t=1" muted preload="metadata" style="height:96px;aspect-ratio:9/16;object-fit:cover;border-radius:8px" onmouseenter="this.play()" onmouseleave="this.pause()"></video>`).join('') || '<span class="dim">nič</span>'}
    <div style="flex:1;min-width:180px"><div class="small muted">${esc(sc.onscreen || '')}</div><div class="row" style="margin-top:6px"><input id="sq${i}" value="${esc(sc.q)}" style="flex:1"><button class="btn sec sm" onclick="shotSwap(${iid},${i})">${I('refresh', 's')}Vymeniť</button></div></div></div>`).join('') + '<p class="small dim" style="margin-top:8px">Zábery: Pexels, Pixabay (bezplatná licencia) a tvoje vlastné.</p>';
}
async function shotsPick(iid) { await api(`/api/ideas/${iid}/shots`, { method: 'POST', body: {} }, 'Hľadám zábery…'); loadShots(iid); }
async function shotSwap(iid, i) { await api(`/api/ideas/${iid}/shots`, { method: 'POST', body: { scene: i, q: $('#sq' + i).value } }, 'Hľadám iný záber…'); loadShots(iid); }
async function videosAll(iid) { const r = await api(`/api/ideas/${iid}/videos-all`, { method: 'POST', body: vOpts() }, 'Vytváram hlasy a videá… (pár minút)'); toast(`Hotových ${r.created} videí` + (r.errors.length ? ' · chyby: ' + r.errors.join('; ') : ''), !!r.errors.length); render(); }
async function newSound(sid) { await api(`/api/scripts/${sid}/to-video`, { method: 'POST', body: { ...vOpts(), new_voice: true } }, 'Nahrávam hlas nanovo a skladám video…'); toast('Nový zvuk je hotový'); render(); }
async function oneVideo(sid) { await api(`/api/scripts/${sid}/to-video`, { method: 'POST', body: vOpts() }, 'Vytváram video…'); render(); }
async function attachVid(sid, f) { if (!f) return; const fd = new FormData(); fd.append('file', f); await api(`/api/scripts/${sid}/attach-video`, { method: 'POST', body: fd }, 'Nahrávam video…'); toast('Video pridané'); render(); }

async function sSocial(b, { p, scripts, src, iid }) {
  if (!src) return sProto(b, { p, src, iid });
  scripts = scripts.filter(s => p.languages.includes(s.lang));
  const accs = await api('/api/accounts');
  const plats = p.platforms.length ? p.platforms : PLATS;
  const accFor = (pl, lang) => accs.filter(a => a.platform === pl && (!a.project_id || a.project_id === p.id) && (!a.lang || a.lang === lang));
  const cell = (s, pl) => {
    const ps = s.posts.filter(x => x.platform === pl);
    const n = accFor(pl, s.lang).length;
    if (ps.some(x => x.status === 'done')) { const u = ps.find(x => x.url && x.url.startsWith('http')); return `<a class="cell ok" ${u ? `href="${esc(u.url)}" target="_blank"` : ''} title="Zverejnené">${I('check', 's')}</a>`; }
    if (ps.some(x => x.status === 'failed')) return `<span class="cell bad" title="${esc(ps.find(x => x.status === 'failed').error)}">${I('alert', 's')}</span>`;
    if (ps.length) return `<span class="cell q" title="${esc(ps[0].scheduled_at)}">${I('clock', 's')}</span>`;
    return n ? `<span class="cell" title="${n} účet(y), zatiaľ nič">–</span>` : `<span class="cell" title="Žiadny účet pre tento jazyk" style="opacity:.35">${I('x', 's')}</span>`;
  };
  const now = new Date(Date.now() + 5 * 60000), local = new Date(now - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  b.innerHTML = `<div class="card"><h2>${I('layers')}Jazyky × siete</h2>
    <table class="mx"><tr><th>Jazyk</th><th>Video</th>${plats.map(x => `<th>${plat(x, false)}</th>`).join('')}</tr>
    ${scripts.map(s => `<tr><td><label class="row"><input type="checkbox" class="pubL" value="${s.lang}" ${s.videos.length ? 'checked' : 'disabled'}><b>${langName(s.lang)}</b></label></td>
      <td>${s.videos.length ? `<span class="cell ok">${I('film', 's')}</span>` : `<span class="cell" style="opacity:.35">${I('x', 's')}</span>`}</td>${plats.map(x => `<td>${cell(s, x)}</td>`).join('')}</tr>`).join('')}</table>
    <p class="small dim" style="margin-top:10px">${I('x', 's')} = pre daný jazyk nie je pripojený účet. Účty a ich krajiny nastavíš v <a href="#/p/${p.id}/ucty">Účty a siete</a>.</p></div>
  <div class="card"><h2>${I('calendar')}Naplánovať</h2>
    <label class="l">Kam</label><div class="pick">${plats.map(x => `<label><input type="checkbox" name="pp" value="${x}" checked>${I(x, 's')}${PL[x]}</label>`).join('')}</div>
    <div class="g3"><div><label class="l">Kedy začať</label><input type="datetime-local" id="sStart" value="${local}"></div>
    <div><label class="l">Časy publikovania</label><input id="sTimes" value="09:00, 13:00, 18:00"></div>
    <div><label class="l">Viditeľnosť</label><select id="sPriv"><option value="public">Verejné</option><option value="unlisted">Nezaradené (YouTube)</option><option value="private">Súkromné</option></select></div></div>
    <div class="row" style="margin-top:16px"><button class="btn" onclick="pubIdea(${iid},false)">${I('calendar')}Naplánovať</button><button class="btn sec" onclick="pubIdea(${iid},true)">${I('send')}Zverejniť hneď</button></div></div>`;
}
async function pubIdea(iid, now) {
  const body = { langs: $$('.pubL:checked').map(c => c.value), platforms: $$('[name=pp]:checked').map(c => c.value), start: $('#sStart').value, times: $('#sTimes').value.split(',').map(s => s.trim()).filter(Boolean), privacy: $('#sPriv').value, now };
  body.per_day = body.times.length;
  const r = await api(`/api/ideas/${iid}/publish`, { method: 'POST', body });
  toast(`Naplánovaných ${r.created} publikovaní` + (r.skipped.length ? ` · ${r.skipped.length} bez účtu` : ''), !r.created); render();
}

// ---------- knižnica ----------
async function tLibrary(b, p) {
  const vids = await api(`/api/videos?project_id=${p.id}&lang=${S.vLang || ''}`);
  b.innerHTML = `<div class="g2" style="margin-bottom:14px">
    <div class="drop" id="drop">${I('upload', 'l')}<div style="margin-top:6px">Pretiahni sem videá (aj veľa naraz)</div><div class="small dim">jazyk sa spozná z názvu, napr. recept_de.mp4</div><input type="file" id="fileIn" multiple accept="video/*" class="hidden"></div>
    <div class="card"><h3>${I('folder', 's')} Pridať celý priečinok</h3><p class="small muted">Videá sa nekopírujú, šetrí to miesto. Podpriečinky s kódom jazyka (/de/, /pl/) sa rozpoznajú.</p>
      <div class="row"><input id="folder" placeholder="/Users/meno/Videa/Projekt" style="flex:1"><button class="btn sec" onclick="importFolder(${p.id})">Pridať</button></div></div></div>
  <div class="card"><div class="row" style="margin-bottom:10px"><h2 style="margin:0">${I('library')}Videá <span class="chip">${vids.length}</span></h2><span class="sp"></span>
    <select style="width:auto" onchange="S.vLang=this.value;render()"><option value="">Všetky jazyky</option>${p.languages.map(l => `<option value="${l}" ${S.vLang === l ? 'selected' : ''}>${langName(l)}</option>`).join('')}</select>
    <button class="btn sm" onclick="scheduleDialog(${p.id})">${I('calendar', 's')}Naplánovať vybrané</button><button class="btn sec sm" onclick="bulkAI()">${I('sparkles', 's')}AI popisy</button><button class="btn sec sm" onclick="bulkLang()">${I('globe', 's')}Jazyk</button><button class="btn bad sm" onclick="bulkDel()">${I('trash', 's')}</button></div>
  ${vids.length ? `<table><tr><th style="width:30px"><input type="checkbox" onclick="$$('.vchk').forEach(c=>c.checked=this.checked)"></th><th>Video</th><th>Jazyk</th><th>Dĺžka</th><th>Siete</th><th></th></tr>
  ${vids.map(v => `<tr><td><input type="checkbox" class="vchk" value="${v.id}"></td><td><b>${esc(v.title || v.original_name)}</b><div class="small dim">${esc(v.original_name)} · ${(v.size / 1048576).toFixed(1)} MB</div></td>
    <td>${langName(v.lang)}</td><td class="muted">${v.duration ? Math.round(v.duration) + ' s' : '—'}</td>
    <td>${(v.posts || '').split(',').filter(Boolean).map(x => { const [pl, st] = x.split(':'); return `<span class="chip ${ST[st]?.[1]}">${I(pl, 's')}</span>`; }).join(' ') || '<span class="dim small">—</span>'}</td>
    <td><button class="btn ghost sm" onclick="editVideo(${v.id})">${I('pencil', 's')}</button></td></tr>`).join('')}</table>` : empty('film', 'Knižnica je prázdna.')}</div>`;
  const drop = $('#drop'), fin = $('#fileIn');
  drop.onclick = () => fin.click();
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
  drop.ondragleave = () => drop.classList.remove('over');
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over'); uploadFiles(p.id, e.dataTransfer.files); };
  fin.onchange = () => uploadFiles(p.id, fin.files);
  S.vids = vids;
}
async function uploadFiles(pid, files) { const fd = new FormData(); fd.append('project_id', pid); fd.append('lang', S.vLang || ''); [...files].forEach(f => fd.append('files', f)); const r = await api('/api/videos/upload', { method: 'POST', body: fd }, `Nahrávam ${files.length} videí…`); toast(`Pridaných ${r.created} videí`); render(); }
async function importFolder(pid) { const r = await api('/api/videos/import-folder', { method: 'POST', body: { path: $('#folder').value, project_id: pid } }, 'Pridávam videá…'); toast(`Pridaných ${r.created} videí`); render(); }
const selVids = () => $$('.vchk:checked').map(c => +c.value);
async function bulkDel() { const ids = selVids(); if (!ids.length || !confirm(`Zmazať ${ids.length} videí?`)) return; await api('/api/videos/bulk', { method: 'POST', body: { action: 'delete', ids } }); render(); }
function bulkLang() { const ids = selVids(); if (!ids.length) return toast('Vyber videá', true); modal(`<h2>${I('globe')}Jazyk pre ${ids.length} videí</h2><select id="bl">${S.meta.languages.map(l => `<option value="${l.code}">${l.name}</option>`).join('')}</select><button class="btn" style="margin-top:14px" onclick="api('/api/videos/bulk',{method:'POST',body:{action:'set',ids:[${ids}],fields:{lang:$('#bl').value}}}).then(()=>{closeModal();render()})">${I('check')}Uložiť</button>`); }
function bulkAI() { const ids = selVids(); if (!ids.length) return toast('Vyber videá', true); modal(`<h2>${I('sparkles')}AI názvy a popisy (${ids.length})</h2><label class="l">O čom sú videá</label><textarea id="about"></textarea><button class="btn" style="margin-top:14px" onclick="runBulkAI([${ids}])">${I('sparkles')}Vytvoriť</button>`); }
async function runBulkAI(ids) { const about = $('#about').value; closeModal(); await api('/api/videos/bulk', { method: 'POST', body: { action: 'ai-meta', ids, about } }, 'AI píše názvy a popisy…'); render(); }
function editVideo(id) {
  const v = S.vids.find(x => x.id === id);
  modal(`<h2>${I('pencil')}Upraviť video</h2><div class="g2"><video src="/api/file?path=${encodeURIComponent(v.file_path)}" controls style="width:100%;max-height:360px"></video><div>
  <label class="l" style="margin-top:0">Názov</label><input id="vT" value="${esc(v.title)}"><label class="l">Text príspevku</label><input id="vC" value="${esc(v.caption)}">
  <label class="l">Hashtagy</label><input id="vH" value="${esc(v.hashtags)}"><label class="l">Jazyk</label><select id="vL"><option value="">—</option>${S.meta.languages.map(l => `<option value="${l.code}" ${l.code === v.lang ? 'selected' : ''}>${l.name}</option>`).join('')}</select></div></div>
  <label class="l">Popis (YouTube)</label><textarea id="vD">${esc(v.description)}</textarea>
  <button class="btn" style="margin-top:14px" onclick="saveVideo(${id})">${I('check')}Uložiť</button>`);
}
async function saveVideo(id) { await api('/api/videos/' + id, { method: 'PUT', body: { title: $('#vT').value, description: $('#vD').value, caption: $('#vC').value, hashtags: $('#vH').value, lang: $('#vL').value } }); closeModal(); render(); }
function scheduleDialog(pid) {
  const ids = selVids(); if (!ids.length) return toast('Najprv zaškrtni videá', true);
  const p = S.projects.find(x => x.id === pid);
  const now = new Date(Date.now() + 5 * 60000), local = new Date(now - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  modal(`<h2>${I('calendar')}Naplánovať ${ids.length} videí</h2><p class="muted small">Každé video pôjde na účty s rovnakým jazykom.</p>
  <label class="l">Kam</label><div class="pick">${(p.platforms.length ? p.platforms : PLATS).map(x => `<label><input type="checkbox" name="pp" value="${x}" checked>${I(x, 's')}${PL[x]}</label>`).join('')}</div>
  <div class="g2"><div><label class="l">Kedy začať</label><input type="datetime-local" id="sStart" value="${local}"></div><div><label class="l">Časy (max toľko videí denne na účet)</label><input id="sTimes" value="09:00, 13:00, 18:00"></div></div>
  <label class="l">Viditeľnosť</label><select id="sPriv"><option value="public">Verejné</option><option value="unlisted">Nezaradené (YouTube)</option><option value="private">Súkromné</option></select>
  <div class="row" style="margin-top:16px"><button class="btn" onclick="doSchedule([${ids}],false)">${I('calendar')}Naplánovať</button><button class="btn sec" onclick="doSchedule([${ids}],true)">${I('send')}Hneď</button></div>`);
}
async function doSchedule(ids, now) {
  const times = $('#sTimes').value.split(',').map(s => s.trim()).filter(Boolean);
  const r = await api('/api/posts/schedule', { method: 'POST', body: { video_ids: ids, platforms: $$('[name=pp]:checked').map(c => c.value), start: $('#sStart').value, times, per_day: times.length, privacy: $('#sPriv').value, now } });
  closeModal(); toast(`Naplánovaných ${r.created}` + (r.review ? ' · čakajú na tvoje schválenie v Kontrole' : '') + (r.skipped.length ? ` · ${r.skipped.length} videí nemá účet` : ''), !r.created); render();
}

// ================= KONTROLA PRED ZVEREJNENÍM =================
async function pReview(m) {
  const groups = (await api('/api/review')).filter(g => !S.pf || g.project_id === S.pf);
  const total = groups.reduce((a, g) => a + g.posts, 0);
  m.innerHTML = `<div class="top"><div>${pTitle('Kontrola')}<p class="sub">Pozri si video a pusti ho von jedným klikom – naraz vo všetkých jazykoch a na všetkých účtoch.</p></div>
    ${groups.length ? `<button class="btn" onclick="revApprove(${S.pf ? `[${groups.map(g => `'${g.key}'`).join(',')}]` : `'all'`})">${I('check')}Schváliť všetko (${groups.length})</button>` : ''}</div>
  ${groups.length ? groups.map((g, gi) => { const proj = S.projects.find(p => p.id === g.project_id) || {}; const L = g.langs[0]; return `<div class="card rev" style="margin-bottom:14px">
    <div class="rev-v"><video id="rv${gi}" src="/api/file?path=${encodeURIComponent(L.file)}" controls playsinline preload="metadata"></video></div>
    <div class="rev-b"><div class="small dim"><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${proj.color || '#666'};margin-right:6px"></span>${esc(proj.name || '')} · od ${esc(g.first.slice(0, 16).replace('T', ' '))}</div>
      <h2 style="margin:6px 0 4px">${esc(g.title)}</h2>
      <div class="small muted">${g.langs.length} ${g.langs.length === 1 ? 'jazyk' : g.langs.length < 5 ? 'jazyky' : 'jazykov'} · ${g.accounts} ${g.accounts === 1 ? 'účet' : g.accounts < 5 ? 'účty' : 'účtov'} · ${g.platforms.map(x => I(x, 's')).join(' ')} · spolu ${g.posts} zverejnení</div>
      <div class="pick" style="margin:12px 0">${g.langs.map((l, li) => `<label class="${li ? '' : 'on'}" onclick="revLang(${gi},${li},this)" style="cursor:pointer">${esc(langName(l.lang))}${l.source ? ' ★' : ''}</label>`).join('')}</div>
      <div id="rc${gi}" class="small" style="${L.caption || L.hashtags ? "" : "display:none;"}white-space:pre-wrap;background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px;max-height:140px;overflow:auto">${esc((L.caption || '') + (L.hashtags ? '\n' + L.hashtags : ''))}</div>
      <div class="row" style="margin-top:14px"><button class="btn" onclick="revApprove(['${g.key}'])">${I('check')}Schváliť a pustiť</button><button class="btn sec" onclick="revReject('${g.key}')">${I('x')}Vrátiť na úpravu</button></div>
    </div></div>`; }).join('') : `<div class="card empty">${I('check', 'l')}<p>Nič nečaká na schválenie.</p><p class="small dim">Keď naplánuješ videá, objavia sa tu. Kým ich neschváliš, nikam sa neodošlú.</p></div>`}`;
  window._rev = groups;
}
function revLang(gi, li, el) { const l = window._rev[gi].langs[li]; $('#rv' + gi).src = '/api/file?path=' + encodeURIComponent(l.file); $('#rc' + gi).style.display = (l.caption || l.hashtags) ? '' : 'none'; $('#rc' + gi).textContent = (l.caption || '') + (l.hashtags ? '\n' + l.hashtags : ''); el.parentNode.querySelectorAll('label').forEach(x => x.classList.remove('on')); el.classList.add('on'); }
async function revApprove(keys) { const r = await api('/api/review/approve', { method: 'POST', body: { keys } }); toast(`Schválené: ${r.approved} zverejnení ide von`); S.meta = await api('/api/meta'); render(); }
async function revReject(key) { if (!confirm('Zrušiť naplánovanie tohto videa vo všetkých jazykoch? Videá ostanú, po oprave ich naplánuješ znova.')) return; const r = await api('/api/review/reject', { method: 'POST', body: { keys: [key] } }); toast(`Vrátené (${r.rejected})`); S.meta = await api('/api/meta'); render(); }

// ================= PUBLIKOVANIE =================
async function pCalendar(m) {
  const f = new URLSearchParams(location.hash.split('?')[1] || '').get('f') ?? 'queued';
  const posts = (await api('/api/posts?status=' + f)).filter(p => !S.pf || p.project_id === S.pf);
  const paused = S.meta.settings.paused;
  const days = {}; posts.forEach(p => (days[p.scheduled_at.slice(0, 10)] ||= []).push(p));
  const dn = d => new Date(d + 'T12:00').toLocaleDateString('sk', { weekday: 'long', day: 'numeric', month: 'long' });
  m.innerHTML = `<div class="top"><div>${pTitle('Publikovanie')}<p class="sub">Appka nahráva videá sama v naplánovaný čas, keď je zapnutá. Pri chybe to skúsi ešte 2×.</p></div><span class="sp"></span>
    <button class="btn" onclick="planDialog()">${I('calendar')}Naplánovať týždeň</button>
    <button class="btn ${paused ? '' : 'sec'}" onclick="api('/api/settings',{method:'POST',body:{paused:${!paused}}}).then(render)">${I(paused ? 'play' : 'pause')}${paused ? 'Spustiť plánovač' : 'Pozastaviť'}</button></div>
  <div class="seg" style="margin-bottom:16px">${[['review', 'Na schválenie'], ['queued', 'Naplánované'], ['uploading', 'Nahráva sa'], ['done', 'Zverejnené'], ['failed', 'Chyby'], ['', 'Všetko']].map(([k, n]) => `<button class="${f === k ? 'on' : ''}" onclick="location.hash=here()+'?f=${k}'">${n}</button>`).join('')}</div>
  ${Object.keys(days).length ? Object.entries(days).map(([d, list]) => `<div class="card"><h2>${I('calendar', 's')}${dn(d)} <span class="chip">${list.length}</span></h2><table>${list.map(p => `<tr>
    <td style="width:60px" class="muted">${p.scheduled_at.slice(11, 16)}</td><td style="width:150px">${plat(p.platform)}<div class="small dim">${esc(p.account_name)}</div></td>
    <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${p.color || '#666'};margin-right:6px"></span>${esc(p.title || p.original_name)} <span class="chip">${esc((p.lang || '').toUpperCase())}</span>${p.error ? `<div class="small ${p.status === 'failed' ? 'bad-t' : 'dim'}">${esc(p.error.slice(0, 260))}</div>` : ''}${p.url && !p.url.startsWith('http') ? `<div class="small muted">${esc(p.url)}</div>` : ''}</td>
    <td style="text-align:right;white-space:nowrap"><span class="chip ${ST[p.status][1]}">${ST[p.status][0]}</span>
      ${p.url && p.url.startsWith('http') ? `<a class="btn ghost sm" href="${esc(p.url)}" target="_blank">${I('ext', 's')}</a>` : ''}
      ${p.status === 'queued' || p.status === 'failed' ? `<button class="btn ghost sm" title="Teraz" onclick="api('/api/posts/${p.id}/retry',{method:'POST'}).then(render)">${I('send', 's')}</button>` : ''}
      ${p.status !== 'uploading' ? `<button class="btn ghost sm" title="Zmazať" onclick="api('/api/posts/${p.id}',{method:'DELETE'}).then(render)">${I('trash', 's')}</button>` : ''}</td></tr>`).join('')}</table></div>`).join('') : `<div class="card">${empty('calendar', 'Prázdne.')}</div>`}`;
}

// ================= ÚČTY =================
async function pAccounts(m) {
  const all = await api('/api/accounts'), pid = S.pf, accs = all.filter(a => a.project_id === pid);
  api('/api/connect-project', { method: 'POST', body: { project_id: pid } }); // nové účty pôjdu do tohto projektu
  const h = S.meta.has, st = S.meta.settings;
  const c = (icon, title, body) => `<div class="card"><h2>${I(icon)}${title}</h2>${body}</div>`;
  const ok = '<span class="chip ok">' + I('check', 's') + 'uložené</span>';
  m.innerHTML = `<div class="top"><div>${pTitle('Účty a siete')}<p class="sub">Účty tohto projektu. Novo pripojené účty sa pridajú sem. Pri každom nastav krajinu. Jazyk videí sa doplní sám podľa krajiny (pri Švajčiarsku, Belgicku a Luxembursku si ho vyber). Jedno video v jazyku pôjde na účty všetkých krajín s týmto jazykom.</p></div></div>
  <div class="card" style="margin-bottom:14px"><div class="row"><h2 style="margin:0">${I('link')}Pripojené účty <span class="chip">${accs.length}</span></h2><span class="sp"></span>
    ${PLATS.filter(x => accs.some(a => a.platform === x)).map(x => `<span class="chip">${I(x, 's')}${accs.filter(a => a.platform === x).length}</span>`).join('')}</div>
    ${accs.length ? `<div class="row" style="margin:12px 0"><input id="accQ" placeholder="Hľadať účet…" style="flex:1;min-width:160px" oninput="accFilter()">
      <select id="accPf" onchange="accFilter()" style="max-width:170px"><option value="">Všetky siete</option>${PLATS.map(x => `<option value="${x}">${PL[x]}</option>`).join('')}</select>
</div>
    <div class="row small" style="margin-bottom:8px;gap:8px"><span class="dim">Označeným:</span><select id="bkP" style="max-width:200px"><option value="">presunúť do projektu…</option>${S.projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('')}</select>
      <select id="bkC" style="max-width:190px"><option value="">krajina…</option>${S.meta.countries.map(c => `<option value="${c.code}">${c.name}</option>`).join('')}</select><select id="bkL" style="max-width:180px"><option value="">jazyk…</option><option value="-">Všetky jazyky</option>${S.meta.languages.map(l => `<option value="${l.code}">${l.name}</option>`).join('')}</select><button class="btn sec sm" onclick="accBulk()">${I('check', 's')}Nastaviť</button></div>
    <table id="accT"><tr><th><input type="checkbox" onchange="$$('#accT tr:not([hidden]) .aS').forEach(c=>c.checked=this.checked)"></th><th>Sieť</th><th>Účet</th><th>Projekt</th><th>Krajina</th><th>Jazyk videí</th><th></th></tr>${accs.map(a => `<tr data-pf="${a.platform}" data-pr="${a.project_id || 0}" data-n="${esc((a.name || '').toLowerCase())}">
    <td><input type="checkbox" class="aS" value="${a.id}"></td><td>${plat(a.platform)}</td><td><input value="${esc(a.name)}" onchange="api('/api/accounts/${a.id}',{method:'PUT',body:{name:this.value}}).then(()=>toast('Uložené'))">${a.days_left !== null && a.days_left !== undefined && a.days_left <= 10 ? `<div class="small" style="margin-top:4px"><span class="${a.days_left <= 3 ? 'bad-t' : ''}" style="color:${a.days_left <= 3 ? '' : 'var(--acc)'}">${a.days_left ? `Prihlásenie vyprší o ${a.days_left} ${a.days_left === 1 ? 'deň' : a.days_left < 5 ? 'dni' : 'dní'}` : 'Prihlásenie vypršalo'}</span> <a class="btn sm" href="/api/accounts/linkedin/connect${a.org ? '?org=1' : ''}">${I('refresh', 's')}Prihlásiť znova</a></div>` : ''}</td>
    <td><select class="aP" onchange="accSet(${a.id},this.closest('tr'))">${S.projects.map(p => `<option value="${p.id}" ${p.id === a.project_id ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}</select></td>
    <td><select class="aC" onchange="accCountry(${a.id},this.value)"><option value="">krajina…</option>${S.meta.countries.map(c => `<option value="${c.code}" ${c.code === a.country ? 'selected' : ''}>${c.name}</option>`).join('')}</select></td>
    <td><select class="aL" onchange="accSet(${a.id},this.closest('tr'))"><option value="">Všetky jazyky</option>${S.meta.languages.map(l => `<option value="${l.code}" ${l.code === a.lang ? 'selected' : ''}>${l.name}</option>`).join('')}</select></td>
    <td><button class="btn ghost sm" onclick="if(confirm('Odpojiť účet?'))api('/api/accounts/${a.id}',{method:'DELETE'}).then(render)">${I('trash', 's')}</button></td></tr>`).join('')}</table>` : empty('link', 'Zatiaľ žiadne. Pripoj ich nižšie.')}</div>
  <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr))">
  ${c('youtube', 'YouTube', `<p class="small muted">1) Nahraj JSON z Google Cloud (OAuth klient „Desktop app“). 2) Klikni Pripojiť kanál a v Google okne vyber kanál. Pre ďalší kanál klikni znova – aj keď sú všetky pod jedným Google účtom, Google ti ponúkne na výber každý kanál zvlášť.</p>
    ${(S.meta.yt_usage || []).length ? `<table class="small">${S.meta.yt_usage.map(u => `<tr><td>Google projekt ${u.n}</td><td>${u.channels} kanálov</td><td>dnes ${u.today}/${u.limit} nahratí</td></tr>`).join('')}</table>` : ''}
    <input type="file" id="ytJson" accept=".json" style="margin:8px 0"><div class="row"><button class="btn sec sm" onclick="uploadYt()">${I('upload', 's')}${h.yt_client ? 'Pridať ďalší Google projekt' : 'Nahrať JSON'}</button><a class="btn sm" href="/api/accounts/youtube/connect">${I('link', 's')}Pripojiť kanál</a></div>
    <p class="small dim">Jeden Google projekt zvládne cca 100 nahratí denne. Pri 40 kanáloch a 1–2 videách denne stačí jeden, pri viac pridaj druhý (rovnaký postup, nový projekt v Google Cloud) – nové kanály sa rozložia samé. Keď sa limit minie, video počká do rána.</p>`)}
  ${c('facebook', 'Facebook + Instagram', `<p class="small muted">Vlož System User token z Meta Business. Appka sama načíta všetky stránky aj prepojené Instagram účty. Na odpisovanie na správy musí mať token aj práva pages_messaging, pages_manage_metadata a instagram_manage_messages.</p>
    <textarea id="metaTok" placeholder="EAAG…" style="min-height:70px"></textarea><button class="btn sm" style="margin-top:8px" onclick="connectMeta()">${I('link', 's')}Pripojiť</button> <button class="btn sec sm" style="margin-top:8px" onclick="refreshMeta()">Načítať nové stránky</button>`)}
  ${c('tiktok', 'TikTok – veľa účtov', `<p class="small muted">Business API: verejne na tvoje vlastné účty (aj 50+). Potrebuje verejnú adresu v Nastaveniach.</p>${h.ttb_creds ? ok : ''}
    <input id="ttbId" placeholder="App ID" style="margin:6px 0"><input id="ttbSec" placeholder="Secret" type="password">
    <p class="small dim">Redirect URL: <code>${esc(S.meta.ttb_redirect)}</code></p>
    <div class="row"><button class="btn sec sm" onclick="saveTtb()">Uložiť</button><a class="btn sm" href="/api/accounts/ttb/connect">${I('link', 's')}Pripojiť účet</a></div>
    <details style="margin-top:10px"><summary>Presmerovanie neprešlo?</summary><input id="ttbUrl" placeholder="Vlož adresu, kde si skončil" style="margin-top:8px"><button class="btn sec sm" style="margin-top:6px" onclick="pasteTtb()">Pripojiť z adresy</button></details>
    <p class="small dim">Pre ďalší účet sa v TikToku prihlás do iného účtu a klikni Pripojiť znova.</p>`)}
  ${c('tiktok', 'TikTok – koncepty (záloha)', `<p class="small muted">Video príde ako koncept do TikTok appky, zverejníš ho v mobile. Nepotrebuje verejnú adresu.</p>${h.tt_creds ? ok : ''}
    <input id="ttKey" placeholder="Client key" style="margin:6px 0"><input id="ttSec" placeholder="Client secret" type="password">
    <select id="ttMode" style="margin-top:6px"><option value="inbox" ${st.tt_mode === 'inbox' ? 'selected' : ''}>Koncept do appky</option><option value="direct" ${st.tt_mode === 'direct' ? 'selected' : ''}>Priamo (po schválení TikTokom)</option></select>
    <p class="small dim">Redirect URI: <code>http://localhost:8765/oauth/tiktok/callback/</code></p>
    <div class="row"><button class="btn sec sm" onclick="saveTt()">Uložiť</button><a class="btn sm" href="/api/accounts/tiktok/connect">${I('link', 's')}Pripojiť účet</a></div>`)}
  ${c('linkedin', 'LinkedIn', `<p class="small muted">Dve LinkedIn appky (tak to LinkedIn chce). Redirect URL: <code>http://localhost:8765/oauth/linkedin/callback</code></p>
    <b class="small">Osobný profil</b> ${h.li_creds ? ok : ''}<input id="liId" placeholder="Client ID" style="margin:6px 0"><input id="liSec" placeholder="Client Secret" type="password">
    <div class="row" style="margin:8px 0 14px"><button class="btn sec sm" onclick="saveLi(false)">Uložiť</button><a class="btn sm" href="/api/accounts/linkedin/connect">${I('link', 's')}Pripojiť profil</a></div>
    <b class="small">Firemné stránky</b> ${h.li_org ? ok : ''}<input id="liOId" placeholder="Client ID" style="margin:6px 0"><input id="liOSec" placeholder="Client Secret" type="password">
    <div class="row" style="margin-top:8px"><button class="btn sec sm" onclick="saveLi(true)">Uložiť</button><a class="btn sm" href="/api/accounts/linkedin/connect?org=1">${I('link', 's')}Pripojiť stránky</a></div>
    ${all.some(a => a.org) ? `<div style="margin-top:14px"><b class="small">Jazyky na firemnej stránke</b>
      <p class="small dim">Jedna stránka pre všetky krajiny. Vyber, v ktorých jazykoch tam majú ísť videá (každý jazyk = samostatný príspevok). ${S.meta.li.followers ? `Sledovateľov: <b>${S.meta.li.followers}</b>. ` : ''}${S.meta.li.followers >= 300 ? 'Príspevky sa ukážu hlavne ľuďom v danom jazyku.' : 'Od 300 sledovateľov appka začne každý príspevok ukazovať hlavne ľuďom v jeho jazyku.'}</p>
      <div class="row small" style="gap:6px;flex-wrap:wrap">${S.meta.languages.map(l => `<label class="chip" style="cursor:pointer"><input type="checkbox" class="liL" value="${l.code}" ${S.meta.li.page_langs.includes(l.code) ? 'checked' : ''} onchange="saveLiLangs()"> ${l.name}</label>`).join('')}</div></div>` : ''}
    <p class="small dim">Osobný profil treba prihlásiť znova po 60 dňoch, appka ťa upozorní. Firemná stránka sa obnovuje sama.</p>`)}
  </div>`;
}
async function uploadYt() { const f = $('#ytJson').files[0]; if (!f) return toast('Vyber JSON súbor', true); const fd = new FormData(); fd.append('file', f); const r = await api('/api/accounts/youtube/client', { method: 'POST', body: fd }); toast(`Uložené (Google projektov: ${r.projects}), teraz klikni Pripojiť kanál`); S.meta = await api('/api/meta'); render(); }
function accFilter() { const q = $('#accQ').value.toLowerCase(), pf = $('#accPf').value; $$('#accT tr[data-pf]').forEach(tr => { tr.hidden = (q && !tr.dataset.n.includes(q)) || (pf && tr.dataset.pf !== pf); }); }
async function accBulk() { const ids = $$('.aS:checked').map(c => +c.value), pv = $('#bkP').value, lv = $('#bkL').value, cv = $('#bkC').value; if (!ids.length) return toast('Označ účty', true); if (!pv && !lv && !cv) return toast('Vyber projekt, krajinu alebo jazyk', true); const body = {}; if (pv) body.project_id = +pv; if (cv) body.country = cv; if (lv) body.lang = lv === '-' ? '' : lv; for (const id of ids) await api('/api/accounts/' + id, { method: 'PUT', body }); toast(`Nastavené pre ${ids.length} účtov`); render(); }
async function refreshMeta() { const r = await api('/api/accounts/meta', { method: 'POST', body: { token: '' } }, 'Hľadám nové stránky a Instagramy…'); toast(`Pripojených ${r.created} účtov`); render(); }
async function connectMeta() { const r = await api('/api/accounts/meta', { method: 'POST', body: { token: $('#metaTok').value } }, 'Načítavam stránky a Instagram…'); toast(`Pripojených ${r.created} účtov`); render(); }
async function saveTt() { await api('/api/accounts/tiktok/creds', { method: 'POST', body: { client_key: $('#ttKey').value, client_secret: $('#ttSec').value, mode: $('#ttMode').value } }); toast('Uložené'); render(); }
async function saveTtb() { await api('/api/accounts/ttb/creds', { method: 'POST', body: { app_id: $('#ttbId').value, secret: $('#ttbSec').value } }); toast('Uložené'); render(); }
async function pasteTtb() { const r = await api('/api/accounts/ttb/paste', { method: 'POST', body: { url: $('#ttbUrl').value } }, 'Pripájam…'); toast(`Pripojených ${r.created}`); render(); }
async function saveLiLangs() { const v = $$('.liL:checked').map(c => c.value); await api('/api/settings', { method: 'POST', body: { li_page_langs: v } }); S.meta.li.page_langs = v; toast('Uložené'); }
async function saveLi(org) { await api('/api/accounts/linkedin/creds', { method: 'POST', body: { client_id: $(org ? '#liOId' : '#liId').value, client_secret: $(org ? '#liOSec' : '#liSec').value, org } }); toast('Uložené'); render(); }
async function accCountry(id, c) { await api('/api/accounts/' + id, { method: 'PUT', body: { country: c } }); toast('Uložené'); render(); }
async function accSet(id, tr) { const np = +$('.aP', tr).value; await api('/api/accounts/' + id, { method: 'PUT', body: { project_id: np, lang: $('.aL', tr).value } }); if (np !== S.pf) { toast('Účet presunutý do projektu ' + (S.projects.find(x => x.id === np)?.name || '')); render(); } else toast('Uložené'); }

// ================= NASTAVENIA =================
async function pSettings(m) {
  const ai = S.meta.ai, mo = S.meta.models, st = S.meta.settings;
  const u = await api('/api/ai-usage');
  const opt = cur => ['haiku', 'sonnet', 'opus'].map(x => `<option ${x === cur ? 'selected' : ''}>${x}</option>`).join('');
  m.innerHTML = `<div class="top"><div><h1>Nastavenia</h1></div></div>
  <div class="g2" style="align-items:start"><div>
  <div class="card"><h2>${I('bot')}Claude (tvoj Max plán)</h2>
    <div class="hint" style="${ai.cli_found ? '' : 'background:var(--warnSoft);border-color:rgba(245,176,0,.35)'}">${I(ai.cli_found ? 'check' : 'alert')}<div>${ai.cli_found ? `Claude Code nájdený (${esc(ai.version || '')}). AI ide cez Max plán, nič sa neplatí navyše.` : 'Claude Code som nenašiel – appka je v ručnom režime (kopíruješ text do claude.ai).'}</div></div>
    <div class="g2"><div><label class="l">Režim</label><select id="aiMode"><option value="auto" ${st.ai_mode === 'auto' ? 'selected' : ''}>Automaticky</option><option value="manual" ${st.ai_mode === 'manual' ? 'selected' : ''}>Ručne cez claude.ai</option></select></div>
    <div><label class="l">Cesta ku Claude Code (ak ho nenájde)</label><input id="cPath" value="${esc(st.claude_path)}"></div>
    <div><label class="l">Model na vymýšľanie</label><select id="mC">${opt(mo.creative)}</select></div><div><label class="l">Model na preklady</label><select id="mCh">${opt(mo.cheap)}</select></div></div>
    <p class="small dim">Najlepší pomer: sonnet na vymýšľanie, haiku na preklady. Opus míňa limit najrýchlejšie.</p>
    <button class="btn sm" onclick="saveSettings()">${I('check', 's')}Uložiť</button></div>
  <div class="card"><h2>${I('volume')}Hlas</h2>
    ${voiceUsageHTML(S.meta.google_tts)}
    <p class="small muted">Najprirodzenejšie znejú <b>Google hlasy (Chirp 3 HD)</b>. Prvý milión znakov mesačne (cca 1 000 minút) je zadarmo. Bez kľúča appka používa bezplatné Microsoft hlasy.</p>
    <details><summary class="small">Ako získam kľúč (5 minút)</summary><ol class="small muted">
      <li>Otvor <a href="https://console.cloud.google.com/apis/library/texttospeech.googleapis.com" target="_blank">Cloud Text-to-Speech API</a> v tom istom projekte ako YouTube a klikni <b>Enable</b> (Google si vypýta kartu).</li>
      <li>Choď do <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Credentials</a> → <b>Create credentials → API key</b>.</li>
      <li>Pri kľúči daj <b>Restrict key</b> → povoľ len <i>Cloud Text-to-Speech API</i>. Kľúč skopíruj sem.</li></ol></details>
    <div class="g2"><div><label class="l">Google kľúč (API key)</label><input id="gKey" type="password" placeholder="${S.meta.google_tts.enabled ? 'uložený – nový vlož sem' : 'AIza…'}"></div>
    <div><label class="l">Mesačne smie minúť navyše (€)</label><input id="gBud" type="number" min="0" step="1" value="${S.meta.google_tts.budget || 0}"></div></div>
    <p class="small dim">0 € = len bezplatný limit, potom appka sama prepne na Microsoft hlas. Napr. 5 € = ďalších cca 180 minút.</p>
    <button class="btn sm" onclick="saveVoiceSet()">${I('check', 's')}Uložiť</button>
    <label class="l" style="margin-top:16px">Vypočuj si hlasy</label><div class="row"><select id="tL" onchange="loadVoiceList()">${S.meta.languages.map(l => `<option value="${l.code}">${l.name}</option>`).join('')}</select></div>
    <div id="vList" class="vlist"></div></div>
  <div class="card"><h2>${I('mic')}Výslovnosť</h2>
    <p class="small muted">Hlas pred čítaním sám opraví názvy, skratky a jednotky vo všetkých jazykoch (napr. PROLINE, SCOP, R290, A+++, dB(A), kW). Titulky vo videu ostanú napísané pôvodne. Nič to nestojí a nepoužíva AI.</p>
    <label class="l">Tvoje slová</label>
    <p class="small dim">Napíš slovo a vedľa po slovensky tak, ako to má znieť (napr. <i>prolajn</i>). Do ostatných jazykov sa to prevedie samo.</p>
    <div id="prList" class="vlist"><span class="small dim">Načítavam…</span></div>
    <div class="row" style="margin-top:10px"><button class="btn sec sm" onclick="prAdd()">${I('plus', 's')}Pridať slovo</button><button class="btn sm" onclick="prSave()">${I('check', 's')}Uložiť</button></div>
    <label class="l" style="margin-top:16px">Vyskúšaj vetu</label>
    <textarea id="prText" rows="2"></textarea>
    <div class="row" style="margin-top:8px"><select id="prLang">${S.meta.languages.map(l => `<option value="${l.code}">${l.name}</option>`).join('')}</select><button class="btn sec sm" onclick="prTest(this)">${I('play', 's')}Vypočuť</button></div>
    <p class="small dim" id="prOut"></p>
    <details><summary class="small">Čo už hlas vie sám</summary><div id="prBuilt" class="small muted" style="margin-top:8px"></div></details></div>
  ${typeof soundCard === 'function' ? soundCard() : ''}
  <div class="card"><h2>${I('film')}Zábery a hudba</h2>
    <p class="small muted">Videá sa skladajú zo záberov: najprv tvoje vlastné (priečinok Moje zábery, názov súboru = o čom je záber, napr. <i>varenie-cestoviny.mp4</i>), potom bezplatné Pexels a Pixabay, a keď nič nenájde, AI obrázok (Cloudflare, zadarmo denne). Stiahnuté zábery si appka pamätá. V knižnici: <b>${S.meta.footage?.library || 0}</b> · tvojich: <b>${S.meta.footage?.own || 0}</b> · hudby: <b>${S.meta.footage?.music || 0}</b></p>
    <p class="small muted">Animované schémy vo videách (ako N2N Akadémia): ${S.meta.anim?.ready ? '<span class="ok-t">pripravené</span>' : S.meta.anim?.installing ? 'pripravujem na pozadí (stiahne sa raz, pár minút)…' : 'pripravia sa samé po ďalšom zapnutí appky' + (S.meta.anim?.error ? ' <span class="bad-t">(' + esc(S.meta.anim.error.slice(-120)) + ')</span>' : '')}</p>
    <div class="row" style="margin-bottom:10px"><button class="btn sec sm" onclick="api('/api/open-folder',{method:'POST',body:{which:'own'}})">${I('upload', 's')}Otvoriť Moje zábery</button><button class="btn sec sm" onclick="api('/api/open-folder',{method:'POST',body:{which:'music'}})">${I('volume', 's')}Otvoriť Hudbu</button></div>
    <details><summary class="small">Ako získam kľúče (zadarmo)</summary><ol class="small muted">
      <li><b>Pexels</b>: <a href="https://www.pexels.com/api/new/" target="_blank">pexels.com/api</a> → prihlás sa → vyplň krátky formulár → skopíruj API key.</li>
      <li><b>Pixabay</b>: <a href="https://pixabay.com/api/docs/" target="_blank">pixabay.com/api/docs</a> → prihlás sa → kľúč je priamo na stránke (zelený).</li>
      <li><b>AI obrázky</b> (voliteľné): <a href="https://dash.cloudflare.com/profile/api-tokens" target="_blank">Cloudflare → API Tokens</a> → Create Token → šablóna <i>Workers AI</i>. Account ID nájdeš vpravo na <a href="https://dash.cloudflare.com/" target="_blank">hlavnej stránke</a>.</li>
      <li><b>Hudba</b>: stiahni bezplatné skladby (napr. Pixabay Music alebo YouTube Audio Library) do priečinka Hudba. Hrá potichu pod hlasom.</li></ol></details>
    <div class="g2"><div><label class="l">Pexels kľúč</label><input id="fxPx" type="password" placeholder="${S.meta.footage?.pexels ? 'uložený' : ''}"></div><div><label class="l">Pixabay kľúč</label><input id="fxPb" type="password" placeholder="${S.meta.footage?.pixabay ? 'uložený' : ''}"></div>
    <div><label class="l">Cloudflare Account ID</label><input id="fxCa" type="password" placeholder="${S.meta.footage?.ai ? 'uložené' : ''}"></div><div><label class="l">Cloudflare token</label><input id="fxCt" type="password" placeholder="${S.meta.footage?.ai ? 'uložený' : ''}"></div></div>
    <button class="btn sm" style="margin-top:10px" onclick="saveFx()">${I('check', 's')}Uložiť</button></div>
  <div class="card"><h2>${I('globe')}Preklady zadarmo (bez tokenov)</h2>
    <p class="small muted">Preklady do jazykov urobí bezplatný prekladač namiesto Clauda – Max limit ostane na vymýšľanie. Stačí jeden, najlepšie Microsoft (2 mil. znakov mesačne ≈ 55 videí v 36 jazykoch). Appka sa zastaví pred limitom, nič sa neplatí.</p>
    ${Object.entries(S.meta.mt || {}).map(([k, u]) => `<div class="vrow"><span style="min-width:90px"><b>${u.name}</b></span><span class="small ${u.enabled ? 'ok-t' : 'dim'}">${u.enabled ? 'zapnutý' : 'nenastavený'}</span><span style="flex:1"><div class="bar"><i style="width:${Math.min(100, Math.round(u.used / u.free * 100))}%"></i></div></span><span class="small dim">${Math.round(u.used / 1000)}k / ${u.free / 1000}k</span></div>`).join('')}
    <details><summary class="small">Ako získam kľúč</summary><ol class="small muted">
      <li><b>Microsoft</b> (odporúčam): <a href="https://portal.azure.com/#create/Microsoft.CognitiveServicesTextTranslation" target="_blank">vytvor Translator</a> → Pricing tier <b>Free F0</b> → Create → v časti <i>Keys and Endpoint</i> skopíruj <b>KEY 1</b> a <b>Location/Region</b>.</li>
      <li><b>DeepL</b> (voliteľne, najlepšia kvalita pre veľké jazyky): <a href="https://www.deepl.com/pro-api" target="_blank">DeepL API Free</a> → účet → <i>API Keys</i> → skopíruj kľúč.</li>
      <li><b>Google</b>: v tom istom projekte ako hlas zapni <a href="https://console.cloud.google.com/apis/library/translate.googleapis.com" target="_blank">Cloud Translation API</a> (Enable) a zaškrtni nižšie. Ak má kľúč obmedzenie, pridaj mu aj Cloud Translation API.</li></ol></details>
    <div class="g2"><div><label class="l">Microsoft kľúč</label><input id="mtAz" type="password" placeholder="${S.meta.mt?.azure?.enabled ? 'uložený' : ''}"></div><div><label class="l">Microsoft región</label><input id="mtAzR" value="${esc(st.mt_azure_region || '')}" placeholder="westeurope"></div>
    <div><label class="l">DeepL kľúč</label><input id="mtDl" type="password" placeholder="${S.meta.mt?.deepl?.enabled ? 'uložený' : ''}"></div><div><label class="l">Google</label><label class="small" style="display:flex;gap:8px;align-items:center;margin-top:10px"><input type="checkbox" id="mtGo" ${st.mt_google ? 'checked' : ''}>Použiť Google kľúč z hlasu</label></div></div>
    <button class="btn sm" style="margin-top:10px" onclick="saveMt()">${I('check', 's')}Uložiť</button></div>
  <div class="card"><h2>${I('radar')}Radar a plánovanie</h2>
    <p class="small muted">Radar sám zbiera trendy (Google, Wikipédia, správy), videá konkurencie a čísla tvojich videí – zadarmo, bez AI. Claude dostane raz týždenne krátky výťah a navrhne 5 nápadov na projekt.</p>
    <label class="row"><input type="checkbox" ${st.radar_enabled !== false ? 'checked' : ''} onchange="api('/api/settings',{method:'POST',body:{radar_enabled:this.checked}}).then(()=>toast('Uložené'))"> Sledovať trendy a konkurenciu</label>
    <label class="row" style="margin-top:6px"><input type="checkbox" ${st.radar_weekly !== false ? 'checked' : ''} onchange="api('/api/settings',{method:'POST',body:{radar_weekly:this.checked}}).then(()=>toast('Uložené'))"> Každý pondelok navrhnúť nové nápady (1 volanie Claude na projekt)</label>
    <label class="row" style="margin-top:6px"><input type="checkbox" ${st.auto_plan_week ? 'checked' : ''} onchange="api('/api/settings',{method:'POST',body:{auto_plan_week:this.checked}}).then(()=>toast('Uložené'))"> Každú nedeľu večer naplánovať ďalší týždeň samé</label>
    <label class="l">YouTube kľúč (zadarmo, na sledovanie konkurencie) ${S.meta.yt_key ? '<span class="chip ok">uložený</span>' : ''}</label>
    <div class="row"><input id="ytKey" type="password" style="flex:1" placeholder="AIza…"><button class="btn sm" onclick="saveYtKey()">${I('check', 's')}Uložiť</button></div>
    <details><summary class="small">Ako získam kľúč (3 minúty)</summary><ol class="small muted">
      <li>Otvor <a href="https://console.cloud.google.com/apis/library/youtube.googleapis.com" target="_blank">YouTube Data API v3</a> v tom istom Google projekte ako hlas a klikni <b>Enable</b> (ak už je zapnuté, preskoč).</li>
      <li>Choď do <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Credentials</a> → <b>Create credentials → API key</b>.</li>
      <li>Pri kľúči daj <b>Restrict key</b> → povoľ len <i>YouTube Data API v3</i>. Skopíruj ho sem. Je zadarmo, appka minie najviac 8 000 z 10 000 bodov denne.</li></ol></details></div>
  <div class="card"><h2>${I('refresh')}Aktualizácie</h2><div id="updBox" class="small muted">Kontrolujem…</div>
    <p class="small dim">Nové verzie si appka sťahuje sama (pri zapnutí a každé 4 hodiny). Projekty, videá, účty a nastavenia ostávajú.</p>
    <label class="l">Nový zip appky</label><input type="file" id="updZip" accept=".zip"><button class="btn sm" style="margin-top:8px" onclick="updZip()">${I('upload', 's')}Aktualizovať zo zipu</button>
    <div class="row" style="margin-top:8px"><button class="btn sm" onclick="updGh()">${I('refresh', 's')}Skontrolovať teraz</button></div>
    <details style="margin-top:10px"><summary class="small dim">Pokročilé</summary><label class="l">Odkiaľ sa sťahujú nové verzie (GitHub)</label><div class="row"><input id="updRepo" style="flex:1" placeholder="Supnoga/social-manager"></div>
      <label class="l">Kľúč na čítanie (len pri súkromnom repozitári)</label><input id="updTok" type="password" placeholder="github_pat_…">
      <button class="btn sec sm" style="margin-top:8px" onclick="saveRepo()">Uložiť</button></details></div>
  </div><div>
  <div class="card"><h2>${I('chart')}Spotreba AI</h2>
    <div class="row" style="gap:20px;margin-bottom:10px"><div><b style="font-size:22px">${((u.day.inp + u.day.outp) / 1000).toFixed(1)}k</b><div class="small muted">tokenov za 24 h</div></div><div><b style="font-size:22px">${((u.week.inp + u.week.outp) / 1000).toFixed(1)}k</b><div class="small muted">za 7 dní</div></div><div><b style="font-size:22px">${u.day.cached}</b><div class="small muted">zadarmo z pamäte</div></div></div>
    <table><tr><th>Čas</th><th>Úloha</th><th>Model</th><th>Tokeny</th></tr>${u.last.slice(0, 12).map(r => `<tr><td class="small muted">${r.ts.slice(5, 16)}</td><td>${r.purpose}</td><td class="muted">${r.model}</td><td>${r.cached ? '<span class="chip ok">pamäť</span>' : r.ok ? ((r.input_tokens + r.output_tokens) / 1000).toFixed(1) + 'k' : `<span class="chip bad" title="${esc(r.note)}">chyba</span>`}</td></tr>`).join('')}</table></div>
  <div class="card"><h2>${I('globe')}Verejná adresa (TikTok Business)</h2>
    <p class="small muted">TikTok si videá sťahuje z internetu. Appka ich sprístupní cez bezplatný Cloudflare Tunnel na tvojej doméne – zvonka sú viditeľné len tajné odkazy na videá.</p>
    <label class="l">Verejná adresa</label><input id="pubUrl" value="${esc(st.public_base_url)}" placeholder="https://videa.tvojadomena.sk">
    <label class="l">Cloudflare Tunnel token</label><input id="cfTok" type="password" value="${esc(st.cf_tunnel_token)}">
    <p class="small">Tunel: ${S.meta.tunnel.running ? '<span class="ok-t">beží</span>' : S.meta.tunnel.configured ? '<span class="bad-t">nebeží</span> ' + esc(S.meta.tunnel.error || '') : '<span class="dim">nenastavený</span>'}</p>
    <div class="g2"><div><label class="l">Overovací súbor – názov</label><input id="vfName" placeholder="tiktokXXXX.txt"></div><div><label class="l">…a obsah</label><input id="vfCont"></div></div>
    <p class="small dim">Uložené: ${Object.keys(st.verify_files || {}).map(esc).join(', ') || 'žiadne'}</p>
    <label class="row"><input type="checkbox" id="ttbDraft" ${st.ttb_draft ? 'checked' : ''}> TikTok Business: posielať len ako koncept</label>
    <label class="row" style="margin-top:6px"><input type="checkbox" id="ttbAi" ${st.ttb_ai_label ? 'checked' : ''}> Označiť videá ako AI-generované</label>
    <label class="l">Náhodný posun času publikovania (min)</label><input id="jit" type="number" value="${st.jitter_min}" style="max-width:120px">
    <div style="margin-top:12px"><button class="btn sm" onclick="savePub()">${I('check', 's')}Uložiť</button></div></div>
  <div class="card"><h2>${I('settings')}Ostatné</h2><p class="small muted">Video nástroj: ${S.meta.ffmpeg ? '<span class="ok-t">OK</span>' : '<span class="bad-t">chýba</span>'} · Dáta sú v priečinku <code>data</code> vedľa appky.</p>
    <label class="row" style="margin-top:4px"><input type="checkbox" id="reqApp" ${st.require_approval !== false ? 'checked' : ''} onchange="api('/api/settings',{method:'POST',body:{require_approval:this.checked}}).then(()=>toast('Uložené'))"> Pred zverejnením chcem videá schváliť (Kontrola)</label>
    <label class="l">Verzia Meta API</label><input id="metaV" value="${esc(st.meta_api_version)}" style="max-width:160px"></div>
  </div></div>`;
  loadUpd(); loadVoiceList(); prLoad();
}
async function saveSettings() { await api('/api/settings', { method: 'POST', body: { ai_mode: $('#aiMode').value, claude_path: $('#cPath').value, model_creative: $('#mC').value, model_cheap: $('#mCh').value, meta_api_version: $('#metaV').value } }); toast('Uložené'); render(); }
async function savePub() { await api('/api/settings', { method: 'POST', body: { public_base_url: $('#pubUrl').value.trim(), cf_tunnel_token: $('#cfTok').value.trim(), verify_name: $('#vfName').value, verify_content: $('#vfCont').value, ttb_draft: $('#ttbDraft').checked, ttb_ai_label: $('#ttbAi').checked, jitter_min: +$('#jit').value } }); toast('Uložené'); setTimeout(render, 1500); }
function voiceUsageHTML(g) {
  if (!g || !g.enabled) return `<div class="hint">${I('alert')}<div>Google hlasy nie sú zapnuté – používajú sa bezplatné Microsoft hlasy.</div></div>`;
  const pct = Math.min(100, Math.round(g.used / g.free * 100));
  return `<div class="hint">${I('check')}<div style="flex:1">Google hlasy zapnuté. Tento mesiac: <b>${g.used.toLocaleString('sk')}</b> z ${g.free.toLocaleString('sk')} znakov zadarmo (cca ${g.minutes} min)${g.spent ? ` · navyše cca <b>${g.spent} €</b>` : ''}.<div class="bar"><i style="width:${pct}%"></i></div></div></div>`;
}
async function saveFx() { const b = {}; [['fxPx', 'pexels_key'], ['fxPb', 'pixabay_key'], ['fxCa', 'cf_account'], ['fxCt', 'cf_ai_token']].forEach(([i, k]) => { const v = $('#' + i).value.trim(); if (v) b[k] = v; }); if (!Object.keys(b).length) return toast('Vlož aspoň jeden kľúč', true); await api('/api/settings', { method: 'POST', body: b }); toast('Uložené'); S.meta = await api('/api/meta'); render(); }
async function saveMt() { const b = { mt_azure_region: $('#mtAzR').value.trim(), mt_google: $('#mtGo').checked }; if ($('#mtAz').value.trim()) b.mt_azure_key = $('#mtAz').value.trim(); if ($('#mtDl').value.trim()) b.mt_deepl_key = $('#mtDl').value.trim(); await api('/api/settings', { method: 'POST', body: b }); toast('Uložené'); S.meta = await api('/api/meta'); render(); }
async function saveVoiceSet() { await api('/api/settings', { method: 'POST', body: { ...($('#gKey').value.trim() ? { google_tts_key: $('#gKey').value.trim() } : {}), google_tts_budget: +$('#gBud').value || 0 } }); toast('Uložené'); for (const k in VCACHE) delete VCACHE[k]; S.meta = await api('/api/meta'); render(); }
const VCACHE = {};
async function voicesFor(lang) { return VCACHE[lang] || (VCACHE[lang] = await api('/api/voices/' + lang)); }
let curAudio;
async function playVoice(lang, voice, btn) {
  if (curAudio) curAudio.pause();
  if (btn) btn.classList.add('loading');
  try {
    const r = await api('/api/voices/preview', { method: 'POST', body: { lang, voice } });
    if (r.note) toast('Vybraný hlas nešiel, hrá náhradný: ' + r.note, true);
    curAudio = new Audio('/api/file?path=' + encodeURIComponent(r.voice_path)); curAudio.play();
  } finally { if (btn) btn.classList.remove('loading'); }
}
async function loadVoiceList() {
  const lang = $('#tL').value, box = $('#vList'); box.innerHTML = '<span class="small dim">Načítavam…</span>';
  const d = await voicesFor(lang);
  box.innerHTML = d.voices.map(v => `<div class="vrow"><button class="btn sec sm ic" onclick="playVoice('${lang}','${v.id}',this)">${I('play', 's')}</button><span style="flex:1">${esc(v.label)}</span><span class="tag ${v.engine === 'google' ? 'acc' : ''}">${v.engine === 'google' ? 'Google HD' : 'Microsoft'}</span><span class="small dim">${v.gender === 'F' ? 'žena' : 'muž'}</span></div>`).join('');
}
// ----- výslovnosť (vlastné slová pre hlas) -----
let PR = [];
function prRows() {
  const langs = S.meta.languages;
  $('#prList').innerHTML = PR.length ? PR.map((x, i) => `<div class="vrow"><input class="prW" placeholder="Slovo (napr. PROLINE)" value="${esc(x.w)}" style="flex:1 1 0;width:0;min-width:0"><input class="prS" placeholder="Ako sa číta (napr. prolajn)" value="${esc(x.say)}" style="flex:1 1 0;width:0;min-width:0"><select class="prL" title="V ktorom jazyku" style="flex:0 0 150px;width:150px"><option value="*">Všetky jazyky</option>${langs.map(l => `<option value="${l.code}" ${l.code === x.lang ? 'selected' : ''}>len ${l.name}</option>`).join('')}</select><button class="btn sec sm ic" title="Vypočuť" onclick="prPlay(${i},this)">${I('play', 's')}</button><button class="btn ghost sm ic" title="Odstrániť" onclick="prRead();PR.splice(${i},1);prRows()">${I('trash', 's')}</button></div>`).join('') : '<span class="small dim">Zatiaľ žiadne vlastné slová.</span>';
}
function prRead() { PR = $$('#prList .vrow').map(r => ({ w: $('.prW', r).value.trim(), say: $('.prS', r).value.trim(), lang: $('.prL', r).value })); return PR; }
function prAdd() { prRead(); PR.push({ w: '', say: '', lang: '*' }); prRows(); const a = $$('#prList .prW'); a[a.length - 1].focus(); }
async function prLoad() {
  if (!$('#prList')) return;
  const d = await api('/api/pronounce'); PR = d.custom; prRows();
  $('#prText').value = d.demo; $('#prLang').value = 'sk';
  $('#prBuilt').innerHTML = `<p>Názvy: ${d.builtin.map(b => `<b>${esc(b.w)}</b> (${esc(b.say)})`).join(', ')}. Ak chceš niektorý čítať inak, pridaj ho hore medzi svoje slová.</p><p>Ďalej: chladivá (R290, R32), energetické triedy (A+++), jednotky po čísle (kW, kWh, W, dB, dB(A), °C, m², m³), rozsahy (5–10), tisícky s medzerou (1 200), znak & a slová písané VEĽKÝMI písmenami, ktoré by inak hláskoval. Smajlíky a mriežky nečíta, nový riadok a pomlčka sú krátka pauza.</p>`;
}
async function prSave(quiet) { const r = await api('/api/pronounce', { method: 'POST', body: { items: prRead().filter(x => x.w && x.say) } }); if (!quiet) { PR = r.custom; prRows(); toast('Uložené. Platí pre každý nový hlas.'); } }
async function prSay(text, lang, btn) {
  if (curAudio) curAudio.pause();
  if (btn) btn.classList.add('loading');
  try {
    await prSave(true);
    const r = await api('/api/voices/preview', { method: 'POST', body: { lang, text } });
    if ($('#prOut')) $('#prOut').textContent = r.spoken ? 'Hlas prečíta: ' + r.spoken : '';
    curAudio = new Audio('/api/file?path=' + encodeURIComponent(r.voice_path)); curAudio.play();
  } finally { if (btn) btn.classList.remove('loading'); }
}
function prPlay(i, btn) { const x = prRead()[i]; if (!x.w || !x.say) return toast('Doplň slovo aj to, ako sa číta', true); prSay(x.w + '.', x.lang === '*' ? $('#prLang').value : x.lang, btn); }
function prTest(btn) { const t = $('#prText').value.trim(); if (!t) return toast('Napíš vetu', true); prSay(t, $('#prLang').value, btn); }
function voiceNote(r) { const n = r.note || (r.notes || []).join('; '); if (n) toast('Použitý náhradný hlas: ' + n, true); }
async function testVoice() { const r = await api('/api/voice/test', { method: 'POST', body: { text: $('#tT').value, lang: $('#tL').value, gender: $('#tG').value } }, 'Vytváram hlas…'); $('#tA').innerHTML = `<audio autoplay controls src="/api/file?path=${encodeURIComponent(r.voice_path)}"></audio>`; }
async function loadUpd() {
  const u = await api('/api/update'); if (!$('#updBox')) return;
  $('#updRepo').value = u.repo || '';
  $('#updBox').innerHTML = `Verzia <b style="color:#fff">${esc(u.version)}</b> · ` + (u.available ? `<span style="color:var(--acc)">dostupná nová ${esc(u.available)}</span>` : u.latest ? '<span class="ok-t">najnovšia</span>' : u.error ? esc(u.error) : 'automatické aktualizácie nie sú nastavené');
}
async function waitRestart() { busy(true, 'Aktualizujem a reštartujem…'); for (let i = 0; i < 60; i++) { await new Promise(r => setTimeout(r, 2000)); try { const r = await fetch('/api/meta'); if (r.ok) { busy(false); toast('Aktualizované'); return location.reload(); } } catch (e) { } } busy(false); toast('Appka sa nespustila znova – spusti ju ručne.', true); }
async function updZip() { const f = $('#updZip').files[0]; if (!f) return toast('Vyber zip', true); const fd = new FormData(); fd.append('file', f); await api('/api/update/zip', { method: 'POST', body: fd }, 'Inštalujem novú verziu…'); waitRestart(); }
async function quitApp() { if (!confirm('Vypnúť appku? Naplánované videá sa nezverejnia, kým ju znova nezapneš ikonkou.')) return; await fetch('/api/quit', { method: 'POST' }).catch(() => { }); document.body.innerHTML = '<div style="padding:60px;font:16px Inter,sans-serif;color:#fff">Appka je vypnutá. Zapneš ju ikonkou Social Manager.</div>'; }
async function saveRepo() { await api('/api/settings', { method: 'POST', body: { update_repo: $('#updRepo').value.trim(), ...($('#updTok').value.trim() ? { update_token: $('#updTok').value.trim() } : {}) } }); toast('Uložené'); loadUpd(); }
async function updGh() { const r = await api('/api/update/github', { method: 'POST' }, 'Sťahujem aktualizáciu…'); if (r.updated) waitRestart(); else { toast(r.latest ? 'Máš najnovšiu verziu' : (r.error || 'Hotovo')); loadUpd(); } }

render();
async function saveYtKey() { const key = $('#ytKey').value.trim(); if (!key) return toast('Vlož kľúč', true); await api('/api/radar/yt-key', { method: 'POST', body: { key } }, 'Skúšam kľúč…'); toast('Kľúč funguje a je uložený'); S.meta = await api('/api/meta'); render(); }
// po samočinnej aktualizácii appky sa stránka obnoví sama (keď práve nič nerobíš)
(() => { let v = null; setInterval(async () => { try { const j = await (await fetch('/api/ping')).json(); if (v && j.version !== v && $('#modal').classList.contains('hidden') && $('#busy').classList.contains('hidden')) { location.reload(); return; } v = v || j.version; } catch (e) { } }, 30000); })();
