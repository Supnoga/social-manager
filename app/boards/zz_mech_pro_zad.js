// Presné modely 30 – zips (zips s jazdcom, pohľad zboku na zuby). Jazdec ich stlačí dohromady: zuby z oboch pásov
// zapadnú do seba. Pred jazdcom sú zuby otvorené, za ním zatvorené. Hýbe sa len jazdec a zuby, ktorých sa dotkne.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const TEETH='#c9d0d6',TAPE='#3b4048',SL='#9aa3ab';
PRO.zipper=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={teeth:[330,300,zf*1.8],slider:[470,300,zf*2.1]};
const ORD=['teeth','slider'],KF=cams(d,FULL,FV,ORD,DUR);
const NT=30,X0=170,DX=16;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
const sx=X0+(NT*DX)*(.5+.5*Math.sin(t*.5));
// pásy (látka)
x.fillStyle=TAPE;x.fillRect(X0-30,224,NT*DX+60,22);x.fillRect(X0-30,354,NT*DX+60,22);
// zuby: vľavo od jazdca sú zapadnuté, vpravo sú otvorené
for(let k=0;k<NT;k++){const xk=X0+k*DX,c=ez((sx-xk)/12),yt=240+(288-240)*c,yb=348+(300-348)*c;
x.fillStyle=TEETH;x.fillRect(xk-5,yt,10,12);x.fillRect(xk-5,yb,10,12)}
// jazdec: ťahá zuby k sebe
x.fillStyle=SL;x.fillRect(sx-12,226,24,130);x.strokeStyle='#e6eaee';x.lineWidth=2;x.strokeRect(sx-12,226,24,130);
dot(x,[sx,300],4,A,p*sp*(1-zi),true);
// popisy
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||'',200,140,X0+100,246);lead(S,LN[1]||'',720,120,sx,226);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'2 rows','OF TEETH',A,a,fi>=0);
badge(S,'INTERLOCKING TEETH','THE SLIDER PUSHES THEM TOGETHER',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
