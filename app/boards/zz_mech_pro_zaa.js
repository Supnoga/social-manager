// Presné modely 27 – pevná kladka (bočný pohľad). Lano prebieha cez kladku; ťahom dole sa bremeno zdvihne o rovnakú dĺžku.
// Kladka nezosilňuje silu, len mení smer ťahu. Hýbe sa lano, kladka a bremeno.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const ROPE='#c8783a',LOAD='#d9822b',ST='#9aa3ab';
PRO.pulley=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={wheel:[450,190,zf*2.2],rope:[450,270,zf*1.6],load:[390,320,zf*1.9]};
const ORD=['wheel','rope','load'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const u=.5+.5*Math.sin(t*.9),WX=450,WY=190,R=60;
// držiak
x.fillStyle='#3b4048';x.fillRect(360,120,180,22);x.fillRect(440,142,20,20);
// kladka: otáča sa, keď sa lano pohybuje
const ang=u*90/R*1.0;
x.beginPath();x.arc(WX,WY,R,0,TAU);x.fillStyle=ST;x.fill();x.strokeStyle='#e6eaee';x.lineWidth=4;x.stroke();
for(let k=0;k<4;k++){const an=ang+k*TAU/4;x.beginPath();x.moveTo(WX,WY);x.lineTo(WX+Math.cos(an)*R*.85,WY+Math.sin(an)*R*.85);x.strokeStyle='#4a525c';x.lineWidth=6;x.stroke()}
x.beginPath();x.arc(WX,WY,10,0,TAU);x.fillStyle='#1d2228';x.fill();
x.strokeStyle='#8a939c';x.lineWidth=2;x.beginPath();x.moveTo(WX-8,WY-R-12);x.lineTo(WX+8,WY-R-12);x.stroke();
// lano: ľavá strana drží bremeno, pravá strana ju ťahá dole
const yL=330-90*u,yR=240+90*u;
x.strokeStyle=ROPE;x.lineWidth=5;x.beginPath();x.moveTo(WX-R,WY);x.lineTo(WX-R,yL);x.moveTo(WX+R,WY);x.lineTo(WX+R,yR);x.stroke();
// bremeno (vľavo) a rukoväť ťahu (vpravo)
x.fillStyle=LOAD;x.fillRect(WX-R-30,yL,60,50);x.strokeStyle='rgba(0,0,0,.35)';x.lineWidth=2;x.strokeRect(WX-R-30,yL,60,50);
x.fillStyle='#e6eaee';x.fillRect(WX+R-10,yR,20,14);
dot(x,[WX+R,yR+30],4,A,p*sp*(1-zi),true);
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',150,200,WX-R-10,WY);lead(S,LN[1]||'',740,120,WX+R,(WY+yR)/2);lead(S,LN[2]||'',150,420,WX-R-30,yL+30);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'1 : 1','FORCE RATIO',A,a,fi>=0);
badge(S,'FIXED PULLEY','CHANGES DIRECTION, NOT FORCE',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
