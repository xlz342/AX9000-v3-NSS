#!/usr/bin/env python3
"""Exercise the actual image acceptance block with an unprivileged squashfs fixture."""
import ast
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

assert __import__('os').geteuid() != 0, 'Run this regression as an unprivileged user'
source = Path(__file__).with_name('validate-image.py').read_text()
block = next(n for n in ast.parse(source).body if isinstance(n, ast.With)
             and 'tempfile.TemporaryDirectory()' in ast.unparse(n.items[0].context_expr))
with tempfile.TemporaryDirectory() as tmp:
    tree = Path(tmp)
    root = tree/'fixture'
    def put(rel, data, executable=False):
        path = root/rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if executable:
            path.chmod(0o755)
        return path
    board = b'AX9000 regression board data'
    put('lib/firmware/ath11k/QCN9074/hw1.0/board-2.bin', board)
    names = ['qca_nss_drv', 'qca_nss_dp', 'ecm', 'qca_nss_bridge_mgr',
             'qca_nss_vlan', 'qca_nss_pppoe', 'qca_nss_crypto', 'ath11k']
    for name in names:
        put('lib/modules/test/'+name+'.ko', b'x'*2048 + b'parmtype=nss_offload:int\0parmtype=frame_mode:int\0')
    for core in [0, 1]:
        put(f'lib/firmware/qca-nss{core}-retail.bin', b'x'*100001)
    put('etc/modules.d/ath11k', b'ath11k nss_offload=1 frame_mode=2\n')
    put('etc/config/ecm', b"option acceleration_engine 'nss'\n")
    put('etc/config/nss', b'config general\n')
    put('etc/init.d/nikki', b'ax9000-ecm-flush\n', True)
    for name in ['qca-nss-ecm', 'ax9000-nss-defaults', 'ax9000-wifi-pbuf']:
        put('etc/init.d/'+name, b'#!/bin/sh\n', True)
        link = root/'etc/rc.d'/('S26'+name)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to('../init.d/'+name)
    for rel in ['root/ax9000-v4-check.sh', 'usr/sbin/ax9000-wifi-nss', 'usr/sbin/ax9000-ecm-flush']:
        put(rel, b'#!/bin/sh\n', True)
    (root/'dev').mkdir()
    squashfs = tree/'fixture.squashfs'
    subprocess.run(['mksquashfs', str(root), str(squashfs), '-noappend',
                    '-processors', '1', '-quiet', '-p', 'dev/console c 0600 0 0 5 1'], check=True)
    # Prove this fixture reproduces the original failure; it must not pass silently.
    old = subprocess.run(['unsquashfs', '-d', str(tree/'old'), str(squashfs)], capture_output=True)
    assert old.returncode != 0 and b'console' in old.stderr, old.stderr
    imported = tree/'board.bin'
    imported.write_bytes(board)
    host = tree/'staging_dir/host/bin'
    host.mkdir(parents=True)
    (host/'unsquashfs4').symlink_to(shutil.which('unsquashfs'))
    image = tree/'sysupgrade.bin'
    prefix = 'sysupgrade-xiaomi_ax9000-stock/'
    with tarfile.open(image, 'w') as tar:
        tar.add(squashfs, arcname=prefix+'root')
    context = dict(tree=tree, image=image, imported=imported, prefix=prefix,
                   tempfile=tempfile, Path=Path, tarfile=tarfile, shutil=shutil, subprocess=subprocess)
    exec(compile(ast.Module(body=[block], type_ignores=[]), 'acceptance-block', 'exec'), context)
    # A missing mandatory module must still be rejected by the same validator.
    (root/'lib/modules/test/ecm.ko').unlink()
    squashfs.unlink()
    subprocess.run(['mksquashfs', str(root), str(squashfs), '-noappend',
                    '-processors', '1', '-quiet', '-p', 'dev/console c 0600 0 0 5 1'], check=True)
    with tarfile.open(image, 'w') as tar:
        tar.add(squashfs, arcname=prefix+'root')
    try:
        exec(compile(ast.Module(body=[block], type_ignores=[]), 'acceptance-block', 'exec'), context)
    except AssertionError as error:
        assert str(error) == 'Missing module: ecm', error
    else:
        raise AssertionError('Missing ECM module was accepted')
print('PASS: device-node failure reproduced, all acceptance inputs checked, missing ECM rejected')
