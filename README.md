# Xiaomi AX9000 ImmortalWrt NSS 固件归档

本仓库汇总 AX9000 项目的成功构建、各版源码、编译记录和验收结果。设备为 **Xiaomi AX9000 stock 布局**，系统基线为 **ImmortalWrt 25.12.2 / Linux 6.12.103**。

> 当前结论：固件编译与离线镜像检查已通过；Nikki 与 ECM/NSS 已在实机同时运行，但最近一次下载测试中 ECM 加速连接为 0、NSS 命中数未增长。因此，**尚未验证代理开启后的 NSS 流量加速成功，更不代表代理加解密全部硬件加速**。

## 版本与下载

所有版本的相同文件名都必须结合所在 Release 区分；不要混用校验文件或配置。

| 版本 | 软件与差异 | 固件下载 | 源码分支 |
|---|---|---|---|
| v3 / 成功构建 8 | NSS 有线基础版本；原始构建归档 | [v3-NSS-8](https://github.com/xlz342/AX9000-v3-NSS/releases/tag/AX9000-v3-NSS-8) | [archive-v3-nss-8](https://github.com/xlz342/AX9000-v3-NSS/tree/archive-v3-nss-8) |
| v4 / 成功构建 11 | NSS + ath11k NSS，无线补丁；Nikki、SmartDNS、Argon、OpenSSH | [AX9000-v4-NSS-11](https://github.com/xlz342/AX9000-v3-NSS/releases/tag/AX9000-v4-NSS-11) | [archive-v4-nss-11](https://github.com/xlz342/AX9000-v3-NSS/tree/archive-v4-nss-11) |
| 本地精简保守版 | PassWall/Xray、UPnP、WireGuard、AirConnect、UU；PassWall 启动前停用 ECM | [保守版 20261022](https://github.com/xlz342/AX9000-v3-NSS/releases/tag/AX9000-local-PassWall-20261022) | [local-passwall-20261022](https://github.com/xlz342/AX9000-v3-NSS/tree/local-passwall-20261022) |
| 本地精简共存版 | 同上五类插件；PassWall 不停用 ECM/NSS | [精简共存版 20261022](https://github.com/xlz342/AX9000-v3-NSS/releases/tag/AX9000-local-PassWall-ECM-coexist-20261022) | [local-passwall-ecm-coexist-20261022](https://github.com/xlz342/AX9000-v3-NSS/tree/local-passwall-ecm-coexist-20261022) |
| v4 完整基础共存版 | 保留构建 11 全部软件，再加入上述五类插件；PassWall 或 Nikki 启动时启动 ECM | [完整共存版 20261022](https://github.com/xlz342/AX9000-v3-NSS/releases/tag/AX9000-v4-full-coexist-20261022) | [v4-full-coexist-20261022](https://github.com/xlz342/AX9000-v3-NSS/tree/v4-full-coexist-20261022) |

完整共存版系统版本为 `25.12.2`，日期只加在固件文件名中。版本仍为预发布；表格不构成实机性能认证。

## 文件说明

- `*-squashfs-sysupgrade.bin`：stock 固件升级镜像。
- `*-squashfs-factory.ubi`：target 原生生成的 factory 镜像。实际 U-Boot 接受何种格式仍需匹配其实现。
- `SHA256SUMS`：该 Release 原始固件及报告的校验清单。后续追加的构建日志 ZIP 不在原始清单内，其信息见归档索引。
- `*.manifest`、`config.buildinfo`、`config.seed`、`sources.lock.json`：包列表、配置与来源锁定记录，依各版实际产物提供。
- `validation.json`：离线镜像验收；完整共存版另有 `plugin-validation.json`。
- `test_coexist.py`、`COEXIST-TEST-README.md`：LAN 客户端测试及使用说明，依共存版提供。
- `*-build-records.zip`：本地构建日志，已处理本机路径、私网地址和特定 URL 参数；日志保留失败重试历史。

## 设备与边界

- target/subtarget/profile：`qualcommax/ipq807x/xiaomi_ax9000-stock`。
- metadata 兼容标识：`xiaomi,ax9000-stock`；不能替换成普通布局的 `xiaomi,ax9000`。
- 不改变 MTD/MIBIB 布局、U-Boot 环境或 ART/calibration 数据；保留官方 stock DTS 与升级逻辑。
- 不修改无线国家码或功率限制。NSS/无线补丁仍需要实机兼容性及性能验证。
- 原始 `uboot.bin`、`mibib.bin` 只作为本地参考，仓库保留摘要及解析结果，不将其作为刷机内容发布。

## 共存的实际含义

共存版保留 ECM/NSS 运行，代理规则变化时清理旧加速连接。关闭 firewall4 的 flowtable 加速，避免与 ECM 重复处理；**firewall4/nftables 保留工作**。

代理的解密、加密和用户态转发仍由 CPU 执行。模块已加载、历史计数较大，都不能证明当前被测连接经过 NSS。PassWall 与 Nikki 应选择一种透明代理接管流量，不能将两者同时启用等同于更多加速。

## 详细资料

- [版本、来源与重现构建](docs/BUILD-AND-SOURCES.md)
- [构建历史与失败原因](docs/BUILD-HISTORY.md)
- [离线与实机检查结论](docs/VALIDATION.md)
- [机器可读 Release 索引](docs/releases.json)
- [源码分支归档提交](docs/source-archive-index.json)
- [早期 v3 原始说明](docs/history/v3-original-README.md)

本次整理不触发 GitHub Actions。`main` 保留早期 v3 构建源码与工作流供追溯，**默认分支根目录源码不是最新完整共存版**；请使用表格中的对应分支。归档和本地版本分支不包含云工作流。
