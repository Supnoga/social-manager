// Presné modely 2 – skladajú sa zo stavebnice KIT (zz_mech_pro.js): veľké plátno, kamera, čiastočky, kov, šrafovanie.
// Každý model: f = záber na jednu časť (názvy sú v auto_visual.FOCUS), "run" = beží naplno, l = popisky, c = číslo z hlasu.
{
const K=window.KIT,PRO=K.PRO,{G,GEARPRO,HS,rgba,mix,ez,lerp,wob,dot,flame,spark,metal,hatch,STG,camAt,stamp,callout,AIR,FUEL,SMOKE,FIRE,WATER,CTX}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
const LBL=d=>(Array.isArray(d.l)?d.l:[]).map(s=>String(s==null?'':s).toUpperCase());
const tag=(S,s,px,py,al,col,fs)=>{if(!s)return;const x=S.x;x.font=`800 ${fs||24}px ${S.FT}`;x.textAlign=al||'center';x.textBaseline='middle';x.lineJoin='round';x.strokeStyle='rgba(0,0,0,.8)';x.lineWidth=7;x.strokeText(s,px,py);x.fillStyle=col||'#e9ecef';x.fillText(s,px,py)};
// veľké číslo s jednotkou vľavo dole (otáčky, tlak, teplota) – hodnota sa počíta z pohybu modelu
const meter=(S,val,unit,A,a,top)=>{const x=S.x,X=40,Y=top?118:S.h-70;x.save();x.globalAlpha*=a;x.textAlign='left';x.textBaseline='alphabetic';x.font=`900 64px ${S.FT}`;const w=x.measureText(val).width;x.fillStyle='rgba(0,0,0,.8)';x.beginPath();x.roundRect(X-14,Y-62,w+x.measureText(unit).width*.5+70,84,16);x.fill();x.fillStyle='#fff';x.fillText(val,X,Y);x.font=`800 30px ${S.FT}`;x.fillStyle=A;x.fillText(unit,X+w+12,Y);x.restore()};
// kamera modelu: celok → zábery na časti → celok; f = jeden záber; run = pomalý nájazd
const cams=(d,FULL,FV,tour,DUR)=>{const f=String(d.f||'');if(f=='run')return [[0,FULL],[.2,[FULL[0],FULL[1],FULL[2]*1.14],Math.max(3,DUR)]];if(FV[f])return [[0,FULL],[.45,FV[f],.8]];
const n=tour.length,KF=[[0,FULL]];tour.forEach((k,i)=>KF.push([.9+i*(DUR*.72-.9)/n,FV[k],.8]));KF.push([DUR*.8,FULL,1]);return KF};

// ---------- turbodmychadlo: výfukové plyny točia turbínu, tá cez hriadeľ točí kompresor, ktorý stláča vzduch do motora ----------
// l = [výfuk dnu, turbína, kompresor, vzduch do motora]; f = turbine | shaft | compressor | run
PRO.turbo=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),T=[250,296],C=[614,296],Rw=78,R0=Rw+12,R1=Rw+62,DUR=N(d._dur)||9,RUN=String(d.f||'')=='run',NP=60;
const zf=Math.min(S.w/830,S.h/470)*.98,FULL=[432,270,zf],FV={turbine:[T[0]-34,T[1]-26,zf*1.7],shaft:[432,T[1],zf*2.1],compressor:[C[0]+34,C[1]-26,zf*1.7]},KF=cams(d,FULL,FV,['turbine','shaft','compressor'],DUR);
// rozbeh: otáčky rastú s prúdom výfukových plynov (uhol je integrál otáčok, takže koleso nikdy neposkočí)
const TS=RUN?.01:Math.max(2.4,DUR*.4),W0=RUN?7.5:1.4,W1=7.5,spd=t=>W0+(W1-W0)*ez(t/TS),ang=t=>{const u=Math.min(1,t/TS);return W0*t+(W1-W0)*(TS*(u*u*u-u*u*u*u/2)+Math.max(0,t-TS))};
const Rt=a=>R1-(R1-R0)*(a+Math.PI/2)/TAU,Rc=a=>R0+(R1-R0)*(a+Math.PI/2)/TAU;
const scroll=(c,Rf,off,left)=>{for(let i=0;i<=96;i++){const a=-Math.PI/2+i/96*TAU,r=Rf(a)+off,P=[c[0]+r*Math.cos(a),c[1]+r*Math.sin(a)];i?x.lineTo(P[0],P[1]):x.moveTo(P[0],P[1])}x.closePath();x.rect(left?c[0]-236:c[0],c[1]-R1-off,236,R1-R0-6+2*off)};
const house=(c,Rf,left,hot)=>{x.beginPath();scroll(c,Rf,13,left);x.lineWidth=8;x.strokeStyle='#fff';x.stroke();const g=x.createLinearGradient(0,c[1]-160,0,c[1]+160);g.addColorStop(0,hot?'#4a3a32':'#33373c');g.addColorStop(1,hot?'#2a1f1a':'#1c1e21');x.fillStyle=g;x.fill();hatch(x,()=>scroll(c,Rf,13,left));
x.beginPath();scroll(c,Rf,0,left);x.lineWidth=6;x.strokeStyle='#fff';x.stroke();x.fillStyle='#050607';x.fill()};
const wheel=(c,th,nb,sw,k)=>{x.save();x.translate(c[0],c[1]);x.rotate(th);x.shadowColor='rgba(0,0,0,.6)';x.shadowBlur=14;x.beginPath();x.arc(0,0,Rw-2,0,TAU);const g=x.createRadialGradient(-20,-24,8,0,0,Rw);g.addColorStop(0,'#565b62');g.addColorStop(1,'#1e2023');x.fillStyle=g;x.fill();x.shadowBlur=0;x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=2;x.stroke();
for(let b=0;b<nb;b++){x.beginPath();for(let j=0;j<=10;j++){const u=j/10,r=24+(Rw-6-24)*u,a=b*TAU/nb+sw*u*u;j?x.lineTo(r*Math.cos(a),r*Math.sin(a)):x.moveTo(r*Math.cos(a),r*Math.sin(a))}x.strokeStyle='#eceef0';x.lineWidth=5.5;x.stroke()}
x.beginPath();x.arc(0,0,24,0,TAU);x.fillStyle=metal(x,-24,24);x.fill();x.strokeStyle='#fff';x.lineWidth=2.5;x.stroke();x.beginPath();for(let j=0;j<6;j++){const a=j*TAU/6;j?x.lineTo(11*Math.cos(a),11*Math.sin(a)):x.moveTo(11,0)}x.closePath();x.fillStyle='#5d6268';x.fill();x.restore();
if(k>.05){x.save();x.globalAlpha*=.22*k;x.strokeStyle='#fff';x.lineWidth=3;for(let j=0;j<5;j++){const r=34+j*9,a=th*.37+j*1.3;x.beginPath();x.arc(c[0],c[1],r,a,a+1.6);x.stroke()}x.restore()}};
const PT=[...Array(NP)].map((_,i)=>({o:HS(i,81),lat:HS(i,82),a:(-Math.PI/2)+(.16+.8*((i%12)+HS(i,83))/12)*TAU,k:.8+.4*HS(i,84),rr:.8+.5*HS(i,85)}));
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const th=ang(t),w=spd(t),k=(w-1.4)/(W1-1.4),cm=camAt(KF,t,.8);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(432,280,20,432,280,470);g.addColorStop(0,'rgba(86,118,160,.2)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(-60,-200,980,960)}
// stredová skriňa s ložiskami a olejom, hriadeľ spája obe kolesá
x.beginPath();x.rect(T[0]+70,T[1]-36,C[0]-T[0]-140,72);x.lineWidth=8;x.strokeStyle='#fff';x.stroke();x.fillStyle='#24272b';x.fill();hatch(x,()=>x.rect(T[0]+70,T[1]-36,C[0]-T[0]-140,72));
x.fillStyle='#5a3d12';x.fillRect(T[0]+70,T[1]-17,C[0]-T[0]-140,34);for(let j=0;j<10;j++){const u=(t*.5+HS(j,90))%1;dot(x,[T[0]+130+u*(C[0]-T[0]-260),T[1]+(HS(j,91)-.5)*26],2.4,'#e0a13a',.8*Math.sin(Math.PI*u),false)}
x.fillStyle=metal(x,0,1);{const g=x.createLinearGradient(0,T[1]-9,0,T[1]+9);g.addColorStop(0,'#868b91');g.addColorStop(.35,'#f4f6f8');g.addColorStop(1,'#70757b');x.fillStyle=g}x.fillRect(T[0],T[1]-9,C[0]-T[0],18);x.save();x.beginPath();x.rect(T[0]+70,T[1]-9,C[0]-T[0]-140,18);x.clip();x.strokeStyle='rgba(0,0,0,.5)';x.lineWidth=3;for(let j=-2;j<14;j++){const xx=T[0]+70+j*22,o=((th*9)%22+22)%22-11;x.beginPath();x.moveTo(xx,T[1]-9+((o+11)%22)*.82);x.lineTo(xx+12,T[1]-9+((o+11)%22)*.82);x.stroke()}x.restore();
house(T,Rt,true,true);house(C,Rc,false,false);
// horúca strana žiari, keď sa turbo roztočí
x.save();x.globalCompositeOperation='lighter';{const g=x.createRadialGradient(T[0],T[1],40,T[0],T[1],190);g.addColorStop(0,`rgba(255,120,40,${.05+.2*k})`);g.addColorStop(1,'rgba(255,120,40,0)');x.fillStyle=g;x.fillRect(T[0]-240,T[1]-200,440,400)}x.restore();
// prúdenie: výfukové plyny po špirále dovnútra na turbínu, čerstvý vzduch zo stredu kompresora po špirále von (stlačený = hustejší)
const fl=th*.047;PT.forEach((o,i)=>{let u=((fl*o.k+o.o)%1+1)%1;const r0=Rw+4+52*(1-.8*o.lat);
if(u<.3){dot(x,[T[0]-232+232*(u/.3),T[1]-r0],4.2*o.rr,mix('#ffb060',SMOKE,.25),.75*Math.min(1,u*14),true)}
else if(u<.75){const q=(u-.3)/.45,a=-Math.PI/2+q*(o.a+Math.PI/2),r=Rw+4+(Rt(a)-Rw-10)*(1-.8*o.lat)*(1-ez(q)),ww=wob(i,t,2.5,3);dot(x,[T[0]+r*Math.cos(a)+ww[0],T[1]+r*Math.sin(a)+ww[1]],4.2*o.rr,mix('#ffb060',SMOKE,.25+.3*q),.75,true)}
else{const q=(u-.75)/.25,a=o.a+q*1.5,r=(Rw+4)*(1-q)+20*q;dot(x,[T[0]+r*Math.cos(a),T[1]+r*Math.sin(a)],(4.2+2*q)*o.rr,mix('#ffb060',SMOKE,.55+.45*q),.75*(1-q),true)}
u=((fl*o.k+o.o+.37)%1+1)%1;const r1=Rw+4+52*(.2+.8*o.lat);
if(u<.2){const q=u/.2,a=o.a-(1-q)*1.5,r=18+(Rw+4-18)*q;dot(x,[C[0]+r*Math.cos(a),C[1]+r*Math.sin(a)],3*o.rr,AIR,Math.min(1,q*4),true)}
else if(u<.6){const q=(u-.2)/.4,a=o.a+q*(1.5*Math.PI-o.a),r=Rw+4+(Rc(a)-Rw-10)*(.2+.8*o.lat)*ez(q),ww=wob(i+90,t,2,3);dot(x,[C[0]+r*Math.cos(a)+ww[0],C[1]+r*Math.sin(a)+ww[1]],3*o.rr,mix(AIR,'#e6f5ff',q*.7),1,true)}
else{const q=(u-.6)/.4;dot(x,[C[0]+232*q,C[1]-r1],3*o.rr,'#d4edff',Math.min(1,(1-q)*8),true)}});
wheel(T,th,11,.55,k);wheel(C,th,12,-.75,k);
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-ez((cm[2]/zf-1)/.22));tag(S,LN[0],T[0]-120,T[1]-R1-34,'center','#ffb060');tag(S,LN[1],T[0],T[1]+R1+22,'center','#e9ecef');tag(S,LN[2],C[0],C[1]+R1+22,'center','#e9ecef');tag(S,LN[3],C[0]+120,C[1]-R1-34,'center',AIR);
x.restore();x.globalAlpha=p;
const fi=['turbine','shaft','compressor'].indexOf(String(d.f||''));if(fi>=0&&t>.35)stamp(S,fi,[LN[1],LN[1]?'SHAFT':'',LN[2]][fi]||'',3,t-.35,A);
if(fi<0)meter(S,(Math.round(w/W1*150)*1000).toLocaleString('en-US'),'RPM',A,cl((t-.6)/.4));
callout(S,d,t,A);x.globalAlpha=1}};
CTX.turbo=['car','engine'];

// ---------- vačkový hriadeľ a ventil: vačka tlačí zdvihátko, ventil sa otvorí, pružina ho vráti; rozvodový remeň točí vačku polovičnou rýchlosťou kľuky ----------
// l = [vačkový hriadeľ, ventil, rozvodový remeň]; f = cam | valve | belt | run
PRO.camshaft=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,RUN=String(d.f||'')=='run',C1=[520,150],C2=[190,430],R1=92,R2=46,Rb=44,Lm=30,P0=1.15,VX=520,SEAT=392,NP=44;
const zf=Math.min(S.w/760,S.h/560)*.96,FULL=[440,292,zf],FV={cam:[520,196,zf*2.05],valve:[548,372,zf*1.9],belt:[340,300,zf*1.22]},KF=cams(d,FULL,FV,['cam','valve','belt'],DUR);
// profil vačky a presný zdvih plochého zdvihátka: najnižší bod profilu pri danom natočení (dotyk je vždy dotyčnicový)
const rc=f=>{f=Math.atan2(Math.sin(f),Math.cos(f));return Rb+(Math.abs(f)<P0?Lm*Math.pow(Math.cos(Math.PI/2*f/P0),2):0)};
const hgt=th=>{let m=0;for(let i=0;i<360;i++){const f=i/360*TAU,y=rc(f)*Math.sin(f+th);if(y>m)m=y}return m};
const HT=[...Array(361)].map((_,i)=>hgt(i/360*TAU)-Rb),lift=th=>{const u=((th%TAU)+TAU)%TAU/TAU*360,i=Math.floor(u);return HT[i]+(HT[i+1]-HT[i])*(u-i)};
// prietok cez ventil rastie so zdvihom: čiastočky sa hýbu len vtedy, keď je ventil otvorený
const CUM=[0];for(let i=0;i<360;i++)CUM.push(CUM[i]+(HT[i]+HT[i+1])/2);const flow=th=>{const r=Math.floor(th/TAU),u=(th-r*TAU)/TAU*360,i=Math.floor(u);return (r*CUM[360]+CUM[i]+(CUM[i+1]-CUM[i])*(u-i))/CUM[360]};
const W=RUN?4.6:1.5,th0=Math.PI/2-P0-.5;
// remeň: vonkajšie dotyčnice dvoch kolies, obe sa točia rovnakým smerom
const f0=Math.atan2(C2[1]-C1[1],C2[0]-C1[0]),dd=Math.hypot(C2[0]-C1[0],C2[1]-C1[1]),be=Math.acos((R1-R2)/dd),BP=[];
for(let i=0;i<=60;i++){const a=f0+be+i/60*(TAU-2*be);BP.push([C1[0]+R1*Math.cos(a),C1[1]+R1*Math.sin(a)])}for(let i=0;i<=24;i++){const a=f0-be+i/24*2*be;BP.push([C2[0]+R2*Math.cos(a),C2[1]+R2*Math.sin(a)])}BP.push(BP[0]);
const BL=[0];for(let i=1;i<BP.length;i++)BL.push(BL[i-1]+Math.hypot(BP[i][0]-BP[i-1][0],BP[i][1]-BP[i-1][1]));const LEN=BL[BL.length-1],bpt=s=>{s=((s%LEN)+LEN)%LEN;let i=1;while(BL[i]<s)i++;const f=(s-BL[i-1])/(BL[i]-BL[i-1]||1);return lerp(BP[i-1],BP[i],f)};
const port=()=>{x.beginPath();x.moveTo(720,322);x.lineTo(626,322);x.quadraticCurveTo(VX,322,VX,SEAT+2)};
const ppt=(u,lat)=>{u=cl(u);if(u<.5)return [720-94*(u/.5),322+lat];const q=(u-.5)/.5,a=1-q;return [a*a*626+2*a*q*VX+q*q*VX+lat*q*.9,a*a*322+2*a*q*322+q*q*(SEAT-6)+lat*(1-q)]};
const PT=[...Array(NP)].map((_,i)=>({o:(i+HS(i,101))/NP,lat:(HS(i,102)-.5)*34,sd:HS(i,103)<.5?-1:1,k:.9+.2*HS(i,104),gx:HS(i,105),gy:HS(i,106),fuel:HS(i,107)<.24,rr:.8+.5*HS(i,108)}));
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const th=th0+W*t,L=lift(th),yT=C1[1]+Rb+L,cm=camAt(KF,t,.8);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(440,290,20,440,290,470);g.addColorStop(0,'rgba(86,118,160,.2)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(-60,-200,980,960)}
// rozvod vzadu: remeň a dve kolesá (kľuka 2 otáčky = vačka 1 otáčka)
x.save();x.globalAlpha=p*.8;x.beginPath();BP.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.strokeStyle='#fff';x.lineWidth=17;x.stroke();x.strokeStyle='#23262a';x.lineWidth=11;x.stroke();
for(let s0=0;s0<LEN;s0+=17){const q=bpt(s0+W*t*R1);dot(x,q,2.6,'#8f959c',1,false)}
GEARPRO(x,C1[0],C1[1],R1-9,40,th,'#fff',{fill:'#2b2e33'});GEARPRO(x,C2[0],C2[1],R2-9,20,2*th,'#fff',{fill:'#2b2e33'});dot(x,C2,9,A,1,true);
{const a=2*th;x.strokeStyle=A;x.lineWidth=6;x.beginPath();x.moveTo(C2[0],C2[1]);x.lineTo(C2[0]+26*Math.cos(a),C2[1]+26*Math.sin(a));x.stroke()}x.restore();x.globalAlpha=p;
// hlava valca v reze: sací kanál, vedenie ventilu, priestor pružiny, valec pod ňou
const head=()=>{x.rect(396,252,324,SEAT-252)};x.beginPath();head();x.lineWidth=8;x.strokeStyle='#fff';x.stroke();{const g=x.createLinearGradient(0,252,0,SEAT);g.addColorStop(0,'#33373c');g.addColorStop(1,'#1c1e21');x.fillStyle=g}x.fill();hatch(x,head);
x.lineCap='butt';port();x.strokeStyle='#fff';x.lineWidth=62;x.stroke();port();x.strokeStyle='#050607';x.lineWidth=54;x.stroke();x.lineCap='round';
x.fillStyle='#050607';x.fillRect(VX-40,246,80,62);x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(VX-40,250);x.lineTo(VX-40,308);x.lineTo(VX+40,308);x.lineTo(VX+40,250);x.stroke();
x.fillStyle='#050607';x.fillRect(372,SEAT,372,150);x.strokeStyle='#fff';x.lineWidth=8;x.beginPath();x.moveTo(372,SEAT+150);x.lineTo(372,SEAT);x.lineTo(VX-36,SEAT);x.moveTo(VX+36,SEAT);x.lineTo(744,SEAT);x.lineTo(744,SEAT+150);x.stroke();
// zmes: v kanáli čaká, cez otvorený ventil prúdi okolo taniera do valca
const F=flow(th);PT.forEach((o,i)=>{const u=((F*1.15*o.k+o.o)%1+1)%1,col=o.fuel?FUEL:AIR,r=(o.fuel?3.6:2.9)*o.rr,w=wob(i,t,2.2,2.6);
if(u<.56){const q=ppt(u/.56,o.lat);dot(x,[q[0]+w[0],q[1]+w[1]],r,col,Math.min(1,u*14),true)}
else if(u<.68){const q=(u-.56)/.12,a=ppt(1,o.lat),b=[VX+o.sd*(40+6*o.gx),SEAT+10+L*.5];const P=lerp(a,b,ez(q));dot(x,P,r,col,1,true)}
else{const q=(u-.68)/.32,b=[VX+o.sd*(40+6*o.gx),SEAT+10+L*.5],e=[VX+o.sd*(60+150*o.gx),SEAT+34+96*o.gy];const P=lerp(b,e,ez(q));dot(x,[P[0]+w[0]*2,P[1]+w[1]*2],r,col,1-q*q,true)}});
// ventil s pružinou a zdvihátkom (jeden tuhý celok: všetko sa posúva o rovnaký zdvih)
x.strokeStyle='#e8eaec';x.lineWidth=9;x.beginPath();x.moveTo(VX,yT+20);x.lineTo(VX,SEAT-12+L);x.stroke();
x.beginPath();x.moveTo(VX-35,SEAT+3+L);x.lineTo(VX+35,SEAT+3+L);x.lineTo(VX+16,SEAT-13+L);x.lineTo(VX-16,SEAT-13+L);x.closePath();x.fillStyle=metal(x,VX-35,VX+35);x.fill();x.strokeStyle='#000';x.lineWidth=1.5;x.stroke();
x.strokeStyle='#c2c6ca';x.lineWidth=4;x.beginPath();{const y0=yT+32,y1=304,n=8;for(let i=0;i<=n;i++)x.lineTo(VX+(i%2?26:-26),y0+(y1-y0)*i/n)}x.stroke();
x.fillStyle='#e8eaec';x.fillRect(VX-31,yT+24,62,7);x.save();x.shadowColor='rgba(0,0,0,.5)';x.shadowBlur=10;x.fillStyle=metal(x,VX-34,VX+34);x.fillRect(VX-34,yT,68,24);x.restore();x.strokeStyle='#fff';x.lineWidth=2.5;x.strokeRect(VX-34,yT,68,24);
// vačka
x.save();x.translate(C1[0],C1[1]);x.rotate(th);x.shadowColor='rgba(0,0,0,.6)';x.shadowBlur=14;x.beginPath();for(let i=0;i<=120;i++){const f=-Math.PI+i/120*TAU,r=rc(f);i?x.lineTo(r*Math.cos(f),r*Math.sin(f)):x.moveTo(r*Math.cos(f),r*Math.sin(f))}x.closePath();const cg=x.createRadialGradient(-12,-14,6,0,0,Rb+Lm);cg.addColorStop(0,'#d9dde1');cg.addColorStop(1,'#70757b');x.fillStyle=cg;x.fill();x.shadowBlur=0;x.strokeStyle='#fff';x.lineWidth=3.5;x.stroke();
x.beginPath();x.arc(0,0,20,0,TAU);x.fillStyle='#3a3e44';x.fill();x.stroke();x.fillStyle=A;x.fillRect(14,-4,12,8);x.restore();
// miesto dotyku svieti, keď vačka tlačí
if(L>.5){x.save();x.globalCompositeOperation='lighter';const g=x.createRadialGradient(VX,yT,0,VX,yT,34);g.addColorStop(0,rgba(A,.8*Math.min(1,L/8)));g.addColorStop(1,rgba(A,0));x.fillStyle=g;x.fillRect(VX-40,yT-34,80,68);x.restore()}
x.globalAlpha=p*sp*(1-ez((cm[2]/zf-1)/.22));tag(S,LN[0],C1[0]+118,C1[1]-64,'left');tag(S,LN[1],VX+62,SEAT-166,'left');tag(S,LN[2],C2[0]+10,C2[1]-R2-150,'center');
x.restore();x.globalAlpha=p;
const fi=['cam','valve','belt'].indexOf(String(d.f||''));if(fi>=0&&t>.35)stamp(S,fi,LN[fi]||'',3,t-.35,A);
if(fi<1)meter(S,(L/Lm*10).toFixed(1),'MM',A,cl((t-.6)/.4),fi==0);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- kotúčová brzda: tlak kvapaliny tlačí piest, doštičky zovrú kotúč, trenie mení pohyb na teplo ----------
// l = [brzdový kotúč, strmeň, brzdové doštičky]; f = disc | caliper
PRO.car_brake=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,DC=[262,300],R=150,SX=640,W0=9,NS=26;
const zf=Math.min(S.w/850,S.h/470)*.98,FULL=[432,292,zf],FV={disc:[DC[0]+30,DC[1],zf*1.5],caliper:[SX+20,236,zf*2.0]},KF=cams(d,FULL,FV,['caliper','disc'],DUR);
// priebeh: voľná jazda → stlačenie pedálu → brzdenie stálou silou (otáčky klesajú rovnomerne) → stojí a chladne
const TC=Math.max(5,Math.min(9,DUR*.82)),tA=TC*.24,tB=TC*.34,tS=TC*.86,dec=W0/(tS-tB);
const om=t=>t<tB?W0:t<tS?W0-dec*(t-tB):0,an=t=>t<tB?W0*t:t<tS?W0*tB+W0*(t-tB)-dec*(t-tB)*(t-tB)/2:W0*tB+W0*(tS-tB)/2;
const app=t=>ez((t-tA)/(tB-tA))*(1-ez((t-tS-.5)/.6)),temp=t=>t<tB?0:t<tS?1-Math.pow(om(t)/W0,2):Math.exp(-(t-tS)*.22);
const heat=k=>k<.5?mix('#2a2d31','#b3260a',k/.5,.0+.9*k*2):mix('#b3260a','#ffb347',(k-.5)/.5,.9);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const tt=t%(TC+2.2),th=an(tt),w=om(tt),a=app(tt),K=temp(tt),g=5*(1-a),cm=camAt(KF,t,.8),braking=tt>tB&&w>0;
x.save();x.translate(S.w/2+(braking?Math.sin(t*90)*1.2:0),S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const gg=x.createRadialGradient(432,290,20,432,290,480);gg.addColorStop(0,'rgba(86,118,160,.2)');gg.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=gg;x.fillRect(-60,-200,980,960)}
// kotúč spredu: vetracie otvory ukazujú otáčanie, trecia plocha sa rozžeraví
x.save();x.translate(DC[0],DC[1]);x.save();x.rotate(th);x.shadowColor='rgba(0,0,0,.6)';x.shadowBlur=16;x.beginPath();x.arc(0,0,R,0,TAU);const dg=x.createRadialGradient(-40,-50,20,0,0,R);dg.addColorStop(0,'#aab0b6');dg.addColorStop(1,'#5b6066');x.fillStyle=dg;x.fill();x.shadowBlur=0;x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
for(let i=0;i<24;i++){const aa=i*TAU/24,rr=[108,124,138][i%3];x.beginPath();x.arc(rr*Math.cos(aa),rr*Math.sin(aa),4.2,0,TAU);x.fillStyle='#16181a';x.fill()}
if(K>.02){x.globalCompositeOperation='lighter';x.beginPath();x.arc(0,0,R-3,0,TAU);x.arc(0,0,92,0,TAU,true);x.fillStyle=heat(K);x.globalAlpha=p*Math.min(1,K*1.6);x.fill('evenodd');x.globalCompositeOperation='source-over';x.globalAlpha=p}
x.beginPath();x.arc(0,0,88,0,TAU);x.fillStyle='#1b1d20';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.beginPath();x.arc(0,0,58,0,TAU);x.fillStyle='#3a3e44';x.fill();x.stroke();
for(let i=0;i<5;i++){const aa=i*TAU/5;x.beginPath();x.arc(36*Math.cos(aa),36*Math.sin(aa),8,0,TAU);x.fillStyle='#c9cdd1';x.fill();x.strokeStyle='#000';x.lineWidth=1.5;x.stroke();x.strokeStyle='#fff';x.lineWidth=3}
x.beginPath();x.arc(0,0,15,0,TAU);x.fillStyle='#0b0c0d';x.fill();x.stroke();x.restore();
// strmeň spredu (stojí) a prach z doštičiek pri brzdení
x.beginPath();x.arc(0,0,R+16,-.62,.62);x.arc(0,0,86,.5,-.5,true);x.closePath();x.fillStyle=A;x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();x.fillStyle='rgba(0,0,0,.35)';x.beginPath();x.arc(0,0,R+4,-.36,.36);x.arc(0,0,100,.3,-.3,true);x.closePath();x.fill();
if(braking)for(let i=0;i<NS;i++){const u=(t*(1.4+HS(i,121))+HS(i,122))%1,rr=96+56*HS(i,123),a0=.62,ex=u*(40+70*HS(i,124))*(w/W0+.25),P=[rr*Math.cos(a0)-Math.sin(a0)*ex,rr*Math.sin(a0)+Math.cos(a0)*ex+u*u*26];dot(x,P,1.6+1.6*HS(i,125),K>.45?'#ffcf7a':'#b9bec4',(1-u)*.9,false)}
x.restore();
// rez strmeňom zhora: kotúč medzi dvoma doštičkami, piest a brzdová kvapalina
const sl=5-g,bx=SX+sl;   // plávajúci strmeň sa posunie, aby pritlačil aj vonkajšiu doštičku
x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;x.setLineDash([7,7]);x.beginPath();x.moveTo(DC[0]+R+20,DC[1]-30);x.lineTo(SX-96,236);x.stroke();x.setLineDash([]);
const body=()=>{x.moveTo(bx-84,126);x.lineTo(bx+150,126);x.lineTo(bx+150,330);x.lineTo(bx+46,330);x.lineTo(bx+46,170);x.lineTo(bx-52,170);x.lineTo(bx-52,318);x.lineTo(bx-84,318);x.closePath()};
x.beginPath();body();x.lineWidth=8;x.strokeStyle='#fff';x.stroke();{const gg=x.createLinearGradient(0,126,0,330);gg.addColorStop(0,'#3a3e44');gg.addColorStop(1,'#1c1e21');x.fillStyle=gg}x.fill();hatch(x,body);
// valec s kvapalinou a prívodná hadička: pri stlačení pedálu kvapalina svieti (tlak) a tečie dnu
const px=SX+13+g+28,fl=mix('#8a5a18','#ffc247',a);x.fillStyle='#050607';x.fillRect(bx+46,204,84,72);x.fillStyle=fl;x.fillRect(px+50,206,bx+130-(px+50),68);x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(bx+46,204,84,72);
x.strokeStyle='#fff';x.lineWidth=18;x.beginPath();x.moveTo(bx+128,240);x.lineTo(bx+236,240);x.stroke();x.strokeStyle=fl;x.lineWidth=11;x.stroke();
for(let i=0;i<7;i++){const u=((a*1.6+i/7)%1);dot(x,[bx+236-u*120,240],3,'#fff3d0',(tt>tA&&tt<tB+.3?.9:.0)*Math.sin(Math.PI*u),false)}
x.save();x.shadowColor='rgba(0,0,0,.5)';x.shadowBlur=8;x.fillStyle=metal(x,px,px+52);x.fillRect(px,208,52,64);x.restore();x.strokeStyle='#fff';x.lineWidth=2.5;x.strokeRect(px,208,52,64);
// kotúč v reze (žeraví sa rovnako ako spredu) a doštičky s kovovou podložkou
x.fillStyle='#8f959c';x.fillRect(SX-13,150,26,330);if(K>.02){x.save();x.globalCompositeOperation='lighter';x.globalAlpha=p*Math.min(1,K*1.6);x.fillStyle=heat(K);x.fillRect(SX-13,176,26,150);x.restore()}x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(SX-13,150,26,330);
[[SX+13+g,1],[SX-13-g,-1]].forEach(([fx,sd])=>{x.fillStyle='#4a4038';x.fillRect(sd>0?fx:fx-20,186,20,120);x.fillStyle='#c9cdd1';x.fillRect(sd>0?fx+20:fx-28,182,8,128);x.strokeStyle='#fff';x.lineWidth=2;x.strokeRect(sd>0?fx:fx-28,182,28,128)});
if(a>.6&&braking){x.save();x.globalCompositeOperation='lighter';[SX+13,SX-13].forEach(fx=>{const gg=x.createLinearGradient(fx-14,0,fx+14,0);gg.addColorStop(0,'rgba(255,160,60,0)');gg.addColorStop(.5,`rgba(255,160,60,${.55*(w/W0+.3)})`);gg.addColorStop(1,'rgba(255,160,60,0)');x.fillStyle=gg;x.fillRect(fx-14,186,28,120)});x.restore()}
// šípky sily na doštičky
if(a>.05){x.globalAlpha=p*a;[[SX+96,1],[SX-70,-1]].forEach(([ax,sd])=>{x.strokeStyle=A;x.fillStyle=A;x.lineWidth=6;x.beginPath();x.moveTo(ax,350);x.lineTo(ax-sd*34,350);x.stroke();x.beginPath();x.moveTo(ax-sd*48,350);x.lineTo(ax-sd*30,340);x.lineTo(ax-sd*30,360);x.closePath();x.fill()});x.globalAlpha=p}
x.globalAlpha=p*sp*(1-ez((cm[2]/zf-1)/.22));tag(S,LN[0],DC[0],DC[1]+R+34,'center');tag(S,LN[1],SX+30,96,'center');tag(S,LN[2],SX,392,'center');
x.restore();x.globalAlpha=p;
const fi=['disc','caliper'].indexOf(String(d.f||''));if(fi>=0&&t>.35)stamp(S,fi,LN[fi]||'',2,t-.35,A);
meter(S,String(Math.round(w/W0*100)),'KM/H',A,cl((t-.6)/.4),fi>=0);
if(K>.03){x.save();x.globalAlpha=p*Math.min(1,K*3);x.textAlign='right';x.textBaseline='alphabetic';x.font=`900 54px ${S.FT}`;x.lineJoin='round';x.strokeStyle='rgba(0,0,0,.8)';x.lineWidth=10;const s2=Math.round(40+460*K)+' °C';x.strokeText(s2,S.w-44,S.h-74);x.fillStyle=K>.5?'#ffb347':'#ff6a3a';x.fillText(s2,S.w-44,S.h-74);x.restore()}
callout(S,d,t,A);x.globalAlpha=1}};
// pomôcky pre ďalšie súbory s modelmi (zz_mech_pro_c.js)
Object.assign(K,{LBL,tag,meter,cams});
}
