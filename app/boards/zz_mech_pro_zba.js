// Presné modely 37 – elektrický obvod (schéma so skutočným prúdom). Elektróny tečú len v uzavretom okruhu. Keď je spínač
// otvorený, prúd netečie a žiarovka nesvieti. Hýbe sa len elektróny a svetlo žiarovky.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.circuit=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={battery:[180,310,zf*2.0],switch:[450,220,zf*2.2],bulb:[720,310,zf*2.0]};
const ORD=['battery','switch','bulb'],KF=cams(d,FULL,FV,ORD,DUR);
const P=u=>{let s=((u%1)+1)%1*1440;if(s<540)return[180+s,220];s-=540;if(s<180)return[720,220+s];s-=180;if(s<540)return[720-s,400];s-=540;return[180,400-s]};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const on=(t%6)<3,lb=on?1:.08;
x.strokeStyle="#6d7680";x.lineWidth=6;x.beginPath();x.moveTo(180,220);x.lineTo(420,220);x.moveTo(480,220);x.lineTo(720,220);x.lineTo(720,400);x.lineTo(180,400);x.closePath();x.stroke();
x.fillStyle="#c9d0d6";x.fillRect(166,276,28,68);x.fillStyle="#2a2f36";x.fillRect(176,290,8,40);
x.beginPath();x.moveTo(420,220);x.lineTo(on?480:470,on?220:190);x.strokeStyle="#e6eaee";x.lineWidth=5;x.stroke();
x.beginPath();x.arc(720,310,26,0,TAU);x.fillStyle=mix("#2a2f36","#ffd27a",lb);x.fill();x.strokeStyle="#e6eaee";x.lineWidth=3;x.stroke();
if(on)for(let k=0;k<12;k++)dot(x,P(k/12+t*.25),3.5,A,p*sp*(1-zi),false);
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",120,130,180,250);lead(S,LN[1]||"",440,120,450,220);lead(S,LN[2]||"",780,120,720,290);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"9 V","BATTERY",A,a,fi>=0);
badge(S,"CLOSED LOOP = CURRENT","OPEN SWITCH = NO CURRENT",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
