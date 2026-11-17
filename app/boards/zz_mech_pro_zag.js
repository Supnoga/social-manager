// Presné modely 33 – jadrový reaktor (rez tlakovou nádobou). Atóm uránu sa rozštiepi po zásahu neutrónom, vzniknú dva fragmenty
// a 2 až 3 nové neutróny, ktoré ďalej štiepia. Riadiace tyče ich pohlcujú a reťazová reakcia sa tak udržiava v rovnováhe.
// Hýbe sa len riadiace tyče, neutróny a praskajúce jadrá; teplo odvádza chladivo (vodu) do parnej turbíny.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const FUEL='#7a8a3a',CTRL='#3b4048',VES='#8a939c',WATER='#4aa8e8',NEU='#ffd27a';
// jadrá v palivových tyčiach (mriežka), každé sa štiepi v inom čase
const NUC=[];for(let r=0;r<5;r++)for(let c=0;c<4;c++)NUC.push([370+c*40+(r%2)*10,220+r*36,((r*4+c)*0.37)%2.4]);
PRO.fission=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={fuel:[450,300,zf*1.8],control:[300,300,zf*2.0],steam:[700,200,zf*1.9]};
const ORD=['fuel','control','steam'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// nádoba a voda
x.beginPath();x.rect(330,170,240,260);x.fillStyle='#1d2228';x.fill();x.strokeStyle=VES;x.lineWidth=6;x.stroke();
x.fillStyle='rgba(74,168,232,.18)';x.fillRect(336,176,228,248);
// palivové tyče
for(let c=0;c<4;c++){x.fillStyle=FUEL;x.fillRect(360+c*40,200,16,220)}
// riadiace tyče medzi nimi: sa spúšťajú a zdvíhajú
const cy=30*Math.sin(t*.4);x.fillStyle=CTRL;for(let c=0;c<3;c++){x.fillRect(380+c*40,180+cy,8,160)}
// štiepenie: každé jadro v pravidelnom cykle blikne, dva fragmenty a neutróny odletia
NUC.forEach(([nx,ny,t0])=>{const ph=((t-t0)%2.4+2.4)%2.4;if(ph<.6){const q=ph/.6;x.beginPath();x.arc(nx,ny,4+10*q,0,TAU);x.fillStyle=`rgba(255,210,122,${(1-q)*.8*p*sp})`;x.fill();
dot(x,[nx-q*14,ny-q*6],3,'#e6eaee',p*sp*(1-q)*(1-zi),false);dot(x,[nx+q*14,ny+q*6],3,'#e6eaee',p*sp*(1-q)*(1-zi),false);
for(let j=0;j<2;j++){const an=j*2.2+t0;dot(x,[nx+Math.cos(an)*q*30,ny+Math.sin(an)*q*30],2.5,NEU,p*sp*(1-q)*(1-zi),false)}}});
// potrubie na paru
x.beginPath();x.moveTo(570,220);x.lineTo(700,220);x.lineTo(700,300);x.strokeStyle='#6d7680';x.lineWidth=12;x.stroke();
for(let k=0;k<6;k++){const q=(k/6+t*.2)%1;dot(x,[570+130*q,220],3,WATER,p*sp*(1-zi)*.8,false)}
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',140,140,400,300);lead(S,LN[1]||'',140,420,300,330);lead(S,LN[2]||'',780,120,700,220);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'2-3 neutrons','PER SPLIT',A,a,fi>=0);
badge(S,'CHAIN REACTION','CONTROL RODS ABSORB NEUTRONS',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
