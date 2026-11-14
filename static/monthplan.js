// ================= MESAČNÝ PLÁN (1.64) =================
// Každý kanál: každý deň 1 dlhé video + jeho 3 krátke. Zostavuje sa bez AI z nápadov v appke.
const MP_COVER = { model: ['ok', 'presný model'], verify: ['warn', 'overí sa pri skladaní'], gap: ['bad', 'chýba téma'] };
const mpDay = d => { const x = new Date(d + 'T12:00:00'); return ['ne', 'po', 'ut', 'st', 'št', 'pi', 'so'][x.getDay()] + ' ' + d.slice(8, 10) + '.' + d.slice(5, 7) + '.'; };
const mpModel = m => m ? (({ piston: 'piestový motor', wankel: 'rotačný motor', rotary: 'rotačný motor', gears: 'ozubené kolesá', turbo: 'turbo', camshaft: 'vačkový hriadeľ', car_brake: 'brzda', gearbox: 'prevodovka', differential: 'diferenciál', heatpump: 'tepelné čerpadlo', wind_turbine: 'veterná turbína', solar: 'solárny panel' })[m] || m) : '';

async function mpBuild(pid) {
  await api('/api/month-plan/build', { method: 'POST', body: pid ? { project_ids: [pid] } : {} }, 'Skladám mesačný plán z nápadov (bez AI)…');
  toast('Plán je hotový'); render();
}

function mpSummaryRow(p) {
  const s = p.summary || {}, n = s.long_slots || p.days.length || 30;
  const bar = k => `<div style="width:${(s[k] || 0) / n * 100}%;background:${k === 'model' ? 'var(--ok, #2fbf71)' : k === 'verify' ? '#d9a400' : '#ff4d4d'}"></div>`;
  const miss = Object.entries(s.missing || {}).map(([m, c]) => `${esc(mpModel(m))} ${c}`).join(', ');
  return `<tr onclick="go('p/${p.id}/plan')" style="cursor:pointer"><td><b style="color:#fff">${esc(p.name)}</b><div class="small dim">${p.machine ? 'kanál o strojoch' : 'iné témy'}${p.spare ? ' · v zálohe ' + p.spare + ' tém' : ''}</div></td>
    <td style="width:38%"><div style="display:flex;height:10px;border-radius:5px;overflow:hidden;background:#222">${bar('model')}${bar('verify')}${bar('gap')}</div>
      <div class="small dim" style="margin-top:4px">${s.longs || 0} dlhých (${s.model || 0} s modelom, ${s.verify || 0} overí sa) · ${s.shorts || 0} krátkych${s.gap ? ` · <span style="color:#ff8080">${s.gap} chýba</span>` : ''}</div></td>
    <td class="small dim">${miss ? 'chýbajú modely: ' + miss : ''}</td><td style="text-align:right">${I('right', 's')}</td></tr>`;
}

async function pMonthPlan(m) {
  const d = await api('/api/month-plan');
  const ps = d.projects;
  const tot = k => ps.reduce((a, p) => a + ((p.summary || {})[k] || 0), 0);
  m.innerHTML = `<div class="top"><div><h1>${I('calendar')}Mesačný plán</h1>
    <p class="muted">Každý kanál: 1 krátke video denne (18:00) a dlhé každý 3. deň (14:00), kanály sa pri dlhých striedajú. 3 krátke patria k dlhému: prvé ide v jeho deň po ňom, ďalšie 2 dni potom. Plán sa skladá z nápadov, ktoré už máš, bez AI a nič sa podľa neho zatiaľ nevyrába ani nenahráva.</p></div>
    <span class="sp"></span><button class="btn" onclick="mpBuild(0)">${I('refresh')}Zostaviť plán</button></div>
    ${ps.length ? `<div class="card"><div class="row" style="gap:18px;margin-bottom:10px"><span>Od <b>${esc(d.start)}</b> na ${d.days} dní</span>
      <span class="chip">${tot('longs')} dlhých · ${tot('shorts')} krátkych</span><span class="chip ok">${tot('model')} dlhých s presným modelom</span><span class="chip warn">${tot('verify')} overí sa pri skladaní</span>${tot('gap') ? `<span class="chip bad">${tot('gap')} chýba téma</span>` : ''}
      <span class="sp"></span><span class="small dim">zostavené ${esc(d.built)}</span></div>
      <table>${ps.map(mpSummaryRow).join('')}</table></div>
      <p class="small dim">Zelená: video ukáže presný model stroja. Žltá: téma bez stroja, obraz skontroluje appka pri skladaní a video, ktoré neprejde, ostane zadržané (plán vezme ďalšiu tému). Červená: na ten deň zatiaľ nie je téma s dobrým obrazom.</p>`
      : empty('calendar', 'Plán ešte nie je zostavený. Klikni na „Zostaviť plán“.')}`;
}

async function pProjectPlan(m, p) {
  const d = await api('/api/month-plan?project_id=' + p.id);
  const x = d.projects[0];
  const chip = c => c ? `<span class="chip ${MP_COVER[c.cover][0]}">${c.cover === 'model' ? esc(mpModel(c.model)) : MP_COVER[c.cover][1]}</span>` : '';
  const shortTxt = (s, r) => !s ? (r && r.wait ? '<span class="small dim">kanál začína až svojím prvým dlhým videom</span>' : '<span class="small" style="color:#ff8080">krátke chýba</span>')
    : s.idea_id ? `${FMT('short')} <span class="small">${esc(s.title)}</span>${s.script ? '' : ' <span class="small dim">· scenár až pri výrobe</span>'}`
    : `${FMT('short')} <span class="small dim">výrez ${s.cut} z „${esc(s.title)}“</span>`;
  const row = r => `<tr${r.long ? ' style="background:rgba(255,107,0,.06)"' : ''}><td style="width:90px;white-space:nowrap" class="small muted">${mpDay(r.date)}</td>
    <td>${r.long ? `<div style="margin-bottom:4px"><span class="small dim">14:00</span> ${FMT('long')} <a href="#/p/${p.id}/v/${r.long.idea_id}" style="color:#fff">${esc(r.long.title)}</a>${r.long.script ? '' : ' <span class="small dim">· scenár až pri výrobe</span>'}</div>` : r.long_gap ? '<div class="small" style="color:#ff8080;margin-bottom:4px">dlhé video: zatiaľ nie je téma s dobrým obrazom</div>' : ''}
      <div>${r.short ? '<span class="small dim">18:00</span> ' : ''}${shortTxt(r.short, r)}</div></td>
    <td style="text-align:right;white-space:nowrap">${chip(r.long || r.short)}</td></tr>`;
  m.innerHTML = `<div class="top"><div>${pTitle('Plán na mesiac')}
    <p class="muted">1 krátke video denne o 18:00, dlhé každý 3. deň o 14:00 a jeho 3 krátke v ten deň po ňom a 2 dni potom. ${x ? `Od ${esc(d.start)} na ${d.days} dní.` : ''}</p></div>
    <span class="sp"></span><a class="btn ghost" href="#/plan">${I('layers')}Všetky kanály</a><button class="btn" onclick="mpBuild(${p.id})">${I('refresh')}Zostaviť znova</button></div>
    ${x ? `<div class="card">${(() => { const s = x.summary; const miss = Object.entries(s.missing || {}).map(([k, c]) => esc(mpModel(k)) + ' ' + c).join(', ');
      return `<div class="row" style="gap:10px;margin-bottom:10px"><span class="chip">${s.longs} dlhých · ${s.shorts} krátkych</span><span class="chip ok">${s.model} s modelom</span><span class="chip warn">${s.verify} overí sa</span>${s.gap ? `<span class="chip bad">${s.gap} chýba</span>` : ''}<span class="chip">${s.scripts_ready} dlhých má hotový scenár</span>${x.spare ? `<span class="chip">${x.spare} tém v zálohe</span>` : ''}</div>${miss ? `<p class="small dim">Témy čakajú na modely: ${miss}.</p>` : ''}`; })()}
      <table>${x.days.map(row).join('')}</table></div>` : empty('calendar', 'Plán pre tento kanál ešte nie je zostavený.')}`;
}
