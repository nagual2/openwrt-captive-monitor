# Тестовое окружение

## OpenWrt Test Environment 1

### Основная информация

**Хост:** `root@192.168.35.127`  
**Доступ:** SSH по ключу (без пароля)  
**Назначение:** Тестирование пакетов OpenWrt, интеграционные тесты

### Характеристики системы

```
Дистрибутив: OpenWrt 23.05.3 r23809-234f1a2efa
Архитектура: x86/64 (x86_64)
Ядро: Linux 5.15.150 #0 SMP
Память: 209 MB RAM (112 MB доступно)
Диск: 2.0 GB (1.1 GB свободно)
```

### Сетевая конфигурация

```
Интерфейс: br-lan
IP адрес: 192.168.35.127/24
IPv6: fd5d:235:5ede:0:20c:29ff:fe15:16b1/64
      2a11:6c7:1101:4f00:20c:29ff:fe15:16b1/64
MAC: 00:0c:29:15:16:b1
Протокол: DHCP
```

### Доступные инструменты

**Системные утилиты:**
- ✅ `opkg` - пакетный менеджер OpenWrt
- ✅ `uci` - Unified Configuration Interface
- ✅ `bash` - Bash shell (5.2.15)
- ✅ `busybox` - BusyBox utilities (1.36.1)

**Инструменты разработки:**
- ✅ `gcc` - GNU C Compiler
- ✅ `make` - GNU Make
- ✅ `git` - Git version control
- ✅ `autoconf` (2.72-1)
- ✅ `automake` (1.16.5-1)
- ✅ `binutils` (2.40-1)

**Сетевые утилиты:**
- ✅ `curl` (8.7.1)
- ✅ `wget`
- ✅ `dnsmasq` (2.90-2)

**Утилиты Python:**
- ✅ `python3`

**Дополнительные инструменты:**
- ✅ `btop` - мониторинг системы (1.4.4)
- ✅ `coreutils` - GNU core utilities (9.3)
- ✅ `diffutils` (3.8)
- ✅ `bzip2` (1.0.8)

## Подключение к тестовой среде

### Из PowerShell (через WSL)

```powershell
# Простое подключение
wsl ssh root@192.168.35.127

# Выполнить команду
wsl ssh root@192.168.35.127 "uname -a"

# Выполнить несколько команд
wsl bash -c "ssh root@192.168.35.127 'uci show network && ip addr'"
```

### Из WSL напрямую

```bash
# Подключение
ssh root@192.168.35.127

# Выполнить команду
ssh root@192.168.35.127 "opkg list-installed"

# Копировать файл на роутер
scp package.ipk root@192.168.35.127:/tmp/

# Копировать файл с роутера
scp root@192.168.35.127:/etc/config/network ./network.backup
```

### Проверка доступности

```powershell
# Ping тест
Test-Connection -ComputerName 192.168.35.127 -Count 2

# SSH тест
wsl ssh -o ConnectTimeout=5 root@192.168.35.127 "echo 'Connection OK'"
```

## Типичные сценарии тестирования

### 1. Установка и тестирование пакета

```bash
# Скопировать пакет на роутер
scp dist/openwrt-captive-monitor_*.ipk root@192.168.35.127:/tmp/

# Подключиться к роутеру
ssh root@192.168.35.127

# На роутере:
# Установить пакет
opkg install /tmp/openwrt-captive-monitor_*.ipk

# Проверить установку
opkg list-installed | grep captive

# Проверить файлы
ls -la /usr/sbin/openwrt_captive_monitor
ls -la /etc/init.d/captive-monitor
ls -la /etc/config/captive-monitor

# Запустить сервис
/etc/init.d/captive-monitor start

# Проверить статус
/etc/init.d/captive-monitor status

# Проверить логи
logread | grep captive-monitor

# Включить автозапуск
/etc/init.d/captive-monitor enable

# Проверить автозапуск
ls -la /etc/rc.d/*captive*
```

### 2. Обновление пакета

```bash
# На роутере:
# Остановить сервис
/etc/init.d/captive-monitor stop

# Удалить старую версию
opkg remove openwrt-captive-monitor

# Установить новую версию
opkg install /tmp/openwrt-captive-monitor_*.ipk

# Запустить сервис
/etc/init.d/captive-monitor start
```

### 3. Тестирование конфигурации

```bash
# На роутере:
# Просмотр конфигурации
uci show captive-monitor

# Изменение конфигурации
uci set captive-monitor.config.enabled='1'
uci set captive-monitor.config.check_interval='60'
uci commit captive-monitor

# Перезапуск сервиса
/etc/init.d/captive-monitor restart

# Проверка применения настроек
logread | grep captive-monitor | tail -20
```

### 4. Отладка проблем

```bash
# На роутере:
# Запуск скрипта вручную для отладки
/usr/sbin/openwrt_captive_monitor

# Проверка зависимостей
opkg list-installed | grep -E "(curl|wget|iptables|nftables)"

# Проверка сетевых интерфейсов
ip addr show
uci show network

# Проверка правил firewall
iptables -L -n -v
# или для nftables
nft list ruleset

# Проверка DNS
nslookup google.com
cat /etc/resolv.conf

# Мониторинг системы
btop
# или
top
```

### 5. Сбор логов для анализа

```bash
# На роутере:
# Полные логи системы
logread > /tmp/system.log

# Логи конкретного сервиса
logread | grep captive-monitor > /tmp/captive-monitor.log

# Информация о системе
uname -a > /tmp/system-info.txt
cat /etc/openwrt_release >> /tmp/system-info.txt
free -m >> /tmp/system-info.txt
df -h >> /tmp/system-info.txt

# Копировать логи на локальную машину
# (выполнить на локальной машине)
scp root@192.168.35.127:/tmp/*.log ./logs/
scp root@192.168.35.127:/tmp/system-info.txt ./logs/
```

## Автоматизация тестирования

### Скрипт для автоматической установки и тестирования

```bash
#!/bin/bash
# test-on-openwrt.sh

set -euo pipefail

ROUTER_IP="192.168.35.127"
PACKAGE_FILE=$1

if [ -z "$PACKAGE_FILE" ]; then
    echo "Usage: $0 <package.ipk>"
    exit 1
fi

echo "=== Testing package on OpenWrt ==="
echo "Router: $ROUTER_IP"
echo "Package: $PACKAGE_FILE"
echo

# Копировать пакет
echo "Copying package to router..."
scp "$PACKAGE_FILE" root@$ROUTER_IP:/tmp/

# Установить пакет
echo "Installing package..."
ssh root@$ROUTER_IP "opkg install /tmp/$(basename $PACKAGE_FILE)"

# Проверить установку
echo "Verifying installation..."
ssh root@$ROUTER_IP "opkg list-installed | grep captive"

# Запустить сервис
echo "Starting service..."
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor start"

# Подождать 5 секунд
sleep 5

# Проверить статус
echo "Checking service status..."
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor status"

# Проверить логи
echo "Checking logs..."
ssh root@$ROUTER_IP "logread | grep captive-monitor | tail -10"

echo
echo "✅ Test completed successfully"
```

### Использование скрипта

```powershell
# Из PowerShell
wsl bash test-on-openwrt.sh dist/openwrt-captive-monitor_1.0.0_all.ipk

# Или из WSL
bash test-on-openwrt.sh dist/openwrt-captive-monitor_1.0.0_all.ipk
```

## Smoke Tests

### Базовый smoke test

```bash
#!/bin/bash
# smoke-test.sh

ROUTER_IP="192.168.35.127"

echo "=== OpenWrt Smoke Test ==="

# Тест 1: Подключение
echo "Test 1: SSH connection..."
if ssh -o ConnectTimeout=5 root@$ROUTER_IP "echo OK" | grep -q OK; then
    echo "✅ SSH connection OK"
else
    echo "❌ SSH connection failed"
    exit 1
fi

# Тест 2: Пакет установлен
echo "Test 2: Package installed..."
if ssh root@$ROUTER_IP "opkg list-installed | grep -q captive-monitor"; then
    echo "✅ Package installed"
else
    echo "❌ Package not installed"
    exit 1
fi

# Тест 3: Файлы на месте
echo "Test 3: Files present..."
if ssh root@$ROUTER_IP "test -f /usr/sbin/openwrt_captive_monitor"; then
    echo "✅ Main script present"
else
    echo "❌ Main script missing"
    exit 1
fi

# Тест 4: Сервис запущен
echo "Test 4: Service running..."
if ssh root@$ROUTER_IP "/etc/init.d/captive-monitor status" | grep -q running; then
    echo "✅ Service running"
else
    echo "⚠️  Service not running (may be expected)"
fi

# Тест 5: Логи без критических ошибок
echo "Test 5: No critical errors in logs..."
if ssh root@$ROUTER_IP "logread | grep captive-monitor | grep -i error"; then
    echo "⚠️  Errors found in logs"
else
    echo "✅ No critical errors"
fi

echo
echo "=== Smoke test completed ==="
```

## Очистка тестовой среды

### Удаление пакета и очистка

```bash
# На роутере:
# Остановить сервис
/etc/init.d/captive-monitor stop

# Отключить автозапуск
/etc/init.d/captive-monitor disable

# Удалить пакет
opkg remove openwrt-captive-monitor

# Проверить удаление
opkg list-installed | grep captive

# Удалить временные файлы
rm -f /tmp/openwrt-captive-monitor_*.ipk
rm -f /tmp/*.log

# Очистить логи (опционально)
logread -c
```

### Скрипт для полной очистки

```bash
#!/bin/bash
# cleanup-test-env.sh

ROUTER_IP="192.168.35.127"

echo "=== Cleaning up test environment ==="

ssh root@$ROUTER_IP "
    # Остановить сервис
    /etc/init.d/captive-monitor stop 2>/dev/null || true
    
    # Отключить автозапуск
    /etc/init.d/captive-monitor disable 2>/dev/null || true
    
    # Удалить пакет
    opkg remove openwrt-captive-monitor 2>/dev/null || true
    
    # Удалить временные файлы
    rm -f /tmp/openwrt-captive-monitor_*.ipk
    rm -f /tmp/*.log
    
    echo 'Cleanup completed'
"

echo "✅ Test environment cleaned"
```

## Мониторинг и диагностика

### Мониторинг ресурсов

```bash
# На роутере:
# Использование памяти
free -m

# Использование диска
df -h

# Топ процессов
top -b -n 1 | head -20

# Или использовать btop для интерактивного мониторинга
btop
```

### Сетевая диагностика

```bash
# На роутере:
# Проверка интерфейсов
ip addr show

# Проверка маршрутов
ip route show

# Проверка DNS
nslookup google.com

# Проверка подключения
ping -c 3 8.8.8.8

# Проверка портов
netstat -tuln
```

## Ограничения тестовой среды

### Известные ограничения

1. **Память:** Только 209 MB RAM - может быть недостаточно для тяжелых тестов
2. **Диск:** 2 GB - ограниченное пространство для логов и временных файлов
3. **Архитектура:** x86/64 - тесты для других архитектур (ARM, MIPS) требуют других устройств
4. **Версия:** OpenWrt 23.05.3 - для тестирования других версий нужны дополнительные среды

### Рекомендации

- Регулярно очищать временные файлы и логи
- Мониторить использование памяти при длительных тестах
- Использовать smoke tests для быстрой проверки базовой функциональности
- Для полного тестирования использовать VM или дополнительные устройства

## Backup и восстановление

### Создание backup конфигурации

```bash
# На роутере:
# Backup всей конфигурации
sysupgrade -b /tmp/backup-$(date +%Y%m%d).tar.gz

# Копировать backup на локальную машину
# (выполнить на локальной машине)
scp root@192.168.35.127:/tmp/backup-*.tar.gz ./backups/
```

### Восстановление конфигурации

```bash
# Копировать backup на роутер
scp backups/backup-20250128.tar.gz root@192.168.35.127:/tmp/

# На роутере:
# Восстановить конфигурацию
sysupgrade -r /tmp/backup-20250128.tar.gz

# Перезагрузить
reboot
```
