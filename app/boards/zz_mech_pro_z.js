// Presné modely 26 – pásový dopravník (bočný pohľad). Gumový pás ide v slučke cez dva valce; poháňa ho hnací valec.
// Hýbe sa pás, valce a náklad na páse. Náklad sa s pásom posúva bez šmyku.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const LOAD='#d9822b',BELT='#2a2f36',ST='#9aa3ab';
PRO.conveyor=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,330,zf*1.0],FV={rollers:[200,380,zf*1.8],load:[450,300,zf*1.8]};
const ORD=['rollers','load'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// rám
x.fillStyle='#1d2228';x.fillRect(150,470,600,30);x.strokeStyle='#3b4048';x.lineWidth=4;x.strokeRect(150,470,600,30);
// pás v slučke (hore a dole)
x.beginPath();x.moveTo(200,330);x.lineTo(700,330);x.arc(700,380,50,-Math.PI/2,Math.PI/2,false);x.lineTo(200,430);x.arc(200,380,50,Math.PI/2,3*Math.PI/2,false);x.closePath();
x.strokeStyle=BELT;x.lineWidth=14;x.stroke();x.strokeStyle='#4a525c';x.lineWidth=2;x.stroke();
// valce: točia sa, lúče ukazujú otáčanie
[[200,380],[700,380]].forEach(([cx,cy],i)=>{x.beginPath();x.arc(cx,cy,44,0,TAU);x.fillStyle=ST;x.fill();x.strokeStyle='#e6eaee';x.lineWidth=3;x.stroke();
for(let k=0;k<3;k++){const an=t*2.5*(i?1:1)+k*TAU/3;x.beginPath();x.moveTo(cx,cy);x.lineTo(cx+Math.cos(an)*40,cy+Math.sin(an)*40);x.strokeStyle='#4a525c';x.lineWidth=5;x.stroke()}
x.beginPath();x.arc(cx,cy,8,0,TAU);x.fillStyle='#1d2228';x.fill()});
x.fillStyle='#3b4048';x.fillRect(180,500,40,30);x.fillRect(680,500,40,30);
// náklad na hornej vetve: putuje spolu s pásom
for(let k=0;k<6;k++){const u=(k/6+t*.1)%1,bx=230+u*440;x.fillStyle=LOAD;x.fillRect(bx-30,298,60,32);x.strokeStyle='rgba(0,0,0,.35)';x.lineWidth=2;x.strokeRect(bx-30,298,60,32)}
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,140,200,336);lead(S,LN[1]||'',760,220,520,300);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'1.2 m/s','BELT SPEED',A,a,fi>=0);
badge(S,'BELT IN A LOOP','ROLLERS PULL THE BELT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
