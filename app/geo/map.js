// ---------- mapa: glóbus sa otočí ku krajine, priblíži sa, krajina sa rozsvieti, potom mestá, trasy a rieky ----------
let GEOF=null;
function geoInit(){if(GEOF||!window.topojson||!window.d3||!window.TOPO)return GEOF;GEOF=topojson.feature(TOPO,TOPO.objects.c).features;
GEOF.forEach(f=>{f._c=d3.geoCentroid(f);const b=d3.geoBounds(f);let r=0;[[b[0][0],b[0][1]],[b[1][0],b[1][1]],[b[0][0],b[1][1]],[b[1][0],b[0][1]]].forEach(p=>{r=Math.max(r,d3.geoDistance(f._c,p))});f._r=b[0][0]>b[1][0]?Math.PI:r});return GEOF}
// hlavná časť krajiny (bez zámorských území), aby sa priblížilo na to podstatné
function geoCore(f){const g=f.geometry;if(!g||g.type!='MultiPolygon')return g;const P=g.coordinates.map(c=>{const p={type:'Polygon',coordinates:c};return {c,a:d3.geoArea(p),m:d3.geoCentroid(p),p}});
const big=P.reduce((a,b)=>b.a>a.a?b:a);const bb=d3.geoBounds(big.p);let r0=0;[[bb[0][0],bb[0][1]],[bb[1][0],bb[1][1]],[bb[0][0],bb[1][1]],[bb[1][0],bb[0][1]]].forEach(p=>{r0=Math.max(r0,d3.geoDistance(big.m,p))});
const lim=Math.max(.17,r0*1.5);return {type:'MultiPolygon',coordinates:P.filter(x=>d3.geoDistance(x.m,big.m)<lim).map(x=>x.c)}}
V.map=(v,d)=>{if(d.hist)return V.hmap(v,d);const F=geoInit();if(!F)return V.text(v,{w:d.l||(d.names&&d.names[d.main])||''});
const MW=864,MH=560,R=1.6;const cv=el('canvas','',`position:absolute;left:0;top:${D.wide?36:0}px;width:${MW}px;height:${MH}px;-webkit-mask-image:radial-gradient(ellipse 70% 66% at 50% 50%,#000 62%,transparent 100%);mask-image:radial-gradient(ellipse 70% 66% at 50% 50%,#000 62%,transparent 100%)`);cv.width=MW*R;cv.height=MH*R;v.append(cv);
const ctx=cv.getContext('2d');ctx.scale(R,R);ctx.lineJoin='round';ctx.lineCap='round';
const C=d.c||[],sel=new Set(C),group=!!d.group,PTS=d.pts||[],RT=d.r||[],RV=d.v||[];
const SF=F.filter(f=>sel.has(f.id)).sort((a,b)=>(a.id==d.main)-(b.id==d.main));
const core={};SF.forEach(f=>{core[f.id]=geoCore(f)});
const geoms=SF.map(f=>core[f.id]);PTS.forEach(p=>geoms.push({type:'Point',coordinates:[p.lon,p.lat]}));RT.forEach(r=>geoms.push({type:'LineString',coordinates:r}));RV.forEach(x=>geoms.push({type:'MultiLineString',coordinates:x.l}));
const ONTO=d.onto?F.find(f=>f.id==d.onto):null;if(ONTO)geoms.push(geoCore(ONTO));
const tiny=C.filter(c=>!SF.some(f=>f.id==c)&&d.lp&&d.lp[c]);tiny.forEach(c=>geoms.push({type:'Point',coordinates:d.lp[c]}));
if(!geoms.length)return V.text(v,{w:d.l||''});
const FC={type:'GeometryCollection',geometries:geoms};const gb=d3.geoBounds(FC);let lo0=gb[0][0],lo1=gb[1][0];if(lo1<lo0)lo1+=360;
const cen=gb[1][0]-gb[0][0]>300&&gb[0][0]<gb[1][0]?d3.geoCentroid(FC):[((lo0+lo1)/2+540)%360-180,(gb[0][1]+gb[1][1])/2];
const proj=d3.geoOrthographic().clipAngle(90).precision(.4),path=d3.geoPath(proj,ctx);
const S0=MH*.46,ROT=[-cen[0],-Math.max(-60,Math.min(60,cen[1]))];
proj.rotate(ROT).scale(1).translate([0,0]);const bb=d3.geoPath(proj).bounds(FC);const bw=bb[1][0]-bb[0][0],bh=bb[1][1]-bb[0][1];
const onlyPts=!SF.length&&!RV.length&&RT.length==0;
let SF_=bw>1e-6||bh>1e-6?Math.min((MW-150)/Math.max(bw,1e-6),(MH-130)/Math.max(bh,1e-6)):2400;
SF_=Math.max(S0,Math.min(onlyPts?2400:5200,SF_));
const R0=[ROT[0]+62,ROT[1]*.35];const GR=d3.geoGraticule10();
const ip=d3.geoInterpolate([-R0[0],-R0[1]],[-ROT[0],-ROT[1]]);
// popisky (HTML, písmo značky)
const OY=D.wide?36:0;const mk=(css,html)=>{const e=el('div','',`position:absolute;margin-top:${OY}px;white-space:nowrap;opacity:0;text-shadow:0 2px 10px #000,0 0 3px #000;${css}`,html);v.append(e);return e};
const CL=group?[]:SF.concat([]).reverse().map(f=>f.id).concat(tiny).slice(0,4).map((c,i)=>{const isM=c==d.main;const fl=d.flags&&d.flags[c]?`<img src="${d.flags[c]}" style="height:${isM?38:28}px;width:auto;border-radius:3px;margin-right:12px;vertical-align:middle;box-shadow:0 2px 10px rgba(0,0,0,.6)">`:'';
return {c,e:mk(`font-weight:800;text-transform:uppercase;letter-spacing:${isM?1:2}px;font-size:${isM?40:26}px;color:${isM?'#fff':'#e6e6e6'}`,fl+`<span style="vertical-align:middle">${esc((d.names||{})[c]||c)}</span>`),m:isM}});
const PL=PTS.map(p=>({p,e:mk(`font-family:var(--ft);font-weight:700;font-size:24px;color:#fff;letter-spacing:1px`,esc(p.n))}));
const TAG=d.l||(group&&C.length?'':'');const tg=TAG?mk(`left:0;top:${MH-46}px;font-weight:800;text-transform:uppercase;font-size:30px;letter-spacing:3px;color:var(--acc);border-left:6px solid var(--acc);padding-left:14px`,esc(TAG)):null;
const NST=1.2;
return (t,st)=>{const p=st(0,1.7),pr=EI(cl(p*1.35)),pz=EI(cl((p-.22)/.78));const rc=ip(pr);const rot=[-rc[0],-rc[1]];const sc=S0*Math.pow(SF_/S0,pz);
proj.rotate(rot).scale(sc).translate([MW/2,MH/2]);ctx.clearRect(0,0,MW,MH);
ctx.beginPath();path({type:'Sphere'});ctx.fillStyle='rgba(255,255,255,.035)';ctx.fill();ctx.strokeStyle='rgba(255,255,255,.25)';ctx.lineWidth=1.5;ctx.stroke();
ctx.beginPath();path(GR);ctx.strokeStyle='rgba(255,255,255,.06)';ctx.lineWidth=1;ctx.stroke();
const cr=[rc[0],rc[1]],va=Math.min(Math.PI/2,Math.asin(Math.min(1,Math.hypot(MW,MH)/2/sc)))+.06;
ctx.beginPath();F.forEach(f=>{if(d3.geoDistance(cr,f._c)-f._r<va)path(f)});ctx.fillStyle='#262626';ctx.fill();ctx.strokeStyle='rgba(255,255,255,.30)';ctx.lineWidth=.9;ctx.stroke();
const hp=st(NST,.8);
SF.forEach(f=>{const isM=f.id==d.main||group;ctx.beginPath();path(f);ctx.globalAlpha=hp*(isM?.88:.42);ctx.fillStyle=isM?D.acc:'#e8e8e8';ctx.fill();ctx.globalAlpha=hp;
ctx.strokeStyle=isM?'#fff':'rgba(255,255,255,.9)';ctx.lineWidth=isM&&!group?2.2:1.2;if(isM&&!group){ctx.shadowColor=D.acc;ctx.shadowBlur=26}ctx.stroke();ctx.shadowBlur=0;ctx.globalAlpha=1});
// skutočná veľkosť: hlavná krajina sa presunie na inú (rovnaká plocha na zemeguli)
if(ONTO&&SF.length){const M=SF.find(f=>f.id==d.main)||SF[SF.length-1];const g=core[M.id];const s0=d3.geoCentroid(g),t0=d3.geoCentroid(geoCore(ONTO));const mp=EI(st(NST+.9,1.8));
ctx.beginPath();path(ONTO);ctx.strokeStyle='rgba(255,255,255,.9)';ctx.lineWidth=1.6;ctx.globalAlpha=st(NST+.5,.6);ctx.stroke();ctx.globalAlpha=1;
if(mp>0){const m=d3.geoInterpolate(s0,t0)(mp);const r1=d3.geoRotation([-s0[0],-s0[1]]),r2=d3.geoRotation([-m[0],-m[1]]);const mv=c=>r2.invert(r1(c));
const tr=geo=>({type:geo.type,coordinates:geo.type=='Polygon'?geo.coordinates.map(r=>r.map(mv)):geo.coordinates.map(pp=>pp.map(r=>r.map(mv)))});
ctx.beginPath();path(tr(g));ctx.globalAlpha=.6;ctx.fillStyle=D.acc;ctx.fill();ctx.globalAlpha=1;ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.setLineDash([8,6]);ctx.stroke();ctx.setLineDash([]);
const lo=CL.find(o=>o.c==M.id);if(lo&&d.lp&&d.lp[M.id]){d.lp[M.id+'_m']=mv(d.lp[M.id])}}}
// malé krajiny: pulzujúci kruh, aby boli vidno
C.forEach(c=>{const f=SF.find(x=>x.id==c);const tinyNow=!f||path.area(core[c])<500;if(!tinyNow||!d.lp||!d.lp[c])return;const q=proj(d.lp[c]);if(!q||d3.geoDistance(cr,d.lp[c])>1.5)return;
ctx.globalAlpha=hp;ctx.strokeStyle=D.acc;ctx.lineWidth=4;ctx.beginPath();ctx.arc(q[0],q[1],20+6*Math.sin(t*4),0,6.3);ctx.stroke();ctx.globalAlpha=1});
// rieky
RV.forEach((x,i)=>{const rp=st(NST+.6+i*.5,1.4);if(rp<=0)return;ctx.strokeStyle='#fff';ctx.lineWidth=3.2;ctx.globalAlpha=.95;ctx.shadowColor='#fff';ctx.shadowBlur=8;
x.l.forEach(ln=>{const n=Math.max(2,Math.round(ln.length*rp));ctx.beginPath();path({type:'LineString',coordinates:ln.slice(0,n)});ctx.stroke()});ctx.shadowBlur=0;ctx.globalAlpha=1});
// trasy po oblúku zemegule s bodom, ktorý po nej beží
const RTP=RT.map(r=>{const P=[];for(let a=0;a<r.length-1;a++){const g=d3.geoInterpolate(r[a],r[a+1]);const n=Math.max(6,Math.round(d3.geoDistance(r[a],r[a+1])*60));for(let j=a?1:0;j<=n;j++)P.push(g(j/n))}return P});
RT.forEach((r,i)=>{const rp=st(NST+1+i*.6,1.2+.3*(r.length-2));if(rp<=0)return;const AP=RTP[i];const N=AP.length-1,k=Math.max(1,Math.round(N*rp));const L=AP.slice(0,k+1);const g=u=>AP[Math.min(N,Math.floor(u*N))];
ctx.strokeStyle=D.acc;ctx.lineWidth=4.5;ctx.setLineDash([14,9]);ctx.lineDashOffset=-t*30;ctx.beginPath();path({type:'LineString',coordinates:L});ctx.stroke();ctx.setLineDash([]);
const hd=proj(rp<1?L[L.length-1]:g((t*.35+i*.3)%1));if(hd){ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(hd[0],hd[1],7,0,6.3);ctx.fill()}});
// mestá
const cb=[];PTS.forEach((pt,i)=>{const pp=st(NST+.4+i*.35,.5);const q=proj([pt.lon,pt.lat]);const on=q&&d3.geoDistance(cr,[pt.lon,pt.lat])<1.5;PL[i].e.style.opacity=on?pp:0;if(!on||pp<=0)return;
ctx.globalAlpha=pp;if(pt.cap){ctx.strokeStyle=D.acc;ctx.lineWidth=3;ctx.beginPath();ctx.arc(q[0],q[1],13+3*Math.sin(t*3+i),0,6.3);ctx.stroke()}ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(q[0],q[1],7,0,6.3);ctx.fill();ctx.globalAlpha=1;
const e=PL[i].e,w=e.offsetWidth,h=e.offsetHeight||30;let x=q[0]+20;if(x+w>MW-6)x=q[0]-20-w;x=Math.max(4,x);let y=q[1]-16;
for(let k=0;k<3;k++){const hit=cb.find(b=>x<b[0]+b[2]&&x+w>b[0]&&y<b[1]+b[3]&&y+h>b[1]);if(!hit)break;y=hit[1]+hit[3]+2}cb.push([x,y,w,h]);e.style.left=x+'px';e.style.top=y+'px'});
// popisky krajín (vlajka + názov)
const lp=st(NST+.3,.6);const boxes=PL.filter(o=>o.e.style.opacity>0).map(o=>[o.e.offsetLeft,o.e.offsetTop,o.e.offsetWidth,o.e.offsetHeight]);
CL.forEach(o=>{const ll=d.lp&&(d.lp[o.c+'_m']||d.lp[o.c]);const q=ll&&proj(ll);const on=q&&d3.geoDistance(cr,ll)<1.4;o.e.style.opacity=on?lp:0;if(!on)return;const w=o.e.offsetWidth,h=o.e.offsetHeight;
let x=Math.max(6,Math.min(MW-w-6,q[0]-w/2)),y=Math.max(6,Math.min(MH-h-6,q[1]-h/2));
for(let k=0;k<4;k++){const hit=boxes.find(b=>x<b[0]+b[2]&&x+w>b[0]&&y<b[1]+b[3]&&y+h>b[1]);if(!hit)break;y=Math.min(MH-h-6,hit[1]+hit[3]+8);if(y>=MH-h-6){y=Math.max(6,hit[1]-h-8)}}
boxes.push([x,y,w,h]);o.e.style.left=x+'px';o.e.style.top=y+'px';o.e.style.transform=`translateY(${(1-E(lp))*16}px)`});
if(tg)tg.style.opacity=st(NST+.5,.6)}};
// ---------- historická mapa: hranice podľa roku (približné), rast ríše v čase ----------
const YEARW={en:['AD','BC'],sk:['n. l.','pred n. l.'],cs:['n. l.','př. n. l.'],de:['n. Chr.','v. Chr.'],fr:['apr. J.-C.','av. J.-C.'],es:['d. C.','a. C.'],it:['d.C.','a.C.'],pl:['n.e.','p.n.e.'],hu:['i. sz.','i. e.'],nl:['n.Chr.','v.Chr.'],pt:['d.C.','a.C.']};
const yearTxt=y=>{const w=YEARW[D.lang]||YEARW.en;return '≈ '+(y<0?String(-y)+' '+w[1]:String(y)+(y<1500?' '+w[0]:''))};
V.hmap=(v,d)=>{const F=geoInit();if(!F||!window.HIST)return V.text(v,{w:d.l||''});
const FR=(d.hist||[]).map(f=>{const T=HIST[String(f.y)];if(!T)return null;const fs=topojson.feature(T,T.objects.h).features;const hs=new Set(f.hl||[]);return {y:f.y,fs,hl:fs.filter(x=>hs.has(x.properties.n))}}).filter(Boolean);
if(!FR.length)return V.text(v,{w:d.l||''});
const MW=864,MH=560,R=1.6,OY=D.wide?36:0;const cv=el('canvas','',`position:absolute;left:0;top:${OY}px;width:${MW}px;height:${MH}px;-webkit-mask-image:radial-gradient(ellipse 70% 66% at 50% 50%,#000 62%,transparent 100%);mask-image:radial-gradient(ellipse 70% 66% at 50% 50%,#000 62%,transparent 100%)`);cv.width=MW*R;cv.height=MH*R;v.append(cv);
const ctx=cv.getContext('2d');ctx.scale(R,R);ctx.lineJoin='round';
const HL=[].concat(...FR.map(f=>f.hl));const FC={type:'FeatureCollection',features:HL.length?HL:FR[0].fs};
const gb=d3.geoBounds(FC);let lo0=gb[0][0],lo1=gb[1][0];if(lo1<lo0)lo1+=360;const cen=HL.length?[((lo0+lo1)/2+540)%360-180,(gb[0][1]+gb[1][1])/2]:[15,40];
const proj=d3.geoOrthographic().clipAngle(90).precision(.5),path=d3.geoPath(proj,ctx);const ROT=[-cen[0],-Math.max(-60,Math.min(60,cen[1]))];proj.rotate(ROT).scale(1).translate([0,0]);
const bb=d3.geoPath(proj).bounds(FC);const S0=MH*.46;let SF_=Math.min((MW-120)/Math.max(1e-6,bb[1][0]-bb[0][0]),(MH-110)/Math.max(1e-6,bb[1][1]-bb[0][1]));SF_=Math.max(S0,Math.min(3600,SF_));
const ip=d3.geoInterpolate([-(ROT[0]+50),-ROT[1]*.35],[-ROT[0],-ROT[1]]);const GR=d3.geoGraticule10();
const yt=el('div','big',`left:0;top:${OY+4}px;font-size:58px;color:var(--acc);white-space:nowrap;opacity:0;text-shadow:0 2px 12px #000`);v.append(yt);
const tg=d.l?el('div','',`position:absolute;left:0;top:${OY+MH-46}px;font-weight:800;text-transform:uppercase;font-size:30px;letter-spacing:3px;color:var(--acc);border-left:6px solid var(--acc);padding-left:14px;opacity:0`,esc(d.l)):null;if(tg)v.append(tg);
const LB=FR.map(f=>{const seen=new Set();return f.hl.filter(x=>{if(seen.has(x.properties.n))return false;seen.add(x.properties.n);return true}).slice(0,3).map(x=>{const big=x.geometry.type=='MultiPolygon'?x.geometry.coordinates.map(c=>({type:'Polygon',coordinates:c})).reduce((a,b)=>d3.geoArea(b)>d3.geoArea(a)?b:a):x.geometry;
const e=el('div','',`position:absolute;margin-top:${OY}px;white-space:nowrap;font-weight:800;text-transform:uppercase;font-size:30px;letter-spacing:1px;color:#fff;text-shadow:0 2px 10px #000,0 0 3px #000;opacity:0`,esc(x.properties.n));v.append(e);return {e,c:d3.geoCentroid(big)}})});
const n=FR.length,SEG=1.25;
return (t,st)=>{const p=st(0,1.5),pr=EI(cl(p*1.35)),pz=EI(cl((p-.22)/.78));const rc=ip(pr);const sc=S0*Math.pow(SF_/S0,pz);proj.rotate([-rc[0],-rc[1]]).scale(sc).translate([MW/2,MH/2]);
ctx.clearRect(0,0,MW,MH);ctx.beginPath();path({type:'Sphere'});ctx.fillStyle='rgba(255,255,255,.035)';ctx.fill();ctx.strokeStyle='rgba(255,255,255,.25)';ctx.lineWidth=1.5;ctx.stroke();
ctx.beginPath();path(GR);ctx.strokeStyle='rgba(255,255,255,.06)';ctx.lineWidth=1;ctx.stroke();
ctx.beginPath();F.forEach(f=>path(f));ctx.fillStyle='#1d1d1d';ctx.fill();
// ktorý rok práve ukazujeme (prelínanie medzi rokmi)
const k=n>1?cl((st(1,1)>0?(t-0):0)):0;let fi=0,mix=0;if(n>1){for(let i=1;i<n;i++){const q=st(1+i*SEG,.7);if(q>0){fi=i-1;mix=q}if(q>=1){fi=i;mix=0}}}
const drawF=(f,a)=>{if(a<=0)return;ctx.globalAlpha=a;ctx.beginPath();f.fs.forEach(x=>path(x));ctx.fillStyle='#2c2c2c';ctx.fill();ctx.strokeStyle='rgba(255,255,255,.22)';ctx.lineWidth=.8;ctx.stroke();
const hp=st(.9,.8);ctx.beginPath();f.hl.forEach(x=>path(x));ctx.globalAlpha=a*hp*.88;ctx.fillStyle=D.acc;ctx.fill();ctx.globalAlpha=a*hp;ctx.strokeStyle='#fff';ctx.lineWidth=1.8;ctx.shadowColor=D.acc;ctx.shadowBlur=20;ctx.stroke();ctx.shadowBlur=0;ctx.globalAlpha=1};
drawF(FR[fi],1-mix);if(mix>0)drawF(FR[fi+1],mix);
const cur=mix>.5?fi+1:fi;yt.textContent=yearTxt(FR[cur].y);yt.style.opacity=st(.5,.5);if(tg)tg.style.opacity=st(1.2,.6);
LB.forEach((L,i)=>L.forEach(o=>{const q=proj(o.c);const on=i==cur&&q&&d3.geoDistance([rc[0],rc[1]],o.c)<1.4;o.e.style.opacity=on?st(1.2,.5):0;if(!on)return;const w=o.e.offsetWidth,h=o.e.offsetHeight;
o.e.style.left=Math.max(6,Math.min(MW-w-6,q[0]-w/2))+'px';o.e.style.top=Math.max(50,Math.min(MH-h-6,q[1]-h/2))+'px'}))}};
