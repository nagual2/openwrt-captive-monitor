# Планы тестирования

> Без реального маршрутизатора требуется комбинировать статические проверки, эмуляцию rootfs и последующие полевые испытания.

## 1. Локальные проверки (разработчик / CI)
- `shfmt -i 2 -ci -sr -d $(git ls-files '*.sh')` — контроль стиля (CI уже настроен).
- `shellcheck -s sh <files>` — статический анализ (CI уже настроен).
- `bats`/`shunit2`-скрипты для функций `setup_firewall_redirects_*`, `cleanup_captive_intercept`, `write_dnsmasq_intercept` (выполняются в контейнере с поддельными бинарями iptables/nft/dnsmasq).
- Локальный smoke-test `sh -n package/.../etc/init.d/captive-monitor`.

## 2. Эмуляция OpenWrt окружения
1. Сборка rootfs через `docker run --rm -it openwrtorg/rootfs:x86-64 /bin/sh` или OpenWrt SDK (`scripts/build_ipk.sh` → `qemu` rootfs).
2. Установка зависимостей внутри rootfs:
   - `opkg update && opkg install dnsmasq-full curl iptables-nft busybox` (для nft) / `iptables-legacy` (для legacy).
   - Развёртывание пакета `opkg install /tmp/openwrt-captive-monitor_*.ipk`.
3. Сценарии:
   - **Нет интернета**: заблокировать `ping`/`curl` (iptables DROP или подмена `/bin/ping`), убедиться что скрипт сообщает об ошибке, но корректно очищает перехват.
   - **Появление captive-портала**: запустить локальный HTTP-redirector (например `python3 -m http.server` с редиректом через iptables) и проверить, что busybox httpd поднимается, dnsmasq пишет `address=/#/`.
   - **Перезапуск Wi-Fi**: подменить `ifup/ifdown` скриптами, которые меняют флаг UP у тестового интерфейса, и убедиться в корректной обработке тайм-аутов (`MAX_WAIT_TIME`).
   - **Очистка правил**: после завершения скрипта проверить `iptables-save` / `nft list ruleset` на отсутствие цепочек `CAPTIVE_*`.
   - **Переключение backend'ов**: прогнать сценарий с `REQUESTED_FIREWALL_BACKEND=iptables` и `...=nftables`.

## 3. Полевые испытания на маршрутизаторе
1. **Подготовка**:
   - Установить пакет, включить сервис через `uci set captive-monitor.config.enabled=1; uci commit; /etc/init.d/captive-monitor enable && start`.
   - Настроить логирование (`logread -f`) для мониторинга.
2. **Сценарии**:
   - **Отсутствие интернета**: отключить WAN, убедиться в попытках перезапуска Wi-Fi и отсутствия «вечных» перехватов.
   - **Captive portal**: подключиться к публичной сети с авторизацией, убедиться в редиректе на портал и автоматическом снятии правил после успеха.
   - **Возвращение интернета**: восстановить WAN и проверить, что правила, dnsmasq-конфиг и httpd завершаются.
   - **Перезапуск Wi-Fi**: вручную `wifi down/up` во время мониторинга, убедиться что сервис корректно восстанавливается.
   - **Failover init**: `service captive-monitor restart` и `reload`, проверить что procd пересоздаёт инстанс без зомбирования.
   - **IPv6**: при наличии IPv6 в LAN убедиться, что IPv6-правила создаются и удаляются.
   - **Стресс**: длительный мониторинг (12-24 ч) с логированием, чтобы отследить утечки правил/процессов.
3. **Анализ логов**: собрать `/var/log/messages`, `logread`, `iptables-save`, `nft list ruleset`, `/tmp/dnsmasq.d/captive_intercept.conf` до и после тестов.

## 4. Регрессия перед релизом
- Повторить локальные и эмуляционные проверки.
- Прогнать чек-лист из `docs/RELEASE_CHECKLIST.md`.
- Сравнить `opkg files` установленного пакета с ожидаемым содержимым.
