// Presné modely 55–56 – ventilátor (lopatky, motor, prúd vzduchu) a vietor (tlak na stenu, podtlak na streche, víry za domom).
{
const K=window.KIT,PRO=K.PRO,{ez,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead}=K;
const N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.fan=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={blades:[450,300,zf*2.1],motor:[450,300,zf*2.2],air:[740,300,zf*1.8]};
const ORD=['blades','motor','air'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const rot=t*10;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.strokeStyle="#5a636d";x.lineWidth=14;x.beginPath();x.arc(450,300,160,0,Math.PI*2);x.stroke();
x.strokeStyle="#9aa3ab";x.lineWidth=3;for(let k=0;k<12;k++){const a=k*Math.PI/6;x.beginPath();x.moveTo(450+Math.cos(a)*150,300+Math.sin(a)*150);x.lineTo(450+Math.cos(a)*166,300+Math.sin(a)*166);x.stroke()}
x.fillStyle="#2a2f36";x.fillRect(120,285,40,30);x.fillRect(740,285,40,30);
x.fillStyle="#3b4048";x.beginPath();x.arc(450,300,46,0,Math.PI*2);x.fill();
x.fillStyle="#1d2530";x.beginPath();x.arc(450,300,22,0,Math.PI*2);x.fill();
x.save();x.translate(450,300);x.rotate(rot);for(let k=0;k<4;k++){x.rotate(Math.PI/2);x.beginPath();x.moveTo(40,0);x.quadraticCurveTo(110,-40,150,-10);x.lineTo(150,8);x.quadraticCurveTo(110,-18,40,14);x.closePath();x.fillStyle="#d9822b";x.fill()}x.restore();
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(120,190,255,.8)";x.lineWidth=3;for(let k=0;k<8;k++){const yy=170+k*35;const xx=((t*260+k*70)%420)-300;x.beginPath();x.moveTo(xx,yy);x.lineTo(xx+70,yy);x.stroke()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,330,300);lead(S,LN[1]||"",780,470,480,300);lead(S,LN[2]||"",780,160,640,200);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"1400 RPM","FAN",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.wind=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={windward:[300,300,zf*2.0],roof:[450,150,zf*2.0],leeward:[640,330,zf*2.0]};
const ORD=['windward','roof','leeward'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#7b848d";x.fillRect(-100,470,1100,130);
x.fillStyle="#e8ecef";x.fillRect(300,270,260,200);
x.fillStyle="#c9d0d6";x.beginPath();x.moveTo(280,270);x.lineTo(430,160);x.lineTo(580,270);x.closePath();x.fill();
x.fillStyle="#1d2530";for(let k=0;k<2;k++)x.fillRect(340+k*120,300,50,50);
x.globalAlpha=p*sp*(1-zi);
x.fillStyle="rgba(230,70,70,.35)";x.fillRect(300,270,20,200);
x.fillStyle="rgba(70,130,230,.35)";x.beginPath();x.moveTo(280,270);x.lineTo(430,160);x.lineTo(580,270);x.closePath();x.fill();
x.fillStyle="rgba(70,130,230,.3)";x.fillRect(560,270,20,200);
x.strokeStyle="rgba(190,220,255,.8)";x.lineWidth=3;for(let k=0;k<6;k++){const yy=190+k*45;const xx=((t*240+k*60)%700)-200;x.beginPath();x.moveTo(xx,yy);x.lineTo(xx+80,yy+6);x.stroke()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,380,300,380);lead(S,LN[1]||"",450,80,430,160);lead(S,LN[2]||"",780,380,620,380);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"WIND","PRESSURE",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};
}
