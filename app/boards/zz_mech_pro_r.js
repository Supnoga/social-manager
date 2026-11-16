// Presné modely 18 – priemyselná robotická ruka (bočný pohľad). Uhly kĺbov počíta inverzná kinematika dvoch ramien:
// koniec ruky ide po dráhe (zdvihni, prenes, polož) a ramená sa natočia presne tak, aby tam dosiahli (lakeť hore).
// V každom kĺbe je elektromotor s prevodom; aktívny kĺb svieti. f=weld: zvárací hrot ide po švíku karosérie a letia iskry.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,STG,camAt,stamp,callout,LBL,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u);

PRO.robot_arm=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),WD=F=='weld';
const BX=380,FL=480,SH=[BX,392],L1=190,L2=170,L3=46,CYC=7.2;
const zf=Math.min(S.w/900,S.h/600)*.98,FULL=[440,350,zf*1.25],FV={base:[BX,420,zf*2],shoulder:[BX,370,zf*1.9],elbow:[470,250,zf*1.7],gripper:[560,360,zf*1.8],weld:[580,330,zf*1.5]};
const ORD=['base','shoulder','elbow','gripper'],KF=cams(d,FULL,FV,ORD,DUR);
// dráha konca ruky (zápästia) v cykle: [čas, x, y, zovretie]
const PATH=WD?null:[[0,610,350,0],[.9,640,416,0],[1.3,640,416,1],[2.1,640,320,1],[3.6,230,250,1],[4.5,170,346,1],[4.9,170,346,0],[5.6,230,270,0],[CYC,610,350,0]];
const SEAM=[[560,300],[610,290],[660,300],[700,318]];
const tip=u=>{if(WD){const k=(Math.sin(u/CYC*TAU-Math.PI/2)+1)/2,i=Math.min(2,Math.floor(k*3)),f=k*3-i;return [SEAM[i][0]+(SEAM[i+1][0]-SEAM[i][0])*f,SEAM[i][1]+(SEAM[i+1][1]-SEAM[i][1])*f-L3,0]}
let i=1;while(i<PATH.length-1&&u>PATH[i][0])i++;const a=PATH[i-1],b=PATH[i],f=sm((u-a[0])/(b[0]-a[0]));return [a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f,f<.5?a[3]:b[3]]};
// inverzná kinematika: uhly ramena (q1) a lakťa (q2) pre bod zápästia
const ik=(px,py)=>{let dx=px-SH[0],dy=py-SH[1],dd=Math.hypot(dx,dy);const mx=L1+L2-2;if(dd>mx){dx*=mx/dd;dy*=mx/dd;dd=mx}
const c2=(dd*dd-L1*L1-L2*L2)/(2*L1*L2),q2=Math.acos(Math.max(-1,Math.min(1,c2))),q1=Math.atan2(dy,dx)-Math.atan2(L2*Math.sin(q2),L1+L2*Math.cos(q2));return [q1,q2]};
const link=(x0,y0,x1,y1,w,col)=>{const a=Math.atan2(y1-y0,x1-x0),l=Math.hypot(x1-x0,y1-y0);x.save();x.translate(x0,y0);x.rotate(a);x.beginPath();x.roundRect(-w/2,-w/2,l+w,w,w/2);x.fillStyle=col;x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.restore()};
const joint=(px,py,r,on,ang)=>{x.beginPath();x.arc(px,py,r,0,TAU);x.fillStyle=mix('#2a2f35',A,on*.7);x.fill();x.strokeStyle=on>.2?A:'#fff';x.lineWidth=3;x.stroke();
x.strokeStyle='rgba(255,255,255,.7)';x.lineWidth=2;for(let k=0;k<3;k++){const a=ang+k*TAU/3;x.beginPath();x.moveTo(px,py);x.lineTo(px+Math.cos(a)*r*.7,py+Math.sin(a)*r*.7);x.stroke()}};
let prev=null;
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1.25)/.25);
const u=t%CYC,[wx,wy,grip]=tip(u),[q1,q2]=ik(wx,wy),[r1,r2]=ik(...tip((u+.05)%CYC).slice(0,2));
const v1=Math.abs(r1-q1)*20,v2=Math.abs(r2-q2)*20;   // ktorý motor práve pracuje (rýchlosť kĺbu)
const E1=[SH[0]+Math.cos(q1)*L1,SH[1]+Math.sin(q1)*L1],E2=[E1[0]+Math.cos(q1+q2)*L2,E1[1]+Math.sin(q1+q2)*L2];
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// podlaha, pás s dielmi vpravo, odkladací stôl vľavo
x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.beginPath();x.moveTo(60,FL);x.lineTo(800,FL);x.stroke();
if(!WD){x.beginPath();x.roundRect(560,446,220,16,8);x.fillStyle='#2a2f35';x.fill();x.strokeStyle='#fff';x.stroke();for(let k=0;k<6;k++){x.beginPath();x.arc(574+k*39,454,5,0,TAU);x.stroke()}
x.fillStyle='#2a2f35';x.fillRect(110,378,120,10);x.strokeRect(110,378,120,10);x.fillRect(120,388,8,FL-388);x.fillRect(212,388,8,FL-388);
// diel: na páse, v chápadle, alebo na stole
const held=u>1.3&&u<4.9,onT=u>=4.9,belt=u<1.3;const bx=held?E2[0]:onT?170:640+(belt?0:0),by=held?E2[1]+L3+12:onT?362:430;
if(belt||held||onT){x.beginPath();x.roundRect(bx-22,by-16,44,32,4);x.fillStyle='#8f959c';x.fill();x.strokeStyle='#fff';x.lineWidth=2;x.stroke()}
if(u>=4.9){x.globalAlpha=p*cl(1-(u-6.4)/.6);x.beginPath();x.roundRect(618,414,44,32,4);x.fillStyle='#8f959c';x.fill();x.stroke();x.globalAlpha=p}}
else{x.beginPath();x.moveTo(520,FL);x.lineTo(530,330);x.quadraticCurveTo(560,290,640,284);x.quadraticCurveTo(700,284,740,330);x.lineTo(780,340);x.lineTo(790,FL);x.closePath();x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.strokeStyle=A;x.lineWidth=3;x.setLineDash([8,6]);x.beginPath();SEAM.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke();x.setLineDash([])}
// podstavec s otočným kĺbom
x.beginPath();x.moveTo(BX-70,FL);x.lineTo(BX-48,FL-46);x.lineTo(BX+48,FL-46);x.lineTo(BX+70,FL);x.closePath();x.fillStyle='#1b1e22';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();
x.beginPath();x.roundRect(BX-34,SH[1]-6,68,FL-46-SH[1]+6,8);x.fillStyle='#2a2f35';x.fill();x.stroke();
// ramená
link(SH[0],SH[1],E1[0],E1[1],40,'#3a3f46');link(E1[0],E1[1],E2[0],E2[1],32,'#3a3f46');
// zápästie a chápadlo (alebo zvárací hrot) – vždy kolmo dole
const gx=E2[0],gy=E2[1];x.strokeStyle='#fff';x.lineWidth=3;x.fillStyle='#2a2f35';x.beginPath();x.roundRect(gx-10,gy,20,L3-10,4);x.fill();x.stroke();
if(WD){x.fillStyle='#c9ced3';x.beginPath();x.moveTo(gx-8,gy+L3-10);x.lineTo(gx+8,gy+L3-10);x.lineTo(gx,gy+L3+4);x.closePath();x.fill();x.stroke();
for(let k=0;k<9;k++){const ph=(t*3+k*.37)%1,ang=-Math.PI/2+(k%2?1:-1)*(.4+k*.18)+.3*Math.sin(k*7),r=ph*60;dot(x,[gx+Math.cos(ang)*r,gy+L3+4+Math.sin(ang)*r+ph*ph*30],3.5*(1-ph)+1,ph<.3?'#fff':'#ffb347',p*(1-ph),true)}dot(x,[gx,gy+L3+4],18,'#fff',p*.8,true)}
else{const o=grip?22:34;x.fillStyle='#c9ced3';[-1,1].forEach(s=>{x.beginPath();x.roundRect(gx+s*o-5,gy+L3-14,10,30,3);x.fill();x.stroke()});x.fillRect(gx-o,gy+L3-16,2*o,6)}
// kĺby s motormi: svieti ten, ktorý sa práve točí
joint(BX,FL-46,16,0,0);joint(SH[0],SH[1],24,cl(v1),q1*3);joint(E1[0],E1[1],20,cl(v2),q2*3);joint(E2[0],E2[1],13,0,0);
x.globalAlpha=p*sp*(1-zi);
lead(S,LN[0],250,520,BX-50,FL-24);lead(S,LN[1],170,190,SH[0]-18,SH[1]-14);lead(S,LN[2],470,150,E1[0],E1[1]-20);lead(S,LN[3],730,200,E2[0]+14,E2[1]+L3);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4),deg=Math.round(((-q1*180/Math.PI)%360+540)%360-180);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(deg)+'°',FN=='elbow'?'ELBOW':'SHOULDER ANGLE',A,a,fi>=0);
badge(S,WD?'WELD':grip?(u<2.1?'PICK':'MOVE'):(u>4.9&&u<5.6?'PLACE':'REACH'),WD?'FOLLOWS THE SEAM':'MOTORS IN EVERY JOINT',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
