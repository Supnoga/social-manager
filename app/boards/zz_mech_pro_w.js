// Presné modely 23 – transformátor (rez). Striedavý prúd v primárnom vinutí vytvára striedavý magnetický tok v železnom jadre,
// ktorý obteká okruh jadra a v sekundárnom vinutí indukuje napätie. Vinutia nie sú spojené drôtom, len tokom.
// Pomer napätí = pomer závitov: 20 závitov na vstupe, 2 na výstupe → 230 V na 23 V. Hýbe sa len tok a prúd vo vodičoch.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const LX=245,RX=655,TY=170,BY=430,P1=410,P2=260;   // stred jadra: ľavý a pravý stĺp, horné a dolné jarmo
const CORE='#4a525c',WIRE='#c8783a',WIRE2='#e8a060',FLUX='#7fd0ff';
// bod na obvode stredu jadra (u v 0..1, v smere hodinových ručičiek)
const loopAt=u=>{let s=((u%1)+1)%1*(2*P1+2*P2);if(s<P1)return[LX+s,TY];s-=P1;if(s<P2)return[RX,TY+s];s-=P2;if(s<P1)return[RX-s,BY];s-=P1;return[LX,BY-s]};
// bod na vodiči (polyline) v u 0..1
const pathAt=(pts,u)=>{let L=0,ls=[];for(let i=1;i<pts.length;i++){const l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);ls.push(l);L+=l}let s=((u%1)+1)%1*L;for(let i=1;i<pts.length;i++){if(s<=ls[i-1]){const f=s/ls[i-1];return[pts[i-1][0]+(pts[i][0]-pts[i-1][0])*f,pts[i-1][1]+(pts[i][1]-pts[i-1][1])*f]}s-=ls[i-1]}return pts[pts.length-1]};
const PRIM=[[215,230],[150,230],[150,120],[100,120]],PRIM2=[[215,370],[150,370],[150,470],[100,470]];
const SEC=[[685,230],[760,230],[760,240],[781,240]],SEC2=[[685,370],[760,370],[760,262]];
PRO.transformer=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={core:[450,300,zf*1.3],primary:[230,300,zf*1.8],secondary:[670,300,zf*1.8]};
const ORD=['core','primary','secondary'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const sg=Math.sin(t*2.2),fl=Math.abs(sg);   // striedavý prúd: tok aj smer prúdu sa menia v rytme
// jadro (rám bez otvoru)
x.beginPath();x.rect(170,140,560,320);x.moveTo(290,210);x.lineTo(290,390);x.lineTo(610,390);x.lineTo(610,210);x.closePath();
x.fillStyle=CORE;x.fill('evenodd');x.strokeStyle='#8a939c';x.lineWidth=3;x.stroke();
// vrstvy plechov v stĺpoch
x.strokeStyle='rgba(255,255,255,.12)';x.lineWidth=2;for(let k=0;k<7;k++){const xx=178+k*12;x.beginPath();x.moveTo(xx,150);x.lineTo(xx,460);x.stroke()}
// vinutia: primárne 20 závitov na ľavom stĺpe, sekundárne 2 hrubé závity na pravom
x.lineWidth=6;x.strokeStyle=WIRE;for(let k=0;k<20;k++){const y=230+k*7;x.beginPath();x.moveTo(218,y);x.lineTo(287,y);x.stroke()}
x.strokeStyle=WIRE2;x.lineWidth=8;[280,330].forEach(y=>{x.beginPath();x.moveTo(612,y);x.lineTo(684,y);x.stroke()});
// magnetický tok: svetlé bodky obiehajú okruh jadra, smer sa mení s prúdom
for(let k=0;k<14;k++){const u=k/14+sg*t*.06,P=loopAt(u);dot(x,P,4,FLUX,p*(.35+.6*fl)*(1-zi),true)}
// vodiče a elektróny (smer podľa prúdu)
x.strokeStyle='#6d7680';x.lineWidth=4;[PRIM,PRIM2,SEC,SEC2].forEach(pts=>{x.beginPath();pts.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke()});
for(let k=0;k<8;k++){dot(x,pathAt(PRIM,k/8+sg*t*.15),3,'#fff',p*sp*(.4+.5*fl)*(1-zi),false);dot(x,pathAt(SEC,k/8+sg*t*.15),3,A,p*sp*(.4+.5*fl)*(1-zi),false)}
// žiarovka na výstupe: svieti podľa napätia
const lb=fl*.8+.2;x.beginPath();x.arc(805,240,22,0,TAU);x.fillStyle=mix('#2a2f36','#ffd27a',lb);x.fill();x.strokeStyle='#e6eaee';x.lineWidth=3;x.stroke();
dot(x,[805,240],6,'#ffd27a',p*lb*(1-zi),true);
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',150,520,450,450);lead(S,LN[1]||'',120,80,190,200);lead(S,LN[2]||'',800,120,664,250);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
if(FN=='secondary')meter(S,'23 V','SECONDARY',A,a,fi>=0);else meter(S,'230 V','PRIMARY',A,a,fi>=0);
badge(S,'TURNS RATIO 10 : 1','NO WIRE BETWEEN COILS, ONLY FLUX',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
