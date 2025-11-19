# IPK Version Validation

---

## 🌐 Language / Язык

**English** | [Русский](#ipk-%D0%B2%D0%B0%D0%BB%D0%B8%D0%B4%D0%B0%D1%86%D0%B8%D1%8F-%D0%B2%D0%B5%D1%80%D1%81%D0%B8%D0%B8)

---

## Overview

The CI pipeline includes automated validation of `.ipk` package version metadata to ensure correct version suffix handling based on the build context:

- **Main branch** development builds
- **Pull request** builds
- **Tagged release** builds

The validation is implemented in `scripts/validate-ipk-version.sh` and is wired into the SDK-based CI workflows as well as the tag-based release workflow.

## Validation Rules

### Main Branch Builds

Packages built from the `main` branch **must** include a `-dev` suffix in their `Version` field:

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

### Release Builds (Tag-Based)

Packages built for **tagged releases** (workflow `tag-build-release.yml`) **must NOT** include a `-dev` suffix. They use the **same pattern as PR builds**:

- **Pattern**: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`
- **Examples**:
  - `1.0.8`
  - `1.0.8-20240101`
  - `1.0.8-2024010112`

### PKG_RELEASE Validation

The validation also checks for date-based release suffixes embedded in the `Version` field (which correspond to `PKG_RELEASE`):

- **Format**: `YYYYMMDD` or `YYYYMMDDHHMM`
- **Examples**: `20240101`, `202401011530`

If a date suffix is present but does not match one of these formats, validation fails.

## Implementation

### Script Location

The logic is implemented in:

- `scripts/validate-ipk-version.sh`

### How It Works

`validate-ipk-version.sh` operates as follows:

1. Takes two arguments: the `.ipk` path and a **branch type** (`main`, `pr`, or `release`).
2. Extracts the `.ipk` archive (an `ar` archive) to a temporary directory.
3. Extracts `control.tar.gz` and locates the `control` metadata file.
4. Reads the `Version` field from the control file.
5. Validates the `Version` value against the regex appropriate for the branch type:
   - `main` → must contain `-dev`.
   - `pr` → must **not** contain `-dev`.
   - `release` → must **not** contain `-dev`.
6. If a date suffix is present, validates its length (8 or 10 digits) as a plausible `PKG_RELEASE` value.
7. Exits with status:
   - `0` on success
   - `1` on failure

## CI Integration

The validation is run in three CI contexts:

1. **Main branch dev builds** – job `build-dev-package` in `.github/workflows/ci.yml`:
   - For each generated `.ipk` under `artifacts/${BUILD_NAME}`, CI runs:
     - `./scripts/validate-ipk-version.sh "$IPK_FILE" main`
   - Ensures dev artifacts are clearly marked with `-dev`.

2. **Pull request builds** – job `build-pr-package` in `.github/workflows/ci.yml`:
   - For each `.ipk` in the PR artifacts directory, CI runs:
     - `./scripts/validate-ipk-version.sh "$IPK_FILE" pr`
   - Ensures candidate packages do **not** carry the `-dev` suffix.

3. **Tagged releases** – job `Build OpenWrt Package` in `.github/workflows/tag-build-release.yml`:
   - After the release package is built and structurally validated, CI runs:
     - `./scripts/validate-ipk-version.sh "$IPK_FILE" release`
   - Ensures final release IPKs have clean `Version` metadata suitable for distribution.

## Usage

### Manual Validation

You can validate a built `.ipk` by hand, for example after downloading it from a CI artifact or GitHub Release:

```bash
# Main branch dev build (Version must include -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_1.0.8-dev_all.ipk main

# Pull request build (Version must NOT include -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_1.0.8_all.ipk pr

# Tagged release build (Version must NOT include -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_1.0.8_all.ipk release
```

### CI Validation

In CI, validation runs automatically and checks **all** `.ipk` files in the relevant artifacts directory. If any package fails validation, the job (and workflow) fails, preventing accidentally mis‑versioned packages from being published.

## Troubleshooting

### Common Failure Scenarios

**1. Main branch package without `-dev`:**

```text
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' suffix (e.g., 1.0.8-dev or 1.0.8-dev-20240101)
  Got: 1.0.8-20240101
```

Resolution:

- Ensure the CI environment passes `DEV_SUFFIX=1` into the OpenWrt SDK build.
- Check that `package/openwrt-captive-monitor/Makefile` appends `-dev` when `DEV_SUFFIX=1`.

**2. PR or release package with `-dev`:**

```text
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for PR/non-main branch
  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)
  Got: 1.0.8-dev-20240101
```

Resolution:

- Ensure PR builds and tagged releases build with `DEV_SUFFIX=0` (or unset).
- Verify that the package `Makefile` only appends `-dev` when explicitly requested.

**3. Invalid date suffix:**

```text
✗ Validation FAILED: Date format invalid (expected YYYYMMDD or YYYYMMDDHHMM)
```

Resolution:

- Confirm that `PKG_RELEASE` uses a valid date format: `YYYYMMDD` or `YYYYMMDDHHMM`.
- Update the package metadata before re-running the build.

---

# IPK валидация версии

---

## 🌐 Язык

[English](#ipk-version-validation) | **Русский**

---

## Обзор

Конвейер CI выполняет автоматическую проверку поля `Version` в `.ipk`‑пакетах, чтобы:

- Сборки из ветки **`main`** всегда имели суффикс `-dev`.
- Сборки из **pull request'ов** не содержали суффикс `-dev`.
- Сборки для **релизных тегов** (workflow `tag-build-release.yml`) также не имели суффикс `-dev`.

Скрипт `scripts/validate-ipk-version.sh` проверяет только метаданные пакета и не изменяет сам архив.

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

### Релизные сборки (теги)

Пакеты, собранные для **релизных тегов** (`v...`), также **НЕ должны** содержать суффикс `-dev` и используют тот же шаблон, что и PR‑сборки:

- **Шаблон**: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`
- **Примеры**:
  - `1.0.8`
  - `1.0.8-20240101`
  - `1.0.8-2024010112`

### Проверка PKG_RELEASE

Дополнительно проверяется дата‑суффикс релиза, закодированный в конце `Version`:

- **Формат**: `YYYYMMDD` или `YYYYMMDDHHMM`
- **Примеры**: `20240101`, `202401011530`

Если суффикс даты присутствует, но не соответствует одному из этих форматов, проверка считается неуспешной.

## Реализация

### Расположение скрипта

- `scripts/validate-ipk-version.sh`

### Логика работы

1. Скрипт принимает два аргумента: путь до `.ipk` и тип ветки: `main`, `pr` или `release`.
2. Извлекает `control.tar.gz` из IPK‑архива и находит файл `control`.
3. Считывает значение поля `Version`.
4. Сопоставляет версию с регулярным выражением в зависимости от типа ветки:
   - `main` → версия **обязана** содержать `-dev`.
   - `pr` → версия **не должна** содержать `-dev`.
   - `release` → версия **не должна** содержать `-dev`.
5. При наличии суффикса даты проверяет его длину (8 или 10 цифр) как допустимое значение `PKG_RELEASE`.
6. Возвращает код выхода `0` при успехе или `1` при ошибке.

## Интеграция с CI

Проверка вызывается в трёх контекстах CI:

1. **build-dev-package** (ветка `main`) – проверяет, что версии содержат суффикс `-dev`.
2. **build-pr-package** (pull request'ы) – проверяет, что версии **не** содержат суффикс `-dev`.
3. **tag-build-release.yml / Build OpenWrt Package** (релизные теги) – проверяет, что релизные `.ipk` имеют «чистую» версию без `-dev`.

## Использование вручную

Примеры ручного запуска проверки:

```bash
# Для сборок из ветки main (должен быть -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_1.0.8-dev_all.ipk main

# Для PR‑сборок (не должно быть -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_1.0.8_all.ipk pr

# Для релизных тегов (не должно быть -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_1.0.8_all.ipk release
```

## Устранение неполадок

**1. Ветка main без `-dev`**

```text
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' suffix (e.g., 1.0.8-dev or 1.0.8-dev-20240101)
  Got: 1.0.8-20240101
```

**2. PR/релизная сборка с `-dev`**

```text
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for PR/non-main branch
  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)
  Got: 1.0.8-dev-20240101
```

**3. Некорректный формат даты**

```text
✗ Validation FAILED: Date format invalid (expected YYYYMMDD or YYYYMMDDHHMM)
```

Во всех случаях рекомендуется скорректировать `PKG_VERSION`/`PKG_RELEASE` в `Makefile` пакета и повторно запустить сборку или соответствующий workflow.
