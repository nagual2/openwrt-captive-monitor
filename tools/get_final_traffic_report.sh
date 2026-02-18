#!/bin/bash
# Получить финальные результаты анализа трафика после завершения мониторинга

set -euo pipefail

echo "=== Final Traffic Analysis Report ==="
echo "Fetching results from prod-openwrt..."
echo ""

# Проверить завершился ли мониторинг
echo "Checking monitor status..."
if wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ps w | grep traffic_mon | grep -v grep" 2>/dev/null; then
    echo "⚠️  Monitoring still in progress"
    echo "Please wait for completion or run this script later"
    echo ""
else
    echo "✅ Monitoring completed"
    echo ""
fi

# Получить timing информацию
echo "=== Timing Information ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "cat /tmp/traffic_analysis/info.txt 2>/dev/null || echo 'Not available'"
echo ""

# Получить размеры файлов
echo "=== Collected Data ==="
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ls -lh /tmp/traffic_analysis/ 2>/dev/null || echo 'Directory not found'"
echo ""

# Количество собранных samples
echo "=== Connection Samples ==="
SAMPLES=$(wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "grep -c '^===' /tmp/traffic_analysis/connections.txt 2>/dev/null || echo 0")
echo "Collected $SAMPLES samples (expected 6)"
echo ""

# Топ IP адреса
echo "=== Top 20 IP Addresses ==="
wsl timeout 30 ssh -o ConnectTimeout=5 root@prod-openwrt "
  grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' /tmp/traffic_analysis/capture.txt | \
  sort | uniq -c | sort -rn | head -20 | \
  awk '{printf \"%8s packets: %s\n\", \$1, \$2}'
"
echo ""

# Топ соединения по времени
if [ "$SAMPLES" -gt 0 ]; then
    echo "=== Top Destination IPs (from connection samples) ==="
    wsl timeout 30 ssh -o ConnectTimeout=5 root@prod-openwrt "
      grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+' /tmp/traffic_analysis/connections.txt | \
      sed 's/:[0-9]*$//' | sort | uniq -c | sort -rn | head -20 | \
      awk '{printf \"%6s connections: %s\n\", \$1, \$2}'
    "
    echo ""
fi

# Статистика интерфейсов
echo "=== Interface Traffic Statistics ==="
echo "Calculating differences..."
wsl timeout 30 ssh -o ConnectTimeout=5 root@prod-openwrt "
  if [ -f /tmp/traffic_analysis/iface_end.txt ]; then
    echo 'Start snapshot:'
    grep -E 'wlan|eth|br-lan' /tmp/traffic_analysis/iface_start.txt | head -5
    echo ''
    echo 'End snapshot:'
    grep -E 'wlan|eth|br-lan' /tmp/traffic_analysis/iface_end.txt | head -5
  else
    echo 'End snapshot not available yet'
  fi
"
echo ""

# Сохранить результаты локально
echo "=== Saving Results Locally ==="
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="traffic_reports/${TIMESTAMP}"
mkdir -p "$REPORT_DIR"

echo "Downloading files to $REPORT_DIR..."
wsl timeout 30 ssh -o ConnectTimeout=5 root@prod-openwrt "cd /tmp/traffic_analysis && tar czf /tmp/traffic_report.tar.gz ." 2>/dev/null || true
wsl timeout 30 ssh -o ConnectTimeout=5 root@prod-openwrt "cat /tmp/traffic_report.tar.gz" > "$REPORT_DIR/traffic_report.tar.gz" 2>/dev/null || echo "Failed to download"

if [ -f "$REPORT_DIR/traffic_report.tar.gz" ]; then
    cd "$REPORT_DIR"
    tar xzf traffic_report.tar.gz
    rm traffic_report.tar.gz
    echo "✅ Files saved to $REPORT_DIR"
    ls -lh
else
    echo "⚠️  Failed to download files"
fi

echo ""
echo "=== Report Complete ==="
echo "Local files: $REPORT_DIR"
echo "Remote files: prod-openwrt:/tmp/traffic_analysis/"
