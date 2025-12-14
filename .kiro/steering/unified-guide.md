# Объединённое руководство по проекту OpenWrt Captive Monitor

## Языковые предпочтения

- Общение с пользователем на русском языке
- Планы, документация и объяснения на русском
- Git commit сообщения только на английском
- Показывать команды перед выполнением для прозрачности

## Работающие и неработающие инструменты

### ✅ Работающие инструменты

**Git и GitHub:**
- `gh` CLI - все операции (status, pr create, release, workflow run)
- Git через executePwsh - все операции
- GitKraken MCP - git operations (НО НЕ pr create - требует авторизацию)

**Тестирование:**
- `wsl bash tests/run.sh` - локальные unit тесты
- GitHub Actions - CI/CD в облаке

**Cline CLI (WSL) - НЕ ИСПОЛЬЗОВАТЬ:**
- ❌ **Требует внешнюю авторизацию и регистрацию аккаунта**
- Установлен но не настроен (версия 1.0.8)
- Использовать вместо: стандартные инструменты (git, gh, docker, wsl)

**SSH и удаленный доступ:**
- ⚠️ **ВСЕ SSH подключения ТОЛЬКО через WSL для безопасности**
- Используй короткие имена из /etc/hosts (IP могут меняться)
- ✅ **WSL 2**: Автогенерация /etc/hosts отключена через /etc/wsl.conf
- Тестовая среда: `wsl ssh root@dev-openwrt` (доступна по COM порту)
- Production среда: `wsl ssh root@prod-openwrt` (только после одобрения пользователя!)

**Сборка пакетов:**
- GitHub Releases - пакеты собираются автоматически через workflows
- Скачивание: `gh release download vX.X.X.X -p "*.ipk"`

**COM порт (Serial Console):**
- Доступ к тестовому роутеру: `python tools/serial_console.py COM1 115200 "command"`
- Используй для проверки IP адреса когда SSH недоступен
- Используй для первоначальной настройки SSH ключей

**Google Chrome (WSL) с debugging:**
- ✅ **ЕДИНСТВЕННЫЙ рекомендуемый браузер для тестирования**
- Запуск с debugging: `wsl google-chrome --headless=new --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug --no-sandbox --disable-gpu`
- DevTools API: `http://localhost:9222/json/list` (доступен из Windows и WSL)
- Headless операции: скриншоты, PDF, парсинг HTML
- WebSocket управление в реальном времени

### ❌ НЕ работающие инструменты (НЕ ИСПОЛЬЗОВАТЬ!)

**Act (локальное тестирование GitHub Actions):**
- Не работает на Windows (проблемы с путями)
- Использовать вместо: `wsl bash tests/run.sh` для локальных тестов

**Serial Console:**
- Нет доступа к COM порту
- Использовать вместо: SSH доступ к роутерам

**scripts/build_ipk.sh:**
- Зависает без вывода при локальном запуске
- Использовать вместо: GitHub workflows для сборки пакетов

**GitKraken MCP pull_request_create:**
- Требует авторизацию через браузер
- Использовать вместо: `gh pr create`

**ultrascript-tools MCP:**
- Добавляет 69 инструментов (перегрузка)
- Вызывает проблемы с производительностью
- Держать отключенным в `.kiro/settings/mcp.json`

**Другие браузеры (Firefox, Chromium):**
- НЕ ИСПОЛЬЗОВАТЬ - требуют snap установку
- Firefox и Chromium установлены как transitional packages
- Используй вместо: Google Chrome с debugging API

**Cline CLI:**
- НЕ ИСПОЛЬЗОВАТЬ - требует внешнюю авторизацию
- Установлен в WSL но не настроен
- Используй вместо: стандартные инструменты разработки### ⚠
️ Важные особенности

**Auto-version-tag workflow:**
- НЕ запускается автоматически при push в main
- Запускать вручную: `gh workflow run "Auto Version Tag and Release" --ref main`
- После создания релиза пакеты доступны в GitHub Releases

**Тестовая среда:**
- Короткое имя: `dev-openwrt` (IP может меняться, смотри в /etc/hosts)
- Доступ: `wsl ssh root@dev-openwrt`
- COM порт: `python tools/serial_console.py COM1 115200 "command"`

**Production среда:**
- Короткое имя: `prod-openwrt` (IP может меняться, смотри в /etc/hosts)
- Доступ: `wsl ssh root@prod-openwrt` (только после одобрения!)

**Конвертация путей для WSL:**
```powershell
# Правильная конвертация Windows путей
$wslPath = $windowsPath -replace '\\','/' -replace 'C:','/mnt/c'
wsl scp "$wslPath" root@dev-openwrt:/tmp/
```

## Приоритет использования команд

### Правило: Нативные Windows команды в первую очередь

**Всегда используй нативные Windows/PowerShell команды когда это возможно, вместо WSL.**

WSL добавляет overhead на запуск Linux окружения. Используй WSL только когда нет альтернативы.

### Матрица выбора команд

| Задача | ❌ Не используй WSL | ✅ Используй нативно |
|--------|---------------------|----------------------|
| Git операции | `wsl git status` | `git status` |
| GitHub CLI | `wsl gh pr list` | `gh pr list` |
| Файловые операции | `wsl ls -la` | `Get-ChildItem` или `dir` |
| Чтение файлов | `wsl cat file.txt` | `Get-Content file.txt` |
| Копирование | `wsl cp file1 file2` | `Copy-Item file1 file2` |
| Удаление | `wsl rm file` | `Remove-Item file` |
| Проверка файла | `wsl test -f file` | `Test-Path file` |
| Сетевые проверки | `wsl ping host` | `Test-Connection host` |
| Переменные окружения | `wsl echo $PATH` | `$env:PATH` |
| Python | `wsl python script.py` | `python script.py` |
| Curl | `wsl curl url` | `Invoke-WebRequest url` |
| Node.js / Bun | `wsl node script.js` | `node script.js` или `bun script.js` |###
 ⚠️ Используй WSL только когда необходимо:

| Задача | Причина |
|--------|---------|
| `wsl ssh host` | Только если используются PuTTY ключи (.ppk) без конвертации в OpenSSH формат |
| `wsl bash script.sh` | Bash скрипты требуют Linux окружение |
| `wsl grep pattern file` | Нет прямого аналога в PowerShell |
| `wsl sed 's/old/new/' file` | Нет прямого аналога в PowerShell |
| `wsl awk '{print $1}' file` | Нет прямого аналога в PowerShell |
| `wsl make` | Makefile требует Linux окружение |

### SSH через WSL (обязательно для безопасности)

**⚠️ ВСЕ SSH подключения ТОЛЬКО через WSL!**

```powershell
# ✅ Правильно - через WSL с короткими именами
wsl ssh root@dev-openwrt "uname -a"
wsl ssh root@prod-openwrt "ps w"

# ❌ Неправильно - прямой Windows SSH
ssh root@192.168.1.1 "uname -a"
```

**WSL /etc/hosts (короткие имена):**
```bash
# OpenWrt роутеры (IP могут меняться, обновляй при необходимости)
192.168.1.1     dev-openwrt      # Тестовая среда
192.168.35.1    prod-openwrt     # Production среда
```

**Настройка WSL 2 (отключение автогенерации /etc/hosts):**
```powershell
# Отключить автогенерацию /etc/hosts
wsl bash -c "sudo mkdir -p /etc && echo -e '[network]\ngenerateHosts = false' | sudo tee /etc/wsl.conf"

# Перезапустить WSL для применения настроек
wsl --shutdown

# Добавить записи роутеров (один раз)
wsl bash -c "echo '192.168.1.1     dev-openwrt' | sudo tee -a /etc/hosts"
wsl bash -c "echo '192.168.35.1    prod-openwrt' | sudo tee -a /etc/hosts"

# Проверить
wsl bash -c "cat /etc/hosts | grep openwrt"
```**Об
новление IP адресов роутеров:**
```powershell
# Проверить текущий IP через COM порт
python tools/serial_console.py COM1 115200 "ip addr show br-lan"

# Обновить IP в /etc/hosts (замени на актуальный IP)
wsl bash -c "sudo sed -i 's/192.168.1.1.*dev-openwrt/192.168.1.1     dev-openwrt/' /etc/hosts"
wsl bash -c "sudo sed -i 's/192.168.35.1.*prod-openwrt/192.168.35.1    prod-openwrt/' /etc/hosts"
```

**Генерация SSH ключа в WSL:**
```powershell
# Генерировать ed25519 ключ БЕЗ пароля в WSL
wsl ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_openwrt -N "" -C "openwrt"

# Установить публичный ключ на роутер через COM порт
$pubKey = wsl cat ~/.ssh/id_ed25519_openwrt.pub
python tools/serial_console.py COM1 115200 "echo '$pubKey' >> /etc/dropbear/authorized_keys"

# Проверить подключение
wsl ssh root@dev-openwrt "uname -a"
```

## Контекст проекта

### Обзор проекта

**openwrt-captive-monitor** - легковесный сервис для автоматического обнаружения и обработки captive порталов на маршрутизаторах OpenWrt.

### Критичные исправления (декабрь 2025)

**1. Детекция captive порталов (3xx коды)**
- **Проблема:** 302/303 редиректы captive порталов считались успешным интернетом
- **Решение:** `http_probe_internet()` теперь принимает только 2xx коды
- **Код:** `[ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]`

**2. Доступ к LuCI во время intercept**
- **Проблема:** nftables блокировал доступ к веб-интерфейсу роутера
- **Решение:** Добавлен bypass для IP роутера в `setup_nftables_intercept()`
- **Код:** `nft add rule inet fw4 dstnat ip daddr $ROUTER_IP accept`

**3. Bypass connectivity check доменов**
- **Проблема:** Блокировались проверочные домены (msftconnecttest.com и т.д.)
- **Решение:** DNS bypass через `server=/$domain/#` в dnsmasq
- **Файл:** `/tmp/dnsmasq.d/connectivity-bypass.conf`

## Google Chrome управление

### Запуск Chrome с debugging

```powershell
# Остановить существующие процессы Chrome
wsl pkill chrome

# Запустить Chrome с debugging API (headless)
wsl google-chrome --headless=new --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug --no-sandbox --disable-gpu --disable-dev-shm-usage https://google.com &

# Проверить доступность API
Invoke-WebRequest "http://localhost:9222/json/list" -UseBasicParsing
```

### Chrome DevTools Protocol API

```powershell
# Список всех вкладок
Invoke-WebRequest "http://localhost:9222/json/list" -UseBasicParsing

# Создать новую вкладку
Invoke-WebRequest "http://localhost:9222/json/new?https://example.com" -UseBasicParsing

# Закрыть вкладку (замени ID)
Invoke-WebRequest "http://localhost:9222/json/close/TAB_ID" -UseBasicParsing

# Версия Chrome
Invoke-WebRequest "http://localhost:9222/json/version" -UseBasicParsing
```

### Headless операции

```powershell
# Скриншот страницы
wsl google-chrome --headless=new --screenshot=/tmp/screenshot.png --window-size=1920,1080 https://example.com

# Сохранить в PDF
wsl google-chrome --headless=new --print-to-pdf=/tmp/page.pdf https://example.com

# Получить HTML содержимое
wsl google-chrome --headless=new --dump-dom https://example.com

# Тестирование captive portal
wsl google-chrome --headless=new --dump-dom http://detectportal.firefox.com/canonical.html
```

### Тестирование роутеров

```powershell
# Доступ к веб-интерфейсу роутера
wsl google-chrome --headless=new --dump-dom http://192.168.1.1

# Скриншот LuCI интерфейса
wsl google-chrome --headless=new --screenshot=/tmp/luci.png --window-size=1920,1080 http://192.168.1.1

# Тестирование captive portal intercept
wsl google-chrome --headless=new --dump-dom http://example.com
```

### ⚠️ Важно: НЕ использовать другие браузеры

- **Firefox** - требует `snap install firefox` (transitional package)
- **Chromium** - требует `snap install chromium` (transitional package)
- **Текстовые браузеры** (lynx, w3m) - ограниченная функциональность
- **Используй только Google Chrome** - полностью настроен и готов к работе
