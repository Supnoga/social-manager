// Presné modely 24 – věžový žeriav (bočný pohľad). Vežu drží protiváha na zadnej strane ramena, vozík s hákom sa posúva po ramene
// a lano s bremenom sa spúšťa a zdvíha. Bremeno sa pri pohybe mierne kýve. Hýbe sa len vozík, háková kladka a bremeno.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const STEEL='#9aa3ab',DKS='#5d666f',LOAD='#d9822b';
PRO.crane=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,330,zf*.95],FV={trolley:[450,160,zf*1.9],hook:[450,300,zf*1.8],counterweight:[190,200,zf*2.1]};
const ORD=['trolley','hook','counterweight'],KF=cams(d,FULL,FV,ORD,DUR);
// vozík sa posúva po ramene (hore), háková kladka sa zdvíha a spúšťa, bremeno sa kýve
const trX=t=>450+190*Math.sin(t*.35),hkY=t=>300+70*Math.sin(t*.5+1);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// základ a stožiar (mriežka)
x.fillStyle='#2a2f36';x.fillRect(360,500,180,60);
x.strokeStyle=STEEL;x.lineWidth=5;x.beginPath();x.moveTo(410,150);x.lineTo(410,500);x.moveTo(490,150);x.lineTo(490,500);x.stroke();
x.lineWidth=2;x.strokeStyle=DKS;x.beginPath();for(let y=150;y<500;y+=30){x.moveTo(410,y);x.lineTo(490,y+30);x.moveTo(490,y);x.lineTo(410,y+30)}x.stroke();
// kabína na vrchu a protiváha vzadu
x.fillStyle='#3b4048';x.fillRect(370,120,120,30);x.fillStyle=DKS;x.fillRect(374,124,40,22);
x.strokeStyle=STEEL;x.lineWidth=4;x.beginPath();x.moveTo(370,135);x.lineTo(150,135);x.stroke();
x.fillStyle='#5c636c';for(let k=0;k<3;k++)x.fillRect(150,140+k*16,60,14);
// rameno (hore: dve pásy a diagonály)
x.strokeStyle=STEEL;x.lineWidth=5;x.beginPath();x.moveTo(170,122);x.lineTo(780,122);x.moveTo(170,142);x.lineTo(780,142);x.stroke();
x.lineWidth=2;x.strokeStyle=DKS;x.beginPath();for(let xx=170;xx<780;xx+=20){x.moveTo(xx,122);x.lineTo(xx+20,142);x.moveTo(xx+20,122);x.lineTo(xx,142)}x.stroke();
x.beginPath();x.moveTo(410,122);x.lineTo(780,142);x.stroke();
// vozík a lano s hákom
const tx=trX(t),hy=hkY(t),sw=.035*Math.sin(t*1.3)*(1-zi*.5);
x.fillStyle='#e6eaee';x.fillRect(tx-22,142,44,14);x.fillStyle=DKS;x.fillRect(tx-14,156,28,8);
x.strokeStyle='#e6eaee';x.lineWidth=2;x.beginPath();x.moveTo(tx-10,156);x.lineTo(tx-10,hy);x.moveTo(tx+10,156);x.lineTo(tx+10,hy);x.stroke();
x.lineWidth=5;x.strokeStyle=STEEL;x.beginPath();x.arc(tx,hy,10,0,TAU);x.stroke();
x.save();x.translate(tx,hy+10);x.rotate(sw);x.fillStyle=LOAD;x.fillRect(-32,0,64,48);x.strokeStyle='rgba(0,0,0,.35)';x.lineWidth=2;x.strokeRect(-32,0,64,48);
x.restore();
// svetlo bremena: smer pohybu
dot(x,[tx,hy+58],4,A,p*sp*(1-zi),true);
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',760,70,tx+30,150);lead(S,LN[1]||'',160,380,tx-40,hy+30);lead(S,LN[2]||'',120,260,180,160);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
if(FN=='counterweight')meter(S,'8 t','COUNTERWEIGHT',A,a,fi>=0);else meter(S,'2 t','LOAD',A,a,fi>=0);
badge(S,'BALANCE','COUNTERWEIGHT HOLDS THE TOWER',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
