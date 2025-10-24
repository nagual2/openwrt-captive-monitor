# Статический анализ (ShellCheck + shfmt)

Дата проверки: 2024-10-24 (целевой релиз OpenWrt 24.x / mediatek-filogic / AX3000T)

## Использованные команды

```sh
shellcheck -s sh \
  openwrt_captive_monitor.sh \
  init.d/captive-monitor \
  package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
  package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
  scripts/build_ipk.sh

shfmt -i 2 -ci -sr -d \
  openwrt_captive_monitor.sh \
  init.d/captive-monitor \
  package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
  package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
  scripts/build_ipk.sh
```

> В окружении отсутствовали `shellcheck` и `shfmt`; установлены через `sudo apt-get install shellcheck shfmt`.

## ShellCheck (`-s sh`)

| Файл | Правило | Класс | Статус / предложенный фикс | Комментарий |
| --- | --- | --- | --- | --- |
| `package/.../etc/init.d/captive-monitor` | SC2034 (`START/STOP/USE_PROCD` кажутся неиспользуемыми) | Minor | Добавлена директива `# shellcheck disable=SC2034` с пояснением, что значения считывает `/etc/rc.common`. | Ложноположительное предупреждение, устранено.
| `package/.../etc/init.d/captive-monitor` | SC2154 (`enabled` может быть неинициализирован) | Minor | Перед вызовами `config_get*` переменные инициализируются значениями по умолчанию. | Делает намерение очевидным и защищает от будущих рефакторингов.
| `package/.../etc/init.d/captive-monitor` | SC1091 (невозможно прочитать `/lib/functions.sh`) | Minor | Добавлена директива `# shellcheck disable=SC1091` с пояснением про рантайм procd. | Без железа файл недоступен, достаточно документированного подавления.
| `package/.../etc/init.d/captive-monitor` | SC3043 (`local` вне POSIX) | Minor | Переписан код без `local`, глобальные переменные контролируются вручную. | Повышает совместимость с `/bin/sh` даже вне ash.
| `scripts/build_ipk.sh` | SC2129 (несколько `>>` подряд) | Minor | Запись в `Packages` сгруппирована в один блок `{ ... } >> file`. | Снижает шум в diffs и соответствует рекомендации ShellCheck.
| `scripts/build_ipk.sh` | SC3043 (`local`) | Minor | Оставлено целевое подавление в заголовке: скрипт выполняется под ash/bash. Альтернатива — переписать функции без `local`. | Рекомендация для будущего улучшения, текущее подавление документировано.

После перечисленных корректировок повторный прогон `shellcheck -s sh` проходит без предупреждений.

## shfmt (`-i 2 -ci -sr`)

shfmt формирует суммарный дифф ~2 678 строк. Основные наблюдения:

| Файл | Симптом | Класс | Предложение |
| --- | --- | --- | --- |
| `openwrt_captive_monitor.sh` | Автоформатирование меняет отступы (4 → 2 пробела) и выравнивает `if/fi`. | Minor | Лончер можно отформатировать сразу после утверждения стиля (низкий риск).
| `init.d/captive-monitor` | Те же изменения по отступам и пробелам вокруг перенаправлений. | Minor | Применить `shfmt -w` после согласования 2‑пробельного стиля.
| `package/.../etc/init.d/captive-monitor` | Выравнивание `case`/`procd_*` блоков. | Minor | Можно отформатировать вместе с функциональными правками init-скрипта.
| `package/.../usr/sbin/openwrt_captive_monitor` | Массовое переиндентирование >1k строк, затрагивает heredoc и вложенные `case`. | Major | Вынести форматирование в отдельный PR после появления автоматических тестов и/или snapshot ruleset, чтобы облегчить ревью.
| `scripts/build_ipk.sh` | Приведение отступов к 2 пробелам, выравнивание блоков `{ ... }`. | Minor | Можно прогнать `shfmt` сразу после утверждения стиля в `.shfmt.conf`.

## Рекомендации
- Зафиксировать договорённость о 2‑пробельном стиле (`.shfmt.conf` уже лежит в корне) и включить `shfmt -d` в CI (workflow `shellcheck.yml` делает это).
- Перед массовым форматированием основного скрипта обеспечить автоматические тесты (минимум — скриптовые mocks для nft/iptables/dnsmasq) и обновить тест-план.
- Поддерживать адресные директивы ShellCheck рядом с местами использования, чтобы будущие изменения не возвращали ложноположительные предупреждения.
