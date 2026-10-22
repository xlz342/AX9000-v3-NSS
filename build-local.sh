#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
BASE=$(dirname "$ROOT")
TREE="$BASE/build"
mkdir -p "$ROOT/logs" "$ROOT/artifacts"
exec > >(tee -a "$BASE/pipeline-v4-full.log") 2>&1
trap 'rc=$?; echo "exit=$rc" > "$BASE/status-v4-full"' EXIT
if ! test -f "$TREE/config.seed"; then
 bash "$ROOT/scripts/setup.sh" "$TREE"
fi
cd "$TREE"
export FORCE_UNSAFE_CONFIGURE=1
# Windows PATH entries contain spaces/parentheses unsafe in the Go make recipes.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export GOPROXY=https://goproxy.cn
make download -j8 V=s 2>&1 | tee "$ROOT/logs/download.log"
make -j10 V=s 2>&1 | tee "$ROOT/logs/build.log" || make -j1 V=s 2>&1 | tee "$ROOT/logs/build-retry.log"
python3 "$ROOT/scripts/validate-image.py" "$TREE" "$ROOT/artifacts"
python3 "$ROOT/scripts/check-plugins.py" "$TREE" "$ROOT/artifacts"
python3 "$ROOT/scripts/date-filenames.py" "$ROOT/artifacts"
cp "$TREE/config.seed" "$ROOT/artifacts/"
cp "$ROOT/local-packages.lock.json" "$ROOT/artifacts/"
cp "$ROOT/sources.lock.json" "$ROOT/artifacts/"
cp "$ROOT/tests/test_coexist.py" "$ROOT/artifacts/"
cp "$ROOT/README.md" "$ROOT/artifacts/COEXIST-TEST-README.md"
cat > "$ROOT/artifacts/README-local.txt" <<'EOF'
AX9000 stock / ImmortalWrt 25.12.2 / NSS + ath11k NSS, locally built.
Full AX9000-v4-NSS-11 base: Nikki/Mihomo, Argon, SmartDNS, OpenSSH retained.
Added: PassWall (Xray), UPnP, WireGuard, AirConnect 1.12.4, UU 14.10.6.
Optional services disabled until configured. PassWall or Nikki keeps ECM/NSS enabled; proxy crypto remains CPU work. Experimental, no hardware acceptance.
Stock partition/calibration/U-Boot logic preserved. No private backup included.
AirConnect binaries are upstream static aarch64 release binaries. UU is official
precompiled aarch64 plugin packaged using ttc0419/uuplugin init service.
CI/offline validation is not on-device wireless/proxy acceptance.
EOF
cd "$ROOT/artifacts"
find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\0' | sort -z | xargs -0 sha256sum > "$BASE/all-SHA256SUMS"
cp "$BASE/all-SHA256SUMS" SHA256SUMS
DEST=/mnt/c/Users/Administrator/Downloads/AX9000-v4-full-coexist-20261022
mkdir -p "$DEST"
cp -a . "$DEST/"
# Publish the exact local recipe on a branch with no workflows, avoiding Actions.
cd "$ROOT"
if ! test -d .git; then
 git init -b v4-full-coexist-20261022
 git config user.name xlz342
 git config user.email xlz342@users.noreply.github.com
 printf '\nlocal-vendor/\n' >> .gitignore
 git add tests config files inputs reference scripts vendor sources.lock.json local-packages.lock.json build-local.sh README.md .gitignore
 git commit -m "AX9000 local PassWall variant [skip ci]"
 git remote add origin https://github.com/xlz342/AX9000-v3-NSS.git
 git push -u origin v4-full-coexist-20261022
fi
cd "$ROOT/artifacts"
TAG=AX9000-v4-full-coexist-20261022
if ! gh release view "$TAG" -R xlz342/AX9000-v3-NSS >/dev/null 2>&1; then
 gh release create "$TAG" -R xlz342/AX9000-v3-NSS --target v4-full-coexist-20261022 --prerelease --title "AX9000 v4 full ECM-NSS coexist 20261022" --notes-file README-local.txt
fi
gh release upload "$TAG" ./* -R xlz342/AX9000-v3-NSS --clobber
printf 'success: locally compiled, validated, copied and uploaded
'
