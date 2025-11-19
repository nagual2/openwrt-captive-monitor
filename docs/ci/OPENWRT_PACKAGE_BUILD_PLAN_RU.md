# OpenWrt Package Build Plan

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

## Goal

Standardize the **openwrt-captive-monitor** package build in CI/CD so that it is:

- **Reproducible** – predictable outputs for the same inputs
- **Versioned consistently** – clear dev vs release semantics
- **Secure** – artifacts are validated and safely published
- **Diagnosable** – CI failures are easy to understand and fix

## Inputs and Existing Components

- CI builds use the **OpenWrt SDK** via `openwrt/gh-action-sdk`.
- SDK container image: `ghcr.io/openwrt/sdk:{arch}-{version}`, passed to the action via `CONTAINER` env.
- Local feed layout:
  - `FEED_DIR` points to a local feed tree
  - `FEEDNAME=local`
  - `PACKAGES` selects `openwrt-captive-monitor` for build
- Existing scripts in the repository:
  - `scripts/validate-sdk-image.sh` – validate SDK Docker image tag and target/subtarget.
  - `scripts/validate-sdk-url.sh` – validate SDK tarball URLs across mirrors.
  - `scripts/setup-opkg-utils.sh` – install `opkg-build` on the host (no `apt install opkg-utils` on Ubuntu 24.04).
  - `scripts/validate-ipk-version.sh` and `docs/ci/ipk-version-validation.md` – enforce `.ipk` version rules (main vs PR builds).
  - `scripts/stage_artifacts.sh` – stage artifacts under `artifacts/<build-name>`.
- Artifact requirements:
  - CI artifact name must include `dev+<shortsha>` for dev builds.
  - **Do not** rewrite `PKG_VERSION` inside the `.ipk`; only artifact names and control `Version` field reflect dev/pr channel.

## High-Level Roadmap

### Phase 0 – Unblock CI (Lint)

- Fix shell script formatting with:
  - `shfmt -w -s -i 4 -ci -sr .`
- Ensure the following CI jobs are green:
  - `Lint (shfmt)`, `Lint (shellcheck)`, `Lint (markdownlint)`, `Lint (actionlint)`
  - Security checks: ShellCheck Security Analysis, Trivy, Dependency Review
- **Outcome**: Core lint/security gates are green; package builds can safely run on top.

### Phase 1 – Normalize Dev Package Builds

- **Validate SDK image and parameters before invoking the SDK action**:
  - Add steps calling `scripts/validate-sdk-image.sh` and (for tarball flows) `scripts/validate-sdk-url.sh` at the start of the job.
- **Pin SDK image explicitly**:
  - Example: `CONTAINER=ghcr.io/openwrt/sdk:x86_64-23.05.3`.
- **Build package via `openwrt/gh-action-sdk`** with:
  - `FEEDNAME=local`, `FEED_DIR=./feed`, `PACKAGES=openwrt-captive-monitor`.
- **Artifact staging**:
  - `scripts/stage_artifacts.sh` collects `*.ipk`, `SHA256SUMS`, and logs into `artifacts/dev-<branch>`.
  - Artifact name pattern: `dev-<branch>-dev+<shortsha>` (do **not** mutate `PKG_VERSION` inside the `.ipk`).
- **IPK version validation**:
  - `main` branch: `scripts/validate-ipk-version.sh main <ipk>` – Version in `control` **must** include `-dev` (see `docs/ci/ipk-version-validation.md`).
  - PR/non-main: `scripts/validate-ipk-version.sh pr <ipk>` – Version **must not** include `-dev`.
- **Outcome**: Reproducible dev builds with consistent version metadata and CI artifacts.

### Phase 2 – Target Matrix, Caching, Performance

- Introduce a matrix over `target/subtarget/arch` (for example: `x86_64`, `mips_24kc`, `aarch64_cortex-a53`, etc.).
- Add caching:
  - Pre-pull required SDK images with retries and TTL.
  - Optionally cache feed sources (carefully, to avoid polluting the workspace).
- Resource and concurrency management:
  - Use `concurrency: cancel-in-progress` for PRs.
  - Apply least-privilege `permissions` for `GITHUB_TOKEN`.
- **Outcome**: Parallel builds across multiple architectures with controlled resource usage and predictable runtimes.

### Phase 3 – Testing and Integration

- Extend unit/integration tests for scripts:
  - Reuse `tests/run.sh` and existing mock scripts; add coverage for build and validation paths.
- IPK verification:
  - Use `scripts/verify_package.sh` to check contents, checksums, `postinst`/`prerm`, init scripts, etc.
- Optional smoke tests in QEMU/VM:
  - `scripts/run_openwrt_vm.sh` – boot image, install IPK, start service, basic log checks.
- **Outcome**: Automated regression coverage for key install and startup scenarios.

### Phase 4 – Release Preparation

- Split **dev** and **release** pipelines:
  - `main/dev`: Version field in `.ipk` includes `-dev`.
  - Release: clean version from package `Makefile` without `-dev`.
- Dedicated release workflow triggered by tags `vX.Y.Z`:
  - Verify `PKG_VERSION` matches the tag; `PKG_RELEASE` is a date `YYYYMMDD[HHMM]`.
  - Build matrix, upload artifacts, generate release notes.
- Optional artifact signing:
  - `cosign`/Sigstore or detached signatures for `SHA256SUMS`.
- **Outcome**: Reproducible, verifiable releases with a clear audit trail.

### Phase 5 – Documentation and Support

- Keep `docs/packaging.md`, `docs/PACKAGES.md` up to date; add a quick start for local SDK builds.
- Add a **CI diagnostics** section:
  - Link `scripts/diagnose-*.sh` and describe common failure patterns.
- Provide a guide for BusyBox `ash` compatibility and script style:
  - `set -eu`, conditional `pipefail`, centralized colors via `scripts/lib/colors.sh`, `shfmt` formatting profile.

## Ready-Made Building Blocks (Reuse)

- SDK image and URL validation are already implemented:
  - Always include these fail-fast steps before `openwrt/gh-action-sdk`.
- IPK versioning rules are already standardized:
  - Preserve `main` vs `PR` semantics from `docs/ci/ipk-version-validation.md`.
- Stage artifacts under `artifacts/<build-name>` and upload with `actions/upload-artifact@v5` using clear names.
- **Do not** use `apt install opkg-utils` on Ubuntu 24.04:
  - Use `scripts/setup-opkg-utils.sh` and verify with `opkg-build -h` instead.

## Definition of Done (DoD)

- Lint and security checks are green:
  - `Lint (shfmt)`, `Lint (shellcheck)`, `Lint (markdownlint)`, `Lint (actionlint)`, Trivy, Dependency Review, ShellCheck Security Analysis.
- Dev job builds the package for at least two architectures and passes `validate-sdk-*` and `validate-ipk` checks.
- Artifacts are correctly named and downloadable; each contains `.ipk` files and `SHA256SUMS`.
- Documentation is updated; a fast local SDK build scenario is documented.

## Developer Commands (Local)

- Format scripts:
  - `shfmt -w -s -i 4 -ci -sr .`
- Install `opkg-utils` on Ubuntu 24.04:
  - `./scripts/setup-opkg-utils.sh && opkg-build -h`
- Check `.ipk` version after build:
  - `./scripts/validate-ipk-version.sh pr path/to/*.ipk`  # for PR builds
  - `./scripts/validate-ipk-version.sh main path/to/*.ipk`  # for main branch builds

## Notes

- Apply minimum required permissions for `GITHUB_TOKEN` and correct `concurrency`/`permissions` settings in workflows (GitHub Actions best practices).
- Keep `PKG_VERSION` inside package files unchanged for dev builds; dev markers should live only in the CI artifact name and in the `Version` field of `control` according to main/PR rules.

---

# Русский

---

## 🌐 Язык

[English](#openwrt-package-build-plan) | **Русский**

---

# План продолжения разработки функционала сборки пакетов (OpenWrt)

Цель: довести и стандартизировать сборку пакета **openwrt-captive-monitor** в CI/CD с гарантированной воспроизводимостью, предсказуемой версификацией, безопасной поставкой артефактов и удобной диагностикой.

## Вводные и существующие компоненты

- Билды в CI выполняются через OpenWrt SDK (`openwrt/gh-action-sdk`).
- Контейнер SDK: `ghcr.io/openwrt/sdk:{arch}-{version}`; передаётся в action через переменную окружения `CONTAINER`.
- Локальный feed:
  - `FEED_DIR` указывает на локальное дерево feed'а
  - `FEEDNAME=local`
  - `PACKAGES` указывает собираемый пакет `openwrt-captive-monitor`.
- Скрипты в репозитории:
  - `scripts/validate-sdk-image.sh` — проверка Docker‑образа SDK и `target/subtarget`.
  - `scripts/validate-sdk-url.sh` — проверка доступности tarball SDK с использованием зеркал.
  - `scripts/setup-opkg-utils.sh` — установка `opkg-build` на host (не через `apt` в Ubuntu 24.04).
  - `scripts/validate-ipk-version.sh` и `docs/ci/ipk-version-validation.md` — правила версии внутри `.ipk` (main vs PR).
  - `scripts/stage_artifacts.sh` — выкладка артефактов под `artifacts/<build-name>`.
- Требования к артефактам:
  - Имя артефакта в CI содержит `dev+<shortsha>` для dev‑сборок.
  - Внутри `.ipk` `PKG_VERSION` не переписывается.

## Глобальная дорожная карта

### Фаза 0 — Разблокировка CI (lint)

- Исправить форматирование shell‑скриптов: `shfmt -w -s -i 4 -ci -sr .`.
- Убедиться, что проходят проверки:
  - «Lint (shfmt)», «Lint (shellcheck)», «Lint (markdownlint)», «Lint (actionlint)».
  - Security‑проверки: ShellCheck Security Analysis, Trivy, Dependency Review.
- **Результат**: базовые проверки зелёные, путь к сборкам пакетов открыт.

### Фаза 1 — Нормализация dev‑сборок пакета

- Валидация SDK‑образа и параметров **до** вызова сборки:
  - В начале job добавить шаги `scripts/validate-sdk-image.sh` и (при tarball‑сценарии) `scripts/validate-sdk-url.sh`.
- Жёстко задать образ SDK:
  - Пример: `CONTAINER=ghcr.io/openwrt/sdk:x86_64-23.05.3`.
- Собрать пакет через `openwrt/gh-action-sdk` с `FEEDNAME=local`, `FEED_DIR=./feed`, `PACKAGES=openwrt-captive-monitor`.
- Стадирование артефактов:
  - `scripts/stage_artifacts.sh` складывает `*.ipk`, `sha256` и логи в `artifacts/dev-<branch>`.
  - Имя загружаемого артефакта: `dev-<branch>-dev+<shortsha>` (внутри `.ipk` `PKG_VERSION` **не** переписывать!).
- Валидация версии `.ipk`:
  - В `main`: `scripts/validate-ipk-version.sh main <ipk>` — поле `Version` в `control` должно содержать `-dev` (см. `docs/ci/ipk-version-validation.md`).
  - В PR/не‑`main`: `scripts/validate-ipk-version.sh pr <ipk>` — суффикса `-dev` быть не должно.
- **Результат**: воспроизводимая dev‑сборка с корректной версификацией и артефактами в CI.

### Фаза 2 — Матрица таргетов, кеши, ускорение

- Ввести матрицу `target/subtarget/arch` (например: `x86_64`, `mips_24kc`, `aarch64_cortex-a53` и др.).
- Реализовать кеширование:
  - `docker pull` заранее нужных SDK‑образов с retry и TTL.
  - Кеш исходников feed (если применимо) — аккуратно, чтобы не загрязнять workspace.
- Управление параллелизмом и ресурсами:
  - `concurrency: cancel-in-progress` для PR.
  - `permissions` по принципу минимально необходимых прав для `GITHUB_TOKEN`.
- **Результат**: параллельные сборки под несколько архитектур с контролем ресурсов и быстрым откликом.

### Фаза 3 — Тестирование и интеграции

- Модульные и интеграционные тесты для скриптов:
  - `tests/run.sh` и мок‑скрипты уже есть — расширить покрытие для путей сборки и валидаций.
- Проверка `.ipk`:
  - `scripts/verify_package.sh`: проверить наличие файлов, контрольных сумм, `postinst`/`prerm`, init‑скриптов и т.д.
- Smoke‑тесты в QEMU/VM (опционально):
  - `scripts/run_openwrt_vm.sh` — загрузка образа, установка `.ipk`, запуск сервиса, базовые проверки логов.
- **Результат**: автоматическая регрессия по ключевым сценариям установки и запуска.

### Фаза 4 — Подготовка к релизам

- Разделить dev‑ и release‑пайплайны:
  - `main/dev`: с `-dev` в поле `Version` `.ipk`.
  - release: без `-dev`, фиксированная версия из `PACKAGE/Makefile`.
- Отдельный workflow релиза по тегу `vX.Y.Z`:
  - Проверка, что `PKG_VERSION` совпадает с тегом; `PKG_RELEASE` — дата `YYYYMMDD[HHMM]`.
  - Сборка матрицы, загрузка артефактов, генерация release notes.
- Подпись артефактов (опционально):
  - `cosign`/Sigstore или detached‑подписи `sha256sum.sig`.
- **Результат**: воспроизводимые релизы с полным аудит‑трейлом и верификацией.

### Фаза 5 — Документация и поддержка

- Актуализировать `docs/packaging.md`, `docs/PACKAGES.md`, добавить quick‑start для локальной сборки через SDK.
- Раздел «Диагностика CI»: ссылки на `scripts/diagnose-*.sh` и типовые ошибки.
- Гайд по совместимости с BusyBox `ash` (стиль скриптов: `set -eu`, условный `pipefail`, `colors.sh`, форматирование `shfmt`).

## Готовые элементы и принципы (использовать)

- Валидация SDK‑образа и URL уже реализована — включать эти шаги **fail‑fast** в workflow перед `openwrt/gh-action-sdk`.
- Версионирование `.ipk` уже стандартизировано — поддерживать правила для `main` и PR.
- Артефакты складывать под `artifacts/<build-name>` и загружать `actions/upload-artifact@v5` с корректным именем.
- Не использовать `apt` для `opkg-utils` на Ubuntu 24.04; вместо этого `scripts/setup-opkg-utils.sh` и проверка `opkg-build -h`.

## Критерии готовности (DoD)

- Lint и Security‑проверки зелёные:
  - «Lint (shfmt)», "Lint (shellcheck)", "Lint (markdownlint)", "Lint (actionlint)", Trivy, Dependency Review, ShellCheck Security Analysis.
- Dev‑job собирает пакет минимум под 2 архитектуры, проходит `validate-sdk-*` и `validate-ipk`.
- Артефакты корректно именуются и доступны для скачивания; содержат `.ipk` и `sha256`.
- Документация обновлена, быстрый сценарий локальной сборки задокументирован.

## Команды для разработчиков (локально)

- Форматирование скриптов:
  - `shfmt -w -s -i 4 -ci -sr .`
- Установка `opkg-utils` (на Ubuntu 24.04):
  - `./scripts/setup-opkg-utils.sh && opkg-build -h`
- Проверка версии `.ipk` (после сборки):
  - `./scripts/validate-ipk-version.sh pr path/to/*.ipk`  # для PR
  - `./scripts/validate-ipk-version.sh main path/to/*.ipk`  # для main

## Примечания

- Соблюдать минимум прав для `GITHUB_TOKEN` и корректные `concurrency`/`permissions` в workflow (best practices GitHub Actions).
- Сохранять `PKG_VERSION` внутри файлов пакета неизменным при dev‑сборках; маркеры dev — только в имени CI‑артефакта и в поле `Version` `control` по правилам (main/PR).
