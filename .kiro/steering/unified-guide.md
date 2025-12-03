# Объединённое руководство по проекту OpenWrt Captive Monitor

## Языковые предпочтения

- Общение с пользователем на русском языке
- Планы, документация и объяснения на русском
- Git commit сообщения только на английском
- Показывать команды перед выполнением для прозрачности

## Приоритет использования команд

### Правило: Нативные Windows команды в первую очередь

**Всегда используй нативные Windows/PowerShell команды когда это возможно, вместо WSL.**

WSL добавляет overhead на запуск Linux окружения. Используй WSL только когда нет альтернативы.

### Матрица выбора команд

| Задача | ❌ Не используй WSL | ✅ Используй нативно |
|--------|---------------------|----------------------|
| Git операции | `wsl git status` | `git status` |
| GitHub CLI | `wsl gh pr list` | `gh pr list` |
| Docker | `wsl docker ps` | `docker ps` |
| Файловые операции | `wsl ls -la` | `Get-ChildItem` или `dir` |
| Чтение файлов | `wsl cat file.txt` | `Get-Content file.txt` |
| Копирование | `wsl cp file1 file2` | `Copy-Item file1 file2` |
| Удаление | `wsl rm file` | `Remove-Item file` |
| Проверка файла | `wsl test -f file` | `Test-Path file` |
| Сетевые проверки | `wsl ping host` | `Test-Connection host` |
| Переменные окружения | `wsl echo $PATH` | `$env:PATH` |
| Python | `wsl python script.py` | `python script.py` |
| Curl | `wsl curl url` | `Invoke-WebRequest url` |

### ⚠️ Используй WSL только когда необходимо:

| Задача | Причина |
|--------|---------|
| `wsl ssh host` | SSH клиент в Windows может не быть настроен |
| `wsl bash script.sh` | Bash скрипты требуют Linux окружение |
| `wsl grep pattern file` | Нет прямого аналога в PowerShell |
| `wsl sed 's/old/new/' file` | Нет прямого аналога в PowerShell |
| `wsl awk '{print $1}' file` | Нет прямого аналога в PowerShell |
| `wsl make` | Makefile требует Linux окружение |

## Контекст проекта

### Обзор проекта

**openwrt-captive-monitor** - легковесный сервис для автоматического обнаружения и обработки captive порталов на маршрутизаторах OpenWrt.

### Ключевые компоненты

- **Основной скрипт**: `openwrt_captive_monitor.sh` - bash скрипт для обнаружения и обработки captive порталов
- **Пакет OpenWrt**: `package/openwrt-captive-monitor/` - структура пакета для OpenWrt
- **Docker SDK**: `docker/sdk/` - Docker образы для сборки пакетов через OpenWrt SDK
- **CI/CD**: `.github/workflows/` - автоматизированная сборка, тестирование и релизы

### Поддерживаемые версии OpenWrt

- 21.02 (LTS) - iptables backend
- 22.03 (LTS) - автоопределение backend
- 23.05 (Stable) - полная поддержка nftables
- 24.10 (Development)

### Поддерживаемые архитектуры

- mips_24kc (основная для роутеров)
- aarch64_cortex-a53
- x86_64
- all (универсальный пакет)## Да
тированное авто-версионирование

### Формат версии

```
vYYYY.M.D.N
```

**Компоненты:**
- `YYYY` - год (4 цифры)
- `M` - месяц (1-12, **без ведущих нулей**)
- `D` - день (1-31, **без ведущих нулей**)
- `N` - порядковый номер релиза за день (начинается с 1)

**Примеры:**
- `v2025.1.15.1` - первый релиз 15 января 2025
- `v2025.1.15.2` - второй релиз того же дня
- `v2025.12.3.1` - первый релиз 3 декабря 2025

### Workflow auto-version-tag.yml

**Триггер:** Push в main

**Процесс:**
1. Получить все существующие теги
2. Найти теги за текущую дату (`vYYYY.M.D.*`)
3. Определить следующий порядковый номер `N`
4. Обновить метаданные:
   - `VERSION` = `YYYY.M.D.N` (без `v`)
   - `PKG_VERSION` = `YYYY.M.D.N`
   - `PKG_RELEASE` = `1`
5. Создать коммит с обновлением метаданных
6. Создать тег `vYYYY.M.D.N` на этом коммите
7. Создать GitHub Release с changelog
8. Запустить `tag-build-release.yml`

### Conventional Commits

Типы коммитов:
- `feat:` - новая функциональность
- `fix:` - исправление ошибки
- `docs:` - изменения в документации
- `ci:` - изменения в CI/CD
- `refactor:` - рефакторинг кода
- `test:` - добавление/изменение тестов
- `chore:` - рутинные задачи
- `perf:` - улучшение производительности
- `style:` - форматирование кода

## Git Workflow

### Основной процесс

1. **Always work in feature branches** - never commit directly to main
2. **Create a new branch** for each feature or fix
3. **Make commits** with clear, descriptive messages in English
4. **Create Pull Request (PR)** for code review
5. **Check GitHub Actions** after PR creation
6. **Merge to main** (only after actions pass)
7. **Check GitHub Actions** after merge to main
8. **Delete feature branch** after successful merge

### Детальный workflow

```powershell
# 1. Создать feature branch
git checkout -b feature/my-feature

# 2. Сделать изменения и коммиты
git add .
git commit -m "feat: add new feature"

# 3. Push ветки
git push origin feature/my-feature

# 4. Создать PR
gh pr create --title "feat: add new feature" --body "Description"

# 5. Проверить статус Actions
gh run list --branch feature/my-feature --limit 5

# 6. Если Actions упали - исправить
git add .
git commit -m "fix: resolve CI issues"
git push

# 7. Когда Actions прошли - мержить
gh pr merge --squash

# 8. Проверить статус Actions на main
gh run list --branch main --limit 5

# 9. Если Actions на main прошли - удалить ветку
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```## Doc
ker паттерны

### Оптимизация размера Docker образов

**Целевые метрики:**
- Максимальный размер образа: 2GB (2147483648 bytes)
- Типичный размер после оптимизации: ~1.5GB
- Экономия от оптимизации: ~40%

### Multi-stage builds

```dockerfile
# Stage 1: Downloader - загрузка и распаковка
FROM ubuntu:24.04 AS sdk-downloader

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        xz-utils && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY docker/sdk/download-sdk.sh /tmp/
RUN bash /tmp/download-sdk.sh && \
    rm -f /tmp/download-sdk.sh

# Stage 2: Final - финальный образ
FROM ubuntu:24.04 AS final

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libncurses-dev \
        python3 \
        git && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=sdk-downloader /opt/openwrt-sdk /opt/openwrt-sdk

RUN useradd -m -u 1000 builder && \
    chown -R builder:builder /opt/openwrt-sdk

USER builder
WORKDIR /opt/openwrt-sdk
```

### Правила оптимизации

**Объединение RUN команд:**
```dockerfile
# ✅ Хорошо - один слой с очисткой
RUN apt-get update && \
    apt-get install -y --no-install-recommends pkg1 pkg2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

**Использование --no-install-recommends:**
```dockerfile
RUN apt-get install -y --no-install-recommends \
    build-essential \
    libncurses-dev \
    python3
```

**Удаление архивов после распаковки:**
```dockerfile
RUN tar -C /opt/openwrt-sdk --strip-components=1 -xf sdk.tar.xz && \
    rm -f sdk.tar.xz sha256sums
```

### Проверка размера образа

```powershell
# Получить размер в байтах
$imageSize = docker inspect "$IMAGE" --format='{{.Size}}'
$maxSize = 2 * 1024 * 1024 * 1024  # 2GB

if ($imageSize -gt $maxSize) {
    Write-Host "ERROR: Image size exceeds 2GB limit" -ForegroundColor Red
    Write-Host "Actual: $([math]::Round($imageSize/1GB, 2))GB"
    exit 1
}

Write-Host "✅ Image size: $([math]::Round($imageSize/1GB, 2))GB"
```

### Параллельная сборка Docker образов

```powershell
# Список архитектур
$architectures = @(
    @{target="x86"; subtarget="64"},
    @{target="ath79"; subtarget="generic"},
    @{target="ramips"; subtarget="mt76x8"}
)

# Запуск параллельных сборок через controlPwshProcess
foreach ($arch in $architectures) {
    $target = $arch.target
    $subtarget = $arch.subtarget

    Write-Host "Starting build for $target-$subtarget"

    # Запуск через Kiro controlPwshProcess
    kiro controlPwshProcess --action start `
        --command "docker build --build-arg SDK_TARGET=$target --build-arg SDK_SUBTARGET=$subtarget -t sdk:$target-$subtarget ." `
        --path "docker/sdk"
}
```##
 GitHub Actions паттерны

### Concurrency в GitHub Actions

```yaml
# Базовый формат
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true|false
```

**Правила выбора cancel-in-progress:**

**cancel-in-progress: true** - использовать когда:
- Workflow запускается часто (при каждом коммите в PR)
- Результаты предыдущего запуска становятся неактуальными
- Workflow выполняется быстро (< 10 минут)

**cancel-in-progress: false** - использовать когда:
- Workflow создает критичные артефакты (релизы, Docker образы)
- Workflow выполняется долго (> 10 минут)
- Workflow запускается по тегам или schedule

### Работа с GitHub CLI

**Всегда указывай --ref при запуске:**

```powershell
# Запустить workflow на текущей ветке
gh workflow run "Build SDK Images" --ref $(git branch --show-current)

# Запустить с параметрами
gh workflow run "OpenWrt Build" --ref feature/my-feature -f openwrt_version=23.05.5

# Мониторинг workflow
gh run list --limit 10
gh run list --branch feature/my-feature --limit 5
gh run list --status in_progress

# Просмотр логов
gh run view --log
gh run view 12345678 --log

# Отмена workflow
gh run cancel 12345678
```

### Matrix builds

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

### Timeout и retry

```yaml
jobs:
  build:
    runs-on: ubuntu-24.04
    timeout-minutes: 30  # Job будет отменен через 30 минут
    steps:
      - name: Download SDK
        timeout-minutes: 10  # Step будет отменен через 10 минут
        run: |
          bash docker/sdk/download-sdk.sh
```

## Bash скрипты паттерны

### Обязательные флаги безопасности

**Всегда начинай bash скрипты с:**

```bash
#!/bin/bash
set -euo pipefail
```

**Что делают флаги:**
- `set -e` - завершить скрипт при любой ошибке (exit code != 0)
- `set -u` - ошибка при использовании неопределенных переменных
- `set -o pipefail` - ошибка в любой части pipeline

### Валидация входных параметров

```bash
#!/bin/bash
set -euo pipefail

# Проверка наличия параметров
if [ $# -lt 2 ]; then
    echo "Usage: $0 <target> <subtarget>"
    exit 1
fi

TARGET=$1
SUBTARGET=$2

# Проверка значений
if [ -z "$TARGET" ] || [ -z "$SUBTARGET" ]; then
    echo "ERROR: Target and subtarget cannot be empty"
    exit 1
fi

# Проверка переменных окружения
: "${OPENWRT_VERSION:?ERROR: OPENWRT_VERSION is not set}"
: "${SDK_TARGET:?ERROR: SDK_TARGET is not set}"
```###
 Обработка ошибок и cleanup

```bash
#!/bin/bash
set -euo pipefail

# Временные файлы
TEMP_DIR=$(mktemp -d)

# Cleanup функция
cleanup() {
    local exit_code=$?
    echo "Cleaning up..."
    rm -rf "$TEMP_DIR"
    exit $exit_code
}

# Вызвать cleanup при выходе
trap cleanup EXIT INT TERM

# Функции для логирования
error() {
    echo "ERROR: $*" >&2
    exit 1
}

warn() {
    echo "WARNING: $*" >&2
}

info() {
    echo "INFO: $*"
}

# Использование
[ -f "$CONFIG_FILE" ] || error "Config file not found: $CONFIG_FILE"
[ -d "$SDK_DIR" ] || warn "SDK directory does not exist: $SDK_DIR"
info "Starting build process..."
```

### Retry логика для сетевых операций

```bash
retry_with_backoff() {
    local max_retries=15
    local retry_count=0
    local wait_time=1

    while [ $retry_count -lt $max_retries ]; do
        if "$@"; then
            return 0
        fi

        retry_count=$((retry_count + 1))
        wait_time=$((2 ** retry_count))
        [ $wait_time -gt 60 ] && wait_time=60  # Max 60 секунд

        echo "Retry $retry_count/$max_retries after ${wait_time}s..."
        sleep $wait_time
    done

    echo "ERROR: Failed after $max_retries attempts"
    return 1
}

# Использование
retry_with_backoff curl -fsSL "$URL" -o "$OUTPUT"
```

### Curl опции для надежной загрузки

```bash
curl \
  -f \                      # Fail on HTTP errors (4xx, 5xx)
  -s \                      # Silent mode (no progress bar)
  -S \                      # Show errors even in silent mode
  -L \                      # Follow redirects
  --retry 15 \              # Retry up to 15 times
  --retry-delay 10 \        # Wait 10s between retries
  --retry-all-errors \      # Retry on all errors, not just transient
  --max-time 3600 \         # Maximum time for operation (1 hour)
  --connect-timeout 60 \    # Connection timeout (60s)
  --speed-limit 1000 \      # Minimum speed (1KB/s)
  --speed-time 30 \         # Time to maintain minimum speed (30s)
  -C - \                    # Continue interrupted download
  -o "$output" \            # Output file
  "$url"
```

## Troubleshooting паттерны

### Общий подход к troubleshooting

1. **Сбор информации** - логи, error messages, контекст
2. **Воспроизведение** - можно ли воспроизвести проблему локально?
3. **Изоляция** - какой компонент вызывает проблему?
4. **Анализ** - что является root cause?
5. **Решение** - минимальное изменение для исправления
6. **Валидация** - проверка, что проблема решена
7. **Документация** - обновление docs/troubleshooting

### Команды, требующие интерактивного ввода

**Проблемные команды:**
```bash
git show <commit>           # Открывает less
git log                     # Открывает less
git diff                    # Открывает less
git commit                  # Открывает vim/nano
docker exec -it container bash    # Интерактивный терминал
ssh user@host               # Может спросить пароль
```

**Решения:**
```bash
# Git команды - использовать --no-pager
git --no-pager show 9724d68
git --no-pager log --oneline
git --no-pager diff HEAD~1

# Или установить переменную окружения
export GIT_PAGER=cat

# Git commit - использовать -m для сообщения
git commit -m "commit message"

# Docker - использовать неинтерактивный режим
docker exec container bash -c "ls -la"  # Без -it

# SSH - использовать ключи или флаги
ssh -o BatchMode=yes user@host
```#
## Универсальное решение для скриптов

**Добавь в начало каждого bash скрипта:**
```bash
#!/bin/bash
set -euo pipefail

# Отключить все интерактивные режимы
export GIT_PAGER=cat
export PAGER=cat
export SYSTEMD_PAGER=cat
export EDITOR=cat
export VISUAL=cat
export DEBIAN_FRONTEND=noninteractive

# Теперь все команды работают неинтерактивно
```

### Глобальное решение для зависающих команд

**Всегда используй timeout в executePwsh:**

```typescript
// ✅ Хорошо - прервется через 30 секунд
executePwsh({
  command: "wsl bash scripts/some-script.sh",
  timeout: 30000  // 30 секунд
})

// ✅ Еще лучше - с отключением пейджера
executePwsh({
  command: "wsl bash -c 'export GIT_PAGER=cat; bash scripts/some-script.sh'",
  timeout: 30000
})
```

### Типичные проблемы и решения

**1. Docker образ превышает 2GB**
- Объединить RUN команды для уменьшения слоев
- Очистка кэшей apt в том же слое
- Использование multi-stage builds
- Правильный .dockerignore

**2. GitHub Actions workflow timeout**
- Добавить timeout на job и step уровне
- Использовать кэширование
- Использовать предсобранные Docker образы

**3. Проблемы с путями на Windows**
```powershell
# ✅ PowerShell - используй ${PWD}
docker run -v ${PWD}:/workspace image

# Для путей с пробелами
docker run -v "${PWD}:/workspace" image
```

**4. Версия в пакете не совпадает с VERSION файлом**
```bash
# Использовать скрипт обновления версии
bash scripts/update-version-metadata.sh

# Или вручную синхронизировать
VERSION=$(cat VERSION)
sed -i "s/^PKG_VERSION:=.*/PKG_VERSION:=${VERSION}/" package/openwrt-captive-monitor/Makefile
```

## Тестирование паттерны

### Property-Based Testing (PBT)

**Когда использовать PBT:**
- Парсеры и сериализаторы (round-trip properties)
- Конфигурационные файлы (YAML, JSON)
- Математические функции (коммутативность, ассоциативность)
- Инварианты системы (размер образа, формат версии)

### Три типа тестов

**1. Unit тесты**
- Тестируют отдельные функции/компоненты
- Быстрые (< 1 секунды)
- Изолированные (без внешних зависимостей)

**2. Property-Based тесты**
- Проверяют универсальные свойства
- Минимум 100 итераций
- Автоматическая генерация входных данных

**3. Integration тесты**
- Тестируют полный цикл работы
- Медленные (минуты)
- Используют реальные зависимости

### Act - локальное тестирование GitHub Actions

```powershell
# Список всех workflow
act --list

# Dry-run конкретного workflow
act -W .github/workflows/ci.yml --job lint -n

# Запуск workflow локально
act -W .github/workflows/ci.yml --job lint

# Интерактивный режим для отладки
act -W .github/workflows/ci.yml --job lint --interactive --verbose
```## Спец
ификации паттерны

### Структура спецификаций

Каждая спецификация находится в `.kiro/specs/{feature-name}/` и содержит:
- `requirements.md` - требования в формате EARS с acceptance criteria
- `design.md` - детальный дизайн с correctness properties
- `tasks.md` - список задач для имплементации

### Формат требований (EARS)

Все требования должны следовать одному из EARS паттернов:
- **Ubiquitous**: THE {system} SHALL {response}
- **Event-driven**: WHEN {trigger}, THE {system} SHALL {response}
- **State-driven**: WHILE {condition}, THE {system} SHALL {response}
- **Unwanted event**: IF {condition}, THEN THE {system} SHALL {response}
- **Optional feature**: WHERE {option}, THE {system} SHALL {response}

### Correctness Properties

Каждое свойство корректности должно:
- Начинаться с "For any" (универсальная квантификация)
- Быть тестируемым через Property-Based Testing
- Ссылаться на конкретный acceptance criteria из requirements
- Использовать формат: **Validates: Requirements X.Y**

**Пример:**
```
Property 1: Image size compliance
*For any* built Docker image, the size should be less than 2GB (2147483648 bytes)
**Validates: Requirements 2.1**
```

## Тестовое окружение

### OpenWrt Test Environment

**Хост:** `root@192.168.35.127`
**Доступ:** SSH по ключу (без пароля)
**Назначение:** Тестирование пакетов OpenWrt, интеграционные тесты

**Характеристики системы:**
```
Дистрибутив: OpenWrt 23.05.3 r23809-234f1a2efa
Архитектура: x86/64 (x86_64)
Ядро: Linux 5.15.150 #0 SMP
Память: 209 MB RAM (112 MB доступно)
Диск: 2.0 GB (1.1 GB свободно)
```

### OpenWrt Production Environment

**Хост:** `root@192.168.35.1`
**Доступ:** SSH по ключу (без пароля)
**Назначение:** Продакшен среда, финальное тестирование перед релизом, проверка в реальных условиях

**⚠️ ВНИМАНИЕ:** Это продакшен роутер! Будь осторожен с изменениями.

### Подключение к тестовым средам

**Test Environment (192.168.35.127):**
```powershell
# Простое подключение
wsl ssh root@192.168.35.127

# Выполнить команду
wsl ssh root@192.168.35.127 "uname -a"

# Проверка доступности
Test-Connection -ComputerName 192.168.35.127 -Count 2
```

**Production Environment (192.168.35.1):**
```powershell
# Простое подключение
wsl ssh root@192.168.35.1

# Выполнить команду
wsl ssh root@192.168.35.1 "uname -a"

# Проверка доступности
Test-Connection -ComputerName 192.168.35.1 -Count 2
```

### Типичные сценарии тестирования

**1. Установка и тестирование пакета**
```bash
# Скопировать пакет на роутер
scp dist/openwrt-captive-monitor_*.ipk root@192.168.35.127:/tmp/

# Подключиться к роутеру и установить
ssh root@192.168.35.127 "
  opkg install /tmp/openwrt-captive-monitor_*.ipk &&
  /etc/init.d/captive-monitor start &&
  /etc/init.d/captive-monitor status
"
```

**2. Автоматизация тестирования**
```bash
#!/bin/bash
# test-on-openwrt.sh

set -euo pipefail

ROUTER_IP="192.168.35.127"
PACKAGE_FILE=$1

echo "=== Testing package on OpenWrt ==="
scp "$PACKAGE_FILE" root@$ROUTER_IP:/tmp/
ssh root@$ROUTER_IP "opkg install /tmp/$(basename $PACKAGE_FILE)"
ssh root@$ROUTER_IP "/etc/init.d/captive-monitor start"
ssh root@$ROUTER_IP "logread | grep captive-monitor | tail -10"
echo "✅ Test completed successfully"
```

## Remote-SSH Setup

### SSH Config файлы

**Windows:** `C:\Users\Администратор\.ssh\config`
**WSL:** `~/.ssh/config`

### Настроенные хосты

```
Host openwrt-test
    HostName 192.168.35.127
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Использование в Kiro

**Подключение через Remote-SSH:**
1. Открыть Command Palette (Ctrl+Shift+P)
2. Выбрать "Remote-SSH: Connect to Host..."
3. Выбрать "openwrt-test"

**Быстрое подключение:**
```bash
wsl ssh openwrt-test
```#
# Часто используемые команды

### Git операции

```powershell
# Создать новую feature ветку
git checkout -b feature/feature-name

# Обновить ветку из main
git fetch origin
git rebase origin/main

# Staged commit с conventional commit message
git add .
git commit -m "feat: add new feature"
git commit -m "fix: resolve issue with docker build"

# Push ветки и создать PR
git push origin feature/feature-name
gh pr create --title "Feature: Description" --body "Details"

# Проверить статус PR и мержить
gh pr status
gh pr merge --squash  # только после одобрения пользователя!
```

### Docker операции

```powershell
# Сборка Docker SDK образа
docker build `
  --build-arg OPENWRT_VERSION=23.05.5 `
  --build-arg SDK_TARGET=x86 `
  --build-arg SDK_SUBTARGET=64 `
  -t openwrt-sdk:local `
  -f docker/sdk/Dockerfile `
  .

# Проверка образов
docker images
docker inspect openwrt-sdk:local --format='{{.Size}}'
docker run --rm openwrt-sdk:local ls -la /opt/openwrt-sdk

# Очистка
docker system prune -a
docker rmi openwrt-sdk:local
```

### GitHub Actions

```powershell
# Список workflows и запуск
gh workflow list
gh workflow run "Build SDK Images" --ref $(git branch --show-current)

# Мониторинг
gh run list --limit 5
gh run view 12345678 --log

# Отмена старых запусков
gh run list --status in_progress --branch $(git branch --show-current) --json databaseId --jq '.[].databaseId' | ForEach-Object { gh run cancel $_ }
```

### Валидация и тестирование

```bash
# Проверить bash скрипты (требует WSL)
wsl shellcheck openwrt_captive_monitor.sh
wsl shfmt -i 2 -ci -sr -w openwrt_captive_monitor.sh

# Unit тесты
wsl bash tests/run.sh

# Валидация Docker образа
wsl bash scripts/validate-docker-image-size.sh openwrt-sdk:local
```

### Диагностика проблем

```powershell
# Docker проблемы
docker info
docker system df

# GitHub Actions проблемы
gh run list --status failure --limit 1 --json databaseId --jq '.[0].databaseId' | ForEach-Object { gh run view $_ --log > failed_job_log.txt }

# OpenWrt SDK проблемы
Invoke-WebRequest -Method Head -Uri "https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/"
```

### Полезные алиасы для PowerShell

```powershell
# Добавь в $PROFILE:

# Git алиасы
function gst { git status }
function gco { param($branch) git checkout $branch }
function gcb { param($branch) git checkout -b $branch }
function gp { git push origin $(git branch --show-current) }

# Docker алиасы
function dps { docker ps }
function di { docker images }
function dclean { docker system prune -a -f }

# GitHub CLI алиасы
function ghw { gh workflow list }
function ghr { gh run list --limit 10 }
function ghp { gh pr status }

# Act алиасы
function act-list { act --list }
function act-lint { act -W .github/workflows/ci.yml --job lint }
function act-debug { param($workflow, $job) act -W $workflow --job $job --interactive --verbose }
```

## Быстрые проверки

### Проверка окружения

```powershell
# Версии инструментов
git --version
docker --version
gh --version
python --version

# Проверка Docker
docker run --rm hello-world

# Проверка WSL (когда необходимо)
wsl uname -a
wsl bash --version
```

### Проверка проекта

```powershell
# Структура проекта
Get-ChildItem .kiro\specs

# Текущая версия и статус
Get-Content VERSION
git log -1 --oneline
git branch --show-current

# Статус CI
gh run list --limit 5
```

## Чеклист для troubleshooting

Когда сталкиваешься с проблемой:

1. ✅ Собрал все логи и error messages
2. ✅ Попытался воспроизвести локально
3. ✅ Изолировал проблемный компонент
4. ✅ Проверил документацию и существующие issues
5. ✅ Создал минимальный воспроизводимый пример
6. ✅ Определил root cause
7. ✅ Реализовал минимальное исправление
8. ✅ Добавил тесты для предотвращения регрессии
9. ✅ Обновил документацию

## Когда обращаться к пользователю

Обращайся к пользователю когда:

1. **Неоднозначность** - несколько возможных решений, нужен выбор
2. **Критическое изменение** - изменение может повлиять на другие компоненты
3. **Недостаточно информации** - нужны дополнительные детали
4. **Нестандартная ситуация** - проблема выходит за рамки обычных паттернов
5. **Требуется подтверждение** - перед merge в main или созданием release

**Не обращайся к пользователю** для:
- Стандартных исправлений с очевидным решением
- Рутинных задач (форматирование, линтинг)
- Промежуточных шагов в процессе решения
- Вопросов, на которые можно найти ответ в документации
## G
it History Cleanup

### git-filter-repo

**Назначение:** Переписывание истории Git для удаления секретов, больших файлов или проблемных путей.

**Установка:**
```powershell
# Windows
pip install git-filter-repo

# WSL/Linux
pip3 install git-filter-repo
```

**Проверка установки:**
```powershell
# Windows
python -m git_filter_repo --version

# WSL
wsl python3 -m git_filter_repo --version
```

### Использование git-filter-repo

**⚠️ ВНИМАНИЕ:** git-filter-repo переписывает историю Git. Это необратимая операция!

**Перед использованием:**
1. Создать backup репозитория
2. Убедиться что все изменения закоммичены
3. Уведомить команду о предстоящем rebase

### Проблемы с Windows и невалидными путями

**Проблема:** Windows не поддерживает файлы с некоторыми спецсимволами в путях:
- Запятые в начале имени: `, 1):`
- Кавычки в имени: `"sarif_file: results\")"`
- Другие спецсимволы: `<>:|?*`

**Симптомы:**
```
fatal: invalid path ', 1):'
OSError: [Errno 22] Invalid argument
```

**Решение:** Использовать WSL для работы с такими файлами:

```powershell
# 1. Клонировать репозиторий в WSL
wsl bash -c "cd /tmp && git clone https://github.com/user/repo.git repo-clean"

# 2. Найти проблемные файлы
wsl bash -c 'cd /tmp/repo-clean && git log --all --name-only --pretty=format: | sort -u | grep -E "(^,|\")" > /tmp/paths-to-remove.txt'

# 3. Удалить проблемные файлы из истории
wsl bash -c 'cd /tmp/repo-clean && git remote remove origin && python3 -m git_filter_repo --invert-paths --paths-from-file /tmp/paths-to-remove.txt --force'

# 4. Создать файл с секретами для замены
wsl bash -c "cat > /tmp/replace-secrets.txt << 'EOF'
SECRET_KEY_1==>REDACTED
SECRET_KEY_2==>REDACTED
EOF"

# 5. Заменить секреты в истории
wsl bash -c 'cd /tmp/repo-clean && python3 -m git_filter_repo --replace-text /tmp/replace-secrets.txt --force'

# 6. Скопировать обратно в Windows
wsl bash -c "cd /tmp && tar -czf repo-clean.tar.gz repo-clean"
wsl bash -c "cp /tmp/repo-clean.tar.gz /mnt/c/git/"
cd C:\git
tar -xzf repo-clean.tar.gz

# 7. Push из Windows
cd repo-clean
git remote add origin https://github.com/user/repo.git
git push origin --force --all
git push origin --force --tags

# 8. Заменить основной репозиторий
cd C:\git
Remove-Item openwrt-captive-monitor -Recurse -Force
Rename-Item repo-clean openwrt-captive-monitor

# 9. Очистить WSL
wsl bash -c "rm -rf /tmp/repo-clean /tmp/replace-secrets.txt /tmp/paths-to-remove.txt /tmp/repo-clean.tar.gz"
```

### Проверка результатов

**Проверить что секреты удалены:**
```bash
# Поиск секрета в истории
git log --all -S "SECRET_KEY" --oneline
# Должно быть пусто

# Поиск в содержимом всех коммитов
git rev-list --all | xargs git grep "SECRET_KEY"
# Должно быть пусто
```

**Проверить что файлы удалены:**
```bash
# Список всех файлов в истории
git log --all --name-only --pretty=format: | sort -u | grep "problematic-file"
# Должно быть пусто
```

### После force push

**Команда должна:**
1. Переклонировать репозиторий
2. Обновить все локальные ветки
3. Проверить что CI/CD работает

**Уведомление команды:**
```
⚠️ История Git была переписана для удаления секретов/проблемных файлов.

Действия:
1. Удалите старый клон: rm -rf old-repo
2. Клонируйте заново: git clone https://github.com/user/repo.git
3. Проверьте что все работает

Изменения:
- Хеши всех коммитов изменились
- Старые ссылки на коммиты недействительны
- Теги обновлены
```

### Best Practices

1. **Всегда создавай backup** перед переписыванием истории
2. **Используй WSL** для работы с проблемными путями на Windows
3. **Проверяй результат** перед force push
4. **Уведоми команду** о предстоящем rebase
5. **Отзови секреты** даже после удаления из истории
6. **Обнови .gitignore** чтобы предотвратить повторное добавление
7. **Проверь CI/CD** после force push
8. **Организуй бакапы** в отдельную папку (например `C:\git\backups\`)

### Troubleshooting

**Ошибка: "Refusing to destructively overwrite repo history"**
```bash
# Решение: добавить --force
python3 -m git_filter_repo --replace-text secrets.txt --force
```

**Ошибка: "fatal: invalid path"**
```bash
# Решение: использовать WSL
wsl python3 -m git_filter_repo --invert-paths --paths-from-file paths.txt --force
```

**Ошибка: "OSError: [Errno 22] Invalid argument"**
```bash
# Решение: в истории есть файлы с невалидными путями для Windows
# Используй WSL для очистки (см. раздел выше)
```

**Папка не удаляется на Windows:**
```powershell
# Проверить текущую директорию
Get-Location

# Если находишься в удаляемой папке - выйти
Set-Location C:\git

# Удалить через robocopy
New-Item -ItemType Directory -Path C:\git\empty -Force | Out-Null
robocopy C:\git\empty C:\git\old-repo /MIR /R:0 /W:0
Remove-Item C:\git\old-repo -Force
Remove-Item C:\git\empty -Force
```
