// Social Manager – Súkromné správy (samostatný súbor, používa pomocníkov z app.js)
IC.inbox = '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>';
IC.clock = '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>';
S.dmCount = 0;
const DM_ST = { new: ['Nová', 'acc'], draft: ['Návrh pripravený', 'warn'], sent: ['Odoslané', 'ok'], skip: ['Preskočené', ''], failed: ['Chyba', 'bad'], answered: ['Už zodpovedané', 'ok'] };

async function dmRefreshCount() {
  try { const r = await (await fetch('/api/dms/count')).json(); if (r.n !== S.dmCount) { S.dmCount = r.n; if (S.meta) sidebar(); } } catch (e) { }
}
setInterval(dmRefreshCount, 5 * 60000); setTimeout(dmRefreshCount, 1800);

async function pMessages(m) {
  const q = new URLSearchParams(location.hash.split('?')[1] || '');
  const f = q.has('f') ? q.get('f') : 'new';
  const d = await api('/api/dms?status=' + encodeURIComponent(f) + (S.pf ? '&project_id=' + S.pf : ''));
  if (!S.pf) { S.dmCount = (d.counts.new || 0) + (d.counts.draft || 0); sidebar(); }
  const nNew = d.counts.new || 0, nDraft = d.counts.draft || 0, st = d.settings;
  const errs = Object.values(d.errors || {});
  m.innerHTML = `<div class="top"><div>${pTitle('Správy')}<p class="sub">Súkromné správy z Facebooku a Instagramu na jednom mieste. AI navrhne odpoveď v jazyku zákazníka, ty ju schváliš.</p></div><div class="sp"></div>
    <button class="btn sec" onclick="dmFetch()">${I('refresh')}Načítať nové</button>
    ${nNew ? `<button class="btn sec" onclick="dmDraft()">${I('bot')}Navrhnúť odpovede (${nNew})</button>` : ''}
    ${nDraft ? `<button class="btn" onclick="dmSendAll(${nDraft})">${I('send')}Odoslať všetky návrhy (${nDraft})</button>` : ''}</div>
  <div class="seg" style="margin-bottom:14px">${[['new', 'Na vybavenie'], ['sent', 'Odoslané'], ['skip', 'Preskočené'], ['answered', 'Už zodpovedané'], ['', 'Všetko']].map(([k, n]) => `<button class="${f === k ? 'on' : ''}" onclick="location.hash=here()+'?f=${k}'">${n}</button>`).join('')}</div>
  <div class="small dim" style="margin-bottom:10px">${d.state.running ? 'Práve načítavam…' : d.state.last_fetch ? 'Naposledy načítané ' + esc(d.state.last_fetch) + ' · ďalej samé každú hodinu' : 'Správy sa načítajú samé každú hodinu.'}</div>
  ${errs.length ? `<div class="hint" style="margin-bottom:14px;background:var(--warnSoft);border-color:rgba(245,176,0,.35)">${I('alert')}<div>${errs.map(e => `<div><b>${esc(PL[e.platform] || e.platform)} · ${esc(e.name)}:</b> ${esc(e.error)}</div>`).join('')}</div></div>` : ''}
  ${d.items.length ? d.items.map(dmCard).join('') : `<div class="card">${empty('inbox', f === 'new' ? 'Žiadne nové správy.' : 'Nič tu nie je.')}</div>`}
  ${dmSettings(st)}`;
}

function dmLeft(h) {
  if (h === null || h === undefined) return '';
  if (h <= 0) return `<span class="chip bad">${I('clock', 's')}Čas na odpoveď vypršal</span>`;
  const t = h >= 24 ? Math.floor(h / 24) + ' d' : h >= 1 ? Math.floor(h) + ' h' : Math.max(1, Math.round(h * 60)) + ' min';
  return `<span class="chip ${h < 4 ? 'warn' : ''}">${I('clock', 's')}Zostáva ${t}</span>`;
}

function dmCard(c) {
  const s = DM_ST[c.status] || [c.status, ''];
  const open = ['new', 'draft', 'failed', 'skip'].includes(c.status);
  const hist = (c.history || []).filter(x => x.t);
  return `<div class="card" style="margin-bottom:12px">
    <div class="row small dim">${plat(c.platform)} · ${esc(c.account_name)}${c.lang ? ' · ' + esc(langName(c.lang)) : ''}<span class="sp" style="flex:1"></span>${open ? dmLeft(c.hours_left) : ''}<span class="chip ${s[1]}">${s[0]}</span></div>
    <div style="margin:10px 0 4px"><b>${esc(c.author || 'Niekto')}</b></div>
    ${hist.length ? `<div class="small muted" style="margin-bottom:6px;border-left:2px solid var(--line2);padding-left:8px">${hist.map(x => `<div>${x.me ? 'My: ' : ''}${esc(x.t)}</div>`).join('')}</div>` : ''}
    <div style="white-space:pre-wrap">${esc(c.text)}</div>
    ${c.text_sk ? `<div class="small muted" style="margin-top:4px">Po slovensky: ${esc(c.text_sk)}</div>` : ''}
    ${open ? `<label class="l" style="margin-top:12px">Odpoveď</label>
      <textarea id="dmr${c.id}" style="min-height:64px" placeholder="Napíš odpoveď alebo nechaj AI navrhnúť" onchange="dmSave(${c.id})">${esc(c.reply)}</textarea>
      ${c.reply_sk ? `<div class="small muted" style="margin-top:4px">Po slovensky: ${esc(c.reply_sk)}</div>` : ''}
      ${c.error ? `<div class="small" style="color:var(--bad);margin-top:4px">${esc(c.error)}</div>` : ''}
      <div class="row" style="margin-top:10px"><button class="btn sm" onclick="dmSend(${c.id})">${I('send')}Odoslať</button>
        <button class="btn sec sm" onclick="dmDraft([${c.id}])">${I('bot')}Návrh od AI</button>
        ${c.status !== 'skip' ? `<button class="btn ghost sm" onclick="dmSkip(${c.id})">${I('x')}Preskočiť</button>` : ''}</div>`
      : c.reply ? `<div class="small" style="margin-top:10px;padding:8px 10px;background:var(--panel2);border-radius:10px;border:1px solid var(--line)">${I('send', 's')} ${esc(c.reply)}</div>` : ''}
  </div>`;
}

function dmSettings(st) {
  return `<div class="card" style="margin-top:18px"><h2>${I('settings')}Nastavenie správ</h2>
    <label class="row" style="margin:6px 0"><input type="checkbox" ${st.auto_fetch ? 'checked' : ''} onchange="dmSet({auto_fetch:this.checked})">Načítavať správy samé každú hodinu (zadarmo, bez AI)</label>
    <label class="row" style="margin:6px 0"><input type="checkbox" ${st.auto_draft ? 'checked' : ''} onchange="dmSet({auto_draft:this.checked})">Hneď pripraviť návrhy odpovedí od AI (míňa trochu Claude limitu, odoslanie aj tak schvaľuješ ty)</label>
    <label class="row" style="margin:6px 0"><input type="checkbox" ${st.human_agent ? 'checked' : ''} onchange="dmSet({human_agent:this.checked})">Odpisovať až do 7 dní (zapni, až keď Meta schváli povolenie „Human Agent“)</label>
    <div class="hint" style="margin-top:12px">${I('alert')}<div>Čo treba, aby to fungovalo:<br>
      <b>Facebook a Instagram:</b> nový token s právami pages_messaging, pages_manage_metadata a instagram_manage_messages, vlož ho v Účtoch. V appke Instagram zapni Nastavenia → Správy → Pripojené nástroje → Povoliť prístup k správam.<br>
      Správy od bežných ľudí (nie od správcov stránky) Meta pustí až po jednorazovom schválení appky (App Review) a overení firmy. Je to zadarmo.<br>
      Odpísať sa dá do 24 hodín od poslednej správy človeka.<br>
      <b>TikTok:</b> v Európe TikTok správy cez appky nepovoľuje, odpisuje sa v appke TikTok.<br>
      <b>LinkedIn:</b> správy cez appky povoľuje len svojim partnerom, odpisuje sa na LinkedIne.</div></div>
  </div>`;
}

async function dmFetch() { const r = await api('/api/dms/fetch', { method: 'POST' }, 'Načítavam správy zo všetkých účtov…'); toast(r.busy ? 'Už sa načítava, chvíľu počkaj' : `Nových správ: ${r.new}` + (r.errors ? ` · ${r.errors} účtov s chybou` : '')); render(); }
async function dmDraft(ids) { const r = await api('/api/dms/draft', { method: 'POST', body: { ids: ids || null } }, 'AI pripravuje odpovede…'); toast(`Návrhy: ${r.drafted}` + (r.skipped ? ` · preskočených (spam, bez potreby odpovede): ${r.skipped}` : '')); render(); }
async function dmSave(id) { await api('/api/dms/' + id, { method: 'PUT', body: { reply: $('#dmr' + id).value } }); }
async function dmSkip(id) { await api('/api/dms/' + id, { method: 'PUT', body: { status: 'skip' } }); render(); }
async function dmSend(id) {
  const t = $('#dmr' + id).value.trim(); if (!t) return toast('Odpoveď je prázdna', true);
  await api('/api/dms/' + id, { method: 'PUT', body: { reply: t } });
  const r = await api('/api/dms/send', { method: 'POST', body: { ids: [id] } }, 'Odosielam…');
  toast(r.sent ? 'Odoslané' : 'Nepodarilo sa odoslať', !r.sent); render();
}
async function dmSendAll(n) {
  if (!confirm(`Odoslať ${n} odpovedí tak, ako sú teraz napísané?`)) return;
  const r = await api('/api/dms/send', { method: 'POST', body: { all_drafts: true, project_id: S.pf || 0 } }, 'Odosielam odpovede…');
  toast(`Odoslané: ${r.sent}` + (r.failed ? ` · chyby: ${r.failed}` : ''), !!r.failed); render();
}
async function dmSet(v) { await api('/api/dms/settings', { method: 'POST', body: v }); toast('Uložené'); }
