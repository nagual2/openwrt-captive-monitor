#!/usr/bin/env bash
# Bash script to build and push all OpenWrt SDK Docker images
# This script builds all 8 architectures locally and pushes them to GHCR

set -euo pipefail

# Default values
OPENWRT_VERSION="${OPENWRT_VERSION:-23.05.5}"
REGISTRY="${REGISTRY:-ghcr.io/nagual2}"
IMAGE_NAME="openwrt-sdk"
SKIP_BUILD=false
PUSH_ONLY=false

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_header() {
    echo -e "${CYAN}$*${NC}"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build and push all OpenWrt SDK Docker images to GHCR

OPTIONS:
    -v, --version VERSION    OpenWrt version (default: ${OPENWRT_VERSION})
    -r, --registry REGISTRY  Container registry (default: ${REGISTRY})
    -s, --skip-build         Skip building, only push existing images
    -p, --push-only          Only push images, don't build
    -h, --help               Show this help message

EXAMPLES:
    # Build and push all images
    $0

    # Build with custom version
    $0 --version 23.05.4

    # Only push existing images
    $0 --push-only

PREREQUISITES:
    - Docker must be running
    - You must be logged in to GHCR: docker login ghcr.io
    - Git must be available for commit SHA

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v | --version)
            OPENWRT_VERSION="$2"
            shift 2
            ;;
        -r | --registry)
            REGISTRY="$2"
            shift 2
            ;;
        -s | --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -p | --push-only)
            PUSH_ONLY=true
            shift
            ;;
        -h | --help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Define all architectures
declare -a ARCHITECTURES=(
    "x86:64:x86-64"
    "ath79:generic:ath79-generic"
    "ramips:mt76x8:ramips-mt76x8"
    "mediatek:filogic:mediatek-filogic"
    "ipq40xx:generic:ipq40xx-generic"
    "ipq806x:generic:ipq806x-generic"
    "bcm27xx:bcm2711:bcm27xx-bcm2711"
    "rockchip:armv8:rockchip-armv8"
)

log_header "=== OpenWrt SDK Docker Images Build Script ==="
log_info "OpenWrt Version: ${OPENWRT_VERSION}"
log_info "Registry: ${REGISTRY}"
log_info "Total architectures: ${#ARCHITECTURES[@]}"
echo

# Check Docker
log_info "Checking Docker..."
if ! docker --version > /dev/null 2>&1; then
    log_error "Docker not found or not running"
    exit 1
fi
log_info "Docker found: $(docker --version)"

# Check GHCR login
log_info "Checking GHCR authentication..."
if ! docker login ghcr.io --password-stdin < /dev/null 2>&1 | grep -q "already logged in"; then
    log_warn "Not logged in to GHCR. Attempting to use existing credentials..."
fi

# Get commit SHA
if SHORT_SHA=$(git rev-parse --short=8 HEAD 2> /dev/null); then
    log_info "Commit SHA: ${SHORT_SHA}"
else
    SHORT_SHA="local"
    log_warn "Could not get git SHA, using 'local'"
fi

echo

SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0
declare -a FAILED_ARCHS=()

for arch_spec in "${ARCHITECTURES[@]}"; do
    IFS=':' read -r TARGET SUBTARGET SLUG <<< "$arch_spec"
    
    IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:${OPENWRT_VERSION}-${SLUG}-latest"
    IMAGE_TAG_SHA="${REGISTRY}/${IMAGE_NAME}:${OPENWRT_VERSION}-${SLUG}-${SHORT_SHA}"
    
    log_header "================================================"
    log_header "Processing: ${TARGET}/${SUBTARGET} (${SLUG})"
    log_header "================================================"
    
    if [[ $PUSH_ONLY == "false" ]] && [[ $SKIP_BUILD == "false" ]]; then
        log_info "Building image..."
        
        BUILD_START=$(date +%s)
        
        if docker build \
            --build-arg UBUNTU_VERSION=24.04 \
            --build-arg OPENWRT_VERSION="${OPENWRT_VERSION}" \
            --build-arg SDK_TARGET="${TARGET}" \
            --build-arg SDK_SUBTARGET="${SUBTARGET}" \
            --tag "${IMAGE_TAG}" \
            --tag "${IMAGE_TAG_SHA}" \
            --file docker/sdk/Dockerfile \
            .; then
            
            BUILD_END=$(date +%s)
            BUILD_DURATION=$((BUILD_END - BUILD_START))
            BUILD_MINUTES=$((BUILD_DURATION / 60))
            
            log_info "Build completed in ${BUILD_MINUTES} minutes"
            
            # Check image size
            IMAGE_SIZE=$(docker images "${IMAGE_TAG}" --format "{{.Size}}")
            log_info "Image size: ${IMAGE_SIZE}"
            
            # Validate image
            log_info "Validating image..."
            if docker run --rm "${IMAGE_TAG}" test -d /opt/openwrt-sdk; then
                log_info "Image validation passed"
            else
                log_warn "Image validation failed"
            fi
        else
            log_error "Build failed for ${SLUG}"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_ARCHS+=("${SLUG}")
            continue
        fi
    else
        log_info "Skipping build (using existing image)"
        
        # Check if image exists
        if ! docker images "${IMAGE_TAG}" --format "{{.Repository}}:{{.Tag}}" | grep -q "${IMAGE_TAG}"; then
            log_warn "Image ${IMAGE_TAG} not found locally"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            continue
        fi
    fi
    
    # Push image
    log_info "Pushing image to registry..."
    
    if docker push "${IMAGE_TAG}" && docker push "${IMAGE_TAG_SHA}"; then
        log_info "Successfully pushed ${SLUG}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        log_error "Push failed for ${SLUG}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_ARCHS+=("${SLUG}")
    fi
    
    echo
done

# Summary
log_header "================================================"
log_header "Build and Push Summary"
log_header "================================================"
log_info "Total architectures: ${#ARCHITECTURES[@]}"
log_info "Successful: ${SUCCESS_COUNT}"
log_error "Failed: ${FAILED_COUNT}"
log_warn "Skipped: ${SKIPPED_COUNT}"

if [[ ${FAILED_COUNT} -gt 0 ]]; then
    echo
    log_error "Failed architectures:"
    for arch in "${FAILED_ARCHS[@]}"; do
        log_error "  - ${arch}"
    done
    exit 1
fi

echo
log_info "All images processed successfully!"
exit 0
