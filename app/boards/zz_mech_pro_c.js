// Presné modely 3 – prevody: prevodovka a diferenciál. Kolesá sú kreslené zboku (os leží v rovine obrazu),
// zuby sú pásiky, ktoré sa posúvajú presne podľa uhla natočenia. Točí sa len to, čo sa točí naozaj.
{
const K=window.KIT,PRO=K.PRO,{mix,ez,poly,hatch,STG,camAt,stamp,callout,LBL,tag,meter,cams,CTX}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},mx=(a,b,k)=>a+(b-a)*k;
// uhol = integrál otáčok (Simpson), aby sa pri zmene rýchlosti nič neposkočilo a snímka sa dala vypočítať pre ľubovoľný čas
const integ=(f,t)=>{if(t<=0)return 0;const n=48,h=t/n;let s=f(0)+f(t);for(let i=1;i<n;i++)s+=f(i*h)*(i%2?4:2);return s*h/3};
// koleso alebo hriadeľ zboku: valec (r0=r1) alebo kužeľ; th = uhol natočenia, z = počet zubov; kladný uhol posúva viditeľnú stranu v smere +y
const edge=(x,cx,cy,wd,r0,r1,th,z,o)=>{o=o||{};x.save();x.translate(cx,cy);if(o.rot)x.rotate(o.rot);const h=wd/2,P=[[-h,-r0],[h,-r1],[h,r1],[-h,r0]],rm=Math.max(r0,r1),ga=x.globalAlpha,c=o.col||['#30343a','#8f959c','#2a2d32'];
x.beginPath();poly(x,P);const g=x.createLinearGradient(0,-rm,0,rm);g.addColorStop(0,c[0]);g.addColorStop(.4,c[1]);g.addColorStop(1,c[2]);x.fillStyle=g;x.fill();
x.save();x.clip();x.lineCap='butt';x.strokeStyle=o.tooth||'#ffffff';for(let k=0;k<z;k++){const ph=th+k*TAU/z,cs=Math.cos(ph);if(cs<=.04)continue;const s=Math.sin(ph);x.lineWidth=Math.max(.8,(o.lw||3.2)*cs);x.globalAlpha=ga*(.2+.75*cs)*(o.ta==null?1:o.ta);x.beginPath();x.moveTo(-h,r0*s);x.lineTo(h,r1*s);x.stroke()}x.restore();
x.globalAlpha=ga;x.beginPath();poly(x,P);x.strokeStyle=o.line||'#fff';x.lineWidth=o.ow||3;x.lineJoin='round';x.stroke();x.restore()};
const SH=['#5b6067','#eef1f4','#565b62'];   // leštený hriadeľ
const bearing=(x,cx,cy,w,h)=>{x.fillStyle='#4a4f56';x.strokeStyle='#fff';x.lineWidth=2.5;x.beginPath();x.rect(cx-w/2,cy-h/2,w,h);x.fill();x.stroke();x.beginPath();x.moveTo(cx-w/2,cy-h/2);x.lineTo(cx+w/2,cy+h/2);x.moveTo(cx+w/2,cy-h/2);x.lineTo(cx-w/2,cy+h/2);x.lineWidth=1.5;x.stroke()};
const rr=(x,X,Y,W,H,r)=>x.roundRect(X,Y,W,H,r);
// popisok s tenkou čiarou k dielu
const lead=(S,s,px,py,tx,ty)=>{if(!s)return;const x=S.x;x.save();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=2;x.beginPath();x.moveTo(px,py+(ty>py?16:-16));x.lineTo(tx,ty);x.stroke();x.fillStyle='#fff';x.beginPath();x.arc(tx,ty,4,0,TAU);x.fill();x.restore();tag(S,s,px,py,'center')};
const badge=(S,big,small,A,a)=>{const x=S.x;x.save();x.globalAlpha*=a;x.textAlign='right';x.textBaseline='alphabetic';x.font=`800 34px ${S.FT}`;const w2=x.measureText(small).width;x.font=`900 84px ${S.FT}`;const w1=x.measureText(big).width,X=S.w-44,Y=S.h-62;
x.fillStyle='rgba(0,0,0,.8)';x.beginPath();x.roundRect(X-w1-w2-34,Y-76,w1+w2+50,100,16);x.fill();x.fillStyle='#fff';x.font=`800 34px ${S.FT}`;x.fillText(small,X,Y);x.fillStyle=A;x.font=`900 84px ${S.FT}`;x.fillText(big,X-w2-16,Y+4);x.restore()};

// ---------- prevodovka (manuálna, stále v zábere): motor točí vstupný hriadeľ a predlohu, všetky páry sa točia stále,
// presuvná objímka uzamkne jedno koleso k výstupnému hriadeľu – tým sa zaradí stupeň ----------
// l = [vstupný hriadeľ, páry kolies, presuvná objímka, výstupný hriadeľ]; f = input | gears | collar | output | run | g1 | g2 | g3 (zaradený stupeň)
PRO.gearbox=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,Y1=196,Y2=376,M=7.5,FW=46,WI=2.3;
const zf=Math.min(S.w/880,S.h/600)*.98,FULL=[420,292,zf],GV=[445,300,zf*1.3],FV={input:[150,286,zf*1.7],gears:[445,300,zf*1.42],collar:[540,206,zf*2.25],output:[690,240,zf*1.7],g1:GV,g2:GV,g3:GV},G0=({g1:1,g2:2,g3:3})[String(d.f||'')]||0,KF=cams(d,FULL,FV,['input','gears','collar','output'],DUR);
// páry: [x, zuby na predlohe, zuby hore]; súčet zubov je vždy 48, preto všetky páry sedia na tej istej vzdialenosti hriadeľov
const IN=[130,28,20],GP=[[620,14,34],[450,20,28],[270,26,22]],WL=WI*IN[2]/IN[1],WG=GP.map(g=>WL*g[1]/g[2]),RAT=WG.map(w=>WI/w),SD=.9,T1=G0?(G0==1?1e9:G0==2?.9:-10):DUR*.34,T2=G0?(G0==3?.9:1e9):DUR*.64;   // g1–g3: stupeň ostane zaradený (g2, g3 sa na začiatku zaradia)
const sh=t=>ez((t-T1)/SD)+ez((t-T2)/SD),wout=t=>{const s=sh(t);return s<=1?mx(WG[0],WG[1],s):mx(WG[1],WG[2],s-1)};
const gear=(X,Y,z,th,col,ta)=>edge(x,X,Y,FW,M*z/2,M*z/2,th,z,{tooth:col,ta});
const fork=(xc,k)=>{x.fillStyle=mix('#6c7178',A,k);x.strokeStyle='#fff';x.lineWidth=2;x.beginPath();x.rect(xc-5,64,10,Y1-64-52);x.fill();x.stroke();x.beginPath();x.rect(xc-22,Y1-56,44,12);x.fill();x.stroke()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),wo=wout(t),ao=integ(wout,t),ai=WI*t,al=-WL*t;
const e1=1-ez((t-T1)/(SD*.4)),e2=ez((t-T1-SD*.6)/(SD*.4))*(1-ez((t-T2)/(SD*.4))),e3=ez((t-T2-SD*.6)/(SD*.4)),EN=[e1,e2,e3],xB=535+36*e1-36*e2,xA=355-36*e3;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(420,290,20,420,290,500);g.addColorStop(0,'rgba(86,118,160,.2)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(-120,-240,1080,1060)}
// skriňa
x.beginPath();rr(x,40,34,760,488,26);x.fillStyle='#24272b';x.fill();hatch(x,()=>rr(x,40,34,760,488,26));x.lineWidth=7;x.strokeStyle='#fff';x.beginPath();rr(x,40,34,760,488,26);x.stroke();x.beginPath();rr(x,58,52,724,452,14);x.fillStyle='#07090b';x.fill();x.lineWidth=4;x.stroke();
// vodiaca tyč vidlíc
x.fillStyle='#565b62';x.fillRect(250,60,420,8);x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=1.5;x.strokeRect(250,60,420,8);
// predloha: všetky štyri kolesá sú na nej napevno
edge(x,420,Y2,716,14,14,al,6,{col:SH,tooth:'#30343a',lw:2,ow:2.5});gear(IN[0],Y2,IN[1],al,A,1);GP.forEach((g,i)=>gear(g[0],Y2,g[1],al,mix('#ffffff',A,EN[i]),.55+.45*EN[i]));
// vstupný hriadeľ s kolesom napevno
edge(x,82,Y1,188,15,15,ai,6,{col:SH,tooth:'#30343a',lw:2,ow:2.5});gear(IN[0],Y1,IN[2],ai,A,1);
// výstupný hriadeľ; kolesá sa na ňom točia voľne, kým ich objímka neuzamkne
edge(x,517,Y1,666,15,15,ao,6,{col:SH,tooth:'#30343a',lw:2,ow:2.5});
GP.forEach((g,i)=>{const th=WG[i]*t,col=mix('#ffffff',A,EN[i]);gear(g[0],Y1,g[2],th,col,.55+.45*EN[i]);const dx=i==0?-(FW/2+8):FW/2+8;edge(x,g[0]+dx,Y1,16,38,38,th,18,{tooth:col,lw:2,ow:2,ta:.7})});
// náboje a presuvné objímky sa točia vždy s výstupným hriadeľom
[[535,xB,Math.max(e1,e2)],[355,xA,e3]].forEach(q=>{edge(x,q[0],Y1,30,30,30,ao,10,{tooth:'#30343a',lw:2,ow:2});edge(x,q[1],Y1,36,45,45,ao,18,{col:['#3a2a1a','#c9843e','#33230f'],tooth:mix('#ffffff',A,q[2]),lw:2.4});fork(q[1],q[2])});
// ložiská v stenách skrine
[[49,Y1],[791,Y1]].forEach(q=>{bearing(x,q[0],q[1]-24,18,14);bearing(x,q[0],q[1]+24,18,14)});[[66,Y2],[774,Y2]].forEach(q=>bearing(x,q[0],q[1],16,44));
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-ez((cm[2]/zf-1)/.22));lead(S,LN[0],150,6,84,Y1-17);lead(S,LN[2],445,6,445,58);lead(S,LN[3],700,6,720,Y1-17);lead(S,LN[1],440,550,450,Y2+78);
x.restore();x.globalAlpha=p;
const fi=G0?1:['input','gears','collar','output'].indexOf(String(d.f||''));if(fi>=0&&t>.35)stamp(S,fi,LN[fi]||'',4,t-.35,A);
const gn=Math.min(2,Math.round(sh(t))),a=cl((t-.6)/.4);meter(S,(Math.round(3000*wo/WI/10)*10).toLocaleString('en-US'),'RPM',A,a,fi>=0);badge(S,String(gn+1),RAT[gn].toFixed(2)+' : 1',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
CTX.gearbox=['car','gearbox'];

// ---------- diferenciál (otvorený): pastorok točí tanierové koleso s klietkou; v klietke sú satelity, ktoré dovolia,
// aby sa kolesá v zákrute točili rôzne rýchlo. Súčet otáčok oboch kolies je vždy dvojnásobok otáčok klietky. ----------
// Pohľad zhora, rez v rovine osí. Vnútro klietky je kreslené voči klietke: rovno sa v nej nič nehýbe, v zákrute sa satelity pretáčajú.
// l = [pastorok, tanierové koleso, satelity, poloos]; f = pinion | spider | turn (celý čas zákruta) | straight (celý čas rovno)
PRO.differential=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,CX=430,CY=310,RR=190,RP=57,WC=1.15,ZR=40,ZP=12,F=String(d.f||''),HOLD=F=='hold'||!!d.h,DV=HOLD?1:.35,H=Math.PI/2;
const zf=Math.min(S.w/770,S.h/700)*.98,FULL=[430,332,zf],FV={pinion:[404,196,zf*1.9],spider:[430,339,zf*2.2],turn:[430,332,zf*1.04],hold:[430,332,zf*.87],straight:[430,339,zf*1.5]},KF=cams(d,FULL,FV,['pinion','spider'],DUR);
// jazda: rovno → zákruta vľavo (ľavé koleso je vnútorné, ide pomalšie) → rovno; HOLD = ľavé koleso niekto drží, pravé ide dvakrát rýchlejšie než klietka
const TA=F=='straight'?1e9:HOLD&&F!='hold'?-9:(F=='turn'||F=='hold')?.8:DUR*.3,TB=(F=='turn'||HOLD)?1e9:DUR*.74,turn=t=>ez((t-TA)/1)*(1-ez((t-TB)/1)),wl=t=>WC*(1-DV*turn(t)),wr=t=>WC*(1+DV*turn(t)),rel=t=>WC*DV*turn(t);
const tyre=(X,th)=>{edge(x,X,CY,72,118,118,th,24,{col:['#0c0d0e','#3b3e42','#0a0b0c'],tooth:'#9aa0a6',lw:5,ta:.8,ow:3});edge(x,X+(X<CX?45:-45),CY,18,40,40,th,5,{tooth:'#30343a',lw:2,ow:2})};
const cage=()=>{x.beginPath();rr(x,CX-112,CY-112,224,224,20);rr(x,CX-150,CY-36,300,72,8)};
const arrow=k=>{x.save();x.translate(S.w/2,S.h-48);x.fillStyle='rgba(0,0,0,.8)';x.beginPath();x.roundRect(-84,-106,148,128,16);x.fill();x.strokeStyle=A;x.lineWidth=9;x.lineCap='round';x.lineJoin='round';const ex=-60*k,ey=-78+22*k;x.beginPath();x.moveTo(0,0);x.quadraticCurveTo(0,-52,ex,ey);x.stroke();x.translate(ex,ey);x.rotate(-k*1.15);x.beginPath();x.moveTo(-17,16);x.lineTo(0,-6);x.lineTo(17,16);x.stroke();x.restore()};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),k=turn(t),ac=-WC*t,aL=-integ(wl,t),aR=-integ(wr,t),ar=integ(rel,t),ap=WC*ZR/ZP*t;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
{const g=x.createRadialGradient(430,300,20,430,300,500);g.addColorStop(0,'rgba(86,118,160,.2)');g.addColorStop(1,'rgba(86,118,160,0)');x.fillStyle=g;x.fillRect(-120,-240,1100,1080)}
// skriňa a rúry nápravy (stoja)
x.beginPath();rr(x,246,34,368,502,46);x.fillStyle='#14161a';x.fill();x.lineWidth=5;x.strokeStyle='rgba(255,255,255,.7)';x.stroke();
x.strokeStyle='rgba(255,255,255,.45)';x.lineWidth=3;[[168,246],[614,692]].forEach(q=>{x.beginPath();x.moveTo(q[0],CY-36);x.lineTo(q[1],CY-36);x.moveTo(q[0],CY+36);x.lineTo(q[1],CY+36);x.stroke()});
// poloosi a kolesá: točia sa voči zemi, každé svojou rýchlosťou
edge(x,(150+CX-47)/2,CY,CX-47-150,14,14,aL,6,{col:SH,tooth:'#30343a',lw:2,ow:2.5});edge(x,(710+CX+47)/2,CY,710-CX-47,14,14,aR,6,{col:SH,tooth:'#30343a',lw:2,ow:2.5});tyre(112,aL);tyre(748,aR);
if(HOLD&&k>.02){x.save();x.globalAlpha*=k;x.fillStyle=A;x.strokeStyle='#fff';x.lineWidth=3;[-1,1].forEach(q=>{x.beginPath();x.roundRect(112-50,CY+q*(118+4+16*(1-k))-(q<0?26:0),100,26,8);x.fill();x.stroke()});x.restore()}
// hnací hriadeľ (prichádza spredu, od motora) a tanierové koleso na prírube klietky
edge(x,CX,46,116,14,14,ap,6,{rot:H,col:SH,tooth:'#30343a',lw:2,ow:2.5});bearing(x,CX-27,64,18,36);bearing(x,CX+27,64,18,36);
x.fillStyle='#2c3035';x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.rect(CX-RP-36,CY-RR-10,20,2*RR+20);x.fill();x.stroke();
edge(x,CX-RP-1,CY,32,RR+15,RR-15,ac,ZR,{tooth:A,lw:2.6});
edge(x,CX,CY-RR,54,RP+16,RP-16,ap,ZP,{rot:H,tooth:A});
// klietka: točí sa ako jeden celok okolo osi kolies (pásiky na čapoch ukazujú jej otáčanie)
cage();x.fillStyle='#2c3035';x.fill();hatch(x,cage);cage();x.lineWidth=5;x.strokeStyle='#fff';x.stroke();
edge(x,CX-131,CY,38,36,36,ac,8,{tooth:A,lw:2.4,col:['#23262a','#6f757c','#1f2226']});edge(x,CX+131,CY,38,36,36,ac,8,{tooth:A,lw:2.4,col:['#23262a','#6f757c','#1f2226']});
[[CX-131,-50],[CX-131,50],[CX+131,-50],[CX+131,50]].forEach(q=>bearing(x,q[0],CY+q[1],28,16));
x.beginPath();rr(x,CX-92,CY-92,184,184,12);x.fillStyle='#07090b';x.fill();x.lineWidth=3;x.strokeStyle='#fff';x.stroke();
// vnútro klietky (pohyb voči klietke): čap, dva satelity na čape a dve planétové kolesá na poloosiach
x.fillStyle='#b9bec4';x.fillRect(CX-7,CY-92,14,184);x.strokeStyle='#fff';x.lineWidth=1.5;x.strokeRect(CX-7,CY-92,14,184);
const sc=mix('#ffffff',A,Math.min(1,k*1.4));edge(x,CX-62,CY,30,78,46,ar,14,{tooth:'#ffffff'});edge(x,CX+62,CY,30,46,78,-ar,14,{tooth:'#ffffff'});
edge(x,CX,CY-62,30,78,46,-ar,14,{rot:H,tooth:sc});edge(x,CX,CY+62,30,46,78,ar,14,{rot:H,tooth:sc});
// šípka: celá klietka sa točí
x.strokeStyle=A;x.lineWidth=4;x.lineCap='round';x.lineJoin='round';x.beginPath();x.ellipse(CX+168,CY,18,96,0,-1.1,1.1);x.stroke();x.beginPath();x.moveTo(CX+162,CY-96);x.lineTo(CX+176,CY-86);x.lineTo(CX+190,CY-98);x.stroke();
// popisky pri celkovom pohľade
x.globalAlpha=p*sp*(1-ez((cm[2]/zf-1)/.22));lead(S,LN[0],CX+150,CY-RR-70,CX+44,CY-RR-8);lead(S,LN[1],CX-RP-150,CY+RR-10,CX-RP-8,CY+RR-40);lead(S,LN[2],CX+212,CY+158,CX+24,CY+70);lead(S,LN[3],668,CY-86,650,CY-14);
x.restore();
// otáčky ľavého a pravého kolesa: súčet je stále rovnaký
const fi=['pinion','spider'].indexOf(F),a=cl((t-.6)/.4),nl=Math.round(500*wl(t)/WC/5)*5;x.globalAlpha=p;
if(fi>=0&&t>.35)stamp(S,fi,[LN[0],LN[2]][fi]||'',2,t-.35,A);
if(HOLD){meter(S,(1-k).toFixed(1),'× CAGE',A,a,fi>=0);badge(S,(1+k).toFixed(1),'× CAGE',A,a)}else{meter(S,String(nl),'RPM',A,a,fi>=0);badge(S,String(1000-nl),'RPM',A,a);x.globalAlpha=p*a;arrow(k);x.globalAlpha=p}
callout(S,d,t,A);x.globalAlpha=1}};
CTX.differential=['car','diff'];
}
