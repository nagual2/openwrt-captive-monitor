#!/bin/sh
# shellcheck shell=ash
# OpenWrt Captive Portal Test Scenarios
# Usage: ./test_captive_scenarios.sh [SCENARIO]

set -euo pipefail

# Basic configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

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

# Test 1: Check main OpenWrt script
test_main_script() {
    log "Testing main OpenWrt script..."

    main_script="$PROJECT_ROOT/openwrt_captive_monitor.sh"
    if [ ! -f "$main_script" ]; then
        error "Main script not found: $main_script"
    fi

    if ! sh -n "$main_script" 2>/dev/null; then
        error "Main script has syntax errors"
    fi

    success "Main script is valid"
}

# Test 2: Check OpenWrt configuration files
test_config_files() {
    log "Testing OpenWrt configuration files..."

    # POSIX-compatible config list
    configs="package/openwrt-captive-monitor/files/etc/config/captive-monitor"

    for config in $configs; do
        if [ ! -f "$PROJECT_ROOT/$config" ]; then
            error "Config file missing: $config"
        fi
    done

    success "OpenWrt configuration files present"
}

# Test 3: Check OpenWrt init script
test_init_script() {
    log "Testing OpenWrt init script..."

    init_script="$PROJECT_ROOT/package/openwrt-captive-monitor/files/etc/init.d/captive-monitor"
    if [ ! -f "$init_script" ]; then
        error "Init script not found: $init_script"
    fi

    if ! sh -n "$init_script" 2>/dev/null; then
        error "Init script has syntax errors"
    fi

    success "OpenWrt init script is valid"
}

# Test 4: Check UCI defaults
test_uci_defaults() {
    log "Testing UCI defaults..."
    uci_defaults="$PROJECT_ROOT/package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor"
    if [ ! -f "$uci_defaults" ]; then
        error "UCI defaults not found: $uci_defaults"
    fi

    if ! sh -n "$uci_defaults" 2>/dev/null; then
        error "UCI defaults has syntax errors"
    fi

    success "UCI defaults is valid"
}

# Main test execution
main() {
    echo -e "${BLUE}🧪 OpenWrt Captive Portal Tests${NC}"
    echo "================================"

    case "${1:-all}" in
        "main" | "all")
            test_main_script
            ;;
        "config" | "all")
            test_config_files
            ;;
        "init" | "all")
            test_init_script
            ;;
        "uci" | "all")
            test_uci_defaults
            ;;
        *)
            echo "Usage: $0 [SCENARIO]"
            echo "Scenarios:"
            echo "  main    Test main OpenWrt script"
            echo "  config  Test OpenWrt configuration files"
            echo "  init    Test OpenWrt init script"
            echo "  uci     Test UCI defaults"
            echo "  all     Test all OpenWrt tests (default)"
            exit 1
            ;;
    esac

    echo ""
    success "All OpenWrt tests passed! ✅"
}

# Run tests
main "$@"
