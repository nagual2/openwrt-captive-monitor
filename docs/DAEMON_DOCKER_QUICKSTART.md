# Captive Portal Daemon - Docker Quick Start

## ✅ Преимущества Docker версии

- Все зависимости включены (Chrome, ChromeDriver, Python)
- Работает одинаково на Windows, Linux, macOS
- Автоматический перезапуск при сбоях
- Изолированное окружение
- Простое обновление

## 🚀 Быстрый старт

### Windows (PowerShell)

```powershell
# Запустить демон
.\docker\daemon\manage.ps1 start

# Проверить статус
.\docker\daemon\manage.ps1 status

# Просмотр логов в реальном времени
.\docker\daemon\manage.ps1 logs

# Остановить демон
.\docker\daemon\manage.ps1 stop

# Перезапустить
.\docker\daemon\manage.ps1 restart
```

### Linux / WSL

```bash
# Запустить демон
cd docker/daemon
docker-compose up -d

# Проверить статус
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановить
docker-compose stop
```

## 📋 Логи

Логи сохраняются в `docker/daemon/logs/captive_portal_daemon.log`

```powershell
# Windows
Get-Content docker\daemon\logs\captive_portal_daemon.log -Tail 50 -Wait

# Linux
tail -f docker/daemon/logs/captive_portal_daemon.log
```

## ⚙️ Конфигурация

Создай файл `docker/daemon/.env` для настройки:

```bash
# Conn4 credentials (опционально)
CONN4_USERNAME=your_username
CONN4_PASSWORD=your_password

# Интервал проверки (секунды)
CHECK_INTERVAL=60

# Уровень логирования
LOG_LEVEL=INFO
```

## 🔧 Управление

### Пересборка образа

```powershell
# Windows
.\docker\daemon\manage.ps1 build
.\docker\daemon\manage.ps1 restart

# Linux
docker-compose build --no-cache
docker-compose up -d
```

### Полная очистка

```powershell
# Windows
.\docker\daemon\manage.ps1 clean

# Linux
docker-compose down
docker rmi captive-portal-daemon:latest
```

## 📊 Мониторинг

```powershell
# Статус контейнера
docker ps --filter name=captive-daemon

# Использование ресурсов
docker stats captive-daemon

# Логи Docker
docker logs captive-daemon --tail 50 -f
```

## ❓ Troubleshooting

### Демон не запускается

```powershell
# Проверить логи
.\docker\daemon\manage.ps1 logs

# Пересоздать контейнер
.\docker\daemon\manage.ps1 stop
.\docker\daemon\manage.ps1 start
```

### Chrome не работает

Образ использует Google Chrome stable с автоматическим Selenium Manager.

```powershell
# Проверить версию Chrome в контейнере
docker exec captive-daemon google-chrome --version

# Пересобрать образ
.\docker\daemon\manage.ps1 build
.\docker\daemon\manage.ps1 restart
```

### Высокое использование памяти

По умолчанию лимит 512MB. Изменить в `docker-compose.yml`:

```yaml
mem_limit: 1g
```

## 📚 Дополнительная информация

- Полная документация: [docker/daemon/README.md](docker/daemon/README.md)
- Основной проект: [README.md](README.md)
