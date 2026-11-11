// Nastavenia → Zvuk videí: hudba v pozadí, jej hlasitosť, zvukové efekty a čítanie čísel podľa gramatiky
let SOUND = null, sndAudio = null;
function soundCard() {
  setTimeout(soundLoad, 0);
  return `<div class="card" id="soundCard"><h2>${I('volume')}Zvuk videí</h2>
    <p class="small muted">Každé video dostane tichú hudbu pod hlas (keď hlas hovorí, hudba sa sama stíši), jemný zvuk pri zmene scény a hlasitosť vyrovnanú tak, ako to majú videá na TikToku, Instagrame a YouTube. Hudba je zabudovaná a zadarmo; keď si dáš vlastnú do priečinka Hudba, použije sa tá.</p>
    <div id="soundBody" class="small dim">Načítavam…</div></div>`;
}
async function soundLoad() {
  const b = $('#soundBody'); if (!b) return;
  SOUND = await api('/api/sound');
  const o = SOUND, opt = (v, t, cur) => `<option value="${v}" ${v === cur ? 'selected' : ''}>${t}</option>`;
  b.className = '';
  b.innerHTML = `<div class="g2"><div><label class="l">Hudba</label><select id="sndMusic" onchange="soundSave()">${Object.entries(o.moods).map(([k, t]) => opt(k, t, o.music)).join('')}</select></div>
    <div><label class="l">Hlasitosť hudby</label><select id="sndLevel" onchange="soundSave()">${opt('low', 'Tichšia', o.level)}${opt('mid', 'Stredná', o.level)}${opt('high', 'Výraznejšia', o.level)}</select></div></div>
    <label class="row" style="margin-top:12px"><input type="checkbox" id="sndFx" ${o.fx ? 'checked' : ''} onchange="soundSave()"> Jemné zvukové efekty (začiatok videa a zmena scény)</label>
    <label class="row" style="margin-top:8px"><input type="checkbox" id="sndNum" ${o.numbers?.on ? 'checked' : ''} onchange="soundSave()"> Čísla a jednotky čítať podľa gramatiky každého jazyka (2 percentá → „dve percentá“, 2 kW → „dva kilowatty“)</label>
    <p class="small dim" style="margin:4px 0 0 24px">Robí to Claude z tvojho plánu: posiela len vety, v ktorých je číslo, všetky jazyky naraz, a každú vetu si zapamätá. Titulky ostanú napísané číslicami. Zapamätaných viet: ${o.numbers?.sentences || 0}.</p>
    <label class="l" style="margin-top:14px">Vypočuj si zabudovanú hudbu</label>
    <div class="row">${['calm', 'drive', 'ambient'].map(k => `<button class="btn sec sm" onclick="soundPlay('${k}',this)">${I('play', 's')}${o.moods[k]}</button>`).join('')}</div>
    <p class="small dim" style="margin-top:10px">Tvojich skladieb v priečinku Hudba: <b>${o.own || 0}</b>. Zmena platí pre videá, ktoré vyrobíš odteraz.</p>`;
}
async function soundSave() {
  SOUND = { ...SOUND, ...(await api('/api/sound', { method: 'POST', body: { music: $('#sndMusic').value, level: $('#sndLevel').value, fx: $('#sndFx').checked, numbers: $('#sndNum').checked } })) };
  toast('Uložené');
}
function soundPlay(k, btn) {
  const same = sndAudio && sndAudio._k === k && !sndAudio.paused;
  if (sndAudio) sndAudio.pause();
  if (same) return;
  sndAudio = new Audio('/api/sound/sample/' + k); sndAudio._k = k; sndAudio.volume = 0.6; sndAudio.play();
}
