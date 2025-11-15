#!/bin/sh
# Stage build artifacts into artifacts/<BUILD_NAME>
#
# This script discovers common OpenWrt build outputs and copies them into
# a deterministic artifacts directory under the repository root:
#   artifacts/<BUILD_NAME>/ ...
#
# BUILD_NAME resolution (in order of precedence):
#   1) If BUILD_NAME is provided in the environment, it is used as-is (sanitized)
#   2) Otherwise: $(date +%Y%m%d-%H%M%S)-<short git SHA or GITHUB_SHA>
#
# The script searches for artifacts in the following locations:
#   - dist/opkg/**/* (standalone .ipk and feed indices)
#   - **/bin/packages/**/* (SDK package outputs)
#   - **/bin/targets/**/* (SDK image/firmware outputs)
# and copies:
#   - *.ipk, Packages, Packages.gz
#   - *.img, *.img.gz, *.bin, *.tar, *.tar.gz
#   - *manifest*, *sha256sums*, *SHA256SUMS* and metadata (.json, .log, .txt)
#
# The script fails if no artifacts are found to avoid empty uploads.
# All paths are resolved relative to the repository root.

set -eu

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
cd "$repo_root"

sanitize_name() {
    # Allow only safe characters in folder names
    printf '%s' "$1" | sed 's/[^A-Za-z0-9._-]/-/g'
}

# Determine BUILD_NAME
build_name="${BUILD_NAME:-}"
if [ -z "$build_name" ]; then
    ts=$(date -u +%Y%m%d-%H%M%S)
    if [ -n "${GITHUB_SHA:-}" ]; then
        short_sha=$(printf '%s' "$GITHUB_SHA" | cut -c1-7)
    else
        short_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
    fi
    build_name="${ts}-${short_sha}"
fi
build_name=$(sanitize_name "$build_name")

# Target directory
artifacts_dir="$repo_root/artifacts/$build_name"
mkdir -p "$artifacts_dir"

# Build a list of files to stage
# Use a temporary file to store absolute paths to avoid word-splitting issues
list_file=$(mktemp)
cleanup() {
    rm -f "$list_file"
}
trap cleanup EXIT INT TERM HUP

add_if_exists() {
    # Usage: add_if_exists <glob>
    # Expands glob and appends existing files to list_file
    # shellcheck disable=SC2046
    for f in $1; do
        if [ -f "$f" ]; then
            printf '%s\n' "$f" >> "$list_file"
        fi
    done
}

# 1) dist/opkg
if [ -d "$repo_root/dist/opkg" ]; then
    # ipk and feed indices
    # shellcheck disable=SC2046
    find "$repo_root/dist/opkg" -type f \( \
        -name "*.ipk" -o \
        -name "Packages" -o \
        -name "Packages.gz" -o \
        -name "SHA256SUMS" -o \
        -name "*.json" -o \
        -name "*.log" -o \
        -name "*.txt" \
    \) -print >> "$list_file"
fi

# 2) **/bin/packages and **/bin/targets from provided roots or whole repo
search_roots="."
if [ "$#" -gt 0 ]; then
    # Accept additional search roots (e.g., SDK_DIR/bin)
    for p in "$@"; do
        if [ -d "$p" ]; then
            search_roots="$search_roots $p"
        fi
    done
fi

for root in $search_roots; do
    if [ -d "$root" ]; then
        # Direct package/feed artifacts under this root
        find "$root" -type f \( \
            -name "*.ipk" -o \
            -name "Packages" -o \
            -name "Packages.gz" -o \
            -name "SHA256SUMS*" -o \
            -name "*sha256sums*" -o \
            -name "*.json" -o \
            -name "*.log" -o \
            -name "*.txt" \
        \) -print >> "$list_file" || true

        # Packages outputs (.ipk, indices) inside bin/packages
        find "$root" -type f -path "*/bin/packages/*" \( \
            -name "*.ipk" -o \
            -name "Packages" -o \
            -name "Packages.gz" -o \
            -name "SHA256SUMS*" -o \
            -name "*sha256sums*" -o \
            -name "*.json" -o \
            -name "*.log" -o \
            -name "*.txt" \
        \) -print >> "$list_file" || true

        # Target/image outputs inside bin/targets
        find "$root" -type f -path "*/bin/targets/*" \( \
            -name "*.img" -o \
            -name "*.img.gz" -o \
            -name "*.bin" -o \
            -name "*.tar" -o \
            -name "*.tar.gz" -o \
            -name "*manifest*" -o \
            -name "SHA256SUMS*" -o \
            -name "*sha256sums*" \
        \) -print >> "$list_file" || true
    fi
done

# De-duplicate and copy
uniq_list=$(mktemp)
sort -u "$list_file" > "$uniq_list"
count=$(wc -l < "$uniq_list" | tr -d ' ')

if [ "$count" -eq 0 ]; then
    echo "error: no build artifacts found to stage into $artifacts_dir" >&2
    rm -f "$uniq_list"
    exit 1
fi

echo "Staging $count artifact(s) into $artifacts_dir"
while IFS= read -r src; do
    # Normalize source path to absolute for reliable comparisons
    case "$src" in
        /*) src_abs="$src" ;;
        ./*) src_abs="$repo_root/${src#./}" ;;
        *) src_abs="$repo_root/$src" ;;
    esac

    # Skip files that are already inside the destination artifacts directory
    case "$src_abs" in
        "$artifacts_dir"/*) continue ;;
    esac

    base=$(basename "$src_abs")
    # If file with same name exists, prefix with index to avoid clobber
    dest="$artifacts_dir/$base"
    if [ -e "$dest" ] && ! cmp -s "$src_abs" "$dest" 2>/dev/null; then
        i=1
        while [ -e "$artifacts_dir/${i}-$base" ]; do
            i=$((i+1))
        done
        dest="$artifacts_dir/${i}-$base"
    fi
    cp -f "$src_abs" "$dest"
    echo "  + $(basename "$dest")"
done < "$uniq_list"
rm -f "$uniq_list"

echo "BUILD_NAME=$build_name"
echo "ARTIFACTS_DIR=$artifacts_dir"
# Support GitHub Actions step outputs when GITHUB_OUTPUT is present
if [ -n "${GITHUB_OUTPUT:-}" ] && [ -w "$GITHUB_OUTPUT" ]; then
    {
        printf 'build_name=%s\n' "$build_name"
        printf 'artifacts_dir=%s\n' "$artifacts_dir"
        printf 'files_staged=%s\n' "$count"
    } >> "$GITHUB_OUTPUT"
fi

echo "Artifacts staged successfully."
