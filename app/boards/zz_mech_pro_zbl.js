// Presné modely 44–54 – strechový rez, čip na karte, robotický vysávač, pretekárske auto, atóm, hrádza, mikrovlnka, čerpadlo, kotol, umývačka, koľajnica.
{
const K=window.KIT,PRO=K.PRO,{ez,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead}=K;
const N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.roofcut=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={tiles:[450,170,zf*1.8],insulation:[450,330,zf*1.8],barrier:[300,400,zf*2.2]};
const ORD=['tiles','insulation','barrier'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.fillRect(120,380,660,40);
x.fillStyle="#7b848d";for(let k=0;k<6;k++)x.fillRect(180+k*100,340,14,40);
x.fillStyle="#d7dde3";x.beginPath();x.moveTo(120,320);x.lineTo(450,120);x.lineTo(780,320);x.closePath();x.fill();
x.strokeStyle="#9aa3ab";x.lineWidth=3;x.stroke();
x.globalAlpha=p*sp;x.fillStyle="#c9542b";for(let r=0;r<5;r++)for(let c=0;c<8;c++){const ox=(r%2)*26;x.fillRect(190+c*52+ox-r*0,300-r*30+(r*0),40,20)}
x.globalAlpha=p;x.fillStyle="#8b5a3c";x.fillRect(150,314,600,8);
x.fillStyle="#e8ecef";x.fillRect(200,300,500,14);
x.fillStyle="#f2d9a6";x.fillRect(200,345,500,22);
x.fillStyle="#b9c2ca";x.fillRect(200,366,500,12);
const drip=(t*60)%260;for(let k=0;k<6;k++){const dx=200+k*90+((drip*.6)%90);x.beginPath();x.arc(dx,160+(k*37+drip)%150,3,0,Math.PI*2);x.fillStyle="rgba(120,190,255,.8)";x.fill()}
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0]||"",120,80,300,180);lead(S,LN[1]||"",780,330,700,355);lead(S,LN[2]||"",120,400,240,380);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"3 layers","ROOF",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.cardchip=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={chip:[330,260,zf*2.2],terminal:[640,340,zf*1.8],data:[480,300,zf*1.6]};
const ORD=['chip','terminal','data'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const ins=cl((t-.2)/.5),pulse=.5+.5*Math.sin(t*6);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.fillRect(640,220,180,260);x.fillStyle="#12171c";x.fillRect(660,240,140,60);x.fillStyle="#3b7fc4";x.fillRect(680,262,100,14);
x.fillStyle="#1f5fa8";x.fillRect(680,420,100,24);
x.fillStyle="#c9d0d6";x.fillRect(160+(1-ins)*-300,180,420,250);x.fillStyle="#9aa3ab";x.fillRect(160+(1-ins)*-300,400,420,30);
x.fillStyle="#d4a72c";x.fillRect(200+(1-ins)*-300,240,90,70);x.strokeStyle="#8a6d1a";x.lineWidth=3;x.strokeRect(200+(1-ins)*-300,240,90,70);
x.beginPath();x.moveTo(200+(1-ins)*-300,275);x.lineTo(290+(1-ins)*-300,275);x.moveTo(245+(1-ins)*-300,240);x.lineTo(245+(1-ins)*-300,310);x.stroke();
x.globalAlpha=p*ins*sp;for(let k=0;k<5;k++){const bx=490+((t*180+k*60)%240);x.beginPath();x.arc(bx,300+(k%2)*26,5,0,Math.PI*2);x.fillStyle=`rgba(255,107,0,${.4+.6*pulse})`;x.fill()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,240,250);lead(S,LN[1]||"",780,200,720,265);lead(S,LN[2]||"",400,100,480,290);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"1 chip","CARD",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.robovac=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={lidar:[450,200,zf*2.2],brushes:[450,380,zf*2.0],wheels:[450,420,zf*2.0]};
const ORD=['lidar','brushes','wheels'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const bx=450+200*Math.sin(t*.7),by=300+120*Math.sin(t*1.3),rot=t*5;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.beginPath();x.arc(450,300,2*0+0+1,0,1);
x.strokeStyle="rgba(255,107,0,.35)";x.lineWidth=40;x.beginPath();x.moveTo(230,150);x.lineTo(670,450);x.stroke();
for(let k=0;k<14;k++){x.beginPath();x.arc(260+k*30,160+k*20,4,0,Math.PI*2);x.fillStyle="rgba(200,200,200,.5)";x.fill()}
x.save();x.translate(bx,by);x.beginPath();x.arc(0,0,130,0,Math.PI*2);x.fillStyle="#2a2f36";x.fill();x.strokeStyle="#5a636d";x.lineWidth=4;x.stroke();
x.beginPath();x.arc(0,0,52,0,Math.PI*2);x.fillStyle="#3b4048";x.fill();
x.beginPath();x.arc(0,0,22,0,Math.PI*2);x.fillStyle="#9aa3ab";x.fill();
x.save();x.rotate(rot);x.fillStyle="#1d2530";x.fillRect(-100,-8,200,16);x.restore();
x.fillStyle="#12171c";x.beginPath();x.arc(0,-36,14,0,Math.PI*2);x.fill();
x.save();x.rotate(rot*.5);x.beginPath();for(let k=0;k<4;k++){const aa=k*Math.PI/2;x.moveTo(0,0);x.lineTo(Math.cos(aa)*60,Math.sin(aa)*60)}x.strokeStyle="#c9d0d6";x.lineWidth=6;x.stroke();x.restore();
x.beginPath();x.arc(-90,20,30,0,Math.PI*2);x.fillStyle="#12171c";x.fill();x.beginPath();x.arc(90,20,30,0,Math.PI*2);x.fill();
x.beginPath();x.arc(0,-150,20,0,Math.PI*2);x.fillStyle="#5a636d";x.fill();
x.restore();
x.globalAlpha=p*sp*(1-zi);lead(S,LN[0]||"",120,80,450,by-150);lead(S,LN[1]||"",780,300,bx+60,by-30);lead(S,LN[2]||"",120,460,bx-90,by+50);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"LIDAR","MAP",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.racecar=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={wing:[660,200,zf*2.1],tyres:[300,380,zf*2.1],downforce:[450,330,zf*1.6]};
const ORD=['wing','tyres','downforce'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const rot=t*9;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#c9d0d6";x.fillRect(120,400,660,8);
x.fillStyle="#d9822b";x.beginPath();x.moveTo(230,360);x.lineTo(300,300);x.lineTo(560,300);x.lineTo(700,340);x.lineTo(700,380);x.lineTo(230,380);x.closePath();x.fill();
x.fillStyle="#1d2530";x.fillRect(300,310,120,36);x.fillRect(470,320,100,28);
x.fillStyle="#3b4048";x.fillRect(160,320,30,70);x.fillRect(120,330,90,8);x.fillRect(680,330,100,8);
x.fillStyle="#2a2f36";x.fillRect(120,238,70,6);x.fillRect(120,200,8,40);x.fillRect(180,200,8,40);
x.fillStyle="#e8ecef";x.fillRect(660,190,40,14);
for(const wx of [300,620]){x.beginPath();x.arc(wx,400-6,44,0,Math.PI*2);x.fillStyle="#12171c";x.fill();x.beginPath();x.arc(wx,394,20,0,Math.PI*2);x.fillStyle="#9aa3ab";x.fill();
x.save();x.translate(wx,394);x.rotate(rot);x.fillStyle="#3b4048";x.fillRect(-18,-3,36,6);x.restore()}
x.globalAlpha=p*sp*(1-zi);for(let k=0;k<4;k++){const ay=250+k*34;x.beginPath();x.moveTo(450,ay);x.lineTo(450,ay+30);x.strokeStyle="#FF6B00";x.lineWidth=4;x.stroke();x.beginPath();x.moveTo(440,ay+22);x.lineTo(450,ay+32);x.lineTo(460,ay+22);x.fillStyle="#FF6B00";x.fill()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,660,190);lead(S,LN[1]||"",780,470,300,420);lead(S,LN[2]||"",120,250,420,300);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"DOWNFORCE","AT SPEED",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.atom=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={nucleus:[450,300,zf*2.4],electrons:[450,300,zf*1.8],orbit:[450,300,zf*1.4]};
const ORD=['nucleus','electrons','orbit'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);
for(let k=0;k<3;k++){x.save();x.translate(450,300);x.rotate(k*Math.PI/3);x.beginPath();x.ellipse(0,0,230,80,0,0,Math.PI*2);x.strokeStyle="rgba(154,163,171,.6)";x.lineWidth=3;x.stroke();
const ea=t*(2.2-k*.4)+k*2;x.beginPath();x.arc(230*Math.cos(ea),80*Math.sin(ea),10,0,Math.PI*2);x.fillStyle="#3b7fc4";x.globalAlpha=p*sp*(1-zi);x.fill();x.globalAlpha=p;x.restore()}
for(let k=0;k<8;k++){const a1=k*Math.PI/4;x.beginPath();x.arc(450+Math.cos(a1)*22,300+Math.sin(a1)*16,13,0,Math.PI*2);x.fillStyle=k%2?"#c9d0d6":"#d9822b";x.fill()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,90,420,290);lead(S,LN[1]||"",780,150,640,250);lead(S,LN[2]||"",780,460,600,380);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"8 PROTONS","NUCLEUS",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.dike=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={dike:[430,300,zf*1.7],water:[200,300,zf*1.8],base:[450,460,zf*1.9]};
const ORD=['dike','water','base'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const lvl=270+6*Math.sin(t*1.4);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.fillRect(-100,470,1100,130);
x.fillStyle="#1f5fa8";x.fillRect(-100,lvl,300,300);
x.beginPath();x.moveTo(-100,lvl);x.lineTo(200,lvl);x.lineTo(600,380);x.lineTo(900,380);x.lineTo(900,470);x.lineTo(-100,470);x.closePath();x.fillStyle="#7b848d";x.fill();
x.beginPath();x.moveTo(200,lvl);x.lineTo(600,380);x.lineTo(900,380);x.lineTo(900,430);x.lineTo(600,430);x.lineTo(200,lvl+60);x.closePath();x.fillStyle="#5b636c";x.fill();
x.fillStyle="#c9d0d6";x.fillRect(560,372,340,10);
x.strokeStyle="#9aa3ab";x.lineWidth=2;for(let k=0;k<5;k++){x.beginPath();x.moveTo(200+k*60,lvl+20+k*10);x.lineTo(260+k*60,lvl+20+k*10);x.stroke()}
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(120,190,255,.8)";x.lineWidth=4;
for(let k=0;k<4;k++){const wx=40+k*40-((t*60)%40);x.beginPath();x.moveTo(wx,lvl-6+Math.sin((wx+t*80)/20)*4);x.lineTo(wx+30,lvl-6+Math.sin((wx+30+t*80)/20)*4);x.stroke()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,520,330);lead(S,LN[1]||"",120,400,150,lvl+20);lead(S,LN[2]||"",780,500,700,470);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"SEA","LEVEL",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.microwave=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={magnetron:[640,200,zf*2.2],waves:[450,300,zf*1.6],turntable:[450,380,zf*1.9]};
const ORD=['magnetron','waves','turntable'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const th=t*1.5;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#c9d0d6";x.fillRect(150,150,600,320);x.fillStyle="#12171c";x.fillRect(190,190,420,240);
x.fillStyle="#2a2f36";x.fillRect(630,190,90,240);x.fillStyle="#9aa3ab";x.fillRect(650,220,8,8);
x.beginPath();x.arc(450,310,130,0,Math.PI*2);x.fillStyle="#3b4048";x.fill();
x.save();x.translate(450,310);x.rotate(th);x.beginPath();x.arc(0,0,110,0,Math.PI*2);x.fillStyle="#e8ecef";x.fill();x.beginPath();x.arc(0,0,40,0,Math.PI*2);x.fillStyle="#d9822b";x.globalAlpha=p*sp*.8;x.fill();x.restore();x.globalAlpha=p;
x.fillStyle="#2a2f36";x.fillRect(200,130,160,30);x.beginPath();x.arc(640,190,16,0,Math.PI*2);x.fillStyle="#5a636d";x.fill();
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(255,107,0,.7)";x.lineWidth=3;for(let k=0;k<6;k++){x.beginPath();const yy=250+k*18+(t*40)%18;x.moveTo(200,yy);for(let s=0;s<=20;s++){x.lineTo(200+s*21,yy+Math.sin(s*1.2+t*6+k)*4)}x.stroke()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,80,640,200);lead(S,LN[1]||"",780,260,520,260);lead(S,LN[2]||"",120,460,400,400);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"2450 MHz","WAVES",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.pump=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={impeller:[450,300,zf*2.2],inlet:[180,300,zf*1.9],outlet:[720,300,zf*1.9]};
const ORD=['impeller','inlet','outlet'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const rot=t*4;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#9aa3ab";x.fillRect(60,285,140,30);x.fillRect(700,285,140,30);
x.fillStyle="#5a636d";x.beginPath();x.arc(450,300,150,0,Math.PI*2);x.fill();x.fillStyle="#3b7fc4";x.beginPath();x.arc(450,300,132,0,Math.PI*2);x.fill();
x.fillStyle="#2a5d93";x.beginPath();x.arc(450,300,120,0,Math.PI*2);x.fill();
x.save();x.translate(450,300);x.rotate(rot);for(let k=0;k<6;k++){x.rotate(Math.PI/3);x.beginPath();x.moveTo(20,0);x.lineTo(110,-22);x.lineTo(110,22);x.closePath();x.fillStyle="#dfe5ea";x.fill()}x.restore();
x.beginPath();x.arc(450,300,22,0,Math.PI*2);x.fillStyle="#12171c";x.fill();
x.globalAlpha=p*sp*(1-zi);for(let k=0;k<6;k++){const fx=120+((t*220+k*140)%620);x.beginPath();x.arc(fx,300+Math.sin(fx/40+k)*6,6,0,Math.PI*2);x.fillStyle="rgba(120,190,255,.9)";x.fill()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,90,450,180);lead(S,LN[1]||"",120,460,120,300);lead(S,LN[2]||"",780,460,760,300);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"RPM","PUMP",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.boiler=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={burner:[220,400,zf*2.1],exchanger:[300,260,zf*1.8],radiator:[690,240,zf*1.8]};
const ORD=['burner','exchanger','radiator'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const fl=.8+.2*Math.sin(t*14);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#5a636d";x.fillRect(160,140,220,300);x.fillStyle="#2a2f36";x.fillRect(180,160,180,240);
x.fillStyle="#d9822b";x.beginPath();x.moveTo(230,400);x.lineTo(260,330*fl+60);x.lineTo(290,400);x.closePath();x.globalAlpha=p*sp;x.fill();x.globalAlpha=p;
x.fillStyle="#9aa3ab";x.fillRect(200,400,140,20);
x.strokeStyle="#c9542b";x.lineWidth=18;x.beginPath();x.moveTo(380,260);x.lineTo(520,260);x.lineTo(520,160);x.lineTo(640,160);x.stroke();
x.fillStyle="#b9c2ca";for(let k=0;k<5;k++)x.fillRect(640+k*16,120,8,160);
x.fillStyle="#c9542b";x.fillRect(640,120,70,8);
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(120,190,255,.7)";x.lineWidth=3;for(let k=0;k<4;k++){x.beginPath();const xx=400+k*50+(t*120)%50;x.arc(xx,260+(k%2)*10,4,0,Math.PI*2);x.stroke()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,470,230,420);lead(S,LN[1]||"",120,100,240,200);lead(S,LN[2]||"",780,300,680,220);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"80 °C","WATER",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.dishwasher=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={spray:[450,300,zf*2.0],filter:[450,400,zf*2.0],heater:[450,130,zf*2.0]};
const ORD=['spray','filter','heater'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const rot=t*6;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#c9d0d6";x.fillRect(180,120,540,380);x.fillStyle="#12171c";x.fillRect(220,160,460,300);
x.fillStyle="#3b4048";x.fillRect(220,150,460,10);
x.save();x.translate(450,310);x.rotate(rot);x.fillStyle="#9aa3ab";x.fillRect(-180,-7,360,14);x.restore();
x.fillStyle="#5a636d";x.fillRect(430,380,40,22);
x.fillStyle="#d9822b";x.fillRect(260,130,380,8);
x.globalAlpha=p*sp*(1-zi);x.fillStyle="rgba(120,190,255,.8)";for(let k=0;k<12;k++){const ang=rot+k*Math.PI/6;const rr=60+((t*200+k*30)%170);x.beginPath();x.arc(450+Math.cos(ang)*rr,310+Math.sin(ang)*rr*.6,4,0,Math.PI*2);x.fill()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,90,450,260);lead(S,LN[1]||"",780,470,450,400);lead(S,LN[2]||"",780,110,450,130);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"12 PLACES","DISHES",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.railtrack=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={rail:[450,380,zf*2.2],sleeper:[450,450,zf*2.0],ballast:[300,500,zf*1.8]};
const ORD=['rail','sleeper','ballast'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const off=(t*90)%60;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#5b636c";x.fillRect(-200,380,1300,120);
x.fillStyle="#9aa3ab";for(let sx=-200-off;sx<1100;sx+=60)x.fillRect(sx,400,40,30);
x.fillStyle="#c9d0d6";x.fillRect(-200,360,1300,10);x.fillStyle="#9aa3ab";x.fillRect(-200,370,1300,12);x.fillStyle="#7b848d";x.fillRect(-200,382,1300,6);
x.fillStyle="#2a2f36";x.fillRect(680,220,10,140);x.beginPath();x.arc(685,215,26,0,Math.PI*2);x.fillStyle="#d9822b";x.globalAlpha=p*sp*(1-zi)+p*0.2;x.fill();x.globalAlpha=p;
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,450,360);lead(S,LN[1]||"",780,460,450,410);lead(S,LN[2]||"",120,470,300,470);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"1435 mm","GAUGE",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};
}
