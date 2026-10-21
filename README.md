# AX9000 本地精简插件版

基于已成功编译的 AX9000 v4 stock/NSS 版本，ImmortalWrt 25.12.2。
保留官方 xiaomi_ax9000-stock target、NSS 12.5 和 ath11k NSS 补丁、QCN9074 BDF。
不修改 MTD 分区、U-Boot 环境或校准数据。

附加应用仅选 PassWall（Xray）、UPnP、WireGuard、AirConnect、UU。
必要的 LuCI、防火墙、DNS、SSH 和依赖库保留。使用默认 Bootstrap 主题。
Nikki、SmartDNS、Argon 不安装。AirConnect 1.12.4 使用官方静态 aarch64
发行文件；UU 14.10.6 使用网易官方 aarch64 文件和 ttc0419/uuplugin init 脚本。
两者是预编译组件封装，不声称 UU 为开源源码编译。
插件来源和二进制 SHA256 见 local-packages.lock.json。

PassWall、UPnP、AirConnect 和 UU 默认禁用，配置后手动启用。
WireGuard 需创建接口及密钥。无订阅、账号、私钥或个人备份。
PassWall 启动前停止 ECM，配置 enabled=1 时 ECM 不启动。
停止 PassWall 后应将 enabled 设为 0，再重启 qca-nss-ecm 恢复普通 NAT 加速。
此保守策略避免对未验证的代理/ECM 共存作出承诺。
NSS/无线/UU/代理性能需要上机验收，编译检查不能替代。

在 Linux 本地运行 build-local.sh。构建输出验收通过后才自动上传 Release。
此分支无 GitHub Actions 工作流；不使用云编译。
构建目录应有 60 GiB 以上可用空间，主机须保持开机联网。
