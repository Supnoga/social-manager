// Presné modely 21 – hurikán v reze (bočný pohľad cez oko).
// Hýbe sa len to, čo sa hýbe naozaj: teplý oceán (aspoň 26 °C) odparuje vodu, vlhký vzduch sa pri hladine sťahuje k stredu
// (čím bližšie k oku, tým rýchlejšie), v očnej stene stúpa, para kondenzuje na mraky a dážď a uvoľnené teplo ho ženie vyššie;
// hore vzduch odteká von. V oku vzduch pomaly klesá, preto je tam jasno. Kategória sa počíta z rýchlosti vetra (Saffir-Simpson).
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},WET='#7fd0ff';

PRO.hurricane=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,LF=String(d.f||'')=='landfall';
const CX=450,SEA=460,TOP=120,RE=46,RW=120,RO=410;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={ocean:[450,470,zf*1.8],eyewall:[560,300,zf*1.6],eye:[450,300,zf*2],outflow:[600,140,zf*1.7],landfall:[450,300,zf*1.0]};
const ORD=['ocean','eyewall','eye','outflow'],KF=cams(d,FULL,FV,ORD,DUR);
// mraky: kruhy pevného tvaru (očná stena vysoká, dažďové pásy nižšie)
const CL=[];[-1,1].forEach(sd=>{for(let y=TOP+30;y<=330;y+=26)for(let k=0;k<4;k++)CL.push([CX+sd*(RE+24+k*32),y+((k*7)%13),30+(k==1||k==2?8:0)]);
for(let k=0;k<11;k++)CL.push([CX+sd*(RE+20+k*30),TOP+6+(k%2)*8,26-k*1.2]);
[[250,350,30],[278,340,34],[306,352,28],[360,372,24],[384,366,26],[408,376,20]].forEach(([r,y,z])=>CL.push([CX+sd*r,y,z]))});
// dráha častice vzduchu: 0–1 k oku pri hladine, 1–2 hore očnou stenou, 2–3 von hore
const air=(s,sd)=>{if(s<1){const r=RW+(RO-RW)*(1-Math.pow(s,1.6));return [CX+sd*r,SEA-14,0]}if(s<2){const q=s-1;return [CX+sd*(RW-10+q*30),SEA-14-(SEA-14-TOP)*q,1]}const q=s-2;return [CX+sd*(RW+20+(RO-RW)*q),TOP-20+q*20,2]};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
// pri pevnine (landfall) slabne: bez teplej vody vietor klesá
const land=LF?Math.min(1,Math.max(0,(t-2)/(DUR-3))):0,wind=Math.round((255+8*Math.sin(t*.9))*(1-.6*land)),cat=wind>=252?5:wind>=209?4:wind>=178?3:wind>=154?2:wind>=119?1:0;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// oceán: teplý (pod búrkou), vlnky; pri landfall sa sprava vysúva pevnina
x.fillStyle=mix('#0e2a44','#7a3a10',.45*(1-land));x.fillRect(20,SEA,860,110);
x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;for(let k=0;k<16;k++){const wx=40+k*54+((t*30)%54);x.beginPath();x.arc(wx,SEA+8,10,Math.PI*1.1,Math.PI*1.9);x.stroke()}
if(LF){const lx=880-430*land;x.beginPath();x.moveTo(lx,SEA-6);x.lineTo(880,SEA-6);x.lineTo(880,570);x.lineTo(lx-20,570);x.closePath();x.fillStyle='#3d4a2e';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke()}
// odparovanie: para stúpa z teplej hladiny
for(let k=0;k<14;k++){const ph=(t*.6+k*.071)%1,ex=CX+(k%2?1:-1)*(RW+20+((k*53)%260));dot(x,[ex,SEA-ph*36],3,WET,p*(1-ph)*(1-land),true)}
// mraky
CL.forEach(([cx,cy,r])=>{x.beginPath();x.arc(cx,cy,r,0,TAU);x.fillStyle='#4a5058';x.fill()});
x.fillStyle='rgba(255,255,255,.07)';CL.forEach(([cx,cy,r])=>{x.beginPath();x.arc(cx-r*.2,cy-r*.35,r*.5,0,TAU);x.fill()});
// dážď pod očnou stenou
x.strokeStyle='rgba(127,208,255,.55)';x.lineWidth=2;for(let k=0;k<26;k++){const sd=k%2?1:-1,rx=CX+sd*(RE+14+((k*29)%110)),ph=(t*1.8+k*.13)%1,ry=330+ph*120;x.beginPath();x.moveTo(rx,ry);x.lineTo(rx-sd*4,ry+14);x.stroke()}
// oko: jasno, vzduch pomaly klesá
x.fillStyle='rgba(255,255,255,.04)';x.fillRect(CX-RE,TOP-30,RE*2,SEA-TOP+30);
for(let k=0;k<5;k++){const ph=(t*.25+k/5)%1;dot(x,[CX-24+k*12,TOP+ph*(SEA-TOP-40)],3,'#fff',p*.6,true)}
// prúdenie vzduchu (obe strany)
for(let k=0;k<18;k++)[-1,1].forEach(sd=>{const s=((t*.32+k/18)%1)*3,[ax,ay,ph]=air(s,sd);dot(x,[ax,ay],ph==1?5:4,ph==0?WET:ph==1?'#fff':'#aab2bb',p*(1-land*.5),true)});
// šípky smeru
const arr=(x0,y0,x1,y1)=>{const a=Math.atan2(y1-y0,x1-x0);x.strokeStyle=A;x.lineWidth=4;x.beginPath();x.moveTo(x0,y0);x.lineTo(x1,y1);x.stroke();x.fillStyle=A;x.beginPath();x.moveTo(x1,y1);x.lineTo(x1-Math.cos(a-.45)*16,y1-Math.sin(a-.45)*16);x.lineTo(x1-Math.cos(a+.45)*16,y1-Math.sin(a+.45)*16);x.closePath();x.fill()};
[-1,1].forEach(sd=>{arr(CX+sd*330,SEA-36,CX+sd*230,SEA-36);arr(CX+sd*(RW+8),330,CX+sd*(RW+8),230);arr(CX+sd*(RW+120),TOP-46,CX+sd*(RW+220),TOP-46)});
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0],160,530,CX-260,SEA+20);lead(S,LN[1],760,250,CX+RW+30,250);lead(S,LN[2],450,40,CX,TOP+20);lead(S,LN[3],780,60,CX+RW+200,TOP-30);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
if(FN=='ocean')meter(S,String(Math.round(29-3*land))+' °C','SEA SURFACE',A,a,fi>=0);else meter(S,String(wind)+' km/h','EYEWALL WIND',A,a,fi>=0);
badge(S,cat?'CATEGORY '+cat:'STORM',LF?'NO WARM WATER = WEAKER':'WARM WATER IS THE FUEL',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
