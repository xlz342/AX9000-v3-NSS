# 版本来源与本地构建

## 源码位置

`main` 的构建源码仍是 v3 基线；首页承担各版本索引，不将各版差异混入同一配置。下载某版固件时应同时记录 Release、构建配置及来源锁文件。

原始构建提交：

| 构建 | 提交 |
|---|---|
| v3 成功构建 8 | `e029280bd2932ac50622aeab1f0b840206c34265` |
| v4 成功构建 11 | `1b04f21cca0599f031e235cbc262a33b82626a1e` |
| 本地精简保守版 | `fcd0eab1e55282d0c4106a62287e0e5999183458` |
| 本地精简共存版 | `0096d24139880839314fd4ea5bcd48157b926454` |
| v4 完整共存版 | `76ba6af053e325818e8daea25fc42aa4891c391b` |

后续归档维护提交不会改变已发布固件。`source-archive-index.json` 记录本次整理后的分支提交。

完整 v4 关键来源：

| 来源 | 固定提交 |
|---|---|
| ImmortalWrt | `4fc16f2985a358bd43bb522e43f05395fcbd6ed5` |
| NSS packages | `0d970dbf0185e3f53709bd803e8a466598023c57` |
| NSS donor | `d6848fa2ea00193b5b7d3973e3990da7f608027c` |
| ath11k NSS donor | `92a2d104145c8d265851c4b388a41bd8e9c21cd9` |
| Nikki | `7b203f6c4c5e94c6c0026acb301090aa1d310e7f` |
| Argon | `23c3e525578374d6b20f5e7b93d27874cd01a252` |
| Argon config | `3e099a37c3f71d0de677f1b6b0f4bffd57d91dac` |

版本差异和官方 feed 提交应以对应 Release 的锁文件和 `feeds.buildinfo` 为准。

## 附加插件

PassWall、UPnP、WireGuard 来自固定发行版 feeds。PassWall 选用 Xray，必要依赖随之安装。

AirConnect 1.12.4 使用上游静态 aarch64 发行文件；UU 14.10.6 使用网易官方预编译 aarch64 文件，启动脚本来自 [ttc0419/uuplugin](https://github.com/ttc0419/uuplugin)。**两者是预编译组件封装，不是从源码编译出 UU 二进制**。具体二进制哈希见 `local-packages.lock.json`。

UU 官方下载 API 是动态入口，未来可能返回不同版本。重新获取时必须核对已有锁文件中的二进制哈希，不能仅凭文件名声称位级复现。本次归档不上传路由器个人备份、代理订阅、WireGuard 私钥、SSH 私钥或账号数据。

## 本地构建步骤

以完整共存版为例，在 Linux/WSL 的 Linux 文件系统中构建，避免直接在 `/mnt/c` 上执行大量编译 I/O。

```sh
git clone --branch v4-full-coexist-20261022 https://github.com/xlz342/AX9000-v3-NSS.git source
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export GOPROXY=https://goproxy.cn
bash source/scripts/setup.sh "$PWD/build"
cd build
make download -j8 V=s
make -j4 V=s
python3 ../source/scripts/validate-image.py "$PWD" "$PWD/../artifacts"
python3 ../source/scripts/check-plugins.py "$PWD" "$PWD/../artifacts"
```

依赖 Ubuntu 构建工具、Git、Python3/PyYAML、curl、rsync 等；硬盘应为完整工具链、Go、内核和镜像留出数十 GiB 空间。并行数按内存调整。

`build-local.sh` 是本次工作机的自动化脚本，包含固定目录、日期、GitHub 仓库和发布步骤；其他机器不要不加修改直接运行。上述步骤仅构建和验收，不自动发布。

Go 下载采用国内 `goproxy.cn`，保留模块校验。不能关闭校验来绕过依赖下载问题。Linux `PATH` 不混入含空格和括号的 Windows 路径，避免 Go 配方命令解析出错。

## 源码字节校验

各版本 `vendor/*/manifest.json` 固定 NSS 和无线补丁的 SHA256。归档分支通过 `.gitattributes` 对 `vendor/**` 和 `inputs/**` 禁止文本换行转换，使 Windows/Linux 检出后保持原始字节。

源码分支中的构建测试应与该分支匹配。`docs/maintenance` 中的脚本保留为历史排查材料，可能引用当时的目录，不能替代当前正式验收脚本。
