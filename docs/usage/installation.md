# Installation Guide

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This guide covers the different ways to install **openwrt-captive-monitor** on your OpenWrt router.

## 📦 Installation Options

| Method | Best For | Complexity | Maintenance |
|--------|----------|------------|-------------|
| Prebuilt Package | Quick deployment, production use | ⭐ Easy | Automatic updates |
| SDK Build | Custom builds, development | ⭐⭐ Medium | Manual updates |
| Local Build | Testing, custom modifications | ⭐⭐⭐ Hard | Manual updates |

---

## 🚀 Method 1: Prebuilt Package (Recommended)

### Step 1: Download Package

Visit the [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) page and download the latest `.ipk` file for your architecture.

```bash
## Example for the latest release
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
```

### Step 2: Transfer to Router

```bash
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
```

### Step 3: Install Package

```bash
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

### Step 4: Configure and Start

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Enable the service
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Start the service
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start

## Check status
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔧 Method 2: OpenWrt SDK Build

### Prerequisites

- OpenWrt SDK matching your target architecture
- Build environment (Linux/macOS/WSL)

### Step 1: Download OpenWrt SDK

```bash
## Example for OpenWrt 22.03.5, ath79 target
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*
```

### Step 2: Add Package Source

```bash
## Clone this repository into the package directory
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor
```

### Step 3: Build Package

```bash
## Update package feeds
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor

## Build the package
make package/openwrt-captive-monitor/compile V=s
```

### Step 4: Locate and Install

The built package will be at:
```
bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk
```

```bash
## Transfer and install
scp bin/packages/*/base/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🛠️ Method 3: Local Build (Development)

### Prerequisites

Install build dependencies:

```bash
## Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Or use the build script that checks dependencies
scripts/build_ipk.sh --check-deps
```

### Step 1: Build Package

```bash
## Build for specific architecture
scripts/build_ipk.sh --arch mips_24kc

## Or build for all architectures
scripts/build_ipk.sh --arch all
```

### Step 2: Install

```bash
## The package is created in dist/opkg/<arch>/
scp dist/opkg/*/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🔍 Architecture Compatibility

| Architecture | OpenWrt Target | Package Name |
|--------------|---------------|--------------|
| `all` | Universal | `openwrt-captive-monitor_*_all.ipk` |
| `mips_24kc` | ath79, ramips | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| `aarch64_cortex-a53` | filogic, mediatek | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| `x86_64` | x86/64 | `openwrt-captive-monitor_*_x86_64.ipk` |

**Note**: The `all` architecture package works on most systems since this is a shell script package.

---

## 📋 Post-Installation Verification

### 1. Check Package Installation

```bash
ssh root@192.168.1.1 "opkg list-installed | grep captive-monitor"
```

### 2. Verify Service Files

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Check executable
ls -la /usr/sbin/openwrt_captive_monitor

## Check init script
ls -la /etc/init.d/captive-monitor

## Check configuration
cat /etc/config/captive-monitor
EOSSH
```

### 3. Test Service

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Enable service
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Start service
/etc/init.d/captive-monitor start

## Check logs
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔄 Upgrading

### From Prebuilt Package

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Download and install new version
wget -O /tmp/new-package.ipk "https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk"
opkg install /tmp/new-package.ipk

## Restart service
/etc/init.d/captive-monitor restart
EOSSH
```

### From Source

Follow the same build process as above, then install the new package. The upgrade process preserves your UCI configuration.

---

## 🗑️ Uninstallation

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Stop and disable service
/etc/init.d/captive-monitor stop
/etc/init.d/captive-monitor disable

## Remove package
opkg remove openwrt-captive-monitor

## Clean up configuration (optional)
uci delete captive-monitor.config
uci commit captive-monitor
EOSSH
```

---

## 🆘 Troubleshooting Installation

### Package Installation Fails

```bash
## Check package dependencies
opkg info openwrt-captive-monitor

## Check available space
df -h

## Check package integrity
file /tmp/openwrt-captive-monitor_*.ipk
```

### Service Won't Start

```bash
## Check service status
/etc/init.d/captive-monitor status

## Check logs
logread | grep captive-monitor

## Manual test
/usr/sbin/openwrt_captive_monitor --help
```

### Configuration Issues

```bash
## Validate UCI configuration
uci show captive-monitor

## Reset to defaults
uci revert captive-monitor
```

For more troubleshooting tips, see the [Troubleshooting Guide](../guides/troubleshooting.md).

---

# Русский

---

## 🌐 Язык

[English](#installation-guide) | **Русский**

---

# Руководство по установке

Это руководство охватывает различные способы установки **openwrt-captive-monitor** на вашем маршрутизаторе OpenWrt.

## 📦 Варианты установки

| Метод | Лучше всего для | Сложность | Обслуживание |
|--------|----------------|-----------|-------------|
| Готовый пакет | Быстрое развертывание, производственное использование | ⭐ Легко | Автоматические обновления |
| Сборка SDK | Пользовательские сборки, разработка | ⭐⭐ Средне | Ручные обновления |
| Локальная сборка | Тестирование, пользовательские модификации | ⭐⭐⭐ Сложно | Ручные обновления |

---

## 🚀 Метод 1: Готовый пакет (Рекомендуется)

### Шаг 1: Загрузка пакета

Посетите страницу [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) и загрузите последний файл `.ipk` для вашей архитектуры.

```bash
## Пример для последнего выпуска
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
```

### Шаг 2: Передача на маршрутизатор

```bash
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
```

### Шаг 3: Установка пакета

```bash
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

### Шаг 4: Конфигурация и запуск

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Включить сервис
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Запустить сервис
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start

## Проверить статус
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔧 Метод 2: Сборка OpenWrt SDK

### Предварительные требования

- OpenWrt SDK, соответствующий вашей целевой архитектуре
- Среда сборки (Linux/macOS/WSL)

### Шаг 1: Загрузка OpenWrt SDK

```bash
## Пример для OpenWrt 22.03.5, цели ath79
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*
```

### Шаг 2: Добавление источника пакета

```bash
## Клонировать этот репозиторий в директорию package
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor
```

### Шаг 3: Сборка пакета

```bash
## Обновить feed'ы пакетов
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor

## Собрать пакет
make package/openwrt-captive-monitor/compile V=s
```

### Шаг 4: Поиск и установка

Собранный пакет будет находиться по адресу:
```
bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk
```

```bash
## Передача и установка
scp bin/packages/*/base/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🛠️ Метод 3: Локальная сборка (Разработка)

### Предварительные требования

Установите зависимости сборки:

```bash
## Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Или используйте скрипт сборки, который проверяет зависимости
scripts/build_ipk.sh --check-deps
```

### Шаг 1: Сборка пакета

```bash
## Собрать для конкретной архитектуры
scripts/build_ipk.sh --arch mips_24kc

## Или собрать для всех архитектур
scripts/build_ipk.sh --arch all
```

### Шаг 2: Установка

```bash
## Пакет создается в dist/opkg/<arch>/
scp dist/opkg/*/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🔍 Совместимость архитектур

| Архитектура | Цель OpenWrt | Имя пакета |
|--------------|---------------|-------------|
| `all` | Универсальная | `openwrt-captive-monitor_*_all.ipk` |
| `mips_24kc` | ath79, ramips | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| `aarch64_cortex-a53` | filogic, mediatek | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| `x86_64` | x86/64 | `openwrt-captive-monitor_*_x86_64.ipk` |

**Примечание**: Пакет архитектуры `all` работает на большинстве систем, поскольку это пакет shell скриптов.

---

## 📋 Проверка после установки

### 1. Проверка установки пакета

```bash
ssh root@192.168.1.1 "opkg list-installed | grep captive-monitor"
```

### 2. Проверка файлов сервиса

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Проверить исполняемый файл
ls -la /usr/sbin/openwrt_captive_monitor

## Проверить init скрипт
ls -la /etc/init.d/captive-monitor

## Проверить конфигурацию
cat /etc/config/captive-monitor
EOSSH
```

### 3. Тестирование сервиса

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Включить сервис
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Запустить сервис
/etc/init.d/captive-monitor start

## Проверить логи
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔄 Обновление

### Из готового пакета

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Загрузить и установить новую версию
wget -O /tmp/new-package.ipk "https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk"
opkg install /tmp/new-package.ipk

## Перезапустить сервис
/etc/init.d/captive-monitor restart
EOSSH
```

### Из исходного кода

Следуйте тому же процессу сборки, что и выше, затем установите новый пакет. Процесс обновления сохраняет вашу конфигурацию UCI.

---

## 🗑️ Удаление

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Остановить и отключить сервис
/etc/init.d/captive-monitor stop
/etc/init.d/captive-monitor disable

## Удалить пакет
opkg remove openwrt-captive-monitor

## Очистить конфигурацию (опционально)
uci delete captive-monitor.config
uci commit captive-monitor
EOSSH
```

---

## 🆘 Устранение проблем с установкой

### Сбой установки пакета

```bash
## Проверить зависимости пакета
opkg info openwrt-captive-monitor

## Проверить доступное пространство
df -h

## Проверить целостность пакета
file /tmp/openwrt-captive-monitor_*.ipk
```

### Сервис не запускается

```bash
## Проверить статус сервиса
/etc/init.d/captive-monitor status

## Проверить логи
logread | grep captive-monitor

## Ручной тест
/usr/sbin/openwrt_captive_monitor --help
```

### Проблемы с конфигурацией

```bash
## Проверить конфигурацию UCI
uci show captive-monitor

## Сбросить до значений по умолчанию
uci revert captive-monitor
```

Для получения дополнительных советов по устранению проблем см. [Руководство по устранению неполадок](../guides/troubleshooting.md).
