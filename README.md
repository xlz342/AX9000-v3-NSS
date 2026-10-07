# AX9000-v4-NSS-WiFi-Nikki-experimental

基于已构建成功、用户已验证有线 NSS 的 v3 提交 `e029280bd2932ac50622aeab1f0b840206c34265`。这是 **experimental build**；编译检查不能代替 AX9000 实机启动、Apple 认证、代理出口与吞吐验收。

仅用于现有 **Xiaomi AX9000 stock 分区**设备：ImmortalWrt 25.12.2、Linux 6.12.103、qualcommax/ipq807x、`xiaomi_ax9000-stock`。不刷写 bootloader/MIBIB，不更改 ART、caldata、MTD、U-Boot 环境。没有包含 uboot.bin、mibib.bin 或用户配置备份。

## 从 v3 保留的内容

`vendor/nss/` 的所有文件及哈希原样沿用，包括 NSS DTS 增量、0600–0607 的适用内核补丁、0981 skb recycler 及 v3 的三处重基修复。NSS packages 固定 `0d970dbf0185e3f53709bd803e8a466598023c57`（检查时也是 NSS-12.5-K6.x 分支 HEAD），NSS 核心 donor 固定 `d6848fa2ea00193b5b7d3973e3990da7f608027c`。NSS firmware 保持 **NSS.FW.12.5-210-HK.R**，保留 drv/dp/ECM、bridge/VLAN/PPPoE/crypto、IPv4/IPv6 加速。

保留官方 stock DTS、image recipe、sysupgrade 和 calibration hotplug；`prepare.py` 与最终验证器检查受保护源文件 SHA256。不通过改 metadata 冒充其他分区设备：官方兼容标识实际为 **`xiaomi,ax9000-stock`**，不是非 stock 的 `xiaomi,ax9000`。切勿强制忽略 LuCI 的兼容性检查。

Argon/Argon config、Nikki/LuCI Nikki、SmartDNS/LuCI SmartDNS、OpenSSH server/keygen 沿用。默认 LAN 不改，国家码和发射功率不改。OpenSSH 已支持 ed25519，无须替换为不固定版本。保持 v3 的 Dropbear 22 端口服务；如需使用 OpenSSH 服务，先安装公钥并配置独立测试端口，确认能登录后再停用 Dropbear、启用 sshd，避免把自己锁在设备外。

## Wi-Fi NSS 来源与适配

Wi-Fi donor：[qosmio/openwrt-ipq main-nss](https://github.com/qosmio/openwrt-ipq/tree/92a2d104145c8d265851c4b388a41bd8e9c21cd9)，固定提交 `92a2d104145c8d265851c4b388a41bd8e9c21cd9`。导入其 `patches/nss/subsys` 与 `patches/nss/ath11k`；没有导入无关 ath10k NSS 或替换整个无线目录。

该 donor 基于 backports 6.18.26，本项目保留 ImmortalWrt 的 **backports 6.18.39**。3 个补丁已针对新代码重基：RX histogram 保留新版有效 peer ID=0 处理；bitmap TX cleanup 保留 tx_status=NULL；BSS transition 的 peer 查找/monitor status 改为新版上下文。完整原厂补丁后再应用 NSS 补丁，本地 `patch --fuzz=0` 全部通过。详细记录见 `vendor/wifi/PROVENANCE.md`。保留官方 qcom-qmi-helpers 打包方式，开启 ath11k NSS、1GB profile 和 NSS WiFi/ext-vdev 接口；不启用要求 NSS 11.4 的 NSS mesh。

`generic-ax9000.tar.gz` 已解包审核：只有 `lib/firmware/ath11k/QCN9074/hw1.0/board-2.bin`，并非 C 源码补丁。沿用 v3 的精确文件导入到 ipq-wifi/src，然后校验 package prepare 与最终 squashfs 中的字节。因此它与 ath11k NSS 源码补丁分别合并，不覆盖 DTS、ART 或校准读取路径。

实验默认 `ath11k nss_offload=1 frame_mode=2`。提供 1GB Wi-Fi pbuf 配置，只调整 NSS 无线 buffer，不改变 v3 CPU governor/时钟/RPS。带补丁驱动同时支持普通路径。

## Apple 认证与无线回退

检查时 [上游 Apple EAPOL/authorization 问题 #95](https://github.com/qosmio/openwrt-ipq/issues/95) 仍开放，没有可确认修复并已验证 AX9000 的结论。donor 的 peer/BSS transition 修复已包含，但不宣称解决该问题。

保持有线 LAN 管理连接。若 iPhone/Mac 无法完成认证，在 SSH 执行：

```sh
ax9000-wifi-nss off
reboot
```

这会持久化 `nss_offload=0 frame_mode=1`，仅关闭 Wi-Fi NSS；NSS 核心和有线 ECM 仍保留。重新实验：

```sh
ax9000-wifi-nss on
reboot
ax9000-wifi-nss status
```

脚本不热卸载无线驱动，`status` 区分下次启动配置与当前参数。`/etc/modules.d/ath11k` 被加入 sysupgrade 保留列表。模块参数存在仅证明编译支持，不证明无线数据包已进入 NSS。

## Nikki 与 ECM 共存

删除 v3 对 Nikki enabled/mihomo 的 ECM 启动阻拦，也删除 Nikki 启动前的 ECM stop。ECM 开机服务直接读取 `ecm.global.acceleration_engine=nss` 并传给 modprobe，不依赖旧 `/etc/modules.conf`。v4 每次启动在 network/firewall 前保持 flow_offloading=0、flow_offloading_hw=0、packet_steering=0，因此恢复私人网络备份后仍可保持这些要求。

`scripts/feed-fixes.py` 针对固定 Nikki 提交的真实函数修改：

- `service_started()`：先成功安装 policy routing，生成临时 nft 文件并通过 `nft -c`，成功执行 nft transaction 后调用 `ax9000-ecm-flush`。
- `cleanup()`：删除 Nikki nft/policy routing、完成清理后 flush；覆盖 stop、restart、reload。配置/订阅切换通过正常 Nikki reload/start 路径生效，单纯下载未启用的订阅不改变活动规则。
- `firewall_include.sh`：firewall4 重建 TUN accept 规则后 flush；在 service_started 内调用时延后至完整安装之后。ECM 自身 fw4 include 也 flush。
- helper 仅在 debugfs `defunct_all` 可写时写入 1，从不 rmmod ECM。不修改 Nikki 的 bypass、TCP redirect、TUN mark、table 或 DNS hijack 策略。

DIRECT/bypass 返回 Linux forwarding 后由 ECM 加速；PROXY TCP 经 redirect、PROXY UDP 经 mark/TUN。此版本遵循用户实测的简单共存方案，**不能仅凭两组 counter 同时增长判定没有泄漏**。切换规则后会清理加速记录，但不销毁全部 conntrack；已经建立的 NAT/代理会话可能仍保留旧决定。验收应同时覆盖新建连接和已有长连接，必要时重新建立测试会话。Nikki 重启期间的上游服务规则空窗与 fail-open 行为没有被本项目改造成 fail-closed。

SmartDNS 保持原有软件与用户配置；本项目不强制启用 Nikki IPv4/IPv6 DNS hijack。恢复后确认 SmartDNS 监听6053、dnsmasq上游127.0.0.1#6053、Nikki两种DNS hijack关闭。不会上传或内嵌用户订阅。

## 云编译与输出

在分支 `v4-nss-wifi-nikki` 运行 `.github/workflows/build.yml`（push 自动触发，也支持 Actions 的 Run workflow）。全部源码版本见 `sources.lock.json`；原厂 release feeds 的 commit pins 保持。kernel/mac80211 prepare 任何 patch reject 都失败；没有通过忽略失败跳过 ath11k。

Actions 输出：

- `AX9000-v4-NSS-WiFi-Nikki-experimental-<run_number>`：仅通过验证的 stock sysupgrade、原生 factory.ubi、manifest、metadata、容量报告和 SHA256SUMS。
- `AX9000-v4-diagnostics-<run_number>`：最终 `.config`（保存为config）、config.seed、feeds revisions、完整日志、kernel/wifi patch application日志。

必需文件：`immortalwrt-25.12.2-qualcommax-ipq807x-xiaomi_ax9000-stock-squashfs-sysupgrade.bin`。最终 squashfs 检查 NSS 两个 core firmware、drv/dp/ecm/bridge/VLAN/PPPoE/crypto 模块、ath11k ELF 的 nss_offload/frame_mode modinfo、模块默认参数、ECM启动链接、诊断脚本与QCN9074 BDF。若 `ath11k.ko` 没有 nss_offload，禁止发布固件 artifact。

## 刷机与恢复

先保留成功 v3 的 sysupgrade 和私人备份，在有线连接下操作。核对下载 SHA256SUMS，LuCI选择 **stock squashfs-sysupgrade.bin**；建议全新配置启动后先做 NSS/无线检查，再从本地恢复 restore-ready 备份。不要把备份放入项目目录、GitHub、Actions artifact 或 Release。备份中缺省的 ECM/NSS/模块文件由本固件提供。

U-Boot 接受 sysupgrade tar 还是 factory UBI 取决于当前 bootloader 的刷机页面；本项目不能仅凭二进制参考证明它接受任意格式。使用已验证的 stock 刷机流程，不改环境变量，不擦写 MIBIB/ART。如果 v4 无法稳定工作，通过已验证的 LuCI/U-Boot恢复流程刷回 v3 stock sysupgrade；无线认证故障优先使用上述 off+reboot，无须重刷。

## 实机验收

运行 `/root/ax9000-v4-check.sh`，保存空闲和测试后的两份输出。脚本只读，筛选诊断字段，不输出 PPPoE/WiFi密码、API secret、订阅或节点凭据。

1. 冷启动：NSS FW12.5、core0/core1正常；ecm自动加载；所有必需模块存在；两个ath11k参数存在。
2. DIRECT有线/无线分别测试：ECM IPv4/IPv6 accelerated_count非零，NSS create_requests/hash_hits/packet counters增长。没有流量时计数为0并不单独证明故障。
3. 无线：2.4GHz、各5GHz/QCN9074、80/160MHz，Apple WPA认证、DHCP、断线重连、睡眠唤醒、漫游和持续传输；有问题先off+reboot，再对照v3。
4. 开启Nikki：ecm仍加载；对**已配置必须代理**的域名分别发起新TCP与UDP流量；检查TCP redirect与UDP TUN计数，同时确认外部网站报告的实际出口为代理节点。IPv4和IPv6分开验证，防止IPv6直连绕过。
5. 在持续DIRECT与PROXY长连接时测试Nikki stop/start/restart/reload、订阅/配置切换、firewall reload；观察规则安装和清理顺序、旧连接与新连接的出口，重复统计检查。仅Nikki控制面内更换节点而未重载nft并不触发系统规则安装。
6. 若确认某类代理连接绕过，记录协议、mark、conntrack与出口证据，再按连接添加选择性排除；不要恢复“全局关闭ECM”。

近千兆 NAT、160MHz 无线吞吐和代理性能均为实测目标，不是构建保证。Wi-Fi NSS、ECM共存和Apple兼容仍为实验功能。
