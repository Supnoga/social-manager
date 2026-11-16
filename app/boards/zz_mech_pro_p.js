// Presné modely 16 – elektromotor so synchrónnym rotorom (permanentné magnety), pohľad spredu v reze.
// Hýbe sa len to, čo sa hýbe naozaj: cievky statora sa zapínajú v poradí fáz A, B, C, ich magnetické pole sa otáča
// a magnety rotora ho naháňajú (rotor je o štvrť otáčky za poľom = najväčší krútiaci moment). Pri rekuperácii rotor pole predbieha
// a prúd tečie späť do batérie. Póly zubov (N/S) sa počítajú z polohy poľa: sila zubu = cos(uhol zubu − uhol poľa).
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},COLD='#5aa9ff';

PRO.emotor=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),RUN=F=='run',REGEN=F=='regen';
const CX=432,CY=280,RO=226,RI=196,RT=128,RR=116,RS=26,NT=6;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[CX,CY,zf*1.02],FV={coils:[CX,CY-150,zf*1.75],magnets:[CX,CY,zf*1.85],field:[CX,CY,zf*1.25],shaft:[CX,CY,zf*2.6],regen:[CX,CY,zf*1.2]};
const ORD=['coils','magnets','field','shaft'],KF=cams(d,FULL,FV,ORD,DUR);
// zuby statora: uhol, fáza (A, B, C sa opakujú; protiľahlý zub patrí tej istej fáze)
const TE=[...Array(NT)].map((_,k)=>({a:-Math.PI/2+k*TAU/NT,ph:'ABC'[k%3]}));
const tooth=a=>{const w=24,c=Math.cos(a),s=Math.sin(a),px=-s,py=c;x.beginPath();x.moveTo(CX+c*RI+px*w*1.25,CY+s*RI+py*w*1.25);x.lineTo(CX+c*(RT+14)+px*w,CY+s*(RT+14)+py*w);
x.lineTo(CX+c*RT+px*w*1.7,CY+s*RT+py*w*1.7);x.arc(CX,CY,RT,a+w*1.7/RT,a-w*1.7/RT,true);x.lineTo(CX+c*(RT+14)-px*w,CY+s*(RT+14)-py*w);x.lineTo(CX+c*RI-px*w*1.25,CY+s*RI-py*w*1.25);x.closePath()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1.02)/.25);
// rýchlosť: rozbeh v prvej sekunde; naplno sa točí rýchlejšie
const w=(RUN?1.15:.3)*TAU,psi=w*(t-(1-Math.exp(-t*1.4))/1.4),fld=psi+(REGEN?-1:1)*Math.PI/2;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// kostra statora (plech v reze)
const yoke=()=>{x.beginPath();x.arc(CX,CY,RO,0,TAU);x.moveTo(CX+RI,CY);x.arc(CX,CY,RI,0,TAU,true)};
yoke();x.fillStyle='#1b1e22';x.fill('evenodd');hatch(x,yoke,'evenodd');x.strokeStyle='#fff';x.lineWidth=3.5;x.beginPath();x.arc(CX,CY,RO,0,TAU);x.stroke();
// zuby + cievky: farba a prúd podľa toho, ako veľmi zub práve tvorí pól (N = farba kanála, S = modrá)
TE.forEach((q,k)=>{const s=Math.cos(q.a-fld),m=Math.abs(s),col=s>0?A:COLD;
tooth(q.a);x.fillStyle=mix('#2a2f35',col,m*.55);x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
const c=Math.cos(q.a),sn=Math.sin(q.a),px=-sn,py=c;
for(let j=0;j<4;j++){const r=RI-14-j*12;x.strokeStyle=mix('#b87333',col,m*.8);x.lineWidth=7;x.beginPath();x.moveTo(CX+c*r+px*36,CY+sn*r+py*36);x.lineTo(CX+c*r-px*36,CY+sn*r-py*36);x.stroke()}
// prúd v cievke: bodky bežia po závite, smer podľa znamienka (pri rekuperácii opačne)
if(m>.15){const dir=(s>0?1:-1)*(REGEN?-1:1);for(let j=0;j<3;j++){const u=((t*1.6*dir+j/3)%1+1)%1,r=RI-14-((j*12)%48),o=(u*2-1)*36;dot(x,[CX+c*r+px*o,CY+sn*r+py*o],5,'#fff',p*m,true)}}
// písmeno pólu na hrote zubu
if(m>.35){x.save();x.globalAlpha*=cl((m-.35)/.3);x.font=`900 26px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';x.fillStyle=col;x.fillText(s>0?'N':'S',CX+c*(RT+36),CY+sn*(RT+36));x.restore()}});
// rotor: oceľ + dva magnety (N a S), pootočený o psi
x.save();x.translate(CX,CY);x.rotate(psi);
x.beginPath();x.arc(0,0,RR,0,TAU);x.fillStyle='#2a2f35';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
const mag=(a0,col,lt)=>{x.beginPath();x.arc(0,0,RR-4,a0-1.05,a0+1.05);x.arc(0,0,RR-30,a0+1.05,a0-1.05,true);x.closePath();x.fillStyle=col;x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke();
x.save();x.rotate(a0);x.translate(RR-17,0);x.rotate(-a0-psi);x.font=`900 22px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';x.fillStyle='#000';x.fillText(lt,0,1);x.restore()};
mag(0,COLD,'S');mag(Math.PI,A,'N');
// rebrá rotora, aby bolo vidno, že sa točí
x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;for(let k=0;k<4;k++){const a=Math.PI/2+k*TAU/4*.5-Math.PI/4;x.beginPath();x.moveTo(Math.cos(a)*(RS+10),Math.sin(a)*(RS+10));x.lineTo(Math.cos(a)*(RR-36),Math.sin(a)*(RR-36));x.stroke()}
// hriadeľ s perom
x.beginPath();x.arc(0,0,RS,0,TAU);x.fillStyle='#c9ced3';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();x.fillStyle='#1b1e22';x.fillRect(-6,-RS,12,12);
x.restore();
// smer poľa: prerušovaná šípka cez stred (najviac pri zábere na pole)
const fa=FN=>FN=='field'||REGEN?1:.35;{const [FN0]=shot(KF,d,t);x.save();x.globalAlpha*=fa(FN0);const L=RT-8,ex=CX+Math.cos(fld)*L,ey=CY+Math.sin(fld)*L;x.strokeStyle=A;x.lineWidth=4;x.setLineDash([12,9]);x.beginPath();
x.moveTo(CX-Math.cos(fld)*L,CY-Math.sin(fld)*L);x.lineTo(ex,ey);x.stroke();x.setLineDash([]);x.fillStyle=A;x.beginPath();x.moveTo(ex,ey);x.lineTo(ex-Math.cos(fld-.4)*24,ey-Math.sin(fld-.4)*24);x.lineTo(ex-Math.cos(fld+.4)*24,ey-Math.sin(fld+.4)*24);x.closePath();x.fill();x.restore()}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0],130,70,CX+Math.cos(TE[5].a)*(RI-30),CY+Math.sin(TE[5].a)*(RI-30));
lead(S,LN[1],740,70,CX+Math.cos(psi+Math.PI)*(RR-17),CY+Math.sin(psi+Math.PI)*(RR-17));
lead(S,LN[2],130,500,CX+Math.cos(fld)*(RT-40),CY+Math.sin(fld)*(RT-40));
lead(S,LN[3],740,500,CX+RS*.7,CY+RS*.7);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
const ph=TE.slice(0,3).map(q=>[q.ph,Math.abs(Math.cos(q.a-fld))]).sort((u,v2)=>v2[1]-u[1])[0][0];
meter(S,String(Math.round(w*6000/TAU*(1-Math.exp(-t*1.4))/10)*10),'RPM',A,a,fi>=0);
badge(S,REGEN?'REGEN':'PHASE '+ph,REGEN?'CHARGES BATTERY':'COILS ON',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
