#!/bin/bash
# Скрипт для сборки и тестирования проблемы с procd
set -euo pipefail

ROUTER_IP="${1:-192.168.35.127}"

echo "=== Building and testing procd issue ==="
echo "Router: $ROUTER_IP"
echo

# Шаг 1: Сборка пакета
echo "=== Step 1: Building package ==="
bash scripts/build_ipk_simple.sh --arch all
echo

# Шаг 2: Копирование на роутер
echo "=== Step 2: Copying package to router ==="
PACKAGE_FILE=$(find dist -name "openwrt-captive-monitor_*.ipk" | head -1)
if [ -z "$PACKAGE_FILE" ]; then
    echo "ERROR: Package file not found"
    exit 1
fi
echo "Package: $PACKAGE_FILE"
scp "$PACKAGE_FILE" root@"$ROUTER_IP":/tmp/
echo

# Шаг 3: Остановка старого сервиса
echo "=== Step 3: Stopping old service ==="
ssh root@"$ROUTER_IP" "/etc/init.d/captive-monitor stop" || true
ssh root@"$ROUTER_IP" "killall openwrt_captive_monitor" || true
sleep 2
echo

# Шаг 4: Удаление старой версии
echo "=== Step 4: Removing old version ==="
ssh root@"$ROUTER_IP" "opkg remove openwrt-captive-monitor" || true
echo

# Шаг 5: Установка новой версии
echo "=== Step 5: Installing new version ==="
PACKAGE_NAME=$(basename "$PACKAGE_FILE")
# shellcheck disable=SC2029 # Variable intentionally expands on client side
ssh root@"$ROUTER_IP" "opkg install /tmp/$PACKAGE_NAME"
echo

# Шаг 6: Проверка установки
echo "=== Step 6: Verifying installation ==="
ssh root@"$ROUTER_IP" "opkg list-installed | grep captive"
ssh root@"$ROUTER_IP" "ls -la /usr/sbin/openwrt_captive_monitor"
ssh root@"$ROUTER_IP" "ls -la /etc/init.d/captive-monitor"
ssh root@"$ROUTER_IP" "ls -la /etc/init.d/captive-monitor-minimal" || echo "Minimal script not installed"
echo

# Шаг 7: Настройка конфигурации
echo "=== Step 7: Configuring service ==="
ssh root@"$ROUTER_IP" "uci set captive-monitor.config.enabled='1'"
ssh root@"$ROUTER_IP" "uci set captive-monitor.config.monitor_interval='60'"
ssh root@"$ROUTER_IP" "uci commit captive-monitor"
ssh root@"$ROUTER_IP" "uci show captive-monitor"
echo

# Шаг 8: Запуск тестов
echo "=== Step 8: Running tests ==="
bash scripts/test-procd-issue.sh "$ROUTER_IP"
echo

echo "=== Build and test completed ==="
echo "Check the logs above for debug information"
