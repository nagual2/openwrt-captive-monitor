# Установка на Debian/Ubuntu (Docker)

## Системные требования

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker (`curl -fsSL https://get.docker.com | sudo sh`)
- 4GB+ RAM (рекомендуется)
- x86-64 архитектура

## Быстрая установка

### Вариант 1: Из GitHub Releases (Рекомендуется)

```bash
# Установить Docker (если ещё не установлен)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Скачать последний .deb пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Установить пакет
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

Пакет автоматически:
1. Загрузит Docker образ с Chrome и Selenium
2. Установит systemd сервис `captive-daemon`
3. Запустит daemon

### Вариант 2: Docker Compose

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon

cp .env.example .env
# Отредактируйте .env при необходимости

docker compose up -d
```

### Вариант 3: Сборка deb пакета из исходного кода

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Собрать пакет (требует Docker)
bash scripts/build_deb_docker.sh

# Установить
sudo dpkg -i dist/deb-docker/openwrt-captive-monitor-docker_*.deb
```

## Конфигурация

Файл `/etc/default/captive-daemon` создаётся автоматически при установке:

```bash
# Интервал проверки в секундах (по умолчанию: 60)
CHECK_INTERVAL=60

# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Conn4 credentials (опционально)
CONN4_USERNAME=
CONN4_PASSWORD=
```

## Управление сервисом

```bash
# Запустить сервис
sudo systemctl start captive-daemon

# Остановить сервис
sudo systemctl stop captive-daemon

# Перезапустить сервис
sudo systemctl restart captive-daemon

# Проверить статус
sudo systemctl status captive-daemon

# Включить автозапуск
sudo systemctl enable captive-daemon

# Отключить автозапуск
sudo systemctl disable captive-daemon
```

## Просмотр логов

```bash
# Через journalctl
sudo journalctl -u captive-daemon -f

# Через файл логов
tail -f /var/log/captive-daemon/captive_portal_daemon.log

# Через Docker
docker logs captive-daemon --tail 50
docker logs captive-daemon -f
```

## Удаление

```bash
# Остановить и удалить
sudo systemctl stop captive-daemon
sudo dpkg -r openwrt-captive-monitor-docker

# Удалить Docker образ
sudo docker rmi captive-portal-daemon:latest
```

## Решение проблем

### Docker не установлен

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable docker
sudo systemctl start docker
```

### Контейнер не запускается

```bash
# Проверить логи
docker logs captive-daemon

# Проверить статус Docker
sudo systemctl status docker

# Пересоздать контейнер
sudo systemctl restart captive-daemon
```

### Высокое использование памяти

Docker контейнер ограничен 512MB RAM. Если нужно больше, отредактируйте systemd unit:

```bash
sudo systemctl edit captive-daemon
# Добавьте: Environment="DOCKER_MEM_LIMIT=1g"
```

### Chrome не работает в контейнере

```bash
# Проверить Chrome в контейнере
docker exec captive-daemon google-chrome --version

# Проверить Selenium
docker exec captive-daemon python3 -c "import selenium; print(selenium.__version__)"
```

## Архитектура

```
┌──────────────────────────────┐
│  Docker Container            │
│  ┌────────────────────────┐  │
│  │ Python Daemon          │  │
│  │ + Selenium + Chrome    │  │
│  │                        │  │
│  │ Проверка каждые 60с:   │  │
│  │ 1. HTTP probe          │  │
│  │ 2. Portal detection    │  │
│  │ 3. Auto-auth           │  │
│  └────────────────────────┘  │
│  network_mode: host          │
└──────────────────────────────┘
         │
         │ Captive Portal Auth
         ▼
┌──────────────────────────────┐
│  Conn4 Portal (conn4.com)    │
│  - Checkbox accept           │
│  - "Get Free Wi-Fi" button   │
└──────────────────────────────┘
```

## Дополнительная информация

- [Основной README](../README.ru.md)
- [Docker Daemon README](../docker/daemon/README.md)
- [Troubleshooting](troubleshooting.md)
- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues)
