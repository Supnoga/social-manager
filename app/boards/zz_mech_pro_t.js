// Presné modely 20 – kapacitný dotykový displej (mobil). Hore pohľad na mriežku elektród pod sklom, dole rez vrstvami.
// Hýbe sa len to, čo sa hýbe naozaj: prst si „požičia“ náboj z elektród pod sebou; čím bližšie stĺpec/riadok, tým väčší pokles
// (stĺpce grafov). Ovládač z nich vypočíta ťažisko = súradnice dotyku (číslo v meradle sa počíta z grafov). f=pinch: dva prsty.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};

PRO.touchscreen=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,PN=String(d.f||'')=='pinch';
const GX0=250,GX1=610,GY0=110,GY1=380,NC=9,NR=7,CX=[...Array(NC)].map((_,j)=>GX0+20+j*(GX1-GX0-40)/(NC-1)),RY=[...Array(NR)].map((_,i)=>GY0+20+i*(GY1-GY0-40)/(NR-1));
const LY=530;   // rez vrstvami
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[440,318,zf*1.15],FV={grid:[430,245,zf*1.6],finger:[430,245,zf*1.6],controller:[560,330,zf*1.7],glass:[430,530,zf*2.2],pinch:[430,245,zf*1.4]};
const ORD=['grid','finger','controller','glass'],KF=cams(d,FULL,FV,ORD,DUR);
const sig=(c,F)=>F.reduce((s,f)=>s+Math.exp(-(((c-f)/30)**2)),0);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1.15)/.25);
// prsty: jeden ide po krivke, pri pinch dva od seba a k sebe
const FG=PN?(r=>[[430-r,245-r*.5],[430+r,245+r*.5]])(50+60*(.5+.5*Math.sin(t*1.4))):[[430+125*Math.sin(t*.9),245+85*Math.sin(t*1.3+.6)]];
const SC=CX.map(c=>sig(c,FG.map(f=>f[0]))),SR=RY.map(r=>sig(r,FG.map(f=>f[1])));
const cx=CX.reduce((s,c,j)=>s+c*SC[j],0)/SC.reduce((a,b)=>a+b,0),cy=RY.reduce((s,r,i)=>s+r*SR[i],0)/SR.reduce((a,b)=>a+b,0);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// telefón
x.beginPath();x.roundRect(GX0-30,GY0-40,GX1-GX0+60,GY1-GY0+80,34);x.fillStyle='#14171b';x.fill();x.strokeStyle='#fff';x.lineWidth=3.5;x.stroke();
x.fillStyle='#0b0d10';x.fillRect(GX0,GY0,GX1-GX0,GY1-GY0);
// mriežka elektród: stĺpce (vysielajú) a riadky (prijímajú); svietia tam, kde prst berie náboj
RY.forEach((r,i)=>{x.strokeStyle=mix('#3a4048',A,Math.min(1,SR[i])*.9);x.lineWidth=5;x.beginPath();x.moveTo(GX0+6,r);x.lineTo(GX1-6,r);x.stroke()});
CX.forEach((c,j)=>{x.strokeStyle=mix('#4a5560','#7fd0ff',Math.min(1,SC[j])*.9);x.lineWidth=5;x.beginPath();x.moveTo(c,GY0+6);x.lineTo(c,GY1-6);x.stroke();
RY.forEach(r=>{x.fillStyle='#14171b';x.beginPath();x.arc(c,r,4,0,TAU);x.fill()})});
// prst (bruško prsta zhora, priesvitné, aby bolo vidno mriežku)
FG.forEach(f=>{x.beginPath();x.ellipse(f[0],f[1],30,38,0,0,TAU);x.fillStyle='rgba(232,190,160,.28)';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke()});
// grafy ovládača: pod telefónom stĺpce, vpravo riadky
CX.forEach((c,j)=>{const h=6+30*Math.min(1,SC[j]);x.fillStyle=mix('#3a4048','#7fd0ff',Math.min(1,SC[j]));x.fillRect(c-9,GY1+86-h,18,h)});
RY.forEach((r,i)=>{const w=8+46*Math.min(1,SR[i]);x.fillStyle=mix('#3a4048',A,Math.min(1,SR[i]));x.fillRect(GX1+38,r-8,w,16)});
x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.beginPath();x.moveTo(GX0,GY1+86);x.lineTo(GX1,GY1+86);x.moveTo(GX1+38,GY0);x.lineTo(GX1+38,GY1);x.stroke();
// vypočítaný bod dotyku (pri jednom prste ťažisko; pri dvoch vrcholy grafov)
const TP=PN?FG:[[cx,cy]];TP.forEach(q=>{x.strokeStyle=A;x.lineWidth=2;x.setLineDash([6,6]);x.beginPath();x.moveTo(q[0],GY0);x.lineTo(q[0],GY1);x.moveTo(GX0,q[1]);x.lineTo(GX1,q[1]);x.stroke();x.setLineDash([]);
x.beginPath();x.arc(q[0],q[1],10,0,TAU);x.strokeStyle=A;x.lineWidth=3;x.stroke()});
// rez vrstvami: sklo, elektródy, displej; prst a siločiary, ktoré si „ťahá“
const f0=FG[0][0];x.fillStyle='rgba(180,220,255,.25)';x.fillRect(GX0-30,LY,GX1-GX0+60,16);x.strokeStyle='#fff';x.lineWidth=2;x.strokeRect(GX0-30,LY,GX1-GX0+60,16);
CX.forEach((c,j)=>{x.fillStyle=mix('#4a5560','#7fd0ff',Math.min(1,SC[j]));x.fillRect(c-12,LY+18,24,5)});
for(let k=GX0-28;k<GX1+28;k+=12){x.fillStyle=['#c33','#3a3','#36c'][Math.floor((k-GX0)/12+99)%3];x.globalAlpha=p*.6;x.fillRect(k,LY+26,10,14)}x.globalAlpha=p;
x.beginPath();x.roundRect(f0-26,LY-58,52,56,[4,4,26,26]);x.fillStyle='#e8bea0';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
x.strokeStyle=rgba(A,.85);x.lineWidth=2;for(let k=-2;k<=2;k++){const ex=f0+k*22;x.beginPath();x.moveTo(ex,LY+18);x.quadraticCurveTo(ex+k*6,LY-6,f0+k*9,LY-2);x.stroke()}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0],150,90,GX0+6,RY[1]);lead(S,LN[1],150,300,FG[0][0]-28,FG[0][1]);lead(S,LN[2],760,90,GX1+60,RY[0]);lead(S,LN[3],760,560,GX1+20,LY+8);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
const px=Math.round((cx-GX0)/(GX1-GX0)*1080/10)*10,py=Math.round((cy-GY0)/(GY1-GY0)*2400/10)*10;
meter(S,PN?String(Math.round(Math.hypot(FG[1][0]-FG[0][0],FG[1][1]-FG[0][1])/(GX1-GX0)*1080))+' px':px+', '+py,PN?'FINGER GAP':'TOUCH AT X, Y',A,a,fi>=0);
badge(S,PN?'PINCH':'TOUCH',PN?'TWO PEAKS = TWO FINGERS':'FINGER STEALS CHARGE',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
