#!/usr/bin/env python3
import re
import sys
from pathlib import Path

actual = Path(sys.argv[1]).read_text().splitlines()
seed = Path(sys.argv[2]).read_text().splitlines()
required = [s for s in seed if s.startswith('CONFIG_') and s.endswith('=y')]
missing = sorted(set(required) - set(actual))
devices = [s for s in actual if re.match(r'CONFIG_TARGET_.*_DEVICE_.*=y$', s)]
assert devices == ['CONFIG_TARGET_qualcommax_ipq807x_DEVICE_xiaomi_ax9000-stock=y'], devices
assert not missing, 'Kconfig dropped required options: ' + ', '.join(missing)
assert 'CONFIG_PACKAGE_kmod-qca-nss-cfi-cryptoapi=y' not in actual, 'Upstream marks CFI BROKEN'
print('Required packages/NSS options survived defconfig; official stock profile only.')
