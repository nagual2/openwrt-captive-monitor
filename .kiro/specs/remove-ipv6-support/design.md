# Design Document

## Overview

Данный дизайн описывает процесс удаления поддержки IPv6 из проекта openwrt-captive-monitor. Удаление будет выполнено систематически, затрагивая код, документацию, тесты и конфигурацию, при этом сохраняя системные настройки IPv6 на роутере нетронутыми.

Основные принципы:
- Удалить весь код, связанный с IPv6
- Не изменять системные настройки IPv6 роутера
- Упростить кодовую базу
- Сохранить обратную совместимость (игнорировать старые IPv6 параметры)
- Обновить документацию

## Architecture

### Текущая архитектура с IPv6

```
┌─────────────────────────────────────────┐
│   openwrt_captive_monitor.sh            │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ IPv4 Support │  │ IPv6 Support │   │
│  │              │  │              │   │
│  │ - LAN_IP     │  │ - LAN_IPV6   │   │
│  │ - iptables   │  │ - ip6tables  │   │
│  │ - IPv4 DNS   │  │ - IPv6 DNS   │   │
│  │ - httpd IPv4 │  │ - httpd IPv6 │   │
│  └──────────────┘  └──────────────┘   │
│         │                  │            │
│         └──────────┬───────┘            │
│                    │                    │
│              ┌─────▼─────┐              │
│              │  Router   │              │
│              │  Config   │              │
│              └───────────┘              │
└─────────────────────────────────────────┘
```

### Целевая архитектура без IPv6

```
┌─────────────────────────────────────────┐
│   openwrt_captive_monitor.sh            │
│                                         │
│  ┌──────────────┐                      │
│  │ IPv4 Support │                      │
│  │              │                      │
│  │ - LAN_IP     │                      │
│  │ - iptables   │                      │
│  │ - IPv4 DNS   │                      │
│  │ - httpd IPv4 │                      │
│  └──────────────┘                      │
│         │                               │
│         │                               │
│         │                               │
│    ┌────▼────┐                          │
│    │ Router  │                          │
│    │ Config  │                          │
│    │ (IPv6   │                          │
│    │ intact) │                          │
│    └─────────┘                          │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### Компоненты для удаления

#### 1. Переменные IPv6

**Файл:** `usr/sbin/openwrt_captive_monitor` или `openwrt_captive_monitor.sh`

Переменные для удаления:
- `LAN_IPV6` - IPv6 адрес LAN интерфейса
- `HTTPD_IPV6_READY` - флаг готовности HTTP сервера для IPv6

#### 2. Функции IPv6

Функции для удаления:
- `ensure_lan_ipv6()` - определение IPv6 адреса LAN интерфейса
- `resolve_portal_ipv6()` - разрешение IPv6 адреса портала
- `is_ipv6()` - проверка, является ли адрес IPv6 (в awk скрипте)

#### 3. Логика IPv6 в существующих функциях

Блоки кода для удаления:
- Чтение `lan_ipv6` из UCI конфигурации
- Запуск busybox httpd с `[::]` (IPv6 wildcard)
- Создание правил ip6tables для HTTP перехвата
- Создание правил ip6tables для DNS перехвата
- Добавление IPv6 адресов в dnsmasq конфигурацию
- Разрешение IPv6 адресов captive порталов

#### 4. Логирование IPv6

Сообщения для удаления/изменения:
- "Запущен busybox httpd (PID $pid) для редиректа (IPv4/IPv6)" → "Запущен busybox httpd (PID $pid) для редиректа"
- "Не удалось запустить busybox httpd с IPv6, пробуем только IPv4" → удалить
- Все предупреждения об ip6tables
- Все предупреждения об отсутствии IPv6 адресов

### Компоненты для сохранения

#### 1. Системные настройки IPv6

**НЕ изменять:**
- `network.lan.ip6addr` в UCI
- IPv6 адреса на интерфейсах
- Существующие правила ip6tables других сервисов
- DHCPv6 настройки
- IPv6 routing

#### 2. IPv4 функциональность

**Сохранить без изменений:**
- `ensure_lan_ip()` - определение IPv4 адреса
- `ensure_lan_interface()` - определение LAN интерфейса
- Все iptables правила для IPv4
- HTTP сервер на IPv4
- DNS перехват для IPv4

## Data Models

### Конфигурация UCI (до удаления)

```
config captive_monitor 'config'
    option enabled '1'
    option lan_interface 'br-lan'
    option lan_ip '192.168.1.1'
    option lan_ipv6 'fd00::1'  # Будет удалено
    option firewall_backend 'auto'
```

### Конфигурация UCI (после удаления)

```
config captive_monitor 'config'
    option enabled '1'
    option lan_interface 'br-lan'
    option lan_ip '192.168.1.1'
    # lan_ipv6 удалена из документации
    # но если присутствует в конфигурации, будет игнорироваться
    option firewall_backend 'auto'
```

### Переменные окружения (до удаления)

```bash
LAN_INTERFACE="br-lan"
LAN_IP="192.168.1.1"
LAN_IPV6="fd00::1"           # Удалить
HTTPD_IPV6_READY=0           # Удалить
```

### Переменные окружения (после удаления)

```bash
LAN_INTERFACE="br-lan"
LAN_IP="192.168.1.1"
# Только IPv4 переменные
```

## C
orrectness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

На основе prework анализа, большинство acceptance criteria являются статическими проверками (examples), а не универсальными свойствами. Однако мы можем определить несколько comprehensive properties:

### Property 1: Code IPv6 Absence

*For any* source code file in the project, the file should not contain any IPv6-related identifiers (LAN_IPV6, HTTPD_IPV6_READY, ensure_lan_ipv6, resolve_portal_ipv6, is_ipv6, ip6tables, lan_ipv6)

**Validates: Requirements 1.1, 1.2, 1.4, 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 2: Documentation IPv6 Absence

*For any* documentation file (README, guides, examples), the file should not contain IPv6 configuration examples or instructions, except for explicit statement that IPv6 is not supported

**Validates: Requirements 4.1, 4.2, 4.3, 8.2, 8.3**

### Property 3: Log Messages IPv6 Absence

*For any* log message generated by the system, the message should not mention IPv6, ip6tables, or IPv6 addresses

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 4: Test Code IPv6 Absence

*For any* test file in the project, the file should not contain IPv6 function tests, ip6tables mocks, or IPv6 test data

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 5: Configuration IPv6 Graceful Handling

*For any* UCI configuration that contains legacy lan_ipv6 parameter, the system should ignore this parameter without errors or warnings

**Validates: Requirements 8.5**

### Static Checks (Examples)

Следующие проверки являются конкретными examples, а не properties:

**Example 1:** HTTP server starts with IPv4 only (0.0.0.0)
**Validates: Requirements 1.3**

**Example 2:** dnsmasq configuration contains no IPv6 addresses
**Validates: Requirements 1.5**

**Example 3:** Documentation explicitly states IPv6 is not supported
**Validates: Requirements 4.4**

**Example 4:** CHANGELOG contains entry about IPv6 removal
**Validates: Requirements 4.5**

**Example 5:** Configuration examples do not contain lan_ipv6 option
**Validates: Requirements 8.1**

**Example 6:** Configuration documentation states only IPv4 is supported
**Validates: Requirements 8.4**

**Example 7:** Deactivation does not call ip6tables commands
**Validates: Requirements 7.4**

## Error Handling

### Обработка legacy конфигурации

Система должна корректно обрабатывать старые конфигурации, содержащие IPv6 параметры:

```bash
# В функции чтения конфигурации
# Старый код (удалить):
value=$(uci_safe_get "${section}.lan_ipv6")
[ -n "$value" ] && LAN_IPV6="$value"

# Новый код: просто не читать этот параметр
# Если параметр присутствует в UCI, он будет проигнорирован
```

### Обработка отсутствия IPv6 функций

После удаления IPv6 кода, система должна работать корректно:

```bash
# Старый код (удалить):
if [ "$HTTPD_IPV6_READY" = "1" ]; then
    # IPv6 логика
fi

# Новый код: просто удалить весь блок
# Никаких проверок на IPv6 не требуется
```

### Логирование

Все сообщения, упоминающие IPv6, должны быть удалены или изменены:

```bash
# Старый код (удалить):
log_info "Запущен busybox httpd (PID $pid) для редиректа (IPv4/IPv6)"
log_warn "Не удалось запустить busybox httpd с IPv6, пробуем только IPv4"

# Новый код:
log_info "Запущен busybox httpd (PID $pid) для редиректа"
# Предупреждение об IPv6 удалить полностью
```

## Testing Strategy

### Dual Testing Approach

Проект будет использовать комбинацию unit тестов и property-based тестов:

**Unit Tests:**
- Проверка конкретных примеров (examples из Correctness Properties)
- Проверка запуска HTTP сервера с IPv4
- Проверка содержимого dnsmasq конфигурации
- Проверка обработки legacy конфигурации

**Property-Based Tests:**
- Проверка отсутствия IPv6 идентификаторов во всех файлах кода
- Проверка отсутствия IPv6 в документации
- Проверка отсутствия IPv6 в логах
- Проверка отсутствия IPv6 в тестах

### Property-Based Testing Library

Для bash скриптов будем использовать **bats-core** с кастомными генераторами для проверки файлов.

Для статического анализа будем использовать **grep** и **awk** для поиска паттернов.

### Test Configuration

- Минимум 100 итераций для каждого property-based теста (где применимо)
- Каждый property-based тест должен иметь комментарий с ссылкой на property из design.md
- Формат комментария: `# Feature: remove-ipv6-support, Property N: <property_text>`

### Test Tagging

Каждый property-based тест должен быть помечен:

```bash
# Feature: remove-ipv6-support, Property 1: Code IPv6 Absence
# For any source code file in the project, the file should not contain any IPv6-related identifiers
# Validates: Requirements 1.1, 1.2, 1.4, 3.1, 3.2, 3.3, 3.4, 3.5
@test "no IPv6 identifiers in source code" {
    # Test implementation
}
```

### Integration Testing

Интеграционные тесты (Requirements 2.x, 7.x) требуют реального OpenWrt окружения и будут выполняться вручную или в VM:

- Проверка, что системные настройки IPv6 не изменяются
- Проверка работы captive portal с IPv4
- Проверка совместимости с другими сервисами

Эти тесты не будут автоматизированы в рамках данной спецификации.

## Implementation Notes

### Порядок удаления

1. **Удалить функции IPv6** - начать с функций, которые явно связаны с IPv6
2. **Удалить переменные IPv6** - удалить объявления и использование переменных
3. **Удалить логику IPv6** - удалить условные блоки и вызовы ip6tables
4. **Обновить логирование** - удалить/изменить сообщения с упоминанием IPv6
5. **Обновить документацию** - удалить примеры и инструкции по IPv6
6. **Обновить тесты** - удалить тесты IPv6 функций
7. **Добавить статические проверки** - добавить тесты для проверки отсутствия IPv6

### Файлы для изменения

**Основной код:**
- `usr/sbin/openwrt_captive_monitor` или `openwrt_captive_monitor.sh`

**Документация:**
- `README.md`
- `docs/` (все файлы с упоминанием IPv6)
- Примеры конфигурации

**Тесты:**
- `tests/` (удалить IPv6 тесты, добавить проверки отсутствия IPv6)

**Конфигурация:**
- Примеры UCI конфигурации
- Документация конфигурационных опций

### Обратная совместимость

Система должна корректно работать со старыми конфигурациями:

- Если в UCI конфигурации присутствует `lan_ipv6`, он будет проигнорирован
- Никаких ошибок или предупреждений не должно генерироваться
- Система должна работать только с IPv4

### Changelog Entry

Добавить в CHANGELOG.md:

```markdown
## [YYYY.M.D.N] - YYYY-MM-DD

### Removed
- **BREAKING CHANGE**: Removed IPv6 support from captive monitor
  - Removed LAN_IPV6 and HTTPD_IPV6_READY variables
  - Removed ensure_lan_ipv6(), resolve_portal_ipv6(), is_ipv6() functions
  - Removed ip6tables rules configuration
  - Removed IPv6 addresses from dnsmasq configuration
  - System now operates in IPv4-only mode
  - Legacy lan_ipv6 configuration parameter is ignored if present
  - Router system IPv6 settings remain unchanged
```

## Migration Path

Для пользователей, использующих текущую версию с IPv6:

1. **Обновление пакета** - установить новую версию через opkg
2. **Конфигурация** - существующая конфигурация продолжит работать, IPv6 параметры будут проигнорированы
3. **Перезапуск сервиса** - `/etc/init.d/captive-monitor restart`
4. **Проверка** - убедиться, что captive portal работает с IPv4

Никаких дополнительных действий не требуется. Системные настройки IPv6 роутера останутся нетронутыми.
