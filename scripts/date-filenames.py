import sys,json
from pathlib import Path
out=Path(sys.argv[1]); names={}
for p in out.iterdir():
 if p.name.startswith('immortalwrt-25.12.2-') and p.suffix in ['.bin','.ubi','.manifest']:
  name=p.name.replace('immortalwrt-25.12.2-','immortalwrt-25.12.2-20261022-',1)
  names[p.name]=name;p.rename(p.with_name(name))
def rename(value):
 if isinstance(value,str):return names.get(value,value)
 if isinstance(value,list):return [rename(v) for v in value]
 if isinstance(value,dict):return {k:rename(v) for k,v in value.items()}
 return value
for p in out.glob('*.json'):
 p.write_text(json.dumps(rename(json.loads(p.read_text())),indent=2)+'\n')
