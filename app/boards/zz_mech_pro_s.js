// Presné modely 19 – nervová bunka (neurón) a synapsia, bočný pohľad.
// Hýbe sa len to, čo sa hýbe naozaj: signály z dendritov sa zbierajú v tele bunky; keď napätie prekročí prah (-55 mV),
// vznikne vzruch (+40 mV) a preskakuje po axóne medzi myelínovými obalmi (od uzla k uzlu). Na konci sa z mechúrikov
// uvoľní neurotransmiter, prejde štrbinou synapsie a ďalší neurón sa rozsvieti. Napätie v meradle sa počíta z času cyklu.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),SIG='#7fd0ff';

PRO.neuron=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const SO=[200,300],RS=40,NODES=[252,326,400,474,548,612],BT=[640,300],N2=[820,300],CYC=3.6;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[480,300,zf*1.15],FV={dendrites:[150,300,zf*2],soma:[200,300,zf*2.4],axon:[430,300,zf*1.6],synapse:[680,300,zf*2.4],myelin:[400,300,zf*2]};
const ORD=['dendrites','soma','axon','synapse'],KF=cams(d,FULL,FV,ORD,DUR);
// dendrity: vetvy z tela bunky doľava (pevný tvar)
const DEN=[[-2.5,95],[-3.0,110],[2.6,100],[-2.0,80],[2.1,85]].map(([a,l],i)=>{const e=[SO[0]+Math.cos(a)*(RS+l),SO[1]+Math.sin(a)*(RS+l)];
return {a,s:[SO[0]+Math.cos(a)*RS*.9,SO[1]+Math.sin(a)*RS*.9],e,b:[[e,a-.5,34],[e,a+.45,30]]}});
const D2=[[-.8,50],[.8,50],[-.2,0]];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1.15)/.25);
const u=t%CYC;
// napätie tela bunky (mV): pokoj -70, vstupy ho dvíhajú k prahu -55, vzruch +40, krátky pokles pod pokoj
const mv=u<.9?-70+15*sm(u/.9):u<1.05?-55+95*sm((u-.9)/.15):u<1.4?40-120*sm((u-1.05)/.35):-80+10*sm((u-1.4)/.8);
const fire=cl((mv+55)/95);
// poloha vzruchu na axóne: od uzla k uzlu (skoky), 0.2 s na uzol
const ap=(u-1.0)/.18,ni=Math.floor(ap),nf=ap-ni;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// dendrity a vstupné signály
DEN.forEach((q,i)=>{x.strokeStyle='#5d636b';x.lineWidth=9;x.beginPath();x.moveTo(q.s[0],q.s[1]);x.lineTo(q.e[0],q.e[1]);x.stroke();
q.b.forEach(([o,a,l])=>{x.lineWidth=5;x.beginPath();x.moveTo(o[0],o[1]);x.lineTo(o[0]+Math.cos(a)*l,o[1]+Math.sin(a)*l);x.stroke()});
const k=(u-i*.12)/.55;if(k>0&&k<1){const px=q.e[0]+(q.s[0]-q.e[0])*k,py=q.e[1]+(q.s[1]-q.e[1])*k;dot(x,[px,py],6,SIG,p,true)}});
// telo bunky s jadrom: svieti podľa napätia
x.beginPath();x.arc(SO[0],SO[1],RS,0,TAU);x.fillStyle=mix('#2a2f35',A,fire*.8+cl((mv+70)/15)*.15);x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.arc(SO[0]-4,SO[1]-2,14,0,TAU);x.fillStyle='#1b1e22';x.fill();x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2;x.stroke();
// axón + myelínové obaly medzi uzlami
x.strokeStyle='#5d636b';x.lineWidth=8;x.beginPath();x.moveTo(SO[0]+RS-2,SO[1]);x.lineTo(BT[0]-14,BT[1]);x.stroke();
for(let i=0;i<NODES.length-1;i++){const a=NODES[i]+7,b=NODES[i+1]-7;x.beginPath();x.roundRect(a,SO[1]-15,b-a,30,14);x.fillStyle='#d8dde2';x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke();
x.strokeStyle='rgba(0,0,0,.18)';x.lineWidth=1.5;for(let k=a+10;k<b-6;k+=10){x.beginPath();x.moveTo(k,SO[1]-13);x.lineTo(k,SO[1]+13);x.stroke()}}
// vzruch: svieti uzol, kde práve je, a oblúk skoku k ďalšiemu
if(ni>=0&&ni<NODES.length){const nx=NODES[ni];dot(x,[nx,SO[1]],16,A,p*(1-nf*.6),true);dot(x,[nx,SO[1]],7,'#fff',p,true);
if(ni<NODES.length-1){const nx2=NODES[ni+1];x.strokeStyle=rgba(A,.8*(1-nf));x.lineWidth=3;x.setLineDash([6,6]);x.beginPath();x.moveTo(nx,SO[1]-18);x.quadraticCurveTo((nx+nx2)/2,SO[1]-46,nx2,SO[1]-18);x.stroke();x.setLineDash([])}}
// zakončenie s mechúrikmi a synaptická štrbina
x.beginPath();x.ellipse(BT[0],BT[1],26,34,0,0,TAU);x.fillStyle=mix('#2a2f35',A,cl(1-Math.abs(u-2.05)/.4)*.6);x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
const rel=cl((u-2.0)/.15);[[-8,-14],[6,-4],[-6,8],[8,14],[-10,0]].forEach(([dx,dy],i)=>{const vx=BT[0]+dx+rel*(14-dx*.3),vy=BT[1]+dy;
x.globalAlpha=p*(1-rel*.9);x.beginPath();x.arc(vx,vy,6,0,TAU);x.strokeStyle=A;x.lineWidth=2;x.stroke();x.globalAlpha=p});
for(let k=0;k<10;k++){const g=cl((u-2.05-k*.04)/.5);if(g<=0||g>=1)continue;const py=BT[1]-24+((k*37)%48),px=BT[0]+26+g*(N2[0]-110-BT[0]-26);dot(x,[px,py],4,A,p,true)}
// ďalší neurón: dendrit s receptormi pri štrbine
const on2=cl(1-Math.abs(u-2.9)/.5);
x.strokeStyle=mix('#5d636b',A,on2*.7);x.lineWidth=12;x.beginPath();x.moveTo(N2[0]-100,N2[1]);x.lineTo(N2[0]-RS,N2[1]);x.stroke();
x.beginPath();x.ellipse(N2[0]-104,N2[1],10,34,0,0,TAU);x.fillStyle=mix('#2a2f35',A,on2*.6);x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
for(let k=-2;k<=2;k++){x.fillStyle='#c9ced3';x.fillRect(N2[0]-116,N2[1]+k*13-3,6,6)}
D2.forEach(([a,l])=>{if(!l)return;x.strokeStyle='#5d636b';x.lineWidth=7;x.beginPath();x.moveTo(N2[0]+Math.cos(a)*RS,N2[1]+Math.sin(a)*RS);x.lineTo(N2[0]+Math.cos(a)*(RS+l),N2[1]+Math.sin(a)*(RS+l));x.stroke()});
x.beginPath();x.arc(N2[0],N2[1],RS,0,TAU);x.fillStyle=mix('#2a2f35',A,on2*.8);x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0],110,170,DEN[0].e[0]+10,DEN[0].e[1]+6);lead(S,LN[1],230,450,SO[0]+14,SO[1]+RS-6);lead(S,LN[2],440,180,NODES[2]+30,SO[1]-16);lead(S,LN[3],690,440,(BT[0]+N2[0]-104)/2,BT[1]+20);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(Math.round(mv))+' mV',FN=='synapse'?'BEFORE THE GAP':'MEMBRANE VOLTAGE',A,a,fi>=0);
badge(S,u>=.9&&u<2.0?'FIRING':u>=2.0&&u<3.2?'SYNAPSE':'RESTING',u>=.9&&u<2.0?'JUMPS NODE TO NODE':u>=2.0&&u<3.2?'CHEMICALS CROSS THE GAP':'SIGNALS ADD UP',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
