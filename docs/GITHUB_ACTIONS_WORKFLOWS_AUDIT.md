# Анализ GitHub Actions Workflows

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


**Дата анализа:** 2024  
**Репозиторий:** openwrt-captive-monitor  
**Директория workflows:** `.github/workflows/`

---

## Содержание

- [Обзор](#обзор)
- [Активные workflows](#активные-workflows)
  - [1. CI (ci.yml)](#1-ci-ciyml)
  - [2. Cleanup Artifacts and Runs (cleanup.yml)](#2-cleanup-artifacts-and-runs-cleanupyml)
  - [3. Release Please (release-please.yml)](#3-release-please-release-pleaseyml)
  - [4. Upload SDK to GitHub Release (upload-sdk-to-release.yml)](#4-upload-sdk-to-github-release-upload-sdk-to-releaseyml)
- [Отключённые workflows](#отключённые-workflows)
  - [5. Build OpenWrt packages (openwrt-build.yml.disabled)](#5-build-openwrt-packages-openwrt-buildymldisabled)
- [Взаимосвязи между workflows](#взаимосвязи-между-workflows)
- [Ключевые параметры и настройки](#ключевые-параметры-и-настройки)
- [Выводы](#выводы)

---

## Обзор

В проекте присутствует **5 workflow-файлов**, из которых **4 активных** и **1 отключённый** (с расширением `.disabled`).

### Список файлов

| Файл | Статус | Назначение |
|------|--------|------------|
| `ci.yml` | ✅ Активен | Основной CI/CD pipeline |
| `cleanup.yml` | ✅ Активен | Очистка старых артефактов и запусков |
| `release-please.yml` | ✅ Активен | Автоматическое создание релизов |
| `upload-sdk-to-release.yml` | ✅ Активен | Загрузка OpenWrt SDK на GitHub Releases |
| `openwrt-build.yml.disabled` | ❌ Отключён | Устаревший build workflow |

---

## Активные workflows

### 1. CI (ci.yml)

**Название:** CI  
**Файл:** `.github/workflows/ci.yml`  
**Размер:** 477 строк

#### Назначение

Основной CI/CD pipeline проекта. Выполняет линтинг, тестирование и сборку пакета с использованием официального OpenWrt SDK.

#### Триггеры

```yaml
on:
  push:
    branches: [main, feature/**, feature-*, fix/**, fix-*, chore/**, chore-*, docs/**, docs-*, hotfix/**, hotfix-*]
    tags: [v*]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

- **Push:** на main и feature/fix/chore/docs/hotfix ветки, а также на теги версий (`v*`)
- **Pull Request:** на ветку main
- **Manual trigger:** через workflow_dispatch

#### Permissions

```yaml
permissions:
  contents: write
  pull-requests: read
```

#### Concurrency

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Автоматическая отмена предыдущих запусков для той же ветки/тега.

#### Environment Variables

```yaml
env:
  OPENWRT_VERSION: "23.05.3"
  OPENWRT_ARCH: "x86_64"
  SDK_CHECKSUM: "f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254"
```

#### Jobs и их последовательность

```
lint (параллельно 4 линтера)
  ↓
test (зависит от lint)
  ↓
build-sdk (зависит от lint и test)
```

##### Job 1: `lint` (параллельный)

**Стратегия:** Matrix strategy с 4 линтерами

```yaml
strategy:
  matrix:
    linter: [shfmt, shellcheck, markdownlint, actionlint]
```

**Основные шаги:**

1. `actions/checkout@v5` - клонирование репозитория
2. `actions/cache@v4` - кеширование apt пакетов
3. Установка зависимостей (binutils, tar)
4. Установка специфичных инструментов для линтера:
   - **shfmt/shellcheck:** установка через apt (busybox, shfmt, shellcheck)
   - **markdownlint/actionlint:** использование Docker-based линтеров
5. Выполнение соответствующего линтера:
   - **shfmt:** `shfmt -d -s -i 4 -ci -sr .`
   - **shellcheck:** проверка всех `.sh` файлов + `openwrt_captive_monitor.sh`
   - **markdownlint:** через `DavidAnson/markdownlint-cli2-action@v20`
   - **actionlint:** через `reviewdog/action-actionlint@v1`

**Кеширование:**

```yaml
path: [/var/cache/apt/archives, /var/lib/apt/lists]
key: ${{ runner.os }}-apt-${{ hashFiles('.github/workflows/*.yml') }}
```

##### Job 2: `test`

**Зависимости:** `needs: lint`

**Основные шаги:**

1. Checkout репозитория
2. Кеширование apt пакетов
3. Установка BusyBox
4. Запуск тестов: `busybox ash tests/run.sh`
5. Загрузка результатов тестов как артефактов

**Артефакты:**

```yaml
name: test-results
path: tests/_out/
retention-days: 7
if-no-files-found: warn
```

##### Job 3: `build-sdk`

**Зависимости:** `needs: [lint, test]`

**Основные шаги:**

1. **Checkout репозитория**

2. **Установка базовых инструментов** (binutils, tar)

3. **Кеширование OpenWrt SDK:**

```yaml
path: openwrt-sdk-*
key: ${{ runner.os }}-openwrt-sdk-${{ env.OPENWRT_VERSION }}-${{ env.OPENWRT_ARCH }}-v3
```

4. **Установка build-зависимостей** (с ретраями):
   - build-essential, ccache, curl, file, gawk, gettext, git
   - libncurses5-dev, libssl-dev, python3, rsync, unzip
   - wget, zlib1g-dev, flex, bison
   - Используется механизм retry с 3 попытками и 10-секундными паузами

5. **Загрузка OpenWrt SDK** (только при отсутствии кеша):
   - Первичный источник: GitHub Releases (`nagual2/openwrt-captive-monitor`)
   - Fallback: официальный сайт OpenWrt
   - Retry логика: 3 попытки с экспоненциальной задержкой (1s, 2s, 4s)
   - Проверка размера файла (>100MB)
   - Проверка SHA256 checksum

6. **Поиск SDK директории:**
   - `find . -maxdepth 1 -type d -name "openwrt-sdk-*"`
   - Результат сохраняется в `$GITHUB_OUTPUT`

7. **Копирование пакета в SDK:**
   - Копирование из `package/openwrt-captive-monitor/*` в SDK
   - Копирование `VERSION` и `LICENSE` файлов

8. **Обновление и установка feeds** (с продвинутым retry механизмом):
   - Очистка старых feeds перед каждой попыткой
   - До 10 попыток с экспоненциальной задержкой + jitter
   - Git конфигурация для больших репозиториев:
     ```bash
     git config --global http.postBuffer 524288000
     git config --global core.compression 0
     ```

9. **Конфигурация SDK:**
   - `make defconfig`

10. **Сборка пакета:**
    - `make package/openwrt-captive-monitor/compile V=s`
    - Verbose mode для полного лога
    - Вывод последних 100 строк при ошибке

11. **Поиск и подготовка артефактов:**
    - Поиск .ipk файла в `SDK_DIR/bin/packages`
    - Копирование .ipk, Packages, Packages.gz в `artifacts/`
    - Копирование build.log

12. **Валидация пакета:**
    - `./scripts/validate_ipk.sh`

13. **Загрузка артефактов:**

```yaml
name: openwrt-captive-monitor-sdk-build
path: artifacts/
retention-days: 30
```

14. **Прикрепление к релизу** (только для тегов):
    - Условие: `github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')`
    - Используется `softprops/action-gh-release@v2`
    - Прикрепляемые файлы: .ipk, Packages, Packages.gz, build.log

15. **Отображение информации о пакете:**
    - Извлечение control.tar.gz из .ipk
    - Вывод содержимого control файла

#### Используемые GitHub Actions

- `actions/checkout@v5` - клонирование репозитория
- `actions/cache@v4` - кеширование (apt пакеты, SDK)
- `actions/upload-artifact@v5` - загрузка артефактов
- `DavidAnson/markdownlint-cli2-action@v20` - markdown линтинг
- `reviewdog/action-actionlint@v1` - workflow линтинг
- `softprops/action-gh-release@v2` - публикация релиза

#### Особенности

- **Продвинутый retry механизм** для сетевых операций (apt-get, feeds update, SDK download)
- **Экспоненциальная задержка с jitter** для feeds update (до 10 попыток)
- **Двухуровневая система загрузки SDK**: GitHub CDN → Official mirror
- **Строгая валидация SDK**: размер файла + SHA256 checksum
- **Verbose build mode** для детальной диагностики
- **Кеширование на всех уровнях**: apt пакеты, OpenWrt SDK

---

### 2. Cleanup Artifacts and Runs (cleanup.yml)

**Название:** Cleanup Artifacts and Runs  
**Файл:** `.github/workflows/cleanup.yml`  
**Размер:** 114 строк

#### Назначение

Автоматическая очистка старых артефактов и workflow runs для экономии места в GitHub storage.

#### Триггеры

```yaml
on:
  schedule:
    - cron: '0 3 * * *'  # Каждый день в 3:00 UTC
  workflow_dispatch:
    inputs:
      force:
        description: 'Force delete all artifacts (including recent ones)'
        required: false
        default: 'false'
```

- **Расписание:** ежедневно в 03:00 UTC
- **Manual trigger:** с возможностью принудительного удаления всех артефактов

#### Permissions

```yaml
permissions:
  actions: write
  contents: read
```

#### Jobs

##### Job: `cleanup`

**Основные шаги:**

1. **Checkout code** (`actions/checkout@v5`)

2. **Delete all artifacts** (только при manual trigger с `force=true`):
   - Использует GitHub CLI (`gh`)
   - Получает список всех артефактов через API
   - Удаляет каждый артефакт через DELETE запрос

```bash
gh api --paginate -H "Accept: application/vnd.github+json" \
  /repos/${{ github.repository }}/actions/artifacts \
  --jq '.artifacts[] | .id' | \
xargs -I{} gh api --silent \
  -X DELETE \
  /repos/${{ github.repository }}/actions/artifacts/{} \
  -f confirm=true
```

3. **Delete old artifacts** (только при scheduled запуске):
   - Использует `actions/github-script@v8`
   - **Retention period:** 1 день
   - Получает все артефакты (до 100 штук)
   - Вычисляет возраст каждого артефакта
   - Удаляет артефакты старше 1 дня

```javascript
const retentionDays = 1;
const artifactAge = (now - new Date(artifact.created_at)) / (1000 * 60 * 60 * 24);
if (artifactAge > retentionDays) {
  await github.rest.actions.deleteArtifact({...});
}
```

4. **Cleanup workflow runs:**
   - Использует `actions/github-script@v8`
   - **Retention period:** 3 дня
   - **Minimum runs to keep:** 5 (всегда сохраняются минимум 5 последних запусков)
   - Сортирует запуски по дате создания (старые первыми)
   - Удаляет только если возраст > 3 дней И осталось > 5 запусков

```javascript
const retainDays = 3;
const keepMinimumRuns = 5;
if (runAge > retainDays && runsLeft > keepMinimumRuns) {
  await github.rest.actions.deleteWorkflowRun({...});
}
```

5. **Show disk usage after cleanup:**
   - `df -h` для мониторинга результата

#### Используемые GitHub Actions

- `actions/checkout@v5`
- `actions/github-script@v8`

#### Параметры очистки

| Тип | Retention | Минимум для хранения | Частота |
|-----|-----------|----------------------|---------|
| Artifacts | 1 день | - | Ежедневно 03:00 UTC |
| Workflow runs | 3 дня | 5 последних запусков | Ежедневно 03:00 UTC |

#### Особенности

- **Бережная очистка:** всегда сохраняются минимум 5 последних workflow runs
- **Два режима работы:**
  - Scheduled: удаление только старых артефактов/runs по правилам
  - Manual force: удаление всех артефактов без исключений
- **Error handling:** продолжает работу даже при ошибках удаления отдельных элементов
- **Monitoring:** выводит disk usage после очистки

---

### 3. Release Please (release-please.yml)

**Название:** Release Please  
**Файл:** `.github/workflows/release-please.yml`  
**Размер:** 75 строк

#### Назначение

Автоматическое создание релизов на основе Conventional Commits с помощью Release Please от Google.

#### Триггеры

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

- **Push:** только на main ветку
- **Manual trigger:** через workflow_dispatch

#### Permissions

```yaml
permissions:
  contents: write
  pull-requests: write
  actions: read
  checks: write
```

#### Jobs и их последовательность

```
release-please (создаёт PR/релиз)
  ↓
update-version (зависит от release-please, если релиз создан)
  ↓
trigger-sdk-build (зависит от release-please и update-version)
```

##### Job 1: `release-please`

**Outputs:**

```yaml
outputs:
  release_created: ${{ steps.release.outputs.release_created }}
  tag_name: ${{ steps.release.outputs.tag_name }}
```

**Основные шаги:**

1. **Release Please** - `googleapis/release-please-action@v4`
   - Использует манифест: `.release-please-manifest.json`
   - Автоматически создаёт/обновляет Release PR
   - При мердже Release PR создаёт GitHub Release и тег

#### Release Please работает следующим образом:

- Анализирует Conventional Commits в main ветке
- Определяет версию согласно SemVer (feat → minor, fix → patch, BREAKING CHANGE → major)
- Создаёт/обновляет PR с изменениями CHANGELOG
- При мердже PR создаёт GitHub Release с тегом

##### Job 2: `update-version`

**Зависимости:** `needs: release-please`  
**Условие:** `if: needs.release-please.outputs.release_created == 'true'`

**Основные шаги:**

1. **Checkout** с полной историей (`fetch-depth: 0`)

2. **Update package version:**
   - Извлечение версии из тега: `TAG="${{ needs.release-please.outputs.tag_name }}"`
   - Обновление `VERSION` файла
   - Обновление `PKG_VERSION` в `package/openwrt-captive-monitor/Makefile`
   - Сброс `PKG_RELEASE` в 1 для новой версии
   - Commit и push изменений:

```bash
git config --local user.email "action@github.com"
git config --local user.name "GitHub Action"
git add VERSION package/openwrt-captive-monitor/Makefile
git commit -m "chore(release): bump version to $VERSION"
git push
```

##### Job 3: `trigger-sdk-build`

**Зависимости:** `needs: [release-please, update-version]`  
**Условие:** `if: needs.release-please.outputs.release_created == 'true'`

**Основные шаги:**

1. **Trigger SDK build:**
   - Просто выводит информацию о созданном релизе
   - Настоящий build триггерится автоматически через push тега (workflow `ci.yml`)

#### Используемые GitHub Actions

- `actions/checkout@v5`
- `googleapis/release-please-action@v4`

#### Особенности

- **Автоматическое версионирование** на основе Conventional Commits
- **Двухэтапный процесс:**
  1. Release PR создаётся и обновляется автоматически
  2. При мердже PR создаётся релиз
- **Автоматическое обновление версий** в коде после создания релиза
- **Интеграция с CI workflow:** тег автоматически запускает build и attach артефактов

#### Связь с другими workflows

- Создание тега триггерит `ci.yml` (условие: `startsWith(github.ref, 'refs/tags/')`)
- `ci.yml` собирает пакет и прикрепляет его к релизу

---

### 4. Upload SDK to GitHub Release (upload-sdk-to-release.yml)

**Название:** Upload SDK to GitHub Release  
**Файл:** `.github/workflows/upload-sdk-to-release.yml`  
**Размер:** 119 строк

#### Назначение

Загрузка OpenWrt SDK на GitHub Releases для использования в качестве CDN-зеркала в CI/CD pipeline. Ускоряет загрузку SDK в workflow `ci.yml`.

#### Триггеры

```yaml
on:
  workflow_dispatch:
    inputs:
      sdk_version:
        description: 'OpenWrt SDK version'
        required: true
        default: '23.05.3'
      force_update:
        description: 'Force update existing release'
        required: false
        default: 'false'
        type: boolean
```

- **Только manual trigger** через workflow_dispatch
- **Параметры:**
  - `sdk_version` - версия SDK (по умолчанию 23.05.3)
  - `force_update` - принудительное обновление существующего релиза

#### Permissions

```yaml
permissions:
  contents: write
```

#### Jobs

##### Job: `upload-sdk`

**Основные шаги:**

1. **Checkout репозитория**

2. **Install dependencies:**
   - wget
   - gh (GitHub CLI)

3. **Authenticate with GitHub CLI:**

```bash
echo "${{ secrets.GITHUB_TOKEN }}" | gh auth login --with-token
```

4. **Download and upload SDK to GitHub Release:**
   - Формирование имени файла: `openwrt-sdk-${SDK_VERSION}-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz`
   - Загрузка с официального сайта OpenWrt:
     ```
     https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/x86/64/${SDK_FILE}
     ```
   - Вычисление SHA256 checksum для integrity
   - **Если `force_update=true`:** удаление существующего релиза `sdk-${SDK_VERSION}`
   - Создание GitHub Release:
     ```
     Tag: sdk-${SDK_VERSION}
     Title: OpenWrt SDK ${SDK_VERSION} Mirror
     Notes: SDK mirror for fast CI/CD builds. Checksum: $SHA256
     ```
   - Если релиз уже существует: обновление файлов
   - Создание файла `sdk-checksum.txt` с контрольной суммой
   - Загрузка checksum файла с `--clobber` (перезапись)
   - Формирование download URL для использования в CI:
     ```
     https://github.com/$REPO/releases/download/sdk-${SDK_VERSION}/$SDK_FILE
     ```

5. **Verify upload:**
   - Проверка доступности файла через `wget --spider`
   - Вывод списка assets в релизе через `gh release view`

#### Используемые GitHub Actions

- `actions/checkout@v5`

#### Используемые инструменты

- `wget` - загрузка SDK с официального сайта
- `gh` (GitHub CLI) - создание релиза и загрузка файлов
- `sha256sum` - вычисление контрольной суммы

#### Особенности

- **CDN-зеркало для CI:** загруженный SDK используется в `ci.yml` как primary source
- **Force update режим:** позволяет переписать существующий релиз
- **Автоматическая верификация:** проверка доступности после загрузки
- **Checksum файл:** для integrity проверки в CI

#### Связь с другими workflows

- SDK загруженный этим workflow используется в `ci.yml`:
  ```bash
  SDK_URL="https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-${SDK_VERSION}/${SDK_FILE}"
  FALLBACK_URL="https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/x86/64/${SDK_FILE}"
  ```
- Fallback на официальный сайт если GitHub CDN недоступен

---

## Отключённые workflows

### 5. Build OpenWrt packages (openwrt-build.yml.disabled)

**Название:** Build OpenWrt packages  
**Файл:** `.github/workflows/openwrt-build.yml.disabled`  
**Размер:** 229 строк  
**Статус:** ❌ **ОТКЛЮЧЁН**

#### Назначение

Старый workflow для сборки пакетов без использования официального OpenWrt SDK. Использовал standalone build script `scripts/build_ipk.sh`.

#### Почему отключён?

Заменён на `ci.yml` который использует **официальный OpenWrt SDK** вместо самописного скрипта сборки. SDK-подход более надёжный и соответствует стандартам OpenWrt.

#### Отличия от текущего ci.yml

| Параметр | openwrt-build.yml.disabled | ci.yml (текущий) |
|----------|----------------------------|------------------|
| Сборка | `./scripts/build_ipk.sh` | OpenWrt SDK + `make` |
| Линтинг | В одном job | Параллельно (4 линтера) |
| Тестирование | `busybox sh tests/run.sh` | `busybox ash tests/run.sh` |
| Артефакты | dist/opkg/<arch>/ | SDK bin/packages/ |
| SDK | Не используется | Официальный SDK кешируется |

#### Jobs структура (для справки)

```
build (сборка пакета)
  ↓
release (публикация релиза, только для тегов)
```

#### Триггеры (были бы, если активен)

```yaml
on:
  push:
    branches: [main, feature/**, feature-*, fix/**, fix-*, chore/**, chore-*, docs/**, docs-*, hotfix/**, hotfix-*]
    tags: [v*]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

Аналогичны `ci.yml`.

---

## Взаимосвязи между workflows

### Диаграмма взаимодействий

```
┌─────────────────────────────────────────────────────────────────┐
│                          Developer                               │
└───────┬─────────────────────────────────────────────────────────┘
        │
        │ Push to main with Conventional Commits
        ↓
┌───────────────────────┐
│  release-please.yml   │ Анализирует коммиты
│  (автоматический PR)  │ Создаёт Release PR
└───────┬───────────────┘
        │
        │ При мердже Release PR
        ↓
┌───────────────────────┐
│  release-please.yml   │ Создаёт GitHub Release
│  (создание релиза)    │ Создаёт тег v*
└───────┬───────────────┘
        │
        │ Обновление VERSION + Makefile
        │ Push тега триггерит...
        ↓
┌───────────────────────┐
│      ci.yml           │ Lint → Test → Build SDK
│  (основной CI/CD)     │ Attach artifacts to release
└───────┬───────────────┘
        │
        │ Использует SDK из
        ↓
┌─────────────────────────┐
│ upload-sdk-to-release.yml│ (manual) Загружает SDK
│  (SDK CDN зеркало)      │ на GitHub Releases
└─────────────────────────┘

        ┌─────────────────────────┐
        │    cleanup.yml          │ (scheduled) Ежедневная
        │  (очистка артефактов)   │ очистка старых runs
        └─────────────────────────┘
```

### Описание взаимосвязей

1. **Developer → release-please.yml:**
   - Разработчик делает push в main с Conventional Commits
   - Release Please анализирует коммиты и создаёт/обновляет Release PR

2. **release-please.yml → release-please.yml:**
   - При мердже Release PR создаётся GitHub Release и тег
   - Job `update-version` обновляет версию в коде
   - Job `trigger-sdk-build` информирует о необходимости сборки

3. **release-please.yml → ci.yml:**
   - Созданный тег (`v*`) автоматически триггерит `ci.yml`
   - `ci.yml` собирает пакет и прикрепляет артефакты к релизу

4. **upload-sdk-to-release.yml → ci.yml:**
   - SDK загруженный на GitHub Releases используется как primary CDN
   - В `ci.yml` сначала пробуется GitHub URL, потом fallback на официальный сайт

5. **cleanup.yml (независимый):**
   - Работает по расписанию (ежедневно в 03:00 UTC)
   - Не зависит от других workflows
   - Очищает старые артефакты всех workflows

### Зависимости между jobs внутри workflows

#### ci.yml

```
lint (matrix: 4 параллельных линтера)
  ↓
test
  ↓
build-sdk → (если тег) → attach to release
```

#### release-please.yml

```
release-please
  ↓
update-version
  ↓
trigger-sdk-build
```

---

## Ключевые параметры и настройки

### Кеширование

| Workflow | Что кешируется | Key | Сохранение |
|----------|----------------|-----|------------|
| ci.yml (lint) | apt packages | `${{ runner.os }}-apt-${{ hashFiles('.github/workflows/*.yml') }}` | Инвалидируется при изменении workflow файлов |
| ci.yml (test) | apt packages | То же | То же |
| ci.yml (build-sdk) | OpenWrt SDK | `${{ runner.os }}-openwrt-sdk-${{ env.OPENWRT_VERSION }}-${{ env.OPENWRT_ARCH }}-v3` | Инвалидируется при смене версии SDK или архитектуры |

### Retry механизмы

#### ci.yml - Build dependencies

```bash
# 3 попытки с 10-секундной паузой
for attempt in {1..3}; do
  if sudo apt-get update ...; then
    break
  else
    sleep 10
  fi
done
```

#### ci.yml - SDK download

```bash
# 3 попытки с экспоненциальной задержкой (1s, 2s, 4s)
for attempt in {1..3}; do
  if wget ... "$SDK_URL" ...; then
    break
  else
    wait_time=$((2 ** (attempt - 1)))
    sleep "$wait_time"
  fi
done
```

#### ci.yml - Feeds update/install

```bash
# 10 попыток с экспоненциальной задержкой + jitter
max_attempts=10
base_wait=$((2 ** (attempt - 1)))
jitter=$((base_wait / 5))
wait_time=$((base_wait + RANDOM % jitter))
```

**Особенность:** jitter предотвращает thundering herd problem при массовых ретраях.

### Timeouts

| Операция | Timeout | Retries |
|----------|---------|---------|
| apt-get http | 30s | 3 |
| wget SDK download | 120s (CDN), 300s (fallback) | 3 (CDN), 3 (fallback) |
| feeds update | Нет явного timeout | 10 попыток |

### Retention periods

| Тип артефакта | Retention (workflow) | Retention (cleanup) | Примечание |
|---------------|----------------------|---------------------|------------|
| test-results | 7 дней | 1 день | cleanup перезаписывает |
| sdk-build artifacts | 30 дней | 1 день | cleanup перезаписывает |
| workflow runs | - | 3 дня (минимум 5) | Всегда сохраняется ≥5 runs |

**Важно:** `cleanup.yml` удаляет артефакты старше 1 дня, игнорируя retention из workflow.

### Concurrency control

**ci.yml:**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

- Отменяет предыдущие запуски для той же ветки/тега
- Экономит runner minutes
- Ускоряет feedback loop для разработчиков

**Другие workflows:** не используют concurrency control.

### Environment variables

#### ci.yml

```yaml
env:
  OPENWRT_VERSION: "23.05.3"
  OPENWRT_ARCH: "x86_64"
  SDK_CHECKSUM: "f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254"
```

**Централизованное управление версией SDK и checksum для consistency.**

### Используемые версии actions

| Action | Версия | Workflows |
|--------|--------|-----------|
| actions/checkout | v5 | Все |
| actions/cache | v4 | ci.yml |
| actions/upload-artifact | v5 | ci.yml |
| actions/download-artifact | v6 | openwrt-build.yml.disabled |
| actions/github-script | v8 | cleanup.yml |
| DavidAnson/markdownlint-cli2-action | v20 | ci.yml |
| reviewdog/action-actionlint | v1 | ci.yml |
| softprops/action-gh-release | v2 | ci.yml, openwrt-build.yml.disabled |
| googleapis/release-please-action | v4 | release-please.yml |

### Permissions по workflows

| Workflow | contents | pull-requests | actions | checks |
|----------|----------|---------------|---------|--------|
| ci.yml | write | read | - | - |
| cleanup.yml | read | - | write | - |
| release-please.yml | write | write | read | write |
| upload-sdk-to-release.yml | write | - | - | - |

### Runners

**Все workflows используют:** `ubuntu-latest`

---

## Выводы

### Архитектура CI/CD

Проект использует **современную многоуровневую CI/CD архитектуру** с разделением ответственности:

1. **Основной pipeline** (ci.yml): линтинг → тестирование → сборка
2. **Release automation** (release-please.yml): автоматическое версионирование и релизы
3. **Инфраструктура** (upload-sdk-to-release.yml): CDN-зеркало для SDK
4. **Обслуживание** (cleanup.yml): автоматическая очистка storage

### Сильные стороны

✅ **Надёжность:**

- Продвинутые retry механизмы с экспоненциальной задержкой и jitter
- Двухуровневая система загрузки SDK (CDN → fallback)
- Строгая валидация (checksums, размеры файлов, структура пакетов)

✅ **Производительность:**

- Многоуровневое кеширование (apt, SDK)
- Параллельный линтинг (matrix strategy)
- Concurrency control для отмены лишних запусков
- GitHub CDN для быстрой загрузки SDK

✅ **Автоматизация:**

- Release Please для автоматического версионирования
- Автоматическое обновление версий в коде после релиза
- Автоматическое прикрепление артефактов к релизам
- Ежедневная очистка старых артефактов

✅ **Observability:**

- Verbose build logs для диагностики
- Подробный вывод на каждом этапе
- Сохранение build.log как артефакт
- Вывод package control information после сборки

### Потенциальные улучшения

⚠️ **Cleanup workflow:**

- Retention 1 день для артефактов слишком агрессивный (workflow указывает 7/30 дней)
- Может удалять артефакты до истечения их официального retention period

⚠️ **SDK checksum:**

- Hardcoded в `ci.yml` (env.SDK_CHECKSUM)
- При обновлении SDK нужно вручную менять в двух местах (workflow + variable)

⚠️ **Отключённый workflow:**

- `openwrt-build.yml.disabled` можно удалить (устарел)
- Или перенести в docs/ как reference

⚠️ **Error handling в cleanup.yml:**

- `continue-on-error` для некоторых ошибок может скрывать проблемы
- Но это допустимо для cleanup job

### Соответствие best practices

✅ **Использование официального OpenWrt SDK вместо самописного build script**  
✅ **Conventional Commits + Release Please для версионирования**  
✅ **Pinned versions для всех actions (v5, v4, etc.)**  
✅ **Минимальные permissions для каждого workflow**  
✅ **Кеширование на всех уровнях**  
✅ **Retry логика для нестабильных операций**  
✅ **Concurrency control для экономии ресурсов**  
✅ **Artifact validation перед публикацией**

### Метрики

| Метрика | Значение |
|---------|----------|
| Общее количество workflows | 5 (4 активных, 1 отключён) |
| Общее количество jobs | 9 (ci: 3, cleanup: 1, release-please: 3, upload-sdk: 1, disabled: 2) |
| Строк кода в workflows | ~1000 строк |
| Используемые actions | 9 разных actions |
| Scheduled workflows | 1 (cleanup) |
| Manual workflows | 2 (upload-sdk, cleanup с force) |
| Workflows с кешированием | 1 (ci.yml) |
| Cache keys | 2 (apt, SDK) |
| Retention periods | 7д, 30д (артефакты), 1д (cleanup), 3д (runs) |

### Рекомендации

1. **Согласовать retention policies:** установить 1 день в workflow артефактах ИЛИ увеличить в cleanup.yml
2. **Рассмотреть dynamic SDK checksum:** загружать checksum из sdk-checksum.txt в GitHub Release
3. **Удалить или архивировать** `openwrt-build.yml.disabled`
4. **Добавить GitHub Environments:** для разделения staging/production релизов (опционально)
5. **Рассмотреть matrix strategy для build-sdk:** сборка для нескольких архитектур параллельно (если нужно)

---

**Конец анализа**

*Этот документ содержит только фактическую информацию, извлечённую из реальных workflow-файлов в директории `.github/workflows/`. Никакие предположения или домыслы не включены.*
