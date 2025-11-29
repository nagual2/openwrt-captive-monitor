#!/bin/bash
# Скрипт для тестирования проблемы с procd на OpenWrt
set -euo pipefail

ROUTER_IP="${1:-192.168.35.127}"

echo "=== Testing procd issue on OpenWrt ==="
echo "Router: $ROUTER_IP"
echo

# Функция для выполнения команды на роутере
run_on_router() {
  # shellcheck disable=SC2029 # Intentionally expand on client side
  ssh root@"$ROUTER_IP" "$@"
}

# Функция для проверки логов
check_logs() {
  echo "=== Checking logs ==="
  run_on_router "logread | grep -E 'captive-monitor|procd' | tail -20"
}

# Функция для проверки процессов
check_processes() {
  echo "=== Checking processes ==="
  run_on_router "ps | grep -E 'openwrt_captive|captive-monitor' || echo 'No processes found'"
}

# Функция для проверки procd сервисов
check_procd_services() {
  echo "=== Checking procd services ==="
  run_on_router "ubus call service list | grep -A 10 captive || echo 'Service not found in procd'"
}

# Тест 1: Проверка текущего состояния
echo "=== Test 1: Current state ==="
check_processes
check_procd_services
echo

# Тест 2: Остановка сервиса если запущен
echo "=== Test 2: Stopping service ==="
run_on_router "/etc/init.d/captive-monitor stop" || true
sleep 2
check_processes
echo

# Тест 3: Очистка логов
echo "=== Test 3: Clearing logs ==="
run_on_router "logread -c" || true
echo

# Тест 4: Запуск с debug логированием
echo "=== Test 4: Starting service with debug logging ==="
run_on_router "/etc/init.d/captive-monitor start"
sleep 3
check_logs
echo

# Тест 5: Проверка процессов после запуска
echo "=== Test 5: Checking processes after start ==="
check_processes
echo

# Тест 6: Проверка procd регистрации
echo "=== Test 6: Checking procd registration ==="
check_procd_services
echo

# Тест 7: Проверка статуса
echo "=== Test 7: Checking service status ==="
run_on_router "/etc/init.d/captive-monitor status" || echo "Status command failed"
echo

# Тест 8: Тест минимального init скрипта (если установлен)
if run_on_router "test -f /etc/init.d/captive-monitor-minimal"; then
  echo "=== Test 8: Testing minimal init script ==="
  run_on_router "/etc/init.d/captive-monitor-minimal stop" || true
  sleep 2
  run_on_router "logread -c" || true
  run_on_router "/etc/init.d/captive-monitor-minimal start"
  sleep 3
  echo "Minimal script logs:"
  run_on_router "logread | grep captive-monitor-minimal | tail -10"
  echo "Minimal script processes:"
  check_processes
  echo "Minimal script procd:"
  check_procd_services
  echo
fi

# Тест 9: Ручной запуск для сравнения
echo "=== Test 9: Manual start for comparison ==="
run_on_router "killall openwrt_captive_monitor" || true
sleep 2
run_on_router "/usr/sbin/openwrt_captive_monitor --monitor > /dev/null 2>&1 &"
sleep 3
echo "Manual start processes:"
check_processes
echo "Manual start logs:"
run_on_router "logread | grep captive-monitor | tail -10"
echo

# Тест 10: Проверка прав доступа
echo "=== Test 10: Checking file permissions ==="
run_on_router "ls -la /usr/sbin/openwrt_captive_monitor"
run_on_router "ls -la /etc/init.d/captive-monitor"
run_on_router "ls -la /etc/config/captive-monitor"
echo

# Тест 11: Проверка UCI конфигурации
echo "=== Test 11: Checking UCI configuration ==="
run_on_router "uci show captive-monitor"
echo

# Тест 12: Проверка зависимостей
echo "=== Test 12: Checking dependencies ==="
run_on_router "which curl || echo 'curl not found'"
run_on_router "which logger || echo 'logger not found'"
run_on_router "which procd || echo 'procd not found'"
echo

# Итоговый отчет
echo "=== Summary ==="
echo "1. Check debug logs above for procd_* function calls"
echo "2. Compare manual start vs procd start behavior"
echo "3. Check if minimal init script works differently"
echo "4. Look for any error messages in logs"
echo

echo "=== Cleanup ==="
run_on_router "killall openwrt_captive_monitor" || true
echo "Test completed"
