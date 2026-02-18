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
if ! command -v dpkg-deb >/dev/null 2>&1; then
    if [ "$EUID" -eq 0 ]; then
        apt-get update
        apt-get install -y dpkg-dev
    else
        sudo apt-get update
        sudo apt-get install -y dpkg-dev
    fi
else
    echo "dpkg-deb found, skipping installation"
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/deb

# Create build directory in /tmp to avoid WSL permission issues
BUILD_DIR=$(mktemp -d)
echo "Using build directory: $BUILD_DIR"

mkdir -p "$BUILD_DIR/openwrt-captive-monitor/DEBIAN"
mkdir -p "$BUILD_DIR/openwrt-captive-monitor/usr/bin"
mkdir -p "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor"
mkdir -p "$BUILD_DIR/openwrt-captive-monitor/lib/systemd/system"
mkdir -p "$BUILD_DIR/openwrt-captive-monitor/usr/share/doc/openwrt-captive-monitor"

# Fix permissions for DEBIAN directory (required by dpkg-deb)
chmod 755 "$BUILD_DIR/openwrt-captive-monitor/DEBIAN"

# Create control file
cat > "$BUILD_DIR/openwrt-captive-monitor/DEBIAN/control" <<EOF
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
cp debian/postinst "$BUILD_DIR/openwrt-captive-monitor/DEBIAN/"
chmod 755 "$BUILD_DIR/openwrt-captive-monitor/DEBIAN/postinst"

# Copy prerm script
cp debian/prerm "$BUILD_DIR/openwrt-captive-monitor/DEBIAN/"
chmod 755 "$BUILD_DIR/openwrt-captive-monitor/DEBIAN/prerm"

# Install main script
install -m 755 tools/captive_portal_wsl_selenium.py "$BUILD_DIR/openwrt-captive-monitor/usr/bin/captive-portal-monitor"

# Install Python modules
install -m 644 tools/__init__.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"
install -m 644 tools/conn4_auth_lib.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"
install -m 644 tools/conn4_shared.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"
install -m 644 tools/conn4_utils.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"
install -m 644 tools/conn4_wbs_client.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"
install -m 644 tools/html_form_parser.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"
install -m 644 tools/schema_utils.py "$BUILD_DIR/openwrt-captive-monitor/usr/lib/python3/dist-packages/captive_monitor/"

# Install systemd service
install -m 644 debian/captive-portal-monitor.service "$BUILD_DIR/openwrt-captive-monitor/lib/systemd/system/"

# Install documentation
install -m 644 README.md "$BUILD_DIR/openwrt-captive-monitor/usr/share/doc/openwrt-captive-monitor/"
install -m 644 LICENSE "$BUILD_DIR/openwrt-captive-monitor/usr/share/doc/openwrt-captive-monitor/"

# Build package
echo "Building package..."
dpkg-deb --build "$BUILD_DIR/openwrt-captive-monitor"

# Move to dist directory
mkdir -p dist/deb
mv "$BUILD_DIR/openwrt-captive-monitor.deb" "dist/deb/openwrt-captive-monitor_${VERSION}-1_all.deb"

# Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "=== Build complete ==="
ls -lh dist/deb/*.deb

echo ""
echo "To install:"
echo "  sudo dpkg -i dist/deb/openwrt-captive-monitor_${VERSION}-1_all.deb"
echo "  sudo apt-get install -f  # Install dependencies"
