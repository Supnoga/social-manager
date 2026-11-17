// Presné modely 22 – pevný disk (zhora, pohľad na plotňu). Plotňa sa točí, rameno s hlavou sa natáča po stopách (hľadanie stopy),
// hlava letí nad povrchom na vzduchovom vankúši (asi 3 nm). Dáta sú magnetické bity na stopách; hlava číta a zapisuje len pod sebou.
// Hýbe sa len to, čo sa hýbe naozaj: plotňa, rameno a hlava. Ložisko ramena je v rohu.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const CX=450,CY=300,R=200,PX=735,PY=520,L=330,MET='#8a939c',DK='#1d2228',DIR=Math.atan2(CY-PY,CX-PX);

PRO.harddrive=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={platter:[450,300,zf*1.0],head:[560,260,zf*1.9],spindle:[450,300,zf*2.6]};
const ORD=['platter','head','spindle'],KF=cams(d,FULL,FV,ORD,DUR);
// hlava hľadá stopu: 0 = blízko stredu (r≈90), 1 = pri vonkajšej stope (r≈190); ease, aby sa rameno nehýbalo skokom
const seek=t=>{const s=.5+.5*Math.sin(t*1.1);return s*s*(3-2*s)};
const headAt=t=>{const a=DIR+.25+.3*seek(t);return [PX+L*Math.cos(a),PY+L*Math.sin(a),a]};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// kryt disku
x.fillStyle=DK;x.fillRect(110,60,680,490);x.strokeStyle=MET;x.lineWidth=4;x.strokeRect(110,60,680,490);
// plotňa: tmavý kov
const g=x.createRadialGradient(CX,CY,20,CX,CY,R);g.addColorStop(0,'#4a5560');g.addColorStop(1,'#2a3138');
x.beginPath();x.arc(CX,CY,R,0,TAU);x.fillStyle=g;x.fill();x.strokeStyle=MET;x.lineWidth=3;x.stroke();
// stopy: bity (magnetické smery) sa otáčajú s plotňou
const ang=t*2.4,n=48;
for(let k=0;k<8;k++){const rr=64+k*17;for(let j=0;j<n;j++){const a0=ang+j*TAU/n;x.beginPath();x.arc(CX,CY,rr,a0+.03,a0+TAU/n-.03);x.strokeStyle=((j*5+k*3)%7<3)?'rgba(255,255,255,.3)':'rgba(255,255,255,.08)';x.lineWidth=3;x.stroke()}}
// hlava a stopa, ktorú práve číta/zapisuje
const H=headAt(t),hx=H[0],hy=H[1],ps=Math.atan2(hy-CY,hx-CX),rh=Math.hypot(hx-CX,hy-CY);
x.beginPath();x.arc(CX,CY,rh,ps-.16,ps+.16);x.strokeStyle=A;x.lineWidth=6;x.globalAlpha=p*sp*(1-zi)*.9;x.stroke();x.globalAlpha=p;
// ložisko motora v strede
x.beginPath();x.arc(CX,CY,26,0,TAU);x.fillStyle=MET;x.fill();x.strokeStyle='#e6eaee';x.lineWidth=3;x.stroke();
x.beginPath();x.arc(CX,CY,8,0,TAU);x.fillStyle=DK;x.fill();
// rameno: otáča sa okolo ložiska v rohu, na konci je hlava, na zadnom konci cievka
x.beginPath();x.moveTo(PX,PY);x.lineTo(hx,hy);x.strokeStyle='#9aa3ab';x.lineWidth=14;x.stroke();
x.beginPath();x.moveTo(PX,PY);x.lineTo(hx,hy);x.strokeStyle='#5d666f';x.lineWidth=4;x.stroke();
x.beginPath();x.arc(PX,PY,26,0,TAU);x.fillStyle='#aeb5bc';x.fill();x.beginPath();x.arc(PX,PY,10,0,TAU);x.fillStyle=DK;x.fill();
// hlava (slider) letí nad plotňou; svetlý bod = miesto čítania
x.save();x.translate(hx,hy);x.rotate(H[2]);x.fillStyle='#e6eaee';x.fillRect(-12,-5,24,10);x.restore();
dot(x,[hx,hy],3,A,p*sp*(1-zi),true);
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',160,520,CX-170,CY+150);lead(S,LN[1]||'',800,170,hx+20,hy-20);lead(S,LN[2]||'',250,90,CX,CY-120);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
if(FN=='head')meter(S,'3 nm','FLYING HEIGHT',A,a,fi>=0);else meter(S,'7200 RPM','PLATTER SPEED',A,a,fi>=0);
badge(S,'MAGNETIC BITS','HEAD FLIES ON AIR, NEVER TOUCHES',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
