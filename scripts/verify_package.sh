#!/bin/bash
# Verification script for package contents
set -eu

PACKAGE_FILE="dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "Package file not found: $PACKAGE_FILE"
    echo "Run ./scripts/build_ipk.sh first"
    exit 1
fi

echo "=== Package Verification ==="
echo "Package: $PACKAGE_FILE"
echo "Size: $(stat -c%s "$PACKAGE_FILE") bytes"
echo ""

# Extract and list contents
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

cd "$TEMP_DIR"
ar x "/home/engine/project/$PACKAGE_FILE"

echo "=== Data Archive Contents ==="
tar -tzf data.tar.gz | sort

echo ""
echo "=== Control Archive Contents ==="
tar -tzf control.tar.gz | sort

echo ""
echo "=== File Details ==="
tar -xzf data.tar.gz
echo "Data files:"
find . -path "*.tar.gz" -prune -o -type f -exec ls -la {} \; | grep -v "\.tar\.gz"

echo ""
echo "Control files:"
tar -xzf control.tar.gz
find . -name "*.tar.gz" -prune -o -type f -exec ls -la {} \; | grep -v "\.tar\.gz"

echo ""
echo "=== Package Metadata ==="
cat control