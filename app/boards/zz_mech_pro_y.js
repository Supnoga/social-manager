// Presné modely 25 – eskalátor (bočný pohľad). Schodíky sú pripevnené k reťazi, ktorú poháňa motor hore a ide v slučke.
// Hýbe sa len schodíky, reťaz a madlá; schodík vždy ostáva vodorovný.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const AX=150,AY=450,BX=760,BY=230,STEP='#c9d0d6',TRU='#5d666f';
PRO.escalator=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,330,zf*1.0],FV={steps:[400,340,zf*1.7],drive:[700,250,zf*2.0]};
const ORD=['steps','drive'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// podlažia a nosník
x.fillStyle='#2a2f36';x.fillRect(90,450,120,30);x.fillRect(690,200,130,30);
x.strokeStyle=TRU;x.lineWidth=12;x.beginPath();x.moveTo(AX,AY);x.lineTo(BX,BY);x.stroke();
// madlo (dvojitý pás nad schodíkmi)
x.strokeStyle='#2a2f36';x.lineWidth=12;x.beginPath();x.moveTo(AX,AY-72);x.lineTo(BX,BY-72);x.stroke();
x.strokeStyle='#e6eaee';x.lineWidth=3;x.beginPath();x.moveTo(AX,AY-78);x.lineTo(BX,BY-78);x.stroke();
// schodíky: putujú po reťazi (ich tvar ostáva vodorovný)
for(let k=0;k<14;k++){const u=((k/14+t*.07)%1),px=AX+(BX-AX)*u,py=AY+(BY-AY)*u;x.fillStyle=STEP;x.fillRect(px-20,py-12,40,10);x.fillStyle=TRU;x.fillRect(px-20,py-2,40,12)}
// hnací motor hore
x.beginPath();x.arc(BX+30,BY-6,30,0,TAU);x.fillStyle='#3b4048';x.fill();x.strokeStyle='#9aa3ab';x.lineWidth=4;x.stroke();
for(let k=0;k<3;k++){const an=t*2+k*TAU/3;x.beginPath();x.moveTo(BX+30,BY-6);x.lineTo(BX+30+Math.cos(an)*22,BY-6+Math.sin(an)*22);x.strokeStyle='#9aa3ab';x.lineWidth=3;x.stroke()}
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,140,330,330);lead(S,LN[1]||'',760,80,BX+30,BY-40);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'0.5 m/s','STEP SPEED',A,a,fi>=0);
badge(S,'STAIRS ON A LOOP','MOTOR PULLS THE CHAIN',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
