# OpenWrt Package Build Instructions for Windows

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---


## 🚀 Самый простой способ: GitHub Actions (РЕКОМЕНДУЕТСЯ)

Проект автоматически собирает пакеты через GitHub Actions. Готовые .ipk файлы можно скачать напрямую:

### Шаг 1: Перейдите в Actions
1. Откройте: https://github.com/nagual2/openwrt-captive-monitor/actions
2. Найдите последний успешный run workflow "Build OpenWrt packages"
3. Скачайте артефакты для нужной архитектуры

### Шаг 2: Выберите архитектуру
- **ath79-generic** (mips_24kc) - для старых роутеров TP-Link, D-Link
- **ramips-mt7621** (mipsel_24kc) - для новых роутеров Xiaomi, TP-Link

### Шаг 3: Установка на роутер
```bash
## Скопируйте .ipk файл на роутер
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/

## Установите пакет
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

## 🔧 Альтернативный способ: Локальная сборка

Если нужно собрать самостоятельно, есть несколько вариантов:

### Вариант 1: Docker Desktop (Windows)
```bash
## Установите Docker Desktop для Windows
## Затем создайте Dockerfile для сборки
```

### Вариант 2: WSL (Windows Subsystem for Linux)
```bash
## Включите WSL в Windows Features
wsl --install

## В WSL установите инструменты
sudo apt update
sudo apt install build-essential git wget xz-utils

## Скачайте и соберите
wget https://downloads.openwrt.org/releases/23.05.3/targets/ath79/generic/openwrt-sdk-23.05.3-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cp -r package/openwrt-captive-monitor openwrt-sdk-*/package/
cd openwrt-sdk-*
make package/openwrt-captive-monitor/compile V=s
```

### Вариант 3: Git Bash + дополнительные утилиты
```bash
## Установите MSYS2 или Cygwin для дополнительных Unix утилит
## В MSYS2:
pacman -S base-devel tar gzip

## Для команды 'ar' (нужна для .ipk):
pacman -S binutils
```

## 📦 Проверка готового пакета

Если сборка удалась, в папке `dist/opkg/<arch>/` появятся:
- `openwrt-captive-monitor_<version>_<arch>.ipk` - сам пакет
- `Packages` и `Packages.gz` - индексы для opkg feed

## 🏃‍♂️ Быстрый тест

После установки проверьте:
```bash
## На роутере
opkg list | grep captive-monitor
/etc/init.d/captive-monitor status
```

## 📚 Дополнительная информация

- Подробные инструкции: [../../README.md](../../README.md#build-with-the-openwrt-sdk--buildroot)
- Release checklist: [../RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md)
- Troubleshooting: [../../docs/openwrt_captive_monitor_README.md](../../docs/openwrt_captive_monitor_README.md)

**Рекомендация:** Используйте GitHub Actions - это самый надежный и быстрый способ получить готовые пакеты без установки дополнительных инструментов!
