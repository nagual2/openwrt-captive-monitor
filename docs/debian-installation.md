# Установка Debian/Ubuntu пакета

## Системные требования

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- 4GB+ RAM (рекомендуется)
- Python 3.8+
- Chromium или Google Chrome

## Быстрая установка

### Вариант 1: Из GitHub Releases (Рекомендуется)

```bash
# Скачать последний .deb пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_2026.1.16.5-1_all.deb

# Установить пакет
sudo dpkg -i openwrt-captive-monitor_*.deb

# Установить зависимости (если есть ошибки)
sudo apt-get install -f
```

### Вариант 2: Сборка из исходного кода

```bash
# Клонировать репозиторий
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Собрать пакет
bash scripts/build_deb.sh

# Установить
sudo dpkg -i dist/deb/openwrt-captive-monitor_*.deb
sudo apt-get install -f
```

## Конфигурация

### Переменные окружения

Файл `/etc/default/captive-portal-monitor` создаётся автоматически при установке:

```bash
# Использовать cron вместо systemd (по умолчанию: false)
# Установите "true" для использования cron, "false" для systemd
USE_CRON=false

# OpenWrt роутер для SOCKS прокси
OPENWRT_SSH_HOST=192.168.1.1
OPENWRT_SSH_USER=root

# Порт SOCKS прокси (по умолчанию 10800)
NOJS_SOCKS_PORT=10800

# Окружение (dev или prod)
CPM_ENV=prod

# Язык браузера
SELENIUM_ACCEPT_LANGUAGE=en-US,en;q=0.9
```

### Выбор режима запуска

**Режим systemd (по умолчанию):**
- Сервис постоянно работает в фоне
- Автоматический перезапуск при падении (каждые 60 секунд)
- Управление через `systemctl`
- Логи через `journalctl`

**Режим cron:**
- Скрипт запускается каждую минуту через cron
- Автоматическая блокировка предотвращает множественные запуски
- Подходит для минимального использования ресурсов
- Аналогично установке на Minisforum

**Переключение на cron:**

```bash
# 1. Отредактируйте конфигурацию
sudo nano /etc/default/captive-portal-monitor
# Установите: USE_CRON=true

# 2. Переустановите пакет для применения
sudo apt-get install --reinstall openwrt-captive-monitor

# Или вручную:
sudo systemctl stop captive-portal-monitor
sudo systemctl disable captive-portal-monitor
(crontab -l 2>/dev/null; echo "* * * * * /usr/bin/captive-portal-wrapper") | crontab -
```

**Переключение обратно на systemd:**

```bash
# 1. Отредактируйте конфигурацию
sudo nano /etc/default/captive-portal-monitor
# Установите: USE_CRON=false

# 2. Переустановите пакет
sudo apt-get install --reinstall openwrt-captive-monitor
```

### SSH ключи

Настройте SSH доступ к OpenWrt роутеру без пароля:

```bash
# Сгенерировать SSH ключ (если еще нет)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Скопировать публичный ключ на роутер
ssh-copy-id root@192.168.1.1

# Проверить подключение
ssh root@192.168.1.1 "uname -a"
```

## Управление сервисом

```bash
# Запустить сервис
sudo systemctl start captive-portal-monitor

# Остановить сервис
sudo systemctl stop captive-portal-monitor

# Перезапустить сервис
sudo systemctl restart captive-portal-monitor

# Проверить статус
sudo systemctl status captive-portal-monitor

# Включить автозапуск
sudo systemctl enable captive-portal-monitor

# Отключить автозапуск
sudo systemctl disable captive-portal-monitor
```

## Просмотр логов

```bash
# Последние 50 строк
sudo journalctl -u captive-portal-monitor -n 50

# Следить за логами в реальном времени
sudo journalctl -u captive-portal-monitor -f

# Логи за последний час
sudo journalctl -u captive-portal-monitor --since "1 hour ago"

# Логи за сегодня
sudo journalctl -u captive-portal-monitor --since today
```

## Ручной запуск (для отладки)

```bash
# Запустить скрипт вручную
/usr/bin/captive-portal-monitor

# С переменными окружения
OPENWRT_SSH_HOST=192.168.1.1 /usr/bin/captive-portal-monitor
```

## Удаление

```bash
# Остановить и отключить сервис
sudo systemctl stop captive-portal-monitor
sudo systemctl disable captive-portal-monitor

# Удалить пакет
sudo apt-get remove openwrt-captive-monitor

# Удалить пакет и конфигурацию
sudo apt-get purge openwrt-captive-monitor
```

## Решение проблем

### Проблема: Сервис не запускается

```bash
# Проверить логи
sudo journalctl -u captive-portal-monitor -n 100

# Проверить зависимости
dpkg -l | grep -E "python3-selenium|chromium"

# Переустановить зависимости
sudo apt-get install --reinstall python3-selenium chromium-browser chromium-chromedriver
```

### Проблема: Не удается подключиться к роутеру

```bash
# Проверить SSH подключение
ssh root@192.168.1.1 "uname -a"

# Проверить SOCKS прокси
curl --socks5 127.0.0.1:10800 http://example.com
```

### Проблема: Chrome не найден

```bash
# Установить Chromium
sudo apt-get install chromium-browser chromium-chromedriver

# Или Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f
```

## Архитектура

```
┌─────────────────┐         SSH Tunnel          ┌──────────────┐
│  Debian Server  │◄──────── (SOCKS5) ─────────►│ OpenWrt      │
│  (4GB+ RAM)     │                              │ Router       │
│                 │                              │              │
│  ┌───────────┐  │                              │ ┌──────────┐ │
│  │ Selenium  │  │                              │ │ Captive  │ │
│  │ + Chrome  │  │                              │ │ Portal   │ │
│  └───────────┘  │                              │ │ Detector │ │
│                 │                              │ └──────────┘ │
└─────────────────┘                              └──────────────┘
        │                                                │
        │                                                │
        └────────────► Авторизация ◄────────────────────┘
                    на Captive Portal
```

## Рекомендуемое оборудование

- **Raspberry Pi 3+** - минимум 1GB RAM, рекомендуется 2GB+
- **Raspberry Pi 4** - 4GB RAM (оптимально)
- **x86-64 mini-PC** - 4GB+ RAM (Intel NUC, Minisforum и т.д.)
- **Виртуальная машина** - 2 CPU, 4GB RAM

## Дополнительная информация

- [Основной README](../README.ru.md)
- [Troubleshooting](troubleshooting.md)
- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues)
