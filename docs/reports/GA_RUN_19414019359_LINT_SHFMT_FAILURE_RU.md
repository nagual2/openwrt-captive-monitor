# CI Failure Report: Lint (shfmt)

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

## Run Metadata

- **Workflow run URL**: https://github.com/nagual2/openwrt-captive-monitor/actions/runs/19414019359/job/55539517588
- **Workflow run ID**: `19414019359`
- **Job ID**: `55539517588`
- **Job**: `Lint (shfmt)`
- **Status**: `failure`
- **Branch**: `fix-actionlint-ci-matrix-include-sc2231` (PR merge ref: `pull/259/merge`)
- **Runner**: GitHub Actions `ubuntu-24.04`
- **Time window**: `2025-11-16T23:50:16Z` → `2025-11-16T23:50:40Z` (24 seconds)

## Summary

The **`Lint (shfmt)`** job failed because multiple shell scripts did not match the project’s enforced formatting policy.

- `shfmt` version: **3.8.0** (Ubuntu 24.04 / noble)
- Command used:
  - `shfmt -d -s -i 4 -ci -sr .`
- `shfmt` detected differences and exited with a **non-zero exit code**. The job log contains unified diffs for each affected file.

## Affected Files (from shfmt logs)

- `openwrt_captive_monitor.sh`
- `package/openwrt-captive-monitor/files/etc/init.d/captive-monitor`
- `scripts/build_ipk.sh`
- `scripts/check-pipe-guards.sh`
- `scripts/ci-helper.sh`
- `scripts/diagnose-actions.sh`
- `scripts/diagnose-github-actions.sh`
- `scripts/lib/colors.sh`
- `scripts/monitor-github-actions.sh`
- `scripts/parse-latest-failed-workflows.sh`
- `scripts/run_openwrt_vm.sh`
- `scripts/setup-opkg-utils.sh`
- `scripts/stage_artifacts.sh`
- `scripts/test-version-calculation.sh`
- `scripts/upload-sdk-to-github.sh`
- `scripts/validate-docs.sh`
- `scripts/validate-sdk-image.sh`
- `scripts/validate-sdk-url.sh`
- `scripts/validate-workflows.sh`
- `scripts/validate_ipk.sh`
- `scripts/verify_package.sh`
- `setup_captive_monitor.sh`
- `tests/mocks/_iptables_mock.sh`
- `tests/mocks/_lib.sh`
- `tests/run.sh`

## Nature of the Formatting Issues

The diffs show primarily **indentation and alignment** problems:

- Enforcing 4‑space indentation (`-i 4`).
- Aligning `case/esac`, `if/then/fi`, function bodies and multi‑line pipelines (`-ci`, `-sr`, `-s`).
- Normalizing spaces around command arguments and line breaks.

### Example (from init script)

**Before:**

```sh
     if [ ! -x "$SCRIPT_PATH" ]; then
             logger -t captive-monitor -p user.err "Script not found or not executable: $SCRIPT_PATH"
             return 1
     fi
```

**After (shfmt):**

```sh
    if [ ! -x "$SCRIPT_PATH" ]; then
        logger -t captive-monitor -p user.err "Script not found or not executable: $SCRIPT_PATH"
        return 1
    fi
```

## Root Cause

Unformatted or partially formatted shell scripts were committed without running `shfmt` with the project’s configuration (`.shfmt.conf` and/or CI parameters). This is **a style violation**, not a functional bug, but CI enforces style strictly.

## Local Reproduction Steps

1. On **Ubuntu 24.04**:
   - `sudo apt-get update && sudo apt-get install -y shfmt`
   - Verify version: `shfmt --version` (expected **3.8.0**)
2. Run the formatter in the repo root:
   - `shfmt -d -s -i 4 -ci -sr .`
3. Auto‑fix formatting:
   - `shfmt -w -s -i 4 -ci -sr .`

## Recommended Fix Plan

- Run automatic reformatting on all shell scripts:
  - `shfmt -w -s -i 4 -ci -sr .`
- Re‑check **BusyBox ash** compatibility after formatting, especially:
  - `set -eu` and conditional `pipefail` (via `set -o pipefail` where supported).
  - Absence of Bash‑only features in scripts executed by BusyBox `ash`.
  - Continued use of the shared color helper `scripts/lib/colors.sh` where applicable.
- Optionally add a local **pre‑commit hook** that runs `shfmt` before commits:
  - Reuse `scripts/ci-helper.sh` or add `.githooks/pre-commit` that calls `shfmt -w`.
- After fixing formatting, run all lint jobs locally or via a PR to ensure CI is clean.

## Environment Observations

- Runner: `ubuntu-24.04 (noble)`; `apt` installs `shfmt` 3.8.0.
- Lint packages for the job are installed via composite action `./.github/actions/setup-system-packages` (BusyBox, `shfmt`, `shellcheck`).

## Conclusion

- The failure is **not** related to project logic or package builds.
- It is a **style enforcement issue**: shell scripts must conform to the `shfmt` style profile configured by the project.
- All modified scripts need to be reformatted to restore a green `Lint (shfmt)` job.

---

# Русский

---

## 🌐 Язык

[English](#ci-failure-report-lint-shfmt) | **Русский**

---

# Отчёт по сбою CI: Lint (shfmt)

Ссылка на задание: https://github.com/nagual2/openwrt-captive-monitor/actions/runs/19414019359/job/55539517588

## Идентификаторы

- Workflow run ID: `19414019359`
- Job ID: `55539517588`
- Job: `Lint (shfmt)`
- Статус: `failure`
- Ветка: `fix-actionlint-ci-matrix-include-sc2231` (PR merge: `pull/259/merge`)
- Runner: GitHub Actions `ubuntu-24.04`
- Время: `2025-11-16T23:50:16Z` → `2025-11-16T23:50:40Z` (24 сек)

## Краткий вывод

- Задача **«Lint (shfmt)»** завершилась с ошибкой, так как форматирование ряда shell‑скриптов не соответствует политике форматирования проекта.
- Использовался `shfmt` версии **3.8.0** (Ubuntu 24.04 / noble), с командой:
  - `shfmt -d -s -i 4 -ci -sr .`
- `shfmt` обнаружил отличия и вернул ненулевой код выхода. В логе присутствуют unified diff для затронутых файлов.

## Затронутые файлы (по логам shfmt)

- `openwrt_captive_monitor.sh`
- `package/openwrt-captive-monitor/files/etc/init.d/captive-monitor`
- `scripts/build_ipk.sh`
- `scripts/check-pipe-guards.sh`
- `scripts/ci-helper.sh`
- `scripts/diagnose-actions.sh`
- `scripts/diagnose-github-actions.sh`
- `scripts/lib/colors.sh`
- `scripts/monitor-github-actions.sh`
- `scripts/parse-latest-failed-workflows.sh`
- `scripts/run_openwrt_vm.sh`
- `scripts/setup-opkg-utils.sh`
- `scripts/stage_artifacts.sh`
- `scripts/test-version-calculation.sh`
- `scripts/upload-sdk-to-github.sh`
- `scripts/validate-docs.sh`
- `scripts/validate-sdk-image.sh`
- `scripts/validate-sdk-url.sh`
- `scripts/validate-workflows.sh`
- `scripts/validate_ipk.sh`
- `scripts/verify_package.sh`
- `setup_captive_monitor.sh`
- `tests/mocks/_iptables_mock.sh`
- `tests/mocks/_lib.sh`
- `tests/run.sh`

## Суть несоответствий

Основные проблемы — отступы и выравнивание конструкций:

- Приведение отступа к 4 пробелам (`-i 4`).
- Выравнивание `case/esac`, `if/then/fi`, функций и многострочных пайплайнов (`-ci`, `-sr`, `-s`).
- Нормализация пробелов перед/после аргументов команд и переносов строк.

### Пример (фрагмент из лога для init‑скрипта)

**Было:**

```sh
     if [ ! -x "$SCRIPT_PATH" ]; then
             logger -t captive-monitor -p user.err "Script not found or not executable: $SCRIPT_PATH"
             return 1
     fi
```

**Стало:**

```sh
    if [ ! -x "$SCRIPT_PATH" ]; then
        logger -t captive-monitor -p user.err "Script not found or not executable: $SCRIPT_PATH"
        return 1
    fi
```

## Первопричина

В репозиторий попали изменения shell‑скриптов, не отформатированные `shfmt` в конфигурации проекта (`.shfmt.conf` и/или параметры в CI). Это системное несоответствие стилю (не ошибка выполнения), которое принудительно контролируется в CI.

## Воспроизведение локально

1. На **Ubuntu 24.04**:
   - `sudo apt-get update && sudo apt-get install -y shfmt`
   - Проверка: `shfmt --version` (ожидается **3.8.0**)
2. Запустить проверку в корне репозитория:
   - `shfmt -d -s -i 4 -ci -sr .`
3. Автоисправление формата:
   - `shfmt -w -s -i 4 -ci -sr .`

## Рекомендации по исправлению

- Выполнить автоматическую переформатировку всех shell‑скриптов указанной командой: `shfmt -w -s -i 4 -ci -sr .`.
- Перепроверить **bash/ash‑совместимость** после форматирования, особенно:
  - `set -eu` и условный `pipefail` (через `set -o pipefail`, если доступно).
  - Отсутствие bash‑специфичных расширений в скриптах, исполняемых BusyBox `ash`.
  - Сохранение зависимости от общего файла цветов `scripts/lib/colors.sh` (если используется).
- Добавить локальный **pre‑commit‑хук** (опционально), который вызывает `shfmt` перед коммитом:
  - Через `scripts/ci-helper.sh` или отдельный `.githooks/pre-commit` с вызовом `shfmt` в режиме `-w`.
- После фикса запустить все lint‑задачи локально либо в PR, чтобы убедиться в чистоте CI.

## Наблюдения по среде выполнения

- Runner: `ubuntu-24.04 (noble)`, пакет `shfmt` версии 3.8.0 ставится через `apt`.
- Пакеты для шага линтинга устанавливаются композитным экшеном `./.github/actions/setup-system-packages` (BusyBox, `shfmt`, `shellcheck`).

## Итог

- Сбой **не** связан с логикой проекта или сборкой пакетов; это нарушение стиля shell‑скриптов.
- Стиль задаётся `shfmt` и принудительно проверяется в CI.
- Необходимо привести все изменённые скрипты к этому стилю, чтобы вернуть зелёный статус задачи **`Lint (shfmt)`**.

## Приложение: фрагменты лога

- Команда линтера: `shfmt -d -s -i 4 -ci -sr .`
- Обнаружены отличия в **25** файлах (см. список выше).
