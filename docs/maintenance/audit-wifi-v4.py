import hashlib, pathlib, subprocess, tarfile, urllib.request, shutil
root=pathlib.Path(__file__).resolve().parents[1]
out=pathlib.Path('/var/tmp/ax9000-v4-wifi-audit')
out.mkdir(exist_ok=True)
archive=out/'backports-6.18.39.tar.zst'
if not archive.exists():
    urllib.request.urlretrieve('https://github.com/openwrt/backports/releases/download/backports-v6.18.39/backports-6.18.39.tar.zst',archive)
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='8951c1e270d7c311432377bd50951cd1d5dee2b5fedf33d30db41aa8e428aeb0'
tree=out/'backports-6.18.39'
assert tree.resolve().parent == out.resolve()
if tree.exists(): shutil.rmtree(tree)
subprocess.run(['tar','--zstd','-xf',str(archive),'-C',str(out)],check=True)
stock=root/'work/immortalwrt/package/kernel/mac80211/patches'
vendor=root/'outputs/AX9000-v4-NSS/vendor/wifi/patches'
with (out/'patch.log').open('w') as log:
    for patches in [stock/p for p in ['build','subsys','ath','ath5k','ath9k','ath10k','ath11k','ath12k','rt2x00','mt7601u','mwl','brcm','rtl']]+[vendor/p for p in ['subsys','ath11k']]:
        for patch in sorted(patches.glob('*.patch')):
            log.write(str(patch)+'\n');log.flush()
            result=subprocess.run(['patch','-p1','--batch','--forward','--fuzz=0','-i',str(patch)],cwd=tree,stdout=log,stderr=subprocess.STDOUT)
            if result.returncode:
                print('FAILED',patch,flush=True);raise SystemExit(1)
print('All stock and NSS WiFi patches applied without fuzz',flush=True)
