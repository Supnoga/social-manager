// Presné modely 29 – raketa s dvoma stupňami (bočný pohľad). Motory ťahajú nahor, po vyhorení spodný stupeň odpadne
// a horný pokračuje ďalej. Hýbe sa len raketa, plamene, odpadnutý stupeň a čiary rýchlosti.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const HULL='#dfe5ea',FIN='#9aa3ab',FIRE='#ff8a1e',NOZ='#4a525c';
PRO.rocket=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={nose:[450,190,zf*2.0],booster:[450,380,zf*1.9],nozzle:[450,420,zf*2.4]};
const ORD=['nose','booster','nozzle'],KF=cams(d,FULL,FV,ORD,DUR);
const SEP=3;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const sep=Math.max(0,t-SEP),fall=sep*sep*60,boost=t<SEP+2.5;
// čiary rýchlosti za raketou: smerujú dole
for(let k=0;k<10;k++){const yy=((k*70+t*260)%520)+40;x.beginPath();x.moveTo(300+k*30,yy);x.lineTo(300+k*30,yy+30);x.strokeStyle='rgba(255,255,255,.18)';x.lineWidth=3;x.stroke()}
// odpadnutý spodný stupeň: padá dole a mizne
if(fall<320){x.save();x.translate(0,fall);x.globalAlpha=p*sp*(1-zi)*(1-fall/320);
x.fillStyle=HULL;x.fillRect(415,300,70,120);x.fillStyle=FIN;x.beginPath();x.moveTo(415,380);x.lineTo(385,440);x.lineTo(415,440);x.fill();x.beginPath();x.moveTo(485,380);x.lineTo(515,440);x.lineTo(485,440);x.fill();x.restore();x.globalAlpha=p*sp*(1-zi)}
// horný stupeň: nos, trup, zadný valec
const up=Math.min(sep,4)*4;x.save();x.translate(0,-up);
x.beginPath();x.moveTo(450,110);x.lineTo(415,190);x.lineTo(485,190);x.closePath();x.fillStyle=HULL;x.fill();
x.fillStyle=HULL;x.fillRect(415,190,70,110);x.strokeStyle='#8a939c';x.lineWidth=2;x.beginPath();x.moveTo(415,250);x.lineTo(485,250);x.stroke();
if(boost){x.fillStyle=HULL;x.fillRect(415,300,70,120);x.fillStyle=FIN;x.beginPath();x.moveTo(415,380);x.lineTo(385,440);x.lineTo(415,440);x.fill();x.beginPath();x.moveTo(485,380);x.lineTo(515,440);x.lineTo(485,440);x.fill();}
x.fillStyle=NOZ;x.beginPath();x.moveTo(425,420);x.lineTo(475,420);x.lineTo(465,436);x.lineTo(435,436);x.closePath();x.fill();
// plamene: pulzujú, keď motory ťahajú
const fl=.75+.25*Math.sin(t*25);if(boost){x.beginPath();x.moveTo(435,436);x.lineTo(465,436);x.lineTo(450,436+90*fl);x.closePath();x.fillStyle=FIRE;x.globalAlpha=p*sp*(1-zi)*.9;x.fill();x.globalAlpha=p*sp*(1-zi)}
x.restore();
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,130,410,140);lead(S,LN[1]||'',760,380,520,380);lead(S,LN[2]||'',160,470,420,430);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'2 stages','ROCKET',A,a,fi>=0);
badge(S,'DROP EMPTY WEIGHT','THE TOP STAGE KEEPS GOING',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
