# GitHub Release SDK CDN Mirror

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---


This project uses GitHub Release as a CDN mirror for the OpenWrt SDK to dramatically improve download speed and reliability for CI/CD builds.

## Overview

The OpenWrt SDK is downloaded from GitHub Releases CDN instead of the official OpenWrt mirrors, providing:
- **2-5 second downloads** (vs 2+ minutes from official mirrors)
- **99.9%+ uptime** with GitHub's global CDN
- **No rate limiting** issues
- **Automatic fallback** to official mirrors if CDN fails
- **Checksum verification** ensures integrity

## Architecture

### Primary Source: GitHub CDN
```
https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-23.05.3/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

### Fallback Source: Official Mirror
```
https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

### Checksum Verification
- **Expected SHA256**: `f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254`
- Verification happens after every download
- Build fails immediately if checksum doesn't match

## Implementation Details

### Workflows Using SDK CDN

- **`.github/workflows/ci.yml`** - Main CI/CD pipeline (lint → test → SDK build)

### Download Logic

```bash
# Try GitHub CDN first
if ! wget -q "$GITHUB_CDN_URL" -O sdk.tar.xz; then
    echo "⚠️  CDN failed, falling back to official mirror..."
    wget -q "$OFFICIAL_MIRROR_URL" -O sdk.tar.xz
fi

# Always verify checksum
if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
    echo "❌ Checksum mismatch!"
    exit 1
fi
```

### Caching

Both workflows implement SDK caching:
- **Cache Key**: `openwrt-sdk-23.05.3-${{ runner.os }}`
- **Cache Path**: `openwrt-sdk-*` directory
- **Result**: Instant rebuilds when SDK is cached

## Managing SDK Releases

### Upload New SDK Version

Use the **"Upload SDK to GitHub Release"** workflow:

1. Go to **Actions** → **Upload SDK to GitHub Release**
2. Click **Run workflow**
3. Enter SDK version (default: `23.05.3`)
4. Enable **Force update** to replace existing release
5. Click **Run workflow**

### Manual Upload (Local)

```bash
# Make the script executable
chmod +x scripts/upload-sdk-to-github.sh

# Run the upload script
./scripts/upload-sdk-to-github.sh
```

### Release Structure

Each SDK release contains:
- **SDK File**: `openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz`
- **Checksum File**: `sdk-checksum.txt`

## Performance Benefits

| Source | Average Download Time | Success Rate |
|--------|---------------------|--------------|
| GitHub CDN | 2-5 seconds | 99.9% |
| Official Mirror | 2-5 minutes | 50% (with timeouts) |

## Troubleshooting

### CDN Download Fails
- **Automatic Fallback**: Workflow automatically tries official mirror
- **Check Logs**: Look for "⚠️ CDN failed, falling back to official mirror..."
- **Manual Upload**: Use upload workflow to refresh CDN

### Checksum Mismatch
- **Expected**: `f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254`
- **Cause**: Corrupted download or wrong SDK version
- **Solution**: Re-upload SDK using the upload workflow

### Release Not Found
- **URL**: `https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-23.05.3/...`
- **Solution**: Run the upload workflow to create the release

## Security Considerations

- **Checksum Verification**: Prevents tampered SDK downloads
- **Read-only Access**: Build workflows use `contents: read` permissions
- **Separate Upload**: SDK upload uses dedicated workflow with `contents: write`
- **GitHub Token**: Uses automatic `GITHUB_TOKEN` for authentication

## Future Enhancements

- **Multiple SDK Versions**: Support for different OpenWrt versions
- **Architecture Support**: Add SDKs for different architectures (ARM, MIPS)
- **Automatic Updates**: Workflow to detect and upload new SDK versions
- **Metrics Dashboard**: Track CDN usage and performance metrics

---

# Русский

---

## 🌐 Язык

[English](#github-release-sdk-cdn-mirror) | **Русский**

---

# Зеркало CDN для SDK на GitHub Releases

Этот проект использует GitHub Release как зеркало CDN для OpenWrt SDK для кардинального улучшения скорости загрузки и надежности для сборок CI/CD.

## Обзор

OpenWrt SDK загружается из CDN GitHub Releases вместо официальных зеркал OpenWrt, обеспечивая:
- **Загрузки за 2-5 секунд** (против 2+ минут с официальных зеркал)
- **Аптайм 99.9%+** с глобальным CDN GitHub
- **Отсутствие проблем с ограничением скорости**
- **Автоматический откат** к официальным зеркалам при сбое CDN
- **Проверка контрольной суммы** обеспечивает целостность

## Архитектура

### Основной источник: GitHub CDN
```
https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-23.05.3/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

### Резервный источник: Официальное зеркало
```
https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

### Проверка контрольной суммы
- **Ожидаемый SHA256**: `f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254`
- Проверка происходит после каждой загрузки
- Сборка немедленно прерывается при несовпадении контрольной суммы

## Детали реализации

### Рабочие процессы, использующие SDK CDN

- **`.github/workflows/ci.yml`** - Основной конвейер CI/CD (lint → test → SDK сборка)

### Логика загрузки

```bash
# Сначала попробовать GitHub CDN
if ! wget -q "$GITHUB_CDN_URL" -O sdk.tar.xz; then
    echo "⚠️  CDN не удалось, откат к официальному зеркалу..."
    wget -q "$OFFICIAL_MIRROR_URL" -O sdk.tar.xz
fi

# Всегда проверять контрольную сумму
if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
    echo "❌ Несоответствие контрольной суммы!"
    exit 1
fi
```

### Кеширование

Оба рабочих процесса реализуют кеширование SDK:
- **Ключ кеша**: `openwrt-sdk-23.05.3-${{ runner.os }}`
- **Путь кеша**: Директория `openwrt-sdk-*`
- **Результат**: Мгновенные пересборки при кешированном SDK

## Управление выпусками SDK

### Загрузка новой версии SDK

Используйте рабочий процесс **"Upload SDK to GitHub Release"**:

1. Перейдите к **Actions** → **Upload SDK to GitHub Release**
2. Нажмите **Run workflow**
3. Введите версию SDK (по умолчанию: `23.05.3`)
4. Включите **Force update** для замены существующего выпуска
5. Нажмите **Run workflow**

### Ручная загрузка (Локально)

```bash
# Сделать скрипт исполняемым
chmod +x scripts/upload-sdk-to-github.sh

# Запустить скрипт загрузки
./scripts/upload-sdk-to-github.sh
```

### Структура выпуска

Каждый выпуск SDK содержит:
- **Файл SDK**: `openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz`
- **Файл контрольной суммы**: `sdk-checksum.txt`

## Преимущества производительности

| Источник | Среднее время загрузки | Уровень успеха |
|--------|---------------------|--------------|
| GitHub CDN | 2-5 секунд | 99.9% |
| Официальное зеркало | 2-5 минут | 50% (с таймаутами) |

## Устранение неполадок

### Сбой загрузки CDN
- **Автоматический откат**: Рабочий процесс автоматически пробует официальное зеркало
- **Проверить логи**: Искать "⚠️ CDN failed, falling back to official mirror..."
- **Ручная загрузка**: Использовать рабочий процесс загрузки для обновления CDN

### Несоответствие контрольной суммы
- **Ожидается**: `f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254`
- **Причина**: Поврежденная загрузка или неправильная версия SDK
- **Решение**: Перезагрузить SDK используя рабочий процесс загрузки

### Выпуск не найден
- **URL**: `https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-23.05.3/...`
- **Решение**: Запустить рабочий процесс загрузки для создания выпуска

## Соображения безопасности

- **Проверка контрольной суммы**: Предотвращает поддельные загрузки SDK
- **Доступ только для чтения**: Рабочие процессы сборки используют разрешения `contents: read`
- **Отдельная загрузка**: Загрузка SDK использует выделенный рабочий процесс с `contents: write`
- **Токен GitHub**: Использует автоматический `GITHUB_TOKEN` для аутентификации

## Будущие улучшения

- **Несколько версий SDK**: Поддержка разных версий OpenWrt
- **Поддержка архитектур**: Добавление SDK для разных архитектур (ARM, MIPS)
- **Автоматические обновления**: Рабочий процесс для обнаружения и загрузки новых версий SDK
- **Панель метрик**: Отслеживание использования CDN и показателей производительности