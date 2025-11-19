# Release Documentation

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

This section contains documentation related to the release process, versioning, and deployment.

## 📋 Core Documentation

### Release Process
- [**Auto Version Tag (Active)**](AUTO_VERSION_TAG.md) - Date-based automatic versioning (vYYYY.M.D.N)
- [Release Process (Legacy)](RELEASE_PROCESS.md) - Historical semantic versioning documentation
- [Changelog](CHANGELOG.md) - Version history and release notes

## 🚀 Release Overview

### Release Types
- **Major releases** (X.0.0) - Breaking changes and major features
- **Minor releases** (X.Y.0) - New features and improvements
- **Patch releases** (X.Y.Z) - Bug fixes and security patches

### Release Cadence
- **Major**: As needed, with extensive testing
- **Minor**: Monthly or as features are ready
- **Patch**: As needed for critical fixes

## 🔄 Release Process

### Pre-Release Checklist
1. All tests passing
2. Documentation updated
3. Changelog updated
4. Security scan completed
5. Review completed

### Release Steps
1. Create release branch
2. Update version numbers
3. Run full test suite
4. Build packages
5. Create GitHub release
6. Deploy to repositories
7. Update documentation

### Post-Release
1. Monitor for issues
2. Announce release
3. Update project status
4. Plan next release

## 📦 Package Distribution

### Official Packages
- [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) - Official IPK packages
- OpenWrt packages feed (future)

### Build Artifacts
- IPK packages for all architectures
- Source tarballs
- Build logs
- Test results

## 🔍 Version Information

### Current Version
See the [VERSION](../../VERSION) file for the current version.

### Version History
See the [Changelog](CHANGELOG.md) for detailed version history.

### Semantic Versioning
This project follows [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes

## 🛡️ Security Releases

### Security Patch Process
1. Security vulnerability identified
2. Fix developed in private branch
3. Security advisory prepared
4. Coordinated release with maintainers
5. Public disclosure and patch release

### Security Updates
- Critical security patches released as soon as possible
- Security advisories published with each security release
- Backports provided for supported versions

## 📊 Release Metrics

### Release Statistics
- Release frequency and patterns
- Bug fix turnaround time
- Feature delivery timeline
- Security response time

### Quality Metrics
- Test coverage per release
- Bug counts and types
- Performance benchmarks
- User feedback analysis

## 🔧 Development Tools

### Release Automation
- **Release Please** - Automated versioning and changelog generation
- **GitHub Actions** - Automated build, test, and release workflows
- **Cosign** - Artifact signing and verification

### Configuration
- [Release Please Config](../../release-please-config.json) - Release automation configuration
- [GitHub Workflows](../../../.github/workflows/) - CI/CD and release workflows

## 📚 Related Documentation

### Development
- [Contributing Guide](../contributing/CONTRIBUTING.md) - Development guidelines
- [Setup Documentation](../setup/) - Development setup
- [CI/CD Documentation](../setup/CI_MODERNIZATION_2025.md) - Build and release automation

### Project Management
- [Project Management](../project/management.md) - Project planning and roadmap
- [Release Checklist](../project/release-checklist.md) - Detailed release checklist
- [Test Plan](../project/test-plan.md) - Testing procedures

### Security
- [Security Documentation](../security/) - Security policies and procedures
- [Security Scanning](../SECURITY_SCANNING.md) - Automated security scanning

## 📞 Support

### Getting Help
- [Support Documentation](../../../.github/SUPPORT.md) - Getting help and support
- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - Community support

### Release Issues
- Report release-specific issues via GitHub Issues
- Use the "release" label for release-related problems
- Include version information in all reports

---

**Last updated:** 2025-11-14

---

# Русский

---

## 🌐 Язык

[English](#release-documentation) | **Русский**

---

# Документация по релизам

Этот раздел содержит документацию, связанную с процессом релизов, версионированием и развёртыванием.

## 📋 Основная документация

### Процесс релизов
- [**Auto Version Tag (активный)**](AUTO_VERSION_TAG.md) — Датированное автоматическое версионирование (vYYYY.M.D.N)
- [Процесс релизов (устаревший)](RELEASE_PROCESS.md) — Историческая документация по семантическому версионированию
- [Журнал изменений](CHANGELOG.md) — История версий и примечания к релизам

## 🚀 Обзор релизов

### Типы релизов
- **Мажорные релизы** (X.0.0) — Ломающие изменения и крупные функции
- **Минорные релизы** (X.Y.0) — Новые функции и улучшения
- **Патч‑релизы** (X.Y.Z) — Исправления ошибок и патчи безопасности

### Периодичность релизов
- **Мажорные**: По мере необходимости, после обширного тестирования
- **Минорные**: Ежемесячно или по мере готовности функционала
- **Патчи**: По необходимости для критических исправлений

## 🔄 Процесс релиза

### Предрелизный чек‑лист
1. Все тесты проходят
2. Документация обновлена
3. Обновлён журнал изменений
4. Выполнено сканирование безопасности
5. Завершено ревью

### Шаги релиза
1. Создать ветку релиза
2. Обновить номера версий
3. Запустить полный набор тестов
4. Собрать пакеты
5. Создать релиз на GitHub
6. Развернуть артефакты в репозиториях
7. Обновить документацию

### После релиза
1. Мониторить возможные проблемы
2. Анонсировать релиз
3. Обновить статус проекта
4. Спланировать следующий релиз

## 📦 Распространение пакетов

### Официальные пакеты
- [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) — Официальные IPK‑пакеты
- OpenWrt packages feed (планируется в будущем)

### Артефакты сборки
- IPK‑пакеты для всех архитектур
- Исходные tar‑архивы
- Логи сборки
- Результаты тестов

## 🔍 Информация о версиях

### Текущая версия
Актуальную версию см. в файле [VERSION](../../VERSION).

### История версий
Подробную историю версий см. в [журнале изменений](CHANGELOG.md).

### Семантическое версионирование
Проект следует [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR**: Несовместимые изменения API
- **MINOR**: Новая функциональность, совместимая назад
- **PATCH**: Исправления ошибок, не ломающие совместимость

## 🛡️ Релизы безопасности

### Процесс выпуска патчей безопасности
1. Обнаружена уязвимость безопасности
2. Исправление разрабатывается в приватной ветке
3. Готовится security‑advisory
4. Проводится согласованный релиз с мейнтейнерами
5. Публичное раскрытие и выпуск патча

### Обновления безопасности
- Критические патчи безопасности выпускаются как можно быстрее
- Для каждого релиза безопасности публикуются security‑advisory
- Для поддерживаемых версий предоставляются backport‑исправления

## 📊 Метрики релизов

### Статистика релизов
- Частота и структура релизов
- Время реакции на баг‑фиксы
- Сроки доставки функционала
- Время реакции на инциденты безопасности

### Метрики качества
- Покрытие тестами на каждый релиз
- Количество и типы багов
- Результаты производительных тестов
- Анализ отзывов пользователей

## 🔧 Инструменты разработки

### Автоматизация релизов
- **Release Please** — Автоматическое версионирование и генерация changelog
- **GitHub Actions** — Автоматическая сборка, тестирование и выпуск релизов
- **Cosign** — Подпись и проверка артефактов

### Конфигурация
- [Конфигурация Release Please](../../release-please-config.json) — Настройки автоматизации релизов
- [GitHub‑workflow](../../../.github/workflows/) — CI/CD и workflows для релизов

## 📚 Связанная документация

### Разработка
- [Руководство по вкладу](../contributing/CONTRIBUTING.md) — Рекомендации по разработке
- [Документация по настройке](../setup/) — Настройка окружения разработки
- [Документация по CI/CD](../setup/CI_MODERNIZATION_2025.md) — Автоматизация сборки и релизов

### Управление проектом
- [Управление проектом](../project/management.md) — Планирование и дорожная карта
- [Чек‑лист релиза](../project/release-checklist.md) — Подробный чек‑лист релиза
- [План тестирования](../project/test-plan.md) — Процедуры тестирования

### Безопасность
- [Документация по безопасности](../security/) — Политики и процедуры безопасности
- [Сканирование безопасности](../SECURITY_SCANNING.md) — Автоматизированное сканирование безопасности

## 📞 Поддержка

### Получение помощи
- [Документация по поддержке](../../../.github/SUPPORT.md) — Как получить помощь и поддержку
- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) — Отчёты об ошибках и запросы функций
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) — Поддержка от сообщества

### Проблемы, связанные с релизами
- Сообщайте о проблемах, связанных с релизами, через GitHub Issues
- Используйте метку "release" для релиз‑связанных задач
- Всегда указывайте информацию о версии в отчётах

---

**Последнее обновление:** 2025-11-14
