#!/bin/sh
# shellcheck shell=ash
# Captive Portal Test Scenarios for OpenWrt Captive Monitor
# Usage: ./test_captive_scenarios.sh [SCENARIO]
#
# Scenarios:
#   setup         Setup test environment
#   working       Test with working internet
#   captive       Test with simulated captive portal
#   offline       Test with no internet
#   cleanup       Cleanup test environment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuration
TEST_DIR="/tmp/captive_test"
HTTPD_PORT="8080"
DNS_PORT="5353"

setup_test_environment() {
    log "Setting up test environment..."

    # Create test directories
    mkdir -p "${TEST_DIR}/httpd"
    mkdir -p "${TEST_DIR}/dnsmasq"

    # Create test HTTP server files
    cat > "${TEST_DIR}/httpd/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Test Captive Portal</title>
    <meta http-equiv="refresh" content="0; url=https://httpbin.org/html">
</head>
<body>
    <h1>Redirecting to captive portal...</h1>
    <p>If you see this, the captive portal detection should trigger.</p>
    <a href="https://httpbin.org/html">Click here to authenticate</a>
</body>
</html>
EOF

    # Create fake captive portal response
    cat > "${TEST_DIR}/httpd/generate_204.php" << 'EOF'
<?php
// Simulate captive portal detection endpoint
http_response_code(302);
header('Location: https://example.com/login?redirect=http://connectivitycheck.gstatic.com/generate_204');
?>
EOF

    success "Test environment setup completed"
}

start_captive_simulation() {
    log "Starting captive portal simulation..."

    # Start HTTP server for captive portal simulation
    if command -v python3 >/dev/null 2>&1; then
        cd "${TEST_DIR}/httpd"
        python3 -m http.server "${HTTPD_PORT}" > /dev/null 2>&1 &
        HTTPD_PID=$!
        log "HTTP server started on port ${HTTPD_PORT} (PID: ${HTTPD_PID})"
    elif command -v busybox >/dev/null 2>&1; then
        busybox httpd -p "${HTTPD_PORT}" -h "${TEST_DIR}/httpd" > /dev/null 2>&1 &
        HTTPD_PID=$!
        log "BusyBox HTTP server started on port ${HTTPD_PORT} (PID: ${HTTPD_PID})"
    else
        warning "No HTTP server available for testing"
        return 1
    fi

    # Setup iptables/nftables rules for DNS redirection
    if command -v nft >/dev/null 2>&1; then
        log "Setting up nftables rules..."

        # Create captive portal table
        nft add table inet captive_test
        nft add chain inet captive_test prerouting { type nat hook prerouting priority dstnat \; }

        # DNS interception (redirect DNS queries to our fake portal)
        nft add rule inet captive_test prerouting udp dport 53 redirect to :5353
        nft add rule inet captive_test prerouting tcp dport 53 redirect to :5353

        # HTTP interception (redirect port 80 to our test server)
        nft add rule inet captive_test prerouting tcp dport 80 redirect to :8080

        success "NFTables rules configured"
    elif command -v iptables >/dev/null 2>&1; then
        log "Setting up iptables rules..."

        # DNS interception
        iptables -t nat -A PREROUTING -p udp --dport 53 -j REDIRECT --to-port 5353
        iptables -t nat -A PREROUTING -p tcp --dport 53 -j REDIRECT --to-port 5353

        # HTTP interception
        iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

        success "IPTables rules configured"
    fi

    success "Captive portal simulation started"
}

test_working_internet() {
    log "Testing with working internet..."

    # Test connectivity
    if curl -s --connect-timeout 10 http://httpbin.org/ip >/dev/null; then
        success "Internet connectivity confirmed"

        # Run captive monitor in oneshot mode
        if [ -f /usr/sbin/openwrt_captive_monitor ]; then
            timeout 30s /usr/sbin/openwrt_captive_monitor --oneshot
            success "Oneshot test completed"
        elif [ -f /tmp/captive_test/extract/usr/sbin/openwrt_captive_monitor ]; then
            timeout 30s /tmp/captive_test/extract/usr/sbin/openwrt_captive_monitor --oneshot
            success "Oneshot test completed (from extracted package)"
        fi

        # Check that no firewall rules are active
        if command -v nft >/dev/null 2>&1; then
            RULE_COUNT=$(nft list ruleset 2>/dev/null | grep -c captive_monitor || true)
            if [ "$RULE_COUNT" -eq 0 ]; then
                success "No captive portal rules active (correct behavior)"
            else
                error "Found $RULE_COUNT unexpected captive portal rules"
            fi
        fi

    else
        warning "No internet connectivity detected"
    fi
}

test_captive_portal() {
    log "Testing captive portal detection..."

    # Test captive portal detection
    if command -v curl >/dev/null 2>&1; then
        # Test connectivity check endpoint
        RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://connectivitycheck.gstatic.com/generate_204" 2>/dev/null || echo "000")

        if [ "$RESPONSE" != "204" ]; then
            success "Captive portal detected (HTTP ${RESPONSE})"

            # Start the captive monitor service
            if command -v systemctl >/dev/null 2>&1; then
                systemctl start openwrt-captive-monitor
            elif [ -f /etc/init.d/captive-monitor ]; then
                /etc/init.d/captive-monitor start
            fi

            # Wait a bit and check if firewall rules are created
            sleep 5

            if command -v nft >/dev/null 2>&1; then
                RULE_COUNT=$(nft list ruleset 2>/dev/null | grep -c captive_monitor || true)
                if [ "$RULE_COUNT" -gt 0 ]; then
                    success "Firewall rules created: ${RULE_COUNT} rules"
                else
                    warning "No firewall rules created"
                fi
            fi

            # Check if HTTP redirect server is running
            if netstat -tlnp 2>/dev/null | grep -q ":${HTTPD_PORT}"; then
                success "HTTP redirect server is running"
            fi

        else
            warning "No captive portal detected (got HTTP 204)"
        fi
    fi
}

test_offline_mode() {
    log "Testing offline mode..."

    # Block internet access (simulate network issues)
    if command -v iptables >/dev/null 2>&1; then
        # Block all outbound traffic except localhost
        iptables -I OUTPUT -o eth0 -j DROP 2>/dev/null || true
        iptables -I OUTPUT -o wlan0 -j DROP 2>/dev/null || true

        success "Internet access blocked"

        # Start captive monitor and see how it behaves
        timeout 60s /usr/sbin/openwrt_captive_monitor --monitor &
        MONITOR_PID=$!

        # Wait and check behavior
        sleep 10

        # Restore internet
        iptables -D OUTPUT -o eth0 -j DROP 2>/dev/null || true
        iptables -D OUTPUT -o wlan0 -j DROP 2>/dev/null || true

        # Kill monitor
        kill $MONITOR_PID 2>/dev/null || true

        success "Offline test completed"

    else
        warning "Cannot simulate offline mode without iptables"
    fi
}

cleanup_test_environment() {
    log "Cleaning up test environment..."

    # Kill HTTP server
    if [ -n "${HTTPD_PID:-}" ]; then
        kill $HTTPD_PID 2>/dev/null || true
        log "HTTP server stopped"
    fi

    # Remove firewall rules
    if command -v nft >/dev/null 2>&1; then
        nft delete table inet captive_test 2>/dev/null || true
        nft delete table inet captive_monitor 2>/dev/null || true
    fi

    if command -v iptables >/dev/null 2>&1; then
        iptables -t nat -F 2>/dev/null || true
        iptables -F 2>/dev/null || true
    fi

    # Remove test directories
    rm -rf "${TEST_DIR}"

    # Stop captive monitor service
    if command -v systemctl >/dev/null 2>&1; then
        systemctl stop openwrt-captive-monitor 2>/dev/null || true
    elif [ -f /etc/init.d/captive-monitor ]; then
        /etc/init.d/captive-monitor stop 2>/dev/null || true
    fi

    success "Test environment cleanup completed"
}

# Main execution
SCENARIO="${1:-setup}"

case "$SCENARIO" in
    "setup")
        setup_test_environment
        ;;
    "working")
        test_working_internet
        ;;
    "captive")
        start_captive_simulation
        test_captive_portal
        ;;
    "offline")
        test_offline_mode
        ;;
    "cleanup")
        cleanup_test_environment
        ;;
    *)
        echo "Usage: $0 [SCENARIO]"
        echo ""
        echo "Scenarios:"
        echo "  setup     Setup test environment"
        echo "  working   Test with working internet"
        echo "  captive   Test with simulated captive portal"
        echo "  offline   Test with no internet"
        echo "  cleanup   Cleanup test environment"
        exit 1
        ;;
esac

success "Test scenario '$SCENARIO' completed"
