// Presné modely 4 – teplo: tepelné čerpadlo vzduch–voda v reze. Točí sa len ventilátor a kompresor; chladivo, vzduch a voda tečú.
// Farba chladiva ukazuje jeho stav: studená zmes → chladný plyn → horúci stlačený plyn → teplá kvapalina. Hustota bodiek sedí s hustotou látky.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,CTX,INTRO,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const COLD='#2f86ff',GASL='#a9dcff',HOT='#ff4a2e',WARM='#ffb040',WAT0='#4aa8e8',WAT1='#ff7a3a',AIR0='#d6ebff',AIR1='#5c9dff';
// lomená dráha: bod v pomere u (0..1) jej dĺžky
const track=P=>{const L=[0];for(let i=1;i<P.length;i++)L.push(L[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));const T=L[L.length-1];
return {P,T,at:u=>{const s=Math.max(0,Math.min(1,u))*T;let i=1;while(i<P.length-1&&L[i]<s)i++;const k=(s-L[i-1])/((L[i]-L[i-1])||1);return [P[i-1][0]+(P[i][0]-P[i-1][0])*k,P[i-1][1]+(P[i][1]-P[i-1][1])*k]}}};
const line=(x,P)=>{x.beginPath();P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]))};
// rúrka: steny (0 biele, 1 meď, 2 oceľ – s tieňom), tmavé vnútro zafarbené podľa stavu toho, čo v nej tečie
const pipe=(x,P,w,inner,m)=>{x.lineJoin='round';x.lineCap='butt';if(m){x.save();x.translate(5,8);line(x,P);x.strokeStyle='rgba(0,0,0,.36)';x.lineWidth=w+8;x.stroke();x.restore();line(x,P);x.strokeStyle=m==2?'#59606a':'#7c4622';x.lineWidth=w+9.5;x.stroke();line(x,P);x.strokeStyle=m==2?'#c6cdd4':'#e0a070';x.lineWidth=w+5.5;x.stroke()}
else{line(x,P);x.strokeStyle='rgba(255,255,255,.92)';x.lineWidth=w+6;x.stroke()}line(x,P);x.strokeStyle=inner;x.lineWidth=w;x.stroke()};
// teplota pri rúrke (veľkosť sa pri priblížení zväčšuje len mierne)
const pill=(S,s,px,py,col,k)=>{const x=S.x;x.save();x.translate(px,py);x.scale(k,k);x.font=`900 26px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';const w=x.measureText(s).width+26;x.fillStyle='rgba(0,0,0,.85)';x.beginPath();x.roundRect(-w/2,-20,w,40,12);x.fill();x.strokeStyle=col;x.lineWidth=2;x.stroke();x.fillStyle=col;x.fillText(s,0,1);x.restore()};

// ---------- tepelné čerpadlo: výparník berie teplo zo vzduchu, kompresor chladivo stlačí (zohreje), kondenzátor odovzdá teplo vode, ventil tlak uvoľní ----------
// l = [výparník, kompresor, kondenzátor, expanzný ventil]; f = evap | comp | cond | valve | run (celý okruh beží, kamera pomaly ide bližšie)
// Úroveň detailu (D.detail>=2 alebo d.det): medené rúrky, tiene, základ a stena domu, riadiaca doska s káblami, tlakomery, zberač, filter, priezor,
// skrutky, pružina lamely, výtlačný ventil, kondenzát na lamelách, cievka ventilu. Fyzika a zábery sú rovnaké ako v základnej úrovni.
PRO.heatpump=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),EN=LN.length>0,DUR=N(d._dur)||9,F=String(d.f||''),HI=(+D.detail||1)>=2||!!d.det,M=HI?1:0;
const zf=Math.min(S.w/955,S.h/(WIDE?700:610))*.98,FULL=[472,WIDE?322:286,zf],FV={evap:[222,330,zf*1.5],comp:[540,132,zf*2.2],cond:[806,305,zf*1.6],valve:[516,490,zf*2.5]},ORD=['evap','comp','cond','valve'],KF=cams(d,FULL,FV,ORD,DUR);
const CC=[540,150],RC=62,RH=80,EC=14,RR=RC-EC,WC=4.2,FAN=[150,330],FR=108,NP=HI?168:118,NA=HI?86:46,NW=HI?40:30,PR=HI?.86:1;
const COILP=[];for(let k=0;k<8;k++){const y=470-40*k;COILP.push(k%2?[246,y]:[304,y],k%2?[304,y]:[246,y])}
// úseky okruhu: T = ako dlho v nich chladivo je (pomalá kvapalina = husté bodky, rýchly plyn = riedke)
const SEG=[{p:track([[480,500],[350,500],[350,470],[304,470]]),T:.9,c:[COLD,COLD],r:[4.6,4.6],w:16,ic:'#081a33',mist:1},
{p:track(COILP),T:4.2,c:[COLD,GASL],r:[4.6,3.8],w:9,ic:'#0a1c30'},
{p:track([[304,190],[350,190],[350,40],[504,40],[504,99]]),T:1.1,c:[GASL,GASL],r:[3.8,3.8],w:16,ic:'#0d2233'},
{p:null,T:.5},
{p:track([[576,99],[576,40],[765,40],[765,170]]),T:1.6,c:[HOT,HOT],r:[4.2,4.2],w:16,ic:'#3a120c'},
{p:track([[765,170],[765,440]]),T:3,c:[HOT,WARM],r:[4.2,5.2],w:16,ic:'#33180a'},
{p:track([[765,440],[765,500],[560,500],[526,500]]),T:1.8,c:[WARM,WARM],r:[5.2,5.2],w:16,ic:'#33220a'},
{p:track([[526,500],[480,500]]),T:.25,c:[WARM,COLD],r:[3.6,4.6],w:0}],TT=SEG.reduce((s,g)=>s+g.T,0);
// teploty pri priblížení: [text, x, y, farba, pri ktorých záberoch] – každá len tam, kde jej nezavadzia nápis
const PILLS=[['7 °C',74,196,AIR0,['evap']],['3 °C',392,330,AIR1,['evap']],['0 °C',420,450,COLD,['evap','valve']],['5 °C',HI?416:404,HI?160:150,GASL,['evap','comp']],['60 °C',690,190,HOT,['comp','cond']],['33 °C',700,395,WARM,['cond']],['33 °C',645,HI?456:462,WARM,['valve']],['30 °C',HI?884:900,374,WAT0,['cond']],['35 °C',HI?884:900,236,WAT1,['cond']]];
const WP=track([[HI?1010:944,410],[815,410],[815,200],[HI?1010:944,200]]);
const blade=(ph,front)=>{const sy=Math.sin(ph),cz=Math.cos(ph);if((cz>=0)!=front)return;const cy=FAN[1]+sy*FR*.55,ry=Math.max(FR*.45*Math.abs(sy),20*Math.abs(cz))+4;x.beginPath();x.ellipse(FAN[0],cy,8+6*Math.abs(cz),ry,0,0,TAU);
if(HI){const g=x.createLinearGradient(FAN[0]-12,0,FAN[0]+14,0);g.addColorStop(0,front?'#e2e6ea':'#5a6068');g.addColorStop(1,front?'#7d848c':'#33373c');x.fillStyle=g}else x.fillStyle=front?'#aeb4bb':'#4a4f56';x.fill();x.strokeStyle=front?'#fff':'rgba(255,255,255,.5)';x.lineWidth=2;x.stroke();
if(HI&&front){x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=1.5;x.beginPath();x.moveTo(FAN[0]-3,cy-ry*.7);x.lineTo(FAN[0]-3,cy+ry*.7);x.stroke()}};
// tieň pod dielom (len detailná úroveň)
const shd=fn=>{if(!HI)return;x.save();x.translate(6,9);x.beginPath();fn();x.fillStyle='rgba(0,0,0,.42)';x.fill();x.restore()};
const nut=(X,Y,w,h,c)=>{x.beginPath();x.roundRect(X,Y,w,h,2.5);x.fillStyle=c||'#b9904e';x.fill();x.strokeStyle='rgba(255,255,255,.85)';x.lineWidth=1.5;x.stroke();x.strokeStyle='rgba(0,0,0,.35)';x.lineWidth=1.2;x.beginPath();if(w>h){x.moveTo(X+w/3,Y+1);x.lineTo(X+w/3,Y+h-1);x.moveTo(X+2*w/3,Y+1);x.lineTo(X+2*w/3,Y+h-1)}else{x.moveTo(X+1,Y+h/3);x.lineTo(X+w-1,Y+h/3);x.moveTo(X+1,Y+2*h/3);x.lineTo(X+w-1,Y+2*h/3)}x.stroke()};
// tlakomer na rúrke: stopka, ciferník, ručička (mierne sa chveje), tlak sa ukáže pri priblížení
const gauge=(X,col,fr,s,t,za)=>{const Y=88,a0=TAU*.375,an=a0+TAU*.75*(fr+.012*Math.sin(t*9+X));x.strokeStyle='#dc9a68';x.lineWidth=5;x.lineCap='butt';x.beginPath();x.moveTo(X,51);x.lineTo(X,Y-17);x.stroke();
x.beginPath();x.arc(X,Y,18,0,TAU);x.fillStyle='#0b0c0e';x.fill();x.strokeStyle='#e9edf0';x.lineWidth=3;x.stroke();x.strokeStyle=col;x.lineWidth=3;x.beginPath();x.arc(X,Y,12.5,a0,a0+TAU*.75);x.stroke();
x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=1.2;x.beginPath();for(let j=0;j<=6;j++){const a=a0+TAU*.75*j/6;x.moveTo(X+9*Math.cos(a),Y+9*Math.sin(a));x.lineTo(X+12.5*Math.cos(a),Y+12.5*Math.sin(a))}x.stroke();
x.strokeStyle='#fff';x.lineWidth=2.2;x.lineCap='round';x.beginPath();x.moveTo(X,Y);x.lineTo(X+11*Math.cos(an),Y+11*Math.sin(an));x.stroke();x.lineCap='butt';x.beginPath();x.arc(X,Y,2.6,0,TAU);x.fillStyle='#fff';x.fill();
if(za>.01){const g=x.globalAlpha;x.globalAlpha=g*za;x.font=`900 13px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';const w=x.measureText(s).width+12;x.fillStyle='rgba(0,0,0,.8)';x.beginPath();x.roundRect(X-w/2,Y+22,w,18,6);x.fill();x.fillStyle=col;x.fillText(s,X,Y+31.5);x.globalAlpha=g}};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-(F=='run'?1.16:1))/.22),pk=1/Math.pow(Math.max(1,cm[2]/zf),.6),th=-Math.PI/2-WC*t,q=(WC*t/TAU)%1,ex=CC[0]+EC*Math.cos(th),ey=CC[1]+EC*Math.sin(th);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);

if(HI){// prostredie: zem, betónový základ na gumených nohách, stena domu a teplo za ňou
x.fillStyle='rgba(255,255,255,.04)';x.fillRect(-200,598,1400,420);x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=2;x.beginPath();x.moveTo(-200,598);x.lineTo(1200,598);x.stroke();
x.fillStyle='rgba(255,255,255,.2)';for(let j=0;j<70;j++)x.fillRect(-190+HS(j,64)*1380,606+HS(j,65)*120,2.2,2.2);
{const g=x.createLinearGradient(950,0,1200,0);g.addColorStop(0,'rgba(255,138,58,.2)');g.addColorStop(1,'rgba(255,138,58,.03)');x.fillStyle=g;x.fillRect(950,-300,260,898)}
x.beginPath();x.rect(900,-300,50,898);x.fillStyle='#22252a';x.fill();x.strokeStyle='rgba(255,255,255,.13)';x.lineWidth=1.5;x.beginPath();for(let j=0;j<41;j++){const Y=-300+j*22;x.moveTo(900,Y);x.lineTo(950,Y);x.moveTo(j%2?916:934,Y);x.lineTo(j%2?916:934,Y+22)}x.stroke();
x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=3;x.beginPath();x.moveTo(900,-300);x.lineTo(900,598);x.moveTo(950,-300);x.lineTo(950,598);x.stroke();
x.beginPath();x.rect(6,574,884,24);x.fillStyle='#2a2d32';x.fill();x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.stroke();x.fillStyle='rgba(255,255,255,.22)';for(let j=0;j<46;j++)x.fillRect(12+HS(j,61)*870,577+HS(j,62)*17,2,2);
[[92,558],[790,558]].forEach(q=>{x.beginPath();x.roundRect(q[0],q[1],48,16,4);x.fillStyle='#08090a';x.fill();x.strokeStyle='rgba(255,255,255,.65)';x.lineWidth=2;x.stroke();x.strokeStyle='rgba(255,255,255,.3)';x.beginPath();x.moveTo(q[0]+3,q[1]+8);x.lineTo(q[0]+45,q[1]+8);x.stroke()});
x.save();x.translate(9,12);x.beginPath();x.roundRect(34,2,846,556,30);x.fillStyle='rgba(0,0,0,.5)';x.fill();x.restore()}
// skriňa vonkajšej jednotky, vľavo mriežka, ktorou ide vzduch
x.beginPath();x.roundRect(34,2,846,556,30);if(HI){const g=x.createLinearGradient(0,2,0,558);g.addColorStop(0,'#1c2026');g.addColorStop(.45,'#111316');g.addColorStop(1,'#0a0b0d');x.fillStyle=g}else x.fillStyle='#101215';x.fill();x.lineWidth=4;x.strokeStyle=HI?'rgba(255,255,255,.62)':'rgba(255,255,255,.5)';x.stroke();
if(HI){x.beginPath();x.roundRect(45,13,824,534,21);x.strokeStyle='rgba(255,255,255,.09)';x.lineWidth=2;x.stroke();
[[58,26],[856,26],[58,534],[856,534],[457,14],[457,546]].forEach(q=>{x.beginPath();x.arc(q[0],q[1],5.5,0,TAU);x.fillStyle='#4a5058';x.fill();x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=1.5;x.stroke();x.beginPath();x.moveTo(q[0]-3.2,q[1]-3.2);x.lineTo(q[0]+3.2,q[1]+3.2);x.stroke()})}
x.strokeStyle='#101215';x.lineWidth=8;x.beginPath();x.moveTo(34,216);x.lineTo(34,444);x.stroke();x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=3;for(let j=0;j<9;j++){const y=222+j*27;x.beginPath();x.moveTo(26,y+8);x.lineTo(44,y);x.stroke()}
if(!HI){// obeh okruhu (smer toku chladiva)
x.save();x.globalAlpha*=.16;x.strokeStyle='#fff';x.lineWidth=6;x.lineCap='round';x.beginPath();x.arc(500,316,50,-1.2,3.9);x.stroke();{const a=3.9,X=500+50*Math.cos(a),Y=316+50*Math.sin(a);x.beginPath();x.moveTo(X-16,Y+2);x.lineTo(X+2,Y-4);x.lineTo(X+4,Y+15);x.stroke()}x.restore()}
else{// riadiaca doska: káble ku kompresoru, ventilátoru a ventilu
x.lineJoin='round';x.lineCap='butt';[[[470,245],[470,284]],[[548,340],[576,340],[576,546],[196,546],[196,352]],[[576,448],[540,448]]].forEach((P,i)=>{line(x,P);x.strokeStyle='rgba(0,0,0,.5)';x.lineWidth=5;x.stroke();line(x,P);x.strokeStyle=i?'rgba(255,214,150,.55)':rgba(A,.8);x.lineWidth=2.2;x.stroke()});
shd(()=>x.roundRect(452,282,96,68,6));x.beginPath();x.roundRect(452,282,96,68,6);x.fillStyle='#0c3324';x.fill();x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=2.5;x.stroke();
x.strokeStyle='rgba(120,235,170,.38)';x.lineWidth=1.4;x.beginPath();[[[462,340],[462,318],[484,318]],[[516,312],[538,312],[538,292]],[[500,330],[500,342],[530,342]],[[470,292],[484,306]],[[516,322],[540,322],[540,340]]].forEach(P=>P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])));x.stroke();
x.fillStyle='#07080a';x.fillRect(484,302,32,28);x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=1.2;x.strokeRect(484,302,32,28);x.beginPath();for(let j=0;j<5;j++){x.moveTo(488+j*6,298);x.lineTo(488+j*6,302);x.moveTo(488+j*6,330);x.lineTo(488+j*6,334)}x.stroke();
[[468,330],[534,300]].forEach(q=>{x.beginPath();x.arc(q[0],q[1],6.5,0,TAU);x.fillStyle='#2c3035';x.fill();x.strokeStyle='rgba(255,255,255,.6)';x.stroke()});
dot(x,[462,292],3,'#58ff8a',Math.sin(t*5.2)>-.2?1:.25,true);dot(x,[474,292],3,A,.9,true)}
// ventilátor zboku: lopatky za nábojom, motor, lopatky pred nábojom
x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(112,FAN[1]-FR-10);x.lineTo(206,FAN[1]-FR-10);x.moveTo(112,FAN[1]+FR+10);x.lineTo(206,FAN[1]+FR+10);x.stroke();
if(HI){x.lineCap='round';x.beginPath();x.moveTo(112,FAN[1]-FR-10);x.quadraticCurveTo(98,FAN[1]-FR-10,94,FAN[1]-FR-24);x.moveTo(112,FAN[1]+FR+10);x.quadraticCurveTo(98,FAN[1]+FR+10,94,FAN[1]+FR+24);x.stroke();x.lineCap='butt';
x.fillStyle='rgba(255,255,255,.6)';for(let j=0;j<=14;j++){x.beginPath();x.arc(86,FAN[1]-FR+j*FR/7,2,0,TAU);x.fill()}}
x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=3;x.beginPath();x.moveTo(190,FAN[1]-FR-10);x.lineTo(190,FAN[1]+FR+10);x.stroke();
for(let b=0;b<3;b++)blade(t*5.5+b*TAU/3,false);
shd(()=>x.roundRect(FAN[0]+6,FAN[1]-22,52,44,6));
x.beginPath();x.roundRect(FAN[0]+6,FAN[1]-22,52,44,6);if(HI){const g=x.createLinearGradient(0,FAN[1]-22,0,FAN[1]+22);g.addColorStop(0,'#666c74');g.addColorStop(.5,'#3a3f45');g.addColorStop(1,'#1e2125');x.fillStyle=g}else x.fillStyle='#3a3f45';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
if(HI){x.strokeStyle='rgba(255,255,255,.3)';x.lineWidth=1.5;x.beginPath();for(let j=0;j<5;j++){x.moveTo(FAN[0]+18,FAN[1]-14+j*7);x.lineTo(FAN[0]+52,FAN[1]-14+j*7)}x.stroke()}
x.beginPath();x.roundRect(FAN[0]-12,FAN[1]-15,24,30,6);x.fillStyle='#8a9097';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
for(let b=0;b<3;b++)blade(t*5.5+b*TAU/3,true);
// vzduch: prejde výparníkom a odovzdá mu teplo (vychádza chladnejší)
for(let i=0;i<NA;i++){const u=(t*.34*(.8+.4*HS(i,21))+HS(i,22))%1,X=-40+u*480,Y=FAN[1]+(HS(i,23)-.5)*2*(FR-6)+Math.sin(t*1.7+i)*4,k=cl((X-232)/86),al=cl(u/.08)*cl(1-(X-345)/90)*.85;
if(HI&&al>.02){const g=x.globalAlpha;x.globalAlpha=g*al*.4;x.strokeStyle=mix(AIR0,AIR1,k);x.lineWidth=2;x.lineCap='round';x.beginPath();x.moveTo(X-13,Y);x.lineTo(X,Y);x.stroke();x.lineCap='butt';x.globalAlpha=g}
dot(x,[X,Y],HI?2.6:3.2,mix(AIR0,AIR1,k),al,false)}
// výparník: lamely a had rúrky
shd(()=>x.rect(230,166,90,328));
x.beginPath();x.rect(230,166,90,328);x.fillStyle='rgba(18,22,28,.72)';x.fill();x.strokeStyle=HI?'rgba(214,226,238,.3)':'rgba(255,255,255,.22)';x.lineWidth=HI?1.2:1.5;x.beginPath();for(let X=236;X<318;X+=HI?3.9:6.3){x.moveTo(X,168);x.lineTo(X,492)}x.stroke();x.beginPath();x.rect(230,166,90,328);x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=3;x.stroke();
if(HI){[158,494].forEach(Y=>{x.beginPath();x.rect(225,Y,100,8);x.fillStyle='#50565e';x.fill();x.strokeStyle='rgba(255,255,255,.85)';x.lineWidth=1.8;x.stroke()});
// vanička a odtok kondenzátu
x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=2.5;x.lineJoin='round';x.beginPath();x.moveTo(218,510);x.lineTo(223,524);x.lineTo(327,524);x.lineTo(332,510);x.stroke();x.fillStyle='rgba(120,190,255,.5)';x.fillRect(225,518,100,5);
x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=6;x.beginPath();x.moveTo(236,525);x.lineTo(236,566);x.stroke();x.strokeStyle='#0c2238';x.lineWidth=3;x.stroke()}
pipe(x,COILP,SEG[1].w,SEG[1].ic,M);
if(HI){const g=x.createLinearGradient(0,470,0,190);g.addColorStop(0,rgba(COLD,.3));g.addColorStop(.6,rgba(COLD,.05));g.addColorStop(1,rgba(COLD,0));line(x,COILP);x.strokeStyle=g;x.lineWidth=9;x.stroke()}
// kompresor: skriňa s vodidlom lamely
shd(()=>x.arc(CC[0],CC[1],RH,0,TAU));
x.beginPath();x.roundRect(CC[0]-17,CC[1]-RH-(HI?54:30),34,HI?70:46,5);x.fillStyle='#2c3035';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.beginPath();x.arc(CC[0],CC[1],RH,0,TAU);if(HI){const g=x.createRadialGradient(CC[0]-34,CC[1]-44,10,CC[0],CC[1],RH);g.addColorStop(0,'#5a6068');g.addColorStop(1,'#1d2024');x.fillStyle=g}else x.fillStyle='#2c3035';x.fill();hatch(x,()=>x.arc(CC[0],CC[1],RH,0,TAU));x.beginPath();x.arc(CC[0],CC[1],RH,0,TAU);x.strokeStyle='#fff';x.lineWidth=5;x.stroke();
if(HI)for(let k=0;k<10;k++){const a=TAU*(k+.5)/10,c=Math.cos(a),s=Math.sin(a);if(s<-.55)continue;const X=CC[0]+71*c,Y=CC[1]+71*s;if(Math.hypot(X-470,Y-224)<28)continue;x.beginPath();for(let j=0;j<6;j++){const b=a+j*TAU/6;j?x.lineTo(X+6*Math.cos(b),Y+6*Math.sin(b)):x.moveTo(X+6*Math.cos(b),Y+6*Math.sin(b))}x.closePath();x.fillStyle='#8a9097';x.fill();x.strokeStyle='rgba(255,255,255,.85)';x.lineWidth=1.3;x.stroke();x.beginPath();x.arc(X,Y,2.4,0,TAU);x.fillStyle='#2c3035';x.fill()}
// doskový výmenník (kondenzátor): chladivo dole, voda oproti nemu hore
if(HI){x.beginPath();x.roundRect(727,162,126,286,14);x.fillStyle='rgba(58,62,68,.55)';x.fill();x.setLineDash([7,5]);x.strokeStyle='rgba(255,255,255,.3)';x.lineWidth=1.5;x.stroke();x.setLineDash([])}
shd(()=>x.roundRect(735,170,110,270,10));
x.beginPath();x.roundRect(735,170,110,270,10);x.fillStyle='#16191d';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
// rúrky
[0,2,4,6].forEach(j=>pipe(x,SEG[j].p.P,SEG[j].w,SEG[j].ic,M));
{const g=x.createLinearGradient(0,170,0,440);g.addColorStop(0,'#3a120c');g.addColorStop(1,'#33220a');pipe(x,SEG[5].p.P,16,g,M)}
{const g=x.createLinearGradient(0,410,0,200);g.addColorStop(0,'#0a2033');g.addColorStop(1,'#3a1a0c');pipe(x,WP.P,16,g,HI?2:0)}
if(HI){// kvapalina vypĺňa rúrku, plyn nie
x.lineCap='butt';x.lineJoin='round';line(x,SEG[6].p.P);x.strokeStyle=rgba(WARM,.24);x.lineWidth=16;x.stroke();line(x,SEG[0].p.P);x.strokeStyle=rgba(COLD,.22);x.stroke();
{const g=x.createLinearGradient(0,170,0,440);g.addColorStop(0,rgba(WARM,0));g.addColorStop(.45,rgba(WARM,.05));g.addColorStop(1,rgba(WARM,.26));line(x,SEG[5].p.P);x.strokeStyle=g;x.stroke()}
{const g=x.createLinearGradient(0,410,0,200);g.addColorStop(0,rgba(WAT0,.26));g.addColorStop(1,rgba(WAT1,.26));line(x,WP.P);x.strokeStyle=g;x.stroke()}
// lisovaný vzor dosiek
x.strokeStyle='rgba(255,255,255,.1)';x.lineWidth=1.5;x.beginPath();for(let j=0;j<15;j++){const Y=180+j*17.4;x.moveTo(741,Y+10);x.lineTo(763,Y);x.lineTo(783,Y+10);x.moveTo(797,Y);x.lineTo(817,Y+10);x.lineTo(839,Y)}x.stroke();
// zberač kvapaliny pred kompresorom (do kompresora smie ísť len plyn)
shd(()=>x.roundRect(331,74,38,92,17));x.beginPath();x.roundRect(331,74,38,92,17);x.fillStyle='rgba(30,36,44,.93)';x.fill();x.save();x.clip();x.fillStyle=rgba(COLD,.42);x.fillRect(331,146+1.5*Math.sin(t*2.1),38,22);x.restore();x.beginPath();x.roundRect(331,74,38,92,17);x.strokeStyle='#e9edf0';x.lineWidth=2.8;x.stroke();x.strokeStyle='rgba(255,255,255,.3)';x.lineWidth=2;x.beginPath();x.moveTo(338,90);x.lineTo(338,140);x.stroke();
// filter (sušič) a priezor na kvapalinovej rúrke
shd(()=>x.roundRect(662,486,64,28,12));x.beginPath();x.roundRect(662,486,64,28,12);x.fillStyle='rgba(44,50,58,.9)';x.fill();x.save();x.clip();x.strokeStyle='rgba(255,255,255,.2)';x.lineWidth=1.2;x.beginPath();for(let X=650;X<740;X+=6){x.moveTo(X,486);x.lineTo(X+28,514);x.moveTo(X+28,486);x.lineTo(X,514)}x.stroke();x.restore();x.beginPath();x.roundRect(662,486,64,28,12);x.strokeStyle='#e9edf0';x.lineWidth=2.8;x.stroke();
x.beginPath();x.arc(610,500,16,0,TAU);x.fillStyle='#1a1408';x.fill();x.fillStyle=rgba(WARM,.3);x.fill()}
x.strokeStyle='rgba(255,255,255,.85)';x.lineWidth=2.5;x.lineJoin='round';x.beginPath();for(let j=0;j<=28;j++){const Y=180+j*9;j?x.lineTo(790+(j%2?5:-5),Y):x.moveTo(785,Y)}x.stroke();
// teplo prechádza cez dosku z chladiva do vody
for(let j=0;j<12;j++){const u=(t*.9+HS(j,7))%1;dot(x,[772+u*36,188+j*21.5],2.6,'#ffb46a',Math.sin(Math.PI*u)*.9,false)}
// expanzný ventil: ihla zužuje priechod, za ním tlak aj teplota prudko klesnú
shd(()=>x.roundRect(480,466,80,68,8));
x.beginPath();x.roundRect(480,466,80,68,8);if(HI){const g=x.createLinearGradient(480,466,560,534);g.addColorStop(0,'#50565e');g.addColorStop(1,'#1d2024');x.fillStyle=g}else x.fillStyle='#2c3035';x.fill();hatch(x,()=>x.roundRect(480,466,80,68,8));x.beginPath();x.roundRect(480,466,80,68,8);x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.beginPath();[[560,492],[532,492],[524,498],[516,498],[494,492],[480,492],[480,508],[494,508],[516,502],[524,502],[532,508],[560,508]].forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.closePath();x.fillStyle='#06080a';x.fill();x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=1.5;x.stroke();
x.beginPath();x.roundRect(500,430,40,36,6);x.fillStyle='#3a3f45';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
if(HI){x.strokeStyle='#dc9a68';x.lineWidth=1.8;x.beginPath();for(let Y=436;Y<462;Y+=3.6){x.moveTo(504,Y);x.lineTo(513,Y);x.moveTo(527,Y);x.lineTo(536,Y)}x.stroke()}
{const ny=HI?1.1*Math.sin(t*.9):0;x.beginPath();x.moveTo(514,462);x.lineTo(526,462);x.lineTo(526,486+ny);x.lineTo(520,499+ny);x.lineTo(514,486+ny);x.closePath();x.fillStyle='#d5dade';x.fill();x.strokeStyle='#fff';x.lineWidth=1.5;x.stroke()}
// kompresor (valivý piest): valec, sacia komora rastie, stláčaná sa zmenšuje a hreje
x.beginPath();x.arc(CC[0],CC[1],RC,0,TAU);x.fillStyle='#06080a';x.fill();
x.beginPath();x.moveTo(CC[0],CC[1]);x.arc(CC[0],CC[1],RC,-Math.PI/2,-Math.PI/2-TAU*q,true);x.closePath();x.fillStyle=rgba(GASL,.5);x.fill();
x.beginPath();x.moveTo(CC[0],CC[1]);x.arc(CC[0],CC[1],RC,-Math.PI/2-TAU*q,-Math.PI/2-TAU,true);x.closePath();x.fillStyle=mix(GASL,HOT,Math.pow(q,1.4),.72);x.fill();
x.beginPath();x.arc(CC[0],CC[1],RC,0,TAU);x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
{const g=x.createRadialGradient(ex-14,ey-16,6,ex,ey,RR);g.addColorStop(0,HI?'#b4bac0':'#8d9399');g.addColorStop(1,'#2a2d31');x.beginPath();x.arc(ex,ey,RR,0,TAU);x.fillStyle=g;x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke()}
if(HI){x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;x.beginPath();x.arc(ex,ey,RR-6,-2.6,-1.2);x.stroke()}
x.beginPath();x.arc(ex,ey,30,0,TAU);x.fillStyle='#3a3f45';x.fill();x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.stroke();
x.strokeStyle=A;x.lineWidth=7;x.lineCap='round';x.beginPath();x.moveTo(CC[0],CC[1]);x.lineTo(CC[0]+26*Math.cos(th),CC[1]+26*Math.sin(th));x.stroke();x.lineCap='butt';
x.beginPath();x.arc(CC[0],CC[1],12,0,TAU);x.fillStyle='#e6e9ec';x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke();
{const cu=-EC*Math.sin(th),rt=cu+Math.sqrt(RR*RR-EC*EC+cu*cu),Y=CC[1]-rt;x.beginPath();x.rect(CC[0]-7,Y-46,14,46);x.fillStyle='#cfd4d9';x.fill();x.strokeStyle='#fff';x.lineWidth=1.5;x.stroke();
if(HI){const y0=22,y1=Y-46,n=7;x.strokeStyle='#e6e9ec';x.lineWidth=2;x.lineJoin='round';x.beginPath();x.moveTo(CC[0],y0-3);x.lineTo(CC[0],y0);for(let j=0;j<n;j++)x.lineTo(CC[0]+(j%2?9:-9),y0+(y1-y0)*(j+.5)/n);x.lineTo(CC[0],y1);x.stroke()}}
// elektrina poháňa len kompresor
{const X=CC[0]-70,Y=CC[1]+74,g=.5+.5*Math.sin(t*6);x.beginPath();x.arc(X,Y,21,0,TAU);x.fillStyle='rgba(0,0,0,.85)';x.fill();x.strokeStyle=rgba(A,.6+.4*g);x.lineWidth=3;x.stroke();x.beginPath();[[3,-14],[-8,2],[-1,2],[-4,14],[8,-3],[1,-3]].forEach((q,i)=>i?x.lineTo(X+q[0],Y+q[1]):x.moveTo(X+q[0],Y+q[1]));x.closePath();x.fillStyle=A;x.fill()}
if(HI){// prúd v kábli ku kompresoru, jemná hmla za ihlou, kondenzát na lamelách a kvapky do vaničky
for(let j=0;j<3;j++){const u=(t*1.6+j/3)%1;dot(x,[470,284-u*39],2.4,A,Math.sin(Math.PI*u),true)}
for(let j=0;j<18;j++){const u=(t*2.3*(.7+.6*HS(j,73))+HS(j,71))%1;dot(x,[515-u*64,500+(HS(j,72)-.5)*15*Math.min(1,u*2.2)],1.5,'#d9f0ff',(1-u)*.85,false)}
for(let j=0;j<20;j++){const X=236+Math.floor(HS(j,41)*21)*3.9,Y=172+((t*(9+16*HS(j,42))+HS(j,43)*318)%318);dot(x,[X,Y],2.3,'#e4f3ff',.9,false)}
for(let j=0;j<4;j++){const u=(t*.8+HS(j,44))%1;dot(x,[246+j*22,503+u*u*14],2.2,'#bfe2ff',cl((1-u)/.2)*.9,false)}
{const u=(t*.7)%1;dot(x,[236,566+u*u*8],2.2,'#bfe2ff',cl((1-u)/.3)*.9,false)}}
// chladivo
for(let i=0;i<NP;i++){let s=((t/TT+i/NP+HS(i,3)*.004)%1)*TT,j=0;while(j<SEG.length-1&&s>SEG[j].T){s-=SEG[j].T;j++}const g=SEG[j];if(!g.p)continue;const u=cl(s/g.T),P=g.p.at(j==7?u*u:u);
dot(x,[P[0]+(g.mist?(HS(i,5)-.5)*7:0),P[1]+(g.mist?(HS(i,6)-.5)*7:0)],(g.r[0]+(g.r[1]-g.r[0])*u)*PR,g.mist&&i%3==0?'#d9f0ff':mix(g.c[0],g.c[1],u),1,true)}
// voda do domu: vo výmenníku sa ohreje
for(let i=0;i<NW;i++){const u=(t/5.2+i/NW)%1,P=WP.at(u),k=cl((u*WP.T-(HI?195:129))/210);dot(x,P,4.4*PR,mix(WAT0,WAT1,k),cl(u/.04)*cl((1-u)/.04),true)}
if(HI){// armatúry pred chladivom: matice, objímky v stene, priezor, výtlačný ventil kompresora, tlakomery
nut(752,157,26,13);nut(752,440,26,13);nut(845,188,13,24,'#9aa2aa');nut(845,398,13,24,'#9aa2aa');nut(341,68,18,7);nut(341,165,18,7);nut(654,490,9,20);nut(725,490,9,20);nut(468,490,12,20);nut(560,490,12,20);
[200,410].forEach(Y=>{[896,946].forEach(X=>{x.beginPath();x.rect(X,Y-14,8,28);x.fillStyle='#3a3f45';x.fill();x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=1.5;x.stroke()})});
x.beginPath();x.arc(610,500,16,0,TAU);x.strokeStyle='#b9904e';x.lineWidth=5;x.stroke();x.beginPath();x.arc(610,500,18.5,0,TAU);x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=1.5;x.stroke();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=2.2;x.lineCap='round';x.beginPath();x.arc(610,500,10,-2.5,-1.5);x.stroke();
{const o=cl((q-.5)/.12)*cl((1-q)/.04)*.75;x.save();x.translate(567,100);x.rotate(-o);x.strokeStyle='#f2f4f6';x.lineWidth=3;x.beginPath();x.moveTo(0,0);x.lineTo(18,0);x.stroke();x.restore();x.beginPath();x.arc(567,100,2.6,0,TAU);x.fillStyle='#f2f4f6';x.fill()}x.lineCap='butt';
gauge(430,GASL,.3,'5 bar',t,zi);gauge(670,HOT,.74,'13 bar',t,zi)}
// popisky pri celkovom pohľade, teploty pri priblížení
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],128,482,232,468);lead(S,LN[1],652,258,596,206);lead(S,LN[2],650,330,735,330);lead(S,LN[3],440,406,494,468);tag(S,EN?'+3 kW FROM AIR':'+3 kW',154,148,'center',A,21);
PILLS.forEach(q=>{const w=Math.max(...q[4].map(k=>cl(1.5-Math.hypot(cm[0]-FV[k][0],cm[1]-FV[k][1])/120)));if(w>.01){x.globalAlpha=p*sp*zi*w;pill(S,q[0],q[1],q[2],q[3],pk)}});
x.restore();
// z 1 kW elektriny sú 4 kW tepla
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'1',EN?'kW IN':'kW',A,a,fi>=0);badge(S,d._first?(1+3*ez((t-.9)/2.4)).toFixed(1):'4.0',EN?'kW HEAT':'kW',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- úvod: dom s vonkajšou jednotkou (stojí; točí sa len ventilátor a prúdi vzduch) ----------
const HOUSE=(x,t,hot,A,pulse,pv)=>{const dim='rgba(255,255,255,.34)',on=hot=='unit';x.lineJoin='round';
x.beginPath();x.moveTo(190,0);x.lineTo(190,-150);x.lineTo(168,-150);x.lineTo(330,-264);x.lineTo(492,-150);x.lineTo(470,-150);x.lineTo(470,0);x.closePath();x.fillStyle='rgba(255,255,255,.045)';x.fill();
{const g=x.createRadialGradient(330,-64,10,330,-64,180);g.addColorStop(0,'rgba(255,138,58,.26)');g.addColorStop(1,'rgba(255,138,58,0)');x.fillStyle=g;x.fill()}x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.strokeStyle=dim;x.lineWidth=2.2;[222,384].forEach(X=>{x.strokeRect(X,-120,54,54);x.beginPath();x.moveTo(X+27,-120);x.lineTo(X+27,-66);x.moveTo(X,-93);x.lineTo(X+54,-93);x.stroke()});x.strokeRect(308,-86,44,86);
// solárne panely na streche (len vo videu o nich)
if(pv){const sun=hot=='roof';x.save();x.lineCap='round';x.strokeStyle=sun?A:dim;x.lineWidth=sun?9:5;if(sun){x.shadowColor=A;x.shadowBlur=16+10*pulse}x.beginPath();x.moveTo(356,-253);x.lineTo(462,-178);x.stroke();x.restore();
if(sun){for(let j=0;j<6;j++){const u=(t*.6+j/6)%1;x.fillStyle=`rgba(255,216,74,${(.9*Math.sin(Math.PI*u)).toFixed(3)})`;x.beginPath();x.arc(300+j*26+u*52,-420+u*150+j*9,3.5,0,TAU);x.fill()}x.beginPath();x.arc(409,-216,58+16*pulse,0,TAU);x.strokeStyle=rgba(A,.75*(1-pulse));x.lineWidth=3;x.stroke()}}
if(pv)return;
// teplá voda do podlahy
x.strokeStyle='rgba(255,138,58,.85)';x.lineWidth=3;x.beginPath();x.moveTo(130,-34);x.lineTo(204,-34);x.lineTo(204,-12);for(let X=204;X<452;X+=24){x.lineTo(X+12,-12);x.lineTo(X+12,-22);x.lineTo(X+24,-22);x.lineTo(X+24,-12)}x.stroke();
for(let j=0;j<5;j++){const u=(t*.45+j/5)%1;x.fillStyle=`rgba(255,160,90,${.8*Math.sin(Math.PI*u)})`;x.beginPath();x.arc(132+u*72,-34,3.5,0,TAU);x.fill()}
// vzduch k jednotke
for(let j=0;j<7;j++){const u=(t*.5+HS(j,31))%1;x.fillStyle=`rgba(190,225,255,${.75*Math.sin(Math.PI*u)})`;x.beginPath();x.arc(-40+u*78,-64+j*7.5,3,0,TAU);x.fill()}
// vonkajšia jednotka
x.strokeStyle=dim;x.lineWidth=3;x.beginPath();x.moveTo(52,-8);x.lineTo(52,0);x.moveTo(118,-8);x.lineTo(118,0);x.stroke();
x.beginPath();x.roundRect(40,-80,90,72,8);x.fillStyle=on?A:'rgba(255,255,255,.06)';x.strokeStyle=on?'#fff':dim;x.lineWidth=on?2.6:2;if(on){x.save();x.shadowColor=A;x.shadowBlur=18+10*pulse;x.fill();x.restore()}else x.fill();x.stroke();
x.beginPath();x.arc(85,-44,27,0,TAU);x.fillStyle='rgba(0,0,0,.55)';x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke();
x.lineWidth=5;x.lineCap='round';for(let b=0;b<3;b++){const a=t*6+b*TAU/3;x.beginPath();x.moveTo(85+5*Math.cos(a),-44+5*Math.sin(a));x.quadraticCurveTo(85+18*Math.cos(a+.5),-44+18*Math.sin(a+.5),85+23*Math.cos(a+.9),-44+23*Math.sin(a+.9));x.stroke()}x.lineCap='butt';
if(on){x.beginPath();x.arc(85,-44,58+16*pulse,0,TAU);x.strokeStyle=rgba(A,.75*(1-pulse));x.lineWidth=3;x.stroke()}};
INTRO.house={hot:{unit:[85,-44]},still:1,draw:HOUSE};
INTRO.roof={hot:{roof:[409,-216]},still:1,draw:(x,t,hot,A,pulse)=>HOUSE(x,t,hot,A,pulse,true)};
CTX.heatpump=['house','unit'];
}
