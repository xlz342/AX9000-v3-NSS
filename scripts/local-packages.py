#!/usr/bin/env python3
import sys, subprocess, shutil, hashlib, json, tarfile, zipfile
from pathlib import Path
import urllib.request

tree=Path(sys.argv[1]); project=Path(__file__).resolve().parents[1]
custom=tree/'package/custom'; custom.mkdir(exist_ok=True)
locks={}

def clone(url, commit, name):
    dest=project/'local-vendor'/name
    if not dest.exists():
        subprocess.run(['git','clone','--depth','1',url,str(dest)],check=True)
    subprocess.run(['git','-C',str(dest),'fetch','--depth','1','origin',commit],check=True)
    subprocess.run(['git','-C',str(dest),'checkout','--detach',commit],check=True)
    locks[name+'_source_commit']=commit
    return dest

def recipe(name,version,deps,files):
    dest=custom/name; (dest/'files').mkdir(parents=True,exist_ok=True)
    for source,target in files:
        shutil.copyfile(source,dest/'files'/target)
    text=f"""include $(TOPDIR)/rules.mk
PKG_NAME:={name}
PKG_VERSION:={version}
PKG_RELEASE:=1
PKG_LICENSE:={"Proprietary" if name == "uuplugin" else "MIT"}
include $(INCLUDE_DIR)/package.mk
define Package/{name}
  SECTION:=net
  CATEGORY:=Network
  TITLE:={name}
  DEPENDS:=@aarch64 {deps}
endef
define Build/Compile
endef
define Package/{name}/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/etc
"""
    for source,target in files:
        folder='etc/init.d' if target.endswith('.init') else ('etc' if target.endswith('.conf') else 'usr/bin')
        out=name if target.endswith('.init') else target
        text+=f'\t$(INSTALL_BIN) ./files/{target} $(1)/{folder}/{out}\n'
        locks[target]=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    text+=f'endef\n$(eval $(call BuildPackage,{name}))\n'
    (dest/'Makefile').write_text(text)

uu=clone('https://github.com/ttc0419/uuplugin.git','d7e58b7cad087df4c524a9327f4eb3663fb8da59','uuplugin')
cache=project/'local-vendor/uu-aarch64'; cache.mkdir(exist_ok=True)
archive=cache/'uu.tar.gz'
if not archive.exists():
    url=urllib.request.urlopen(urllib.request.Request('https://router.uu.163.com/api/plugin?type=openwrt-aarch64',headers={'Accept':'text/plain'}),timeout=60).read().decode().split(',')[0].replace('http://','https://',1)
    urllib.request.urlretrieve(url,archive)
locks['uu_archive']=hashlib.sha256(archive.read_bytes()).hexdigest()
with tarfile.open(archive) as t:
    for name in ['uuplugin','uu.conf','xtables-nft-multi']:
        member=next(m for m in t.getmembers() if Path(m.name).name==name and m.isfile())
        (cache/name).write_bytes(t.extractfile(member).read())
recipe('uuplugin','14.10.6','+kmod-tun +iptables-nft',[(cache/n,n) for n in ['uuplugin','uu.conf','xtables-nft-multi']]+[(uu/'files/uuplugin.init','uuplugin.init')])

air=clone('https://github.com/philippe44/AirConnect.git','613c6b31c88a6b7cd5b2417828e9461353d3eadf','airconnect')
with zipfile.ZipFile(air/'AirConnect-1.12.4.zip') as z:
    for name in ['aircast','airupnp']:
        (air/(name+'.bin')).write_bytes(z.read(name+'-linux-aarch64-static'))
init=air/'airconnect.init';init.write_text('#!/bin/sh /etc/rc.common\nSTART=99\nUSE_PROCD=1\nstart_service() {\n for name in aircast airupnp; do\n procd_open_instance "$name"\n procd_set_param command /usr/bin/$name -Z\n procd_set_param respawn\n procd_close_instance\n done\n}\n')
recipe('airconnect','1.12.4','',[(air/(n+'.bin'),n) for n in ['aircast','airupnp']]+[(init,'airconnect.init')])
# Coexist edition: no ECM stop/unload hooks in PassWall.
p=tree/'feeds/luci/applications/luci-app-passwall/root/etc/init.d/passwall'
s=p.read_text();assert s.count('\t$APP_FILE start')==2
s=s.replace('\t$APP_FILE start','\t/etc/init.d/qca-nss-ecm start\n\t$APP_FILE start')
p.write_text(s)
p=tree/'feeds/luci/applications/luci-app-passwall/root/usr/share/passwall/nftables.sh'
s=p.read_text()
for anchor in ['\nstart() {', '\nstop() {']:
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'\n\t/usr/sbin/ax9000-ecm-flush')
for anchor in ['\n\tgen_include\n}', '\n\tflush_include\n}']:
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor[:-2]+'\n\t/usr/sbin/ax9000-ecm-flush\n}')
anchor='\n\t${__nft}\n\n\treturn 0'
assert s.count(anchor)==1
s=s.replace(anchor,'\n\t${__nft}\n\t/usr/sbin/ax9000-ecm-flush\n\n\treturn 0')
p.write_text(s)
(project/'local-packages.lock.json').write_text(json.dumps(locks,indent=2)+'\n')
