# openwrt-captive-monitor

[![CI](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml/badge.svg?branch=main&label=CI)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml?query=branch%3Amain)
[![Security Scanning](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/security-scanning.yml/badge.svg?branch=main&label=Security)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/security-scanning.yml?query=branch%3Amain)
[![Package Build](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml/badge.svg?branch=main&label=Package%20Build)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml?query=branch%3Amain)
[![Release](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml/badge.svg?branch=main&label=Release)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Язык

[English](README.md) | [Deutsch](README.de.md) | **Русский**

---

## ✨ Возможности

- **🔍 Автоматическое обнаружение** - Обнаружение портала аутентификации без вмешательства пользователя
- **🌐 Перехват трафика** - Временное перенаправление DNS/HTTP трафика на портал
- **🔄 Самовосстановление** - Автоматическое восстановление нормальной работы после аутентификации
- **⚡ Легковесность** - Минимальное использование ресурсов на оборудовании маршрутизатора
- **🛡️ Безопасность в приоритете** - HTTPS трафик никогда не перехватывается, приватность сохраняется
- **🔧 Гибкая конфигурация** - UCI, переменные окружения и опции командной строки
- **📊 Надежный мониторинг** - Множество методов обнаружения и резервных вариантов

> **Примечание**: IPv6 не поддерживается. Сервис работает только в режиме IPv4.

## 🏗️ Обзор архитектуры

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Клиентские    │    │   Маршрутизатор │    │   Внешняя       │
│   устройства    │◄──►│   (OpenWrt +    │◄──►│   сеть          │
│                 │    │   Captive       │    │                 │
│                 │    │   Monitor)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

Сервис плотно интегрируется со стеком сетевых компонентов OpenWrt:
- **dnsmasq** - Перехват DNS для перенаправления клиентов
- **iptables/nftables** - Перехват трафика и перенаправление
- **procd** - Управление сервисами и мониторинг
- **UCI** - Управление конфигурацией

## 🚀 Быстрый старт

### Предварительные требования

- OpenWrt 21.02+ (рекомендуется 22.03+)
- Корневой доступ к маршрутизатору
- 64МБ+ ОЗУ (рекомендуется 128МБ+)

### Установка

#### Вариант 1: Готовый пакет (Рекомендуется)

```bash
## Загрузить последний пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

## Установить на маршрутизатор
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

#### Вариант 2: Сборка из исходного кода

**Локальная сборка (Простая):**
```bash
## Клонировать репозиторий
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Собрать пакет локально
scripts/build_ipk.sh --arch all

## Установить собранный пакет
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

**Сборка через SDK (Официальный способ):**
```bash
## Клонировать репозиторий
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Проект использует OpenWrt SDK для официальной сборки
## См.: docs/guides/sdk-build-workflow.md

## Для локальной сборки через SDK:
wget https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*/
cp -r ../package/openwrt-captive-monitor package/
./scripts/feeds update -a && ./scripts/feeds install -a
make package/openwrt-captive-monitor/compile V=s
```

> **Примечание**: Конвейер CI/CD автоматически собирает пакеты с помощью официального OpenWrt SDK. Подробнее см. [docs/guides/sdk-build-workflow.md](docs/guides/sdk-build-workflow.md).

### Базовая конфигурация

```bash
## Включить сервис
ssh root@192.168.1.1 <<'EOSSH'
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
EOSSH
```

### Проверка

```bash
## Проверить статус сервиса
ssh root@192.168.1.1 "logread | grep captive-monitor | tail -5"
```

## 📋 Содержание

- [Установка](#-быстрый-старт)
  - [Предварительные требования](#предварительные-требования)
  - [Установка](#установка)
  - [Базовая конфигурация](#базовая-конфигурация)
- [Варианты установки](#-варианты-установки)
  - [Матрица установки](#матрица-установки)
  - [Сборка через OpenWrt SDK](#сборка-через-openwrt-sdk)
  - [Зависимости](#зависимости)
- [Конфигурация](#-конфигурация)
  - [Базовые настройки](#базовые-настройки)
  - [Продвинутые опции](#продвинутые-опции)
  - [Переменные окружения](#переменные-окружения)
- [Использование](#-использование)
  - [Режимы работы](#режимы-работы)
  - [Мониторинг](#мониторинг)
- [Решение проблем](#-решение-проблем)
  - [Часто встречаемые проблемы](#часто-встречаемые-проблемы)
  - [Проверка здоровья](#проверка-здоровья)
- [Разработка](#-разработка)
  - [Сборка](#сборка)
  - [Тестирование](#тестирование)
  - [Как внести вклад](#как-внести-вклад)
- [Документация](#-документация)
- [Сообщество](#-сообщество)
  - [Поддержка](#поддержка)
  - [Безопасность](#безопасность)
  - [Вклад](#вклад)
- [Статус проекта](#-статус-проекта)
  - [Последний выпуск](#последний-выпуск)
  - [Совместимость](#совместимость)
- [Лицензия](#-лицензия)
- [Благодарности](#-благодарности)
- [Связанные проекты](#-связанные-проекты)

## 📦 Варианты установки

### Матрица установки

| Метод | Сценарий использования | Сложность | Обслуживание |
| ----- | ---------------------- | --------- | ------------ |
| **Готовый пакет** | Производство, быстрое развертывание | ⭐ Легко | Автоматические обновления |
| **Сборка через SDK** | Пользовательские сборки, разработка | ⭐⭐ Среднее | Ручные обновления |
| **Локальная сборка** | Тестирование, модификации | ⭐⭐⭐ Сложно | Ручные обновления |

### Сборка через OpenWrt SDK

```bash
## Загрузить OpenWrt SDK
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

## Добавить источник пакета
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor

## Собрать пакет
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor
make package/openwrt-captive-monitor/compile V=s
```

### Зависимости

**Зависимости во время выполнения:**
- `dnsmasq` - DNS и DHCP сервер
- `curl` - HTTP пробы и обнаружение портала
- `iptables` или `nftables` - Перенаправление трафика

**Зависимости сборки:**
- `binutils`, `busybox`, `gzip`, `pigz`, `tar`, `xz-utils`

## 🔧 Конфигурация

### Базовые настройки

```uci
config captive_monitor 'config'
    option enabled '1'                    # Включить сервис
    option mode 'monitor'                 # monitor или oneshot
    option wifi_interface 'phy1-sta0'       # WiFi интерфейс
    option wifi_logical 'wwan'              # Логический интерфейс
    option monitor_interval '60'            # Интервал проверки (секунды)
    option ping_servers '1.1.1.1 8.8.8.8'   # Серверы для ping
    option enable_syslog '1'               # Включить логирование
```

### Продвинутые опции

```uci
config captive_monitor 'config'
    # Сетевые настройки
    option lan_interface 'br-lan'           # LAN интерфейс (автоопределение)
    option firewall_backend 'auto'            # iptables/nftables/auto
    
    # Настройки времени
    option ping_timeout '2'                 # Timeout ping
    option http_probe_timeout '5'            # Timeout HTTP пробы
    option gateway_check_retries '2'         # Повторы проверки шлюза
    
    # Обнаружение портала
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
```

### Переменные окружения

```bash
## Переопределить конфигурацию
export MONITOR_INTERVAL="30"
export WIFI_INTERFACE="wlan0"
export PING_SERVERS="1.1.1.1 9.9.9.9"
export CAPTIVE_DEBUG="1"
```

## 📖 Использование

### Режимы работы

#### Режим монитора (По умолчанию)

Непрерывный мониторинг с указанным интервалом:

```bash
## Начать мониторинг
/usr/sbin/openwrt_captive_monitor --monitor

## С пользовательским интервалом
/usr/sbin/openwrt_captive_monitor --monitor --interval 30
```

#### Режим Oneshot

Однократная проверка и выход, идеально для cron:

```bash
## Однократная проверка
/usr/sbin/openwrt_captive_monitor --oneshot

## Cron задание (каждые 15 минут)
*/15 * * * * /usr/sbin/openwrt_captive_monitor --oneshot
```

### Мониторинг

**Статус сервиса:**
```bash
## Проверить запущен ли сервис
ps aux | grep openwrt_captive_monitor

## Статус сервиса
/etc/init.d/captive-monitor status

## Последние логи
logread | grep captive-monitor | tail -20
```

**Режим отладки:**
```bash
## Подробный вывод
/usr/sbin/openwrt_captive_monitor --oneshot --verbose

## Режим отладки
export CAPTIVE_DEBUG="1"
/usr/sbin/openwrt_captive_monitor --oneshot
```

## 🔍 Решение проблем

### Часто встречаемые проблемы

**Сервис не запускается:**
```bash
## Проверить конфигурацию
uci show captive-monitor

## Проверить права доступа
ls -la /usr/sbin/openwrt_captive_monitor

## Ручной тест
/usr/sbin/openwrt_captive_monitor --help
```

**Портал аутентификации не обнаруживается:**
```bash
## Проверить URL обнаружения вручную
curl -I http://connectivitycheck.gstatic.com/generate_204
curl -I http://detectportal.firefox.com/success.txt

## Добавить пользовательские URL
uci add_list captive-monitor.config.captive_check_urls='http://your-portal.com/detect'
```

**Перенаправление не работает:**
```bash
## Проверить правила файервола
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

## Проверить переопределения DNS
cat /tmp/dnsmasq.d/captive_intercept.conf

## Перезагрузить сервисы
/etc/init.d/dnsmasq restart
```

### Проверка здоровья

```bash
## Комплексная проверка здоровья
/usr/local/bin/captive-health-check.sh

## Ручная очистка (если необходимо)
/usr/sbin/openwrt_captive_monitor --force-cleanup
```

## 🧪 Разработка

### Оптимизированная система сборки

Проект использует оптимизированную систему сборки CI/CD с предварительно собранными Docker SDK образами:

**Возможности:**
- ⚡ **На 2-3 минуты быстрее** сборки с использованием Docker SDK образов
- 🐳 Предварительно собранные образы в GitHub Container Registry (GHCR)
- 🔄 Автоматическое обновление и очистка образов
- 📦 Поддержка 8 архитектур OpenWrt

**Время сборки:**
- С Docker SDK: ~1.5-2.5 минут
- Традиционный SDK: ~3-5 минут
- **Экономия: 40-60%**

📖 См. [Документация Docker SDK образов](docs/docker-sdk-images.md) для подробностей.

### Сборка

```bash
## Установить зависимости сборки
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Собрать пакет
scripts/build_ipk.sh --arch all

## Проверить пакет
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Тестирование

```bash
## Запустить тесты
busybox sh tests/run.sh

## Тестирование на ВМ на основе OpenWrt
./scripts/run_openwrt_vm.sh

## Проверка кода
shellcheck openwrt_captive_monitor.sh
shfmt -i 2 -ci -sr -d openwrt_captive_monitor.sh

## Ручное тестирование
/usr/sbin/openwrt_captive_monitor --oneshot --verbose
```

#### Виртуальная машина для тестирования

Проект включает комплексную систему тестирования на основе ВМ, которая автоматизирует сквозную валидацию:

- **Автоматическая подготовка ВМ OpenWrt** с QEMU/KVM
- **Сборка и установка пакета** в изолированную среду
- **Дымовые тесты** для базовых, портала аутентификации и режимов монитора
- **Сбор артефактов** для отладки и анализа
- **Готовность для CI/CD** с резервным использованием эмуляции TCG

```bash
# Базовое тестирование на ВМ
./scripts/run_openwrt_vm.sh

# Пользовательская конфигурация
./scripts/run_openwrt_vm.sh --openwrt-version 23.05 --workdir /tmp/test

# CI окружение (без KVM)
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

Подробнее см. [Руководство виртуализации](docs/guides/virtualization.md).

### Создание релиза

Этот проект использует **ручной рабочий процесс релизов** для создания новых выпусков. Поддерживающие могут запускать релизы по запросу через GitHub Actions.

**Создание нового релиза:**

1. Перейдите в **Actions** → **Manual Release** в репозитории GitHub
2. Нажмите **"Run workflow"**
3. Настройте релиз (все поля необязательны):
   - **Custom version**: Укажите версию, например `2025.11.27.1`, или оставьте пустым для автоматической генерации на основе текущей даты
   - **Release notes**: Предоставьте собственные примечания к релизу, или оставьте пустым для автоматической генерации
   - **Pre-release**: Отметьте этот флажок, чтобы пометить релиз как предварительный
4. Нажмите **"Run workflow"** для запуска процесса релиза

**Что происходит во время релиза:**

Рабочий процесс автоматически:
- Генерирует или использует указанный тег версии (`vYYYY.M.D.N`)
- Обновляет файл `VERSION` и `PKG_VERSION` в Makefile
- Создает коммит с изменениями версии
- Создает и отправляет git тег
- Собирает универсальный пакет (`arch=all`)
- Проверяет пакет
- Создает GitHub Release с прикрепленным пакетом
- Загружает файл `.ipk` и `SHA256SUMS` в релиз

**Формат версии:**
- **Тег:** `vYYYY.M.D.N` (например, `v2025.11.27.1`)
- **Файл VERSION:** `YYYY.M.D.N` (без префикса `v`)
- **PKG_VERSION** в Makefile: `YYYY.M.D.N`
- **PKG_RELEASE:** всегда `1` для официальных релизов

> **Пример:**
> - Тег: `v2025.11.27.1`
> - Файл `VERSION`: `2025.11.27.1`
> - `package/openwrt-captive-monitor/Makefile`:
>   - `PKG_VERSION:=2025.11.27.1`
>   - `PKG_RELEASE:=1`

**Параметры рабочего процесса:**

| Параметр       | Описание                              | Обязательный | По умолчанию                         |
| -------------- | ------------------------------------- | ------------ | ------------------------------------ |
| `version`       | Пользовательская версия (например, `2025.11.27.1`) | Нет | Автогенерация из текущей даты |
| `release_notes` | Пользовательские примечания к релизу | Нет          | Автогенерация из git коммитов        |
| `prerelease`    | Пометить как предварительный релиз   | Нет          | `false`                              |

Для подробной информации о процессе релизов см.:
- [Manual Release Workflow](.github/workflows/manual-release.yml)
- [Auto Version Tag Guide](docs/release/AUTO_VERSION_TAG.md)
- [Release Process Documentation](docs/release/RELEASE_PROCESS.md)

### Как внести вклад

1. Форк репозитория
2. Создайте ветку функции (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения используя соглашения о коммитах (`git commit -m 'feat: add amazing feature'`)
4. Отправьте ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

Подробнее см. [CONTRIBUTING.md](docs/contributing/CONTRIBUTING.md).

## 📚 Документация

- [Индекс документации](docs/index.md) - Полные руководства и справочники
- [Руководство быстрого старта](docs/usage/quick-start.md) - Начните за минуты
- [Справочник конфигурации](docs/configuration/reference.md) - Все опции конфигурации
- [Руководство по решению проблем](docs/guides/troubleshooting.md) - Частые проблемы и решения
- [Обзор архитектуры](docs/guides/architecture.md) - Проектирование систем и компоненты
- [Процесс релизов](docs/release/RELEASE_PROCESS.md) - Рабочий процесс релизов и версионирование
- [Восстановление релизов](docs/release/RELEASE_RESTORATION.md) - Восстановление отсутствующих релизов

## 🤝 Сообщество

### Поддержка

- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Отчеты об ошибках и запросы функций
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - Общие вопросы и помощь
- [Документация](docs/index.md) - Полные руководства и справочники

### Безопасность

- [Политика безопасности](.github/SECURITY.md) - Отчеты об уязвимостях безопасности
- [Рекомендации по безопасности](https://github.com/nagual2/openwrt-captive-monitor/security/advisories) - Уведомления о безопасности
- [Сканирование безопасности](docs/SECURITY_SCANNING.md) - Документация по автоматизированному сканированию безопасности

### Вклад

- [Руководство по вкладу](docs/contributing/CONTRIBUTING.md) - Рекомендации по разработке и процесс PR
- [Кодекс поведения](docs/contributing/CODE_OF_CONDUCT.md) - Рекомендации сообщества
- [Управление проектом](docs/project/management.md) - Дорожная карта и процесс выпуска

## 📊 Статус проекта

### Последний выпуск

- **Версия**: v1.0.6 (См. [страницу выпусков](https://github.com/nagual2/openwrt-captive-monitor/releases) для подробностей)
- **Лицензия**: [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
- **Платформа**: [![OpenWrt](https://img.shields.io/badge/OpenWrt-21.02%2B-blue.svg)](https://openwrt.org/)

### Совместимость

| Версия OpenWrt | Статус | Примечания |
| -------------- | ------ | --------- |
| 21.02 (LTS) | ✅ Поддерживается | Использует бэкэнд iptables |
| 22.03 (LTS) | ✅ Поддерживается | Автоопределение бэкэнда |
| 23.05 (Stable) | ✅ Поддерживается | Полная поддержка nftables |
| 24.10 (Development) | ✅ Поддерживается | Последние функции |

| Архитектура | Статус | Пакет |
| ----------- | ------ | ----- |
| mips_24kc | ✅ Поддерживается | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| aarch64_cortex-a53 | ✅ Поддерживается | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| x86_64 | ✅ Поддерживается | `openwrt-captive-monitor_*_x86_64.ipk` |
| all | ✅ Универсальный | `openwrt-captive-monitor_*_all.ipk` |

## 📄 Лицензия

Этот проект лицензирован под [MIT License](LICENSE) - см. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- **Сообщество OpenWrt** - За отличную прошивку маршрутизатора и инструменты
- **Проект BusyBox** - Предоставление необходимых утилит Unix для встроенных систем
- **Участники** - Каждый, кто помогал улучшать этот проект

## 🔗 Связанные проекты

- [uspot](https://github.com/f00b4r0/uspot) - Полнофункциональный портал аутентификации для OpenWrt
- [apfree-wifidog](https://github.com/liudf0716/apfree-wifidog) - Высокопроизводительный портал аутентификации
- [CaptivePortalAutologin](https://github.com/jsparber/CaptivePortalAutologin) - Приложение Android для автоматического входа

---

<div align="center">
[📖 Документация](docs/) • [🐛 Проблемы](https://github.com/nagual2/openwrt-captive-monitor/issues) • [💬 Обсуждения](https://github.com/nagual2/openwrt-captive-monitor/discussions)

Сделано с ❤️ для сообщества OpenWrt

</div>
