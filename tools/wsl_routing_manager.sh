#!/bin/bash
# WSL Routing Manager - управление маршрутизацией через dev сервер
# Использование: ./wsl_routing_manager.sh [enable|disable|status|reset]

set -euo pipefail

# Конфигурация
DEV_SERVER_IP="192.168.1.1"
DEV_SERVER_NAME="dev-openwrt"
PROD_SERVER_IP="192.168.35.1"
PROD_SERVER_NAME="prod-openwrt"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка прав sudo
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        error "Требуются права sudo для изменения маршрутизации"
        echo "Выполните: sudo -v"
        exit 1
    fi
}

# Получить текущий шлюз по умолчанию
get_default_gateway() {
    ip route show default | awk '/default via/ {print $3; exit}'
}

# Получить интерфейс по умолчанию
get_default_interface() {
    ip route show default | awk '/default via/ {print $5; exit}'
}

# Проверить доступность хоста
check_host_reachable() {
    local host=$1
    local timeout=${2:-3}

    if ping -c 1 -W "$timeout" "$host" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Показать текущий статус маршрутизации
show_status() {
    log "=== Текущий статус маршрутизации WSL ==="

    local default_gw
    default_gw=$(get_default_gateway)
    local default_iface
    default_iface=$(get_default_interface)

    echo "Шлюз по умолчанию: $default_gw (интерфейс: $default_iface)"

    # Проверить маршруты к OpenWrt серверам
    echo
    echo "Маршруты к OpenWrt серверам:"

    if ip route show | grep -q "$DEV_SERVER_IP"; then
        local dev_route
        dev_route=$(ip route show | grep "$DEV_SERVER_IP" | head -1)
        echo "  $DEV_SERVER_NAME ($DEV_SERVER_IP): $dev_route"
    else
        echo "  $DEV_SERVER_NAME ($DEV_SERVER_IP): через шлюз по умолчанию"
    fi

    if ip route show | grep -q "$PROD_SERVER_IP"; then
        local prod_route
        prod_route=$(ip route show | grep "$PROD_SERVER_IP" | head -1)
        echo "  $PROD_SERVER_NAME ($PROD_SERVER_IP): $prod_route"
    else
        echo "  $PROD_SERVER_NAME ($PROD_SERVER_IP): через шлюз по умолчанию"
    fi

    # Проверить доступность серверов
    echo
    echo "Доступность серверов:"

    if check_host_reachable "$DEV_SERVER_IP" 2; then
        success "  $DEV_SERVER_NAME ($DEV_SERVER_IP): доступен"
    else
        error "  $DEV_SERVER_NAME ($DEV_SERVER_IP): недоступен"
    fi

    if check_host_reachable "$PROD_SERVER_IP" 2; then
        success "  $PROD_SERVER_NAME ($PROD_SERVER_IP): доступен"
    else
        warning "  $PROD_SERVER_NAME ($PROD_SERVER_IP): недоступен"
    fi

    # Показать активные маршруты
    echo
    echo "Все маршруты:"
    ip route show | while read -r route; do
        echo "  $route"
    done
}

# Включить маршрутизацию через dev сервер
enable_dev_routing() {
    log "Включение маршрутизации через dev сервер..."

    check_sudo

    # Проверить доступность dev сервера
    if ! check_host_reachable "$DEV_SERVER_IP" 5; then
        error "Dev сервер $DEV_SERVER_IP недоступен!"
        echo "Проверьте:"
        echo "1. Подключение к сети dev сервера"
        echo "2. IP адрес в /etc/hosts"
        echo "3. Состояние dev сервера"
        exit 1
    fi

    # Сохранить текущий шлюз
    local original_gw
    original_gw=$(get_default_gateway)
    local original_iface
    original_iface=$(get_default_interface)

    echo "$original_gw $original_iface" > /tmp/wsl_original_gateway

    log "Сохранен оригинальный шлюз: $original_gw (интерфейс: $original_iface)"

    # Добавить маршрут через dev сервер для интернет трафика
    # Сначала добавим специфичные маршруты для сохранения доступа к WSL

    # Сохранить доступ к WSL сети
    local wsl_network
    wsl_network=$(ip route show | grep "$original_iface" | grep -v default | head -1 | awk '{print $1}')

    if [[ -n "$wsl_network" ]]; then
        log "Сохраняем маршрут к WSL сети: $wsl_network"
        # Этот маршрут уже существует, не нужно добавлять
    fi

    # Добавить маршрут для доступа к оригинальному шлюзу
    log "Добавляем маршрут к оригинальному шлюзу..."
    sudo ip route add "$original_gw/32" via "$original_gw" dev "$original_iface" 2>/dev/null || true

    # Изменить шлюз по умолчанию на dev сервер
    log "Изменяем шлюз по умолчанию на dev сервер..."
    sudo ip route del default 2>/dev/null || true
    sudo ip route add default via "$DEV_SERVER_IP" dev "$original_iface"

    # Проверить новую конфигурацию
    sleep 2

    if check_host_reachable "8.8.8.8" 3; then
        success "Маршрутизация через dev сервер включена успешно!"
        success "Интернет трафик теперь идет через $DEV_SERVER_NAME ($DEV_SERVER_IP)"
    else
        error "Не удалось установить соединение через dev сервер"
        warning "Восстанавливаем оригинальную маршрутизацию..."
        disable_dev_routing
        exit 1
    fi

    show_status
}

# Отключить маршрутизацию через dev сервер
disable_dev_routing() {
    log "Отключение маршрутизации через dev сервер..."

    check_sudo

    # Восстановить оригинальный шлюз
    if [[ -f /tmp/wsl_original_gateway ]]; then
        local original_gw original_iface
        read -r original_gw original_iface < /tmp/wsl_original_gateway

        log "Восстанавливаем оригинальный шлюз: $original_gw (интерфейс: $original_iface)"

        # Удалить текущий шлюз по умолчанию
        sudo ip route del default 2>/dev/null || true

        # Восстановить оригинальный шлюз
        sudo ip route add default via "$original_gw" dev "$original_iface"

        # Удалить временные маршруты
        sudo ip route del "$original_gw/32" 2>/dev/null || true

        # Удалить файл с сохраненным шлюзом
        rm -f /tmp/wsl_original_gateway

        success "Оригинальная маршрутизация восстановлена"
    else
        warning "Файл с оригинальным шлюзом не найден, выполняем сброс..."
        reset_routing
    fi

    show_status
}

# Сброс маршрутизации к состоянию по умолчанию
reset_routing() {
    log "Сброс маршрутизации к состоянию по умолчанию..."

    check_sudo

    # Получить интерфейс WSL
    local wsl_iface
    wsl_iface=$(ip route show | grep -E "172\.(1[6-9]|2[0-9]|3[01])\." | head -1 | awk '{print $3}')

    if [[ -z "$wsl_iface" ]]; then
        wsl_iface="eth0"  # Fallback
    fi

    # Получить сеть WSL
    local wsl_network wsl_gateway
    wsl_network=$(ip addr show "$wsl_iface" | grep -E "inet 172\." | awk '{print $2}' | cut -d'/' -f1)

    if [[ -n "$wsl_network" ]]; then
        # Вычислить шлюз WSL (обычно .1 в подсети)
        wsl_gateway=$(echo "$wsl_network" | sed 's/\.[0-9]*$/\.1/')

        log "Восстанавливаем WSL маршрутизацию: шлюз $wsl_gateway, интерфейс $wsl_iface"

        # Очистить все маршруты по умолчанию
        sudo ip route del default 2>/dev/null || true

        # Добавить стандартный WSL маршрут
        sudo ip route add default via "$wsl_gateway" dev "$wsl_iface"

        success "Маршрутизация сброшена к WSL по умолчанию"
    else
        error "Не удалось определить WSL сеть для сброса"
        exit 1
    fi

    # Очистить временные файлы
    rm -f /tmp/wsl_original_gateway

    show_status
}

# Тест подключения через разные маршруты
test_connectivity() {
    log "=== Тест подключения ==="

    # Тест локальных серверов
    echo "Тестирование локальных серверов:"

    for server in "$DEV_SERVER_NAME:$DEV_SERVER_IP" "$PROD_SERVER_NAME:$PROD_SERVER_IP"; do
        local name ip
        name=$(echo "$server" | cut -d':' -f1)
        ip=$(echo "$server" | cut -d':' -f2)

        printf "  %-15s (%s): " "$name" "$ip"
        if check_host_reachable "$ip" 3; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAIL${NC}"
        fi
    done

    # Тест интернет подключения
    echo
    echo "Тестирование интернет подключения:"

    for host in "8.8.8.8:Google DNS" "1.1.1.1:Cloudflare DNS" "ya.ru:Yandex"; do
        local ip name
        ip=$(echo "$host" | cut -d':' -f1)
        name=$(echo "$host" | cut -d':' -f2)

        printf "  %-15s (%s): " "$name" "$ip"
        if check_host_reachable "$ip" 5; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAIL${NC}"
        fi
    done

    # Показать текущий маршрут для интернет трафика
    echo
    echo "Маршрут для интернет трафика:"
    local trace_result
    if command -v traceroute >/dev/null; then
        trace_result=$(timeout 10 traceroute -m 3 8.8.8.8 2>/dev/null | head -3 || echo "Timeout")
        echo "$trace_result"
    else
        echo "traceroute не установлен, используем ping для проверки первого хопа"
        local default_gw
        default_gw=$(get_default_gateway)
        printf "  Первый хоп (%s): " "$default_gw"
        if check_host_reachable "$default_gw" 2; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAIL${NC}"
        fi
    fi
}

# Показать помощь
show_help() {
    echo "WSL Routing Manager - управление маршрутизацией через dev сервер"
    echo
    echo "Использование: $0 [команда]"
    echo
    echo "Команды:"
    echo "  enable    - Включить маршрутизацию через dev сервер ($DEV_SERVER_IP)"
    echo "  disable   - Отключить маршрутизацию через dev сервер"
    echo "  status    - Показать текущий статус маршрутизации"
    echo "  reset     - Сбросить маршрутизацию к WSL по умолчанию"
    echo "  test      - Протестировать подключение"
    echo "  help      - Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 enable     # Включить маршрутизацию через dev сервер"
    echo "  $0 status     # Проверить текущее состояние"
    echo "  $0 test       # Протестировать подключение"
    echo "  $0 disable    # Вернуться к обычной маршрутизации"
    echo
    echo "Примечания:"
    echo "  - Требуются права sudo для изменения маршрутов"
    echo "  - Dev сервер должен быть доступен по адресу $DEV_SERVER_IP"
    echo "  - Оригинальная маршрутизация сохраняется и восстанавливается"
    echo "  - Используйте 'reset' если что-то пошло не так"
}

# Основная логика
main() {
    local command=${1:-status}

    case "$command" in
        enable)
            enable_dev_routing
            ;;
        disable)
            disable_dev_routing
            ;;
        status)
            show_status
            ;;
        reset)
            reset_routing
            ;;
        test)
            test_connectivity
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Неизвестная команда: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Проверка, что скрипт запущен в WSL или Linux окружении
if [[ ! -f /proc/version ]]; then
    error "Этот скрипт должен запускаться в Linux окружении (WSL или нативный Linux)"
    exit 1
fi

# Запуск основной функции
main "$@"
