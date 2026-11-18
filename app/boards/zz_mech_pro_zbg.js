// Presné modely 43 – dopravné lietadlo (bočný pohľad). Krídlo nesie vztlak, motor ťahá dopredu a klapky sa pri pristávaní vysúvajú. Hýbe sa len vrtule/ventilátor motora, klapky a palivo v nádržiach krídla.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.airliner=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={hull:[450,300,zf*1.2],wing:[450,380,zf*1.8],engine:[460,370,zf*2.2]};
const ORD=['hull','wing','engine'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const fl=.5+.5*Math.sin(t*.4);
x.beginPath();x.moveTo(230,290);x.lineTo(640,290);x.quadraticCurveTo(700,300,700,320);x.lineTo(700,330);x.quadraticCurveTo(690,350,640,350);x.lineTo(230,350);x.quadraticCurveTo(190,340,190,320);x.quadraticCurveTo(200,290,230,290);x.closePath();
x.fillStyle="#dfe5ea";x.fill();x.strokeStyle="#8a939c";x.lineWidth=3;x.stroke();
for(let k=0;k<14;k++){x.beginPath();x.arc(260+k*30,306,7,0,TAU);x.fillStyle="#2a3138";x.fill()}
x.beginPath();x.moveTo(600,290);x.lineTo(700,150);x.lineTo(730,150);x.lineTo(680,290);x.closePath();x.fillStyle="#c9d0d6";x.fill();
x.beginPath();x.moveTo(330,350);x.lineTo(560,350);x.lineTo(470,430);x.lineTo(380,430);x.closePath();x.fillStyle="#9aa3ab";x.fill();
x.beginPath();x.moveTo(420,430+0);x.lineTo(470,430);x.lineTo(480,470);x.lineTo(430,470);x.closePath();x.fillStyle="#6d7680";x.fill();
x.fillStyle="#9aa3ab";x.fillRect(470,440,10,28);x.fillRect(430,440,10,28);
x.beginPath();x.ellipse(440,444,50,22,0,0,TAU);x.strokeStyle="#c9d0d6";x.lineWidth=3;x.stroke();
for(let k=0;k<4;k++){const an=t*16+k*TAU/4;x.beginPath();x.moveTo(440,444);x.lineTo(440+Math.cos(an)*44,444+Math.sin(an)*18);x.strokeStyle="rgba(255,255,255,.5)";x.lineWidth=3;x.stroke()}
x.beginPath();x.moveTo(380,430);x.lineTo(380+30*fl,450);x.strokeStyle="#c9d0d6";x.lineWidth=4;x.stroke();
for(let k=0;k<6;k++){dot(x,[400+k*10,430+4*Math.sin(t*3+k)],2,"#ffd27a",p*sp*(1-zi)*.7,false)}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",120,160,190,310);lead(S,LN[1]||"",780,300,700,340);lead(S,LN[2]||"",160,440,440,444);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"250 km/h","TAKE-OFF SPEED",A,a,fi>=0);
badge(S,"ENGINE PULLS FORWARD","WING MAKES THE LIFT",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
