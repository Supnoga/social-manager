// Presné modely 45 – ulica v reze (kanalizácia). Vrstvy asfaltu, štrku a zeminy držia cestu, pod ňou je kanalizačné potrubie, do ktorého steká voda z vpusti a šachta umožňuje prístup. Hýbe sa len voda v potrubí a odtoková vpusť.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.sewer=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={layers:[450,300,zf*1.2],pipe:[450,440,zf*2.2],trap:[200,350,zf*2.0]};
const ORD=['layers','pipe','trap'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.fillRect(80,180,740,300);
x.fillStyle="#2a2f36";x.fillRect(80,180,740,40);x.fillStyle="#3b4048";x.fillRect(80,220,740,40);x.fillStyle="#5d4a2e";x.fillRect(80,260,740,80);
x.fillStyle="#1d2228";x.fillRect(80,340,740,140);
x.fillStyle="#3b4048";x.fillRect(380,180,20,50);x.fillStyle="#c9d0d6";x.fillRect(360,170,60,12);
x.beginPath();x.arc(450,440,80,0,TAU);x.fillStyle="#6d7680";x.fill();x.beginPath();x.arc(450,440,64,0,TAU);x.fillStyle="#1d2228";x.fill();
x.beginPath();x.moveTo(260,340);x.lineTo(260,300);x.lineTo(340,300);x.lineTo(340,340);x.strokeStyle="#6d7680";x.lineWidth=8;x.stroke();
for(let k=0;k<10;k++){const q=(k/10+t*.15)%1;dot(x,[440+Math.cos(q*TAU)*46,440+Math.sin(q*TAU)*46],3,"#7fd0ff",p*sp*(1-zi)*.8,false)}
for(let k=0;k<8;k++){const q=(k/8+t*.2)%1;dot(x,[270+q*60,300+q*40],3,"#7fd0ff",p*sp*(1-zi)*(1-q),false)}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",120,200,160,240);lead(S,LN[1]||"",740,420,520,440);lead(S,LN[2]||"",120,380,260,320);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"3 layers","ROAD LAYERS",A,a,fi>=0);
badge(S,"WATER FLOWS DOWNHILL","PIPE CARRIES IT AWAY",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
