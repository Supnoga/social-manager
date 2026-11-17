// Presné modely 28 – páka (bočný pohľad). Páka sa otáča okolo opory. Dlhšie rameno na strane úsilia znamená menšiu silu
// potrebnú na zdvih bremena. Hýbe sa len páka a bremeno, ktoré s ňou ide hore a dole.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const LOAD='#d9822b',ST='#9aa3ab';
PRO.lever=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={load:[170,330,zf*1.9],effort:[730,330,zf*1.9],fulcrum:[450,380,zf*2.2]};
const ORD=['load','effort','fulcrum'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const th=.22*Math.sin(t*.9);
// opora (trojuholník) a podklad
x.beginPath();x.moveTo(450,380);x.lineTo(418,460);x.lineTo(482,460);x.closePath();x.fillStyle='#3b4048';x.fill();x.strokeStyle='#9aa3ab';x.lineWidth=3;x.stroke();
x.fillStyle='#2a2f36';x.fillRect(360,460,180,22);
// páka: otáča sa okolo opory
x.save();x.translate(450,380);x.rotate(th);
x.beginPath();x.moveTo(-300,0);x.lineTo(300,0);x.strokeStyle=ST;x.lineWidth=14;x.stroke();
// bremeno na ľavom konci (ide s pákou)
x.fillStyle=LOAD;x.fillRect(-330,-52,60,52);x.strokeStyle='rgba(0,0,0,.35)';x.lineWidth=2;x.strokeRect(-330,-52,60,52);
// šípka úsilia na pravom konci: tlačí dole
x.strokeStyle=A;x.lineWidth=5;x.beginPath();x.moveTo(270,-70);x.lineTo(270,-6);x.stroke();
x.fillStyle=A;x.beginPath();x.moveTo(270,-2);x.lineTo(256,-22);x.lineTo(284,-22);x.closePath();x.fill();
x.restore();
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,190,140,300);lead(S,LN[1]||'',760,190,730,300);lead(S,LN[2]||'',450,120,450,350);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'3 : 1','ARM RATIO',A,a,fi>=0);
badge(S,'LEVER','LONG ARM = LESS EFFORT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
