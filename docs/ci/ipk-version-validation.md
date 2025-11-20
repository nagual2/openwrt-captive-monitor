# IPK Version Validation

---

## 🌐 Language / Язык

**English** | [Русский](#ipk-%D0%B2%D0%B0%D0%BB%D0%B8%D0%B4%D0%B0%D1%86%D0%B8%D1%8F-%D0%B2%D0%B5%D1%80%D1%81%D0%B8%D0%B8)

---

## Overview

The CI pipeline includes automated validation of `.ipk` package version metadata to enforce a strict, date‑based version scheme.

Validation covers three contexts:

- **Main branch** development builds
- **Pull request** builds
- **Tagged release** builds

The logic is implemented in `scripts/validate-ipk-version.sh` and wired into both the SDK‑based CI workflows and the tag‑based release workflow.

---

## Version model

All builds share the same base “date version”:

- **Format:** `YYYY.M.D.N`
- **Regex:** `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+$`
- **Meaning:**
  - `YYYY` – four‑digit year (e.g. `2025`)
  - `M` – month `1–12` (no leading zero required)
  - `D` – day `1–31` (no leading zero required)
  - `N` – build counter for that calendar date

The final `Version` field inside the `.ipk` control metadata is built by combining:

```text
<date-version> [-dev] - <PKG_RELEASE>
```

where `PKG_RELEASE` is now a **small, numeric integer counter** (`^[0-9]+$`), e.g. `1`, `2`, `3`.

This scheme intentionally **rejects semantic versions** like `1.0.8` and legacy date‑stamp releases embedded in `PKG_RELEASE` such as `20240101`.

---

## Validation Rules

### Main Branch Builds

Packages built from the `main` branch **must** include `-dev` between the date version and the numeric release:

- **Pattern:**  
  `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-dev-[0-9]+$`
- **Examples (valid):**
  - `2025.11.20.2-dev-1`
  - `2025.11.20.5-dev-3`

### Pull Request Builds

Packages built from pull requests **must NOT** include `-dev`:

- **Pattern:**  
  `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-[0-9]+$`
- **Examples (valid):**
  - `2025.11.20.2-1`
  - `2025.11.20.5-3`

### Release Builds (Tag‑Based)

Packages built for **tagged releases** (workflow `tag-build-release.yml`) use the **same pattern as PR builds** and also **must NOT** include `-dev`:

- **Pattern:**  
  `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-[0-9]+$`
- **Examples (valid):**
  - `2025.11.20.2-1`
  - `2025.11.20.5-2`

### PKG_RELEASE Validation

The `PKG_RELEASE` component (the last `-<number>` in the `Version` string):

- **Must** match `^[0-9]+$` (only digits)
- Is expected to be a **small integer counter** (e.g. `1`, `2`, `3`)
- **Must not** be a date stamp like `20240101` or `202401011530`

If `PKG_RELEASE` contains anything other than digits, or looks like a long date stamp, validation fails.

---

## Implementation

### Script Location

Version validation is implemented in:

- `scripts/validate-ipk-version.sh`

### How It Works

`scripts/validate-ipk-version.sh`:

1. Accepts two arguments: the `.ipk` path and a **branch type** (`main`, `pr`, or `release`).
2. Extracts the `.ipk` (an `ar` archive) to a temporary directory.
3. Extracts `control.tar.gz` and locates the `control` metadata file.
4. Reads the `Version` field from the control file.
5. Validates the `Version` value:
   - Ensures the base component matches the date‑version regex (`YYYY.M.D.N`).
   - Ensures the trailing `PKG_RELEASE` component is numeric (`^[0-9]+$`).
   - Enforces branch‑specific suffix rules:
     - `main` → `<date-version>-dev-<PKG_RELEASE>`
     - `pr` → `<date-version>-<PKG_RELEASE>` (no `-dev`)
     - `release` → `<date-version>-<PKG_RELEASE>` (no `-dev`)
6. Prints detailed diagnostics when validation fails, including whether the base date or the release number is invalid.
7. Exits with status:
   - `0` on success
   - `1` on failure

---

## CI Integration

Validation runs in three CI contexts:

1. **Main branch dev builds** – job `build-dev-package` in `.github/workflows/ci.yml`:
   - For each generated `.ipk`, CI runs:
     - `./scripts/validate-ipk-version.sh "$IPK_FILE" main`
   - Ensures dev artifacts are clearly marked with `-dev` and follow the date‑based format.

2. **Pull request builds** – job `build-pr-package` in `.github/workflows/ci.yml`:
   - For each `.ipk` in the PR artifacts directory, CI runs:
     - `./scripts/validate-ipk-version.sh "$IPK_FILE" pr`
   - Ensures candidate packages use date‑based versions **without** `-dev`.

3. **Tagged releases** – job `Build OpenWrt Package` in `.github/workflows/tag-build-release.yml`:
   - After building and verifying the release package, CI runs:
     - `./scripts/validate-ipk-version.sh "$IPK_FILE" release`
   - Ensures final release IPKs have clean, date‑based `Version` metadata suitable for distribution.

---

## Usage

### Manual Validation

You can validate a built `.ipk` by hand, for example after downloading it from CI artifacts or a GitHub Release:

```bash
# Main branch dev build (Version must be <date-version>-dev-<PKG_RELEASE>)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_2025.11.20.2-dev-1_all.ipk main

# Pull request build (Version must be <date-version>-<PKG_RELEASE>, no -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_2025.11.20.2-1_all.ipk pr

# Tagged release build (same pattern as PR)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_2025.11.20.2-1_all.ipk release
```

### CI Validation

In CI, validation runs automatically and checks **all** `.ipk` files in the relevant artifacts directory. If any package fails validation, the job (and workflow) fails, preventing accidentally mis‑versioned packages from being published.

---

## Troubleshooting

### 1. Main branch package without `-dev`

```text
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' and numeric PKG_RELEASE (e.g., 2025.11.20.2-dev-1)
  Got: 2025.11.20.2-1
```

**Resolution:**

- Ensure the CI environment passes `DEV_SUFFIX=1` into the OpenWrt SDK build for `main`.
- Check that `package/openwrt-captive-monitor/Makefile` appends `-dev` to `PKG_VERSION` when `DEV_SUFFIX=1`.

### 2. PR or release package with `-dev`

```text
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for non-main build
  Expected: version without '-dev' (e.g., 2025.11.20.2-1)
  Got: 2025.11.20.2-dev-1
```

**Resolution:**

- Ensure PR builds and tagged releases build with `DEV_SUFFIX=0` (or unset).
- Verify that the package `Makefile` only appends `-dev` when explicitly requested.

### 3. Semver-style or non‑date base version

```text
✗ Validation FAILED: Base component '1.0.8' is not a valid date-based version (expected YYYY.M.D.N)
  Got: 1.0.8-dev-1
```

**Resolution:**

- Update `PKG_VERSION` in the package `Makefile` to use the `YYYY.M.D.N` format.
- Regenerate the package so that the `Version` control field matches the date‑based scheme.

### 4. Non-numeric or date-stamp PKG_RELEASE

```text
ERROR: PKG_RELEASE must be a numeric integer (^[0-9]+$).
  Got: '2024-01-01'
```

or

```text
ERROR: PKG_RELEASE looks like a date stamp ('20240101').
       PKG_RELEASE is now a small integer counter (e.g., 1, 2, 3).
```

**Resolution:**

- Set `PKG_RELEASE` in the package `Makefile` to a small integer (`1`, `2`, `3`, …).
- Avoid embedding date stamps in `PKG_RELEASE`; the date already lives in `PKG_VERSION` via `<date-version>`.

---

# IPK валидация версии

---

## 🌐 Язык

[English](#ipk-version-validation) | **Русский**

---

## Обзор

Конвейер CI выполняет автоматическую проверку поля `Version` в `.ipk`‑пакетах, чтобы обеспечить единый формат **дата‑версий** и корректные суффиксы в зависимости от контекста сборки:

- Сборки из ветки **`main`**
- Сборки из **pull request'ов**
- Сборки для **релизных тегов**

Валидация реализована в `scripts/validate-ipk-version.sh` и используется как в SDK‑сборках, так и в workflow для тегированных релизов.

---

## Модель версионирования

Общий базовый формат версии:

- **Формат:** `YYYY.M.D.N`
- **Регулярное выражение:** `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+$`
- **Семантика:**
  - `YYYY` – год из 4 цифр (например, `2025`)
  - `M` – месяц `1–12` (ведущий ноль не обязателен)
  - `D` – день `1–31` (ведущий ноль не обязателен)
  - `N` – счётчик сборки для данной календарной даты

Поле `Version` в `control`‑файле пакета строится по схеме:

```text
<date-version> [-dev] - <PKG_RELEASE>
```

где `PKG_RELEASE` — это **небольшое целое число** (`^[0-9]+$`), например `1`, `2`, `3`.

Таким образом:

- Базовая версия кодирует дату и номер сборки (`2025.11.20.2`).
- `PKG_RELEASE` служит коротким счётчиком релизов для одной и той же базовой версии.
- Семантические версии (`1.0.8`) и старые форматы с датой в `PKG_RELEASE` (`20240101`) **отвергаются**.

---

## Правила валидации

### Сборки из ветки main

Пакеты, собранные из ветки `main`, **обязаны** содержать суффикс `-dev` между базовой датой и номером релиза:

- **Шаблон:**  
  `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-dev-[0-9]+$`
- **Примеры (корректные):**
  - `2025.11.20.2-dev-1`
  - `2025.11.20.5-dev-3`

### Сборки из pull request'ов

Пакеты, собранные в контексте pull request, **НЕ должны** содержать `-dev`:

- **Шаблон:**  
  `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-[0-9]+$`
- **Примеры (корректные):**
  - `2025.11.20.2-1`
  - `2025.11.20.5-3`

### Релизные сборки (теги)

Пакеты, собранные для **релизных тегов** (`v...`), используют тот же шаблон, что и PR‑сборки, и также **НЕ должны** содержать `-dev`:

- **Шаблон:**  
  `^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-[0-9]+$`
- **Примеры (корректные):**
  - `2025.11.20.2-1`
  - `2025.11.20.5-2`

### Проверка PKG_RELEASE

Компонент `PKG_RELEASE` (последний `-<number>` в `Version`):

- **Обязан** соответствовать `^[0-9]+$` (только цифры).
- Должен быть **небольшим целым** (`1`, `2`, `3`, …).
- **Не должен** выглядеть как дата (`20240101`, `202401011530` и т.п.).

Если `PKG_RELEASE` содержит что‑то кроме цифр или похож на длинную дату, проверка считается неуспешной.

---

## Реализация

### Расположение скрипта

- `scripts/validate-ipk-version.sh`

### Логика работы

`scripts/validate-ipk-version.sh`:

1. Принимает два аргумента: путь до `.ipk` и тип ветки: `main`, `pr` или `release`.
2. Извлекает `control.tar.gz` из IPK‑архива и находит файл `control`.
3. Считывает значение поля `Version`.
4. Проверяет:
   - Что базовая часть версии соответствует формату `YYYY.M.D.N`.
   - Что компонент `PKG_RELEASE` содержит только цифры.
   - Что структура и суффиксы соответствуют типу ветки:
     - `main` → `<date-version>-dev-<PKG_RELEASE>`
     - `pr` → `<date-version>-<PKG_RELEASE>`
     - `release` → `<date-version>-<PKG_RELEASE>`
5. В случае ошибки выводит подробные сообщения: какая часть версии некорректна (база или номер релиза).
6. Возвращает код выхода `0` при успехе или `1` при ошибке.

---

## Интеграция с CI

Проверка вызывается в трёх контекстах CI:

1. **build-dev-package** (ветка `main`) – для каждого `.ipk` выполняется:
   - `./scripts/validate-ipk-version.sh "$IPK_FILE" main`
   - Гарантирует наличие суффикса `-dev` и корректный формат даты.

2. **build-pr-package** (pull request'ы) – для каждого `.ipk` выполняется:
   - `./scripts/validate-ipk-version.sh "$IPK_FILE" pr`
   - Гарантирует отсутствие `-dev` и дату‑ориентированную версию.

3. **tag-build-release.yml / Build OpenWrt Package** (релизные теги) – для релизных пакетов выполняется:
   - `./scripts/validate-ipk-version.sh "$IPK_FILE" release`
   - Гарантирует «чистые» версии без `-dev`, с корректным `PKG_RELEASE`.

---

## Использование вручную

Примеры ручного запуска проверки:

```bash
# Для сборок из ветки main (должен быть формат <date-version>-dev-<PKG_RELEASE>)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_2025.11.20.2-dev-1_all.ipk main

# Для PR‑сборок (формат <date-version>-<PKG_RELEASE>, без -dev)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_2025.11.20.2-1_all.ipk pr

# Для релизных тегов (тот же формат, что и для PR)
./scripts/validate-ipk-version.sh openwrt-captive-monitor_2025.11.20.2-1_all.ipk release
```

---

## Устранение неполадок

### 1. Ветка main без `-dev`

```text
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' and numeric PKG_RELEASE (e.g., 2025.11.20.2-dev-1)
  Got: 2025.11.20.2-1
```

### 2. PR/релизная сборка с `-dev`

```text
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for non-main build
  Expected: version without '-dev' (e.g., 2025.11.20.2-1)
  Got: 2025.11.20.2-dev-1
```

### 3. Семантическая или «старая» версия

```text
✗ Validation FAILED: Base component '1.0.8' is not a valid date-based version (expected YYYY.M.D.N)
  Got: 1.0.8-dev-1
```

### 4. Некорректный PKG_RELEASE

```text
ERROR: PKG_RELEASE must be a numeric integer (^[0-9]+$).
  Got: '2024-01-01'
```

или

```text
ERROR: PKG_RELEASE looks like a date stamp ('20240101').
       PKG_RELEASE is now a small integer counter (e.g., 1, 2, 3).
```

Во всех случаях рекомендуется скорректировать `PKG_VERSION`/`PKG_RELEASE` в `Makefile` пакета согласно новой схеме `YYYY.M.D.N` + числовой `PKG_RELEASE`, после чего повторно запустить сборку или соответствующий workflow.
