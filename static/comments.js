// Social Manager – Komentáre (samostatný súbor, používa pomocníkov z app.js)
IC.message = '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>';
S.cmCount = 0;
const CM_ST = { new: ['Nezodpovedaný', 'acc'], draft: ['Návrh pripravený', 'warn'], sent: ['Odoslané', 'ok'], skip: ['Preskočené', ''], failed: ['Chyba', 'bad'], answered: ['Už zodpovedané', 'ok'] };

async function cmRefreshCount() {
  try { const r = await (await fetch('/api/comments/count')).json(); if (r.n !== S.cmCount) { S.cmCount = r.n; if (S.meta) sidebar(); } } catch (e) { }
}
setInterval(cmRefreshCount, 5 * 60000); setTimeout(cmRefreshCount, 1500);

async function pComments(m) {
  const q = new URLSearchParams(location.hash.split('?')[1] || '');
  const f = q.has('f') ? q.get('f') : 'new';
  const all = q.get('all') === '1';
  const d = await api('/api/comments?status=' + encodeURIComponent(f) + (S.pf && !all ? '&project_id=' + S.pf : ''));
  S.cmCount = (d.counts.new || 0) + (d.counts.draft || 0); sidebar();
  const nNew = d.counts.new || 0, nDraft = d.counts.draft || 0, st = d.settings;
  const errs = Object.values(d.errors || {});
  m.innerHTML = `<div class="top"><div>${pTitle('Komentáre')}<p class="sub">Komentáre zo všetkých účtov na jednom mieste. AI navrhne odpoveď v jazyku komentára, ty ju schváliš.</p></div><div class="sp"></div>
    <button class="btn sec" onclick="cmFetch()">${I('refresh')}Načítať nové</button>
    ${nNew ? `<button class="btn sec" onclick="cmDraft()">${I('bot')}Navrhnúť odpovede (${nNew})</button>` : ''}
    ${nDraft ? `<button class="btn" onclick="cmSendAll(${nDraft})">${I('send')}Odoslať všetky návrhy (${nDraft})</button>` : ''}</div>
  <div class="row" style="gap:10px;margin-bottom:14px;flex-wrap:wrap"><div class="seg"><button class="${!all ? 'on' : ''}" onclick="location.hash=here()+'?f=${f}'">Tento projekt</button><button class="${all ? 'on' : ''}" onclick="location.hash=here()+'?f=${f}&all=1'">Všetky projekty</button></div>
  <div class="seg">${[['new', 'Nezodpovedané'], ['sent', 'Odoslané'], ['skip', 'Preskočené'], ['answered', 'Už zodpovedané'], ['', 'Všetko']].map(([k, n]) => `<button class="${f === k ? 'on' : ''}" onclick="location.hash=here()+'?f=${k}${all ? '&all=1' : ''}'">${n}</button>`).join('')}</div></div>
  <div class="small dim" style="margin-bottom:10px">${d.state.running ? 'Práve načítavam…' : d.state.last_fetch ? 'Naposledy načítané ' + esc(d.state.last_fetch) : 'Komentáre sa načítajú samé každé 2 hodiny.'}</div>
  ${errs.length ? `<div class="hint" style="margin-bottom:14px;background:var(--warnSoft);border-color:rgba(245,176,0,.35)">${I('alert')}<div>${errs.map(e => `<div><b>${esc(PL[e.platform] || e.platform)} · ${esc(e.name)}:</b> ${esc(e.error)}</div>`).join('')}</div></div>` : ''}
  ${d.items.length ? d.items.map(cmCard).join('') : `<div class="card">${empty('message', f === 'new' ? 'Žiadne nové komentáre. Komentáre sa zbierajú z videí zverejnených cez appku.' : 'Nič tu nie je.')}</div>`}
  ${cmSettings(st)}`;
}

const cmWhen = t => { if (!t) return ''; const d = new Date(t.includes('T') ? t : t.replace(' ', 'T')); if (isNaN(d)) return ''; const m = Math.round((Date.now() - d) / 6e4);
  return m < 60 ? `pred ${Math.max(1, m)} min` : m < 1440 ? `pred ${Math.round(m / 60)} h` : `${d.getDate()}. ${d.getMonth() + 1}. ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`; };
const cmLink = c => c.platform === 'youtube' && c.post_ext ? `https://www.youtube.com/watch?v=${encodeURIComponent(c.post_ext)}&lc=${encodeURIComponent(c.external_id)}` : (c.post_url && c.post_url.startsWith('http') ? c.post_url : '');
function cmCard(c) {
  const s = CM_ST[c.status] || [c.status, ''];
  const open = ['new', 'draft', 'failed', 'skip'].includes(c.status);
  return `<div class="card" style="margin-bottom:12px">
    <div class="row small dim">${plat(c.platform)} · ${esc(c.account_name)}${c.lang ? ' · ' + esc(langName(c.lang)) : ''}${c.post_title ? ' · ' + (c.post_url && c.post_url.startsWith('http') ? `<a href="${esc(c.post_url)}" target="_blank" style="color:inherit">${esc(c.post_title)} ${I('ext', 's')}</a>` : esc(c.post_title)) : ''}<span class="sp" style="flex:1"></span>${c.project_name ? `<span class="chip"><span class="dot" style="display:inline-block;width:7px;height:7px;border-radius:2px;background:${c.project_color};margin-right:5px"></span>${esc(c.project_name)}</span>` : ''}<span class="dim">${cmWhen(c.created)}</span><span class="chip ${s[1]}">${s[0]}</span>${cmLink(c) ? `<a class="btn ghost sm" href="${esc(cmLink(c))}" target="_blank" title="Otvoriť komentár na sieti a odpovedať tam">${I('ext', 's')}Odpovedať na ${PL[c.platform] || 'sieti'}</a>` : ''}</div>
    <div style="margin:10px 0 4px"><b>${esc(c.author || 'Niekto')}</b>${c.likes ? ` <span class="small dim">${I('thumbUp', 's')} ${c.likes}</span>` : ''}</div>
    <div style="white-space:pre-wrap">${esc(c.text)}</div>
    ${c.text_sk ? `<div class="small muted" style="margin-top:4px">Po slovensky: ${esc(c.text_sk)}</div>` : ''}
    ${open ? `<label class="l" style="margin-top:12px">Odpoveď</label>
      <textarea id="cmr${c.id}" style="min-height:64px" placeholder="Napíš odpoveď alebo nechaj AI navrhnúť" onchange="cmSave(${c.id})">${esc(c.reply)}</textarea>
      ${c.reply_sk ? `<div class="small muted" style="margin-top:4px">Po slovensky: ${esc(c.reply_sk)}</div>` : ''}
      ${c.error ? `<div class="small" style="color:var(--bad);margin-top:4px">${esc(c.error)}</div>` : ''}
      <div class="row" style="margin-top:10px"><button class="btn sm" onclick="cmSend(${c.id})">${I('send')}Odoslať</button>
        <button class="btn sec sm" onclick="cmDraft([${c.id}])">${I('bot')}Návrh od AI</button>
        ${c.status !== 'skip' ? `<button class="btn ghost sm" onclick="cmSkip(${c.id})">${I('x')}Preskočiť</button>` : ''}</div>`
      : c.reply ? `<div class="small" style="margin-top:10px;padding:8px 10px;background:var(--panel2);border-radius:10px;border:1px solid var(--line)">${I('send', 's')} ${esc(c.reply)}</div>` : ''}
  </div>`;
}

function cmSettings(st) {
  return `<div class="card" style="margin-top:18px"><h2>${I('settings')}Nastavenie komentárov</h2>
    <label class="row" style="margin:6px 0"><input type="checkbox" ${st.auto_fetch ? 'checked' : ''} onchange="cmSet({auto_fetch:this.checked})">Načítavať komentáre samé každé 3 hodiny (zadarmo, bez AI)</label>
    <label class="row" style="margin:6px 0"><input type="checkbox" ${st.auto_draft ? 'checked' : ''} onchange="cmSet({auto_draft:this.checked})">Hneď pripraviť návrhy odpovedí od AI (míňa trochu Claude limitu, odoslanie aj tak schvaľuješ ty)</label>
    <label class="row" style="margin:6px 0"><input type="checkbox" ${st.tiktok ? 'checked' : ''} onchange="cmSet({tiktok:this.checked})">TikTok komentáre (zapni až keď ich TikTok v Business portáli schváli, potom účty pripoj znova)</label>
    <div class="row" style="margin:6px 0">Sledovať videá zverejnené za posledných <input type="number" min="1" max="90" value="${st.days}" style="width:70px" onchange="cmSet({days:+this.value})"> dní</div>
    <div class="hint" style="margin-top:12px">${I('alert')}<div>Čo treba, aby to fungovalo:<br>
      <b>YouTube:</b> raz pripoj kanály znova (appka si pýta nové povolenie na komentáre).<br>
      <b>Facebook a Instagram:</b> nový token s právami pages_read_engagement, pages_read_user_content, pages_manage_engagement a instagram_manage_comments, vlož ho v Účtoch.<br>
      <b>TikTok:</b> len cez TikTok API for Business, v portáli pridať comment.list a comment.list.manage.<br>
      <b>LinkedIn:</b> len firemné stránky. Pri osobnom profile LinkedIn čítanie komentárov nedovolí.</div></div>
  </div>`;
}

async function cmFetch() { const r = await api('/api/comments/fetch', { method: 'POST' }, 'Načítavam komentáre zo všetkých účtov…'); toast(r.busy ? 'Už sa načítava, chvíľu počkaj' : `Nových komentárov: ${r.new}` + (r.errors ? ` · ${r.errors} účtov s chybou` : '')); render(); }
async function cmDraft(ids) { const r = await api('/api/comments/draft', { method: 'POST', body: { ids: ids || null } }, 'AI pripravuje odpovede…'); toast(`Návrhy: ${r.drafted}` + (r.skipped ? ` · preskočených (spam, bez potreby odpovede): ${r.skipped}` : '')); render(); }
async function cmSave(id) { await api('/api/comments/' + id, { method: 'PUT', body: { reply: $('#cmr' + id).value } }); }
async function cmSkip(id) { await api('/api/comments/' + id, { method: 'PUT', body: { status: 'skip' } }); render(); }
async function cmSend(id) {
  const t = $('#cmr' + id).value.trim(); if (!t) return toast('Odpoveď je prázdna', true);
  await api('/api/comments/' + id, { method: 'PUT', body: { reply: t } });
  const r = await api('/api/comments/send', { method: 'POST', body: { ids: [id] } }, 'Odosielam…');
  toast(r.sent ? 'Odoslané' : 'Nepodarilo sa odoslať', !r.sent); render();
}
async function cmSendAll(n) {
  if (!confirm(`Odoslať ${n} odpovedí tak, ako sú teraz napísané?`)) return;
  const r = await api('/api/comments/send', { method: 'POST', body: { all_drafts: true } }, 'Odosielam odpovede…');
  toast(`Odoslané: ${r.sent}` + (r.failed ? ` · chyby: ${r.failed}` : ''), !!r.failed); render();
}
async function cmSet(v) { await api('/api/comments/settings', { method: 'POST', body: v }); toast('Uložené'); }

// ---------- Hlavná stránka: nové komentáre zo všetkých projektov ----------
async function homeComments(el) {
  if (!el) return;
  let d; try { d = await api('/api/comments/summary'); } catch (e) { el.innerHTML = ''; return; }
  if (!el.isConnected) return;
  const lp = (() => { try { return +localStorage.getItem('lastP'); } catch (e) { return 0; } })();
  const pid = (S.projects.find(x => x.id === lp) || S.projects[0] || {}).id;
  const all = pid ? `#/p/${pid}/komentare?f=new&all=1` : '#/';
  el.innerHTML = `<div class="row" style="flex-wrap:wrap;gap:10px;margin-bottom:10px"><h2 style="margin:0;flex:1">${I('message')}Komentáre</h2>
      <span class="chip ${d.open ? 'acc' : ''}">${d.open} nezodpovedaných</span><span class="chip">${d.day} za 24 h</span>
      <a class="btn sec sm" href="${all}">${I('right', 's')}Všetky komentáre</a></div>
    ${d.latest.length ? d.latest.map(c => `<div class="hcm"><div class="small dim row" style="gap:6px;flex-wrap:wrap">${plat(c.platform, false)}<span class="dot" style="display:inline-block;width:7px;height:7px;border-radius:2px;background:${c.project_color}"></span>${esc(c.project_name || '')} · ${esc(c.account_name)}${c.post_title ? ' · ' + esc(c.post_title) : ''}<span style="flex:1"></span>${cmWhen(c.created)}</div>
      <div class="row" style="gap:10px;align-items:flex-start;margin-top:4px"><div style="flex:1"><b>${esc(c.author || 'Niekto')}:</b> ${esc(c.text)}${c.text_sk ? `<div class="small muted">Po slovensky: ${esc(c.text_sk)}</div>` : ''}</div>
      ${cmLink(c) ? `<a class="btn ghost sm" href="${esc(cmLink(c))}" target="_blank">${I('ext', 's')}Odpovedať</a>` : ''}</div></div>`).join('')
      : empty('message', 'Žiadne nezodpovedané komentáre.' + (d.last ? ' Naposledy načítané ' + esc(d.last) + '.' : ' Načítavajú sa samé každé 2 hodiny.'))}`;
}
