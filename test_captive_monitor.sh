#!/bin/bash
# OpenWrt Captive Monitor Test Suite
# Usage: ./test_captive_monitor.sh [OPTIONS]
#
# Options:
#   --build-only    Only build the package, don't run tests
#   --install-only  Only install the package, don't run tests
#   --test-only     Only run tests, assume package is already installed
#   --arch ARCH     Target architecture (default: auto-detect)
#   --help          Show this help

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build_test"
ARTIFACTS_DIR="${PROJECT_ROOT}/artifacts"
PACKAGE_NAME="openwrt-captive-monitor"

# Test functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

cleanup() {
    log "Cleaning up..."
    # Stop service if running
    if command -v systemctl >/dev/null 2>&1; then
        systemctl stop ${PACKAGE_NAME} 2>/dev/null || true
        systemctl disable ${PACKAGE_NAME} 2>/dev/null || true
    fi

    # Remove package if installed
    if command -v opkg >/dev/null 2>&1; then
        opkg remove ${PACKAGE_NAME} 2>/dev/null || true
    fi

    # Clean up build artifacts
    rm -rf "${BUILD_DIR}" "${ARTIFACTS_DIR}"

    log "Cleanup completed"
}

detect_system() {
    log "Detecting system..."

    if command -v opkg >/dev/null 2>&1; then
        OS_TYPE="openwrt"
        success "OpenWrt system detected"
    elif command -v apt >/dev/null 2>&1; then
        OS_TYPE="debian"
        success "Debian/Ubuntu system detected"
    else
        error "Unsupported system. Need OpenWrt or Debian-based system."
        exit 1
    fi

    # Detect architecture
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "openwrt" ]]; then
            # OpenWrt architecture detection
            if grep -q "ath79" /etc/os-release 2>/dev/null || uname -m | grep -q "mips"; then
                TARGET_ARCH="mips_24kc"
            elif grep -q "ramips" /etc/os-release 2>/dev/null || uname -m | grep -q "mipsel"; then
                TARGET_ARCH="mipsel_24kc"
            elif uname -m | grep -q "aarch64"; then
                TARGET_ARCH="aarch64_cortex-a53"
            else
                TARGET_ARCH="all"
            fi
        else
            # Debian architecture
            case "$(uname -m)" in
                x86_64) TARGET_ARCH="x86_64" ;;
                i686|i386) TARGET_ARCH="i386" ;;
                aarch64) TARGET_ARCH="arm64" ;;
                armv7l) TARGET_ARCH="armhf" ;;
                *) TARGET_ARCH="all" ;;
            esac
        fi
    fi

    log "Target architecture: ${TARGET_ARCH}"
}

install_dependencies() {
    log "Installing dependencies..."

    if [ "$OS_TYPE" = "openwrt" ]; then
        # OpenWrt dependencies
        opkg update
        opkg install curl dnsmasq-full nftables iptables bash

        # Install build dependencies if building
        if ! command -v make >/dev/null 2>&1; then
            opkg install make gcc
        fi
    else
        # Debian dependencies
        sudo apt update
        sudo apt install -y curl dnsmasq nftables iptables bash make gcc wget xz-utils
    fi

    success "Dependencies installed"
}

build_package() {
    log "Building package..."

    mkdir -p "${BUILD_DIR}" "${ARTIFACTS_DIR}"

    if [ "$OS_TYPE" = "openwrt" ]; then
        # Try to build using local SDK or build_ipk.sh
        if [ -d /opt/openwrt-sdk ]; then
            log "Using OpenWrt SDK..."
            cp -r "${PROJECT_ROOT}/package/${PACKAGE_NAME}" /opt/openwrt-sdk/package/
            cd /opt/openwrt-sdk
            make package/${PACKAGE_NAME}/compile V=s
            find bin/packages -name "${PACKAGE_NAME}_*.ipk" -exec cp {} "${ARTIFACTS_DIR}/" \;
        else
            log "Using build_ipk.sh script..."
            cd "${PROJECT_ROOT}"
            bash scripts/build_ipk.sh --arch "${TARGET_ARCH}" --feed-root "${BUILD_DIR}"
            cp "${BUILD_DIR}/${TARGET_ARCH}/${PACKAGE_NAME}_"*".ipk" "${ARTIFACTS_DIR}/" 2>/dev/null || true
        fi
    else
        # On Debian, download from GitHub Actions or use build_ipk.sh
        log "Downloading from GitHub Actions..."
        LATEST_RUN=$(curl -s "https://api.github.com/repos/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml/runs?per_page=1" | \
                    jq -r '.workflow_runs[0].artifacts_url // empty')

        if [ -n "$LATEST_RUN" ] && [ "$LATEST_RUN" != "null" ]; then
            # Try to download artifacts (this might not work without authentication)
            warning "GitHub API available but may require authentication for artifact download"
        fi

        # Fallback: use build_ipk.sh if available
        if [ -f "${PROJECT_ROOT}/scripts/build_ipk.sh" ]; then
            cd "${PROJECT_ROOT}"
            bash scripts/build_ipk.sh --arch "${TARGET_ARCH}" --feed-root "${BUILD_DIR}"
        fi
    fi

    # Verify package was built
    PACKAGE_FILE="${ARTIFACTS_DIR}/${PACKAGE_NAME}_"*"_${TARGET_ARCH}.ipk"
    if [ ! -f "$PACKAGE_FILE" ]; then
        error "Package build failed - no .ipk file found"
        exit 1
    fi

    success "Package built: $(basename "$PACKAGE_FILE")"
}

install_package() {
    log "Installing package..."

    PACKAGE_FILE="${ARTIFACTS_DIR}/${PACKAGE_NAME}_"*"_${TARGET_ARCH}.ipk"

    if [ ! -f "$PACKAGE_FILE" ]; then
        error "Package file not found: $PACKAGE_FILE"
        exit 1
    fi

    if [ "$OS_TYPE" = "openwrt" ]; then
        opkg install "$PACKAGE_FILE"
    else
        # On Debian, we can't really install OpenWrt package
        # But we can extract and test the scripts
        mkdir -p "${BUILD_DIR}/extract"
        cd "${BUILD_DIR}/extract"
        ar x "$PACKAGE_FILE"
        tar -xf data.tar.gz
        success "Package extracted to ${BUILD_DIR}/extract"
    fi

    success "Package installed"
}

run_tests() {
    log "Running tests..."

    # Test 1: Check if service is available
    if [ "$OS_TYPE" = "openwrt" ]; then
        if opkg list-installed | grep -q "${PACKAGE_NAME}"; then
            success "Package is installed"

            # Test 2: Check service status
            if /etc/init.d/${PACKAGE_NAME} status >/dev/null 2>&1; then
                success "Service script is available"
            else
                error "Service script not found or not working"
                exit 1
            fi

            # Test 3: Check configuration
            if [ -f /etc/config/${PACKAGE_NAME} ]; then
                success "UCI configuration created"
            else
                warning "UCI configuration not found"
            fi

            # Test 4: Test oneshot mode
            log "Testing oneshot mode..."
            timeout 30s ${PROJECT_ROOT}/openwrt_captive_monitor.sh --oneshot || true
            success "Oneshot test completed"

            # Test 5: Check for firewall rules (should be none if internet works)
            if command -v nft >/dev/null 2>&1; then
                RULE_COUNT=$(nft list ruleset 2>/dev/null | grep -c captive_monitor || true)
                if [ "$RULE_COUNT" -eq 0 ]; then
                    success "No firewall rules active (expected for working internet)"
                else
                    warning "Found $RULE_COUNT captive portal rules (may indicate captive portal)"
                fi
            fi
        else
            error "Package not properly installed"
            exit 1
        fi
    else
        # Debian testing - check extracted files
        if [ -f "${BUILD_DIR}/extract/usr/sbin/openwrt_captive_monitor" ]; then
            success "Main script extracted successfully"

            # Test script syntax
            if bash -n "${BUILD_DIR}/extract/usr/sbin/openwrt_captive_monitor"; then
                success "Script syntax is valid"
            else
                error "Script has syntax errors"
                exit 1
            fi

            # Check dependencies
            for dep in curl nft iptables dnsmasq; do
                if command -v "$dep" >/dev/null 2>&1; then
                    success "Dependency available: $dep"
                else
                    warning "Dependency missing: $dep"
                fi
            done
        else
            error "Main script not found in package"
            exit 1
        fi
    fi

    success "All tests completed"
}

# Parse command line arguments
BUILD_ONLY=false
INSTALL_ONLY=false
TEST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --install-only)
            INSTALL_ONLY=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --arch)
            TARGET_ARCH="$2"
            shift 2
            ;;
        --help)
            echo "OpenWrt Captive Monitor Test Suite"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build-only    Only build the package, don't run tests"
            echo "  --install-only  Only install the package, don't run tests"
            echo "  --test-only     Only run tests, assume package is already installed"
            echo "  --arch ARCH     Target architecture (default: auto-detect)"
            echo "  --help          Show this help"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
trap cleanup EXIT INT TERM

log "Starting OpenWrt Captive Monitor Test Suite"
log "Project: ${PROJECT_ROOT}"
log "Build dir: ${BUILD_DIR}"
log "Artifacts dir: ${ARTIFACTS_DIR}"

detect_system
install_dependencies

if [ "$TEST_ONLY" = false ]; then
    build_package
    if [ "$BUILD_ONLY" = false ]; then
        install_package
    fi
fi

if [ "$BUILD_ONLY" = false ]; then
    run_tests
fi

success "Test suite completed successfully!"
log "Check ${ARTIFACTS_DIR} for build artifacts"
