#!/usr/bin/env bash
# Validate Docker image size
# This script checks if a Docker image size is within acceptable limits

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default maximum size in bytes (2GB)
MAX_SIZE_BYTES=${MAX_SIZE_BYTES:-2147483648}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

# shellcheck disable=SC2317
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

usage() {
    cat << EOF
Usage: $0 <image_name> [max_size_mb]

Validate Docker image size

ARGUMENTS:
    image_name      Docker image name (e.g., ghcr.io/user/image:tag)
    max_size_mb     Maximum allowed size in MB (default: 2048)

EXAMPLES:
    # Check if image is under 2GB
    $0 ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest

    # Check if image is under 1.5GB
    $0 ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest 1536

ENVIRONMENT VARIABLES:
    MAX_SIZE_BYTES  Maximum size in bytes (overrides max_size_mb argument)

EXIT CODES:
    0   Image size is within limits
    1   Image size exceeds limits or validation failed

EOF
    exit 1
}

# Convert MB to bytes
mb_to_bytes() {
    local mb=$1
    echo $((mb * 1024 * 1024))
}

# Convert bytes to human-readable format
bytes_to_human() {
    local bytes=$1
    
    if [[ $bytes -lt 1024 ]]; then
        echo "${bytes}B"
    elif [[ $bytes -lt $((1024 * 1024)) ]]; then
        echo "$((bytes / 1024))KB"
    elif [[ $bytes -lt $((1024 * 1024 * 1024)) ]]; then
        echo "$((bytes / 1024 / 1024))MB"
    else
        echo "$((bytes / 1024 / 1024 / 1024))GB"
    fi
}

# Main validation function
validate_image_size() {
    local image_name="$1"
    local max_size_mb="${2:-2048}"
    
    # Convert max size to bytes if not already set via environment
    if [[ -z "${MAX_SIZE_BYTES:-}" ]]; then
        MAX_SIZE_BYTES=$(mb_to_bytes "$max_size_mb")
    fi
    
    log_info "Validating image: $image_name"
    log_info "Maximum allowed size: $(bytes_to_human "$MAX_SIZE_BYTES")"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        return 1
    fi
    
    # Check if image exists locally, if not try to pull
    if ! docker image inspect "$image_name" &> /dev/null; then
        log_info "Image not found locally, attempting to pull..."
        if ! docker pull "$image_name"; then
            log_error "Failed to pull image: $image_name"
            return 1
        fi
    fi
    
    # Get image size
    local image_size
    image_size=$(docker image inspect "$image_name" --format='{{.Size}}' 2>/dev/null)
    
    if [[ -z "$image_size" ]]; then
        log_error "Failed to get image size for: $image_name"
        return 1
    fi
    
    log_info "Image size: $(bytes_to_human "$image_size")"
    
    # Compare sizes
    if [[ $image_size -gt $MAX_SIZE_BYTES ]]; then
        local excess=$((image_size - MAX_SIZE_BYTES))
        log_error "Image size exceeds limit!"
        log_error "  Current: $(bytes_to_human "$image_size")"
        log_error "  Maximum: $(bytes_to_human "$MAX_SIZE_BYTES")"
        log_error "  Excess: $(bytes_to_human "$excess")"
        return 1
    fi
    
    local remaining=$((MAX_SIZE_BYTES - image_size))
    local percentage=$((image_size * 100 / MAX_SIZE_BYTES))
    
    log_info "✓ Image size is within limits"
    log_info "  Used: $(bytes_to_human "$image_size") (${percentage}%)"
    log_info "  Remaining: $(bytes_to_human "$remaining")"
    
    return 0
}

# Parse arguments
if [[ $# -lt 1 ]]; then
    log_error "Missing required argument: image_name"
    usage
fi

IMAGE_NAME="$1"
MAX_SIZE_MB="${2:-2048}"

# Run validation
if validate_image_size "$IMAGE_NAME" "$MAX_SIZE_MB"; then
    exit 0
else
    exit 1
fi
