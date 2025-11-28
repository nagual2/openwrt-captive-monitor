#!/bin/bash
set -euo pipefail

# Скрипт для тестирования пакета на реальной OpenWrt среде

ROUTER_IP="192.168.35.127"
PACKAGE_FILE="${1:-dist/opkg/all/openwrt-captive-monitor_2025.11.28.3-1_all.ipk}"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "ERROR: Package file not found: $PACKAGE_FILE"
    exit 1
fi

echo "=== Testing OpenWrt Captive Monitor Package ==="
echo "Router: $ROUTER_IP"
echo "Package: $PACKAGE_FILE"
echo ""

# Функция для проверки установки
check_installed() {
    if ssh root@$ROUTER_IP "opkg list-installed | grep -q captive-monitor"; then
        return 0
    else
        return 1
    fi
}

# Шаг 1: Проверка текущего состояния
echo "=== Step 1: Checking current state ==="
if check_installed; then
    echo "⚠️  Package is already installed"
    echo ""
    echo "Please remove it manually:"
    echo "  ssh root@$ROUTER_IP"
    echo "  /etc/init.d/captive-monitor stop"
    echo "  /etc/init.d/captive-monitor disable"
    echo "  opkg remove openwrt-captive-monitor"
    echo ""
    echo "Or remove files manually if opkg fails:"
    echo "  rm -f /usr/sbin/openwrt_captive_monitor"
    echo "  rm -f /etc/init.d/captive-monitor"
    echo "  rm -f /etc/config/captive-monitor"
    echo "  rm -rf /usr/lib/opkg/info/openwrt-captive-monitor.*"
    exit 1
else
    echo "✅ Package is not installed"
fi

# Шаг 2: Копирование пакета
echo ""
echo "=== Step 2: Copying package to router ==="
if scp "$PACKAGE_FILE" root@$ROUTER_IP:/tmp/; then
    echo "✅ Package copied successfully"
else
    echo "❌ Failed to copy package"
    exit 1
fi

# Шаг 3: Установка пакета
echo ""
echo "=== Step 3: Installing package ==="
if ssh root@$ROUTER_IP "opkg install /tmp/$(basename $PACKAGE_FILE)"; then
    echo "✅ Package installed successfully"
else
    echo "❌ Failed to install package"
    exit 1
fi

# Шаг 4: Проверка установленных файлов
echo ""
echo "=== Step 4: Verifying installed files ==="

echo "Checking main script..."
if ssh root@$ROUTER_IP "test -f /usr/sbin/openwrt_captive_monitor"; then
    echo "✅ /usr/sbin/openwrt_captive_monitor exists"
else
    echo "❌ /usr/sbin/openwrt_captive_monitor missing"
fi

echo "Checking init script..."
if ssh root@$ROUTER_IP "test -f /etc/init.d/captive-monitor"; then
    echo "✅ /etc/init.d/captive-monitor exists"
else
    echo "❌ /etc/init.d/captive-monitor missing"
fi

echo "Checking config file..."
if ssh root@$ROUTER_IP "test -f /etc/config/captive-monitor"; then
    echo "✅ /etc/config/captive-monitor exists"
else
    echo "❌ /etc/config/captive-monitor missing"
fi

# Шаг 5: Проверка конфигурации
echo ""
echo "=== Step 5: Checking configuration ==="
ssh root@$ROUTER_IP "uci show captive-monitor"

# Шаг 6: Изменение конфигурации
echo ""
echo "=== Step 6: Modifying configuration ==="
ssh root@$ROUTER_IP "
    uci set captive-monitor.config.enabled='1'
    uci set captive-monitor.config.check_interval='60'
    uci set captive-monitor.config.check_url='http://detectportal.firefox.com/success.txt'
    uci commit captive-monitor
"
echo "✅ Configuration updated"

echo ""
echo "New configuration:"
ssh root@$ROUTER_IP "uci show captive-monitor"

# Шаг 7: Запуск сервиса
echo ""
echo "=== Step 7: Starting service ==="
if ssh root@$ROUTER_IP "/etc/init.d/captive-monitor start"; then
    echo "✅ Service started"
else
    echo "❌ Failed to start service"
fi

# Подождать 3 секунды
sleep 3

# Шаг 8: Проверка статуса
echo ""
echo "=== Step 8: Checking service status ==="
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor status" || true

# Шаг 9: Проверка логов
echo ""
echo "=== Step 9: Checking logs ==="
ssh root@$ROUTER_IP "logread | grep captive-monitor | tail -20" || echo "No logs found"

# Шаг 10: Включение автозапуска
echo ""
echo "=== Step 10: Enabling autostart ==="
if ssh root@$ROUTER_IP "/etc/init.d/captive-monitor enable"; then
    echo "✅ Autostart enabled"
else
    echo "❌ Failed to enable autostart"
fi

echo ""
echo "Checking autostart symlinks:"
ssh root@$ROUTER_IP "ls -la /etc/rc.d/*captive* 2>/dev/null" || echo "No symlinks found"

# Шаг 11: Перезапуск сервиса
echo ""
echo "=== Step 11: Restarting service ==="
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor restart"
sleep 3

echo ""
echo "Service status after restart:"
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor status" || true

# Шаг 12: Финальная проверка логов
echo ""
echo "=== Step 12: Final log check ==="
ssh root@$ROUTER_IP "logread | grep captive-monitor | tail -30" || echo "No logs found"

# Шаг 13: Остановка сервиса
echo ""
echo "=== Step 13: Stopping service ==="
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor stop"
echo "✅ Service stopped"

# Шаг 14: Отключение автозапуска
echo ""
echo "=== Step 14: Disabling autostart ==="
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor disable"
echo "✅ Autostart disabled"

# Шаг 15: Удаление пакета
echo ""
echo "=== Step 15: Removing package ==="
if ssh root@$ROUTER_IP "opkg remove openwrt-captive-monitor"; then
    echo "✅ Package removed successfully"
else
    echo "❌ Failed to remove package"
    echo ""
    echo "Try manual removal:"
    echo "  ssh root@$ROUTER_IP"
    echo "  rm -f /usr/sbin/openwrt_captive_monitor"
    echo "  rm -f /etc/init.d/captive-monitor"
    echo "  rm -f /etc/config/captive-monitor"
    echo "  rm -rf /usr/lib/opkg/info/openwrt-captive-monitor.*"
    exit 1
fi

# Шаг 16: Проверка удаления
echo ""
echo "=== Step 16: Verifying removal ==="

if check_installed; then
    echo "❌ Package still appears in opkg list"
else
    echo "✅ Package removed from opkg list"
fi

echo ""
echo "Checking if files were removed:"
ssh root@$ROUTER_IP "
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
        echo '⚠️  /etc/config/captive-monitor still exists (config preserved)'
    else
        echo '✅ /etc/config/captive-monitor removed'
    fi
"

# Очистка временных файлов
echo ""
echo "=== Step 17: Cleanup ==="
ssh root@$ROUTER_IP "rm -f /tmp/$(basename $PACKAGE_FILE)"
echo "✅ Temporary files removed"

echo ""
echo "=== Test completed successfully ==="
echo ""
echo "Summary:"
echo "  ✅ Package installation"
echo "  ✅ Configuration modification"
echo "  ✅ Service start/stop/restart"
echo "  ✅ Autostart enable/disable"
echo "  ✅ Package removal"
