# Статический анализ (shfmt + ShellCheck)

Дата проверки: 2024-10-24 (целевой релиз OpenWrt 24.x, filogic/AX3000T)

## Использованные команды

```sh
shellcheck -s sh \
  openwrt_captive_monitor.sh \
  init.d/captive-monitor \
  package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
  scripts/build_ipk.sh

shfmt -i 2 -ci -sr -d \
  openwrt_captive_monitor.sh \
  init.d/captive-monitor \
  package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
  package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
  scripts/build_ipk.sh
```

> Примечание: `shfmt` отсутствовал в базовой среде, установлен через `apt-get install shfmt`.

## ShellCheck (`-s sh`)

| Файл | Предупреждение | Кол-во | Класс | Рекомендация |
| --- | --- | --- | --- | --- |
| Все перечисленные скрипты | — | 0 | — | Все предупреждения устранены/подавлены. Поддерживать директиву `# shellcheck shell=ash` и адресные `disable` рядом с нестандартными конструкциями. |

ShellCheck в профиле POSIX `sh` не обнаружил проблем: в основном скрипте присутствует адресное подавление `SC3043` (использование `local` в ash), остальные предупреждения отсутствуют.

## shfmt (`-i 2 -ci -sr`)

| Файл | Симптом | Класс | Рекомендация |
| --- | --- | --- | --- |
| `openwrt_captive_monitor.sh` | Полное переиндентирование (4 → 2 пробела), выравнивание `if/fi`. | Minor (стиль) | При подтверждении общего стиля прогнать `shfmt -w` на тонком launcher'е. |
| `init.d/captive-monitor` | Различия в отступах `case`/`if`; предлагается 2-пробельный стиль. | Minor (стиль) | Автоформатирование после согласования стиля. |
| `package/.../etc/init.d/captive-monitor` | Смешанные отступы в блоках `procd_*`, лишние пробелы вокруг heredoc. | Minor (стиль) | Применить `shfmt` либо вручную привести к 2 пробелам. |
| `package/.../usr/sbin/openwrt_captive_monitor` | Массовое переиндентирование >1k строк, выравнивание heredoc и подстановок. | Major (объём изменений) | Разбить форматирование на отдельный PR после внедрения автоматизированных тестов, чтобы снизить риск регрессий. |
| `scripts/build_ipk.sh` | Приведение отступов к 2 пробелам, форматирование блоков `{ ... } > file`. | Minor (стиль) | Разрешить автоформатирование либо вручную синхронизировать стиль с `.shfmt.conf`. |

Пока формат кода держится на 4 пробелах, целесообразно зафиксировать договорённость в команде и запускать `shfmt -d` в CI (уже включено). Полное автоформатирование рекомендуется отложить до выделенного PR, чтобы упростить ревью и тестирование.
