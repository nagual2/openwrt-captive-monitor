# openwrt-captive-monitor Documentation

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

Welcome to the comprehensive documentation for **openwrt-captive-monitor**, a lightweight OpenWrt helper that monitors WAN connectivity, detects captive portals, and temporarily intercepts LAN DNS/HTTP traffic to facilitate client authentication.

## 📚 Documentation Structure

### 🚀 Getting Started
- [Quick Start Guide](usage/quick-start.md) - Get up and running in minutes
- [Installation Guide](usage/installation.md) - Prebuilt packages vs SDK builds
- [Basic Configuration](configuration/basic-config.md) - Essential UCI settings

### 📖 User Guides
- [Captive Portal Walkthrough](guides/captive-portal-walkthrough.md) - End-to-end example
- [Oneshot Recovery Mode](guides/oneshot-recovery.md) - Manual connectivity recovery
- [Advanced Configuration](configuration/advanced-config.md) - Environment variables and CLI flags
- [Troubleshooting](guides/troubleshooting.md) - Common issues and solutions

### ⚙️ Reference
- [Configuration Reference](configuration/reference.md) - Complete UCI options, environment variables, and CLI flags
- [FAQ](project/faq.md) - Frequently asked questions
- [Architecture Overview](guides/architecture.md) - System design and components

### 🏗️ Project
- [Project Management](project/management.md) - Date-based versioning strategy (with legacy semantic context), release cadence, and project boards
- [Contributing](contributing/CONTRIBUTING.md) - Development guidelines and pull request process
- [Security](../.github/SECURITY.md) - Security policy and vulnerability reporting
- [Security Scanning](SECURITY_SCANNING.md) - Automated security scanning infrastructure
- [Support](../.github/SUPPORT.md) - Get help and community resources

### 📋 Development
- [Release Checklist](project/release-checklist.md) - Step-by-step release process
- [Test Plan](project/test-plan.md) - Testing procedures and validation
- [Virtualization Guide](guides/virtualization.md) - VM-based end-to-end testing
- [Virtualized Testing Guide](guides/virtualized-testing.md) - VM-based testing strategy and automation
- [SDK Build Workflow](guides/sdk-build-workflow.md) - OpenWrt SDK-based CI/CD pipeline
- [Build System Root Causes and Target Flow](BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) - Historical failures, root causes, and future workflow
- [Backlog](project/backlog.md) - Feature roadmap and priorities
- [Package Management](project/packages.md) - Build and distribution details
- [Packaging and Distribution](packaging.md) - Complete packaging workflow and automation

## 🔗 Quick Links

- **Latest Release**: [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases)
- **Package Repository**: [OpenWrt Feed](https://github.com/nagual2/openwrt-captive-monitor/releases)
- **Issue Tracker**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions)

## 📖 About This Documentation

This documentation is organized to serve both end-users who want to deploy and configure the captive monitor, as well as developers who want to contribute to the project. The markdown files can be viewed directly on GitHub or any markdown viewer.

For the most up-to-date information, always refer to the [main repository](https://github.com/nagual2/openwrt-captive-monitor).

---

# Русский

---

## 🌐 Язык

[English](#openwrt-captive-monitor-documentation) | **Русский**

---

# Документация openwrt-captive-monitor

Добро пожаловать в подробную документацию по **openwrt-captive-monitor**, легкого помощника OpenWrt, который контролирует подключение WAN, обнаруживает портали аутентификации и временно перехватывает трафик DNS/HTTP на локальной сети для облегчения аутентификации клиентов.

## 📚 Структура документации

### 🚀 Начало работы
- [Руководство быстрого старта](usage/quick-start.md) - Начните работу за несколько минут
- [Руководство по установке](usage/installation.md) - Готовые пакеты в сравнении со сборками SDK
- [Базовая конфигурация](configuration/basic-config.md) - Основные параметры UCI

### 📖 Руководства пользователя
- [Пошаговый обход портала аутентификации](guides/captive-portal-walkthrough.md) - Комплексный пример
- [Режим восстановления Oneshot](guides/oneshot-recovery.md) - Ручное восстановление подключения
- [Продвинутая конфигурация](configuration/advanced-config.md) - Переменные окружения и флаги CLI
- [Решение проблем](guides/troubleshooting.md) - Частые проблемы и решения

### ⚙️ Справочник
- [Справочник конфигурации](configuration/reference.md) - Полные опции UCI, переменные окружения и флаги CLI
- [Часто задаваемые вопросы](project/faq.md) - Ответы на частые вопросы
- [Обзор архитектуры](guides/architecture.md) - Проектирование системы и компоненты

### 🏗️ Проект
- [Управление проектом](project/management.md) - Схема датированного версионирования (с историческим описанием SemVer), период выпуска и доски проектов
- [Вклад](contributing/CONTRIBUTING.md) - Рекомендации по разработке и процесс pull request
- [Безопасность](../.github/SECURITY.md) - Политика безопасности и отчет об уязвимостях
- [Сканирование безопасности](SECURITY_SCANNING.md) - Инфраструктура автоматизированного сканирования безопасности
- [Поддержка](../.github/SUPPORT.md) - Получение помощи и ресурсы сообщества

### 📋 Разработка
- [Чеклист выпуска](project/release-checklist.md) - Пошаговый процесс выпуска
- [План тестирования](project/test-plan.md) - Процедуры тестирования и валидация
- [Руководство виртуализации](guides/virtualization.md) - Тестирование сквозного потока на основе ВМ
- [Руководство виртуализированного тестирования](guides/virtualized-testing.md) - Стратегия и автоматизация тестирования на основе ВМ
- [Рабочий процесс сборки SDK](guides/sdk-build-workflow.md) - Конвейер CI/CD на основе OpenWrt SDK
- [Основные причины системы сборки и целевой поток](BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) - Исторические сбои, коренные причины и будущий рабочий процесс
- [Невыполненные задачи](project/backlog.md) - Дорожная карта функций и приоритеты
- [Управление пакетами](project/packages.md) - Детали сборки и распространения
- [Упаковка и распространение](packaging.md) - Полный рабочий процесс упаковки и автоматизация

## 🔗 Быстрые ссылки

- **Последний выпуск**: [GitHub Выпуски](https://github.com/nagual2/openwrt-captive-monitor/releases)
- **Репозиторий пакетов**: [OpenWrt Feed](https://github.com/nagual2/openwrt-captive-monitor/releases)
- **Отслеживание проблем**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues)
- **Обсуждения**: [GitHub Обсуждения](https://github.com/nagual2/openwrt-captive-monitor/discussions)

## 📖 О документации

Эта документация организована для обслуживания как конечных пользователей, которые хотят развернуть и настроить монитор портала аутентификации, так и разработчиков, которые хотят внести вклад в проект. Файлы markdown можно просматривать непосредственно на GitHub или в любом средстве просмотра markdown.

Для самой актуальной информации всегда обратитесь к [основному репозиторию](https://github.com/nagual2/openwrt-captive-monitor).
