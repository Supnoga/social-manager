// ================= OBRÁZKY, LOGÁ A SÚBORY ZNAČKY (v Popise a dizajne projektu) =================
IC.image = '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/>';
IC.star = '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>';
const BRAND_ACCEPT = 'image/*,.svg,.heic,.heif,.avif,video/*,.mp4,.mov,.m4v,.webm,.ttf,.otf,.woff,.woff2,.pdf,.md,.markdown,.txt';

async function brandCard(pid) {
  const el = $('#brandCard'); if (!el) return;
  const d = await api('/api/brand/' + pid);
  const by = k => d.assets.filter(a => k.includes(a.kind));
  const t = Date.now();
  const tile = a => {
    const img = ['logo', 'photo', 'font'].includes(a.kind);
    const pv = img ? `<img src="/api/brand/file/${a.id}?preview=1&${t}" class="${a.kind}">`
      : a.kind === 'video' ? `<video src="/api/brand/file/${a.id}#t=0.5" muted preload="metadata"></video>` : `<div class="bicon">${I('file', 'l')}</div>`;
    const acts = [
      ['logo', 'font'].includes(a.kind) && !a.main ? `<button class="btn ghost sm ic" title="Použiť ako hlavné" onclick="brandEdit(${pid},${a.id},{main:1})">${I('star', 's')}</button>` : '',
      a.kind === 'photo' ? `<button class="btn ghost sm ic" title="Je to logo" onclick="brandEdit(${pid},${a.id},{kind:'logo'})">${I('palette', 's')}</button>` : '',
      a.kind === 'logo' ? `<button class="btn ghost sm ic" title="Je to fotka, nie logo" onclick="brandEdit(${pid},${a.id},{kind:'photo'})">${I('image', 's')}</button>` : '',
      `<button class="btn ghost sm ic" title="Odstrániť" onclick="brandDel(${pid},${a.id})">${I('trash', 's')}</button>`].join('');
    return `<div class="btile">${pv}<div class="bname" title="${esc(a.name)}">${a.main ? `<span class="chip">hlavné</span> ` : ''}${esc(a.name)}</div>
      ${['photo', 'video'].includes(a.kind) ? `<input class="bnote" value="${esc(a.note || '')}" placeholder="Čo je na nej (napr. tepelné čerpadlo pri dome)" onchange="brandEdit(${pid},${a.id},{note:this.value},1)">` : a.note ? `<div class="small dim">${esc(a.note)}</div>` : ''}
      <div class="row bacts">${acts}</div></div>`;
  };
  const sec = (title, list, hint) => list.length ? `<h3 class="bh">${title} <span class="chip">${list.length}</span></h3>${hint ? `<p class="small dim">${hint}</p>` : ''}<div class="btiles">${list.map(tile).join('')}</div>` : '';
  const o = d.opts, ck = (k, txt) => `<label><input type="checkbox" ${o[k] ? 'checked' : ''} onchange="brandOpt(${pid},'${k}',this.checked)">${txt}</label>`;
  el.innerHTML = `<h2>${I('image')}Obrázky, logá a súbory značky</h2>
    <p class="muted small">Pretiahni sem logo, fotky produktov, videá, fonty alebo PDF brand manuál. Logo sa samo dá do videí a na profilovky účtov, fotky a videá sa použijú ako zábery vo videách tohto projektu. Bez AI, nič to nestojí.</p>
    <div class="drop" id="brandDrop">${I('upload', 'l')}<div style="margin-top:6px">Pretiahni sem súbory alebo klikni</div><div class="small dim" style="margin-top:4px">PNG, JPG, SVG, WebP, HEIC (iPhone), GIF, MP4, MOV, TTF, OTF, WOFF, PDF, MD</div><input type="file" id="brandIn" multiple accept="${BRAND_ACCEPT}" class="hidden"></div>
    ${d.assets.length ? `<div class="pick" style="margin-top:12px">${ck('logo_corner', 'Logo v rohu videa')}${ck('logo_end', 'Logo na konci videa')}${ck('photos_often', 'Fotky značky v každom videu')}</div>` : ''}
    ${sec('Logá', by(['logo']), 'Hlavné logo ide do videí a na profilovku. Tmavé logo dostane bielu podložku, aby ho bolo vidieť.')}
    ${sec('Fotky a videá', by(['photo', 'video']), 'Napíš ku každej, čo je na nej – appka ju potom dá k scéne, ktorá o tom hovorí.')}
    ${sec('Fonty', by(['font']), 'Titulky a texty vo videách budú v hlavnom fonte (ak má písmená daného jazyka).')}
    ${sec('Dokumenty', by(['pdf']), 'Text z PDF sa pridal k dizajnu značky.')}`;
  const drop = $('#brandDrop'), fin = $('#brandIn');
  drop.onclick = () => fin.click();
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
  drop.ondragleave = () => drop.classList.remove('over');
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over'); brandUpload(pid, e.dataTransfer.files); };
  fin.onchange = () => brandUpload(pid, fin.files);
}

// SVG prevedie na PNG priamo v prehliadači (spoľahlivé a bez ďalších programov)
async function svgToPng(file) {
  const txt = await file.text();
  const vb = txt.match(/viewBox=["']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)/i);
  const url = URL.createObjectURL(new Blob([txt], { type: 'image/svg+xml' }));
  try {
    const img = new Image();
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url; });
    let w = img.naturalWidth, h = img.naturalHeight;
    if (vb) { const r = +vb[2] / +vb[1]; w = w || 1000; h = w * r; }
    if (!w || !h) { w = 1000; h = 1000; }
    const s = 1600 / Math.max(w, h), c = document.createElement('canvas');
    c.width = Math.round(w * s); c.height = Math.round(h * s);
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    const blob = await new Promise(res => c.toBlob(res, 'image/png'));
    return blob ? new File([blob], file.name.replace(/\.svg$/i, '') + '.svg.png', { type: 'image/png' }) : null;
  } catch { return null; } finally { URL.revokeObjectURL(url); }
}

async function brandUpload(pid, files) {
  files = [...files]; if (!files.length) return;
  const fd = new FormData();
  for (const f of files) {
    fd.append('files', f);
    if (/\.svg$/i.test(f.name)) { const p = await svgToPng(f); if (p) fd.append('files', p); }
  }
  const r = await api(`/api/brand/${pid}/upload`, { method: 'POST', body: fd }, 'Nahrávam súbory…');
  const ok = r.added.length + r.texts;
  toast((ok ? `Pridané: ${ok}` : 'Nič nepridané') + (r.errors.length ? ' · ' + r.errors.join('; ') : ''), !!r.errors.length);
  render();
}
async function brandEdit(pid, aid, body, quiet) { await api('/api/brand/asset/' + aid, { method: 'PUT', body }); if (quiet) toast('Uložené'); else brandCard(pid); }
async function brandDel(pid, aid) { if (!confirm('Odstrániť tento súbor?')) return; await api('/api/brand/asset/' + aid, { method: 'DELETE' }); render(); }
async function brandOpt(pid, k, v) { await api(`/api/brand/${pid}/opts`, { method: 'PUT', body: { [k]: v } }); toast('Uložené'); }
