// Presné modely 7 – visutý most a krídlo lietadla.
// Hýbe sa len to, čo sa hýbe naozaj: po moste ide nákladiak, mostovka sa pod ním prehne a ťah ide lanom do veží a kotiev;
// okolo krídla prúdi vzduch (hore rýchlejšie), vztlak rastie s uhlom nábehu a pri odtrhnutí prúdenia padne.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};

// ---------- visutý most: l = [mostovka, závesy, hlavné lano, veže, kotvenie]; f = deck | hangers | cable | towers | anchor | wind (rozkmitanie vetrom) | gap (dilatačná škára) ----------
PRO.bridge=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),WN=F=='wind',GP=F=='gap';
const DY=362,TX=[250,650],TT=128,WY=476,AN=[[44,378],[856,378]];
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={deck:[450,356,zf*1.7],hangers:[450,304,zf*1.9],cable:[340,220,zf*1.8],towers:[250,300,zf*1.5],anchor:[100,372,zf*2.2],wind:[450,322,zf*1.3],gap:[790,368,zf*3.1]},ORD=['deck','hangers','cable','towers','anchor'],KF=cams(d,FULL,FV,ORD,DUR);
const cab0=X=>{if(X<TX[0]){const u=(X-AN[0][0])/(TX[0]-AN[0][0]);return AN[0][1]+(TT-AN[0][1])*u+16*Math.sin(Math.PI*u)}if(X>TX[1]){const u=(X-TX[1])/(AN[1][0]-TX[1]);return TT+(AN[1][1]-TT)*u+16*Math.sin(Math.PI*u)}return 330-202*Math.pow((X-450)/200,2)};
const env=X=>X>TX[0]&&X<TX[1]?Math.min(1,(X-TX[0])/70,(TX[1]-X)/70):0;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const xt=WN||GP?-999:-90+((t*92)%1080),amp=22*cl(t/3.5),g=GP?4+6*(.5+.5*Math.sin(t*.9)):3,XE=800-g;
const dd=X=>WN?env(X)*amp*Math.sin(TAU*(X-250)/400)*Math.sin(t*5.2):env(X)*7*Math.exp(-Math.pow((X-xt)/105,2)),cab=X=>cab0(X)+.55*dd(X);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// voda s vlnami
x.fillStyle='#0b131c';x.fillRect(-300,WY,1500,400);for(let j=0;j<4;j++){x.strokeStyle=`rgba(255,255,255,${.3-.06*j})`;x.lineWidth=2;x.beginPath();for(let X=-300;X<=1200;X+=20){const Y=WY+j*26+3*Math.sin(X*.035+t*(1.4-.2*j)+j*2);X==-300?x.moveTo(X,Y):x.lineTo(X,Y)}x.stroke()}
// vietor (len pri rozkmitaní)
if(WN)for(let i=0;i<16;i++){const X=((t*300+HS(i,31)*1500)%1500)-300,Y=70+HS(i,32)*380;x.strokeStyle='rgba(255,255,255,.28)';x.lineWidth=2.5;x.beginPath();x.moveTo(X,Y);x.lineTo(X+50+HS(i,33)*50,Y);x.stroke()}
// brehy a kotevné bloky
[[-300,100,150],[1200,800,750]].forEach(([a,b,c])=>{x.beginPath();x.moveTo(a,DY+15);x.lineTo(b,DY+15);x.lineTo(c,WY+140);x.lineTo(a,WY+140);x.closePath();x.fillStyle='#14171a';x.fill();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=3;x.stroke()});
AN.forEach(a=>{const bx=()=>{x.beginPath();x.roundRect(a[0]-36,a[1]-4,72,64,6)};bx();x.fillStyle='#474c53';x.fill();hatch(x,bx);bx();x.strokeStyle='#fff';x.lineWidth=3;x.stroke()});
// veže: piliere vo vode, nohy a priečky
TX.forEach(X=>{x.fillStyle='#474c53';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(X-32,WY-16,64,80,5);x.fill();x.stroke();
const gr=x.createLinearGradient(X-14,0,X+14,0);gr.addColorStop(0,'#7b8188');gr.addColorStop(.5,'#eef1f4');gr.addColorStop(1,'#6b7077');x.fillStyle=gr;x.beginPath();x.rect(X-13,TT-10,26,WY-6-TT);x.fill();x.stroke();
x.strokeStyle='rgba(20,22,25,.55)';x.lineWidth=2;for(let Y=TT+26;Y<WY-30;Y+=42){x.beginPath();x.moveTo(X-13,Y);x.lineTo(X+13,Y+20);x.moveTo(X+13,Y);x.lineTo(X-13,Y+20);x.stroke()}
x.fillStyle=A;x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.roundRect(X-17,TT-20,34,12,4);x.fill();x.stroke()});
// cesta na brehoch a mostovka (nosník s priehradou); pri škáre sa koniec mostovky posúva teplom
x.fillStyle='#2a2e33';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.rect(-300,DY,400,15);x.fill();x.stroke();x.beginPath();x.rect(800,DY,400,15);x.fill();x.stroke();
x.beginPath();for(let X=100;X<XE;X+=10)X==100?x.moveTo(X,DY+dd(X)):x.lineTo(X,DY+dd(X));x.lineTo(XE,DY);x.lineTo(XE,DY+15);for(let X=Math.floor(XE/10)*10;X>=100;X-=10)x.lineTo(X,DY+15+dd(X));x.closePath();x.fill();x.stroke();
x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=1.6;x.beginPath();for(let X=110;X<XE-10;X+=20){x.moveTo(X,DY+3+dd(X));x.lineTo(X+10,DY+12+dd(X+10));x.lineTo(X+20,DY+3+dd(X+20))}x.stroke();
x.fillStyle=A;x.fillRect(XE-1,DY-3,g+7,3);
// závesy: tie pri náklade nesú najviac
for(let X=70;X<=830;X+=20){if(Math.abs(X-TX[0])<8||Math.abs(X-TX[1])<8)continue;const c=cab(X),y1=DY+dd(X);if(c>y1-6)continue;const k=Math.exp(-Math.pow((X-xt)/60,2));x.strokeStyle=k>.12?mix('#ffffff',A,k):'rgba(255,255,255,.8)';x.lineWidth=2+1.6*k;x.beginPath();x.moveTo(X,c);x.lineTo(X,y1);x.stroke()}
// hlavné lano
x.strokeStyle='#fff';x.lineWidth=5.5;x.beginPath();for(let X=AN[0][0];X<=AN[1][0];X+=6)X==AN[0][0]?x.moveTo(X,cab(X)):x.lineTo(X,cab(X));x.stroke();
// cesta sily: od nákladu lanom do veží, vežami dolu do základov a bočným lanom do kotiev
if(xt>100&&xt<800){const sl=xt<TX[0]?AN[0][0]:xt<TX[1]?TX[0]:TX[1],sr=xt<TX[0]?TX[0]:xt<TX[1]?TX[1]:AN[1][0];
for(let i=0;i<5;i++){const u=(t*.55+i/5)%1,al=p*Math.sin(Math.PI*u);[sl,sr].forEach(s=>{const X=xt+(s-xt)*u;dot(x,[X,cab(X)],5,A,al,true)});
TX.forEach((X,j)=>{const w=cl(1.25-Math.abs(xt-X)/330);dot(x,[X,TT+(WY-20-TT)*u],5,A,al*w,true);const X2=X+(AN[j][0]-X)*u;if((j?xt<TX[1]:xt>TX[0]))dot(x,[X2,cab(X2)],4,A,al*w*.8,true)})}}
// nákladiak
if(xt>-60&&xt<1140){const Y=DY+(xt>100&&xt<XE?dd(xt):0);x.save();x.translate(xt,Y);x.fillStyle='#d9dde1';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.roundRect(-30,-27,40,21,3);x.fill();x.stroke();x.fillStyle=A;x.beginPath();x.roundRect(12,-22,15,16,3);x.fill();x.stroke();
[-22,-8,19].forEach(X=>dot(x,[X,-5],5,'#16181b',1,false));x.restore()}
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],560,428,560,DY+12);lead(S,LN[1],340,428,350,330);lead(S,LN[2],450,236,380,cab0(380));lead(S,LN[3],250,76,250,TT-20);lead(S,LN[4],150,452,60,420);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',5,ts-.35,A);
if(GP){meter(S,String(Math.round(g*10)),'MM',A,a,false);badge(S,String(Math.round(35-(g-4)/6*45)),'°C',A,a)}
else if(!WN){meter(S,String(Math.round(Math.max(0,dd(xt))*4)),'CM',A,a,fi>=0);badge(S,'40 T','TRUCK',A,a)}
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- krídlo: l = [prúdenie, podtlak, pretlak, vztlak]; f = flow | pressure | lift | stall (odtrhnutie prúdenia) | flap (vztlaková klapka) ----------
PRO.wing=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),STL=F=='stall',FLP=F=='flap',Q=[365,315],C=540;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,292,zf],FV={flow:[280,315,zf*1.6],pressure:[480,262,zf*1.5],lift:[450,240,zf*1.15],stall:[520,262,zf*1.25],flap:[690,355,zf*1.6]},ORD=['flow','pressure','lift'],KF=cams(d,FULL,FV,ORD,DUR);
const th=s=>.6*(.2969*Math.sqrt(s)-.126*s-.3516*s*s+.2843*s*s*s-.1015*s*s*s*s);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const al=STL?4+14*ez(cl((t-.8)/3.2)):4+3*Math.sin(t*.5),ar=al*Math.PI/180,fd=FLP?28*ez(cl((t-.9)/1.6)):0,tf=Math.tan(fd*Math.PI/180),sep=cl((al-13)/4);
const CLn=Math.max(0,Math.min(1.5,(Math.min(al,14)+2)/16*(1-.45*cl((al-14)/3))+.5*fd/28));
const cam=s=>(s<.4?.04/.16*(.8*s-s*s):.04/.36*(.2+.8*s-s*s))-(s>.75?(s-.75)*tf:0),yu=s=>cam(s)+th(s),yl=s=>cam(s)-th(s);
const e=[Math.cos(ar),Math.sin(ar)],n=[Math.sin(ar),-Math.cos(ar)],LE=[Q[0]-.25*C*e[0],Q[1]-.25*C*e[1]],TE=[Q[0]+.75*C*e[0],Q[1]+.75*C*e[1]],P=(s,h)=>[LE[0]+s*C*e[0]+h*C*n[0],LE[1]+s*C*e[1]+h*C*n[1]];
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// prúdnice: ďaleko pred krídlom rovné, pri krídle ho obtekajú, za ním sú sklonené dolu (krídlo tlačí vzduch dolu)
const mm=X=>X<LE[0]?(LE[1]-Q[1])*Math.exp((X-LE[0])/90):X<=TE[0]?LE[1]+(X-LE[0])*Math.tan(ar)-Q[1]:TE[1]-Q[1]+70*Math.tan(ar*.6+fd*.006)*(1-Math.exp(-(X-TE[0])/130));
const Y0s=[-205,-160,-118,-82,-52,-28,-9,9,28,52,82,118,160,205],V0=235,sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u);
Y0s.forEach((Y0,li)=>{const up=Y0<0,ay=Math.abs(Y0),pts=[],tau=[0];let T=0;
for(let X=-160;X<=1060;X+=12){const s=(X-LE[0])/(TE[0]-LE[0]),sc=cl(s),B=s<0?0:s<=1?(up?yu(sc):yl(sc))*C:cam(1)*C*Math.exp(-(X-TE[0])/170);
let Y=Q[1]+Y0+mm(X)*Math.exp(-ay/170)-B*Math.exp(-ay/110);if(up&&sep>0)Y-=sep*Math.exp(-ay/130)*72*(s<1?sm((s-.12)/.8):Math.exp(-(s-1)*.7));
const gb=s>-.1&&s<1.1?Math.sin(Math.PI*(s+.1)/1.2):0,k=Math.exp(-ay/100)*gb,vv=V0*(up?1+.6*CLn*k-(sep*.9*k):1-.25*CLn*k);pts.push([X,Y]);T+=12/Math.max(40,vv);tau.push(T)}
x.strokeStyle='rgba(255,255,255,.32)';x.lineWidth=2;x.beginPath();pts.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();
for(let i=0;i<6;i++){const tp=(t+i*T/6+li*.37)%T;let j=1;while(j<pts.length-1&&tau[j]<tp)j++;const u=(tp-tau[j-1])/((tau[j]-tau[j-1])||1),a0=pts[j-1],a1=pts[j];
dot(x,[a0[0]+(a1[0]-a0[0])*u,a0[1]+(a1[1]-a0[1])*u],3.4,'#cfe6ff',p*.9*Math.min(1,tp*3,(T-tp)*3),false)}});
// odtrhnuté prúdenie: víry nad zadnou časťou krídla
if(sep>0)for(let k=0;k<6;k++){const s=.3+.13*k,c=P(s,yu(Math.min(1,s))+.035+.03*k*sep),r=8+5*k*sep;x.strokeStyle=`rgba(255,255,255,${.55*sep})`;x.lineWidth=2.4;x.beginPath();x.arc(c[0],c[1],r,t*(4-.3*k)+k,t*(4-.3*k)+k+4.3);x.stroke()}
// krídlo (profil); klapka je zadná štvrtina
{x.beginPath();for(let i=0;i<=40;i++){const s=i/40,ss=.5*s*s*(3-2*s)+.5*s,r=P(ss,yu(ss));i?x.lineTo(r[0],r[1]):x.moveTo(r[0],r[1])}for(let i=40;i>=0;i--){const s=i/40,ss=.5*s*s*(3-2*s)+.5*s,r=P(ss,yl(ss));x.lineTo(r[0],r[1])}x.closePath();
const gr=x.createLinearGradient(0,Q[1]-60,0,Q[1]+70);gr.addColorStop(0,'#f2f4f6');gr.addColorStop(.55,'#b9bec4');gr.addColorStop(1,'#70757c');x.fillStyle=gr;x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
const h0=P(.75,yu(.75)),h1=P(.75,yl(.75));x.strokeStyle=FLP?A:'rgba(20,22,25,.6)';x.lineWidth=2.5;x.beginPath();x.moveTo(h0[0],h0[1]);x.lineTo(h1[0],h1[1]);x.stroke()}
// tlak: hore podtlak ťahá krídlo nahor (šípky od krídla), dole pretlak tlačí (šípky ku krídlu)
const arw=(a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(9,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};
[.07,.19,.32,.46,.6,.74].forEach(s=>{const L=40*CLn*(1.2-s)*(1-.75*sep)/C;if(L*C>5){x.globalAlpha=p*.95;arw(P(s,yu(s)+.014),P(s,yu(s)+.014+L),A,3)}const L2=20*CLn*(1.1-s)/C;if(L2*C>4){x.globalAlpha=p*.75;arw(P(s,yl(s)-.014-L2),P(s,yl(s)-.014),'#fff',2.6)}});x.globalAlpha=p;
// vztlak: jedna veľká šípka, dĺžka podľa uhla nábehu
const lb=P(.3,.02),lt=[lb[0],lb[1]-46-150*CLn];arw([lb[0],lb[1]-34],lt,A,9);
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],120,96,120,Q[1]-160);lead(S,LN[1],650,128,P(.42,yu(.42)+.07)[0],P(.42,yu(.42)+.07)[1]);lead(S,LN[2],630,486,P(.4,yl(.4)-.05)[0],P(.4,yl(.4)-.05)[1]);lead(S,LN[3],lt[0]+96,lt[1]+6,lt[0]+8,lt[1]+10);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[[0,1,3][fi]]||'',3,ts-.35,A);
meter(S,String(Math.round(al)),'° ANGLE',A,a,fi>=0);badge(S,String(Math.round(CLn*100))+' %','LIFT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
