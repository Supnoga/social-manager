// Presné modely 11 – tranzistor (MOSFET v reze) a istič (rez; aj porovnanie s poistkou).
// Hýbe sa len to, čo sa hýbe naozaj: napätie na hradle pritiahne elektróny, vznikne kanál a obvodom tečie prúd;
// v ističi sa pri preťažení ohne bimetal, pri skrate vystrelí kotva cievky, západka pustí a pružina rozpojí kontakty.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),EL='#8fd0ff',HOT='#ff6a3d';
const arw=(x,a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(4+w*2,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};
const lens=P=>{const c=[0];for(let i=1;i<P.length;i++)c.push(c[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));return c};
const at=(P,c,s)=>{let i=1;while(i<P.length-1&&c[i]<s)i++;const k=(s-c[i-1])/((c[i]-c[i-1])||1);return [P[i-1][0]+(P[i][0]-P[i-1][0])*k,P[i-1][1]+(P[i][1]-P[i-1][1])*k]};

// ---------- tranzistor: l = [emitor/source, hradlo, kolektor/drain, kanál]; f = source | gate | drain | channel | on | off ----------
PRO.transistor=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||'');
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,330,zf*1.2],FV={source:[300,320,zf*2.2],gate:[450,280,zf*2.3],drain:[600,320,zf*2.2],channel:[450,322,zf*2.9],on:[450,330,zf*1.2],off:[450,330,zf*1.2]},ORD=['source','gate','drain','channel'],KF=cams(d,FULL,FV,ORD,DUR);
const LP=[[305,300],[370,310],[530,310],[595,300],[595,130],[305,130],[305,300]],LC=lens(LP),LL=LC[LC.length-1];
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
const u=t%6,vg=F=='on'?sm((t-.8)/.8):F=='off'?0:u<1.2?0:u<2?sm((u-1.2)/.8):u<4.6?1:u<5.3?1-sm((u-4.6)/.7):0,on=cl((vg-.45)/.3);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// kremík: podložka (typ P, diery) a dve oblasti typu N (plné voľných elektrónov)
x.beginPath();x.roundRect(200,300,500,220,8);x.fillStyle='#232b33';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
for(let i=0;i<40;i++){const X=220+HS(i,3)*460,Y0=330+HS(i,4)*176,under=X>360&&X<540?cl(1-(Y0-330)/90):0,Y=Y0+under*34*vg+2*Math.sin(t*1.3+i);x.strokeStyle='rgba(255,255,255,.3)';x.lineWidth=1.6;x.beginPath();x.arc(X,Y,3.6,0,TAU);x.stroke()}
[[240,'s'],[530,'d']].forEach(([X])=>{x.beginPath();x.roundRect(X,300,130,72,[0,0,14,14]);x.fillStyle='#254a63';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();for(let i=0;i<12;i++)dot(x,[X+12+HS(i,5+X)*106+2.5*Math.sin(t*3+i),312+HS(i,6+X)*48+2.5*Math.cos(t*2.6+i*2)],3,EL,p*.9,false)});
// izolant (oxid), hradlo a kontakty
x.fillStyle='#d9dde1';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(366,288,168,12);x.fill();x.stroke();
x.fillStyle=mix('#8f959c',A,vg);x.lineWidth=3.5;x.beginPath();x.roundRect(378,246,144,42,6);x.fill();x.stroke();if(vg>.02){x.strokeStyle=rgba(A,.5*vg);x.lineWidth=10;x.beginPath();x.roundRect(378,246,144,42,6);x.stroke()}
x.fillStyle='#8f959c';x.strokeStyle='#fff';x.lineWidth=3.5;[270,560].forEach(X=>{x.beginPath();x.roundRect(X,262,70,38,5);x.fill();x.stroke()});
// pole hradla ťahá elektróny pod oxid: vznikne kanál
for(let k=0;k<5;k++){x.globalAlpha=p*vg*.9;arw(x,[394+k*28,302],[394+k*28,302+16*vg],A,2.6)}x.globalAlpha=p;
for(let i=0;i<22;i++){const X=374+i*7.3+2*Math.sin(t*5+i),a=cl(vg*22-i*.6);if(a>0)dot(x,[X+(on?((t*60)%7.3):0),308+3*Math.sin(i*2.1)],3,EL,p*a,false)}
// obvod: batéria a žiarovka medzi source a drain; signál na hradle
x.strokeStyle='#e8ecef';x.lineWidth=3.5;x.beginPath();x.moveTo(305,262);x.lineTo(305,130);x.lineTo(352,130);x.moveTo(372,130);x.lineTo(478,130);x.moveTo(522,130);x.lineTo(595,130);x.lineTo(595,262);x.moveTo(450,246);x.lineTo(450,196);x.stroke();
x.lineWidth=4;x.beginPath();x.moveTo(352,108);x.lineTo(352,152);x.stroke();x.lineWidth=7;x.beginPath();x.moveTo(372,118);x.lineTo(372,142);x.stroke();
if(on>.02){const g=x.createRadialGradient(500,130,4,500,130,64);g.addColorStop(0,rgba('#ffe08a',.85*on));g.addColorStop(1,rgba('#ffe08a',0));x.fillStyle=g;x.beginPath();x.arc(500,130,64,0,TAU);x.fill()}
x.fillStyle=mix('#16181b','#ffe08a',on*.9);x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.arc(500,130,22,0,TAU);x.fill();x.stroke();x.strokeStyle=on>.5?'#fff':'#8f959c';x.lineWidth=2.4;x.beginPath();x.moveTo(488,138);x.lineTo(494,122);x.lineTo(500,138);x.lineTo(506,122);x.lineTo(512,138);x.stroke();
x.fillStyle=mix('#2a2e33',A,vg);x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(426,160,48,36,6);x.fill();x.stroke();x.strokeStyle='#fff';x.lineWidth=2.6;x.beginPath();x.moveTo(434,186);x.lineTo(442,186);x.lineTo(442,186-14*vg);x.lineTo(458,186-14*vg);x.lineTo(458,186);x.lineTo(466,186);x.stroke();
// prúd: elektróny idú zo source kanálom do drain a obvodom späť
if(on>.02)for(let i=0;i<18;i++){const s=((t*150+i*LL/18)%LL+LL)%LL;if(s>LC[1]&&s<LC[2])continue;const q=at(LP,LC,s);dot(x,q,3.6,EL,p*on,true)}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],230,566,300,374);lead(S,LN[1],730,236,524,268);lead(S,LN[2],670,566,600,374);lead(S,LN[3],450,566,450,316);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,vg.toFixed(1),'V ON GATE',A,a,fi>=0);badge(S,on>.5?'ON':'OFF',on>.5?'CURRENT':'NO CURRENT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};

// ---------- istič: l = [kontakty, bimetal, cievka, zhášacia komora]; f = contacts | bimetal | coil | arc | overload | short | fuse (porovnanie s poistkou) ----------
PRO.breaker=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),SH=F=='short',FU=F=='fuse',FC=[430,172],PV=[520,212];
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf*1.05],FV={contacts:[445,186,zf*2.5],bimetal:[548,322,zf*2.1],coil:[450,428,zf*2.4],arc:[392,184,zf*2.6],overload:[470,300,zf*1.3],short:[450,320,zf*1.3],fuse:[375,300,zf]},ORD=['contacts','bimetal','coil','arc'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
// časová os: bežný prúd → preťaženie (bimetal sa hreje) → vypnutie → chladnutie → znovu zapnutie; pri skrate vypne cievka okamžite
let I=10,h=0,open=0,since=-1,plg=0;const u=SH?t%9:FU?Math.min(t,9.9):t%10;
if(SH){if(u>=7){open=1-sm((u-7)/.5);I=open<.05?10:0}else if(u>=1.5){I=u<1.56?3000:0;plg=cl((u-1.5)/.05)*(1-sm((u-3)/.8));since=u-1.56;open=cl(since/.12)}}
else{if(u<2){}else if(u<6){I=24;h=(u-2)/4}else if(u<8.5){I=0;h=Math.max(0,1-(u-6)/2.2);since=u-6;open=cl(since/.12)}else{h=0;open=1-sm((u-8.5)/.5);I=open<.05?10:0}}
const th=-.52*open,c=Math.cos(th),s=Math.sin(th),TIP=[PV[0]-90*c+40*s,PV[1]-90*s-40*c],bend=26*sm(h),closed=open<.04,PATH=[[450,74],[450,150],FC,PV,[560,252],[560,400],[500,426],[400,426],[400,480],[450,508]],PC=lens(PATH),PL=PC[PC.length-1];
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// poistka na porovnanie: tenký drôtik sa pri preťažení roztaví a už sa nedá zapnúť
if(FU){const melt=u>=6;x.strokeStyle='#e8ecef';x.lineWidth=3.5;x.beginPath();x.moveTo(40,452);x.lineTo(96,452);x.moveTo(244,452);x.lineTo(270,452);x.stroke();
x.fillStyle='rgba(207,230,255,.1)';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(104,430,132,44,8);x.fill();x.stroke();x.fillStyle='#8f959c';[[92,426],[226,426]].forEach(q=>{x.beginPath();x.roundRect(q[0],q[1],22,52,5);x.fill();x.stroke()});
x.strokeStyle=mix('#e8ecef',HOT,melt?.2:sm(h));x.lineWidth=2.4+1.5*sm(h)*(melt?0:1);x.beginPath();if(melt){x.moveTo(114,452);x.lineTo(152,452);x.moveTo(188,452);x.lineTo(226,452);x.stroke();for(let i=0;i<5;i++)dot(x,[158+i*6,456+Math.min(12,(u-6)*30)*(.4+HS(i,7))],2.4,'#8f959c',p,false)}else{x.moveTo(114,452);x.lineTo(226,452);x.stroke();if(h>.3)for(let i=0;i<3;i++)dot(x,[140+i*30,452],5+3*Math.sin(t*9+i),HOT,p*.5*sm(h),true)}}
// puzdro, svorky, páčka
x.beginPath();x.roundRect(280,56,340,490,14);x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
x.fillStyle='#8f959c';x.lineWidth=3;[[420,66],[420,496]].forEach(q=>{x.beginPath();x.roundRect(q[0],q[1],60,34,5);x.fill();x.stroke();dot(x,[q[0]+30,q[1]+17],8,'#16181b',p,false)});
{const a=.5-1*open;x.save();x.translate(296,330);x.rotate(a);x.fillStyle=closed?A:'#8f959c';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.roundRect(-66,-12,84,24,8);x.fill();x.stroke();x.restore();dot(x,[296,330],8,'#eef1f4',p,false)}
// zhášacia komora: plechy, na ktorých sa oblúk rozdelí a zhasne
x.strokeStyle='#c9ced3';x.lineWidth=3.2;for(let k=0;k<7;k++){x.beginPath();x.moveTo(312,134+k*16);x.lineTo(392,134+k*16);x.stroke()}
// vodiče prúdovej cesty: pevný kontakt, rameno, bimetal, cievka
x.strokeStyle='#e8ecef';x.lineWidth=5;x.beginPath();x.moveTo(450,100);x.lineTo(450,150);x.lineTo(FC[0],FC[1]);x.stroke();
x.strokeStyle='rgba(232,236,239,.75)';x.lineWidth=3;x.setLineDash([5,4]);x.beginPath();x.moveTo(PV[0],PV[1]);x.quadraticCurveTo(552,214,560-bend,252);x.stroke();x.setLineDash([]);
x.strokeStyle='#e8ecef';x.lineWidth=9;x.beginPath();x.moveTo(PV[0],PV[1]);x.lineTo(TIP[0],TIP[1]);x.stroke();dot(x,TIP,8,A,p,false);dot(x,FC,8,A,p,false);dot(x,PV,9,'#eef1f4',p,false);
x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=2.4;x.beginPath();{const m=[(PV[0]+TIP[0])/2,(PV[1]+TIP[1])/2],e=[596,128],n=9;x.moveTo(m[0],m[1]);for(let k=1;k<n;k++){const q=k/n,w=(k%2?1:-1)*(7-3*open);x.lineTo(m[0]+(e[0]-m[0])*q+w,m[1]+(e[1]-m[1])*q+w*.6)}x.lineTo(e[0],e[1])}x.stroke();
x.strokeStyle=mix('#c9ced3',HOT,sm(h));x.lineWidth=9;x.beginPath();x.moveTo(560,400);x.quadraticCurveTo(560,320,560-bend,252);x.stroke();x.strokeStyle='#e8ecef';x.lineWidth=5;x.beginPath();x.moveTo(560,400);x.lineTo(532,426);x.lineTo(500,426);x.moveTo(400,426);x.lineTo(400,480);x.lineTo(450,500);x.stroke();
// západka: drží rameno, kým do nej nezatlačí bimetal alebo kotva cievky
{const P1=[PV[0]-36*c+16*s,PV[1]-36*s-16*c],la=.5*open,P2=[500-34*Math.cos(la),292-34*Math.sin(la)],dx=P2[0]-P1[0],dy=P2[1]-P1[1],dd=Math.hypot(dx,dy),hh=Math.sqrt(Math.max(0,52*52-dd*dd/4)),KN=[(P1[0]+P2[0])/2-dy/dd*hh,(P1[1]+P2[1])/2+dx/dd*hh];x.strokeStyle='#c9ced3';x.lineWidth=5;x.beginPath();x.moveTo(P1[0],P1[1]);x.lineTo(KN[0],KN[1]);x.lineTo(P2[0],P2[1]);x.stroke();dot(x,P1,5,'#eef1f4',p,false);dot(x,KN,5,'#eef1f4',p,false);
x.save();x.translate(500,292);x.rotate(.5*open);x.fillStyle=open>.5?'#8f959c':A;x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.roundRect(-34,-7,68,14,5);x.fill();x.stroke();x.restore();dot(x,[500,292],5,'#eef1f4',p,false)}
// cievka s kotvou: pri skrate ju magnetické pole vystrelí hore do západky
x.fillStyle='#c9ced3';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.roundRect(442,372-70*plg,16,74,5);x.fill();x.stroke();x.strokeStyle=SH&&u>=1.5&&u<1.9?A:'#e8a52e';x.lineWidth=4.5;x.beginPath();for(let k=0;k<=10;k++){const X=500-k*10;x.moveTo(X,408);x.lineTo(X-6,444)}x.stroke();
// prúd: bodky po celej ceste, pri preťažení a skrate ich je viac a idú rýchlejšie
if(closed&&I>0){const n=I>100?46:I>15?22:12,spd=I>100?520:I>15?170:90;for(let i=0;i<n;i++){const q=at(PATH,PC,((t*spd+i*PL/n)%PL+PL)%PL);dot(x,q,I>100?4.2:3.4,I>15?'#ffd27a':'#fff',p*.95,I>15)}}
// oblúk pri rozpojení: preskočí medzi kontaktmi, vtiahne sa do plechov a zhasne
if(since>=0&&since<.42){const k=since/.42;x.strokeStyle=mix('#ffffff',A,k);x.lineWidth=5*(1-k)+1.5;x.globalAlpha=p*(1-k*k);x.beginPath();x.moveTo(FC[0],FC[1]);for(let j=1;j<6;j++){const q=j/6;x.lineTo(FC[0]+(TIP[0]-FC[0])*q-70*k*Math.sin(Math.PI*q)+(HS(j+Math.floor(t*40),9)-.5)*14,FC[1]+(TIP[1]-FC[1])*q+(HS(j+Math.floor(t*40),8)-.5)*14)}x.lineTo(TIP[0],TIP[1]);x.stroke();x.globalAlpha=p}
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0],652,118,TIP[0]+30,TIP[1]-10);lead(S,LN[1],656,330,566,330);lead(S,LN[2],652,484,504,430);lead(S,LN[3],170,150,312,166);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(I),'A',A,a,fi>=0);badge(S,closed?'ON':'TRIPPED',closed?(I>15?'TOO MUCH':'NORMAL'):'POWER CUT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
