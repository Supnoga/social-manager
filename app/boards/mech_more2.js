// tretia sada hotových mechanizmov pre V.mech (d.m): tepelné čerpadlo / klimatizácia / chladnička, plavebná komora, priehrada,
// vežový žeriav, visutý most, razenie tunela, vrtná veža, eskalátor, veterná turbína, kotúčová brzda, diferenciál, vačkový hriadeľ,
// procesor, HDD vs SSD, optické vlákno, padák, reťazový prevod bicykla
{
const MECH3={};
const M3=(v,d)=>{const x=cv2(v,864,560),A=D.acc,L=(Array.isArray(d.l)?d.l:[]).map(s=>s==null?'':String(s));const n=Array.isArray(d.n)?d.n:(d.n!=null?[d.n]:[]);
const nn=(i,def,lo,hi)=>{const r=N(n[i]);return r>0?Math.max(lo,Math.min(hi,r)):def};
const lab=(i,l,t,w,al,fs,col,dflt)=>{const s=L[i]||dflt||'';if(!s.trim())return null;const e=el('div','lab',`left:${l}px;top:${t}px;width:${w}px;text-align:${al||'center'};font-size:${fs||22}px;opacity:0;${col?'color:'+col:''}`,esc(s));v.append(e);fit(e,fs||22,13,60,w);return e};
const val=(l,t,w,al,fs,col)=>{const e=el('div','big',`left:${l}px;top:${t}px;width:${w}px;text-align:${al||'center'};font-size:${fs||44}px;opacity:0;white-space:nowrap;color:${col||'#fff'}`,'');v.append(e);return e};
const txt=(e,s,p)=>{if(!e)return;if(s!=null&&e.textContent!==s){e.textContent=s;const w=parseFloat(e.style.width);if(w)fit(e,parseFloat(e.dataset.fs||e.style.fontSize),16,80,w)}e.style.opacity=cl(p)};
const op=(e,p)=>{if(e)e.style.opacity=cl(p)};
const mv=(e,l,t)=>{if(e){e.style.left=l+'px';e.style.top=t+'px'}};
const ln=(x1,y1,x2,y2,c,w)=>{x.strokeStyle=c||'#fff';x.lineWidth=w||4;x.beginPath();x.moveTo(x1,y1);x.lineTo(x2,y2);x.stroke()};
const pl=(P,c,w,close,f)=>{x.beginPath();P.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));if(close)x.closePath();if(f){x.fillStyle=f;x.fill()}if(c){x.strokeStyle=c;x.lineWidth=w||4;x.stroke()}};
const ar=(x1,y1,x2,y2,c,w,h)=>{ln(x1,y1,x2,y2,c,w);const a=Math.atan2(y2-y1,x2-x1),hs=h||(12+(w||4)*1.5);x.beginPath();x.moveTo(x2-hs*Math.cos(a-.5),y2-hs*Math.sin(a-.5));x.lineTo(x2,y2);x.lineTo(x2-hs*Math.cos(a+.5),y2-hs*Math.sin(a+.5));x.stroke()};
const ci=(cx,cy,r,c,w,f)=>{x.beginPath();x.arc(cx,cy,Math.max(0,r),0,6.2832);if(f){x.fillStyle=f;x.fill()}if(c){x.strokeStyle=c;x.lineWidth=w||4;x.stroke()}};
const dot=(cx,cy,r,f)=>{x.fillStyle=f;x.beginPath();x.arc(cx,cy,r,0,6.2832);x.fill()};
const rc=(l,t,w,h,c,lw,f)=>{if(f){x.fillStyle=f;x.fillRect(l,t,w,h)}if(c){x.strokeStyle=c;x.lineWidth=lw||4;x.strokeRect(l,t,w,h)}};
const ct=(s,X,Y,fs,col,al,wt)=>{x.fillStyle=col||'#bdbdbd';x.font=`${wt||700} ${fs||18}px sans-serif`;x.textAlign=al||'center';x.textBaseline='middle';x.fillText(s,X,Y)};
const gear=(cx,cy,r,nT,rot,col,spk)=>{x.save();x.translate(cx,cy);x.rotate(rot);x.beginPath();for(let i=0;i<nT*2;i++){const a=i*Math.PI/nT,rr=i%2?r:r*(1+Math.min(.16,2.4/nT)),a2=a+Math.PI/nT,o=.72/nT;x.lineTo(Math.cos(a-o)*rr,Math.sin(a-o)*rr);x.lineTo(Math.cos(a2-o)*rr,Math.sin(a2-o)*rr)}x.closePath();x.fillStyle='#000';x.fill();x.strokeStyle=col;x.lineWidth=3;x.stroke();
x.lineWidth=3;x.beginPath();x.arc(0,0,r*.2,0,6.3);x.stroke();const k=spk||5;for(let j=0;j<k;j++){const a=j*Math.PI*2/k;x.beginPath();x.moveTo(Math.cos(a)*r*.2,Math.sin(a)*r*.2);x.lineTo(Math.cos(a)*r*.82,Math.sin(a)*r*.82);x.stroke()}x.restore()};
const path=(P,closed)=>{const pts=closed?P.concat([P[0]]):P;const seg=[];let tot=0;for(let i=1;i<pts.length;i++){const l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);seg.push(l);tot+=l}
return {tot,pts,at:(u)=>{let s=((u%1)+1)%1*tot;for(let i=0;i<seg.length;i++){if(s<=seg[i]||i==seg.length-1){const f=seg[i]?s/seg[i]:0;return [pts[i][0]+(pts[i+1][0]-pts[i][0])*f,pts[i][1]+(pts[i+1][1]-pts[i][1])*f]}s-=seg[i]}return pts[0]},
draw:(c,w)=>{x.strokeStyle=c||'#fff';x.lineWidth=w||4;x.beginPath();pts.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.stroke()}}};
const flow=(pp,cnt,u,r,f,a)=>{for(let k=0;k<cnt;k++){const q=pp.at(u+k/cnt);x.globalAlpha=(a==null?1:a);dot(q[0],q[1],r,f)}};
const wavy=(x1,y1,x2,y2,c,ph,amp)=>{const L=Math.hypot(x2-x1,y2-y1),a=Math.atan2(y2-y1,x2-x1),k=Math.max(8,L/4);x.strokeStyle=c;x.lineWidth=4;x.beginPath();for(let j=0;j<=k;j++){const s=j/k*L,w=Math.sin(s/9-ph)*(amp||6)*Math.min(1,(L-s)/14);const px=x1+Math.cos(a)*s-Math.sin(a)*w,py=y1+Math.sin(a)*s+Math.cos(a)*w;j?x.lineTo(px,py):x.moveTo(px,py)}x.stroke();
const hs=12;x.beginPath();x.moveTo(x2-hs*Math.cos(a-.55),y2-hs*Math.sin(a-.55));x.lineTo(x2,y2);x.lineTo(x2-hs*Math.cos(a+.55),y2-hs*Math.sin(a+.55));x.stroke()};
const kota=(x1,y1,x2,y2,c)=>{c=c||'#8a8a8a';ln(x1,y1,x2,y2,c,2);const a=Math.atan2(y2-y1,x2-x1),px=-Math.sin(a)*9,py=Math.cos(a)*9;ln(x1-px,y1-py,x1+px,y1+py,c,2);ln(x2-px,y2-py,x2+px,y2+py,c,2)};
const f1=(v)=>NF(v,Math.abs(v)>=100||Math.abs(v-Math.round(v))<.05?0:(Math.abs(v)>=1||Math.abs(v*10-Math.round(v*10))<.005)?1:2);
const big=(v,u)=>{const a=Math.abs(v);return a>=1e9?f1(v/1e9)+' G'+u:a>=1e6?f1(v/1e6)+' M'+u:a>=1e3?f1(v/1e3)+' k'+u:f1(v)+' '+u};
return {x,A,L,n,nn,lab,val,txt,op,mv,ln,pl,ar,ci,dot,rc,ct,gear,path,flow,wavy,kota,f1,big}};
const RUN=(S,fn)=>(t,st)=>{const p=E(st(0,1));S.x.clearRect(0,0,864,560);S.x.globalAlpha=1;S.x.save();S.x.globalAlpha=p;fn(t,st,p);S.x.restore()};
const has=(d,i)=>Array.isArray(d.n)?d.n[i]!=null&&N(d.n[i])>0:(i==0&&d.n!=null&&N(d.n)>0);
const HOUSE=(S,l,tp,r,b)=>{S.pl([[l,b],[l,tp],[(l+r)/2,tp-80],[r,tp],[r,b]],'#fff',4);S.ln(l-20,b,r+20,b,'rgba(255,255,255,.5)',2)};
const FRIDGE=(S,l,tp,r,b)=>{S.rc(l,tp,r-l,b-tp,'#fff',4,'#000');const mid=tp+(b-tp)*.34;S.ln(l,mid,r,mid,'#fff',3);S.ln(r-16,tp+26,r-16,mid-20,'#fff',6);S.ln(r-16,mid+22,r-16,mid+80,'#fff',6);S.ln(l,b,r,b,'#fff',4);S.ln(l+8,b,l+8,b+10,'#fff',4);S.ln(r-8,b,r-8,b+10,'#fff',4)};

// ---------- kompresorový obeh: tepelné čerpadlo (teplo dnu), klimatizácia a chladnička (teplo von) ----------
// n=[príkon kW, COP] → teplo / chlad; l=[vonku, kompresor, ventil, vnútri]
const CYC=(mode)=>(v,d)=>{const S=M3(v,d),{x,A}=S;const hp=mode=='hp';const kw=S.nn(0,mode=='fridge'?.1:1,.001,1e6),cop=S.nn(1,mode=='fridge'?2:hp?4:3.5,.5,20);const hasN=has(d,0)||has(d,1);
const Lx=250,Rx=520,T=150,B=430,cx=385,cy=290;const cc=[cx,T],vv=[cx,B];
const zig=(X,dir)=>{const P=[];for(let k=0;k<=8;k++)P.push([X+(k%2?22:-22)*(k&&k<8?1:0),dir>0?205+k*22.5:381-k*22.5]);return P};
// tepelné čerpadlo: horúca cievka vpravo (dnu), klimatizácia: horúca vľavo (von)
const hotX=hp?Rx:Lx,coldX=hp?Lx:Rx;
const hot=S.path([[cx+(hp?36:-36),T],[hotX,T],...zig(hotX,1),[hotX,B],[cx+(hp?18:-18),B]]),cold=S.path([[cx+(hp?-18:18),B],[coldX,B],...zig(coldX,-1),[coldX,T],[cx+(hp?-36:36),T]]);
const inR=mode!='hp'?true:true; // vnútro vždy vpravo
const L0=S.lab(0,10,96,210,'center',20,'#bdbdbd'),L1=S.lab(1,cx-150,30,300,'center',20),L2=S.lab(2,cx-170,480,340,'center',20),L3=S.lab(3,mode=='fridge'?630:644,mode=='fridge'?110:214,mode=='fridge'?190:180,'center',20,hp?A:'#bdbdbd');
const vIn=S.val(cx+46,T-64,160,'left',30,'#bdbdbd'),vH=S.val(mode=='fridge'?630:644,mode=='fridge'?304:270,mode=='fridge'?160:180,'center',mode=='fridge'?36:44,hp?A:'#fff'),vC=S.val(10,380,220,'center',36,hp?'#bdbdbd':A);
const qIn=kw*cop,heatOut=hp?qIn:kw*(cop+1),cool=hp?kw*(cop-1):qIn;
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),q=st(1,.7);
// dom / chladnička vpravo
x.globalAlpha=p*st(.2,.6);if(mode=='fridge')FRIDGE(S,612,150,820,470);else HOUSE(S,600,200,834,480);x.globalAlpha=p;
// potrubie a cievky
hot.draw(A,4);cold.draw('#bdbdbd',4);
// kompresor
S.ci(cc[0],cc[1],36,'#fff',4,'#000');x.save();x.translate(cc[0],cc[1]);x.rotate(t*4*sp);for(let k=0;k<3;k++){const a=k*2.094;S.ln(0,0,Math.cos(a)*24,Math.sin(a)*24,'#fff',3)}x.restore();
// expanzný ventil
x.fillStyle='#000';S.pl([[cx-20,B-14],[cx+20,B+14],[cx+20,B-14],[cx-20,B+14]],'#fff',4,true,'#000');S.ln(cx,B,cx,B-30,'#fff',3);S.ln(cx-12,B-30,cx+12,B-30,'#fff',3);
// chladivo
S.flow(hot,12,t*.22*sp,5.5,A,p*sp);S.flow(cold,12,t*.22*sp,5.5,'#e6e6e6',p*sp);x.globalAlpha=p;
// teplo: tepelné čerpadlo berie z vonkajšieho vzduchu a dáva dnu; klimatizácia berie zvnútra a dáva von
const ph=t*6;x.globalAlpha=p*q;
if(hp){for(let k=0;k<3;k++){const y=230+k*60;S.wavy(40,y,190,y,'#8a8a8a',ph+k);S.wavy(Rx+30,y,Rx+100,y,A,ph+k)}}
else{for(let k=0;k<3;k++){const y=230+k*60;S.wavy(Rx+104,y,Rx+36,y,'#8a8a8a',ph+k);S.wavy(Lx-40,y,Lx-190,y,A,ph+k)}}
x.globalAlpha=p;
// elektrina do kompresora
const qe=st(.7,.6);x.globalAlpha=p*qe;S.pl([[cx+2,T-44],[cx-8,T-60],[cx+6,T-62],[cx-4,T-78]],A,4);x.globalAlpha=p;
S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.op(L2,st(.8,.6));S.op(L3,st(.5,.6));
if(hasN){S.txt(vIn,S.big(kw*1000,'W'),qe);S.txt(vH,S.big((hp?heatOut:cool)*1000,'W'),q);S.txt(vC,S.big((hp?cool:heatOut)*1000,'W'),q)}
else{S.txt(vH,'',0);S.txt(vC,'',0)}})};
MECH3.heatpump=CYC('hp');MECH3.aircon=CYC('ac');MECH3.fridge=CYC('fridge');

// ---------- plavebná komora: loď vpláva, komora sa naplní, loď stúpne. n=[výška zdvihu m, dĺžka komory m, šírka m] ----------
MECH3.canal_lock=(v,d)=>{const S=M3(v,d),{x,A}=S;const h=S.nn(0,10,.5,200),Lc=S.nn(1,200,5,2000),Wc=S.nn(2,25,2,200);const vol=h*Lc*Wc;
const up=190,lo=330,bedU=400,bed=470,gl=262,gr=600;
const L0=S.lab(0,10,494,250,'center',20),L1=S.lab(1,gl+20,494,gr-gl-20,'center',20,A),L2=S.lab(2,610,494,250,'center',20);
const vV=S.val(232,24,400,'center',44,A),vH=S.val(690,224,100,'right',30);
const ship=(cx,wl)=>{x.save();x.translate(cx,wl);S.pl([[-96,-14],[96,-14],[80,22],[-84,22]],'#fff',4,true,'#000');S.rc(-70,-46,56,32,'#fff',3,'#000');S.rc(-10,-36,40,22,'#fff',3,'#000');S.rc(36,-30,30,16,'#fff',3,'#000');S.ln(-56,-46,-56,-70,'#fff',3);x.restore()};
const gate=(X,top,bot,open)=>{if(open>.5){x.save();x.setLineDash([6,6]);S.rc(X,top,18,bot-top,'rgba(255,255,255,.35)',2);x.restore()}else S.rc(X,top,18,bot-top,'#fff',3,'#d9d9d9')};
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,.6));
// časová os procesu
const T=t;const ein=cl((T-1)/1.6),gC=T>2.8,fill=EI(cl((T-3)/2.2)),gO=T>5.4,eout=EI(cl((T-5.8)/1.7));
const lvl=lo+(up-lo)*fill;
// voda
x.globalAlpha=p*.3;x.fillStyle=A;x.fillRect(0,up,gl,bedU-up);x.fillRect(gl+18,lvl,gr-gl-18,bed-lvl);x.fillRect(gr+18,lo,864-gr-18,bed-lo);x.globalAlpha=p;
S.ln(0,up,gl,up,A,3);S.ln(gl+18,lvl,gr,lvl,A,3);S.ln(gr+18,lo,864,lo,A,3);
// dno a steny
S.pl([[0,bedU],[gl,bedU],[gl,bed],[864,bed]],'#fff',4);S.ln(gl+18,140,gl+18,bed,'#fff',4);S.ln(gr,140,gr,bed,'#fff',4);S.ln(gl,140,gl,bedU,'#fff',2);
x.fillStyle='rgba(255,255,255,.05)';x.fillRect(0,bed,864,20);
// obtokový kanál so stavidlom
const cul=S.path([[200,bedU-6],[200,bed-14],[gl+60,bed-14]]);cul.draw('rgba(255,255,255,.5)',3);if(T>3&&fill<1){S.flow(cul,6,t*.6,4.5,A,p*(1-fill)*1.2)}x.globalAlpha=p;
// brány
gate(gl,140,bedU,gO?1:0);gate(gr,140,bed,(T<2.8||T>99)?1:0);
// loď
let sx,wl;if(eout>0){sx=440-(440-130)*eout;wl=up}else{sx=760-(760-440)*E(ein);wl=lvl}
x.save();x.beginPath();x.rect(0,0,864,bed);x.clip();ship(sx,wl);x.restore();
// kóta zdvihu
const qk=st(1,.6);x.globalAlpha=p*qk;x.save();x.setLineDash([5,6]);S.ln(gr+18,up,864,up,'rgba(255,255,255,.35)',2);x.restore();S.kota(820,up,820,lo,'#bdbdbd');x.globalAlpha=p;
S.txt(vH,S.f1(h)+' m',qk);if(has(d,1)&&has(d,2))S.txt(vV,NF(Math.round(vol),0)+' m³',st(1.4,.6));
S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.op(L2,st(.8,.6))})};

// ---------- priehrada: spád × prietok → výkon. n=[spád m, prietok m³/s] ----------
MECH3.dam=(v,d)=>{const S=M3(v,d),{x,A}=S;const h=S.nn(0,100,1,2000),Q=S.nn(1,500,.01,1e6);const P=1000*9.81*h*Q*.9;
const wl=140,gnd=470,tx=590,ty=432;
const L0=S.lab(0,28,392,250,'center',20),L1=S.lab(1,tx-110,gnd+16,220,'center',20),L2=S.lab(2,630,124,220,'center',20);
const vH=S.val(36,248,230,'center',36),vP=S.val(560,38,300,'center',50,A);
const pen=S.path([[284,360],[330,380],[tx-34,ty]]),out=S.path([[tx+30,ty+14],[860,ty+14]]);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),q=st(.8,.7);
// nádrž
x.globalAlpha=p*.3;x.fillStyle=A;x.beginPath();x.moveTo(0,wl+Math.sin(t*2)*2);for(let X=0;X<=300;X+=20)x.lineTo(X,wl+Math.sin(t*2+X/40)*3);x.lineTo(300,gnd);x.lineTo(0,gnd);x.fill();x.globalAlpha=p;
x.strokeStyle=A;x.lineWidth=3;x.beginPath();for(let X=0;X<=296;X+=8){const y=wl+Math.sin(t*2+X/40)*3;X?x.lineTo(X,y):x.moveTo(X,y)}x.stroke();
// teleso hrádze
S.pl([[290,100],[350,100],[540,gnd],[290,gnd]],'#fff',4,true,'#000');x.save();x.beginPath();x.moveTo(290,100);x.lineTo(350,100);x.lineTo(540,gnd);x.lineTo(290,gnd);x.clip();x.strokeStyle='rgba(255,255,255,.12)';x.lineWidth=2;for(let k=-10;k<20;k++){x.beginPath();x.moveTo(290+k*30,gnd);x.lineTo(290+k*30+200,gnd-200);x.stroke()}x.restore();
// prívodné potrubie
x.lineCap='round';S.ln(284,360,330,380,'#fff',22);S.ln(330,380,tx-34,ty,'#fff',22);S.ln(284,360,330,380,'#000',14);S.ln(330,380,tx-34,ty,'#000',14);x.lineCap='butt';
S.flow(pen,7,t*.5*sp,5,A,p*sp);x.globalAlpha=p;
// zem a odtok
S.ln(0,gnd,864,gnd,'#fff',4);x.globalAlpha=p*.3;x.fillStyle=A;x.fillRect(tx+30,ty+2,864-tx-30,gnd-ty-2);x.globalAlpha=p;S.flow(out,8,t*.4*sp,4,A,p*sp*.9);x.globalAlpha=p;
// turbína a generátor
S.ci(tx,ty,34,'#fff',4,'#000');x.save();x.translate(tx,ty);x.rotate(t*6*sp);for(let k=0;k<6;k++){x.rotate(Math.PI/3);x.beginPath();x.moveTo(6,0);x.quadraticCurveTo(18,-14,28,-4);x.strokeStyle='#fff';x.lineWidth=3;x.stroke()}x.restore();S.ci(tx,ty,6,null,0,A);
S.ln(tx,ty-34,tx,ty-62,'#fff',5);S.rc(tx-38,ty-118,76,56,'#fff',4,'#000');x.save();x.translate(tx,ty-90);x.rotate(t*6*sp);S.ln(-18,0,18,0,A,3);S.ln(0,-18,0,18,A,3);x.restore();
// vedenie a stožiar
const sx=740;S.pl([[sx-30,gnd],[sx,200],[sx+30,gnd]],'#fff',3);S.ln(sx-40,220,sx+40,220,'#fff',3);S.ln(sx-28,260,sx+28,260,'#fff',3);S.ln(sx-20,330,sx+20,380,'rgba(255,255,255,.5)',2);S.ln(sx+20,330,sx-20,380,'rgba(255,255,255,.5)',2);
const wire=S.path([[tx+38,ty-96],[640,ty-96],[640,220],[sx-40,220],[860,226]]);wire.draw('#bdbdbd',2);x.globalAlpha=p*q;S.flow(wire,8,t*.5,4,A);x.globalAlpha=p;
// kóta spádu
const qk=st(.6,.6);x.globalAlpha=p*qk;x.save();x.setLineDash([5,6]);S.ln(0,wl,24,wl,'#bdbdbd',2);S.ln(24,ty,tx-40,ty,'rgba(255,255,255,.3)',2);x.restore();S.kota(18,wl,18,ty,'#bdbdbd');x.globalAlpha=p;
S.txt(vH,'h = '+S.f1(h)+' m',qk);S.txt(vP,S.big(P,'W'),q);S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.op(L2,st(.9,.6))})};

// ---------- vežový žeriav: moment bremena = moment protizávažia. n=[bremeno t, vyloženie m, protivýložník m] ----------
MECH3.crane=(v,d)=>{const S=M3(v,d),{x,A}=S;const m=S.nn(0,5,.01,1e4),r=S.nn(1,40,.5,500),rc=S.nn(2,15,.5,500);const cw=m*r/rc;
const mx=380,jy=120,jL=830,cL=160,hx=736,gnd=520;
const L0=S.lab(0,590,gnd+14,240,'center',20),L1=S.lab(1,40,290,240,'center',20,A);
const vR=S.val(mx+40,jy+74,hx-mx-80,'center',28,'#bdbdbd'),vC=S.val(cL+20,jy+74,mx-cL-40,'center',28,'#bdbdbd'),vW=S.val(40,240,240,'center',40,A);
const truss=(x1,x2,y,hh)=>{S.ln(x1,y,x2,y,'#fff',4);S.ln(x1,y+hh,x2,y+hh,'#fff',4);x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2;x.beginPath();const st=Math.sign(x2-x1)*22;for(let X=x1;Math.abs(X-x1)<Math.abs(x2-x1)-2;X+=st){x.moveTo(X,y+hh);x.lineTo(X+st/2,y);x.lineTo(X+st,y+hh)}x.stroke()};
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));
// veža
S.ln(mx-18,gnd,mx-18,jy+16,'#fff',4);S.ln(mx+18,gnd,mx+18,jy+16,'#fff',4);x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2;x.beginPath();for(let y=gnd;y>jy+30;y-=36){x.moveTo(mx-18,y);x.lineTo(mx+18,y-18);x.lineTo(mx-18,y-36)}x.stroke();
S.rc(mx-50,gnd-10,100,14,'#fff',3,'#000');S.ln(20,gnd+4,844,gnd+4,'rgba(255,255,255,.5)',2);
// výložníky a hrot
truss(mx,jL,jy,16);truss(mx,cL,jy,16);S.pl([[mx-14,jy],[mx,40],[mx+14,jy]],'#fff',4);S.ln(mx,40,640,jy,'#bdbdbd',2);S.ln(mx,40,cL+30,jy,'#bdbdbd',2);
S.rc(mx+20,jy+16,44,34,'#fff',3,'#000');
// protizávažie
const qw=st(.9,.7);S.rc(cL+6,jy+18,62,40,qw>.5?A:'#fff',4,'#000');S.ln(cL+6,jy+38,cL+68,jy+38,qw>.5?A:'#fff',2);
// mačka, lano, bremeno (zdvíha sa)
const lift=EI(cl((t-1.2)/3.2)),ly=gnd-66-lift*170,sw=Math.sin(t*1.6)*4*lift;
S.rc(hx-20,jy+16,40,14,'#fff',3,'#000');S.ln(hx-6,jy+30,hx-6+sw,ly-8,'#bdbdbd',2);S.ln(hx+6,jy+30,hx+6+sw,ly-8,'#bdbdbd',2);
S.pl([[hx-6+sw,ly-8],[hx+sw-36,ly],[hx+sw+36,ly]],'#fff',2,true);S.rc(hx+sw-46,ly,92,62,'#fff',4,'#000');S.ct(S.f1(m)+' t',hx+sw,ly+32,24,'#fff','center',800);
// kóty a momenty
const qk=st(.6,.6);x.globalAlpha=p*qk;S.kota(mx,jy+64,hx,jy+64,'#8a8a8a');S.kota(cL+37,jy+64,mx,jy+64,'#8a8a8a');x.globalAlpha=p;
S.txt(vR,S.f1(r)+' m',qk);S.txt(vC,S.f1(rc)+' m',qk);S.txt(vW,S.f1(cw)+' t',qw);S.op(L1,qw);S.op(L0,st(.4,.6))})};

// ---------- visutý most: cesta záťaže mostovka → závesy → nosné lano → pylóny → kotvy ----------
MECH3.bridge=(v,d)=>{const S=M3(v,d),{x,A}=S;const dk=380,t1=250,t2=614,top=120,sag=330,wat=470;
const cab=(X)=>{if(X<=t1)return 360+(top-360)*((X-60)/(t1-60));if(X>=t2)return 360+(top-360)*((804-X)/(804-t2));const u=(X-432)/(t2-432);return sag+(top-sag)*u*u};
const DEF=['','','','',''];const cp=(a,b)=>{const P=[];for(let j=0;j<=40;j++){const X=a+(b-a)*j/40;P.push([X,cab(X)])}return S.path(P)};const CL=cp(432,60),CR=cp(432,804);const L=[0,1,2,3,4].map(i=>S.L[i]||DEF[i]);
const cap=el('div','lab','left:0;top:24px;width:864px;text-align:center;font-size:26px;opacity:0;color:'+A,'');v.append(cap);
const row=el('div','lab','left:0;top:500px;width:864px;text-align:center;font-size:20px;opacity:0',esc(L.filter(s=>s).join('  →  ')));v.append(row);fit(row,20,12,40,840);
return RUN(S,(t,st,p)=>{const s0=[st(.5,.4),st(.8,.4),st(1.1,.4),st(1.4,.4),st(1.7,.4)];const cyc=t>4.4&&s0[4]>.99?Math.floor((t-4.4)/1.3)%5:-1;const stg=cyc<0?s0:s0.map((q,k)=>k==cyc?1:0);const c=k=>stg[k]>.5?A:'#fff';
// voda
x.globalAlpha=p*.2;x.fillStyle='#fff';x.fillRect(0,wat,864,20);x.globalAlpha=p;for(let k=0;k<12;k++){const X=((k*80+t*20)%880)-20;S.ln(X,wat+10,X+30,wat+10,'rgba(255,255,255,.3)',2)}
// kotvy
[[20,330,80,wat],[784,330,844,wat]].forEach(b=>S.rc(b[0],b[1],b[2]-b[0],b[3]-b[1],c(4),4,'#000'));
// pylóny
[t1,t2].forEach(X=>{S.ln(X-10,top-10,X-10,wat,c(3),6);S.ln(X+10,top-10,X+10,wat,c(3),6);S.ln(X-10,top+40,X+10,top+40,c(3),4);S.ln(X-10,dk+30,X+10,dk+30,c(3),4)});
// nosné lano
x.strokeStyle=c(2);x.lineWidth=5;x.beginPath();for(let X=60;X<=804;X+=4){const y=cab(X);X==60?x.moveTo(X,y):x.lineTo(X,y)}x.stroke();
// závesy
for(let X=90;X<790;X+=26){if(Math.abs(X-t1)<16||Math.abs(X-t2)<16)continue;const y=cab(X);if(dk-y<8)continue;S.ln(X,y,X,dk,stg[1]>.5?A:'rgba(255,255,255,.55)',2)}
// mostovka
S.rc(40,dk,784,14,c(0),4,'#000');
// náklad
const tx=((t*60)%960)-80;x.save();x.beginPath();x.rect(40,0,784,560);x.clip();S.rc(tx,dk-28,70,26,'#fff',3,'#000');S.rc(tx+70,dk-22,22,20,'#fff',3,'#000');x.restore();
// tok síl: šípky
const fa=cyc<0?stg[0]:stg[0]*cl((t-4.4-0)%1.3/.3);x.globalAlpha=p*fa;S.ar(tx+40,dk-70,tx+40,dk-34,A,4);x.globalAlpha=p;
if(stg[3]>.5){x.globalAlpha=p*cl((stg[3]-.5)*2);[t1,t2].forEach(X=>S.ar(X,wat-60,X,wat+16,A,5));x.globalAlpha=p}
if(stg[4]>.5){x.globalAlpha=p*cl((stg[4]-.5)*2);S.ar(110,300,60,340,A,5);S.ar(754,300,804,340,A,5);x.globalAlpha=p}
// bodky po trase sily
const k=cyc<0?s0.filter(s=>s>.5).length:cyc+1;if(stg[2]>.5){x.globalAlpha=p*.9;[CL,CR].forEach(pp=>{for(let j=0;j<4;j++){const q=pp.at(t*.25+j/4);S.dot(q[0],q[1],5,'#fff')}});x.globalAlpha=p}
const cur=k?k-1:-1;const s=cur>=0?L[cur]:'';if(cap.textContent!==s){cap.textContent=s;fit(cap,26,14,60,860)}cap.style.opacity=cur>=0?1:0;S.op(row,st(2,.5))})};

// ---------- razenie tunela (TBM): rezná hlava, štít, ukladanie tubingov, pás s rubaninou. n=[postup m/deň, šírka prstenca m] ----------
MECH3.tunnel=(v,d)=>{const S=M3(v,d),{x,A}=S;const adv=S.nn(0,15,.1,500),rw=S.nn(1,1.5,.2,10);const rings=adv/rw;
const ay=320,R=78,gs=110;const st0=[];for(let k=0;k<70;k++)st0.push([(k*137)%864,140+((k*73)%390)]);
const L0=S.lab(0,560,150,300,'center',20,A),L1=S.lab(1,40,150,320,'center',20),L2=S.lab(2,40,ay+R+30,320,'center',20,'#bdbdbd');
const vA=S.val(420,436,420,'center',40,A),vR=S.val(420,486,420,'center',26,'#bdbdbd');
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));const fx=500+Math.min(230,t*30)*sp;
// povrch s domami
S.ln(0,gs,864,gs,'#fff',3);[[40,70],[130,50],[520,80],[620,40],[700,64]].forEach(([X,hh])=>S.rc(X,gs-hh,60,hh,'rgba(255,255,255,.6)',2));
// horniny
x.fillStyle='rgba(255,255,255,.22)';st0.forEach(([X,Y])=>{if(Math.abs(Y-ay)<R+8&&X<fx+8)return;x.fillRect(X,Y,3,3)});
// vyrazený tunel
S.ln(0,ay-R,fx,ay-R,'#fff',3);S.ln(0,ay+R,fx,ay+R,'#fff',3);
// tubingy (prstence) za štítom
const sh=fx-230;for(let X=12,i=0;X<sh-4;X+=34,i++){const q=cl((sh-X)/40);x.globalAlpha=p*q;S.rc(X,ay-R+2,30,14,'#fff',2,i%2?'#bdbdbd':'#8a8a8a');S.rc(X,ay+R-16,30,14,'#fff',2,i%2?'#bdbdbd':'#8a8a8a')}x.globalAlpha=p;
// štít
S.rc(sh,ay-R+2,fx-sh-14,2*R-4,'#fff',4,'#000');S.ln(sh+60,ay-R+2,sh+60,ay+R-2,'rgba(255,255,255,.5)',2);
for(let k=0;k<3;k++){S.ln(sh+70,ay-40+k*40,fx-40,ay-40+k*40,'#9a9a9a',6)}
// rezná hlava (bočný pohľad)
S.ln(fx-10,ay-R-4,fx-10,ay+R+4,A,6);for(let k=0;k<8;k++){const a=t*3*sp+k*Math.PI/4,Y=ay+Math.sin(a)*(R-4);if(Math.cos(a)>0)S.rc(fx-6,Y-5,10,10,null,0,A)}
// dopravník s rubaninou
const belt=S.path([[fx-30,ay+30],[10,ay+30]]);belt.draw('#bdbdbd',3);S.flow(belt,14,t*.18*sp,4.5,'#bdbdbd',p*sp);x.globalAlpha=p;
// smer postupu
const qa=st(.7,.6);x.globalAlpha=p*qa;S.ar(fx+20,ay,fx+80,ay,A,5);x.globalAlpha=p;
S.op(L0,st(.4,.6));S.op(L1,st(.7,.6));S.op(L2,st(.9,.6));if(has(d,0)){S.txt(vA,S.f1(adv)+' m / 24 h',st(1.1,.6));S.txt(vR,'≈ '+S.f1(rings)+' × '+S.f1(rw)+' m',st(1.4,.6))}
mv(L0,Math.min(560,fx-150),150)})};
const mv=(e,l,t)=>{if(e){e.style.left=l+'px';e.style.top=t+'px'}};

// ---------- vrtná veža: vrtná kolóna, dláto, výplach. n=[hĺbka m] ----------
MECH3.drill=(v,d)=>{const S=M3(v,d),{x,A}=S;const dep=S.nn(0,3000,1,20000);const hx=200,gs=200,res=[440,500];
const bands=[[gs,262,0],[262,330,1],[330,398,2],[398,440,3],[440,500,4],[500,560,5]];
const L0=S.lab(0,300,60,300,'left',20),L1=S.lab(1,8,0,hx-36,'right',20),L2=S.lab(2,520,454,330,'center',20,A);const vD=S.val(hx+34,0,200,'left',34);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));const g=EI(cl((t-.6)/4.2)),by=gs+30+g*(res[0]+30-gs-30);
// vrstvy hornín
bands.forEach(([a,b,k])=>{if(k==4){x.globalAlpha=p*.28;x.fillStyle=A;x.fillRect(0,a,864,b-a);x.globalAlpha=p}S.ln(0,a,864,a,k==4||k==5?A:'rgba(255,255,255,.4)',2);
if(k==4)return;x.fillStyle='rgba(255,255,255,.2)';for(let X=12+k*7;X<864;X+=(k%2?38:26))for(let Y=a+10;Y<b-4;Y+=(k%2?20:26)){if(Math.abs(X-hx)<26)continue;if(k%3==0)x.fillRect(X,Y,3,3);else if(k%3==1){x.fillRect(X,Y,12,2)}else{x.beginPath();x.arc(X,Y,2.5,0,6.3);x.fill()}}});
S.ln(0,gs,864,gs,'#fff',4);
// veža
S.pl([[hx-70,gs],[hx-12,40],[hx+12,40],[hx+70,gs]],'#fff',4);x.strokeStyle='rgba(255,255,255,.6)';x.lineWidth=2;x.beginPath();for(let k=0;k<4;k++){const y1=gs-k*40,y2=gs-(k+1)*40,w1=70-k*14.5,w2=70-(k+1)*14.5;x.moveTo(hx-w1,y1);x.lineTo(hx+w2,y2);x.moveTo(hx+w1,y1);x.lineTo(hx-w2,y2)}x.stroke();
S.rc(hx-90,gs-26,180,26,'#fff',3,'#000');S.rc(hx+90,gs-56,90,56,'#fff',3,'#000');
// vrt
x.fillStyle='#000';x.fillRect(hx-20,gs,40,by-gs+10);S.ln(hx-20,gs,hx-20,by,'#fff',3);S.ln(hx+20,gs,hx+20,by,'#fff',3);
// kolóna a rotácia
S.ln(hx,52,hx,by-16,'#d9d9d9',7);for(let y=gs+20;y<by-20;y+=34){const o=((t*40*sp)%34);S.ln(hx-4,y+o-34>gs?y+o-34:y,hx+4,(y+o-34>gs?y+o-34:y),'#000',2)}
// dláto (trojkužeľ)
x.save();x.translate(hx,by);S.pl([[-16,-18],[16,-18],[12,0],[0,10],[-12,0]],A,4,true,'#000');const a=t*8*sp;for(let k=0;k<3;k++){const xx=Math.sin(a+k*2.1)*10;if(Math.cos(a+k*2.1)>0)S.dot(xx,-4,3,A)}x.restore();
// výplach: dole v kolóne, hore medzikružím
const dn=S.path([[hx,60],[hx,by-14]]),u1=S.path([[hx-13,by-6],[hx-13,gs+4]]),u2=S.path([[hx+13,by-6],[hx+13,gs+4]]);S.flow(dn,8,t*.5*sp,3.5,'#fff',p*sp*.9);S.flow(u1,5,t*.3*sp,3,'#8a8a8a',p*sp);S.flow(u2,5,t*.3*sp+.5,3,'#8a8a8a',p*sp);x.globalAlpha=p;
// popisky a hĺbka
const dd=g*dep;if(by<432){x.fillStyle='#000';if(S.L[1])x.fillRect(4,by-18,hx-36,34);x.fillRect(hx+24,by-24,170,46)}if(S.L[1])mv(L1,8,by-14);S.op(L1,st(.6,.6));S.op(L0,st(.4,.6));S.op(L2,st(1,.6));mv(vD,hx+34,by-24);S.txt(vD,NF(Math.round(dd/10)*10,0)+' m',st(.8,.5))})};

// ---------- eskalátor: stupne po slučke, pohon hore, madlo. n=[výška m, rýchlosť m/s] → čas jazdy ----------
MECH3.escalator=(v,d)=>{const S=M3(v,d),{x,A}=S;const h=S.nn(0,6,.5,100),sp0=S.nn(1,.5,.1,5);const len=h/Math.sin(Math.PI/6),T=len/sp0;
const P=[[30,450],[150,450],[670,150],[800,150]];const run=S.path(P);const ret=S.path([[150,490],[670,190]]);
const L0=S.lab(0,170,150,260,'center',20),L1=S.lab(1,560,236,300,'center',20,A),L2=S.lab(2,520,470,320,'center',20,'#bdbdbd');
const vH=S.val(736,290,96,'right',30),vT=S.val(520,500,320,'center',40,A);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));const off=t*.04*sp;
// podlažia
S.ln(0,450+14,150,450+14,'#fff',3);S.ln(670,150+14,864,150+14,'#fff',3);
// nosník (priehradový)
S.ln(150,490,670,190,'rgba(255,255,255,.5)',3);S.ln(150,464,670,164,'rgba(255,255,255,.5)',2);x.strokeStyle='rgba(255,255,255,.25)';x.lineWidth=2;x.beginPath();for(let k=0;k<13;k++){const u=k/13,u2=(k+.5)/13;x.moveTo(150+520*u,490-300*u);x.lineTo(150+520*u2,464-300*u2)}x.stroke();
// reťazové kolesá
[[160,476,1],[662,176,1]].forEach(([X,Y],i)=>{S.ci(X,Y,22,i?A:'#fff',4,'#000');x.save();x.translate(X,Y);x.rotate(-t*2*sp);S.ln(-14,0,14,0,i?A:'#fff',3);S.ln(0,-14,0,14,i?A:'#fff',3);x.restore()});
S.rc(700,180,70,44,A,3,'#000');S.ln(684,190,700,196,A,3);
// stupne
const pitch=run.tot/26;for(let k=0;k<26;k++){const u=(k/26+off)%1,a=run.at(u),b=run.at(u+pitch/run.tot);if(u+pitch/run.tot>1)continue;S.pl([[a[0],a[1]],[b[0],a[1]],[b[0],b[1]]],'#fff',3)}
// madlo
const hr=S.path([[60,370],[150,370],[670,70],[780,70]]);hr.draw('#bdbdbd',6);for(let k=0;k<6;k++){const q=hr.at(k/6+off);S.dot(q[0],q[1],3,'#000')}S.ln(150,370,150,450,'rgba(255,255,255,.35)',2);S.ln(670,70,670,150,'rgba(255,255,255,.35)',2);
// cestujúci
const u=cl((t*.11*sp)%1),q=run.at(.12+u*.76);x.globalAlpha=p*Math.min(1,Math.sin(u*Math.PI)*4);S.ln(q[0],q[1],q[0],q[1]-46,A,5);S.ci(q[0],q[1]-58,10,A,4,'#000');S.ln(q[0],q[1]-38,q[0]+18,q[1]-60,A,4);x.globalAlpha=p;
// kóta výšky
const qk=st(.9,.6);x.globalAlpha=p*qk;S.kota(848,164,848,464,'#8a8a8a');x.globalAlpha=p;S.txt(vH,S.f1(h)+' m',qk);
S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.op(L2,st(1.1,.6));S.txt(vT,S.f1(T)+' s',st(1.2,.6))})};

// ---------- veterná turbína: P = ½·ρ·A·v³·cp. n=[rýchlosť vetra m/s, priemer rotora m] ----------
MECH3.wind_turbine=(v,d)=>{const S=M3(v,d),{x,A}=S;const ws=S.nn(0,12,.5,60),D=S.nn(1,120,1,300);const Pw=w=>.5*1.225*Math.PI*D*D/4*w*w*w*.45;const P=Pw(ws);
const hx=280,hy=190,gL=520,gR=830,gT=150,gB=430,vm=ws*1.6;
const L0=S.lab(0,10,52,180,'left',20,'#bdbdbd'),L1=S.lab(1,gL-20,gT-56,gR-gL+40,'left',18,'#bdbdbd'),L2=S.lab(2,gL,gB+14,gR-gL,'center',18,'#bdbdbd');
const vP=S.val(gL,gT-8,gR-gL,'right',40,A),vV=S.val(gL,gB+44,gR-gL,'center',30);
const gx=w=>gL+(gR-gL)*w/vm,gy=w=>gB-(gB-gT-50)*Math.pow(w/ws,3)/Math.pow(vm/ws,3)*Math.pow(vm/ws,3)/Math.pow(1.6,3)*1;
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));
// vietor
x.globalAlpha=p*sp;for(let k=0;k<6;k++){const y=90+k*44,o=((t*ws*12+k*90)%240);x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;x.beginPath();x.moveTo(10+o-60,y);x.lineTo(10+o,y);x.stroke();}x.globalAlpha=p;
// stožiar a gondola
S.pl([[hx-8,hy+20],[hx-18,gB+90],[hx+18,gB+90],[hx+8,hy+20]],'#fff',4,true,'#000');S.ln(hx-120,gB+90,hx+120,gB+90,'rgba(255,255,255,.5)',2);
S.rc(hx-2,hy-14,60,28,'#fff',4,'#000');
// listy
const a=t*ws*.12*sp;x.save();x.translate(hx-6,hy);for(let k=0;k<3;k++){x.save();x.rotate(a+k*2.094);x.beginPath();x.moveTo(0,-8);x.quadraticCurveTo(40,-16,150,-3);x.lineTo(150,3);x.quadraticCurveTo(40,10,0,8);x.closePath();x.fillStyle='#000';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.restore()}x.restore();S.ci(hx-6,hy,12,'#fff',3,A);
// graf P ~ v³
const qg=st(.7,.8);x.globalAlpha=p*qg;S.ln(gL,gB,gR,gB,'#8a8a8a',2);S.ln(gL,gB,gL,gT,'#8a8a8a',2);
x.strokeStyle=A;x.lineWidth=4;x.beginPath();const k=1/Math.pow(1.6,3);for(let j=0;j<=60*qg;j++){const w=j/60*vm,y=gB-(gB-gT-40)*Math.pow(w/vm,3);j?x.lineTo(gx(w),y):x.moveTo(gx(w),y)}x.stroke();
const yv=gB-(gB-gT-40)*k;const qm=st(1.2,.6);x.globalAlpha=p*qm;x.save();x.setLineDash([5,6]);S.ln(gx(ws),gB,gx(ws),yv,'#bdbdbd',2);S.ln(gL,yv,gx(ws),yv,'#bdbdbd',2);x.restore();S.ci(gx(ws),yv,8,A,4,'#000');
// 2× vietor = 8× výkon
const w2=ws/2,y2=gB-(gB-gT-40)*Math.pow(w2/vm,3);S.ci(gx(w2),y2,6,'#bdbdbd',3,'#000');x.globalAlpha=p;
S.op(L0,st(.4,.6));S.op(L1,qg);S.op(L2,qg);S.txt(vP,S.big(P,'W'),qm);S.txt(vV,S.f1(ws)+' m/s',qm)})};

// ---------- kotúčová brzda: brzdový kotúč, strmeň, platničky; ½mv² → teplo. n=[km/h, kg] ----------
MECH3.car_brake=(v,d)=>{const S=M3(v,d),{x,A}=S;const kmh=S.nn(0,100,1,1000),kg=S.nn(1,1500,1,1e6);const Ek=.5*kg*Math.pow(kmh/3.6,2);
const cx=250,cy=280,R=150,sx=700;
const L0=S.lab(0,cx-150,450,300,'center',20),L1=S.lab(1,sx-130,30,260,'center',20,A),L2=S.lab(2,sx-130,436,260,'center',20);
const vV=S.val(cx-150,486,300,'center',36),vE=S.val(sx-150,480,300,'center',40,A);
return RUN(S,(t,st,p)=>{const br=EI(cl((t-1.4)/.6)),sl=cl((t-1.6)/3.4);const sp=cl(st(.3,1));const w=(t<1.6?t*7:1.6*7+(1-Math.pow(1-sl,2))*3.4*7*.5)*sp;const heat=cl((t-1.8)/2.5)*br;
// kotúč – čelný pohľad
if(heat>0){const g=x.createRadialGradient(cx,cy,R*.55,cx,cy,R);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,A);x.globalAlpha=p*.45*heat;x.fillStyle=g;x.beginPath();x.arc(cx,cy,R,0,6.3);x.fill();x.globalAlpha=p}
S.ci(cx,cy,R,'#fff',4);S.ci(cx,cy,R*.55,'#fff',3);x.save();x.translate(cx,cy);x.rotate(w);for(let k=0;k<24;k++){const a=k*Math.PI/12,r=k%2?R*.72:R*.86;S.ci(Math.cos(a)*r,Math.sin(a)*r,5,'rgba(255,255,255,.7)',2)}
for(let k=0;k<5;k++){const a=k*1.2566;S.ci(Math.cos(a)*36,Math.sin(a)*36,8,'#fff',3,'#000')}x.restore();S.ci(cx,cy,14,'#fff',3);
// strmeň na okraji
x.save();x.translate(cx,cy);x.beginPath();x.arc(0,0,R+14,-.42,.42);x.arc(0,0,R*.62,.42,-.42,true);x.closePath();x.fillStyle='#000';x.fill();x.strokeStyle=A;x.lineWidth=4;x.stroke();x.restore();
// rez strmeňom vpravo
const dl=sx-12,dr=sx+12,top=110,bot=420,gap=10*(1-br);
S.rc(dl,top,dr-dl,bot-top,'#fff',3,heat>.2?'rgba(255,107,0,'+(.15+.45*heat)+')':'#000');
// pohybujúce sa otvory kotúča (rez)
x.save();x.beginPath();x.rect(dl,top,dr-dl,bot-top);x.clip();for(let k=0;k<10;k++){const y=top+((k*36+w*40)%(bot-top));S.ln(dl,y,dr,y,'rgba(255,255,255,.4)',2)}x.restore();
const pT=200,pB=330;S.rc(dl-26-gap,pT,22,pB-pT,'#fff',3,'#8a8a8a');S.rc(dr+4+gap,pT,22,pB-pT,'#fff',3,'#8a8a8a');
// telo strmeňa a piest
S.pl([[dl-30-gap-50,pT-30],[dr+90,pT-30],[dr+90,pB+30],[dl-30-gap-50,pB+30]],A,4,true);S.rc(dl-30-gap-50,pT+10,46,pB-pT-20,'#fff',3,'#000');S.rc(dl-30-gap-14,pT+10,4,pB-pT-20,null,0,'#fff');
S.rc(dr+26+gap,pT-26,60,pB-pT+52,null,0,'#000');S.ln(dr+26+gap,pT-30,dr+26+gap,pB+30,A,4);
// hydraulika
const hy=S.path([[dl-80-gap-40,90],[dl-80-gap-40,pT+40],[dl-30-gap-50,pT+40]]);hy.draw('#bdbdbd',3);if(br>0)S.flow(hy,5,t*.5,4,'#fff',p*br);x.globalAlpha=p;
if(br>.5){x.globalAlpha=p*br;S.ar(dl-70-gap,pB+50,dl-40-gap,pB+50,'#fff',3);S.ar(dr+90,pB+50,dr+60,pB+50,'#fff',3);x.globalAlpha=p}
// teplo
if(heat>.05){x.globalAlpha=p*heat;for(let k=0;k<3;k++){const xx=sx-24+k*24;x.strokeStyle=A;x.lineWidth=3;x.beginPath();for(let j=0;j<=8;j++){const y=top-8-j*4,X=xx+Math.sin(j*.8-t*6)*4;j?x.lineTo(X,y):x.moveTo(X,y)}x.stroke()}x.globalAlpha=p}
S.op(L0,st(.3,.6));S.op(L1,st(.5,.6));S.op(L2,st(.7,.6));S.txt(vV,NF(Math.round(kmh*(1-sl)),0)+' km/h',st(.5,.6));if(has(d,1))S.txt(vE,S.big(Ek,'J'),cl((t-2)/.6))})};

// ---------- diferenciál: v zákrute ide vonkajšie koleso ďalej a rýchlejšie. n=[rozchod m, polomer zákruty m] ----------
MECH3.differential=(v,d)=>{const S=M3(v,d),{x,A}=S;const tw=S.nn(0,1.6,.3,10),Rt=Math.max(tw*.6,S.nn(1,6,.5,1e4));const ri=(Rt-tw/2)/Rt,ro=(Rt+tw/2)/Rt;
const C=[96,512],Rm=290,Ri=240,Ro=340,a0=-1.48,a1=-.22;const wx=610,wi=150,wo=420,wr=62;
const L0=S.lab(0,690,wi-40,170,'left',20),L1=S.lab(1,690,wo-40,170,'left',20,A),L2=S.lab(2,690,280-16,170,'left',18,'#bdbdbd');
const vI=S.val(690,wi-12,170,'left',36),vO=S.val(690,wo-12,170,'left',36,A);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));const u=(t*.11*sp)%1,ph=a0+(a1-a0)*u;
// stopy kolies
x.save();x.setLineDash([8,8]);x.lineWidth=3;x.strokeStyle='#8a8a8a';x.beginPath();x.arc(C[0],C[1],Ri,a0,a1);x.stroke();x.strokeStyle=A;x.beginPath();x.arc(C[0],C[1],Ro,a0,a1);x.stroke();x.restore();
S.ci(C[0],C[1],6,null,0,'#8a8a8a');
// auto zhora
const cx=C[0]+Rm*Math.cos(ph),cy=C[1]+Rm*Math.sin(ph);x.save();x.translate(cx,cy);x.rotate(ph+Math.PI/2);
S.rc(-70,-46,140,92,'#fff',4,'#000');S.rc(-10,-38,46,76,'rgba(255,255,255,.5)',2);
[[-46,50,'#8a8a8a'],[-46,-50,A],[46,50,'#8a8a8a'],[46,-50,A]].forEach(([X,Y,c])=>{x.save();x.translate(X,Y);if(X>0)x.rotate(Y<0?-.2:-.14);S.rc(-16,-7,32,14,c,3,'#000');x.restore()});
S.ln(-46,-44,-46,44,'#bdbdbd',3);S.rc(-56,-10,20,20,A,3,'#000');x.restore();
// pravý panel: kolesá a diferenciál
const wI=t*3*sp*ri,wO=t*3*sp*ro;
[[wi,wI,'#bdbdbd'],[wo,wO,A]].forEach(([Y,a,c])=>{S.ci(wx,Y,wr,c,5,'#000');S.ci(wx,Y,wr-16,c,2);x.save();x.translate(wx,Y);x.rotate(a);for(let k=0;k<5;k++){const b=k*1.2566;S.ln(Math.cos(b)*10,Math.sin(b)*10,Math.cos(b)*(wr-16),Math.sin(b)*(wr-16),c,3)}x.restore()});
S.ln(wx,wi+wr,wx,280-30,'#fff',4);S.ln(wx,280+30,wx,wo-wr,'#fff',4);
// kužeľové kolesá diferenciálu
S.rc(wx-40,250,80,60,'#fff',3,'#000');x.save();x.translate(wx,280);x.rotate(t*3*sp);S.gear(0,0,18,10,0,A,4);x.restore();
S.op(L0,st(.5,.6));S.op(L1,st(.7,.6));S.op(L2,st(.9,.6));S.txt(vI,NF(Math.round(ri*100),0)+' %',st(1.1,.6));S.txt(vO,NF(Math.round(ro*100),0)+' %',st(1.3,.6))})};

// ---------- vačkový hriadeľ: vačky otvárajú sacie a výfukové ventily. n=[otáčky motora / min] ----------
MECH3.camshaft=(v,d)=>{const S=M3(v,d),{x,A}=S;const rpm=S.nn(0,3000,1,1e5);const cams=[[250,'#bdbdbd',0],[470,A,Math.PI*.9]],cy=110,base=34,lobe=26;
const rr=a=>base+lobe*Math.pow(Math.max(0,Math.cos(a)),2);
const L0=S.lab(0,600,cy-18,250,'left',20),L1=S.lab(1,600,330,250,'left',20,A),L2=S.lab(2,600,226,250,'left',20,'#bdbdbd');
const vR=S.val(600,410,250,'left',36),vC=S.val(600,460,250,'left',36,A);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),w=t*2.4*sp;
// hlava valca a valec
const hT=290,cT=380;S.pl([[150,hT],[150,cT],[570,cT],[570,hT]],'rgba(255,255,255,.5)',2);S.ln(150,cT,150,540,'#fff',4);S.ln(570,cT,570,540,'#fff',4);
const pY=470+Math.sin(w*2)*36;S.rc(156,pY,408,60,'#fff',3,'#1a1a1a');
// kanály
S.pl([[150,320],[210,320],[226,cT]],'#bdbdbd',3);S.pl([[570,320],[510,320],[494,cT]],A,3);
// hriadeľ
S.ln(150,cy,580,cy,'#8a8a8a',8);
cams.forEach(([X,c,o],i)=>{const a=w+o;
// profil vačky
x.save();x.translate(X,cy);x.beginPath();for(let j=0;j<=72;j++){const b=j/72*6.2832,r=rr(b);x.lineTo(Math.cos(b+a)*r,Math.sin(b+a)*r)}x.closePath();x.fillStyle='#000';x.fill();x.strokeStyle=c;x.lineWidth=4;x.stroke();S.ci(0,0,8,null,0,c);x.restore();
// zdvih: lalok smerom dole (π/2)
const lift=rr(Math.PI/2-a)-base,ty=cy+base+lift;
S.rc(X-28,ty,56,30,c,4,'#000');const sy=ty+30,vy=cT+lift*1.2;
// pružina
x.strokeStyle='rgba(255,255,255,.75)';x.lineWidth=2;x.beginPath();const n=8;for(let k=0;k<=n;k++){const y=sy+(hT-10-sy)*k/n;x.lineTo(X+(k&&k<n?(k%2?-22:22):0),y)}x.stroke();S.ln(X-30,hT-10,X+30,hT-10,'#fff',3);
// ventil
S.ln(X,sy,X,vy,'#fff',5);S.pl([[X-6,vy-12],[X-34,vy+4],[X+34,vy+4],[X+6,vy-12]],c,4,true,'#000');
// prúd plynu cez otvorený ventil
if(lift>6){x.globalAlpha=p*cl((lift-6)/10);for(let k=0;k<4;k++){const u=((t*1.2+k/4)%1);const px=i?X+40+u*60:X-100+u*60,py=i?cT-10-u*50:cT-60+u*50;S.dot(px,py,4,c)}x.globalAlpha=p}});
S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.op(L2,st(.8,.6));if(has(d,0)){S.txt(vR,NF(Math.round(rpm),0)+' /min',st(1,.6));S.txt(vC,'÷ 2 = '+NF(Math.round(rpm/2),0)+' /min',st(1.3,.6))}})};

// ---------- procesor: dáta z RAM cez cache do jadier, hodinový takt. n=[GHz, počet jadier] ----------
MECH3.cpu=(v,d)=>{const S=M3(v,d),{x,A}=S;const ghz=S.nn(0,4,.01,100),nc=Math.round(S.nn(1,4,1,256));const ops=ghz*1e9*nc;
const R=[24,150,140,270],Dl=270,Dt=100,Dr=840,Db=420,Cx=[300,380],cores=[[410,120],[620,120],[410,276],[620,276]],cw=196,ch=136;
const L0=S.lab(0,R[0]-10,R[1]+R[3]+10,R[2]+20,'center',20),L1=S.lab(1,Dl-20,52,140,'center',18),L2=S.lab(2,410,52,406,'center',20,A),L3=S.lab(3,8,466,170,'right',18,'#bdbdbd');
const vO=S.val(560,438,290,'right',36,A),vS=S.val(560,486,290,'right',26,'#bdbdbd');const ex=Math.floor(Math.log10(ops)/3)*3,sup=String(ex).split('').map(c=>'⁰¹²³⁴⁵⁶⁷⁸⁹'[+c]).join('');
const bus=S.path([[R[0]+R[2],280],[Cx[0],280]]);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));const clk=t*2.2,ph=clk%1,tick=ph<.5;
// RAM
S.rc(R[0],R[1],R[2],R[3],'#fff',4,'#000');for(let k=0;k<6;k++){S.rc(R[0]+18,R[1]+16+k*42,R[2]-36,28,'rgba(255,255,255,.55)',2)}for(let k=0;k<7;k++)S.ln(R[0]+14+k*19,R[1]+R[3],R[0]+14+k*19,R[1]+R[3]+8,'#bdbdbd',3);
// zbernica
x.strokeStyle='rgba(255,255,255,.5)';x.lineWidth=2;for(let k=-2;k<=2;k++){x.beginPath();x.moveTo(R[0]+R[2],280+k*10);x.lineTo(Dl,280+k*10);x.stroke()}
// čip
S.rc(Dl,Dt,Dr-Dl,Db-Dt,'#fff',4,'#000');for(let k=0;k<14;k++){const X=Dl+20+k*40;S.ln(X,Db,X,Db+10,'#8a8a8a',3);S.ln(X,Dt,X,Dt-10,'#8a8a8a',3)}
// cache
S.rc(Cx[0],Dt+20,Cx[1]-Cx[0],Db-Dt-40,'#bdbdbd',3,'#000');for(let k=0;k<12;k++)S.ln(Cx[0]+8,Dt+34+k*22,Cx[1]-8,Dt+34+k*22,'rgba(255,255,255,.3)',2);
// jadrá
const fl=Math.floor(clk);cores.forEach(([X,Y],i)=>{const on=((fl+i)%3!=0)&&sp>.5;S.rc(X,Y,cw,ch,on&&tick?A:'#fff',3,'#000');S.ct(nc>4&&i==3?'…':String(i+1),X+cw-22,Y+20,18,'#8a8a8a');
for(let r=0;r<3;r++)for(let c=0;c<5;c++){const lit=on&&((r*5+c+fl*7+i*3)%4==0);S.rc(X+18+c*30,Y+30+r*30,22,22,null,0,lit?A:'rgba(255,255,255,.18)')}});
// pakety
x.globalAlpha=p*sp;for(let k=0;k<3;k++){const q=bus.at(t*.25+k/3);S.rc(q[0]-7,q[1]-7,14,14,null,0,'#fff')}
cores.forEach(([X,Y],i)=>{const pp=S.path([[Cx[1],Y+ch/2],[X,Y+ch/2]]);for(let k=0;k<2;k++){const q=pp.at(t*.9+k/2+i*.13);S.rc(q[0]-6,q[1]-6,12,12,null,0,A)}});
x.globalAlpha=p;
// takt
const qc=st(.8,.6);x.globalAlpha=p*qc;x.strokeStyle='#bdbdbd';x.lineWidth=3;x.beginPath();const y0=500,y1=462;for(let X=190;X<=540;X+=2){const ph2=((X-190)/35-clk*2)%2,hi=(ph2+2)%2<1;const y=hi?y1:y0;X==190?x.moveTo(X,y):x.lineTo(X,y)}x.stroke();x.globalAlpha=p;
S.op(L0,st(.3,.6));S.op(L1,st(.5,.6));S.op(L2,st(.6,.6));S.op(L3,qc);S.txt(vO,nc+' × '+S.f1(ghz)+' GHz',st(1,.6));S.txt(vS,'= '+S.f1(ops/Math.pow(10,ex))+' · 10'+sup+' /s',st(1.3,.6))})};

// ---------- HDD vs SSD: rotujúci tanier a hlava vs. pamäťové bunky. n=[prístup HDD ms, prístup SSD ms] ----------
MECH3.hdd=(v,d)=>{const S=M3(v,d),{x,A}=S;const th=S.nn(0,10,.001,1e5),ts=S.nn(1,.1,.0001,1e5);const ratio=th/ts;
const cx=210,cy=260,R=160,sl=500,sr=830,stp=120,sb=400;
const L0=S.lab(0,cx-170,440,340,'center',22),L1=S.lab(1,sl,440,sr-sl,'center',22,A);
const vH=S.val(cx-170,474,340,'center',40),vS=S.val(sl,474,sr-sl,'center',40,A),vX=S.val(sl,40,sr-sl,'center',44,A);
const cells=[];for(let r=0;r<6;r++)for(let c=0;c<8;c++)cells.push([sl+26+c*37,stp+60+r*36]);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));
// tanier
S.rc(cx-R-24,cy-R-24,2*R+48+60,2*R+48,'rgba(255,255,255,.4)',2);S.ci(cx,cy,R,'#fff',4,'#000');for(let k=1;k<5;k++)S.ci(cx,cy,R*(.3+k*.16),'rgba(255,255,255,.18)',2);
x.save();x.translate(cx,cy);x.rotate(t*5*sp);for(let k=0;k<8;k++){const a=k*Math.PI/4;S.ln(Math.cos(a)*R*.3,Math.sin(a)*R*.3,Math.cos(a)*R*.98,Math.sin(a)*R*.98,'rgba(255,255,255,.12)',2)}
x.strokeStyle=A;x.lineWidth=6;x.beginPath();x.arc(0,0,R*.78,0,.5);x.stroke();x.restore();S.ci(cx,cy,R*.22,'#fff',3,'#000');S.ci(cx,cy,6,null,0,'#fff');
// rameno hlavy – hľadá stopu
const px=cx+R+40,py=cy+R-10;const seek=Math.sin(t*1.3)*.22*sp;const ang=-2.35+seek;const hx=px+Math.cos(ang)*230,hy=py+Math.sin(ang)*230;
S.ci(px,py,16,'#fff',3,'#000');x.lineCap='round';S.ln(px,py,hx,hy,'#fff',8);S.ln(px,py,hx,hy,'#000',3);x.lineCap='butt';S.rc(hx-7,hy-7,14,14,null,0,A);
// SSD
S.rc(sl,stp,sr-sl,sb-stp,'#fff',4,'#000');S.rc(sl+18,stp+16,80,28,'#bdbdbd',2);for(let k=0;k<10;k++)S.rc(sl+20+k*30,sb,14,10,null,0,'#bdbdbd');
const f=Math.floor(t*6);cells.forEach(([X,Y],i)=>{const on=sp>.5&&((i*7+f*5)%11<2);S.rc(X,Y,28,26,on?A:'rgba(255,255,255,.4)',2,on?A:'#000')});
S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));if(has(d,0)||has(d,1)){S.txt(vH,S.f1(th)+' ms',st(.9,.6));S.txt(vS,S.f1(ts)+' ms',st(1.1,.6));S.txt(vX,'× '+NF(Math.round(ratio),0),st(1.5,.6))}})};
MECH3.ssd=MECH3.hdd;

// ---------- optické vlákno: totálny odraz, kritický uhol z n=[n jadra, n plášťa] ----------
MECH3.fiber=(v,d)=>{const S=M3(v,d),{x,A}=S;let n1=S.nn(0,1.46,1,4),n2=S.nn(1,1.44,1,4);if(n2>=n1)n2=n1*.99;const thc=Math.asin(n2/n1)*180/Math.PI;
const fl=110,fr=780,cT=210,cB=310,mT=160,mB=360,per=180;
const L0=S.lab(0,200,420,260,'center',20,A),L1=S.lab(1,470,420,260,'center',20),L2=S.lab(2,10,186,90,'center',16,'#bdbdbd');
const vT=S.val(150,40,600,'center',44,A),vN=S.val(150,96,600,'center',22,'#bdbdbd');
const zz=[];for(let X=fl,k=0;X<=fr+per/2;X+=per/2,k++)zz.push([Math.min(X,fr),k%2?cB:cT+((k==0)?50:0)]);zz[0]=[fl,cT+50];
const ray=S.path(zz);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1));
// plášť a jadro
S.rc(fl,mT,fr-fl,mB-mT,'#fff',3,'rgba(255,255,255,.05)');S.rc(fl,cT,fr-fl,cB-cT,'rgba(255,255,255,.6)',2,'#000');
x.save();x.beginPath();x.ellipse(fr,(mT+mB)/2,18,(mB-mT)/2,0,0,6.3);x.fillStyle='#000';x.fill();x.strokeStyle='#fff';x.lineWidth=3;x.stroke();x.beginPath();x.ellipse(fr,(cT+cB)/2,9,(cB-cT)/2,0,0,6.3);x.stroke();x.restore();
// laser
S.rc(14,cT+24,86,52,'#fff',3,'#000');S.ci(86,cT+50,6,null,0,A);
// lúč – slabá dráha + svetelné impulzy
ray.draw('rgba(255,107,0,.25)',2);x.globalAlpha=p*.25;ray.draw(A,2);x.globalAlpha=p;
const bits=[1,0,1,1,0,1];for(let k=0;k<bits.length;k++){if(!bits[k])continue;const u=((t*.16*sp+k/bits.length)%1);for(let j=0;j<10;j++){const q=ray.at(Math.max(0,u-j*.004));x.globalAlpha=p*sp*(1-j/10);S.dot(q[0],q[1],5-j*.3,A)}}x.globalAlpha=p;
// normála a uhol pri jednom odraze
const qa=st(.9,.6);const rx=zz[3][0],ry=zz[3][1];x.globalAlpha=p*qa;x.save();x.setLineDash([5,5]);S.ln(rx,ry,rx,ry-86,'#fff',2);x.restore();
const a1=Math.atan2(zz[2][1]-ry,zz[2][0]-rx),a2=Math.atan2(zz[4][1]-ry,zz[4][0]-rx);x.strokeStyle='#fff';x.lineWidth=3;x.beginPath();x.arc(rx,ry,40,a1,-Math.PI/2);x.stroke();x.beginPath();x.arc(rx,ry,40,-Math.PI/2,a2);x.stroke();x.globalAlpha=p;
// príliš strmý lúč uniká
const qe=st(1.3,.6);if(qe>0){x.globalAlpha=p*qe*.8;const e=((t*.5)%1);S.ln(fl+40,cT+50,fl+90,cB,'#8a8a8a',3);S.ln(fl+90,cB,fl+90+(e)*70,cB+e*120,'#8a8a8a',3);x.globalAlpha=p}
// odkazy
const ql=st(.5,.6);x.globalAlpha=p*ql*(L0?1:0);S.ln(330,cB-14,330,410,'rgba(255,255,255,.5)',2);S.dot(330,cB-14,4,A);x.globalAlpha=p*ql*(L1?1:0);S.ln(600,mB-10,600,410,'rgba(255,255,255,.5)',2);S.dot(600,mB-10,4,'#fff');x.globalAlpha=p;
S.op(L0,ql);S.op(L1,ql);S.op(L2,st(.3,.5));S.txt(vT,'θ > '+NF(thc,1)+'°',st(1,.6));S.txt(vN,'n₁ = '+NF(n1,3)+'  ·  n₂ = '+NF(n2,3),st(1.1,.6))})};

// ---------- padák: odpor vzduchu vs. tiaž, ustálená rýchlosť. n=[hmotnosť kg, plocha m²] ----------
MECH3.parachute=(v,d)=>{const S=M3(v,d),{x,A}=S;const m=S.nn(0,90,.01,1e5),Ar=S.nn(1,40,.01,1e5);const g=9.81,rho=1.225;const vt=Math.sqrt(2*m*g/(rho*1.3*Ar)),vf=Math.sqrt(2*m*g/(rho*1*.7));
const px=210,gL=470,gR=840,gT=130,gB=420,T1=.3;
const L0=S.lab(0,px+90,70,200,'left',20,A),L1=S.lab(1,px+50,440,240,'left',20),L2=S.lab(2,gL-10,gT-40,220,'left',18,'#bdbdbd');
const vT=S.val(gL,gB-96,gR-gL,'right',40,A),vF=S.val(600,gT-6,200,'left',30,'#bdbdbd');
const vel=u=>u<T1?vf*Math.tanh(u/T1*2.2):vt+(vf*Math.tanh(2.2)-vt)*Math.exp(-(u-T1)*14);const ym=gB-(gB-gT)*1,yv=w=>gB-(gB-gT)*w/Math.max(vf,vt*1.1);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),bob=Math.sin(t*1.6)*6;const q=st(.7,.7);
// prúdenie vzduchu (padá → vzduch ide hore)
x.globalAlpha=p*sp;for(let k=0;k<7;k++){const X=40+k*60,y=560-((t*90+k*137)%600);S.ln(X,y,X,y+40,'rgba(255,255,255,.3)',2)}x.globalAlpha=p;
// vrchlík
const cy0=150+bob;x.beginPath();x.moveTo(px-120,cy0+30);x.quadraticCurveTo(px-120,cy0-70,px,cy0-74);x.quadraticCurveTo(px+120,cy0-70,px+120,cy0+30);
for(let k=6;k>=0;k--){const X=px-120+k*40;x.quadraticCurveTo(X+20,cy0+14,X,cy0+30)}x.fillStyle='#000';x.fill();x.strokeStyle='#fff';x.lineWidth=4;x.stroke();
for(let k=1;k<6;k++){const X=px-120+k*40;x.beginPath();x.moveTo(X,cy0+30);x.quadraticCurveTo(px+(X-px)*.6,cy0-50,px+(X-px)*.3,cy0-66);x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=2;x.stroke()}
// šnúry a parašutista
const hy=330+bob;for(let k=0;k<=6;k++)S.ln(px-120+k*40,cy0+30,px+(k-3)*3,hy-6,'rgba(255,255,255,.6)',2);
S.ci(px,hy+8,12,'#fff',4,'#000');S.ln(px,hy+20,px,hy+70,'#fff',5);S.ln(px,hy+30,px-26,hy+6,'#fff',4);S.ln(px,hy+30,px+26,hy+6,'#fff',4);S.ln(px,hy+70,px-16,hy+108,'#fff',4);S.ln(px,hy+70,px+16,hy+108,'#fff',4);
// sily
x.globalAlpha=p*q;S.ar(px+150,cy0+10,px+150,cy0-30-50*q,A,7);S.ar(px+70,hy+40,px+70,hy+90+50*q,'#fff',7);x.globalAlpha=p;
mv(L0,px+170,cy0-90-50*q);mv(L1,px+90,Math.min(500,hy+100+50*q-20));
// graf rýchlosti
const qg=st(.9,.8);x.globalAlpha=p*qg;S.ln(gL,gB,gR,gB,'#8a8a8a',2);S.ln(gL,gB,gL,gT,'#8a8a8a',2);x.save();x.setLineDash([5,6]);S.ln(gL,yv(vt),gR,yv(vt),'rgba(255,107,0,.6)',2);x.restore();
const T=cl((t-1.4)/4)*qg;x.lineWidth=4;[[0,T1,'#bdbdbd'],[T1,1,A]].forEach(([a,b,c])=>{x.beginPath();let f=1;for(let j=Math.round(a*100);j<=Math.min(b,T)*100;j++){const u=j/100,X=gL+(gR-gL)*u,Y=yv(vel(u));f?x.moveTo(X,Y):x.lineTo(X,Y);f=0}x.strokeStyle=c;x.stroke()});
if(T>0){const u=T,X=gL+(gR-gL)*u,Y=yv(vel(u));S.ci(X,Y,7,A,3,'#000')}x.globalAlpha=p;
S.op(L0,q);S.op(L1,q);S.op(L2,qg);S.txt(vF,S.f1(vf)+' m/s',cl((t-2)/.6));S.txt(vT,S.f1(vt)+' m/s',cl((t-3.2)/.6))})};

// ---------- bicykel: reťazový prevod. n=[zuby prevodníka, zuby pastorka, obvod kolesa m] ----------
MECH3.bicycle=(v,d)=>{const S=M3(v,d),{x,A}=S;const z1=Math.round(S.nn(0,44,10,80)),z2=Math.round(S.nn(1,16,8,60)),cir=S.nn(2,2.1,.5,10);const i=z1/z2,dist=i*cir;
const W=[220,300],Rw=170,C=[540,330],k=2.2,r1=z1*k*1.04,r2=z2*k*1.04;
const L0=S.lab(0,C[0]-120,C[1]+r1+30,240,'center',20,A),L1=S.lab(1,W[0]-150,W[1]+Rw+12,300,'center',20),L2=S.lab(2,648,250,214,'center',15,'#bdbdbd');
const vI=S.val(660,110,200,'center',44,A),vX=S.val(660,166,200,'center',28,'#bdbdbd'),vD=S.val(660,284,200,'center',44);
// reťaz: vonkajšie dotyčnice
const dx=C[0]-W[0],dy=C[1]-W[1],dd=Math.hypot(dx,dy),ux=dx/dd,uy=dy/dd,s=(r2-r1)/dd,h=Math.sqrt(Math.max(0,1-s*s));
const nU=[s*ux-h*uy,s*uy+h*ux],nL=[s*ux+h*uy,s*uy-h*ux];
const chainPts=(()=>{const P=[];const aU1=Math.atan2(nU[1],nU[0]),aL1=Math.atan2(nL[1],nL[0]);
// okolo pastorka (vľavo) z dolnej na hornú cez ľavú stranu
let a=aL1,b=aU1;while(b>a)b-=6.2832;for(let j=0;j<=20;j++){const q=a+(b-a)*j/20;P.push([W[0]+Math.cos(q)*r2,W[1]+Math.sin(q)*r2])}
let c1=aU1,c2=aL1;while(c2>c1)c2-=6.2832;for(let j=0;j<=30;j++){const q=c1+(c2-c1)*j/30;P.push([C[0]+Math.cos(q)*r1,C[1]+Math.sin(q)*r1])}return P})();
const chain=S.path(chainPts,true);
return RUN(S,(t,st,p)=>{const sp=cl(st(.3,1)),w=t*1.4*sp;
// koleso
S.ci(W[0],W[1],Rw,'#fff',5);S.ci(W[0],W[1],Rw-14,'rgba(255,255,255,.5)',2);x.save();x.translate(W[0],W[1]);x.rotate(w*i);for(let j=0;j<16;j++){const a=j*Math.PI/8;S.ln(Math.cos(a)*r2*.6,Math.sin(a)*r2*.6,Math.cos(a+.2)*(Rw-14),Math.sin(a+.2)*(Rw-14),'rgba(255,255,255,.3)',1.5)}x.restore();
// rám
x.globalAlpha=p*.6;S.ln(W[0],W[1],C[0],C[1],'#8a8a8a',6);S.ln(W[0],W[1],C[0]-80,120,'#8a8a8a',6);S.ln(C[0],C[1],C[0]-80,120,'#8a8a8a',6);x.globalAlpha=p;
// ozubené kolesá
S.gear(W[0],W[1],r2,z2,w*i,'#fff',5);S.gear(C[0],C[1],r1,z1,w,A,5);
// reťaz
chain.draw('#bdbdbd',3);const nl=Math.round(chain.tot/14);for(let j=0;j<nl;j++){const q=chain.at(j/nl+w*r1/chain.tot);S.dot(q[0],q[1],3.5,'#fff')}
// kľuka a pedál
const ca=w,ex=C[0]+Math.cos(ca)*110,ey=C[1]+Math.sin(ca)*110;S.ln(C[0],C[1],ex,ey,'#fff',8);S.rc(ex-20,ey-7,40,14,'#fff',3,'#000');S.ci(C[0],C[1],10,'#fff',3,'#000');
S.op(L0,st(.4,.6));S.op(L1,st(.6,.6));S.txt(vI,z1+' : '+z2,st(.9,.6));S.txt(vX,'× '+NF(i,2),st(1.1,.6));S.op(L2,st(1.3,.6));S.txt(vD,S.f1(dist)+' m',st(1.3,.6))})};

const _m2=V.mech;V.mech=(v,d)=>MECH3[d&&d.m]?MECH3[d.m](v,d):_m2(v,d);
}
