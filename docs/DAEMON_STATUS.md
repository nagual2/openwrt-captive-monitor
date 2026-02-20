# 📊 Captive Portal Daemon - Текущий статус

## ✅ Где работает демон

**Docker контейнер в WSL (BOOK25)**

```
Контейнер: captive-daemon
Хост: BOOK25 (WSL Ubuntu)
Статус: Up 5 minutes (healthy)
Сеть: host mode (доступ к локальной сети Windows)
Платформа: linux/amd64
```

## 🗑️ Удалённые установки

### WSL (BOOK25)
- ✅ Debian пакет `openwrt-captive-monitor` удалён
- ✅ Systemd сервис `captive-portal-daemon` остановлен и отключён

### Minisforum (max-Z83-F)
- ✅ Доступен (192.168.35.160 / 192.168.35.125)
- ✅ Debian пакет НЕ установлен
- ✅ Systemd сервис НЕ найден
- ℹ️ Режим: Router (NAT, bridge br0)
- ℹ️ Kernel: 6.14.0-37-generic Ubuntu 24.04

## 🐳 Docker демон

### Расположение
```
Windows: C:\Git\openwrt-captive-monitor\docker\daemon\
WSL: /mnt/c/git/openwrt-captive-monitor/docker/daemon/
```

### Конфигурация
```
Образ: captive-portal-daemon:latest
Сеть: host (прямой доступ к сети Windows)
Память: 512MB limit
CPU: 1.0 limit
Логи: docker/daemon/logs/captive_portal_daemon.log
```

### Работа демона
```
✅ Chrome инициализирован (Selenium Manager)
✅ Проверка каждые 60 секунд
✅ Текущий статус: Авторизация активна (редирект на MSN)
✅ Healthcheck: healthy
```

## 🔄 Как работает

1. **Docker контейнер** запущен в WSL
2. **Network mode: host** - контейнер использует сеть Windows напрямую
3. **Проверка авторизации** - каждые 60 секунд открывает http://www.msftconnecttest.com/redirect
4. **Обнаружение портала** - если редирект на conn4.com, запускает авторизацию
5. **Логирование** - все события записываются в `docker/daemon/logs/captive_portal_daemon.log`

## 📋 Управление

### PowerShell (Windows)
```powershell
# Статус
.\docker\daemon\manage.ps1 status

# Логи
.\docker\daemon\manage.ps1 logs

# Перезапуск
.\docker\daemon\manage.ps1 restart

# Остановка
.\docker\daemon\manage.ps1 stop
```

### Docker команды (WSL)
```bash
# Статус
wsl docker ps --filter name=captive-daemon

# Логи
wsl docker logs captive-daemon -f

# Перезапуск
wsl docker restart captive-daemon

# Остановка
wsl docker stop captive-daemon
```

## 🌐 Сетевая архитектура

```
Windows Host (BOOK25)
    ↓
WSL Ubuntu (BOOK25)
    ↓
Docker Container (captive-daemon)
    ↓ network: host
Windows Network Stack
    ↓
Internet / Captive Portal
```

**Преимущество host mode:**
- Контейнер видит ту же сеть, что и Windows
- Может обнаруживать captive порталы на Windows сети
- Прямой доступ к локальным ресурсам

## 📊 Последняя проверка

```
Время: 2026-02-19 11:03:11
URL: http://www.msftconnecttest.com/redirect
Результат: https://www.msn.com/de-de?ocid=wispr&pc=u477
Статус: ✅ Авторизация активна (редирект на MSN)
```

## 🔍 Мониторинг

### Healthcheck
```powershell
wsl docker inspect captive-daemon --format='{{.State.Health.Status}}'
# Output: healthy
```

### Использование ресурсов
```powershell
wsl docker stats captive-daemon --no-stream
```

### Логи в реальном времени
```powershell
Get-Content docker\daemon\logs\captive_portal_daemon.log -Tail 20 -Wait
```

## 🚀 Автозапуск

Для автозапуска при загрузке Windows:

```powershell
# Создать задачу в Task Scheduler
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-File C:\git\openwrt-captive-monitor\docker\daemon\manage.ps1 start"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
    -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "CaptivePortalDaemon" `
    -Action $action -Trigger $trigger -Principal $principal
```

## 📚 Документация

- [Docker Quick Start](DAEMON_DOCKER_QUICKSTART.md)
- [Docker Setup Complete](DAEMON_DOCKER_SETUP_COMPLETE.md)
- [Docker Daemon README](docker/daemon/README.md)
