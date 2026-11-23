// Presné modely 57–63 – sklad s robotmi, búrka a blesk, kombajn, servo s potenciometrom, Magnusov efekt, ťažba bitcoinu, vrstvy soli v oceáne.
{
const K=window.KIT,PRO=K.PRO,{ez,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead}=K;
const N=v=>{v=parseFloat(v);return isFinite(v)?v:0};
PRO.warehouse=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={robot:[300,300,zf*2.0],shelf:[560,260,zf*1.8],pads:[760,430,zf*2.0]};
const ORD=['robot','shelf','pads'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const ph=(t*.25)%1,rx=200+ph*380;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#1d2530";x.fillRect(60,120,780,380);x.strokeStyle="#3b4048";x.lineWidth=2;for(let gx=60;gx<=840;gx+=60){x.beginPath();x.moveTo(gx,120);x.lineTo(gx,500);x.stroke()}for(let gy=120;gy<=500;gy+=60){x.beginPath();x.moveTo(60,gy);x.lineTo(840,gy);x.stroke()}
for(let r=0;r<2;r++)for(let c=0;c<4;c++){const sx=150+c*170,sy=190+r*150;x.fillStyle="#5a636d";x.fillRect(sx,sy,110,80);x.strokeStyle="#9aa3ab";x.strokeRect(sx,sy,110,80)}
x.fillStyle="#d9822b";x.fillRect(120+rx*0,470,60,20);
for(const cx of [90,780]){x.fillStyle="#2a5d93";x.fillRect(cx,440,50,40);x.fillStyle="#3b7fc4";x.fillRect(cx+12,452,26,16)}
const rbx=130+((t*70)%520),rby=236;x.fillStyle="#d9822b";x.fillRect(rbx,rby+80,46,46);x.fillStyle="#1d2530";x.beginPath();x.arc(rbx+23,rby+103,8,0,Math.PI*2);x.fill();
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(255,107,0,.7)";x.lineWidth=3;x.beginPath();x.moveTo(rbx+23,rby+80);x.lineTo(rbx+23,rby+30);x.stroke();
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,rbx+23,rby+100);lead(S,LN[1]||"",780,130,560,220);lead(S,LN[2]||"",120,470,110,460);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"4 ROBOTS","MOVING",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.storm=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={charge:[450,250,zf*1.2],bolt:[450,300,zf*1.2],energy:[450,380,zf*1.2]};
const ORD=['charge','bolt','energy'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=0;
const flash=(Math.floor(t*1.3)%3===0)?1:0;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.beginPath();x.ellipse(450,190,300,90,0,0,Math.PI*2);x.fill();x.fillStyle="#3b4048";x.beginPath();x.ellipse(450,240,260,60,0,0,Math.PI*2);x.fill();
x.fillStyle="#5a636d";x.fillRect(-100,500,1100,100);
x.globalAlpha=p*(1-zi);x.fillStyle="#FF6B00";for(let k=0;k<8;k++){x.beginPath();x.arc(250+k*55,160+(k%3)*20,6,0,Math.PI*2);x.fill()}
x.fillStyle="#7fb3ff";for(let k=0;k<8;k++){x.beginPath();x.arc(250+k*55,320+(k%3)*18,6,0,Math.PI*2);x.fill()}
const bx=430+Math.sin(t*2)*20;x.globalAlpha=p*sp*(1-zi)*(flash?1:.35);x.strokeStyle="#ffe27a";x.lineWidth=5;x.beginPath();x.moveTo(bx,300);for(let k=1;k<=8;k++){x.lineTo(bx+(k%2?16:-16),300+k*24)}x.stroke();
x.fillStyle=`rgba(255,226,122,${flash?.25:0})`;x.fillRect(-100,0,1100,600);
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,80,300,180);lead(S,LN[1]||"",780,330,450,360);lead(S,LN[2]||"",780,470,600,470);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"+ / -","CHARGES",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.combine=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={header:[220,400,zf*2.0],drum:[450,300,zf*2.2],sieve:[520,400,zf*2.0]};
const ORD=['header','drum','sieve'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const rot=t*6,sh=Math.sin(t*12)*4;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a2f36";x.fillRect(120,300,520,170);x.fillStyle="#d9822b";x.fillRect(60,380,200,30);
x.fillStyle="#3b4048";x.fillRect(640,220,150,250);x.fillStyle="#c9a24a";x.fillRect(660,260,110,140);
x.save();x.translate(340,300);x.rotate(rot);x.fillStyle="#7b848d";x.fillRect(-150,-14,300,28);x.restore();
x.save();x.translate(420,320);x.rotate(rot*2);x.beginPath();x.arc(0,0,60,0,Math.PI*2);x.fillStyle="#4b535c";x.fill();x.strokeStyle="#c9d0d6";x.lineWidth=6;for(let k=0;k<6;k++){x.rotate(Math.PI/3);x.beginPath();x.moveTo(0,0);x.lineTo(56,0);x.stroke()}x.restore();
x.fillStyle="#9aa3ab";x.fillRect(200+sh,420,260,16);
x.globalAlpha=p*sp*(1-zi);x.fillStyle="rgba(214,170,80,.9)";for(let k=0;k<10;k++){const gx=((t*120+k*70)%520)+130;x.beginPath();x.arc(gx,470+(k%2)*6,4,0,Math.PI*2);x.fill()}
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,260,380);lead(S,LN[1]||"",780,120,500,300);lead(S,LN[2]||"",120,500,300,430);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"GRAIN","TANK",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.servo=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={motor:[300,300,zf*2.0],gears:[480,300,zf*2.0],pot:[660,300,zf*2.0]};
const ORD=['motor','gears','pot'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
const th=t*2.2,wip=Math.sin(th)*1.1;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.fillStyle="#2a5d93";x.fillRect(150,220,200,160);x.fillStyle="#3b7fc4";x.fillRect(150,240,200,120);
x.fillStyle="#9aa3ab";x.fillRect(350,280,70,40);
x.save();x.translate(450,300);x.rotate(th);x.fillStyle="#c9d0d6";for(let k=0;k<2;k++){x.beginPath();x.arc(k*-32,0,26,0,Math.PI*2);x.fill()}x.restore();
x.save();x.translate(580,300);x.beginPath();x.arc(0,0,80,Math.PI*0.8,Math.PI*2.2);x.strokeStyle="#5a636d";x.lineWidth=14;x.stroke();x.beginPath();x.arc(0,0,80,Math.PI*0.8,Math.PI*2.2);x.strokeStyle="#d9822b";x.lineWidth=3;x.stroke();x.rotate(-Math.PI*0.9+(wip+1.1)*1.0);x.fillStyle="#FF6B00";x.fillRect(-4,-84,8,90);x.restore();
x.fillStyle="#12171c";x.beginPath();x.arc(580,300,12,0,Math.PI*2);x.fill();
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(255,107,0,.7)";x.lineWidth=3;x.setLineDash([8,8]);x.beginPath();x.moveTo(430,260);x.lineTo(520,160);x.lineTo(660,160);x.lineTo(660,220);x.stroke();x.setLineDash([]);
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,240,300);lead(S,LN[1]||"",780,100,450,290);lead(S,LN[2]||"",780,470,580,400);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"FEEDBACK","POT",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.magnus=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={ball:[450,300,zf*1.2],airflow:[450,300,zf*1.15],force:[450,260,zf*1.2]};
const ORD=['ball','airflow','force'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=0;
const rot=t*9,bx=450,by=300;
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="rgba(190,220,255,.7)";x.lineWidth=3;
for(let k=0;k<6;k++){const yy=170+k*50;x.beginPath();x.moveTo(60,yy);for(let s=0;s<=20;s++){const xx=60+s*40;const dy=(yy<by?-1:1)*Math.max(0,60-Math.abs(xx-bx))*.6*(yy<by?1:1);x.lineTo(xx,yy+dy*0.5)}x.stroke()}
x.globalAlpha=p;x.beginPath();x.arc(bx,by,90,0,Math.PI*2);x.fillStyle="#e8ecef";x.fill();x.strokeStyle="#9aa3ab";x.lineWidth=4;x.stroke();
x.save();x.translate(bx,by);x.rotate(rot);for(let k=0;k<6;k++){x.rotate(Math.PI/3);x.beginPath();x.moveTo(0,0);x.lineTo(70,0);x.strokeStyle="#c9542b";x.lineWidth=4;x.stroke()}x.restore();
x.globalAlpha=p*sp*(1-zi);x.strokeStyle="#FF6B00";x.lineWidth=7;x.beginPath();x.moveTo(bx-120,by);x.lineTo(bx-40,by-90);x.stroke();x.beginPath();x.moveTo(bx-40,by-90);x.lineTo(bx-60,by-70);x.moveTo(bx-40,by-90);x.lineTo(bx-62,by-88);x.stroke();
x.globalAlpha=p*(1-zi);lead(S,LN[0]||"",120,100,bx,by-90);lead(S,LN[1]||"",780,470,640,400);lead(S,LN[2]||"",780,100,bx-40,by-90);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"SPIN","FORCE",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.miner=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={hash:[300,260,zf*1.9],board:[560,300,zf*1.9],block:[720,460,zf*1.9]};
const ORD=['hash','board','block'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
for(let r=0;r<3;r++){x.fillStyle="#2a2f36";x.fillRect(120,140+r*120,360,100);for(let c=0;c<6;c++){x.fillStyle="#12171c";x.fillRect(140+c*56,160+r*120,44,60);x.fillStyle=((Math.floor(t*4)+c+r)%3===0)?"#3dd68c":"#1d6b47";x.beginPath();x.arc(162+c*56,232+r*120-60,4,0,Math.PI*2);x.fill()}}
x.fillStyle="#1d2530";x.fillRect(540,140,200,340);x.fillStyle="#3b4048";for(let k=0;k<6;k++)x.fillRect(560,160+k*50,160,36);
x.globalAlpha=p*sp*(1-zi);x.fillStyle="rgba(214,170,80,.9)";x.font="18px monospace";for(let k=0;k<5;k++){x.fillText(((t*3e4+k*9731)%1e10).toFixed(0).padStart(10,"0").slice(0,8),150,310+k*0+ (k%3)*2);}
x.globalAlpha=p*(1-zi);
for(let k=0;k<5;k++){const bx=150+k*120,by=490;x.fillStyle=k<=Math.floor(t)%6?"#3b7fc4":"#2a2f36";x.fillRect(bx,by,100,40);}
lead(S,LN[0]||"",120,100,240,300);lead(S,LN[1]||"",780,100,640,300);lead(S,LN[2]||"",780,500,700,470);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"HASH","RATE",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};

PRO.salt=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[450,300,zf],FV={surface:[450,170,zf*2.0],layer:[450,300,zf*1.8],deep:[450,450,zf*1.8]};
const ORD=['surface','layer','deep'],KF=cams(d,FULL,FV,ORD,DUR);
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.25);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin="round";x.lineCap="round";
const bands=[["#1f5fa8",100],["#17497f",100],["#123a66",120],["#0c2a4d",140],["#071d37",140]];let y=100;
for(const [c,h] of bands){x.fillStyle=c;x.fillRect(120,y,660,h);y+=h}
x.strokeStyle="rgba(255,255,255,.4)";x.lineWidth=2;x.setLineDash([10,10]);x.beginPath();x.moveTo(120,300);x.lineTo(780,300);x.stroke();x.setLineDash([]);
x.globalAlpha=p*sp*(1-zi);x.fillStyle="rgba(255,107,0,.85)";for(let k=0;k<8;k++){const yy=(120+k*40+t*30)%480+100;x.beginPath();x.arc(180+k*70,yy,5,0,Math.PI*2);x.fill()}
x.globalAlpha=p*(1-zi);x.fillStyle="#c9d0d6";x.fillRect(90,100,20,4);x.fillRect(90,300,20,4);x.fillRect(90,500,20,4);
lead(S,LN[0]||"",120,80,450,120);lead(S,LN[1]||"",780,300,500,300);lead(S,LN[2]||"",780,470,450,450);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||"",4,ts-.35,A);
meter(S,"150 m","SALINITY",A,a,fi>=0);callout(S,d,t,A);x.globalAlpha=1}};
}
