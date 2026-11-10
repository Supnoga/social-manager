// ================= VZHĽAD ÚČTOV (profilovka, pozadie, popis) =================
IC.user = '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>';

async function pProfiles(m) {
  if (!S.projects.length) { m.innerHTML = `<div class="card">${empty('user', 'Najprv vytvor projekt.')}</div>`; return; }
  const r = R(), pid = S.pf || +r[1] || S.profP || S.projects[0].id; S.profP = pid;
  const p = S.projects.find(x => x.id === pid) || S.projects[0];
  const d = await api('/api/profiles/' + p.id);
  const k = d.kit, t = Date.now();
  const stc = { done: ['hotovo', 'ok'], manual: ['treba ručne', 'acc'], ready: ['pripravené', ''] };
  m.innerHTML = `<div class="top"><div>${pTitle('Vzhľad účtov')}<p class="sub">Profilovka, pozadie a popis naraz pre všetky účty projektu. Popis sa preloží do jazyka každého účtu zadarmo.</p></div><span class="sp"></span>
    ${S.pf ? '' : `<select onchange="go('p/'+this.value+'/profily')" style="max-width:240px">${S.projects.map(x => `<option value="${x.id}" ${x.id === p.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>`}</div>
  <div class="card"><h2>${I('palette')}1. Spoločný vzhľad projektu</h2>
    <div class="g2"><div><label class="l">Profilová fotka (logo, štvorec)</label>
      ${k.avatar_ok ? `<img src="/api/profiles/${p.id}/img/profilovka.jpg?${t}" style="width:96px;height:96px;border-radius:50%;object-fit:cover;display:block;margin-bottom:8px">` : ''}
      <input type="file" id="pfA" accept="image/*"></div>
      <div><label class="l">Pozadie / banner (najlepšie široký obrázok, aspoň 2560 px)</label>
      ${k.banner_ok ? `<img src="/api/profiles/${p.id}/img/pozadie-youtube.jpg?${t}" style="width:100%;max-height:110px;object-fit:cover;border-radius:10px;display:block;margin-bottom:8px">` : ''}
      <input type="file" id="pfB" accept="image/*"></div></div>
    <label class="l">Popis (bio) – napíš raz v jazyku</label>
    <div class="row"><select id="pfL" style="max-width:180px">${S.meta.languages.map(l => `<option value="${l.code}" ${l.code === k.lang ? 'selected' : ''}>${l.name}</option>`).join('')}</select></div>
    <textarea id="pfBio" style="margin-top:8px" placeholder="Krátko: čo tu ľudia nájdu a prečo sledovať. Prvých 80 znakov je najdôležitejších (TikTok viac neukáže).">${esc(k.bio || '')}</textarea>
    <div class="small dim" id="pfCnt"></div>
    <div class="row" style="margin-top:10px"><button class="btn" onclick="pfSave(${p.id})">${I('check')}Uložiť a pripraviť obrázky</button>
      <button class="btn sec" onclick="pfTexts(${p.id})">${I('globe')}Preložiť popis do jazykov účtov</button></div>
    ${d.mt ? '' : `<p class="small dim">${I('alert', 's')} Na preklad treba bezplatný prekladač (Nastavenia → Preklady zadarmo). Bez neho dostanú účty popis v origináli.</p>`}
    <p class="small dim">Obrázky appka sama oreže na presné rozmery každej siete (profilovka 800×800, YouTube 2560×1440, Facebook 1640×624, LinkedIn 1584×396).</p></div>
  <div class="card" style="margin-top:14px"><div class="row"><h2 style="margin:0">${I('user')}2. Účty <span class="chip">${d.accounts.length}</span></h2><span class="sp"></span>
    <button class="btn sec sm" onclick="api('/api/profiles/${p.id}/open',{method:'POST'})">${I('folder', 's')}Otvoriť obrázky</button>
    <button class="btn sm" onclick="pfApply(${p.id})">${I('zap', 's')}Nastaviť označeným</button></div>
    <p class="small muted">Samo sa nastaví: <b>YouTube</b> popis a pozadie, <b>Facebook</b> popis, pozadie aj profilovka. <b>Instagram, TikTok a LinkedIn</b> zmenu zvonka nedovolia – pri nich máš pripravený text na skopírovanie, obrázky v priečinku a odkaz priamo na úpravu profilu.</p>
    ${d.accounts.length ? `<table><tr><th><input type="checkbox" checked onchange="$$('.pfS').forEach(c=>c.checked=this.checked)"></th><th>Účet</th><th>Popis</th><th></th></tr>${d.accounts.map(a => `<tr>
      <td style="vertical-align:top"><input type="checkbox" class="pfS" value="${a.id}" checked></td>
      <td style="vertical-align:top;width:190px">${plat(a.platform)}<div class="small">${esc(a.name)}</div><div class="small dim">${esc(langName(a.lang))}</div>
        ${a.status ? `<span class="chip ${stc[a.status]?.[1] || ''}" style="margin-top:6px">${stc[a.status]?.[0] || a.status}</span>` : ''}</td>
      <td><textarea rows="2" data-pa="${a.id}" maxlength="${a.max}" onchange="api('/api/profiles/account/${a.id}',{method:'PUT',body:{bio:this.value}})" oninput="this.nextElementSibling.textContent=this.value.length+' / ${a.max}'">${esc(a.bio)}</textarea><div class="small dim">${a.bio.length} / ${a.max}</div>
        ${a.note ? `<div class="small muted">${esc(a.note)}</div>` : ''}</td>
      <td style="vertical-align:top;white-space:nowrap;text-align:right">
        <button class="btn ghost sm" title="Kopírovať popis" onclick="navigator.clipboard.writeText($('[data-pa=&quot;${a.id}&quot;]').value).then(()=>toast('Popis skopírovaný'))">${I('copy', 's')}</button>
        ${a.link ? `<a class="btn ghost sm" title="Otvoriť úpravu profilu" target="_blank" href="${esc(a.link)}">${I('ext', 's')}</a>` : ''}
        ${a.status === 'manual' ? `<button class="btn sec sm" onclick="api('/api/profiles/${p.id}/manual-done/${a.id}',{method:'POST'}).then(render)">${I('check', 's')}Hotovo</button>` : ''}</td></tr>`).join('')}</table>`
      : empty('user', 'V tomto projekte nie sú účty. Priraď ich v Účty a siete.')}</div>`;
  const cnt = () => { const n = $('#pfBio').value.length; $('#pfCnt').textContent = `${n} znakov · Instagram max 150, TikTok 80, Facebook 255 (dlhší popis appka pre ne skráti)`; };
  $('#pfBio').oninput = cnt; cnt();
}
async function pfSave(pid) {
  const fd = new FormData(); fd.append('bio', $('#pfBio').value); fd.append('lang', $('#pfL').value);
  if ($('#pfA').files[0]) fd.append('avatar', $('#pfA').files[0]); if ($('#pfB').files[0]) fd.append('banner', $('#pfB').files[0]);
  await api(`/api/profiles/${pid}/kit`, { method: 'POST', body: fd }, 'Pripravujem obrázky…'); toast('Uložené'); render();
}
async function pfTexts(pid) {
  await pfSave(pid);
  const r = await api(`/api/profiles/${pid}/texts`, { method: 'POST', body: { account_ids: $$('.pfS:checked').map(c => +c.value) } }, 'Prekladám popisy…');
  toast(`Popisy pre ${r.done} účtov` + (r.errors.length ? ' · nepreložené: ' + r.errors.join('; ') : ''), !!r.errors.length); render();
}
async function pfApply(pid) {
  const ids = $$('.pfS:checked').map(c => +c.value); if (!ids.length) return toast('Označ účty', true);
  const r = await api(`/api/profiles/${pid}/apply`, { method: 'POST', body: { account_ids: ids } }, 'Nastavujem účty…');
  toast(`Nastavené samé: ${r.auto} účtov` + (r.manual.length ? ` · ručne doklikni: ${r.manual.length}` : '') + (r.errors.length ? ' · chyby: ' + r.errors.join('; ') : ''), !!r.errors.length); render();
}
