// Presné modely 39 – procesor (čip zhora). Milióny tranzistorov sa zapínajú a vypínajú v rytme hodín. Jadrá sa striedajú
// pri výpočtoch a signály putujú po zberniciach. Hýbe sa len signály, aktívne jadro a hodinový signál.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.cpu=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={cores:[450,300,zf*1.8],bus:[450,300,zf*2.2],clock:[200,220,zf*2.4]};
const ORD=['cores','bus','clock'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const act=Math.floor(t*2)%4;
// kolíky po okrajoch
for(let k=0;k<12;k++){x.fillStyle="#9aa3ab";x.fillRect(262+k*31,132,10,22);x.fillRect(262+k*31,446,10,22)}
// čip
x.fillStyle="#1d2228";x.fillRect(250,160,400,280);x.strokeStyle="#8a939c";x.lineWidth=4;x.strokeRect(250,160,400,280);
// štyri jadrá
for(let c=0;c<4;c++){const cx=290+(c%2)*190,cy=200+Math.floor(c/2)*140;x.fillStyle=c===act?mix("#2a3138",A,.45):"#2a3138";x.fillRect(cx,cy,170,120);
for(let r=0;r<6;r++)for(let q=0;q<8;q++){x.fillStyle="rgba(255,255,255,.07)";x.fillRect(cx+8+q*20,cy+8+r*18,12,10)}}
// zbernice medzi jadrami
x.strokeStyle="#c9d0d6";x.lineWidth=3;x.beginPath();x.moveTo(460,200);x.lineTo(460,440);x.moveTo(290,340);x.lineTo(610,340);x.stroke();
for(let k=0;k<10;k++){const q=(k/10+t*.6)%1;dot(x,[460,200+240*q],3,A,p*sp*(1-zi),false);dot(x,[290+320*((k/10+t*.6*.7)%1),340],3,"#fff",p*sp*(1-zi),false)}
// hodiny: štvorcový signál
x.beginPath();for(let i=0;i<=100;i++){const xx=120+i*1.2,yy=(Math.floor((i/100*12+t*4))%2)?180:200;i?x.lineTo(xx,yy):x.moveTo(xx,yy)}x.strokeStyle=A;x.lineWidth=3;x.stroke();
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",760,140,640,260);lead(S,LN[1]||"",760,380,610,340);lead(S,LN[2]||"",120,300,180,230);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"3 GHz","CLOCK",A,a,fi>=0);
badge(S,"TRANSISTORS SWITCH ON AND OFF","CLOCK SETS THE PACE",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
