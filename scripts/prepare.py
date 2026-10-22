#!/usr/bin/env python3
"""Import audited NSS support without replacing the official device target."""
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

project = Path(__file__).resolve().parents[1]
tree = Path(sys.argv[1]).resolve()
lock = json.loads((project / 'sources.lock.json').read_text())
assert subprocess.check_output(['git', '-C', str(tree), 'rev-parse', 'HEAD'], text=True).strip() == lock['immortalwrt']
assert 'KERNEL_PATCHVER:=6.12' in (tree / 'target/linux/qualcommax/Makefile').read_text()
protected = [
    'target/linux/qualcommax/image/ipq807x.mk',
    'target/linux/qualcommax/image/Makefile',
    'target/linux/qualcommax/files/arch/arm64/boot/dts/qcom/ipq8072-ax9000-stock.dts',
    'target/linux/qualcommax/ipq807x/base-files/lib/upgrade/platform.sh',
    'target/linux/qualcommax/ipq807x/base-files/etc/hotplug.d/firmware/11-ath11k-caldata',
]
before = {p: hashlib.sha256((tree / p).read_bytes()).hexdigest() for p in protected}
vendor = project / 'vendor/nss'
for rel, digest in json.loads((vendor / 'manifest.json').read_text()).items():
    source = vendor / rel
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, rel
    target = tree / rel
    assert not target.exists(), f'Unexpected upstream overlap: {rel}'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
# Only add NSS hardware nodes to the official parent DTS. Partition/calibration
# content remains byte-for-byte intact; the stock child continues to use SMEM.
dts = tree / 'target/linux/qualcommax/files/arch/arm64/boot/dts/qcom/ipq8072-ax9000.dts'
text = dts.read_text()
anchor = '#include "ipq8074-ess.dtsi"'
assert text.count(anchor) == 1
dts.write_text(text.replace(anchor, anchor + '\n#include "ipq8074-nss.dtsi"'))
cfg = tree / 'target/linux/qualcommax/config-6.12'
# OpenWrt keeps a complete kernel seed and uses syncconfig without stdin.
# Explicitly answer every visible recycler prompt: kernel defaults alone still
# count as NEW and abort a non-interactive build before any compilation.
cfg.write_text(cfg.read_text() + '''
CONFIG_SKB_RECYCLER=y
CONFIG_SKB_RECYCLER_MULTI_CPU=y
# CONFIG_SKB_RECYCLER_PREALLOC is not set
CONFIG_SKB_RECYCLE_SIZE=2304
# CONFIG_ALLOC_SKB_PAGE_FRAG_DISABLE is not set
''')
# Import exactly one regular file, never blindly extract an untrusted archive.
archive = project / 'inputs/generic-ax9000.tar.gz'
audit = json.loads((project / 'reference/input-audit.json').read_text())
assert hashlib.sha256(archive.read_bytes()).hexdigest() == audit[archive.name]['sha256']
with tarfile.open(archive) as tar:
    entries = tar.getmembers()
    assert len(entries) == 1 and entries[0].isfile()
    assert entries[0].name == 'lib/firmware/ath11k/QCN9074/hw1.0/board-2.bin'
    board = tar.extractfile(entries[0]).read()
    assert board.startswith(b'QCA-ATH11K'), 'Invalid ath11k board data header'
    # This release's Build/Prepare/Default copies ./src, not ./files.
    target = tree / 'package/firmware/ipq-wifi/src/board-xiaomi_ax9000.qcn9074'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(board)
subprocess.run([sys.executable, str(project/'scripts/prepare-wifi.py'), str(tree)], check=True)
shutil.copytree(project / 'files', tree / 'files', dirs_exist_ok=True)
for rel in ['etc/uci-defaults/zz-ax9000-v4', 'usr/sbin/ax9000-wifi-nss', 'usr/sbin/ax9000-ecm-flush', 'root/ax9000-v4-check.sh', 'etc/init.d/ax9000-nss-defaults', 'etc/init.d/ax9000-wifi-pbuf']:
    (tree / 'files' / rel).chmod(0o755)
rc = tree/'files/etc/rc.d'
rc.mkdir(parents=True, exist_ok=True)
for priority, name in [('18', 'ax9000-nss-defaults'), ('26', 'qca-nss-ecm'), ('95', 'ax9000-wifi-pbuf')]:
    (rc/('S'+priority+name)).symlink_to('../init.d/'+name)
for p, digest in before.items():
    assert hashlib.sha256((tree / p).read_bytes()).hexdigest() == digest, p
(tree / 'protected-source.json').write_text(json.dumps(before, indent=2) + '\n')
print('Official stock target and upgrade logic preserved; NSS and QCN9074 BDF imported.')
