#!/bin/sh
# shellcheck shell=ash
#
# Validate OpenWrt SDK download URL (tarball)
# Fails fast if SDK URL is not accessible
#
# Usage:
#   validate-sdk-url.sh <sdk_version> [target] [arch]
#
# Examples:
#   validate-sdk-url.sh 23.05.2 x86/64 x86-64
#   validate-sdk-url.sh 22.03.5
#

set -eu
if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

# Source color library for consistent output formatting
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/colors.sh"

# Function to print error message and exit
error_exit() {
    printf "%sError:%s %s\n" "$RED" "$NC" "$1" >&2
    exit 1
}

# Function to print info message
info() {
    printf "%sInfo:%s %s\n" "$BLUE" "$NC" "$1"
}

# Function to print success message
success() {
    printf "%sSuccess:%s %s\n" "$GREEN" "$NC" "$1"
}

# Default values
SDK_VERSION="$1"
TARGET="${2:-x86/64}"
ARCH="${3:-x86-64}"

# Validate arguments
if [ $# -lt 1 ]; then
    error_exit "Usage: validate-sdk-url.sh <sdk_version> [target] [arch]"
fi

info "Validating OpenWrt SDK download URL..."
echo "  SDK Version: $SDK_VERSION"
echo "  Target: $TARGET"
echo "  Architecture: $ARCH"
echo ""

# Validate OpenWrt version format
if ! echo "$SDK_VERSION" | grep -qE '^[0-9]+\.[0-9]+(\.[0-9]+)?$'; then
    error_exit "Invalid OpenWrt version format: $SDK_VERSION (expected: X.Y or X.Y.Z)"
fi

# Validate target format
if ! echo "$TARGET" | grep -qE '^[a-z0-9]+/[a-z0-9]+$'; then
    error_exit "Invalid target format: $TARGET (expected: target/subtarget, e.g., x86/64)"
fi

# Validate arch format
if ! echo "$ARCH" | grep -qE '^[a-z0-9-]+$'; then
    error_exit "Invalid architecture format: $ARCH (expected: alphanumeric and hyphens)"
fi

# Construct SDK filename and URLs
SDK_FILE="openwrt-sdk-${SDK_VERSION}-${ARCH}_gcc-12.3.0_musl.Linux-x86_64.tar.xz"

# Primary and fallback mirrors
info "Checking SDK download URLs..."
valid_mirror_found=false

# Check each mirror in sequence
for mirror in \
    "https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-${SDK_VERSION}/${SDK_FILE}" \
    "https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/${TARGET}/${SDK_FILE}" \
    "https://mirror2.openwrt.org/sources/${SDK_FILE}" \
    "https://mirror.bytemark.co.uk/openwrt/releases/${SDK_VERSION}/targets/${TARGET}/${SDK_FILE}"; do
    printf "  Checking: %s\n" "$mirror"

    # Use curl to check if URL is accessible with timeout
    if curl --head --silent --connect-timeout 10 --max-time 30 "$mirror" | grep -q "HTTP/.* 200"; then
        success "URL is accessible: $mirror"
        valid_mirror_found=true
        break
    else
        printf "%sWarning:%s URL not accessible: %s\n" "$YELLOW" "$NC" "$mirror" >&2
    fi
done

if [ "$valid_mirror_found" = false ]; then
    error_exit "No accessible SDK mirrors found for version $SDK_VERSION

This usually means:
1. The OpenWrt version ($SDK_VERSION) doesn't exist
2. The target/architecture combination ($TARGET / $ARCH) is not supported
3. Network connectivity issues

Please verify:
- The OpenWrt version is correct
- The target/architecture combination is valid
- Network connectivity is working"
fi

success "SDK URL validation passed"
