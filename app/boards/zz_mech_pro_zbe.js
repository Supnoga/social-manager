// Presné modely 41 – dráha telesa vrhu (bočný pohľad). Gravitácia ťahá teleso dole, vodorovná rýchlosť zostáva rovnaká.
// Výsledok je parabola: najvyšší bod je v polovici dráhy. Hýbe sa len teleso a jeho stopa.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.trajectory=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={launch:[200,380,zf*1.8],peak:[450,220,zf*1.8],landing:[700,420,zf*1.8]};
const ORD=['launch','peak','landing'],KF=cams(d,FULL,FV,ORD,DUR);
const PT=u=>[150+600*u,440-1000*u*(1-u)];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.fillRect(80,460,740,40);
// celá dráha (bodkovaná)
x.beginPath();for(let i=0;i<=60;i++){const q=PT(i/60);i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.setLineDash([4,8]);x.strokeStyle="rgba(255,255,255,.2)";x.lineWidth=2;x.stroke();x.setLineDash([]);
// teleso a stopa
const u=(t%3)/3;
for(let k=1;k<=12;k++){const q=PT(Math.max(0,u-k*.012));dot(x,q,3,A,p*sp*(1-zi)*(1-k/13),false)}
const b=PT(u);dot(x,b,9,"#e6eaee",p*sp*(1-zi),true);
// najvyšší bod
const pk=PT(.5);x.beginPath();x.moveTo(pk[0],pk[1]+14);x.lineTo(pk[0],460);x.strokeStyle="rgba(255,255,255,.25)";x.lineWidth=2;x.stroke();
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",120,150,150,420);lead(S,LN[1]||"",700,130,pk[0]+8,pk[1]);lead(S,LN[2]||"",780,400,700,420);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"45°","LAUNCH ANGLE",A,a,fi>=0);
badge(S,"GRAVITY ONLY PULLS DOWN","SAME SPEED ALONG THE GROUND",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
