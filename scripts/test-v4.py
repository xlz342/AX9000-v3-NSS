#!/usr/bin/env python3
"""Host checks for persistent fallback, feed hooks and pinned source integrity."""
import ast
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import yaml
project=Path(__file__).resolve().parents[1]
for p in (project/'scripts').glob('*.py'):
    ast.parse(p.read_text(), filename=str(p))
for p in (project/'files').rglob('*'):
    if p.is_file() and p.read_bytes().startswith(b'#!/bin/sh'):
        subprocess.run(['sh','-n',str(p)],check=True)
workflow=yaml.safe_load((project/'.github/workflows/build.yml').read_text())
for step in workflow['jobs']['build']['steps']:
    if 'run' in step:
        subprocess.run(['bash','-n'],input=step['run'],text=True,check=True)
for directory in ['nss','wifi']:
    base=project/'vendor'/directory
    for rel,digest in json.loads((base/'manifest.json').read_text()).items():
        assert hashlib.sha256((base/rel).read_bytes()).hexdigest()==digest,rel
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/'etc/modules.d').mkdir(parents=True)
    params=root/'etc/modules.d/ath11k'
    params.write_text('ath11k nss_offload=1 frame_mode=2\n')
    source=(project/'files/usr/sbin/ax9000-wifi-nss').read_text()
    # Redirect filesystem paths only inside this isolated test fixture.
    source=source.replace('/etc/modules.d',str(root/'etc/modules.d'))
    source=source.replace('/sys/module/ath11k/parameters',str(root/'live'))
    script=root/'switch.sh';script.write_text(source)
    for mode,expected in [('off','ath11k nss_offload=0 frame_mode=1'),('on','ath11k nss_offload=1 frame_mode=2')]:
        subprocess.run(['sh',str(script),mode],check=True,capture_output=True)
        assert params.read_text().strip()==expected
    assert subprocess.run(['sh',str(script),'invalid'],capture_output=True).returncode==2
    before=params.read_bytes()
    status=subprocess.check_output(['sh',str(script),'status'],text=True)
    assert 'Next boot:' in status and 'unavailable' in status
    assert params.read_bytes()==before
print('PASS: source hashes, Python/Bash syntax, workflow, on/off persistence and read-only status.')
