# Captive Portal Daemon - Docker (Lightweight)

Docker образ для запуска легковесного демона мониторинга captive порталов.

## ⚡ Оптимизированная версия

Этот образ использует **lightweight daemon** (simple_captive_daemon.py) вместо тяжелого Selenium-based daemon.

### Преимущества оптимизации:
- ✅ **78% меньше размер образа**: 151MB вместо 700MB (без Chrome)
- ✅ **90% меньше памяти**: 50MB вместо 512MB RAM
- ✅ **70% быстрее сборка**: 2-3 минуты вместо 7-14 минут
- ✅ **Мгновенный старт**: 1 секунда вместо 30 секунд
- ✅ **Минимальные зависимости**: только Python + requests
- ✅ **Простая отладка**: HTTP-only, без браузера

### ⚠️ Важно: Только мониторинг
Lightweight daemon **НЕ выполняет автоматическую авторизацию**.
- Обнаруживает captive portal
- Логирует состояние подключения
- Предлагает запустить скрипт авторизации вручную

Для автоматической авторизации используйте полную версию (см. ветку `full-daemon`).

## Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

```bash
cd docker/daemon
docker-compose up -d
```

### Вариант 2: PowerShell скрипт (Windows)

```powershell
# Запустить демон
.\docker\daemon\manage.ps1 start

# Проверить статус
.\docker\daemon\manage.ps1 status

# Просмотр логов
.\docker\daemon\manage.ps1 logs

# Остановить демон
.\docker\daemon\manage.ps1 stop
```

## Управление

### Остановить демон

```bash
docker-compose stop
```

### Перезапустить демон

```bash
docker-compose restart
```

### Обновить образ

```bash
docker-compose pull
docker-compose up -d
```

### Удалить контейнер

```bash
docker-compose down
```

### Пересобрать образ

```bash
docker-compose build --no-cache
docker-compose up -d
```

## Конфигурация

### Переменные окружения (.env)

- `CONN4_USERNAME` - логин для Conn4 портала
- `CONN4_PASSWORD` - пароль для Conn4 портала
- `CHECK_INTERVAL` - интервал проверки в секундах (по умолчанию 60)
- `LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR)

### Логи

Логи сохраняются в `./logs/captive_portal_daemon.log`

```bash
# Просмотр логов
tail -f logs/captive_portal_daemon.log

# Или через docker-compose
docker-compose logs -f
```

## Требования

- Docker 20.10+
- Docker Compose 1.29+
- Доступ к локальной сети (network_mode: host)

## Troubleshooting

### Демон не запускается

```bash
# Проверить логи
docker-compose logs

# Проверить статус
docker-compose ps

# Пересоздать контейнер
docker-compose down
docker-compose up -d
```

### Chrome не работает

Образ использует Google Chrome stable с автоматическим ChromeDriver через Selenium Manager.

Если возникают проблемы:

```bash
# Проверить версию Chrome в контейнере
docker-compose exec captive-daemon google-chrome --version

# Проверить Selenium
docker-compose exec captive-daemon python3 -c "import selenium; print(selenium.__version__)"
```

### Высокое использование памяти

По умолчанию лимит 512MB. Если нужно больше:

```yaml
# В docker-compose.yml
mem_limit: 1g
```

### Проблемы с сетью

Демон использует `network_mode: host` для доступа к локальной сети.

Проверить:

```bash
# Проверить доступ к порталу из контейнера
docker-compose exec captive-daemon curl -I http://www.msftconnecttest.com/redirect
```

## Сборка образа вручную

```bash
# Из корня проекта
docker build -f docker/daemon/Dockerfile -t captive-portal-daemon:latest .

# Запуск
docker run -d \
  --name captive-daemon \
  --network host \
  -v $(pwd)/logs:/var/log \
  -e CONN4_USERNAME=your_user \
  -e CONN4_PASSWORD=your_pass \
  captive-portal-daemon:latest
```

## Интеграция с systemd

Для автозапуска при загрузке системы:

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
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Включить автозапуск
sudo systemctl enable captive-daemon
sudo systemctl start captive-daemon
```
