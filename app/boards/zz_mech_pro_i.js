// Presné modely 9 – hydraulický zdvihák (rez) a výťah s protizávažím (rez šachtou).
// Hýbe sa len to, čo sa hýbe naozaj: malý piest pumpuje olej cez spätné ventily pod veľký piest, ten po kúskoch dvíha auto;
// kabína a protizávažie idú proti sebe cez trakčný kotúč, pri pretrhnutí lana zachytávače zovrú vodidlá.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),OIL='#e8a52e';
const arw=(x,a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(4+w*2,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};
const steel=(x,x0,x1)=>{const g=x.createLinearGradient(x0,0,x1,0);g.addColorStop(0,'#7b8188');g.addColorStop(.5,'#eef1f4');g.addColorStop(1,'#6b7077');return g};

// ---------- hydraulický zdvihák: l = [malý piest, veľký piest, olej, spätné ventily]; f = small | big | oil | valves ----------
PRO.hydraulic=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,ST=1.6,NS=7,BOT=455;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[420,322,zf*1.15],FV={small:[230,330,zf*1.6],big:[600,300,zf*1.25],oil:[400,440,zf*1.9],valves:[300,452,zf*2.5]},ORD=['small','big','oil','valves'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const tt=t%(NS*ST+2.6),n=Math.floor(tt/ST),ph=tt%ST,lift=n<NS,down=lift&&ph<.6,s=!lift?0:down?sm(ph/.6):1-sm((ph-.6)/1),ys=290+70*s,yb=lift?430-14*(n+(down?sm(ph/.6):1)):332+98*sm((tt-NS*ST-.3)/2);
const yr=BOT-(30074-44*(BOT-ys-14)-220*(BOT-yb-18))/110,yj=ys-90,th=Math.atan2(yj-190,130),HE=[120+310*Math.cos(th),190+310*Math.sin(th)],py=yb-182;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// teleso zdviháka v reze a dutiny: zásobník, malý valec, veľký valec, kanál
const blk=()=>{x.beginPath();x.moveTo(70,235);x.lineTo(300,235);x.lineTo(300,292);x.lineTo(760,292);x.lineTo(760,512);x.lineTo(70,512);x.closePath()};blk();x.fillStyle='#474c53';x.fill();hatch(x,blk);blk();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
const cav=[[90,250,110,BOT-250],[228,235,44,BOT-235],[490,292,220,BOT-292],[228,BOT,482,24],[200,432,28,16],[90,488,640,10],[90,BOT,12,34],[718,BOT+24,12,10]];x.fillStyle='#0a0c0f';cav.forEach(q=>x.fillRect(q[0],q[1],q[2],q[3]));
// olej: všade rovnaký tlak; objem sa zachováva (čo ubudne v zásobníku, pribudne pod veľkým piestom)
x.fillStyle=rgba(OIL,.85);x.fillRect(90,yr,110,BOT-yr);x.fillRect(228,ys+14,44,BOT-ys-14);x.fillRect(490,yb+18,220,BOT-yb-18);x.fillRect(228,BOT,482,24);x.fillRect(200,432,28,16);x.fillRect(90,488,640,10);x.fillRect(90,BOT,12,34);x.fillRect(718,BOT+24,12,10);
x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();[[90,250,110,BOT-250],[490,292,220,BOT-292]].forEach(q=>{x.moveTo(q[0],q[1]);x.lineTo(q[0],q[1]+q[3]);x.moveTo(q[0]+q[2],q[1]);x.lineTo(q[0]+q[2],q[1]+q[3])});x.moveTo(228,235);x.lineTo(228,432);x.moveTo(272,235);x.lineTo(272,BOT);x.stroke();
// spätné ventily (guľôčky): sací sa otvára pri zdvihu malého piesta, výtlačný pri stlačení; vypúšťací pri spúšťaní
const suck=lift&&!down&&ph>.62&&ph<1.55,push=down&&ph>.03;[[214-(suck?0:7),440,suck],[392+(push?9:0),BOT+12,push],[724,BOT+29-(lift?0:8),!lift]].forEach(q=>{dot(x,[q[0],q[1]],7.5,q[2]?A:'#c9ced3',p,false);x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.arc(q[0],q[1],7.5,0,TAU);x.stroke()});
x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.moveTo(380,BOT);x.lineTo(380,BOT+5);x.moveTo(380,BOT+24);x.lineTo(380,BOT+19);x.stroke();
if(suck)for(let i=0;i<4;i++){const u=(t*1.6+i/4)%1;dot(x,[196+u*44,440+(u>.7?(u-.7)*30:0)],3.4,'#fff',p*Math.sin(Math.PI*u),false)}
if(push)for(let i=0;i<7;i++){const u=(t*1.4+i/7)%1;dot(x,[250+u*320,BOT+12],3.4,'#fff',p*Math.sin(Math.PI*u),false)}
if(!lift)for(let i=0;i<7;i++){const u=(t*1.2+i/7)%1;dot(x,[724-u*620,493],3.2,'#fff',p*Math.sin(Math.PI*u),false)}
// malý piest s pákou
x.fillStyle=steel(x,229,271);x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(244,yj,12,ys-yj);x.fill();x.stroke();x.beginPath();x.roundRect(229,ys,42,14,3);x.fill();x.stroke();
x.fillStyle='#474c53';x.beginPath();x.rect(112,190,16,45);x.fill();x.stroke();x.strokeStyle='#fff';x.lineWidth=13;x.beginPath();x.moveTo(120,190);x.lineTo(HE[0],HE[1]);x.stroke();x.strokeStyle='#8f959c';x.lineWidth=8;x.stroke();
x.strokeStyle=A;x.lineWidth=13;x.beginPath();x.moveTo(HE[0]-60*Math.cos(th),HE[1]-60*Math.sin(th));x.lineTo(HE[0],HE[1]);x.stroke();dot(x,[120,190],8,'#eef1f4',p,false);dot(x,[250,yj],7,'#eef1f4',p,false);
if(down)arw(x,[HE[0]-24,HE[1]-78],[HE[0]-24,HE[1]-22],A,6);
// veľký piest, piestnica, plošina a auto
x.fillStyle=steel(x,570,630);x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(570,py+12,60,yb-py-12);x.fill();x.stroke();x.fillStyle=steel(x,491,709);x.beginPath();x.roundRect(491,yb,218,18,3);x.fill();x.stroke();
x.fillStyle='#8f959c';x.beginPath();x.roundRect(500,py,200,12,4);x.fill();x.stroke();
x.fillStyle='#d9dde1';x.lineWidth=3;x.beginPath();x.roundRect(498,py-60,204,36,11);x.fill();x.stroke();x.fillStyle='#8f959c';x.beginPath();x.moveTo(536,py-60);x.lineTo(560,py-90);x.lineTo(640,py-90);x.lineTo(668,py-60);x.closePath();x.fill();x.stroke();
[545,655].forEach(X=>{dot(x,[X,py-17],17,'#16181b',p,false);x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.arc(X,py-17,17,0,TAU);x.stroke();dot(x,[X,py-17],6,'#c9ced3',p,false)});
// tlak oleja na piesty (rovnaký tlak, väčšia plocha = väčšia sila)
if(down){for(let k=0;k<5;k++)arw(x,[512+k*44,yb+52],[512+k*44,yb+24],'#fff',3);arw(x,[250,ys+20],[250,ys+46],'#fff',3)}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],330,150,262,ys-40);lead(S,LN[1],800,400,712,yb+9);lead(S,LN[2],150,560,150,yr+30);lead(S,LN[3],400,560,392,BOT+22);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,'10','KG PUSH',A,a,fi>=0);badge(S,'1250 KG','LIFT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- výťah: l = [kabína, protizávažie, trakčný kotúč, zachytávače]; f = car | counterweight | sheave | brake | snap (pretrhnuté lano) ----------
PRO.elevator=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,SNP=String(d.f||'')=='snap',SC=[449,62],SR=44;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,302,zf*1.08],FV={car:[405,300,zf*1.6],counterweight:[540,300,zf*1.6],sheave:[460,84,zf*2.4],brake:[405,340,zf*2.1],snap:[430,300,zf*1.25]},ORD=['car','counterweight','sheave','brake'],KF=cams(d,FULL,FV,ORD,DUR);
const mv=u=>{u=((u%11)+11)%11;return u<4?430-300*sm(u/4):u<5.5?130:u<9.5?130+300*sm((u-5.5)/4):430};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8).slice(),zi=ez((cm[2]/zf-1)/.22),[FN,ts]=shot(KF,d,t);
let yc,ycw,vel,cut=false,grip=0,q=0;
if(SNP){const u=t-1.6;if(u<0){yc=330-60*t;vel=-60}else{cut=true;if(u<.4){yc=234-60*u+300*u*u;vel=-60+600*u}else{const w=Math.min(.45,u-.4);yc=258+180*w-200*w*w;vel=180-400*w;grip=cl((u-.4)/.12);q=u-.4}}ycw=cut?Math.min(460,346+300*(t-1.6)*(t-1.6)):580-yc}
else{yc=mv(t);vel=(mv(t+.03)-mv(t-.03))/.06;ycw=580-yc}
if(FN=='car'||FN=='brake'||SNP)cm[1]+=(yc+55-300)*Math.min(1,zi)*.9;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// šachta, podlažia, vodidlá, nárazníky
x.fillStyle='#0b0d10';x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.rect(300,14,300,576);x.fill();x.stroke();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=3;[240,340,440,540].forEach(Y=>{x.beginPath();x.moveTo(170,Y);x.lineTo(300,Y);x.stroke()});
x.fillStyle='#14171a';x.fillRect(170,540,130,50);x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=2;x.beginPath();x.moveTo(300,118);x.lineTo(600,118);x.stroke();
x.strokeStyle='#8f959c';x.lineWidth=5;x.beginPath();[332,478,508,572].forEach(X=>{x.moveTo(X,122);x.lineTo(X,586)});x.stroke();
x.strokeStyle='#fff';x.lineWidth=3;[[405,552],[540,552]].forEach(([X,Y])=>{x.beginPath();for(let k=0;k<=6;k++)x.lineTo(X+(k%2?9:-9),Y+k*5.5);x.stroke();x.beginPath();x.moveTo(X-14,Y);x.lineTo(X+14,Y);x.stroke()});
// laná, trakčný kotúč s motorom a vodiaci kotúč
const rot=SNP?(cut?-96/SR:(-60*t)/SR):(yc-430)/SR;x.strokeStyle='#e8ecef';x.lineWidth=3.2;
if(!cut){x.beginPath();x.moveTo(405,yc);x.lineTo(405,SC[1]);x.arc(SC[0],SC[1],SR,Math.PI,.42);x.lineTo(540,112);x.lineTo(540,ycw);x.stroke()}
else{x.beginPath();x.moveTo(405,yc);x.lineTo(405+6*Math.sin(t*14),yc-34);x.stroke();x.beginPath();x.moveTo(405,SC[1]+40+10*Math.sin(t*9));x.lineTo(405,SC[1]);x.arc(SC[0],SC[1],SR,Math.PI,.42);x.lineTo(540,112);x.lineTo(540,ycw);x.stroke()}
x.fillStyle=steel(x,340,402);x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(322,36,74,52,6);x.fill();x.stroke();x.fillStyle=A;x.beginPath();x.roundRect(396,50,12,24,3);x.fill();x.stroke();
x.fillStyle='#2a2e33';x.beginPath();x.arc(SC[0],SC[1],SR,0,TAU);x.fill();x.stroke();x.strokeStyle='#c9ced3';x.lineWidth=4;for(let k=0;k<5;k++){const a=rot+k*TAU/5;x.beginPath();x.moveTo(SC[0]+9*Math.cos(a),SC[1]+9*Math.sin(a));x.lineTo(SC[0]+(SR-7)*Math.cos(a),SC[1]+(SR-7)*Math.sin(a));x.stroke()}dot(x,SC,9,'#eef1f4',p,false);
x.fillStyle='#2a2e33';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.arc(524,108,16,0,TAU);x.fill();x.stroke();dot(x,[524,108],4,'#c9ced3',p,false);
// obmedzovač rýchlosti: malé lanko popri šachte; pri prekročení rýchlosti zovrie a potiahne zachytávače
x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=1.8;x.beginPath();x.moveTo(314,60);x.lineTo(314,570);x.moveTo(322,60);x.lineTo(322,570);x.stroke();[[318,56],[318,572]].forEach(c=>{dot(x,c,9,grip?A:'#8f959c',p,false);x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.arc(c[0],c[1],9,0,TAU);x.stroke()});
// protizávažie
x.fillStyle='#474c53';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(512,ycw,56,92,4);x.fill();x.stroke();x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.beginPath();for(let k=1;k<6;k++){x.moveTo(514,ycw+k*15.3);x.lineTo(566,ycw+k*15.3)}x.stroke();
// kabína so zachytávačmi na vodidlách
x.fillStyle='#1b1e22';x.strokeStyle='#fff';x.lineWidth=3.5;x.beginPath();x.roundRect(340,yc,130,110,5);x.fill();x.stroke();x.fillStyle='rgba(255,236,190,.16)';x.fillRect(348,yc+8,114,94);
{const uu=((t%11)+11)%11,op=SNP?0:Math.max(sm(Math.min(uu-4.1,5.4-uu)/.4),sm(Math.min(uu-9.6,10.9-uu)/.4));x.fillStyle='#8f959c';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(340,yc+14,6,90*(1-.8*op));x.fill();x.stroke()}
x.fillStyle='#d9dde1';[[384,yc+52],[428,yc+52]].forEach(c=>{dot(x,[c[0],c[1]-18],9,'#d9dde1',p,false);x.beginPath();x.roundRect(c[0]-11,c[1]-6,22,46,8);x.fill()});
x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2;x.beginPath();x.moveTo(322,yc+6);x.lineTo(340,yc+10);x.stroke();
[[332,1],[478,-1]].forEach(([X,g])=>{const Y=yc+110,o=4-4*grip;x.fillStyle='#474c53';x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(X-10,Y-6,20,18);x.fill();x.stroke();x.fillStyle=grip?A:'#c9ced3';[-1,1].forEach(h=>{x.beginPath();x.moveTo(X+h*(3+o),Y-4);x.lineTo(X+h*(8+o),Y-4);x.lineTo(X+h*(8+o),Y+10);x.lineTo(X+h*(1.5+o),Y+10);x.closePath();x.fill()});
if(grip&&q<.5)for(let i=0;i<7;i++){const a=-Math.PI/2+(HS(i,41+X)-.5)*2.4,r=8+((q*90+HS(i,42)*30)%34);x.strokeStyle=rgba('#ffd27a',1-q*2);x.lineWidth=2.2;x.beginPath();x.moveTo(X+Math.cos(a)*r,Y+Math.sin(a)*r);x.lineTo(X+Math.cos(a)*(r+7),Y+Math.sin(a)*(r+7));x.stroke()}});
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],230,yc+40,338,yc+50);lead(S,LN[1],700,ycw+40,570,ycw+46);lead(S,LN[2],700,70,SC[0]+SR-2,SC[1]);lead(S,LN[3],230,yc+150,326,yc+114);
x.restore();
const fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,(Math.abs(vel)/24).toFixed(1),'M/S',A,a,fi>=0);if(!SNP)badge(S,String(1+Math.round((430-yc)/100)),'FLOOR',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
