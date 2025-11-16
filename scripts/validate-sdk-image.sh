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
# then fall back to a direct GHCR registry check with token handshake.
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
fi

# --- Fallback path: direct GHCR registry manifest check ---
# Extract tag and ensure we hit the correct registry endpoint
image_tag=$(printf '%s' "$CONTAINER_IMAGE" | sed 's/^.*://')
repo_path="openwrt/sdk"
registry_endpoint="https://ghcr.io/v2/${repo_path}/manifests/${image_tag}"

# Utility: perform a HEAD request and capture status + WWW-Authenticate header
try_head() {
    token="$1"
    hdr_file=$(mktemp)
    # Use -sS to stay quiet but preserve non-200 codes; -o /dev/null to avoid body
    # -D to capture headers for parsing
    if [ -n "$token" ]; then
        code=$(curl -sS -o /dev/null -D "$hdr_file" -w "%{http_code}" \
            -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json" \
            -H "Authorization: Bearer $token" \
            "$registry_endpoint" 2>/dev/null || printf '000')
    else
        code=$(curl -sS -o /dev/null -D "$hdr_file" -w "%{http_code}" \
            -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json" \
            "$registry_endpoint" 2>/dev/null || printf '000')
    fi
    www_auth=$(grep -i '^WWW-Authenticate:' "$hdr_file" | head -n1 || true)
    rm -f "$hdr_file"
    HTTP_CODE="$code"
    WWW_AUTH="$www_auth"
}

parse_www_auth() {
    # Parse WWW-Authenticate: Bearer realm="...",service="...",scope="..."
    line="$1"
    realm=$(printf '%s' "$line" | sed -n 's/.*realm="\([^"]*\)".*/\1/p' | head -n1)
    service=$(printf '%s' "$line" | sed -n 's/.*service="\([^"]*\)".*/\1/p' | head -n1)
    scope=$(printf '%s' "$line" | sed -n 's/.*scope="\([^"]*\)".*/\1/p' | head -n1)
    # Provide sane defaults if scope is missing
    if [ -z "$scope" ]; then
        scope="repository:${repo_path}:pull"
    fi
}

fetch_token() {
    realm_url="$1"
    svc="$2"
    scp="$3"
    # Construct token URL; components are safe as-is for GHCR
    token_json=$(curl -sS "${realm_url}?service=${svc}&scope=${scp}" 2>/dev/null || printf '')
    token=$(printf '%s' "$token_json" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p' | head -n1)
    printf '%s' "$token"
}

attempt=1
while [ $attempt -le $max_attempts ]; do
    printf "  Attempt %d/%d (registry HEAD): " "$attempt" "$max_attempts"
    try_head ""
    if [ "$HTTP_CODE" = "200" ]; then
        success "Registry reports image manifest available"
        success "SDK image validation passed"
        exit 0
    fi

    if [ "$HTTP_CODE" = "401" ] && [ -n "$WWW_AUTH" ]; then
        # Authenticate and retry with bearer token
        parse_www_auth "$WWW_AUTH"
        if [ -n "$realm" ] && [ -n "$service" ] && [ -n "$scope" ]; then
            token=$(fetch_token "$realm" "$service" "$scope")
            if [ -n "$token" ]; then
                try_head "$token"
                if [ "$HTTP_CODE" = "200" ]; then
                    success "Registry (auth) reports image manifest available"
                    success "SDK image validation passed"
                    exit 0
                fi
            fi
        fi
    fi

    if [ $attempt -lt $max_attempts ]; then
        printf "Retrying in 5 seconds...\n"
        sleep 5
    fi
    attempt=$((attempt + 1))
done

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
