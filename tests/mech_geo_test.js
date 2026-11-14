// Automatická kontrola presných modelov: kolesá do seba zapadajú bez prekrytia, rotor Wankela nikdy neprejde cez stenu komory,
// piest ostáva vo valci. Spustenie: node tests/mech_geo_test.js
const fs=require('fs'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','app','boards','zz_mech_pro.js'),'utf8');
const geo=src.split('//--GEO--')[1].split('//--END-GEO--')[0];
const G=new Function(geo+';return MECHGEO')();
let fail=0;const ok=(c,m)=>{if(!c){fail++;console.log('CHYBA:',m)}};
const inside=(p,P)=>{let c=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j];if((a[1]>p[1])!=(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c}return c};
const dist=(p,P)=>{let m=1e9;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j],dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));m=Math.min(m,Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy))}return m};
const rot=(P,a,cx,cy)=>P.map(q=>[cx+q[0]*Math.cos(a)-q[1]*Math.sin(a),cy+q[0]*Math.sin(a)+q[1]*Math.cos(a)]);
const dense=P=>{const o=[];for(let i=0;i<P.length;i++){const a=P[i],b=P[(i+1)%P.length];for(let k=0;k<4;k++)o.push([a[0]+(b[0]-a[0])*k/4,a[1]+(b[1]-a[1])*k/4])}return o};
// 1) ozubenie: pre rôzne počty zubov a natočenia nesmie zub vojsť do druhého kolesa viac než o 0,12 modulu, a kolesá sa musia dotýkať
let worst=0;
for(const [z1,z2] of [[9,9],[9,48],[12,30],[12,36],[16,16],[20,45],[24,36],[10,40],[13,17],[30,30],[48,48]]){const A=G.gearPts(z1),B=G.gearPts(z2),D=(z1+z2)/2;
 for(let s=0;s<24;s++){const w=s/24*2*Math.PI/z1*3.7;const P1=dense(rot(A,w,0,0)),P2=rot(B,G.meshRot(w,z1,z2,0),D,0);let pen=0;
  for(const p of P1){if(p[0]<z1/2-1.5)continue;if(inside(p,P2))pen=Math.max(pen,dist(p,P2))}
  let gap=1e9;for(const p of P1){if(p[0]>z1/2-1.5)gap=Math.min(gap,dist(p,P2))}ok(gap<.2,`kolesá ${z1}:${z2} sa nedotýkajú (medzera ${gap.toFixed(2)} modulu)`);
  if(s==0){const P3=rot(B,G.meshRot(w,z1,z2,0)+Math.PI/z2,D,0);let bad=0;for(const p of P1){if(p[0]>z1/2-1.5&&inside(p,P3))bad=Math.max(bad,dist(p,P3))}ok(bad>.2,'test ozubenia nič nemeria')}
  worst=Math.max(worst,pen);ok(pen<.12,`kolesá ${z1}:${z2} sa prekrývajú o ${pen.toFixed(3)} modulu (natočenie ${s})`)}}
console.log('ozubenie: najväčšie prekrytie',worst.toFixed(3),'modulu');
// 2) Wankel: bok rotora je vždy vnútri komory, vrcholy ležia presne na stene, objem komory sa mení aspoň 5x
for(const [R,e] of [[190,27],[105,15]]){const W=G.wankel(R,e);const H=[];for(let i=0;i<720;i++)H.push(W.house(i/720*2*Math.PI));let out=0,vmin=1e12,vmax=0;
 for(let s=0;s<360;s++){const fi=s/360*2*Math.PI;for(let k=0;k<3;k++){for(const p of W.flank(fi,k,24).slice(1,-1)){if(!inside(p,H))out=Math.max(out,dist(p,H))}
   const a=W.apex(fi,k);ok(dist(a,H)<.6,`Wankel: vrchol nie je na stene (${dist(a,H).toFixed(2)})`);const ar=W.area(W.chamber(fi,k,40));vmin=Math.min(vmin,ar);vmax=Math.max(vmax,ar)}}
 ok(out<.5,`Wankel R=${R}: rotor prechádza cez stenu o ${out.toFixed(2)} px`);ok(vmax/vmin>5,`Wankel: malý kompresný pomer ${(vmax/vmin).toFixed(1)}`);console.log(`Wankel R=${R}: presah ${out.toFixed(2)} px, pomer objemov ${(vmax/vmin).toFixed(1)}`)}
// 3) kľuka: zdvih = 2r, v úvratiach 0 a 2r
{const r=56,l=176;ok(Math.abs(G.crank(0,r,l).drop)<1e-9,'kľuka: horná úvrať');ok(Math.abs(G.crank(Math.PI,r,l).drop-2*r)<1e-9,'kľuka: dolná úvrať');
 for(let i=0;i<360;i++){const k=G.crank(i/360*2*Math.PI,r,l);ok(Math.abs(Math.hypot(k.px,k.py-(-r-l+k.drop))-l)<1e-6,'kľuka: dĺžka ojnice sa mení')}}
console.log(fail?`ZLYHALO: ${fail}`:'VŠETKO V PORIADKU');process.exit(fail?1:0);
