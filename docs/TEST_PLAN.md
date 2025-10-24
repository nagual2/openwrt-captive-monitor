# Тест-план OpenWrt Captive Monitor (OpenWrt 24.x / filogic / Xiaomi Mi Router AX3000T)

> Полевой лаборатории нет — опираемся на статические проверки, эмуляцию OpenWrt и финальные тесты на устройстве, когда оно появится.

## 1. Локальные проверки (разработчик и CI)
- `shfmt -i 2 -ci -sr -d $(git ls-files '*.sh')` — проверка стиля в соответствии с `.shfmt.conf`.
- `shellcheck -s sh <files>` — статический анализ всех shell-скриптов.
- `bats`/`shunit2` тесты для функций `setup_firewall_redirects_*`, `cleanup_firewall_redirects_*`, `write_dnsmasq_intercept`, `detect_firewall_backend` (с mock-бинарями `ip`, `iptables`, `nft`).
- `sh -n package/openwrt-captive-monitor/files/etc/init.d/captive-monitor` — синтаксическая проверка init-скрипта.
- Запуск `openwrt_captive_monitor.sh --oneshot` с подменой команд (через `PATH`) для проверки обработки нештатных ситуаций.

## 2. Эмуляция OpenWrt 24.x (SDK/контейнер)
1. Развернуть OpenWrt 24.02 rootfs (таргет `mediatek/filogic`) через SDK или контейнер `openwrtorg/rootfs:x86-64` с установленным `nft`.
2. Установить зависимости: `opkg install dnsmasq-full curl iptables-nft nftables busybox httpd`.
3. Собрать пакет (`scripts/build_ipk.sh --arch aarch64_cortex-a53`) и установить его в rootfs.
4. Провести сценарии:
   - **Отсутствие интернета**: блокировать `ping`/`curl`, проверить сообщение об ошибке и очистку правил.
   - **Captive portal**: эмулировать редирект (локальный HTTP + DNAT), убедиться в запуске `busybox httpd`, генерации `dnsmasq.d/captive_intercept.conf` и корректной очистке.
   - **Переключение backend'ов**: прогнать `REQUESTED_FIREWALL_BACKEND=nftables` и `iptables`, сравнить `nft list ruleset` / `iptables-save` до и после остановки.
   - **Перезапуск Wi-Fi**: мок `ifup/ifdown` с задержкой получения IP, проверка тайм-аутов и повторной диагностики шлюза.
   - **fw4 reload**: после активации перехвата выполнить `fw4 reload` и проверить наличие таблицы `captive_monitor`, а также её автоматическое восстановление сервисом.
   - **IPv6**: при наличии SLAAC убедиться в добавлении и очистке IPv6 DNAT.

## 3. Полевые испытания на Xiaomi Mi Router AX3000T
1. **Подготовка**: прошивка OpenWrt 24.02, установка пакета из feed, настройка `uci` (реальные имена интерфейсов, интервалы, backend).
2. **Сценарии**:
   - `openwrt_captive_monitor --oneshot` при рабочем интернете — убедиться, что перехват не активируется.
   - **WAN down**: отключить интернет, отследить перезапуск Wi-Fi, переход в captive-режим, попытки health-check.
   - **Реальный captive portal**: подключиться к сети с авторизацией, проверить редирект, повторный доступ к сети и очистку правил.
   - **Перезапуск Wi-Fi/ifup**: `wifi down/up`, `ifdown/ifup` логического интерфейса, наблюдать стабильность сервиса.
   - **fw4 reload / firewall restart**: убедиться, что таблица `captive_monitor` и цепочки `CAPTIVE_*` не «залипают».
   - **IPv6**: с активной IPv6 подсетью проверить перехват и очистку IPv6 DNAT.
   - **Stress (12–24ч)**: мониторинг лога, `nft list ruleset`, `ps`, `top` на предмет утечек.
3. **Сбор артефактов**: `logread`, `dmesg`, `nft list ruleset`, `iptables-save`, `/tmp/dnsmasq.d/captive_intercept.conf`, `/tmp/captive_httpd/`.

## 4. Регрессия перед релизом
- Повторить локальные и эмуляционные проверки после каждой правки firewall/health-check/init.
- Выполнить чек-лист `docs/RELEASE_CHECKLIST.md`.
- Проверить `opkg files openwrt-captive-monitor` и отсутствие неожиданных модификаций в `/etc/config`.
- Убедиться, что `fw4 reload`, `service captive-monitor restart` и перезапуск устройства не оставляют активных правил или процессов.
