# openwrt-captive-monitor


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Язык

[English](README.md) | [Deutsch](README.de.md) | **Русский**

---

## ✨ Возможности

- **🔍 Автоматическая аутентификация** - Автоматически авторизуется на Conn4 captive порталах (например, отели Leonardo)
- **⚡ Легковесность** - Простой shell-скрипт (~10KB), без тяжелых зависимостей
- **🔄 Поддержание сессии** - Проверки по расписанию (cron) гарантируют, что вы останетесь онлайн
- **🛡️ Безопасность** - Использует стандартные системные утилиты (`curl`)

> **Примечание**: Этот пакет разработан специально для captive порталов на базе Conn4.

## 🚀 Быстрый старт

### Предварительные требования

- OpenWrt 21.02+ (или любая система с `opkg`, `curl` и `cron`)
- Пакет `curl` установлен (автоматически обрабатывается как зависимость)

### Установка

#### Вариант 1: Готовый пакет (Рекомендуется)

```bash
## Загрузить последний пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

## Установить на маршрутизатор
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

Пакет автоматически:
1. Установит скрипт авторизации в `/usr/sbin/auth_conn4.sh`
2. Добавит задание cron в `/etc/crontabs/root` для запуска каждую минуту
3. Перезапустит службу cron

#### Вариант 2: Сборка из исходного кода

```bash
## Клонировать репозиторий
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Собрать пакет
scripts/build_ipk.sh --arch all

## Установить
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

## 🔧 Конфигурация

Конфигурация не требуется (Zero-Touch). Скрипт автоматически определяет URL портала.

Чтобы отключить или изменить расписание, отредактируйте корневой crontab:

```bash
crontab -e
```

Запись по умолчанию:
```cron
*/1 * * * * /usr/sbin/auth_conn4.sh
```

## 🔍 Решение проблем

**Проверить логи:**
```bash
logread | grep conn4_auth
```

**Запустить вручную:**
```bash
sh /usr/sbin/auth_conn4.sh
```

**Проверить установку:**
```bash
ls -l /usr/sbin/auth_conn4.sh
grep auth_conn4 /etc/crontabs/root
```

## 📄 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).
