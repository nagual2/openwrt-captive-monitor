#!/bin/bash
set -euo pipefail

# Скрипт для ручного удаления пакета с OpenWrt роутера

ROUTER_IP="192.168.35.127"

echo "=== Manual Cleanup of OpenWrt Captive Monitor ==="
echo "Router: $ROUTER_IP"
echo ""

echo "Step 1: Stopping service..."
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor stop 2>/dev/null || true"
echo "✅ Service stopped (or was not running)"

echo ""
echo "Step 2: Disabling autostart..."
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor disable 2>/dev/null || true"
echo "✅ Autostart disabled (or was not enabled)"

echo ""
echo "Step 3: Removing files..."
ssh root@$ROUTER_IP "
    rm -f /usr/sbin/openwrt_captive_monitor
    rm -f /etc/init.d/captive-monitor
    rm -f /etc/config/captive-monitor
    rm -rf /usr/lib/opkg/info/openwrt-captive-monitor.*
    rm -f /tmp/openwrt-captive-monitor*.ipk
"
echo "✅ Files removed"

echo ""
echo "Step 4: Verifying cleanup..."
ssh root@$ROUTER_IP "
    echo 'Checking for remaining files:'
    
    if [ -f /usr/sbin/openwrt_captive_monitor ]; then
        echo '❌ /usr/sbin/openwrt_captive_monitor still exists'
    else
        echo '✅ /usr/sbin/openwrt_captive_monitor removed'
    fi
    
    if [ -f /etc/init.d/captive-monitor ]; then
        echo '❌ /etc/init.d/captive-monitor still exists'
    else
        echo '✅ /etc/init.d/captive-monitor removed'
    fi
    
    if [ -f /etc/config/captive-monitor ]; then
        echo '❌ /etc/config/captive-monitor still exists'
    else
        echo '✅ /etc/config/captive-monitor removed'
    fi
    
    if ls /usr/lib/opkg/info/openwrt-captive-monitor.* 2>/dev/null; then
        echo '❌ opkg info files still exist'
    else
        echo '✅ opkg info files removed'
    fi
"

echo ""
echo "Step 5: Checking opkg database..."
if ssh root@$ROUTER_IP "opkg list-installed | grep -q captive-monitor"; then
  echo "⚠️  Package still in opkg database"
  echo ""
  echo "Try running: opkg remove openwrt-captive-monitor --force-remove"
else
  echo "✅ Package not in opkg database"
fi

echo ""
echo "=== Manual cleanup completed ==="
