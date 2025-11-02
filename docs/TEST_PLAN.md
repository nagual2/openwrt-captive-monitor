# Тест-план OpenWrt Captive Monitor (OpenWrt 24.x / filogic / Xiaomi Mi Router AX3000T)

> Полевой лаборатории нет — опираемся на статические проверки, эмуляцию OpenWrt
> и завершающие испытания на устройстве.

## 1. Локальные проверки (разработчик и CI)

- `shfmt -i 2 -ci -sr -d $(git ls-files '*.sh')` — проверка стиля `.shfmt.conf`
- `shellcheck -s sh <files>` — статический анализ shell-скриптов
- `sh -n package/openwrt-captive-monitor/files/etc/init.d/captive-monitor` — проверка синтаксиса init-скрипта
- `scripts/build_ipk.sh --arch aarch64_cortex-a53` — проверка сборки IPK

### Тесты для ключевых функций

Используем mock бинарей `ip`, `nft`, `iptables`, `dnsmasq`, `curl`:

- `detect_firewall_backend`
- `setup_firewall_redirects_*`
- `cleanup_firewall_redirects_*`
- `write_dnsmasq_intercept`
- `ensure_lan_interface`
- `restart_wifi_*` (с симуляцией задержек и таймаутов)

### Проверка зависимостей

Ручные вызовы с подменой `PATH`:

```bash
openwrt_captive_monitor --oneshot
openwrt_captive_monitor --monitor
```

## 2. Эмуляция OpenWrt 24.x (SDK/контейнер)

1. **Настройка окружения**:
   - Развернуть rootfs OpenWrt 24.02 (mediatek/filogic)
   - Использовать контейнер `openwrtorg/rootfs:x86-64`
   - Установить зависимости:
     - `nftables`
     - `iptables-nft`
     - `dnsmasq-full`
     - `curl`
     - `busybox httpd`

2. **Установка пакета**:
   ```bash
   opkg install ./openwrt-captive-monitor_*.ipk
   ```

3. **Сценарии тестирования**:

   - **Рабочий интернет**:
     ```bash
     openwrt_captive_monitor --oneshot
     # Проверить, что captive-режим не активируется
     # Проверить, что таблицы nft пусты
     ```

   - **WAN down / блокировка ICMP**:
     ```bash
     # Запретить ping или отключить маршрут до шлюза
     # Проверить повторные попытки с экспоненциальным бэкоффом
     # Проверить корректность сообщений об ошибках
     ```

   - **Captive portal**:
     ```bash
     # Поднять локальный HTTP
     # Настроить DNAT/DNS для редиректа
     # Проверить запуск busybox httpd
     # Проверить генерацию dnsmasq.d/captive_intercept.conf
     # Проверить очистку после авторизации
     ```

   - **Переключение backend'ов**:
     ```bash
     # Запуск с разными бэкендами
     REQUESTED_FIREWALL_BACKEND=nftables openwrt_captive_monitor
     REQUESTED_FIREWALL_BACKEND=iptables openwrt_captive_monitor
     
     # Сравнить вывод
     nft list ruleset
     iptables-save
     ```

   - **fw4 reload**:
     ```bash
     # Активировать сервис
     /etc/init.d/captive-monitor start
     
     # Перезагрузить fw4
     fw4 reload
     
     # Проверить восстановление таблиц
     nft list ruleset
     ```

   - **Аварийное завершение**:
     ```bash
     # Запустить сервис
     /etc/init.d/captive-monitor start
     
     # Принудительно завершить
     kill -9 $(pgrep -f openwrt_captive_monitor)
     
     # Проверить очистку
     nft list ruleset
     iptables-save
     ```

   - **IPv6 / dual-stack**:
     ```bash
     # При наличии SLAAC
     # Проверить создание и очистку IPv6 DNAT
     # Проверить корректный выбор DNS
     ```


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
