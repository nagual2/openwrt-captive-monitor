#!/bin/bash
# Тестовый скрипт для проверки daemon

set -e

DAEMON_SCRIPT="tools/captive_portal_selenium2.py"
PID_FILE="/tmp/captive_portal_daemon.pid"
LOG_FILE="/tmp/captive_portal_daemon.log"

echo "=== Тест Captive Portal Daemon ==="
echo

# Функция для проверки запущен ли daemon
check_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Daemon запущен (PID: $PID)"
            return 0
        else
            echo "❌ PID файл существует, но процесс не запущен"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "❌ Daemon не запущен"
        return 1
    fi
}

# Функция для остановки daemon
stop_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "Остановка daemon (PID: $PID)..."
        kill -TERM "$PID" 2>/dev/null || true
        sleep 2
        
        # Проверяем что процесс завершился
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Принудительная остановка..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Daemon остановлен"
    else
        echo "Daemon не запущен"
    fi
}

# Функция для просмотра логов
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Последние 20 строк лога ==="
        tail -n 20 "$LOG_FILE"
    else
        echo "Лог файл не найден"
    fi
}

# Обработка команд
case "${1:-}" in
    start)
        echo "Запуск daemon..."
        if check_daemon; then
            echo "Daemon уже запущен"
            exit 0
        fi
        
        # Очистка старого лога
        > "$LOG_FILE"
        
        # Запуск в фоне
        python3 "$DAEMON_SCRIPT" &
        sleep 2
        
        if check_daemon; then
            echo "✅ Daemon успешно запущен"
            echo "Лог: $LOG_FILE"
        else
            echo "❌ Не удалось запустить daemon"
            show_logs
            exit 1
        fi
        ;;
    
    stop)
        stop_daemon
        ;;
    
    restart)
        stop_daemon
        sleep 1
        $0 start
        ;;
    
    status)
        check_daemon
        ;;
    
    logs)
        show_logs
        ;;
    
    tail)
        echo "=== Мониторинг лога (Ctrl+C для выхода) ==="
        tail -f "$LOG_FILE"
        ;;
    
    test)
        echo "=== Тест daemon (30 секунд) ==="
        
        # Остановка если запущен
        stop_daemon
        
        # Очистка лога
        > "$LOG_FILE"
        
        # Запуск с DEBUG режимом
        echo "Запуск daemon в DEBUG режиме..."
        CAPTIVE_DAEMON_DEBUG=1 python3 "$DAEMON_SCRIPT" &
        DAEMON_PID=$!
        
        echo "Daemon PID: $DAEMON_PID"
        echo "Ожидание 30 секунд..."
        
        # Мониторинг в течение 30 секунд
        for i in {1..30}; do
            sleep 1
            if ! ps -p "$DAEMON_PID" > /dev/null 2>&1; then
                echo "❌ Daemon завершился преждевременно!"
                show_logs
                exit 1
            fi
            
            # Показываем прогресс каждые 5 секунд
            if [ $((i % 5)) -eq 0 ]; then
                echo "  $i секунд прошло..."
            fi
        done
        
        echo "✅ Daemon работает стабильно"
        
        # Остановка
        echo "Остановка daemon..."
        kill -TERM "$DAEMON_PID"
        sleep 2
        
        if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
            echo "Принудительная остановка..."
            kill -9 "$DAEMON_PID"
        fi
        
        echo
        show_logs
        ;;
    
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|tail|test}"
        echo
        echo "Команды:"
        echo "  start   - Запустить daemon"
        echo "  stop    - Остановить daemon"
        echo "  restart - Перезапустить daemon"
        echo "  status  - Проверить статус daemon"
        echo "  logs    - Показать последние 20 строк лога"
        echo "  tail    - Мониторинг лога в реальном времени"
        echo "  test    - Тест daemon (30 секунд)"
        exit 1
        ;;
esac
