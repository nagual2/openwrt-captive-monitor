# Индекс документации проекта OpenWrt Captive Monitor

## 📚 Навигация по документации

### 🚀 Быстрый старт
- [README.md](../README.md) - Основная документация проекта

### 🏗️ Архитектура и разработка
- [Architecture Guide](guides/architecture.md) - Архитектура системы
- [SDK Build Workflow](guides/sdk-build-workflow.md) - Процесс сборки через SDK
- [Captive Portal Walkthrough](guides/captive-portal-walkthrough.md) - Как работает обнаружение captive portal
- [Troubleshooting Guide](guides/troubleshooting.md) - Решение проблем

### ⚙️ Конфигурация
- **Configuration**: Настройка производится через cron. См. `README.md`.

### 📦 Пакетирование и сборка
- [Package Build Process](PACKAGE_BUILD_PROCESS_AND_MANIFEST.md) - Процесс сборки пакетов
- [Package Build Quick Summary](PACKAGE_BUILD_QUICK_SUMMARY.md) - Краткое описание сборки
- [Packages Documentation](PACKAGES.md) - Документация по пакетам
- [Packaging Guide](packaging.md) - Руководство по упаковке

### 🔄 Релизы
- [Release Process](release/RELEASE_PROCESS.md) - Процесс создания релизов
- [Release Checklist](RELEASE_CHECKLIST.md) - Чеклист для релизов
- [Manual Release](release/MANUAL_RELEASE.md) - Ручной релиз
- [Auto Version Tag](release/AUTO_VERSION_TAG.md) - Автоматическое версионирование
- [Changelog](release/CHANGELOG.md) - История изменений

### 🧪 Тестирование
- [Test Plan](TEST_PLAN.md) - План тестирования
- [Virtualized Testing](guides/virtualized-testing.md) - Тестирование в виртуальной среде
- [One-shot Recovery](guides/oneshot-recovery.md) - Восстановление в режиме oneshot

### 🔧 CI/CD и разработка
- [CI Workflow Simplified](ci/CI_WORKFLOW_SIMPLIFIED.md) - Упрощенный CI workflow
- [GitHub Actions Workflows Audit](ci/GITHUB_ACTIONS_WORKFLOWS_AUDIT.md) - Аудит workflows
- [Docker SDK Images](docker-sdk-images.md) - Docker образы для SDK

### 🔒 Безопасность
- [Security Scanning](SECURITY_SCANNING.md) - Сканирование безопасности
- [Security Audit Report](security/SECURITY_AUDIT_REPORT.md) - Отчет аудита безопасности
- [Security Scanning Implementation](security/SECURITY_SCANNING_IMPLEMENTATION.md) - Реализация сканирования

### 📝 Участие в разработке
- [Contributing Guide](contributing/CONTRIBUTING.md) - Руководство для контрибьюторов
- [Code of Conduct](contributing/CODE_OF_CONDUCT.md) - Кодекс поведения
- [PR Triage](project/PR_TRIAGE.md) - Триаж Pull Request

### 🐛 Известные проблемы
- [Known Issues](KNOWN_ISSUES.md) - Список известных проблем
- [PROCD Investigation](PROCD_INVESTIGATION.md) - Исследование проблем с procd

### 📊 Отчеты и аналитика
- [Reports Index](reports/README.md) - Индекс всех отчетов
- [Diagnostics Index](reports/DIAGNOSTICS_INDEX.md) - Индекс диагностики
- [Analysis Index](reports/ANALYSIS_INDEX.md) - Индекс аналитики

### 🔍 Специфичные темы
- [Docker SDK Optimization](ci/docker-sdk-optimization.md) - Оптимизация Docker SDK
- [IPK Format Investigation](IPK_FORMAT_INVESTIGATION.md) - Исследование формата IPK
- [Git WSL Workflow](git-wsl-workflow.md) - Работа с Git через WSL
- [Workflow Diagnostics](WORKFLOW_DIAGNOSTICS.md) - Диагностика workflows

### 📋 Проектная документация
- [Project Management](project/management.md) - Управление проектом
- [Backlog](BACKLOG.md) - Бэклог проекта
- [Branch Protection Setup](project/BRANCH_PROTECTION_SETUP.md) - Настройка защиты веток
- [Branches and Merge Policy](project/BRANCHES_AND_MERGE_POLICY.md) - Политика веток и мержа

### 🛠️ Настройка и установка
- [Setup Guide](setup/README.md) - Руководство по настройке
- [CI Modernization 2025](setup/CI_MODERNIZATION_2025.md) - Модернизация CI в 2025
- [Toolchain Initialization Fix](setup/TOOLCHAIN_INITIALIZATION_FIX.md) - Исправление инициализации toolchain

### 📈 Оптимизация
- [Optimization Recommendations](OPTIMIZATION_RECOMMENDATIONS.md) - Рекомендации по оптимизации
- [Documentation Cleanup Summary](DOCUMENTATION_CLEANUP_SUMMARY.md) - Отчет об очистке документации

---

## 📂 Структура документации

```
docs/
├── INDEX.md (этот файл)
├── README.md - Главная документация
├── configuration/ - Конфигурация
├── contributing/ - Участие в разработке
├── guides/ - Руководства
├── release/ - Релизы
├── reports/ - Отчеты
│   └── archive/ - Архив старых отчетов
├── security/ - Безопасность
├── setup/ - Настройка
├── usage/ - Использование
├── project/ - Проектная документация
├── ci/ - CI/CD документация
└── triage/ - Триаж issues/PR
```

---

## 🔍 Поиск по категориям

### Для пользователей
- Установка: [Installation Guide](usage/installation.md)
- Быстрый старт: [Quick Start](usage/quick-start.md)
- Конфигурация: [Configuration Reference](configuration/reference.md)
- Решение проблем: [Troubleshooting](guides/troubleshooting.md)

### Для разработчиков
- Архитектура: [Architecture Guide](guides/architecture.md)
- Процесс сборки: [Package Build Process](PACKAGE_BUILD_PROCESS_AND_MANIFEST.md)
- Тестирование: [Test Plan](TEST_PLAN.md)
- Участие: [Contributing Guide](contributing/CONTRIBUTING.md)

### Для DevOps
- CI/CD: [CI Workflow](ci/CI_WORKFLOW_SIMPLIFIED.md)
- Docker: [Docker SDK Images](docker-sdk-images.md)
- Релизы: [Release Process](release/RELEASE_PROCESS.md)

---

## 📝 Примечания

- Все документы обновляются регулярно
- Устаревшие документы перемещаются в `archive/`
- Актуальная версия всегда в корне соответствующих папок
- Для предложений по улучшению документации создавайте issue

---

*Последнее обновление: 2025-12-03*
