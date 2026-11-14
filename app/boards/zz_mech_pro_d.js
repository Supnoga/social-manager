// Presné modely 4 – teplo: tepelné čerpadlo vzduch–voda v reze. Točí sa len ventilátor a kompresor; chladivo, vzduch a voda tečú.
// Farba chladiva ukazuje jeho stav: studená zmes → chladný plyn → horúci stlačený plyn → teplá kvapalina. Hustota bodiek sedí s hustotou látky.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,CTX,INTRO,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const COLD='#2f86ff',GASL='#a9dcff',HOT='#ff4a2e',WARM='#ffb040',WAT0='#4aa8e8',WAT1='#ff7a3a',AIR0='#d6ebff',AIR1='#5c9dff';
// lomená dráha: bod v pomere u (0..1) jej dĺžky
const track=P=>{const L=[0];for(let i=1;i<P.length;i++)L.push(L[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));const T=L[L.length-1];
return {P,T,at:u=>{const s=Math.max(0,Math.min(1,u))*T;let i=1;while(i<P.length-1&&L[i]<s)i++;const k=(s-L[i-1])/((L[i]-L[i-1])||1);return [P[i-1][0]+(P[i][0]-P[i-1][0])*k,P[i-1][1]+(P[i][1]-P[i-1][1])*k]}}};
const line=(x,P)=>{x.beginPath();P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]))};
// rúrka: biele steny, tmavé vnútro zafarbené podľa stavu toho, čo v nej tečie
const pipe=(x,P,w,inner)=>{x.lineJoin='round';x.lineCap='butt';line(x,P);x.strokeStyle='rgba(255,255,255,.92)';x.lineWidth=w+6;x.stroke();line(x,P);x.strokeStyle=inner;x.lineWidth=w;x.stroke()};
// teplota pri rúrke (veľkosť sa pri priblížení zväčšuje len mierne)
const pill=(S,s,px,py,col,k)=>{const x=S.x;x.save();x.translate(px,py);x.scale(k,k);x.font=`900 26px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';const w=x.measureText(s).width+26;x.fillStyle='rgba(0,0,0,.85)';x.beginPath();x.roundRect(-w/2,-20,w,40,12);x.fill();x.strokeStyle=col;x.lineWidth=2;x.stroke();x.fillStyle=col;x.fillText(s,0,1);x.restore()};

// ---------- tepelné čerpadlo: výparník berie teplo zo vzduchu, kompresor chladivo stlačí (zohreje), kondenzátor odovzdá teplo vode, ventil tlak uvoľní ----------
// l = [výparník, kompresor, kondenzátor, expanzný ventil]; f = evap | comp | cond | valve | run (celý okruh beží, kamera pomaly ide bližšie)
PRO.heatpump=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),EN=LN.length>0,DUR=N(d._dur)||9,F=String(d.f||'');
const zf=Math.min(S.w/955,S.h/610)*.98,FULL=[472,286,zf],FV={evap:[222,330,zf*1.5],comp:[540,132,zf*2.2],cond:[806,305,zf*1.6],valve:[516,490,zf*2.5]},ORD=['evap','comp','cond','valve'],KF=cams(d,FULL,FV,ORD,DUR);
const CC=[540,150],RC=62,RH=80,EC=14,RR=RC-EC,WC=4.2,FAN=[150,330],FR=108,NP=118,NA=46,NW=30;
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
const PILLS=[['7 °C',74,196,AIR0,['evap']],['3 °C',392,330,AIR1,['evap']],['0 °C',420,450,COLD,['evap','valve']],['5 °C',404,150,GASL,['evap','comp']],['60 °C',690,190,HOT,['comp','cond']],['33 °C',700,395,WARM,['cond']],['33 °C',645,462,WARM,['valve']],['30 °C',900,374,WAT0,['cond']],['35 °C',900,236,WAT1,['cond']]];
const WP=track([[944,410],[815,410],[815,200],[944,200]]);
const blade=(ph,front)=>{const sy=Math.sin(ph),cz=Math.cos(ph);if((cz>=0)!=front)return;x.beginPath();x.ellipse(FAN[0],FAN[1]+sy*FR*.55,8+6*Math.abs(cz),Math.max(FR*.45*Math.abs(sy),20*Math.abs(cz))+4,0,0,TAU);x.fillStyle=front?'#aeb4bb':'#4a4f56';x.fill();x.strokeStyle=front?'#fff':'rgba(255,255,255,.5)';x.lineWidth=2;x.stroke()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-(F=='run'?1.16:1))/.22),pk=1/Math.pow(Math.max(1,cm[2]/zf),.6),th=-Math.PI/2-WC*t,q=(WC*t/TAU)%1,ex=CC[0]+EC*Math.cos(th),ey=CC[1]+EC*Math.sin(th);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(470,290,20,470,290,560);g.addColorStop(0,'rgba(86,118,160,.2)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(-140,-260,1240,1100)}
// skriňa vonkajšej jednotky, vľavo mriežka, ktorou ide vzduch
x.beginPath();x.roundRect(34,2,846,556,30);x.fillStyle='#101215';x.fill();x.lineWidth=4;x.strokeStyle='rgba(255,255,255,.5)';x.stroke();
x.strokeStyle='#101215';x.lineWidth=8;x.beginPath();x.moveTo(34,216);x.lineTo(34,444);x.stroke();x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=3;for(let j=0;j<9;j++){const y=222+j*27;x.beginPath();x.moveTo(26,y+8);x.lineTo(44,y);x.stroke()}
// obeh okruhu (smer toku chladiva)
x.save();x.globalAlpha*=.16;x.strokeStyle='#fff';x.lineWidth=6;x.lineCap='round';x.beginPath();x.arc(500,316,50,-1.2,3.9);x.stroke();{const a=3.9,X=500+50*Math.cos(a),Y=316+50*Math.sin(a);x.beginPath();x.moveTo(X-16,Y+2);x.lineTo(X+2,Y-4);x.lineTo(X+4,Y+15);x.stroke()}x.restore();
// ventilátor zboku: lopatky za nábojom, motor, lopatky pred nábojom
x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(112,FAN[1]-FR-10);x.lineTo(206,FAN[1]-FR-10);x.moveTo(112,FAN[1]+FR+10);x.lineTo(206,FAN[1]+FR+10);x.stroke();
x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=3;x.beginPath();x.moveTo(190,FAN[1]-FR-10);x.lineTo(190,FAN[1]+FR+10);x.stroke();
for(let b=0;b<3;b++)blade(t*5.5+b*TAU/3,false);
x.beginPath();x.roundRect(FAN[0]+6,FAN[1]-22,52,44,6);x.fillStyle='#3a3f45';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();x.beginPath();x.roundRect(FAN[0]-12,FAN[1]-15,24,30,6);x.fillStyle='#8a9097';x.fill();x.stroke();
for(let b=0;b<3;b++)blade(t*5.5+b*TAU/3,true);
// vzduch: prejde výparníkom a odovzdá mu teplo (vychádza chladnejší)
for(let i=0;i<NA;i++){const u=(t*.34*(.8+.4*HS(i,21))+HS(i,22))%1,X=-40+u*480,Y=FAN[1]+(HS(i,23)-.5)*2*(FR-6)+Math.sin(t*1.7+i)*4,k=cl((X-232)/86);dot(x,[X,Y],3.2,mix(AIR0,AIR1,k),cl(u/.08)*cl(1-(X-345)/90)*.85,false)}
// výparník: lamely a had rúrky
x.beginPath();x.rect(230,166,90,328);x.fillStyle='rgba(18,22,28,.72)';x.fill();x.strokeStyle='rgba(255,255,255,.22)';x.lineWidth=1.5;x.beginPath();for(let X=236;X<318;X+=6.3){x.moveTo(X,168);x.lineTo(X,492)}x.stroke();x.beginPath();x.rect(230,166,90,328);x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=3;x.stroke();
pipe(x,COILP,SEG[1].w,SEG[1].ic);
// kompresor: skriňa s vodidlom lamely
x.beginPath();x.roundRect(CC[0]-17,CC[1]-RH-30,34,46,5);x.fillStyle='#2c3035';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.beginPath();x.arc(CC[0],CC[1],RH,0,TAU);x.fillStyle='#2c3035';x.fill();hatch(x,()=>x.arc(CC[0],CC[1],RH,0,TAU));x.beginPath();x.arc(CC[0],CC[1],RH,0,TAU);x.strokeStyle='#fff';x.lineWidth=5;x.stroke();
// doskový výmenník (kondenzátor): chladivo dole, voda oproti nemu hore
x.beginPath();x.roundRect(735,170,110,270,10);x.fillStyle='#16191d';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
// rúrky
[0,2,4,6].forEach(j=>pipe(x,SEG[j].p.P,SEG[j].w,SEG[j].ic));
{const g=x.createLinearGradient(0,170,0,440);g.addColorStop(0,'#3a120c');g.addColorStop(1,'#33220a');pipe(x,SEG[5].p.P,16,g)}
{const g=x.createLinearGradient(0,410,0,200);g.addColorStop(0,'#0a2033');g.addColorStop(1,'#3a1a0c');pipe(x,WP.P,16,g)}
x.strokeStyle='rgba(255,255,255,.85)';x.lineWidth=2.5;x.lineJoin='round';x.beginPath();for(let j=0;j<=28;j++){const Y=180+j*9;j?x.lineTo(790+(j%2?5:-5),Y):x.moveTo(785,Y)}x.stroke();
// teplo prechádza cez dosku z chladiva do vody
for(let j=0;j<12;j++){const u=(t*.9+HS(j,7))%1;dot(x,[772+u*36,188+j*21.5],2.6,'#ffb46a',Math.sin(Math.PI*u)*.9,false)}
// expanzný ventil: ihla zužuje priechod, za ním tlak aj teplota prudko klesnú
x.beginPath();x.roundRect(480,466,80,68,8);x.fillStyle='#2c3035';x.fill();hatch(x,()=>x.roundRect(480,466,80,68,8));x.beginPath();x.roundRect(480,466,80,68,8);x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.beginPath();[[560,492],[532,492],[524,498],[516,498],[494,492],[480,492],[480,508],[494,508],[516,502],[524,502],[532,508],[560,508]].forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.closePath();x.fillStyle='#06080a';x.fill();x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=1.5;x.stroke();
x.beginPath();x.roundRect(500,430,40,36,6);x.fillStyle='#3a3f45';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.moveTo(514,462);x.lineTo(526,462);x.lineTo(526,486);x.lineTo(520,499);x.lineTo(514,486);x.closePath();x.fillStyle='#d5dade';x.fill();x.strokeStyle='#fff';x.lineWidth=1.5;x.stroke();
// kompresor (valivý piest): valec, sacia komora rastie, stláčaná sa zmenšuje a hreje
x.beginPath();x.arc(CC[0],CC[1],RC,0,TAU);x.fillStyle='#06080a';x.fill();
x.beginPath();x.moveTo(CC[0],CC[1]);x.arc(CC[0],CC[1],RC,-Math.PI/2,-Math.PI/2-TAU*q,true);x.closePath();x.fillStyle=rgba(GASL,.5);x.fill();
x.beginPath();x.moveTo(CC[0],CC[1]);x.arc(CC[0],CC[1],RC,-Math.PI/2-TAU*q,-Math.PI/2-TAU,true);x.closePath();x.fillStyle=mix(GASL,HOT,Math.pow(q,1.4),.72);x.fill();
x.beginPath();x.arc(CC[0],CC[1],RC,0,TAU);x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
{const g=x.createRadialGradient(ex-14,ey-16,6,ex,ey,RR);g.addColorStop(0,'#8d9399');g.addColorStop(1,'#2a2d31');x.beginPath();x.arc(ex,ey,RR,0,TAU);x.fillStyle=g;x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke()}
x.beginPath();x.arc(ex,ey,30,0,TAU);x.fillStyle='#3a3f45';x.fill();x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.stroke();
x.strokeStyle=A;x.lineWidth=7;x.lineCap='round';x.beginPath();x.moveTo(CC[0],CC[1]);x.lineTo(CC[0]+26*Math.cos(th),CC[1]+26*Math.sin(th));x.stroke();x.lineCap='butt';
x.beginPath();x.arc(CC[0],CC[1],12,0,TAU);x.fillStyle='#e6e9ec';x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke();
{const cu=-EC*Math.sin(th),rt=cu+Math.sqrt(RR*RR-EC*EC+cu*cu),Y=CC[1]-rt;x.beginPath();x.rect(CC[0]-7,Y-46,14,46);x.fillStyle='#cfd4d9';x.fill();x.strokeStyle='#fff';x.lineWidth=1.5;x.stroke()}
// elektrina poháňa len kompresor
{const X=CC[0]-70,Y=CC[1]+74,g=.5+.5*Math.sin(t*6);x.beginPath();x.arc(X,Y,21,0,TAU);x.fillStyle='rgba(0,0,0,.85)';x.fill();x.strokeStyle=rgba(A,.6+.4*g);x.lineWidth=3;x.stroke();x.beginPath();[[3,-14],[-8,2],[-1,2],[-4,14],[8,-3],[1,-3]].forEach((q,i)=>i?x.lineTo(X+q[0],Y+q[1]):x.moveTo(X+q[0],Y+q[1]));x.closePath();x.fillStyle=A;x.fill()}
// chladivo
for(let i=0;i<NP;i++){let s=((t/TT+i/NP+HS(i,3)*.004)%1)*TT,j=0;while(j<SEG.length-1&&s>SEG[j].T){s-=SEG[j].T;j++}const g=SEG[j];if(!g.p)continue;const u=cl(s/g.T),P=g.p.at(j==7?u*u:u);
dot(x,[P[0]+(g.mist?(HS(i,5)-.5)*7:0),P[1]+(g.mist?(HS(i,6)-.5)*7:0)],g.r[0]+(g.r[1]-g.r[0])*u,g.mist&&i%3==0?'#d9f0ff':mix(g.c[0],g.c[1],u),1,true)}
// voda do domu: vo výmenníku sa ohreje
for(let i=0;i<NW;i++){const u=(t/5.2+i/NW)%1,P=WP.at(u),k=cl((u*WP.T-129)/210);dot(x,P,4.4,mix(WAT0,WAT1,k),cl(u/.04)*cl((1-u)/.04),true)}
// popisky pri celkovom pohľade, teploty pri priblížení
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],196,530,262,494);lead(S,LN[1],652,258,596,206);lead(S,LN[2],650,330,735,330);lead(S,LN[3],440,406,494,468);tag(S,EN?'+3 kW FROM AIR':'+3 kW',154,148,'center',A,21);
PILLS.forEach(q=>{const w=Math.max(...q[4].map(k=>cl(1.5-Math.hypot(cm[0]-FV[k][0],cm[1]-FV[k][1])/120)));if(w>.01){x.globalAlpha=p*sp*zi*w;pill(S,q[0],q[1],q[2],q[3],pk)}});
x.restore();
// z 1 kW elektriny sú 4 kW tepla
const fi=ORD.indexOf(F),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&t>.35)stamp(S,fi,LN[fi]||'',4,t-.35,A);
meter(S,'1',EN?'kW IN':'kW',A,a,fi>=0);badge(S,d._first?(1+3*ez((t-.9)/2.4)).toFixed(1):'4.0',EN?'kW HEAT':'kW',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- úvod: dom s vonkajšou jednotkou (stojí; točí sa len ventilátor a prúdi vzduch) ----------
const HOUSE=(x,t,hot,A,pulse)=>{const dim='rgba(255,255,255,.34)',on=hot=='unit';x.lineJoin='round';
x.beginPath();x.moveTo(190,0);x.lineTo(190,-150);x.lineTo(168,-150);x.lineTo(330,-264);x.lineTo(492,-150);x.lineTo(470,-150);x.lineTo(470,0);x.closePath();x.fillStyle='rgba(255,255,255,.045)';x.fill();
{const g=x.createRadialGradient(330,-64,10,330,-64,180);g.addColorStop(0,'rgba(255,138,58,.26)');g.addColorStop(1,'rgba(255,138,58,0)');x.fillStyle=g;x.fill()}x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.strokeStyle=dim;x.lineWidth=2.2;[222,384].forEach(X=>{x.strokeRect(X,-120,54,54);x.beginPath();x.moveTo(X+27,-120);x.lineTo(X+27,-66);x.moveTo(X,-93);x.lineTo(X+54,-93);x.stroke()});x.strokeRect(308,-86,44,86);
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
CTX.heatpump=['house','unit'];
}
