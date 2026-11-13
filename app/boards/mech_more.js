// ďalšie hotové mechanizmy pre V.mech (d.m): prevodovka, hydraulika, páka, kladkostroj, generátor, motor, transformátor,
// raketa, ponorka, výťah, šikmý vrh, štiepenie, obvod, rotor vrtuľníka, montážna linka, solárny článok
{
const MECH2={};
// spoločný základ: plátno, popisky (d.l), čísla (d.n), kresliace pomôcky
const M2=(v,d)=>{const x=cv2(v,864,560),A=D.acc,L=(Array.isArray(d.l)?d.l:[]).map(s=>s==null?'':String(s));const n=Array.isArray(d.n)?d.n:(d.n!=null?[d.n]:[]);
const nn=(i,def,lo,hi)=>{const r=N(n[i]);return r?Math.max(lo,Math.min(hi,r)):def};
const lab=(i,l,t,w,al,fs,col)=>{const s=L[i]||'';if(!s.trim())return null;const e=el('div','lab',`left:${l}px;top:${t}px;width:${w}px;text-align:${al||'center'};font-size:${fs||24}px;opacity:0;${col?'color:'+col:''}`,esc(s));v.append(e);fit(e,fs||24,14,60,w);return e};
const val=(l,t,w,al,fs,col)=>{const e=el('div','big',`left:${l}px;top:${t}px;width:${w}px;text-align:${al||'center'};font-size:${fs||44}px;opacity:0;white-space:nowrap;color:${col||'#fff'}`,'');v.append(e);return e};
const txt=(e,s,p)=>{if(!e)return;if(s!=null&&e.textContent!==s)e.textContent=s;e.style.opacity=cl(p)};
const op=(e,p)=>{if(e)e.style.opacity=cl(p)};
const mv=(e,l,t)=>{if(e){e.style.left=l+'px';e.style.top=t+'px'}};
const ln=(x1,y1,x2,y2,c,w)=>{x.strokeStyle=c||'#fff';x.lineWidth=w||4;x.beginPath();x.moveTo(x1,y1);x.lineTo(x2,y2);x.stroke()};
const ar=(x1,y1,x2,y2,c,w,h)=>{ln(x1,y1,x2,y2,c,w);const a=Math.atan2(y2-y1,x2-x1),hs=h||(12+(w||4)*1.5);x.beginPath();x.moveTo(x2-hs*Math.cos(a-.5),y2-hs*Math.sin(a-.5));x.lineTo(x2,y2);x.lineTo(x2-hs*Math.cos(a+.5),y2-hs*Math.sin(a+.5));x.stroke()};
const ci=(cx,cy,r,c,w,f)=>{x.beginPath();x.arc(cx,cy,r,0,6.2832);if(f){x.fillStyle=f;x.fill()}if(c){x.strokeStyle=c;x.lineWidth=w||4;x.stroke()}};
const dot=(cx,cy,r,f)=>{x.fillStyle=f;x.beginPath();x.arc(cx,cy,r,0,6.2832);x.fill()};
const rc=(l,t,w,h,c,lw,f)=>{if(f){x.fillStyle=f;x.fillRect(l,t,w,h)}if(c){x.strokeStyle=c;x.lineWidth=lw||4;x.strokeRect(l,t,w,h)}};
const gear=(cx,cy,r,nT,rot,col)=>{x.save();x.translate(cx,cy);x.rotate(rot);x.beginPath();for(let i=0;i<nT*2;i++){const a=i*Math.PI/nT,rr=i%2?r:r*1.16,a2=a+Math.PI/nT,o=.72/nT;x.lineTo(Math.cos(a-o)*rr,Math.sin(a-o)*rr);x.lineTo(Math.cos(a2-o)*rr,Math.sin(a2-o)*rr)}x.closePath();x.fillStyle='#000';x.fill();x.strokeStyle=col;x.lineWidth=4;x.stroke();
x.beginPath();x.arc(0,0,r*.26,0,6.3);x.stroke();for(let k=0;k<4;k++){const a=k*Math.PI/2;x.beginPath();x.moveTo(Math.cos(a)*r*.26,Math.sin(a)*r*.26);x.lineTo(Math.cos(a)*r*.8,Math.sin(a)*r*.8);x.stroke()}x.restore()};
// bodky prúdu po lomenej čiare (pole bodov), u = posun 0..1
const path=(P,closed)=>{const pts=closed?P.concat([P[0]]):P;const seg=[];let tot=0;for(let i=1;i<pts.length;i++){const l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);seg.push(l);tot+=l}
return {tot,at:(u)=>{let s=((u%1)+1)%1*tot;for(let i=0;i<seg.length;i++){if(s<=seg[i]||i==seg.length-1){const f=seg[i]?s/seg[i]:0;return [pts[i][0]+(pts[i+1][0]-pts[i][0])*f,pts[i][1]+(pts[i+1][1]-pts[i][1])*f]}s-=seg[i]}return pts[0]},
draw:(c,w)=>{x.strokeStyle=c||'#fff';x.lineWidth=w||4;x.beginPath();pts.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke()}}};
const flow=(pp,cnt,u,r,f,a)=>{for(let k=0;k<cnt;k++){const q=pp.at(u+k/cnt);x.globalAlpha=a==null?1:a;dot(q[0],q[1],r,f)}x.globalAlpha=1};
const bulb=(cx,cy,r,glow)=>{if(glow>0){const g=x.createRadialGradient(cx,cy,0,cx,cy,r*2.6);g.addColorStop(0,A);g.addColorStop(1,'rgba(0,0,0,0)');x.globalAlpha=.55*glow;x.fillStyle=g;x.beginPath();x.arc(cx,cy,r*2.6,0,6.3);x.fill();x.globalAlpha=1}
ci(cx,cy,r,'#fff',4,'#000');rc(cx-r*.45,cy+r*.9,r*.9,r*.55,'#fff',4,'#000');x.strokeStyle=glow>.05?A:'#8a8a8a';x.lineWidth=glow>.05?5:3;x.beginPath();x.moveTo(cx-r*.3,cy+r*.9);x.lineTo(cx-r*.3,cy);x.lineTo(cx-r*.1,cy-r*.3);x.lineTo(cx+r*.1,cy);x.lineTo(cx+r*.3,cy-r*.3);x.lineTo(cx+r*.3,cy+r*.9);x.stroke();
if(glow>.05){x.strokeStyle=A;x.lineWidth=4;x.globalAlpha=glow;for(let k=0;k<8;k++){const a=k*Math.PI/4-Math.PI/2;if(Math.abs(Math.sin(a))>.95&&Math.sin(a)>0)continue;x.beginPath();x.moveTo(cx+Math.cos(a)*(r+12),cy+Math.sin(a)*(r+12));x.lineTo(cx+Math.cos(a)*(r+28),cy+Math.sin(a)*(r+28));x.stroke()}x.globalAlpha=1}};
const f1=(v)=>NF(v,Math.abs(v)>=100||Math.abs(v-Math.round(v))<.05?0:Math.abs(v)>=10?1:2);
return {x,A,L,n,nn,lab,val,txt,op,mv,ln,ar,ci,dot,rc,gear,path,flow,bulb,f1}};
const RUN=(S,fn)=>(t,st)=>{const p=E(st(0,1));S.x.clearRect(0,0,864,560);S.x.globalAlpha=1;S.x.save();S.x.globalAlpha=p;fn(t,st,p);S.x.restore()};

// ---------- prevodovka: n=[zuby hnacieho, zuby hnaného] → otáčky a krútiaci moment ----------
MECH2.gearbox=(v,d)=>{const S=M2(v,d),{x,A}=S;const a=Math.round(S.nn(0,12,6,60)),b=Math.round(S.nn(1,36,6,60));const i=b/a;
const k=Math.min(165/(Math.max(a,b)*1.16),470/(2.32*(a+b))),r1=a*k,r2=b*k,D2=r1+r2+6;const c1=432-(r2-r1)/2-D2/2+0,c2=c1+D2,cy=215;const e1=c1-r1*1.16-18,e2=c2+r2*1.16+18;
const L0=S.lab(0,8,cy-30,e1-8,'right',22),L1=S.lab(1,e2,cy-30,856-e2,'left',22,A);
const vN=S.val(32,470,250,'center',46),vI=S.val(307,462,250,'center',58,A),vM=S.val(582,470,250,'center',46);
const sN=el('div','lab',`left:32px;top:432px;width:250px;text-align:center;font-size:20px;opacity:0`,esc(S.L[2]||'n')),sM=el('div','lab',`left:582px;top:432px;width:250px;text-align:center;font-size:20px;opacity:0`,esc(S.L[3]||'M'));v.append(sN,sM);fit(sN,20,13,30,250);fit(sM,20,13,30,250);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),w=t*1.6;x.globalAlpha=p;S.gear(c1,cy,r1,a,w,'#fff');S.gear(c2,cy,r2,b,-w/i+Math.PI/b+(b%2?0:Math.PI/b),A);
// smer otáčania
x.globalAlpha=p*sp;[[c1,r1,1,'#fff'],[c2,r2,-1,A]].forEach(([cx,r,s,c])=>{const R=r*1.16+16,a0=-Math.PI/2-.5,a1=-Math.PI/2+.5;x.strokeStyle=c;x.lineWidth=3;x.beginPath();x.arc(cx,cy,R,a0,a1);x.stroke();const e=s>0?a1:a0,tx=-Math.sin(e)*s,ty=Math.cos(e)*s,px=cx+Math.cos(e)*R,py=cy+Math.sin(e)*R;x.beginPath();x.moveTo(px-tx*12-Math.cos(e)*7,py-ty*12-Math.sin(e)*7);x.lineTo(px,py);x.lineTo(px-tx*12+Math.cos(e)*7,py-ty*12+Math.sin(e)*7);x.stroke()});
x.globalAlpha=p;S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));const q=st(1.2,.8);S.txt(vI,'1 : '+S.f1(i),q);S.txt(vN,'× '+S.f1(1/i),st(1.6,.6));S.txt(vM,'× '+S.f1(i),st(1.9,.6));S.op(sN,st(1.6,.6));S.op(sM,st(1.9,.6));
x.globalAlpha=p*q*.5;S.ln(60,420,804,420,'#fff',2)})};

// ---------- hydraulický lis: n=[plocha malého piesta, plocha veľkého] → sila × pomer ----------
MECH2.hydraulic=(v,d)=>{const S=M2(v,d),{x,A}=S;const a1=S.nn(0,1,.01,1e6),a2=S.nn(1,10,.01,1e8);const k=Math.max(1.2,Math.min(400,a2/a1));
const ws=56,wb=Math.min(300,Math.max(110,ws*Math.sqrt(k))),xs=120,xb=500,top=170,bot=420;
const L0=S.lab(0,xs+ws/2-130,bot+68,260),L1=S.lab(1,xb+wb/2-150,bot+68,300),L2=S.lab(2,xs+ws+20,330,xb-xs-ws-40,'center',22);
const vF=S.val(xs+ws/2+18,40,120,'left',44),vG=S.val(xb+wb/2-150,40,300,'center',48,A);
return RUN(S,(t,st,p)=>{const sp=cl(st(.4,1));const ph=(1-Math.cos(t*1.5))/2*sp;const ds=110*ph,db=Math.max(2,110/k)*ph;const ys=200+ds,yb=300-db;
// kvapalina
x.fillStyle=A;x.globalAlpha=p*.28;x.fillRect(xs,ys+18,ws,bot-ys-18);x.fillRect(xb,yb+18,wb,bot-yb-18);x.fillRect(xs,bot,xb+wb-xs,40);x.globalAlpha=p;
// nádoby
x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(xs,top);x.lineTo(xs,bot+40);x.lineTo(xb+wb,bot+40);x.lineTo(xb+wb,top);x.moveTo(xb,top);x.lineTo(xb,bot);x.lineTo(xs+ws,bot);x.lineTo(xs+ws,top);x.stroke();
// piesty
S.rc(xs+3,ys,ws-6,18,null,0,'#d9d9d9');S.ln(xs+ws/2,ys,xs+ws/2,ys-70,'#9a9a9a',8);S.ln(xs+ws/2-26,ys-70,xs+ws/2+26,ys-70,'#fff',6);
S.rc(xb+3,yb,wb-6,18,null,0,'#d9d9d9');const bw=Math.min(wb-30,200);S.rc(xb+wb/2-bw/2,yb-90,bw,90,'#fff',4,'#000');S.ln(xb+wb/2-bw/2,yb-45,xb+wb/2+bw/2,yb-45,'rgba(255,255,255,.35)',2);
// sily
const fa=st(.8,.7);x.globalAlpha=p*fa;S.ar(xs+ws/2,ys-150,xs+ws/2,ys-80,'#fff',5);const la=Math.min(150,40+20*Math.log2(k)*1.5);S.ar(xb+wb+28,yb+40,xb+wb+28,yb+40-la,A,8);x.globalAlpha=p;
// tok kvapaliny
x.globalAlpha=p*sp*.9;for(let j=0;j<5;j++){const u=((t*.35+j/5)%1);const X=xs+ws/2+u*(xb+wb/2-xs-ws/2);S.dot(X,bot+20,4,'#fff')}x.globalAlpha=p;
vF.style.top=(ys-150)+'px';S.txt(vF,'F',fa);S.txt(vG,'F × '+S.f1(k),st(1.3,.7));S.op(L0,st(.3,.6));S.op(L1,st(.5,.6));S.op(L2,st(.7,.6))})};

// ---------- páka: n=[rameno sily, rameno bremena] → potrebná sila ----------
MECH2.lever=(v,d)=>{const S=M2(v,d),{x,A}=S;const ae=S.nn(0,3,.01,1e6),al=S.nn(1,1,.01,1e6);let fr=al/(al+ae);fr=Math.max(.1,Math.min(.9,fr));const k=ae/al;
const x0=110,x1=754,fx=x0+(x1-x0)*fr,fy=340;const Ll=fx-x0,Le=x1-fx;const amax=.11;
const top=fy-Math.max(Ll*Math.sin(amax)+90,Le*Math.sin(amax)+96);
const L1=S.lab(1,Math.max(0,x0-60),Math.max(4,top-104),260),L0=S.lab(0,Math.min(604,x1-190),Math.max(4,top-104),260),L2=S.lab(2,fx-130,506,260,'center',20);
const vE=S.val(Math.min(604,x1-190),Math.max(4,top-104)+34,260,'center',44,A),vL=S.val(Math.max(0,x0-60),Math.max(4,top-104)+34,260,'center',44);
const dl=el('div','lab','left:0;top:'+(fy+124)+'px;width:10px;text-align:center;font-size:22px;text-transform:none;opacity:0',''),de=el('div','lab','left:0;top:'+(fy+124)+'px;width:10px;text-align:center;font-size:22px;text-transform:none;opacity:0','');v.append(dl,de);const u=d.u?' '+String(d.u):'';
return RUN(S,(t,st,p)=>{const sp=cl(st(.4,1));const ang=amax*Math.sin(t*1.4)*sp;const c=Math.cos(ang),s=Math.sin(ang);
const lx=fx-Ll*c,ly=fy+Ll*s,ex=fx+Le*c,ey=fy-Le*s;
// podpera a zem
x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(fx,fy+8);x.lineTo(fx-46,fy+90);x.lineTo(fx+46,fy+90);x.closePath();x.stroke();S.ln(60,fy+90,804,fy+90,'rgba(255,255,255,.5)',2);
S.ln(lx,ly,ex,ey,'#fff',8);S.ci(fx,fy,8,null,0,A);
// bremeno
x.save();x.translate(lx+40*c,ly-40*s);x.rotate(-ang);S.rc(-40,-86,80,80,'#fff',4,'#000');x.restore();
// sila
const fa=st(.8,.6);x.globalAlpha=p*fa;const sx=ex-30*c,sy=ey+30*s*-1;S.ar(ex-20*c,ey+20*s-84,ex-20*c,ey+20*s-12,A,7);x.globalAlpha=p;
// kóty
const q=st(1.2,.7);x.globalAlpha=p*q;const yk=fy+112;[[x0,fx],[fx,x1]].forEach(([a,b])=>{S.ln(a,yk,b,yk,'#8a8a8a',2);S.ln(a,yk-8,a,yk+8,'#8a8a8a',2);S.ln(b,yk-8,b,yk+8,'#8a8a8a',2)});x.globalAlpha=p;
dl.style.left=(x0+fx)/2-80+'px';dl.style.width='160px';de.style.left=(fx+x1)/2-80+'px';de.style.width='160px';S.txt(dl,S.f1(al)+u,q);S.txt(de,S.f1(ae)+u,q);
S.txt(vL,'G',st(1,.6));S.txt(vE,k>=1?'G ÷ '+S.f1(k):'G × '+S.f1(1/k),st(1.6,.7));S.op(L0,st(.8,.6));S.op(L1,st(.5,.6));S.op(L2,st(.3,.6))})};

// ---------- kladkostroj: n = počet nosných lán → sila ÷ n, dráha × n ----------
MECH2.pulley=(v,d)=>{const S=M2(v,d),{x,A}=S;const nr=Math.round(S.nn(0,4,1,8));const sp0=Math.min(44,200/nr),bwid=nr*sp0+24,cx=320,lft=cx-bwid/2;
const L0=S.lab(0,cx-140,506,280),L2=S.lab(2,40,98,lft-60,'right',20),L1=S.lab(1,560,370,290,'left',22);
const vF=S.val(560,120,300,'left',52,A),vS=S.val(560,190,300,'left',34,'#bdbdbd');
return RUN(S,(t,st,p)=>{const sp=cl(st(.4,1));const ph=(1-Math.cos(t*1.3))/2*sp;const lift=150/nr*ph,pull=150*ph;const tb=70,bb=300-lift;
// strop
S.ln(60,40,520,40,'#fff',4);x.strokeStyle='rgba(255,255,255,.45)';x.lineWidth=2;for(let k=0;k<12;k++){x.beginPath();x.moveTo(70+k*38,40);x.lineTo(56+k*38,26);x.stroke()}S.ln(cx,40,cx,tb,'#fff',4);
// kladky (horné a dolné)
const xs=[...Array(nr)].map((_,i)=>lft+12+sp0/2+i*sp0);const rot=t*1.3*Math.sin(t*1.3)*.0+ph*6;
S.rc(lft,tb,bwid,34,'#fff',4,'#000');S.rc(lft,bb,bwid,34,'#fff',4,'#000');
for(let i=0;i<nr;i++){const top=i%2==0;const yy=top?tb+17:bb+17;S.ci(xs[i]+(top?sp0/2:-sp0/2)*0,yy,10,'#8a8a8a',2)}
// laná
for(let i=0;i<nr;i++)S.ln(xs[i],tb+34,xs[i],bb,i==nr-1?'#fff':'#fff',3);
const fx=lft+bwid+40;x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.moveTo(xs[nr-1],tb);x.quadraticCurveTo(xs[nr-1],tb-24,(xs[nr-1]+fx)/2,tb-20);x.quadraticCurveTo(fx,tb-20,fx,tb+10);x.lineTo(fx,250+pull);x.stroke();
// ťah
const fa=st(.8,.6);x.globalAlpha=p*fa;S.ar(fx,250+pull,fx,330+pull,A,7);x.globalAlpha=p;
// bremeno
S.ln(cx,bb+34,cx,bb+60,'#fff',4);S.rc(cx-70,bb+60,140,120,'#fff',4,'#000');x.fillStyle='#fff';x.font='800 40px sans-serif';x.textAlign='center';x.textBaseline='middle';x.globalAlpha=p*st(.8,.6);x.fillText('G',cx,bb+120);x.globalAlpha=p;
// číslovanie lán
x.globalAlpha=p*st(1,.6);x.font='800 17px sans-serif';for(let i=0;i<nr;i++){const yy=(tb+34+bb)/2;S.ci(xs[i],yy,12,A,2,'#000');x.fillStyle=A;x.fillText(String(i+1),xs[i],yy+1)}x.globalAlpha=p;
S.txt(vF,'F = G ÷ '+nr,st(1.3,.7));S.txt(vS,'s × '+nr,st(1.7,.6));S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.op(L2,st(.3,.6));S.mv(L1,fx+24,380+pull*.0)})};

// ---------- generátor: turbína točí cievku v magnetickom poli → prúd do žiarovky ----------
MECH2.generator=(v,d)=>{const S=M2(v,d),{x,A}=S;const hx=150,hy=230,gx=330,gw=250,gy=150,gh=160,bx=752,by=230;
const L0=S.lab(0,hx-140,470,280),L1=S.lab(1,gx+gw/2-150,470,300),L2=S.lab(2,bx-110,470,220);
const w1=S.path([[gx+gw,gy+50],[bx-40,gy+50],[bx-40,by+40]]),w2=S.path([[bx+40,by+40],[bx+40,gy+gh+60],[gx+gw,gy+gh+60],[gx+gw,gy+gh-30]]);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),a=t*2.2*sp+t*.0;
// turbína
S.ln(hx,hy,hx,440,'#fff',5);S.ln(hx-60,440,hx+60,440,'rgba(255,255,255,.5)',2);for(let k=0;k<3;k++){const b=a+k*2.094;x.save();x.translate(hx,hy);x.rotate(b);x.beginPath();x.moveTo(0,-8);x.quadraticCurveTo(30,-110,0,-130);x.quadraticCurveTo(-14,-80,0,-8);x.closePath();x.strokeStyle='#fff';x.lineWidth=4;x.fillStyle='#000';x.fill();x.stroke();x.restore()}S.ci(hx,hy,12,'#fff',4,A);
// hriadeľ
S.ln(hx+12,hy,gx+gw/2-60,hy,'#9a9a9a',8);
// magnety
S.rc(gx,gy,gw,gh,'#fff',4);S.rc(gx+20,gy+14,gw-40,30,null,0,A);S.rc(gx+20,gy+gh-44,gw-40,30,null,0,'#d9d9d9');x.fillStyle='#000';x.font='800 24px sans-serif';x.textAlign='center';x.textBaseline='middle';x.fillText('N',gx+gw/2,gy+30);x.fillText('S',gx+gw/2,gy+gh-29);
// siločiary
x.strokeStyle='rgba(255,255,255,.25)';x.lineWidth=2;x.setLineDash([4,8]);x.lineDashOffset=-t*10;for(let k=0;k<5;k++){const X=gx+40+k*(gw-80)/4;x.beginPath();x.moveTo(X,gy+48);x.lineTo(X,gy+gh-48);x.stroke()}x.setLineDash([]);
// cievka (otáčajúca sa slučka)
const cw=Math.cos(a*1.0)*90;x.strokeStyle='#fff';x.lineWidth=5;x.strokeRect(gx+gw/2-Math.abs(cw),hy-34,Math.max(2,Math.abs(cw)*2),68);if(Math.abs(cw)>4){x.strokeStyle=cw>0?A:'#8a8a8a';x.beginPath();x.moveTo(gx+gw/2-cw,hy-34);x.lineTo(gx+gw/2-cw,hy+34);x.stroke()}
// vodiče a prúd
const on=st(1,.8);w1.draw('#fff',3);w2.draw('#fff',3);
x.globalAlpha=p*on;S.flow(w1,6,t*.5,6,A);S.flow(w2,9,t*.5,6,A);x.globalAlpha=p;
S.bulb(bx,by,40,on*(.75+.25*Math.abs(Math.sin(a))));S.op(L0,st(.2,.6));S.op(L1,st(.6,.6));S.op(L2,st(1.1,.6))})};

// ---------- elektromotor: prúd v cievke medzi magnetmi → otáčanie ----------
MECH2.motor=(v,d)=>{const S=M2(v,d),{x,A}=S;const cx=432,cy=230;
const L0=S.lab(0,20,90,260),L1=S.lab(1,cx-130,30,260),L2=S.lab(2,560,474,300,'left',22);
const wl=S.path([[cx-14,392],[cx-14,440],[cx-120,440],[cx-120,500],[cx-40,500]]),wr=S.path([[cx+40,500],[cx+120,500],[cx+120,440],[cx+14,440],[cx+14,392]]);
return RUN(S,(t,st,p)=>{const sp=cl(st(.4,1)),a=t*2.4*sp;
// magnety
S.rc(130,130,90,200,'#fff',4,'#000');S.rc(644,130,90,200,'#fff',4,'#000');x.fillStyle=A;x.globalAlpha=p*.85;x.fillRect(134,134,82,192);x.globalAlpha=p;x.fillStyle='#000';x.font='800 48px sans-serif';x.textAlign='center';x.textBaseline='middle';x.fillText('N',175,230);x.fillStyle='#fff';x.fillText('S',689,230);
x.strokeStyle='rgba(255,255,255,.22)';x.lineWidth=2;x.setLineDash([4,10]);x.lineDashOffset=-t*14;for(let k=0;k<5;k++){const Y=150+k*40;x.beginPath();x.moveTo(224,Y);x.lineTo(640,Y);x.stroke()}x.setLineDash([]);
// cievka
const w=Math.cos(a)*170;const lft=cx-Math.abs(w);S.rc(lft,cy-90,Math.max(3,Math.abs(w)*2),180,'#fff',5);if(Math.abs(w)>6){S.ln(cx-w,cy-90,cx-w,cy+90,A,6);S.ln(cx+w,cy-90,cx+w,cy+90,'#8a8a8a',6)}
// sily na strany cievky
const fa=st(.9,.6);x.globalAlpha=p*fa*cl(Math.abs(w)/60);if(Math.abs(w)>30){S.ar(cx-w,cy,cx-w,cy+(w>0?70:-70),A,5);S.ar(cx+w,cy,cx+w,cy+(w>0?-70:70),'#bdbdbd',5)}x.globalAlpha=p;
// hriadeľ, komutátor, batéria
S.ln(cx,cy+90,cx,392,'#9a9a9a',8);S.rc(cx-26,360,52,32,'#fff',3,'#000');S.ln(cx,360,cx,392,'#fff',2);
S.ln(cx-40,486,cx-40,514,'#fff',4);S.ln(cx-26,494,cx-26,506,'#fff',4);S.ln(cx+26,486,cx+26,514,'#fff',4);S.ln(cx+40,494,cx+40,506,'#fff',4);x.fillStyle='#bdbdbd';x.font='700 20px sans-serif';x.fillText('+',cx-40,472);x.fillText('−',cx+40,472);
wl.draw('#fff',3);wr.draw('#fff',3);const on=st(.6,.6);x.globalAlpha=p*on;S.flow(wl,4,t*.6,6,A);S.flow(wr,4,t*.6,6,A);x.globalAlpha=p;
// smer otáčania
x.globalAlpha=p*sp;x.strokeStyle=A;x.lineWidth=4;x.beginPath();x.ellipse(cx,cy+112,74,14,0,Math.PI*.12,Math.PI*.88);x.stroke();{const ex=cx+74*Math.cos(Math.PI*.12),ey=cy+112+14*Math.sin(Math.PI*.12);x.beginPath();x.moveTo(ex+4,ey+14);x.lineTo(ex,ey);x.lineTo(ex+15,ey-4);x.stroke()}x.globalAlpha=p;
S.op(L0,st(.2,.6));S.op(L1,st(.5,.6));S.op(L2,st(.7,.6))})};

// ---------- transformátor: n=[závity 1, závity 2, napätie 1] → napätie 2 ----------
MECH2.transformer=(v,d)=>{const S=M2(v,d),{x,A}=S;const n1=Math.round(S.nn(0,500,1,1e6)),n2=Math.round(S.nn(1,50,1,1e6)),u1=S.nn(2,230,.001,1e7);const u2=u1*n2/n1;const mx=Math.max(n1,n2);
const t1=Math.max(2,Math.round(12*n1/mx)),t2=Math.max(2,Math.round(12*n2/mx));const ox=262,oy=110,ow=340,oh=250,th=44;
const L0=S.lab(0,10,40,260),L2=S.lab(2,302,40,260),L1=S.lab(1,594,40,260);
const vU1=S.val(20,488,300,'center',46),vU2=S.val(544,488,300,'center',46,A),vN1=S.val(20,452,300,'center',22,'#8a8a8a'),vN2=S.val(544,452,300,'center',22,'#8a8a8a');
const core=S.path([[ox+th/2,oy+th/2],[ox+ow-th/2,oy+th/2],[ox+ow-th/2,oy+oh-th/2],[ox+th/2,oy+oh-th/2]],true);const fu=u=>u>=1000?NF(u/1000,u>=1e5?0:1)+' kV':S.f1(u)+' V';
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));
// jadro
S.rc(ox,oy,ow,oh,'#fff',4);S.rc(ox+th,oy+th,ow-2*th,oh-2*th,'#fff',4);x.globalAlpha=p*sp*.8;S.flow(core,14,t*.18,4,A);x.globalAlpha=p;
// cievky
const coil=(X,cnt,col,q)=>{const y0=oy+th+12,y1=oy+oh-th-12,dy=(y1-y0)/cnt;x.strokeStyle=col;x.lineWidth=4;x.globalAlpha=p*q;for(let i=0;i<cnt;i++){x.beginPath();x.ellipse(X,y0+dy*(i+.5),th/2+14,Math.min(9,dy*.45),0,0,6.3);x.stroke()}x.globalAlpha=p;return [y0,y1]};
const q1=st(.5,.6),q2=st(.9,.6);const c1=coil(ox+th/2,t1,'#fff',q1),c2=coil(ox+ow-th/2,t2,A,q2);
x.globalAlpha=p*q1;S.ln(ox-2,c1[0],60,c1[0],'#fff',3);S.ln(ox-2,c1[1],60,c1[1],'#fff',3);S.ci(60,c1[0],6,'#fff',3,'#000');S.ci(60,c1[1],6,'#fff',3,'#000');
x.globalAlpha=p*q2;S.ln(ox+ow+2,c2[0],804,c2[0],A,3);S.ln(ox+ow+2,c2[1],804,c2[1],A,3);S.ci(804,c2[0],6,A,3,'#000');S.ci(804,c2[1],6,A,3,'#000');x.globalAlpha=p;
// striedavé napätie (amplitúda podľa pomeru)
const am1=u1>=u2?34:Math.max(5,34*u1/u2),am2=u2>=u1?34:Math.max(5,34*u2/u1);
const wave=(X0,col,am,q)=>{x.globalAlpha=p*q;x.strokeStyle='rgba(255,255,255,.3)';x.lineWidth=2;x.beginPath();x.moveTo(X0,410);x.lineTo(X0+220,410);x.stroke();x.strokeStyle=col;x.lineWidth=4;x.beginPath();for(let X=0;X<=220;X+=4){const Y=410-am*Math.sin(X/220*Math.PI*4-t*5);X?x.lineTo(X0+X,Y):x.moveTo(X0+X,Y)}x.stroke();x.globalAlpha=p};
wave(60,'#fff',am1,q1);wave(584,A,am2,q2);
S.txt(vU1,fu(u1),q1);S.txt(vN1,'N₁ = '+NF(n1,0),q1);S.txt(vU2,fu(u2),st(1.4,.7));S.txt(vN2,'N₂ = '+NF(n2,0),q2);S.op(L0,q1);S.op(L1,q2);S.op(L2,st(.3,.6))})};

// ---------- viacstupňová raketa: oddelenie stupňov, výfukové plyny ----------
MECH2.rocket=(v,d)=>{const S=M2(v,d),{x,A}=S;const cx=360,K=1.18,Y=(y)=>y*K-6;
const L2=S.lab(2,cx+80,Y(82)-14,320,'left',22),L1=S.lab(1,cx+80,Y(182)-14,320,'left',22),L0=S.lab(0,cx+80,0,320,'left',22);
const stars=[...Array(26)].map((_,i)=>[(i*197)%864,(i*331)%560,i%3]);
const flame=(y,w,len,t)=>{for(let k=0;k<3;k++){const l=len*(.75+.25*Math.sin(t*25+k*2))*(1-k*.28);x.fillStyle=k==0?A:k==1?'#ffd9b0':'#fff';x.beginPath();x.moveTo(-w*(1-k*.3),y);x.quadraticCurveTo(0,y+l*1.25,w*(1-k*.3),y);x.closePath();x.fill()}};
return RUN(S,(t,st,p)=>{const sep=st(2,2),sp=cl(st(.3,1));const shake=Math.sin(t*40)*1.2*sp;
// pohyb: hviezdy/čiary letia dole
stars.forEach(s=>{const y=(s[1]+t*(80+s[2]*60)*sp)%560;x.globalAlpha=x.globalAlpha;x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;x.beginPath();x.moveTo(s[0],y);x.lineTo(s[0],y+12+s[2]*10);x.stroke()});
// 1. stupeň (po oddelení padá a otáča sa)
const lin=1-Math.cbrt(1-cl(sep)),fall=lin*lin;x.save();x.translate(cx-90*fall+shake,Y(330)+200*fall);x.scale(K,K);x.rotate(-.5*fall);const g=x.globalAlpha;x.globalAlpha=g*(1-cl((lin-.75)/.25));
if(sep<.05)flame(108,30,90+20*Math.sin(t*9),t);S.rc(-40,-96,80,200,'#fff',4,'#000');S.ln(-40,-56,40,-56,'rgba(255,255,255,.35)',2);x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(-40,60);x.lineTo(-66,108);x.lineTo(-40,104);x.moveTo(40,60);x.lineTo(66,108);x.lineTo(40,104);x.stroke();S.rc(-24,104,48,10,'#fff',3,'#000');x.restore();
// 2. stupeň + náklad
x.save();x.translate(cx+shake,-6);x.scale(K,K);const g2=x.globalAlpha;if(sep>.15){x.globalAlpha=g2*cl((sep-.15)/.2);flame(234,22,70+15*Math.sin(t*11),t);x.globalAlpha=g2}
S.rc(-30,110,60,116,'#fff',4,'#000');S.rc(-16,226,32,8,'#fff',3,'#000');x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(-30,110);x.lineTo(-30,70);x.quadraticCurveTo(-26,30,0,12);x.quadraticCurveTo(26,30,30,70);x.lineTo(30,110);x.closePath();x.fillStyle='#000';x.fill();x.stroke();S.ci(0,72,9,null,0,A);x.restore();
// čiarky k popiskom
x.globalAlpha=p*.5;S.ln(cx+42,Y(82),cx+70,Y(82),'#fff',2);S.ln(cx+42,Y(182),cx+70,Y(182),'#fff',2);x.globalAlpha=p*(1-cl(lin*3));S.ln(cx+52,Y(342),cx+70,Y(342),'#fff',2);x.globalAlpha=p;
S.op(L2,st(.3,.6));S.op(L1,st(.5,.6));if(L0){L0.style.opacity=cl(st(.7,.6))*(1-cl(lin*3));L0.style.top=(Y(342)-14+200*fall)+'px'}})};

// ---------- ponorka: balastné nádrže sa plnia → klesá, vyfúknutie → stúpa ----------
MECH2.submarine=(v,d)=>{const S=M2(v,d),{x,A}=S;const maxD=S.nn(0,300,1,12000);
const L0=S.lab(0,0,0,200,'center',22),L1=S.lab(1,10,500,260,'left',20),L2=S.lab(2,0,0,200,'center',20,A);const vD=S.val(600,0,172,'right',30,A);
const bub=[...Array(14)].map((_,i)=>[(i*37)%60-30,(i*53)%100/100]);
return RUN(S,(t,st,p)=>{const T=Math.max(0,t-.5),c=(T/10)%1;const sp=cl(st(.3,1));
const fill=c<.25?c/.25:c<.5?1:c<.7?1-(c-.5)/.2:0;const sm=z=>{z=cl(z);return z*z*(3-2*z)};const dep=(c<.5?sm((c-.1)/.38):1-sm((c-.5)/.42))*sp;
const sy=118+dep*262,sx=400;
// voda
x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();for(let X=20;X<=844;X+=6){const Y=90+4*Math.sin(X/40+t*2);X==20?x.moveTo(X,Y):x.lineTo(X,Y)}x.stroke();x.fillStyle='rgba(255,255,255,.04)';x.fillRect(20,94,824,446);
S.ln(20,540,844,540,'rgba(255,255,255,.4)',2);
// hĺbkomer
S.ln(800,94,800,520,'rgba(255,255,255,.35)',2);for(let k=0;k<=4;k++)S.ln(792,100+k*100,808,100+k*100,'rgba(255,255,255,.35)',2);S.ar(780,sy,796,sy,A,4,10);vD.style.top=(sy-16)+'px';S.txt(vD,'−'+NF(Math.round(dep*maxD),0)+' m',sp);
// trup
x.save();x.translate(sx,sy);x.strokeStyle='#fff';x.lineWidth=4;x.fillStyle='#000';x.beginPath();x.ellipse(0,0,190,44,0,0,6.3);x.fill();x.stroke();
x.beginPath();x.moveTo(-40,-42);x.lineTo(-30,-86);x.lineTo(30,-86);x.lineTo(44,-42);x.stroke();S.ln(0,-86,0,-110,'#fff',3);
x.beginPath();x.moveTo(190,0);x.lineTo(222,-26);x.lineTo(222,26);x.closePath();x.stroke();
// nádrže
[[-150,-70],[70,150]].forEach(([a,b])=>{x.strokeStyle='#fff';x.lineWidth=3;x.strokeRect(a,-24,b-a,48);x.fillStyle=A;x.globalAlpha=p*.85;x.fillRect(a+2,24-46*fill,b-a-4,46*fill-2);x.globalAlpha=p;if(fill<.98&&fill>0){S.ln(a+2,24-46*fill,b-2,24-46*fill,'#fff',2)}});
x.restore();
// voda dnu / vzduch von
if(c<.25){x.globalAlpha=p*sp;[-110,110].forEach(X=>{S.ar(sx+X,sy+90,sx+X,sy+50,'#bdbdbd',3,10)});x.globalAlpha=p}
let ba=0;if(c>=.5&&c<.75){ba=sp;bub.forEach(b=>{[-110,110].forEach(X=>{const u=(b[1]+t*.9)%1;S.ci(sx+X+b[0]*.6,sy-30-u*130,4+b[1]*5,'#fff',2);})})}
if(L0){L0.style.left=(sx-100)+'px';L0.style.top=(sy+94)+'px';L0.style.opacity=st(.5,.6)}if(L2){L2.style.left=(sx+130)+'px';L2.style.top=(sy-130)+'px';L2.style.opacity=ba*cl(sy-170>90?1:0)}S.op(L1,st(.7,.6))})};

// ---------- výťah: kabína a protiváha na lane cez kladku ----------
MECH2.elevator=(v,d)=>{const S=M2(v,d),{x,A}=S;const sc=432,R=60,sh=80,xc=sc-R,xw=sc+R;const m1=N(S.n[0]),m2=N(S.n[1]);
const L0=S.lab(0,0,0,250,'right',22),L1=S.lab(1,600,0,250,'left',22),L2=S.lab(2,600,30,250,'left',20);
const vM0=S.val(0,0,250,'right',28,'#8a8a8a'),vM1=S.val(600,0,250,'left',28,'#8a8a8a');
return RUN(S,(t,st,p)=>{const sp=cl(st(.4,1));const u=Math.sin(t*.9-1)*sp;const yc=270-u*110,yw=270+u*110;
// šachta
S.ln(270,150,270,540,'rgba(255,255,255,.5)',3);S.ln(560,150,560,540,'rgba(255,255,255,.5)',3);S.ln(260,540,570,540,'rgba(255,255,255,.5)',3);S.rc(270,20,290,130,'rgba(255,255,255,.5)',3);
// motor + kladka
S.rc(sc+R+24,sh-26,62,52,'#fff',4,'#000');S.ln(sc,sh,sc+R+24,sh,'#9a9a9a',6);S.ci(sc,sh,R,'#fff',4,'#000');const a=-u*3;for(let k=0;k<3;k++){const b=a+k*2.094;S.ln(sc,sh,sc+Math.cos(b)*R*.85,sh+Math.sin(b)*R*.85,'#8a8a8a',3)}S.ci(sc,sh,8,null,0,A);
x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.moveTo(xc,yc);x.lineTo(xc,sh);x.arc(sc,sh,R,Math.PI,0);x.lineTo(xw,yw);x.stroke();
// kabína
S.rc(xc-75,yc,150,120,'#fff',4,'#000');x.fillStyle=A;x.globalAlpha=p*.25;x.fillRect(xc-71,yc+4,142,112);x.globalAlpha=p;
// protiváha
S.rc(xw-22,yw,44,110,'#fff',4,'#000');for(let k=1;k<5;k++)S.ln(xw-22,yw+k*22,xw+22,yw+k*22,'rgba(255,255,255,.4)',2);
// smer
x.globalAlpha=p*sp;const dv=Math.cos(t*.9-1);if(Math.abs(dv)>.15){S.ar(xc,yc+60+dv*15,xc,yc+60-dv*15,'#fff',4,10);S.ar(xw+50,yw+55+dv*20,xw+50,yw+55+dv*50,'#bdbdbd',4,10)}x.globalAlpha=p;
S.mv(L0,0,yc+20);S.mv(vM0,0,yc+70);S.mv(L1,600,yw+20);S.mv(vM1,600,yw+70);S.mv(L2,sc+R+100,sh-14);
S.op(L0,st(.3,.6));S.op(L1,st(.6,.6));S.op(L2,st(.8,.6));S.txt(vM0,m1?NF(m1,0)+' kg':'',st(1,.6));S.txt(vM1,m2?NF(m2,0)+' kg':'',st(1.2,.6))})};

// ---------- šikmý vrh: n=[rýchlosť m/s, uhol °] → dolet, výška, čas ----------
MECH2.trajectory=(v,d)=>{const S=M2(v,d),{x,A}=S;const v0=S.nn(0,30,.5,8000),th=S.nn(1,45,3,87)*Math.PI/180,g=9.81;
const R=v0*v0*Math.sin(2*th)/g,H=v0*v0*Math.sin(th)**2/(2*g),T=2*v0*Math.sin(th)/g;
const X0=90,Y0=430,sc=Math.min(640/R,280/H),Rx=R*sc,Hy=H*sc;const fm=m=>m>=10000?NF(m/1000,m>=1e5?0:1)+' km':S.f1(m)+' m';const fs=s=>s>=600?NF(s/60,1)+' min':S.f1(s)+' s';
const lbl=(i,def)=>(S.L[i]&&S.L[i].trim()?S.L[i]:def);
const vR=S.val(X0+Rx/2-200,492,400,'center',40,A),vH=S.val(0,0,330,'left',32),vT=S.val(574,20,280,'right',32,'#bdbdbd'),vV=S.val(X0+4,0,240,'left',24,'#bdbdbd');
const pR=el('div','lab',`left:${X0+Rx/2-200}px;top:460px;width:400px;text-align:center;font-size:18px;opacity:0`,esc(lbl(0,'R'))),pH=el('div','lab',`left:0;top:0;width:330px;font-size:18px;opacity:0`,esc(lbl(1,'H'))),pT=el('div','lab',`left:574px;top:58px;width:280px;text-align:right;font-size:18px;opacity:0`,esc(lbl(2,'t')));v.append(pR,pH,pT);[pR,pH,pT].forEach(e=>fit(e,18,12,26,e===pR?400:e===pH?330:280));
const apx=X0+Rx/2,apy=Y0-Hy;const hw=Math.max(120,Math.min(220,Rx*.36));pH.style.width=hw+'px';vH.style.width=hw+'px';fit(pH,18,11,26,hw);pH.style.left=(apx+14)+'px';vH.style.left=(apx+14)+'px';pH.style.top=(Y0-Hy*.45)+'px';vH.style.top=(Y0-Hy*.45+24)+'px';
if(Hy<150){pH.style.left=(apx-hw/2)+'px';vH.style.left=(apx-hw/2)+'px';pH.style.textAlign='center';vH.style.textAlign='center';pH.style.top=(apy-72)+'px';vH.style.top=(apy-48)+'px'}
return RUN(S,(t,st,p)=>{const sp=cl(st(.4,.6));
S.ln(50,Y0,830,Y0,'#fff',3);x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=2;for(let k=0;k<20;k++){x.beginPath();x.moveTo(60+k*40,Y0);x.lineTo(48+k*40,Y0+12);x.stroke()}
// celá dráha (prerušovaná) + prejdená časť
const pos=u=>[X0+Rx*u,Y0-4*Hy*u*(1-u)];x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;x.setLineDash([6,8]);x.beginPath();for(let k=0;k<=60;k++){const q=pos(k/60);k?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.stroke();x.setLineDash([]);
const tt=Math.max(0,t-1.2),u=cl((tt%4.6)/3.4)*sp;x.strokeStyle=A;x.lineWidth=5;x.beginPath();for(let k=0;k<=60;k++){const q=pos(u*k/60);k?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.stroke();const b=pos(u);S.ci(b[0],b[1],11,null,0,'#fff');
// vektor rýchlosti a uhol
const va=st(.6,.6);x.globalAlpha=p*va;const vl=Math.min(130,Math.max(60,Hy*.6));S.ar(X0,Y0,X0+vl*Math.cos(th),Y0-vl*Math.sin(th),'#fff',4);x.strokeStyle='#bdbdbd';x.lineWidth=2;x.beginPath();x.arc(X0,Y0,46,-th,0);x.stroke();x.fillStyle='#bdbdbd';x.font='700 18px sans-serif';x.textAlign='left';x.textBaseline='middle';x.textAlign='right';x.fillText(Math.round(th*180/Math.PI)+'°',X0-12,Y0-14);x.globalAlpha=p;
vV.style.top=(th<.5?Y0-vl*Math.sin(th)-40:Y0-vl*Math.sin(th)*.5-14)+'px';vV.style.left=(X0+vl*Math.cos(th)+14)+'px';S.txt(vV,S.f1(v0)+' m/s',va);
// kóty
const q1=st(1.2,.7),q2=st(1.6,.7),q3=st(2,.7);x.globalAlpha=p*q1;S.ar(X0+Rx/2,Y0+26,X0+6,Y0+26,'#bdbdbd',2,10);S.ar(X0+Rx/2,Y0+26,X0+Rx-6,Y0+26,'#bdbdbd',2,10);x.globalAlpha=p*q2;x.setLineDash([4,6]);S.ln(apx,Y0,apx,apy,'#bdbdbd',2);x.setLineDash([]);x.globalAlpha=p;
S.txt(vR,fm(R),q1);S.op(pR,q1);S.txt(vH,fm(H),q2);S.op(pH,q2);S.txt(vT,fs(T),q3);S.op(pT,q3)})};

// ---------- štiepenie jadra: reťazová reakcia neutrónov ----------
MECH2.fission=(v,d)=>{const S=M2(v,d),{x,A}=S;
const g0=[[190,280]],g1=[[440,96],[440,280],[440,464]],g2=[50,142,234,326,418,510].map(y=>[700,y]);
const L0=S.lab(0,20,206,200,'left',20),L1=S.lab(1,90,334,200,'center',20),L2=S.lab(2,20,420,300,'left',22,A);const vC=S.val(20,456,320,'left',40,A);
const nuc=(cx,cy,r,w)=>{x.save();x.translate(cx+Math.sin(w*30)*1.2,cy);S.ci(0,0,r,'#fff',3,'#000');for(let k=0;k<7;k++){const a=k*2.4,rr=r*.55*Math.sqrt((k+1)/7);S.dot(Math.cos(a)*rr,Math.sin(a)*rr,r*.2,k%2?'#8a8a8a':A)}x.restore()};
const split=(c,q,t,targets,emit)=>{if(q<=0){nuc(c[0],c[1],30,t+c[1]);return}const o=E(q);
// záblesk energie
const fl=Math.sin(cl(q*1.2)*Math.PI);if(fl>0){const g=x.createRadialGradient(c[0],c[1],0,c[0],c[1],70);g.addColorStop(0,A);g.addColorStop(1,'rgba(0,0,0,0)');const ga=x.globalAlpha;x.globalAlpha=ga*fl;x.fillStyle=g;x.beginPath();x.arc(c[0],c[1],70,0,6.3);x.fill();x.globalAlpha=ga}
const ga=x.globalAlpha;x.globalAlpha=ga*(1-.5*o);S.ci(c[0]-4-o*26,c[1]-4-o*22,16,'#bdbdbd',3,'#000');S.ci(c[0]+4+o*26,c[1]+4+o*22,14,'#bdbdbd',3,'#000');x.globalAlpha=ga};
const neut=(a,b,q)=>{if(q<=0||q>=1)return;const X=a[0]+(b[0]-a[0])*q,Y=a[1]+(b[1]-a[1])*q;const ang=Math.atan2(b[1]-a[1],b[0]-a[0]);const ga=x.globalAlpha;x.globalAlpha=ga*.4;S.ln(X-Math.cos(ang)*26,Y-Math.sin(ang)*26,X,Y,'#fff',3);x.globalAlpha=ga;S.dot(X,Y,7,'#fff')};
return RUN(S,(t,st,p)=>{const qin=st(.2,.8),s0=st(1,.8),qn1=st(1.4,1),s1=st(2.5,.8),qn2=st(2.9,1),s2=st(4,.8);
neut([20,280],[160,280],qin);
const P=x.globalAlpha;
split(g0[0],s0,t,g1);x.globalAlpha=P;
g1.forEach(c=>{x.globalAlpha=P;neut(g0[0],[c[0]-30,c[1]],qn1)});
g1.forEach((c,i)=>{x.globalAlpha=P;split(c,s1,t)});
g1.forEach((c,i)=>{x.globalAlpha=P;neut(c,[g2[i*2][0]-28,g2[i*2][1]],qn2);neut(c,[g2[i*2+1][0]-28,g2[i*2+1][1]],qn2)});
g2.forEach(c=>{x.globalAlpha=P;split(c,s2,t)});x.globalAlpha=P;
// po poslednom štiepení: ďalšie neutróny letia ďalej
if(s2>0){g2.forEach((c,i)=>{for(let k=0;k<2;k++){const u=((t*.6+k*.5+i*.13)%1);x.globalAlpha=P*s2*(1-u);S.dot(c[0]+40+u*150,c[1]+(k?-1:1)*u*30,6,'#fff')}});x.globalAlpha=P}
S.op(L0,st(.3,.5));S.op(L1,st(.5,.5));S.op(L2,st(1,.6));S.txt(vC,s2>.2?'1 → 3 → 6':s1>.2?'1 → 3':'1',st(1,.6))})};

// ---------- elektrický obvod: batéria → spínač → žiarovka, n=[U volt, R ohm] → prúd ----------
MECH2.circuit=(v,d)=>{const S=M2(v,d),{x,A}=S;const U=S.nn(0,9,.001,1e6),Ro=S.nn(1,18,.001,1e9),I=U/Ro;const has=N(S.n[0])&&N(S.n[1]);
const l=150,r=714,tp=110,bt=450,by=280,sx=400;
const L0=S.lab(0,l+52,by-32,230,'left',22),L1=S.lab(1,sx-85,36,260,'center',22),L2=S.lab(2,r-316,by-32,226,'right',22);
const vU=S.val(l+52,by+4,230,'left',32,'#bdbdbd'),vR=S.val(r-316,by+4,226,'right',32,'#bdbdbd'),vI=S.val(232,370,400,'center',50,A);
const loop=S.path([[l,by-30],[l,tp],[sx,tp],[sx+90,tp],[r,tp],[r,by-46],[r,by+46],[r,bt],[l,bt],[l,by+30]]);
const fI=I>=1?S.f1(I)+' A':I>=.001?S.f1(I*1000)+' mA':S.f1(I*1e6)+' µA';
return RUN(S,(t,st,p)=>{const on=st(1,.5);
x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.moveTo(l,by-30);x.lineTo(l,tp);x.lineTo(sx,tp);x.moveTo(sx+90,tp);x.lineTo(r,tp);x.lineTo(r,by-46);x.moveTo(r,by+46);x.lineTo(r,bt);x.lineTo(l,bt);x.lineTo(l,by+30);x.stroke();
// batéria
S.ln(l-36,by-12,l+36,by-12,'#fff',5);S.ln(l-18,by+12,l+18,by+12,'#fff',9);S.ln(l,by-30,l,by-12,'#fff',4);S.ln(l,by+12,l,by+30,'#fff',4);x.fillStyle='#bdbdbd';x.font='700 22px sans-serif';x.textAlign='center';x.textBaseline='middle';x.fillText('+',l-52,by-16);x.fillText('−',l-52,by+14);
// spínač
const ang=(1-on)*.6;S.ci(sx,tp,6,'#fff',3,'#000');S.ci(sx+90,tp,6,'#fff',3,'#000');S.ln(sx,tp,sx+90*Math.cos(ang),tp-90*Math.sin(ang),on>.99?A:'#fff',5);
// žiarovka
S.bulb(r,by-6,40,cl((on-.9)/.1));
// prúd
if(on>.97){x.globalAlpha=p*cl((on-.97)/.03);S.flow(loop,22,t*.22,5,A);x.globalAlpha=p}
S.op(L0,st(.3,.6));S.op(L1,st(.5,.6));S.op(L2,st(.7,.6));if(has){S.txt(vU,S.f1(U)+' V',st(.3,.6));S.txt(vR,S.f1(Ro)+' Ω',st(.7,.6));S.txt(vI,'I = '+fI,st(1.5,.6))}})};

// ---------- rotor vrtuľníka: hlavný a chvostový rotor, reakčný moment ----------
MECH2.rotor=(v,d)=>{const S=M2(v,d),{x,A}=S;const cx=300,cy=290,Rr=210,tx=724,ty=290;
const L0=S.lab(0,4,8,300,'left',22),L1=S.lab(1,590,40,270,'center',22),L2=S.lab(2,cx-150,512,300,'center',20,'#bdbdbd');
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),a=-t*5*sp-.4;
// rotorový disk
x.globalAlpha=p*.5;S.ci(cx,cy,Rr,'rgba(255,255,255,.25)',2);x.globalAlpha=p;
// trup zhora
x.strokeStyle='#fff';x.lineWidth=4;x.fillStyle='#000';x.beginPath();x.ellipse(cx,cy,110,52,0,0,6.3);x.fill();x.stroke();x.beginPath();x.moveTo(cx+100,cy-14);x.lineTo(tx-20,cy-6);x.lineTo(tx-20,cy+6);x.lineTo(cx+100,cy+14);x.stroke();x.beginPath();x.ellipse(cx-62,cy,30,34,0,0,6.3);x.stroke();
S.ln(tx-60,cy-40,tx-40,cy,'#fff',3);S.ln(tx-60,cy+40,tx-40,cy,'#fff',3);
// chvostový rotor
const ta=t*14*sp;x.save();x.translate(tx,ty);S.ci(0,0,44,'rgba(255,255,255,.25)',2);for(let k=0;k<2;k++){const b=ta+k*Math.PI;S.ln(-Math.cos(b)*40,-Math.sin(b)*40,Math.cos(b)*40,Math.sin(b)*40,'#fff',5)}S.ci(0,0,6,null,0,A);x.restore();
// listy hlavného rotora
for(let k=0;k<4;k++){const b=a+k*Math.PI/2;x.save();x.translate(cx,cy);x.rotate(b);x.fillStyle='#fff';x.globalAlpha=p*.95;x.fillRect(12,-6,Rr-12,12);x.restore()}x.globalAlpha=p;S.ci(cx,cy,14,'#fff',3,A);
// smer otáčania rotora (proti smeru hodinových ručičiek)
const qa=st(.6,.6);x.globalAlpha=p*qa;x.strokeStyle=A;x.lineWidth=5;x.beginPath();x.arc(cx,cy,Rr+20,-2.6,-1.5);x.stroke();const e1=-2.6;x.beginPath();const px=cx+Math.cos(e1)*(Rr+20),py=cy+Math.sin(e1)*(Rr+20);x.moveTo(px+10,py-14);x.lineTo(px,py);x.lineTo(px+16,py+8);x.stroke();
// reakčný moment na trupe (v smere hodinových ručičiek)
const qm=st(1,.7);x.globalAlpha=p*qm;x.strokeStyle='#bdbdbd';x.lineWidth=5;x.beginPath();x.arc(cx,cy,150,1.0,2.2);x.stroke();const e2=2.2,qx=cx+Math.cos(e2)*150,qy=cy+Math.sin(e2)*150;x.beginPath();x.moveTo(qx+18,qy+2);x.lineTo(qx,qy);x.lineTo(qx+2,qy-18);x.stroke();
// ťah chvostového rotora ho vyrovná
const qt=st(1.5,.7);x.globalAlpha=p*qt;S.ar(tx,ty-56,tx,ty-56-60*qt-Math.sin(t*6)*4,A,7);x.globalAlpha=p;
S.op(L0,st(.4,.6));S.op(L1,st(1.5,.6));S.op(L2,st(1,.6))})};

// ---------- montážna linka: pás, stanice, krabice ----------
MECH2.conveyor=(v,d)=>{const S=M2(v,d),{x,A}=S;const SX=[220,432,644],by=380,sp0=212;
const LS=SX.map((X,i)=>S.lab(i,X-104,56,208,'center',20));const L3=S.lab(3,620,500,240,'right',20,A);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));const off=t*70*sp;
// pás a valce
S.ln(40,by,824,by,'#fff',4);S.ln(40,by+40,824,by+40,'#fff',4);x.strokeStyle='#fff';x.lineWidth=4;x.beginPath();x.arc(40,by+20,20,Math.PI/2,Math.PI*1.5);x.stroke();x.beginPath();x.arc(824,by+20,20,-Math.PI/2,Math.PI/2);x.stroke();
for(let k=0;k<9;k++){const X=60+k*94;S.ci(X,by+20,13,'#8a8a8a',2);const b=off/13;S.ln(X,by+20,X+Math.cos(b+k)*13,by+20+Math.sin(b+k)*13,'#8a8a8a',2)}
x.strokeStyle='rgba(255,255,255,.4)';x.lineWidth=2;for(let k=0;k<30;k++){const X=40+((k*30+off)%784);x.beginPath();x.moveTo(X,by-0);x.lineTo(X,by+5);x.stroke()}
S.ln(40,by+40,40,520,'rgba(255,255,255,.4)',3);S.ln(824,by+40,824,520,'rgba(255,255,255,.4)',3);
// krabice
const pos=[];for(let k=-1;k<5;k++){const X=((k*sp0+off)%(sp0*4))-60;pos.push(X)}
// stanice
SX.forEach((X,i)=>{const q=st(.3+i*.3,.6);x.globalAlpha=p*q;S.ln(X-80,by-4,X-80,140,'#fff',4);S.ln(X+80,by-4,X+80,140,'#fff',4);S.ln(X-90,140,X+90,140,'#fff',4);
let near=999;pos.forEach(b=>{const c=b+45;near=Math.min(near,Math.abs(c-X))});const dn=cl(1-near/55);const hy=190+dn*70;S.ln(X,140,X,hy,'#9a9a9a',8);S.rc(X-30,hy,60,22,'#fff',4,dn>.6?A:'#000');x.globalAlpha=p});
pos.forEach(b=>{if(b<-100||b>900)return;const c=b+45;const st1=c>SX[0]+10,st2=c>SX[1]+10,st3=c>SX[2]+10;x.save();x.beginPath();x.rect(42,0,780,560);x.clip();
S.rc(b,by-80,90,76,'#fff',4,st3?A:'#000');if(st1)S.ln(b+45,by-80,b+45,by-4,st3?'#000':'#8a8a8a',3);if(st2){S.ln(b-6,by-80,b+96,by-80,st3?'#000':'#fff',5);S.ln(b+30,by-92,b+60,by-92,'#fff',4)}x.restore()});
LS.forEach((e,i)=>S.op(e,st(.3+i*.3,.6)));S.op(L3,st(1.4,.6))})};

// ---------- solárny článok: fotóny vybíjajú elektróny, prúd tečie do spotrebiča ----------
MECH2.solar=(v,d)=>{const S=M2(v,d),{x,A}=S;const sx=110,sy=100,pl=200,pr=620,pt=270,pj=325,pb=420,bx=760,bby=330;
const L0=S.lab(0,180,20,300,'left',22,A),L1=S.lab(1,pl,452,pr-pl,'center',22),L2=S.lab(2,bx-100,452,200,'center',22);
const wire=S.path([[pr-60,pt-10],[pr-60,200],[bx,200],[bx,bby-46]]),wire2=S.path([[bx,bby+40],[bx,pb+5],[pr,pb+5]]);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),on=st(1,.8);
// slnko
S.ci(sx,sy,44,A,4,'#000');for(let k=0;k<10;k++){const a=k*Math.PI/5+t*.3;S.ln(sx+Math.cos(a)*56,sy+Math.sin(a)*56,sx+Math.cos(a)*74,sy+Math.sin(a)*74,A,4)}
// článok
S.rc(pl,pt,pr-pl,pj-pt,'#fff',4,'#000');S.rc(pl,pj,pr-pl,pb-pj,'#fff',4,'#000');x.setLineDash([6,6]);S.ln(pl,pj,pr,pj,A,3);x.setLineDash([]);S.rc(pl,pb,pr-pl,10,null,0,'#bdbdbd');
for(let k=0;k<6;k++)S.rc(pl+30+k*60,pt-10,12,10,null,0,'#bdbdbd');
x.fillStyle='#8a8a8a';x.font='800 26px sans-serif';x.textAlign='left';x.textBaseline='middle';x.fillText('n',pl+12,pt+20);x.fillText('p',pl+12,pj+35);
// fotóny
for(let k=0;k<6;k++){const u=((t*.45*sp+k/6)%1);const tx=pl+40+k*58,ty=pt-6;const X=sx+50+(tx-sx-50)*u,Y=sy+40+(ty-sy-40)*u;const ang=Math.atan2(ty-sy-40,tx-sx-50);x.globalAlpha=p*sp*Math.sin(u*Math.PI);x.strokeStyle=A;x.lineWidth=4;x.beginPath();for(let j=0;j<=24;j++){const s=j/24*50-50,w=Math.sin(j/24*Math.PI*4-t*20)*7;const px=X+Math.cos(ang)*s-Math.sin(ang)*w,py=Y+Math.sin(ang)*s+Math.cos(ang)*w;j?x.lineTo(px,py):x.moveTo(px,py)}x.stroke();
// elektrón vyrazený pri dopade
const e=((t*.45*sp+k/6+.0)%1);if(sp>.5){const q=((t*.45+k/6+.35)%1);if(q<.4){x.globalAlpha=p*on*(1-q/.4);S.dot(tx+6,pj-q/.4*(pj-pt-10),6,'#fff');S.ci(tx+6,pj+q/.4*(pb-pj-16),6,'#8a8a8a',2)}}}x.globalAlpha=p;
// vodiče, spotrebič
wire.draw('#fff',3);wire2.draw('#fff',3);x.globalAlpha=p*on;S.flow(wire,6,t*.35,5,'#fff');S.flow(wire2,6,t*.35,5,'#fff');x.globalAlpha=p;S.bulb(bx,bby-4,40,on);
S.op(L0,st(.3,.6));S.op(L1,st(.6,.6));S.op(L2,st(1.1,.6))})};

const _mech0=V.mech;V.mech=(v,d)=>MECH2[d&&d.m]?MECH2[d.m](v,d):_mech0(v,d);
}
