// Presné modely 17 – lítium-iónový článok (batéria mobilu, auta) v reze.
// Hýbe sa len to, čo sa hýbe naozaj: pri vybíjaní idú ióny lítia z grafitu (anóda) cez separátor do oxidu kovu (katóda)
// a elektróny idú vonkajším drôtom cez spotrebič; pri nabíjaní naopak. Opotrebenie: na anóde rastie vrstva (SEI) a zachytí časť iónov,
// takže kapacita klesá. Počet iónov na každej strane = stav nabitia, číslo sa počíta z neho.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),ION='#ffd23f';

PRO.battery=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),CH=F=='charge',WR=F=='wear';
const BX=170,BY=170,BW=524,BH=300,AX0=196,AX1=388,SX=420,SW=24,CX0=476,CX1=668,NI=16,L=Math.max(8,DUR+1),STUCK=WR?[2,7,11]:[];
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[432,300,zf*.94],FV={anode:[292,330,zf*1.9],cathode:[572,330,zf*1.9],separator:[432,330,zf*2.2],circuit:[432,140,zf*1.6],wear:[300,330,zf*1.8],charge:[432,250,zf*1.2]};
const ORD=['anode','cathode','separator','circuit'],KF=cams(d,FULL,FV,ORD,DUR);
// miesta iónov: v anóde medzi vrstvami grafitu, v katóde v mriežke oxidu
const LAY=[...Array(8)].map((_,j)=>BY+30+j*34),AS=[...Array(NI)].map((_,i)=>[AX0+26+(i%4)*48+(Math.floor(i/4)%2)*14,LAY[1+Math.floor(i/4)*2]-17]),
CS=[...Array(NI)].map((_,i)=>[CX0+28+(i%4)*46,BY+48+Math.floor(i/4)*64+32]);
const ORDI=[...Array(NI)].map((_,i)=>i).sort((a,b)=>(AS[b][0]-AS[a][0])||(a-b));   // najprv idú ióny pri separátore
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-.94)/.25);
const u=t%L,go=n=>{const t0=.6+n*(L-2.2)/NI;return sm((u-t0)/1.1)};   // 0 = na štartovej strane, 1 = prešiel
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// obal článku + elektrolyt
x.beginPath();x.roundRect(BX-14,BY-14,BW+28,BH+28,18);x.fillStyle='#14171b';x.fill();x.strokeStyle='#fff';x.lineWidth=3.5;x.stroke();
x.fillStyle='rgba(90,169,255,.10)';x.fillRect(BX,BY,BW,BH);
// anóda: grafit vo vrstvách na medenej fólii
x.fillStyle='#b87333';x.fillRect(AX0-16,BY,12,BH);
LAY.forEach(y=>{x.strokeStyle='#5d636b';x.lineWidth=7;x.beginPath();x.moveTo(AX0,y);x.lineTo(AX1,y);x.stroke();x.strokeStyle='rgba(255,255,255,.25)';x.lineWidth=1.5;for(let k=AX0+6;k<AX1;k+=14){x.beginPath();x.arc(k,y,3.2,0,TAU);x.stroke()}});
// vrstva SEI rastie pri opotrebení
if(WR){const g=sm((u-.5)/(L-2));x.fillStyle=mix('#3a3f46','#7a6a55',g);x.fillRect(AX1,BY+6,4+16*g,BH-12)}
// separátor (pórovitá fólia)
x.fillStyle='#e9ecef';x.globalAlpha=p*.85;for(let y=BY;y<BY+BH;y+=12){x.fillRect(SX,y,SW,7)}x.globalAlpha=p;
// katóda: oxid kovu v mriežke na hliníkovej fólii
x.fillStyle='#aab2bb';x.fillRect(CX1+4,BY,12,BH);
for(let r=0;r<4;r++)for(let c=0;c<4;c++){const cx=CX0+28+c*46,cy=BY+48+r*64;x.fillStyle='#3a4a5a';x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=1.5;x.beginPath();x.arc(cx,cy,13,0,TAU);x.fill();x.stroke();
x.fillStyle='#c33';x.beginPath();x.arc(cx+15,cy+15,6,0,TAU);x.fill()}
// ióny lítia: z anódy do katódy (vybíjanie) alebo späť (nabíjanie); dráha ide stredom separátora
let inA=0;
ORDI.forEach((i,n)=>{const a=AS[i],c=CS[i],stuck=STUCK.includes(i);let g=go(n);if(CH)g=1-g;if(stuck)g=Math.min(g,.0);
const k=CH?1-g:g,mx=SX+SW/2,my=(a[1]+c[1])/2+((i%3)-1)*30;let px,py;
if(stuck){px=AX1+10;py=a[1]}else if(g<=0){px=a[0];py=a[1]}else if(g>=1){px=c[0];py=c[1]}else{const q=g,qq=1-q;px=qq*qq*a[0]+2*qq*q*mx+q*q*c[0];py=qq*qq*a[1]+2*qq*q*my+q*q*c[1]}
if(g<.5)inA++;
const moving=g>0&&g<1;x.fillStyle=stuck?'#7d838a':ION;x.strokeStyle='#000';x.lineWidth=1.5;x.beginPath();x.arc(px,py,moving?10:8,0,TAU);x.fill();x.stroke();
if(moving)dot(x,[px,py],14,ION,p*.5,true);
x.save();x.font=`900 ${moving?13:11}px ${S.FT}`;x.textAlign='center';x.textBaseline='middle';x.fillStyle='#000';x.fillText('+',px,py+.5);x.restore()});
// vonkajší obvod: drôt hore, spotrebič (alebo nabíjačka) v strede
const W=[[AX0-10,BY-14],[AX0-10,92],[CX1+10,92],[CX1+10,BY-14]];x.strokeStyle='#cfd4d9';x.lineWidth=5;x.beginPath();W.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();
x.beginPath();x.roundRect(392,64,80,56,10);x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
if(CH){x.fillStyle=A;x.beginPath();x.moveTo(436,70);x.lineTo(420,95);x.lineTo(434,95);x.lineTo(426,114);x.lineTo(446,86);x.lineTo(432,86);x.lineTo(440,70);x.closePath();x.fill()}
else{const glow=.55+.45*Math.sin(t*3);x.fillStyle=mix('#555',A,glow);x.beginPath();x.arc(432,88,13,0,TAU);x.fill();x.strokeStyle=A;x.lineWidth=2;for(let k=0;k<6;k++){const aa=k*TAU/6;x.beginPath();x.moveTo(432+Math.cos(aa)*18,88+Math.sin(aa)*18);x.lineTo(432+Math.cos(aa)*24,88+Math.sin(aa)*24);x.stroke()}}
// elektróny po drôte: pri vybíjaní z anódy (vľavo) cez spotrebič do katódy, pri nabíjaní ich nabíjačka tlačí späť do anódy
const len=[0];for(let i=1;i<W.length;i++)len.push(len[i-1]+Math.hypot(W[i][0]-W[i-1][0],W[i][1]-W[i-1][1]));const TL=len[len.length-1];
const at=s=>{for(let i=1;i<W.length;i++)if(s<=len[i]){const f=(s-len[i-1])/(len[i]-len[i-1]);return [W[i-1][0]+(W[i][0]-W[i-1][0])*f,W[i-1][1]+(W[i][1]-W[i-1][1])*f]}return W[W.length-1]};
for(let k=0;k<10;k++){const s=((t*110*(CH?-1:1)+k*TL/10)%TL+TL)%TL,q=at(s);if(Math.abs(q[0]-432)<48&&q[1]<100)continue;dot(x,q,6,'#7fd0ff',p,true)}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0],220,512,AX0+60,BY+BH-20);lead(S,LN[1],650,512,CX0+120,BY+BH-30);lead(S,LN[2],432,512,SX+SW/2,BY+BH-10);lead(S,LN[3],150,60,AX0-10,120);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4),cap=WR?Math.round(100-20*sm((u-.5)/(L-2))):100,soc=Math.round(inA/NI*cap);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,WR?String(cap)+' %':String(soc)+' %',WR?'CAPACITY LEFT':'CHARGE',A,a,fi>=0);
badge(S,CH?'CHARGING':WR?'AGING':'IN USE',CH?'IONS BACK TO ANODE':WR?'IONS GET TRAPPED':'IONS TO CATHODE',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
