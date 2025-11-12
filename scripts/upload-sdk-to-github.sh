#!/bin/bash
set -e
REPO="nagual2/openwrt-captive-monitor"
SDK_VERSION="23.05.3"
SDK_FILE="openwrt-sdk-${SDK_VERSION}-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz"
SDK_URL="https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/x86/64/${SDK_FILE}"
# Download SDK once
echo "📥 Downloading SDK from official mirror..."
wget -q "$SDK_URL" -O "$SDK_FILE"
# Calculate checksum for integrity
SHA256=$(sha256sum "$SDK_FILE" | awk '{print $1}')
echo "✓ SDK downloaded: $SHA256"
# Create GitHub Release
echo "📤 Uploading to GitHub Release..."
gh release create "sdk-${SDK_VERSION}" "$SDK_FILE" \
    --title "OpenWrt SDK ${SDK_VERSION} Mirror" \
    --notes "SDK mirror for fast CI/CD builds. Checksum: $SHA256" \
    --repo "$REPO" ||
    echo "Release already exists, updating..."
# Update/create checksum file
echo "$SHA256  $SDK_FILE" > sdk-checksum.txt
gh release upload "sdk-${SDK_VERSION}" sdk-checksum.txt \
    --repo "$REPO" \
    --clobber || true
echo "✅ SDK uploaded to: https://github.com/$REPO/releases/download/sdk-${SDK_VERSION}/$SDK_FILE"
