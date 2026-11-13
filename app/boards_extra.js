// ---------- časová os: roky na čiare, udalosti sa odkrývajú postupne ----------
V.timeline=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)).slice(0,5);const n=I.length||1;const y0=250,x0=40,x1=824,step=n>1?(x1-x0)/(n-1):0;
const s=svg(864,560,`<path class="d ax" pathLength="1" d="M${x0-20} ${y0} H${x1+20}" stroke="#fff" stroke-width="3"/>`);v.append(s);
const it=I.map((x,i)=>{const cx=n>1?x0+i*step:432,last=i==n-1,up=i%2==0;const dot=el('div','',`position:absolute;left:${cx-13}px;top:${y0-13}px;width:26px;height:26px;border-radius:50%;background:${last?'var(--acc)':'#fff'};transform:scale(0)`);
const xl=Math.max(0,Math.min(864-220,cx-110));const yr=el('div','big',`left:${xl}px;width:220px;text-align:center;top:${up?y0-118:y0+40}px;font-size:56px;${last?'color:var(--acc)':''}`,esc(x[0]));
const lb=el('div','lab',`left:${xl+5}px;width:210px;text-align:center;top:${up?y0-178:y0+108}px;font-size:24px;line-height:1.15;white-space:normal`,esc(x[1]||''));
const tick=el('div','',`position:absolute;left:${cx-1}px;width:2px;top:${up?y0-52:y0+14}px;height:38px;background:rgba(255,255,255,.5);transform-origin:${up?'bottom':'top'};transform:scaleY(0)`);
v.append(tick,dot,yr,lb);fit(yr,56,28,70,220);fit(lb,24,15,up?60:120,210);if(up)lb.style.top=(y0-128-lb.offsetHeight)+'px';return {dot,yr,lb,tick}});
return (t,st)=>{const ax=s.querySelector('.ax');ax.style.strokeDasharray='1 1';ax.style.strokeDashoffset=1-st(0,.8);
it.forEach((o,i)=>{const p=st(.4+i*.8,.6);o.dot.style.transform=`scale(${E(p)})`;o.tick.style.transform=`scaleY(${E(p)})`;show(o.yr,p,14);show(o.lb,st(.6+i*.8,.6),14)})}};
// ---------- vývoj v čase: čiarový graf, ktorý sa nakreslí zľava doprava ----------
V.line=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)&&x.length>1).slice(0,10);if(I.length<2)return V.bars(v,{u:d.u,i:I});
const vals=I.map(x=>N(x[1])),mn=Math.min(0,...vals),mx=Math.max(...vals,1e-9);const L=60,Rr=804,T=70,B=430;const X=i=>L+(Rr-L)*i/(I.length-1),Y=y=>B-(B-T)*(y-mn)/((mx-mn)||1);
const pts=I.map((x,i)=>[X(i),Y(vals[i])]);const dl='M'+pts.map(p=>p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' L');
const s=svg(864,560,`<path class="d ax" pathLength="1" d="M${L-20} ${B} H${Rr+30}" stroke="#fff" stroke-width="3"/>
<path class="ar" d="${dl} L${Rr} ${B} L${L} ${B} Z" fill="var(--acc)" opacity="0"/><path class="d ln" pathLength="1" d="${dl}" stroke="var(--acc)" stroke-width="7" fill="none"/>`);v.append(s);
const dot=el('div','',`position:absolute;width:24px;height:24px;border-radius:50%;background:#fff;box-shadow:0 0 0 8px rgba(255,255,255,.18);opacity:0`);v.append(dot);
const labs=I.map((x,i)=>{const show_=i==0||i==I.length-1||I.length<=6||i%Math.ceil(I.length/5)==0;if(!show_)return null;const e=el('div','lab',`left:${X(i)-60}px;width:120px;text-align:center;top:${B+16}px;font-size:24px`,esc(x[0]));v.append(e);return e}).filter(Boolean);
const first=el('div','big',`left:${Math.max(0,pts[0][0]-80)}px;top:${pts[0][1]-62}px;width:260px;font-size:38px;color:#cfcfcf;white-space:nowrap`);const lastv=el('div','big',`left:${Math.min(864-260,pts[pts.length-1][0]-200)}px;width:260px;text-align:right;font-size:64px;color:var(--acc);white-space:nowrap`);v.append(first,lastv);
const dec=Math.max(...I.map(x=>decs(x[1])));const u=d.u?' '+d.u:'';first.textContent=NF(vals[0],dec)+u;
const ln=s.querySelector('.ln'),tot=ln.getTotalLength?ln.getTotalLength():1;
return (t,st)=>{const ax=s.querySelector('.ax');ax.style.strokeDasharray='1 1';ax.style.strokeDashoffset=1-st(0,.6);labs.forEach((e,i)=>show(e,st(.2+i*.15,.5),0));show(first,st(.5,.5),10);
const p=st(.6,2.2);ln.style.strokeDasharray='1 1';ln.style.strokeDashoffset=1-p;s.querySelector('.ar').setAttribute('opacity',(.16*p).toFixed(3));
let pt=pts[0];try{const q=ln.getPointAtLength(tot*E(p));pt=[q.x,q.y]}catch(e){}dot.style.left=(pt[0]-12)+'px';dot.style.top=(pt[1]-12)+'px';dot.style.opacity=cl(p*4);
const k=Math.min(I.length-1,Math.floor(E(p)*(I.length-1)+.0001));lastv.textContent=NF(p>=1?vals[vals.length-1]:vals[k],dec)+u;lastv.style.top=(Math.max(0,pt[1]-96))+'px';lastv.style.opacity=cl(p*3)}};
