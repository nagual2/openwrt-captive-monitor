#!/bin/sh
# shellcheck shell=ash
#
# Validate OpenWrt SDK Docker image tag and target/subtarget
# Fails fast if the Docker image is not available in the registry
#
# Usage:
#   validate-sdk-image.sh <container_image> <sdk_target> <openwrt_version> <sdk_slug>
#
# Examples:
#   validate-sdk-image.sh ghcr.io/openwrt/sdk:x86_64-23.05.3 x86/64 23.05.3 x86_64
#

set -eu
if (set -o pipefail) 2> /dev/null; then
# shellcheck disable=SC3040
set -o pipefail
fi

# Source color library for consistent output formatting
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/colors.sh
. "$SCRIPT_DIR/lib/colors.sh"

# Function to print error message and exit
error_exit() {
printf "%sError:%s %s\n" "$RED" "$NC" "$1" >&2
exit 1
}

# Function to print warning message
warn() {
printf "%sWarning:%s %s\n" "$YELLOW" "$NC" "$1" >&2
}

# Function to print info message
info() {
printf "%sInfo:%s %s\n" "$BLUE" "$NC" "$1"
}

# Function to print success message
success() {
printf "%sSuccess:%s %s\n" "$GREEN" "$NC" "$1"
}

# Validate arguments
if [ $# -lt 4 ]; then
error_exit "Usage: validate-sdk-image.sh <container_image> <sdk_target> <openwrt_version> <sdk_slug>"
fi

CONTAINER_IMAGE="$1"
SDK_TARGET="$2"
OPENWRT_VERSION="$3"
SDK_SLUG="$4"

info "Validating OpenWrt SDK image and target..."
echo "  Container Image: $CONTAINER_IMAGE"
echo "  SDK Target: $SDK_TARGET"
echo "  OpenWrt Version: $OPENWRT_VERSION"
echo "  SDK Slug: $SDK_SLUG"
echo ""

# Validate OpenWrt version format
if ! echo "$OPENWRT_VERSION" | grep -qE '^[0-9]+\.[0-9]+(\.[0-9]+)?$'; then
error_exit "Invalid OpenWrt version format: $OPENWRT_VERSION (expected: X.Y or X.Y.Z)"
fi

# Validate SDK target format
if ! echo "$SDK_TARGET" | grep -qE '^[a-z0-9]+/[a-z0-9]+$'; then
error_exit "Invalid SDK target format: $SDK_TARGET (expected: target/subtarget, e.g., x86/64)"
fi

# Validate SDK slug format (should match target with / replaced by -)
if ! echo "$SDK_SLUG" | grep -qE '^[a-z0-9_-]+$'; then
error_exit "Invalid SDK slug format: $SDK_SLUG (expected: alphanumeric, hyphens and underscores)"
fi

# Verify container image tag format
expected_tag="$SDK_SLUG-$OPENWRT_VERSION"
if ! echo "$CONTAINER_IMAGE" | grep -q "$expected_tag"; then
error_exit "Container image tag mismatch. Expected suffix: $expected_tag, got: $CONTAINER_IMAGE"
fi

# Check if Docker/Podman is available
if ! command -v docker >/dev/null 2>&1; then
error_exit "Docker is not available. Cannot validate container image."
fi

info "Checking Docker image availability in registry..."

# Attempt to inspect the manifest
# Using --dry-run flag to avoid pulling the image, just checking if it exists
max_attempts=3
attempt=1
while [ $attempt -le $max_attempts ]; do
printf "  Attempt %d/%d: " "$attempt" "$max_attempts"

if docker manifest inspect "$CONTAINER_IMAGE" >/dev/null 2>&1; then
success "Docker image exists in registry"
success "SDK image validation passed"
exit 0
fi

if [ $attempt -lt $max_attempts ]; then
printf "Retrying in 5 seconds...\n"
sleep 5
fi
attempt=$((attempt + 1))
done

# Image not found after retries
error_exit "Docker image not found in registry: $CONTAINER_IMAGE

This usually means:
1. The OpenWrt version ($OPENWRT_VERSION) doesn't exist
2. The target/subtarget combination ($SDK_TARGET / $SDK_SLUG) is not supported
3. Network connectivity issue (even after $max_attempts attempts)

Please verify:
- The OpenWrt version is correct
- The target/subtarget combination is valid
- Network connectivity is working"