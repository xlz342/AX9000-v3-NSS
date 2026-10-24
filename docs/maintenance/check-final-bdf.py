import ast, io, pathlib, shutil, subprocess, tarfile, tempfile
source = pathlib.Path('outputs/AX9000-v3-NSS/scripts/validate-image.py').read_text()
nodes = ast.parse(source).body
block = next(n for n in nodes if isinstance(n, ast.With) and 'TemporaryDirectory' in ast.unparse(n.items[0].context_expr))
code = compile(ast.Module(body=[block], type_ignores=[]), '<final-bdf-check>', 'exec')
with tempfile.TemporaryDirectory() as tmp:
    tree = pathlib.Path(tmp)
    tool = tree/'staging_dir/host/bin/unsquashfs4'
    tool.parent.mkdir(parents=True)
    tool.symlink_to('/usr/bin/unsquashfs')
    root = tree/'root'
    bdf = root/'lib/firmware/ath11k/QCN9074/hw1.0/board-2.bin'
    bdf.parent.mkdir(parents=True)
    bdf.write_bytes(b'QCA-ATH11K\x00test board data')
    squash = tree/'root.squashfs'
    subprocess.run(['mksquashfs', str(root), str(squash), '-noappend', '-processors', '1'], check=True, stdout=subprocess.DEVNULL)
    image = tree/'sysupgrade.bin'
    prefix = 'sysupgrade-xiaomi_ax9000-stock/'
    with tarfile.open(image, 'w') as tar:
        tar.add(squash, arcname=prefix+'root')
    imported = tree/'imported'
    imported.write_bytes(bdf.read_bytes())
    env = dict(tree=tree, image=image, prefix=prefix, imported=imported, Path=pathlib.Path, tempfile=tempfile, tarfile=tarfile, shutil=shutil, subprocess=subprocess)
    exec(code, env)
    imported.write_bytes(b'wrong board')
    try:
        exec(code, env)
    except AssertionError:
        print('PASS: matching final squashfs BDF accepted; wrong BDF rejected')
    else:
        raise AssertionError('wrong board accepted')
