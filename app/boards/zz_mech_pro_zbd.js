// Presné modely 40 – padák (bočný pohľad). Vzduch tlačí na plochu kupoly nahor. Keď sila odporu vyrovná váhu, padák padá
// stálou rýchlosťou. Hýbe sa len vzduch, šnúry a záves s ľudským telom, ktorý sa kýve.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.parachute=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={canopy:[450,200,zf*1.8],lines:[450,320,zf*1.7],load:[450,440,zf*2.0]};
const ORD=['canopy','lines','load'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const bob=6*Math.sin(t*2),oy=bob;
// vzduch tlačí nahor: čiary prúdenia
for(let k=0;k<12;k++){const q=(k/12+t*.3)%1,xx=160+k*50;dot(x,[xx,520-q*380],3,A,p*sp*(1-zi)*.7,false)}
// kupola (plátno) s dielmi
x.beginPath();x.arc(450,200+oy,150,Math.PI,2*Math.PI);x.lineTo(450+150,200+oy);x.closePath();x.fillStyle="#e6eaee";x.fill();
x.strokeStyle="#8a939c";x.lineWidth=3;for(let k=1;k<6;k++){const an=Math.PI+k*Math.PI/6;x.beginPath();x.moveTo(450,200+oy);x.lineTo(450+Math.cos(an)*150,200+oy+Math.sin(an)*150);x.stroke()}
// šnúry od okraja k záveru
x.strokeStyle="#c9d0d6";x.lineWidth=2;for(let k=0;k<=6;k++){const an=Math.PI+k*Math.PI/6;x.beginPath();x.moveTo(450+Math.cos(an)*150,200+oy+Math.sin(an)*150);x.lineTo(450,440+oy);x.stroke()}
// záves s telom
x.fillStyle="#d9822b";x.fillRect(425,430+oy,50,50);x.strokeStyle="rgba(0,0,0,.35)";x.lineWidth=2;x.strokeRect(425,430+oy,50,50);
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",160,120,350,190+oy);lead(S,LN[1]||"",760,300,570,320+oy);lead(S,LN[2]||"",760,460,480,455+oy);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"5 m/s","FALL SPEED",A,a,fi>=0);
badge(S,"DRAG PUSHES UP","BIG CANOPY = SLOW FALL",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
