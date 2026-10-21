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
    'luci-app-passwall', 'xray-core', 'luci-app-upnp', 'miniupnpd-nftables',
    'luci-proto-wireguard', 'kmod-wireguard', 'wireguard-tools', 'airconnect', 'uuplugin',
}
assert required_packages <= packages, sorted(required_packages - packages)
assert not ({'nikki','luci-app-nikki','smartdns','luci-app-smartdns','luci-theme-argon','luci-app-argon-config'} & packages)
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
    rootfs = Path(tmp)/'rootfs'
    # Extract only acceptance inputs: unprivileged runners cannot create /dev nodes.
    # Keep extraction errors fatal; never suppress missing/corrupt firmware data.
    acceptance_paths = ['lib/modules', 'lib/firmware', 'etc/config/ecm',
                        'etc/config/nss', 'etc/init.d', 'etc/modules.d/ath11k',
                        'etc/rc.d', 'root/ax9000-v4-check.sh',
                        'usr/sbin/ax9000-wifi-nss', 'usr/sbin/ax9000-ecm-flush', 'usr/bin/uuplugin', 'usr/bin/aircast', 'usr/bin/airupnp']
    subprocess.run([str((tree/'staging_dir/host/bin/unsquashfs4').resolve()),
                    '-d', str(rootfs), str(squashfs), *acceptance_paths],
                   check=True, stdout=subprocess.DEVNULL)
    modules = {p.name.replace('-', '_'): p for p in (rootfs/'lib/modules').rglob('*.ko')}
    required_modules = ['qca_nss_drv', 'qca_nss_dp', 'ecm', 'qca_nss_bridge_mgr',
                        'qca_nss_vlan', 'qca_nss_pppoe', 'qca_nss_crypto', 'ath11k']
    for name in required_modules:
        assert name+'.ko' in modules, f'Missing module: {name}'
        assert modules[name+'.ko'].stat().st_size > 1024
    ath11k = modules['ath11k.ko'].read_bytes()
    assert b'parmtype=nss_offload:' in ath11k, 'ath11k NSS parameter absent'
    assert b'parmtype=frame_mode:' in ath11k, 'ath11k frame_mode parameter absent'
    assert (rootfs/'etc/modules.d/ath11k').read_text().strip() == 'ath11k nss_offload=1 frame_mode=2'
    assert "option acceleration_engine 'nss'" in (rootfs/'etc/config/ecm').read_text()
    assert list((rootfs/'etc/rc.d').glob('S*qca-nss-ecm')), 'ECM boot service disabled'
    for name in ['ax9000-nss-defaults', 'ax9000-wifi-pbuf']:
        assert list((rootfs/'etc/rc.d').glob('S*'+name)), name
    for rel in ['root/ax9000-v4-check.sh', 'usr/sbin/ax9000-wifi-nss', 'usr/sbin/ax9000-ecm-flush', 'usr/bin/uuplugin', 'usr/bin/aircast', 'usr/bin/airupnp']:
        assert (rootfs/rel).stat().st_mode & 0o111, rel
    assert (rootfs/'etc/config/nss').is_file()
    for core in [0, 1]:
        fw = rootfs/f'lib/firmware/qca-nss{core}-retail.bin'
        assert fw.is_file() and fw.stat().st_size > 100000, f'NSS core{core} firmware missing'
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
for name in ['profiles.json', 'config.buildinfo', 'feeds.buildinfo', 'version.buildinfo']:
    if (target/name).exists():
        shutil.copyfile(target/name, out/name)
(out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
(out/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))
print(json.dumps(report, indent=2))
