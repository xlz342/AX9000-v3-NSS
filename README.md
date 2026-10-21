# AX9000 PassWall + ECM/NSS coexist experimental

第二版，保留 stock 分区、NSS/无线补丁、相同的五类插件。
PassWall 启动时启动 ECM，不停用、不卸载 ECM/NSS。
PassWall nftables 规则开始/结束调整时请求清理 ECM 旧加速连接。
保留 firewall4；关闭软件/硬件 flowtable，避免与 ECM 重复处理。
不承诺“代理全部硬件加速”：代理协议的解密和加密属于 CPU 工作，
符合条件的直连/转发连接才可能被 NSS 接管。规则切换、UDP、IPv6、
DNS、连接复用和代理故障回退行为必须实机验收。
无实机验证，不能声称没有绕过代理或性能达标。

配置代理后，从经 AX9000 上网的 LAN 客户端运行 tests/test_coexist.py。
需要 Python 3、OpenSSH 客户端、curl，及已经建立的路由器 SSH 密钥登录。
不要在路由器自身运行此 LAN 路径测试。两个 IP 查询 URL 必须在 PassWall
中分别强制 PROXY 和 DIRECT；提前独立确认各自预期出口 IP，不能将本次
脚本首次查询结果反过来当成期望值。域名不可重合。
示例（替换所有尖括号值）：

python tests/test_coexist.py --router root@192.168.1.1 --proxy-url <代理IP查询URL> --expected-proxy-ip <已知代理出口IP> --direct-url <直连IP查询URL> --expected-direct-ip <已知WAN出口IP>

可加 --direct-download-url <强制直连的大文件URL> --seconds 30，观察
负载前后的 ECM/NSS 统计变化。下载会占用带宽。
脚本不写路由配置、不切换服务、不读取代理订阅或 WireGuard 密钥。
结果保存在本地 JSON，不随固件上传；IP 测试端点会看到请求出口地址。
测试重复验证 TCP IPv4 出口，收集模块、参数、ECM/NSS 统计和 nft 计数。
全局计数增长无法证明指定连接已被加速，因此硬件流量归属始终标记
INCONCLUSIVE；UDP/IPv6/DNS 泄漏、节点失效、切换旧连接均标记 NOT_TESTED。
退出码：0=本次有限的功能检查通过；1=失败；2=证据不足或运行出错。
退出码 0 也不代表全部硬件加速或完整的无泄漏验收。
