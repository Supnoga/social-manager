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
const zz=1+.07*ez(t/3.5);x.save();x.translate(c1+r1,cy);x.scale(zz,zz);x.translate(-(c1+r1),-cy);
GEARPRO(x,c1,cy,r1,z1,w,'#fff');GEARPRO(x,c2,cy,r2,z2,G.meshRot(w,z1,z2,0),A);
{const gg=x.createRadialGradient(c1+r1,cy,0,c1+r1,cy,m*4.2);gg.addColorStop(0,rgba(A,.55+.2*Math.sin(t*z1*1.1)));gg.addColorStop(1,rgba(A,0));x.fillStyle=gg;x.fillRect(c1+r1-m*5,cy-m*5,m*10,m*10)}
x.globalAlpha=p*sp;arr(c1,r1,1,'#fff');arr(c2,r2,-1,A);x.restore();x.globalAlpha=1;
L.forEach(e=>e.style.opacity=e._on?sp:0);big.style.opacity=E(st(1,.6))}};

// ---------- efekty: prirodzené čiastočky, plameň, dym (všetko je funkcia času, takže video vyjde vždy rovnako) ----------
const HS=(i,k)=>{const s=Math.sin(i*127.1+k*311.7+13.37)*43758.5453;return s-Math.floor(s)};
const hex=c=>{c=String(c||'').replace('#','');if(c.length==3)c=c.split('').map(h=>h+h).join('');const v=[0,2,4].map(i=>parseInt(c.substr(i,2),16));return v.some(isNaN)?[255,107,0]:v};
const rgba=(c,a)=>{const v=hex(c);return `rgba(${v[0]},${v[1]},${v[2]},${a})`};
const mix=(c1,c2,f,a)=>{const A=hex(c1),B=hex(c2);return `rgba(${A.map((v,i)=>Math.round(v+(B[i]-v)*f)).join(',')},${a==null?1:a})`};
const ez=u=>{u=cl(u);return u*u*(3-2*u)};
const lerp=(a,b,f)=>[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f];
// neusporiadaný pohyb čiastočky i (vírenie): amp v px, sp = rýchlosť
const wob=(i,t,amp,sp)=>[(Math.sin(t*sp*(.7+HS(i,1))+HS(i,2)*TAU)+.6*Math.sin(t*sp*(1.9+HS(i,3))+HS(i,4)*TAU))*amp*.62,(Math.cos(t*sp*(.8+HS(i,5))+HS(i,6)*TAU)+.6*Math.sin(t*sp*(2.1+HS(i,7))+HS(i,8)*TAU))*amp*.62];
const dot=(x,P,r,col,a,halo)=>{if(a<=.01)return;const g=x.globalAlpha;if(halo){x.globalAlpha=g*a*.22;x.fillStyle=col;x.beginPath();x.arc(P[0],P[1],r*2.3,0,TAU);x.fill()}x.globalAlpha=g*a;x.fillStyle=col;x.beginPath();x.arc(P[0],P[1],r,0,TAU);x.fill();x.globalAlpha=g};
// plameň: čelo horenia sa šíri od sviečky (q = priebeh expanzie 0..1), clipFn = tvar spaľovacieho priestoru
const flame=(x,clipFn,C,maxR,q,A,p,t)=>{const burn=ez(q/.16),R0=Math.max(2,burn*maxR),al=p*(1-.55*q);x.save();x.beginPath();clipFn();x.clip();
const g=x.createRadialGradient(C[0],C[1],0,C[0],C[1],R0);g.addColorStop(0,'#fff');g.addColorStop(.16,mix(A,'#ffffff',.6));g.addColorStop(.5,A);g.addColorStop(.88,mix(A,'#000000',.4));g.addColorStop(1,burn<1?rgba(A,0):mix(A,'#000000',.55));
x.globalAlpha=al;x.fillStyle=g;x.fillRect(C[0]-maxR-40,C[1]-maxR-40,2*maxR+80,2*maxR+80);
// živé jazyky plameňa
for(let i=0;i<9;i++){const a=HS(i,31)*TAU+t*(1.2+HS(i,32)),rr=R0*(.25+.6*HS(i,33)),P=[C[0]+Math.cos(a)*rr*.9,C[1]+Math.abs(Math.sin(a))*rr],w=wob(i+70,t,10,5),r=18+34*HS(i,34);const gg=x.createRadialGradient(P[0]+w[0],P[1]+w[1],0,P[0]+w[0],P[1]+w[1],r);gg.addColorStop(0,mix(A,'#ffffff',.7,.5));gg.addColorStop(1,mix(A,'#ffffff',.3,0));x.globalAlpha=al*burn;x.fillStyle=gg;x.fillRect(P[0]+w[0]-r,P[1]+w[1]-r,2*r,2*r)}
x.restore()};
const spark=(x,C,k,A,p,t)=>{if(k<=0)return;x.save();x.translate(C[0],C[1]);const g=x.createRadialGradient(0,0,0,0,0,30);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.35,mix(A,'#ffffff',.5,.8));g.addColorStop(1,rgba(A,0));x.globalAlpha=p*k;x.fillStyle=g;x.fillRect(-30,-30,60,60);x.strokeStyle='#fff';x.lineWidth=2.5;for(let i=0;i<7;i++){const a=i*TAU/7+t*11,r1=5,r2=13+9*HS(i,Math.floor(t*30));x.beginPath();x.moveTo(Math.cos(a)*r1,Math.sin(a)*r1);x.lineTo(Math.cos(a)*r2,Math.sin(a)*r2);x.stroke()}x.restore()};
const metal=(x,x0,x1)=>{const g=x.createLinearGradient(x0,0,x1,0);g.addColorStop(0,'#8e8e8e');g.addColorStop(.3,'#f2f2f2');g.addColorStop(.62,'#c4c4c4');g.addColorStop(1,'#7c7c7c');return g};

// ---------- štvortaktný motor v reze: l = názvy 4 dôb ----------
PRO.piston=(v,d)=>{const x=cv2(v,864,560),A=D.acc,L=labs(v,d,4),any=L.some(e=>e._on);
const CX=any?290:432,B=92,TOP=36,DECK=96,r=56,l=176,PH=84,PIN=46,CL=12,CY=DECK+CL+PIN+r+l,Ri=104,LB=306,T=Math.max(4.8,Math.min(7.2,(N(d._dur)||7)-.6)),NP=48;
L.forEach((e,i)=>place(e,CX+250,138+i*74,864-(CX+250)-6,'left'));
const FOC=[[CX-46,92,1.22],[CX,150,1.1],[CX,132,1.24],[CX+46,92,1.22]],FSEL={intake:0,compression:1,power:2,exhaust:3}[String(d.f||'')];x.canvas.style.webkitMaskImage='linear-gradient(#000 0,#000 92%,transparent 100%)';
const num=L.map((e,i)=>{const n=el('div','big',`left:${CX+196}px;top:${130+i*74}px;width:44px;text-align:center;font-size:34px;opacity:0`,String(i+1));v.append(n);return n});
const PT=[...Array(NP)].map((_,i)=>({gx:((i%8)+.12+.76*HS(i,11))/8,gy:(Math.floor(i/8)+.12+.76*HS(i,12))/6,fuel:HS(i,13)<.27,ein:.04+.7*HS(i,14),eex:.04+.7*HS(i,16),sd:HS(i,15)<.5?-1:1,lat:(HS(i,17)-.5)*22,rr:.8+.5*HS(i,18)}));
const outer=()=>{x.rect(CX-B-24,TOP,2*B+48,LB-TOP+40);x.moveTo(CX+Ri+16,CY);x.arc(CX,CY,Ri+16,0,TAU)};
const cavity=()=>{x.rect(CX-B,DECK,2*B,CY-DECK);x.moveTo(CX+Ri,CY);x.arc(CX,CY,Ri,0,TAU)};
const port=s=>{x.beginPath();x.moveTo(CX+s*(B+118),62);x.lineTo(CX+s*96,62);x.quadraticCurveTo(CX+s*46,62,CX+s*46,DECK+1)};
// stred kanála (u: 0 = vonku, 1 = pri ventile) + posun do strany, aby čiastočky nešli v jednej línii
const portPt=(s,u,lat)=>{u=cl(u);let P;if(u<.62){P=[CX+s*(B+118)+(s*96-s*(B+118))*(u/.62),62]}else{const q=(u-.62)/.38,a=1-q;P=[CX+a*a*s*96+2*a*q*s*46+q*q*s*46,a*a*62+2*a*q*62+q*q*(DECK+8)]}const b=ez((u-.6)/.36);return [P[0]+lat*b*.8,P[1]+lat*(1-b)*.62]};
const INJ=[CX-112,46];
const valve=(s,lift)=>{const vx=CX+s*46,y=DECK+lift;x.strokeStyle='#e8e8e8';x.lineWidth=6;x.beginPath();x.moveTo(vx,y);x.lineTo(vx,TOP-30+lift);x.stroke();
x.beginPath();x.moveTo(vx-27,y+3);x.lineTo(vx+27,y+3);x.lineTo(vx+15,y-9);x.lineTo(vx-15,y-9);x.closePath();x.fillStyle=metal(x,vx-27,vx+27);x.fill();x.strokeStyle='#000';x.lineWidth=1.5;x.stroke();
x.strokeStyle='#bdbdbd';x.lineWidth=2.5;x.beginPath();const y0=TOP-26+lift,y1=TOP-3,n=5;for(let i=0;i<=n;i++){const yy=y0+(y1-y0)*i/n;x.lineTo(vx+(i%2?10:-10),yy)}x.stroke();
x.fillStyle='#e8e8e8';x.fillRect(vx-13,TOP-32+lift,26,5)};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));x.clearRect(0,0,864,560);x.globalAlpha=p;const cyc=((t/T)%1+1)%1,th=cyc*2*TAU,stg=Math.min(3,Math.floor(cyc*4)),q=cyc*4-stg;
// kamera: plynulo sa presúva na miesto, kde sa práve niečo deje, pri zážihu sa zatrasie
let cf;if(FSEL!=null)cf=[FOC[FSEL][0],FOC[FSEL][1],1.4];else{const a=FOC[(stg+3)%4],b=FOC[stg],f=ez(q/.4);cf=[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f]}
const zz=1+(cf[2]-1)*ez((t-.6)/1.4),shk=stg==2&&q<.16?1-q/.16:0;x.save();x.translate(cf[0]+Math.sin(t*93)*5*shk,cf[1]+Math.cos(t*71)*4*shk);x.scale(zz,zz);x.translate(-cf[0],-cf[1]);
const K=G.crank(th,r,l),wy=CY-r-l+K.drop,crown=wy-PIN,pinX=CX+K.px,pinY=CY+K.py,top=DECK+2,hgt=Math.max(0,crown-top);
const home=(o,i,amp,spd)=>{const w=wob(i,t,amp,spd);return [Math.max(CX-B+8,Math.min(CX+B-8,CX+(o.gx-.5)*2*(B-14)+w[0])),Math.max(top+5,Math.min(crown-5,top+7+o.gy*Math.max(2,hgt-14)+w[1]*Math.min(1,hgt/70)))]};
const chamber=()=>x.rect(CX-B+2,top,2*B-4,hgt);
// blok a hlava v reze
x.lineWidth=8;x.strokeStyle='#fff';x.beginPath();outer();x.stroke();x.fillStyle=WALL;x.beginPath();outer();x.fill();hatch(x,outer);
x.beginPath();cavity();x.lineWidth=8;x.stroke();x.fillStyle='#000';x.beginPath();cavity();x.fill();
// olej v kľukovej skrini
x.save();x.beginPath();x.arc(CX,CY,Ri-4,0,TAU);x.clip();x.beginPath();x.moveTo(CX-Ri,CY+Ri);for(let i=0;i<=24;i++){const xx=CX-Ri+2*Ri*i/24;x.lineTo(xx,CY+Ri*.74+Math.sin(i*.9+t*2.2)*2.2+Math.sin(i*.37-t*1.3)*1.6)}x.lineTo(CX+Ri,CY+Ri);x.closePath();x.fillStyle='#2f2a24';x.fill();x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;x.stroke();x.restore();
// sací a výfukový kanál, vstrekovač
[-1,1].forEach(s=>{x.lineCap='butt';port(s);x.strokeStyle='#fff';x.lineWidth=40;x.stroke();port(s);x.strokeStyle='#000';x.lineWidth=32;x.stroke();x.lineCap='round'});
x.save();x.translate(INJ[0],INJ[1]);x.rotate(.62);x.fillStyle='#d8d8d8';x.fillRect(-7,-40,14,34);x.fillStyle='#8a8a8a';x.fillRect(-10,-46,20,8);x.fillStyle=A;x.fillRect(-3.5,-7,7,9);x.restore();
// plyn vo valci
if(hgt>1){x.beginPath();chamber();x.fillStyle=stg==1?`rgba(255,255,255,${.05+.11*q})`:stg==3?`rgba(150,150,150,${.2*(1-.5*q)})`:'rgba(255,255,255,.05)';x.fill()}
const PLUG=[CX,DECK+9],maxR=Math.hypot(B,hgt)+12;
if(stg==2)flame(x,chamber,PLUG,maxR,q,A,p,t);
if(stg==3&&q<.18){x.save();x.globalAlpha=p*.45*(1-q/.18);x.beginPath();chamber();x.fillStyle=mix(A,'#000000',.35);x.fill();x.restore();x.globalAlpha=p}
// čiastočky: vzduch (biele) a palivo (farebné) vírivo vtekajú, stláčajú sa, zhoria, dym odchádza
PT.forEach((o,i)=>{const cA=o.fuel?A:'#fff',rA=(o.fuel?3.5:2.7)*o.rr;
// v sacom kanáli (už počas konca výfuku sa blížia k ventilu)
const qi=stg==0?q:stg==3?q-1:null;if(qi!=null){const uu=(qi-(o.ein-.3))/.3;if(uu>0&&uu<1){const w=wob(i+200,t,3,4);let P=portPt(-1,uu,o.lat);P=[P[0]+w[0],P[1]+w[1]];if(o.fuel){if(uu<.42)return;P=lerp(INJ,P,ez((uu-.42)/.2))}dot(x,P,rA,cA,Math.min(1,uu*5),o.fuel)}}
if(stg==0&&q>=o.ein){const f=ez((q-o.ein)/.26),gap=[CX-46+o.sd*25,DECK+9+7*Math.sin(Math.PI*q)];dot(x,lerp(gap,home(o,i,7,2.4),f),rA,cA,1,o.fuel)}
if(stg==1)dot(x,home(o,i,5+3*q,2.6+4*q),rA,cA,1,o.fuel);
if(stg==2&&q<.16){const P=home(o,i,8,6.5);if(Math.hypot(P[0]-PLUG[0],P[1]-PLUG[1])>ez(q/.16)*maxR)dot(x,P,rA,cA,1,o.fuel)}
if(stg==2&&i<18){const P=home(o,i,13,9);dot(x,P,1.6+1.4*HS(i,40),'#fff',(1-q)*(.5+.5*Math.sin(t*23+i)),false)}
// dym: najprv vo valci, potom cez ventil von (dobieha ešte na začiatku sania)
const qx=stg==3?q:stg==0?q+1:null;if(qx!=null){const rS=(4.2+2.6*HS(i,19));if(qx<o.eex){if(stg==3)dot(x,home(o,i,6,2.2),rS,'#a0a0a0',.5*Math.min(1,q/.1),true)}
else if(qx<o.eex+.2){if(stg==3)dot(x,lerp(home(o,i,6,2.2),[CX+46+o.sd*25,DECK+9],ez((qx-o.eex)/.2)),rS,'#a0a0a0',.5,true)}
else{const uu=(qx-o.eex-.2)/.34;if(uu<1){const w=wob(i+300,t,4,3),P=portPt(1,1-uu,o.lat);dot(x,[P[0]+w[0],P[1]+w[1]],rS*(1+1.3*uu),'#a0a0a0',.5*(1-uu),true)}}}});
// rozprašovanie paliva zo vstrekovača
if(stg==0&&q>.06&&q<.74)for(let k=0;k<12;k++){const u=((t*2.3+HS(k,50))%1),a=.95+(HS(k,51)-.5)*.75,dd=6+u*46;dot(x,[INJ[0]+Math.cos(a)*dd,INJ[1]+Math.sin(a)*dd*.55+2],1.7,A,(1-u)*.9,false)}
// kľuka s protizávažím
const ca=th-Math.PI/2;x.save();x.translate(CX,CY);x.rotate(ca);x.beginPath();x.moveTo(r,-22);x.lineTo(-8,-34);x.arc(0,0,78,Math.PI-1.05,Math.PI+1.05);x.lineTo(-8,34);x.lineTo(r,22);x.arc(r,0,22,Math.PI/2,-Math.PI/2,true);x.closePath();const cg=x.createRadialGradient(0,0,6,0,0,80);cg.addColorStop(0,'#4a4a4a');cg.addColorStop(1,'#262626');x.fillStyle=cg;x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.restore();
x.beginPath();x.arc(CX,CY,17,0,TAU);x.fillStyle='#8f8f8f';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
// ojnica
const ang=Math.atan2(pinY-wy,pinX-CX),nx=-Math.sin(ang),ny=Math.cos(ang);x.beginPath();x.moveTo(CX+nx*9,wy+ny*9);x.lineTo(pinX+nx*15,pinY+ny*15);x.lineTo(pinX-nx*15,pinY-ny*15);x.lineTo(CX-nx*9,wy-ny*9);x.closePath();x.fillStyle='#a2a2a2';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.arc(pinX,pinY,23,0,TAU);x.fillStyle='#a2a2a2';x.fill();x.stroke();dot(x,[pinX,pinY],12,A,1,true);
// piest s krúžkami
x.fillStyle=metal(x,CX-B,CX+B);x.fillRect(CX-B+3,crown,2*B-6,PH);x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(CX-B+3,crown,2*B-6,PH);x.fillStyle='#333';[11,22,33].forEach(o=>x.fillRect(CX-B+3,crown+o,2*B-6,4));
x.beginPath();x.arc(CX,wy,13,0,TAU);x.fillStyle='#5a5a5a';x.fill();x.strokeStyle='#222';x.lineWidth=2;x.stroke();
// ventily a sviečka
const lin=stg==0?Math.sin(Math.PI*q)*18:0,lex=stg==3?Math.sin(Math.PI*q)*18:0;valve(-1,lin);valve(1,lex);
x.fillStyle='#e8e8e8';x.fillRect(CX-9,TOP-24,18,DECK-TOP+22);x.fillStyle='#8a8a8a';x.fillRect(CX-13,TOP-10,26,12);x.strokeStyle='#e8e8e8';x.lineWidth=3;x.beginPath();x.moveTo(CX,DECK-2);x.lineTo(CX,DECK+7);x.stroke();
spark(x,PLUG,stg==2&&q<.2?1-q/.2:(stg==1&&q>.95?(q-.95)/.05:0),A,p,t);
x.restore();x.globalAlpha=1;L.forEach((e,i)=>{e.style.opacity=e._on?(i==stg?1:.32)*sp:0;e.style.color=i==stg?A:'#cfcfcf';num[i].style.opacity=e._on?(i==stg?1:.32)*sp:0;num[i].style.color=i==stg?A:'#cfcfcf'})}};

// ---------- rotačný (Wankelov) motor v reze: l = sanie, kompresia, expanzia, výfuk ----------
PRO.wankel=(v,d)=>{const x=cv2(v,864,560),A=D.acc,L=labs(v,d,4),e0=27,R=190,W=G.wankel(R,e0),CX=432,CY=292,mm=4.5,TH=24,NC=30;
place(L[0],CX+96,46,330,'left');place(L[3],CX-426,46,330,'right');place(L[1],CX+150,506,280,'left');place(L[2],CX-430,506,280,'right');L[2].style.color=A;
const hp=(off)=>{for(let i=0;i<=120;i++){const q=W.house(i/120*TAU,off);i?x.lineTo(CX+q[0],CY+q[1]):x.moveTo(CX+q[0],CY+q[1])}x.closePath()};
// kanály hore: vpravo sanie, vľavo výfuk (rotor sa točí v smere hodinových ručičiek)
const PX=62,PW=34,yIn=(()=>{let b=0;for(let i=0;i<=400;i++){const q=W.house(Math.PI+i/400*Math.PI);if(Math.abs(q[0]-PX)<3)b=q[1]}return CY+b})();
const ports=()=>{[1,-1].forEach(s=>{x.fillStyle='#000';x.fillRect(CX+s*PX-PW/2,74,PW,yIn-74+14);x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(CX+s*PX-PW/2,74);x.lineTo(CX+s*PX-PW/2,yIn-4);x.moveTo(CX+s*PX+PW/2,74);x.lineTo(CX+s*PX+PW/2,yIn-4);x.stroke()})};
const CP=[...Array(NC)].map((_,i)=>({s:.07+.86*((i%10)+.15+.7*HS(i,61))/10,dp:.14+.72*(Math.floor(i/10)+.15+.7*HS(i,62))/3,fuel:HS(i,63)<.27,ein:.04+.68*HS(i,64),eex:.12+.58*HS(i,65),rr:.8+.5*HS(i,66)}));
const sy=CY+R-e0,MIN=[CX+PX,yIn+8],MEX=[CX-PX,yIn+8],SPK=[CX,sy-10];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));x.clearRect(0,0,864,560);x.globalAlpha=p;const fi=t*.72,c=W.center(fi);
let sk=0;for(let k=0;k<3;k++){const psi=(((fi+TAU*k/3+Math.PI/3)%TAU)+TAU)%TAU,dd=psi-Math.PI/2;if(dd>-.05&&dd<.3)sk=Math.max(sk,dd<0?1+dd/.05:1-dd/.3)}
const zz=1+.09*ez(t/3.5);x.save();x.translate(CX+Math.sin(t*93)*4*sk,CY+Math.cos(t*71)*3*sk);x.scale(zz,zz);x.translate(-CX,-CY);
// skriňa v reze
x.beginPath();hp(TH);x.lineWidth=8;x.strokeStyle='#fff';x.stroke();x.fillStyle=WALL;x.fill();hatch(x,()=>hp(TH));
x.beginPath();hp(0);x.lineWidth=8;x.stroke();x.fillStyle='#000';x.fill();ports();
// prúdenie v kanáloch: vzduch s palivom dnu, dym von
for(let k=0;k<16;k++){const u=(t*.5*(.7+.6*HS(k,71))+HS(k,72))%1,w=wob(k+400,t,3,3.5),fu=HS(k,73)<.3;dot(x,[CX+PX+(HS(k,74)-.5)*20+w[0],76+u*(yIn-70)],(fu?3.3:2.6),fu?A:'#fff',Math.min(1,u*6),fu);
const u2=(t*.42*(.7+.6*HS(k,75))+HS(k,76))%1,w2=wob(k+500,t,4,3);dot(x,[CX-PX+(HS(k,77)-.5)*16+w2[0],yIn+6-u2*(yIn-66)],4.5*(1+1.1*u2),'#a0a0a0',.5*(1-u2)*Math.min(1,u2*6),true)}
// tri komory: v každej sa deje iná doba
for(let k=0;k<3;k++){const psi=(((fi+TAU*k/3+Math.PI/3)%TAU)+TAU)%TAU,sec=Math.floor(psi/(Math.PI/2))%4,q=psi/(Math.PI/2)-sec;const C=W.chamber(fi,k,26).map(P=>[CX+P[0],CY+P[1]]),clipC=()=>poly(x,C);
const a0=fi+TAU*k/3,F=W.flank(fi,k,40);
const cpt=(o,i,amp,spd)=>{const h=W.house(a0+o.s*TAU/3),f=F[Math.round(o.s*40)],w=wob(i+k*40,t,amp,spd);return [CX+h[0]+(f[0]-h[0])*o.dp+w[0]*.6,CY+h[1]+(f[1]-h[1])*o.dp+w[1]*.6]};
x.beginPath();clipC();x.fillStyle=sec==3?'rgba(255,255,255,.06)':sec==0?`rgba(255,255,255,${.06+.12*q})`:sec==2?`rgba(150,150,150,${.2*(1-.5*q)})`:'rgba(0,0,0,0)';x.fill();
if(sec==1)flame(x,clipC,SPK,330,q,A,p,t+k);
if(sec==2&&q<.18){x.save();x.globalAlpha=p*.45*(1-q/.18);x.beginPath();clipC();x.fillStyle=mix(A,'#000000',.35);x.fill();x.restore();x.globalAlpha=p}
x.save();x.beginPath();clipC();x.clip();
CP.forEach((o,i)=>{const cA=o.fuel?A:'#fff',rA=(o.fuel?3.4:2.6)*o.rr;
if(sec==3){if(q>=o.ein)dot(x,lerp(MIN,cpt(o,i,6,2.4),ez((q-o.ein)/.26)),rA,cA,1,o.fuel)}
else if(sec==0)dot(x,cpt(o,i,5+3*q,2.6+4*q),rA,cA,1,o.fuel);
else if(sec==1){if(q<.16){const P=cpt(o,i,8,6.5);if(Math.hypot(P[0]-SPK[0],P[1]-SPK[1])>ez(q/.16)*330)dot(x,P,rA,cA,1,o.fuel)}if(i<14)dot(x,cpt(o,i,12,9),1.5+1.4*HS(i,40),'#fff',(1-q)*(.5+.5*Math.sin(t*23+i)),false)}
else{const rS=4+2.4*HS(i,19);if(q<o.eex)dot(x,cpt(o,i,6,2.2),rS,'#a0a0a0',.5*Math.min(1,q/.1),true);else{const f=ez((q-o.eex)/.26);if(f<1)dot(x,lerp(cpt(o,i,6,2.2),MEX,f),rS,'#a0a0a0',.5*(1-f*f),true)}}});
x.restore()}
// rotor
x.beginPath();for(let k=0;k<3;k++)W.flank(fi,k,22).forEach((P,i)=>(k||i)?x.lineTo(CX+P[0],CY+P[1]):x.moveTo(CX+P[0],CY+P[1]));x.closePath();const rg=x.createRadialGradient(CX+c[0],CY+c[1],40,CX+c[0],CY+c[1],R);rg.addColorStop(0,'#3d3d3d');rg.addColorStop(1,'#232323');x.fillStyle=rg;x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
// vnútorné ozubenie rotora (36 zubov) sa odvaľuje po pevnom kolese (24 zubov): pomer 3:2
x.save();x.translate(CX+c[0],CY+c[1]);x.rotate(fi);x.beginPath();x.arc(0,0,3*e0+mm*2.4,0,TAU);x.fillStyle='#4a4a4a';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();G.gearPts(36,-.06).forEach((q,i)=>i?x.lineTo(q[0]*mm,q[1]*mm):x.moveTo(q[0]*mm,q[1]*mm));x.closePath();x.fillStyle='#000';x.fill();x.lineWidth=2;x.stroke();x.restore();
GEARPRO(x,CX,CY,2*e0,24,0,'#fff',{fill:'#8f8f8f'});
// výstupný hriadeľ s excentrom (točí sa 3x rýchlejšie ako rotor)
x.strokeStyle=A;x.lineWidth=9;x.beginPath();x.moveTo(CX,CY);x.lineTo(CX+c[0],CY+c[1]);x.stroke();dot(x,[CX,CY],11,A,1,true);dot(x,[CX+c[0],CY+c[1]],8,'#fff',1,false);
// tesniace lišty vo vrcholoch
for(let k=0;k<3;k++){const a=W.apex(fi,k);dot(x,[CX+a[0]-Math.cos(fi+TAU*k/3)*5,CY+a[1]-Math.sin(fi+TAU*k/3)*5],5,'#fff',1,false)}
// sviečka dole + iskra, keď je komora najmenšia
x.fillStyle='#e8e8e8';x.fillRect(CX-8,sy-4,16,TH+26);x.fillStyle='#8a8a8a';x.fillRect(CX-12,sy+TH+2,24,10);
spark(x,SPK,sk,A,p,t);x.restore();
x.globalAlpha=1;L.forEach(e=>e.style.opacity=e._on?sp:0)}};
PRO.rotary=PRO.wankel;

// ---------- réžia: úvodný záber „kde to v aute je“ a zoom dnu ----------
// auto z boku (miestne súradnice: zem y=0, dĺžka 520), priehľadné, s pohonom; hot = diel, ktorý svieti
const CARHOT={engine:[430,-78],gearbox:[370,-70],diff:[105,-44],brake:[410,-44]};
const CAR=(x,roll,hot,A,pulse)=>{const dim='rgba(255,255,255,.34)';x.lineJoin='round';
// karoséria
x.beginPath();x.moveTo(18,-34);x.bezierCurveTo(10,-60,14,-84,30,-96);x.lineTo(78,-112);x.bezierCurveTo(110,-150,150,-170,196,-172);x.lineTo(286,-172);x.bezierCurveTo(320,-170,350,-140,372,-116);x.bezierCurveTo(420,-110,470,-104,498,-88);x.bezierCurveTo(512,-78,514,-52,508,-34);
x.lineTo(460,-30);x.arc(410,-44,52,.273,Math.PI-.273,true);x.lineTo(155,-30);x.arc(105,-44,52,.273,Math.PI-.273,true);x.closePath();x.fillStyle='rgba(255,255,255,.045)';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.moveTo(122,-118);x.bezierCurveTo(140,-146,160,-160,198,-162);x.lineTo(284,-162);x.bezierCurveTo(310,-160,334,-140,352,-118);x.closePath();x.moveTo(240,-162);x.lineTo(240,-118);x.strokeStyle=dim;x.lineWidth=2.2;x.stroke();
x.beginPath();x.moveTo(240,-118);x.lineTo(240,-40);x.moveTo(130,-112);x.lineTo(126,-60);x.moveTo(352,-118);x.lineTo(356,-60);x.stroke();
x.fillStyle='#fff';x.fillRect(494,-84,12,7);x.fillStyle=A;x.fillRect(16,-88,7,12);
// pohon: motor, prevodovka, hriadeľ, rozvodovka
const part=(k,fn)=>{const on=hot==k;x.beginPath();fn();x.fillStyle=on?A:'rgba(255,255,255,.06)';x.strokeStyle=on?'#fff':dim;x.lineWidth=on?2.6:2;if(on){x.save();x.shadowColor=A;x.shadowBlur=18+10*pulse;x.fill();x.restore()}else x.fill();x.stroke()};
x.strokeStyle=dim;x.lineWidth=4;x.beginPath();x.moveTo(350,-70);x.lineTo(122,-46);x.stroke();
part('engine',()=>{x.rect(392,-106,76,56);x.rect(402,-118,56,12)});part('gearbox',()=>{x.moveTo(392,-98);x.lineTo(350,-86);x.lineTo(350,-56);x.lineTo(392,-52);x.closePath()});
// kolesá
[105,410].forEach(cx=>{x.beginPath();x.arc(cx,-44,44,0,TAU);x.fillStyle='#0a0a0a';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.beginPath();x.arc(cx,-44,27,0,TAU);x.strokeStyle=dim;x.lineWidth=2.2;x.stroke();
for(let k=0;k<5;k++){const a=roll+k*TAU/5;x.beginPath();x.moveTo(cx+Math.cos(a)*7,-44+Math.sin(a)*7);x.lineTo(cx+Math.cos(a)*27,-44+Math.sin(a)*27);x.stroke()}});
part('diff',()=>{x.arc(105,-44,15,0,TAU)});part('brake',()=>{x.arc(410,-44,22,0,TAU)});
if(hot&&CARHOT[hot]){const h=CARHOT[hot];x.beginPath();x.arc(h[0],h[1],58+16*pulse,0,TAU);x.strokeStyle=rgba(A,.75*(1-pulse));x.lineWidth=3;x.stroke()}};
const CTX={piston:['car','engine'],wankel:['car','engine'],rotary:['car','engine'],camshaft:['car','engine'],gearbox:['car','gearbox'],differential:['car','diff'],car_brake:['car','brake']};
// obalí model: auto príde, diel sa rozsvieti, kamera doň vletí a prelne sa do rezu
const withIntro=(v,d,ctx,base)=>{const vm=el('div','','position:absolute;left:0;top:0;width:864px;height:560px;transform-origin:50% 50%;opacity:0');v.append(vm);const upd=base(vm,d);
const x=cv2(v,864,560);x.canvas.style.webkitMaskImage='radial-gradient(ellipse 52% 54% at 50% 50%,#000 72%,transparent 100%)';const A=D.acc,IN=Math.max(1.7,Math.min(2.8,(N(d._dur)||8)*.3)),S=1.4,OX=68,OY=420,h=CARHOT[ctx[1]],H=[OX+h[0]*S,OY+h[1]*S];
return (t,st)=>{x.clearRect(0,0,864,560);const u=t/IN;if(u<1.02){const drive=1-ez(u/.42),dx=-drive*drive*620,zo=ez((u-.6)/.4),z=1+zo*zo*8.5,P=lerp(H,[432,280],ez((u-.6)/.34));
x.save();x.globalAlpha=E(u/.12)*(1-ez((u-.74)/.2));x.translate(P[0],P[1]);x.scale(z,z);x.translate(-H[0],-H[1]);
x.strokeStyle='rgba(255,255,255,.22)';x.lineWidth=2;x.beginPath();x.moveTo(-200,OY);x.lineTo(1064,OY);x.stroke();
x.translate(OX+dx,OY);x.scale(S,S);CAR(x,dx/(44*S),u>.36?ctx[1]:null,A,((t*1.5)%1));x.restore()}
const ma=ez((u-.76)/.24);vm.style.opacity=ma;vm.style.transform=`scale(${(.3+.7*ez((u-.68)/.32)).toFixed(4)})`;if(ma>0)upd(Math.max(0,t-IN*.78),st)}};
window.MECHPRO=PRO;
const _m3=V.mech;V.mech=(v,d)=>{const base=PRO[d&&d.m]?PRO[d.m]:_m3,c=d&&d._in&&CTX[d.m];return c?withIntro(v,d,c,base):base(v,d)};
}
