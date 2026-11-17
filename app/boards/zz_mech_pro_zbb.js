// Presné modely 38 – vlna na lane (bočný pohľad). Častice kmitajú len hore a dole na mieste; vlna sa posúva ďalej. Energia
// putuje, hmota ostáva. Hýbe sa len častice a tvar vlny.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.wave=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={wave:[450,300,zf*1.5],particle:[300,300,zf*2.4],crest:[600,240,zf*2.0]};
const ORD=['wave','particle','crest'],KF=cams(d,FULL,FV,ORD,DUR);
const K2=2*Math.PI/300,W=2*Math.PI*.6,Y=y=>300+80*Math.sin(K2*0+y);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const yw=xx=>300+80*Math.sin(K2*xx-W*t);
x.beginPath();for(let xx=120;xx<=780;xx+=6){xx===120?x.moveTo(xx,yw(xx)):x.lineTo(xx,yw(xx))}x.strokeStyle="#c9d0d6";x.lineWidth=6;x.stroke();
for(let i=0;i<=20;i++){const xx=120+i*33;dot(x,[xx,300],2.5,"#4a525c",p*sp*(1-zi),false);dot(x,[xx,yw(xx)],5,A,p*sp*(1-zi),true)}
// hrebeň sa posúva doprava
const cr=(W*t)/K2;const cx=120+((cr%660)+660)%660;x.beginPath();x.arc(cx,yw(cx),10,0,TAU);x.strokeStyle="#fff";x.lineWidth=3;x.globalAlpha=p*sp*(1-zi)*.8;x.stroke();x.globalAlpha=p*sp*(1-zi);
x.beginPath();x.moveTo(140,130);x.lineTo(260,130);x.strokeStyle=A;x.lineWidth=4;x.stroke();
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",160,170,300,250);lead(S,LN[1]||"",160,420,300,300);lead(S,LN[2]||"",760,170,cx,yw(cx)-20);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"1.2 m","WAVELENGTH",A,a,fi>=0);
badge(S,"WAVE MOVES, ROPE STAYS","ENERGY TRAVELS",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
