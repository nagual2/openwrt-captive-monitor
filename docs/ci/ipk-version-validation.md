# IPK Version Validation

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

## Overview

The CI pipeline includes automated validation of `.ipk` package version metadata to ensure correct version suffix handling based on the build context (main branch vs. pull requests).

## Validation Rules

### Main Branch Builds

Packages built from the `main` branch **must** include a `-dev` suffix in their Version field:

- **Pattern**: `^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$`
- **Examples**:
  - `1.0.8-dev`
  - `1.0.8-dev-20240101`
  - `1.0.8-dev-2024010112`

### Pull Request Builds

Packages built from pull requests **must NOT** include a `-dev` suffix:

- **Pattern**: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`
- **Examples**:
  - `1.0.8`
  - `1.0.8-20240101`
  - `1.0.8-2024010112`

### PKG_RELEASE Validation

The validation also checks for date-based release suffixes:

- **Format**: `YYYYMMDD` or `YYYYMMDDHHMM`
- **Example**: `20240101` or `202401011530`

## Implementation

### Script Location

The validation is implemented in `scripts/validate-ipk-version.sh`.

### How It Works

1. Extracts the `.ipk` archive (which is an `ar` archive).
2. Extracts the `control.tar.gz` from the package.
3. Reads the `control` file metadata.
4. Validates the `Version` field against branch-specific regex patterns.
5. Optionally validates the PKG_RELEASE date format.
6. Exits with code 0 on success, 1 on failure.

### CI Integration

The validation runs in two CI jobs:

1. **build-dev-package** (main branch only):
   - Validates packages include a `-dev` suffix.
   - Step: "Validate IPK version metadata".

2. **build-pr-package** (pull requests only):
   - Validates packages do **NOT** include a `-dev` suffix.
   - Step: "Validate IPK version metadata".

## Usage

### Manual Validation

You can manually validate an `.ipk` file:

```bash
# For main branch packages (should have -dev)
./scripts/validate-ipk-version.sh package.ipk main

# For PR packages (should NOT have -dev)
./scripts/validate-ipk-version.sh package.ipk pr
```

### CI Validation

The validation runs automatically in CI after building packages. It checks all `.ipk` files in the artifacts directory.

## Troubleshooting

### Validation Failures

If validation fails, check:

1. **Main branch**: Ensure `DEV_SUFFIX=1` is set during the SDK build.
2. **Pull requests**: Ensure `DEV_SUFFIX=0` or unset during the SDK build.
3. **Makefile**: Verify the package `Makefile` correctly appends `-dev` when `DEV_SUFFIX=1`.

### Expected Error Messages

**Main branch without -dev**:

```text
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' suffix (e.g., 1.0.8-dev or 1.0.8-dev-20240101)
  Got: 1.0.8-20240101
```

**PR with -dev**:

```text
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for PR/non-main branch
  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)
  Got: 1.0.8-dev-20240101
```

## Related Files

- `scripts/validate-ipk-version.sh` – Validation script.
- `.github/workflows/ci.yml` – CI workflow with validation steps.
- `package/openwrt-captive-monitor/Makefile` – Package Makefile with `DEV_SUFFIX` logic.
- `scripts/lib/colors.sh` – Color output library.

## Design Rationale

The `-dev` suffix distinguishes **development** builds from **stable** releases:

- **Development builds** (main branch) are continuous and may contain breaking changes.
- **PR builds** represent candidate changes that could be merged.
- **Release builds** (tags) are stable and versioned releases.

This validation ensures that packages are correctly labeled based on their build context, preventing confusion between development and stable versions.

---

# Русский

---

## 🌐 Язык

[English](#ipk-version-validation) | **Русский**

---

## Обзор

Конвейер CI включает автоматическую проверку метаданных версии `.ipk`‑пакетов, чтобы обеспечить корректную обработку суффиксов версии в зависимости от контекста сборки (ветка `main` против pull request'ов).

## Правила валидации

### Сборки из ветки main

Пакеты, собранные из ветки `main`, **должны** содержать суффикс `-dev` в поле `Version`:

- **Шаблон**: `^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$`
- **Примеры**:
  - `1.0.8-dev`
  - `1.0.8-dev-20240101`
  - `1.0.8-dev-2024010112`

### Сборки из pull request'ов

Пакеты, собранные в контексте pull request, **НЕ должны** содержать суффикс `-dev`:

- **Шаблон**: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`
- **Примеры**:
  - `1.0.8`
  - `1.0.8-20240101`
  - `1.0.8-2024010112`

### Проверка PKG_RELEASE

Дополнительно проверяется дата‑суффикс релиза:

- **Формат**: `YYYYMMDD` или `YYYYMMDDHHMM`
- **Примеры**: `20240101` или `202401011530`

## Реализация

### Расположение скрипта

Логика проверки реализована в скрипте `scripts/validate-ipk-version.sh`.

### Как это работает

1. Извлекается архив `.ipk` (по сути это `ar`‑архив).
2. Из него извлекается `control.tar.gz`.
3. Считывается файл `control` с метаданными.
4. Поле `Version` проверяется на соответствие регулярным выражениям для ветки `main` или PR.
5. Опционально проверяется формат даты в `PKG_RELEASE`.
6. При успехе скрипт завершает работу с кодом 0, при ошибке — с кодом 1.

### Интеграция с CI

Проверка выполняется в двух заданиях CI:

1. **build-dev-package** (только ветка `main`):
   - Убеждается, что версия содержит суффикс `-dev`.
   - Шаг: «Validate IPK version metadata».

2. **build-pr-package** (только pull request'ы):
   - Убеждается, что версия **не** содержит суффикс `-dev`.
   - Шаг: «Validate IPK version metadata».

## Использование

### Ручная проверка

Вы можете проверить `.ipk`‑файл вручную:

```bash
# Для пакетов ветки main (должен быть -dev)
./scripts/validate-ipk-version.sh package.ipk main

# Для пакетов PR (НЕ должен быть -dev)
./scripts/validate-ipk-version.sh package.ipk pr
```

### Проверка в CI

Валидация выполняется автоматически в CI после сборки пакетов. Скрипт проверяет все `.ipk`‑файлы в каталоге артефактов.

## Устранение неполадок

### Ошибки валидации

Если проверка не проходит, убедитесь, что:

1. **Для ветки main**: в окружении сборки установлен `DEV_SUFFIX=1`.
2. **Для pull request'ов**: `DEV_SUFFIX=0` или переменная не установлена.
3. **Makefile**: `Makefile` пакета корректно добавляет `-dev`, когда `DEV_SUFFIX=1`.

### Ожидаемые сообщения об ошибках

**main без -dev**:

```text
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' suffix (e.g., 1.0.8-dev or 1.0.8-dev-20240101)
  Got: 1.0.8-20240101
```

**PR с -dev**:

```text
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for PR/non-main branch
  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)
  Got: 1.0.8-dev-20240101
```

## Связанные файлы

- `scripts/validate-ipk-version.sh` — сам скрипт валидации.
- `.github/workflows/ci.yml` — workflow CI с шагами проверки.
- `package/openwrt-captive-monitor/Makefile` — Makefile пакета с логикой `DEV_SUFFIX`.
- `scripts/lib/colors.sh` — библиотека цветного вывода.

## Обоснование дизайна

Суффикс `-dev` служит для различения **разработческих** сборок и **стабильных** релизов:

- **Dev‑сборки** (ветка `main`) непрерывны и могут содержать потенциально разрушающие изменения.
- **Сборки PR** представляют собой кандидатов на слияние и не должны маркироваться как dev.
- **Релизные сборки** (по тегам) являются стабильными и имеют чистые версии без `-dev`.

Такая валидация гарантирует корректную маркировку пакетов в зависимости от контекста сборки и предотвращает путаницу между dev‑ и стабильными версиями.
