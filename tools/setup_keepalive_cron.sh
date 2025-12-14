#!/bin/sh
"""
Скрипт для настройки cron задачи keep-alive на роутере OpenWrt.

Автор: OpenWrt Captive Monitor Project
Версия: 1.0.0
"""

set -e

KEEPALIVE_SCRIPT="/usr/sbin/captive_portal_keepalive.py"
CRON_ENTRY="*/10 * * * * /usr/bin/python3 $KEEPALIVE_SCRIPT --quiet"
CRON_FILE="/etc/crontabs/root"

# Функция для логирования
log_info() {
    echo "[INFO] $1"
    logger -t "captive-keepalive-setup" -p user.info "$1"
}

log_error() {
    echo "[ERROR] $1" >&2
    logger -t "captive-keepalive-setup" -p user.err "$1"
}

# Проверяем наличие Python3
if ! command -v python3 > /dev/null 2>&1; then
    log_error "Python3 не найден. Установите python3 через opkg install python3"
    exit 1
fi

# Проверяем наличие requests
if ! python3 -c "import requests" 2>/dev/null; then
    log_info "Модуль requests не найден, устанавливаем..."
    if command -v pip3 > /dev/null 2>&1; then
        pip3 install requests
    else
        log_error "pip3 не найден. Установите python3-pip через opkg install python3-pip"
        exit 1
    fi
fi

# Проверяем наличие скрипта keep-alive
if [ ! -f "$KEEPALIVE_SCRIPT" ]; then
    log_error "Скрипт $KEEPALIVE_SCRIPT не найден"
    exit 1
fi

# Делаем скрипт исполняемым
chmod +x "$KEEPALIVE_SCRIPT"

# Создаем cron файл если не существует
if [ ! -f "$CRON_FILE" ]; then
    touch "$CRON_FILE"
fi

# Проверяем, не добавлена ли уже задача
if grep -q "captive_portal_keepalive.py" "$CRON_FILE"; then
    log_info "Cron задача keep-alive уже существует"
else
    # Добавляем cron задачу (каждые 10 минут)
    echo "$CRON_ENTRY" >> "$CRON_FILE"
    log_info "Добавлена cron задача: $CRON_ENTRY"
fi

# Перезапускаем cron
if [ -x /etc/init.d/cron ]; then
    /etc/init.d/cron restart
    log_info "Cron сервис перезапущен"
else
    log_error "Cron сервис не найден"
    exit 1
fi

log_info "Keep-alive настроен успешно"
log_info "Задача будет выполняться каждые 10 минут"
log_info "Для просмотра логов используйте: logread | grep captive"

# Тестовый запуск
log_info "Выполняем тестовый запуск..."
if python3 "$KEEPALIVE_SCRIPT" --timeout 5; then
    log_info "✅ Тестовый запуск успешен"
else
    log_error "❌ Тестовый запуск не удался"
    exit 1
fi
