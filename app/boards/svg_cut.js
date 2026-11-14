// "svg": rez / schéma na mieru pre scénu (AI napíše malé animované SVG 864x560 s <animate>/<animateTransform>/<animateMotion>).
// Čas animácie riadi render snímka po snímke (setCurrentTime), takže je presný aj pri skladaní videa.
{
V.svg=(v,d)=>{const s=document.createElementNS(SVGNS,'svg');s.setAttribute('viewBox','0 0 864 560');s.setAttribute('width','864');s.setAttribute('height','560');
s.style.cssText='position:absolute;left:0;top:0;overflow:visible;font-family:var(--ft);font-weight:700;letter-spacing:1px';
s.innerHTML=String(d.svg||'').replace(/\bACC\b/g,D.acc);v.append(s);
s.querySelectorAll('text').forEach(t=>{if(!t.getAttribute('fill'))t.setAttribute('fill','#fff');if(!t.getAttribute('font-size'))t.setAttribute('font-size','26')});
try{s.pauseAnimations()}catch(e){}
return (t,st)=>{try{s.setCurrentTime(Math.max(0,t-.5))}catch(e){}}};
}
