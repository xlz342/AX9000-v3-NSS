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

print('ECM nftables hook retained; PassWall uses conservative ECM bypass while enabled.')
