#!/usr/bin/env python3
import sys
from pathlib import Path

tree = Path(sys.argv[1])
# The pinned feed's two providers have symmetric CONFLICTS, producing a
# recursive Kconfig dependency in this release. This project uses stable meta
# only, so exclude the unused alpha recipe from package discovery entirely.
alpha = tree / 'package/feeds/nikki/mihomo-alpha'
assert alpha.is_symlink()
alpha.unlink()
ecm = tree / 'feeds/nss_packages/qca-nss-ecm/files'
# fw4 explicitly rejects script includes without fw4_compatible=1.
p = ecm / 'qca-nss-ecm.defaults'
s = p.read_text()
anchor = '    set firewall.qcanssecm.type=script'
assert s.count(anchor) == 1
p.write_text(s.replace(anchor, anchor + '\n    set firewall.qcanssecm.fw4_compatible=1'))
# Drop the upstream optional packet rate limiter. It is not the ECM hook;
# using it as an acceleration fix would also limit legitimate NEW connections.
# Instead invalidate accelerated connections each time firewall4 rebuilds rules.
(ecm / 'qca-nss-ecm.firewall').write_text('''#!/bin/sh
[ -w /sys/kernel/debug/ecm/ecm_db/defunct_all ] &&
    echo 1 > /sys/kernel/debug/ecm/ecm_db/defunct_all
exit 0
''')
# Refuse to load ECM alongside Nikki. This also handles preserved sysupgrade
# settings and a manual ECM start after Nikki has been enabled.
p = ecm / 'qca-nss-ecm.init'
s = p.read_text()
anchor = 'start_service() {'
assert s.count(anchor) == 1
p.write_text(s.replace(anchor, anchor + '''
  if [ "$(uci -q get nikki.config.enabled)" = "1" ] || pidof mihomo >/dev/null; then
    logger -t AX9000-NSS "Nikki enabled: ECM remains stopped to preserve proxy rules"
    return 0
  fi
'''))
# Stop acceleration before any proxy process/rules are started, including the
# transition from a previously accelerated NAT-only session.
p = tree / 'feeds/nikki/nikki/files/nikki.init'
s = p.read_text()
anchor = '\tlog "App" "Enabled."'
assert s.count(anchor) == 1
p.write_text(s.replace(anchor, '''
\t/etc/init.d/qca-nss-ecm stop || return 1
\tif [ -d /sys/module/ecm ]; then
\t\tlogger -t AX9000-NSS "ECM could not unload; refusing to start Nikki"
\t\treturn 1
\tfi
''' + anchor))
