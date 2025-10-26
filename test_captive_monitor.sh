#!/bin/sh
# shellcheck shell=ash
# OpenWrt Captive Monitor Tests
# Usage: ./test_captive_monitor.sh

set -euo pipefail

# Basic configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PACKAGE_NAME="openwrt-captive-monitor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Test 1: Check if all required files exist
test_files() {
    log "Testing required OpenWrt files..."

    for file in \
        "package/${PACKAGE_NAME}/Makefile" \
        "package/${PACKAGE_NAME}/files/usr/sbin/openwrt_captive_monitor" \
        "package/${PACKAGE_NAME}/files/etc/init.d/captive-monitor" \
        "package/${PACKAGE_NAME}/files/etc/config/captive-monitor" \
        "scripts/build_ipk.sh" \
        "openwrt_captive_monitor.sh"
    do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            error "Required file missing: $file"
        fi
    done

    success "All required OpenWrt files present"
}

# Test 2: Check OpenWrt init scripts
test_openwrt_scripts() {
    log "Testing OpenWrt init scripts..."

    for script in \
        "package/${PACKAGE_NAME}/files/etc/init.d/captive-monitor" \
        "package/${PACKAGE_NAME}/files/usr/sbin/openwrt_captive_monitor"
    do
        if ! sh -n "$PROJECT_ROOT/$script" 2>/dev/null; then
            error "Syntax error in $script"
        fi
    done

    success "OpenWrt init scripts have valid syntax"
}

# Test 3: Check OpenWrt Makefile
test_openwrt_makefile() {
    log "Testing OpenWrt Makefile..."

    makefile="$PROJECT_ROOT/package/${PACKAGE_NAME}/Makefile"
    if [ ! -f "$makefile" ]; then
        error "OpenWrt Makefile not found: $makefile"
    fi

    # Check for required OpenWrt variables
    if ! grep -q "^PKG_NAME:=" "$makefile"; then
        error "PKG_NAME not defined in OpenWrt Makefile"
    fi

    if ! grep -q "^PKG_VERSION:=" "$makefile"; then
        error "PKG_VERSION not defined in OpenWrt Makefile"
    fi

    success "OpenWrt Makefile is valid"
}

# Test 4: Check UCI configuration
test_uci_config() {
    log "Testing UCI configuration..."

    config_file="$PROJECT_ROOT/package/${PACKAGE_NAME}/files/etc/config/captive-monitor"
    if [ ! -f "$config_file" ]; then
        error "UCI config file missing: $config_file"
    fi

    success "UCI configuration file present"
}

# Main test execution
main() {
    echo -e "${BLUE}🧪 OpenWrt Captive Monitor Tests${NC}"
    echo "================================"

    test_files
    test_openwrt_scripts
    test_openwrt_makefile
    test_uci_config

    echo ""
    success "All OpenWrt tests passed! ✅"
}

# Run tests
main "$@"
