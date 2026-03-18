# openwrt-captive-monitor 🐳

Гибридная система автоматизации для captive порталов на базе Conn4 (например, Leonardo Hotels). Легковесный мониторинг на OpenWrt и мощная браузерная авторизация на выделенном Docker-устройстве.

---

## ✨ Возможности

- **🔍 Автоматическая авторизация** — использует Selenium & Chromium для прохождения сложных порталов
- **🐳 Docker упаковка** — все зависимости (Chrome, Selenium, Python) упакованы в единый образ на базе Debian
- **🔄 Поддержание сессии** — оптимизированный демон мониторит соединение и переавторизуется только при необходимости
- **🛡️ Безопасность и чистота** — работа в изолированном Docker окружении с лимитами ресурсов

## 🚀 Быстрый старт

### Системные требования

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker & Docker Compose
- 512MB+ RAM (лимит Docker инстанса)

### Вариант 1: Установка из .deb пакета (Рекомендуется)

Самый простой способ развертывания на Debian-совместимом сервере.

```bash
# Скачать последний пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Установить
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

### Вариант 2: Docker Compose (Локальная сборка)

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon-selenium

# Собрать и запустить
docker compose up -d
```

## 🔧 Управление

### Использование PowerShell (Windows/WSL)
Используйте скрипт управления в `docker/daemon-selenium/manage.ps1`:
```powershell
.\manage.ps1 status    # Проверить статус
.\manage.ps1 logs      # Посмотреть логи
.\manage.ps1 restart   # Перезапустить демон
```

### Использование Docker CLI
```bash
# Статус контейнера
docker ps -a --filter name=captive-daemon

# Просмотр логов
docker logs -f captive-daemon
```

## ⚙️ Конфигурация

Файл куков (на хосте): `/var/lib/captive-daemon/cookies.pkl` (управляется автоматически)
Окружение Systemd: `/etc/default/captive-daemon`

```bash
CHECK_INTERVAL=60
LOG_LEVEL=INFO
```

## 📦 Пакет OpenWrt

Для роутера (Xiaomi AX3000T и др.) вы можете собрать и установить легковесный пакет `.ipk` с помощью OpenWrt SDK:

```bash
# Сборка через OpenWrt SDK (см. docs/docker-master.md)
# Затем установка на роутер:
opkg install openwrt-captive-monitor_*.ipk
```

📖 **Подробная документация:** [docs/docker-master.md](docs/docker-master.md)

## 📄 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).
