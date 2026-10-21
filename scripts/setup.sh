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
python3 "$ROOT/scripts/feed-fixes.py" "$TREE"
python3 "$ROOT/scripts/local-packages.py" "$TREE"
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
