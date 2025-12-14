# Tools Directory

Этот каталог содержит вспомогательные инструменты для разработки и отладки OpenWrt Captive Monitor.

## Captive Portal WSL Selenium

**`captive_portal_wsl_selenium.py`** - консолидированный скрипт авторизации на captive порталах через WSL с Selenium.

### Возможности

- ✅ Принудительная маршрутизация через роутер 192.168.1.1
- ✅ Автоматическое обнаружение captive порталов
- ✅ Поддержка различных типов авторизации
- ✅ Работа с Chrome в headless режиме
- ✅ Автоматическое восстановление сетевых настроек

### Использование

```bash
# Базовый запуск (headless режим)
wsl python3 tools/captive_portal_wsl_selenium.py

# С отображением браузера для отладки
wsl python3 tools/captive_portal_wsl_selenium.py --show-browser

# С учетными данными
wsl python3 tools/captive_portal_wsl_selenium.py --username "12345" --password "secret"

# Отладочный режим
wsl python3 tools/captive_portal_wsl_selenium.py --debug --verbose
```

### Тестирование

```bash
# Полное тестирование скрипта
wsl python3 tools/test_captive_portal_wsl_selenium.py

# Быстрая проверка доступа к интернету через dev
wsl python3 tools/test_dev_internet_access.py

# Тестирование с учетными данными
wsl python3 tools/test_captive_portal_wsl_selenium.py --username "12345" --password "secret"
```

### Документация

Подробная документация: [docs/captive-portal-wsl-selenium.md](../docs/captive-portal-wsl-selenium.md)

## WSL Routing Manager

Инструменты для управления маршрутизацией WSL через dev сервер для отладки captive portal detection.

### Файлы

- **`wsl_routing_manager.ps1`** - PowerShell обертка (рекомендуется)
- **`wsl_routing_manager.sh`** - основной bash скрипт
- **`setup_wsl_sudo.sh`** - настройка sudo без пароля

### Быстрый старт

```powershell
# 1. Настроить sudo (один раз)
wsl bash tools/setup_wsl_sudo.sh

# 2. Проверить статус
.\tools\wsl_routing_manager.ps1 status

# 3. Включить маршрутизацию через dev сервер
.\tools\wsl_routing_manager.ps1 enable

# 4. Тестировать
wsl curl -v http://detectportal.firefox.com/canonical.html

# 5. Отключить маршрутизацию
.\tools\wsl_routing_manager.ps1 disable
```

### Документация

Подробная документация: [docs/wsl-routing-debug.md](../docs/wsl-routing-debug.md)

## Другие инструменты

- **`serial_console.py`** - доступ к serial консоли роутера
- **`captive_portal_keepalive.py`** - keep-alive для поддержания авторизации

### Serial Console

```powershell
# Проверить IP адрес роутера
python tools/serial_console.py COM1 115200 "ip addr show br-lan"

# Выполнить команду на роутере
python tools/serial_console.py COM1 115200 "logread | tail -20"
```

## Использование в отладке

### Типичный workflow отладки

1. **Подготовка**
   ```powershell
   # Проверить доступность серверов
   .\tools\wsl_routing_manager.ps1 test
   ```

2. **Включение отладки**
   ```powershell
   # Включить маршрутизацию через dev
   .\tools\wsl_routing_manager.ps1 enable
   ```

3. **Мониторинг** (в отдельном терминале)
   ```powershell
   # Логи captive monitor
   wsl ssh root@dev-openwrt "logread -f | grep captive"

   # Логи DNS
   wsl ssh root@dev-openwrt "logread -f | grep dnsmasq"
   ```

4. **Тестирование**
   ```powershell
   # HTTP запросы
   wsl curl -v http://detectportal.firefox.com/canonical.html

   # DNS запросы
   wsl nslookup google.com
   ```

5. **Завершение**
   ```powershell
   # Отключить маршрутизацию
   .\tools\wsl_routing_manager.ps1 disable
   ```

### Диагностика проблем

```powershell
# Если dev сервер недоступен
python tools/serial_console.py COM1 115200 "ip addr show br-lan"

# Если маршрутизация не работает
.\tools\wsl_routing_manager.ps1 reset

# Если нет прав sudo
wsl bash tools/setup_wsl_sudo.sh
```
