// Presné modely 31 – rotačná vŕtačka (bočný pohľad). Motor točí vrták a zároveň ho tlačí do materiálu. Špirála odvádza triesky
// von z diery. Hýbe sa len vrták, triesky a materiál sa odlupuje, ako vŕtačka postupuje.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const BIT='#c9d0d6',BODY='#d9822b',MAT='#5d666f';
PRO.drill=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={motor:[450,200,zf*1.9],bit:[450,330,zf*2.2],chips:[560,380,zf*1.8]};
const ORD=['motor','bit','chips'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const u=Math.min(1,t/9),TIP=340+60*u;   // vrták postupuje do materiálu
// materiál: vrstvy, vyvŕtaná diera je tmavá
x.fillStyle=MAT;x.fillRect(250,340,400,160);x.fillStyle='#4a525c';x.fillRect(250,380,400,8);x.fillStyle='#3b4048';x.fillRect(250,440,400,8);
x.fillStyle='#0b0e11';x.fillRect(430,340,40,TIP-340);
// telo vŕtačky a skľučovadlo
x.fillStyle=BODY;x.fillRect(400,150,100,70);x.fillStyle='#3b4048';x.fillRect(430,220,40,30);
// vrták: špirála sa točí a odvádza triesky
x.save();x.beginPath();x.rect(440,250,20,TIP-250);x.clip();
x.beginPath();x.moveTo(440,250);x.lineTo(460,250);x.lineTo(460,TIP);x.lineTo(440,TIP);x.closePath();x.fillStyle=BIT;x.fill();
const ph=(t*6)%20;x.strokeStyle='#4a525c';x.lineWidth=3;for(let y=250-20+ph;y<TIP;y+=20){x.beginPath();x.moveTo(440,y);x.lineTo(460,y+10);x.stroke()}
x.restore();
x.beginPath();x.moveTo(440,TIP);x.lineTo(450,TIP+14);x.lineTo(460,TIP);x.closePath();x.fillStyle=BIT;x.fill();
// triesky: odlietajú hore z diery
for(let k=0;k<8;k++){const q=(k/8+t*.8)%1,cx=440+(k%2?1:-1)*(10+30*q),cy=TIP-q*50;dot(x,[cx,cy],3,'#e6eaee',p*sp*(1-zi)*(1-q),false)}
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,140,400,190);lead(S,LN[1]||'',760,250,460,300);lead(S,LN[2]||'',760,440,520,400);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'1500 RPM','DRILL SPEED',A,a,fi>=0);
badge(S,'ROTATION + PRESSURE','SPIRAL CARRIES THE DUST OUT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
