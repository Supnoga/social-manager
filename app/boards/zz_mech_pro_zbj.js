// Presné modely 46 – práčka (predný pohľad). Bubon sa otáča so zmenou smeru a cez prívod vteká voda, čerpadlo ju potom vyháňa von. Hýbe sa len bubon, voda a čerpadlo odtoku.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.washer=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={drum:[450,300,zf*1.8],drain:[450,500,zf*2.2],inlet:[160,160,zf*2.2]};
const ORD=['drum','drain','inlet'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const sp2=Math.sign(Math.sin(t*.6)||1)*(t*2.5);
x.fillStyle="#dfe5ea";x.fillRect(260,80,380,460);x.strokeStyle="#8a939c";x.lineWidth=4;x.strokeRect(260,80,380,460);
x.beginPath();x.arc(450,300,140,0,TAU);x.fillStyle="#2a2f36";x.fill();x.strokeStyle="#9aa3ab";x.lineWidth=6;x.stroke();
x.save();x.beginPath();x.arc(450,300,120,0,TAU);x.clip();
x.beginPath();x.arc(450,300,120,0,TAU);x.fillStyle="rgba(74,168,232,.35)";x.fill();
for(let k=0;k<8;k++){const an=sp2+k*TAU/8;x.beginPath();x.moveTo(450,300);x.lineTo(450+Math.cos(an)*120,300+Math.sin(an)*120);x.strokeStyle="#6d7680";x.lineWidth=6;x.stroke()}
x.restore();
x.beginPath();x.moveTo(160,160);x.lineTo(260,160);x.strokeStyle="#7fd0ff";x.lineWidth=8;x.stroke();
for(let k=0;k<6;k++){const q=(k/6+t*.4)%1;dot(x,[160+100*q,160],3,"#7fd0ff",p*sp*(1-zi)*(1-q),false)}
x.beginPath();x.arc(450,500,22,0,TAU);x.fillStyle="#3b4048";x.fill();x.beginPath();x.moveTo(450,520);x.lineTo(450,580);x.strokeStyle="#6d7680";x.lineWidth=8;x.stroke();
for(let k=0;k<5;k++){const q=(k/5+t*.5)%1;dot(x,[450,520+60*q],3,"#7fd0ff",p*sp*(1-zi)*(1-q),false)}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",740,220,600,300);lead(S,LN[1]||"",740,520,470,500);lead(S,LN[2]||"",100,160,160,160);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"40 °C","WATER TEMP",A,a,fi>=0);
badge(S,"DRUM SPINS BOTH WAYS","WATER IN, PUMP OUT",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
