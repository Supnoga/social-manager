// ---------- balíky vizuálov podľa témy kanála (peniaze, technika, veľkosti, vrstvy, pravdepodobnosť) ----------
const GREYS=['#e9e9e9','#9a9a9a','#5c5c5c','#3a3a3a'];
const cv2=(v,w,h)=>{const R=1.6,c=el('canvas','',`position:absolute;left:0;top:0;width:${w}px;height:${h}px`);c.width=w*R;c.height=h*R;v.append(c);const x=c.getContext('2d');x.scale(R,R);x.lineCap='round';x.lineJoin='round';return x};
const SHORT=(v)=>{const a=Math.abs(v);const f=(x,s)=>NF(x,x<10&&x%1?1:0)+s;return a>=1e12?f(v/1e12,' T'):a>=1e9?f(v/1e9,' B'):a>=1e6?f(v/1e6,' M'):a>=1e4?f(v/1e3,' k'):NF(v,v%1?Math.min(2,decs(v)):0)};
// zložené úročenie: appka sama vypočíta každý rok (žiadne vymyslené čísla)
V.growth=(v,d)=>{const P=N(d.p),r=N(d.r)/100,Y=Math.max(1,Math.min(60,Math.round(N(d.y)||10))),M=N(d.m)||0,u=d.u||'';
const pts=[];let bal=P,inv=P;for(let y=0;y<=Y;y++){pts.push([y,bal,inv]);bal=bal*(1+r)+M*12;inv+=M*12}
const K=Math.min(10,Y),idx=Array.from({length:K},(_,i)=>Math.round((i+1)*Y/K));const mx=Math.max(...idx.map(i=>pts[i][1]),1);
const base=430,mh=280,bw=Math.min(64,700/K-14),gap=(864-bw*K)/(K+1);
const s=svg(864,560,`<path class="d ax" pathLength="1" d="M0 ${base} H864" stroke="#fff" stroke-width="3"/>`);v.append(s);
const bars=idx.map((y,i)=>{const L=gap+i*(bw+gap);const a=el('div','',`position:absolute;left:${L}px;width:${bw}px;bottom:${560-base}px;height:0;background:#4a4a4a`),b=el('div','',`position:absolute;left:${L}px;width:${bw}px;height:0;background:var(--acc)`);
const lb=el('div','lab',`left:${L-20}px;width:${bw+40}px;top:${base+14}px;text-align:center;font-size:22px;letter-spacing:1px`,esc(String(y)));v.append(a,b,lb);return {a,b,lb,inv:pts[y][2]/mx*mh,tot:pts[y][1]/mx*mh,L}});
const big=el('div','big',`left:0;top:0;width:864px;text-align:right;font-size:76px;color:var(--acc);white-space:nowrap`);const sub=el('div','lab',`left:0;top:84px;width:864px;text-align:right`,esc(d.l||''));
const key=el('div','lab',`left:0;top:6px;width:520px;font-size:22px;line-height:1.6`,`<span style="display:inline-block;width:18px;height:18px;background:#4a4a4a;margin-right:10px;vertical-align:-2px"></span>${esc(d.a||'paid in')}<br><span style="display:inline-block;width:18px;height:18px;background:var(--acc);margin-right:10px;vertical-align:-2px"></span>${esc(d.b||'interest')}`);
const yl=el('div','lab',`left:0;top:${base+50}px;width:864px;text-align:center;font-size:20px;color:#8a8a8a`,esc(d.x||'years'));v.append(big,sub,key,yl);
return (t,st)=>{const ax=s.querySelector('.ax');ax.style.strokeDasharray='1 1';ax.style.strokeDashoffset=1-st(0,.5);show(key,st(.2,.5),0);show(yl,st(.2,.5),0);
let last=0;bars.forEach((o,i)=>{const p=E(st(.4+i*.22,.5));o.a.style.height=(o.inv*p)+'px';o.b.style.height=((o.tot-o.inv)*p)+'px';o.b.style.bottom=(560-base+o.inv*p)+'px';if(p>0)last=i;show(o.lb,p,0)});
const f=E(st(.4+(K-1)*.22,.5));const cur=pts[idx[last]][1];big.textContent=(d.pre||'')+SHORT(f>=1?pts[Y][1]:cur)+(u?' '+u:'');show(big,st(.4,.4),0);show(sub,st(1,.5),10)}};
// koláč / prstenec: kam idú peniaze, rozpočet, podiely
V.pie=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)).slice(0,5);const tot=I.reduce((s,x)=>s+N(x[1]),0)||1;const cx=250,cy=280,R0=220,r0=128;
const cols=['var(--acc)',...GREYS];const s=svg(864,560,'');v.append(s);let a0=-Math.PI/2;const NS='http://www.w3.org/2000/svg';
const segs=I.map((x,i)=>{const fr=N(x[1])/tot,a1=a0+fr*Math.PI*2;const p=document.createElementNS(NS,'path');p.setAttribute('fill',cols[i%cols.length]);s.append(p);const o={p,a0,a1,fr};a0=a1;return o});
const arc=(o,k)=>{const b=o.a0+(o.a1-o.a0)*k;if(k<=0)return '';const big=b-o.a0>Math.PI?1:0,c=Math.cos,sn=Math.sin;return `M${cx+R0*c(o.a0)} ${cy+R0*sn(o.a0)} A${R0} ${R0} 0 ${big} 1 ${cx+R0*c(b)} ${cy+R0*sn(b)} L${cx+r0*c(b)} ${cy+r0*sn(b)} A${r0} ${r0} 0 ${big} 0 ${cx+r0*c(o.a0)} ${cy+r0*sn(o.a0)} Z`};
const rh=Math.min(110,520/Math.max(1,I.length));const rows=I.map((x,i)=>{const r=el('div','',`position:absolute;left:520px;top:${280-rh*I.length/2+i*rh}px;width:344px;height:${rh}px`);
r.innerHTML=`<div class="big" style="position:relative;font-size:54px;color:${i==0?'var(--acc)':'#fff'}">${esc(NF(N(x[1]),decs(x[1]))+(d.u?' '+d.u:''))}</div><div class="lab" style="position:relative;font-size:22px;margin-top:6px">${esc(x[0])}</div>`;v.append(r);return r});
const mid=el('div','big',`left:${cx-r0}px;width:${r0*2}px;top:${cy-34}px;text-align:center;font-size:52px`,esc(d.c||''));v.append(mid);fit(mid,52,22,70,r0*1.7);
return (t,st)=>{segs.forEach((o,i)=>{const k=E(st(i*.55,.7));o.p.setAttribute('d',arc(o,k))});rows.forEach((r,i)=>show(r,st(.3+i*.55,.5),0));show(mid,st(.2,.6),0)}};
// veľké čísla: plochy štvorcov v správnom pomere (milión vs miliarda)
V.stack=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)&&N(x[1])>0).slice(0,3).sort((a,b)=>N(b[1])-N(a[1]));if(!I.length)return V.text(v,{w:d.l||''});const mx=N(I[0][1]),S=440;
const sq=I.map((x,i)=>{const side=Math.max(3,S*Math.sqrt(N(x[1])/mx));if(side<40){const ring=el('div','',`position:absolute;left:${30+side/2-34}px;top:${500-side/2-34}px;width:68px;height:68px;border-radius:50%;border:3px solid var(--acc);opacity:0`);v.append(ring);setTimeout(()=>0);x.ring=ring}const b=el('div','',`position:absolute;left:30px;top:${500-side}px;width:${side}px;height:${side}px;border:3px solid ${i==0?'#fff':'var(--acc)'};background:${i==0?'rgba(255,255,255,.06)':'var(--acc)'};transform-origin:0 100%;transform:scale(0)`);
const lb=el('div','',`position:absolute;left:510px;top:${60+i*150}px;width:354px`,`<div class="big" style="position:relative;font-size:56px;${i?'color:var(--acc)':''}">${esc((d.pre||'')+SHORT(N(x[1]))+(d.u?' '+d.u:''))}</div><div class="lab" style="position:relative;font-size:22px;margin-top:6px">${esc(x[0])}</div>`);v.append(b,lb);return {b,lb}});
const ratio=I.length>1?mx/N(I[I.length-1][1]):0;const rt=el('div','big',`left:510px;top:${60+I.length*150}px;width:354px;font-size:44px;color:#9a9a9a`,ratio>1?'× '+SHORT(ratio):'');v.append(rt);
return (t,st)=>{sq.forEach((o,i)=>{const p=E(st(i*.9,.8));o.b.style.transform=`scale(${p})`;if(I[i].ring)I[i].ring.style.opacity=cl(p*2)*(.6+.4*Math.sin(t*4));show(o.lb,st(i*.9+.2,.5),12)});show(rt,st(I.length*.9,.5),12)}};
// pravdepodobnosť a podiely: 100 bodiek, zvýraznených toľko, koľko hovorí hlas
V.dots=(v,d)=>{const n=Math.max(10,Math.min(400,Math.round(N(d.n)||100))),h=Math.max(0,Math.min(n,N(d.h)));const cols=n<=100?10:20,rows=Math.ceil(n/cols);const cell=Math.min(46,440/rows,500/cols),R=cell*.36,x0=20,y0=(560-rows*cell)/2;
const x=cv2(v,560,560);const big=el('div','big',`left:560px;top:150px;width:304px;font-size:110px;color:var(--acc);white-space:nowrap`),lb=el('div','lab',`left:560px;top:290px;width:304px;font-size:24px;line-height:1.3`,esc(d.l||''));v.append(big,lb);fit(big,110,40,130,304);fit(lb,24,15,200,304);
const H=Math.floor(h),fr=h-H;
return (t,st)=>{x.clearRect(0,0,560,560);const p=st(0,.8),q=st(.8,1.4);for(let i=0;i<n;i++){const cx=x0+(i%cols)*cell+cell/2,cy=y0+Math.floor(i/cols)*cell+cell/2;const on=i<H*E(q)||(i==H&&fr>0&&q>=1);
const a=cl(p*n/ (i+1)*.15+p*1.2-i/n*.6);x.globalAlpha=cl(a);x.fillStyle=on?D.acc:'#3d3d3d';x.beginPath();x.arc(cx,cy,(i==H&&fr>0&&q>=1)?R*Math.sqrt(fr):R,0,6.3);x.fill()}x.globalAlpha=1;
big.textContent=NF(h*E(q),decs(d.h))+(d.u!=null?d.u:(n==100?' %':' / '+n));show(big,st(.8,.5),10);show(lb,st(1.2,.5),10)}};
// porovnanie veľkostí: výšky budov, dĺžky lodí a lietadiel v správnom pomere
V.size=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)&&N(x[1])>0).slice(0,4);if(!I.length)return V.text(v,{w:''});const mx=Math.max(...I.map(x=>N(x[1])));const hz=d.d=='h';const n=I.length;
const s=svg(864,560,'');v.append(s);const NS='http://www.w3.org/2000/svg';
const items=I.map((x,i)=>{const fr=N(x[1])/mx,last=i==n-1||N(x[1])==mx;let bx,by,bw,bh;if(hz){const rowh=Math.min(130,520/n);bw=Math.max(4,fr*600);bh=Math.min(54,rowh*.45);bx=40;by=30+i*rowh+40}else{const colw=864/n;bh=Math.max(3,fr*290);bw=Math.min(120,colw*.42);bx=colw*i+colw/2-bw/2;by=450-bh}
const r=document.createElementNS(NS,'rect');r.setAttribute('x',bx);r.setAttribute('y',by);r.setAttribute('width',bw);r.setAttribute('height',bh);r.setAttribute('fill',N(x[1])==mx?'var(--acc)':'#e9e9e9');r.setAttribute('opacity','.9');s.append(r);
const ic=x[2]?icon(x[2],hz?60:70,N(x[1])==mx?D.acc:'#fff',3):null;if(ic){ic.style.left=(hz?bx+bw+16:bx+bw/2-35)+'px';ic.style.top=(hz?by+bh/2-30:by-80)+'px';v.append(ic)}
const val=el('div','big',hz?`left:${bx}px;top:${by-44}px;width:600px;font-size:34px`:`left:${bx+bw/2-100}px;width:200px;text-align:center;top:${by-(ic?128:48)}px;font-size:36px`,esc(NF(N(x[1]),decs(x[1]))+(d.u?' '+d.u:'')));
const lb=el('div','lab',hz?`left:${bx+(ic?bw+90:bw+16)}px;top:${by+bh/2-14}px;width:300px;font-size:22px`:`left:${bx+bw/2-100}px;width:200px;text-align:center;top:466px;font-size:22px`,esc(x[0]));v.append(val,lb);fit(lb,22,14,56,hz?300:200);return {r,ic,val,lb,bx,by,bw,bh}});
if(!hz){const g=document.createElementNS(NS,'path');g.setAttribute('d','M0 450 H864');g.setAttribute('stroke','#fff');g.setAttribute('stroke-width','3');s.append(g)}
return (t,st)=>items.forEach((o,i)=>{const p=E(st(i*.7,.9));if(hz)o.r.setAttribute('width',o.bw*p);else{o.r.setAttribute('height',o.bh*p);o.r.setAttribute('y',o.by+o.bh*(1-p))}if(o.ic){o.ic.style.opacity=cl(p*2);draw(o.ic,p)}show(o.val,st(i*.7+.4,.5),8);show(o.lb,st(i*.7+.2,.5),0)})};
// prierez vrstvami: stena, strecha, cesta, zem do hĺbky (hrúbky v správnom pomere, aspoň čitateľné)
V.layers=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)).slice(0,7);const n=I.length||1;const tot=I.reduce((s,x)=>s+Math.max(0,N(x[1])),0)||1;const H=500,minh=34;
let hs=I.map(x=>N(x[1])/tot*H);for(let it=0;it<8;it++){const sm=hs.map(h=>h<minh),fixed=sm.filter(Boolean).length*minh,rest=hs.reduce((a,h,i)=>a+(sm[i]?0:h),0)||1;hs=hs.map((h,i)=>sm[i]?minh:h*(H-fixed)/rest)}const fills=['#5a5a5a','#3a3a3a','#8a8a8a','#2a2a2a','#6e6e6e','#474747','#9c9c9c'];
let y=30,acc=0;const L=[];I.forEach((x,i)=>{const hl=x[2]==1;const r=el('div','',`position:absolute;left:150px;top:${y}px;width:340px;height:${hs[i]-3}px;background:${hl?'var(--acc)':fills[i%fills.length]};border-radius:4px;transform-origin:0 50%;transform:scaleX(0);background-image:repeating-linear-gradient(135deg,rgba(255,255,255,.07) 0 2px,transparent 2px 14px)`);
const lb=el('div','',`position:absolute;left:520px;top:${y+hs[i]/2-22}px;width:344px;white-space:nowrap`,`<span class="lab" style="position:relative;font-size:24px;color:${hl?'var(--acc)':'#fff'}">${esc(x[0])}</span> <span class="lab" style="position:relative;font-size:22px;color:#8a8a8a;letter-spacing:1px">${N(x[1])?esc(NF(N(x[1]),decs(x[1]))+(d.u?' '+d.u:'')):''}</span>`);
acc+=N(x[1]);const dep=d.z&&hs[i]>=30?el('div','lab',`left:0;top:${y+hs[i]-16}px;width:130px;text-align:right;font-size:20px;color:#9a9a9a`,esc(NF(acc,decs(acc))+(d.u?' '+d.u:''))):null;v.append(r,lb);if(dep)v.append(dep);L.push({r,lb,dep});y+=hs[i]});
if(d.z){const ax=el('div','',`position:absolute;left:138px;top:30px;width:2px;height:${H}px;background:rgba(255,255,255,.5)`);v.append(ax)}
return (t,st)=>L.forEach((o,i)=>{const p=E(st(i*.45,.6));o.r.style.transform=`scaleX(${p})`;show(o.lb,st(i*.45+.2,.5),0);if(o.dep)show(o.dep,st(i*.45+.3,.4),0)})};
// hotové animované mechanizmy (piest, ozubené kolesá, krídlo, vlna, radar, obežná dráha, kyvadlo)
V.mech=(v,d)=>{const m=String(d.m||'gears');const W=864,Hh=560,x=cv2(v,W,Hh);const L=(Array.isArray(d.l)?d.l:[]).map(String);const A=D.acc;
const lab=[0,1,2,3].map(i=>{const e=el('div','lab','left:0;top:0;width:260px;font-size:24px;opacity:0',esc(L[i]||''));v.append(e);return e});
const put=(i,px,py,al)=>{const e=lab[i];if(!L[i])return;e.style.left=(al=='r'?px-260:al=='c'?px-130:px)+'px';e.style.top=py+'px';e.style.textAlign=al=='r'?'right':al=='c'?'center':'left'};
const gear=(cx,cy,r,n,rot,col)=>{x.save();x.translate(cx,cy);x.rotate(rot);x.beginPath();for(let i=0;i<n*2;i++){const a=i*Math.PI/n,rr=i%2?r:r+r*0.16;const a2=a+Math.PI/n;x.lineTo(Math.cos(a-.12/n*6)*rr,Math.sin(a-.12/n*6)*rr);x.lineTo(Math.cos(a2-.12/n*6)*rr,Math.sin(a2-.12/n*6)*rr)}x.closePath();x.strokeStyle=col;x.lineWidth=4;x.stroke();x.beginPath();x.arc(0,0,r*.28,0,6.3);x.stroke();
for(let k=0;k<4;k++){x.beginPath();x.moveTo(Math.cos(k*Math.PI/2)*r*.28,Math.sin(k*Math.PI/2)*r*.28);x.lineTo(Math.cos(k*Math.PI/2)*r*.8,Math.sin(k*Math.PI/2)*r*.8);x.stroke()}x.restore()};
return (t,st)=>{const p=E(st(0,1));x.clearRect(0,0,W,Hh);x.globalAlpha=p;const sp=cl(st(.3,1));x.lineWidth=4;x.strokeStyle='#fff';
if(m=='piston'){const ph=(t*.55)%1,ang=ph*Math.PI*4,cx=360,crY=430,cr=60,rod=170;const py=crY-cr*Math.cos(ang)-rod;x.strokeStyle='#fff';x.strokeRect(cx-110,70,220,330);
const stg=Math.floor(ph*4);x.fillStyle=stg==2?A:'rgba(255,255,255,.08)';x.fillRect(cx-106,74,212,Math.max(0,py-74));
const vo=(k)=>stg==k?14:0;x.beginPath();x.moveTo(cx-60,40);x.lineTo(cx-60,70+vo(0));x.moveTo(cx+60,40);x.lineTo(cx+60,70+vo(3));x.stroke();
if(stg==1||stg==2){x.fillStyle=stg==2?'#fff':'#777';x.beginPath();x.arc(cx,80,stg==2?12:6,0,6.3);x.fill()}
x.fillStyle='#d9d9d9';x.fillRect(cx-104,py,208,70);const pinX=cx+cr*Math.sin(ang),pinY=crY-cr*Math.cos(ang);x.beginPath();x.moveTo(cx,py+50);x.lineTo(pinX,pinY);x.lineWidth=12;x.strokeStyle='#9a9a9a';x.stroke();
x.lineWidth=4;x.strokeStyle='#fff';x.beginPath();x.arc(cx,crY,cr+18,0,6.3);x.stroke();x.beginPath();x.arc(pinX,pinY,10,0,6.3);x.fillStyle=A;x.fill();
lab.forEach((e,i)=>{put(i,520,110+i*80,'l');e.style.opacity=L[i]?(i==stg?1:.35)*sp:0;e.style.color=i==stg?A:'#bdbdbd'})}
else if(m=='gears'){const n1=Math.max(6,Math.min(40,Math.round(N((d.n||[])[0])||12))),n2=Math.max(6,Math.min(40,Math.round(N((d.n||[])[1])||24)));const k=7.5,r1=n1*k/1.15,r2=n2*k/1.15;const sc=Math.min(1,380/(r1+r2+40));
x.save();x.translate(432-(r2-r1)*sc/2,280);x.scale(sc,sc);const w=t*1.2*sp;gear(-r2-6,0,r1,n1,w,'#fff');gear(r1+6,0,r2,n2,-w*n1/n2+Math.PI/n2,A);x.restore();
put(0,432-(r2-r1)*sc/2-(r2+6)*sc,280+r1*sc+40,'c');put(1,432-(r2-r1)*sc/2+(r1+6)*sc,280+r2*sc+40,'c');lab[0].style.opacity=sp;lab[1].style.opacity=sp;lab[2].style.opacity=0;lab[3].style.opacity=0}
else if(m=='wing'){const foil=(s)=>{x.beginPath();x.moveTo(230,300);x.bezierCurveTo(300,190,520,200,650,300);x.bezierCurveTo(520,300,320,320,230,300);x.closePath()};foil();x.fillStyle='#e9e9e9';x.fill();
for(let j=0;j<7;j++){const yb=150+j*40,top=yb<300;for(let q=0;q<5;q++){const u=((t*(top?.45:.3)+q/5+j*.07)%1);const X=40+u*780;const bump=Math.exp(-Math.pow((X-440)/170,2));const Y=yb+(top?-1:1)*bump*(top?(300-yb)*.35+40*(1-(300-yb)/150):12);
x.fillStyle=top?A:'#9a9a9a';x.globalAlpha=p*Math.sin(u*Math.PI);x.beginPath();x.arc(X,Y,5,0,6.3);x.fill()}}x.globalAlpha=p;
const lp=E(st(1,.8));x.strokeStyle=A;x.lineWidth=10;x.beginPath();x.moveTo(440,230);x.lineTo(440,230-lp*150);x.stroke();x.beginPath();x.moveTo(410,230-lp*150+34);x.lineTo(440,230-lp*150);x.lineTo(470,230-lp*150+34);x.stroke();
put(0,460,70,'l');put(1,40,380,'l');lab[0].style.opacity=lp;lab[0].style.color=A;lab[1].style.opacity=sp;lab[2].style.opacity=0;lab[3].style.opacity=0}
else if(m=='wave'){const two=(d.n||[]).length>1;const ws=two?[N(d.n[0])||1,N(d.n[1])||2]:[N((d.n||[])[0])||1.5];ws.forEach((f,k)=>{const yc=two?(k?400:170):280,amp=two?80:130;x.beginPath();for(let X=40;X<=824;X+=4){const Y=yc+amp*Math.sin((X/784)*f*Math.PI*2-t*3)*cl((X-40)/784/sp||0);X==40?x.moveTo(X,Y):x.lineTo(X,Y)}
x.strokeStyle=k?'#e9e9e9':A;x.lineWidth=5;x.stroke();put(k,40,yc-amp-44,'l');lab[k].style.opacity=sp});lab[2].style.opacity=0;lab[3].style.opacity=0}
else if(m=='radar'){const cx=432,cy=280,R=240;x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;[1,.66,.33].forEach(f=>{x.beginPath();x.arc(cx,cy,R*f,0,6.3);x.stroke()});x.beginPath();x.moveTo(cx-R,cy);x.lineTo(cx+R,cy);x.moveTo(cx,cy-R);x.lineTo(cx,cy+R);x.stroke();
const a=t*1.6;for(let k=0;k<26;k++){x.globalAlpha=p*(1-k/26)*.5;x.fillStyle=A;x.beginPath();x.moveTo(cx,cy);x.arc(cx,cy,R,a-(k+1)*.03,a-k*.03);x.closePath();x.fill()}x.globalAlpha=p;
[[.6,-.8],[-.5,.3],[.2,.55]].forEach((b,i)=>{const ba=Math.atan2(b[1],b[0]),dd=((a-ba)%(Math.PI*2)+Math.PI*2)%(Math.PI*2);const fade=cl(1-dd/3);x.fillStyle='#fff';x.globalAlpha=p*fade;x.beginPath();x.arc(cx+b[0]*R*.8,cy+b[1]*R*.8,9,0,6.3);x.fill()});x.globalAlpha=p;
put(0,cx+R+20,cy-20,'l');lab[0].style.opacity=sp;[1,2,3].forEach(i=>lab[i].style.opacity=0)}
else if(m=='orbit'){const cx=432,cy=290;x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.arc(cx,cy,95,0,6.3);x.stroke();x.lineWidth=1.5;x.strokeStyle='rgba(255,255,255,.4)';for(let k=-2;k<=2;k++){x.beginPath();x.ellipse(cx,cy,95,Math.abs(k)*30+4,0,0,6.3);x.stroke()}
const ns=Math.max(1,Math.min(6,Math.round(N(d.n)||3)));const g=[cx+40,cy-60];for(let i=0;i<ns;i++){const rr=170+i%2*50,an=t*.5*(i%2?-.7:1)+i*6.28/ns;const sx=cx+rr*Math.cos(an),sy=cy+rr*.62*Math.sin(an);x.strokeStyle='rgba(255,255,255,.18)';x.beginPath();x.ellipse(cx,cy,rr,rr*.62,0,0,6.3);x.stroke();
x.fillStyle=i<3?A:'#fff';x.fillRect(sx-9,sy-6,18,12);x.fillStyle='#bbb';x.fillRect(sx-24,sy-2,12,4);x.fillRect(sx+12,sy-2,12,4);if(i<3){x.strokeStyle=A;x.setLineDash([6,8]);x.lineDashOffset=-t*20;x.beginPath();x.moveTo(sx,sy);x.lineTo(g[0],g[1]);x.stroke();x.setLineDash([])}}
x.fillStyle=A;x.beginPath();x.arc(g[0],g[1],8,0,6.3);x.fill();put(0,cx-130,cy+130,'c');lab[0].style.opacity=sp;put(1,600,40,'l');lab[1].style.opacity=sp;[2,3].forEach(i=>lab[i].style.opacity=0)}
else if(m=='pendulum'){const ox=432,oy=40,len=380,an=.6*Math.cos(t*2.2)*sp;const bx=ox+len*Math.sin(an),by=oy+len*Math.cos(an);x.strokeStyle='#fff';x.beginPath();x.moveTo(ox-120,oy);x.lineTo(ox+120,oy);x.stroke();x.lineWidth=3;x.beginPath();x.moveTo(ox,oy);x.lineTo(bx,by);x.stroke();
x.fillStyle=A;x.beginPath();x.arc(bx,by,36,0,6.3);x.fill();x.strokeStyle='rgba(255,255,255,.25)';x.setLineDash([6,8]);x.beginPath();x.arc(ox,oy,len,Math.PI/2-.6,Math.PI/2+.6);x.stroke();x.setLineDash([]);put(0,ox+160,oy+20,'l');lab[0].style.opacity=sp;[1,2,3].forEach(i=>lab[i].style.opacity=0)}
x.globalAlpha=1}};
