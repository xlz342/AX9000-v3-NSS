#!/usr/bin/env python3
import sys,json,tarfile,tempfile,subprocess,hashlib,os
from pathlib import Path
tree,out=map(Path,sys.argv[1:3]); image=next(out.glob('*sysupgrade.bin'))
packages={line.split(' - ')[0] for line in next(out.glob('*.manifest')).read_text().splitlines()}
required={'nikki','luci-app-nikki','mihomo-meta','smartdns','luci-app-smartdns','luci-theme-argon','luci-app-argon-config','openssh-server','luci-app-passwall','xray-core','luci-app-upnp','miniupnpd-nftables','kmod-wireguard','wireguard-tools','luci-proto-wireguard','airconnect','uuplugin'}
assert required<=packages,required-packages
report={'status':'offline-image-checks-passed; runtime-not-tested','packages':sorted(required),'checks':{}}
with tempfile.TemporaryDirectory() as tmp:
 squash=Path(tmp)/'root'
 with tarfile.open(image) as t:squash.write_bytes(t.extractfile('sysupgrade-xiaomi_ax9000-stock/root').read())
 def read(rel):return subprocess.check_output([str(tree/'staging_dir/host/bin/unsquashfs4'),'-cat',str(squash),rel])
 for name,paths in {'xray':['usr/bin/xray'],'mihomo':['usr/libexec/mihomo'],'smartdns':['usr/sbin/smartdns'],'wireguard':['usr/bin/wg'],'aircast':['usr/bin/aircast'],'airupnp':['usr/bin/airupnp'],'uuplugin':['usr/bin/uuplugin']}.items():
  data=read(paths[0]);assert data[:4]==b'\x7fELF' and int.from_bytes(data[18:20],'little')==183,name
  report['checks'][name]='ARM64 ELF present'
 for service in ['passwall','nikki']:
  data=read('etc/init.d/'+service).decode()
  assert 'qca-nss-ecm stop' not in data and 'rmmod ecm' not in data,service
  assert '/etc/init.d/qca-nss-ecm start' in data,service
  subprocess.run(['sh','-n'],input=data,text=True,check=True)
 ecm=read('etc/init.d/qca-nss-ecm').decode()
 assert 'get passwall.@global[0].enabled' not in ecm
 assert 'Nikki enabled: ECM remains stopped' not in ecm
 for name in ['airconnect','uuplugin','miniupnpd']:
  subprocess.run(['sh','-n'],input=read('etc/init.d/'+name),check=True)
 assert '/usr/sbin/ax9000-ecm-flush' in read('usr/share/passwall/nftables.sh').decode()
 assert '/usr/sbin/ax9000-ecm-flush' in read('etc/init.d/nikki').decode()
 release=read('etc/openwrt_release').decode()
 assert "DISTRIB_RELEASE='25.12.2'" in release
 report['checks']['coexist_hooks']='PassWall and Nikki start ECM; no stop/unload guards; nft flush hooks present'
 report['checks']['version']='25.12.2 without custom version suffix'
(out/'plugin-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
