#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TREE=${1:?usage: setup.sh absolute-build-directory}
mkdir -p "$TREE"
read_lock() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$ROOT/sources.lock.json" "$1"; }
git -C "$TREE" init
git -C "$TREE" remote add origin https://github.com/immortalwrt/immortalwrt.git
git -C "$TREE" fetch --depth=1 origin refs/tags/v25.12.2
git -C "$TREE" checkout --detach FETCH_HEAD
test "$(git -C "$TREE" rev-parse HEAD)" = "$(read_lock immortalwrt)"
python3 "$ROOT/scripts/prepare.py" "$TREE"
cd "$TREE"
# Official release feeds already contain pinned commits; retain those pins.
printf 'src-git nss_packages https://github.com/qosmio/nss-packages.git^%s\n' "$(read_lock nss_packages)" >> feeds.conf.default
printf 'src-git nikki https://github.com/nikkinikki-org/OpenWrt-nikki.git^%s\n' "$(read_lock nikki)" >> feeds.conf.default
./scripts/feeds update -a
./scripts/feeds install -a
for spec in 'argon luci-theme-argon' 'argon_config luci-app-argon-config'; do
  read -r key name <<< "$spec"
  # Prefer one known pinned recipe over a duplicate feed package.
  rm -f "package/feeds/luci/$name"
  git init "package/custom/$name"
  git -C "package/custom/$name" remote add origin "https://github.com/jerrykuku/$name.git"
  git -C "package/custom/$name" fetch --depth=1 origin "$(read_lock "$key")"
  git -C "package/custom/$name" checkout --detach FETCH_HEAD
done
python3 "$ROOT/scripts/feed-fixes.py" "$TREE"
cp "$ROOT/config/ax9000.config" .config
make defconfig
python3 "$ROOT/scripts/check-config.py" .config "$ROOT/config/ax9000.config"
./scripts/diffconfig.sh > config.seed
git diff --binary > source-changes.patch
cp "$ROOT/sources.lock.json" sources.lock.json
mkdir -p "$ROOT/logs"
for feed in feeds/*; do
  if test -d "$feed/.git"; then
    printf '%s %s\n' "$feed" "$(git -C "$feed" rev-parse HEAD)"
  fi
done > "$ROOT/logs/feed-commits.txt"
