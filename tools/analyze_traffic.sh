#!/bin/bash
# Скрипт для анализа трафика на OpenWrt роутере
# Собирает статистику в течение заданного времени

set -euo pipefail

DURATION=${1:-1800}  # По умолчанию 30 минут (1800 секунд)
OUTPUT_DIR="/tmp/traffic_analysis_$(date +%Y%m%d_%H%M%S)"

echo "=== Traffic Analysis Started ==="
echo "Duration: ${DURATION} seconds ($((DURATION / 60)) minutes)"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Создать директорию для результатов
mkdir -p "${OUTPUT_DIR}"

# Функция для сбора статистики интерфейсов
collect_interface_stats() {
    local interval=60  # Собирать каждую минуту
    local iterations=$((DURATION / interval))
    
    echo "Collecting interface statistics..."
    for i in $(seq 1 ${iterations}); do
        {
            echo "=== Timestamp: $(date '+%Y-%m-%d %H:%M:%S') ==="
            cat /proc/net/dev
            echo ""
        } >> "${OUTPUT_DIR}/interface_stats.log"
        sleep ${interval}
    done
}

# Функция для сбора активных соединений
collect_connections() {
    local interval=60
    local iterations=$((DURATION / interval))
    
    echo "Collecting active connections..."
    for i in $(seq 1 ${iterations}); do
        {
            echo "=== Timestamp: $(date '+%Y-%m-%d %H:%M:%S') ==="
            netstat -tunap 2>/dev/null | head -100
            echo ""
        } >> "${OUTPUT_DIR}/connections.log"
        sleep ${interval}
    done
}

# Функция для захвата топ хостов через tcpdump
collect_top_hosts() {
    echo "Capturing traffic for top hosts analysis..."
    timeout ${DURATION} tcpdump -i any -nn -q -t \
        'not port 22' \
        2>/dev/null | \
        awk '{print $2, $4}' | \
        sed 's/:[0-9]*$//' | \
        sort | uniq -c | sort -rn > "${OUTPUT_DIR}/top_hosts_raw.log" || true
}

# Функция для мониторинга DNS запросов
collect_dns_queries() {
    local interval=60
    local iterations=$((DURATION / interval))
    
    echo "Collecting DNS queries..."
    for i in $(seq 1 ${iterations}); do
        {
            echo "=== Timestamp: $(date '+%Y-%m-%d %H:%M:%S') ==="
            logread | grep -i 'dnsmasq\|dns' | tail -50
            echo ""
        } >> "${OUTPUT_DIR}/dns_queries.log"
        sleep ${interval}
    done
}

# Запустить все сборщики в фоне
collect_interface_stats &
PID_IFACE=$!

collect_connections &
PID_CONN=$!

collect_dns_queries &
PID_DNS=$!

# Захват трафика (блокирующий)
collect_top_hosts
PID_TCPDUMP=$!

# Дождаться завершения всех фоновых процессов
wait ${PID_IFACE} 2>/dev/null || true
wait ${PID_CONN} 2>/dev/null || true
wait ${PID_DNS} 2>/dev/null || true

echo ""
echo "=== Collection Complete ==="
echo ""

# Анализ собранных данных
echo "=== Analyzing Results ==="
echo ""

# Топ хосты по количеству пакетов
if [ -f "${OUTPUT_DIR}/top_hosts_raw.log" ]; then
    echo "Top 20 hosts by packet count:"
    head -20 "${OUTPUT_DIR}/top_hosts_raw.log" | \
        awk '{printf "%8s packets: %s\n", $1, $2}' | \
        tee "${OUTPUT_DIR}/top_hosts.txt"
    echo ""
fi

# Статистика по интерфейсам
if [ -f "${OUTPUT_DIR}/interface_stats.log" ]; then
    echo "Interface traffic summary:"
    {
        echo "Interface statistics from first and last snapshots:"
        echo ""
        echo "=== First snapshot ==="
        head -20 "${OUTPUT_DIR}/interface_stats.log"
        echo ""
        echo "=== Last snapshot ==="
        tail -20 "${OUTPUT_DIR}/interface_stats.log"
    } > "${OUTPUT_DIR}/interface_summary.txt"
    cat "${OUTPUT_DIR}/interface_summary.txt"
    echo ""
fi

# Топ соединения
if [ -f "${OUTPUT_DIR}/connections.log" ]; then
    echo "Top 10 most frequent connections:"
    grep -E '^(tcp|udp)' "${OUTPUT_DIR}/connections.log" | \
        awk '{print $5}' | \
        sed 's/:[0-9]*$//' | \
        sort | uniq -c | sort -rn | head -10 | \
        awk '{printf "%6s connections: %s\n", $1, $2}' | \
        tee "${OUTPUT_DIR}/top_connections.txt"
    echo ""
fi

# Топ DNS запросы
if [ -f "${OUTPUT_DIR}/dns_queries.log" ]; then
    echo "Top 10 DNS queries:"
    grep -oE 'query\[[A-Z]+\] [^ ]+' "${OUTPUT_DIR}/dns_queries.log" | \
        awk '{print $2}' | \
        sort | uniq -c | sort -rn | head -10 | \
        awk '{printf "%6s queries: %s\n", $1, $2}' | \
        tee "${OUTPUT_DIR}/top_dns.txt" || echo "No DNS queries found"
    echo ""
fi

echo "=== Analysis Complete ==="
echo "Results saved to: ${OUTPUT_DIR}"
echo ""
echo "Summary files:"
ls -lh "${OUTPUT_DIR}"/*.txt 2>/dev/null || echo "No summary files generated"
