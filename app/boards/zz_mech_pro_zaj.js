// Presné modely 36 – kyvadlo hodín (bočný pohľad). Závažie sa kýve okolo závesu; gravitácia ho vracia dole a zotrvačnosť
// ho nesie ďalej. Perióda závisí od dĺžky ramena, nie od hmotnosti závažia. Hýbe sa len ramie a závažie.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const ROD='#9aa3ab',BOB='#d9822b';
PRO.pendulum=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={pivot:[450,150,zf*2.2],rod:[450,300,zf*1.6],bob:[450,460,zf*1.9]};
const ORD=['pivot','rod','bob'],KF=cams(d,FULL,FV,ORD,DUR);
const PX=450,PY=150,LEN=300;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const th=.5*Math.sin(t*2.4),bx=PX+LEN*Math.sin(th),by=PY+LEN*Math.cos(th);
for(let k=-3;k<=3;k++){const an=Math.PI/2+k*.12;x.beginPath();x.moveTo(PX+Math.cos(an)*(LEN+10),PY+Math.sin(an)*(LEN+10));x.lineTo(PX+Math.cos(an)*(LEN+26),PY+Math.sin(an)*(LEN+26));x.strokeStyle='#8a939c';x.lineWidth=3;x.stroke()}
// stopa: záves na pevnej konzole
x.fillStyle='#3b4048';x.fillRect(400,100,100,30);
// dráha kyvu (bodkovaná)
x.beginPath();x.arc(PX,PY,LEN,Math.PI/2-.5,Math.PI/2+.5);x.strokeStyle='rgba(255,255,255,.15)';x.lineWidth=2;x.setLineDash([4,8]);x.stroke();x.setLineDash([]);
// rameno a závažie
x.beginPath();x.moveTo(PX,PY);x.lineTo(bx,by);x.strokeStyle=ROD;x.lineWidth=5;x.stroke();
x.beginPath();x.arc(bx,by,30,0,TAU);x.fillStyle=BOB;x.fill();x.strokeStyle='rgba(0,0,0,.35)';x.lineWidth=2;x.stroke();
x.beginPath();x.arc(PX,PY,8,0,TAU);x.fillStyle='#e6eaee';x.fill();
// gravitácia: šípka dole
x.beginPath();x.moveTo(600,380);x.lineTo(600,460);x.strokeStyle=A;x.lineWidth=4;x.stroke();x.fillStyle=A;x.beginPath();x.moveTo(600,470);x.lineTo(590,452);x.lineTo(610,452);x.fill();
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,140,400,150);lead(S,LN[1]||'',160,260,PX+LEN*.5*Math.sin(th),PY+LEN*.5*Math.cos(th));lead(S,LN[2]||'',740,460,bx+30,by);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'1 s','ONE SWING',A,a,fi>=0);
badge(S,'LENGTH SETS THE PERIOD','GRAVITY PULLS IT BACK',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
