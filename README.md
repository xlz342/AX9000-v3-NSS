# AX9000-v4-NSS-11 full base + extras (20261022)

保留 run 11 全部基础配置：Nikki/Mihomo、SmartDNS、Argon、OpenSSH、
NSS 12.5 和 ath11k NSS WiFi。添加 PassWall/Xray、UPnP、WireGuard、
AirConnect 1.12.4、UU 14.10.6。版本为 25.12.2，日期只在固件名。
使用本地缓存源码编译，不触发 Actions。官方 stock target/分区不改。

PassWall 或 Nikki 启动均启动 ECM，不停止或卸载 NSS/ECM。
规则变化时清理 ECM 旧连接。不代表代理加密、解密进入 NSS。
请选用一种透明代理；两种代理同时接管流量的互相干扰未经验证。
新增服务默认禁用，须配置并启用。WireGuard 需配置接口及密钥。
离线镜像检查确认包、ARM64 二进制、启动脚本和共存挂钩已安装；
运行状态、无线性能和代理出口只能上机确认，不能据此声称全部硬件加速。

tests/test_coexist.py 从 LAN 电脑运行，--service passwall 或 --service nikki。
还需 --router root@192.168.1.1 --proxy-url URL --expected-proxy-ip IP
--direct-url URL --expected-direct-ip IP，两 URL 域名不同且分别强制代理和直连，
预期出口需独立确认。依赖 Python3、curl、SSH 密钥登录。
可加 --direct-download-url URL --seconds 30 收集流量统计。
脚本不改配置、不读取密钥。退出码 0 仅代表有限 TCP IPv4 检查通过；
UDP/IPv6/DNS/故障回退均未测试，统计增长不能证明某连接的硬件归属。
