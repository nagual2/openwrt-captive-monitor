#!/bin/sh
# OpenWRT Captive Portal Monitor and Auto-Redirect Script
# Проверяет интернет, перезагружает WiFi и редиректит трафик на captive portal

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

# Сетевые интерфейсы
WIFI_INTERFACE="${WIFI_INTERFACE:-phy1-sta0}"
WIFI_LOGICAL="${WIFI_LOGICAL:-wwan}"  # Логический интерфейс OpenWRT (wwan/wan)

# Серверы для проверки интернета
PING_SERVERS="1.1.1.1 8.8.8.8 9.9.9.9"
PING_COUNT=1
PING_TIMEOUT=2

# Параметры проверки
GATEWAY_CHECK_RETRIES=3
GATEWAY_CHECK_DELAY=3
INTERNET_CHECK_RETRIES=3
INTERNET_CHECK_DELAY=5
MAX_WAIT_TIME=90

# Интервал мониторинга (секунды)
MONITOR_INTERVAL=60

# Логирование
LOG_TAG="captive-monitor"
ENABLE_SYSLOG=1

# ============================================================================
# ФУНКЦИИ ЛОГИРОВАНИЯ
# ============================================================================

log_info() {
    local msg="$1"
    echo "[INFO] $msg"
    [ "$ENABLE_SYSLOG" = "1" ] && logger -t "$LOG_TAG" -p user.info "$msg"
}

log_warn() {
    local msg="$1"
    echo "[WARN] $msg" >&2
    [ "$ENABLE_SYSLOG" = "1" ] && logger -t "$LOG_TAG" -p user.warn "$msg"
}

log_error() {
    local msg="$1"
    echo "[ERROR] $msg" >&2
    [ "$ENABLE_SYSLOG" = "1" ] && logger -t "$LOG_TAG" -p user.err "$msg"
}

# ============================================================================
# ФУНКЦИИ ПРОВЕРКИ СЕТИ
# ============================================================================

# Проверка доступности хоста через ping
ping_host() {
    local host="$1"
    ping -c "$PING_COUNT" -W "$PING_TIMEOUT" "$host" >/dev/null 2>&1
    return $?
}

# Получение IP шлюза для интерфейса
get_gateway_ip() {
    local iface="${1:-$WIFI_INTERFACE}"
    local gateway
    
    # Метод 1: Через ip route show dev
    gateway=$(ip route show dev "$iface" 2>/dev/null | grep '^default' | awk '{print $3}' | head -n1)
    
    if [ -n "$gateway" ]; then
        echo "$gateway"
        return 0
    fi
    
    # Метод 2: Через ip route (без dev)
    gateway=$(ip route 2>/dev/null | grep "^default.*dev $iface" | awk '{print $3}' | head -n1)
    
    if [ -n "$gateway" ]; then
        echo "$gateway"
        return 0
    fi
    
    # Метод 3: Через route -n
    gateway=$(route -n 2>/dev/null | grep "^0.0.0.0.*$iface" | awk '{print $2}' | head -n1)
    
    if [ -n "$gateway" ]; then
        echo "$gateway"
        return 0
    fi
    
    # Метод 4: Получаем из dhcp lease (если используется DHCP)
    if [ -f "/tmp/dhcp.leases" ]; then
        gateway=$(grep "$iface" /tmp/dhcp.leases 2>/dev/null | awk '{print $3}' | head -n1)
        if [ -n "$gateway" ]; then
            echo "$gateway"
            return 0
        fi
    fi
    
    # Метод 5: Пробуем получить из uci (OpenWRT config)
    if command -v uci >/dev/null 2>&1; then
        local logical="${WIFI_LOGICAL:-$iface}"
        gateway=$(uci get "network.${logical}.gateway" 2>/dev/null)
        if [ -n "$gateway" ]; then
            echo "$gateway"
            return 0
        fi
    fi
    
    # Метод 6: Последний шанс - берем любой default gateway
    gateway=$(ip route 2>/dev/null | grep '^default' | awk '{print $3}' | head -n1)
    
    if [ -n "$gateway" ]; then
        log_warn "Используем общий default gateway: $gateway"
        echo "$gateway"
        return 0
    fi
    
    return 1
}

# Проверка доступности шлюза
check_gateway() {
    local gateway
    local attempt
    
    for attempt in $(seq 1 $GATEWAY_CHECK_RETRIES); do
        gateway=$(get_gateway_ip)
        
        if [ -n "$gateway" ]; then
            if ping_host "$gateway"; then
                log_info "Шлюз $gateway доступен"
                return 0
            fi
            log_warn "Шлюз $gateway не отвечает (попытка $attempt/$GATEWAY_CHECK_RETRIES)"
        else
            log_warn "Шлюз не найден (попытка $attempt/$GATEWAY_CHECK_RETRIES)"
            log_warn "Диагностика:"
            ip route show 2>&1 | head -5 | while read line; do
                log_warn "  route: $line"
            done
        fi
        
        [ "$attempt" -lt "$GATEWAY_CHECK_RETRIES" ] && sleep "$GATEWAY_CHECK_DELAY"
    done
    
    log_error "Шлюз недоступен после $GATEWAY_CHECK_RETRIES попыток"
    return 1
}

# Проверка доступности интернета
check_internet() {
    local attempt
    local server
    
    for attempt in $(seq 1 $INTERNET_CHECK_RETRIES); do
        for server in $PING_SERVERS; do
            if ping_host "$server"; then
                log_info "Интернет доступен (сервер: $server)"
                return 0
            fi
        done
        
        if [ "$attempt" -lt "$INTERNET_CHECK_RETRIES" ]; then
            log_warn "Интернет недоступен, повтор через ${INTERNET_CHECK_DELAY}с (попытка $attempt/$INTERNET_CHECK_RETRIES)"
            sleep "$INTERNET_CHECK_DELAY"
        fi
    done
    
    log_warn "Интернет недоступен после $INTERNET_CHECK_RETRIES попыток"
    return 1
}

# ============================================================================
# ФУНКЦИИ УПРАВЛЕНИЯ WiFi
# ============================================================================

# Проверка существования интерфейса
interface_exists() {
    local iface="${1:-$WIFI_INTERFACE}"
    ip link show "$iface" >/dev/null 2>&1
    return $?
}

# Проверка состояния интерфейса (up/down)
is_interface_up() {
    local iface="${1:-$WIFI_INTERFACE}"
    ip link show "$iface" 2>/dev/null | grep -q "state UP"
    return $?
}

# Перезапуск WiFi через ifdown/ifup (OpenWRT)
restart_wifi_logical() {
    local logical="${1:-$WIFI_LOGICAL}"
    
    log_info "Перезапуск логического интерфейса: $logical"
    
    ifdown "$logical" 2>/dev/null
    sleep 2
    
    if ifup "$logical" 2>/dev/null; then
        log_info "Логический интерфейс $logical успешно поднят"
        return 0
    else
        log_error "Ошибка при поднятии логического интерфейса $logical"
        return 1
    fi
}

# Перезапуск WiFi через ip link
restart_wifi_physical() {
    local iface="${1:-$WIFI_INTERFACE}"
    
    log_info "Перезапуск физического интерфейса: $iface"
    
    if ! interface_exists "$iface"; then
        log_error "Интерфейс $iface не существует"
        return 1
    fi
    
    # Опускаем интерфейс
    ip link set dev "$iface" down 2>/dev/null
    sleep 2
    
    # Поднимаем интерфейс
    if ip link set dev "$iface" up 2>/dev/null; then
        log_info "Интерфейс $iface успешно поднят"
    else
        log_error "Ошибка при поднятии интерфейса $iface"
        return 1
    fi
    
    # Ждем получения IP и доступности шлюза
    local start_time=$(date +%s)
    local current_time
    local elapsed
    
    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        if [ "$elapsed" -ge "$MAX_WAIT_TIME" ]; then
            log_error "Таймаут ожидания готовности интерфейса ($MAX_WAIT_TIME сек)"
            return 1
        fi
        
        # Проверяем наличие IP
        if is_interface_up "$iface" && ip -4 addr show dev "$iface" | grep -q 'inet '; then
            log_info "Интерфейс $iface получил IP адрес"
            
            # Проверяем доступность шлюза
            local gateway=$(get_gateway_ip "$iface")
            if [ -n "$gateway" ] && ping_host "$gateway"; then
                log_info "Шлюз $gateway доступен, интерфейс готов"
                return 0
            fi
        fi
        
        sleep 3
    done
}

# Основная функция перезапуска WiFi
restart_wifi() {
    log_info "Начало перезапуска WiFi"
    
    # Пробуем через логический интерфейс (если настроен)
    if [ -n "$WIFI_LOGICAL" ] && [ "$WIFI_LOGICAL" != "$WIFI_INTERFACE" ]; then
        if restart_wifi_logical "$WIFI_LOGICAL"; then
            return 0
        fi
        log_warn "Перезапуск через логический интерфейс не удался, пробуем физический"
    fi
    
    # Перезапуск через физический интерфейс
    restart_wifi_physical "$WIFI_INTERFACE"
    return $?
}

# ============================================================================
# ФУНКЦИИ УПРАВЛЕНИЯ DNS
# ============================================================================

# Путь к конфигурации dnsmasq для captive portal
DNSMASQ_CAPTIVE_CONF="/tmp/dnsmasq.d/captive-portal.conf"
DNSMASQ_CAPTIVE_DIR="/tmp/dnsmasq.d"

# Проверка наличия DNS spoofing
dns_spoofing_exists() {
    [ -f "$DNSMASQ_CAPTIVE_CONF" ]
}

# Установка DNS spoofing - все DNS запросы возвращают адрес шлюза
setup_dns_spoofing() {
    local gateway
    
    gateway=$(get_gateway_ip)
    
    if [ -z "$gateway" ]; then
        log_error "Не удалось получить IP шлюза для DNS spoofing"
        log_error "Диагностика маршрутов:"
        ip route show 2>&1 | while read line; do
            log_error "  $line"
        done
        return 1
    fi
    
    log_info "Установка DNS spoofing: все домены -> $gateway"
    
    # Создаем директорию для dnsmasq конфигов
    mkdir -p "$DNSMASQ_CAPTIVE_DIR"
    
    # Создаем конфиг для dnsmasq
    # address=/#/ означает что все домены будут резолвиться в указанный IP
    # local-ttl=0 устанавливает минимальное время жизни DNS записей
    cat > "$DNSMASQ_CAPTIVE_CONF" <<EOF
# Captive Portal DNS Configuration
# Все DNS запросы возвращают адрес шлюза
address=/#/$gateway

# Минимальное время жизни DNS записей (0 секунд)
local-ttl=0
min-cache-ttl=0
max-cache-ttl=0

# Не кешировать negative responses
no-negcache
EOF
    
    # Перезапускаем dnsmasq для применения конфигурации
    if /etc/init.d/dnsmasq restart >/dev/null 2>&1; then
        log_info "DNS spoofing установлен, dnsmasq перезапущен"
    else
        log_warn "Не удалось перезапустить dnsmasq, пробуем reload"
        /etc/init.d/dnsmasq reload >/dev/null 2>&1
    fi
    
    return 0
}

# Удаление DNS spoofing
remove_dns_spoofing() {
    log_info "Удаление DNS spoofing"
    
    if [ -f "$DNSMASQ_CAPTIVE_CONF" ]; then
        rm -f "$DNSMASQ_CAPTIVE_CONF"
        
        # Перезапускаем dnsmasq для применения изменений
        if /etc/init.d/dnsmasq restart >/dev/null 2>&1; then
            log_info "DNS spoofing удален, dnsmasq перезапущен"
        else
            log_warn "Не удалось перезапустить dnsmasq, пробуем reload"
            /etc/init.d/dnsmasq reload >/dev/null 2>&1
        fi
    fi
    
    return 0
}

# ============================================================================
# ФУНКЦИИ УПРАВЛЕНИЯ IPTABLES РЕДИРЕКТОМ
# ============================================================================

# Проверка наличия правил редиректа
redirect_exists() {
    iptables -t nat -L PREROUTING -n 2>/dev/null | grep -q "CAPTIVE_REDIRECT"
}

# Проверка наличия DNS редиректа
dns_redirect_exists() {
    iptables -t nat -L PREROUTING -n 2>/dev/null | grep -q "CAPTIVE_DNS_REDIRECT"
}

# Установка редиректа DNS (TCP/UDP порт 53) на локальный DNS
setup_dns_redirect() {
    local router_ip
    
    # Получаем IP адрес роутера на WiFi интерфейсе
    router_ip=$(ip -4 addr show dev "$WIFI_INTERFACE" 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    
    if [ -z "$router_ip" ]; then
        log_warn "Не удалось получить IP роутера, используем default"
        router_ip="192.168.1.1"
    fi
    
    log_info "Установка DNS редиректа на локальный DNS: $router_ip:53"
    
    # Создаем цепочку для DNS редиректа (если не существует)
    if ! iptables -t nat -L CAPTIVE_DNS_REDIRECT -n >/dev/null 2>&1; then
        iptables -t nat -N CAPTIVE_DNS_REDIRECT
    fi
    
    # Очищаем цепочку
    iptables -t nat -F CAPTIVE_DNS_REDIRECT
    
    # Редирект DNS UDP (порт 53)
    iptables -t nat -A CAPTIVE_DNS_REDIRECT -p udp --dport 53 -j DNAT --to-destination "$router_ip:53"
    
    # Редирект DNS TCP (порт 53)
    iptables -t nat -A CAPTIVE_DNS_REDIRECT -p tcp --dport 53 -j DNAT --to-destination "$router_ip:53"
    
    # Добавляем правило в PREROUTING (если еще не добавлено)
    if ! dns_redirect_exists; then
        iptables -t nat -I PREROUTING -i "$WIFI_INTERFACE" -j CAPTIVE_DNS_REDIRECT
    fi
    
    log_info "DNS редирект установлен: DNS (TCP/UDP 53) -> $router_ip:53"
    return 0
}

# Удаление DNS редиректа
remove_dns_redirect() {
    log_info "Удаление DNS редиректа"
    
    # Удаляем правило из PREROUTING
    iptables -t nat -D PREROUTING -i "$WIFI_INTERFACE" -j CAPTIVE_DNS_REDIRECT 2>/dev/null
    
    # Очищаем и удаляем цепочку
    iptables -t nat -F CAPTIVE_DNS_REDIRECT 2>/dev/null
    iptables -t nat -X CAPTIVE_DNS_REDIRECT 2>/dev/null
    
    log_info "DNS редирект удален"
    return 0
}

# Установка редиректа HTTP/HTTPS на шлюз
setup_redirect() {
    local gateway
    
    gateway=$(get_gateway_ip)
    
    if [ -z "$gateway" ]; then
        log_error "Не удалось получить IP шлюза для редиректа"
        log_error "Диагностика маршрутов:"
        ip route show 2>&1 | while read line; do
            log_error "  $line"
        done
        return 1
    fi
    
    log_info "Установка редиректа трафика на шлюз: $gateway"
    
    # Создаем цепочку для редиректа (если не существует)
    if ! iptables -t nat -L CAPTIVE_REDIRECT -n >/dev/null 2>&1; then
        iptables -t nat -N CAPTIVE_REDIRECT
    fi
    
    # Очищаем цепочку
    iptables -t nat -F CAPTIVE_REDIRECT
    
    # Редирект HTTP (порт 80)
    iptables -t nat -A CAPTIVE_REDIRECT -p tcp --dport 80 -j DNAT --to-destination "$gateway:80"
    
    # Редирект HTTPS (порт 443) - некоторые порталы используют
    iptables -t nat -A CAPTIVE_REDIRECT -p tcp --dport 443 -j DNAT --to-destination "$gateway:80"
    
    # Добавляем правило в PREROUTING (если еще не добавлено)
    if ! redirect_exists; then
        iptables -t nat -I PREROUTING -i "$WIFI_INTERFACE" -j CAPTIVE_REDIRECT
    fi
    
    log_info "Редирект установлен: HTTP/HTTPS -> $gateway:80"
    return 0
}

# Удаление редиректа
remove_redirect() {
    log_info "Удаление редиректа трафика"
    
    # Удаляем правило из PREROUTING
    iptables -t nat -D PREROUTING -i "$WIFI_INTERFACE" -j CAPTIVE_REDIRECT 2>/dev/null
    
    # Очищаем и удаляем цепочку
    iptables -t nat -F CAPTIVE_REDIRECT 2>/dev/null
    iptables -t nat -X CAPTIVE_REDIRECT 2>/dev/null
    
    log_info "Редирект удален"
    return 0
}

# Установка полного captive portal режима (DNS spoofing + HTTP/HTTPS redirect + DNS redirect)
setup_captive_mode() {
    log_info "=== Установка Captive Portal режима ==="
    
    # 1. DNS Spoofing через dnsmasq (все домены -> шлюз)
    if ! setup_dns_spoofing; then
        log_error "Не удалось установить DNS spoofing"
        return 1
    fi
    
    # 2. DNS Redirect через iptables (все DNS запросы -> локальный DNS)
    if ! setup_dns_redirect; then
        log_error "Не удалось установить DNS redirect"
        return 1
    fi
    
    # 3. HTTP/HTTPS Redirect (весь веб-трафик -> шлюз)
    if ! setup_redirect; then
        log_error "Не удалось установить HTTP/HTTPS redirect"
        return 1
    fi
    
    log_info "Captive Portal режим полностью установлен"
    return 0
}

# Удаление полного captive portal режима
remove_captive_mode() {
    log_info "=== Удаление Captive Portal режима ==="
    
    # Удаляем в обратном порядке
    remove_redirect
    remove_dns_redirect
    remove_dns_spoofing
    
    log_info "Captive Portal режим полностью удален"
    return 0
}

# ============================================================================
# ОСНОВНАЯ ЛОГИКА
# ============================================================================

# Обработка одного цикла проверки
check_and_fix_connection() {
    log_info "=== Проверка подключения ==="
    
    # Проверяем интернет
    if check_internet; then
        log_info "Интернет доступен, Captive Portal режим не требуется"
        
        # Убираем captive portal режим если был установлен
        if redirect_exists || dns_redirect_exists || dns_spoofing_exists; then
            remove_captive_mode
        fi
        
        return 0
    fi
    
    log_warn "Интернет недоступен, начинаем процедуру восстановления"
    
    # Перезапускаем WiFi
    if ! restart_wifi; then
        log_error "Не удалось перезапустить WiFi"
        return 1
    fi
    
    # Проверяем интернет после перезапуска
    if check_internet; then
        log_info "Интернет восстановлен после перезапуска WiFi"
        return 0
    fi
    
    # Интернет все еще недоступен - устанавливаем полный captive portal режим
    log_warn "Интернет недоступен после перезапуска, устанавливаем Captive Portal режим"
    
    if ! setup_captive_mode; then
        log_error "Не удалось установить Captive Portal режим"
        return 1
    fi
    
    # Ждем восстановления интернета
    log_info "Ожидание восстановления интернета (проверка каждые ${INTERNET_CHECK_DELAY}с)"
    
    local wait_count=0
    local max_wait_cycles=$((MAX_WAIT_TIME / INTERNET_CHECK_DELAY))
    
    while [ "$wait_count" -lt "$max_wait_cycles" ]; do
        sleep "$INTERNET_CHECK_DELAY"
        
        if check_internet; then
            log_info "Интернет восстановлен, удаляем Captive Portal режим"
            remove_captive_mode
            return 0
        fi
        
        wait_count=$((wait_count + 1))
        log_info "Интернет все еще недоступен (ожидание: ${wait_count}/${max_wait_cycles})"
    done
    
    log_warn "Интернет не восстановился за отведенное время"
    return 1
}

# Режим мониторинга (бесконечный цикл)
monitor_mode() {
    log_info "Запуск в режиме мониторинга (интервал: ${MONITOR_INTERVAL}с)"
    
    while true; do
        check_and_fix_connection
        
        log_info "Следующая проверка через ${MONITOR_INTERVAL}с"
        sleep "$MONITOR_INTERVAL"
    done
}

# Однократная проверка
oneshot_mode() {
    log_info "Запуск в режиме однократной проверки"
    check_and_fix_connection
    exit $?
}

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

show_usage() {
    cat <<EOF
Использование: $0 [ОПЦИИ]

Опции:
  -m, --monitor     Режим мониторинга (бесконечный цикл)
  -o, --oneshot     Однократная проверка и выход
  -i, --interface   WiFi интерфейс (по умолчанию: $WIFI_INTERFACE)
  -l, --logical     Логический интерфейс OpenWRT (по умолчанию: $WIFI_LOGICAL)
  -t, --interval    Интервал мониторинга в секундах (по умолчанию: $MONITOR_INTERVAL)
  -h, --help        Показать эту справку

Примеры:
  $0 --oneshot                    # Однократная проверка
  $0 --monitor                    # Постоянный мониторинг
  $0 -m -i wlan0 -l wan -t 30    # Мониторинг с кастомными параметрами

Переменные окружения:
  WIFI_INTERFACE    Физический WiFi интерфейс
  WIFI_LOGICAL      Логический интерфейс OpenWRT
  MONITOR_INTERVAL  Интервал проверки в секундах

EOF
}

# Парсинг аргументов
MODE="oneshot"

while [ $# -gt 0 ]; do
    case "$1" in
        -m|--monitor)
            MODE="monitor"
            shift
            ;;
        -o|--oneshot)
            MODE="oneshot"
            shift
            ;;
        -i|--interface)
            WIFI_INTERFACE="$2"
            shift 2
            ;;
        -l|--logical)
            WIFI_LOGICAL="$2"
            shift 2
            ;;
        -t|--interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Неизвестная опция: $1" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Проверка прав root
if [ "$(id -u)" -ne 0 ]; then
    log_error "Скрипт требует прав root"
    exit 1
fi

# Запуск в выбранном режиме
case "$MODE" in
    monitor)
        monitor_mode
        ;;
    oneshot)
        oneshot_mode
        ;;
    *)
        log_error "Неизвестный режим: $MODE"
        exit 1
        ;;
esac