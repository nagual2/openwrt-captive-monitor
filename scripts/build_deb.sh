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

# Install build dependencies
echo "Installing build dependencies..."
sudo apt-get update
sudo apt-get install -y debhelper dh-python python3-all python3-setuptools

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf debian/openwrt-captive-monitor
rm -f ../openwrt-captive-monitor_*.deb
rm -f ../openwrt-captive-monitor_*.build
rm -f ../openwrt-captive-monitor_*.buildinfo
rm -f ../openwrt-captive-monitor_*.changes

# Make scripts executable
chmod +x debian/rules
chmod +x debian/postinst
chmod +x debian/prerm

# Build package
echo "Building package..."
dpkg-buildpackage -us -uc -b

# Move package to dist directory
mkdir -p dist/deb
mv ../openwrt-captive-monitor_*.deb dist/deb/ || true
mv ../openwrt-captive-monitor_*.build dist/deb/ || true
mv ../openwrt-captive-monitor_*.buildinfo dist/deb/ || true
mv ../openwrt-captive-monitor_*.changes dist/deb/ || true

echo ""
echo "=== Build complete ==="
ls -lh dist/deb/

echo ""
echo "To install:"
echo "  sudo dpkg -i dist/deb/openwrt-captive-monitor_${VERSION}-1_all.deb"
echo "  sudo apt-get install -f  # Install dependencies"
