#!/bin/sh
# shellcheck shell=ash
# Verification script for package contents
set -eu

if [ "${TRACE:-0}" = "1" ]; then
    set -x
fi

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)

require_command() {
    local cmd="$1"
    if ! command -v "$cmd" > /dev/null 2>&1; then
        echo "error: required command '$cmd' not found in PATH" >&2
        exit 1
    fi
}

require_command ar
require_command tar
require_command stat
require_command find
require_command sort
require_command mktemp

resolve_path() {
    case "$1" in
        /*)
            printf '%s\n' "$1"
            ;;
        *)
            printf '%s/%s\n' "$repo_root" "${1#./}"
            ;;
    esac
}

print_usage() {
    cat << 'EOF'
Usage: scripts/verify_package.sh [package.ipk]

When no package path is provided, the script searches under dist/opkg for the
latest openwrt-captive-monitor package and verifies its contents. A package can
also be provided with the PACKAGE_FILE environment variable.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    print_usage
    exit 0
fi

package_input="${1:-${PACKAGE_FILE:-}}"

if [ -n "$package_input" ]; then
    package_path=$(resolve_path "$package_input")
else
    package_dir=$(resolve_path "${PACKAGE_DIR:-dist/opkg}")
    if [ ! -d "$package_dir" ]; then
        echo "error: package directory not found: $package_dir" >&2
        exit 1
    fi

    # Find the most recent package using find and sort (POSIX compatible)
    package_path=$(find "$package_dir" -type f -name 'openwrt-captive-monitor_*.ipk' -print 2> /dev/null | sort -r | head -n 1 || true)
    if [ -z "$package_path" ]; then
        echo "error: no openwrt-captive-monitor package found under $package_dir" >&2
        echo "run ./scripts/build_ipk.sh first" >&2
        exit 1
    fi
fi

if [ ! -f "$package_path" ]; then
    echo "error: package file not found: $package_path" >&2
    echo "run ./scripts/build_ipk.sh first" >&2
    exit 1
fi

package_rel="$package_path"
case "$package_rel" in
    "$repo_root"/*)
        package_rel="${package_rel#"$repo_root"/}"
        ;;
esac

package_size=$(stat -c%s "$package_path")

echo "=== Package Verification ==="
echo "Package: $package_rel"
echo "Size: $package_size bytes"

# Check file type
if command -v file > /dev/null 2>&1; then
    file_type=$(file "$package_path")
    echo "File type: $file_type"

    # Modern OpenWrt IPK packages are tar.gz archives
    # Legacy IPK packages are ar archives
    if echo "$file_type" | grep -q "gzip compressed"; then
        echo "Detected gzip compressed file (modern IPK format)"
    elif echo "$file_type" | grep -q "ar archive\|current ar archive"; then
        echo "Detected ar archive (legacy IPK format)"
    else
        echo "WARNING: Unexpected file type for IPK package"
    fi
fi

# Check if it's a symlink
if [ -L "$package_path" ]; then
    echo "WARNING: Package is a symlink to: $(readlink -f "$package_path")"
fi

echo ""

temp_dir=$(mktemp -d)
cleanup() {
    rm -rf "$temp_dir"
    [ -f "$package_path.decompressed" ] && rm -f "$package_path.decompressed"
    [ -d "$package_path.extracted" ] && rm -rf "$package_path.extracted"
}
trap cleanup EXIT INT TERM HUP

work_dir="$temp_dir/ipk"
mkdir -p "$work_dir"

# Modern OpenWrt IPK packages are tar.gz archives, not ar archives
# Try to extract as tar.gz first, fall back to ar if that fails
if tar -xzf "$package_path" -C "$work_dir" 2> /dev/null; then
    echo "Extracted as tar.gz archive (modern IPK format)"
else
    echo "Attempting to extract as ar archive (legacy IPK format)"
    (
        cd "$work_dir"
        ar x "$package_path"
    )
fi

for archive in data.tar.gz control.tar.gz; do
    if [ ! -f "$work_dir/$archive" ]; then
        echo "error: expected $archive inside $package_rel" >&2
        exit 1
    fi
    if ! tar -tzf "$work_dir/$archive" > /dev/null 2>&1; then
        echo "error: unable to list $archive contents" >&2
        exit 1
    fi
done

echo "=== Data Archive Contents ==="
tar -tzf "$work_dir/data.tar.gz" | sort

echo ""
echo "=== Control Archive Contents ==="
tar -tzf "$work_dir/control.tar.gz" | sort

data_dir="$temp_dir/data"
control_dir="$temp_dir/control"
mkdir -p "$data_dir" "$control_dir"

tar -xzf "$work_dir/data.tar.gz" -C "$data_dir"
tar -xzf "$work_dir/control.tar.gz" -C "$control_dir"

echo ""
echo "=== File Details ==="
echo "Data files:"
find "$data_dir" -type f -exec ls -la {} + 2> /dev/null | sort || echo "No data files found"

echo ""
echo "Control files:"
find "$control_dir" -type f -exec ls -la {} + 2> /dev/null | sort || echo "No control files found"

control_file=""
if [ -f "$control_dir/control" ]; then
    control_file="$control_dir/control"
else
    control_file=$(find "$control_dir" -type f -name control | head -n 1 || true)
fi

echo ""
echo "=== Package Metadata ==="
if [ -n "$control_file" ] && [ -f "$control_file" ]; then
    cat "$control_file"
else
    echo "warning: control metadata not found"
fi

exit 0
