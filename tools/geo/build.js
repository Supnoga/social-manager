const fs=require('fs'),ts=require('topojson-server'),tsim=require('topojson-simplify'),tc=require('topojson-client');
const g=JSON.parse(fs.readFileSync('pov10_deu.geojson'));
g.features=g.features.map(f=>{const p=f.properties;let id=p.ISO_A2_EH!='-99'?p.ISO_A2_EH:p.ADM0_A3;
return {type:'Feature',id,properties:{n:p.NAME_EN||p.NAME,ct:p.CONTINENT,sr:p.SUBREGION,lx:+p.LABEL_X.toFixed(2),ly:+p.LABEL_Y.toFixed(2)},geometry:f.geometry}});
let t=ts.topology({c:g},1e5);t=tsim.presimplify(t);
const W=+process.argv[2]||0.0005;t=tsim.simplify(t,W);t=tsim.filter(t,tsim.filterWeight(t,W));
// quantize
const tq=require('topojson-client').quantize(t,1e5);
fs.writeFileSync('world.json',JSON.stringify(tq));
console.log(fs.statSync('world.json').size);
