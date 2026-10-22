#!/usr/bin/env python3
"""Pinned-feed adaptations. Every edit has an exact, checked anchor."""
import sys
from pathlib import Path
tree = Path(sys.argv[1])
def edit(path, old, new):
    s = path.read_text()
    assert s.count(old) == 1, (path, old)
    path.write_text(s.replace(old, new))
alpha = tree/'package/feeds/nikki/mihomo-alpha'
assert alpha.is_symlink()
alpha.unlink()
ecm = tree/'feeds/nss_packages/qca-nss-ecm/files'
edit(ecm/'qca-nss-ecm.defaults', '    set firewall.qcanssecm.type=script',
     '    set firewall.qcanssecm.type=script\n    set firewall.qcanssecm.fw4_compatible=1')
(ecm/'qca-nss-ecm.firewall').write_text('#!/bin/sh\n/usr/sbin/ax9000-ecm-flush\n')
# v4 enables the service and passes the UCI choice directly to modprobe.
p = ecm/'qca-nss-ecm.init'
edit(p, '#!/bin/sh  /etc/rc.common', '#!/bin/sh /etc/rc.common')
s = p.read_text()
start = s.index('set_front_end() {')
end = s.index('load_ecm() {', start)
s = s[:start] + s[end:]
p.write_text(s)
edit(p, '    set_front_end $get_front_end_mode\n    modprobe ecm',
     '    modprobe ecm front_end_selection="$get_front_end_mode"')
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
