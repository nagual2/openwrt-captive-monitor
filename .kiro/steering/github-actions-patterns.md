# Паттерны работы с GitHub Actions

## Concurrency в GitHub Actions

### Базовый формат

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true|false
```

**Компоненты group:**
- `github.workflow` - имя workflow (уникально для каждого файла)
- `github.ref` - полная ссылка на ветку/тег/PR (refs/heads/main, refs/pull/123/merge)

**Преимущества:**
- Изоляция между разными workflow
- Изоляция между разными ветками/PR
- Workflow для main не отменяют workflow для PR и наоборот

### Правила выбора cancel-in-progress

**cancel-in-progress: true** - использовать когда:
- Workflow запускается часто (при каждом коммите в PR)
- Результаты предыдущего запуска становятся неактуальными
- Workflow выполняется быстро (< 10 минут)
- Примеры: lint, test, security scanning для PR

**cancel-in-progress: false** - использовать когда:
- Workflow создает критичные артефакты (релизы, Docker образы)
- Workflow выполняется долго (> 10 минут)
- Workflow запускается по тегам или schedule
- Workflow изменяет состояние (создает релизы, теги, загружает артефакты)
- Примеры: release builds, Docker image builds, cleanup, version tagging

### Матрица политик для типичных workflow

| Workflow Type | Триггеры | cancel-in-progress | Обоснование |
|---------------|----------|-------------------|-------------|
| CI (lint, test) | push, pull_request | true для PR, false для main | Быстрая обратная связь для PR |
| Build SDK Images | push (main), schedule | false | Долгие сборки, критичные артефакты |
| Release Build | push (tags) | false | Релизные сборки критичны |
| Release Please | push (main) | false | Создание релизов не отменяется |
| Security Scan | push, pull_request, schedule | true | Отменяет устаревшие сканирования |
| Cleanup | schedule, workflow_dispatch | false | Очистка должна завершиться |
| Manual Workflow | workflow_dispatch | false | Ручные запуски не отменяются |

### Условная отмена (main vs PR)

```yaml
# Отменять для PR, сохранять для main
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

### Документирование concurrency

**Обязательный комментарий перед секцией concurrency:**

```yaml
# Concurrency control: Cancel previous runs for the same PR to save resources
# - Group: Isolated per workflow and branch/PR
# - Cancel policy: true for PRs to get fast feedback on latest changes
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Формат комментария:**
1. Краткое описание политики
2. Объяснение формулы группы
3. Объяснение значения cancel-in-progress

### Примеры для разных сценариев

**1. CI workflow для PR:**
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

# Concurrency control: Cancel for PRs, preserve for main branch
# - Group: Isolated per workflow and branch/PR
# - Cancel policy: true for PRs (fast feedback), false for main (preserve history)
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

jobs:
  lint:
    runs-on: ubuntu-24.04
    # ...
```

**2. Release workflow:**
```yaml
name: Release Build

on:
  push:
    tags: ['v*']

# Concurrency control: Never cancel release builds to ensure all artifacts are created
# - Group: Isolated per workflow and tag
# - Cancel policy: false to guarantee completion of release builds
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-24.04
    # ...
```

**3. Docker image build:**
```yaml
name: Build SDK Images

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'
  workflow_dispatch:

# Concurrency control: Never cancel image builds as they take long time
# - Group: Isolated per workflow and branch
# - Cancel policy: false to ensure all images are built and pushed
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-24.04
    # ...
```

## Работа с GitHub CLI (gh)

### Запуск workflow

**Всегда указывай --ref при запуске:**

```bash
# Запустить workflow на текущей ветке
gh workflow run "Build SDK Images" --ref $(git branch --show-current)

# Запустить на конкретной ветке
gh workflow run "Build SDK Images" --ref feature/my-feature

# Запустить с параметрами
gh workflow run "OpenWrt Build" \
  --ref feature/my-feature \
  -f openwrt_version=23.05.5 \
  -f architecture=x86-64
```

**Почему важно указывать --ref:**
- Без --ref workflow запустится на default branch (main)
- Это может привести к запуску неправильной версии кода
- Особенно критично для feature branches

### Мониторинг workflow

```bash
# Список последних запусков
gh run list --limit 10

# Статус запусков для конкретной ветки
gh run list --branch feature/my-feature --limit 5

# Статус конкретного workflow
gh run list --workflow "Build SDK Images" --limit 5

# Запущенные workflow
gh run list --status in_progress

# Проваленные workflow
gh run list --status failure --limit 5
```

### Просмотр логов

```bash
# Логи последнего запуска
gh run view --log

# Логи конкретного запуска
gh run view 12345678 --log

# Сохранить логи в файл
gh run view 12345678 --log > workflow.log

# Логи конкретного job
gh run view 12345678 --log --job lint
```

### Отмена workflow

```bash
# Отменить конкретный запуск
gh run cancel 12345678

# Отменить все запущенные workflow для текущей ветки
gh run list --status in_progress --branch $(git branch --show-current) \
  --json databaseId --jq '.[].databaseId' | \
  ForEach-Object { gh run cancel $_ }

# Отменить все запущенные workflow для конкретного workflow
gh run list --workflow "Build SDK Images" --status in_progress \
  --json databaseId --jq '.[].databaseId' | \
  ForEach-Object { gh run cancel $_ }
```

### Работа с артефактами

```bash
# Список артефактов последнего запуска
gh run list --limit 1 --json databaseId --jq '.[0].databaseId' | \
  ForEach-Object { gh run view $_ --json artifacts }

# Скачать артефакты
gh run download 12345678

# Скачать конкретный артефакт
gh run download 12345678 --name openwrt-package
```

### Создание PR

```bash
# Создать PR с title и body
gh pr create \
  --title "feat: add new feature" \
  --body "Description of changes"

# Создать PR с автоматическим заполнением
gh pr create --fill

# Создать draft PR
gh pr create --draft --title "WIP: feature"

# Проверить статус PR
gh pr status

# Список PR
gh pr list --limit 10
```

### Проверка прав токена

```bash
# Проверить текущего пользователя
gh auth status

# Проверить scopes токена
gh api user -i | grep x-oauth-scopes

# Необходимые scopes для workflow:
# - repo (полный доступ к репозиториям)
# - workflow (запуск и управление workflow)
```

## Matrix builds

### Базовая конфигурация

```yaml
jobs:
  build:
    strategy:
      matrix:
        arch:
          - {target: x86, subtarget: 64}
          - {target: ath79, subtarget: generic}
          - {target: ramips, subtarget: mt76x8}
      max-parallel: 4
      fail-fast: false
    
    runs-on: ubuntu-24.04
    
    steps:
      - name: Build for ${{ matrix.arch.target }}-${{ matrix.arch.subtarget }}
        run: |
          echo "Building for ${{ matrix.arch.target }}-${{ matrix.arch.subtarget }}"
```

### Параметры strategy

**max-parallel:**
- Ограничивает количество параллельных jobs
- Для GitHub Actions: 4 (ограничение ресурсов)
- Для локальной сборки: 8 (если достаточно RAM)

**fail-fast:**
- `true` (default): Отменить все jobs при ошибке в одном
- `false`: Продолжить выполнение остальных jobs
- Используй `false` для сборки всех архитектур даже при ошибке

### Исключение комбинаций

```yaml
strategy:
  matrix:
    os: [ubuntu-24.04, windows-latest]
    arch: [x86-64, arm64]
    exclude:
      - os: windows-latest
        arch: arm64  # Windows ARM64 не поддерживается
```

### Включение дополнительных комбинаций

```yaml
strategy:
  matrix:
    os: [ubuntu-24.04]
    arch: [x86-64, arm64]
    include:
      - os: macos-latest
        arch: arm64  # Добавить macOS ARM64
```

### Использование matrix в названиях

```yaml
jobs:
  build:
    name: Build ${{ matrix.arch.target }}-${{ matrix.arch.subtarget }}
    strategy:
      matrix:
        arch:
          - {target: x86, subtarget: 64}
    # ...
```

## Условное выполнение jobs

### Условия на основе ref

```yaml
jobs:
  integration-tests:
    # Запускать только на main или с меткой [integration]
    if: github.ref == 'refs/heads/main' || contains(github.event.head_commit.message, '[integration]')
    runs-on: ubuntu-24.04
    # ...
```

### Условия на основе типа события

```yaml
jobs:
  deploy:
    # Запускать только для тегов
    if: startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-24.04
    # ...
  
  build-pr:
    # Запускать только для PR
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-24.04
    # ...
```

### Условия на основе изменений в файлах

```yaml
jobs:
  build-docker:
    # Запускать только если изменился Dockerfile
    if: contains(github.event.head_commit.modified, 'docker/sdk/Dockerfile')
    runs-on: ubuntu-24.04
    # ...
```

### Условия на основе результатов предыдущих jobs

```yaml
jobs:
  test:
    runs-on: ubuntu-24.04
    # ...
  
  deploy:
    needs: test
    # Запускать только если test успешен
    if: success()
    runs-on: ubuntu-24.04
    # ...
  
  cleanup:
    needs: test
    # Запускать всегда, даже если test провалился
    if: always()
    runs-on: ubuntu-24.04
    # ...
```

## Timeout и retry

### Timeout на уровне job

```yaml
jobs:
  build:
    runs-on: ubuntu-24.04
    timeout-minutes: 30  # Job будет отменен через 30 минут
    steps:
      # ...
```

### Timeout на уровне step

```yaml
steps:
  - name: Download SDK
    timeout-minutes: 10  # Step будет отменен через 10 минут
    run: |
      bash docker/sdk/download-sdk.sh
```

### Retry для steps

```yaml
steps:
  - name: Download with retry
    uses: nick-invision/retry@v2
    with:
      timeout_minutes: 10
      max_attempts: 3
      retry_wait_seconds: 30
      command: bash docker/sdk/download-sdk.sh
```

## Кеширование

### Кеширование зависимостей

```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.npm
    key: ${{ runner.os }}-deps-${{ hashFiles('**/requirements.txt', '**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-deps-
```

### Кеширование Docker layers

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Cache Docker layers
  uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-

- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
```

### Кеширование SDK

```yaml
- name: Cache OpenWrt SDK
  uses: actions/cache@v4
  with:
    path: /tmp/sdk
    key: sdk-${{ env.OPENWRT_VERSION }}-${{ env.SDK_TARGET }}-${{ env.SDK_SUBTARGET }}
```

## Секреты и переменные окружения

### Использование секретов

```yaml
steps:
  - name: Login to GHCR
    run: |
      echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
```

### Переменные окружения на уровне workflow

```yaml
env:
  OPENWRT_VERSION: 23.05.5
  SDK_TARGET: x86

jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - name: Use env vars
        run: |
          echo "Building for OpenWrt $OPENWRT_VERSION"
```

### Переменные окружения на уровне job

```yaml
jobs:
  build:
    runs-on: ubuntu-24.04
    env:
      BUILD_TYPE: release
    steps:
      - name: Build
        run: |
          echo "Build type: $BUILD_TYPE"
```

### Переменные окружения на уровне step

```yaml
steps:
  - name: Build with custom env
    env:
      CUSTOM_VAR: value
    run: |
      echo "Custom: $CUSTOM_VAR"
```

## Permissions

### Минимальные права для workflow

```yaml
permissions:
  contents: read  # Чтение репозитория
  packages: write  # Запись в GHCR
  pull-requests: write  # Комментарии к PR
```

### Права для конкретного job

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-24.04
    # ...
  
  comment:
    permissions:
      pull-requests: write
    runs-on: ubuntu-24.04
    # ...
```

### Типичные permissions

- `contents: read` - чтение кода
- `contents: write` - создание коммитов, тегов, релизов
- `packages: read` - pull Docker образов из GHCR
- `packages: write` - push Docker образов в GHCR
- `pull-requests: write` - комментарии к PR
- `issues: write` - создание и комментирование issues
- `actions: write` - управление workflow runs

## Reusable workflows

### Определение reusable workflow

```yaml
# .github/workflows/build-package.yml
name: Build Package

on:
  workflow_call:
    inputs:
      architecture:
        required: true
        type: string
      openwrt_version:
        required: true
        type: string
    outputs:
      package_path:
        description: "Path to built package"
        value: ${{ jobs.build.outputs.package_path }}

jobs:
  build:
    runs-on: ubuntu-24.04
    outputs:
      package_path: ${{ steps.build.outputs.path }}
    steps:
      - name: Build
        id: build
        run: |
          echo "path=/tmp/package.ipk" >> $GITHUB_OUTPUT
```

### Использование reusable workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  build-x86:
    uses: ./.github/workflows/build-package.yml
    with:
      architecture: x86-64
      openwrt_version: 23.05.5
  
  build-arm:
    uses: ./.github/workflows/build-package.yml
    with:
      architecture: aarch64
      openwrt_version: 23.05.5
```

## Отладка workflow

### Включение debug логов

```bash
# Установить секреты в репозитории
ACTIONS_RUNNER_DEBUG=true
ACTIONS_STEP_DEBUG=true
```

### Использование tmate для интерактивной отладки

```yaml
- name: Setup tmate session
  if: failure()
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 30
```

### Вывод контекста для отладки

```yaml
- name: Dump GitHub context
  run: echo '${{ toJSON(github) }}'

- name: Dump job context
  run: echo '${{ toJSON(job) }}'

- name: Dump runner context
  run: echo '${{ toJSON(runner) }}'
```
