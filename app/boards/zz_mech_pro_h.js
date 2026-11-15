// Presné modely 8 – priehrada s vodnou elektrárňou (rez) a ponorka (rez zboku).
// Hýbe sa len to, čo sa hýbe naozaj: voda tečie potrubím a točí turbínu, generátor dáva prúd do siete;
// ponorka napúšťa a vyfukuje balastné nádrže, klesá a stúpa, vrtuľa sa točí, kormidlá sa nakláňajú.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},WC='#7cc4ff',sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u);
const along=(P,u)=>{let L=0;const ls=P.slice(1).map((q,i)=>{const l=Math.hypot(q[0]-P[i][0],q[1]-P[i][1]);L+=l;return l});let s=cl(u)*L;for(let i=0;i<ls.length;i++){if(s<=ls[i]||i==ls.length-1){const k=ls[i]?Math.min(1,s/ls[i]):0;return [P[i][0]+(P[i+1][0]-P[i][0])*k,P[i][1]+(P[i+1][1]-P[i][1])*k]}s-=ls[i]}return P[0]};
const arw=(x,a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(4+w*2,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};
const pipe=(x,P,w)=>{x.lineJoin='round';x.lineCap='butt';x.beginPath();P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.strokeStyle='#fff';x.lineWidth=w+7;x.stroke();x.strokeStyle='#12283c';x.lineWidth=w;x.stroke()};

// ---------- priehrada: l = [nádrž, hrádza, prívodné potrubie, turbína, generátor]; f = reservoir | wall | penstock | turbine | generator | spill (prepad) | pressure (tlak vody) | arch (klenbová hrádza zhora) ----------
PRO.dam=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),SPL=F=='spill',PRS=F=='pressure',ARC=F=='arch',BED=470,WL=SPL?133:172;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,318,zf],FV={reservoir:[240,318,zf*1.5],wall:[462,312,zf*1.6],penstock:[505,372,zf*2.1],turbine:[646,446,zf*2.6],generator:[652,386,zf*2.6],spill:[520,322,zf*1.35],pressure:[400,322,zf*1.6],arch:[450,300,zf]},ORD=['reservoir','wall','penstock','turbine','generator'],KF=cams(d,FULL,FV,ORD,DUR);
const PP=[[396,300],[470,326],[592,432],[632,448]],DT=[[640,474],[672,490],[736,484]],face=Y=>404-(Y-150)*12/340,AC=[650,300],AR=232,HA=.76;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22),Q=215+35*Math.sin(t*.45),MW=Math.round(1000*9.81*Q*120*.9/1e6);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
if(ARC){
// pohľad zhora: klenba opretá o steny kaňonu, tlak vody ide oblúkom do skaly
[[140,1],[460,-1]].forEach(([y0,sg])=>{x.beginPath();x.moveTo(-300,y0);for(let X=-240;X<=1200;X+=60)x.lineTo(X,y0+sg*8*HS(X+400,3));x.lineTo(1200,y0-sg*500);x.lineTo(-300,y0-sg*500);x.closePath();x.fillStyle='#17191d';x.fill();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=3;x.stroke()});
x.beginPath();x.moveTo(-300,146);x.lineTo(AC[0]+AR*Math.cos(Math.PI+HA),146);x.arc(AC[0],AC[1],AR,Math.PI+HA,Math.PI-HA,true);x.lineTo(-300,454);x.closePath();x.fillStyle='rgba(40,110,175,.5)';x.fill();
for(let i=0;i<5;i++){x.strokeStyle='rgba(255,255,255,.22)';x.lineWidth=2;x.beginPath();for(let Y=160;Y<=440;Y+=20){const X=60+i*70+4*Math.sin(Y*.05+t*1.2+i);Y==160?x.moveTo(X,Y):x.lineTo(X,Y)}x.stroke()}
x.fillStyle='rgba(40,110,175,.35)';x.fillRect(AC[0]-AR+30,284,900,32);
x.strokeStyle='#5a6068';x.lineWidth=28;x.lineCap='butt';x.beginPath();x.arc(AC[0],AC[1],AR-14,Math.PI-HA,Math.PI+HA);x.stroke();x.strokeStyle='#fff';x.lineWidth=3.5;[AR,AR-28].forEach(r=>{x.beginPath();x.arc(AC[0],AC[1],r,Math.PI-HA,Math.PI+HA);x.stroke()});
for(let k=-3;k<=3;k++){const th=Math.PI+k*.2,c=Math.cos(th),s=Math.sin(th);arw(x,[AC[0]+(AR+62)*c,AC[1]+(AR+62)*s],[AC[0]+(AR+9)*c,AC[1]+(AR+9)*s],A,4)}
for(let i=0;i<5;i++){const u=(t*.5+i/5)%1;[1,-1].forEach(g=>{const th=Math.PI+g*u*HA;dot(x,[AC[0]+(AR-14)*Math.cos(th),AC[1]+(AR-14)*Math.sin(th)],5.5,A,p*Math.sin(Math.PI*u),true)})}
[1,-1].forEach(g=>{const th=Math.PI+g*HA,e=[AC[0]+(AR-14)*Math.cos(th),AC[1]+(AR-14)*Math.sin(th)],dx=.69,dy=-.725*g;arw(x,[e[0]+dx*8,e[1]+dy*8],[e[0]+dx*62,e[1]+dy*62],'#fff',5.5)});
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],200,236,200,300);lead(S,LN[1],590,214,AC[0]+(AR-14)*Math.cos(Math.PI+.42),AC[1]+(AR-14)*Math.sin(Math.PI+.42))
}else{
// skala, vzdialený svah, voda v nádrži
x.fillStyle='#0f1114';x.beginPath();x.moveTo(770,500);x.lineTo(1200,330);x.lineTo(1200,500);x.closePath();x.fill();
x.fillStyle='#14171a';x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=3;x.beginPath();x.moveTo(-300,BED);x.lineTo(380,BED);x.lineTo(380,BED+24);x.lineTo(562,BED+24);x.lineTo(562,502);x.lineTo(1200,502);x.lineTo(1200,900);x.lineTo(-300,900);x.closePath();x.fill();x.stroke();
const wy=X=>WL+2.5*Math.sin(X*.03+t*1.3),fx=face(WL);x.beginPath();x.moveTo(-300,wy(-300));for(let X=-280;X<fx;X+=20)x.lineTo(X,wy(X));x.lineTo(fx,WL);x.lineTo(face(BED),BED);x.lineTo(-300,BED);x.closePath();
{const g=x.createLinearGradient(0,WL,0,BED);g.addColorStop(0,'rgba(60,140,210,.55)');g.addColorStop(1,'rgba(20,50,90,.6)');x.fillStyle=g;x.fill()}
x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=2.5;x.beginPath();x.moveTo(-300,wy(-300));for(let X=-280;X<fx;X+=20)x.lineTo(X,wy(X));x.lineTo(fx,WL);x.stroke();
// hrádza: betón, dole najhrubšia (tam je tlak vody najväčší)
const wall=()=>{x.beginPath();x.moveTo(388,BED+24);x.lineTo(404,150);x.lineTo(428,140);x.lineTo(468,140);x.lineTo(478,172);x.lineTo(552,BED+24);x.closePath()};wall();x.fillStyle='#5a6068';x.fill();hatch(x,wall);wall();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
if(SPL){
// prepad: voda ide cez korunu, dolu po hrádzi a v tlmiacej nádrži sa upokojí
const SP=[[fx-6,WL],[430,133],[468,133],[484,170],[552,452],[604,486],[720,480],[1200,480]];x.fillStyle='rgba(40,110,175,.5)';x.fillRect(562,474,640,28);
x.strokeStyle='rgba(124,196,255,.5)';x.lineWidth=12;x.beginPath();SP.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();
for(let i=0;i<34;i++){const u=(t*.42+HS(i,5))%1,q=along(SP,u);dot(x,[q[0]+(HS(i,6)-.5)*8,q[1]+(HS(i,7)-.5)*8],2.4+HS(i,8)*2.2,'#e8f4ff',p*.9,false)}
for(let i=0;i<18;i++){const X=560+HS(i,9)*120,h=Math.abs(Math.sin(t*5+i*1.7))*26*HS(i,10);x.fillStyle='rgba(255,255,255,.5)';x.beginPath();x.arc(X,478-h,4+HS(i,11)*6,0,TAU);x.fill()}
}else{
// dolná voda, prívodné potrubie, strojovňa s turbínou a generátorom, vedenie do siete
x.fillStyle='rgba(40,110,175,.5)';x.fillRect(736,466,470,36);x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2;x.beginPath();for(let X=736;X<=1200;X+=16){const Y=466+2*Math.sin(X*.05-t*2);X==736?x.moveTo(X,Y):x.lineTo(X,Y)}x.stroke();
pipe(x,PP,17);x.fillStyle='#1b1e22';x.strokeStyle='#fff';x.lineWidth=3.5;x.lineJoin='round';x.beginPath();x.rect(586,362,150,140);x.fill();x.stroke();
pipe(x,[[610,440],[632,448]],17);pipe(x,DT,14);
for(let i=0;i<9;i++)dot(x,along(PP,(t*.5*Q/215+i/9)%1),3.8,WC,p*.95,false);for(let i=0;i<4;i++)dot(x,along(DT,(t*.8+i/4)%1),3.2,WC,p*.9,false);for(let i=0;i<5;i++){const u=(t*.25+i/5)%1;dot(x,[740+u*440,472],3,WC,p*.8*(1-u),false)}
{const c=[640,448];x.fillStyle='#0e1a26';x.strokeStyle='#fff';x.lineWidth=3.5;x.beginPath();x.arc(c[0],c[1],29,0,TAU);x.fill();x.stroke();x.strokeStyle='#dfe3e7';x.lineWidth=3.6;x.lineCap='round';
for(let k=0;k<8;k++){const a=t*6+k*TAU/8;x.beginPath();x.moveTo(c[0]+7*Math.cos(a),c[1]+7*Math.sin(a));x.quadraticCurveTo(c[0]+16*Math.cos(a+.5),c[1]+16*Math.sin(a+.5),c[0]+23*Math.cos(a+.95),c[1]+23*Math.sin(a+.95));x.stroke()}dot(x,c,6,'#c9ced3',p,false)}
x.fillStyle='#b9bec4';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(636,404,8,16);x.fill();x.stroke();
x.fillStyle='#2a2e33';x.lineWidth=3;x.beginPath();x.roundRect(604,370,72,34,5);x.fill();x.stroke();x.fillStyle=A;[608,660].forEach(X=>{x.beginPath();x.roundRect(X,375,10,24,3);x.fill()});
x.save();x.beginPath();x.rect(622,377,36,20);x.clip();x.fillStyle='#c9ced3';x.fillRect(622,377,36,20);x.strokeStyle='#16181b';x.lineWidth=3;for(let k=-1;k<5;k++){const X=622+((t*46)%9)+k*9;x.beginPath();x.moveTo(X,377);x.lineTo(X,397);x.stroke()}x.restore();
x.fillStyle='#474c53';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(694,334,30,28,4);x.fill();x.stroke();x.strokeStyle='rgba(255,255,255,.85)';x.lineWidth=2.2;x.beginPath();x.moveTo(676,386);x.lineTo(709,386);x.lineTo(709,362);x.stroke();
const W=[[709,334],[900,304],[1200,262]];x.beginPath();x.moveTo(709,334);x.quadraticCurveTo(800,334,900,304);x.quadraticCurveTo(1050,300,1200,262);x.stroke();
x.lineWidth=2.6;x.beginPath();x.moveTo(886,448);x.lineTo(900,298);x.lineTo(914,448);x.moveTo(878,306);x.lineTo(922,306);x.moveTo(882,328);x.lineTo(918,328);x.moveTo(889,410);x.lineTo(909,360);x.moveTo(911,410);x.lineTo(891,360);x.stroke();
for(let i=0;i<4;i++){const u=(t*.7+i/4)%1,q=along(W,u);dot(x,[q[0],q[1]+(u<.39?9*Math.sin(Math.PI*u/.39):0)],4.5,A,p*Math.sin(Math.PI*u),true)}}
// tlak vody rastie s hĺbkou: šípky na návodnej strane
if(PRS){for(let k=1;k<=7;k++){const Y=WL+k*(BED-WL)/7.6,L=10+k*10;arw(x,[face(Y)-10-L,Y],[face(Y)-9,Y],A,3.6)}arw(x,[458,236],[458,352],'#fff',6)}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],170,112,170,WL+46);lead(S,LN[1],500,92,452,142);if(!SPL){lead(S,LN[2],604,266,520,368);lead(S,LN[3],560,560,636,478);lead(S,LN[4],800,392,678,388)}}
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',5,ts-.35,A);
if(PRS){meter(S,'120','M DEEP',A,a,false);badge(S,'12','BAR',A,a)}else if(!ARC&&!SPL){meter(S,String(Math.round(Q)),'M³/S',A,a,fi>=0);badge(S,String(MW),'MW',A,a)}
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- ponorka: l = [balastné nádrže, stlačený vzduch, tlakový trup, vrtuľa, hĺbkové kormidlá]; f = tanks | air | hull | propeller | planes | dive | surface | sonar ----------
PRO.submarine=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),DV=F=='dive',SF=F=='surface',SN=F=='sonar',CY=318,R=60,X0=150,X1=770;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[455,308,zf*1.3],FV={tanks:[705,322,zf*2],air:[650,300,zf*2.3],hull:[460,318,zf*1.5],propeller:[160,318,zf*2.3],planes:[480,250,zf*2],dive:[455,300,zf*1.2],surface:[455,300,zf*1.2],sonar:[600,318,zf*1.15]},ORD=['tanks','air','hull','propeller','planes'],KF=cams(d,FULL,FV,ORD,DUR);
const dp=u=>u<8.8?200*sm((u-1.8)/4.6):200*(1-sm((u-8.8)/3.6)),bf=u=>u<1?0:u<3.2?(u-1)/2.2:u<6.5?1:u<7.2?1-.18*(u-6.5)/.7:u<8.6?.82:u<10.6?.82*(1-(u-8.6)/2):0;
const hull=()=>{x.beginPath();x.moveTo(X0+90,CY-R);x.lineTo(X1-80,CY-R);x.bezierCurveTo(X1-20,CY-R,X1,CY-30,X1,CY);x.bezierCurveTo(X1,CY+30,X1-20,CY+R,X1-80,CY+R);x.lineTo(X0+90,CY+R);x.bezierCurveTo(X0+30,CY+R,X0+5,CY+14,X0-10,CY+8);x.lineTo(X0-10,CY-8);x.bezierCurveTo(X0+5,CY-14,X0+30,CY-R,X0+90,CY-R);x.closePath()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22),[FN,ts]=shot(KF,d,t);
const u=DV?Math.min(t,7.6):SF?8.2+Math.min(t,4.7):t%13,dep=dp(u),b=bf(u),dv=(dp(u+.05)-dp(u-.05))/6,vent=u>1&&u<3.2,blow=u>8.6&&u<10.6||(u>6.5&&u<7.2),pit=Math.max(-.07,Math.min(.07,dv*.012)),ys=292-dep*4;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// more: hladina ide hore, keď ponorka klesá; čiastočky ukazujú pohyb dopredu a do hĺbky
x.fillStyle=`rgba(24,70,115,${.52-.2*dep/200})`;x.fillRect(-300,Math.max(-400,ys),1500,1400);if(ys>-300){x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=2.5;x.beginPath();for(let X=-300;X<=1200;X+=20){const Y=ys+3*Math.sin(X*.03+t*1.6);X==-300?x.moveTo(X,Y):x.lineTo(X,Y)}x.stroke()}
for(let i=0;i<44;i++){const X=((HS(i,21)*1500-t*70)%1500+1500)%1500-300,Y=((HS(i,22)*900-dep*4)%900+900)%900-150;if(Y>ys+6)dot(x,[X,Y],1.4+1.6*HS(i,23),'#cfe6ff',p*(.25+.3*HS(i,24)),false)}
x.save();x.translate(460,CY);x.rotate(pit);x.translate(-460,-CY);
// sonar: zvukový impulz z provy
if(SN)for(let k=0;k<3;k++){const r=(t*150+k*125)%375;x.strokeStyle=A;x.globalAlpha=p*(1-r/375);x.lineWidth=5;x.beginPath();x.arc(X1-30,CY,30+r,-.55,.55);x.stroke()}x.globalAlpha=p;
// vrtuľa, kormidlá a veža
{x.fillStyle='#c9ced3';x.strokeStyle='#fff';x.lineWidth=2;for(let k=0;k<3;k++){const h=36*Math.sin(t*9+k*TAU/3);x.beginPath();x.ellipse(X0-19,CY+h/2,5.5,Math.abs(h)/2+.5,0,0,TAU);x.fill();x.stroke()}x.beginPath();x.roundRect(X0-26,CY-6,18,12,4);x.fill();x.stroke()}
x.fillStyle='#22262b';x.strokeStyle='#fff';x.lineWidth=3.5;[[1,-1],[1,1]].forEach(([q,g])=>{x.beginPath();x.moveTo(X0+22,CY+g*14);x.lineTo(X0+34,CY+g*50);x.lineTo(X0+58,CY+g*50);x.lineTo(X0+64,CY+g*22);x.closePath();x.fill();x.stroke()});
x.beginPath();x.moveTo(436,CY-R+2);x.lineTo(446,CY-R-54);x.lineTo(508,CY-R-54);x.quadraticCurveTo(520,CY-R-30,524,CY-R+2);x.closePath();x.fill();x.stroke();x.lineWidth=3;x.beginPath();x.moveTo(474,CY-R-54);x.lineTo(474,CY-R-84);x.moveTo(488,CY-R-54);x.lineTo(488,CY-R-72);x.stroke();
// vonkajší trup a v ňom balastné nádrže (voda zdola, vzduch hore)
hull();x.fillStyle='#22262b';x.fill();x.save();hull();x.clip();[[X0-12,246],[694,X1+4]].forEach(([a0,a1])=>{x.fillStyle='#0a0c0f';x.fillRect(a0,CY-R,a1-a0,2*R);if(blow){x.fillStyle=rgba(A,.22);x.fillRect(a0,CY-R,a1-a0,2*R)}x.fillStyle='rgba(90,170,235,.62)';x.fillRect(a0,CY+R-b*2*R,a1-a0,b*2*R+2);
if(b>.02&&b<.99){x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=2;x.beginPath();x.moveTo(a0,CY+R-b*2*R);x.lineTo(a1,CY+R-b*2*R);x.stroke()}});x.restore();
hull();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
// tlakový trup s priestormi posádky
x.beginPath();x.roundRect(250,CY-47,440,94,42);x.fillStyle='#0d1013';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.strokeStyle='rgba(255,255,255,.45)';x.lineWidth=2;x.beginPath();[340,452,566].forEach(X=>{x.moveTo(X,CY-46);x.lineTo(X,CY+46)});x.moveTo(266,CY+8);x.lineTo(674,CY+8);x.stroke();
x.fillStyle='#3a3e44';x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=2;[[278,CY-30,46,32,6],[360,CY-28,74,30,6],[468,CY-22,30,26,4],[512,CY-22,30,26,4],[590,CY-26,84,11,5],[590,CY-9,84,11,5],[360,CY+18,74,18,4],[470,CY+18,80,18,4]].forEach(q=>{x.beginPath();x.roundRect(q[0],q[1],q[2],q[3],q[4]);x.fill();x.stroke()});
x.strokeStyle='#8f959c';x.lineWidth=4;x.beginPath();x.moveTo(X0-8,CY);x.lineTo(278,CY-14);x.stroke();
// fľaše so stlačeným vzduchom, odvzdušňovacie ventily hore a otvory dole
[[256,-1,232],[648,1,704]].forEach(([fx,g,tx])=>{x.beginPath();x.roundRect(fx,CY+24,38,14,7);x.fillStyle=rgba(A,.3);x.fill();x.strokeStyle=A;x.lineWidth=2.5;x.stroke();
const P1=[[fx+19,CY+24],[fx+19+g*30,CY-52],[tx,CY-50]];if(blow)for(let i=0;i<4;i++)dot(x,along(P1,(t*1.2+i/4)%1),4,A,p,true);
x.fillStyle=vent?A:'#8f959c';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.roundRect(tx-8,CY-R-7,16,7,2);x.fill();x.stroke();
const vy=CY-R-8;if(vent)for(let i=0;i<9;i++){const k=(t*.9+HS(i,31+tx))%1;x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=1.8;x.beginPath();x.arc(tx+(HS(i,32)-.5)*26*k,vy-k*150,2.5+3.5*HS(i,33),0,TAU);x.stroke()}
const by=CY+R-2;x.strokeStyle='#fff';x.lineWidth=3;x.setLineDash([5,5]);x.beginPath();x.moveTo(tx-12,by);x.lineTo(tx+12,by);x.stroke();x.setLineDash([]);
if(vent||blow)for(let i=0;i<4;i++){const k=(t*1.3+i/4)%1,Y=vent?by+34-k*40:by-6+k*40;dot(x,[tx+(i-1.5)*6,Y],3,WC,p*Math.sin(Math.PI*k),false)}});
// hĺbkové kormidlá: na veži a na korme, nakláňajú sa pri klesaní a stúpaní
[[480,CY-R-30,1],[X0+70,CY,-1]].forEach(([px,py,g])=>{x.save();x.translate(px,py);x.rotate(g*dv*.035);x.fillStyle='#c9ced3';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.roundRect(-26,-4.5,52,9,4);x.fill();x.stroke();x.restore()});
// tlak vody na trup rastie s hĺbkou
if(FN=='hull'&&dep>8){const L=8+dep*.15;for(let k=0;k<6;k++){const X=300+k*72;arw(x,[X,CY-R-12-L],[X,CY-R-8],'#fff',3.2);arw(x,[X,CY+R+12+L],[X,CY+R+8],'#fff',3.2)}}
x.restore();
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],712,462,735,352);lead(S,LN[1],560,462,660,CY+38);lead(S,LN[2],380,462,380,CY+47);lead(S,LN[3],196,216,134,CY-22);lead(S,LN[4],620,206,508,CY-R-30);
x.restore();
const fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',5,ts-.35,A);
meter(S,String(Math.round(dep)),'M DEEP',A,a,fi>=0);badge(S,String(Math.round(1+dep/10)),'BAR',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
