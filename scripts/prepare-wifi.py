#!/usr/bin/env python3
"""Import hash-locked, reviewed WiFi patches; reject any upstream overlap."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
project = Path(__file__).resolve().parents[1]
tree = Path(sys.argv[1]).resolve()
vendor = project/'vendor/wifi'
for rel, digest in json.loads((vendor/'manifest.json').read_text()).items():
    assert hashlib.sha256((vendor/rel).read_bytes()).hexdigest() == digest, rel
assert 'PKG_VERSION:=6.18.39' in (tree/'package/kernel/mac80211/Makefile').read_text()
dest = tree/'package/kernel/mac80211/patches/nss'
assert not dest.exists()
shutil.copytree(vendor/'patches', dest)
subprocess.run(['patch', '-p1', '--batch', '--forward', '--fuzz=0', '-i', str(vendor/'recipe.patch')], cwd=tree, check=True)
print('Pinned ath11k/mac80211 NSS patches imported; backports version unchanged.')
