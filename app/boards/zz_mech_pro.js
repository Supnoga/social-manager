// PRESNÉ MODELY (PRO): rozmery a pohyb počíta matematika, nie odhad. Evolventné ozubenie (kolesá do seba naozaj zapadajú),
// kľukový mechanizmus (piest, ojnica, kľuka), rotačný (Wankelov) motor s epitrochoidnou komorou.
// Geometria (MECHGEO) je čistá matematika bez kreslenia, testuje ju tests/mech_geo_test.js.
//--GEO--
var MECHGEO=(()=>{
const inv=a=>Math.tan(a)-a,AL=20*Math.PI/180;
// obrys ozubeného kolesa s modulom 1 (rozstupový polomer z/2), zub 0 mieri na uhol 0; bl = vôľa
const _gc={};
const gearPts=(z,bl)=>{bl=bl==null?.08:bl;const key=z+'|'+bl;if(_gc[key])return _gc[key];const r=z/2,rb=r*Math.cos(AL),rf=r-1.25;let ra=r+1;
const half=q=>Math.PI/(2*z)*(1-bl)+inv(AL)-(q>rb?inv(Math.acos(rb/q)):0);
while(half(ra)<.22/z&&ra>r+.3)ra-=.02;
const q0=Math.max(rf,rb),P=[],S=6;
for(let k=0;k<z;k++){const c=2*Math.PI*k/z;const pt=(q,a)=>P.push([q*Math.cos(a),q*Math.sin(a)]);
if(rf<rb)pt(rf,c-half(rb));for(let i=0;i<=S;i++){const q=q0+(ra-q0)*i/S;pt(q,c-half(q))}
for(let i=S;i>=0;i--){const q=q0+(ra-q0)*i/S;pt(q,c+half(q))}if(rf<rb)pt(rf,c+half(rb));pt(rf,c+Math.PI/z)}
return _gc[key]=P};
// uhol druhého kolesa, aby zapadalo do prvého: koleso 2 leží od kolesa 1 v smere beta
const meshRot=(rot1,z1,z2,beta)=>(beta||0)+Math.PI+Math.PI/z2-(rot1-(beta||0))*z1/z2;
// kľukový mechanizmus: th = uhol kľuky od hornej úvrate; vráti zdvih piestneho čapu pod hornou úvraťou a polohu ojničného čapu
const crank=(th,r,l)=>({drop:r+l-(r*Math.cos(th)+Math.sqrt(l*l-r*r*Math.sin(th)*Math.sin(th))),px:r*Math.sin(th),py:-r*Math.cos(th)});
// Wankel: komora = epitrochoida, rotor = trojuholník s vypuklými bokmi; fi = natočenie rotora, hriadeľ sa točí 3x rýchlejšie
const wankel=(R,e)=>{const house=(u,off)=>{const x=e*Math.cos(3*u)+R*Math.cos(u),y=e*Math.sin(3*u)+R*Math.sin(u);if(!off)return [x,y];
const dx=-3*e*Math.sin(3*u)-R*Math.sin(u),dy=3*e*Math.cos(3*u)+R*Math.cos(u),n=Math.hypot(dx,dy);return [x+dy/n*off,y-dx/n*off]};
const Rm=R-2*e-2,h=R*Math.sin(Math.PI/3),s=Rm-R/2,rho=(h*h+s*s)/(2*s),dc=Rm-rho,ha=Math.asin(h/rho);
const center=fi=>[e*Math.cos(3*fi),e*Math.sin(3*fi)];
const apex=(fi,k)=>{const c=center(fi),a=fi+2*Math.PI*k/3;return [c[0]+R*Math.cos(a),c[1]+R*Math.sin(a)]};
// bok rotora medzi vrcholmi k a k+1, n bodov
const flank=(fi,k,n)=>{const c=center(fi),b=fi+2*Math.PI*k/3+Math.PI/3,ox=c[0]+dc*Math.cos(b),oy=c[1]+dc*Math.sin(b),P=[];
for(let i=0;i<=n;i++){const a=b-ha+2*ha*i/n;P.push([ox+rho*Math.cos(a),oy+rho*Math.sin(a)])}return P};
const chamber=(fi,k,n)=>{const a0=fi+2*Math.PI*k/3,P=[];for(let i=0;i<=n;i++)P.push(house(a0+2*Math.PI/3*i/n));return P.concat(flank(fi,k,n).reverse())};
const area=P=>{let s=0;for(let i=0;i<P.length;i++){const a=P[i],b=P[(i+1)%P.length];s+=a[0]*b[1]-b[0]*a[1]}return Math.abs(s)/2};
return {house,center,apex,flank,chamber,area,Rm}};
return {gearPts,meshRot,crank,wankel}})();
//--END-GEO--
{
const PRO={},G=MECHGEO,TAU=Math.PI*2;
const WALL='#1d1d1d',METAL='#d4d4d4',DARK='#2c2c2c';
// šrafovanie rezu (ako na technickom výkrese) v aktuálnej ceste
const hatch=(x,pathFn,rule)=>{x.save();x.beginPath();pathFn();x.clip(rule||'nonzero');x.strokeStyle='rgba(255,255,255,.13)';x.lineWidth=2;x.beginPath();for(let i=-600;i<900;i+=15){x.moveTo(i,0);x.lineTo(i+560,560)}x.stroke();x.restore()};
const poly=(x,P)=>{P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.closePath()};
const labs=(v,d,n)=>{const L=(Array.isArray(d.l)?d.l:[]).map(s=>s==null?'':String(s));return [...Array(n)].map((_,i)=>{const e=el('div','lab','left:0;top:0;width:280px;font-size:26px;opacity:0',esc(L[i]||''));v.append(e);e._on=!!(L[i]||'').trim();return e})};
const place=(e,l,t,w,al)=>{e.style.left=l+'px';e.style.top=t+'px';e.style.width=w+'px';e.style.textAlign=al||'left';fit(e,26,15,40,w)};

// presné ozubené koleso: rp = rozstupový polomer, z = počet zubov
const GEARPRO=(x,cx,cy,rp,z,rot,col,opt)=>{z=Math.max(8,Math.round(z));const m=2*rp/z,P=G.gearPts(z);x.save();x.translate(cx,cy);x.rotate(rot);x.beginPath();
P.forEach((q,i)=>i?x.lineTo(q[0]*m,q[1]*m):x.moveTo(q[0]*m,q[1]*m));x.closePath();x.fillStyle=(opt&&opt.fill)||'#151515';x.fill();x.strokeStyle=col;x.lineWidth=Math.max(2,Math.min(4,m*.42));x.stroke();
const rf=rp-1.25*m,lw=Math.max(2,Math.min(3.5,rp*.05));x.lineWidth=lw;
if(rp>46){const nH=z>=28?6:z>=18?5:4,rh=rf*(z>=18?.2:.14),rc=rf*(z>=18?.6:.57);for(let k=0;k<nH;k++){const a=k*TAU/nH;x.beginPath();x.arc(Math.cos(a)*rc,Math.sin(a)*rc,rh,0,TAU);x.fillStyle='#000';x.fill();x.stroke()}}
else if(rp>14){x.beginPath();x.arc(rf*.62,0,Math.max(2.5,rf*.13),0,TAU);x.fillStyle=col;x.fill()}
const hub=Math.max(4,Math.min(rf*.26,30));x.beginPath();x.arc(0,0,hub,0,TAU);x.fillStyle='#000';x.fill();x.stroke();if(hub>9){x.fillStyle=col;x.fillRect(-hub*.18,-hub*1.02,hub*.36,hub*.4)}
x.restore()};
window.GEARPRO=GEARPRO;window.GEARMESH=G.meshRot;

// ---------- dve ozubené kolesá: n=[zuby hnacieho, zuby hnaného] ----------
PRO.gears=(v,d)=>{const x=cv2(v,864,560),A=D.acc;const nz=i=>Math.max(9,Math.min(48,Math.round(N((d.n||[])[i])||[12,30][i])));const z1=nz(0),z2=nz(1);
const m=Math.min(640/(z1+z2+4.4),400/(Math.max(z1,z2)+2.6)),r1=m*z1/2,r2=m*z2/2,c1=432-(r1+r2+2*m)+m+r1,c2=c1+r1+r2,cy=232;
const L=labs(v,d,2);const w1=Math.max(150,2*r1+60),w2=Math.max(150,2*r2+40);
place(L[0],Math.max(0,c1-w1/2),cy+Math.max(r1,r2)+m+22,w1,'center');place(L[1],Math.min(864-w2,c2-w2/2),cy+Math.max(r1,r2)+m+22,w2,'center');L[1].style.color=A;
const big=el('div','big',`left:232px;top:${cy+Math.max(r1,r2)+m+62}px;width:400px;text-align:center;font-size:44px;opacity:0;color:#fff`,`${z1} : ${z2}`);v.append(big);
const arr=(cx,r,s,c)=>{const Rr=r+m+14,a0=-Math.PI/2-.45,a1=-Math.PI/2+.45;x.strokeStyle=c;x.lineWidth=3;x.beginPath();x.arc(cx,cy,Rr,a0,a1);x.stroke();const e=s>0?a1:a0,tx=-Math.sin(e)*s,ty=Math.cos(e)*s,px=cx+Math.cos(e)*Rr,py=cy+Math.sin(e)*Rr;x.beginPath();x.moveTo(px-tx*12-Math.cos(e)*7,py-ty*12-Math.sin(e)*7);x.lineTo(px,py);x.lineTo(px-tx*12+Math.cos(e)*7,py-ty*12+Math.sin(e)*7);x.stroke()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));x.clearRect(0,0,864,560);x.globalAlpha=p;const w=t*1.1*Math.min(1,14/z1+.45);
GEARPRO(x,c1,cy,r1,z1,w,'#fff');GEARPRO(x,c2,cy,r2,z2,G.meshRot(w,z1,z2,0),A);x.globalAlpha=p*sp;arr(c1,r1,1,'#fff');arr(c2,r2,-1,A);x.globalAlpha=1;
L.forEach(e=>e.style.opacity=e._on?sp:0);big.style.opacity=E(st(1,.6))}};

// ---------- štvortaktný motor v reze: l = názvy 4 dôb ----------
PRO.piston=(v,d)=>{const x=cv2(v,864,560),A=D.acc,L=labs(v,d,4),any=L.some(e=>e._on);
const CX=any?290:432,B=92,TOP=36,DECK=96,r=56,l=176,PH=84,PIN=46,CL=12,CY=DECK+CL+PIN+r+l,Ri=104,LB=306,T=5.6;
L.forEach((e,i)=>place(e,CX+250,138+i*74,864-(CX+250)-6,'left'));
const num=L.map((e,i)=>{const n=el('div','big',`left:${CX+196}px;top:${130+i*74}px;width:44px;text-align:center;font-size:34px;opacity:0`,String(i+1));v.append(n);return n});
const rnd=[...Array(16)].map((_,i)=>[((i*0.754878+.37)%1),((i*0.569840+.11)%1)]);
const outer=()=>{x.rect(CX-B-24,TOP,2*B+48,LB-TOP+40);x.moveTo(CX+Ri+16,CY);x.arc(CX,CY,Ri+16,0,TAU)};
const cavity=()=>{x.rect(CX-B,DECK,2*B,CY-DECK);x.moveTo(CX+Ri,CY);x.arc(CX,CY,Ri,0,TAU)};
const port=s=>{x.beginPath();x.moveTo(CX+s*(B+118),62);x.lineTo(CX+s*96,62);x.quadraticCurveTo(CX+s*46,62,CX+s*46,DECK+1)};
const portPt=(s,u)=>{u=cl(u);if(u<.62){return [CX+s*(B+118)+(s*96-s*(B+118))*(u/.62),62]}const q=(u-.62)/.38,a=1-q;return [CX+a*a*s*96+2*a*q*s*46+q*q*s*46,a*a*62+2*a*q*62+q*q*(DECK+8)]};
const valve=(s,lift,col)=>{const vx=CX+s*46,y=DECK+lift;x.strokeStyle='#e8e8e8';x.lineWidth=6;x.beginPath();x.moveTo(vx,y);x.lineTo(vx,TOP-30+lift);x.stroke();
x.beginPath();x.moveTo(vx-27,y+3);x.lineTo(vx+27,y+3);x.lineTo(vx+15,y-9);x.lineTo(vx-15,y-9);x.closePath();x.fillStyle=col||METAL;x.fill();x.strokeStyle='#000';x.lineWidth=1.5;x.stroke();
x.strokeStyle='#bdbdbd';x.lineWidth=2.5;x.beginPath();const y0=TOP-26+lift,y1=TOP-3,n=5;for(let i=0;i<=n;i++){const yy=y0+(y1-y0)*i/n;x.lineTo(vx+(i%2?10:-10),yy)}x.stroke();
x.fillStyle='#e8e8e8';x.fillRect(vx-13,TOP-32+lift,26,5)};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));x.clearRect(0,0,864,560);x.globalAlpha=p;const cyc=((t/T)%1+1)%1,th=cyc*2*TAU,stg=Math.min(3,Math.floor(cyc*4)),q=cyc*4-stg;
const K=G.crank(th,r,l),wy=CY-r-l+K.drop,crown=wy-PIN,pinX=CX+K.px,pinY=CY+K.py;
// blok a hlava v reze
x.lineWidth=8;x.strokeStyle='#fff';x.beginPath();outer();x.stroke();x.fillStyle=WALL;x.beginPath();outer();x.fill();hatch(x,outer);
x.beginPath();cavity();x.lineWidth=8;x.stroke();x.fillStyle='#000';x.beginPath();cavity();x.fill();
// sací a výfukový kanál
[-1,1].forEach(s=>{x.lineCap='butt';port(s);x.strokeStyle='#fff';x.lineWidth=40;x.stroke();port(s);x.strokeStyle='#000';x.lineWidth=32;x.stroke();x.lineCap='round'});
// plyn vo valci
const top=DECK+2,hgt=Math.max(0,crown-top);
x.fillStyle=stg==0?'rgba(255,255,255,.07)':stg==1?`rgba(255,255,255,${.07+.2*q})`:stg==2?A:'rgba(150,150,150,.26)';if(stg==2)x.globalAlpha=p*(1-.6*q);x.fillRect(CX-B+2,top,2*B-4,hgt);x.globalAlpha=p;
if(stg!=2)rnd.forEach((u,i)=>{const vis=stg==0?(i/16<q*1.1):stg==3?(i/16>q*1.05):true;if(!vis)return;x.fillStyle=stg==3?'#8a8a8a':'#fff';x.beginPath();x.arc(CX+(u[0]-.5)*2*(B-16),top+8+u[1]*Math.max(0,hgt-16),4,0,TAU);x.fill()});
// prúdenie v kanáloch
if(stg==0)for(let k=0;k<5;k++){const P=portPt(-1,((t*.9+k/5)%1));x.fillStyle='#fff';x.beginPath();x.arc(P[0],P[1],4.5,0,TAU);x.fill()}
if(stg==3)for(let k=0;k<5;k++){const P=portPt(1,1-((t*.9+k/5)%1));x.fillStyle='#8a8a8a';x.beginPath();x.arc(P[0],P[1],4.5,0,TAU);x.fill()}
// kľuka s protizávažím
const ca=th-Math.PI/2;x.save();x.translate(CX,CY);x.rotate(ca);x.beginPath();x.moveTo(r,-22);x.lineTo(-8,-34);x.arc(0,0,78,Math.PI-1.05,Math.PI+1.05);x.lineTo(-8,34);x.lineTo(r,22);x.arc(r,0,22,Math.PI/2,-Math.PI/2,true);x.closePath();x.fillStyle=DARK;x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.restore();
x.beginPath();x.arc(CX,CY,17,0,TAU);x.fillStyle='#8f8f8f';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
// ojnica
const ang=Math.atan2(pinY-wy,pinX-CX),nx=-Math.sin(ang),ny=Math.cos(ang);x.beginPath();x.moveTo(CX+nx*9,wy+ny*9);x.lineTo(pinX+nx*15,pinY+ny*15);x.lineTo(pinX-nx*15,pinY-ny*15);x.lineTo(CX-nx*9,wy-ny*9);x.closePath();x.fillStyle='#9c9c9c';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.arc(pinX,pinY,23,0,TAU);x.fillStyle='#9c9c9c';x.fill();x.stroke();x.beginPath();x.arc(pinX,pinY,12,0,TAU);x.fillStyle=A;x.fill();
// piest s krúžkami
x.fillStyle=METAL;x.fillRect(CX-B+3,crown,2*B-6,PH);x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(CX-B+3,crown,2*B-6,PH);x.fillStyle='#3a3a3a';[11,22,33].forEach(o=>x.fillRect(CX-B+3,crown+o,2*B-6,4));
x.beginPath();x.arc(CX,wy,13,0,TAU);x.fillStyle='#5a5a5a';x.fill();x.strokeStyle='#222';x.lineWidth=2;x.stroke();
// ventily a sviečka
const lin=stg==0?Math.sin(Math.PI*q)*18:0,lex=stg==3?Math.sin(Math.PI*q)*18:0;valve(-1,lin);valve(1,lex);
x.fillStyle='#e8e8e8';x.fillRect(CX-9,TOP-24,18,DECK-TOP+22);x.fillStyle='#8a8a8a';x.fillRect(CX-13,TOP-10,26,12);x.strokeStyle='#e8e8e8';x.lineWidth=3;x.beginPath();x.moveTo(CX,DECK-2);x.lineTo(CX,DECK+7);x.stroke();
const sk=stg==2&&q<.22?1-q/.22:(stg==1&&q>.94?1:0);if(sk>0){x.save();x.translate(CX,DECK+10);x.strokeStyle='#fff';x.lineWidth=3;x.globalAlpha=p*sk;for(let k=0;k<8;k++){const a=k*TAU/8+t*9;x.beginPath();x.moveTo(Math.cos(a)*6,Math.sin(a)*6);x.lineTo(Math.cos(a)*(16+6*(k%2)),Math.sin(a)*(16+6*(k%2)));x.stroke()}x.restore();x.globalAlpha=p}
x.globalAlpha=1;L.forEach((e,i)=>{e.style.opacity=e._on?(i==stg?1:.32)*sp:0;e.style.color=i==stg?A:'#cfcfcf';num[i].style.opacity=e._on?(i==stg?1:.32)*sp:0;num[i].style.color=i==stg?A:'#cfcfcf'})}};

// ---------- rotačný (Wankelov) motor v reze: l = sanie, kompresia, expanzia, výfuk ----------
PRO.wankel=(v,d)=>{const x=cv2(v,864,560),A=D.acc,L=labs(v,d,4),e0=27,R=190,W=G.wankel(R,e0),CX=432,CY=292,mm=4.5,TH=24;
place(L[0],CX+96,46,330,'left');place(L[3],CX-426,46,330,'right');place(L[1],CX+150,506,280,'left');place(L[2],CX-430,506,280,'right');L[2].style.color=A;
const hp=(off)=>{for(let i=0;i<=120;i++){const q=W.house(i/120*TAU,off);i?x.lineTo(CX+q[0],CY+q[1]):x.moveTo(CX+q[0],CY+q[1])}x.closePath()};
// kanály hore: vpravo sanie, vľavo výfuk (rotor sa točí v smere hodinových ručičiek)
const PX=62,PW=34,yIn=(()=>{let b=0;for(let i=0;i<=400;i++){const q=W.house(Math.PI+i/400*Math.PI);if(Math.abs(q[0]-PX)<3)b=q[1]}return CY+b})();
const ports=()=>{[1,-1].forEach(s=>{x.fillStyle='#000';x.fillRect(CX+s*PX-PW/2,74,PW,yIn-74+14);x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(CX+s*PX-PW/2,74);x.lineTo(CX+s*PX-PW/2,yIn-4);x.moveTo(CX+s*PX+PW/2,74);x.lineTo(CX+s*PX+PW/2,yIn-4);x.stroke()})};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));x.clearRect(0,0,864,560);x.globalAlpha=p;const fi=t*.85,c=W.center(fi);
// skriňa v reze
x.beginPath();hp(TH);x.lineWidth=8;x.strokeStyle='#fff';x.stroke();x.fillStyle=WALL;x.fill();hatch(x,()=>hp(TH));
x.beginPath();hp(0);x.lineWidth=8;x.stroke();x.fillStyle='#000';x.fill();ports();
// tri komory: farba podľa toho, čo sa v nich práve deje
for(let k=0;k<3;k++){const psi=(((fi+TAU*k/3+Math.PI/3)%TAU)+TAU)%TAU,sec=Math.floor(psi/(Math.PI/2)),q=psi/(Math.PI/2)-sec;const C=W.chamber(fi,k,26);
x.beginPath();poly(x,C.map(P=>[CX+P[0],CY+P[1]]));if(sec==3){x.fillStyle='rgba(255,255,255,.10)'}else if(sec==0){x.fillStyle=`rgba(255,255,255,${.10+.22*q})`}else if(sec==1){x.fillStyle=A;x.globalAlpha=p*(1-.55*q)}else{x.fillStyle='rgba(150,150,150,.26)'}x.fill();x.globalAlpha=p}
// prúdenie: nasávanie dnu, spaliny von
for(let k=0;k<5;k++){const u=(t*.8+k/5)%1;x.fillStyle='#fff';x.beginPath();x.arc(CX+PX,78+u*(yIn-70),4.5,0,TAU);x.fill();x.fillStyle='#8a8a8a';x.beginPath();x.arc(CX-PX,yIn+8-u*(yIn-70),4.5,0,TAU);x.fill()}
// rotor
x.beginPath();for(let k=0;k<3;k++)W.flank(fi,k,22).forEach((P,i)=>(k||i)?x.lineTo(CX+P[0],CY+P[1]):x.moveTo(CX+P[0],CY+P[1]));x.closePath();x.fillStyle=DARK;x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
// vnútorné ozubenie rotora (36 zubov) sa odvaľuje po pevnom kolese (24 zubov): pomer 3:2
x.save();x.translate(CX+c[0],CY+c[1]);x.rotate(fi);x.beginPath();x.arc(0,0,3*e0+mm*2.4,0,TAU);x.fillStyle='#3a3a3a';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();G.gearPts(36,-.06).forEach((q,i)=>i?x.lineTo(q[0]*mm,q[1]*mm):x.moveTo(q[0]*mm,q[1]*mm));x.closePath();x.fillStyle='#000';x.fill();x.lineWidth=2;x.stroke();x.restore();
GEARPRO(x,CX,CY,2*e0,24,0,'#fff',{fill:'#8f8f8f'});
// výstupný hriadeľ s excentrom (točí sa 3x rýchlejšie ako rotor)
x.strokeStyle=A;x.lineWidth=9;x.beginPath();x.moveTo(CX,CY);x.lineTo(CX+c[0],CY+c[1]);x.stroke();x.fillStyle=A;x.beginPath();x.arc(CX,CY,11,0,TAU);x.fill();x.beginPath();x.arc(CX+c[0],CY+c[1],8,0,TAU);x.fillStyle='#fff';x.fill();
// tesniace lišty vo vrcholoch
for(let k=0;k<3;k++){const a=W.apex(fi,k);x.beginPath();x.arc(CX+a[0]-Math.cos(fi+TAU*k/3)*5,CY+a[1]-Math.sin(fi+TAU*k/3)*5,5,0,TAU);x.fillStyle='#fff';x.fill()}
// sviečka dole + iskra, keď je komora najmenšia
const sy=CY+R-e0;x.fillStyle='#e8e8e8';x.fillRect(CX-8,sy-4,16,TH+26);x.fillStyle='#8a8a8a';x.fillRect(CX-12,sy+TH+2,24,10);
let sk=0;for(let k=0;k<3;k++){const psi=(((fi+TAU*k/3+Math.PI/3)%TAU)+TAU)%TAU,dd=psi-Math.PI/2;if(dd>-.06&&dd<.3)sk=1-Math.max(0,dd)/.3}
if(sk>0){x.save();x.translate(CX,sy-10);x.strokeStyle='#fff';x.lineWidth=3;x.globalAlpha=p*sk;for(let k=0;k<8;k++){const a=k*TAU/8+t*9;x.beginPath();x.moveTo(Math.cos(a)*5,Math.sin(a)*5);x.lineTo(Math.cos(a)*(14+6*(k%2)),Math.sin(a)*(14+6*(k%2)));x.stroke()}x.restore()}
x.globalAlpha=1;L.forEach(e=>e.style.opacity=e._on?sp:0)}};
PRO.rotary=PRO.wankel;

window.MECHPRO=PRO;
const _m3=V.mech;V.mech=(v,d)=>PRO[d&&d.m]?PRO[d.m](v,d):_m3(v,d);
}
