#!/bin/bash
# Проверка прогресса анализа трафика на prod-openwrt

set -euo pipefail

echo "=== Traffic Analysis Progress Check ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Проверить запущен ли процесс мониторинга
echo "Checking monitor process..."
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ps w | grep monitor.sh | grep -v grep || echo 'Monitor process not found'"
echo ""

# Проверить логи
echo "Monitor log (last 10 lines):"
wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "tail -10 /tmp/monitor.log 2>/dev/null || echo 'No log yet'"
echo ""

# Найти директорию с результатами
echo "Finding results directory..."
RESULT_DIR=$(wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ls -dt /tmp/traffic_* 2>/dev/null | head -1" || echo "")

if [ -n "$RESULT_DIR" ]; then
    echo "Results directory: $RESULT_DIR"
    echo ""
    
    echo "Files in results directory:"
    wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "ls -lh $RESULT_DIR/ 2>/dev/null || echo 'Directory not accessible'"
    echo ""
    
    # Показать промежуточные результаты если есть
    echo "=== Intermediate Results ==="
    echo ""
    
    echo "Top 10 hosts (if available):"
    wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "head -10 $RESULT_DIR/hosts.txt 2>/dev/null || echo 'Not ready yet'"
    echo ""
    
    echo "Recent connections (last 20 lines):"
    wsl timeout 10 ssh -o ConnectTimeout=5 root@prod-openwrt "tail -20 $RESULT_DIR/connections.txt 2>/dev/null || echo 'Not ready yet'"
    echo ""
else
    echo "Results directory not found yet"
fi

echo "=== Check Complete ==="
