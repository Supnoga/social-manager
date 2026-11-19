// Presné modely 43 – vlak na koľajniciach: oceľové koleso s obrubou, 20 t na nápravu, podvozok a vozeň v pohybe, brzdenie s dlhou brzdnou dráhou.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.train=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={wheel:[290,380,zf*2.4],bogie:[450,360,zf*1.7],car:[450,250,zf*1.2]};
const ORD=['car','bogie','wheel'],KF=cams(d,FULL,FV,ORD,DUR);
const RAIL=420,R=40,WY=RAIL-R,WX=[260,340,560,640];
const wheel=(cx,ang)=>{x.beginPath();x.arc(cx,WY,R,0,Math.PI*2);x.fillStyle="#8a939c";x.fill();x.strokeStyle="#c9d0d6";x.lineWidth=3;x.stroke();
 x.strokeStyle="#5b636c";x.lineWidth=3;x.beginPath();for(let k=0;k<4;k++){const a=ang+k*Math.PI/2;x.moveTo(cx,WY);x.lineTo(cx+Math.cos(a)*(R-5),WY+Math.sin(a)*(R-5))}x.stroke();
 x.beginPath();x.arc(cx,WY,R-1,ang+Math.PI*.22,ang+Math.PI*.78);x.strokeStyle="#2b3038";x.lineWidth=9;x.stroke();
 x.beginPath();x.arc(cx,WY,8,0,Math.PI*2);x.fillStyle="#4b535c";x.fill()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;
const q=cl(t/DUR),u=cl((q-.3)/.7),pos=q<.3?q:.3+.7*(u-u*u/2),P=pos*1000,rot=P/R,cm=camAt(KF,t,.8);
const bp=cl((q-.28)/.08)*(1-cl((q-.98)/.02));
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
// zem a podvalky, ktoré sa posúvajú (vlak ide doprava, zem uteká doľava)
x.fillStyle="#20262c";x.fillRect(-200,RAIL+40,1300,200);
x.fillStyle="#5b4636";const off=(P%60);for(let sx=-120-off;sx<1000;sx+=60){x.fillRect(sx,RAIL+28,40,12)}
// koľajnica: hlava, stojina, pätka
x.fillStyle="#c9d0d6";x.fillRect(-200,RAIL,1300,12);x.fillStyle="#9aa3ab";x.fillRect(-200,RAIL+12,1300,10);x.fillStyle="#7b848d";x.fillRect(-200,RAIL+22,1300,6);
// vozeň: skriňa, okná, strecha
x.fillStyle="#3b7fc4";x.fillRect(170,190,560,150);x.fillStyle="#2a5d93";x.fillRect(170,190,560,10);
x.fillStyle="#1d2530";for(let k=0;k<7;k++)x.fillRect(190+k*78,215,60,44);
x.fillStyle="#2a5d93";x.fillRect(170,336,560,8);
// podvozky (rám), potom kolesá
x.fillStyle="#5a636d";x.fillRect(240,344,120,26);x.fillRect(540,344,120,26);
// brzdové čeľuste na kolesách
const brk=(cx)=>{x.fillStyle="#6b4a2b";x.fillRect(cx-6,WY-R-4+bp*4,14,8*bp+2)};
wheel(WX[0],rot);wheel(WX[1],rot);wheel(WX[2],rot);wheel(WX[3],rot);
brk(WX[0]+R-16);brk(WX[2]+R-16);
// zaťaženie 20 t zhora
x.globalAlpha=p*sp;x.beginPath();x.moveTo(450,120);x.lineTo(450,182);x.strokeStyle="#FF6B00";x.lineWidth=7;x.stroke();
x.beginPath();x.moveTo(430,172);x.lineTo(450,190);x.lineTo(470,172);x.fillStyle="#FF6B00";x.fill();
// brzdná dráha: prerušovaná čiara, ktorá sa predlžuje počas brzdenia
const bl=Math.min(780,700*u);if(q>.3){x.setLineDash([14,10]);x.beginPath();x.moveTo(110,505);x.lineTo(110+bl,505);x.strokeStyle="#FF6B00";x.lineWidth=4;x.stroke();x.setLineDash([])}
// zväčšený bod kontaktu (veľkosti mince) vpravo hore
x.beginPath();x.arc(800,118,50,0,Math.PI*2);x.fillStyle="#12171c";x.fill();x.strokeStyle="#c9d0d6";x.lineWidth=3;x.stroke();
x.beginPath();x.arc(800,118,20,0,Math.PI*2);x.fillStyle="#FF6B00";x.globalAlpha=p*sp*.85;x.fill();x.globalAlpha=p;
x.globalAlpha=p*sp*(1-ez((cm[2]/zf-1)/.25));
lead(S,LN[0]||"",120,100,FX,380);lead(S,LN[1]||"",780,330,600,362);lead(S,LN[2]||"",120,250,230,262);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"20 t","AXLE LOAD",A,a,fi>=0);
badge(S,"BRAKING","LONG STOPPING DISTANCE",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
