#!/bin/sh
set -e

# Download OpenWrt SDK with error handling
# This script is called from Dockerfile during build

echo "=== OpenWrt SDK Download Script ==="
echo "OpenWrt Version: ${OPENWRT_VERSION}"
echo "Target: ${SDK_TARGET}"
echo "Subtarget: ${SDK_SUBTARGET}"

# Determine MUSL suffix based on architecture
MUSL_SUFFIX="_musl"
if [ "${SDK_TARGET}" = "ipq40xx" ] || [ "${SDK_TARGET}" = "ipq806x" ]; then
    MUSL_SUFFIX="_musl_eabi"
fi

# Construct SDK filename and URLs
SDK_FILE="openwrt-sdk-${OPENWRT_VERSION}-${SDK_TARGET}-${SDK_SUBTARGET}_gcc-12.3.0${MUSL_SUFFIX}.Linux-x86_64.tar.xz"
SDK_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/${SDK_TARGET}/${SDK_SUBTARGET}/${SDK_FILE}"
SHA256_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/${SDK_TARGET}/${SDK_SUBTARGET}/sha256sums"

echo "SDK File: ${SDK_FILE}"
echo "SDK URL: ${SDK_URL}"

# Download SDK
echo "Downloading SDK..."
curl -fL --retry 15 --retry-delay 10 --retry-all-errors \
     --max-time 3600 --connect-timeout 60 --speed-limit 1000 --speed-time 30 \
     -o sdk.tar.xz "${SDK_URL}"

echo "SDK downloaded successfully"
ls -lh sdk.tar.xz

# Download checksums
echo "Downloading checksums..."
curl -fL --retry 5 --retry-delay 5 -o sha256sums "${SHA256_URL}"

# Verify checksum
echo "Verifying checksum for: ${SDK_FILE}"
grep "${SDK_FILE}" sha256sums | sha256sum -c -

echo "=== SDK Download Complete ==="
