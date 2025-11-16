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
if (set -o pipefail) 2>/dev/null; then
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

# Attempt to validate the image availability using Docker if present,
# otherwise fall back to a registry HEAD request to GHCR.
info "Checking SDK image availability in registry..."

max_attempts=3
attempt=1

if command -v docker >/dev/null 2>&1; then
    # Prefer Docker manifest inspection when available
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
else
    # Fallback: Try to query GHCR registry for the manifest without pulling
    # Extract tag and ensure we hit the correct registry endpoint
    image_tag=$(printf '%s' "$CONTAINER_IMAGE" | sed 's/^.*://')
    registry_endpoint="https://ghcr.io/v2/openwrt/sdk/manifests/$image_tag"

    while [ $attempt -le $max_attempts ]; do
        printf "  Attempt %d/%d (curl HEAD): " "$attempt" "$max_attempts"
        # Try different common Accept headers for OCI/Docker manifest
        if curl -fsSLI \
            -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json" \
            "$registry_endpoint" >/dev/null 2>&1; then
            success "Registry responded for $registry_endpoint"
            success "SDK image validation passed"
            exit 0
        fi
        if [ $attempt -lt $max_attempts ]; then
            printf "Retrying in 5 seconds...\n"
            sleep 5
        fi
        attempt=$((attempt + 1))
    done
fi

# Image not found after retries
error_exit "SDK image not found or unreachable in registry: $CONTAINER_IMAGE

This usually means:
1. The OpenWrt version ($OPENWRT_VERSION) doesn't exist
2. The target/subtarget combination ($SDK_TARGET / $SDK_SLUG) is not supported
3. Registry/network connectivity issue (even after $max_attempts attempts)

Please verify:
- The OpenWrt version is correct
- The target/subtarget combination is valid
- Registry/network connectivity is working"
