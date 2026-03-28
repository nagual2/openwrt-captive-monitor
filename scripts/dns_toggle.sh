#!/bin/sh
# Скрипт для быстрого переключения DNS апстримов на OpenWrt
# Использование: ./dns_toggle.sh add | del

ACTION=$1

if [ "$ACTION" = "add" ]; then
    echo "=== Включение временных DNS (8.8.8.8, 1.1.1.1) ==="
    # Разрешаем использование внешних DNS
    uci set dhcp.@dnsmasq[0].noresolv='0'
    # Добавляем Google и Cloudflare
    uci add_list dhcp.@dnsmasq[0].server='8.8.8.8'
    uci add_list dhcp.@dnsmasq[0].server='1.1.1.1'
    
    uci commit dhcp
    /etc/init.d/dnsmasq restart
    echo "✅ Временные DNS добавлены. Связь должна восстановиться."

elif [ "$ACTION" = "del" ]; then
    echo "=== Удаление временных DNS апстримов ==="
    # Удаляем временные серверы
    uci del_list dhcp.@dnsmasq[0].server='8.8.8.8'
    uci del_list dhcp.@dnsmasq[0].server='1.1.1.1'
    # Возвращаем режим 'noresolv' (только локальные прокси)
    uci set dhcp.@dnsmasq[0].noresolv='1'
    
    uci commit dhcp
    /etc/init.d/dnsmasq restart
    echo "✅ Временные DNS удалены. Система вернулась к использованию локальных прокси."

else
    echo "Использование: $0 {add|del}"
    exit 1
fi
