# WSL Routing Manager - Отладка через dev сервер

Этот документ описывает использование WSL Routing Manager для отладки captive portal detection через dev сервер.

## Обзор

WSL Routing Manager позволяет перенаправить весь интернет трафик из WSL через dev сервер OpenWrt для тестирования и отладки captive portal detection. Это полезно для:

- Тестирования обнаружения captive порталов
- Отладки сетевых запросов через OpenWrt
- Проверки работы intercept режима
- Анализа DNS запросов и HTTP трафика

## Установка и настройка

### 1. Настройка sudo без пароля

Для управления маршрутами требуются права sudo. Настройте sudo без пароля:

```powershell
# Запустить скрипт настройки
wsl bash tools/setup_wsl_sudo.sh
```

Скрипт создаст правило sudoers, разрешающее выполнение команд `ip route` без пароля.

### 2. Проверка доступности серверов

Убедитесь, что dev и prod серверы доступны:

```powershell
# Проверить статус
.\tools\wsl_routing_manager.ps1 status

# Протестировать подключение
.\tools\wsl_routing_manager.ps1 test
```

## Использование

### Основные команды

```powershell
# Показать текущий статус маршрутизации
.\tools\wsl_routing_manager.ps1 status

# Включить маршрутизацию через dev сервер
.\tools\wsl_routing_manager.ps1 enable

# Отключить маршрутизацию через dev сервер
.\tools\wsl_routing_manager.ps1 disable

# Сбросить маршрутизацию к WSL по умолчанию
.\tools\wsl_routing_manager.ps1 reset

# Протестировать подключение
.\tools\wsl_routing_manager.ps1 test

# Показать справку
.\tools\wsl_routing_manager.ps1 help
```

### Альтернативное использование через WSL

```bash
# Прямой вызов bash скрипта в WSL
wsl bash tools/wsl_routing_manager.sh status
wsl bash tools/wsl_routing_manager.sh enable
wsl bash tools/wsl_routing_manager.sh disable
```

## Сценарии отладки

### 1. Тестирование captive portal detection

```powershell
# 1. Включить маршрутизацию через dev сервер
.\tools\wsl_routing_manager.ps1 enable

# 2. Подключиться к dev серверу для мониторинга логов
wsl ssh root@dev-openwrt "logread -f | grep captive"

# 3. В другом терминале - тестировать HTTP запросы
wsl curl -v http://detectportal.firefox.com/canonical.html
wsl curl -v http://www.msftconnecttest.com/connecttest.txt
wsl curl -v http://captive.apple.com/hotspot-detect.html

# 4. После тестирования - отключить маршрутизацию
.\tools\wsl_routing_manager.ps1 disable
```

### 2. Отладка DNS запросов

```powershell
# 1. Включить маршрутизацию через dev сервер
.\tools\wsl_routing_manager.ps1 enable

# 2. Мониторить DNS запросы на dev сервере
wsl ssh root@dev-openwrt "logread -f | grep dnsmasq"

# 3. Выполнить DNS запросы из WSL
wsl nslookup google.com
wsl dig @8.8.8.8 detectportal.firefox.com

# 4. Отключить маршрутизацию
.\tools\wsl_routing_manager.ps1 disable
```

### 3. Тестирование intercept режима

```powershell
# 1. Включить маршрутизацию через dev сервер
.\tools\wsl_routing_manager.ps1 enable

# 2. Активировать intercept режим на dev сервере
wsl ssh root@dev-openwrt "/usr/sbin/openwrt_captive_monitor intercept"

# 3. Тестировать HTTP запросы - должны перенаправляться
wsl curl -v http://example.com
wsl curl -v http://google.com

# 4. Деактивировать intercept режим
wsl ssh root@dev-openwrt "/usr/sbin/openwrt_captive_monitor release"

# 5. Отключить маршрутизацию
.\tools\wsl_routing_manager.ps1 disable
```

## Диагностика проблем

### Проблема: Dev сервер недоступен

```powershell
# Проверить IP адрес dev сервера через COM порт
python tools/serial_console.py COM1 115200 "ip addr show br-lan"

# Обновить IP в /etc/hosts WSL
wsl bash -c "sudo sed -i 's/192.168.1.1.*dev-openwrt/NEW_IP     dev-openwrt/' /etc/hosts"

# Проверить подключение
.\tools\wsl_routing_manager.ps1 test
```

### Проблема: Нет прав sudo

```powershell
# Настроить sudo без пароля
wsl bash tools/setup_wsl_sudo.sh

# Или ввести пароль вручную
wsl sudo -v
```

### Проблема: Маршрутизация не восстанавливается

```powershell
# Принудительный сброс к WSL по умолчанию
.\tools\wsl_routing_manager.ps1 reset

# Проверить результат
.\tools\wsl_routing_manager.ps1 status
```

### Проблема: Интернет не работает через dev сервер

```powershell
# Проверить, что dev сервер может маршрутизировать трафик
wsl ssh root@dev-openwrt "ping -c 3 8.8.8.8"

# Проверить NAT правила на dev сервере
wsl ssh root@dev-openwrt "iptables -t nat -L -n -v"

# Проверить маршруты на dev сервере
wsl ssh root@dev-openwrt "ip route show"
```

## Безопасность

### Sudoers правила

Скрипт `setup_wsl_sudo.sh` создает ограниченные sudoers правила только для команд `ip route`. Это безопаснее, чем полные sudo права.

Файл: `/etc/sudoers.d/wsl-routing`
```
# Разрешить только команды ip route без пароля
username ALL=(ALL) NOPASSWD: /sbin/ip route add *, /sbin/ip route del *
```

### Восстановление маршрутизации

Скрипт автоматически сохраняет оригинальную маршрутизацию в `/tmp/wsl_original_gateway` и восстанавливает ее при отключении.

### Откат изменений

Если что-то пошло не так, всегда можно выполнить:

```powershell
# Сброс к WSL по умолчанию
.\tools\wsl_routing_manager.ps1 reset

# Или перезапустить WSL
wsl --shutdown
wsl echo "WSL restarted"
```

## Архитектура

### Компоненты

1. **wsl_routing_manager.sh** - основной bash скрипт для управления маршрутами в WSL
2. **wsl_routing_manager.ps1** - PowerShell обертка для удобного использования
3. **setup_wsl_sudo.sh** - скрипт настройки sudo без пароля

### Принцип работы

1. **Сохранение текущего шлюза** - оригинальный шлюз сохраняется в `/tmp/wsl_original_gateway`
2. **Изменение маршрута по умолчанию** - `ip route add default via 192.168.1.1`
3. **Сохранение доступа к WSL сети** - локальные маршруты остаются без изменений
4. **Восстановление при отключении** - оригинальный шлюз восстанавливается из сохраненного файла

### Сетевая топология

```
WSL (172.22.145.24/20)
    ↓ (обычно)
WSL Gateway (172.22.144.1)
    ↓
Windows Host
    ↓
Internet

WSL (172.22.145.24/20)
    ↓ (с включенной маршрутизацией)
Dev OpenWrt (192.168.1.1)
    ↓
Internet (через dev сервер)
```

## Примеры использования

### Полный цикл тестирования

```powershell
# 1. Проверить исходное состояние
.\tools\wsl_routing_manager.ps1 status

# 2. Включить маршрутизацию через dev
.\tools\wsl_routing_manager.ps1 enable

# 3. Протестировать подключение
.\tools\wsl_routing_manager.ps1 test

# 4. Выполнить отладку (в отдельных терминалах)
# Terminal 1: мониторинг логов
wsl ssh root@dev-openwrt "logread -f"

# Terminal 2: тестирование
wsl curl -v http://detectportal.firefox.com/canonical.html

# 5. Отключить маршрутизацию
.\tools\wsl_routing_manager.ps1 disable

# 6. Проверить восстановление
.\tools\wsl_routing_manager.ps1 status
```

### Автоматизированное тестирование

```powershell
# Скрипт для автоматического тестирования
$testUrls = @(
    "http://detectportal.firefox.com/canonical.html",
    "http://www.msftconnecttest.com/connecttest.txt",
    "http://captive.apple.com/hotspot-detect.html"
)

# Включить маршрутизацию
.\tools\wsl_routing_manager.ps1 enable

# Тестировать каждый URL
foreach ($url in $testUrls) {
    Write-Host "Testing: $url"
    wsl curl -s -o /dev/null -w "HTTP: %{http_code}, Time: %{time_total}s\n" $url
}

# Отключить маршрутизацию
.\tools\wsl_routing_manager.ps1 disable
```
