# Backlog

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

## Backlog

### Iteration 1 — Stabilization and Compatibility
| Task | Priority | Estimate | Comments |
| --- | --- | --- | --- |
| Replace `resolveip -s` with a supported stack (nslookup/host + timeout control) | P0 | 0.5d | BusyBox doesn't support `-s`, which may cause captive portal IP detection to fail. Need to cover IPv4/IPv6 and fallback to system DNS. |
| Rewrite health-check: add HTTP/HTTPS probes, exponential backoff, and separate timeouts for gateway/internet | P0 | 1.5d | Will prevent infinite Wi-Fi restarts in networks with blocked ICMP and provide diagnostics for portals without explicit 204. |
| Strengthen integration with `fw4`/nftables and `iptables-nft` (backend selection, chain ordering, proper cleanup on `fw4 reload`) | P0 | 2d | Verify that the `captive_monitor` table is reinstated after `fw4 reload` and that iptables fallback works correctly with iptables-nft. |
| Improve init script: implement `depends()`, use `procd_kill` in `stop_service`, pass missing UCI variables | P1 | 0.5d | Prevents hanging processes and ensures proper service reload. |
| Automatic interface selection for Filogic (via `ubus network.wireless`, `network.lan.device`) and configuration validation | P1 | 1d | Default values (`phy1-sta0`/`wwan`) don't match AX3000T. Need verifiable defaults and clear error messages. |
| Dependency check at startup (`curl`, `busybox httpd`, `nft`, `iptables`, `dnsmasq`) with clear hints | P1 | 0.5d | Improves diagnostics for custom builds and prevents silent script failures. |
| Additional cleanup guards (restore iptables/nft rules on crash, protection against double calls) | P1 | 0.5d | Reduces risk of rule leaks after crashes or `kill -9`. |

### Iteration 2 — UX and Observability
| Task | Priority | Estimate | Comments |
| --- | --- | --- | --- |
| Extend UCI: health-check timeouts/intervals, HTTP port, firewall backend selection, IPv6 policy | P1 | 1d | Move values from environment variables, document defaults for 24.x. |
| Rework logging: levels (`info/warn/error`), `--syslog-only` flag, grouped output in monitor mode | P1 | 0.5d | Reduces noise in `logread` and eases maintenance. |
| Prepare HTML landing page (busybox httpd) and optional HTTPS (self-signed) | P1 | 1.5d | Improves UX for captive portal users. |
| `ubus` integration: export active state, backend, current timers, status change events | P2 | 1d | Enables LuCI and automation to display service status. |
| Document troubleshooting (fw4 reload, dnsmasq conflicts, mt76 specifics) and update README | P2 | 0.5d | Use test results and field trials. |
| Add whitelist/blacklist support for domains and MAC addresses in UCI | P2 | 1d | Simplifies setup for private networks with exceptions. |

### Iteration 3 — Packaging and CI/CD
| Task | Priority | Estimate | Comments |
| --- | --- | --- | --- |
| Extend CI: update workflow to run `scripts/build_ipk.sh --arch aarch64_cortex-a53` and publish artifacts | P1 | 1.5d | Ensures package builds for Filogic and provides IPK for testing. |
| Prepare OpenWrt 24.x container/SDK profile with mock tools (nft, dnsmasq, curl) for smoke tests | P1 | 2d | Enables captive/cleanup scenario testing without hardware. |
| Finalize code style: run `shfmt -w` across the repository (after test approval) | P1 | 1d | Minimal risk after test automation, clean diffs. |
| Add script/`bats` tests for firewall/dnsmasq and health-check functions | P2 | 1.5d | Cover critical scenarios (fw4 reload, dnsmasq rebuild, rule cleanup). |
| Automate releases: changelog, signing, deployment to opkg feed and GitHub Release | P2 | 1d | On top of `scripts/build_ipk.sh` and `docs/RELEASE_CHECKLIST.md`. |
| Prepare example configs for different scenarios (guest Wi-Fi, IPv6 hotspot, WAN-over-Cellular) | P2 | 0.5d | Simplifies deployment and speeds up field testing. |

---

<a name="русский"></a>
## Бэклог

### Итерация 1 — Стабилизация и совместимость
| Задача | Приоритет | Оценка | Комментарии |
| --- | --- | --- | --- |
| Заменить использование `resolveip -s` на поддерживаемый стек (nslookup/host + контроль времени ожидания) | P0 | 0.5d | BusyBox не поддерживает `-s`, из-за чего определение IP captive-портала может провалиться. Нужно покрыть IPv4/IPv6 и fallback на системный DNS. |
| Переписать health-check: добавить HTTP/HTTPS probes, экспоненциальный бэкофф и отдельные таймауты для gateway/internet | P0 | 1.5d | Исключит бесконечные перезапуски Wi‑Fi в сетях с заблокированным ICMP и обеспечит диагностику порталов без явного 204. |
| Укрепить интеграцию с `fw4`/nftables и `iptables-nft` (выбор backend, порядок цепочек, корректный cleanup при `fw4 reload`) | P0 | 2d | Проверить, что таблица `captive_monitor` переустанавливается после `fw4 reload`, а fallback на iptables корректно работает на iptables-nft. |
| Улучшить init-скрипт: реализовать `depends()`, использовать `procd_kill` в `stop_service`, пробрасывать недостающие UCI переменные | P1 | 0.5d | Предотвратит зависшие процессы и обеспечит корректную перезагрузку службы. |
| Автоматический выбор интерфейсов для Filogic (по `ubus network.wireless`, `network.lan.device`) и валидация конфигурации | P1 | 1d | Значения по умолчанию (`phy1-sta0`/`wwan`) не совпадают с AX3000T. Нужны проверяемые дефолты и понятные ошибки. |
| Проверка зависимостей при старте (`curl`, `busybox httpd`, `nft`, `iptables`, `dnsmasq`) с понятными подсказками | P1 | 0.5d | Улучшит диагностику кастомных сборок и избавит от немых падений скрипта. |
| Дополнительные guard'ы в cleanup (восстановление iptables/nft правил при краше, защита от двойного вызова) | P1 | 0.5d | Снизит риск утечек правил после аварийного завершения или `kill -9`. |

### Итерация 2 — UX и наблюдаемость
| Задача | Приоритет | Оценка | Комментарии |
| --- | --- | --- | --- |
| Расширить UCI: таймауты/интервалы health-check, HTTP порт, выбор firewall backend, политика IPv6 | P1 | 1d | Вынести значения из переменных окружения, документировать дефолты для 24.x. |
| Переработать логирование: уровни (`info/warn/error`), ключ `--syslog-only`, сгруппированный вывод в monitor-режиме | P1 | 0.5d | Снизит шум в `logread` и облегчит поддержку. |
| Подготовить HTML landing page (busybox httpd) и опциональный HTTPS (self-signed) | P1 | 1.5d | Улучшит UX пользователей captive порталов. |
| Интеграция с `ubus`: экспорт активного состояния, backend, текущих таймеров, событий смены статуса | P2 | 1d | Позволит LuCI и автоматизации показывать состояние сервиса. |
| Документировать troubleshooting (fw4 reload, dnsmasq конфликт, mt76 особенности) и обновить README | P2 | 0.5d | Использовать результаты тестов и полевых испытаний. |
| Добавить поддержу whitelist/blacklist доменов и MAC-адресов в UCI | P2 | 1d | Упростит настройку для частных сетей с исключениями. |

### Итерация 3 — Пакетирование и CI/CD
| Задача | Приоритет | Оценка | Комментарии |
| --- | --- | --- | --- |
| Расширить CI: существующий workflow дополнить запуском `scripts/build_ipk.sh --arch aarch64_cortex-a53` и публикацией артефактов | P1 | 1.5d | Гарантия, что пакет собирается для Filogic, и получение IPK для тестов. |
| Подготовить контейнер/SDK профиль OpenWrt 24.x с mock-инструментами (nft, dnsmasq, curl) для smoke-тестов | P1 | 2d | Позволит прогонять сценарии captive/cleanup без железа и ловить регрессии. |
| Финализировать стиль: прогнать `shfmt -w` по всему репозиторию (после утверждения тестов) | P1 | 1d | После автоматизации тестов риск минимален, diffs будут чистыми. |
| Добавить скриптовые/`bats` тесты для функций firewall/dnsmasq и health-check | P2 | 1.5d | Покрыть критические сценарии (fw4 reload, dnsmasq rebuild, чистка правил). |
| Автоматизировать релизы: changelog, подпись, выкладка в opkg feed и GitHub Release | P2 | 1d | Поверх `scripts/build_ipk.sh` и `docs/RELEASE_CHECKLIST.md`. |
| Подготовить набор примерных конфигов для разных сценариев (гостевой Wi-Fi, точка с IPv6, WAN-over-Cellular) | P2 | 0.5d | Упростит внедрение и ускорит полевые тесты. |
