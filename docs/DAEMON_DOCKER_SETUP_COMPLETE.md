# ✅ Captive Portal Daemon - Docker Setup Complete

## Что было сделано

### 1. Установка Docker в WSL

- ✅ Docker Engine 29.2.1 установлен в WSL
- ✅ Docker Compose включен
- ✅ Пользователь добавлен в группу docker
- ✅ Docker daemon запущен и работает

### 2. Создание Docker образа

Создан оптимизированный Docker образ с:
- Python 3.12-slim (базовый образ)
- Google Chrome stable (последняя версия)
- Selenium 4.40.0 с автоматическим Selenium Manager
- Все необходимые Python библиотеки
- Healthcheck для мониторинга

**Файлы:**
- `docker/daemon/Dockerfile` - определение образа
- `docker/daemon/docker-compose.yml` - конфигурация для docker-compose
- `docker/daemon/.env.example` - пример конфигурации

### 3. Скрипт управления

Создан PowerShell скрипт `docker/daemon/manage.ps1` с командами:
- `start` - запустить демон
- `stop` - остановить демон
- `restart` - перезапустить
- `status` - проверить статус
- `logs` - просмотр логов
- `build` - пересобрать образ
- `clean` - полная очистка

### 4. Документация

- `docker/daemon/README.md` - полная документация Docker версии
- `DAEMON_DOCKER_QUICKSTART.md` - краткая инструкция по запуску

## Текущий статус

```
CONTAINER: captive-daemon
STATUS: Up 2 minutes (healthy)
IMAGE: captive-portal-daemon:latest
NETWORK: host (доступ к локальной сети)
MEMORY LIMIT: 512MB
CPU LIMIT: 1.0
```

## Проверка работы

Демон успешно:
- ✅ Инициализировал Chrome через Selenium Manager
- ✅ Проверил авторизацию (http://www.msftconnecttest.com/redirect)
- ✅ Обнаружил активную авторизацию (редирект на MSN)
- ✅ Работает в фоновом режиме с интервалом 60 секунд

## Решённые проблемы

### Проблема 1: ChromeDriver несовместимость
**Было:** ChromeDriver из apt требовал snap chromium, но установлен Google Chrome
**Решение:** Использование Selenium Manager для автоматической загрузки совместимого ChromeDriver

### Проблема 2: Зависимости окружения
**Было:** Разные версии Chrome/ChromeDriver на разных системах
**Решение:** Docker образ с фиксированными версиями всех зависимостей

### Проблема 3: Сложная установка
**Было:** Нужно вручную устанавливать Chrome, ChromeDriver, Python библиотеки
**Решение:** Один Docker образ со всем необходимым

## Использование

### Запуск

```powershell
.\docker\daemon\manage.ps1 start
```

### Проверка статуса

```powershell
.\docker\daemon\manage.ps1 status
```

### Просмотр логов

```powershell
.\docker\daemon\manage.ps1 logs
```

Или напрямую:

```powershell
Get-Content docker\daemon\logs\captive_portal_daemon.log -Tail 50 -Wait
```

### Остановка

```powershell
.\docker\daemon\manage.ps1 stop
```

## Автозапуск при загрузке системы

### Windows (через Task Scheduler)

```powershell
# Создать задачу в Task Scheduler
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\git\openwrt-captive-monitor\docker\daemon\manage.ps1 start"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "CaptivePortalDaemon" -Action $action -Trigger $trigger -Principal $principal
```

### Linux (через systemd)

```bash
# Создать systemd unit
sudo nano /etc/systemd/system/captive-daemon.service
```

```ini
[Unit]
Description=Captive Portal Daemon (Docker)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/openwrt-captive-monitor/docker/daemon
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable captive-daemon
sudo systemctl start captive-daemon
```

## Мониторинг

### Healthcheck

Docker автоматически проверяет здоровье контейнера каждые 60 секунд:

```powershell
docker inspect captive-daemon --format='{{.State.Health.Status}}'
```

### Использование ресурсов

```powershell
docker stats captive-daemon --no-stream
```

### Логи Docker

```powershell
docker logs captive-daemon --tail 50 -f
```

## Обновление

### Обновить код демона

```powershell
# 1. Остановить демон
.\docker\daemon\manage.ps1 stop

# 2. Пересобрать образ
.\docker\daemon\manage.ps1 build

# 3. Запустить заново
.\docker\daemon\manage.ps1 start
```

### Обновить Chrome

Chrome обновляется автоматически при пересборке образа:

```powershell
.\docker\daemon\manage.ps1 build
.\docker\daemon\manage.ps1 restart
```

## Troubleshooting

### Демон не запускается

```powershell
# Проверить логи
.\docker\daemon\manage.ps1 logs

# Проверить Docker
wsl docker ps -a

# Пересоздать контейнер
.\docker\daemon\manage.ps1 stop
.\docker\daemon\manage.ps1 start
```

### Chrome падает

```powershell
# Проверить версию Chrome
docker exec captive-daemon google-chrome --version

# Проверить Selenium
docker exec captive-daemon python3 -c "import selenium; print(selenium.__version__)"

# Пересобрать образ
.\docker\daemon\manage.ps1 build
.\docker\daemon\manage.ps1 restart
```

### Высокое использование памяти

Изменить лимит в `docker-compose.yml`:

```yaml
mem_limit: 1g  # Вместо 512m
```

Затем:

```powershell
.\docker\daemon\manage.ps1 restart
```

## Следующие шаги

1. **Настроить автозапуск** - добавить в Task Scheduler или systemd
2. **Настроить мониторинг** - интеграция с Prometheus/Grafana
3. **Добавить уведомления** - отправка уведомлений при проблемах
4. **Оптимизировать интервал** - настроить CHECK_INTERVAL в .env

## Ссылки

- [Docker Daemon README](docker/daemon/README.md)
- [Quick Start Guide](DAEMON_DOCKER_QUICKSTART.md)
- [Main README](README.md)
