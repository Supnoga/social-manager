// mená krajín vo všetkých jazykoch appky (i18n-iso-countries, MIT)
const fs=require('fs');const L=process.argv[2].split(',');const out={};
for(const l of L){let f='i18n-iso-countries/langs/'+(l=='no'?'nb':l)+'.json';let d;try{d=require(f).countries}catch(e){continue}
 const m={};for(const [c,v] of Object.entries(d)){const arr=(Array.isArray(v)?v:[v]).map(x=>x.split(',')[0].trim()).filter(x=>!/\./.test(x));
  const good=arr.filter(x=>x.length>=4);m[c]=(good.length?good:arr).sort((a,b)=>a.length-b.length)[0]||arr[0];
  if(l=='en')m['_all_'+c]=(Array.isArray(v)?v:[v]);}
 out[l]=m}
fs.writeFileSync('names.json',JSON.stringify(out));
