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

    # If file is gzip compressed, try to decompress it first
    if echo "$file_type" | grep -q "gzip compressed"; then
        echo "WARNING: File is gzip compressed, attempting to decompress..."
        temp_ipk="$package_path.decompressed"
        if gunzip -c "$package_path" > "$temp_ipk" 2> /dev/null; then
            echo "Decompressed successfully, using decompressed file"
            new_file_type=$(file "$temp_ipk")
            echo "New file type: $new_file_type"
            
            # If decompressed file is a tar archive, extract it and find the real .ipk
            if echo "$new_file_type" | grep -q "tar archive"; then
                echo "WARNING: Decompressed file is a tar archive, extracting..."
                temp_extract_dir="$package_path.extracted"
                mkdir -p "$temp_extract_dir"
                if tar -xf "$temp_ipk" -C "$temp_extract_dir" 2> /dev/null; then
                    # Find .ipk file inside the tar
                    real_ipk=$(find "$temp_extract_dir" -name "*.ipk" -type f | head -1)
                    if [ -n "$real_ipk" ] && [ -f "$real_ipk" ]; then
                        echo "Found real .ipk file: $real_ipk"
                        package_path="$real_ipk"
                        echo "Real file type: $(file "$package_path")"
                    else
                        echo "ERROR: No .ipk file found in tar archive" >&2
                    fi
                else
                    echo "ERROR: Failed to extract tar archive" >&2
                fi
            else
                package_path="$temp_ipk"
            fi
        else
            echo "ERROR: Failed to decompress file" >&2
        fi
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

(
    cd "$work_dir"
    ar x "$package_path"
)

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
