# Simplified CI Workflow

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This document explains the simplified CI/CD workflow implemented for openwrt-captive-monitor.

## Overview

The CI workflow has been streamlined to follow the documented OpenWrt SDK workflow pattern. The previous approach using `make distclean` and `make toolchain/install` has been replaced with a simpler, more direct SDK usage pattern.

## Pipeline Structure

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌───────────┐
│  Lint   │ --> │   Test   │ --> │  SDK Build │ --> │  Artifact │
│         │     │          │     │            │     │   Upload  │
└─────────┘     └──────────┘     └────────────┘     └───────────┘
```

## Workflow Steps

### 1. Lint (Parallel)

Runs multiple linters in parallel to ensure code quality:

- **shfmt**: Shell script formatting
- **shellcheck**: Shell script static analysis
- **markdownlint**: Documentation linting
- **actionlint**: GitHub Actions workflow linting

### 2. Test

Runs the BusyBox-based test harness:

```bash
busybox ash tests/run.sh
```

Tests include:
- Mock-based unit tests
- Package validation
- Configuration parsing
- Script logic verification

### 3. SDK Build

Builds the package using the OpenWrt SDK following the documented workflow:

**Steps:**
1. Download and extract OpenWrt SDK (with caching)
2. Copy package files to SDK
3. Update feeds: `./scripts/feeds update -a`
4. Install feeds: `./scripts/feeds install -a`
5. Configure SDK: `make defconfig`
6. Build package: `make package/openwrt-captive-monitor/compile V=s`
7. Validate built `.ipk`
8. Upload artifacts

**Key Points:**
- Uses prebuilt toolchain from SDK (no `make toolchain/install`)
- No `make distclean` before build
- Relies on SDK's built-in configuration
- Simple, straightforward workflow

### 4. Artifact Upload

Uploads build artifacts to GitHub Actions:

- `.ipk` package file
- `Packages` index file
- `Packages.gz` compressed index
- `build.log` verbose build output

## Simplified Approach

### What Changed

**Before:**
```bash
make defconfig
make distclean        # Clean everything
make defconfig        # Reconfigure
make toolchain/install V=s  # Build toolchain (10-30 minutes)
# Copy package
# Update feeds
make package/.../compile
```

**After:**
```bash
# Download SDK
# Copy package
./scripts/feeds update -a
./scripts/feeds install -a
make defconfig
make package/.../compile
```

### Benefits

1. **Faster builds**: No toolchain compilation (saves 10-30 minutes)
2. **Simpler workflow**: Fewer steps, clearer intent
3. **Standard approach**: Follows documented OpenWrt SDK usage
4. **Prebuilt toolchain**: Relies on SDK's included toolchain
5. **More reliable**: Fewer moving parts, less room for error

### Why This Works

The OpenWrt SDK comes with a prebuilt cross-compilation toolchain that includes:
- GCC compiler
- Musl C library and loader (`ld-musl-*.so`)
- Build system tools
- Package dependencies

By using the SDK as intended, we avoid the complexity of rebuilding the toolchain and can focus on package compilation.

## SDK Caching

The workflow uses GitHub Actions cache to speed up subsequent builds:

```yaml
Cache Key: ${{ runner.os }}-openwrt-sdk-${{ version }}-${{ arch }}-v3
```

**First build:**
- Downloads SDK (~500MB-1GB)
- Extracts SDK
- Cache saved

**Subsequent builds:**
- Restores SDK from cache (< 1 minute)
- Skips download and extraction

## Error Handling

The workflow includes robust error handling:

- **SDK download failures**: Retries with exponential backoff, falls back to official mirror
- **Feed update failures**: 10 retry attempts with jitter
- **Build failures**: Captures last 100 lines of build log
- **Validation failures**: Runs `validate_ipk.sh` script

## Artifact Management

Build artifacts are:
- Uploaded to GitHub Actions (30-day retention)
- Available for download from workflow runs
- Automatically attached to releases on tag pushes

## Release Integration

The workflow integrates with the release process:

1. **Release Please** creates release PR and tag
2. **CI workflow** triggered by tag push
3. **SDK build job** compiles package
4. **Artifacts** automatically uploaded to GitHub release

## Documentation References

- [SDK Build Workflow Guide](../guides/sdk-build-workflow.md)
- [Release Checklist](../RELEASE_CHECKLIST.md)
- [Packaging Guide](../packaging.md)

## Troubleshooting

### Build Failures

Check the build log in artifacts:
```bash
# Download and extract artifacts from workflow run
cat build.log
```

### Package Not Found

Verify package was copied to SDK:
```bash
ls -la "$SDK_DIR/package/openwrt-captive-monitor/"
```

### Feed Issues

Check feed update logs for network errors or repository issues.

## Further Reading

- [OpenWrt SDK Documentation](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk)
- [OpenWrt Build System](https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials)
- [Package Build Guide](https://openwrt.org/docs/guide-developer/packages)

---

# Русский

---

## 🌐 Язык

[English](#simplified-ci-workflow) | **Русский**

---

# Упрощенный рабочий процесс CI

Этот документ объясняет упрощенный рабочий процесс CI/CD, реализованный для openwrt-captive-monitor.

## Обзор

Рабочий процесс CI был упрощен для следования документированному шаблону рабочего процесса OpenWrt SDK. Предыдущий подход с использованием `make distclean` и `make toolchain/install` был заменен более простым, более прямым шаблоном использования SDK.

## Структура конвейера

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌───────────┐
│  Lint   │ --> │   Test   │ --> │  SDK Build │ --> │  Artifact │
│         │     │          │     │            │     │   Upload  │
└─────────┘     └──────────┘     └────────────┘     └───────────┘
```

## Шаги рабочего процесса

### 1. Линтинг (Параллельно)

Запускает несколько линтеров параллельно для обеспечения качества кода:

- **shfmt**: Форматирование shell скриптов
- **shellcheck**: Статический анализ shell скриптов
- **markdownlint**: Линтинг документации
- **actionlint**: Линтинг рабочих процессов GitHub Actions

### 2. Тестирование

Запускает тестовый набор на основе BusyBox:

```bash
busybox ash tests/run.sh
```

Тесты включают:
- Модульные тесты на основе mock'ов
- Валидацию пакета
- Парсинг конфигурации
- Проверку логики скрипта

### 3. Сборка SDK

Собирает пакет используя OpenWrt SDK следуя документированному рабочему процессу:

**Шаги:**
1. Загрузить и извлечь OpenWrt SDK (с кешированием)
2. Скопировать файлы пакета в SDK
3. Обновить feed'ы: `./scripts/feeds update -a`
4. Установить feed'ы: `./scripts/feeds install -a`
5. Сконфигурировать SDK: `make defconfig`
6. Собрать пакет: `make package/openwrt-captive-monitor/compile V=s`
7. Валидировать собранный `.ipk`
8. Загрузить артефакты

**Ключевые моменты:**
- Использует предсобранный toolchain из SDK (без `make toolchain/install`)
- Нет `make distclean` перед сборкой
- Полагается на встроенную конфигурацию SDK
- Простой, понятный рабочий процесс

### 4. Загрузка артефактов

Загружает артефакты сборки в GitHub Actions:

- Файл пакета `.ipk`
- Индексный файл `Packages`
- Сжатый индекс `Packages.gz`
- Детальный вывод сборки `build.log`

## Упрощенный подход

### Что изменилось

**До:**
```bash
make defconfig
make distclean        # Очистить все
make defconfig        # Переконфигурировать
make toolchain/install V=s  # Собрать toolchain (10-30 минут)
# Скопировать пакет
# Обновить feed'ы
make package/.../compile
```

**После:**
```bash
# Загрузить SDK
# Скопировать пакет
./scripts/feeds update -a
./scripts/feeds install -a
make defconfig
make package/.../compile
```

### Преимущества

1. **Более быстрые сборки**: Нет компиляции toolchain (экономит 10-30 минут)
2. **Простее рабочий процесс**: Меньше шагов, яснее намерение
3. **Стандартный подход**: Следует документированному использованию OpenWrt SDK
4. **Предсобранный toolchain**: Полагается на включенный в SDK toolchain
5. **Более надежно**: Меньше движущихся частей, меньше места для ошибок

### Почему это работает

OpenWrt SDK поставляется с предсобранным cross-compilation toolchain, который включает:
- GCC компилятор
- Musl C библиотеку и загрузчик (`ld-musl-*.so`)
- Инструменты сборки
- Зависимости пакетов

Используя SDK как предполагалось, мы избегаем сложности пересборки toolchain и можем сфокусироваться на компиляцию пакета.

## Кеширование SDK

Рабочий процесс использует кеш GitHub Actions для ускорения последующих сборок:

```yaml
Cache Key: ${{ runner.os }}-openwrt-sdk-${{ version }}-${{ arch }}-v3
```

**Первая сборка:**
- Загружает SDK (~500MB-1GB)
- Извлекает SDK
- Кеш сохраняется

**Последующие сборки:**
- Восстанавливает SDK из кеша (< 1 минуты)
- Пропускает загрузку и извлечение

## Обработка ошибок

Рабочий процесс включает надежную обработку ошибок:

- **Сбои загрузки SDK**: Повторные попытки с экспоненциальным откатом, откат к официальному зеркалу
- **Сбои обновления feed'ов**: 10 повторных попыток с джиттером
- **Сбои сборки**: Захватывает последние 100 строк лога сборки
- **Сбои валидации**: Запускает скрипт `validate_ipk.sh`

## Управление артефактами

Артефакты сборки:
- Загружаются в GitHub Actions (хранение 30 дней)
- Доступны для загрузки из запусков рабочих процессов
- Автоматически прикрепляются к выпускам при推送 тегов

## Интеграция с выпусками

Рабочий процесс интегрируется с процессом выпуска:

1. **Release Please** создает PR выпуска и тег
2. **Рабочий процесс CI** запускается при推送 тега
3. **Задание сборки SDK** компилирует пакет
4. **Артефакты** автоматически загружаются в выпуск GitHub

## Ссылки на документацию

- [Руководство по рабочему процессу сборки SDK](../guides/sdk-build-workflow.md)
- [Контрольный список выпуска](../RELEASE_CHECKLIST.md)
- [Руководство по упаковке](../packaging.md)

## Устранение неполадок

### Сбои сборки

Проверить лог сборки в артефактах:
```bash
# Загрузить и извлечь артефакты из запуска рабочего процесса
cat build.log
```

### Пакет не найден

Проверить, что пакет был скопирован в SDK:
```bash
ls -la "$SDK_DIR/package/openwrt-captive-monitor/"
```

### Проблемы с feed'ами

Проверить логи обновления feed'ов на сетевые ошибки или проблемы репозитория.

## Дополнительное чтение

- [Документация OpenWrt SDK](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk)
- [Система сборки OpenWrt](https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials)
- [Руководство по сборке пакетов](https://openwrt.org/docs/guide-developer/packages)
