#!/bin/bash
# Получить результаты анализа трафика с prod-openwrt

set -euo pipefail

echo "=== Traffic Analysis Results ==="
echo "Fetching from prod-openwrt:/tmp/traffic_analysis/"
echo ""

# Проверить статус процессов
echo "Checking monitor status..."
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ps w | grep -E 'traffic_mon|tcpdump' | grep -v grep || echo 'Monitoring completed'"
echo ""

# Получить информацию о времени
echo "=== Timing Info ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "cat /tmp/traffic_analysis/info.txt 2>/dev/null || echo 'Not available yet'"
echo ""

# Получить размеры файлов
echo "=== Files ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ls -lh /tmp/traffic_analysis/ 2>/dev/null || echo 'Directory not found'"
echo ""

# Анализ захваченного трафика
echo "=== Traffic Capture Analysis ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "wc -l /tmp/traffic_analysis/capture.txt 2>/dev/null || echo 'No capture yet'"
echo ""

# Топ IP адреса из захвата
echo "=== Top Source IPs (from tcpdump) ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "
  grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' /tmp/traffic_analysis/capture.txt 2>/dev/null | \
  sort | uniq -c | sort -rn | head -20 || echo 'Not ready yet'
"
echo ""

# Анализ соединений
echo "=== Top Destination IPs (from connections) ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "
  grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+' /tmp/traffic_analysis/connections.txt 2>/dev/null | \
  sed 's/:[0-9]*$//' | sort | uniq -c | sort -rn | head -20 || echo 'Not ready yet'
"
echo ""

# Статистика интерфейсов
echo "=== Interface Statistics ==="
echo "Start:"
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "cat /tmp/traffic_analysis/iface_start.txt 2>/dev/null | grep -E 'wlan|eth|br-lan' || echo 'Not available'"
echo ""
echo "End:"
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "cat /tmp/traffic_analysis/iface_end.txt 2>/dev/null | grep -E 'wlan|eth|br-lan' || echo 'Not available yet'"
echo ""

# Количество соединений по времени
echo "=== Connection Samples Over Time ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "
  grep -c '^===' /tmp/traffic_analysis/connections.txt 2>/dev/null && \
  echo 'samples collected' || echo 'No samples yet'
"
echo ""

echo "=== Analysis Complete ==="
