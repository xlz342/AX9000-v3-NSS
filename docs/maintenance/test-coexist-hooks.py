from pathlib import Path
import tempfile, shutil,subprocess
base=Path('/var/tmp/ax9000-local-20261022/build')
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 for rel in ['feeds/luci/applications/luci-app-passwall/root/etc/init.d/passwall','feeds/luci/applications/luci-app-passwall/root/usr/share/passwall/nftables.sh','feeds/nss_packages/qca-nss-ecm/files/qca-nss-ecm.init']:
  p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/rel,p)
 subprocess.run(['python3','/var/tmp/ax9000-local-20261022/coexist-project/scripts/prepare-existing.py',tmp],check=True)
