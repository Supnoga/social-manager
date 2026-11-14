// Presné modely 5 – energia: veterná turbína, gondola v reze zboku. Veža a gondola stoja; točí sa rotor, hriadele, kolesá a generátor.
// Rotor ide skutočnou rýchlosťou (15 ot./min). Rýchly hriadeľ je na obraze spomalený (inak by na 30 snímkach blikal), skutočné otáčky ukazuje číslo.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,CTX,INTRO,lead,badge,integ,edge,bearing}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},SH=['#5b6067','#eef1f4','#565b62'],GC=['#30343a','#8f959c','#2a2d32'];
const track=P=>{const L=[0];for(let i=1;i<P.length;i++)L.push(L[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));const T=L[L.length-1];
return {P,T,at:u=>{const s=Math.max(0,Math.min(1,u))*T;let i=1;while(i<P.length-1&&L[i]<s)i++;const k=(s-L[i-1])/((L[i]-L[i-1])||1);return [P[i-1][0]+(P[i][0]-P[i-1][0])*k,P[i-1][1]+(P[i][1]-P[i-1][1])*k]}}};

// l = [rotor, prevodovka, generátor, veža]; f = rotor | gearbox | generator | run (silnejší vietor)
PRO.wind_turbine=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),RUN=F=='run',CY=280,HUBX=142,BL=380,YI=208,YG=263;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,292,zf],FV={rotor:[222,280,zf*1.4],gearbox:[512,258,zf*2.25],generator:[728,266,zf*1.95]},ORD=['rotor','gearbox','generator'],KF=cams(d,FULL,FV,ORD,DUR);
// vietor zosilnie a rotor zrýchli; uhol je integrál otáčok, nič neposkočí
const W0=d._first?.75:RUN?1.3:1.57,W1=RUN?1.9:1.57,wr=t=>W0+(W1-W0)*ez(t/2.8);
const CAB=track([[812,342],[812,376],[520,376],[520,760]]);
const blade=(ph,front)=>{const sy=Math.sin(ph),cz=Math.cos(ph);if((cz>=0)!=front)return;x.fillStyle=front?'#d9dde1':'#636970';x.strokeStyle=front?'#fff':'rgba(255,255,255,.45)';x.lineWidth=2.5;x.lineJoin='round';
if(Math.abs(sy)<.14){x.beginPath();x.ellipse(HUBX,CY+sy*60,19,25,0,0,TAU);x.fill();x.stroke();return}
const Y=CY+sy*BL,s=sy>0?1:-1;x.beginPath();x.moveTo(HUBX-19,CY+s*30);x.quadraticCurveTo(HUBX-28,CY+sy*BL*.35,HUBX-6,Y);x.lineTo(HUBX+5,Y);x.quadraticCurveTo(HUBX+24,CY+sy*BL*.3,HUBX+19,CY+s*30);x.closePath();x.fill();x.stroke()};
const cone=()=>{x.beginPath();x.moveTo(196,CY-52);x.bezierCurveTo(120,CY-56,62,CY-30,58,CY);x.bezierCurveTo(62,CY+30,120,CY+56,196,CY+52);x.closePath()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-(RUN?1.16:1))/.22),w=wr(t),wk=w/1.57,aR=integ(wr,t),aI=-5*aR,aG=20*aR;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);

// vietor
x.lineCap='round';for(let i=0;i<44;i++){const u=(t*.2*(.7+.6*HS(i,41))*wk+HS(i,42))%1,X=-90+u*1100,Y=-150+HS(i,43)*860;x.strokeStyle=`rgba(190,226,255,${(.32*Math.sin(Math.PI*u)).toFixed(3)})`;x.lineWidth=2.5;x.beginPath();x.moveTo(X,Y);x.lineTo(X+30*wk,Y);x.stroke()}x.lineCap='butt';
// veža a otoč gondoly (stoja)
x.beginPath();x.moveTo(462,412);x.lineTo(578,412);x.lineTo(592,760);x.lineTo(448,760);x.closePath();x.fillStyle='#16191d';x.fill();x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=4;x.stroke();
// lopatky za nábojom
for(let b=0;b<3;b++)blade(aR+b*TAU/3,false);
// gondola
x.beginPath();x.roundRect(196,150,668,262,26);x.fillStyle='#101215';x.fill();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=4;x.stroke();
x.fillStyle='#4a4f56';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(452,404,136,14);x.fill();x.stroke();
x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=6;x.beginPath();x.moveTo(226,394);x.lineTo(842,394);x.stroke();
// kábel z generátora dole vežou
x.strokeStyle='#3a3f45';x.lineWidth=7;x.lineJoin='round';x.beginPath();CAB.P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();
for(let i=0;i<16;i++){const u=(t*.42+i/16)%1;dot(x,CAB.at(u),4,A,.9*cl(u/.05),true)}
// hlavný (pomalý) hriadeľ a jeho ložisko
x.fillStyle='#2c3035';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(246,CY+50,34,342-CY);x.fill();x.stroke();
edge(x,318,CY,244,24,24,aR,6,{col:SH,tooth:'#30343a',lw:3,ow:2.5});bearing(x,263,CY-38,36,26);bearing(x,263,CY+38,36,26);
// prevodovka: dva stupne, každý otáčky znásobí
x.beginPath();x.roundRect(440,150,150,244,10);x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
edge(x,515,YI,120,7,7,aI,2,{col:SH,tooth:'#30343a',lw:2,ow:2});edge(x,616,YG,104,7,7,aG,1,{col:SH,tooth:'#30343a',lw:2.5,ow:2});
bearing(x,448,YI,12,22);bearing(x,582,YI,12,22);bearing(x,582,YG,12,22);
edge(x,472,CY,34,60,60,aR,10,{tooth:A,lw:3,col:GC});edge(x,472,YI,34,12,12,aI,3,{tooth:A,lw:2.4,col:GC});
edge(x,548,YI,30,44,44,aI,5,{tooth:A,lw:3,col:GC});edge(x,548,YG,30,11,11,aG,1,{tooth:A,lw:3,col:GC});
// brzda na rýchlom hriadeli
edge(x,620,YG,8,30,30,aG,1,{tooth:'#30343a',lw:3,col:['#6c7178','#d5dade','#666b72'],ow:2});x.fillStyle='#6c7178';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(608,YG-44,24,18);x.fill();x.stroke();
// generátor: magnety rotora sa točia vnútri medených cievok statora
x.beginPath();x.roundRect(650,184,180,158,10);x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
{const g=.5+.5*Math.sin(t*19);[198,310].forEach(Y=>{x.beginPath();x.roundRect(664,Y,152,18,7);x.fillStyle='#b87333';x.fill();x.save();x.clip();x.strokeStyle='rgba(60,30,8,.75)';x.lineWidth=2;x.beginPath();for(let X=670;X<816;X+=8){x.moveTo(X,Y);x.lineTo(X,Y+18)}x.stroke();x.restore();x.strokeStyle='#fff';x.lineWidth=1.5;x.stroke();
x.save();x.globalCompositeOperation='lighter';x.globalAlpha*=.16+.3*g*cl(wk);x.fillStyle=A;x.fillRect(664,Y,152,18);x.restore()})}
edge(x,740,YG,128,40,40,aG,1,{tooth:A,lw:7,col:['#33373c','#9aa0a6','#2f3237']});bearing(x,658,YG,12,22);bearing(x,822,YG,12,22);
// anemometer na streche: meria vietor
x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.moveTo(826,150);x.lineTo(826,126);x.stroke();for(let k=0;k<3;k++){const a=t*6*wk+k*TAU/3;dot(x,[826+17*Math.cos(a),124],4.2+1.6*Math.sin(a),Math.sin(a)>0?'#fff':'#8a9097',1,false)}
// náboj s lopatkami pred ním
cone();{const g=x.createLinearGradient(0,CY-56,0,CY+56);g.addColorStop(0,'#7b8188');g.addColorStop(.4,'#eef1f4');g.addColorStop(1,'#6b7077');x.fillStyle=g;x.fill()}
x.save();cone();x.clip();x.strokeStyle='#30343a';for(let k=0;k<6;k++){const ph=aR+k*TAU/6,c=Math.cos(ph);if(c<=.04)continue;x.globalAlpha=p*(.2+.6*c);x.lineWidth=3*c;x.beginPath();x.moveTo(50,CY+56*Math.sin(ph));x.lineTo(200,CY+56*Math.sin(ph));x.stroke()}x.restore();x.globalAlpha=p;
cone();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
for(let b=0;b<3;b++)blade(aR+b*TAU/3,true);
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],300,112,214,246);lead(S,LN[1],515,112,515,152);lead(S,LN[2],706,112,726,186);lead(S,LN[3],694,452,582,452);
x.restore();
// otáčky rotora (vľavo) a generátora (vpravo): prevodovka ich znásobí stokrát
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4),rpm=Math.round(15*wk);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',3,ts-.35,A);
meter(S,String(rpm),'RPM',A,a,fi>=0);badge(S,String(rpm*100),'RPM',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- úvod: celá turbína spredu; veža stojí, točí sa len rotor ----------
const TURB=(x,t,hot,A,pulse)=>{const on=hot=='nacelle',HX=260,HY=-270;x.lineJoin='round';
x.lineCap='round';for(let j=0;j<9;j++){const u=(t*.35+HS(j,51))%1;x.strokeStyle=`rgba(190,226,255,${(.4*Math.sin(Math.PI*u)).toFixed(3)})`;x.lineWidth=2.2;const X=-60+u*640,Y=-400+HS(j,52)*370;x.beginPath();x.moveTo(X,Y);x.lineTo(X+26,Y);x.stroke()}x.lineCap='butt';
x.beginPath();x.moveTo(HX-15,0);x.lineTo(HX-7,HY+12);x.lineTo(HX+7,HY+12);x.lineTo(HX+15,0);x.closePath();x.fillStyle='rgba(255,255,255,.07)';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.roundRect(HX-18,HY-17,36,34,8);x.fillStyle=on?A:'rgba(255,255,255,.1)';if(on){x.save();x.shadowColor=A;x.shadowBlur=18+10*pulse;x.fill();x.restore()}else x.fill();x.strokeStyle='#fff';x.lineWidth=2.4;x.stroke();
for(let b=0;b<3;b++){x.save();x.translate(HX,HY);x.rotate(t*1.57+b*TAU/3);x.beginPath();x.moveTo(8,-8);x.quadraticCurveTo(60,-18,142,-2.5);x.lineTo(142,2.5);x.quadraticCurveTo(50,10,8,8);x.closePath();x.fillStyle='rgba(235,238,241,.9)';x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke();x.restore()}
x.beginPath();x.arc(HX,HY,11,0,TAU);x.fillStyle='#fff';x.fill();
if(on){x.beginPath();x.arc(HX,HY,46+16*pulse,0,TAU);x.strokeStyle=rgba(A,.75*(1-pulse));x.lineWidth=3;x.stroke()}};
INTRO.turbine={hot:{nacelle:[260,-270]},still:1,draw:TURB};
CTX.wind_turbine=['turbine','nacelle'];

// ---------- solárny článok v reze: fotón vyrazí elektrón, pole na P-N prechode ho pošle hore, drôtom tečie cez spotrebič späť ----------
// l = [slnečné svetlo, P-N prechod, prúd]; f = light | junction | circuit. Hýbu sa len fotóny, elektróny a diery.
PRO.solar=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),EN=LN.length>0,DUR=N(d._dur)||9,X0=110,X1=690,YT=200,YN=246,YJ=272,YB=400,FX=[180,310,440,570],NPR=24,PER=5.2;
const zf=Math.min(S.w/900,S.h/(WIDE?680:600))*.98,FULL=[440,WIDE?290:262,zf*1.12],FV={light:[390,150,zf*1.45],junction:[400,292,zf*2],circuit:[690,300,zf*1.55]},ORD=['light','junction','circuit'],KF=cams(d,FULL,FV,ORD,DUR);
const CIRC=track([[180,170],[770,170],[770,440],[640,440],[640,414]]),PH='#ffd84a',EL='#8fd4ff',HO='#ff8a6a';
const PR=[...Array(NPR)].map((_,i)=>{const xa=150+HS(i,61)*500,ya=300+HS(i,62)*78,xf=FX.reduce((b,q)=>Math.abs(q-xa)<Math.abs(b-xa)?q:b,FX[0]);return {xa,ya,xf,o:(i+HS(i,63)*.6)/NPR}});
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1.12)/.22);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(60,-120,20,60,-120,760);g.addColorStop(0,'rgba(255,216,74,.2)');g.addColorStop(1,'rgba(255,216,74,0)');x.fillStyle=g;x.fillRect(-200,-320,1300,1100)}
// lúče slnka dopadajú šikmo na článok
x.save();x.globalCompositeOperation='lighter';for(let j=0;j<5;j++){const bx=150+j*118,g=x.createLinearGradient(0,-260,0,YT);g.addColorStop(0,'rgba(255,216,74,0)');g.addColorStop(1,`rgba(255,216,74,${(.1+.03*Math.sin(t*1.3+j)).toFixed(3)})`);x.fillStyle=g;x.beginPath();x.moveTo(bx-166-24,-260);x.lineTo(bx-166+24,-260);x.lineTo(bx+30,YT);x.lineTo(bx-30,YT);x.closePath();x.fill()}x.restore();
// vodič: zberné prsty hore → spotrebič → zadný kontakt
x.strokeStyle='rgba(255,255,255,.9)';x.lineWidth=7;x.lineJoin='round';x.beginPath();FX.forEach(X=>{x.moveTo(X,190);x.lineTo(X,170)});CIRC.P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();
x.strokeStyle='#14171b';x.lineWidth=3;x.beginPath();FX.forEach(X=>{x.moveTo(X,190);x.lineTo(X,170)});CIRC.P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();
// vrstvy článku
x.fillStyle='#1b3a63';x.fillRect(X0,YT,X1-X0,YN-YT);{const g=x.createLinearGradient(0,YN,0,YJ);g.addColorStop(0,'#1b3a63');g.addColorStop(1,'#35264f');x.fillStyle=g;x.fillRect(X0,YN,X1-X0,YJ-YN)}x.fillStyle='#35264f';x.fillRect(X0,YJ,X1-X0,YB-YJ);
{const g=x.createLinearGradient(0,YB,0,YB+14);g.addColorStop(0,'#eef1f4');g.addColorStop(1,'#70757b');x.fillStyle=g;x.fillRect(X0,YB,X1-X0,14)}
x.strokeStyle='rgba(120,220,255,.9)';x.lineWidth=3;x.beginPath();x.moveTo(X0,YT);x.lineTo(X1,YT);x.stroke();
x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=1.5;x.setLineDash([8,7]);x.beginPath();x.moveTo(X0,(YN+YJ)/2);x.lineTo(X1,(YN+YJ)/2);x.stroke();x.setLineDash([]);
x.font=`900 15px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';for(let X=X0+22;X<X1-10;X+=44){x.fillStyle='rgba(255,170,150,.9)';x.fillText('+',X,YN+6);x.fillStyle='rgba(150,205,255,.9)';x.fillText('−',X+22,YJ-7)}
x.beginPath();x.rect(X0,YT,X1-X0,YB+14-YT);x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
FX.forEach(X=>{x.fillStyle='#d5dade';x.strokeStyle='#fff';x.lineWidth=1.5;x.beginPath();x.rect(X-12,188,24,12);x.fill();x.stroke()});
// spotrebič (žiarovka) svieti prúdom z článku
{const g=x.createRadialGradient(770,300,6,770,300,96);g.addColorStop(0,`rgba(255,216,74,${.5+.08*Math.sin(t*5)})`);g.addColorStop(1,'rgba(255,216,74,0)');x.fillStyle=g;x.fillRect(660,190,220,220)}
x.beginPath();x.arc(770,300,36,0,TAU);x.fillStyle='#14171b';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();x.strokeStyle=PH;x.lineWidth=3;x.lineJoin='round';x.beginPath();x.moveTo(770,264);[[758,284],[782,294],[758,306],[782,316],[770,336]].forEach(q=>x.lineTo(q[0],q[1]));x.stroke();
// elektróny tečú vodičom
for(let i=0;i<30;i++){const u=(t*.16+i/30)%1;dot(x,CIRC.at(u),4,EL,.95*cl(u/.03)*cl((1-u)/.03),true)}
// fotón → pár elektrón + diera; pole na prechode ich rozdelí (elektrón hore k prstom, diera dole k zadnému kontaktu)
PR.forEach(q=>{const u=((t/PER+q.o)%1+1)%1;
if(u<.25){const k=u/.25,sx=q.xa-.36*(q.ya+110),P=[sx+(q.xa-sx)*k,-110+(q.ya+110)*k];x.strokeStyle='rgba(255,216,74,.45)';x.lineWidth=3;x.lineCap='round';x.beginPath();x.moveTo(P[0]-9,P[1]-25);x.lineTo(P[0],P[1]);x.stroke();x.lineCap='butt';dot(x,P,5,PH,1,true);return}
if(u<.34){const k=(u-.25)/.09;x.beginPath();x.arc(q.xa,q.ya,6+22*k,0,TAU);x.strokeStyle=`rgba(255,216,74,${(.8*(1-k)).toFixed(3)})`;x.lineWidth=3;x.stroke()}
let e;if(u<.5)e=[q.xa,q.ya+(224-q.ya)*ez((u-.25)/.25)];else if(u<.72)e=[q.xa+(q.xf-q.xa)*ez((u-.5)/.22),224];else e=[q.xf,224-30*ez((u-.72)/.08)];
if(u<.8)dot(x,e,5.5,EL,cl((.8-u)/.03),true);
if(u<.66){const hy=q.ya+(394-q.ya)*ez((u-.25)/.37),al=cl((.66-u)/.04);x.globalAlpha=p*al;x.beginPath();x.arc(q.xa,hy,6,0,TAU);x.strokeStyle=HO;x.lineWidth=2.6;x.stroke();x.globalAlpha=p}});
// popisky
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],250,84,318,150);lead(S,LN[2],610,128,610,166);tag(S,LN[1],400,259,'center','#fff',20);
x.globalAlpha=p*sp;if(EN){tag(S,'N-TYPE SILICON',X0+96,YT+23,'center','#a9c6ee',16);tag(S,'P-TYPE SILICON',X0+96,YB-22,'center','#c4b2e6',16)}
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',3,ts-.35,A);
meter(S,'1000',EN?'W/m² SUN':'W/m²',A,a,fi>=0);badge(S,'220',EN?'W/m² OUT':'W/m²',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
CTX.solar=['roof','roof'];
}
