# 验收范围与实际状态

## 已完成的离线检查

成功产物检查了官方 stock profile、metadata、兼容标识、FIT 内核、SquashFS、镜像大小及参考分区容量余量。板级数据以最终镜像中的 QCN9074 `board-2.bin` 核对，不从通用 staging 目录推断。

v4 完整共存版另检查：

- 原有 Nikki/Mihomo、SmartDNS、Argon、OpenSSH 以及新增五类插件均在最终 manifest 中。
- Xray、Mihomo、SmartDNS、WireGuard、AirConnect、UU 的 ARM64 ELF 文件存在。
- 启动脚本语法通过；PassWall 和 Nikki 启动逻辑调用 ECM start，未插入 ECM stop/unload 守卫。
- ECM/NSS 配置、模块、固件和规则变化清理逻辑存在；版本字符串为 `25.12.2`。
- 本机文件与远端 Release 的大小/可用 SHA256 摘要核对。

这些检查说明文件被打包及逻辑存在，不代表插件已在设备上正确运行。

## 2026-10-22 实机检查摘要

设备报告 Xiaomi AX9000 stock、ImmortalWrt 25.12.2、Linux 6.12.103。Nikki 运行时：

| 检查 | 结果 |
|---|---|
| Nikki | running |
| ECM、qca_nss_drv、qca_nss_dp | 已加载 |
| ECM acceleration engine | nss |
| IPv4/IPv6 front-end stop | 0 |
| firewall4 软件/硬件 flowtable | 均为 0 |
| ath11k nss_offload / frame_mode | 1 / 2 |
| 约 5 MB LAN 下载期间 Nikki 计数 | 持续增加 |
| 同期 ECM IPv4/IPv6 加速连接数 | 均为 0 |
| 同期 NSS IPv4 hash_hits | 未增长 |

**结论：服务共存成功，但本次流量未观察到 NSS 加速生效。** 历史 NSS 累计流量不能证明代理开启后的当前连接已加速。

本次下载没有独立确认它匹配的是 DIRECT 还是 PROXY 规则，也没有预先独立确认代理出口，因此不能用它证明代理绕过、无泄漏或所有 DIRECT 流量不能加速。原始本机网络报告不公开上传，仅发布上述不含地址/账号的摘要。

## 下一步实机验收

1. 单独启用 Nikki 或 PassWall，配置一个明确的 DIRECT 测试域名和一个明确的 PROXY 测试域名。
2. 事先独立确认两者应出现的出口 IP，不能拿本次首次查询结果反过来当作预期值。
3. 在路由器后的 LAN 电脑运行对应 Release 的 `test_coexist.py`，完整共存版使用 `--service nikki` 或 `--service passwall`。
4. 下载负载期间比较 ECM/NSS 计数，进一步结合逐连接证据；全局计数增长本身不能归属某一连接。
5. 分别验证 UDP、IPv6、DNS、节点失效、规则切换旧连接及重启后行为。现有脚本的有限 TCP IPv4 通过不能替代这些项目。

代理协议的解密、加密和用户态处理由 CPU 执行，不能宣称代理数据全程由 NSS 处理。UPnP、WireGuard、AirConnect、UU 的设备运行与性能同样没有完成全面验收。

## 不上传的内容

个人配置备份、订阅、节点认证信息、WireGuard/SSH 私钥、个人 ART/calibration 数据、原始运行流量明细。U-Boot/MIBIB 参考只保留摘要与解析结果，不作为刷写产物发布。

## v3 原始校验文件的大小写

v3 原始 ZIP 同时含 `SHA256SUMS` 与 `sha256sums`，Windows 文件系统不能将两者可靠区分。原始 ZIP 保持不变；Release 将其中小写文件另存为 `run8-upstream-image-checksums.txt`。原始大写校验表中的小写条目应对 ZIP 内原文件核对，其余原始文件哈希未变。
