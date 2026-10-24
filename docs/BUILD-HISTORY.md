# 构建历史与修复记录

本表区分编译失败、环境失败和验收脚本失败。日志中的历史错误不代表最终产物失败。

| 阶段 | 现象或原因 | 处理和结果 |
|---|---|---|
| v3 早期 | NSS recycler 的内核新选项未完整回答，非交互 syncconfig 中断 | 完整设置配置项并验证关闭 stdin 后无新提示 |
| v3 早期 | GitHub runner 可用磁盘不足 | 清理无关 SDK/缓存并检查空间 |
| v3 BDF 验收 | 在共享 staging rootfs 中检查板级数据，未考虑每设备 rootfs-overlay | 改查最终 sysupgrade 内的 SquashFS |
| v3 主机工具 | 误用 unsquashfs 名称或过早要求 fwtool 存在 | 使用构建生成的 unsquashfs4；完整构建后再检查 fwtool |
| v3 构建 8 | 配置、编译、BDF 和 metadata 验收成功 | 原始固件已补充归档到 v3-NSS-8 Release |
| v4 构建 9 | Ubuntu/Azure mirror selection 下载卡住，最终耗尽六小时 | 改用 Ubuntu 官方 HTTPS 源，并增加超时与重试限制 |
| v4 构建 10 | 编译成功；普通用户解包整个 rootfs 时无法创建设备节点 `/dev/console` | 验收只提取需要的文件，保留严格错误检查，并增加设备节点回归测试 |
| v4 构建 11 | 编译与验收成功 | 原始固件已补充归档到 AX9000-v4-NSS-11 Release |
| 20261022 本地精简版 | Go 配方被 Windows PATH 中的空格和括号破坏 | 将构建 PATH 限定为 Linux 路径 |
| 20261022 本地精简版 | 删除 CPU 调频插件后，语言包仍被选中，根文件系统安装失败 | 同时取消插件和对应语言包，重新 defconfig |
| 20261022 完整共存版 | yq/Mihomo 的 Go 依赖下载超时 | 切换国内 goproxy.cn，保留校验并复用缓存后成功编译 |
| 20261022 完整共存版 | 编译完成后的日志管道未正常收尾 | 从最终镜像验收与上传阶段恢复，未伪造构建成功或重新刷机 |
| 20261025 归档 | Git 换行转换改变一份无线补丁字节 | 保护 vendor/input 原始字节，并核对 Git 暂存内容与全部 manifest 哈希 |

原始云构建：

- [v3 成功构建 8](https://github.com/xlz342/AX9000-v3-NSS/actions/runs/37119689224)
- [v4 构建 9](https://github.com/xlz342/AX9000-v3-NSS/actions/runs/37677182216)
- [v4 构建 10](https://github.com/xlz342/AX9000-v3-NSS/actions/runs/37717511292)
- [v4 成功构建 11](https://github.com/xlz342/AX9000-v3-NSS/actions/runs/37731668760)

三个本地版本的 Release 中已追加处理过本机路径及部分敏感参数的 `*-build-records.zip`。不上传原始代理配置或实机流量明细。
