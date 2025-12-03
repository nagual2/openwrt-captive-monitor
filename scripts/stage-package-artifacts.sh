#!/bin/sh
# Stage .ipk artifacts into a clean package/ directory with SHA256SUMS
#
# This script:
#   1. Creates a clean package/ directory in the workspace
#   2. Copies .ipk files from the build artifacts directory
#   3. Generates SHA256SUMS checksum file
#
# Usage: stage-package-artifacts.sh <artifacts_dir>
#
# Environment variables:
#   WORKSPACE_PACKAGE_DIR: Override package directory path (default: package/)

set -eu

# Enable pipefail where supported (BusyBox ash compatible); safe for POSIX sh when guarded.
# shellcheck disable=SC3040
if (set -o pipefail) 2> /dev/null; then
    set -o pipefail
fi

# Source colors for consistent output
script_dir=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=scripts/lib/colors.sh
. "$script_dir/lib/colors.sh"

if [ "$#" -lt 1 ]; then
    echo "error: missing artifacts directory argument" >&2
    exit 1
fi

artifacts_dir="$1"
package_dir="${WORKSPACE_PACKAGE_DIR:-package}"

# Verify artifacts directory exists
if [ ! -d "$artifacts_dir" ]; then
    printf '%s\n' "${RED}error: artifacts directory not found: $artifacts_dir${NC}" >&2
    exit 1
fi

# Create clean package directory
printf '%s\n' "${BLUE}Creating clean package directory: $package_dir${NC}"
rm -rf "$package_dir"
mkdir -p "$package_dir"

# Find and copy all .ipk files
ipk_count=0
for ipk_file in "$artifacts_dir"/*.ipk; do
    if [ -e "$ipk_file" ]; then
        basename_ipk=$(basename "$ipk_file")
        printf '%s\n' "${GREEN}Copying:${NC} $basename_ipk"
        cp -f "$ipk_file" "$package_dir/"
        ipk_count=$((ipk_count + 1))
    fi
done

if [ "$ipk_count" -eq 0 ]; then
    printf '%s\n' "${RED}error: no .ipk files found in $artifacts_dir${NC}" >&2
    exit 1
fi

printf '%s\n' "${BLUE}Staged $ipk_count .ipk file(s)${NC}"

# Generate SHA256SUMS
printf '%s\n' "${BLUE}Generating SHA256SUMS...${NC}"
cd "$package_dir"

if command -v sha256sum > /dev/null 2>&1; then
    # Use ./*glob* form so filenames beginning with '-' are handled safely
    sha256sum ./*.ipk > SHA256SUMS
elif command -v shasum > /dev/null 2>&1; then
    # Use ./*glob* form so filenames beginning with '-' are handled safely
    shasum -a 256 ./*.ipk > SHA256SUMS
else
    printf '%s\n' "${RED}error: neither sha256sum nor shasum found${NC}" >&2
    exit 1
fi

printf '%s\n' "${GREEN}SHA256SUMS created successfully${NC}"
cat SHA256SUMS

cd - > /dev/null

printf '%s\n' "${BLUE}Package directory prepared:${NC}"
ls -la "$package_dir"

printf '%s\n' "${GREEN}✓ Package staging complete${NC}"
