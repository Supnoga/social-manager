const fs=require('fs'),ts=require('topojson-server'),tsim=require('topojson-simplify'),tc=require('topojson-client');
const src=process.argv[2],out=process.argv[3],W=+process.argv[4]||0.01;
const g=JSON.parse(fs.readFileSync(src));
g.features=g.features.filter(f=>f.geometry&&f.properties&&f.properties.NAME).map(f=>({type:'Feature',properties:{n:f.properties.NAME.trim(),s:(f.properties.SUBJECTO||'').trim(),b:f.properties.BORDERPRECISION||1},geometry:f.geometry}));
let t=ts.topology({h:g},1e5);t=tsim.presimplify(t);t=tsim.simplify(t,W);t=tsim.filter(t,tsim.filterWeight(t,W));t=tc.quantize(t,1e4);
fs.writeFileSync(out,JSON.stringify(t));
