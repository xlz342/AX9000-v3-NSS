# AX9000-v3 NSS Edition

用于 Xiaomi AX9000 **stock 分区布局**的 ImmortalWrt 25.12.2 GitHub Actions 云编译项目。
当前为实验性集成项目，尚未完成全量固件编译和 AX9000 实机验收，不能标注为已验证可刷固件。

## 使用

1. 在 GitHub 建立一个空仓库，例如 `AX9000-v3-NSS`。
2. 将本目录内容上传到仓库根目录，必须包含隐藏的 `.github` 目录。
   不要把整个 `AX9000-v3-NSS` 文件夹作为额外一层目录上传。
3. 打开 Actions → AX9000-v3 NSS Edition (experimental) → Run workflow。
4. 只有配置、编译、metadata、包清单、板级数据和容量检查都通过后，才上传 firmware artifact。
   失败时下载 diagnostics artifact；检查 setup、kernel-prepare、build 日志。

也可以用 Git 推送：

```sh
git init
git add .
git commit -m "Add AX9000 stock ImmortalWrt 25.12.2 NSS build"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/AX9000-v3-NSS.git
git push -u origin main
```

GitHub 官方 Ubuntu runner 使用 `-j2` 控制内存占用，超时时间为 6 小时。
Actions 使用 `make defconfig` 自动完成 Kconfig 配置；`make menuconfig` 是可选的本地交互入口。
全量构建需要数十 GB 空间；磁盘不足请使用空间更大的 Ubuntu runner。

## 版本与设备兼容

- 官方源码：`immortalwrt/immortalwrt`，标签 `v25.12.2`，提交固定在 `sources.lock.json`。
- 官方 feeds 保持发行版自带的固定提交。
- target/subtarget/profile：`qualcommax/ipq807x/xiaomi_ax9000-stock`。
- Linux：6.12.103，使用该发行版原始内核版本。
- metadata 必须包含且只包含 **`xiaomi,ax9000-stock`**。

你提供的参考固件的实际 metadata 为 `xiaomi,ax9000-stock`。
要求中的 `xiaomi,ax9000` 是另一布局的标识，因此不能把它添加到 stock 固件兼容列表。
项目不会伪造兼容标识，也不会用普通 AX9000 expand profile 替代 stock profile。

官方 stock DTS、image recipe 和 platform sysupgrade 逻辑受到 SHA-256 保护。
官方 AX9000 父 DTS 仅增加一行 NSS dtsi include，原有无线、calibration、分区内容保留。
该 include 添加 NSS 硬件节点；不会替换整个 DTS。NSS reserved-memory 变更是 RAM 描述，
不涉及 NAND/MTD 分区。stock 设备继续使用 SMEM 分区表。

项目没有刷写 MIBIB、U-Boot、U-Boot 环境、ART 或 calibration 数据的操作。
你提供的两个 bootloader 文件仅记录哈希、长度及 MIBIB 分区参考信息；不进入固件。
参考 sysupgrade 固件也不作为二进制基础重打包，不随仓库发布。
这些文件不能代替读取实际路由器的 `/proc/mtd`、`ubinfo -a` 和设备型号。

## NSS 实际集成范围

固定来源：`qosmio/nss-packages` 的 NSS-12.5-K6.x 分支提交；
内核集成从 `qosmio/openwrt-ipq` 的 25.12-nss 固定提交选择性导入。

| 组件 | 配置 |
|---|---|
| NSS firmware | IPQ807x，QSDK 12.5 |
| qca_nss_drv / qca_nss_dp | 必选；dp 保留官方 recipe |
| qca_nss_ecm | 必选，NSS frontend |
| qca_nss_clients | 上游拆分包：bridge-mgr、vlan-mgr、pppoe |
| ECM classifier | 上游 default、MARK、DSCP；不是独立包 |
| NSS crypto | qca-nss-crypto、nss-eip-firmware |
| 内核支持 | ECM/client 导出接口、DSCP 扩展、skb recycler、NSS 硬件节点 |
| shortcut-fe / fast-classifier | 不启用：所选 6.12 NSS feed 不提供已确认兼容的实现 |
| NSS CFI cryptoapi | 不启用：上游标记 `@BROKEN`，不强行绕过 |
| NSS IPsec clients | 不启用：donor 的 MTU 改动不适合直接覆盖 6.12.103 的边界检查 |
| ath11k NSS Wi-Fi offload | 未集成，保留官方 ath11k 数据通路 |

不能仅凭模块装入或速度较快认定 NSS NAT 生效。必须看到 ECM NSS frontend
的 accelerated_count 和 NSS IPv4/IPv6 统计在真实 LAN↔WAN 转发期间增长。
NSS crypto 不表示 Mihomo 的代理加密自动由 NSS 执行。

## firewall4 / nftables / Nikki

保留 firewall4 和 nftables。ECM 使用内核 netfilter/conntrack 转发路径，
不是靠增加一条 nftables 规则就能启用。

项目为 upstream ECM script include 增加 `fw4_compatible=1`，并在 firewall4
重建规则时使旧 ECM 加速连接失效；移除上游可选的 NEW 连接速率限制脚本。
这只是明确的集成修正，不能替代 firewall reload、丢包规则和代理流量的实机验证。
关闭软件 flow offload 和 nft hardware flow offload，避免与 ECM 争用连接。

Nikki 的两种 Mihomo provider 在该发行版触发递归 Kconfig 依赖；项目只安装固定版本
`mihomo-meta`，排除未使用的 alpha recipe，避免递归依赖。

默认 Nikki 未启用、SmartDNS 未接管 DNS，保留默认联网行为。
启用 Nikki 时，在启动代理前停止 ECM；ECM 卸载失败则拒绝启动代理。
Nikki 配置启用或 Mihomo 运行时，手动启动 ECM 也会被阻止。
这是保守的代理兼容策略：代理模式下不承诺普通 NAT 仍由 NSS 加速。
关闭 Nikki 并停止服务后，可手动恢复 NAT 加速：

```sh
uci set nikki.config.enabled='0'
uci commit nikki
/etc/init.d/nikki stop
/etc/init.d/qca-nss-ecm restart
```

若后续需要“代理流量走 CPU，其他流量继续 NSS”，需要针对 Nikki 的具体
REDIRECT/TPROXY/TUN 方式、fwmark 和 ECM classifier 编写并验证排除逻辑。
当前项目不会假设任意 fwmark 都能自动排除代理流量。
手动运行 Mihomo 或其他透明代理时，也应先停止 ECM；此保护只针对 Nikki 服务。

## 无线数据的真实内容

`inputs/generic-ax9000.tar.gz` 只有一个文件：
`lib/firmware/ath11k/QCN9074/hw1.0/board-2.bin`。

它是 BDF 板级数据，不是无线驱动源码 patch，也不是 ART 备份。
通过官方 `ipq-wifi-xiaomi_ax9000` overlay 安装 QCN9074 BDF，避免覆盖
IPQ8074 的原有 board data。产物检查验证实际 rootfs 中 BDF 与导入文件一致。
使用官方 `kmod-ath11k-ahb`、`kmod-ath11k-pci` 和 QCN9074 firmware；
不修改国家码、txpower、regdb、calibration 读取或默认无线配置。

80/160 MHz 是否可用取决于该射频、当前合法国家码、信道/DFS、驱动和客户端。
2.4 GHz 不支持 80/160 MHz。需要在 QCN9074 对应的 5 GHz radio 验证 80/160 MHz。
不能从一个 BDF 推导“接近官方驱动性能”或宣称已经修复内核无线驱动。

## 默认配置与 OpenSSH

LAN 保留官方默认 `192.168.1.1`；保留设置升级时沿用原有 LAN 配置。
Argon 默认主题，安装 Argon Config、Nikki LuCI、SmartDNS LuCI。
OpenSSH 使用发行版固定 packages feed 的 10.3_p1，支持 Ed25519，不另选不匹配版本。
预装 OpenSSH server/keygen，默认保留 Dropbear 的 SSH 入口，OpenSSH 禁用以免争用 22 端口。

启用 OpenSSH 时，先配置密钥并在当前 SSH 会话保留恢复入口：

```sh
mkdir -p /root/.ssh
chmod 700 /root/.ssh
# 将自己的 ssh-ed25519 公钥放入 /root/.ssh/authorized_keys，再执行：
chmod 600 /root/.ssh/authorized_keys
ssh-keygen -A
sshd -t
/etc/init.d/dropbear stop
/etc/init.d/dropbear disable
/etc/init.d/sshd enable
/etc/init.d/sshd start
```

另开客户端连接，确认 `ssh -o HostKeyAlgorithms=ssh-ed25519 root@192.168.1.1` 成功，
再关闭原会话。项目不会生成共享私钥或预置账户密码。

## 产物与刷写边界

预期 sysupgrade：
`immortalwrt-25.12.2-qualcommax-ipq807x-xiaomi_ax9000-stock-squashfs-sysupgrade.bin`。

官方 UbiFit recipe 还提供 `*-xiaomi_ax9000-stock-squashfs-factory.ubi` 时，
workflow 同时验证并上传。不会自行构造额外 factory.bin。
factory.ubi 与 sysupgrade tar 的格式不同，不能仅改扩展名互换。

CI 检查 fwtool metadata、FIT kernel、squashfs、包清单、8–128 MiB 的 sysupgrade 大小、
参考 MIBIB 的 rootfs 容量余量、受保护源码、BDF 安装及 factory UBI magic。
你提供的 MIBIB 在 128 KiB eraseblock 假设下 rootfs 为 232 MiB；
CI 预留 overlay 和 UBI 开销。实际 NAND 坏块及 UBI 余量仍应以实机为准。

已运行 ImmortalWrt stock 布局时优先走 LuCI sysupgrade；刷写前在设备执行
`sysupgrade -T /tmp/固件文件.bin`，并核对 `ubus call system board`。
不要使用 `sysupgrade -F` 绕过兼容检查。
仅根据 uboot.bin 无法确认其 Web 刷机界面接受 sysupgrade tar，
所以本项目不能承诺这两个格式都可直接通过你的 U-Boot 界面刷入。
需要先确认该 U-Boot 的实际格式支持。

## 实机验收

1. 升级前后对比 `/proc/mtd`、`ubinfo -a`；确认 stock 型号和分区一致。
2. Nikki 关闭，运行 `ax9000-nss-check`；检查 NSS firmware 无加载失败、ECM 存在、
   firewall4 check 成功。模块加载不等同于 hardware offload。
3. LAN 主机向 WAN 侧独立 iperf3 主机连续测试 60 秒，双向分别测试。
   不要用路由器自身作端点。流量期间两次读取统计，确认 accelerated_count > 0
   且 NSS 数据包/字节计数增长；停止 ECM 做对照，记录速度及 CPU 使用。
4. 在受控测试网添加拒绝规则、reload firewall4，确认已有及新连接按规则停止。
   检查 IPv4/IPv6、DHCP WAN 或实际使用的 PPPoE。存在规则绕过则停用 ECM。
5. Nikki 启用，确认 ECM 不存在，代理出口/DNS/访问控制正确；不能用吞吐替代代理验收。
6. 对所有 radio 检查 `iw phy`、`iw dev`、dmesg、calibration/firmware 报错。
   在合法信道上分别测 QCN9074 80/160 MHz；记录协商宽度、PHY rate、吞吐、距离和 CPU。
7. 验证 OpenSSH Ed25519 主机密钥及公钥认证。

接近千兆 NAT、160 MHz 无线吞吐和代理损耗都是验收目标，目前不是已测结果。

来源：[官方 profile](https://github.com/immortalwrt/immortalwrt/blob/v25.12.2/target/linux/qualcommax/image/ipq807x.mk)、
[NSS packages](https://github.com/qosmio/nss-packages/tree/0d970dbf0185e3f53709bd803e8a466598023c57)、
[NSS 内核集成](https://github.com/qosmio/openwrt-ipq/tree/d6848fa2ea00193b5b7d3973e3990da7f608027c)、
[Nikki](https://github.com/nikkinikki-org/OpenWrt-nikki)。
