// Presné bloky 15 – „kto komu“: ľudia, firmy, banky, zariadenia a to, čo si medzi sebou posielajú (peniaze, dáta, tovar, ľudia).
// Nahrádza scény z ikon: každý účastník je nakreslená postava alebo budova, po šípkach naozaj putujú mince, dátové balíčky alebo debny.
// Hýbe sa len to, čo sa hýbe naozaj: tok po šípke, vlny routera, dym komína, ručičky hodín. Ostatné stojí.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,HS,STG,callout,tag}=K;
const TAU=Math.PI*2,PI=Math.PI,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u);
const P0='#14181d',P1='#262b33',P2='#3a414b',P3='#5a6473',LN='#e3e7ec';
const rr=(x,a,b,w,h,r)=>{x.beginPath();x.roundRect(a,b,w,h,r||0)};
const fs=(x,f,s,w)=>{if(f){x.fillStyle=f;x.fill()}if(s){x.strokeStyle=s;x.lineWidth=w||.045;x.stroke()}};
const pl=(x,p,c)=>{x.beginPath();x.moveTo(p[0],p[1]);for(let i=2;i<p.length;i+=2)x.lineTo(p[i],p[i+1]);if(c)x.closePath()};
const ci=(x,a,b,r)=>{x.beginPath();x.arc(a,b,r,0,TAU)};
const at=(x,dx,dy,s,fn)=>{x.save();x.translate(dx,dy);x.scale(s,s);fn();x.restore()};
const lit=(A,a)=>mix(P0,A,.22+.55*a);

// ---------- postavy a budovy v jednotkovom štvorci (-1..1); a = ako veľmi sú práve „v akcii“ (0–1) ----------
const SP={};
SP.person=(x,a,t,A)=>{x.beginPath();x.moveTo(-.62,.84);x.bezierCurveTo(-.62,.22,-.3,.04,0,.04);x.bezierCurveTo(.3,.04,.62,.22,.62,.84);x.closePath();fs(x,P2,LN);
ci(x,0,-.4,.3);fs(x,P2,LN);pl(x,[-.17,.07,0,.32,.17,.07]);fs(x,0,A,.06)};
SP.crowd=(x,a,t,A)=>{at(x,-.56,-.02,.6,()=>SP.person(x,a,t,P3));at(x,.56,-.02,.6,()=>SP.person(x,a,t,P3));at(x,0,.16,.8,()=>SP.person(x,a,t,A))};
SP.phone=(x,a,t,A)=>{rr(x,-.44,-.88,.88,1.76,.14);fs(x,P1,LN);rr(x,-.34,-.7,.68,1.34,.05);fs(x,lit(A,a));rr(x,-.1,-.82,.2,.05,.02);fs(x,LN);
for(let i=0;i<3;i++){pl(x,[-.22,-.42+i*.24,i==2?.04:.22,-.42+i*.24]);fs(x,0,rgba('#ffffff',.4+.5*a),.065)}ci(x,0,.4,.09);fs(x,rgba(A,.6+.4*a))};
SP.screen=(x,a,t,A)=>{rr(x,-.92,-.68,1.84,1.14,.07);fs(x,P1,LN);rr(x,-.82,-.58,1.64,.94,.03);fs(x,lit(A,a));
pl(x,[-.12,-.34,.22,-.11,-.12,.12],1);fs(x,rgba('#ffffff',.55+.45*a));pl(x,[0,.46,0,.72]);fs(x,0,LN,.07);pl(x,[-.42,.74,.42,.74]);fs(x,0,LN,.07)};
SP.laptop=(x,a,t,A)=>{rr(x,-.72,-.62,1.44,.98,.06);fs(x,P1,LN);rr(x,-.62,-.52,1.24,.78,.02);fs(x,lit(A,a));
for(let i=0;i<3;i++){pl(x,[-.42,-.32+i*.2,i==1?.1:.36,-.32+i*.2]);fs(x,0,rgba('#ffffff',.4+.5*a),.055)}pl(x,[-.96,.42,.96,.42,.8,.62,-.8,.62],1);fs(x,P2,LN)};
SP.router=(x,a,t,A)=>{pl(x,[-.5,.3,-.64,-.34]);fs(x,0,LN,.07);pl(x,[.5,.3,.64,-.34]);fs(x,0,LN,.07);rr(x,-.82,.28,1.64,.44,.1);fs(x,P2,LN);
for(let i=0;i<4;i++){ci(x,-.52+i*.2,.5,.05);fs(x,HS(i,Math.floor(t*3))>.4?A:P3)}
for(let i=0;i<3;i++){const u=(t*.55+i/3)%1;x.beginPath();x.arc(0,.2,.22+u*.72,-PI*.78,-PI*.22);x.strokeStyle=rgba(A,(1-u)*.95);x.lineWidth=.065;x.stroke()}};
SP.house=(x,a,t,A)=>{rr(x,-.62,-.12,1.24,.96,.03);fs(x,P2,LN);pl(x,[-.86,-.08,0,-.84,.86,-.08],1);fs(x,P1,LN);rr(x,-.14,.36,.28,.48,.02);fs(x,P1,LN,.035);
rr(x,-.5,.08,.26,.26,.02);fs(x,lit(A,.4+.6*a),LN,.03);rr(x,.24,.08,.26,.26,.02);fs(x,lit(A,.4+.6*a),LN,.03)};
SP.city=(x,a,t,A)=>{[[-.88,-.12,.52],[-.3,-.84,.6],[.36,-.42,.52]].forEach((b,j)=>{rr(x,b[0],b[1],b[2],.82-b[1],.02);fs(x,j==1?P2:P1,LN);const cw=(b[2]-.16)/3;
for(let r=0;b[1]+.3+r*.2<.8;r++)for(let c=0;c<3;c++){rr(x,b[0]+.1+c*cw,b[1]+.12+r*.2,cw-.05,.1,.01);fs(x,HS(j*7+c,r)>.55?rgba(A,.6+.4*a):P3)}});pl(x,[-.98,.82,.98,.82]);fs(x,0,LN,.05)};
SP.shop=(x,a,t,A)=>{rr(x,-.76,-.24,1.52,1.08,.02);fs(x,P2,LN);
for(let i=0;i<5;i++){const l=-.86+i*.344;x.beginPath();x.moveTo(l,-.66);x.lineTo(l+.344,-.66);x.lineTo(l+.344,-.32);x.arc(l+.172,-.32,.172,0,PI);x.closePath();fs(x,i%2?P1:A,LN,.035)}
rr(x,-.58,.04,.52,.42,.02);fs(x,lit(A,.3+.6*a),LN,.035);rr(x,.14,.04,.42,.8,.02);fs(x,P1,LN,.035);ci(x,.23,.46,.035);fs(x,LN)};
SP.bank=(x,a,t,A)=>{pl(x,[-.92,-.38,0,-.88,.92,-.38],1);fs(x,P2,LN);for(let i=0;i<4;i++){rr(x,-.7+i*.4,-.3,.2,.86,.02);fs(x,P1,LN,.04)}
rr(x,-.92,.56,1.84,.14,.02);fs(x,P2,LN);rr(x,-1,.7,2,.14,.02);fs(x,P2,LN);ci(x,0,-.58,.1);fs(x,A)};
SP.factory=(x,a,t,A)=>{for(let i=0;i<3;i++){const u=(t*.3+i/3)%1;ci(x,.58+.1*Math.sin(i*2.1+u*3),-.78-u*.42,.08+u*.1);fs(x,rgba(LN,(1-u)*.45))}
rr(x,.46,-.72,.24,.9,.02);fs(x,P1,LN);pl(x,[-.92,.82,-.92,-.16,-.36,.14,-.36,-.16,.2,.14,.92,.14,.92,.82],1);fs(x,P2,LN);
for(let i=0;i<3;i++){rr(x,-.7+i*.5,.38,.3,.2,.02);fs(x,lit(A,.4+.6*a),LN,.03)}};
SP.server=(x,a,t,A)=>{for(let i=0;i<3;i++){const y=-.82+i*.56;rr(x,-.72,y,1.44,.46,.06);fs(x,P2,LN);for(let j=0;j<2;j++){ci(x,-.5+j*.18,y+.23,.055);fs(x,HS(i*3+j,Math.floor(t*4))>.5-.3*a?A:P3)}
pl(x,[.02,y+.23,.52,y+.23]);fs(x,0,rgba('#ffffff',.5),.05)}};
SP.cloud=(x,a,t,A)=>{x.beginPath();x.arc(-.44,.14,.34,PI*.5,PI*1.5);x.arc(-.08,-.2,.44,PI*1.05,PI*1.85);x.arc(.46,.06,.36,PI*1.4,PI*.5);x.closePath();fs(x,P2,LN);
pl(x,[0,.3,0,-.14]);fs(x,0,A,.08);pl(x,[-.17,.03,0,-.16,.17,.03]);fs(x,0,A,.08)};
SP.doc=(x,a,t,A)=>{pl(x,[-.58,-.86,.24,-.86,.58,-.52,.58,.86,-.58,.86],1);fs(x,P2,LN);pl(x,[.24,-.86,.24,-.52,.58,-.52]);fs(x,0,LN,.04);
for(let i=0;i<4;i++){pl(x,[-.36,-.3+i*.24,i==3?-.04:.36,-.3+i*.24]);fs(x,0,rgba('#ffffff',.55),.06)}ci(x,.28,.56,.14);fs(x,rgba(A,.65+.35*a))};
SP.mail=(x,a,t,A)=>{rr(x,-.88,-.56,1.76,1.12,.06);fs(x,P2,LN);pl(x,[-.86,-.5,0,.12,.86,-.5]);fs(x,0,LN,.05);ci(x,.62,-.52,.16);fs(x,A)};
SP.calendar=(x,a,t,A)=>{rr(x,-.74,-.68,1.48,1.46,.08);fs(x,P2,LN);rr(x,-.74,-.68,1.48,.36,[.08,.08,0,0]);fs(x,A,LN);pl(x,[-.36,-.84,-.36,-.56]);fs(x,0,LN,.09);pl(x,[.36,-.84,.36,-.56]);fs(x,0,LN,.09);
for(let r=0;r<3;r++)for(let c=0;c<4;c++){rr(x,-.56+c*.3,-.16+r*.3,.2,.2,.03);fs(x,r*4+c==6?A:P3)}};
SP.wallet=(x,a,t,A)=>{x.save();x.rotate(-.12);rr(x,-.42,-.76-.08*a,.92,.5,.03);fs(x,A,LN,.035);x.restore();rr(x,-.88,-.44,1.76,1.2,.14);fs(x,P2,LN);rr(x,.3,-.04,.64,.4,.1);fs(x,P1,LN,.04);ci(x,.5,.16,.07);fs(x,A)};
const stack=(x,cx,n,by,A)=>{for(let i=0;i<n;i++){x.beginPath();x.ellipse(cx,by-i*.17,.38,.14,0,0,TAU);fs(x,i==n-1?A:mix(A,'#000000',.4),LN,.035)}};
SP.coins=(x,a,t,A)=>{stack(x,-.4,3,.66,A);stack(x,.42,5,.66,A)};
SP.coin=(x,a,t,A)=>{ci(x,0,0,.74);fs(x,A,LN);ci(x,0,0,.54);fs(x,0,'rgba(0,0,0,.35)',.06);pl(x,[0,-.3,0,.3]);fs(x,0,'rgba(0,0,0,.45)',.1)};
SP.cash=(x,a,t,A)=>{x.save();x.rotate(-.14);rr(x,-.86,-.52,1.72,.96,.05);fs(x,mix(A,'#000000',.5),LN,.035);x.restore();rr(x,-.9,-.4,1.8,1,.06);fs(x,mix(A,'#000000',.22),LN);ci(x,0,.1,.26);fs(x,0,LN,.045);
ci(x,-.66,-.18,.07);fs(x,LN);ci(x,.66,.38,.07);fs(x,LN)};
SP.piggy=(x,a,t,A)=>{ci(x,-.12,-.6-.1*a,.18);fs(x,A,LN,.035);rr(x,-.52,.42,.2,.38,.04);fs(x,P1,LN,.04);rr(x,.2,.42,.2,.38,.04);fs(x,P1,LN,.04);x.beginPath();x.ellipse(-.06,.08,.78,.58,0,0,TAU);fs(x,P2,LN);
pl(x,[.18,-.44,.42,-.76,.52,-.32],1);fs(x,P2,LN,.04);rr(x,.62,-.08,.3,.36,.1);fs(x,P3,LN,.04);ci(x,.4,-.1,.05);fs(x,LN);rr(x,-.34,-.47,.44,.07,.03);fs(x,P0)};
SP.tag=(x,a,t,A)=>{x.save();x.rotate(-.5);pl(x,[-.92,0,-.46,-.5,.82,-.5,.82,.5,-.46,.5],1);fs(x,A,LN);ci(x,-.52,0,.11);fs(x,P0,LN,.035);pl(x,[-.12,-.16,.56,-.16]);fs(x,0,'rgba(0,0,0,.45)',.09);pl(x,[-.12,.16,.34,.16]);fs(x,0,'rgba(0,0,0,.45)',.09);x.restore()};
SP.lock=(x,a,t,A)=>{x.beginPath();x.moveTo(-.36,-.1);x.lineTo(-.36,-.42);x.arc(0,-.42,.36,PI,0);x.lineTo(.36,-.1);fs(x,0,LN,.12);rr(x,-.64,-.12,1.28,.98,.1);fs(x,P2,LN);ci(x,0,.26,.13);fs(x,A);rr(x,-.045,.3,.09,.28,.02);fs(x,A)};
SP.shield=(x,a,t,A)=>{x.beginPath();x.moveTo(0,-.88);x.lineTo(.74,-.6);x.lineTo(.74,0);x.bezierCurveTo(.74,.5,.3,.78,0,.92);x.bezierCurveTo(-.3,.78,-.74,.5,-.74,0);x.lineTo(-.74,-.6);x.closePath();fs(x,P2,LN);pl(x,[-.3,.02,-.06,.28,.36,-.24]);fs(x,0,A,.14)};
SP.key=(x,a,t,A)=>{ci(x,-.46,0,.34);fs(x,0,A,.14);pl(x,[-.12,0,.86,0]);fs(x,0,LN,.12);pl(x,[.5,0,.5,.3]);fs(x,0,LN,.11);pl(x,[.76,0,.76,.24]);fs(x,0,LN,.11)};
SP.chart=(x,a,t,A)=>{pl(x,[-.82,-.82,-.82,.8,.88,.8]);fs(x,0,LN,.055);[.35,.55,.75,1].forEach((h,i)=>{rr(x,-.62+i*.36,.74-h*1.3,.24,h*1.3,.02);fs(x,i==3?A:P3,LN,.03)})};
SP.chart_down=(x,a,t,A)=>{pl(x,[-.82,-.82,-.82,.8,.88,.8]);fs(x,0,LN,.055);[1,.75,.52,.3].forEach((h,i)=>{rr(x,-.62+i*.36,.74-h*1.3,.24,h*1.3,.02);fs(x,i==3?A:P3,LN,.03)})};
SP.growth=(x,a,t,A)=>{pl(x,[-.82,-.82,-.82,.8,.88,.8]);fs(x,0,LN,.055);pl(x,[-.64,.5,-.24,.12,.06,.34,.66,-.5]);fs(x,0,A,.1);pl(x,[.38,-.52,.68,-.54,.66,-.24]);fs(x,0,A,.1)};
SP.box=(x,a,t,A)=>{pl(x,[-.76,-.3,-.5,-.68,.5,-.68,.76,-.3],1);fs(x,P3,LN);rr(x,-.76,-.3,1.52,1.08,.02);fs(x,P2,LN);pl(x,[-.08,-.68,.08,-.68,.12,-.3,-.12,-.3],1);fs(x,A);x.beginPath();x.rect(-.12,-.3,.24,.38);fs(x,A)};
SP.bag=(x,a,t,A)=>{x.beginPath();x.arc(0,-.3,.3,PI,0);fs(x,0,LN,.08);pl(x,[-.6,-.3,.6,-.3,.74,.84,-.74,.84],1);fs(x,P2,LN);ci(x,0,.3,.17);fs(x,A)};
SP.truck=(x,a,t,A)=>{rr(x,-.96,-.52,1.2,.92,.04);fs(x,P2,LN);pl(x,[.24,-.2,.62,-.2,.94,.1,.94,.4,.24,.4],1);fs(x,A,LN);pl(x,[.36,-.1,.58,-.1,.76,.08,.36,.08],1);fs(x,P0);
[-.56,.56].forEach(c=>{ci(x,c,.5,.21);fs(x,P0,LN);ci(x,c,.5,.07);fs(x,LN)})};
SP.plane=(x,a,t,A)=>{pl(x,[-.8,-.14,-.96,-.64,-.68,-.64,-.44,-.16],1);fs(x,A,LN,.04);x.beginPath();x.moveTo(-.86,0);x.quadraticCurveTo(-.86,-.17,-.6,-.17);x.lineTo(.5,-.17);x.quadraticCurveTo(.94,-.1,.96,.04);x.quadraticCurveTo(.9,.17,.5,.17);x.lineTo(-.6,.17);x.quadraticCurveTo(-.86,.17,-.86,0);fs(x,P2,LN);
pl(x,[-.04,.04,-.46,.66,-.2,.66,.32,.04],1);fs(x,P3,LN,.04);for(let i=0;i<5;i++){ci(x,-.28+i*.17,-.05,.035);fs(x,LN)}};
SP.ship=(x,a,t,A)=>{rr(x,.5,-.66,.28,.66,.02);fs(x,P1,LN,.04);for(let i=0;i<2;i++){rr(x,-.44+i*.36,-.62,.32,.3,.01);fs(x,i?A:P3,LN,.03)}for(let i=0;i<3;i++){rr(x,-.62+i*.36,-.32,.32,.3,.01);fs(x,i==1?P3:A,LN,.03)}
pl(x,[-.96,0,.96,0,.74,.46,-.8,.46],1);fs(x,P2,LN);x.beginPath();for(let i=0;i<=24;i++){const u=-.96+i*.08,y=.64+.045*Math.sin(u*9+t*2);i?x.lineTo(u,y):x.moveTo(u,y)}fs(x,0,rgba(LN,.6),.05)};
SP.globe=(x,a,t,A)=>{ci(x,0,0,.8);fs(x,P1,LN);x.save();ci(x,0,0,.8);x.clip();for(let i=0;i<4;i++){const ph=(t*.25+i*PI/4)%PI;x.beginPath();x.ellipse(0,0,Math.abs(Math.cos(ph))*.8,.8,0,0,TAU);fs(x,0,'rgba(255,255,255,.4)',.03)}
[-.42,0,.42].forEach(y=>{pl(x,[-.8,y,.8,y]);fs(x,0,'rgba(255,255,255,.4)',.03)});x.restore();ci(x,.2,-.22,.1);fs(x,A)};
SP.check=(x,a,t,A)=>{ci(x,0,0,.72);fs(x,rgba(A,.2),A,.09);pl(x,[-.32,.02,-.08,.28,.36,-.24]);fs(x,0,'#ffffff',.15)};
SP.cross=(x,a,t,A)=>{ci(x,0,0,.72);fs(x,P1,LN,.09);pl(x,[-.28,-.28,.28,.28]);fs(x,0,LN,.15);pl(x,[.28,-.28,-.28,.28]);fs(x,0,LN,.15)};
SP.clock=(x,a,t,A)=>{ci(x,0,0,.8);fs(x,P1,LN);for(let i=0;i<12;i++){const g=i*TAU/12;pl(x,[Math.sin(g)*.64,-Math.cos(g)*.64,Math.sin(g)*.72,-Math.cos(g)*.72]);fs(x,0,rgba(LN,i%3?.45:1),.05)}
const m=t*.9,h=1+m/12;pl(x,[0,0,Math.sin(h)*.36,-Math.cos(h)*.36]);fs(x,0,LN,.09);pl(x,[0,0,Math.sin(m)*.56,-Math.cos(m)*.56]);fs(x,0,A,.07);ci(x,0,0,.07);fs(x,A)};
SP.bulb=(x,a,t,A)=>{ci(x,0,-.2,.78);fs(x,rgba(A,.1+.2*a));x.beginPath();x.arc(0,-.2,.52,PI*.75,PI*.25);x.lineTo(.2,.44);x.lineTo(-.2,.44);x.closePath();fs(x,mix(P2,A,.3+.5*a),LN);rr(x,-.2,.48,.4,.28,.05);fs(x,P3,LN,.04);pl(x,[-.15,-.04,-.06,-.26,.06,-.04,.15,-.26]);fs(x,0,'#ffffff',.05)};
SP.chip=(x,a,t,A)=>{for(let i=0;i<4;i++){const u=-.39+i*.26;pl(x,[u,-.84,u,-.58]);fs(x,0,LN,.07);pl(x,[u,.58,u,.84]);fs(x,0,LN,.07);pl(x,[-.84,u,-.58,u]);fs(x,0,LN,.07);pl(x,[.58,u,.84,u]);fs(x,0,LN,.07)}
rr(x,-.6,-.6,1.2,1.2,.08);fs(x,P2,LN);rr(x,-.3,-.3,.6,.6,.04);fs(x,lit(A,.3+.7*a),LN,.035)};
SP.warehouse=(x,a,t,A)=>{pl(x,[-.98,-.26,0,-.62,.98,-.26],1);fs(x,P1,LN);rr(x,-.9,-.26,1.8,1.08,.02);fs(x,P2,LN);rr(x,-.9,-.26,1.8,.12,0);fs(x,A);
[-.66,.1].forEach(l=>{rr(x,l,.08,.56,.74,.02);fs(x,P1,LN,.035);for(let i=1;i<5;i++){pl(x,[l+.04,.08+i*.148,l+.52,.08+i*.148]);fs(x,0,'rgba(255,255,255,.3)',.025)}})};
SP.container=(x,a,t,A)=>{rr(x,-.94,-.44,1.88,.88,.03);fs(x,mix(A,'#000000',.3),LN);for(let i=1;i<10;i++){pl(x,[-.94+i*.188,-.36,-.94+i*.188,.36]);fs(x,0,'rgba(0,0,0,.35)',.04)}rr(x,.44,-.3,.36,.6,.02);fs(x,0,LN,.03)};
SP.drop=(x,a,t,A)=>{x.beginPath();x.moveTo(0,-.86);x.bezierCurveTo(.2,-.42,.58,-.06,.58,.3);x.arc(0,.3,.58,0,PI);x.bezierCurveTo(-.58,-.06,-.2,-.42,0,-.86);x.closePath();fs(x,'#7d8896',LN);x.beginPath();x.arc(0,.3,.36,.25,1.25);fs(x,0,'#ffffff',.07)};
SP.bolt=(x,a,t,A)=>{pl(x,[.16,-.9,-.5,.1,-.06,.1,-.2,.9,.52,-.2,.08,-.2],1);fs(x,A,LN)};
const flm=x=>{x.beginPath();x.moveTo(0,-.88);x.bezierCurveTo(.1,-.4,.6,-.1,.56,.34);x.bezierCurveTo(.54,.7,.26,.88,0,.88);x.bezierCurveTo(-.26,.88,-.54,.7,-.56,.34);x.bezierCurveTo(-.58,0,-.3,-.2,-.28,-.42);x.bezierCurveTo(-.1,-.3,-.06,-.6,0,-.88);x.closePath()};
SP.flame=(x,a,t,A)=>{flm(x);fs(x,A,LN);at(x,0,.36,.5,()=>{flm(x);fs(x,mix(A,'#ffffff',.65))})};
SP.snow=(x,a,t,A)=>{for(let i=0;i<6;i++){x.save();x.rotate(i*PI/3);pl(x,[0,0,0,-.82]);fs(x,0,LN,.08);pl(x,[-.2,-.66,0,-.46,.2,-.66]);fs(x,0,LN,.07);x.restore()}ci(x,0,0,.1);fs(x,A)};
SP.leaf=(x,a,t,A)=>{x.beginPath();x.moveTo(-.7,.7);x.quadraticCurveTo(-.8,-.6,.7,-.74);x.quadraticCurveTo(.76,.7,-.7,.7);x.closePath();fs(x,P2,LN);pl(x,[-.7,.7,.4,-.44]);fs(x,0,A,.07)};
SP.car=(x,a,t,A)=>{pl(x,[-.94,.34,-.94,.02,-.6,-.04,-.34,-.44,.3,-.44,.6,-.04,.94,.06,.94,.34],1);fs(x,P2,LN);pl(x,[-.28,-.34,-.48,-.04,-.02,-.04,-.02,-.34],1);fs(x,lit(A,a));pl(x,[.08,-.34,.08,-.04,.48,-.04,.26,-.34],1);fs(x,lit(A,a));
rr(x,.82,.1,.12,.1,.02);fs(x,A);[-.52,.52].forEach(c=>{ci(x,c,.36,.21);fs(x,P0,LN);ci(x,c,.36,.07);fs(x,LN)})};
SP.tank=(x,a,t,A)=>{rr(x,-.6,-.74,1.2,1.52,.22);fs(x,P1);x.save();rr(x,-.6,-.74,1.2,1.52,.22);x.clip();x.beginPath();x.rect(-.6,-.04,1.2,1);fs(x,'#7d8896');x.restore();rr(x,-.6,-.74,1.2,1.52,.22);fs(x,0,LN);pl(x,[-.6,-.04,.6,-.04]);fs(x,0,'#ffffff',.04);
for(let i=0;i<3;i++){pl(x,[.3,-.44+i*.4,.5,-.44+i*.4]);fs(x,0,LN,.04)}rr(x,-.16,-.9,.32,.18,.03);fs(x,P3,LN,.04)};
SP.pump=(x,a,t,A)=>{rr(x,-.96,-.1,.5,.3,.02);fs(x,P1,LN,.04);rr(x,.14,-.9,.3,.5,.02);fs(x,P1,LN,.04);ci(x,0,.06,.58);fs(x,P2,LN);x.save();x.translate(0,.06);x.rotate(t*2.4);for(let i=0;i<4;i++){x.rotate(PI/2);x.beginPath();x.moveTo(.08,0);x.quadraticCurveTo(.3,-.22,.44,.06);fs(x,0,A,.08)}x.restore();ci(x,0,.06,.1);fs(x,LN);pl(x,[-.5,.8,.5,.8]);fs(x,0,LN,.07);pl(x,[0,.64,0,.8]);fs(x,0,LN,.07)};
SP.battery=(x,a,t,A)=>{rr(x,-.84,-.44,1.54,.88,.08);fs(x,P1,LN);rr(x,.7,-.17,.14,.34,.03);fs(x,LN);for(let i=0;i<3;i++){rr(x,-.72+i*.44,-.3,.36,.6,.03);fs(x,i<2?A:P3)}};
SP.card=(x,a,t,A)=>{rr(x,-.92,-.58,1.84,1.16,.1);fs(x,P2,LN);x.beginPath();x.rect(-.92,-.36,1.84,.22);fs(x,P0);rr(x,-.68,.04,.36,.28,.05);fs(x,A);pl(x,[-.1,.34,.66,.34]);fs(x,0,'rgba(255,255,255,.5)',.06)};
SP.air=(x,a,t,A)=>{x.save();x.setLineDash([.34,.16]);x.lineDashOffset=-t*.7;[-.44,0,.44].forEach((y,i)=>{x.beginPath();for(let j=0;j<=20;j++){const u=-.86+j*.086,v=y+.1*Math.sin(u*5+i*1.7);j?x.lineTo(u,v):x.moveTo(u,v)}fs(x,0,i==1?A:LN,.08)});x.restore()};
SP.camera=(x,a,t,A)=>{rr(x,-.3,-.68,.6,.3,.05);fs(x,P1,LN);rr(x,-.88,-.46,1.76,1.14,.1);fs(x,P2,LN);ci(x,0,.1,.38);fs(x,P0,LN);ci(x,0,.1,.21);fs(x,lit(A,.3+.7*a));ci(x,.62,-.24,.07);fs(x,A)};
SP.pin=(x,a,t,A)=>{x.beginPath();x.moveTo(0,.9);x.bezierCurveTo(-.2,.4,-.6,.1,-.6,-.3);x.arc(0,-.3,.6,PI,0);x.bezierCurveTo(.6,.1,.2,.4,0,.9);x.closePath();fs(x,A,LN);ci(x,0,-.3,.22);fs(x,P0)};
SP.search=(x,a,t,A)=>{pl(x,[.24,.24,.78,.78]);fs(x,0,LN,.17);ci(x,-.14,-.14,.52);fs(x,'rgba(255,255,255,.07)',LN,.1);x.beginPath();x.arc(-.14,-.14,.32,PI*1.05,PI*1.5);fs(x,0,A,.07)};
SP.tree=(x,a,t,A)=>{rr(x,-.1,.26,.2,.6,.03);fs(x,P3,LN,.04);ci(x,0,-.2,.6);fs(x,P2,LN);pl(x,[0,.3,0,-.3]);fs(x,0,A,.06);pl(x,[0,-.02,.26,-.28]);fs(x,0,A,.06);pl(x,[0,.12,-.26,-.14]);fs(x,0,A,.06)};
SP.robot=(x,a,t,A)=>{pl(x,[0,-.52,0,-.78]);fs(x,0,LN,.06);ci(x,0,-.84,.07);fs(x,A);rr(x,-.42,.46,.84,.38,.08);fs(x,P1,LN);rr(x,-.58,-.52,1.16,.92,.14);fs(x,P2,LN);[-.24,.24].forEach(c=>{ci(x,c,-.12,.12);fs(x,mix(P0,A,.5+.5*a))});pl(x,[-.2,.2,.2,.2]);fs(x,0,LN,.06)};
SP.satellite=(x,a,t,A)=>{x.save();x.rotate(-.5);for(let i=0;i<3;i++){const u=(t*.5+i/3)%1;x.beginPath();x.arc(0,.5,.2+u*.5,PI*.2,PI*.8);x.strokeStyle=rgba(A,(1-u)*.9);x.lineWidth=.06;x.stroke()}
[-.96,.3].forEach(l=>{rr(x,l,-.22,.66,.44,.02);fs(x,mix(P0,A,.35),LN,.035);pl(x,[l+.22,-.22,l+.22,.22]);fs(x,0,LN,.025);pl(x,[l+.44,-.22,l+.44,.22]);fs(x,0,LN,.025)});rr(x,-.22,-.32,.44,.64,.05);fs(x,P2,LN);x.beginPath();x.arc(0,.5,.2,PI,0);x.closePath();fs(x,P3,LN,.04);x.restore()};
SP.gear=(x,a,t,A)=>{x.beginPath();for(let i=0;i<8;i++){const g=i*PI/4;[[-.14,.62],[-.09,.84],[.09,.84],[.14,.62]].forEach((q,j)=>{const an=g+q[0]*1.6,X=Math.cos(an)*q[1],Y=Math.sin(an)*q[1];i||j?x.lineTo(X,Y):x.moveTo(X,Y)})}x.closePath();fs(x,P2,LN);ci(x,0,0,.26);fs(x,P0,A,.06)};
SP.eye=(x,a,t,A)=>{x.beginPath();x.moveTo(-.92,0);x.quadraticCurveTo(0,-.76,.92,0);x.quadraticCurveTo(0,.76,-.92,0);x.closePath();fs(x,P1,LN);ci(x,0,0,.32);fs(x,A);ci(x,0,0,.14);fs(x,P0)};
SP.sun=(x,a,t,A)=>{for(let i=0;i<8;i++){const g=i*PI/4;pl(x,[Math.cos(g)*.56,Math.sin(g)*.56,Math.cos(g)*.84,Math.sin(g)*.84]);fs(x,0,A,.09)}ci(x,0,0,.4);fs(x,A,LN)};
SP.plug=(x,a,t,A)=>{rr(x,-.24,-.88,.12,.4,.03);fs(x,LN);rr(x,.12,-.88,.12,.4,.03);fs(x,LN);rr(x,-.46,-.52,.92,.64,.12);fs(x,P1,LN);ci(x,0,-.2,.13);fs(x,lit(A,a));x.beginPath();x.moveTo(0,.12);x.bezierCurveTo(0,.62,.52,.4,.52,.9);fs(x,0,LN,.09)};
SP.tool=(x,a,t,A)=>{x.save();x.rotate(-PI/4);rr(x,-.11,-.3,.22,1.18,.1);fs(x,P1,LN);x.beginPath();x.arc(0,-.52,.34,PI*1.72,PI*1.28);x.lineTo(-.13,-.5);x.lineTo(.13,-.5);x.closePath();fs(x,A,LN);x.restore()};
SP.touch=(x,a,t,A)=>{const q=(t*.7)%1;x.save();x.globalAlpha*=1-q;ci(x,-.1,-.5,.16+q*.42);fs(x,0,A,.07);x.restore();rr(x,-.24,-.56,.28,1,.14);fs(x,P1,LN);rr(x,-.24,0,.8,.86,.2);fs(x,P1,LN);ci(x,-.1,-.5,.07);fs(x,A)};
SP.flag=(x,a,t,A)=>{pl(x,[-.52,-.88,-.52,.88]);fs(x,0,LN,.09);x.beginPath();x.moveTo(-.52,-.78);x.quadraticCurveTo(-.1,-.98,.2,-.72);x.quadraticCurveTo(.5,-.5,.78,-.7);x.lineTo(.78,-.08);x.quadraticCurveTo(.5,.12,.2,-.1);x.quadraticCurveTo(-.1,-.36,-.52,-.16);x.closePath();fs(x,A,LN)};
// ikona, ku ktorej nie je kresba: tá istá čiarová ikona na tabuľke (len ako doplnok k nakresleným účastníkom)
const IC={},ico=n=>{if(IC[n])return IC[n];const out=[];try{const src=(typeof ICONS!='undefined'&&ICONS[typeof IR=='function'?IR(n):n])||'';const at=(s,k)=>{const m=new RegExp('\\b'+k+'="([^"]*)"').exec(s);return m?m[1]:''};
src.replace(/<(path|rect|circle)\b([^>]*)>/g,(q,tg,s)=>{const p=new Path2D();if(tg=='path')out.push(new Path2D(at(s,'d')));else if(tg=='rect'){p.roundRect(N(at(s,'x')),N(at(s,'y')),N(at(s,'width')),N(at(s,'height')),N(at(s,'rx')));out.push(p)}else{p.arc(N(at(s,'cx')),N(at(s,'cy')),N(at(s,'r')),0,TAU);out.push(p)}return q})}catch(e){}return IC[n]=out};
const plate=(x,n,A)=>{rr(x,-.8,-.8,1.6,1.6,.22);fs(x,P1,LN);x.save();x.translate(-.56,-.56);x.scale(.0112,.0112);x.strokeStyle=A;x.lineWidth=5.2;x.lineCap='round';x.lineJoin='round';ico(n).forEach(p=>x.stroke(p));x.restore()};
K.SPR=SP;

// ---------- to, čo putuje po šípke ----------
const TOK={
coin:(x,A)=>{ci(x,0,0,11);fs(x,A,'#ffffff',2);ci(x,0,0,6);fs(x,0,'rgba(0,0,0,.4)',2)},
data:(x,A)=>{rr(x,-8,-8,16,16,3);fs(x,'#ffffff');rr(x,-3.5,-3.5,7,7,1.5);fs(x,A)},
box:(x,A)=>{rr(x,-10,-9,20,18,2);fs(x,P3,LN,2);x.beginPath();x.rect(-2.5,-9,5,18);fs(x,A)},
person:(x,A)=>{ci(x,0,-6,5);fs(x,'#ffffff');x.beginPath();x.arc(0,9,9,PI,0);x.closePath();fs(x,'#ffffff')},
doc:(x,A)=>{rr(x,-7.5,-10,15,20,2);fs(x,'#ffffff');pl(x,[-4,-4,4,-4]);fs(x,0,A,2.4);pl(x,[-4,1,4,1]);fs(x,0,'rgba(0,0,0,.45)',2.4);pl(x,[-4,6,1,6]);fs(x,0,'rgba(0,0,0,.45)',2.4)},
drop:(x,A)=>{x.beginPath();x.moveTo(0,-12);x.bezierCurveTo(3,-6,8,-1,8,4);x.arc(0,4,8,0,PI);x.bezierCurveTo(-8,-1,-3,-6,0,-12);x.closePath();fs(x,'#cfd8e3','#ffffff',1.5)},
dot:(x,A)=>{ci(x,0,0,13);fs(x,rgba(A,.25));ci(x,0,0,7);fs(x,A)}};

// text sa zmestí do šírky: menšie písmo, pri dlhšom názve dva riadky
const fit=(x,S,s,maxW,f0)=>{const W=q=>{x.font=`800 ${f0}px ${S.FT}`;return x.measureText(q).width};let L=[s];if(W(s)>maxW&&/\s/.test(s)){const w=s.split(/\s+/);let best=1,bd=1e9;for(let i=1;i<w.length;i++){const d=Math.abs(W(w.slice(0,i).join(' '))-W(w.slice(i).join(' ')));if(d<bd){bd=d;best=i}}L=[w.slice(0,best).join(' '),w.slice(best).join(' ')]}
const mw=Math.max(...L.map(W));return [L,Math.max(15,Math.min(f0,f0*maxW/mw))]};
const label=(S,s,px,py,maxW,f0,col,up)=>{if(!s)return;const x=S.x,[L,f]=fit(x,S,s,maxW,f0),lh=f*1.14,y0=up?py-(L.length-1)*lh:py;x.font=`800 ${f}px ${S.FT}`;
const wi=L.reduce((b,q,i)=>x.measureText(q).width>x.measureText(L[b]).width?i:b,0),n0=S.tags.length,a=K.tagA(S,L[wi],px,y0,'center',f);
if(S.tags.length>n0&&L.length>1)S.tags[n0][3]+=(L.length-1)*lh*x.getTransform().d/S.R;   // miesto zaberajú oba riadky
if(a<=.02)return;x.save();x.globalAlpha*=a;x.textAlign='center';x.textBaseline='middle';x.lineJoin='round';x.strokeStyle='rgba(0,0,0,.8)';x.lineWidth=7;x.fillStyle=col;L.forEach((q,i)=>{x.strokeText(q,px,y0+i*lh);x.fillText(q,px,y0+i*lh)});x.restore()};

PRO.actors=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,DUR=N(d._dur)||9;
const ND=(Array.isArray(d.nd)?d.nd:[]).filter(q=>Array.isArray(q)).slice(0,4).map(q=>[String(q[0]||''),String(q[1]||'').toUpperCase()]),n=ND.length;
const ED=(Array.isArray(d.ed)?d.ed:[]).filter(e=>Array.isArray(e)&&e[0]!=e[1]&&e[0]>=0&&e[1]>=0&&e[0]<n&&e[1]<n).slice(0,4).map(e=>({a:e[0]|0,b:e[1]|0,l:String(e[2]||'').toUpperCase(),hl:!!e[3],k:TOK[e[4]]?e[4]:'dot',stop:!!e[5]})),nE=ED.length;
const chain=n<3||(n==3&&ED.every(e=>Math.abs(e.a-e.b)==1));let P,R,up=[];
if(chain){R=n<=2?130:100;const gap=n<=2?430:300;P=ND.map((q,i)=>[450+(i-(n-1)/2)*gap,300])}
else if(n==3){R=82;const deg=[0,0,0];ED.forEach(e=>{deg[e.a]++;deg[e.b]++});const h=deg.indexOf(Math.max(...deg)),o=[0,1,2].filter(i=>i!=h);P=[];P[h]=[450,166];P[o[0]]=[196,414];P[o[1]]=[704,414];up[h]=1}
else{R=74;P=[[214,158],[686,158],[686,426],[214,426]];up=[1,1,0,0]}
const TS=n<=3?1.35:1.1;
// šípky: v rade oblúk ponad (späť popod), inak rovná spojnica; [začiatok, riadiaci bod, koniec, miesto názvu, názov nad/pod]
const seen={};ED.forEach(e=>{const a=P[e.a],b=P[e.b],key=Math.min(e.a,e.b)+'_'+Math.max(e.a,e.b),second=seen[key];seen[key]=1;
if(chain){const s=second?1:-1,dir=b[0]>a[0]?1:-1,y=300+s*R*.55,mx=(a[0]+b[0])/2;e.p=[[a[0]+dir*R*.78,y],[mx,y+s*72],[b[0]-dir*R*.78,y]];e.lp=[mx,second?300+R+88:y-36-22];e.up=!second;e.mw=Math.abs(b[0]-a[0])-26}
else{const dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy),ux=dx/L,uy=dy/L;let nx=-uy,ny=ux;const mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2;if((mx-450)*nx+(my-300)*ny<0){nx=-nx;ny=-ny}if(Math.hypot(mx-450,my-300)<30&&ny>0){nx=-nx;ny=-ny}
const o=second?-13:0,p0=[a[0]+ux*R*1.12+nx*o,a[1]+uy*R*1.12+ny*o],p1=[b[0]-ux*R*1.18+nx*o,b[1]-uy*R*1.18+ny*o];e.p=[p0,[(p0[0]+p1[0])/2,(p0[1]+p1[1])/2],p1];e.nx=second?-nx:nx;e.ny=second?-ny:ny;e.lp=[mx,my];e.mw=200;e.free=1}});
const seg=nE?Math.max(1.3,Math.min(4.2,(DUR-1.1)/nE)):0;ED.forEach((e,i)=>{e.t0=.95+i*seg;e.per=e.k=='dot'?.6:.72;e.tr=1.25});
const anyHl=ED.some(e=>e.hl),bz=(p,u)=>{const w=1-u;return [w*w*p[0][0]+2*w*u*p[1][0]+u*u*p[2][0],w*w*p[0][1]+2*w*u*p[1][1]+u*u*p[2][1]]};
const zf=Math.min(S.w/900,S.h/600)*.98;
return (t,st)=>{const p=E(st(0,1));S.begin();x.globalAlpha=p;x.save();x.translate(S.w/2,S.h/2);x.scale(zf,zf);x.translate(-450,-300);
const act=ND.map(()=>0),ring=ND.map(()=>-1),cur=nE?Math.max(0,Math.min(nE-1,Math.floor((t-.95)/seg))):-1;
if(!nE){const k=Math.floor(Math.max(0,t-.8)/Math.max(1.2,(DUR-.8)/n))%n;act[k]=sm((t-.8)/.5)}
// šípky a to, čo po nich ide
ED.forEach((e,i)=>{const k=t-e.t0;if(k<=0)return;const g=ez(k/.5),on=anyHl?e.hl:i==cur,col=on?A:'#aeb6c2',end=e.stop?.56:1;
x.save();x.globalAlpha=p*(on?1:.75);x.strokeStyle=col;x.lineWidth=on?4.5:3;x.lineCap='round';x.setLineDash(e.stop?[3,11]:[]);x.beginPath();const M=26;for(let j=0;j<=M;j++){const q=bz(e.p,j/M*g*(e.stop?1:.985));j?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.stroke();x.setLineDash([]);
if(g>.98){const q=e.p[2],c=bz(e.p,.9),an=Math.atan2(q[1]-c[1],q[0]-c[0]);if(!e.stop){x.beginPath();x.moveTo(q[0]-Math.cos(an-.45)*17,q[1]-Math.sin(an-.45)*17);x.lineTo(q[0],q[1]);x.lineTo(q[0]-Math.cos(an+.45)*17,q[1]-Math.sin(an+.45)*17);x.stroke()}
else{const w=bz(e.p,.62),c2=bz(e.p,.56),a2=Math.atan2(w[1]-c2[1],w[0]-c2[0])+PI/2;x.strokeStyle=LN;x.lineWidth=6;x.beginPath();x.moveTo(w[0]-Math.cos(a2)*20,w[1]-Math.sin(a2)*20);x.lineTo(w[0]+Math.cos(a2)*20,w[1]+Math.sin(a2)*20);x.stroke()}}
x.restore();
// žetóny: kým je šípka na rade, idú husto; potom tok pokračuje redšie
const k2=k-.45;if(k2>0){const dense=i==cur?1:2.4,per=e.per*dense,m1=Math.floor(k2/per);for(let m=m1;m>=0&&m>m1-6;m--){const u=(k2-m*per)/e.tr;if(u<0||u>1.25)continue;
if(u>=1){if(!e.stop){ring[e.b]=Math.max(ring[e.b],1-(u-1)/.25*1);act[e.b]=Math.max(act[e.b],1-(u-1)/.25)}continue}
const uu=sm(u)*end,q=bz(e.p,uu),fade=e.stop?1-sm((u-.7)/.3):Math.min(1,(1-u)/.08),al=Math.min(1,u/.1)*fade*(i==cur?1:.8);x.save();x.globalAlpha=p*al;x.translate(q[0],q[1]);x.scale(TS,TS);TOK[e.k](x,A);x.restore();
if(!e.stop&&u>.9)act[e.b]=Math.max(act[e.b],(u-.9)/.1)}
act[e.a]=Math.max(act[e.a],i==cur?.45:.15)}});
// účastníci
ND.forEach((q,i)=>{const k=ez((t-.12-i*.16)/.42);if(k<=.01)return;const c=P[i],s=R*(.72+.28*k);
if(ring[i]>0){x.save();x.globalAlpha=p*ring[i]*.8;x.strokeStyle=A;x.lineWidth=4;x.beginPath();x.arc(c[0],c[1],R*(1.12+.22*(1-ring[i])),0,TAU);x.stroke();x.restore()}
x.save();x.globalAlpha=p*k;x.translate(c[0],c[1]);x.scale(s,s);x.lineCap='round';x.lineJoin='round';(SP[q[0]]?SP[q[0]](x,act[i],t,A):plate(x,q[0].replace(/^ico:/,''),A));x.restore();
x.globalAlpha=p*k;label(S,q[1],c[0],up[i]?c[1]-R-22:c[1]+R+(chain?30:28),chain?(n<=2?330:220):236,n<=3?26:22,'#e9ecef',!!up[i])});
// názvy šípok
ED.forEach((e,i)=>{const k=ez((t-e.t0-.2)/.4);if(k<=.01||!e.l)return;const on=anyHl?e.hl:i==cur;x.globalAlpha=p*k;
if(e.free){const [L,f]=fit(x,S,e.l,e.mw,21);x.font=`800 ${f}px ${S.FT}`;const w=Math.max(...L.map(q=>x.measureText(q).width)),h=L.length*f*1.12,off=16+Math.abs(e.nx)*w/2+Math.abs(e.ny)*h/2;label(S,e.l,e.lp[0]+e.nx*off,e.lp[1]+e.ny*off-(L.length-1)*f*.56,e.mw,21,on?A:'#c9d0d9')}
else label(S,e.l,e.lp[0],e.lp[1],e.mw,24,on?A:'#c9d0d9',e.up)});
x.restore();x.globalAlpha=p;callout(S,d,t,A);x.globalAlpha=1}};
}
