# openwrt-captive-monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Язык

[English](README.md) | [Deutsch](README.de.md) | **Русский**

---

## 🤖 О разработке проекта

Этот проект полностью разработан с помощью AI-агентов и прошёл длительный путь эволюции. Изначально начавшись как простой shell-скрипт для OpenWrt, проект развился до полноценного Python-решения на базе библиотеки Selenium.

В процессе отладки выяснилось, что на компактных роутерах с ограниченными ресурсами невозможно реализовать надёжную авторизацию через браузерные технологии. Скрипты на базе Selenium требуют значительного объёма оперативной памяти (минимум 2-4 GB) и полноценный браузер Chrome/Chromium.

**Текущая архитектура:**
- **OpenWrt роутер** — минимальный shell-скрипт для обнаружения captive portal и авторизации через curl
- **Внешний сервер (Docker)** — Python daemon с Selenium для браузерной авторизации

**Рекомендуемое оборудование для сервера авторизации:**
- Raspberry Pi 3 или выше
- Любой x86-64 mini-PC с 4GB+ RAM
- Linux Mint / Ubuntu / Debian

Этот гибридный подход позволяет использовать преимущества обеих платформ: лёгкий мониторинг на роутере и мощную автоматизацию браузера на выделенном устройстве.

---

## ✨ Возможности

- **🔍 Автоматическая аутентификация** — Автоматически авторизуется на captive порталах Conn4 (напр. Leonardo Hotels)
- **🐳 Docker упаковка** — Все зависимости (Chrome, Selenium, Python) в одном контейнере
- **🔄 Поддержание сессии** — Daemon непрерывно мониторит подключение и переавторизуется при необходимости
- **🛡️ Безопасность** — Изолированное Docker окружение, без системных зависимостей

> **Примечание**: Этот пакет разработан специально для captive порталов на базе Conn4.

## 🚀 Быстрый старт

### Системные требования

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker (`curl -fsSL https://get.docker.com | sudo sh`)
- 4GB+ RAM (рекомендуется)

### Вариант 1: Установка из .deb пакета (Рекомендуется)

Deb пакет включает предсобранный Docker образ и systemd сервис.

```bash
# Скачать последний пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Установить
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

Пакет автоматически:
1. Загрузит Docker образ
2. Установит systemd сервис
3. Запустит daemon

### Вариант 2: Docker Compose

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon

cp .env.example .env
# Отредактируйте .env при необходимости

docker compose up -d
```

### Вариант 3: Docker Run

```bash
# Собрать образ
docker build -f docker/daemon/Dockerfile -t captive-portal-daemon:latest .

# Запустить
docker run -d \
  --name captive-daemon \
  --network host \
  --restart unless-stopped \
  -v /var/log/captive-daemon:/var/log \
  -v /dev/shm:/dev/shm \
  -e CHECK_INTERVAL=60 \
  captive-portal-daemon:latest
```

## 🔧 Управление сервисом

```bash
# Проверить статус
sudo systemctl status captive-daemon

# Просмотр логов
sudo journalctl -u captive-daemon -f
# или
tail -f /var/log/captive-daemon/captive_portal_daemon.log

# Перезапустить
sudo systemctl restart captive-daemon

# Остановить
sudo systemctl stop captive-daemon
```

## ⚙️ Конфигурация

Отредактируйте `/etc/default/captive-daemon`:

```bash
# Интервал проверки в секундах (по умолчанию: 60)
CHECK_INTERVAL=60

# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## 📦 Пакет для OpenWrt

Для роутеров OpenWrt доступен легковесный shell-скрипт:

```bash
# Скачать из GitHub Releases
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_latest_all.ipk

# Установить на роутере
opkg install openwrt-captive-monitor_*.ipk
```

OpenWrt пакет использует `curl` для HTTP-авторизации без браузерных зависимостей.

## 🔍 Решение проблем

**Статус контейнера:**
```bash
docker ps -a --filter name=captive-daemon
```

**Логи daemon:**
```bash
docker logs captive-daemon --tail 50
```

**Перезапуск:**
```bash
docker restart captive-daemon
```

**Пересборка образа:**
```bash
docker compose -f docker/daemon/docker-compose.yml build --no-cache
docker compose -f docker/daemon/docker-compose.yml up -d
```

📖 **Подробная документация:** [docs/debian-installation.md](docs/debian-installation.md)

## 📄 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).
