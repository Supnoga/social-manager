// Presné modely 14 – obvodová stena v reze: vrstvy, priebeh teploty a rosný bod.
// Teploty na rozhraniach sú spočítané z tepelného odporu vrstiev (hrúbka / vodivosť), vnútri 20 °C, vonku −10 °C.
// Hýbe sa len to, čo sa hýbe naozaj: teplo tečie von (tým viac, čím horšie stena izoluje), vodná para ide z izby do steny a na studenom povrchu skondenzuje.
{
const K=window.KIT,PRO=K.PRO,{mix,rgba,ez,hatch,dot,HS,STG,camAt,stamp,callout,LBL,tag,meter,cams,shot,lead,badge}=K;
const TAU=Math.PI*2,N=v=>{v=parseFloat(v);return isFinite(v)?v:0},sm=u=>u<=0?0:u>=1?1:u*u*(3-2*u),EL='#8fd0ff',HOT='#ff6a3d';
const arw=(x,a,b,col,w)=>{const an=Math.atan2(b[1]-a[1],b[0]-a[0]),hl=Math.min(4+w*2,Math.hypot(b[0]-a[0],b[1]-a[1])*.6);x.strokeStyle=col;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.moveTo(b[0]-Math.cos(an-.5)*hl,b[1]-Math.sin(an-.5)*hl);x.lineTo(b[0],b[1]);x.lineTo(b[0]-Math.cos(an+.5)*hl,b[1]-Math.sin(an+.5)*hl);x.stroke()};

PRO.wall=(v,d)=>{const S=STG(v),x=S.x,A=D.acc,LN=LBL(d),DUR=N(d._dur)||9,F=String(d.f||''),ST=['bare','interior','wet','sip'].includes(F)?F:'',Y0=112,Y1=478,TI=20,TO=-10,TD=9.3;
// vrstvy zvnútra von: [druh, šírka na obraze, tepelný odpor = hrúbka / vodivosť]
const PL=['plaster',18,.015/.7],BR=['brick',180,.25/.5],E15=['eps',150,.15/.035],E10=['eps',110,.10/.035],RN=['render',14,.01/.9],OS=['osb',18,.015/.13];
const LAY=ST=='bare'?[PL,BR,RN]:ST=='interior'||ST=='wet'?[PL,E10,BR,RN]:ST=='sip'?[OS,E15,OS]:[PL,BR,E15,RN];
const W=LAY.reduce((a,l)=>a+l[1],0),X0=450-W/2,RT=.13+.04+LAY.reduce((a,l)=>a+l[2],0),U=1/RT,XS=[X0],TS=[TI-(TI-TO)*.13/RT];
LAY.forEach(l=>{XS.push(XS[XS.length-1]+l[1]);TS.push(TS[TS.length-1]-(TI-TO)*l[2]/RT)});
const X1=XS[XS.length-1],yT=T=>172+(TI-T)*9,idx=k=>LAY.findIndex(l=>l[0]==k),mid=k=>{const i=idx(k);return i<0?450:(XS[i]+XS[i+1])/2};
const TP=[[X0-112,TI],[X0-30,TI]];XS.forEach((q,i)=>TP.push([q,TS[i]]));TP.push([X1+26,TO],[X1+112,TO]);
let XD=null;for(let i=1;i<TP.length;i++){const a=TP[i-1],b=TP[i];if(a[1]>=TD&&b[1]<TD){XD=a[0]+(b[0]-a[0])*(a[1]-TD)/(a[1]-b[1]);break}}
const zf=Math.min(S.w/900,S.h/600)*.98,FV={inside:[X0-24,300,zf*1.8],masonry:[mid(ST=='sip'?'osb':'brick'),300,zf*1.8],insulation:[mid('eps'),300,zf*1.8],outside:[X1+24,300,zf*1.8],bare:[450,300,zf*1.05],interior:[450,300,zf*1.05],wet:[450,300,zf*1.05],sip:[450,300,zf*1.05]},FULL=[450,300,zf*1.05],ORD=['inside','masonry','insulation','outside'],KF=cams(d,ST?FV[ST]:FULL,FV,ORD,DUR);
const rows=U>1?5:U>.3?2:1,nar=U>1?5:U>.3?3:2,span=W+190,XB=ST=='interior'?XS[1]:null,XC=ST=='wet'?XS[2]:null;
const layer=(l,a)=>{const w=l[1],k=l[0];if(k=='plaster'){x.fillStyle='#c9ced3';x.fillRect(a,Y0,w,Y1-Y0)}else if(k=='render'){x.fillStyle='#8f959c';x.fillRect(a,Y0,w,Y1-Y0)}
else if(k=='osb'){x.fillStyle='#a8875a';x.fillRect(a,Y0,w,Y1-Y0);x.strokeStyle='rgba(60,40,20,.5)';x.lineWidth=1.5;for(let i=0;i<34;i++){const px=a+2+HS(i,1)*(w-4),py=Y0+4+HS(i,2)*(Y1-Y0-14);x.beginPath();x.moveTo(px,py);x.lineTo(px+(HS(i,3)-.5)*6,py+8);x.stroke()}}
else if(k=='brick'){x.fillStyle='#6e4332';x.fillRect(a,Y0,w,Y1-Y0);x.strokeStyle='rgba(235,225,210,.45)';x.lineWidth=2;x.beginPath();for(let r=0,y=Y0;y<Y1;r++,y+=30.5){if(r){x.moveTo(a,y);x.lineTo(a+w,y)}const ye=Math.min(Y1,y+30.5);(r%2?[w/3,2*w/3]:[w/2]).forEach(q=>{x.moveTo(a+q,y);x.lineTo(a+q,ye)})}x.stroke()}
else{x.fillStyle='rgba(236,222,170,.2)';x.fillRect(a,Y0,w,Y1-Y0);x.strokeStyle='rgba(255,255,255,.2)';x.lineWidth=1.3;const n=Math.round(w*.55);for(let i=0;i<n;i++){x.beginPath();x.arc(a+7+HS(i,4)*(w-14),Y0+7+HS(i,5)*(Y1-Y0-14),3.5+2.5*HS(i,6),0,TAU);x.stroke()}}};
return (t,st)=>{const p=E(st(0,1)),sp=cl(st(.3,1));S.begin();x.globalAlpha=p;const cm=camAt(KF,t,.8),zi=ez((cm[2]/zf-1)/.22);
x.save();x.translate(S.w/2,S.h/2);x.scale(cm[2],cm[2]);x.translate(-cm[0],-cm[1]);x.lineJoin='round';x.lineCap='round';
// izba (teplo) a vonkajší vzduch (zima)
let g=x.createLinearGradient(X0-170,0,X0,0);g.addColorStop(0,'rgba(255,107,0,0)');g.addColorStop(1,'rgba(255,107,0,.12)');x.fillStyle=g;x.fillRect(X0-170,Y0,170,Y1-Y0);
g=x.createLinearGradient(X1,0,X1+170,0);g.addColorStop(0,'rgba(120,190,255,.13)');g.addColorStop(1,'rgba(120,190,255,0)');x.fillStyle=g;x.fillRect(X1,Y0,170,Y1-Y0);
LAY.forEach((l,i)=>layer(l,XS[i]));
x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=1.5;x.beginPath();XS.slice(1,-1).forEach(q=>{x.moveTo(q,Y0);x.lineTo(q,Y1)});x.stroke();
x.strokeStyle='#fff';x.lineWidth=3.5;x.beginPath();x.moveTo(X0,Y0);x.lineTo(X0,Y1);x.moveTo(X1,Y0);x.lineTo(X1,Y1);x.stroke();x.lineWidth=2;x.setLineDash([8,7]);x.beginPath();x.moveTo(X0,Y0);x.lineTo(X1,Y0);x.moveTo(X0,Y1);x.lineTo(X1,Y1);x.stroke();x.setLineDash([]);
if(XB!=null){x.strokeStyle=A;x.lineWidth=4;x.beginPath();x.moveTo(XB,Y0);x.lineTo(XB,Y1);x.stroke()}
// skondenzovaná voda na studenom líci muriva
if(XC!=null){const u=t%14,h=Math.min(96,u*8.5);g=x.createLinearGradient(XC-44,0,XC,0);g.addColorStop(0,'rgba(60,140,210,0)');g.addColorStop(1,'rgba(60,140,210,.5)');x.fillStyle=g;x.fillRect(XC-44,Y1-h,44,h);x.fillStyle='rgba(60,140,210,.35)';x.fillRect(XC,Y1-h*.7,26,h*.7);
for(let i=0;i<8;i++){const yy=Y0+16+((t*46+i*47)%(Y1-Y0-30));dot(x,[XC-4,yy],3.8,'#6fc0ff',p*cl(u/1.5),false)}}
// teplo tečie zvnútra von: čím horšia stena, tým viac
for(let r=0;r<rows;r++){const y=rows==1?Y1-52:Y0+44+r*(Y1-Y0-88)/(rows-1);for(let i=0;i<nar;i++){const q=((t*(46+50*Math.min(U,1.5))+i*span/nar+r*41)%span+span)%span,px=X0-95+q,k=q/span;x.globalAlpha=p*.85*Math.min(1,q/30,(span-q)/30);arw(x,[px,y],[px+24,y],mix(HOT,EL,k),3)}}x.globalAlpha=p;
// vodná para z izby: parozábrana ju zastaví, bez nej dôjde až na studené murivo
if(XB!=null||XC!=null){const xs=X0-104,stop=XB!=null?XB-5:XC-4;for(let i=0;i<16;i++){const u=(t*.2+HS(i,1))%1,y=Y0+26+HS(i,2)*(Y1-Y0-52)+6*Math.sin(t*2+i);let px,al=Math.min(1,u*8);
if(XB!=null){px=u<.55?xs+(stop-xs)*(u/.55):stop-(stop-xs)*.6*((u-.55)/.45);al=Math.min(al,(1-u)*5)}else{px=xs+(stop-xs)*u;al=Math.min(al,(1-u)*12)}dot(x,[px,y],3.4,EL,p*al*.95,false)}}
// priebeh teploty v stene a rosný bod
x.strokeStyle='rgba(0,0,0,.6)';x.lineWidth=10;x.beginPath();TP.forEach((q,i)=>i?x.lineTo(q[0],yT(q[1])):x.moveTo(q[0],yT(q[1])));x.stroke();
g=x.createLinearGradient(TP[0][0],0,TP[TP.length-1][0],0);TP.forEach(q=>g.addColorStop((q[0]-TP[0][0])/(TP[TP.length-1][0]-TP[0][0]),mix(EL,HOT,(q[1]-TO)/(TI-TO))));x.strokeStyle=g;x.lineWidth=5;x.beginPath();TP.forEach((q,i)=>i?x.lineTo(q[0],yT(q[1])):x.moveTo(q[0],yT(q[1])));x.stroke();
XS.forEach((q,i)=>dot(x,[q,yT(TS[i])],4,'#fff',p,false));
if(XD!=null){x.strokeStyle='rgba(143,208,255,.5)';x.lineWidth=1.6;x.setLineDash([5,6]);x.beginPath();x.moveTo(X0-60,yT(TD));x.lineTo(X1+60,yT(TD));x.stroke();x.setLineDash([]);dot(x,[XD,yT(TD)],7,EL,p,true)}
x.globalAlpha=p*sp;tag(S,'20 °C',X0-84,yT(TI)-24,'center',HOT,22);tag(S,'−10 °C',X1+84,yT(TO)+26,'center',EL,22);
if(XD!=null)tag(S,LN[4]||'',X0-64,yT(TD)-14,'right',EL,17);
x.globalAlpha=p*sp*(1-zi);tag(S,LN[0]||'',X0-88,Y1+36,'center','#fff',20);tag(S,LN[3]||'',X1+88,Y1+36,'center','#fff',20);
if(idx('brick')>=0)lead(S,LN[1],mid('brick'),82,mid('brick'),Y0+8);if(idx('eps')>=0)lead(S,LN[2],mid('eps'),82,mid('eps'),Y0+8);if(XB!=null)lead(S,LN[5]||'',XB+40,Y1+66,XB,Y1-10);
x.restore();
const [FN,ts]=shot(KF,d,t),fi=ORD.indexOf(FN),a=cl((t-.6)/.4);x.globalAlpha=p;
if(fi>=0&&ts>.35)stamp(S,fi,LN[fi]||'',4,ts-.35,A);
meter(S,String(Math.round(U*(TI-TO))),'W LOST PER M²',A,a,fi>=0);
if(XC!=null)badge(S,'WET','COLD SIDE',A,a);else badge(S,TS[0].toFixed(0)+' °C','WALL SURFACE',A,a);
callout(S,d,t,A);x.globalAlpha=1}};
}
