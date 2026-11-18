// Presné modely 44 – vnútro mobilu (rez telefónom). Batéria, doska, kamera a indukčná cievka pre bezdrôtové nabíjanie. Medzi cievkou v telefóne a cievkou v nabíjačke prúdi striedavé magnetické pole. Hýbe sa len pole a prúd v cievke.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.phone=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={coil:[450,420,zf*2.0],battery:[450,300,zf*1.8],camera:[660,160,zf*2.2]};
const ORD=['coil','battery','camera'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.beginPath();x.roundRect(300,60,300,480,40);x.fillStyle="#1d2228";x.fill();x.strokeStyle="#8a939c";x.lineWidth=5;x.stroke();
x.fillStyle="#2a3138";x.fillRect(320,80,260,440);
x.fillStyle="#4a525c";x.fillRect(330,320,240,150);x.fillStyle="#7a8a3a";x.fillRect(340,330,220,130);
x.fillStyle="#2a3138";x.fillRect(340,100,120,30);x.beginPath();x.arc(440,115,8,0,TAU);x.fillStyle="#3b4048";x.fill();
x.beginPath();x.arc(560,140,18,0,TAU);x.fillStyle="#1d2228";x.fill();x.strokeStyle="#9aa3ab";x.lineWidth=3;x.stroke();
x.fillStyle="#d9822b";x.fillRect(340,200,160,40);
for(let r=0;r<6;r++){x.beginPath();x.ellipse(450,440,30+r*12,14+r*5,0,0,TAU);x.strokeStyle="#c8783a";x.lineWidth=3;x.stroke()}
for(let k=0;k<3;k++){const rr=(t*60+k*40)%120;x.beginPath();x.arc(450,440,40+rr,Math.PI*1.1,Math.PI*1.9);x.strokeStyle=rgba("#7fd0ff",.5*(1-rr/120)*p*sp*(1-zi));x.lineWidth=3;x.stroke()}
x.beginPath();x.rect(280,540,340,40);x.fillStyle="#3b4048";x.fill();
x.beginPath();x.arc(450,560,14,0,TAU);x.strokeStyle="#c9d0d6";x.lineWidth=3;x.stroke();
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",100,440,300,440);lead(S,LN[1]||"",100,300,340,330);lead(S,LN[2]||"",760,140,578,140);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"5 W","WIRELESS CHARGING",A,a,fi>=0);
badge(S,"MAGNETIC FIELD","NO CABLE, ONLY A COIL",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
