# Тест-план OpenWrt Captive Monitor (OpenWrt 24.x / filogic / Xiaomi Mi Router AX3000T)

> Полевой лаборатории нет — опираемся на статические проверки, эмуляцию OpenWrt и завершающие испытания на устройстве.

## 1. Локальные проверки (разработчик и CI)
- `shfmt -i 2 -ci -sr -d $(git ls-files '*.sh')` — проверка соответствия стилю из `.shfmt.conf`.
- `shellcheck -s sh <files>` — статический анализ всех shell-скриптов (скоро выполняется в GitHub Actions).
- `sh -n package/openwrt-captive-monitor/files/etc/init.d/captive-monitor` — синтаксическая проверка init-скрипта.
- `scripts/build_ipk.sh --arch aarch64_cortex-a53` — проверка сборки IPK и генерации `Packages/Packages.gz` (использовать моковые `nft/iptables` при отсутствии прав root).
- Юнит-/bats тесты для ключевых функций (mock бинарей `ip`, `nft`, `iptables`, `dnsmasq`, `curl`):
  - `detect_firewall_backend`, `setup_firewall_redirects_*`, `cleanup_firewall_redirects_*`.
  - `write_dnsmasq_intercept`, `ensure_lan_interface`, `restart_wifi_*` (с симуляцией задержек и таймаутов).
- Ручные вызовы `openwrt_captive_monitor --oneshot/--monitor` с подменой `PATH`, чтобы убедиться в корректном выводе ошибок при отсутствии зависимостей (`curl`, `busybox httpd`, `dnsmasq`).

## 2. Эмуляция OpenWrt 24.x (SDK/контейнер)
1. Развернуть rootfs OpenWrt 24.02 для целевой архитектуры (mediatek/filogic) в SDK или контейнере `openwrtorg/rootfs:x86-64` с установленными `nftables`, `iptables-nft`, `dnsmasq-full`, `curl`, `busybox httpd`.
2. Установить собранный IPK (`opkg install ./openwrt-captive-monitor_*.ipk`).
3. Прогнать сценарии:
   - **Рабочий интернет**: `openwrt_captive_monitor --oneshot`, убеждаемся, что captive-режим не активируется, таблицы nft пусты.
   - **WAN down / блокировка ICMP**: запретить `ping` или отключить маршрут до шлюза, наблюдать повторные попытки с экспоненциальным бэкоффом и корректные сообщения.
   - **Captive portal**: поднять локальный HTTP и сконфигурировать DNAT/DNS для редиректа, убедиться в запуске `busybox httpd`, генерации `dnsmasq.d/captive_intercept.conf` и корректной очистке после авторизации.
   - **Переключение backend'ов**: запуск с `REQUESTED_FIREWALL_BACKEND=nftables` и `iptables`, сравнить `nft list ruleset` / `iptables-save` до и после остановки.
   - **fw4 reload**: активировать сервис, выполнить `fw4 reload` и проверить, что таблица `captive_monitor`/цепочки `CAPTIVE_*` восстанавливаются автоматически.
   - **Аварийное завершение**: запустить сервис, затем `kill -9 <pid>` и проверить скриптом cleanup, что правила полностью убраны (`nft list ruleset`, `iptables-save`, наличие httpd/dnsmasq drop-in).
   - **IPv6 / dual-stack**: при наличии SLAAC проверить создание и очистку IPv6 DNAT, корректный выбор DNS.


## 3. Полевые испытания на Xiaomi Mi Router AX3000T
1. **Подготовка**: прошивка OpenWrt 24.02, установка пакета из feed, настройка UCI (`wifi_interface`, режимы, интервалы, backend).
2. **Сценарии**:
   - `openwrt_captive_monitor --oneshot` при рабочем интернете — убеждаемся, что перехват не активируется, правила не остаются.
   - **WAN down**: отключить интернет, ожидается перезапуск Wi‑Fi, активация captive-режима, корректный rollout при восстановлении канала.
   - **Реальный captive portal**: подключиться к сети с авторизацией (например, публичный хот-спот), проверить редирект, очищение правил и повторное подключение.
   - **Перезапуск Wi‑Fi вручную**: `wifi down/up`, `ifdown/ifup` логического интерфейса, убедиться, что сервис не теряет состояние и восстанавливает перехват при необходимости.
   - **fw4 reload / firewall restart**: запуск сервиса, затем `fw4 reload` и `service firewall restart` — убедиться в отсутствии дублированных правил и залипаний.
   - **IPv6**: при активной IPv6-подсети проверить поведение `ensure_lan_ipv6`, перехват и очистку IPv6 DNAT.
   - **Stress (12–24 ч)**: оставить сервис в monitor-режиме, отслеживая `logread`, `nft list ruleset`, `ps`, `top` на предмет утечек памяти и зомби-процессов.
3. **Сбор артефактов**: `logread`, `dmesg`, `nft list ruleset`, `iptables-save`, `/tmp/dnsmasq.d/captive_intercept.conf`, `/tmp/captive_httpd/`, статус UCI.

## 4. Регрессия перед релизом
- Повторить локальные и эмуляционные проверки после каждой правки firewall/health-check/init.
- Пройти чек-лист `docs/RELEASE_CHECKLIST.md` (версия, changelog, контроль зависимостей).
- Проверить `opkg files openwrt-captive-monitor` и отсутствие неожиданных модификаций в `/etc/config`/`/etc/init.d`.
- Убедиться, что `fw4 reload`, `service captive-monitor restart` и перезапуск устройства не оставляют активных правил или процессов.
- Провести smoke-тест `scripts/build_ipk.sh` в CI и вручную удостовериться, что пакет корректно устанавливается и удаляется (`opkg remove`).
