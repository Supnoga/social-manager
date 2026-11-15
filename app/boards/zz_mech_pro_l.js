// Presné modely 12 – plavebná komora (pozdĺžny rez) a dráha družice (spočítaná podľa gravitácie).
// Hýbe sa len to, čo sa hýbe naozaj: voda tečie samospádom cez kanál v dne, hladina v komore dvíha loď, vráta sa otvoria až pri rovnakej hladine;
// družica padá okolo Zeme rýchlosťou, ktorá sedí k výške, prechodová dráha je elipsa podľa Keplera.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),EL='#8fd0ff',HOT='#ff6a3d',WAT='#3c8cd2';
const arw=(x,a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(4+w*2,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};
const lens=P=>{const c=[0];for(let i=1;i<P.length;i++)c.push(c[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));return c};
const at=(P,c,s)=>{let i=1;while(i<P.length-1&&c[i]<s)i++;const u=(s-c[i-1])/Math.max(1e-6,c[i]-c[i-1]);return [P[i-1][0]+(P[i][0]-P[i-1][0])*u,P[i-1][1]+(P[i][1]-P[i-1][1])*u]};

PRO.canal_lock=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),UP=230,LO=400,FL=470,UB=330,GU=250,GL=650,PORTS=[300,375,450,525,600];
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,352,zf*1.06],FV={gates:[640,340,zf*1.8],valves:[235,430,zf*2.1],chamber:[450,440,zf*1.9],ship:[450,310,zf*1.5],fill:[450,360,zf*1.2],drain:[450,360,zf*1.2]},ORD=['gates','valves','chamber','ship'],KF=cams(d,FULL,FV,ORD,DUR);
const lvl=u=>u<4?LO:u<9?LO-(LO-UP)*sm((u-4)/5):u<14.3?UP:u<17.3?UP+(LO-UP)*sm((u-14.3)/3):LO;
const sxf=u=>u<3?900-450*(1-Math.pow(1-u/3,2)):u<10?450:450-(u-10)*(u-10)*34;
const gLo=u=>u<3?1:u<4?1-sm(u-3):u<17.3?0:sm((u-17.3)/.7),gUp=u=>u<9?0:u<10?sm(u-9):u<13.5?1:u<14.3?1-sm((u-13.5)/.8):0;
const vF=u=>u>=4&&u<9?Math.min(1,sm((u-4)/.4),sm((9-u)/.4)):0,vD=u=>u>=14.3&&u<17.3?Math.min(1,sm((u-14.3)/.4),sm((17.3-u)/.4)):0;
const PF=[[205,338],[205,505],[600,505]],CF=lens(PF),PD=[[300,505],[695,505],[695,462]],CD=lens(PD),CC=[A,'#c9ced3','#5fa8e6','#8f959c'];
const ship=(sx,wl)=>{x.save();x.translate(sx,wl);x.lineWidth=1.2;x.strokeStyle='rgba(0,0,0,.55)';
for(let i=0;i<8;i++)for(let j=0;j<2+(i%3==1?1:0);j++){x.fillStyle=CC[(i*3+j*5)%4];x.beginPath();x.rect(-104+i*22,-44-j*14,20,12);x.fill();x.stroke()}
x.fillStyle='#e8ecef';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.roundRect(80,-78,28,48,3);x.fill();x.stroke();x.fillStyle='#16181b';x.fillRect(84,-72,20,6);
x.beginPath();x.moveTo(-124,-30);x.lineTo(118,-30);x.lineTo(112,36);x.quadraticCurveTo(110,40,100,40);x.lineTo(-92,40);x.quadraticCurveTo(-112,34,-124,-30);x.closePath();x.fillStyle='#2a2f35';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.strokeStyle=A;x.lineWidth=2.5;x.beginPath();x.moveTo(-118,-8);x.lineTo(115,-8);x.stroke();x.restore()};
const gate=(gx,top,bot,g)=>{const w=14+62*g;x.globalAlpha*=1-.6*g;x.fillStyle='#8f959c';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(gx+7-w,top,w,bot-top);x.fill();x.stroke();x.globalAlpha/=1-.6*g};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const u=F=='fill'?3+(t%7.5):F=='drain'?13.4+(t%4.6):t%18,L=lvl(u),sx=sxf(u),gl=gLo(u),gu=gUp(u),vf=vF(u),vd=vD(u),wl=sx>GL?LO:sx<GU?UP:L;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// zadná stena komory s korunou
x.fillStyle='rgba(255,255,255,.05)';x.fillRect(GU,196,GL-GU,FL-196);x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=3;x.beginPath();x.moveTo(GU-70,196);x.lineTo(GL+10,196);x.stroke();
x.strokeStyle='rgba(255,255,255,.12)';x.lineWidth=1.5;for(let k=1;k<9;k++){x.beginPath();x.moveTo(GU,196+k*30);x.lineTo(GL,196+k*30);x.stroke()}
if(gl>.5)gate(GL,205,FL,gl);if(gu>.5)gate(GU,205,UB,gu);
if(sx>-260)ship(sx,wl);
// voda: horná zdrž, komora, dolná zdrž
x.fillStyle=rgba(WAT,.42);x.fillRect(-300,UP,GU+300,UB-UP);x.fillRect(GU,L,GL-GU,FL-L);x.fillRect(GL,LO,700,FL-LO);
x.strokeStyle='#9fd4ff';x.lineWidth=2.5;x.beginPath();x.moveTo(-300,UP);x.lineTo(GU,UP);x.moveTo(GU,L);x.lineTo(GL,L);x.moveTo(GL,LO);x.lineTo(1300,LO);x.stroke();
// betón v reze: dno hornej zdrže, prah, dno komory
const gr=()=>{x.beginPath();x.moveTo(-300,UB);x.lineTo(GU+7,UB);x.lineTo(GU+7,FL);x.lineTo(1300,FL);x.lineTo(1300,640);x.lineTo(-300,640);x.closePath()};
gr();x.fillStyle='#1b1e22';x.fill();hatch(x,gr);x.strokeStyle='#fff';x.lineWidth=3.5;x.beginPath();x.moveTo(-300,UB);x.lineTo(GU+7,UB);x.lineTo(GU+7,FL);x.lineTo(1300,FL);x.stroke();
// obtokový kanál v dne s vtokom, výtokom a otvormi do komory
x.fillStyle='#173e5f';x.fillRect(197,UB,16,183);x.fillRect(197,497,506,16);x.fillRect(687,FL,16,43);PORTS.forEach(q=>x.fillRect(q-5,FL,10,27));
x.strokeStyle='rgba(255,255,255,.45)';x.lineWidth=1.5;x.beginPath();x.moveTo(213,UB);x.lineTo(213,497);x.moveTo(197,UB);x.lineTo(197,513);x.lineTo(703,513);x.lineTo(703,FL);x.stroke();
// uzávery: plniaci vo vtoku, vypúšťací pred výtokom
x.strokeStyle='rgba(255,255,255,.4)';x.strokeRect(169,412,26,14);x.strokeRect(653,515,14,24);
x.fillStyle=A;x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(193-22*vf,414,24,10);x.fill();x.stroke();x.beginPath();x.rect(655,493+22*vd,10,24);x.fill();x.stroke();
// prúdenie: pri plnení z hornej zdrže do komory, pri vypúšťaní z komory do dolnej zdrže
if(vf>0){for(let i=0;i<12;i++){const q=at(PF,CF,((t*150+i*CF[2]/12)%CF[2]+CF[2])%CF[2]);dot(x,q,3.2,'#cfe9ff',p*vf,false)}
PORTS.forEach((q,i)=>{arw(x,[q,464],[q,464-30*vf],'#cfe9ff',3);for(let k=0;k<3;k++){const w=((t*.9+k/3+i*.17)%1);dot(x,[q+(HS(i,k)-.5)*16,460-w*70],2.6,'#cfe9ff',p*vf*(1-w),false)}})}
if(vd>0){for(let i=0;i<12;i++){const q=at(PD,CD,((t*150+i*CD[2]/12)%CD[2]+CD[2])%CD[2]);dot(x,q,3.2,'#cfe9ff',p*vd,false)}
PORTS.forEach(q=>arw(x,[q,430],[q,430+30*vd],'#cfe9ff',3));arw(x,[712,455],[712+34*vd,440],'#cfe9ff',3)}
if(gl<=.5)gate(GL,205,FL,gl);if(gu<=.5)gate(GU,205,UB,gu);
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],770,150,GL+2,208);lead(S,LN[1],105,566,192,424);lead(S,LN[2],450,116,450,196);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,((LO-L)/(LO-UP)*9).toFixed(1),'M LIFT',A,a,fi>=0);badge(S,'0','PUMPS',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

const earth=(x,C,R,rot)=>{const g=x.createRadialGradient(C[0]-R*.35,C[1]-R*.35,R*.1,C[0],C[1],R);g.addColorStop(0,'#2f7fd0');g.addColorStop(1,'#0e2f5c');
x.save();x.beginPath();x.arc(C[0],C[1],R,0,TAU);x.fillStyle=g;x.fill();x.clip();x.fillStyle='rgba(140,210,170,.42)';
for(let i=0;i<7;i++){const a=rot+i*.9+HS(i,3)*.5,q=R*(.2+.62*HS(i,5));x.beginPath();x.ellipse(C[0]+Math.cos(a)*q,C[1]+Math.sin(a)*q,R*(.16+.2*HS(i,7)),R*(.1+.14*HS(i,9)),a,0,TAU);x.fill()}
x.restore();const w=Math.max(3,R*.07);x.strokeStyle='rgba(140,200,255,.25)';x.lineWidth=w;x.beginPath();x.arc(C[0],C[1],R+w/2,0,TAU);x.stroke();x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.arc(C[0],C[1],R,0,TAU);x.stroke()};
const sat=(x,P,ang,k,A)=>{x.save();x.translate(P[0],P[1]);x.rotate(ang);x.scale(k,k);x.fillStyle='#5fa8e6';x.strokeStyle='#fff';x.lineWidth=1.6;[[-21,-4],[9,-4]].forEach(q=>{x.beginPath();x.rect(q[0],q[1],12,8);x.fill();x.stroke()});x.fillStyle='#e8ecef';x.beginPath();x.roundRect(-8,-7,16,14,2);x.fill();x.stroke();x.fillStyle=A;x.beginPath();x.arc(0,8,3,0,TAU);x.fill();x.restore()};
const ring=(x,C,r,col,w,ds)=>{x.strokeStyle=col;x.lineWidth=w;x.setLineDash(ds||[]);x.beginPath();x.arc(C[0],C[1],r,0,TAU);x.stroke();x.setLineDash([])};

PRO.orbit=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),C=[450,310],ST=['fall','transfer','types','decay','launch'].includes(F)?F:'',RE=ST=='types'?36:ST=='transfer'?70:110,om=TAU/6;
const zf=Math.min(S.w/900,S.h/600)*.98,FV={gravity:[450,170,zf*2],speed:[450,170,zf*2],path:[450,310,zf*1.3],fall:[450,296,zf*1.55],transfer:[440,310,zf*1.42],types:[450,310,zf*1.02],decay:[450,310,zf*1.25],launch:[450,300,zf*1.25]},FULL=ST?FV[ST]:[450,310,zf*1.12],ORD=['gravity','speed','path'],KF=cams(d,FULL,FV,ORD,DUR);
// Newtonovo delo: tri výstrely, dráhy spočítané krok po kroku z gravitácie
const R0=RE+22,VC=150,GM=VC*VC*R0,T0=[.6,3.2,6],SH=[.6,.85].map(f=>{const pts=[];let px=0,py=-R0,vx=f*VC,vy=0;for(let k=0;k<1400;k++){if(k%4==0)pts.push([px,py]);const r=Math.hypot(px,py);if(r<RE)break;const g=-GM/(r*r*r);vx+=g*px/240;vy+=g*py/240;px+=vx/240;py+=vy/240}return pts});
// prechod na vyššiu dráhu: polovica elipsy medzi dvoma kruhmi
const r1=100,r2=190,aa=(r1+r2)/2,ec=(r2-r1)/(r2+r1),T1=4,Te=T1*Math.pow(aa/r1,1.5),T2=T1*Math.pow(r2/r1,1.5),tB=T1,tC=T1+Te/2,TP=tC+4.2;
const ell=tau=>{const M=TAU*tau/Te;let Ek=M;for(let i=0;i<7;i++)Ek-=(Ek-ec*Math.sin(Ek)-M)/(1-ec*Math.cos(Ek));return [aa*(1-ec*Math.cos(Ek)),-2*Math.atan2(Math.sqrt(1+ec)*Math.sin(Ek/2),Math.sqrt(1-ec)*Math.cos(Ek/2))]};
const pol=(r,th)=>[C[0]+r*Math.cos(th),C[1]+r*Math.sin(th)];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8).slice(),zi=ez((cm[2]/zf-1)/.22),[FN,ts]=shot(KF,d,t);
let mv='7.8',mu='KM/S',bb='90',bs='MIN PER LAP';const th0=-1.2-om*t,P0=pol(150,th0);
if(!ST){const w=Math.min(1,zi)*cl(1-Math.hypot(cm[0]-450,cm[1]-170)/90);cm[0]+=(P0[0]-450)*w;cm[1]+=(P0[1]-170)*w}
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
if(ST=='types'){const rr=[39,150,238],TT=[1.6,12,24],rot=TAU*t/24,ga=rot-1.1;earth(x,C,RE,rot);
rr.forEach((r,i)=>ring(x,C,r,'rgba(255,255,255,.4)',1.8,i?[6,7]:[]));
const G=pol(238,ga),gs=pol(RE,ga);x.strokeStyle=rgba(A,.6);x.lineWidth=1.6;x.setLineDash([4,5]);x.beginPath();x.moveTo(gs[0],gs[1]);x.lineTo(G[0],G[1]);x.stroke();x.setLineDash([]);dot(x,gs,3.5,A,p,false);
sat(x,pol(39,.4+TAU*t/TT[0]),.4+TAU*t/TT[0]+TAU/4,.42,A);sat(x,pol(150,2.4+TAU*t/TT[1]),2.4+TAU*t/TT[1]+TAU/4,.8,A);sat(x,G,ga+TAU/4,.9,A);
x.globalAlpha=p*sp;tag(S,LN[5]||'',450,310-238+24,'center','#fff',20);tag(S,LN[4]||'',450,310-150+22,'center','#fff',20);lead(S,LN[3]||'',290,470,C[0]-28,C[1]+28);x.globalAlpha=p;
mv='90';mu='MIN LOW LAP';bb='24';bs='H HIGH LAP'}
else if(ST=='fall'){const u=t%13;earth(x,C,RE,t*TAU/96);
x.fillStyle='#8f959c';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.moveTo(C[0]-18,C[1]-RE+3);x.lineTo(C[0]-3,C[1]-R0+5);x.lineTo(C[0]+4,C[1]-R0+5);x.lineTo(C[0]+18,C[1]-RE+3);x.closePath();x.fill();x.stroke();
x.fillStyle='#e8ecef';x.beginPath();x.roundRect(C[0]-10,C[1]-R0-4,24,9,3);x.fill();x.stroke();
let cur=-1;for(let i=0;i<3;i++){const ta=u-T0[i];if(ta<0)continue;cur=i;if(ta<.14)dot(x,[C[0]+18,C[1]-R0],10,'#ffd27a',p*(1-ta/.14),true);
if(i<2){const pts=SH[i],n=Math.min(pts.length-1,Math.floor(ta*60));x.strokeStyle='#e8ecef';x.lineWidth=2.6;x.setLineDash([6,5]);x.beginPath();x.moveTo(C[0],C[1]-R0);for(let k=1;k<=n;k++)x.lineTo(C[0]+pts[k][0],C[1]+pts[k][1]);x.stroke();x.setLineDash([]);dot(x,[C[0]+pts[n][0],C[1]+pts[n][1]],5,'#e8ecef',p,n<pts.length-1)}
else{const ph=VC/R0*ta;x.strokeStyle=A;x.lineWidth=3;x.beginPath();x.arc(C[0],C[1],R0,-TAU/4,-TAU/4+Math.min(ph,TAU));x.stroke();dot(x,pol(R0,-TAU/4+ph),6,A,p,true)}}
mv=cur<0?'0.0':['4.7','6.7','7.9'][cur];bb=cur<0?'FIRE':cur<2?'FALLS':'ORBIT';bs=cur<0?'SIDEWAYS':cur<2?'TOO SLOW':'NEVER LANDS'}
else if(ST=='transfer'){const u=t%TP;let r,th,vr,ph;if(u<tB){r=r1;th=-TAU*u/T1;vr=1;ph=0}else if(u<tC){[r,th]=ell(u-tB);vr=Math.sqrt(r1*(2/r-1/aa));ph=1}else{r=r2;th=-Math.PI-TAU*(u-tC)/T2;vr=Math.sqrt(r1/r2);ph=2}
earth(x,C,RE,t*TAU/96);ring(x,C,r1,'rgba(255,255,255,.4)',2,[6,7]);ring(x,C,r2,'rgba(255,255,255,.4)',2,[6,7]);
x.strokeStyle='rgba(255,255,255,.16)';x.lineWidth=2;x.setLineDash([3,7]);x.beginPath();x.ellipse(C[0]-aa*ec,C[1],aa,aa*Math.sqrt(1-ec*ec),0,0,TAU);x.stroke();x.setLineDash([]);
if(ph>0){x.strokeStyle=A;x.lineWidth=3;x.beginPath();x.moveTo(C[0]+r1,C[1]);const e=Math.min(u,tC)-tB;for(let w=.05;w<e;w+=.05){const q=ell(w);x.lineTo(C[0]+q[0]*Math.cos(q[1]),C[1]+q[0]*Math.sin(q[1]))}const q=ell(e);x.lineTo(C[0]+q[0]*Math.cos(q[1]),C[1]+q[0]*Math.sin(q[1]));x.stroke()}
if(ph==2){x.strokeStyle=A;x.lineWidth=3;x.beginPath();x.arc(C[0],C[1],r2,th,-Math.PI);x.stroke()}
const P=pol(r,th),vd=[Math.sin(th),-Math.cos(th)],b=Math.max(0,1-Math.abs(u-tB)/.4,1-Math.abs(u-tC)/.4,u<.2?1-u/.2-.6:0);
if(b>0){const n=[-vd[1],vd[0]],L=34*b+6*HS(Math.floor(t*30),2);x.fillStyle='#ffd27a';x.globalAlpha=p*Math.min(1,b*1.6);x.beginPath();x.moveTo(P[0]+n[0]*5,P[1]+n[1]*5);x.lineTo(P[0]-vd[0]*L,P[1]-vd[1]*L);x.lineTo(P[0]-n[0]*5,P[1]-n[1]*5);x.closePath();x.fill();x.globalAlpha=p;dot(x,P,12,HOT,p*.5*b,true)}
sat(x,P,th+TAU/4,.95,A);mv=(7.8*vr).toFixed(1);bb=b>.05?'BURN':ph==0?'LOW':ph==1?'COAST':'HIGH';bs=b>.05?'ENGINE ON':ph==1?'ENGINE OFF':'ORBIT'}
else if(ST=='decay'){const u=t%10,ub=Math.min(u,8),n=Math.round(ub*60),pts=[];let th=-1,r=150;for(let k=0;k<=n;k++){const w=k/60;r=150-36*(w/8)*(w/8);pts.push(pol(r,th));th-=om*Math.pow(150/r,1.5)/60}
x.strokeStyle='rgba(140,200,255,.16)';x.lineWidth=18;x.beginPath();x.arc(C[0],C[1],RE+9,0,TAU);x.stroke();earth(x,C,RE,t*TAU/96);ring(x,C,150,'rgba(255,255,255,.3)',2,[6,7]);
const P=pts[n],Q=pts[Math.max(0,n-2)],h=cl((130-r)/14);x.strokeStyle=A;x.lineWidth=2.6;for(let c=0;c<6;c++){const i0=Math.max(0,n-(c+1)*30),i1=Math.max(0,n-c*30);if(i1<=i0)break;x.globalAlpha=p*(1-c/6)*.9;x.beginPath();x.moveTo(pts[i0][0],pts[i0][1]);for(let k=i0+1;k<=i1;k++)x.lineTo(pts[k][0],pts[k][1]);x.stroke()}x.globalAlpha=p;
if(u<8){const dl=Math.hypot(P[0]-Q[0],P[1]-Q[1])||1,vd=[(P[0]-Q[0])/dl,(P[1]-Q[1])/dl];if(h>0)dot(x,P,9+7*h,HOT,p*.6*h,true);if(n>3)arw(x,[P[0]-vd[0]*12,P[1]-vd[1]*12],[P[0]-vd[0]*(26+16*h),P[1]-vd[1]*(26+16*h)],EL,2.6);sat(x,P,Math.atan2(P[1]-C[1],P[0]-C[0])+TAU/4,.95,A)}
else if(u<8.8){const k=(u-8)/.8;dot(x,P,8+22*k,HOT,p*(1-k),true);for(let i=0;i<6;i++)dot(x,[P[0]+(HS(i,1)-.5)*50*k,P[1]+(HS(i,2)-.5)*50*k],2.4,'#ffd27a',p*(1-k),false)}
mv=u<8?String(Math.round((r-RE)*10)):'0';mu='KM UP';bb='DRAG';bs='THIN AIR'}
else if(ST=='launch'){const u=t%12,n=Math.round(u*60),pts=[];let th=-TAU/4;for(let k=0;k<=n;k++){const w=k/60;pts.push(pol(RE+40*sm(w/4),th));th+=om*sm((w-.8)/4.2)/60}
earth(x,C,RE,t*TAU/96);ring(x,C,150,'rgba(255,255,255,.3)',2,[6,7]);x.fillStyle='#8f959c';x.fillRect(C[0]-9,C[1]-RE-3,18,4);
x.strokeStyle=A;x.lineWidth=2.6;x.beginPath();x.moveTo(pts[0][0],pts[0][1]);for(let k=Math.max(1,n-420);k<=n;k++)x.lineTo(pts[k][0],pts[k][1]);if(n>420){x.beginPath();x.moveTo(pts[n-420][0],pts[n-420][1]);for(let k=n-419;k<=n;k++)x.lineTo(pts[k][0],pts[k][1])}x.stroke();
const P=pts[n],Q=pts[Math.max(0,n-3)],hd=n>3?Math.atan2(P[1]-Q[1],P[0]-Q[0]):-TAU/4;x.save();x.translate(P[0],P[1]);x.rotate(hd+TAU/4);
if(u<5&&u>.05){const L=16+8*HS(Math.floor(t*30),4);x.fillStyle='#ffd27a';x.beginPath();x.moveTo(-4,12);x.lineTo(0,12+L);x.lineTo(4,12);x.closePath();x.fill()}
x.fillStyle='#eef1f4';x.strokeStyle='#fff';x.lineWidth=1.5;x.beginPath();x.moveTo(0,-19);x.quadraticCurveTo(5,-12,5,-6);x.lineTo(5,12);x.lineTo(-5,12);x.lineTo(-5,-6);x.quadraticCurveTo(-5,-12,0,-19);x.closePath();x.fill();x.stroke();x.fillStyle=A;x.fillRect(-5,-2,10,4);x.beginPath();x.moveTo(-5,6);x.lineTo(-10,13);x.lineTo(-5,12);x.moveTo(5,6);x.lineTo(10,13);x.lineTo(5,12);x.fill();x.restore();
mv=(7.8*sm((Math.min(u,5)-.8)/4.2)).toFixed(1);mu='KM/S SIDEWAYS';bb=String(Math.round(400*sm(Math.min(u,4)/4)));bs='KM UP'}
else{const cs=Math.cos(th0),sn=Math.sin(th0),vd=[sn,-cs];earth(x,C,RE,t*TAU/96);ring(x,C,150,'rgba(255,255,255,.35)',2,[6,7]);
x.strokeStyle=A;x.lineWidth=3;for(let k=0;k<14;k++){x.globalAlpha=p*(1-k/14)*.9;x.beginPath();x.arc(C[0],C[1],150,th0+k*.11,th0+(k+1)*.11+.01);x.stroke()}x.globalAlpha=p;
x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=2;x.setLineDash([4,6]);x.beginPath();x.moveTo(P0[0]+vd[0]*58,P0[1]+vd[1]*58);x.lineTo(P0[0]+vd[0]*150,P0[1]+vd[1]*150);x.stroke();x.setLineDash([]);
arw(x,[P0[0]-cs*12,P0[1]-sn*12],[P0[0]-cs*46,P0[1]-sn*46],HOT,4);arw(x,[P0[0]+vd[0]*14,P0[1]+vd[1]*14],[P0[0]+vd[0]*56,P0[1]+vd[1]*56],A,4);sat(x,P0,th0+TAU/4,1,A);
x.globalAlpha=p*sp;tag(S,LN[0]||'',P0[0]-cs*30-vd[0]*46,P0[1]-sn*30-vd[1]*46,'center',HOT,18);tag(S,LN[1]||'',P0[0]+vd[0]*40+cs*26,P0[1]+vd[1]*40+sn*26,'center',A,18);
x.globalAlpha=p*sp*(1-zi);lead(S,LN[2]||'',748,120,C[0]+150*Math.cos(-.75),C[1]+150*Math.sin(-.75));x.globalAlpha=p}
x.restore();
const fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',3,ts-.35,A);
meter(S,mv,mu,A,a,fi>=0);badge(S,bb,bs,A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
