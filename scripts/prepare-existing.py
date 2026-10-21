#!/usr/bin/env python3
import sys, subprocess
from pathlib import Path
tree=Path(sys.argv[1])
p=tree/'feeds/luci/applications/luci-app-passwall/root/etc/init.d/passwall'
s=p.read_text();old='\t/etc/init.d/qca-nss-ecm stop\n';assert s.count(old)==2
s=s.replace(old,'\t/etc/init.d/qca-nss-ecm start\n');p.write_text(s)
p=tree/'feeds/nss_packages/qca-nss-ecm/files/qca-nss-ecm.init'
s=p.read_text();old=' [ "$(uci -q get passwall.@global[0].enabled)" = 1 ] && return 0\n';assert s.count(old)==1
s=s.replace(old,'');p.write_text(s)
p=tree/'feeds/luci/applications/luci-app-passwall/root/usr/share/passwall/nftables.sh'
s=p.read_text()
for anchor in ['\nstart() {', '\nstop() {']:
 assert s.count(anchor)==1
 s=s.replace(anchor,anchor+'\n\t/usr/sbin/ax9000-ecm-flush')
for anchor in ['\n\tgen_include\n}', '\n\tflush_include\n}']:
 assert s.count(anchor)==1
 s=s.replace(anchor,anchor[:-2]+'\n\t/usr/sbin/ax9000-ecm-flush\n}')
anchor='\n\t${__nft}\n\n\treturn 0';assert s.count(anchor)==1
s=s.replace(anchor,'\n\t${__nft}\n\t/usr/sbin/ax9000-ecm-flush\n\n\treturn 0');p.write_text(s)
for p in [tree/'feeds/luci/applications/luci-app-passwall/root/etc/init.d/passwall',p,tree/'feeds/nss_packages/qca-nss-ecm/files/qca-nss-ecm.init']:
 subprocess.run(['sh','-n',str(p)],check=True)
print('Coexist hooks: ECM start retained; no PassWall ECM stop/unload; rule-change flushes installed.')
