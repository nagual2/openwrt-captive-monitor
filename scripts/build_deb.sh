#!/bin/bash
set -euo pipefail

# Build Debian package for openwrt-captive-monitor
# Usage: bash scripts/build_deb.sh

echo "=== Building Debian package ==="

# Check if we're in the project root
if [ ! -f "VERSION" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Read version
VERSION=$(cat VERSION | tr -d '\n\r')
echo "Version: $VERSION"

# Install build dependencies (skip if already installed)
echo "Installing build dependencies..."
if command -v dpkg-deb >/dev/null 2>&1; then
    echo "dpkg-deb found, skipping apt-get update"
else
    sudo apt-get update
    sudo apt-get install -y dpkg-dev
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/deb
mkdir -p dist/deb/openwrt-captive-monitor/DEBIAN
mkdir -p dist/deb/openwrt-captive-monitor/usr/bin
mkdir -p dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor
mkdir -p dist/deb/openwrt-captive-monitor/lib/systemd/system
mkdir -p dist/deb/openwrt-captive-monitor/usr/share/doc/openwrt-captive-monitor

# Create control file
cat > dist/deb/openwrt-captive-monitor/DEBIAN/control <<EOF
Package: openwrt-captive-monitor
Version: ${VERSION}-1
Section: net
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-selenium, python3-requests, python3-dotenv, chromium-browser | google-chrome-stable, chromium-chromedriver | google-chrome-stable
Maintainer: OpenWrt Captive Monitor Team <nahual15@gmail.com>
Description: Automatic captive portal authentication for Conn4 portals
 This package provides automatic authentication against Conn4-based
 captive portals (e.g., Leonardo Hotels) using Selenium and Chrome.
 .
 The service runs as a systemd daemon and monitors network connectivity,
 automatically authenticating when a captive portal is detected.
 .
 Recommended hardware: Raspberry Pi 3+, x86-64 mini-PC with 4GB+ RAM.
Homepage: https://github.com/nagual2/openwrt-captive-monitor
EOF

# Copy postinst script
cp debian/postinst dist/deb/openwrt-captive-monitor/DEBIAN/
chmod 755 dist/deb/openwrt-captive-monitor/DEBIAN/postinst

# Copy prerm script
cp debian/prerm dist/deb/openwrt-captive-monitor/DEBIAN/
chmod 755 dist/deb/openwrt-captive-monitor/DEBIAN/prerm

# Install main script
install -m 755 tools/captive_portal_wsl_selenium.py dist/deb/openwrt-captive-monitor/usr/bin/captive-portal-monitor

# Install Python modules
install -m 644 tools/__init__.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/
install -m 644 tools/conn4_auth_lib.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/
install -m 644 tools/conn4_shared.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/
install -m 644 tools/conn4_utils.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/
install -m 644 tools/conn4_wbs_client.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/
install -m 644 tools/html_form_parser.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/
install -m 644 tools/schema_utils.py dist/deb/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/

# Install systemd service
install -m 644 debian/captive-portal-monitor.service dist/deb/openwrt-captive-monitor/lib/systemd/system/

# Install documentation
install -m 644 README.md dist/deb/openwrt-captive-monitor/usr/share/doc/openwrt-captive-monitor/
install -m 644 LICENSE dist/deb/openwrt-captive-monitor/usr/share/doc/openwrt-captive-monitor/

# Build package
echo "Building package..."
dpkg-deb --build dist/deb/openwrt-captive-monitor

# Rename to proper name
mv dist/deb/openwrt-captive-monitor.deb dist/deb/openwrt-captive-monitor_${VERSION}-1_all.deb

echo ""
echo "=== Build complete ==="
ls -lh dist/deb/*.deb

echo ""
echo "To install:"
echo "  sudo dpkg -i dist/deb/openwrt-captive-monitor_${VERSION}-1_all.deb"
echo "  sudo apt-get install -f  # Install dependencies"
