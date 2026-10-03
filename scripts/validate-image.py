#!/usr/bin/env python3
"""Validate only official stock outputs, publish only after all checks pass."""
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

tree, out = map(Path, sys.argv[1:3])
project = Path(__file__).resolve().parents[1]
target = tree / 'bin/targets/qualcommax/ipq807x'
images = list(target.glob('*-xiaomi_ax9000-stock-squashfs-sysupgrade.bin'))
assert len(images) == 1, images
image = images[0]
assert 8 * 1024**2 < image.stat().st_size < 128 * 1024**2, 'Unexpected image size'
metadata_file = target / 'validated-metadata.json'
fwtool = tree / 'staging_dir/host/bin/fwtool'
subprocess.run([str(fwtool.resolve()), '-i', str(metadata_file), str(image)], check=True)
meta = json.loads(metadata_file.read_text())
assert meta['supported_devices'] == ['xiaomi,ax9000-stock'], meta
assert meta['version']['target'] == 'qualcommax/ipq807x'
assert meta['version']['board'] == 'xiaomi_ax9000-stock'
assert meta['version']['version'] == '25.12.2'
assert meta['version']['dist'] == 'ImmortalWrt'
with tarfile.open(image) as tar:
    members = {m.name: m for m in tar.getmembers()}
    prefix = 'sysupgrade-xiaomi_ax9000-stock/'
    assert set(members) == {prefix.rstrip('/'), prefix+'CONTROL', prefix+'kernel', prefix+'root'}, members
    kernel, root = members[prefix+'kernel'], members[prefix+'root']
    assert kernel.isfile() and root.isfile() and kernel.size > 1024**2 and root.size > 1024**2
    assert tar.extractfile(kernel).read(4) == bytes.fromhex('d00dfeed'), 'Expected FIT kernel'
    assert tar.extractfile(root).read(4) == b'hsqs', 'Expected squashfs rootfs'
    sizes = {'kernel': kernel.size, 'squashfs': root.size}
# Capacity estimate uses the supplied MIBIB, with UBI overhead and overlay reserve.
# This is not a claim about the router's currently active MTD/UBI table.
audit = json.loads((project/'reference/input-audit.json').read_text())
parts = audit['mibib_system_partition_table']['entries']
partition = next(p for p in parts if p['name'] == 'rootfs')
capacity = partition['length_blocks'] * 131072
required = sum(math.ceil(n / 126976) * 131072 for n in sizes.values()) + 16 * 1024**2
assert required < capacity * .95, 'Not enough UBI/overlay headroom'
manifest = target / image.name.replace('-squashfs-sysupgrade.bin', '.manifest')
assert manifest.exists(), manifest
packages = {line.split(' - ')[0] for line in manifest.read_text().splitlines()}
required_packages = {
    'kmod-qca-nss-dp', 'kmod-qca-nss-drv', 'kmod-qca-nss-ecm',
    'kmod-qca-nss-drv-bridge-mgr', 'kmod-qca-nss-drv-vlan-mgr',
    'kmod-qca-nss-drv-pppoe', 'kmod-qca-nss-crypto', 'nss-eip-firmware',
    'nss-firmware-ipq807x', 'kmod-ath11k-ahb', 'kmod-ath11k-pci',
    'ath11k-firmware-qcn9074', 'ipq-wifi-xiaomi_ax9000', 'firewall4',
    'luci-theme-argon', 'luci-app-argon-config', 'nikki', 'luci-app-nikki',
    'smartdns', 'openssh-server', 'openssh-keygen',
}
assert required_packages <= packages, sorted(required_packages - packages)
for rel, digest in json.loads((tree / 'protected-source.json').read_text()).items():
    assert hashlib.sha256((tree / rel).read_bytes()).hexdigest() == digest, rel
# Verify the board data actually ended up in the generated squashfs.
imported = tree/'package/firmware/ipq-wifi/src/board-xiaomi_ax9000.qcn9074'
# ipq-wifi installs into rootfs-overlay, applied per device during image creation.
# The shared root-qualcommax directory still contains the generic firmware BDF.
# Check the actual squashfs inside the sysupgrade archive, not that staging tree.
with tempfile.TemporaryDirectory() as tmp:
    squashfs = Path(tmp) / 'root.squashfs'
    with tarfile.open(image) as tar:
        with squashfs.open('wb') as stream:
            shutil.copyfileobj(tar.extractfile(prefix+'root'), stream)
    board = subprocess.check_output([
        str((tree/'staging_dir/host/bin/unsquashfs4').resolve()), '-cat',
        str(squashfs), 'lib/firmware/ath11k/QCN9074/hw1.0/board-2.bin',
    ])
    assert board == imported.read_bytes(), 'QCN9074 BDF override missing from final squashfs'
factories = list(target.glob('*-xiaomi_ax9000-stock-squashfs-factory.ubi'))
assert len(factories) <= 1
for factory in factories:
    assert factory.read_bytes()[:4] == b'UBI#', 'Expected UBI factory image'
    assert factory.stat().st_size < capacity * .95
report = {
    'status': 'build-validated; hardware acceptance pending',
    'metadata': meta, 'sizes': sizes, 'image_bytes': image.stat().st_size,
    'reference_partition_bytes': capacity, 'estimated_with_overlay_bytes': required,
    'factory': [p.name for p in factories],
    'notes': ['U-Boot image-format acceptance must be tested on the actual bootloader.',
              'No runtime NSS, RF performance or proxy benchmarks performed by CI.'],
}
out.mkdir(parents=True, exist_ok=True)
for p in [image, manifest, metadata_file, *factories]:
    shutil.copyfile(p, out / p.name)
for name in ['profiles.json', 'sha256sums', 'config.buildinfo', 'feeds.buildinfo', 'version.buildinfo']:
    if (target/name).exists():
        shutil.copyfile(target/name, out/name)
(out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
(out/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))
print(json.dumps(report, indent=2))
