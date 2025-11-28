# Remote-SSH Setup для Kiro

## Конфигурация SSH

### SSH Config файлы

**Windows:** `C:\Users\Администратор\.ssh\config`  
**WSL:** `~/.ssh/config`

### Настроенные хосты

#### openwrt-test (основной)
```
Host openwrt-test
    HostName 192.168.35.127
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

#### openwrt (алиас)
```
Host openwrt
    HostName 192.168.35.127
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

## Использование в Kiro

### Подключение через Remote-SSH

1. **Открыть Command Palette** (Ctrl+Shift+P)
2. Выбрать **"Remote-SSH: Connect to Host..."**
3. Выбрать **"openwrt-test"** или **"openwrt"**
4. Kiro откроет новое окно подключенное к OpenWrt

### Быстрое подключение

```bash
# Через WSL
wsl ssh openwrt-test

# Или короткий алиас
wsl ssh openwrt
```

### Выполнение команд

```bash
# Одиночная команда
wsl ssh openwrt-test "uname -a"

# Несколько команд
wsl ssh openwrt-test "uci show network && ip addr"

# С таймаутом
wsl ssh -o ConnectTimeout=5 openwrt-test "command"
```

### Копирование файлов

```bash
# На OpenWrt
wsl scp file.txt openwrt-test:/tmp/

# С OpenWrt
wsl scp openwrt-test:/tmp/file.txt ./

# Директория
wsl scp -r directory/ openwrt-test:/tmp/
```

## Настройки Kiro (settings.json)

```json
{
    "remote.SSH.configFile": "~/.ssh/config",
    "remote.SSH.showLoginTerminal": true,
    "remote.SSH.remotePlatform": {
        "openwrt-test": "linux",
        "openwrt": "linux"
    },
    "remote.SSH.enableDynamicForwarding": false,
    "remote.SSH.connectTimeout": 30
}
```

**Важно:** Используй `~/.ssh/config` вместо полного пути с кириллицей, чтобы избежать проблем с кодировкой.

## Работа с удалённым окружением

### После подключения через Remote-SSH:

1. **Открыть терминал** - будет автоматически на OpenWrt
2. **Открыть файлы** - можно редактировать файлы на OpenWrt
3. **Запускать команды** - как будто работаешь локально

### Типичные задачи:

**Редактирование конфигурации:**
```bash
# В Remote-SSH терминале
vi /etc/config/network
uci show network
```

**Просмотр логов:**
```bash
logread -f
logread | grep captive-monitor
```

**Управление сервисами:**
```bash
/etc/init.d/captive-monitor start
/etc/init.d/captive-monitor status
```

**Установка пакетов:**
```bash
opkg update
opkg install package-name
```

## Troubleshooting

### Проблема: Connection timeout

**Решение:**
```bash
# Проверить доступность хоста
Test-Connection -ComputerName 192.168.35.127 -Count 2

# Проверить SSH порт
wsl nc -zv 192.168.35.127 22
```

### Проблема: Permission denied

**Решение:**
```bash
# Проверить SSH ключи
wsl ssh-add -l

# Проверить права на config
wsl chmod 600 ~/.ssh/config
```

### Проблема: Host key verification failed

**Решение:**
```bash
# Удалить старый ключ
wsl ssh-keygen -R 192.168.35.127

# Или использовать StrictHostKeyChecking no (уже настроено)
```

### Проблема: Remote-SSH не видит хост

**Решение:**
1. Проверить что config файл существует
2. Перезагрузить Kiro
3. Проверить путь в settings.json

## Полезные команды

### Проверка конфигурации

```bash
# Показать SSH config
wsl cat ~/.ssh/config

# Проверить подключение
wsl ssh -v openwrt-test "echo OK"

# Список известных хостов
wsl cat ~/.ssh/known_hosts
```

### Управление SSH сессиями

```bash
# Активные SSH соединения
wsl ps aux | grep ssh

# Убить зависшую сессию
wsl pkill -f "ssh openwrt"
```

## Автоматизация

### Скрипт для быстрого подключения

```powershell
# В PowerShell profile
function Connect-OpenWrt {
    wsl ssh openwrt-test
}

Set-Alias openwrt Connect-OpenWrt
```

### Скрипт для выполнения команды

```powershell
function Invoke-OpenWrtCommand {
    param([string]$Command)
    wsl ssh openwrt-test "$Command"
}

# Использование
Invoke-OpenWrtCommand "uname -a"
```

## Интеграция с тестированием

### Автоматическое тестирование через Remote-SSH

```bash
# Скрипт test-remote.sh
#!/bin/bash
set -euo pipefail

# Копировать пакет
scp dist/package.ipk openwrt-test:/tmp/

# Установить
ssh openwrt-test "opkg install /tmp/package.ipk"

# Проверить
ssh openwrt-test "/etc/init.d/captive-monitor status"

# Собрать логи
ssh openwrt-test "logread | grep captive-monitor" > test-logs.txt
```

## Расширенные возможности

### Port Forwarding

```bash
# Локальный порт 8080 -> OpenWrt порт 80
wsl ssh -L 8080:localhost:80 openwrt-test

# Теперь можно открыть http://localhost:8080
```

### Reverse Tunnel

```bash
# OpenWrt порт 8080 -> локальный порт 3000
wsl ssh -R 8080:localhost:3000 openwrt-test
```

### SOCKS Proxy

```bash
# Создать SOCKS proxy через OpenWrt
wsl ssh -D 1080 openwrt-test

# Настроить браузер использовать localhost:1080
```

## Безопасность

### Рекомендации:

1. ✅ Используй SSH ключи вместо паролей
2. ✅ Регулярно обновляй OpenWrt
3. ✅ Ограничь доступ по IP (если возможно)
4. ⚠️ StrictHostKeyChecking отключен для удобства тестирования
5. ⚠️ UserKnownHostsFile=/dev/null - не сохраняет ключи хостов

**Для production:**
```
Host openwrt-prod
    HostName 192.168.1.1
    User root
    Port 22
    IdentityFile ~/.ssh/openwrt_prod_key
    StrictHostKeyChecking yes
    ServerAliveInterval 60
```

## Ссылки

- [Remote-SSH Documentation](https://code.visualstudio.com/docs/remote/ssh)
- [OpenSSH Config](https://man.openwrt.org/packages/openssh-client.8)
- [Test Environment Details](.kiro/steering/test-environment.md)
