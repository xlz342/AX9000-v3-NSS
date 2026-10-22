#!/usr/bin/env python3
import sys,shutil,subprocess,json
from pathlib import Path
tree=Path(sys.argv[1]); project=Path(__file__).resolve().parents[1]
def edit(path,old,new):
 s=path.read_text();assert s.count(old)==1,(path,old);path.write_text(s.replace(old,new))
# No Nikki guard is inserted into ECM and Nikki never stops/unloads ECM.
p = tree/'feeds/nikki/nikki/files/nikki.init'
edit(p, '\t\tutpl -S "$HIJACK_UT" | nft -f -', '''\t\t# AX9000-v4: render/check/apply before invalidating accelerated flows.
\t\tlocal nss_rules
\t\tnss_rules=$(mktemp "$TEMP_DIR/nss-nft.XXXXXX") || return 1
\t\tif ! utpl -S "$HIJACK_UT" > "$nss_rules" ||
\t\t   ! nft -c -f "$nss_rules" || ! nft -f "$nss_rules"; then
\t\t\trm -f "$nss_rules"
\t\t\tlog "Proxy" "Nftables installation failed."
\t\t\treturn 1
\t\tfi
\t\trm -f "$nss_rules"
\t\t/usr/sbin/ax9000-ecm-flush''')
s = p.read_text()
for line in s.splitlines():
    if line.lstrip().startswith(('ip -4 route add ', 'ip -6 route add ', 'ip -4 rule add ', 'ip -6 rule add ')):
        s = s.replace(line+'\n', line+' || return 1\n')
p.write_text(s)
# cleanup() covers stop/restart/reload; flush after removal finishes.
edit(p, '\n}\n\nclear_logs() {', '\n\t/usr/sbin/ax9000-ecm-flush\n}\n\nclear_logs() {')
# Avoid an intermediate flush from the TUN include inside service_started().
edit(p, '\t\t\t$FIREWALL_INCLUDE_SH', '\t\t\tAX9000_NSS_DEFER_FLUSH=1 $FIREWALL_INCLUDE_SH')
p = tree/'feeds/nikki/nikki/files/scripts/firewall_include.sh'
edit(p, 'exit 0', '[ "$AX9000_NSS_DEFER_FLUSH" = 1 ] || /usr/sbin/ax9000-ecm-flush\nexit 0')
print('Nikki rule installation/removal invalidates ECM after changes; ECM remains loaded.')

p=tree/'feeds/nikki/nikki/files/nikki.init'
edit(p,'\nstart_service() {','\nstart_service() {\n\t/etc/init.d/qca-nss-ecm start')
# Restore the full v4 overlay, retaining the cached stock/NSS/wireless sources.
shutil.copytree(project/'files',tree/'files',dirs_exist_ok=True)
for p in (tree/'files').rglob('*'):
 if p.is_file() and p.read_bytes().startswith(b'#!/bin/sh'): p.chmod(0o755)
for priority,name in [('18','ax9000-nss-defaults'),('26','qca-nss-ecm'),('95','ax9000-wifi-pbuf')]:
 p=tree/'files/etc/rc.d'/('S'+priority+name)
 if not p.is_symlink():p.symlink_to('../init.d/'+name)
for rel in ['etc/uci-defaults/zz-ax9000-local']:
 (tree/'files'/rel).unlink(missing_ok=True)
# The same fixed Argon sources as run 11.
lock=json.loads((project/'sources.lock.json').read_text())
for key,name in [('argon','luci-theme-argon'),('argon_config','luci-app-argon-config')]:
 p=tree/'package/custom'/name
 link=tree/'package/feeds/luci'/name
 if link.is_symlink():link.unlink()
 if not p.exists():subprocess.run(['git','clone','--depth','1','https://github.com/jerrykuku/'+name+'.git',str(p)],check=True)
 subprocess.run(['git','-C',str(p),'fetch','--depth','1','origin',lock[key]],check=True)
 subprocess.run(['git','-C',str(p),'checkout','--detach',lock[key]],check=True)
for rel in ['feeds/nikki/nikki/files/nikki.init','feeds/nikki/nikki/files/scripts/firewall_include.sh']:
 subprocess.run(['sh','-n',str(tree/rel)],check=True)
