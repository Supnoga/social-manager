// Presné modely 35 – klimatizácia split (vnútorná a vonkajšia jednotka). Chladivo kolesá v uzavretom okruhu: vnútri odoberá
// teplo z miestnosti a vonku ho vypúšťa. Kompresor stlačí plyn a ventilátor vonku odvádza teplo. Hýbe sa len chladivo,
// ventilátory a prúdenie vzduchu.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const UNIT='#dfe5ea',PIPE='#6d7680',COLD='#7fd0ff',WARM='#ff8a4a';
const LOOP=[[300,200],[300,260],[600,260],[600,330]];
const at=(pts,u)=>{const L=[];let tot=0;for(let i=1;i<pts.length;i++){const l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);L.push(l);tot+=l}let s=((u%1)+1)%1*tot;for(let i=1;i<pts.length;i++){if(s<=L[i-1]){const f=s/L[i-1];return[pts[i-1][0]+(pts[i][0]-pts[i-1][0])*f,pts[i-1][1]+(pts[i][1]-pts[i-1][1])*f]}s-=L[i-1]}return pts[pts.length-1]};
PRO.aircon=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={indoor:[240,170,zf*1.9],outdoor:[660,400,zf*1.8],pipe:[450,260,zf*1.7]};
const ORD=['indoor','outdoor','pipe'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// vnútorná jednotka na stene a vonkajšia jednotka
x.fillStyle=UNIT;x.fillRect(120,120,240,80);x.fillStyle='#8a939c';x.fillRect(150,186,180,12);
x.fillStyle='#2a2f36';x.fillRect(560,330,200,130);x.strokeStyle='#6d7680';x.lineWidth=3;x.strokeRect(560,330,200,130);
// ventilátor vonku: točí sa a odvádza teplo
x.beginPath();x.arc(660,396,44,0,TAU);x.strokeStyle='#8a939c';x.lineWidth=3;x.stroke();
for(let k=0;k<3;k++){const an=t*7+k*TAU/3;x.beginPath();x.moveTo(660,396);x.lineTo(660+Math.cos(an)*40,396+Math.sin(an)*40);x.strokeStyle='#c9d0d6';x.lineWidth=6;x.stroke()}
// potrubie s chladivom (slučka medzi jednotkami)
x.beginPath();x.moveTo(LOOP[0][0],LOOP[0][1]);for(let i=1;i<LOOP.length;i++)x.lineTo(LOOP[i][0],LOOP[i][1]);x.strokeStyle=PIPE;x.lineWidth=8;x.stroke();
for(let k=0;k<10;k++){const q=at(LOOP,k/10+t*.12);dot(x,q,3.5,A,p*sp*(1-zi),false)}
// vzduch: studený z vnútornej jednotky dole, teplý von z vonkajšej hore
for(let k=0;k<8;k++){const q=(k/8+t*.4)%1;dot(x,[300-q*60,200+q*120],3,COLD,p*sp*(1-q)*(1-zi),false);dot(x,[700+q*40,360-q*90],3,WARM,p*sp*(1-q)*(1-zi),false)}
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',120,300,260,300);lead(S,LN[1]||'',790,260,660,340);lead(S,LN[2]||'',450,120,450,260);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'24 °C','INSIDE ROOM',A,a,fi>=0);
badge(S,'HEAT MOVES, NOT CREATED','INSIDE COLD, OUTSIDE HOT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
