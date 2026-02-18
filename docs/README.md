# Документация OpenWrt Captive Monitor

## Обзор

Эта директория содержит документацию по настройке, анализу и troubleshooting OpenWrt роутера с captive portal мониторингом.

---

## Сетевая инфраструктура

### WiFi и роуминг

- [WiFi Airtime Keeper Setup](WIFI_AIRTIME_KEEPER_SETUP.md) - Настройка сервиса для резервирования эфирного времени
- [WiFi Airtime Quick Reference](WIFI_AIRTIME_QUICK_REFERENCE.md) - Быстрая справка по WiFi Airtime Keeper
- [WiFi STA Connection Analysis](WIFI_STA_CONNECTION_ANALYSIS.md) - Анализ подключения к точке доступа провайдера
- [WiFi AP Clients Analysis](WIFI_AP_CLIENTS_ANALYSIS.md) - Анализ клиентов на точке доступа роутера
- [WiFi Roaming Analysis](wifi-roaming-analysis.md) - Анализ роуминга между точками доступа

### MTU и производительность

- [MTU Analysis](MTU_ANALYSIS.md) - Анализ MTU и фрагментации пакетов для IPv4
- [IPv6 MTU Analysis](IPV6_MTU_ANALYSIS.md) - Анализ MTU для IPv6 туннелей
- [MTU Fix Status](MTU_FIX_STATUS.md) - Статус исправлений MTU
- [Packet Loss Analysis](PACKET_LOSS_ANALYSIS.md) - Полный анализ потерь пакетов
- [Packet Loss Quick Reference](PACKET_LOSS_QUICK_REFERENCE.md) - Быстрая справка по потерям пакетов

### IPv6 и DNS

- [IPv6 DNS Resolution](IPV6_DNS_RESOLUTION.md) - Настройка DNS для IPv6
- [NAT64/DNS64 Summary](NAT64_DNS64_SUMMARY.md) - Обзор NAT64/DNS64
- [NAT64/DNS64 Benchmark](NAT64_DNS64_BENCHMARK.md) - Тесты производительности NAT64/DNS64

### mDNS и Avahi

- [mDNS Avahi IPv6 Guide](MDNS_AVAHI_IPV6_GUIDE.md) - Настройка Avahi для IPv6
- [mDNS Quick Reference](MDNS_QUICK_REFERENCE.md) - Быстрая справка по mDNS
- [Avahi Setup Report](AVAHI_SETUP_REPORT.md) - Отчет о настройке Avahi

### Безопасность

- [MFP Support Check](MFP_SUPPORT_CHECK.md) - Проверка поддержки Management Frame Protection

---

## Настройка и обслуживание

### Backup и восстановление

- [Backup Restore Guide](BACKUP_RESTORE_GUIDE.md) - Руководство по резервному копированию и восстановлению
- [DHCP Cleanup Report](DHCP_CLEANUP_REPORT.md) - Отчет об очистке DHCP конфигурации

### Captive Portal

- [Captive Portal Flow Comparison](captive_portal_flow_comparison.md) - Сравнение методов авторизации
- [Script NoJS Info](script_nojs_info.md) - Информация о NoJS скрипте
- [Script Selenium Info](script_selenium_info.md) - Информация о Selenium скрипте

---

## Разработка и тестирование

### Инструменты

- [Commands Cheatsheet](commands_cheatsheet.md) - Часто используемые команды
- [Tools Overview](tools_overview.md) - Обзор инструментов проекта
- [WSL Guide](wsl_guide.md) - Руководство по работе с WSL
- [Docker Guide](docker_guide.md) - Руководство по Docker

### Тестирование и troubleshooting

- [Testing Procedures](testing_procedures.md) - Процедуры тестирования
- [Troubleshooting](troubleshooting.md) - Решение проблем

---

## Исследования и анализ

- [Theses Summary](theses_summary.md) - Резюме исследований

---

## Быстрый доступ

### Мониторинг WiFi

```bash
# Проверка TX failed
wsl ssh root@prod-openwrt "iw dev phy1-sta0 station dump | grep -E '(tx packets|tx failed)'"

# Проверка сигнала
wsl ssh root@prod-openwrt "iw dev phy1-sta0 link | grep signal"

# Проверка beacon loss
wsl ssh root@prod-openwrt "iw dev phy1-sta0 station dump | grep 'beacon loss'"
```

### Тестирование сети

```bash
# Ping к gateway
wsl ssh root@prod-openwrt "ping -c 100 -W 1 10.73.192.1 | grep 'packet loss'"

# Ping к Google DNS (IPv4)
wsl ssh root@prod-openwrt "ping -c 100 -W 1 8.8.8.8 | grep 'packet loss'"

# Ping к Google DNS (IPv6)
wsl ssh root@prod-openwrt "ping6 -c 100 -W 1 2001:4860:4860::8888 | grep 'packet loss'"
```

### Статистика интерфейсов

```bash
# Статистика phy1-sta0
wsl ssh root@prod-openwrt "cat /proc/net/dev | grep phy1-sta0"

# Фрагментация IPv4
wsl ssh root@prod-openwrt "cat /proc/net/snmp | grep Frag"

# Фрагментация IPv6
wsl ssh root@prod-openwrt "cat /proc/net/snmp6 | grep Frag"
```

---

## Структура документов

### Анализы (Analysis)

Полные технические анализы с детальными данными:
- WiFi STA Connection Analysis
- WiFi AP Clients Analysis
- MTU Analysis
- IPv6 MTU Analysis
- Packet Loss Analysis

### Быстрые справки (Quick Reference)

Краткие справочники для быстрого доступа:
- WiFi Airtime Quick Reference
- mDNS Quick Reference
- Packet Loss Quick Reference

### Руководства (Guide)

Пошаговые инструкции по настройке:
- Backup Restore Guide
- mDNS Avahi IPv6 Guide
- WSL Guide
- Docker Guide

### Отчеты (Report)

Отчеты о выполненных работах:
- Avahi Setup Report
- DHCP Cleanup Report

### Статусы (Status)

Текущее состояние систем:
- MTU Fix Status

---

## Соглашения

### Именование файлов

- `UPPERCASE_WITH_UNDERSCORES.md` - Анализы, отчеты, руководства
- `lowercase-with-dashes.md` - Общие документы, справочники

### Структура документа

Каждый анализ должен содержать:
1. **Дата** - когда проводился анализ
2. **Обзор** - краткое описание
3. **Результаты** - детальные данные
4. **Анализ** - интерпретация результатов
5. **Рекомендации** - предлагаемые действия
6. **Заключение** - итоговая оценка

### Метрики и оценки

Используем единую систему оценок:
- ✅ Отлично - работает идеально
- ⚠️ Приемлемо - работает, но есть потенциал для улучшения
- ❌ Проблема - требуется исправление

---

## Обновление документации

При внесении изменений в систему:

1. Обновить соответствующий анализ
2. Обновить быструю справку (если есть)
3. Добавить запись в историю изменений
4. Обновить дату документа

---

## Контакты и поддержка

Для вопросов и предложений по документации обращайтесь к maintainer проекта.
