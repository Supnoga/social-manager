// Presné modely 34 – vrtuľník (bočný pohľad). Hlavný rotor tlačí vzduch dole a vztlak zdvíha stroj. Chvostový rotor
// vykompenzuje krútiaci moment. Hýbe sa len rotory a vzduch, ktorý rotor odhadzuje dole.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const BODY='#3b4048',BL='#c9d0d6',AIR='#7fd0ff';
PRO.rotor=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={rotor:[450,170,zf*1.9],tail:[740,260,zf*2.0],air:[450,380,zf*1.7]};
const ORD=['rotor','tail','air'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// trup a chvostová časť
x.beginPath();x.ellipse(430,330,170,80,0,0,TAU);x.fillStyle=BODY;x.fill();x.strokeStyle='#8a939c';x.lineWidth=4;x.stroke();
x.beginPath();x.moveTo(560,310);x.lineTo(740,280);x.lineTo(740,300);x.lineTo(560,350);x.closePath();x.fillStyle=BODY;x.fill();
x.beginPath();x.moveTo(430,160);x.lineTo(450,160);x.lineTo(450,200);x.lineTo(430,200);x.closePath();x.fillStyle='#6d7680';x.fill();
// hlavný rotor: z boku sa lopatky javia ako čiara, ktorá sa mení s uhlom
const a=t*9;x.beginPath();x.ellipse(450,160,300,14,0,0,TAU);x.strokeStyle=rgba(BL,.25);x.lineWidth=2;x.stroke();
for(let k=0;k<2;k++){const an=a+k*Math.PI;const ex=450+Math.cos(an)*300,ey=160+Math.sin(an)*14;x.beginPath();x.moveTo(450,160);x.lineTo(ex,ey);x.strokeStyle=BL;x.lineWidth=7;x.stroke()}
// chvostový rotor: v kruhu na konci chvosta
x.beginPath();x.arc(745,260,38,0,TAU);x.strokeStyle=rgba(BL,.3);x.lineWidth=2;x.stroke();
for(let k=0;k<2;k++){const an=a*1.7+k*Math.PI/2;x.beginPath();x.moveTo(745,260);x.lineTo(745+Math.cos(an)*36,260+Math.sin(an)*36);x.strokeStyle=BL;x.lineWidth=5;x.stroke()}
// vzduch odhadzovaný dole: vztlak
for(let k=0;k<14;k++){const q=(k/14+t*.5)%1,xx=450+(k%2?1:-1)*(40+200*q),yy=200+q*250;dot(x,[xx,yy],3,AIR,p*sp*(1-q)*(1-zi),false)}
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,100,450,150);lead(S,LN[1]||'',760,140,745,230);lead(S,LN[2]||'',160,460,300,380);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),ac=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'400 RPM','MAIN ROTOR',A,ac,fi>=0);
badge(S,'ROTOR PUSHES AIR DOWN','LIFT = AIR PUSHED DOWN',A,ac);
callout(S,d,t,A);x.globalAlpha=1}};
}
