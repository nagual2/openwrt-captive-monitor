#!/bin/bash

# Configuration
REMOTE="root@192.168.35.170"
PACKAGE_NAME="openwrt-captive-monitor_0.1.2-1_all.ipk"
LOCAL_PACKAGE_DIR="/mnt/c/git/openwrt-captive-monitor/dist/opkg/all/"
REMOTE_TEMP_DIR="/tmp/captive_test"

# Enable debug output
set -x

# Функция для выполнения команд на удаленном устройстве
remote_exec() {
  ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$REMOTE" "$1"
}

# Функция для копирования файлов на удаленное устройство
remote_copy() {
  local src="$1"
  local dst="$2"
  scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$src" "$REMOTE:$dst"
}

echo "[1/7] Подготовка удаленного устройства..."
remote_exec "uname -a"
remote_exec "which opkg || echo 'opkg not found'"
remote_exec "mkdir -p $REMOTE_TEMP_DIR"

# Копируем пакет на устройство
echo "[2/5] Копируем пакет на устройство..."
remote_copy "${LOCAL_PACKAGE_DIR}${PACKAGE_NAME}" "${REMOTE_TEMP_DIR}/"

# Устанавливаем пакет
echo "[3/5] Устанавливаем пакет..."
remote_exec "opkg install --force-overwrite --force-reinstall ${REMOTE_TEMP_DIR}/${PACKAGE_NAME}"

# Проверяем установку пакета
echo "[4/7] Проверяем установку пакета..."
remote_exec "opkg list-installed | grep captive-monitor"
remote_exec "ls -la /usr/bin/captive-monitor || echo 'captive-monitor not found in /usr/bin/'"
remote_exec "find / -name 'captive-monitor' 2>/dev/null || echo 'captive-monitor not found in system'"

# Проверяем PATH
remote_exec 'echo $PATH' # shellcheck disable=SC2016

# Запускаем базовые тесты
echo "[5/7] Запускаем тесты..."
remote_exec "which captive-monitor || echo 'captive-monitor not in PATH'"
remote_exec "captive-monitor --help || echo 'Failed to run captive-monitor --help'"
remote_exec "captive-monitor --version || echo 'Failed to run captive-monitor --version'"

echo "[7/7] Очистка..."
remote_exec "rm -rf $REMOTE_TEMP_DIR"

echo "\nТестирование завершено. Проверьте вывод на наличие ошибок."
