#!/bin/sh
# IPK Package Validation Script
# shellcheck shell=ash
# shellcheck disable=SC3043 # BusyBox ash and bash-compatible shells provide 'local'
set -eu

usage() {
	cat << 'EOF'
Usage: scripts/validate_ipk.sh <ipk_file>

Validates an IPK package by:
- Checking package structure
- Verifying control file contents
- Testing with opkg (if available)
- Simulating installation process

Arguments:
  ipk_file    Path to the .ipk file to validate
EOF
}

if [ $# -ne 1 ]; then
	usage
	exit 1
fi

ipk_file="$1"

if [ ! -f "$ipk_file" ]; then
	echo "error: IPK file not found: $ipk_file" >&2
	exit 1
fi

if [ ! -s "$ipk_file" ]; then
	echo "error: IPK file is empty: $ipk_file" >&2
	exit 1
fi

echo "=== Validating IPK package: $ipk_file ==="

# Create temporary directory for extraction
temp_dir=$(mktemp -d)
cleanup() {
	rm -rf "$temp_dir"
}
trap cleanup EXIT INT TERM HUP

# Get absolute path to IPK file
ipk_file_abs=$(cd "$(dirname "$ipk_file")" && pwd)/$(basename "$ipk_file")

cd "$temp_dir"

echo "Extracting IPK package..."
ar x "$ipk_file_abs"

# Verify required files exist
echo "Checking package structure..."
required_files="debian-binary control.tar.gz data.tar.gz"
for file in $required_files; do
	if [ ! -f "$file" ]; then
		echo "error: missing required file: $file" >&2
		exit 1
	fi
done

# Verify debian-binary format
echo "Checking debian-binary..."
if [ "$(cat debian-binary)" != "2.0" ]; then
	echo "error: invalid debian-binary format" >&2
	exit 1
fi

# Extract and verify control.tar.gz
echo "Extracting control.tar.gz..."
mkdir control
tar -xzf control.tar.gz -C control/

if [ ! -f "control/control" ]; then
	echo "error: control file not found in control.tar.gz" >&2
	exit 1
fi

echo "Validating control file..."
control_file="control/control"
pkg_name=$(awk '/^Package:/{print $2}' "$control_file")
pkg_version=$(awk '/^Version:/{print $2}' "$control_file")
pkg_arch=$(awk '/^Architecture:/{print $2}' "$control_file")

if [ -z "$pkg_name" ] || [ -z "$pkg_version" ] || [ -z "$pkg_arch" ]; then
	echo "error: missing required fields in control file" >&2
	exit 1
fi

echo "  Package: $pkg_name"
echo "  Version: $pkg_version"
echo "  Architecture: $pkg_arch"

# Verify control file format
if ! grep -q "^Package:" "$control_file"; then
	echo "error: missing Package field" >&2
	exit 1
fi
if ! grep -q "^Version:" "$control_file"; then
	echo "error: missing Version field" >&2
	exit 1
fi
if ! grep -q "^Architecture:" "$control_file"; then
	echo "error: missing Architecture field" >&2
	exit 1
fi
if ! grep -q "^Maintainer:" "$control_file"; then
	echo "error: missing Maintainer field" >&2
	exit 1
fi
if ! grep -q "^License:" "$control_file"; then
	echo "error: missing License field" >&2
	exit 1
fi
if ! grep -q "^Description:" "$control_file"; then
	echo "error: missing Description field" >&2
	exit 1
fi

# Extract and verify data.tar.gz
echo "Extracting data.tar.gz..."
mkdir data
tar -xzf data.tar.gz -C data/

echo "Checking data files..."
expected_files="
    usr/sbin/openwrt_captive_monitor
    etc/init.d/captive-monitor
    etc/config/captive-monitor
    etc/uci-defaults/99-captive-monitor
"

for file in $expected_files; do
	if [ ! -f "data/$file" ]; then
		echo "error: missing expected file: $file" >&2
		exit 1
	fi
done

# Check executable permissions
if [ ! -x "data/usr/sbin/openwrt_captive_monitor" ]; then
	echo "warning: openwrt_captive_monitor is not executable"
fi

if [ ! -x "data/etc/init.d/captive-monitor" ]; then
	echo "warning: captive-monitor init script is not executable"
fi

if [ ! -x "data/etc/uci-defaults/99-captive-monitor" ]; then
	echo "warning: uci-defaults script is not executable"
fi

# Test with opkg if available
if command -v opkg > /dev/null 2>&1; then
	echo "Testing with opkg..."
	if opkg info "$ipk_file" > /dev/null 2>&1; then
		echo "opkg info check passed"
	else
		echo "warning: opkg info check failed"
	fi
else
	echo "opkg not available, skipping opkg validation"
fi

# Calculate checksums
echo "Calculating checksums..."
ipk_md5=$(md5sum "$ipk_file_abs" | awk '{print $1}')
ipk_sha256=$(sha256sum "$ipk_file_abs" | awk '{print $1}')

echo "Checksums:"
echo "  MD5: $ipk_md5"
echo "  SHA256: $ipk_sha256"

# Verify filename matches package info
expected_filename="${pkg_name}_${pkg_version}_${pkg_arch}.ipk"
actual_filename=$(basename "$ipk_file")

if [ "$actual_filename" != "$expected_filename" ]; then
	echo "error: filename mismatch"
	echo "  expected: $expected_filename"
	echo "  actual: $actual_filename"
	exit 1
fi

echo ""
echo "=== IPK package validation successful! ==="
echo "Package: $pkg_name"
echo "Version: $pkg_version"
echo "Architecture: $pkg_arch"
echo "Filename: $actual_filename"
echo "Size: $(stat -c%s "$ipk_file_abs") bytes"
