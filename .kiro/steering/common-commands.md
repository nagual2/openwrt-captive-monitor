# Часто используемые команды

## Git операции

### Работа с ветками

```powershell
# Создать новую feature ветку
git checkout -b feature/feature-name

# Обновить ветку из main
git fetch origin
git rebase origin/main

# Проверить статус
git status

# Посмотреть diff
git diff
git diff --staged
```

### Коммиты

```powershell
# Staged commit с conventional commit message
git add .
git commit -m "feat: add new feature"
git commit -m "fix: resolve issue with docker build"
git commit -m "docs: update README"
git commit -m "ci: optimize workflow"

# Amend последнего коммита
git commit --amend --no-edit
```

### Push и PR

```powershell
# Push ветки
git push origin feature/feature-name

# Создать PR через GitHub CLI
gh pr create --title "Feature: Description" --body "Details"

# Проверить статус PR
gh pr status

# Merge PR (только после одобрения пользователя!)
gh pr merge --squash
```

## Docker операции

### Локальная сборка образов

```powershell
# Сборка Docker SDK образа
cd docker/sdk
bash build-local.sh --target x86 --subtarget 64 --version 23.05.5

# Или напрямую через docker build
docker build `
  --build-arg OPENWRT_VERSION=23.05.5 `
  --build-arg SDK_TARGET=x86 `
  --build-arg SDK_SUBTARGET=64 `
  -t openwrt-sdk:local `
  -f Dockerfile `
  .
```

### Проверка образов

```powershell
# Список образов
docker images

# Проверить размер образа
docker inspect openwrt-sdk:local --format='{{.Size}}'

# Запустить контейнер для проверки
docker run -it --rm openwrt-sdk:local /bin/bash

# Проверить содержимое
docker run --rm openwrt-sdk:local ls -la /opt/openwrt-sdk
docker run --rm openwrt-sdk:local make --version
```

### Очистка

```powershell
# Удалить неиспользуемые образы
docker system prune -a

# Удалить конкретный образ
docker rmi openwrt-sdk:local

# Очистить build cache
docker builder prune -a
```

## OpenWrt пакеты

### Локальная сборка пакета

```bash
# Простая сборка (architecture-independent)
bash scripts/build_ipk.sh --arch all

# Сборка для конкретной архитектуры через SDK
# (требует предварительно загруженный SDK)
cd openwrt-sdk-*/
cp -r ../package/openwrt-captive-monitor package/
make package/openwrt-captive-monitor/compile V=s
```

### Проверка пакета

```bash
# Посмотреть содержимое IPK
tar -tzf openwrt-captive-monitor_*.ipk

# Извлечь и проверить control файл
tar -xzf openwrt-captive-monitor_*.ipk
tar -xzf control.tar.gz
cat control

# Проверить data файлы
tar -xzf data.tar.gz
ls -la
```

### Установка и тестирование

```bash
# Скопировать на роутер
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/

# Установить на роутере
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"

# Проверить установку
ssh root@192.168.1.1 "opkg list-installed | grep captive"

# Проверить файлы
ssh root@192.168.1.1 "ls -la /usr/sbin/openwrt_captive_monitor"

# Запустить сервис
ssh root@192.168.1.1 "/etc/init.d/captive-monitor start"

# Проверить логи
ssh root@192.168.1.1 "logread | grep captive-monitor"
```

## GitHub Actions

### Запуск workflow

```powershell
# Список workflows
gh workflow list

# Запустить workflow на текущей ветке
gh workflow run "Build SDK Images" --ref $(git branch --show-current)

# Запустить с параметрами
gh workflow run "OpenWrt Build" --ref feature/my-feature -f openwrt_version=23.05.5

# Посмотреть статус последних запусков
gh run list --limit 5

# Посмотреть логи конкретного запуска
gh run view 12345678 --log
```

### Отмена старых запусков

```powershell
# Отменить все запущенные workflow для текущей ветки
gh run list --status in_progress --branch $(git branch --show-current) --json databaseId --jq '.[].databaseId' | ForEach-Object { gh run cancel $_ }
```

### Проверка артефактов

```powershell
# Список артефактов последнего запуска
gh run list --limit 1 --json databaseId --jq '.[0].databaseId' | ForEach-Object { gh run view $_ --json artifacts }

# Скачать артефакты
gh run download 12345678
```

## Валидация и тестирование

### Shellcheck и форматирование

```bash
# Проверить bash скрипты
wsl shellcheck openwrt_captive_monitor.sh
wsl shellcheck scripts/*.sh

# Форматирование
wsl shfmt -i 2 -ci -sr -w openwrt_captive_monitor.sh
```

### Запуск тестов

```bash
# Unit тесты
wsl bash tests/run.sh

# VM тесты (требует QEMU/KVM)
wsl bash scripts/run_openwrt_vm.sh

# Валидация Docker образа
wsl bash scripts/validate-docker-image-size.sh openwrt-sdk:local
wsl bash scripts/validate-docker-image-contents.sh openwrt-sdk:local
```

### Валидация документации

```bash
# Проверить markdown файлы
wsl bash scripts/validate-docs.sh

# Проверить ссылки в README
wsl grep -o 'http[s]*://[^)]*' README.md | sort -u
```

## Диагностика проблем

### Docker проблемы

```powershell
# Проверить Docker daemon
docker info

# Проверить WSL интеграцию
wsl docker ps

# Проверить логи Docker Desktop
# Открыть: C:\Users\<User>\AppData\Local\Docker\log.txt

# Проверить disk usage
docker system df
```

### GitHub Actions проблемы

```powershell
# Скачать логи failed job
gh run list --status failure --limit 1 --json databaseId --jq '.[0].databaseId' | ForEach-Object { gh run view $_ --log > failed_job_log.txt }

# Анализ логов с помощью Python скриптов
python analyze_failed_job.py
python find_make_error.py
```

### OpenWrt SDK проблемы

```bash
# Проверить доступность SDK на сервере
curl -I https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/

# Проверить контрольную сумму
curl -fsSL https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/sha256sums | grep sdk

# Тест загрузки SDK
curl -fsSL -o /tmp/test.tar.xz https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/openwrt-sdk-23.05.5-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

## Работа со спецификациями

### Создание новой спецификации

```powershell
# Создать директорию для спецификации
mkdir .kiro/specs/feature-name

# Kiro автоматически создаст requirements.md при запросе
# Просто скажи: "Создай спецификацию для [описание фичи]"
```

### Выполнение задач из спецификации

```powershell
# Открыть tasks.md в редакторе
# Нажать "Start task" рядом с задачей
# Или попросить: "Выполни задачу 1.1 из спецификации feature-name"
```

### Проверка coverage свойств

```powershell
# Kiro может проанализировать coverage
# Попроси: "Проверь property coverage для спецификации feature-name"
```

## Полезные алиасы для PowerShell

Добавь в `$PROFILE`:

```powershell
# Git алиасы
function gst { git status }
function gco { param($branch) git checkout $branch }
function gcb { param($branch) git checkout -b $branch }
function gp { git push origin $(git branch --show-current) }
function gl { git log --oneline --graph --decorate -10 }

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
function act-dry { param($workflow, $job) act -W $workflow --job $job -n }
function act-run { param($workflow, $job) act -W $workflow --job $job }
function act-lint { act -W .github/workflows/ci.yml --job lint }
function act-test { act -W .github/workflows/act-test.yml --job test }
function act-debug { param($workflow, $job) act -W $workflow --job $job --interactive --verbose }

# WSL алиасы
function wslbash { param($script) wsl bash $script }
```

## Act (локальное тестирование GitHub Actions)

### Основные команды act

```powershell
# Список всех workflow
act --list

# Dry-run конкретного workflow
act -W .github/workflows/ci.yml --job lint -n

# Запуск workflow локально
act -W .github/workflows/ci.yml --job lint

# Тестовый workflow (простой, без внешних зависимостей)
act -W .github/workflows/act-test.yml --job test

# Запуск с конкретным matrix параметром
act -W .github/workflows/ci.yml --job lint --matrix linter:shellcheck

# Интерактивный режим для отладки
act -W .github/workflows/ci.yml --job lint --interactive
```

### Полезные опции act

```powershell
# Без загрузки образов (использовать локальные)
act --pull=false

# Переиспользовать контейнеры
act --reuse

# Тихий режим (только ошибки)
act --quiet

# Максимальная детализация
act --verbose

# С переменными окружения
act --env-file .env.local

# С секретами
act --secret-file .secrets
```

### Типичные сценарии использования act

```powershell
# Быстрое тестирование изменений в workflow
act -W .github/workflows/ci.yml --job lint -n  # dry-run
act -W .github/workflows/ci.yml --job lint     # реальный запуск

# Отладка проблемного job
act -W .github/workflows/ci.yml --job lint --interactive --verbose

# Тестирование всех линтеров
act -W .github/workflows/ci.yml --job lint

# Тестирование конкретного линтера
act -W .github/workflows/ci.yml --job lint --matrix linter:yamllint
```

## Быстрые проверки

### Проверка окружения

```powershell
# Версии инструментов
git --version
docker --version
gh --version
wsl --version
python --version

# Проверка WSL
wsl uname -a
wsl bash --version

# Проверка Docker
docker run --rm hello-world
```

### Проверка проекта

```powershell
# Структура проекта
tree /F .kiro\specs

# Текущая версия
type VERSION

# Последний коммит
git log -1 --oneline

# Текущая ветка
git branch --show-current

# Статус CI
gh run list --limit 5
```
