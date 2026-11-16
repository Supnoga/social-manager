// ---------- general_b: gauge, zoom, clock, venn, level, myth, calendar ----------
(()=>{
const SN='http://www.w3.org/2000/svg';
const mk=(tag,at,par)=>{const e=document.createElementNS(SN,tag);for(const k in at)e.setAttribute(k,at[k]);if(par)par.append(e);return e};
const uid=()=>'gb'+Math.random().toString(36).slice(2,9);
const pol=(cx,cy,r,deg)=>[cx+r*Math.cos(deg*Math.PI/180),cy+r*Math.sin(deg*Math.PI/180)];
const arcD=(cx,cy,r,a0,a1)=>{const p=pol(cx,cy,r,a0),q=pol(cx,cy,r,a1);return `M${p[0].toFixed(2)} ${p[1].toFixed(2)} A${r} ${r} 0 ${Math.abs(a1-a0)>180?1:0} 1 ${q[0].toFixed(2)} ${q[1].toFixed(2)}`};
const dash=(p,x)=>{p.style.strokeDasharray='1 1';p.style.strokeDashoffset=1-cl(x)};
const SIG=(x,n)=>{try{return new Intl.NumberFormat(D.lang||'en',{maximumSignificantDigits:n||3}).format(x)}catch(e){return String(+x.toPrecision(n||3))}};
const UNIT=(x,u)=>{try{return new Intl.NumberFormat(D.lang||'en',{style:'unit',unit:u,unitDisplay:'long',maximumFractionDigits:0}).format(x)}catch(e){return NF(x,0)+' '+u}};
const niceStep=r=>{const e=Math.pow(10,Math.floor(Math.log10(r)));const f=r/e;return (f<1.5?1:f<3?2:f<3.5?2.5:f<7.5?5:10)*e};
const hasIcon=n=>!!(n&&(IR(n)!=='check'||n==='check'));
const unitTxt=u=>u?(u=='%'&&!/^(en|zh|ja|ko|he|hi)/.test(D.lang||'en')?'\u202f%':/^[%°]/.test(u)?u:' '+u):'';

// ===== GAUGE: ručičkový merák so zónami =====
V.gauge=(v,d)=>{let a=d.a==null?0:N(d.a),b=d.b==null?100:N(d.b);if(!(b>a))b=a+100;const val=Math.max(a,Math.min(b,N(d.v)));const dec=decs(d.v);
const cx=432,cy=262,R=200,A0=135,SW=270;const ang=x=>A0+SW*(cl((x-a)/(b-a)));
const s=svg(864,560,'');v.append(s);
const track=mk('path',{d:arcD(cx,cy,R,A0,A0+SW),stroke:'#262626','stroke-width':26,fill:'none','stroke-linecap':'butt'},s);
const outer=mk('path',{class:'d',pathLength:1,d:arcD(cx,cy,R+22,A0,A0+SW),stroke:'#fff','stroke-width':2.5},s);
const Z=(Array.isArray(d.z)?d.z:[]).filter(z=>Array.isArray(z)&&z.length>1);const zc=['#4a4a4a','#b5b5b5','var(--acc)'];
const zones=Z.map(z=>{const f=Math.max(a,Math.min(b,N(z[0]))),t=Math.max(a,Math.min(b,N(z[1])));if(t<=f)return null;
return mk('path',{class:'d',pathLength:1,d:arcD(cx,cy,R,ang(f),ang(t)),stroke:zc[Math.max(0,Math.min(2,Math.round(N(z[2]))))],'stroke-width':26,fill:'none','stroke-linecap':'butt'},s)}).filter(Boolean);
const prog=Z.length?null:mk('path',{d:arcD(cx,cy,R,A0,A0+SW),stroke:'var(--acc)','stroke-width':26,fill:'none','stroke-linecap':'butt',pathLength:1},s);
const step=niceStep((b-a)/5);const ticks=mk('g',{},s),nums=[];
for(let i=0;i<=40;i++){const g=A0+SW*i/40,mj=i%8==0,p=pol(cx,cy,R-20,g),q=pol(cx,cy,R-(i%4==0?40:30),g);mk('path',{d:`M${p[0]} ${p[1]} L${q[0]} ${q[1]}`,stroke:i%4==0?'#fff':'#777','stroke-width':i%4==0?3:2},ticks)}
const sd=decs(step);for(let x=Math.ceil(a/step-1e-9)*step;x<=b+1e-9;x+=step){const p=pol(cx,cy,R+46,ang(x));const e=el('div','big',`left:${p[0]-60}px;top:${p[1]-14}px;width:120px;text-align:center;font-size:24px;font-weight:700;color:#bdbdbd`,esc(NF(Math.abs(x)<step*1e-6?0:x,sd)));v.append(e);nums.push(e)}
const nd=mk('g',{},s);mk('path',{d:`M${cx-9} ${cy} L${cx} ${cy-R+44} L${cx+9} ${cy} Z`,fill:'#fff'},nd);mk('path',{d:`M${cx-6} ${cy} L${cx} ${cy+34} L${cx+6} ${cy} Z`,fill:'#fff'},nd);
mk('circle',{cx,cy,r:20,fill:'var(--acc)'},nd);mk('circle',{cx,cy,r:7,fill:'#000'},nd);
const big=el('div','big',`left:${cx-125}px;top:${cy+48}px;width:250px;text-align:center;font-size:80px;color:var(--acc);white-space:nowrap`);
const lb=el('div','lab',`left:62px;top:${cy+R+34}px;width:740px;text-align:center;font-size:26px`,esc(d.l||''));v.append(big,lb);fit(lb,26,15,62,740);
const uu=unitTxt(d.u);big.innerHTML=esc(NF(b,dec))+`<span style="font-size:.42em;color:#cfcfcf">${esc(uu)}</span>`;fit(big,80,30,90,250);
const ob=x=>{const c1=1.1,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
return (t,st)=>{const p0=st(0,1);track.style.opacity=cl(p0*2);dash(outer,p0);ticks.style.opacity=st(.3,.6);nums.forEach((e,i)=>show(e,st(.3+i*.06,.5),0));
zones.forEach((z,i)=>dash(z,st(.6+i*.25,.7)));nd.style.opacity=st(.5,.4);
const q=st(1.1,1.6);let x=a+(val-a)*ob(cl(q));if(q>=1)x+=Math.sin(t*9)*(b-a)*.003;x=Math.max(a,Math.min(b,x));
nd.setAttribute('transform',`rotate(${ang(x)+90} ${cx} ${cy})`);if(prog){prog.style.strokeDasharray='1 1';prog.style.strokeDashoffset=1-cl((x-a)/(b-a))}
big.firstChild.textContent=NF(q>=1?val:x,dec);show(big,st(1.1,.5),10);show(lb,st(1.5,.6),10)}};

// ===== ZOOM: rebrík mierok, kamera sa odďaľuje =====
const fmtLen=m=>{const U=[[9.461e15,'ly'],[1e3,'km'],[1,'m'],[1e-2,'cm'],[1e-3,'mm'],[1e-6,'µm'],[1e-9,'nm'],[1e-12,'pm']];for(const [f,u] of U)if(m>=f*.9999)return SIG(m/f,3)+' '+u;return SIG(m/1e-12,3)+' pm'};
const fmtFac=f=>f>=1e9?'×10<sup style="font-size:.55em">'+Math.round(Math.log10(f))+'</sup>':'×'+esc(SIG(f,2));
const supN=n=>String(n).split('').map(c=>'⁰¹²³⁴⁵⁶⁷⁸⁹'['0123456789'.indexOf(c)]||(c=='-'?'⁻':c)).join('');
V.zoom=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)&&N(x[1])>0).slice(0,6).sort((p,q)=>N(p[1])-N(q[1]));if(I.length<2)return V.text(v,{w:String((I[0]||[d.l||''])[0])});
const n=I.length,Z=I.map(x=>N(x[1])),D0=270,CX=275,BL=372,G=8,SWD=540;
const stg=el('div','',`position:absolute;left:0;top:0;width:${SWD}px;height:400px;overflow:hidden`);v.append(stg);
const base=svg(SWD,400,`<path d="M0 ${BL} H${SWD}" stroke="#555" stroke-width="2"/>`);stg.append(base);
const ob=I.map((x,i)=>{let e;if(hasIcon(x[2]))e=icon(x[2],300,'#fff',2.6);else{e=svg(300,300,'');e.setAttribute('viewBox','0 0 100 100');e.innerHTML='<circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" stroke-width="2.6"/><circle cx="40" cy="44" r="10" fill="none" stroke="currentColor" stroke-width="2.6"/><circle cx="64" cy="64" r="4" fill="currentColor"/>';e.style.color='#fff'}
e.style.transformOrigin='0 0';e.style.left='0';e.style.top='0';stg.append(e);return e});
const mg=svg(SWD,400,'<path class="ml" d="" stroke="var(--acc)" stroke-width="2.5" fill="none"/><circle class="mc" r="48" fill="#000" stroke="var(--acc)" stroke-width="3"/><circle class="md" r="5" fill="var(--acc)"/>');stg.append(mg);const ml=mg.querySelector('.ml'),mc=mg.querySelector('.mc'),md=mg.querySelector('.md');
const mini=I.map(x=>{let e;if(hasIcon(x[2]))e=icon(x[2],56,D.acc,4);else{e=svg(56,56,'');e.setAttribute('viewBox','0 0 100 100');e.innerHTML='<circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="6"/><circle cx="40" cy="44" r="10" fill="none" stroke="currentColor" stroke-width="6"/><circle cx="64" cy="64" r="5" fill="currentColor"/>';e.style.color=D.acc}e.style.opacity=0;stg.append(e);return e});
const sb=svg(SWD,60,'<path class="sbl" d="" stroke="#fff" stroke-width="3" fill="none"/>');sb.style.top='392px';v.append(sb);const sbl=sb.querySelector('.sbl');
const sbt=el('div','lab',`left:0;top:404px;width:300px;font-size:22px;color:#cfcfcf;letter-spacing:1px;text-transform:none`);v.append(sbt);
// panel vpravo
const P=566,PW=298;const pv=el('div','lab',`left:${P}px;top:20px;width:${PW}px;font-size:22px;color:#8a8a8a`),fac=el('div','big',`left:${P}px;top:66px;width:${PW}px;font-size:76px;color:var(--acc);white-space:nowrap`),
cu=el('div','big',`left:${P}px;top:178px;width:${PW}px;font-size:48px;text-transform:uppercase;line-height:1.05`),cs=el('div','big',`left:${P}px;top:300px;width:${PW}px;font-size:36px;color:#bdbdbd;font-weight:700;white-space:nowrap`);v.append(pv,fac,cu,cs);
// rebrík mocnín desiatky dole
const lg=Z.map(z=>Math.log10(z)),l0=Math.floor(lg[0])-.5,l1=Math.ceil(lg[n-1])+.5,LX=x=>30+(804*(x-l0)/(l1-l0)),LY=500;
let lad=`<path class="d lax" pathLength="1" d="M30 ${LY} H834" stroke="#777" stroke-width="2"/>`;for(let k=Math.ceil(l0);k<=l1;k++)lad+=`<path d="M${LX(k)} ${LY-6} V${LY+6}" stroke="#555" stroke-width="2"/>`;
const ls=svg(864,560,lad);v.append(ls);const dots=lg.map(l=>mk('circle',{cx:LX(l),cy:LY,r:8,fill:'#fff',opacity:0},ls));const mark=mk('circle',{cx:LX(lg[0]),cy:LY,r:14,fill:'none',stroke:'var(--acc)','stroke-width':3,opacity:0},ls);
let lastX=-999;const ltx=lg.map((l,i)=>{const x=LX(l);if(x-lastX<96)return null;lastX=x;const e=el('div','lab',`left:${x-60}px;top:${LY+16}px;width:120px;text-align:center;font-size:20px;letter-spacing:0;text-transform:none;color:#9a9a9a`,'10'+supN(Math.floor(l+1e-9))+' m');v.append(e);return e});
fit(cu,48,22,112,PW);let shown=-2;
const setPanel=k=>{if(k==shown)return;shown=k;const c=I[k];cu.textContent=String(c[0]||'');cu.style.fontSize='48px';fit(cu,48,22,112,PW);cs.textContent=fmtLen(Z[k]);fit(cs,36,20,44,PW);
if(k>0){pv.textContent=String(I[k-1][0]||'')+'\u00a0→';fit(pv,22,14,54,PW);fac.innerHTML=fmtFac(Z[k]/Z[k-1]);fac.style.fontSize='76px';fit(fac,76,34,90,PW)}else{pv.textContent='';fac.innerHTML=''}};
return (t,st)=>{const p0=st(0,.7);let u=0;for(let i=1;i<n;i++)u+=st(i,1);let k,p;if(u<=0){k=0;p=0}else{k=Math.min(n-2,Math.ceil(u-1e-9)-1);p=cl(u-k)}
const pz=1-Math.pow(1-p,2.2);let S;ob.forEach(e=>e.style.opacity=0);const put=(e,x,sz,al,c)=>{e.style.opacity=al;e.style.color=c;e.style.transform=`translate(${x}px,${BL-sz}px) scale(${sz/300})`};
let showM=0,dx=0,dy=0;if(u<=0){S=D0/Z[0];put(ob[0],CX-D0/2,D0,p0,'#fff')}else{const Dn=D0*(1+.25*(1-pz)),NL=CX-Dn/2,Do=D0*Math.pow(Z[k]/Z[k+1],pz),R=CX+D0/2+((NL-G)-(CX+D0/2))*pz;S=Do/Z[k];
put(ob[k+1],NL,Dn,cl(p*2.5),'#fff');put(ob[k],R-Do,Do,cl((Do-8)/12),D.acc);showM=cl((34-Do)/14);dx=R-Math.max(Do,1)/2;dy=BL-Math.max(Do/2,5)}
const MX=Math.max(56,(CX-D0/2)-70),MY=BL-150;mc.setAttribute('cx',MX);mc.setAttribute('cy',MY);md.setAttribute('cx',dx);md.setAttribute('cy',dy);
const ang=Math.atan2(dy-MY,dx-MX);ml.setAttribute('d',`M${MX+48*Math.cos(ang)} ${MY+48*Math.sin(ang)} L${dx} ${dy}`);mg.style.opacity=showM;
mini.forEach((e,i)=>{if(!e)return;e.style.opacity=i==k&&u>0?showM:0;e.style.left=(MX-28)+'px';e.style.top=(MY-28)+'px'});
// mierka
let L=Math.pow(10,Math.floor(Math.log10(160/S)));if(L*S*5<=200)L*=5;else if(L*S*2<=200)L*=2;const w=L*S;sbl.setAttribute('d',`M20 14 V30 H${20+w} V14 M${20+w/2} 22 V30`);sb.style.opacity=p0;sbt.textContent=fmtLen(L);sbt.style.left=(w+36)+'px';sbt.style.opacity=p0;
// panel
const cur=u<=0?0:(p>.5?k+1:k);setPanel(cur);const pop=u<=0?1:cl(Math.abs(p-.5)*5);[cu,cs,pv,fac].forEach(e=>e.style.opacity=p0*(.25+.75*pop));fac.style.transform=`scale(${.8+.2*E(pop)})`;fac.style.transformOrigin='0 50%';
ls.querySelector('.lax').style.strokeDasharray='1 1';ls.querySelector('.lax').style.strokeDashoffset=1-p0;dots.forEach((c,i)=>{c.setAttribute('opacity',i<=cur?1:.25*p0);c.setAttribute('fill',i==cur?D.acc:'#fff')});ltx.forEach((e,i)=>{if(e)e.style.opacity=p0*(i<=cur?1:.4)});
const lx=LX(lg[k]+(lg[Math.min(n-1,k+1)]-lg[k])*(u<=0?0:pz));mark.setAttribute('cx',lx);mark.setAttribute('opacity',p0)}};

// ===== CLOCK: 24 h deň v kruhu, alebo "per" = počítadlo za sekundy videa =====
const hh=h=>{h=((h%24)+24)%24;const H=Math.floor(h),M=Math.round((h-H)*60)%60;return String(H).padStart(2,'0')+':'+String(M).padStart(2,'0')};
V.clock=(v,d)=>{if(d.m=='per'||d.r!=null||d.y!=null)return clockPer(v,d);
const I=(d.i||[]).filter(x=>Array.isArray(x)&&x.length>2).slice(0,5);if(!I.length)return V.text(v,{w:d.l||''});
const cx=272,cy=280,R=196,col=['var(--acc)','#e8e8e8','#8a8a8a','#4f4f4f','#bdbdbd'],cH=['#000','#000','#000','#fff','#000'];const A=h=>-90+h*15;
const s=svg(864,560,'');v.append(s);const tr=mk('circle',{cx,cy,r:R,stroke:'#1f1f1f','stroke-width':48,fill:'none'},s);
const tk=mk('g',{},s);for(let h=0;h<24;h++){const p=pol(cx,cy,R+30,A(h)),q=pol(cx,cy,R+(h%6==0?46:38),A(h));mk('path',{d:`M${p[0]} ${p[1]} L${q[0]} ${q[1]}`,stroke:h%6==0?'#fff':'#666','stroke-width':h%6==0?3:2},tk)}
const hl=[0,6,12,18].map(h=>{const p=pol(cx,cy,R+64,A(h));const e=el('div','big',`left:${p[0]-40}px;top:${p[1]-13}px;width:80px;text-align:center;font-size:24px;font-weight:700;color:#bdbdbd`,String(h).padStart(2,'0'));v.append(e);return e});
const seg=I.map((x,i)=>{let f=N(x[1]),t=N(x[2]);f=((f%24)+24)%24;t=((t%24)+24)%24;if(t<=f)t+=24;const p=mk('path',{class:'d',pathLength:1,d:arcD(cx,cy,R,A(f),A(t)-.01),stroke:col[i],'stroke-width':48,fill:'none','stroke-linecap':'butt'},s);return {f,t,p,dur:t-f}});
const hand=mk('g',{},s);mk('path',{d:`M${cx} ${cy} L${cx} ${cy-R+40}`,stroke:'#fff','stroke-width':5,'stroke-linecap':'round'},hand);mk('circle',{cx,cy,r:10,fill:'#fff'},hand);
const tm=el('div','big',`left:${cx-110}px;top:${cy+30}px;width:220px;text-align:center;font-size:54px;font-variant-numeric:tabular-nums`),cc=el('div','lab',`left:${cx-115}px;top:${cy+96}px;width:230px;text-align:center;font-size:20px;color:#9a9a9a`,esc(d.c||''));v.append(tm,cc);fit(cc,20,13,50,230);
const LX=590,LW=274,rh=Math.min(108,(520)/I.length),y0=280-rh*I.length/2;
const leg=I.map((x,i)=>{const y=y0+i*rh;const sw=el('div','',`position:absolute;left:${LX}px;top:${y+8}px;width:14px;height:${rh-26}px;border-radius:3px;background:${col[i]}`);
const lb=el('div','lab',`left:${LX+30}px;top:${y+2}px;width:${LW-30}px;font-size:22px;line-height:1.1;${i==0?'color:var(--acc)':''}`,esc(x[0]));const dv=el('div','big',`left:${LX+30}px;width:${LW-30}px;font-size:30px;white-space:nowrap`);
const S=seg[i];dv.innerHTML=esc(SIG(S.dur,3))+' h <span style="font-size:.66em;color:#8a8a8a;font-weight:700">'+hh(S.f)+'–'+hh(S.t)+'</span>';v.append(sw,lb,dv);fit(lb,22,13,Math.max(26,rh-56),LW-30);dv.style.top=(y+6+lb.offsetHeight+4)+'px';return {sw,lb,dv}});
return (t,st)=>{const p0=st(0,.8);tr.style.opacity=p0;tk.style.opacity=p0;hl.forEach(e=>e.style.opacity=p0);let hand_h=seg[0].f;hand.style.opacity=st(.4,.4);
seg.forEach((S,i)=>{const q=st(.8+i,.9);dash(S.p,q);if(q>0)hand_h=S.f+S.dur*q;const L=leg[i];show(L.lb,st(.8+i,.5),0);show(L.dv,st(1+i,.5),0);L.sw.style.opacity=st(.8+i,.4)});
hand.setAttribute('transform',`rotate(${hand_h*15} ${cx} ${cy})`);tm.textContent=hh(hand_h);tm.style.opacity=st(.4,.4);show(cc,st(.8+I.length,.5),6)}};
const clockPer=(v,d)=>{let r=d.r!=null?N(d.r):N(d.y)/31536000;if(!(r>0))r=1;const cx=220,cy=290,R=180;
const s=svg(864,560,'');v.append(s);const face=mk('g',{},s);mk('circle',{cx,cy,r:R,stroke:'#fff','stroke-width':4,fill:'none'},face);mk('rect',{x:cx-22,y:cy-R-34,width:44,height:22,rx:4,stroke:'#fff','stroke-width':4,fill:'none'},face);mk('path',{d:`M${cx} ${cy-R-12} V${cy-R}`,stroke:'#fff','stroke-width':4},face);
for(let i=0;i<60;i++){const p=pol(cx,cy,R-12,-90+i*6),q=pol(cx,cy,R-(i%5==0?34:22),-90+i*6);mk('path',{d:`M${p[0]} ${p[1]} L${q[0]} ${q[1]}`,stroke:i%5==0?'#fff':'#666','stroke-width':i%5==0?3:2},face)}
const sub=mk('g',{},face);mk('circle',{cx,cy:cy+70,r:34,stroke:'#666','stroke-width':2,fill:'none'},sub);
const sh=mk('path',{d:`M${cx} ${cy+70} L${cx} ${cy+42}`,stroke:'#8a8a8a','stroke-width':3,'stroke-linecap':'round'},sub);
const sweep=mk('path',{d:'',fill:'var(--acc)',opacity:.22},s);const hand=mk('path',{d:`M${cx} ${cy+24} L${cx} ${cy-R+30}`,stroke:'var(--acc)','stroke-width':5,'stroke-linecap':'round'},s);mk('circle',{cx,cy,r:11,fill:'var(--acc)'},s);
const el_=el('div','big',`left:${cx-110}px;top:${cy+R+22}px;width:220px;text-align:center;font-size:40px;font-variant-numeric:tabular-nums;color:#cfcfcf`);v.append(el_);
const X0=450,W0=414;const big=el('div','big',`left:${X0}px;top:40px;width:${W0}px;font-size:120px;color:var(--acc);white-space:nowrap;font-variant-numeric:tabular-nums`),lb=el('div','lab',`left:${X0}px;top:180px;width:${W0}px;font-size:26px`,esc(d.l||'')),
rt=el('div','big',`left:${X0}px;width:${W0}px;font-size:28px;color:#8a8a8a;font-weight:700;white-space:nowrap`);v.append(big,lb,rt);fit(lb,26,15,100,W0);rt.style.top=(186+lb.offsetHeight+10)+'px';
rt.textContent='= '+SIG(r,3)+' / s';fit(rt,28,16,36,W0);const T0=1.1,est=r*8,dec=est<20?1:0;
const gy=rt.offsetTop+62,cell=52,cols=7,cap=Math.max(0,Math.floor((556-gy)/cell))*cols-cols;let per=1;while(est/per>cap&&per<1e12)per*=[2,2.5,2][String(per).length%3]||2;per=[1,2,5,10,20,50,100,200,500,1000,2000,5000,10000].find(z=>est/z<=cap)||per;const ic=d.g&&hasIcon(d.g)?d.g:'user';
const maxI=cap>0?Math.min(cap,Math.ceil(est*1.2/per)):0;const pile=[];for(let i=0;i<maxI;i++){const e=icon(ic,44,i%2?'#fff':D.acc,4);e.style.left=(X0+(i%cols)*(cell+6))+'px';e.style.top=(gy+Math.floor(i/cols)*cell)+'px';e.style.opacity=0;v.append(e);pile.push(e)}
let key=null;if(per>1&&maxI){key=el('div','big',`left:${X0+48}px;top:${gy+Math.ceil(maxI/cols)*cell+6}px;width:300px;font-size:26px;color:#8a8a8a;font-weight:700;white-space:nowrap`,'= '+esc(NF(per,0)));const ki=icon(ic,36,'#8a8a8a',4);ki.style.left=X0+'px';ki.style.top=(gy+Math.ceil(maxI/cols)*cell)+'px';v.append(key,ki);key.ic=ki}
const mxW=NF(Math.max(r*9.5,1),dec);big.textContent=mxW;fit(big,120,40,140,W0);
return (t,st)=>{const p0=st(0,.6);face.style.opacity=p0;el_.style.opacity=p0;show(lb,st(.3,.5),8);show(rt,st(.6,.5),8);const e=Math.max(0,t-T0);
const a=-90+e*6;hand.setAttribute('transform',`rotate(${e*6} ${cx} ${cy})`);sh.setAttribute('transform',`rotate(${(e%1)*360} ${cx} ${cy+70})`);
const q=pol(cx,cy,R-40,a);sweep.setAttribute('d',e>0?`M${cx} ${cy} L${cx} ${cy-R+40} A${R-40} ${R-40} 0 ${e*6>180?1:0} 1 ${q[0]} ${q[1]} Z`:'');
const sec=Math.floor(e),cs=Math.floor((e-sec)*10);el_.textContent=`0:${String(sec).padStart(2,'0')},${cs}`;
const c=r*e;big.textContent=dec?NF(Math.floor(c*10)/10,1):NF(Math.floor(c),0);big.style.opacity=p0;
const cu=c/per;pile.forEach((x,i)=>{const on=cu>=i+1;const k=on?cl((cu-(i+1))*per/r/0.25):0;x.style.opacity=on?1:0;x.style.transform=`scale(${on?.5+.5*E(k+.15):0})`});if(key){key.style.opacity=st(.6,.5);key.ic.style.opacity=st(.6,.5)}}};

// ===== VENN: 2-3 prekrývajúce sa kruhy =====
V.venn=(v,d)=>{const I=(d.i||[]).map(x=>Array.isArray(x)?x[0]:x).filter(x=>x!=null&&String(x).trim()).slice(0,3);if(I.length<2)return V.text(v,{w:String(I[0]||d.c||'')});
const three=I.length==3,R=three?152:180;const C=three?[[317,186],[547,186],[432,385]]:[[302,248],[562,248]];const G=three?[432,252]:[432,248];
const id=uid();const s=svg(864,560,'');v.append(s);const defs=mk('defs',{},s);
const cp=C.map((c,i)=>{const p=mk('clipPath',{id:id+i},defs);return mk('circle',{cx:c[0],cy:c[1],r:R},p)});
const fills=C.map((c,i)=>mk('circle',{cx:c[0],cy:c[1],r:R,fill:i==0?'#ffffff':'#ffffff',opacity:0},s));
const lens=[];const pairs=three?[[0,1],[1,2],[0,2]]:[[0,1]];pairs.forEach(([i,j])=>{const g=mk('g',{'clip-path':`url(#${id+i})`},s);lens.push({c:mk('circle',{cx:C[j][0],cy:C[j][1],r:R,fill:'var(--acc)',opacity:0},g),j})});
let tri=null;if(three){const g1=mk('g',{'clip-path':`url(#${id}0)`},s),g2=mk('g',{'clip-path':`url(#${id}1)`},g1);tri=mk('circle',{cx:C[2][0],cy:C[2][1],r:R,fill:'var(--acc)',opacity:0},g2)}
const rim=C.map((c,i)=>mk('circle',{class:'d',pathLength:1,cx:c[0],cy:c[1],r:R,stroke:i==0?'#fff':i==1?'#d0d0d0':'#9a9a9a','stroke-width':4,fill:'none'},s));
const off=C.map(c=>{const dx=c[0]-G[0],dy=c[1]-G[1],L=Math.hypot(dx,dy)||1;return [dx/L*(three?70:120),dy/L*(three?50:0)]});
const LB=I.map((x,i)=>{let w,h,lx,ly;if(three){const dx=C[i][0]-G[0],dy=C[i][1]-G[1],L=Math.hypot(dx,dy);w=150;h=84;lx=C[i][0]+dx/L*(i==2?0:40)-w/2;ly=C[i][1]+dy/L*62-h/2}else{w=228;h=150;lx=i?C[1][0]+R-w-14:C[0][0]-R+14;ly=C[i][1]-h/2}
const e=el('div','big',`left:${lx}px;top:${ly}px;width:${w}px;height:${h}px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:34px;text-transform:uppercase;line-height:1.05;overflow-wrap:normal`,esc(x));v.append(e);const fs=fit(e,34,14,h,w);return {e,lx,ly,fs}});if(!three){const fmin=Math.min(...LB.map(o=>o.fs));LB.forEach(o=>o.e.style.fontSize=fmin+'px')}
let ov=null,ld=null;if(d.c){if(three){ov=el('div','big',`left:604px;top:452px;width:260px;font-size:30px;color:var(--acc);text-transform:uppercase;line-height:1.05`,esc(d.c));ld=mk('path',{class:'d',pathLength:1,d:`M${G[0]} ${G[1]+14} L596 470`,stroke:'var(--acc)','stroke-width':3},s);mk('circle',{cx:G[0],cy:G[1]+14,r:6,fill:'var(--acc)',class:'ldd',opacity:0},s);v.append(ov);fit(ov,30,14,100,260)}
else{const yb=C[0][1]+Math.sqrt(R*R-Math.pow((C[1][0]-C[0][0])/2,2));ov=el('div','big',`left:82px;top:${yb+86}px;width:700px;text-align:center;font-size:38px;color:var(--acc);text-transform:uppercase`,esc(d.c));ld=mk('path',{class:'d',pathLength:1,d:`M432 ${yb-60} V${yb+74}`,stroke:'var(--acc)','stroke-width':3},s);mk('circle',{cx:432,cy:yb-60,r:6,fill:'var(--acc)',class:'ldd',opacity:0},s);v.append(ov);fit(ov,38,16,560-yb-90,700)}}
const n=I.length;const ldd=s.querySelector('.ldd');
return (t,st)=>{const m=st(n*.6+.1,1.1);
C.forEach((c,i)=>{const x=c[0]+off[i][0]*(1-m),y=c[1]+off[i][1]*(1-m);[rim[i],fills[i],cp[i]].forEach(e=>{e.setAttribute('cx',x);e.setAttribute('cy',y)});lens.forEach(o=>{if(o.j==i){o.c.setAttribute('cx',x);o.c.setAttribute('cy',y)}});if(tri&&i==2){tri.setAttribute('cx',x);tri.setAttribute('cy',y)}
const q=st(i*.6,.8);dash(rim[i],q);fills[i].setAttribute('opacity',.05*q);const L=LB[i];L.e.style.left=(L.lx+off[i][0]*(1-m))+'px';L.e.style.top=(L.ly+off[i][1]*(1-m))+'px';L.e.style.opacity=st(i*.6+.3,.5)});
const f=st(n*.6+.9,.7);lens.forEach(o=>{o.c.setAttribute('opacity',(three?.16:.92)*f);if(three)o.c.setAttribute('fill','#fff')});if(tri)tri.setAttribute('opacity',.9*f);
if(ov){const q=st(n*.6+1.3,.6);dash(ld,q);ldd.setAttribute('opacity',q);show(ov,st(n*.6+1.6,.5),8)}}};

// ===== LEVEL: batéria, nádrž, pohár, pruh =====
V.level=(v,d)=>{const mx=d.m!=null&&N(d.m)>0?N(d.m):100;const a=Math.max(0,Math.min(mx,N(d.a))),b=Math.max(0,Math.min(mx,d.b==null?mx:N(d.b)));const g=['battery','tank','glass','bar'].includes(d.g)?d.g:'tank';
const u=d.u!=null?String(d.u):(mx==100?'%':'');const dec=Math.max(decs(d.a),decs(d.b));const id=uid();const s=svg(864,560,'');v.append(s);
let X0=60,X1=400,Y0=64,Y1=520,shape='',extra='';
if(g=='battery'){X0=120;X1=330;shape=`M${X0+24} ${Y0} H${X1-24} Q${X1} ${Y0} ${X1} ${Y0+24} V${Y1-24} Q${X1} ${Y1} ${X1-24} ${Y1} H${X0+24} Q${X0} ${Y1} ${X0} ${Y1-24} V${Y0+24} Q${X0} ${Y0} ${X0+24} ${Y0} Z`;extra=`<rect x="${(X0+X1)/2-42}" y="${Y0-30}" width="84" height="22" rx="5" fill="#fff"/>`}
else if(g=='glass'){X0=96;X1=364;shape=`M${X0} ${Y0} L${X0+34} ${Y1} H${X1-34} L${X1} ${Y0}`}
else if(g=='bar'){X0=40;X1=824;Y0=230;Y1=330;shape=`M${X0+20} ${Y0} H${X1-20} Q${X1} ${Y0} ${X1} ${Y0+20} V${Y1-20} Q${X1} ${Y1} ${X1-20} ${Y1} H${X0+20} Q${X0} ${Y1} ${X0} ${Y1-20} V${Y0+20} Q${X0} ${Y0} ${X0+20} ${Y0} Z`}
else{X0=90;X1=350;shape=`M${X0} ${Y0+26} V${Y1-26} A${(X1-X0)/2} 26 0 0 0 ${X1} ${Y1-26} V${Y0+26}`;extra=`<ellipse cx="${(X0+X1)/2}" cy="${Y0+26}" rx="${(X1-X0)/2}" ry="26" fill="none" stroke="#fff" stroke-width="4"/>`}
const ins=g=='battery'?12:g=='bar'?10:4;const clipD=g=='glass'?`M${X0+ins} ${Y0} L${X0+34+ins*.6} ${Y1-ins} H${X1-34-ins*.6} L${X1-ins} ${Y0} Z`:g=='tank'?`M${X0+ins} ${Y0+26} V${Y1-26} A${(X1-X0)/2-ins} 24 0 0 0 ${X1-ins} ${Y1-26} V${Y0+26} Z`:shape;
s.innerHTML=`<defs><clipPath id="${id}"><path d="${clipD}" transform="${g=='battery'||g=='bar'?`translate(${(X0+X1)/2} ${(Y0+Y1)/2}) scale(${1-2*ins/(X1-X0)} ${1-2*ins/(Y1-Y0)}) translate(${-(X0+X1)/2} ${-(Y0+Y1)/2})`:''}"/></clipPath></defs>
<g clip-path="url(#${id})"><path class="fl" d="" fill="var(--acc)" opacity=".9"/><path class="sf" d="" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="3"/>${g=='battery'?[1,2,3,4].map(i=>`<path d="M${X0} ${Y0+(Y1-Y0)*i/5} H${X1}" stroke="#000" stroke-width="6"/>`).join(''):''}${g=='bar'?[1,2,3].map(i=>`<path d="M${X0+(X1-X0)*i/4} ${Y0} V${Y1}" stroke="#000" stroke-width="4"/>`).join(''):''}</g>
<path class="d sh" pathLength="1" d="${shape}" fill="none" stroke="#fff" stroke-width="4"/>${extra}<path class="gh" d="" stroke="#fff" stroke-width="2.5" stroke-dasharray="10 8" fill="none" opacity="0"/><g class="bolt" opacity="0"><path d="M${(X0+X1)/2+10} ${(Y0+Y1)/2-60} L${(X0+X1)/2-34} ${(Y0+Y1)/2+8} H${(X0+X1)/2-2} L${(X0+X1)/2-12} ${(Y0+Y1)/2+60} L${(X0+X1)/2+34} ${(Y0+Y1)/2-8} H${(X0+X1)/2+2} Z" fill="#fff" stroke="#000" stroke-width="4"/></g>`;
const q=k=>s.querySelector(k),fl=q('.fl'),sf=q('.sf'),sh=q('.sh'),gh=q('.gh'),bo=q('.bolt'),ex=s.querySelector('rect,ellipse');if(ex)ex.style.opacity=0;
const hz=g=='bar';const PX=hz?40:470,PW=hz?784:394;
const big=el('div','big',hz?`left:${PX}px;top:70px;width:${PW}px;font-size:120px;color:var(--acc);white-space:nowrap`:`left:${PX}px;top:120px;width:${PW}px;font-size:130px;color:var(--acc);white-space:nowrap`);
const lb=el('div','lab',hz?`left:${PX}px;top:360px;width:${PW}px;font-size:28px`:`left:${PX}px;top:280px;width:${PW}px;font-size:26px`,esc(d.l||''));
const ch=el('div','big',`left:${PX}px;width:${PW}px;font-size:34px;font-weight:700;color:#9a9a9a;white-space:nowrap`);v.append(big,lb,ch);fit(lb,hz?28:26,15,hz?90:110,PW);
const uu=unitTxt(u);const fv=x=>NF(x,dec)+uu;ch.textContent=fv(a)+'  →  '+fv(b);fit(ch,34,18,42,PW);ch.style.top=(lb.offsetTop+lb.offsetHeight+18)+'px';
big.innerHTML=esc(NF(mx,dec))+`<span style="font-size:.4em;color:#cfcfcf">${esc(uu)}</span>`;fit(big,hz?120:130,40,150,PW);
const fr=x=>cl(x/mx);
const ga=g=='glass';const lvlY=f=>Y1-(Y1-Y0)*f;const gx=y=>{const k=(Y1-y)/(Y1-Y0);return [X0+34-34*k,X1-34+34*k]};
return (t,st)=>{const p0=st(0,.9);dash(sh,p0);if(ex)ex.style.opacity=cl(p0*2-1);show(lb,st(.4,.5),8);
const p=st(1,1.6);const x=a+(b-a)*p;const f=fr(x);big.firstChild.textContent=NF(x,dec);show(big,st(.6,.5),10);show(ch,st(1,.5),8);
if(hz){const xe=X0+(X1-X0)*f;fl.setAttribute('d',`M${X0} ${Y0} H${xe} V${Y1} H${X0} Z`);sf.setAttribute('d',`M${xe} ${Y0} V${Y1}`);const xa=X0+(X1-X0)*fr(a);gh.setAttribute('d',`M${xa} ${Y0-18} V${Y1+18}`);big.style.width='max-content';const bw=big.offsetWidth;big.style.left=Math.max(X0,Math.min(X1-bw,xe-bw/2))+'px'}
else{const y=lvlY(f);let top='';const w0=X0-10,w1=X1+10;if(g=='battery')top=`M${w0} ${y} H${w1}`;else{top=`M${w0} ${y}`;for(let xx=w0;xx<=w1;xx+=12)top+=` L${xx} ${(y+Math.sin(xx/34+t*3)*6*cl(f*20)*cl((1-f)*20)).toFixed(1)}`}
fl.setAttribute('d',top+` L${w1} ${Y1+30} L${w0} ${Y1+30} Z`);sf.setAttribute('d',top);const ya=lvlY(fr(a));gh.setAttribute('d',`M${X0-26} ${ya} H${X1+26}`)}
fl.style.opacity=st(.8,.4);sf.style.opacity=st(.8,.4);gh.setAttribute('opacity',.7*st(1,.4)*(Math.abs(b-a)>mx*.02&&a>mx*.01&&a<mx*.99?1:0));bo.setAttribute('opacity',g=='battery'&&b>a?st(1,.4)*(.65+.35*Math.sin(t*5)):0)}};

// ===== MYTH: mýtus alebo pravda, pečiatka =====
const MW={en:['MYTH','TRUE'],sk:['MÝTUS','PRAVDA'],cs:['MÝTUS','PRAVDA'],de:['MYTHOS','WAHR'],pl:['MIT','PRAWDA'],hu:['MÍTOSZ','IGAZ'],fr:['MYTHE','VRAI'],es:['MITO','VERDAD'],it:['MITO','VERO'],pt:['MITO','VERDADE'],nl:['MYTHE','WAAR'],ro:['MIT','ADEVĂRAT'],hr:['MIT','ISTINA'],sr:['MIT','ISTINA'],bs:['MIT','ISTINA'],sl:['MIT','RES'],uk:['МІФ','ПРАВДА'],ru:['МИФ','ПРАВДА'],bg:['МИТ','ИСТИНА'],sv:['MYT','SANT'],da:['MYTE','SANDT'],no:['MYTE','SANT'],nb:['MYTE','SANT'],fi:['MYYTTI','TOTTA'],tr:['EFSANE','DOĞRU'],el:['ΜΥΘΟΣ','ΑΛΗΘΕΙΑ'],lt:['MITAS','TIESA'],lv:['MĪTS','PATIESĪBA'],et:['MÜÜT','TÕDE'],id:['MITOS','FAKTA'],vi:['NGỘ NHẬN','SỰ THẬT'],ja:['誤解','事実'],zh:['谣言','事实'],ko:['오해','사실'],ar:['خرافة','حقيقة'],hi:['मिथक','सच'],he:['מיתוס','נכון']};
V.myth=(v,d)=>{const I=(d.i||[]).map(x=>Array.isArray(x)?x:[x,0]).filter(x=>x[0]!=null&&String(x[0]).trim()).slice(0,3);if(!I.length)return V.text(v,{w:d.l||''});
const lw=MW[String(D.lang||'en').slice(0,2).toLowerCase()]||MW.en;const W0=d.a&&typeof d.a=='string'?d.a:lw[0],W1=d.b&&typeof d.b=='string'?d.b:lw[1];
const n=I.length,gap=22,ch=n==1?330:n==2?240:166,y0=(560-(n*ch+(n-1)*gap))/2;
const C=I.map((x,i)=>{const ok=N(x[1])==1,y=y0+i*(ch+gap);const card=el('div','card',`left:0;top:${y}px;width:864px;height:${ch}px`);
const tx=el('div','txt',`left:34px;top:${y+16}px;width:560px;height:${ch-32}px;display:flex;align-items:center;font-weight:700;line-height:1.18`);
const sp=el('span','',`background:linear-gradient(var(--acc),var(--acc)) no-repeat 0 100%/0% 5px;-webkit-box-decoration-break:clone;box-decoration-break:clone;text-decoration:line-through;text-decoration-thickness:5px;text-decoration-color:rgba(190,190,190,0)`);sp.textContent=String(x[0]);tx.append(sp);
const stw=n==3?212:228,sth=n==1?150:n==2?128:108;const stp=el('div','',`position:absolute;left:${614}px;top:${y+ch/2-sth/2}px;width:${stw}px;height:${sth}px;border:6px solid ${ok?'var(--acc)':'#9a9a9a'};border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;color:${ok?'var(--acc)':'#9a9a9a'};opacity:0;box-sizing:border-box`);
const ic=icon(ok?'check':'cross',Math.min(64,sth*.46),ok?D.acc:'#9a9a9a',7);ic.style.position='relative';const wd=el('div','big',`position:relative;font-size:40px;text-transform:uppercase;white-space:nowrap;letter-spacing:1px`,esc(ok?W1:W0));stp.append(ic,wd);
v.append(card,tx,stp);fit(tx,n==1?52:n==2?42:34,18,ch-32,560);fit(wd,40,16,sth*.4,stw-30);return {card,tx,sp,stp,ok,ic}});
return (t,st)=>C.forEach((c,i)=>{const b=.1+i*1.1;show(c.card,st(b,.5),16);show(c.tx,st(b+.1,.5),16);const q=st(b+.6,.35);
c.stp.style.opacity=cl(q*3);c.stp.style.transform=`rotate(-9deg) scale(${1.7-.7*q})`;draw(c.ic,st(b+.75,.4));
const k=st(b+.8,.45);if(!c.ok){c.sp.style.textDecorationColor=`rgba(190,190,190,${k})`;c.tx.style.color=`rgba(255,255,255,${1-.5*k})`}else c.sp.style.backgroundSize=`${100*k}% 5px`;
c.card.style.borderColor=c.ok&&q>=1?'rgba(255,255,255,.16)':'rgba(255,255,255,.16)'})};

// ===== CALENDAR: rok (12 mesiacov) alebo jeden mesiac =====
const expand=(L,mod)=>{const o=new Set();(Array.isArray(L)?L:[L]).forEach(x=>{if(Array.isArray(x)&&x.length>1){let f=Math.round(N(x[0])),t=Math.round(N(x[1]));if(t<f&&mod){for(let k=f;k<=mod;k++)o.add(k);for(let k=1;k<=t;k++)o.add(k)}else for(let k=f;k<=t;k++)o.add(k)}else if(typeof x=='string'&&/^\d+\s*-\s*\d+$/.test(x)){const [f,t]=x.split('-').map(Number);for(let k=f;k<=t;k++)o.add(k)}else{const k=Math.round(N(x));if(k)o.add(k)}});return [...o]};
V.calendar=(v,d)=>{const I=(d.i||[]).filter(x=>Array.isArray(x)).slice(0,4);const yr=Math.round(N(d.y))||new Date().getFullYear();const mon=d.n!=null&&N(d.n)>=1&&N(d.n)<=12&&d.m!='year'?Math.round(N(d.n)):0;
const col=['var(--acc)','#e8e8e8','#7a7a7a','#4a4a4a'],tcol=['#000','#000','#fff','#fff'];const L=D.lang||'en';
const S=I.map(x=>expand(x[1],mon?0:12));const cells=[];const LX=576,LW=288;
const dim=m=>new Date(yr,m,0).getDate();
if(!mon){const tw=126,th=104,gx=12,gy=14,top=(560-(3*th+2*gy))/2;let fm=x=>String(x);try{const f=new Intl.DateTimeFormat(L,{month:'short'});fm=m=>f.format(new Date(yr,m-1,15)).replace('.','')}catch(e){}
for(let m=1;m<=12;m++){const c=(m-1)%4,r=Math.floor((m-1)/4),x=c*(tw+gx),y=top+r*(th+gy);const box=el('div','',`position:absolute;left:${x}px;top:${y}px;width:${tw}px;height:${th}px;border:2px solid rgba(255,255,255,.22);border-radius:10px;overflow:hidden;box-sizing:border-box`);
const ser=S.map((a,i)=>a.includes(m)?i:-1).filter(i=>i>=0);const fills=ser.map((i,j)=>{const f=el('div','',`position:absolute;left:${j*100/ser.length}%;width:${100/ser.length}%;top:0;bottom:0;background:${col[i]};transform-origin:50% 100%;transform:scaleY(0)`);box.append(f);return {f,i}});
const nm=el('div','lab',`left:12px;top:10px;width:${tw-24}px;font-size:22px;letter-spacing:1.5px;color:#fff;z-index:1`,esc(fm(m)));box.append(nm);fit(nm,22,12,30,tw-24);v.append(box);
cells.push({box,fills,nm,k:m,ser})}}
else{const cw=70,chh=60,g=4;const first=(new Date(yr,mon-1,1).getDay()+6)%7,nd=dim(mon);const top=110;let mt='',wd=[];try{mt=new Intl.DateTimeFormat(L,{month:'long',year:'numeric'}).format(new Date(yr,mon-1,15));const f=new Intl.DateTimeFormat(L,{weekday:'short'});wd=[...Array(7)].map((_,i)=>f.format(new Date(2024,0,1+i)).replace('.',''))}catch(e){wd=['1','2','3','4','5','6','7']}
const ti=el('div','big',`left:0;top:16px;width:${7*(cw+g)}px;font-size:36px;text-transform:uppercase`,esc(mt));v.append(ti);fit(ti,36,18,44,7*(cw+g));cells.ttl=ti;
wd.forEach((w,i)=>{const e=el('div','lab',`left:${i*(cw+g)}px;top:72px;width:${cw}px;text-align:center;font-size:18px;letter-spacing:1px;color:${i>4?'#8a8a8a':'#bdbdbd'}`,esc(w));v.append(e);fit(e,18,11,24,cw);cells.push({hd:e})});
const rows=Math.ceil((first+nd)/7),ch=Math.min(chh,(540-top)/rows-g);for(let k=1;k<=nd;k++){const p=first+k-1,x=(p%7)*(cw+g),y=top+Math.floor(p/7)*(ch+g);const box=el('div','',`position:absolute;left:${x}px;top:${y}px;width:${cw}px;height:${ch}px;border:1.5px solid rgba(255,255,255,.18);border-radius:8px;overflow:hidden;box-sizing:border-box`);
const ser=S.map((a,i)=>a.includes(k)?i:-1).filter(i=>i>=0);const fills=ser.map((i,j)=>{const f=el('div','',`position:absolute;left:${j*100/ser.length}%;width:${100/ser.length}%;top:0;bottom:0;background:${col[i]};transform:scale(0)`);box.append(f);return {f,i}});
const nm=el('div','big',`left:0;top:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700;z-index:1`,String(k));box.append(nm);v.append(box);cells.push({box,fills,nm,k,ser})}}
const tot=mon?dim(mon):12;const rh=Math.min(130,520/Math.max(1,I.length)),ly0=280-rh*I.length/2;
const leg=I.map((x,i)=>{const y=ly0+i*rh;const sw=el('div','',`position:absolute;left:${LX}px;top:${y+6}px;width:22px;height:22px;border-radius:5px;background:${col[i]}`);
const lb=el('div','lab',`left:${LX+36}px;top:${y}px;width:${LW-36}px;font-size:24px;line-height:1.1;${i==0?'color:var(--acc)':''}`,esc(x[0]));v.append(sw,lb);fit(lb,24,13,56,LW-36);
const k=S[i].filter(z=>z>=1&&z<=tot).length;const days=mon?0:S[i].filter(z=>z>=1&&z<=12).reduce((a,m)=>a+dim(m),0);
const nb=el('div','big',`left:${LX+36}px;top:${y+lb.offsetHeight+6}px;width:${LW-36}px;font-size:50px;white-space:nowrap`,`${k}<span style="font-size:.55em;color:#8a8a8a"> / ${tot}</span>`);
const sub=el('div','lab',`left:${LX+36}px;top:${y+lb.offsetHeight+62}px;width:${LW-36}px;font-size:18px;letter-spacing:1px;text-transform:none;color:#9a9a9a`,esc(mon?NF(100*k/tot,0)+'\u202f%':'≈ '+UNIT(days,'day')));v.append(nb,sub);fit(nb,50,24,62,LW-36);return {sw,lb,nb,sub,h:lb.offsetHeight+96}});
const TH=leg.reduce((a,o)=>a+o.h+22,-22),sc=TH>540?540/TH:1;let yy=280-Math.min(TH,540)/2;leg.forEach(o=>{const dy=yy-parseFloat(o.lb.style.top);[o.sw,o.lb,o.nb,o.sub].forEach(e=>e.style.top=(parseFloat(e.style.top)+dy)+'px');if(sc<1)o.sub.style.display='none';yy+=(sc<1?o.h-24:o.h)+22});
return (t,st)=>{const p0=st(0,.8);if(cells.ttl)show(cells.ttl,p0,8);cells.forEach((c,j)=>{if(c.hd){c.hd.style.opacity=p0;return}c.box.style.opacity=cl(p0*2.5-(c.k/(mon?31:12))*1.5);
c.fills.forEach(o=>{const n=S[o.i].length||1,pos=S[o.i].indexOf(c.k);const q=st(1+o.i*.8+.7*pos/n,.35);o.f.style.transform=mon?`scale(${E(q)})`:`scaleY(${E(q)})`;if(q>.5&&c.ser.length==1)c.nm.style.color=tcol[o.i]})});
leg.forEach((o,i)=>{const q=st(1+i*.8,.5);o.sw.style.opacity=q;show(o.lb,q,6);show(o.nb,st(1.3+i*.8,.5),6);show(o.sub,st(1.5+i*.8,.5),6)})}};
})();
