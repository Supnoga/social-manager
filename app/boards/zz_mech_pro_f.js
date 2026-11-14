// Presné modely 6 – stavby a obrana: raziaci štít (tunel) v reze zboku a radar.
// Hýbe sa len to, čo sa hýbe naozaj: rezná hlava, lisy, závitovka, pás a nový prstenec; pri radare impulz, ozvena, anténa za cieľom a lietadlo.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge,integ,edge,bearing}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};

// ---------- raziaci štít: l = [rezná hlava, lisy, ostenie, dopravník]; f = cutter | jacks | rings | conveyor ----------
// Cyklus ako v skutočnosti: stroj razí a lisy ho tlačia dopredu o šírku prstenca, potom stojí, lisy sa stiahnu a postaví sa nový prstenec. Na obraze je cyklus zrýchlený.
PRO.tunnel=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,CY=290,R=150,W=72,FACE=742,XR=470,CYC=5.2,BORE=.68;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,290,zf],FV={cutter:[672,290,zf*1.65],jacks:[540,196,zf*2.2],rings:[392,196,zf*2.1],conveyor:[452,352,zf*1.8]},ORD=['cutter','jacks','rings','conveyor'],KF=cams(d,FULL,FV,ORD,DUR);
const spin=t=>{const u=((t/CYC)%1+1)%1;return cl(u/.06)*cl((BORE-u)/.06)},steel=['#5b6067','#eef1f4','#565b62'];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const u=(t/CYC)%1,nR=Math.floor(t/CYC),boring=u<BORE,s=boring?W*ez(u/BORE):W,b=boring?0:(u-BORE)/(1-BORE),G=nR*W+s,aC=integ(spin,t)*1.1,on=spin(t);
const xf=boring?XR-s:XR-W,xj=boring?XR-s:XR-W+W*ez(b/.28),q=ez((b-.3)/.5);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
// zemina: vrstvy a kamene sa posúvajú dozadu tak, ako stroj postupuje
x.fillStyle='#17130e';x.fillRect(-260,-240,1420,1080);
x.lineWidth=2;for(let j=0;j<9;j++){const Y=-150+j*100;x.strokeStyle=`rgba(190,160,120,${j%2?.13:.2})`;x.beginPath();for(let X=-280;X<=1180;X+=40){const yy=Y+18*Math.sin((X+G)*.011+j*1.7)+8*Math.sin((X+G)*.031+j);X==-280?x.moveTo(X,yy):x.lineTo(X,yy)}x.stroke()}
for(let i=0;i<70;i++){const X=((HS(i,11)*1440-G)%1440+1440)%1440-260,Y=-220+HS(i,12)*1040;dot(x,[X,Y],2+3.5*HS(i,13),'#6b5a44',.55,false)}
// vyrazený tunel a ostenie z prstencov
x.fillStyle='#06070a';x.fillRect(-260,CY-R,FACE+260,2*R);
const seg=(X,Y,a)=>{x.globalAlpha=p*a;const g=x.createLinearGradient(0,Y,0,Y+18);g.addColorStop(0,'#aab0b7');g.addColorStop(1,'#6c7178');x.fillStyle=g;x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(X,Y,W,18);x.fill();x.stroke();x.globalAlpha=p};
for(let k=0;k<11;k++){const X=xf-(k+1)*W;seg(X,CY-R,1);seg(X,CY+R-18,1);x.strokeStyle='rgba(255,255,255,.13)';x.lineWidth=2;x.beginPath();x.moveTo(X,CY-R+18);x.lineTo(X,CY+R-18);x.stroke()}
// pás s vyťaženou zeminou (beží len pri razení)
x.strokeStyle='#3a3f45';x.lineWidth=7;x.beginPath();x.moveTo(-260,CY+58);x.lineTo(560,CY+58);x.stroke();x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=1.5;x.beginPath();x.moveTo(-260,CY+62);x.lineTo(560,CY+62);x.stroke();
for(let X=-240;X<560;X+=66){x.beginPath();x.arc(X,CY+69,5,0,TAU);x.fillStyle='#4a4f56';x.fill();x.stroke()}
for(let i=0;i<26;i++){const uu=(t*.42+i/26)%1,X=552-uu*812;dot(x,[X,CY+50-3*HS(i,21)],4+2.5*HS(i,22),'#8a6f4c',spin(t-uu/.42)*cl(uu/.03),false)}
// závitovka: vynáša zeminu z komory na pás
{const P0=[704,CY+116],P1=[556,CY+40],L=Math.hypot(P1[0]-P0[0],P1[1]-P0[1]),an=Math.atan2(P1[1]-P0[1],P1[0]-P0[0]);x.save();x.translate(P0[0],P0[1]);x.rotate(an);x.fillStyle='#1b1e22';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(0,-13,L,26);x.fill();x.stroke();
x.save();x.beginPath();x.rect(2,-11,L-4,22);x.clip();x.strokeStyle='#b9bec4';x.lineWidth=3;const o=(aC*9)%18;for(let X=-18+o;X<L+18;X+=18){x.beginPath();x.moveTo(X,-11);x.lineTo(X+9,11);x.stroke()}
for(let i=0;i<7;i++){const uu=(t*.5+i/7)%1;dot(x,[uu*L,4*Math.sin(i*2.1)],4,'#8a6f4c',on*.9,false)}x.restore();x.restore()}
// plášť štítu (stojí voči stroju), prepážka a pohon hlavy
x.fillStyle='#2c3035';x.strokeStyle='#fff';x.lineWidth=3;[CY-R-6,CY+R-8].forEach(Y=>{x.beginPath();x.rect(XR-30,Y,FACE-XR+8,14);x.fill();x.stroke()});
x.fillStyle='#4a4f56';x.lineWidth=2.5;x.beginPath();x.rect(660,CY-R+8,12,2*R-16);x.fill();x.stroke();
x.beginPath();x.roundRect(580,CY-50,80,100,8);x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();bearing(x,650,CY-34,16,24);bearing(x,650,CY+34,16,24);
edge(x,690,CY,58,24,24,aC,4,{col:steel,tooth:'#30343a',lw:3,ow:2.5});
// komora so zeminou za hlavou
for(let i=0;i<34;i++){const X=676+HS(i,31)*30,Y=CY-R+30+((HS(i,32)*260+t*70*on*(.5+HS(i,33)))%260);dot(x,[X,Y],3+3*HS(i,34),'#8a6f4c',.85,false)}
// rezná hlava: točí sa pri razení, pri stavbe prstenca stojí
edge(x,724,CY,30,R+3,R+3,aC,16,{tooth:A,lw:4,col:['#33373c','#9aa0a6','#2f3237'],ow:3});
for(let k=0;k<9;k++){const phi=aC+k*TAU/9+HS(k,41),c=Math.cos(phi);if(c<.1)continue;const Y=CY+(26+k*13.5)*Math.sin(phi)*(k%2?1:-1);x.globalAlpha=p*(.35+.65*c);x.fillStyle='#d5dade';x.strokeStyle='#fff';x.lineWidth=1.5;x.beginPath();x.roundRect(738,Y-7,11,14,3);x.fill();x.stroke()}x.globalAlpha=p;
for(let i=0;i<12;i++){const uu=(t*1.6+HS(i,51))%1;dot(x,[748-uu*26,CY-R+12+HS(i,52)*(2*R-24)+uu*uu*40],2.6,'#b08a5c',on*(1-uu),false)}
// lisy: opierajú sa o posledný prstenec a tlačia štít dopredu; pri stavbe prstenca sa stiahnu
[CY-R+24,CY+R-46].forEach(Y=>{x.fillStyle='#d5dade';x.strokeStyle='#fff';x.lineWidth=1.5;x.beginPath();x.rect(xj,Y+6,566-xj,10);x.fill();x.stroke();
x.fillStyle='#4a4f56';x.lineWidth=2.5;x.beginPath();x.roundRect(562,Y,96,22,4);x.fill();x.stroke();x.fillStyle=boring?A:'#8f959c';x.beginPath();x.roundRect(xj-9,Y-5,10,32,2);x.fill();x.stroke()});
// nový prstenec: dielce idú zo stredu na svoje miesto
if(!boring&&q>0){x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=3;[[CY-R,-1],[CY+R-18,1]].forEach(([Y1,sg])=>{const Y=CY-9+sg*26+(Y1-(CY-9+sg*26))*q;x.beginPath();x.moveTo(xf+W/2+52,CY);x.lineTo(xf+W/2,Y+9);x.stroke();seg(xf,Y,cl(q*3))});dot(x,[xf+W/2+52,CY],7,'#d5dade',1,false)}
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],716,76,726,CY-R-10);lead(S,LN[1],560,76,606,CY-R+22);lead(S,LN[2],330,76,330,CY-R+2);lead(S,LN[3],250,CY+R+62,250,CY+64);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(Math.round(80*on)),'MM/MIN',A,a,fi>=0);badge(S,String(nR+(b>.8?1:0)),D.lang=='en'?'RINGS':'',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- radar: l = [anténa, impulz, cieľ, obrazovka]; f = antenna | pulse | target | screen | stealth | chaff | doppler | clutter (ozvena sa odrazí inam) ----------
// Impulz letí k lietadlu, ozvena sa vracia; obrazovka meria čas tam a späť. Vzdialenosť a čas sú spočítané z polohy lietadla (1 km = 10 bodov).
PRO.radar=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),ST=F=='stealth',CH=F=='chaff',DP=F=='doppler',CL=F=='clutter',C0=[158,372],GY=520,KS=1.4,C=[158,GY+(372-GY)*KS],T=2.6;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,292,zf],FV={antenna:[200,350,zf*1.7],pulse:[440,268,zf*1.12],target:[660,140,zf*1.8],screen:[706,452,zf*2.1],stealth:[640,165,zf*1.6],chaff:[700,178,zf*1.4],doppler:[440,268,zf*1.12],clutter:[430,255,zf*1.25]},ORD=['antenna','pulse','target','screen'],KF=cams(d,FULL,FV,ORD,DUR);
const PL=t=>[716-7*t,138+5*Math.sin(t*.5)];
let al0=1;const arcs=(c,th,r,half,col,al,gp)=>{for(let k=0;k<3;k++){const rr=r-k*(gp||16);if(rr<8)continue;x.strokeStyle=col;x.globalAlpha=al*(1-k*.3);x.lineWidth=6.5-k*1.6;x.beginPath();x.arc(c[0],c[1],rr,th-half,th+half);x.stroke()}x.globalAlpha=al0};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=al0=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const P=PL(t),Dp=Math.hypot(P[0]-C[0],P[1]-C[1]),th=Math.atan2(P[1]-C[1],P[0]-C[0]),tau=(t%T),km=Dp/10,us=Math.round(km*6.67);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
// nočná obloha a zem
for(let i=0;i<46;i++)dot(x,[-200+HS(i,61)*1300,-180+HS(i,62)*640],1+1.4*HS(i,63),'#fff',.25+.3*HS(i,64),false);
x.fillStyle='#0d0f12';x.fillRect(-300,GY,1500,400);x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=3;x.beginPath();x.moveTo(-300,GY);x.lineTo(1200,GY);x.stroke();
// lúč antény (kam sa díva)
x.fillStyle='rgba(255,255,255,.06)';x.beginPath();x.moveTo(C[0],C[1]);x.lineTo(C[0]+Math.cos(th-.16)*1100,C[1]+Math.sin(th-.16)*1100);x.lineTo(C[0]+Math.cos(th+.16)*1100,C[1]+Math.sin(th+.16)*1100);x.closePath();x.fill();
// impulz tam (biely) a ozvena späť (farba kanála); pri stealth sa ozvena odrazí preč od antény
if(tau<1.02)arcs(C,th,Dp*tau,.15,'#fff',p*cl(tau/.05)*(1-.35*tau));
if(tau>=1&&tau<2.02){const e=tau-1,back=th+Math.PI;if(ST){arcs(P,back+1.9,Dp*e*.8,.3,'#fff',p*.75*(1-e));arcs(P,back-1.5,Dp*e*.8,.3,'#fff',p*.6*(1-e));arcs(P,back,Dp*e,.2,A,p*.12*(1-.4*e))}else{arcs(P,back,Dp*e,.22,A,p*(.95-.45*e),DP?8:16);if(CH)arcs([P[0]+170,P[1]+46],back,Dp*e,.3,A,p*(.95-.45*e))}}
const FC=[C[0]+(P[0]-C[0])*.55,C[1]+(P[1]-C[1])*.55+30];if(CL&&tau>=.55&&tau<1.3)arcs(FC,th+Math.PI,Dp*(tau-.55),.2,A,p*.55*(1-(tau-.55)/.75),11);
// stanica: podstavec stojí, tanier sa nakláňa za cieľom
x.save();x.translate(158,GY);x.scale(KS,KS);x.translate(-158,-GY);x.fillStyle='#16191d';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.moveTo(118,GY);x.lineTo(138,430);x.lineTo(178,430);x.lineTo(198,GY);x.closePath();x.fill();x.stroke();
x.fillStyle='#4a4f56';x.beginPath();x.rect(146,C0[1]-6,24,64);x.fill();x.stroke();
x.save();x.translate(C0[0],C0[1]);x.rotate(th);x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=2.5;x.beginPath();x.moveTo(-6,-66);x.lineTo(52,0);x.lineTo(-6,66);x.stroke();
x.beginPath();for(let k=0;k<=20;k++){const yy=-72+k*7.2,xx=yy*yy/170-34;k?x.lineTo(xx,yy):x.moveTo(xx,yy)}for(let k=20;k>=0;k--){const yy=-72+k*7.2;x.lineTo(yy*yy/170-44,yy)}x.closePath();
{const g=x.createLinearGradient(0,-72,0,72);g.addColorStop(0,'#7b8188');g.addColorStop(.45,'#eef1f4');g.addColorStop(1,'#6b7077');x.fillStyle=g;x.fill()}x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();
x.fillStyle=tau<.12?'#fff':A;x.beginPath();x.roundRect(46,-9,18,18,4);x.fill();x.stroke();x.restore();
dot(x,C0,9,'#d5dade',1,false);x.restore();
// lietadlo (letí k radaru); stealth má hranatý tvar, ktorý odráža vlny do strán
x.save();x.translate(P[0],P[1]);x.scale(1.5,1.5);x.fillStyle=ST?'#2b2f35':'#d9dde1';x.strokeStyle='#fff';x.lineWidth=2.5;x.lineJoin='round';x.beginPath();
if(ST){x.moveTo(-70,4);x.lineTo(-8,-14);x.lineTo(62,-6);x.lineTo(78,6);x.lineTo(20,14);x.closePath()}
else{x.moveTo(-74,2);x.quadraticCurveTo(-66,-12,-36,-13);x.lineTo(40,-13);x.lineTo(62,-40);x.lineTo(74,-40);x.lineTo(66,-11);x.quadraticCurveTo(84,-6,80,6);x.lineTo(-52,12);x.quadraticCurveTo(-70,10,-74,2);x.closePath()}
x.fill();x.stroke();if(!ST){x.fillStyle='#8f959c';x.beginPath();x.moveTo(-14,2);x.lineTo(26,2);x.lineTo(44,18);x.lineTo(10,18);x.closePath();x.fill();x.stroke()}
if(tau>=1&&tau<1.5)dot(x,[-74,2],10+30*(tau-1),ST?'#fff':A,(ST?.25:.6)*(1-(tau-1)*2),false);x.restore();
// klamné ciele: oblak hliníkových pásikov za lietadlom (chaff) alebo kŕdeľ vtákov v lúči (clutter) – oba vracajú vlastnú ozvenu
if(CH)for(let i=0;i<46;i++){const an=t*(1+HS(i,74)*2)+i*1.7,px=P[0]+84+HS(i,71)*190+t*2,py=P[1]+6+HS(i,72)*78+((t*5+HS(i,73)*30)%30)*.5;x.strokeStyle='#e8ecef';x.lineWidth=2.2;x.globalAlpha=p*(.35+.65*Math.abs(Math.sin(an)));x.beginPath();x.moveTo(px-Math.cos(an)*5,py-Math.sin(an)*5);x.lineTo(px+Math.cos(an)*5,py+Math.sin(an)*5);x.stroke()}
if(CL)for(let i=0;i<9;i++){const bx=FC[0]-64+HS(i,81)*128+Math.sin(t*.8+i)*6,by=FC[1]-30+HS(i,82)*56,fl=Math.sin(t*9+i*2)*5;x.strokeStyle='#fff';x.lineWidth=2.6;x.lineJoin='round';x.beginPath();x.moveTo(bx-9,by-fl);x.lineTo(bx,by);x.lineTo(bx+9,by-fl);x.stroke()}
x.globalAlpha=p;
// obrazovka: čiara času; prvý vrchol = vyslaný impulz, druhý = ozvena. Odstup medzi nimi je čas tam a späť.
{const X0=566,Y0=388,WW=290,HH=136,bx=X0+22,by=Y0+HH-30,tx=u=>bx+u/2.3*(WW-44);x.beginPath();x.roundRect(X0,Y0,WW,HH,14);x.fillStyle='#0b0d10';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.strokeStyle='rgba(255,255,255,.1)';x.lineWidth=1;for(let k=1;k<6;k++){x.beginPath();x.moveTo(X0+k*WW/6,Y0+8);x.lineTo(X0+k*WW/6,Y0+HH-8);x.stroke()}
const col='#fff',pk=(u0,h,c)=>{if(tau<u0)return;const X=tx(u0);x.strokeStyle=c;x.beginPath();x.moveTo(X-8,by);x.lineTo(X,by-h);x.lineTo(X+8,by);x.stroke()};
x.strokeStyle=col;x.lineWidth=4;x.lineJoin='round';x.beginPath();x.moveTo(bx,by);x.lineTo(tx(Math.min(tau,2.3)),by);x.stroke();pk(.04,82,col);pk(2,ST?7:54,A);if(CL)[1.02,1.09,1.15,1.22].forEach((u,i)=>pk(u,13+HS(i,91)*10,A));
if(CH&&tau>=2.07){const X1=tx(2.07),X2=tx(2.27);x.beginPath();x.moveTo(X1,by);x.lineTo(X1+9,by-70);x.lineTo(X2-8,by-60);x.lineTo(X2,by);x.fillStyle=rgba(A,.4);x.fill();x.strokeStyle=A;x.stroke()}
dot(x,[tx(Math.min(tau,2.3)),by],5,col,1,true);
if(tau>=2&&!ST){x.strokeStyle=A;x.lineWidth=2.5;const Y=Y0+20,a0=tx(.04),a1=tx(2);x.beginPath();x.moveTo(a0,Y-6);x.lineTo(a0,Y+6);x.moveTo(a0,Y);x.lineTo(a1,Y);x.moveTo(a1,Y-6);x.lineTo(a1,Y+6);x.stroke()}}
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],286,478,214,404);lead(S,LN[1],380,180,C[0]+Math.cos(th)*250,C[1]+Math.sin(th)*250);lead(S,LN[2],P[0]-40,48,P[0],P[1]-26);lead(S,LN[3],711,356,711,386);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(Math.round(km)),'KM',A,a,fi>=0);badge(S,DP?'900':String(us),DP?'KM/H':'µs',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
