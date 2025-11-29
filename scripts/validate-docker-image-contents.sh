#!/usr/bin/env bash
# Validate Docker image contents
# This script checks if a Docker image contains required components

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
  if [[ ${DEBUG:-0} == "1" ]]; then
    echo -e "${BLUE}[DEBUG]${NC} $*"
  fi
}

usage() {
  cat << EOF
Usage: $0 <image_name>

Validate Docker image contents for OpenWrt SDK

ARGUMENTS:
    image_name      Docker image name (e.g., ghcr.io/user/image:tag)

CHECKS:
    - SDK directory exists (/opt/openwrt-sdk)
    - SDK contains required files (Makefile, scripts/, etc.)
    - Build tools are available (make, gcc, etc.)
    - No temporary files in /tmp or /var/tmp
    - APT cache is cleaned

EXAMPLES:
    # Validate SDK image
    $0 ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest

    # With debug output
    DEBUG=1 $0 ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest

ENVIRONMENT VARIABLES:
    DEBUG=1         Enable debug output

EXIT CODES:
    0   All checks passed
    1   One or more checks failed

EOF
  exit 1
}

# Check if SDK directory exists
check_sdk_directory() {
  local image_name="$1"

  log_info "Checking SDK directory..."

  if docker run --rm "$image_name" test -d /opt/openwrt-sdk; then
    log_info "✓ SDK directory exists: /opt/openwrt-sdk"
    return 0
  else
    log_error "✗ SDK directory not found: /opt/openwrt-sdk"
    return 1
  fi
}

# Check SDK required files
check_sdk_files() {
  local image_name="$1"
  local failed=0

  log_info "Checking SDK required files..."

  local required_files=(
    "/opt/openwrt-sdk/Makefile"
    "/opt/openwrt-sdk/scripts/feeds"
    "/opt/openwrt-sdk/include/toplevel.mk"
  )

  for file in "${required_files[@]}"; do
    if docker run --rm "$image_name" test -f "$file"; then
      log_debug "✓ Found: $file"
    else
      log_error "✗ Missing: $file"
      failed=1
    fi
  done

  if [[ $failed -eq 0 ]]; then
    log_info "✓ All required SDK files present"
    return 0
  else
    log_error "✗ Some required SDK files are missing"
    return 1
  fi
}

# Check build tools
check_build_tools() {
  local image_name="$1"
  local failed=0

  log_info "Checking build tools..."

  local required_tools=(
    "make"
    "gcc"
    "g++"
    "git"
    "python3"
  )

  for tool in "${required_tools[@]}"; do
    if docker run --rm "$image_name" bash -c "command -v $tool" &> /dev/null; then
      log_debug "✓ Found: $tool"
    else
      log_error "✗ Missing: $tool"
      failed=1
    fi
  done

  if [[ $failed -eq 0 ]]; then
    log_info "✓ All required build tools present"
    return 0
  else
    log_error "✗ Some required build tools are missing"
    return 1
  fi
}

# Check for temporary files
check_temp_files() {
  local image_name="$1"

  log_info "Checking for temporary files..."

  local temp_count
  temp_count=$(docker run --rm "$image_name" sh -c 'find /tmp /var/tmp -type f 2>/dev/null | wc -l' || echo "0")

  if [[ $temp_count -eq 0 ]]; then
    log_info "✓ No temporary files found"
    return 0
  else
    log_warn "⚠ Found $temp_count temporary files"
    log_warn "  This may indicate incomplete cleanup in Dockerfile"
    # Don't fail, just warn
    return 0
  fi
}

# Check APT cache
check_apt_cache() {
  local image_name="$1"

  log_info "Checking APT cache..."

  local cache_size
  cache_size=$(docker run --rm "$image_name" sh -c 'du -sb /var/lib/apt/lists 2>/dev/null | cut -f1' || echo "0")

  # Consider cache cleaned if less than 1MB
  if [[ $cache_size -lt 1048576 ]]; then
    log_info "✓ APT cache is clean ($((cache_size / 1024))KB)"
    return 0
  else
    log_warn "⚠ APT cache not fully cleaned ($((cache_size / 1024 / 1024))MB)"
    log_warn "  Consider adding 'rm -rf /var/lib/apt/lists/*' to Dockerfile"
    # Don't fail, just warn
    return 0
  fi
}

# Check SDK version
check_sdk_version() {
  local image_name="$1"

  log_info "Checking SDK version..."

  local version_file="/opt/openwrt-sdk/include/version.mk"

  if docker run --rm "$image_name" test -f "$version_file"; then
    local version
    version=$(docker run --rm "$image_name" grep "VERSION_NUMBER" "$version_file" 2> /dev/null | head -1 || echo "unknown")
    log_info "✓ SDK version info: $version"
    return 0
  else
    log_warn "⚠ SDK version file not found"
    return 0
  fi
}

# Check user configuration
check_user() {
  local image_name="$1"

  log_info "Checking user configuration..."

  local current_user
  current_user=$(docker run --rm "$image_name" whoami 2> /dev/null || echo "unknown")

  log_info "  Current user: $current_user"

  # Check if builder user exists
  if docker run --rm "$image_name" id builder &> /dev/null; then
    log_info "✓ Builder user exists"
    return 0
  else
    log_warn "⚠ Builder user not found"
    return 0
  fi
}

# Main validation function
validate_image_contents() {
  local image_name="$1"
  local failed=0

  log_info "Validating image: $image_name"
  log_info "================================"

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

  echo ""

  # Run all checks
  check_sdk_directory "$image_name" || failed=1
  echo ""

  check_sdk_files "$image_name" || failed=1
  echo ""

  check_build_tools "$image_name" || failed=1
  echo ""

  check_temp_files "$image_name" || failed=1
  echo ""

  check_apt_cache "$image_name" || failed=1
  echo ""

  check_sdk_version "$image_name" || failed=1
  echo ""

  check_user "$image_name" || failed=1
  echo ""

  # Summary
  log_info "================================"
  if [[ $failed -eq 0 ]]; then
    log_info "✓ All validation checks passed"
    return 0
  else
    log_error "✗ Some validation checks failed"
    return 1
  fi
}

# Parse arguments
if [[ $# -lt 1 ]]; then
  log_error "Missing required argument: image_name"
  usage
fi

IMAGE_NAME="$1"

# Run validation
if validate_image_contents "$IMAGE_NAME"; then
  exit 0
else
  exit 1
fi
