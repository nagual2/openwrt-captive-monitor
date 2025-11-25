#!/usr/bin/env bash
# Local build script for OpenWrt SDK Docker images
# This script helps developers build and test SDK images locally

set -euo pipefail

# Default values
OPENWRT_VERSION="${OPENWRT_VERSION:-23.05.5}"
UBUNTU_VERSION="${UBUNTU_VERSION:-24.04}"
REGISTRY="${REGISTRY:-ghcr.io/nagual2}"
IMAGE_NAME="${IMAGE_NAME:-openwrt-sdk}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build OpenWrt SDK Docker image locally

OPTIONS:
    -t, --target TARGET         SDK target (e.g., x86)
    -s, --subtarget SUBTARGET   SDK subtarget (e.g., 64)
    -v, --version VERSION       OpenWrt version (default: ${OPENWRT_VERSION})
    -u, --ubuntu VERSION        Ubuntu version (default: ${UBUNTU_VERSION})
    -r, --registry REGISTRY     Container registry (default: ${REGISTRY})
    -p, --push                  Push image to registry after build
    -h, --help                  Show this help message

EXAMPLES:
    # Build x86_64 image
    $0 --target x86 --subtarget 64

    # Build and push ath79 image
    $0 --target ath79 --subtarget generic --push

    # Build with custom OpenWrt version
    $0 --target x86 --subtarget 64 --version 23.05.4

EOF
    exit 0
}

# Parse arguments
PUSH=false
SDK_TARGET=""
SDK_SUBTARGET=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            SDK_TARGET="$2"
            shift 2
            ;;
        -s|--subtarget)
            SDK_SUBTARGET="$2"
            shift 2
            ;;
        -v|--version)
            OPENWRT_VERSION="$2"
            shift 2
            ;;
        -u|--ubuntu)
            UBUNTU_VERSION="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$SDK_TARGET" ]] || [[ -z "$SDK_SUBTARGET" ]]; then
    log_error "Target and subtarget are required"
    usage
fi

# Build image tag
SDK_SLUG="${SDK_TARGET}-${SDK_SUBTARGET}"
IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:${OPENWRT_VERSION}-${SDK_SLUG}-latest"
SHORT_SHA=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "local")
IMAGE_TAG_SHA="${REGISTRY}/${IMAGE_NAME}:${OPENWRT_VERSION}-${SDK_SLUG}-${SHORT_SHA}"

log_info "Building OpenWrt SDK Docker image"
log_info "  OpenWrt version: ${OPENWRT_VERSION}"
log_info "  Ubuntu version: ${UBUNTU_VERSION}"
log_info "  Target: ${SDK_TARGET}/${SDK_SUBTARGET}"
log_info "  Image tag: ${IMAGE_TAG}"
log_info "  Image tag (SHA): ${IMAGE_TAG_SHA}"

# Build image
log_info "Starting Docker build..."
docker build \
    --build-arg UBUNTU_VERSION="${UBUNTU_VERSION}" \
    --build-arg OPENWRT_VERSION="${OPENWRT_VERSION}" \
    --build-arg SDK_TARGET="${SDK_TARGET}" \
    --build-arg SDK_SUBTARGET="${SDK_SUBTARGET}" \
    --tag "${IMAGE_TAG}" \
    --tag "${IMAGE_TAG_SHA}" \
    --file docker/sdk/Dockerfile \
    .

log_info "Build completed successfully"

# Check image size
IMAGE_SIZE=$(docker images "${IMAGE_TAG}" --format "{{.Size}}")
log_info "Image size: ${IMAGE_SIZE}"

# Validate image size (should be < 2GB)
IMAGE_SIZE_BYTES=$(docker inspect "${IMAGE_TAG}" --format='{{.Size}}')
MAX_SIZE_BYTES=$((2 * 1024 * 1024 * 1024)) # 2GB

if [[ ${IMAGE_SIZE_BYTES} -gt ${MAX_SIZE_BYTES} ]]; then
    log_warn "Image size (${IMAGE_SIZE}) exceeds 2GB limit"
else
    log_info "Image size is within 2GB limit"
fi

# Test image
log_info "Testing image..."
if docker run --rm "${IMAGE_TAG}" test -d /opt/openwrt-sdk; then
    log_info "SDK directory found in image"
else
    log_error "SDK directory not found in image"
    exit 1
fi

# Push image if requested
if [[ "$PUSH" == "true" ]]; then
    log_info "Pushing image to registry..."
    docker push "${IMAGE_TAG}"
    docker push "${IMAGE_TAG_SHA}"
    log_info "Image pushed successfully"
fi

log_info "Done!"
