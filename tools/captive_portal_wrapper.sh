#!/bin/bash
# Wrapper для captive_portal_selenium.py
# Гарантирует очистку только своих Chrome процессов после выполнения

set -euo pipefail

SCRIPT="/usr/local/bin/captive_portal_selenium.py"
TIMEOUT=90  # Максимальное время выполнения (секунды)
PYTHON_PID=""

# Функция очистки - убивает только дочерние процессы
cleanup() {
    if [ -n "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
        # Получаем список всех дочерних процессов Python скрипта
        local children=$(pgrep -P "$PYTHON_PID" 2>/dev/null || true)
        
        if [ -n "$children" ]; then
            # Убиваем дочерние процессы (chromedriver, chrome)
            for child_pid in $children; do
                # Рекурсивно убиваем всех потомков
                pkill -P "$child_pid" 2>/dev/null || true
                kill -9 "$child_pid" 2>/dev/null || true
            done
        fi
        
        # Убиваем сам Python процесс
        kill -9 "$PYTHON_PID" 2>/dev/null || true
    fi
    
    # Очищаем временные директории Chrome только если они не используются
    # (проверяем что нет других процессов chrome)
    if ! pgrep -u "$(whoami)" -f "google-chrome.*headless" >/dev/null 2>&1; then
        rm -rf /tmp/org.chromium.Chromium.* 2>/dev/null || true
        rm -rf /tmp/.org.chromium.Chromium.* 2>/dev/null || true
    fi
}

# Устанавливаем trap для очистки при любом выходе
trap cleanup EXIT INT TERM

# Запускаем скрипт в фоне и сохраняем PID
python3 "$SCRIPT" &
PYTHON_PID=$!

# Ждём завершения с таймаутом (проверяем каждую секунду)
elapsed=0
while kill -0 "$PYTHON_PID" 2>/dev/null; do
    if [ $elapsed -ge $TIMEOUT ]; then
        echo "⚠️  Скрипт превысил таймаут ${TIMEOUT}s" >&2
        cleanup
        exit 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
done

# Получаем exit code Python скрипта
wait "$PYTHON_PID" 2>/dev/null || true

exit 0
