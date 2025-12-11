# Руководство по установке

---

## 🌐 Язык

[English](installation.md) | [Deutsch](installation.de.md) | **[Русский](installation.ru.md)**

---

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
