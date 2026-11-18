// Presné modely 42 – nákladná loď s prístavným žeriavom (bočný pohľad). Kontajnery sa nakladajú žeriavom na palubu a loď sa ním udržiava na mieste pri nábreží. Hýbe sa len vlny, háky a kontajner, ktorý žeriav zdvíha.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.containership=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.0],FV={hull:[450,400,zf*1.7],crane:[160,260,zf*1.8],containers:[450,320,zf*1.8]};
const ORD=['hull','crane','containers'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const hx=170+60*Math.sin(t*.5),hy=200+70*(.5+.5*Math.sin(t*.8));
x.fillStyle="#2a2f36";x.fillRect(40,400,200,120);
x.strokeStyle="#9aa3ab";x.lineWidth=5;x.beginPath();x.moveTo(120,400);x.lineTo(120,140);x.moveTo(150,400);x.lineTo(150,140);x.stroke();x.lineWidth=2;x.beginPath();for(let y=140;y<400;y+=30){x.moveTo(120,y);x.lineTo(150,y+30);x.moveTo(150,y);x.lineTo(120,y+30)}x.stroke();
x.strokeStyle="#c9d0d6";x.lineWidth=6;x.beginPath();x.moveTo(110,140);x.lineTo(330,140);x.stroke();
x.beginPath();x.moveTo(hx,140);x.lineTo(hx,hy);x.strokeStyle="#6d7680";x.lineWidth=2;x.stroke();
x.fillStyle="#d9822b";x.fillRect(hx-26,hy,52,30);x.strokeStyle="rgba(0,0,0,.35)";x.lineWidth=2;x.strokeRect(hx-26,hy,52,30);
x.beginPath();x.moveTo(260,400);x.lineTo(740,400);x.lineTo(700,450);x.lineTo(300,450);x.closePath();x.fillStyle="#3b4048";x.fill();
x.fillStyle="#dfe5ea";x.fillRect(640,300,80,100);
const cols=["#d9822b","#3b7fc4","#c9d0d6","#9aa3ab","#d9822b"];
for(let r=0;r<2;r++)for(let c=0;c<5;c++){x.fillStyle=cols[(r+c)%5];x.fillRect(300+c*68,330-r*30,62,28)}
for(let k=0;k<8;k++){const wx=40+k*90+((t*40)%90);x.beginPath();x.arc(wx,470,8,Math.PI*1.1,Math.PI*1.9);x.strokeStyle="rgba(255,255,255,.3)";x.lineWidth=2;x.stroke()}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",760,140,640,330);lead(S,LN[1]||"",140,90,120,140);lead(S,LN[2]||"",600,240,520,330);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"12 boxes","CONTAINERS",A,a,fi>=0);
badge(S,"LOADED BY CRANE","HOOK LIFTS 1 BOX",A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
