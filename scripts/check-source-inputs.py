#!/usr/bin/env python3
"""Reject unexpected tracked inputs before any build or artifact upload."""
import subprocess
from pathlib import PurePosixPath
names = subprocess.check_output(['git', 'ls-files', '-z'], text=True).split('\0')
allowed = {'.github', 'scripts', 'config', 'files', 'inputs', 'vendor', 'reference'}
top = {'.gitignore', '.gitattributes', 'README.md', 'sources.lock.json'}
for name in filter(None, names):
    path = PurePosixPath(name)
    assert name in top or path.parts[0] in allowed, f'Unexpected source: {name}'
    assert not any(s in name.lower() for s in ['restore-ready', 'backup', 'private', 'credential']), name
    if path.parts[0] == 'inputs':
        assert name == 'inputs/generic-ax9000.tar.gz', name
    if name.endswith(('.tar.gz', '.bin', '.ubi', '.key')):
        assert name == 'inputs/generic-ax9000.tar.gz', name
print('Tracked source allowlist passed; only the audited BDF archive is accepted.')
