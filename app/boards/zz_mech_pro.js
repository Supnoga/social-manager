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
const mix=(c1,c2,f,a)=>{const A=hex(c1),B=hex(c2);return `rgba(${A.map((v,i)=>Math.round(v+(B[i]-v)*cl(f))).join(',')},${a==null?1:a})`};
const ez=u=>{u=cl(u);return u*u*(3-2*u)};
const lerp=(a,b,f)=>a.map((v,i)=>v+(b[i]-v)*f);
// skutočné farby médií: studený vzduch modrý, palivo jantárové, oheň, spaliny sivé, chladiaca voda
const AIR='#7cc8ff',FUEL='#ffc247',SMOKE='#9ba1a8',FIRE='#ff8a1e',WATER='#4aa8e8';
const wob=(i,t,amp,sp)=>[(Math.sin(t*sp*(.7+HS(i,1))+HS(i,2)*TAU)+.6*Math.sin(t*sp*(1.9+HS(i,3))+HS(i,4)*TAU))*amp*.62,(Math.cos(t*sp*(.8+HS(i,5))+HS(i,6)*TAU)+.6*Math.sin(t*sp*(2.1+HS(i,7))+HS(i,8)*TAU))*amp*.62];
const dot=(x,P,r,col,a,halo)=>{if(a<=.01)return;const g=x.globalAlpha;if(halo){x.globalAlpha=g*a*.22;x.fillStyle=col;x.beginPath();x.arc(P[0],P[1],r*2.3,0,TAU);x.fill()}x.globalAlpha=g*a;x.fillStyle=col;x.beginPath();x.arc(P[0],P[1],r,0,TAU);x.fill();x.globalAlpha=g};
// plameň: čelo horenia sa šíri od sviečky (q = priebeh expanzie 0..1), clipFn = tvar spaľovacieho priestoru
const flame=(x,clipFn,C,maxR,q,A,p,t)=>{const burn=ez(q/.16),R0=Math.max(2,burn*maxR),al=p*(1-.5*q);x.save();x.beginPath();clipFn();x.clip();
const g=x.createRadialGradient(C[0],C[1],0,C[0],C[1],R0);g.addColorStop(0,'#fff');g.addColorStop(.14,'#fff1bf');g.addColorStop(.42,'#ffb347');g.addColorStop(.72,FIRE);g.addColorStop(.92,'#b5360b');g.addColorStop(1,burn<1?'rgba(181,54,11,0)':'#8a2a0a');
x.globalAlpha=al;x.fillStyle=g;x.fillRect(C[0]-maxR-40,C[1]-maxR-40,2*maxR+80,2*maxR+80);
for(let i=0;i<10;i++){const a=HS(i,31)*TAU+t*(1.2+HS(i,32)),rr=R0*(.2+.62*HS(i,33)),P=[C[0]+Math.cos(a)*rr*.9,C[1]+Math.abs(Math.sin(a))*rr],w=wob(i+70,t,10,5),r=18+36*HS(i,34);const gg=x.createRadialGradient(P[0]+w[0],P[1]+w[1],0,P[0]+w[0],P[1]+w[1],r);gg.addColorStop(0,'rgba(255,236,170,.55)');gg.addColorStop(1,'rgba(255,170,60,0)');x.globalAlpha=al*burn;x.fillStyle=gg;x.fillRect(P[0]+w[0]-r,P[1]+w[1]-r,2*r,2*r)}
// tlaková vlna pri zážihu
if(q<.14){const rw=maxR*ez(q/.14);x.globalAlpha=p*(1-q/.14)*.9;x.strokeStyle='#fff';x.lineWidth=5;x.beginPath();x.arc(C[0],C[1],rw,0,TAU);x.stroke()}
x.restore()};
const spark=(x,C,k,A,p,t)=>{if(k<=0)return;x.save();x.translate(C[0],C[1]);const g=x.createRadialGradient(0,0,0,0,0,34);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.35,'rgba(160,210,255,.8)');g.addColorStop(1,'rgba(120,180,255,0)');x.globalAlpha=p*k;x.fillStyle=g;x.fillRect(-34,-34,68,68);x.strokeStyle='#fff';x.lineWidth=2.5;for(let i=0;i<7;i++){const a=i*TAU/7+t*11,r1=5,r2=13+9*HS(i,Math.floor(t*30));x.beginPath();x.moveTo(Math.cos(a)*r1,Math.sin(a)*r1);x.lineTo(Math.cos(a)*r2,Math.sin(a)*r2);x.stroke()}x.restore()};
const metal=(x,x0,x1)=>{const g=x.createLinearGradient(x0,0,x1,0);g.addColorStop(0,'#868b91');g.addColorStop(.3,'#f4f6f8');g.addColorStop(.62,'#c3c8cd');g.addColorStop(1,'#757a80');return g};

// ---------- veľké plátno a kamera ----------
// plátno presahuje bežnú plochu schémy, aby model vyplnil obrazovku; okraje sa strácajú do pozadia
// Na výšku je plátno vyššie než plocha modelu (PT hore, PB dole): stroj presahuje pod nadpis aj pod titulky a tam sa stráca do pozadia,
// takže zaberá celú obrazovku a text pláva nad ním. Súradnice modelu a čísla pri ňom (S.w × S.h) ostávajú rovnaké.
const STG=v=>{const w=WIDE?900:980,h=WIDE?640:820,PT=WIDE?0:260,PB=WIDE?0:330,HH=PT+h+PB,R=2,c=el('canvas','',`position:absolute;left:${(864-w)/2}px;top:${(560-h)/2-PT}px;width:${w}px;height:${HH}px`);c.width=w*R;c.height=HH*R;v.append(c);const x=c.getContext('2d',{willReadFrequently:true});x.scale(R,R);x.lineCap='round';x.lineJoin='round';
// každá snímka začína z čistého stavu: plátno sa na niektorých počítačoch (grafická karta) samo vynuluje a kresba by ostala malá v rohu
const begin=()=>{x.setTransform(R,0,0,R,0,PT*R);x.globalAlpha=1;x.globalCompositeOperation='source-over';x.shadowBlur=0;x.shadowColor='rgba(0,0,0,0)';x.setLineDash([]);x.lineCap='round';x.lineJoin='round';x.clearRect(0,-PT,w,HH)};
const pc=y=>(y/HH*100).toFixed(1)+'%',VM=WIDE?'transparent 0,#000 6%,#000 94%,transparent 100%':`transparent 0,rgba(0,0,0,.06) ${pc(PT*.55)},rgba(0,0,0,.16) ${pc(PT+30)},#000 ${pc(PT+110)},#000 ${pc(PT+h-70)},rgba(0,0,0,.14) ${pc(PT+h+14)},rgba(0,0,0,.05) ${pc(PT+h+120)},transparent 100%`;
c.style.cssText+=`;-webkit-mask-image:linear-gradient(${VM}),linear-gradient(90deg,transparent 0,#000 7%,#000 93%,transparent 100%);-webkit-mask-composite:source-in;mask-composite:intersect`;const FT=(getComputedStyle(document.documentElement).getPropertyValue('--f')||'').trim()||'Helvetica Neue,Arial,sans-serif';return {x,w,h,FT,begin}};
// kamera po kľúčových záberoch [čas, [cx,cy,zoom]]: plynulý prelet (tr sekúnd) na každý ďalší záber
const camAt=(KF,t,tr)=>{let c=KF[0][1];for(let i=1;i<KF.length;i++){if(t<KF[i][0])break;c=lerp(c,KF[i][1],ez((t-KF[i][0])/(KF[i][2]||tr||.7)))}return c};
// veľký názov práve prebiehajúcej doby (číslo + text) s bodkami priebehu
const stamp=(S,idx,name,n,k,A)=>{const x=S.x,X=34,Y=S.h-118;x.save();x.globalAlpha=ez(k/.28);x.translate(0,(1-ez(k/.28))*18);
x.font=`900 92px ${S.FT}`;x.textBaseline='alphabetic';const wn=x.measureText(String(idx+1)).width;let fs=46;x.font=`800 ${fs}px ${S.FT}`;let wt=name?x.measureText(name).width:0;const maxW=S.w*.5;if(wt>maxW){fs=Math.max(24,fs*maxW/wt);x.font=`800 ${fs}px ${S.FT}`;wt=x.measureText(name).width}
const W=wn+(name?wt+22:0)+44;x.fillStyle='rgba(0,0,0,.62)';x.beginPath();x.roundRect(X-14,Y-78,W,112,18);x.fill();
x.font=`900 92px ${S.FT}`;x.fillStyle=A;x.fillText(String(idx+1),X,Y);if(name){x.font=`800 ${fs}px ${S.FT}`;x.fillStyle='#fff';x.fillText(name,X+wn+22,Y-8)}
for(let i=0;i<n;i++){x.beginPath();x.arc(X+wn+30+i*22,Y+16,i==idx?6:4,0,TAU);x.fillStyle=i==idx?A:'rgba(255,255,255,.35)';x.fill()}x.restore()};

// číslo, ktoré hlas práve povedal (d.c={w:"9,000 rpm",t:čas v scéne}): naskočí veľké pri mieste, na ktoré sa kamera díva
const callout=(S,d,t,A)=>{const c=d.c;if(!c||!c.w)return;const k=t-(N(c.t)||0)+(N(d._sh)||0);if(k<0)return;const x=S.x,X=S.w-96,Y=124,sc=1+.42*Math.exp(-k*8)*Math.cos(k*20),a=ez(k/.12),w=String(c.w);
x.save();x.globalAlpha=a;let fs=118;x.font=`900 ${fs}px ${S.FT}`;const mw=S.w*.46,tw=x.measureText(w).width;if(tw>mw)fs*=mw/tw;x.font=`900 ${fs}px ${S.FT}`;const W=x.measureText(w).width;
if(['intake','compression','power','exhaust'].includes(String(d.f||''))){const P=[X-W*.5,Y+fs*.28],Q=[S.w/2+60,S.h/2-40],u=ez(k/.35);x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=3;x.beginPath();x.moveTo(P[0],P[1]);x.lineTo(P[0]+(Q[0]-P[0])*u,P[1]+(Q[1]-P[1])*u);x.stroke();if(u>=1){x.beginPath();x.arc(Q[0],Q[1],9+14*((k*1.1)%1),0,TAU);x.strokeStyle=rgba(A,1-((k*1.1)%1));x.lineWidth=3;x.stroke();dot(x,Q,6,'#fff',1,false)}}
x.translate(X-W/2,Y);x.scale(sc,sc);x.textAlign='center';x.textBaseline='middle';x.lineJoin='round';x.strokeStyle='rgba(0,0,0,.85)';x.lineWidth=16;x.strokeText(w,0,0);x.shadowColor=A;x.shadowBlur=26*Math.exp(-k*2.5)+8;x.fillStyle=A;x.fillText(w,0,0);x.restore()};

// ---------- štvortaktný motor v reze: l = názvy 4 dôb, f = záber na jednu dobu (tá beží pomaly, ostatné prebehnú) alebo "run" = motor beží naplno ----------
PRO.piston=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=(Array.isArray(d.l)?d.l:[]).map(s=>String(s==null?'':s).toUpperCase());
const CX=432,B=92,TOP=36,DECK=96,r=56,l=176,PH=84,PIN=46,CL=12,CY=DECK+CL+PIN+r+l,Ri=104,LB=306,NP=56,DUR=N(d._dur)||9;
const T1=Math.max(4.6,Math.min(7.6,DUR*.66)),zf=Math.min(S.w/470,S.h/548)*.96,FULL=[CX,266,zf];
const FSEL={intake:0,compression:1,power:2,exhaust:3}[String(d.f||'')],RUN=String(d.f||'')=='run',H=T1/4,PF=Math.max(3.2,Math.min(5.5,DUR*.8));
const VW=[[CX-34,164,zf*1.72],[CX,186,zf*1.5],[CX,142,zf*2.0],[CX+34,164,zf*1.7]];
const KF=RUN?[[0,FULL],[.2,[CX,292,zf*1.2],Math.max(3,DUR)]]:FSEL!=null?[[0,FULL],[.45,VW[FSEL],.8]]:[[0,FULL],[.8,VW[0]],[H-.1,VW[1]],[2*H-.35,VW[2],.5],[2*H+H*.42,[CX,300,zf*1.12],.9],[3*H-.05,VW[3]],[T1-.15,FULL,.9]];
const PT=[...Array(NP)].map((_,i)=>({gx:((i%8)+.12+.76*HS(i,11))/8,gy:(Math.floor(i/8)+.12+.76*HS(i,12))/7,fuel:HS(i,13)<.26,ein:.04+.7*HS(i,14),eex:.04+.7*HS(i,16),sd:HS(i,15)<.5?-1:1,lat:(HS(i,17)-.5)*22,rr:.8+.5*HS(i,18)}));
const outer=()=>{x.rect(CX-B-24,TOP,2*B+48,LB-TOP+40);x.moveTo(CX+Ri+16,CY);x.arc(CX,CY,Ri+16,0,TAU)};
const cavity=()=>{x.rect(CX-B,DECK,2*B,CY-DECK);x.moveTo(CX+Ri,CY);x.arc(CX,CY,Ri,0,TAU)};
const port=s=>{x.beginPath();x.moveTo(CX+s*(B+118),62);x.lineTo(CX+s*96,62);x.quadraticCurveTo(CX+s*46,62,CX+s*46,DECK+1)};
const portPt=(s,u,lat)=>{u=cl(u);let P;if(u<.62){P=[CX+s*(B+118)+(s*96-s*(B+118))*(u/.62),62]}else{const q=(u-.62)/.38,a=1-q;P=[CX+a*a*s*96+2*a*q*s*46+q*q*s*46,a*a*62+2*a*q*62+q*q*(DECK+8)]}const b=ez((u-.6)/.36);return [P[0]+lat*b*.8,P[1]+lat*(1-b)*.62]};
const INJ=[CX-112,46];
const valve=(s,lift)=>{const vx=CX+s*46,y=DECK+lift;x.strokeStyle='#e8eaec';x.lineWidth=6;x.beginPath();x.moveTo(vx,y);x.lineTo(vx,TOP-30+lift);x.stroke();
x.beginPath();x.moveTo(vx-27,y+3);x.lineTo(vx+27,y+3);x.lineTo(vx+15,y-9);x.lineTo(vx-15,y-9);x.closePath();x.fillStyle=metal(x,vx-27,vx+27);x.fill();x.strokeStyle='#000';x.lineWidth=1.5;x.stroke();
x.strokeStyle='#c2c6ca';x.lineWidth=2.5;x.beginPath();const y0=TOP-26+lift,y1=TOP-3,n=5;for(let i=0;i<=n;i++){const yy=y0+(y1-y0)*i/n;x.lineTo(vx+(i%2?10:-10),yy)}x.stroke();
x.fillStyle='#e8eaec';x.fillRect(vx-13,TOP-32+lift,26,5)};
// priebeh cyklu: prvý cyklus pomaly (dá sa sledovať), potom sa motor rozbehne
const phase=t=>{if(RUN)return 2+t*4.2/T1;if(FSEL!=null){const n=Math.floor(t/PF),u=t/PF-n;return n+(u<.74?(FSEL+u/.74)/4:(FSEL+1+(u-.74)/.26*3)/4)}if(t<=T1)return t/T1;const u=t-T1,k=Math.min(1,u/1.6),I=u+3.2*(k<1?1.6*(k*k*k-k*k*k*k/2):.8+(u-1.6));return 1+I/T1};
return (t,st)=>{const p=E(st(0,1));S.begin();x.globalAlpha=p;const ph=phase(t),cyc=((ph%1)+1)%1,th=cyc*2*TAU,stg=Math.min(3,Math.floor(cyc*4)),q=cyc*4-stg,fast=FSEL==null&&ph>1.02;
const K=G.crank(th,r,l),wy=CY-r-l+K.drop,crown=wy-PIN,pinX=CX+K.px,pinY=CY+K.py,top=DECK+2,hgt=Math.max(0,crown-top);
const home=(o,i,amp,spd)=>{const w=wob(i,t,amp,spd);return [Math.max(CX-B+8,Math.min(CX+B-8,CX+(o.gx-.5)*2*(B-14)+w[0])),Math.max(top+5,Math.min(crown-5,top+7+o.gy*Math.max(2,hgt-14)+w[1]*Math.min(1,hgt/70)))]};
const chamber=()=>x.rect(CX-B+2,top,2*B-4,hgt);
// kamera + otras pri zážihu
const cm=camAt(KF,t,.75),shk=stg==2&&q<.16?(1-q/.16)*(fast?.5:1):0;
x.save();x.translate(S.w/2+Math.sin(t*93)*6*shk,S.h/2+Math.cos(t*71)*5*shk);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
// svetlo za modelom
{const g=x.createRadialGradient(CX,270,20,CX,270,430);g.addColorStop(0,'rgba(86,118,160,.22)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(CX-440,-170,880,880)}
// blok a hlava v reze
x.lineWidth=8;x.strokeStyle='#fff';x.beginPath();outer();x.stroke();{const g=x.createLinearGradient(0,TOP,0,CY+Ri);g.addColorStop(0,'#33373c');g.addColorStop(1,'#1c1e21');x.fillStyle=g}x.beginPath();outer();x.fill();hatch(x,outer);
// chladiaca voda v stenách valca
[-1,1].forEach(s=>{const wx=CX+s*(B+12);x.fillStyle=rgba(WATER,.5);x.beginPath();x.roundRect(wx-5,DECK+10,10,LB-DECK-34,5);x.fill();for(let k=0;k<4;k++){const u=((t*.35+k/4)%1);dot(x,[wx,LB-28-u*(LB-DECK-44)],2.2,'#d9f0ff',.8*Math.sin(Math.PI*u),false)}});
x.beginPath();cavity();x.lineWidth=8;x.strokeStyle='#fff';x.stroke();x.fillStyle='#050607';x.beginPath();cavity();x.fill();
{const g=x.createLinearGradient(CX-B,0,CX+B,0);g.addColorStop(0,'rgba(255,255,255,.10)');g.addColorStop(.18,'rgba(255,255,255,0)');g.addColorStop(.82,'rgba(255,255,255,0)');g.addColorStop(1,'rgba(255,255,255,.10)');x.fillStyle=g;x.fillRect(CX-B+4,DECK+4,2*B-8,LB-DECK)}
// olej v kľukovej skrini
x.save();x.beginPath();x.arc(CX,CY,Ri-4,0,TAU);x.clip();x.beginPath();x.moveTo(CX-Ri,CY+Ri);for(let i=0;i<=24;i++){const xx=CX-Ri+2*Ri*i/24;x.lineTo(xx,CY+Ri*.7+Math.sin(i*.9+t*2.2)*2.4+Math.sin(i*.37-t*1.3)*1.8)}x.lineTo(CX+Ri,CY+Ri);x.closePath();x.fillStyle='#5a3d12';x.fill();x.strokeStyle='#c98a2b';x.lineWidth=2;x.stroke();x.restore();
// sací a výfukový kanál, vstrekovač
[-1,1].forEach(s=>{x.lineCap='butt';port(s);x.strokeStyle='#fff';x.lineWidth=40;x.stroke();port(s);x.strokeStyle='#050607';x.lineWidth=32;x.stroke();x.lineCap='round'});
x.save();x.translate(INJ[0],INJ[1]);x.rotate(.62);x.fillStyle='#d8dadd';x.fillRect(-7,-40,14,34);x.fillStyle='#8a8f94';x.fillRect(-10,-46,20,8);x.fillStyle=FUEL;x.fillRect(-3.5,-7,7,9);x.restore();
// plyn vo valci: studená zmes je modrastá, stláčaním sa ohrieva, po zhorení sivé spaliny
if(hgt>1){x.beginPath();chamber();x.fillStyle=stg==0?rgba(AIR,.10):stg==1?mix(AIR,'#ffb347',q,.10+.16*q):stg==3?`rgba(150,155,160,${.22*(1-.5*q)})`:'rgba(0,0,0,0)';x.fill()}
const PLUG=[CX,DECK+9],maxR=Math.hypot(B,hgt)+12;
if(stg==2)flame(x,chamber,PLUG,maxR,q,A,p,t);
if(stg==3&&q<.18){x.save();x.globalAlpha=p*.45*(1-q/.18);x.beginPath();chamber();x.fillStyle='#8a2a0a';x.fill();x.restore();x.globalAlpha=p}
PT.forEach((o,i)=>{const cA=o.fuel?FUEL:(stg==1?mix(AIR,'#ffe2b8',q):AIR),rA=(o.fuel?3.6:2.8)*o.rr;
const qi=stg==0?q:stg==3?q-1:null;if(qi!=null){const uu=(qi-(o.ein-.3))/.3;if(uu>0&&uu<1){const w=wob(i+200,t,3,4);let P=portPt(-1,uu,o.lat);P=[P[0]+w[0],P[1]+w[1]];if(o.fuel){if(uu<.42)return;P=lerp(INJ,P,ez((uu-.42)/.2))}dot(x,P,rA,o.fuel?FUEL:AIR,Math.min(1,uu*5),true)}}
if(stg==0&&q>=o.ein){const f=ez((q-o.ein)/.26),gap=[CX-46+o.sd*25,DECK+9+7*Math.sin(Math.PI*q)];dot(x,lerp(gap,home(o,i,7,2.4),f),rA,cA,1,true)}
if(stg==1)dot(x,home(o,i,5+3*q,2.6+4*q),rA,cA,1,true);
if(stg==2&&q<.16){const P=home(o,i,8,6.5);if(Math.hypot(P[0]-PLUG[0],P[1]-PLUG[1])>ez(q/.16)*maxR)dot(x,P,rA,o.fuel?FUEL:'#ffe2b8',1,true)}
if(stg==2&&i<20){const P=home(o,i,13,9);dot(x,P,1.6+1.4*HS(i,40),'#fff6d8',(1-q)*(.5+.5*Math.sin(t*23+i)),false)}
const qx=stg==3?q:stg==0?q+1:null;if(qx!=null){const rS=(4.2+2.6*HS(i,19));if(qx<o.eex){if(stg==3)dot(x,home(o,i,6,2.2),rS,SMOKE,.5*Math.min(1,q/.1),true)}
else if(qx<o.eex+.2){if(stg==3)dot(x,lerp(home(o,i,6,2.2),[CX+46+o.sd*25,DECK+9],ez((qx-o.eex)/.2)),rS,SMOKE,.5,true)}
else{const uu=(qx-o.eex-.2)/.34;if(uu<1){const w=wob(i+300,t,4,3),P=portPt(1,1-uu,o.lat);dot(x,[P[0]+w[0],P[1]+w[1]],rS*(1+1.3*uu),SMOKE,.5*(1-uu),true)}}}});
if(stg==0&&q>.06&&q<.74)for(let k=0;k<12;k++){const u=((t*2.3+HS(k,50))%1),a=.95+(HS(k,51)-.5)*.75,dd=6+u*46;dot(x,[INJ[0]+Math.cos(a)*dd,INJ[1]+Math.sin(a)*dd*.55+2],1.8,FUEL,(1-u)*.9,false)}
// kľuka s protizávažím
const ca=th-Math.PI/2;x.save();x.shadowColor='rgba(0,0,0,.6)';x.shadowBlur=14;x.translate(CX,CY);x.rotate(ca);x.beginPath();x.moveTo(r,-22);x.lineTo(-8,-34);x.arc(0,0,78,Math.PI-1.05,Math.PI+1.05);x.lineTo(-8,34);x.lineTo(r,22);x.arc(r,0,22,Math.PI/2,-Math.PI/2,true);x.closePath();const cg=x.createRadialGradient(0,0,6,0,0,80);cg.addColorStop(0,'#5a5f65');cg.addColorStop(1,'#2a2d31');x.fillStyle=cg;x.fill();x.shadowBlur=0;x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.restore();
x.beginPath();x.arc(CX,CY,17,0,TAU);x.fillStyle='#9aa0a6';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
// ojnica
const ang=Math.atan2(pinY-wy,pinX-CX),nx=-Math.sin(ang),ny=Math.cos(ang);x.beginPath();x.moveTo(CX+nx*9,wy+ny*9);x.lineTo(pinX+nx*15,pinY+ny*15);x.lineTo(pinX-nx*15,pinY-ny*15);x.lineTo(CX-nx*9,wy-ny*9);x.closePath();x.fillStyle='#aab0b6';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.arc(pinX,pinY,23,0,TAU);x.fillStyle='#aab0b6';x.fill();x.stroke();dot(x,[pinX,pinY],12,A,1,true);
// piest s krúžkami
x.save();x.shadowColor='rgba(0,0,0,.55)';x.shadowBlur=12;x.fillStyle=metal(x,CX-B,CX+B);x.fillRect(CX-B+3,crown,2*B-6,PH);x.restore();x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(CX-B+3,crown,2*B-6,PH);x.fillStyle='#2c2f33';[11,22,33].forEach(o=>x.fillRect(CX-B+3,crown+o,2*B-6,4));
x.beginPath();x.arc(CX,wy,13,0,TAU);x.fillStyle='#5d6268';x.fill();x.strokeStyle='#222';x.lineWidth=2;x.stroke();
// ventily a sviečka
const lin=stg==0?Math.sin(Math.PI*q)*18:0,lex=stg==3?Math.sin(Math.PI*q)*18:0;valve(-1,lin);valve(1,lex);
x.fillStyle='#eceef0';x.fillRect(CX-9,TOP-24,18,DECK-TOP+22);x.fillStyle='#8a8f94';x.fillRect(CX-13,TOP-10,26,12);x.strokeStyle='#eceef0';x.lineWidth=3;x.beginPath();x.moveTo(CX,DECK-2);x.lineTo(CX,DECK+7);x.stroke();
spark(x,PLUG,stg==2&&q<.2?1-q/.2:(stg==1&&q>.95?(q-.95)/.05:0),A,p,t);
// žiara ohňa osvetlí okolie
if(stg==2){x.save();x.globalCompositeOperation='lighter';const g=x.createRadialGradient(CX,top+hgt*.5,10,CX,top+hgt*.5,300);g.addColorStop(0,`rgba(255,150,50,${.42*(1-q)})`);g.addColorStop(1,'rgba(255,150,50,0)');x.fillStyle=g;x.fillRect(CX-300,top-260,600,640);x.restore()}
x.restore();
// názov doby
if(FSEL!=null){const u=(t/PF)%1;if(u<.74)stamp(S,FSEL,LN[FSEL]||'',4,Math.min(u*PF-(t<PF?.35:0),(.74-u)*PF*2),A)}else if(t>.35&&!(fast&&ph>1.6))stamp(S,stg,LN[stg]||'',4,fast?1:Math.min(q*H,t-.35),A);callout(S,d,t,A);
x.globalAlpha=1}};

// ---------- rotačný (Wankelov) motor v reze: l = sanie, kompresia, expanzia, výfuk; f = záber na miesto jednej doby alebo "run" ----------
PRO.wankel=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=(Array.isArray(d.l)?d.l:[]).map(s=>String(s==null?'':s).toUpperCase()),e0=27,R=190,W=G.wankel(R,e0),CX=432,CY=292,mm=4.5,TH=24,NC=30,DUR=N(d._dur)||9;
const zf=Math.min(S.w/520,S.h/520)*.96,FULL=[CX,CY-8,zf],FN=['intake','compression','power','exhaust'].indexOf(String(d.f||'')),RUN=String(d.f||'')=='run',FV=[[CX+100,CY-96,zf*1.65],[CX+165,CY+75,zf*1.6],[CX-150,CY+118,zf*1.6],[CX-100,CY-96,zf*1.65]];
const KF=RUN?[[0,FULL],[.2,[CX,CY,zf*1.18],Math.max(3,DUR)]]:FN>=0?[[0,FULL],[.45,FV[FN],.8]]:[[0,FULL],[.9,[CX+100,CY-96,zf*1.65]],[Math.min(3.6,DUR*.36),[CX+30,CY+120,zf*1.7]],[Math.min(6.2,DUR*.62),[CX-110,CY+30,zf*1.55]],[Math.min(8.2,DUR*.82),FULL,1]];
const hp=(off)=>{for(let i=0;i<=120;i++){const q=W.house(i/120*TAU,off);i?x.lineTo(CX+q[0],CY+q[1]):x.moveTo(CX+q[0],CY+q[1])}x.closePath()};
const PX=62,PW=34,yIn=(()=>{let b=0;for(let i=0;i<=400;i++){const q=W.house(Math.PI+i/400*Math.PI);if(Math.abs(q[0]-PX)<3)b=q[1]}return CY+b})();
const ports=()=>{[1,-1].forEach(s=>{x.fillStyle='#050607';x.fillRect(CX+s*PX-PW/2,74,PW,yIn-74+14);x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(CX+s*PX-PW/2,74);x.lineTo(CX+s*PX-PW/2,yIn-4);x.moveTo(CX+s*PX+PW/2,74);x.lineTo(CX+s*PX+PW/2,yIn-4);x.stroke()})};
const CP=[...Array(NC)].map((_,i)=>({s:.07+.86*((i%10)+.15+.7*HS(i,61))/10,dp:.14+.72*(Math.floor(i/10)+.15+.7*HS(i,62))/3,fuel:HS(i,63)<.27,ein:.04+.68*HS(i,64),eex:.12+.58*HS(i,65),rr:.8+.5*HS(i,66)}));
const sy=CY+R-e0,MIN=[CX+PX,yIn+8],MEX=[CX-PX,yIn+8],SPK=[CX,sy-10];
const tag=(s,px,py,al,col)=>{if(!s)return;x.font=`800 25px ${S.FT}`;x.textAlign=al;x.textBaseline='middle';x.fillStyle=col||'#e9ecef';x.fillText(s,px,py)};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const fi=t*(RUN?1.9:.72),c=W.center(fi);
let sk=0;for(let k=0;k<3;k++){const psi=(((fi+TAU*k/3+Math.PI/3)%TAU)+TAU)%TAU,dd=psi-Math.PI/2;if(dd>-.05&&dd<.3)sk=Math.max(sk,dd<0?1+dd/.05:1-dd/.3)}
const cm=camAt(KF,t,.9);x.save();x.translate(S.w/2+Math.sin(t*93)*5*sk,S.h/2+Math.cos(t*71)*4*sk);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(CX,CY,20,CX,CY,420);g.addColorStop(0,'rgba(86,118,160,.22)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(CX-430,CY-430,860,860)}
// skriňa v reze
x.beginPath();hp(TH);x.lineWidth=8;x.strokeStyle='#fff';x.stroke();{const g=x.createLinearGradient(0,CY-200,0,CY+200);g.addColorStop(0,'#33373c');g.addColorStop(1,'#1c1e21');x.fillStyle=g}x.fill();hatch(x,()=>hp(TH));
x.beginPath();hp(0);x.lineWidth=8;x.strokeStyle='#fff';x.stroke();x.fillStyle='#050607';x.fill();ports();
// prúdenie v kanáloch: studený vzduch s palivom dnu, spaliny von
for(let k=0;k<16;k++){const u=(t*.5*(.7+.6*HS(k,71))+HS(k,72))%1,w=wob(k+400,t,3,3.5),fu=HS(k,73)<.3;dot(x,[CX+PX+(HS(k,74)-.5)*20+w[0],76+u*(yIn-70)],(fu?3.4:2.7),fu?FUEL:AIR,Math.min(1,u*6),true);
const u2=(t*.42*(.7+.6*HS(k,75))+HS(k,76))%1,w2=wob(k+500,t,4,3);dot(x,[CX-PX+(HS(k,77)-.5)*16+w2[0],yIn+6-u2*(yIn-66)],4.5*(1+1.1*u2),SMOKE,.5*(1-u2)*Math.min(1,u2*6),true)}
// tri komory: v každej sa deje iná doba
for(let k=0;k<3;k++){const psi=(((fi+TAU*k/3+Math.PI/3)%TAU)+TAU)%TAU,sec=Math.floor(psi/(Math.PI/2))%4,q=psi/(Math.PI/2)-sec;const C=W.chamber(fi,k,26).map(P=>[CX+P[0],CY+P[1]]),clipC=()=>poly(x,C);
const a0=fi+TAU*k/3,F=W.flank(fi,k,40);
const cpt=(o,i,amp,spd)=>{const h=W.house(a0+o.s*TAU/3),f=F[Math.round(o.s*40)],w=wob(i+k*40,t,amp,spd);return [CX+h[0]+(f[0]-h[0])*o.dp+w[0]*.6,CY+h[1]+(f[1]-h[1])*o.dp+w[1]*.6]};
x.beginPath();clipC();x.fillStyle=sec==3?rgba(AIR,.10):sec==0?mix(AIR,'#ffb347',q,.10+.16*q):sec==2?`rgba(150,155,160,${.22*(1-.5*q)})`:'rgba(0,0,0,0)';x.fill();
if(sec==1)flame(x,clipC,SPK,330,q,A,p,t+k);
if(sec==2&&q<.18){x.save();x.globalAlpha=p*.45*(1-q/.18);x.beginPath();clipC();x.fillStyle='#8a2a0a';x.fill();x.restore();x.globalAlpha=p}
x.save();x.beginPath();clipC();x.clip();
CP.forEach((o,i)=>{const cA=o.fuel?FUEL:(sec==0?mix(AIR,'#ffe2b8',q):AIR),rA=(o.fuel?3.5:2.7)*o.rr;
if(sec==3){if(q>=o.ein)dot(x,lerp(MIN,cpt(o,i,6,2.4),ez((q-o.ein)/.26)),rA,cA,1,true)}
else if(sec==0)dot(x,cpt(o,i,5+3*q,2.6+4*q),rA,cA,1,true);
else if(sec==1){if(q<.16){const P=cpt(o,i,8,6.5);if(Math.hypot(P[0]-SPK[0],P[1]-SPK[1])>ez(q/.16)*330)dot(x,P,rA,o.fuel?FUEL:'#ffe2b8',1,true)}if(i<14)dot(x,cpt(o,i,12,9),1.5+1.4*HS(i,40),'#fff6d8',(1-q)*(.5+.5*Math.sin(t*23+i)),false)}
else{const rS=4+2.4*HS(i,19);if(q<o.eex)dot(x,cpt(o,i,6,2.2),rS,SMOKE,.5*Math.min(1,q/.1),true);else{const f=ez((q-o.eex)/.26);if(f<1)dot(x,lerp(cpt(o,i,6,2.2),MEX,f),rS,SMOKE,.5*(1-f*f),true)}}});
x.restore()}
// rotor
x.save();x.shadowColor='rgba(0,0,0,.6)';x.shadowBlur=16;x.beginPath();for(let k=0;k<3;k++)W.flank(fi,k,22).forEach((P,i)=>(k||i)?x.lineTo(CX+P[0],CY+P[1]):x.moveTo(CX+P[0],CY+P[1]));x.closePath();const rg=x.createRadialGradient(CX+c[0]-40,CY+c[1]-50,30,CX+c[0],CY+c[1],R);rg.addColorStop(0,'#6a7078');rg.addColorStop(1,'#2a2d31');x.fillStyle=rg;x.fill();x.restore();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.save();x.translate(CX+c[0],CY+c[1]);x.rotate(fi);x.beginPath();x.arc(0,0,3*e0+mm*2.4,0,TAU);x.fillStyle='#4d5258';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();G.gearPts(36,-.06).forEach((q,i)=>i?x.lineTo(q[0]*mm,q[1]*mm):x.moveTo(q[0]*mm,q[1]*mm));x.closePath();x.fillStyle='#050607';x.fill();x.lineWidth=2;x.stroke();x.restore();
GEARPRO(x,CX,CY,2*e0,24,0,'#fff',{fill:'#9aa0a6'});
x.strokeStyle=A;x.lineWidth=9;x.beginPath();x.moveTo(CX,CY);x.lineTo(CX+c[0],CY+c[1]);x.stroke();dot(x,[CX,CY],11,A,1,true);dot(x,[CX+c[0],CY+c[1]],8,'#fff',1,false);
for(let k=0;k<3;k++){const a=W.apex(fi,k);dot(x,[CX+a[0]-Math.cos(fi+TAU*k/3)*5,CY+a[1]-Math.sin(fi+TAU*k/3)*5],5,'#fff',1,false)}
x.fillStyle='#eceef0';x.fillRect(CX-8,sy-4,16,TH+26);x.fillStyle='#8a8f94';x.fillRect(CX-12,sy+TH+2,24,10);
spark(x,SPK,sk,A,p,t);
if(sk>0){x.save();x.globalCompositeOperation='lighter';const g=x.createRadialGradient(CX-60,sy-30,10,CX-60,sy-30,260);g.addColorStop(0,`rgba(255,150,50,${.3*sk})`);g.addColorStop(1,'rgba(255,150,50,0)');x.fillStyle=g;x.fillRect(CX-330,sy-300,560,560);x.restore()}
// názvy dôb pri miestach, kde prebiehajú
x.globalAlpha=RUN?0:p*sp*(1-ez((cm[2]/zf-1)/.22));tag(LN[0],CX+PX+30,58,'left',AIR);tag(LN[3],CX-PX-30,58,'right',SMOKE);tag(LN[1],CX+150,CY+222,'left','#e9ecef');tag(LN[2],CX-150,CY+222,'right',FIRE);
x.restore();x.globalAlpha=p;if(FN>=0&&t>.35)stamp(S,FN,LN[FN]||'',4,t-.35,A);callout(S,d,t,A);x.globalAlpha=1}};
PRO.rotary=PRO.wankel;

// ---------- porovnanie: dva stroje bežia vedľa seba (a, b = názvy modelov, l = ich mená) ----------
PRO.versus=(v,d)=>{const ms=[d.a,d.b].map((m,i)=>PRO[m]&&m!='versus'?m:['piston','wankel'][i]),LN=(Array.isArray(d.l)?d.l:[]).map(s=>String(s==null?'':s).toUpperCase()),OFF=WIDE?222:238,SCL=WIDE?.5:.54,A=D.acc;
const FT=(getComputedStyle(document.documentElement).getPropertyValue('--f')||'').trim()||'Helvetica Neue,Arial,sans-serif';
const ups=ms.map((m,i)=>{const w=el('div','',`position:absolute;left:0;top:0;width:864px;height:560px;transform-origin:50% 50%;transform:translate(${(i?1:-1)*OFF}px,26px) scale(${SCL})`);v.append(w);return PRO[m](w,{m,f:'run',_dur:d._dur,l:[]})});
const tags=ms.map((m,i)=>{const e=el('div','',`position:absolute;left:${432+(i?1:-1)*OFF-230}px;top:18px;width:460px;text-align:center;font:800 34px ${FT};letter-spacing:.02em;color:#fff`,esc(LN[i]||''));v.append(e);return e});
const vs=el('div','',`position:absolute;left:382px;top:232px;width:100px;height:100px;border-radius:50%;background:#050607;border:3px solid ${A};color:${A};font:900 38px/94px ${FT};text-align:center;box-shadow:0 0 28px ${A}66`,'VS');v.append(vs);
return (t,st)=>{const p=E(st(0,1));ups.forEach(u=>u(t,st));tags.forEach((e,i)=>{const q=E((t-.25-i*.2)/.5);e.style.opacity=p*q;e.style.transform=`translateY(${(1-q)*14}px)`});const q=E((t-.5)/.4);vs.style.opacity=p*q;vs.style.transform=`scale(${.6+.4*q+.04*Math.sin(t*3)})`}};

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
// úvodné scény „kde to je“: auto príde zboku; ďalšie (napr. dom) si doplnia modely cez KIT.INTRO (still = scéna stojí, hýbe sa v nej len to, čo naozaj)
const INTRO={car:{hot:CARHOT,draw:CAR}};
const CTX={piston:['car','engine'],wankel:['car','engine'],rotary:['car','engine'],camshaft:['car','engine'],gearbox:['car','gearbox'],differential:['car','diff'],car_brake:['car','brake']};
// obalí model: auto príde, diel sa rozsvieti, kamera doň vletí a prelne sa do rezu
const withIntro=(v,d,ctx,base)=>{const vm=el('div','','position:absolute;left:0;top:0;width:864px;height:560px;transform-origin:50% 50%;opacity:0');v.append(vm);d._sh=(d._first?1.15:Math.max(1.7,Math.min(2.8,(N(d._dur)||8)*.3)))*.78;const upd=base(vm,d);
const S=STG(v),x=S.x;x.canvas.style.cssText+=';-webkit-mask-image:radial-gradient(ellipse 56% 56% at 50% 50%,#000 74%,transparent 100%);-webkit-mask-composite:source-over;mask-composite:add';const A=D.acc,IN=d._first?1.15:Math.max(1.7,Math.min(2.8,(N(d._dur)||8)*.3)),SC=WIDE?1.5:1.62,OX=(S.w-520*SC)/2,OY=S.h/2+150,_sh=(d._sh=IN*.78),SCN=INTRO[ctx[0]]||INTRO.car,h=SCN.hot[ctx[1]],H=[OX+h[0]*SC,OY+h[1]*SC];
return (t,st)=>{S.begin();const u=t/IN;if(u<1.02){const drive=1-ez(u/.42),dx=SCN.still?0:-drive*drive*700,zo=ez((u-.6)/.4),z=1+zo*zo*8.5,P=lerp(H,[S.w/2,S.h/2],ez((u-.6)/.34));
x.save();x.globalAlpha=(d._first?1:E(u/.12))*(1-ez((u-.74)/.2));x.translate(P[0],P[1]);x.scale(z,z);x.translate(-H[0],-H[1]);
{const g=x.createRadialGradient(S.w/2,OY-120,20,S.w/2,OY-120,460);g.addColorStop(0,'rgba(86,118,160,.2)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(0,0,S.w,S.h)}
x.strokeStyle='rgba(255,255,255,.22)';x.lineWidth=2;x.beginPath();x.moveTo(-200,OY);x.lineTo(S.w+200,OY);x.stroke();
x.translate(OX+dx,OY);x.scale(SC,SC);SCN.draw(x,SCN.still?t:dx/(44*SC),u>.36?ctx[1]:null,A,((t*1.5)%1));x.restore()}
const ma=ez((u-.76)/.24);vm.style.opacity=ma;vm.style.transform=`scale(${(.3+.7*ez((u-.68)/.32)).toFixed(4)})`;if(ma>0)upd(Math.max(0,t-IN*.78),st)}};
window.MECHPRO=PRO;
// stavebnica: overené diely a efekty, z ktorých sa skladajú ďalšie presné modely (zz_mech_pro_*.js)
window.KIT={PRO,G,GEARPRO,HS,hex,rgba,mix,ez,lerp,wob,dot,flame,spark,metal,hatch,poly,STG,camAt,stamp,callout,CAR,CARHOT,CTX,INTRO,AIR,FUEL,SMOKE,FIRE,WATER};
const _m3=V.mech;V.mech=(v,d)=>{const base=PRO[d&&d.m]?PRO[d.m]:_m3,c=d&&d._in&&CTX[d.m];return c?withIntro(v,d,c,base):base(v,d)};
}
