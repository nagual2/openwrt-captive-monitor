#!/bin/sh

# Test 1: Check if the captive portal is detected
check_captive_portal() {
    echo "Testing captive portal detection..."
    wget -qO- --spider http://detectportal.firefox.com/success.txt
    if [ $? -eq 0 ]; then
        echo "✅ Internet is accessible"
        return 0
    else
        echo "🔒 Captive portal detected"
        return 1
    fi
}

# Test 2: Check DNS resolution
test_dns() {
    echo "\nTesting DNS resolution..."
    nslookup google.com
    if [ $? -eq 0 ]; then
        echo "✅ DNS resolution is working"
    else
        echo "❌ DNS resolution failed"
    fi
}

# Test 3: Test HTTP connectivity
test_http() {
    echo "\nTesting HTTP connectivity..."
    curl -I http://example.com
    if [ $? -eq 0 ]; then
        echo "✅ HTTP connectivity is working"
    else
        echo "❌ HTTP connectivity failed"
    fi
}

# Test 4: Check if the package is installed
test_package() {
    echo "\nChecking if openwrt-captive-monitor is installed..."
    if opkg list-installed | grep -q "openwrt-captive-monitor"; then
        echo "✅ openwrt-captive-monitor is installed"
        # Check if the service is running
        if [ -f "/etc/init.d/captive-monitor" ]; then
            echo "\nCaptive Monitor service status:"
            /etc/init.d/captive-monitor status || true
        fi
    else
        echo "❌ openwrt-captive-monitor is not installed"
    fi
}

# Run all tests
echo "=== Starting Captive Portal Tests ==="
check_captive_portal
test_dns
test_http
test_package
echo "\n=== Test completed ==="
