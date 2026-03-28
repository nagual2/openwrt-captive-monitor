#!/bin/sh
# Скрипт для установки пакетов на OpenWrt, идентичных openwrt-prod (AX3000T)
# Использует менеджер пакетов apk (OpenWrt 24+)

# Список только пользовательских (не базовых) пакетов
PACKAGES="
attendedsysupgrade-common
avahi-dbus-daemon
avahi-utils
bind-dig
bmon
btop
ca-bundle
curl
dbus
htop
https-dns-proxy
iftop
lldpd
luci-app-attendedsysupgrade
luci-app-lldpd
luci-app-package-manager
luci-app-upnp
luci-app-wireguard
luci-i18n-base-ru
luci-i18n-firewall-ru
luci-i18n-lldpd-ru
luci-i18n-upnp-ru
luci-i18n-wireguard-ru
luci-proto-wireguard
mc
miniupnpd-nftables
mtr-json
nmap
owut
procps-ng
procps-ng-watch
stubby
tcpdump
wireguard-tools
zerotier
"

echo "=== Обновление списка пакетов ==="
apk update

echo "=== Установка пакетов ==="
for pkg in $PACKAGES; do
    echo "Установка: $pkg..."
    apk add "$pkg"
done

echo "=== Завершено ==="
