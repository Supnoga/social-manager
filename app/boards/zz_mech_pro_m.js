// Presné modely 13 – cylindrická vložka zámku s kolíkmi (bočný rez + pohľad spredu).
// Hýbe sa len to, čo sa hýbe naozaj: kľúč zdvihne kolíky podľa svojich zárezov, pri správnom kľúči sa všetky delia presne v deliacej rovine a bubon sa otočí;
// pri zlom kľúči ostane kolík cez rovinu a bubon drží; pri otváraní bez kľúča sa kolíky usadia po jednom.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),HOT='#ff6a3d';

PRO.pinlock=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),WR=F=='wrong',PK=F=='pick',SHL=300,REST=372,AX=360,XP=[300,370,440,510,580],LK=[44,62,36,56,48],DL=46,XF=640,FC=[790,330];
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[470,310,zf*1.04],FV={keypins:[440,335,zf*1.9],drivers:[440,235,zf*1.9],shear:[440,300,zf*2.3],plug:[770,320,zf*1.9],wrong:[440,300,zf*1.5],pick:[420,310,zf*1.5]},ORD=['keypins','drivers','shear','plug'],KF=cams(d,FULL,FV,ORD,DUR);
// zárezy kľúča: správny kľúč má dno zárezu presne tam, kde kolík končí v deliacej rovine; zlý kľúč má dva zárezy inak
const CUT=LK.map((l,i)=>SHL+l+(WR?[0,-13,0,11,0][i]:0)),PRF=[[0,364],[28,322]];for(let i=4;i>=0;i--){PRF.push([XF-XP[i],CUT[i]]);PRF.push([XF-XP[i]+35,322])}PRF.push([440,322]);
const prof=s=>{if(s<0)return REST;for(let i=1;i<PRF.length;i++)if(s<=PRF[i][0]){const a=PRF[i-1],b=PRF[i];return Math.min(REST,a[1]+(b[1]-a[1])*(s-a[0])/(b[0]-a[0]))}return 322};
const ORDP=[2,0,4,1,3];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
let xt=-1e3,phi=0,bot=[REST,REST,REST,REST,REST],set=[0,0,0,0,0],pick=null,flash=-1;
if(PK){const u=t%12;phi=.05;for(let j=0;j<5;j++){const i=ORDP[j],w=u-.4-j*1.5;if(w<0)continue;if(w<1.5){const up=w<.5?0:w<1.05?sm((w-.5)/.55):1-sm((w-1.15)/.3),lift=REST-(SHL+LK[i]);bot[i]=REST-lift*Math.max(0,up);pick=[XP[i]-(w<.5?(1-sm(w/.5))*60:0),bot[i]];if(w>=1.05){set[i]=1;if(w<1.2)flash=i}}else set[i]=1}
if(u>=8.2)phi=.05+(TAU/4-.05)*(u<9.6?sm((u-8.2)/1.4):u<11?1:1-sm((u-11)/.8));if(u>=7.9)pick=null}
else if(WR){const u=t%8;xt=u<.5?20:u<3?20+(XF-20)*sm((u-.5)/2.5):u<6?XF:XF-(XF-20)*sm((u-6)/1.6);if(u>3.4&&u<5.6)phi=.045*Math.abs(Math.sin((u-3.4)*7))*Math.min(1,(5.6-u)*3);bot=XP.map(q=>prof(xt-q))}
else{const u=t%12;xt=u<1?20:u<4?20+(XF-20)*sm((u-1)/3):u<10.6?XF:XF-(XF-20)*sm((u-10.6)/1.2);phi=u<5?0:u<7.3?TAU/4*sm((u-5)/2.3):u<8.8?TAU/4:u<10.4?TAU/4*(1-sm((u-8.8)/1.6)):0;bot=XP.map(q=>prof(xt-q))}
const top=bot.map((b,i)=>b-LK[i]),ok=top.map((y,i)=>PK?set[i]:Math.abs(y-SHL)<1.6?1:0),nset=ok.reduce((a,b)=>a+b,0),cph=Math.cos(phi),open=phi>.3;
// horné kolíky: ležia na dolných; keď je bubon pootočený, ostanú stáť na jeho povrchu
const dbot=top.map((y,i)=>PK?(set[i]?SHL:y):phi>.02&&ok[i]?SHL:y);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// teleso vložky v reze, komory kolíkov
const body=()=>{x.beginPath();x.roundRect(200,112,500,188,10)};body();x.fillStyle='#1b1e22';x.fill();hatch(x,body);x.strokeStyle='#fff';x.lineWidth=3.5;body();x.stroke();
x.beginPath();x.roundRect(200,420,500,44,8);x.fillStyle='#1b1e22';x.fill();x.stroke();
x.fillStyle='#0c0e11';XP.forEach(q=>x.fillRect(q-12,138,24,SHL-138));
// bubon: valec, v ktorom je kľúčová dráha a dolné kolíky
x.fillStyle='#2a2f35';x.fillRect(200,SHL,470,120);x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(200,SHL,470,120);x.fillStyle='#8f959c';x.beginPath();x.roundRect(670,330,34,60,4);x.fill();x.stroke();
x.save();x.translate(0,AX);x.scale(1,Math.max(.02,cph));x.translate(0,-AX);
x.fillStyle='#0c0e11';x.fillRect(200,318,452,70);XP.forEach(q=>x.fillRect(q-12,SHL,24,30));
// kľúč
if(xt>-900){x.beginPath();PRF.forEach((q,i)=>i?x.lineTo(xt-q[0],q[1]):x.moveTo(xt-q[0],q[1]));x.lineTo(xt-440,296);x.lineTo(xt-452,296);x.lineTo(xt-452,404);x.lineTo(xt-440,404);x.lineTo(xt-440,386);x.lineTo(xt-10,386);x.lineTo(xt,376);x.closePath();x.fillStyle='#c9ced3';x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
x.beginPath();x.roundRect(xt-560,286,110,128,26);x.fill();x.stroke();x.fillStyle='#0c0e11';x.beginPath();x.arc(xt-520,350,14,0,TAU);x.fill();x.stroke()}
// dolné kolíky (rôzne dlhé, so špičkou)
XP.forEach((q,i)=>{x.fillStyle=A;x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.moveTo(q-9,top[i]);x.lineTo(q+9,top[i]);x.lineTo(q+9,bot[i]-9);x.lineTo(q,bot[i]);x.lineTo(q-9,bot[i]-9);x.closePath();x.fill();x.stroke()});
x.restore();
// horné kolíky a pružiny
XP.forEach((q,i)=>{const b=dbot[i],tp=b-DL;x.fillStyle=WR&&!ok[i]&&xt>=XF-1?mix('#c9ced3',HOT,.5+.5*Math.sin(t*10)):'#c9ced3';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.roundRect(q-9,tp,18,DL,3);x.fill();x.stroke();
x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=2.2;x.beginPath();x.moveTo(q,142);const n=9;for(let k=1;k<n;k++)x.lineTo(q+(k%2?7:-7),142+(tp-142)*k/n);x.lineTo(q,tp);x.stroke();
if(flash==i)dot(x,[q,SHL],16,'#fff',p*.8,true)});
// deliaca rovina: svieti, keď ju nič nepretína
x.strokeStyle=nset==5?A:'rgba(255,255,255,.55)';x.lineWidth=nset==5?3.5:2;x.setLineDash(nset==5?[]:[7,6]);x.beginPath();x.moveTo(212,SHL);x.lineTo(660,SHL);x.stroke();x.setLineDash([]);
// planžeta a napínák pri otváraní bez kľúča
if(PK){x.strokeStyle=A;x.lineWidth=5;x.beginPath();x.moveTo(150,440);x.lineTo(150,384);x.lineTo(226,384);x.stroke();
if(pick){x.strokeStyle='#e8ecef';x.lineWidth=4;x.beginPath();x.moveTo(pick[0]-330,356);x.lineTo(pick[0]-16,pick[1]+12);x.lineTo(pick[0]-4,pick[1]+10);x.lineTo(pick[0],pick[1]+1);x.stroke()}}
// pohľad spredu: teleso, bubon s kľúčovou dráhou, jeden stĺpec kolíkov
{const R=58;x.beginPath();x.arc(FC[0],FC[1],R+18,-.25,Math.PI+.25);x.lineTo(FC[0]-19,FC[1]-150);x.lineTo(FC[0]+19,FC[1]-150);x.closePath();x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=3.5;x.stroke();
x.fillStyle='#0c0e11';x.fillRect(FC[0]-9,FC[1]-140,18,140-R);
const kt=top[0],db=dbot[0],f=.62,dby=FC[1]-R+(db-SHL)*f;x.fillStyle='#c9ced3';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.roundRect(FC[0]-7,dby-DL*f,14,DL*f,2);x.fill();x.stroke();
x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=2;x.beginPath();x.moveTo(FC[0],FC[1]-138);for(let k=1;k<7;k++)x.lineTo(FC[0]+(k%2?5:-5),FC[1]-138+(dby-DL*f-(FC[1]-138))*k/7);x.stroke();
x.beginPath();x.arc(FC[0],FC[1],R,0,TAU);x.fillStyle='#2a2f35';x.fill();x.strokeStyle=nset==5?A:'#fff';x.lineWidth=3;x.stroke();
x.save();x.translate(FC[0],FC[1]);x.rotate(phi);x.fillStyle='#0c0e11';x.fillRect(-7,-R,14,R+34);x.fillStyle=A;x.strokeStyle='#fff';x.lineWidth=1.6;const ky=-R+(kt-SHL)*f;x.beginPath();x.rect(-6,ky,12,LK[0]*f);x.fill();x.stroke();
if(xt>=XP[0]){x.fillStyle='#c9ced3';x.beginPath();x.rect(-5,-R+(bot[0]-SHL)*f,10,(386-bot[0])*f);x.fill();x.stroke()}
x.fillStyle='#8f959c';x.beginPath();x.roundRect(-8,R-6,16,34,4);x.fill();x.stroke();x.restore()}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[1],330,78,XP[1]+2,dbot[1]-DL+8);lead(S,LN[0],250,520,XP[0],Math.min(top[0]+16,AX));lead(S,LN[2],590,78,640,SHL);lead(S,LN[3],790,520,FC[0]+30,FC[1]+30);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(nset),'OF 5 PINS FREE',A,a,fi>=0);badge(S,open?'OPEN':'LOCKED',open?'PLUG TURNS':nset==5?'READY TO TURN':'PINS BLOCK IT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
