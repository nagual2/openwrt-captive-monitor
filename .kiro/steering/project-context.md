# Контекст проекта OpenWrt Captive Monitor

## Обзор проекта

**openwrt-captive-monitor** - это легковесный сервис для автоматического обнаружения и обработки captive порталов на маршрутизаторах OpenWrt.

### Ключевые компоненты

- **Основной скрипт**: `openwrt_captive_monitor.sh` - bash скрипт для обнаружения и обработки captive порталов
- **Пакет OpenWrt**: `package/openwrt-captive-monitor/` - структура пакета для OpenWrt
- **Docker SDK**: `docker/sdk/` - Docker образы для сборки пакетов через OpenWrt SDK
- **CI/CD**: `.github/workflows/` - автоматизированная сборка, тестирование и релизы

### Архитектуры и версии

**Поддерживаемые версии OpenWrt:**
- 21.02 (LTS) - iptables backend
- 22.03 (LTS) - автоопределение backend
- 23.05 (Stable) - полная поддержка nftables
- 24.10 (Development)

**Поддерживаемые архитектуры:**
- mips_24kc (основная для роутеров)
- aarch64_cortex-a53
- x86_64
- all (универсальный пакет)

## Структура сборки

### Docker SDK образы

Проект использует предсобранные Docker образы с OpenWrt SDK для ускорения сборки:
- Образы хранятся в GitHub Container Registry (GHCR)
- Ускорение сборки на 40-60% (с 3-5 минут до 1.5-2.5 минут)
- Поддержка 8 архитектур OpenWrt

**Важные файлы:**
- `docker/sdk/Dockerfile` - определение Docker образа
- `docker/sdk/download-sdk.sh` - скрипт загрузки SDK
- `docker/sdk/build-local.sh` - локальная сборка образов
- `scripts/validate-docker-image-size.sh` - валидация размера образа (лимит 2GB)

### Процесс релиза

**Автоматический релиз на основе даты:**
- Формат тега: `vYYYY.M.D.N` (например, `v2025.11.20.2`)
- Автоматическое обновление VERSION файла и PKG_VERSION в Makefile
- PKG_RELEASE всегда `1` для официальных релизов
- Workflow: `auto-version-tag.yml` → `tag-build-release.yml`

**Важные файлы:**
- `VERSION` - текущая версия проекта
- `package/openwrt-captive-monitor/Makefile` - PKG_VERSION и PKG_RELEASE
- `.github/workflows/auto-version-tag.yml` - автоматическое создание тегов
- `.github/workflows/tag-build-release.yml` - сборка и публикация релиза

## Тестирование

### Виртуализация

Проект включает VM-based тестирование с QEMU/KVM:
- `scripts/run_openwrt_vm.sh` - запуск OpenWrt VM для тестирования
- Автоматическая установка пакета и smoke tests
- Поддержка CI окружения без KVM (TCG emulation)

### Unit тесты

- `tests/run.sh` - основной тестовый раннер
- `tests/mocks/` - моки для системных команд
- Использование BusyBox для тестирования

## Общие задачи разработки

### Работа с Docker образами

**Проблемы, которые могут возникнуть:**
1. Размер образа превышает 2GB - требуется оптимизация слоев
2. Ошибки загрузки SDK - проблемы с URL или суффиксами MUSL
3. Проблемы с путями на Windows - требуется правильное монтирование томов

**Типичные оптимизации:**
- Объединение RUN команд для уменьшения слоев
- Очистка кэшей apt в том же слое
- Использование multi-stage builds
- Правильный .dockerignore

### Работа с GitHub Actions

**Важные workflow:**
- `ci.yml` - основной CI pipeline
- `build-sdk-images.yml` - сборка Docker SDK образов
- `openwrt-build.yml` - сборка пакетов OpenWrt
- `security-scanning.yml` - сканирование безопасности

**Общие проблемы:**
- Старые workflow продолжают работать - нужна отмена через `cancel-old-workflows`
- Проблемы с правами доступа к GITHUB_TOKEN
- Таймауты при загрузке SDK

### Работа с OpenWrt пакетами

**Структура пакета:**
```
package/openwrt-captive-monitor/
├── Makefile              # Определение пакета
├── files/                # Файлы для установки
│   ├── etc/config/       # UCI конфигурация
│   ├── etc/init.d/       # Init скрипты
│   └── usr/sbin/         # Исполняемые файлы
└── LICENSE
```

**Важные переменные Makefile:**
- `PKG_VERSION` - версия пакета (синхронизируется с VERSION файлом)
- `PKG_RELEASE` - номер релиза (1 для официальных релизов)
- `PKG_BUILD_DIR` - директория сборки
- `PKG_INSTALL` - установка файлов

## Соглашения о коммитах

Проект использует Conventional Commits:
- `feat:` - новая функциональность
- `fix:` - исправление ошибок
- `docs:` - изменения в документации
- `ci:` - изменения в CI/CD
- `refactor:` - рефакторинг кода
- `test:` - добавление/изменение тестов
- `chore:` - рутинные задачи

## Документация

**Основные разделы:**
- `docs/guides/` - руководства пользователя
- `docs/ci/` - документация CI/CD
- `docs/project/` - управление проектом
- `docs/reports/` - отчеты и анализ

**Важные документы:**
- `docs/docker-sdk-images.md` - документация Docker SDK
- `docs/guides/sdk-build-workflow.md` - процесс сборки через SDK
- `docs/release/RELEASE_PROCESS.md` - процесс релиза
- `docs/AUTO_VERSION_MIGRATION.md` - миграция на автоверсионирование

## Специфика Windows разработки

### Пути и монтирование

**PowerShell:**
```powershell
docker run -v ${PWD}:/workspace image
docker run -v C:\git\project:/workspace image
```

**CMD:**
```cmd
docker run -v %CD%:/workspace image
```

### Запуск bash скриптов

**Варианты:**
1. Git Bash: `bash script.sh`
2. WSL: `wsl bash script.sh`
3. Docker: `docker run --rm -v ${PWD}:/workspace image bash script.sh`

### Общие проблемы

- Line endings (CRLF vs LF) - настроить `core.autocrlf=input`
- Права доступа при монтировании томов
- Пути с обратными слешами в скриптах
