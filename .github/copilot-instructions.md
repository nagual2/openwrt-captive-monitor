# Copilot Instructions for openwrt-captive-monitor

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

## English

### Project Overview

**openwrt-captive-monitor** is a lightweight OpenWrt service that detects captive portals and automatically redirects client traffic for authentication. It integrates with OpenWrt's networking stack (dnsmasq, iptables/nftables, procd) to intercept DNS/HTTP traffic and restore normal operation after successful authentication.

**Key Constraint**: IPv4-only (IPv6 support explicitly excluded by design).

---

## Architecture & Core Components

### Main Script Flow
- **Entry point**: `package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor` (shell script)
- **Operations Modes**:
  - `--monitor`: Continuous polling with configurable interval (default 60s)
  - `--oneshot`: Single check and exit (ideal for cron/systemd timers)

### Four Core Subsystems
1. **Connectivity Checker** - Validates gateway reachability and internet access via ping/HTTP probes
2. **Detection Engine** - Analyzes HTTP responses to identify captive portals (checks redirects, Location headers, response codes)
3. **Interception Manager** - Activates DNS hijacking (via dnsmasq drop-in) and HTTP redirection (via iptables/nftables NAT rules)
4. **Cleanup Manager** - Restores normal operation when internet access is restored (removes firewall rules, DNS overrides)

### Configuration Hierarchy
1. **UCI config** (`/etc/config/captive-monitor`) - Primary, persistent storage
2. **Environment variables** - Override UCI at runtime (e.g., `MONITOR_INTERVAL=30`)
3. **CLI arguments** - Override both (e.g., `--monitor`, `--oneshot`)

Configuration is loaded in `load_config()` function within the init script.

---

## Critical Developer Workflows

### Building & Testing

**Local IPK build (no SDK required)**:
```bash
scripts/build_ipk.sh --arch all
# Output: dist/opkg/all/openwrt-captive-monitor_*.ipk
```

**Unit tests**:
```bash
make test  # Runs tests/run.sh with busybox ash
```

**Linting**:
```bash
make lint-shell   # shellcheck validation
make format       # shfmt formatting
```

**VM-based end-to-end testing** (automated provisioning, installation, smoke tests):
```bash
./scripts/run_openwrt_vm.sh
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm  # CI-friendly (TCG fallback)
```

### Package Structure
- **Control files** reside in `package/openwrt-captive-monitor/files/`
- **Init script** (`etc/init.d/captive-monitor`) uses procd for service management
- **Default config** (`etc/config/captive-monitor`) includes all UCI options with English/Russian comments
- **Post-install hook** (`etc/uci-defaults/99-captive-monitor`) runs after package install
- **Cleanup hooks** (prerm, postrm) in package Makefile remove firewall rules and temp files

### Version & Release
- **Version format**: `YYYY.M.D.N` (date-based, e.g., `2025.11.28.6`)
- **Files to update**: `VERSION` root file, `PKG_VERSION` in `package/openwrt-captive-monitor/Makefile`
- **Release workflow**: Manual GitHub Actions workflow (see `.github/workflows/manual-release.yml`)
- **Git tags**: Format `vYYYY.M.D.N` (with leading `v`)

---

## Project-Specific Patterns & Conventions

### Shell Script Conventions
- **Shebang**: `#!/bin/sh` for POSIX compatibility (must run on busybox ash)
- **ShellCheck**: Used throughout (`shellcheck shell=ash` directives)
- **Formatting**: `shfmt -i 4 -ci -sr` (4-space indent, compound statement indent, space in function parens)
- **Error handling**: `set -eu` at script start (exit on error, undefined variables fail)
- **Temporary files**: Use `mktemp /tmp/prefix.XXXXXX` with cleanup in trap handlers

### Captive Portal Detection Logic
- **Detection URLs**: Hardcoded defaults include Google Connectivity Check and Firefox detection URLs
- **Portal URL extraction**: Analyzes HTTP Location headers and HTML href attributes to find login URL
- **Multiple detection methods**: Tries multiple URLs, uses first successful redirect
- **Critical function**: `detect_captive_portal()` - extracts `CAPTIVE_PORTAL_URL` and `CAPTIVE_PORTAL_HOST`

### Firewall Backend Abstraction
- **Auto-detection**: Probes for nftables (OpenWrt 23.05+) vs iptables (legacy)
- **Chain names**: Configurable via environment (`CAPTIVE_NAT_CHAIN`, `CAPTIVE_DNS_CHAIN` for iptables; `NFT_TABLE_NAME` for nftables)
- **Rules creation**: Separate functions for iptables and nftables implementations
- **Set `-eu` before any exec** to catch missing dependencies early

### DNS Hijacking Pattern
- Creates dnsmasq drop-in config: `/tmp/dnsmasq.d/captive_intercept.conf`
- Syntax: `address=/*.domain.com/router-ip` (wildcards match all subdomains)
- Preserves portal domain to allow authentication: excludes portal's hostname from hijacking
- Reload via: `/etc/init.d/dnsmasq reload`

### HTTP Interception Pattern
- Starts busybox httpd on port 80 (redirect destination)
- Creates HTML response that redirects to detected portal URL
- Injects firewall NAT rules: `iptables -t nat -A CAPTIVE_HTTP_REDIRECT -j REDIRECT --to-port 80`
- Cleanup removes rules and kills httpd process

---

## Integration Points & Dependencies

### Runtime Dependencies
- **dnsmasq**: DNS interception (configure via drop-in files in `/tmp/dnsmasq.d/`)
- **iptables/nftables**: Traffic redirection (firewall rules)
- **curl**: HTTP probes for detection (must support `-I` for headers-only requests)
- **busybox**: ash shell, httpd (web server), basic utilities
- **procd**: Service supervision, automatic restart on failure

### System Integration
- **Init system**: Controlled via `/etc/init.d/captive-monitor` (OpenWrt rc.common framework)
- **Logging**: Uses `logger` command to write to syslog (tag: `captive-monitor`)
- **Network interfaces**: Auto-detects WiFi interface from uci/environment, validates via `ip link` or `iwconfig`
- **State files**: Temporary state in `/tmp/`, config in `/etc/config/`

### Service Lifecycle
- **Start**: procd spawns main script in monitor mode (or oneshot depending on config)
- **Respawn**: procd automatically restarts on crash (if enabled)
- **Stop**: Calls cleanup to remove all interception rules
- **Disable**: Removes init script symlink from `/etc/rc.d/`

---

## Key Files & Their Roles

| Path | Purpose |
|------|---------|
| `package/openwrt-captive-monitor/Makefile` | OpenWrt SDK package definition (PKG_VERSION, dependencies, install rules) |
| `package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor` | Main script (logic, detection, interception) |
| `package/openwrt-captive-monitor/files/etc/init.d/captive-monitor` | Init script (procd config, service management) |
| `package/openwrt-captive-monitor/files/etc/config/captive-monitor` | Default UCI config |
| `package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor` | Post-install hook |
| `tests/run.sh` | Test harness (unit tests with mocking) |
| `scripts/build_ipk.sh` | Standalone IPK builder (no SDK required) |
| `scripts/run_openwrt_vm.sh` | VM provisioning & testing (QEMU/KVM) |
| `docs/guides/architecture.md` | Detailed component & data flow documentation |
| `README.md` | User-facing documentation (installation, configuration, usage) |

---

## Common Modification Patterns

### Adding a New Configuration Option
1. Add option name to `load_config()` in init script (e.g., `config_get my_option config my_option ""`)
2. Update default value in main script (e.g., `CUSTOM_VAR="${my_option:-default_value}"`)
3. Document in `/etc/config/captive-monitor` template with comments
4. Update `docs/configuration/reference.md` with full description

### Extending Detection Methods
- Modify `detect_captive_portal()` function
- Add new detection URLs to `CAPTIVE_CHECK_URLS` config option
- Update `extract_portal_url_from_response()` to handle new HTML patterns
- Add corresponding unit tests in `tests/run.sh`

### Adding Firewall Rules
- Create separate functions for iptables and nftables (check `FIREWALL_BACKEND` variable)
- Use `setup_firewall_iptables()` and `setup_firewall_nftables()` patterns
- Always create cleanup counterpart (e.g., `cleanup_firewall_iptables()`)
- Test both backends: run tests with `FIREWALL_BACKEND=iptables` and `FIREWALL_BACKEND=nftables`

---

## Testing Strategy

### Unit Tests
- Located in `tests/run.sh`
- Uses mock binaries in `tests/mocks/` (dnsmasq, iptables, curl, etc.)
- Captures all command invocations in `tests/_out/commands.log`
- Run locally: `make test` or `busybox ash tests/run.sh`

### Integration Tests
- VM-based testing via `./scripts/run_openwrt_vm.sh`
- Automatically provisions OpenWrt VM, installs package, runs smoke tests
- Supports multiple OpenWrt versions (23.05, 24.10, etc.)
- Useful for testing firewall backend detection, procd behavior, full package lifecycle

### CI/CD Workflows
- **`.github/workflows/ci.yml`**: Runs unit tests on every push
- **`.github/workflows/openwrt-build.yml`**: Builds package using official SDK
- **`.github/workflows/release-please.yml`**: Automated version bumping and changelog
- **`.github/workflows/security-scanning.yml`**: Security checks (ShellCheck, etc.)

---

## Common Gotchas

1. **IPv6 Handling**: Explicitly NOT supported. All IPv6 logic should be ignored/disabled. Config options with `ipv6` in the name are typically no-ops.

2. **Shell Portability**: Must work with busybox ash (stripped-down POSIX shell). Avoid bash-isms:
   - No `[[...]]` (use `[...]`)
   - No `$(...)` command substitution in certain contexts (prefer backticks if issues arise)
   - No `${var/pattern/repl}` parameter expansion (use `sed`)
   - Test with `shellcheck --shell=ash`

3. **Firewall Backend Detection**: Must probe at runtime because OpenWrt versions vary. Check for nftables binary first, fallback to iptables. Don't hardcode backend choice.

4. **Temporary File Cleanup**: Always use trap to cleanup temp files on exit:
   ```bash
   trap 'rm -f "$temp_file"' EXIT
   ```

5. **DNS Caching**: After modifying dnsmasq drop-in, must call `/etc/init.d/dnsmasq reload`. Restart isn't necessary (slower).

6. **HTTP Server Port 80**: If port is already in use, interception fails silently. Check with `netstat -tln` or `ss -tln` before starting httpd.

7. **Package Version Format**: Use date-based versioning (`YYYY.M.D.N`). If you create a release on 2025-11-28, use `2025.11.28.1` (or increment `N` if multiple releases same day).

---

## Resources for Further Learning

- **Architecture Guide**: `docs/guides/architecture.md` - Deep dive into components, data flow, security model
- **Configuration Reference**: `docs/configuration/reference.md` - All UCI options with defaults
- **Captive Portal Walkthrough**: `docs/guides/captive-portal-walkthrough.md` - Step-by-step detection & interception flow
- **Test Plan**: `docs/project/test-plan.md` - Comprehensive test strategy and scenarios
- **OpenWrt Documentation**: https://openwrt.org/docs - Official UCI, firewall, dnsmasq docs

---

# Русский

### Обзор проекта

**openwrt-captive-monitor** — это лёгкий сервис OpenWrt, который обнаруживает captive portals и автоматически перенаправляет трафик клиентов для аутентификации. Интегрируется со стеком сетей OpenWrt (dnsmasq, iptables/nftables, procd) для перехвата DNS/HTTP трафика и восстановления нормальной работы после успешной аутентификации.

**Ключевое ограничение**: только IPv4 (поддержка IPv6 явно исключена по дизайну).

---

## Архитектура и основные компоненты

### Поток основного скрипта
- **Точка входа**: `package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor` (shell script)
- **Режимы работы**:
  - `--monitor`: Непрерывный опрос с настраиваемым интервалом (по умолчанию 60с)
  - `--oneshot`: Однократная проверка и выход (идеально для cron/systemd таймеров)

### Четыре основные подсистемы
1. **Проверка подключения** - Проверяет доступность шлюза и доступ в интернет через ping/HTTP пробы
2. **Двигатель обнаружения** - Анализирует HTTP ответы для обнаружения captive portals (проверяет редиректы, Location headers, коды ответов)
3. **Менеджер перехвата** - Активирует DNS hijacking (через dnsmasq drop-in) и HTTP перенаправление (через iptables/nftables NAT правила)
4. **Менеджер очистки** - Восстанавливает нормальную работу при восстановлении доступа в интернет (удаляет правила firewall, DNS переопределения)

### Иерархия конфигурации
1. **UCI config** (`/etc/config/captive-monitor`) - Первичное, постоянное хранилище
2. **Переменные окружения** - Переопределяют UCI во время выполнения (напр., `MONITOR_INTERVAL=30`)
3. **Аргументы CLI** - Переопределяют оба варианта (напр., `--monitor`, `--oneshot`)

Конфигурация загружается в функцию `load_config()` в init скрипте.

---

## Критичные рабочие процессы разработки

### Сборка и тестирование

**Локальная сборка IPK (SDK не требуется)**:
```bash
scripts/build_ipk.sh --arch all
# Output: dist/opkg/all/openwrt-captive-monitor_*.ipk
```

**Юнит-тесты**:
```bash
make test  # Запускает tests/run.sh с busybox ash
```

**Проверка кода**:
```bash
make lint-shell   # Проверка shellcheck
make format       # Форматирование shfmt
```

**Тестирование e2e на ВМ** (автоматическое развёртывание, установка, smoke тесты):
```bash
./scripts/run_openwrt_vm.sh
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm  # CI-friendly (TCG резервный вариант)
```

### Структура пакета
- **Файлы управления** находятся в `package/openwrt-captive-monitor/files/`
- **Init скрипт** использует procd для управления сервисом
- **Конфиг по умолчанию** включает все UCI опции с комментариями на английском/русском
- **Hook после установки** запускается после установки пакета
- **Hooks очистки** удаляют firewall правила и временные файлы

### Версия и выпуск
- **Формат версии**: `YYYY.M.D.N` (дата-based, напр., `2025.11.28.6`)
- **Файлы для обновления**: `VERSION` root file, `PKG_VERSION` в `package/openwrt-captive-monitor/Makefile`
- **Workflow выпуска**: Ручной GitHub Actions workflow (см. `.github/workflows/manual-release.yml`)
- **Git tags**: Формат `vYYYY.M.D.N` (с ведущей `v`)

---

## Специфичные для проекта паттерны и соглашения

### Соглашения Shell скриптов
- **Shebang**: `#!/bin/sh` для POSIX совместимости (должен работать на busybox ash)
- **ShellCheck**: Используется везде (`shellcheck shell=ash` директивы)
- **Форматирование**: `shfmt -i 4 -ci -sr` (4-пробел отступ, составной оператор отступ, пробел в скобках функции)
- **Обработка ошибок**: `set -eu` в начале скрипта (выход при ошибке, неопределённые переменные вызывают ошибку)
- **Временные файлы**: Используйте `mktemp /tmp/prefix.XXXXXX` с очисткой в trap handlers

### Логика обнаружения captive portal
- **Detection URLs**: Жёстко закодированные defaults включают Google Connectivity Check и Firefox detection URLs
- **Извлечение URL портала**: Анализирует HTTP Location headers и HTML href атрибуты для поиска login URL
- **Множество методов обнаружения**: Пробует несколько URL, использует первый успешный редирект
- **Критичная функция**: `detect_captive_portal()` - извлекает `CAPTIVE_PORTAL_URL` и `CAPTIVE_PORTAL_HOST`

### Абстракция firewall backend
- **Автоопределение**: Проверяет наличие nftables (OpenWrt 23.05+) vs iptables (legacy)
- **Имена цепей**: Настраиваются через environment (`CAPTIVE_NAT_CHAIN`, `CAPTIVE_DNS_CHAIN` для iptables; `NFT_TABLE_NAME` для nftables)
- **Создание правил**: Отдельные функции для реализаций iptables и nftables
- **Установите `-eu` перед любым exec** для раннего обнаружения отсутствующих зависимостей

### Паттерн DNS hijacking
- Создаёт dnsmasq drop-in конфиг: `/tmp/dnsmasq.d/captive_intercept.conf`
- Синтаксис: `address=/*.domain.com/router-ip` (wildcards совпадают со всеми поддоменами)
- Сохраняет домен портала для разрешения аутентификации: исключает hostname портала из hijacking
- Перезагрузка через: `/etc/init.d/dnsmasq reload`

### Паттерн HTTP interception
- Запускает busybox httpd на порту 80 (пункт назначения редиректа)
- Создаёт HTML ответ, который перенаправляет на обнаруженный portal URL
- Вводит firewall NAT правила: `iptables -t nat -A CAPTIVE_HTTP_REDIRECT -j REDIRECT --to-port 80`
- Очистка удаляет правила и завершает процесс httpd

---

## Точки интеграции и зависимости

### Зависимости во время выполнения
- **dnsmasq**: DNS перехват (конфигурируется через drop-in файлы в `/tmp/dnsmasq.d/`)
- **iptables/nftables**: Перенаправление трафика (firewall правила)
- **curl**: HTTP пробы для обнаружения (должен поддерживать `-I` для request-only запросов)
- **busybox**: ash shell, httpd (web server), основные утилиты
- **procd**: Надзор сервисом, автоматический перезапуск при сбое

### Интеграция с системой
- **Init система**: Управляется через `/etc/init.d/captive-monitor` (OpenWrt rc.common фреймворк)
- **Логирование**: Использует `logger` команду для записи в syslog (tag: `captive-monitor`)
- **Network interfaces**: Автоматически определяет WiFi интерфейс из uci/environment, проверяет через `ip link` или `iwconfig`
- **State files**: Временное состояние в `/tmp/`, конфиг в `/etc/config/`

### Жизненный цикл сервиса
- **Start**: procd запускает основной скрипт в monitor режиме (или oneshot в зависимости от конфига)
- **Respawn**: procd автоматически перезапускает при сбое (если включено)
- **Stop**: Вызывает cleanup для удаления всех правил перехвата
- **Disable**: Удаляет init script symlink из `/etc/rc.d/`

---

## Ключевые файлы и их роли

| Путь | Назначение |
|------|---------|
| `package/openwrt-captive-monitor/Makefile` | Определение пакета OpenWrt SDK (PKG_VERSION, зависимости, правила установки) |
| `package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor` | Основной скрипт (логика, обнаружение, перехват) |
| `package/openwrt-captive-monitor/files/etc/init.d/captive-monitor` | Init скрипт (конфиг procd, управление сервисом) |
| `package/openwrt-captive-monitor/files/etc/config/captive-monitor` | Default UCI конфиг |
| `package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor` | Hook после установки |
| `tests/run.sh` | Тестовая инфраструктура (юнит-тесты с mocking) |
| `scripts/build_ipk.sh` | Standalone IPK builder (SDK не требуется) |
| `scripts/run_openwrt_vm.sh` | Подготовка ВМ и тестирование (QEMU/KVM) |
| `docs/guides/architecture.md` | Подробная документация компонентов и data flow |
| `README.md` | Документация для пользователей (установка, конфиг, использование) |

---

## Частые паттерны модификаций

### Добавление новой конфиг-опции
1. Добавьте имя опции в функцию `load_config()` в init скрипте (e.g., `config_get my_option config my_option ""`)
2. Обновите значение по умолчанию в основном скрипте (e.g., `CUSTOM_VAR="${my_option:-default_value}"`)
3. Документируйте в шаблоне `/etc/config/captive-monitor` с комментариями
4. Обновите `docs/configuration/reference.md` с полным описанием

### Расширение методов обнаружения
- Измените функцию `detect_captive_portal()`
- Добавьте новые URL обнаружения в опцию `CAPTIVE_CHECK_URLS`
- Обновите `extract_portal_url_from_response()` для обработки новых HTML паттернов
- Добавьте соответствующие юнит-тесты в `tests/run.sh`

### Добавление firewall правил
- Создайте отдельные функции для iptables и nftables (проверьте переменную `FIREWALL_BACKEND`)
- Используйте паттерны `setup_firewall_iptables()` и `setup_firewall_nftables()`
- Всегда создавайте функцию очистки (напр., `cleanup_firewall_iptables()`)
- Тестируйте оба бэкэнда: запустите тесты с `FIREWALL_BACKEND=iptables` и `FIREWALL_BACKEND=nftables`

---

## Стратегия тестирования

### Юнит-тесты
- Расположены в `tests/run.sh`
- Используются mock binaries в `tests/mocks/` (dnsmasq, iptables, curl, и т.д.)
- Записывает все вызовы команд в `tests/_out/commands.log`
- Запустите локально: `make test` или `busybox ash tests/run.sh`

### Интеграционные тесты
- VM-based тестирование через `./scripts/run_openwrt_vm.sh`
- Автоматически подготавливает OpenWrt ВМ, устанавливает пакет, запускает smoke тесты
- Поддерживает несколько версий OpenWrt (23.05, 24.10, и т.д.)
- Полезно для тестирования обнаружения firewall бэкэнда, поведения procd, полного жизненного цикла пакета

### CI/CD Workflows
- **`.github/workflows/ci.yml`**: Запускает юнит-тесты при каждом push
- **`.github/workflows/openwrt-build.yml`**: Собирает пакет с помощью официального SDK
- **`.github/workflows/release-please.yml`**: Автоматическое обновление версии и changelog
- **`.github/workflows/security-scanning.yml`**: Проверки безопасности (ShellCheck, и т.д.)

---

## Типичные ошибки и подводные камни

1. **Обработка IPv6**: Явно НЕ поддерживается. Вся логика IPv6 должна игнорироваться/отключаться. Конфиг-опции с `ipv6` в имени — типичные no-ops.

2. **Портативность Shell**: Должен работать с busybox ash (урезанный POSIX shell). Избегайте bash-измов:
   - Нет `[[...]]` (используйте `[...]`)
   - Нет `$(...)` command substitution в некоторых контекстах (предпочитайте backticks при проблемах)
   - Нет `${var/pattern/repl}` параметрической экспансии (используйте `sed`)
   - Тестируйте с помощью `shellcheck --shell=ash`

3. **Обнаружение Firewall Backend**: Должно проверяться во время выполнения, так как версии OpenWrt различаются. Проверьте бинарный файл nftables первым, вернитесь к iptables. Не жёстко кодируйте выбор бэкэнда.

4. **Очистка временных файлов**: Всегда используйте trap для очистки временных файлов при выходе:
   ```bash
   trap 'rm -f "$temp_file"' EXIT
   ```

5. **DNS кеширование**: После изменения dnsmasq drop-in, необходимо вызвать `/etc/init.d/dnsmasq reload`. Перезагрузка не требуется (медленнее).

6. **HTTP сервер порт 80**: Если порт уже занят, перехват не удаётся молча. Проверьте с помощью `netstat -tln` или `ss -tln` перед запуском httpd.

7. **Формат версии пакета**: Используйте дата-based версионирование (`YYYY.M.D.N`). Если вы создаёте выпуск 28 ноября 2025 г., используйте `2025.11.28.1` (или увеличьте `N`, если несколько выпусков в один день).

---

## Ресурсы для дальнейшего обучения

- **Architecture Guide**: `docs/guides/architecture.md` - Глубокое погружение в компоненты, data flow, модель безопасности
- **Configuration Reference**: `docs/configuration/reference.md` - Все UCI опции со значениями по умолчанию
- **Captive Portal Walkthrough**: `docs/guides/captive-portal-walkthrough.md` - Пошаговое обнаружение и flow перехвата
- **Test Plan**: `docs/project/test-plan.md` - Комплексная стратегия тестирования и сценарии
- **OpenWrt Documentation**: https://openwrt.org/docs - Официальная документация UCI, firewall, dnsmasq
