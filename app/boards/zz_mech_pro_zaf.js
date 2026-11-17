// Presné modely 32 – generátor elektriny (rez). Turbína (tu len lopatky) točí hriadeľ a magnetický rotor sa otáča vnútri
// statora s cievkami. Magnetické pole pretína cievky, a tak sa v nich indukuje striedavé napätie, ktoré svieti žiarovku.
// Hýbe sa len lopatky, hriadeľ, rotor a prúd (striedavý, svetlo bliká v rytme).
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const CU='#c8783a',ST='#4a525c',NN='#e05050',SS='#50a0e0';
PRO.generator=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={turbine:[220,300,zf*1.9],stator:[450,300,zf*1.8],bulb:[760,300,zf*2.0]};
const ORD=['turbine','stator','bulb'],KF=cams(d,FULL,FV,ORD,DUR);
const CX=450,CY=300,RS=150;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const ang=t*1.8,emf=Math.sin(ang*2);
// stator: kruh s cievkami
x.beginPath();x.arc(CX,CY,RS+20,0,TAU);x.strokeStyle='#8a939c';x.lineWidth=6;x.stroke();
for(let k=0;k<12;k++){const a=k*TAU/12,rx=CX+Math.cos(a)*(RS+6),ry=CY+Math.sin(a)*(RS+6);x.save();x.translate(rx,ry);x.rotate(a+Math.PI/2);x.fillStyle=CU;x.fillRect(-9,-18,18,36);x.restore()}
// rotor: magnet s pólmi N a S, točí sa vo vnútri
x.save();x.translate(CX,CY);x.rotate(ang);
x.beginPath();x.moveTo(-110,0);x.lineTo(0,0);x.strokeStyle=SS;x.lineWidth=28;x.stroke();
x.beginPath();x.moveTo(0,0);x.lineTo(110,0);x.strokeStyle=NN;x.lineWidth=28;x.stroke();
x.restore();
// hriadeľ a lopatky turbíny vľavo
x.beginPath();x.moveTo(CX-RS-20,CY);x.lineTo(CX-40,CY);x.strokeStyle=ST;x.lineWidth=10;x.stroke();
x.beginPath();x.arc(220,CY,60,0,TAU);x.strokeStyle='#3b4048';x.lineWidth=2;x.stroke();
for(let k=0;k<5;k++){const an=t*2.2+k*TAU/5;x.save();x.translate(220,CY);x.rotate(an);x.fillStyle='#9aa3ab';x.fillRect(0,-8,56,16);x.restore()}
x.beginPath();x.arc(220,CY,12,0,TAU);x.fillStyle='#e6eaee';x.fill();
// vedenie a žiarovka vpravo: svieti podľa prúdu
x.beginPath();x.moveTo(CX+RS+20,CY-40);x.lineTo(740,CY-40);x.strokeStyle='#6d7680';x.lineWidth=4;x.stroke();
const lb=.25+.75*Math.abs(emf);x.beginPath();x.arc(760,CY,34,0,TAU);x.fillStyle=mix('#2a2f36','#ffd27a',lb);x.fill();x.strokeStyle='#e6eaee';x.lineWidth=3;x.stroke();
dot(x,[760,CY],6,'#ffd27a',p*sp*lb*(1-zi),true);
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',150,160,220,220);lead(S,LN[1]||'',440,120,CX+60,CY-100);lead(S,LN[2]||'',760,130,760,CY-40);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'50 Hz','ALTERNATING CURRENT',A,a,fi>=0);
badge(S,'MAGNETS SPIN, WIRES STAY','TURBINE TURNS THE SHAFT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
