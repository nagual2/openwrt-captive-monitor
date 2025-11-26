#!/bin/bash
# Build all architectures in parallel using screen sessions

VERSION="23.05.5"
REGISTRY="ghcr.io/nagual2"
SHORT_SHA=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "local")

echo "=== Starting parallel builds in screen ==="
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo "Commit: $SHORT_SHA"
echo ""

# Create main screen session
screen -dmS openwrt-build bash

sleep 2

# Start builds in separate windows
echo "Starting x86-64..."
screen -S openwrt-build -X title "x86-64"
screen -S openwrt-build -p 0 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=x86 --build-arg SDK_SUBTARGET=64 --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting ath79-generic..."
screen -S openwrt-build -X screen -t "ath79-generic" bash
screen -S openwrt-build -p 1 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=ath79 --build-arg SDK_SUBTARGET=generic --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-ath79-generic-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting ramips-mt76x8..."
screen -S openwrt-build -X screen -t "ramips-mt76x8" bash
screen -S openwrt-build -p 2 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=ramips --build-arg SDK_SUBTARGET=mt76x8 --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-ramips-mt76x8-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting mediatek-filogic..."
screen -S openwrt-build -X screen -t "mediatek-filogic" bash
screen -S openwrt-build -p 3 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=mediatek --build-arg SDK_SUBTARGET=filogic --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-mediatek-filogic-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting ipq40xx-generic..."
screen -S openwrt-build -X screen -t "ipq40xx-generic" bash
screen -S openwrt-build -p 4 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=ipq40xx --build-arg SDK_SUBTARGET=generic --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-ipq40xx-generic-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting ipq806x-generic..."
screen -S openwrt-build -X screen -t "ipq806x-generic" bash
screen -S openwrt-build -p 5 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=ipq806x --build-arg SDK_SUBTARGET=generic --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-ipq806x-generic-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting bcm27xx-bcm2711..."
screen -S openwrt-build -X screen -t "bcm27xx-bcm2711" bash
screen -S openwrt-build -p 6 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=bcm27xx --build-arg SDK_SUBTARGET=bcm2711 --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-bcm27xx-bcm2711-latest --file docker/sdk/Dockerfile .\n'

sleep 1
echo "Starting rockchip-armv8..."
screen -S openwrt-build -X screen -t "rockchip-armv8" bash
screen -S openwrt-build -p 7 -X stuff $'docker build --build-arg UBUNTU_VERSION=24.04 --build-arg OPENWRT_VERSION=23.05.5 --build-arg SDK_TARGET=rockchip --build-arg SDK_SUBTARGET=armv8 --tag ghcr.io/nagual2/openwrt-sdk:23.05.5-rockchip-armv8-latest --file docker/sdk/Dockerfile .\n'

echo ""
echo "✅ All 8 builds started in screen session 'openwrt-build'"
echo ""
echo "To attach: screen -r openwrt-build"
echo "Switch windows: Ctrl+A then 0-7"
echo "Detach: Ctrl+A then d"
