#!/bin/sh
# shellcheck shell=ash
# Simple OpenWrt Captive Monitor Tests
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
    log "Testing required files..."

    # POSIX-compatible way to list files
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

    success "All required files present"
}

# Test 2: Check shell script syntax
test_shell_syntax() {
    log "Testing shell script syntax..."

    # POSIX-compatible way to list scripts
    for script in \
        "openwrt_captive_monitor.sh" \
        "scripts/build_ipk.sh" \
        "package/${PACKAGE_NAME}/files/usr/sbin/openwrt_captive_monitor" \
        "package/${PACKAGE_NAME}/files/etc/init.d/captive-monitor"
    do
        if ! sh -n "$PROJECT_ROOT/$script" 2>/dev/null; then
            error "Syntax error in $script"
        fi
    done

    success "All shell scripts have valid syntax"
}

# Test 3: Check Makefile syntax
test_makefile() {
    log "Testing Makefile..."

    makefile="$PROJECT_ROOT/package/${PACKAGE_NAME}/Makefile"
    if [ ! -f "$makefile" ]; then
        error "Makefile not found: $makefile"
    fi

    # Basic check for required variables
    if ! grep -q "^PKG_NAME:=" "$makefile"; then
        error "PKG_NAME not defined in Makefile"
    fi

    if ! grep -q "^PKG_VERSION:=" "$makefile"; then
        error "PKG_VERSION not defined in Makefile"
    fi

    success "Makefile looks valid"
}

# Test 4: Try to build package if possible
test_build() {
    log "Testing package build..."

    build_script="$PROJECT_ROOT/scripts/build_ipk.sh"
    if [ -x "$build_script" ]; then
        if "$build_script" --help >/dev/null 2>&1; then
            success "Build script is functional"
        else
            warning "Build script may have issues"
        fi
    else
        warning "Build script not executable or missing"
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}🧪 OpenWrt Captive Monitor - Simple Tests${NC}"
    echo "============================================="

    test_files
    test_shell_syntax
    test_makefile
    test_build

    echo ""
    success "All tests passed! ✅"
}

# Run tests
main "$@"
