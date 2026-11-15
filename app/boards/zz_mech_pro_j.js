// Presné modely 10 – chladnička (rez zboku) a prúdový motor (dvojprúdový, rez pozdĺž osi).
// Hýbe sa len to, čo sa hýbe naozaj: chladivo obieha okruhom, kým beží kompresor, teplo ide zvnútra von cez zadnú mriežku;
// v motore prúdi vzduch – väčšina okolo jadra, zvyšok sa stlačí, spáli a roztočí turbínu, ktorá hriadeľom poháňa ventilátor.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),HOT='#ff6a3d',WARM='#ffb057',COLD='#6ec6ff';
const arw=(x,a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(4+w*2,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};
const lens=P=>{const c=[0];for(let i=1;i<P.length;i++)c.push(c[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));return c};
const at=(P,c,s)=>{let i=1;while(i<P.length-1&&c[i]<s)i++;const k=(s-c[i-1])/((c[i]-c[i-1])||1);return [P[i-1][0]+(P[i][0]-P[i-1][0])*k,P[i-1][1]+(P[i][1]-P[i-1][1])*k]};
const line=(x,P,a,b)=>{x.beginPath();for(let i=a;i<=b;i++)i==a?x.moveTo(P[i][0],P[i][1]):x.lineTo(P[i][0],P[i][1]);x.stroke()};

// ---------- chladnička: l = [kompresor, kondenzátor, škrtenie, výparník]; f = compressor | condenser | valve | evaporator | dirty (zaprášená mriežka) ----------
PRO.fridge=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,DRT=String(d.f||'')=='dirty';
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[490,298,zf*1.1],FV={compressor:[520,496,zf*2.3],condenser:[610,270,zf*1.6],valve:[572,446,zf*2.6],evaporator:[490,170,zf*2.1],dirty:[600,290,zf*1.45]},ORD=['compressor','condenser','valve','evaporator'],KF=cams(d,FULL,FV,ORD,DUR);
// okruh: výtlak (horúci plyn) → kondenzátor vzadu → kapilára → výparník vnútri → sanie späť do kompresora
const P=[[520,498],[640,498],[640,112]];const i0=P.length-1;for(let k=0;k<12;k++){const y=112+28*k,xa=k%2?622:578;P.push([k%2?578:622,y]);P.push([xa,y]);if(k<11)P.push([xa,y+28])}
const i1=P.length-1;P.push([P[i1][0],452],[536,452],[536,84]);const i2=P.length-1;for(let k=0;k<8;k++){const y=84+24*k,xa=k%2?528:474;P.push([xa,y]);if(k<7)P.push([xa,y+24])}
const i3=P.length-1;P.push([552,252],[552,484],[506,484]);const C=lens(P),L=C[C.length-1],kind=s=>s<C[i0]?0:s<C[i1]?1:s<C[i2]?2:s<C[i3]?3:4,COLS=[HOT,WARM,WARM,COLD,'#a9d8ff'];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const on=DRT||t%9<6,ph=DRT?t:Math.floor(t/9)*6+Math.min(t%9,6),run=DRT?1:cl(Math.min(t%9,6-t%9)/.4),temp=DRT?6+Math.min(4,t*.45):4+1.4*(t%9<6?1-(t%9)/6:(t%9-6)/3);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// skriňa s izoláciou, vnútro, dvere s tesnením, priestor kompresora
x.beginPath();x.roundRect(300,50,260,490,10);x.fillStyle='#2a2e33';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();x.fillStyle='#0d1216';x.fillRect(318,66,226,404);x.fillStyle='rgba(110,198,255,.07)';x.fillRect(318,66,226,404);
x.fillStyle='#0a0c0f';x.fillRect(318,476,246,58);x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(318,66,226,404);x.moveTo(318,476);x.lineTo(560,476);x.moveTo(318,476);x.lineTo(318,534);x.stroke();
x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.beginPath();x.moveTo(309,54);x.lineTo(309,470);x.stroke();x.fillStyle='#eef1f4';x.beginPath();x.roundRect(287,200,8,74,4);x.fill();
// police a potraviny
x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2.5;x.beginPath();x.moveTo(322,176);x.lineTo(462,176);x.moveTo(322,276);x.lineTo(462,276);x.moveTo(322,372);x.lineTo(540,372);x.stroke();
x.fillStyle='#3a3e44';x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=2;[[336,120,22,56,7],[366,136,22,40,7],[404,146,44,30,4],[336,232,56,44,5],[410,224,18,52,8],[436,224,18,52,8],[340,330,70,42,5],[470,320,26,52,9],[504,320,26,52,9],[350,428,90,42,6]].forEach(q=>{x.beginPath();x.roundRect(q[0],q[1],q[2],q[3],q[4]);x.fill();x.stroke()});[[432,358],[452,358],[474,456],[500,456]].forEach(c=>{dot(x,c,13,'#3a3e44',p,false);x.beginPath();x.arc(c[0],c[1],13,0,TAU);x.stroke()});
// rúrky okruhu podľa stavu chladiva
x.lineJoin='round';x.strokeStyle=HOT;x.lineWidth=5;line(x,P,0,i0);{const g=x.createLinearGradient(0,112,0,440);g.addColorStop(0,HOT);g.addColorStop(1,WARM);x.strokeStyle=g;line(x,P,i0,i1)}
x.strokeStyle=WARM;x.lineWidth=2.2;line(x,P,i1,i2);x.strokeStyle=COLD;x.lineWidth=5;line(x,P,i2,i3);x.strokeStyle='#a9d8ff';x.lineWidth=4;line(x,P,i3,P.length-1);
for(let i=0;i<46;i++){const s=((ph*70+i*L/46)%L+L)%L,q=at(P,C,s),k=kind(s);dot(x,q,k==2?2.2:3.4,'#fff',p*.95,false)}
// kompresor
{const c=[500,508],sh=on?Math.sin(t*40)*.8:0;x.fillStyle='#16181b';x.strokeStyle='#fff';x.lineWidth=3.5;x.beginPath();x.arc(c[0]+sh,c[1],27,Math.PI,0);x.lineTo(c[0]+27+sh,c[1]+20);x.lineTo(c[0]-27+sh,c[1]+20);x.closePath();x.fill();x.stroke();
const a=ph*9;x.strokeStyle=on?A:'#8f959c';x.lineWidth=4;x.beginPath();x.arc(c[0]+sh,c[1]+2,11,0,TAU);x.stroke();x.beginPath();x.moveTo(c[0]+sh,c[1]+2);x.lineTo(c[0]+sh+11*Math.cos(a),c[1]+2+11*Math.sin(a));x.stroke()}
// teplo: zvnútra do výparníka (studené šípky), z kondenzátora von do miestnosti (teplé šípky)
x.globalAlpha=p*run;for(let k=0;k<3;k++){const o=(t*14+k*9)%14;arw(x,[412+o,112+k*56],[448+o,112+k*56],COLD,3)}
x.globalAlpha=p*run*(DRT?.3:1);for(let k=0;k<4;k++){const o=(t*18+k*7)%24;arw(x,[652+o,410-k*84-o*.5],[652+o+(DRT?18:34),410-k*84-o*.5-(DRT?12:24)],HOT,3.4)}x.globalAlpha=p;
// prach na mriežke: teplo nemá kadiaľ odísť, kompresor beží bez prestávky
if(DRT)for(let i=0;i<70;i++){x.fillStyle=`rgba(150,150,150,${.5+.35*HS(i,53)})`;x.beginPath();x.arc(572+HS(i,51)*58,104+HS(i,52)*326,3+4*HS(i,54),0,TAU);x.fill()}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],420,576,484,526);lead(S,LN[1],760,250,628,250);lead(S,LN[2],750,480,590,454);lead(S,LN[3],170,120,472,120);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(Math.round(temp)),'°C INSIDE',A,a,fi>=0);badge(S,on?(DRT?'140 W':'90 W'):'0 W',on?'RUNNING':'RESTING',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- prúdový motor: l = [ventilátor, kompresor, spaľovacia komora, turbína, tryska]; f = fan | compressor | combustor | turbine | nozzle ----------
PRO.jet=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,AY=300;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.12],FV={fan:[220,300,zf*1.5],compressor:[350,300,zf*2.4],combustor:[474,300,zf*3],turbine:[560,300,zf*2.6],nozzle:[670,300,zf*1.8]},ORD=['fan','compressor','combustor','turbine','nozzle'],KF=cams(d,FULL,FV,ORD,DUR);
const ip=(T,X)=>{if(X<=T[0][0])return T[0][1];for(let i=1;i<T.length;i++)if(X<=T[i][0]){const k=(X-T[i-1][0])/(T[i][0]-T[i-1][0]);return T[i-1][1]+(T[i][1]-T[i-1][1])*k}return T[T.length-1][1]};
const NI=[[150,124],[200,134],[500,120],[640,95]],CO=[[268,62],[300,76],[620,72],[720,38]],GO=[[280,70],[430,44],[520,46],[610,62],[720,50]],HB=[[150,0],[200,30],[280,22],[430,34],[520,30],[610,26],[700,0]];
// čas, za ktorý vzduch prejde motorom: v jadre sa spomalí a stlačí, za komorou vyletí oveľa rýchlejšie
const tab=vf=>{const X=[],T=[0];for(let q=-80;q<=900;q+=8){X.push(q);T.push(T[T.length-1]+8/vf(q))}return [X,T]},pos=(tb,s)=>{const T=tb[1],tt=((s%T[T.length-1])+T[T.length-1])%T[T.length-1];let i=1;while(i<T.length-1&&T[i]<tt)i++;return tb[0][i-1]+8*(tt-T[i-1])/((T[i]-T[i-1])||1)};
const TB=tab(X=>X<205?150:230),TC=tab(X=>X<205?150:X<430?105:X<520?85:X<610?210:340);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// horúce plyny z trysky
{const g=x.createLinearGradient(700,0,900,0);g.addColorStop(0,'rgba(255,140,60,0)');g.addColorStop(.12,'rgba(255,140,60,.34)');g.addColorStop(1,'rgba(255,140,60,0)');x.fillStyle=g;x.beginPath();x.moveTo(700,AY-40);x.lineTo(900,AY-30);x.lineTo(900,AY+30);x.lineTo(700,AY+40);x.closePath();x.fill()}
const row=(x0,w,r0,r1,sp2,col,g)=>{x.save();x.beginPath();x.rect(x0,g>0?AY-r1:AY+r0,w,r1-r0);x.clip();x.fillStyle=col;x.fillRect(x0,AY-r1-2,w,2*r1+4);if(sp2){x.strokeStyle='rgba(22,24,27,.75)';x.lineWidth=2.4;const H=r1-r0+14;for(let k=0;k<Math.ceil(H/9)+1;k++){const o=((t*sp2*g+k*9)%H+H)%H-7,Y=(g>0?AY-r1:AY+r0)+o;x.beginPath();x.moveTo(x0-2,Y);x.lineTo(x0+w+2,Y+w*.5);x.stroke()}}x.restore()};
[1,-1].forEach(g=>{const Y=r=>AY-g*r,poly=(a,b,f)=>{x.beginPath();a.forEach((q,i)=>i?x.lineTo(q[0],Y(q[1])):x.moveTo(q[0],Y(q[1])));b.slice().reverse().forEach(q=>x.lineTo(q[0],Y(q[1])));x.closePath();x.fillStyle=f;x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke()};
poly([[150,124],[180,148],[480,144],[640,104]],[[158,118],[200,134],[500,120],[640,95]],'#2a2e33');poly(CO,GO,'#2a2e33');
// spaľovacia komora: plameň
for(let i=0;i<5;i++){const fl=.6+.4*Math.sin(t*17+i*2.1),X=452+i*13,r=40;x.fillStyle=i<2?'#ffd27a':'#ff7a2e';x.globalAlpha=p*(.9-.12*i)*fl;x.beginPath();x.ellipse(X,Y(r),13-i*1.4,5.5,0,0,TAU);x.fill()}x.globalAlpha=p;
x.fillStyle=A;x.beginPath();x.rect(434,Y(40)-3,9,6);x.fill();
// lopatky: rotory sa točia (pásiky idú hore a dole proti sebe), statory stoja
row(206,26,30,ip(NI,219)-2,150,'#c9ced3',g);
for(let k=0;k<5;k++){const X=292+k*28;row(X,11,ip(HB,X)+1,ip(GO,X)-2,210,'#b9bec4',g);row(X+15,7,ip(HB,X+15)+1,ip(GO,X+15)-1,0,'#5a6068',g)}
for(let k=0;k<3;k++){const X=526+k*28;row(X,11,ip(HB,X)+1,ip(GO,X)-2,210,'#e2b48c',g);row(X+15,7,ip(HB,X+15)+1,ip(GO,X+15)-1,0,'#6b5a4c',g)}});
// hriadeľ a náboj: turbína vzadu poháňa kompresor aj ventilátor vpredu
x.beginPath();HB.forEach((q,i)=>i?x.lineTo(q[0],AY-q[1]):x.moveTo(q[0],AY-q[1]));HB.slice().reverse().forEach(q=>x.lineTo(q[0],AY+q[1]));x.closePath();{const g=x.createLinearGradient(0,AY-34,0,AY+34);g.addColorStop(0,'#6b7077');g.addColorStop(.5,'#dfe3e7');g.addColorStop(1,'#5a6068');x.fillStyle=g;x.fill()}x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.save();x.beginPath();x.rect(236,AY-7,290,14);x.clip();x.strokeStyle='rgba(22,24,27,.6)';x.lineWidth=2.5;for(let k=0;k<26;k++){const X=236+k*12,o=((t*60)%14);x.beginPath();x.moveTo(X,AY-7+o-14);x.lineTo(X+6,AY+7+o-14);x.moveTo(X,AY-7+o);x.lineTo(X+6,AY+7+o);x.stroke()}x.restore();
// vzduch: obtok (studený, väčšina ťahu) a jadro (stlačí sa, zohreje, spáli a vyletí)
for(let i=0;i<40;i++){const X=pos(TB,t+i*.19),f=HS(i,61),g=i%2?1:-1,lo=X<205?10:X<268?ip(HB,X)+34:ip(CO,X)+4,hi=X<150?150:X<640?ip(NI,X)-4:95-4,r=X>640?ip(CO,640)+4+f*(91-ip(CO,640)-4)+(X-640)*.02:lo+f*(hi-lo);
if(X<205&&f<.45)continue;dot(x,[X,AY-g*r],3.2,'#cfe6ff',p*.9*cl((X+80)/60)*cl((900-X)/120),false)}
for(let i=0;i<34;i++){const X=pos(TC,t+i*.23),f=.15+.7*HS(i,62),g=i%2?1:-1,lo=ip(HB,X)+3,hi=X<280?70:X>720?50:ip(GO,X)-3,r=X<205?8+f*60:X>700?4+f*44:lo+f*(hi-lo);
dot(x,[X,AY-g*r],X>430&&X<520?3.6:3,X<300?'#cfe6ff':X<430?mix('#cfe6ff','#ffd9a8',cl((X-300)/130)):X<470?'#ffd9a8':'#ff9a4d',p*.95*cl((X+80)/60)*cl((900-X)/140),false)}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],200,96,220,AY-112);lead(S,LN[1],360,96,350,AY-52);lead(S,LN[2],474,520,474,AY+46);lead(S,LN[3],580,96,566,AY-50);lead(S,LN[4],720,520,690,AY+44);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',5,ts-.35,A);
meter(S,'1500','°C FLAME',A,a,fi>=0);badge(S,'80 %','FAN THRUST',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
