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
- **OpenWrt роутер** - минимальный shell-скрипт для обнаружения captive portal
- **Внешний сервер** - Python-скрипт с Selenium для авторизации (Debian/Ubuntu на mini-PC с 4GB RAM)

**Рекомендуемое оборудование для сервера авторизации:**
- Raspberry Pi 3 или выше
- Любой x86-64 mini-PC с 4GB+ RAM
- Linux Mint / Ubuntu / Debian

Этот гибридный подход позволяет использовать преимущества обеих платформ: лёгкий мониторинг на роутере и мощную автоматизацию браузера на выделенном устройстве.

---

## ✨ Возможности

- **🔍 Автоматическая аутентификация** - Автоматически авторизуется на captive порталах одного типа
- **🔄 Поддержание сессии** - Проверки по расписанию (cron) гарантируют, что вы останетесь онлайн

> **Примечание**: Этот пакет разработан специально для captive порталов на базе Conn4.

## 🚀 Быстрый старт

### Системные требования

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- 4GB+ RAM (рекомендуется)
- Python 3.8+
- Chromium или Google Chrome

### Установка из .deb пакета

```bash
# Скачать последний пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_2026.1.16.5-1_all.deb

# Установить пакет
sudo dpkg -i openwrt-captive-monitor_*.deb

# Установить зависимости (если есть ошибки)
sudo apt-get install -f
```

Пакет автоматически:
1. Установит Python скрипт в `/usr/bin/captive-portal-monitor`
2. Установит systemd сервис для автозапуска
3. Включит сервис для автоматического запуска при загрузке

### Управление сервисом

```bash
# Запустить сервис
sudo systemctl start captive-portal-monitor

# Проверить статус
sudo systemctl status captive-portal-monitor

# Посмотреть логи
sudo journalctl -u captive-portal-monitor -f

# Остановить сервис
sudo systemctl stop captive-portal-monitor
```

### Сборка из исходного кода

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

📖 **Подробная документация:** [docs/debian-installation.md](docs/debian-installation.md)

## 🔧 Конфигурация

Сервис работает автоматически. Для настройки создайте файл `/etc/default/captive-portal-monitor`:

```bash
# OpenWrt роутер для SOCKS прокси
OPENWRT_SSH_HOST=192.168.1.1
OPENWRT_SSH_USER=root

# Порт SOCKS прокси (по умолчанию 10800)
NOJS_SOCKS_PORT=10800

# Окружение (dev или prod)
CPM_ENV=prod
```

## 🔍 Решение проблем

**Проверить логи:**
```bash
sudo journalctl -u captive-portal-monitor -n 50
```

**Запустить вручную:**
```bash
sudo /usr/bin/captive-portal-monitor
```

**Проверить статус:**
```bash
sudo systemctl status captive-portal-monitor
```

## 📄 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).
