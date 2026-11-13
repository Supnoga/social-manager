// ---------- general_a: rebríček, súboj, postup, strom, sieť, matica 2x2 ----------
(()=>{
const GA_isI=n=>typeof n=='string'&&n.length>0&&!!(ICONS[n]||ICON_ALIAS[n]||ICONS[n.toLowerCase().replace(/[ -]+/g,'_')]);
const GA_ic=(n,sz,col,x,y,sw)=>{const s=icon(n,sz,col,sw);s.style.left=x+'px';s.style.top=y+'px';return s};
const GA_dash=(p,x)=>{if(!p)return;p.style.strokeDasharray='1 1';p.style.strokeDashoffset=1-cl(x)};
const GA_pop=(e,p)=>{e.style.opacity=cl(p*1.6);e.style.transform=`scale(${.6+.4*E(p)+.06*Math.sin(Math.PI*cl(p))})`};
const GA_num=(v,dec)=>{const a=Math.abs(v);if(a>=1e5){try{return new Intl.NumberFormat(D.lang||'en',{notation:'compact',maximumSignificantDigits:3}).format(v)}catch(e){}}return NF(v,dec)};
const GA_shrink=(s,fs,mn,ok)=>{s.style.hyphens='manual';s.style.webkitHyphens='manual';s.style.fontSize=fs+'px';let f=fs;const m1=Math.max(mn,Math.round(fs*.75));while(f>m1&&!ok()){f--;s.style.fontSize=f+'px'}if(!ok()){s.style.hyphens='auto';s.style.webkitHyphens='auto';f=fs;s.style.fontSize=f+'px';while(f>mn&&!ok()){f--;s.style.fontSize=f+'px'}}return f};
const GA_txt=x=>String(x==null?'':x);
const GA_one=(e,max,min,w)=>{e.style.whiteSpace='nowrap';e.style.overflow='hidden';e.style.textOverflow='ellipsis';e.style.width=w+'px';let f=max;e.style.fontSize=f+'px';while(f>min&&e.scrollWidth>w+1){f--;e.style.fontSize=f+'px'}return e};

// ===== RANK: rebríček, pruhy rastú od posledného miesta k #1 =====
V.rank=(v,d)=>{let I=(Array.isArray(d.i)?d.i:[]).map((x,j)=>Array.isArray(x)&&x.length>1?{l:GA_txt(x[0]),v:N(x[1]),m:x[2],j}:null).filter(Boolean).slice(0,6);
if(!I.length)return V.text(v,{w:d.l||''});I.sort((a,b)=>b.v-a.v);
const n=I.length,rh=Math.min(124,560/n),max=Math.max(...I.map(o=>o.v),1e-9),dec=Math.max(0,...I.map(o=>decs(o.v))),u=d.u?' '+d.u:'';
const fl=d.fl||{};const mk=o=>fl[o.j]||GA_isI(o.m)||(typeof o.m=='string'&&/^[A-Za-z]{2,3}$/.test(o.m.trim()));const hasM=I.some(mk);
const NW=Math.min(72,rh*.8),X0=NW+(hasM?Math.min(84,rh*.8)+14:6),bh=Math.round(rh*.3),ms=Math.min(64,rh*.62),vfs=rh>=90?36:rh>=75?30:26;
const rows=I.map((o,i)=>{const top=i*rh,first=i==0,col=first?'var(--acc)':'#fff';
const num=el('div','big',`left:0;top:${top}px;width:${NW}px;height:${rh}px;display:flex;align-items:center;justify-content:flex-start;font-size:${Math.min(56,rh*.52)}px;color:${first?'var(--acc)':'#7a7a7a'}`,String(i+1));
const lab=el('div','lab',`left:${X0}px;top:${top+rh*.1}px;width:${864-X0}px;font-size:24px;${first?'color:#fff':''}`,esc(o.l));
const track=el('div','',`position:absolute;left:${X0}px;top:${top+rh*.5}px;height:${bh}px;width:0;background:rgba(255,255,255,.06);border-radius:3px`);
const bar=el('div','',`position:absolute;left:${X0}px;top:${top+rh*.5}px;height:${bh}px;width:0;background:${first?'var(--acc)':i==1?'#bdbdbd':'#6a6a6a'};border-radius:3px;overflow:hidden`);
const sh=el('div','',`position:absolute;top:0;left:-120px;width:90px;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);opacity:0`);if(first)bar.append(sh);
const val=el('div','big',`left:${X0}px;top:${top+rh*.5+bh/2-vfs/2}px;font-size:${vfs}px;white-space:nowrap;color:${col}`,GA_num(o.v,dec)+'<span style="font-size:.6em;color:#9a9a9a;font-weight:700">'+esc(u)+'</span>');
v.append(num,lab,track,bar,val);let m=null;
if(mk(o)){const mx=NW+6,my=top+(rh-ms)/2;
if(fl[o.j]){m=el('img','',`position:absolute;left:${mx}px;top:${top+(rh-ms*.74)/2}px;width:${ms}px;height:${ms*.74}px;border-radius:4px;object-fit:cover;box-shadow:0 2px 10px rgba(0,0,0,.6)`);m.src=fl[o.j]}
else if(GA_isI(o.m)){m=GA_ic(o.m,ms,first?D.acc:'#fff',mx,my,3.4)}
else{m=el('div','big',`left:${mx}px;top:${top+(rh-ms*.7)/2}px;width:${ms}px;height:${ms*.7}px;border:2.5px solid ${first?'var(--acc)':'#8a8a8a'};border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:${Math.round(ms*.32)}px;letter-spacing:1px;color:${first?'var(--acc)':'#dcdcdc'}`,esc(o.m.trim().toUpperCase()))}
v.append(m)}
return {o,num,lab,track,bar,sh,val,m,first}});
rows.forEach(r=>GA_one(r.lab,24,14,864-r.lab.offsetLeft));
const vw=Math.max(...rows.map(r=>r.val.offsetWidth),40),BW=864-X0-vw-18;
return (t,st)=>{rows.forEach((r,i)=>{const k=n-1-i,a=.15+k*.7,p=st(a+.1,.8),q=st(a,.45);
show(r.num,q,10);show(r.lab,q,10);if(r.m){r.m.style.opacity=cl(q*1.5);if(r.m.tagName=='svg')draw(r.m,st(a,.7))}
r.track.style.width=BW*q+'px';const w=BW*r.o.v/max*p;r.bar.style.width=Math.max(0,w)+'px';
r.val.style.left=(X0+w+14)+'px';r.val.style.opacity=cl(p*3);r.val.firstChild.textContent=GA_num(r.o.v*(p>=.999?1:p),p>=.999?dec:(r.o.v*p<100?dec:0));
if(r.first){const f=st(a+1,.6);r.bar.style.boxShadow=`0 0 ${(18+8*Math.sin(t*3))*f}px var(--acc)`;r.sh.style.opacity=f;r.sh.style.left=(((t*.45)%1)*(w+240)-120)+'px';
r.num.style.transform=`scale(${1+.08*f*Math.max(0,Math.sin(t*3))})`}})}};

// ===== VERSUS: súboj dvoch strán, pruhy zo stredu, víťaz riadku svieti =====
V.versus=(v,d)=>{const nm=x=>Array.isArray(x)?GA_txt(x[0]):GA_txt(x);const A=(nm(d.a)||'A').replace(/-/g,'\u2011'),B=(nm(d.b)||'B').replace(/-/g,'\u2011');
const ia=d.ia||(Array.isArray(d.a)&&d.a[1]),ib=d.ib||(Array.isArray(d.b)&&d.b[1]);
const R=(Array.isArray(d.r)?d.r:[]).filter(x=>Array.isArray(x)&&x.length>2).slice(0,5);if(!R.length)return V.compare(v,{a:[A,''],b:[B,'']});
const HH=118,n=R.length,rh=Math.min(124,(560-HH-14)/n),C=432;
const vsr=el('div','',`position:absolute;left:${C-42}px;top:${HH/2-46}px;width:84px;height:84px`);const ring=svg(84,84,`<circle cx="42" cy="42" r="38" fill="none" stroke="var(--acc)" stroke-width="3" stroke-dasharray="10 8"/>`);
const vst=el('div','big',`left:0;top:0;width:84px;height:84px;display:flex;align-items:center;justify-content:center;font-size:32px;color:#fff`,'VS');vsr.append(ring,vst);
const sc=el('div','big',`left:0;top:0;width:84px;height:84px;display:flex;align-items:center;justify-content:center;font-size:28px;color:var(--acc);white-space:nowrap;opacity:0`,'');vsr.append(sc);
const head=[];const side=(name,ic,left)=>{const hs=GA_isI(ic)?78:0;const x0=left?0:864-hs;const g=[];
if(hs){const s=GA_ic(ic,hs,'#fff',x0,HH/2-hs/2-6,3.4);v.append(s);g.push(s)}
const nmE=el('div','big',`left:${left?hs+(hs?14:0):C+56}px;top:${HH/2-56}px;width:${C-56-hs-(hs?14:0)}px;height:100px;display:flex;align-items:center;${left?'':'justify-content:flex-end;text-align:right;'}font-size:44px;text-transform:uppercase;line-height:1.02`,esc(name));
v.append(nmE);fit(nmE,44,20,100,C-62-hs-(hs?14:0));g.push(nmE);return {g,nmE,ic:hs?g[0]:null}};
const SA=side(A,ia,1),SB=side(B,ib,0);v.append(vsr);

let wa=0,wb=0;
const rows=R.map((x,i)=>{const top=HH+14+i*rh,va=N(x[1]),vb=N(x[2]),lo=N(x[4])==1,u=x[3]?' '+GA_txt(x[3]):'',mx=Math.max(Math.abs(va),Math.abs(vb),1e-9);
const win=va==vb?0:((va>vb)!=lo?1:2);if(win==1)wa++;if(win==2)wb++;const dec=Math.max(decs(x[1]),decs(x[2]));
const lab=el('div','lab',`left:0;top:${top}px;width:864px;text-align:center;font-size:22px;color:#a9a9a9`,esc(GA_txt(x[0]))+(lo?' <span style="color:#6a6a6a">▼</span>':''));
const by=top+Math.min(rh*.42,44),bh=Math.max(14,Math.min(36,Math.round(rh*.3))),VW=168,BM=C-8-VW;
const mkBar=(l)=>{const g=el('div','',`position:absolute;top:${by}px;height:${bh}px;width:0;${l?'right:'+(864-C+5)+'px':'left:'+(C+5)+'px'};background:#4a4a4a;border-radius:3px;overflow:hidden`);
const a=el('div','',`position:absolute;inset:0;background:var(--acc);opacity:0`);g.append(a);return {g,a}};
const ba=mkBar(1),bb=mkBar(0);
const mkV=(val,l)=>el('div','big',`top:${by+bh/2-17}px;${l?'left:0':'right:0'};width:${VW}px;${l?'':'text-align:right;'}font-size:34px;white-space:nowrap;color:#bdbdbd`,`<span>${GA_num(val,dec)}</span><span style="font-size:.55em;color:#8a8a8a;font-weight:700">${esc(u)}</span>`);
const ea=mkV(va,1),eb=mkV(vb,0),tk=el('div','',`position:absolute;left:${C-1}px;top:${by-6}px;width:2px;height:${bh+12}px;background:#fff;transform:scaleY(0)`);v.append(lab,ba.g,bb.g,ea,eb,tk);fit(lab,22,13,30,860);[ea,eb].forEach(e=>{e.style.height='40px';fit(e,34,18,40,VW)});
return {lab,tk,ba,bb,ea,eb,va,vb,win,dec,la:BM*Math.abs(va)/mx,lb:BM*Math.abs(vb)/mx}});
return (t,st)=>{const h=st(0,.7);[SA,SB].forEach((s,j)=>{show(s.nmE,h,0);s.nmE.style.transform=`translateX(${(1-h)*(j?40:-40)}px)`;if(s.ic){s.ic.style.opacity=cl(h*2);draw(s.ic,st(0,1))}});
GA_pop(vsr,st(.3,.6));ring.style.transform=`rotate(${t*40}deg)`;ring.style.transformOrigin='42px 42px';
rows.forEach((r,i)=>{const a=.8+i*.6,p=st(a,.6),q=st(a+.45,.35);show(r.lab,st(a-.1,.4),8);r.tk.style.transform=`scaleY(${st(a-.1,.3)})`;
r.ba.g.style.width=r.la*p+'px';r.bb.g.style.width=r.lb*p+'px';r.ea.style.opacity=cl(p*3);r.eb.style.opacity=cl(p*3);
r.ea.firstChild.textContent=GA_num(r.va*p,p>.999?r.dec:0);r.eb.firstChild.textContent=GA_num(r.vb*p,p>.999?r.dec:0);
const lit=(b,e,on)=>{b.a.style.opacity=on?q:0;b.g.style.boxShadow=on&&q>0?`0 0 ${14*q}px var(--acc)`:'none';e.style.color=on&&q>.5?D.acc:'#bdbdbd';e.style.transform=`scale(${on?1+.08*Math.sin(Math.PI*q):1})`;e.style.transformOrigin=e.style.left?'left center':'right center'};
lit(r.ba,r.ea,r.win==1);lit(r.bb,r.eb,r.win==2);if(r.win==0&&q>0){r.ba.g.style.background='#9a9a9a';r.bb.g.style.background='#9a9a9a'}});
const f=st(.8+n*.6+.2,.5);sc.textContent=wa+':'+wb;sc.style.opacity=f;vst.style.opacity=1-f;
SA.nmE.style.color=f>.5&&wa>wb?D.acc:'#fff';SB.nmE.style.color=f>.5&&wb>wa?D.acc:'#fff'}};

// ===== STEPS: postup krok za krokom po ceste, bodka putuje =====
V.steps=(v,d)=>{const I=(Array.isArray(d.i)?d.i:[]).map(x=>Array.isArray(x)?x:[null,x]).filter(x=>x[1]!=null||x[0]).slice(0,6);if(!I.length)return V.text(v,{w:d.l||''});
const n=I.length,two=n>3,c=two?Math.ceil(n/2):n,cw=864/c,r=two?48:58;const Y1=two?150:210,Y2=380;
const pos=I.map((x,i)=>{if(!two||i<c)return [cw*(i+.5),Y1,0];const k=i-c;return [cw*(c-1-k+.5),Y2,1]});
let pd=`M${pos[0][0]-(two?0:0)} ${pos[0][1]}`;for(let i=1;i<n;i++){const a=pos[i-1],b=pos[i];if(a[2]!=b[2]){const xr=Math.min(856,a[0]+cw*.48);pd+=` C${xr} ${a[1]} ${xr} ${b[1]} ${b[0]} ${b[1]}`}else pd+=` L${b[0]} ${b[1]}`}
const s=svg(864,560,`<path class="pth" d="${pd}" fill="none" stroke="#5a5a5a" stroke-width="4" stroke-linecap="round"/>`);v.append(s);
const pth=s.querySelector('.pth'),L=pth.getTotalLength();
const at=pos.map(p=>{let best=0,bd=1e9;for(let k=0;k<=400;k++){const q=pth.getPointAtLength(L*k/400),dd=(q.x-p[0])**2+(q.y-p[1])**2;if(dd<bd){bd=dd;best=L*k/400}}return best});
const dot=el('div','',`position:absolute;width:22px;height:22px;border-radius:50%;background:var(--acc);box-shadow:0 0 18px var(--acc);opacity:0`);
const nodes=I.map((x,i)=>{const [cx,cy,row]=pos[i],last=i==n-1;const g=el('div','',`position:absolute;left:${cx-r}px;top:${cy-r}px;width:${r*2}px;height:${r*2}px;border-radius:50%;background:#000;border:3px solid ${last?'var(--acc)':'#fff'};box-sizing:border-box;opacity:0`);
const ic=GA_isI(x[0])?icon(x[0],r*1.12,last?D.acc:'#fff',3.6):null;if(ic){ic.style.left=(r-3-r*.56)+'px';ic.style.top=(r-3-r*.56)+'px';g.append(ic)}else{g.append(el('div','big',`left:0;top:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:${r*.8}px;color:${last?'var(--acc)':'#fff'}`,String(i+1)))}
const bd=el('div','big',`left:${cx-r*.72-17}px;top:${cy-r*.72-17}px;width:34px;height:34px;border-radius:50%;background:var(--acc);color:#000;font-size:20px;display:flex;align-items:center;justify-content:center;opacity:0`,String(i+1));if(!ic)bd.style.display='none';
const up=two&&row==0,lw=Math.min(cw-14,300),lh=two?84:120;const lb=el('div','lab',`left:${cx-lw/2}px;top:${up?cy-r-14-lh:cy+r+14}px;width:${lw}px;height:${lh}px;display:flex;align-items:${up?'flex-end':'flex-start'};justify-content:center;text-align:center;font-size:24px;line-height:1.15;color:${last?'var(--acc)':'#e6e6e6'};hyphens:auto`,'<span>'+esc(GA_txt(x[1]))+'</span>');lb.lang=D.lang;
v.append(g,bd,lb);const sp=lb.firstChild;GA_shrink(sp,24,13,()=>sp.offsetHeight<=lh+2&&lb.scrollWidth<=lw+2);
return {g,ic,bd,lb}});v.append(dot);
return (t,st)=>{let rev=0;nodes.forEach((o,i)=>{const a=.1+i*.7,p=st(a,.5);if(p>0)rev=i;GA_pop(o.g,p);if(o.ic)draw(o.ic,st(a+.1,.7));GA_pop(o.bd,st(a+.3,.4));show(o.lb,st(a+.15,.5),10)});
const seg=i=>st(.1+i*.7-.35,.4);let lenNow=0;for(let i=1;i<n;i++){const p=seg(i);if(p<=0)break;lenNow=at[i-1]+(at[i]-at[i-1])*p}
pth.style.strokeDasharray=`${lenNow} ${L+10}`;
if(lenNow>4){const per=Math.max(1.6,lenNow/260),u=((t/per)%1),q=pth.getPointAtLength(lenNow*u);dot.style.left=(q.x-11)+'px';dot.style.top=(q.y-11)+'px';dot.style.opacity=Math.min(1,u*8,(1-u)*8);
nodes.forEach((o,i)=>{const dd=Math.abs(lenNow*u-at[i]);if(st(.1+i*.7,.5)>=1)o.g.style.transform=`scale(${1+.1*Math.max(0,1-dd/40)})`;o.g.style.boxShadow=dd<40?`0 0 ${22*(1-dd/40)}px var(--acc)`:'none'})}else dot.style.opacity=0}};

// ===== TREE: hierarchia, koreň hore, deti a vnúčatá, čiary zhora nadol =====
V.tree=(v,d)=>{const root=Array.isArray(d.a)?GA_txt(d.a[0]):GA_txt(d.a||d.l||'');const K=(Array.isArray(d.i)?d.i:[]).map(x=>Array.isArray(x)?x.map(GA_txt):[GA_txt(x)]).filter(x=>x[0]).slice(0,3);
if(!K.length)return V.text(v,{w:root});const c=K.length,cw=864/c,bw=Math.min(c==1?420:400,cw-22),RW=Math.min(480,864),RH=78,CY=170,CH=78,GY0=CY+CH+28,GH=Math.min(70,(560-GY0)/3-12),GG=GH+12;
const box=(x,y,w,h,txt,kind)=>{const e=el('div','',`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;box-sizing:border-box;border-radius:12px;background:#0b0b0b;border:${kind==0?3:2}px solid ${kind==0?'var(--acc)':kind==1?'#fff':'#555'};display:flex;align-items:center;justify-content:center;padding:0 12px;opacity:0`);
const s=el('div','',`position:relative;text-align:center;font-weight:${kind==2?700:800};text-transform:uppercase;letter-spacing:${kind==2?1.5:1}px;line-height:1.08;color:${kind==0?'var(--acc)':kind==1?'#fff':'#cfcfcf'};hyphens:auto`,esc(txt));s.lang=D.lang;e.append(s);v.append(e);
GA_shrink(s,kind==0?36:kind==1?28:22,kind==2?12:14,()=>s.offsetHeight<=h-8&&s.scrollWidth<=w-22);return e};
const RX=432-RW/2;let paths=`<path class="d r0" pathLength="1" d="M432 ${RH} V${CY-36}" stroke="#8a8a8a" stroke-width="3"/>`;
if(c>1)paths+=`<path class="d r1" pathLength="1" d="M${cw/2} ${CY-36} H${864-cw/2}" stroke="#8a8a8a" stroke-width="3"/>`;
K.forEach((k,i)=>{const cx=cw*(i+.5);paths+=`<path class="d c${i}" pathLength="1" d="M${cx} ${CY-36} V${CY}" stroke="#8a8a8a" stroke-width="3"/>`;
const g=k.slice(1).filter(Boolean).slice(0,3);if(g.length){const lx=cx-bw/2+22,ly=GY0+(g.length-1)*GG+GH/2;paths+=`<path class="d g${i}" pathLength="1" d="M${lx} ${CY+CH} V${ly}" stroke="#5a5a5a" stroke-width="2.5"/>`;
g.forEach((_,j)=>{paths+=`<path class="d t${i}_${j}" pathLength="1" d="M${lx} ${GY0+j*GG+GH/2} H${lx+18}" stroke="#5a5a5a" stroke-width="2.5"/>`})}});
const s=svg(864,560,paths);v.append(s);const P=k=>s.querySelector(k);
const rb=box(RX,0,RW,RH,root,0);
const ch=K.map((k,i)=>{const cx=cw*(i+.5),e=box(cx-bw/2,CY,bw,CH,k[0],1);const g=k.slice(1).filter(Boolean).slice(0,3).map((x,j)=>box(cx-bw/2+40,GY0+j*GG,bw-40,GH,x,2));return {e,g,cx}});
const pk=K.map((_,i)=>{const e=el('div','',`position:absolute;width:12px;height:12px;border-radius:50%;background:var(--acc);box-shadow:0 0 12px var(--acc);opacity:0`);v.append(e);return e});
return (t,st)=>{show(rb,st(0,.6),-14);GA_dash(P('.r0'),st(.5,.4));GA_dash(P('.r1'),st(.8,.5));
ch.forEach((o,i)=>{const a=1+i*.9;GA_dash(P('.c'+i),st(a-.1,.3));show(o.e,st(a,.5),-12);GA_dash(P('.g'+i),st(a+.3,.6));
o.g.forEach((e,j)=>{GA_dash(P(`.t${i}_${j}`),st(a+.4+j*.2,.3));show(e,st(a+.45+j*.2,.4),0);e.style.transform=`translateX(${(1-st(a+.45+j*.2,.4))*-16}px)`});
const on=st(a+.5,.5);if(on>0){const u=((t*.5+i*.33)%1),y0=RH,y1=CY-36,y2=CY;let x,y;const L1=y1-y0,L2=Math.abs(o.cx-432),L3=y2-y1,T=L1+L2+L3,q=u*T;
if(q<L1){x=432;y=y0+q}else if(q<L1+L2){x=432+Math.sign(o.cx-432)*(q-L1);y=y1}else{x=o.cx;y=y1+(q-L1-L2)}
pk[i].style.left=(x-6)+'px';pk[i].style.top=(y-6)+'px';pk[i].style.opacity=on*Math.min(1,(1-u)*6)}})}};

// ===== NETWORK: uzly a spojenia, po linkách putujú pakety =====
V.network=(v,d)=>{const I=(Array.isArray(d.i)?d.i:[]).map(x=>Array.isArray(x)?x:[null,x]).slice(0,8);if(I.length<2)return V.icons?V.icons(v,{i:I}):V.text(v,{w:''});const n=I.length;
let Lk=(Array.isArray(d.l)?d.l:[]).filter(x=>Array.isArray(x)&&x.length>1).map(x=>[parseInt(x[0]),parseInt(x[1])]).filter(x=>x[0]>=0&&x[1]>=0&&x[0]<n&&x[1]<n&&x[0]!=x[1]);
if(!Lk.length)Lk=I.slice(1).map((_,i)=>[0,i+1]);Lk=Lk.slice(0,14);
const deg=I.map((_,i)=>Lk.filter(l=>l[0]==i||l[1]==i).length);const hub=deg.indexOf(Math.max(...deg));const isHub=n>=4&&deg[hub]>=Math.max(3,(n-1)*.6)&&deg[hub]>=Lk.length*.7;
const CX=432,CY=290,RX=322,RY=172;const others=isHub?I.map((_,i)=>i).filter(i=>i!=hub):I.map((_,i)=>i);const m=others.length;
const pos=[];others.forEach((ix,k)=>{const an=(-90+360*k/m+(m%2==0?180/m:0))*Math.PI/180;pos[ix]=[CX+RX*Math.cos(an),CY+RY*Math.sin(an)]});if(isHub)pos[hub]=[CX,CY];
let ls='';Lk.forEach((l,k)=>{const a=pos[l[0]],b=pos[l[1]];ls+=`<path class="d l${k}" pathLength="1" d="M${a[0].toFixed(1)} ${a[1].toFixed(1)} L${b[0].toFixed(1)} ${b[1].toFixed(1)}" stroke="#5a5a5a" stroke-width="3"/>`});
const s=svg(864,560,ls);v.append(s);
const pk=Lk.map((l,k)=>[0,1].map(z=>{const e=el('div','',`position:absolute;width:${z?10:14}px;height:${z?10:14}px;border-radius:50%;background:${(k+z)%2?'#fff':'var(--acc)'};${(k+z)%2?'':'box-shadow:0 0 12px var(--acc);'}opacity:0`);v.append(e);return e}));
const nodes=I.map((x,i)=>{const h=isHub&&i==hub,r=h?60:44,[cx,cy]=pos[i];const g=el('div','',`position:absolute;left:${cx-r}px;top:${cy-r}px;width:${r*2}px;height:${r*2}px;border-radius:50%;background:#000;box-sizing:border-box;border:${h?4:3}px solid ${h?'var(--acc)':'#fff'};opacity:0`);
const ic=icon(GA_isI(x[0])?x[0]:'globe',r*1.15,h?D.acc:'#fff',3.6);ic.style.left=(r-(h?4:3)-r*.575)+'px';ic.style.top=(r-(h?4:3)-r*.575)+'px';g.append(ic);
const lw=h?200:Math.min(Math.abs(cx-CX)<60?320:260,cw0(cx)),up=!h&&cy<CY-40;const lb=el('div','lab',`left:${Math.max(0,Math.min(864-lw,cx-lw/2))}px;width:${lw}px;text-align:center;font-size:22px;letter-spacing:1.5px;line-height:1.3;color:${h?'var(--acc)':'#e6e6e6'};opacity:0`,'<span style="background:#000;padding:1px 8px;border-radius:6px;-webkit-box-decoration-break:clone;box-decoration-break:clone">'+esc(GA_txt(x[1]))+'</span>');
v.append(g,lb);fit(lb,22,14,h?90:60,lw);lb.style.top=(up?cy-r-10-lb.offsetHeight:cy+r+10)+'px';
return {g,ic,lb}});
function cw0(cx){return 2*Math.min(cx,864-cx)+40}
const order=isHub?[hub,...others]:others;const ap=[];order.forEach((ix,k)=>ap[ix]=.1+k*.45);
return (t,st)=>{nodes.forEach((o,i)=>{const p=st(ap[i],.5);GA_pop(o.g,p);draw(o.ic,st(ap[i]+.1,.7));show(o.lb,st(ap[i]+.2,.4),0)});
Lk.forEach((l,k)=>{const a0=Math.max(ap[l[0]],ap[l[1]])+.2,p=st(a0,.5);GA_dash(s.querySelector('.l'+k),p);const A=pos[l[0]],B=pos[l[1]],on=st(a0+.4,.4);
pk[k].forEach((e,z)=>{let u=((t*(.32+.05*(k%3))+k*.37+z*.5)%1);if(z)u=1-u;e.style.left=(A[0]+(B[0]-A[0])*u-(z?5:7))+'px';e.style.top=(A[1]+(B[1]-A[1])*u-(z?5:7))+'px';e.style.opacity=on*Math.min(1,u*10,(1-u)*10)})})}};

// ===== MATRIX: kvadrant 2x2, položky podľa x/y, jedna zvýraznená =====
V.matrix=(v,d)=>{const I=(Array.isArray(d.i)?d.i:[]).filter(x=>Array.isArray(x)&&x.length>2).slice(0,6);if(!I.length)return V.text(v,{w:d.a||''});
const L0=40,R0=846,T0=56,B0=478,W=R0-L0,H=B0-T0,cx=L0+W/2,cy=T0+H/2;let hi=I.findIndex(x=>N(x[3])==1);if(hi<0)hi=0;
const ql=(Array.isArray(d.l)?d.l:[]).slice(0,4).map(GA_txt);
const s=svg(864,560,`<rect class="qf" x="0" y="0" width="${W/2}" height="${H/2}" fill="var(--acc)" opacity="0"/>
<path class="d ax" pathLength="1" d="M${L0} ${T0-16} V${B0} H${R0+6}" stroke="#fff" stroke-width="3"/>
<path class="d ay" pathLength="1" d="M${L0-10} ${T0-4} L${L0} ${T0-18} L${L0+10} ${T0-4}" stroke="#fff" stroke-width="3"/>
<path class="d axa" pathLength="1" d="M${R0-8} ${B0-10} L${R0+8} ${B0} L${R0-8} ${B0+10}" stroke="#fff" stroke-width="3"/>
<path class="d mv" pathLength="1" d="M${cx} ${T0} V${B0}" stroke="#5a5a5a" stroke-width="2" stroke-dasharray="1 1"/>
<path class="d mh" pathLength="1" d="M${L0} ${cy} H${R0}" stroke="#5a5a5a" stroke-width="2"/>
<circle class="ring" r="20" fill="none" stroke="var(--acc)" stroke-width="3" opacity="0"/>`);v.append(s);
const xa=el('div','lab',`left:${R0-560}px;top:${B0+16}px;width:576px;text-align:right;font-size:24px;color:#e6e6e6`,esc(GA_txt(d.a))+' →');
const ya=el('div','lab',`left:${L0+20}px;top:${T0-30}px;width:520px;font-size:24px;color:#e6e6e6`,'↑ '+esc(GA_txt(d.b)));v.append(xa,ya);GA_one(xa,24,14,576);GA_one(ya,24,14,520);
const box=[];const qpos=[[L0+14,T0+14,0],[cx+14,T0+14,1],[L0+14,B0-14,0],[cx+14,B0-14,1]];
const qe=ql.map((q,k)=>{const e=el('div','lab',`left:${qpos[k][0]}px;width:${W/2-28}px;font-size:20px;letter-spacing:2px;color:#6f6f6f;${qpos[k][2]?'text-align:right;':''}`,'<span>'+esc(q)+'</span>');v.append(e);GA_one(e,20,12,W/2-28);
e.style.top=(k>1?qpos[k][1]-e.offsetHeight:qpos[k][1])+'px';const sw=Math.min(W/2-28,e.firstChild.offsetWidth),x0=qpos[k][2]?qpos[k][0]+W/2-28-sw:qpos[k][0];box.push([x0-6,e.offsetTop-4,x0+sw+6,e.offsetTop+e.offsetHeight+4]);return e});
// x labels of top-left corner area are skipped by the y-axis label (top above plot), fine
const its=I.map((x,i)=>{const px=L0+W*Math.max(.04,Math.min(.96,N(x[1]))),py=B0-H*(.1+.78*Math.max(0,Math.min(1,N(x[2])))),h=i==hi,r=h?14:10;
const dt=el('div','',`position:absolute;left:${px-r}px;top:${py-r}px;width:${r*2}px;height:${r*2}px;border-radius:50%;background:${h?'var(--acc)':'#fff'};opacity:0`);
const lb=el('div','lab',`font-size:${h?24:21}px;letter-spacing:2px;color:${h?'var(--acc)':'#e6e6e6'};white-space:nowrap;opacity:0`,esc(GA_txt(x[0])));v.append(dt,lb);GA_one(lb,h?24:21,13,300);
return {dt,lb,px,py,r,h}});
const dots=its.map(o=>[o.px-o.r-4,o.py-o.r-4,o.px+o.r+4,o.py+o.r+4]);const ov=(a,b)=>a[0]<b[2]&&b[0]<a[2]&&a[1]<b[3]&&b[1]<a[3];
its.forEach((o,i)=>{const w=o.lb.offsetWidth,h=o.lb.offsetHeight,g=o.r+10;const C=[[o.px+g,o.py-h/2],[o.px-g-w,o.py-h/2],[o.px-w/2,o.py-g-h],[o.px-w/2,o.py+g],[o.px+g,o.py-h-4],[o.px+g,o.py+4],[o.px-g-w,o.py-h-4],[o.px-g-w,o.py+4]];
let best=null,bs=1e9;for(const c of C){const x0=Math.max(L0+6,Math.min(R0-w,c[0])),y0=Math.max(0,Math.min(B0-h-4,c[1])),b=[x0,y0,x0+w,y0+h];let sc=Math.abs(x0-c[0])+Math.abs(y0-c[1]);
box.forEach(q=>{if(ov(b,q))sc+=1000});dots.forEach(q=>{if(ov(b,q))sc+=2000});if(ov(b,[L0-12,B0-2,R0+10,B0+2])||ov(b,[cx-2,T0,cx+2,B0])||ov(b,[L0,cy-2,R0,cy+2]))sc+=60;if(sc<bs){bs=sc;best=b}}
o.lb.style.left=best[0]+'px';o.lb.style.top=best[1]+'px';box.push(best)});
const H_=its[hi],qx=H_.px<cx?L0:cx,qy=H_.py<cy?T0:cy,qf=s.querySelector('.qf');qf.setAttribute('x',qx);qf.setAttribute('y',qy);const ring=s.querySelector('.ring');ring.setAttribute('cx',H_.px);ring.setAttribute('cy',H_.py);
const n=I.length,end=1.3+n*.5;
return (t,st)=>{GA_dash(s.querySelector('.ax'),st(0,.8));GA_dash(s.querySelector('.ay'),st(.6,.3));GA_dash(s.querySelector('.axa'),st(.6,.3));
const m=st(.4,.6);const mv=s.querySelector('.mv'),mh=s.querySelector('.mh');[mv,mh].forEach(p=>{p.style.strokeDasharray='0.012 0.012';p.style.opacity=m;p.style.strokeDashoffset=-t*.01});
show(xa,st(.5,.5),0);show(ya,st(.5,.5),0);qe.forEach((e,k)=>show(e,st(.8+k*.1,.4),0));
its.forEach((o,i)=>{const p=st(1.3+i*.5,.45);GA_pop(o.dt,p);show(o.lb,st(1.4+i*.5,.4),0)});
const f=st(end,.6);qf.setAttribute('opacity',(.13*f).toFixed(3));const pr=(t*.8)%1;ring.setAttribute('r',14+pr*26*f);ring.setAttribute('opacity',(f*(1-pr)).toFixed(3));
H_.dt.style.boxShadow=f>0?`0 0 ${20*f}px var(--acc)`:'none'}};
})();
