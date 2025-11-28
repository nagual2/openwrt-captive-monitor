# Release Documentation

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

This section contains documentation related to the release process, versioning, and deployment.

## 📋 Core Documentation

### Release Process
- [**Manual Release Workflow**](MANUAL_RELEASE.md) - Manual release creation with full control
- [Auto Version Tag (Deprecated)](AUTO_VERSION_TAG.md) - Date-based automatic versioning (vYYYY.M.D.N)
- [Release Process (Legacy)](RELEASE_PROCESS.md) - Historical semantic versioning documentation
- [Historical Tags & Releases Restoration](HISTORICAL_TAGS_RESTORATION.md) - Inventory of legacy semantic tags and restoration plan
- [Changelog](CHANGELOG.md) - Version history and release notes

## 🚀 Release Overview

### Active Scheme: Date-Based Releases (2025+)

The current release process is **date-based**. Every official release is identified by a tag of the form:

- **Tag:** `vYYYY.M.D.N`
- **VERSION:** `YYYY.M.D.N` (no leading `v`)
- **PKG_VERSION:** `YYYY.M.D.N`
- **PKG_RELEASE:** `1` (fixed for each new `PKG_VERSION`)

> **Example:** `v2025.11.20.2` → `VERSION=2025.11.20.2`, `PKG_VERSION=2025.11.20.2`, `PKG_RELEASE=1`
>
> - First release on that date might be `v2025.11.20.1`.
> - Second release the same day becomes `v2025.11.20.2`.
>
> All three metadata locations **must match** before cutting a release.

Release cadence with the date-based scheme:
- **Normal releases:** Whenever changes are merged to `main` and a new date-based tag is created
- **Multiple releases per day:** Supported via the `N` sequence number
- **Hotfixes:** Use the same date-based format; the date reflects when the hotfix is released

### Legacy Scheme: Semantic Versioning (Historical)

Earlier versions of this project used **Semantic Versioning (SemVer)** with tags like `v1.2.3`:

- **Major releases** (X.0.0) – Breaking changes and major features
- **Minor releases** (X.Y.0) – New features and improvements
- **Patch releases** (X.Y.Z) – Bug fixes and security patches

This semantic versioning scheme is now considered **legacy** and is retained **only for historical reference**. Existing semantic tags and releases remain available on GitHub but are no longer used for new releases.

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
See the [VERSION](../../VERSION) file for the current date-based version. It is always of the form `YYYY.M.D.N` and must match the latest `vYYYY.M.D.N` tag on `main`.

### Version History
See the [Changelog](CHANGELOG.md) for detailed version history.

### Version Rules (Date-Based)

- **VERSION file:** `YYYY.M.D.N` (no leading `v`).
- **Git tag:** `vYYYY.M.D.N`.
- **PKG_VERSION:** `YYYY.M.D.N`.
- **PKG_RELEASE:** `1` for each new `PKG_VERSION`.

> **Invariant:** Tag, `VERSION`, and `PKG_VERSION` **must be identical**, and `PKG_RELEASE` must be a simple integer starting from `1` for each new version. Dev/CI builds may apply a `-dev` suffix at the artifact level, but release builds do not.

### Legacy Semantic Versioning (Historical)

Earlier releases used [Semantic Versioning 2.0.0](https://semver.org/) with tags like `v1.2.3`. Those tags and releases are still available on GitHub but are no longer used for new releases.

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
- [**Manual Release Workflow**](MANUAL_RELEASE.md) — Ручное создание релизов с полным контролем
- [Auto Version Tag (устарел)](AUTO_VERSION_TAG.md) — Датированное автоматическое версионирование (vYYYY.M.D.N)
- [Процесс релизов (устаревший)](RELEASE_PROCESS.md) — Историческая документация по семантическому версионированию
- [Восстановление исторических тегов и релизов](HISTORICAL_TAGS_RESTORATION.md) — Инвентарь старых SemVer‑тегов и план восстановления
- [Журнал изменений](CHANGELOG.md) — История версий и примечания к релизам

## 🚀 Обзор релизов

### Актуальная схема: датированные релизы (2025+)

Текущий процесс релизов **основан на дате**. Каждый официальный релиз обозначается тегом вида:

- **Тег:** `vYYYY.M.D.N`
- **VERSION:** `YYYY.M.D.N` (без префикса `v`)
- **PKG_VERSION:** `YYYY.M.D.N`
- **PKG_RELEASE:** `1` (фиксированное значение для каждой новой версии `PKG_VERSION`)

> **Пример:** `v2025.11.20.2` → `VERSION=2025.11.20.2`, `PKG_VERSION=2025.11.20.2`, `PKG_RELEASE=1`
>
> - Первый релиз в этот день может быть `v2025.11.20.1`.
> - Второй релиз в тот же день — `v2025.11.20.2`.
>
> Все три места с версией **обязаны совпадать** перед выпуском релиза.

Периодичность релизов в датированной схеме:
- **Обычные релизы:** Каждый раз, когда изменения попадают в `main` и создаётся новый датированный тег
- **Несколько релизов в один день:** Поддерживаются за счёт порядкового номера `N`
- **Хотфиксы:** Используют тот же формат; дата отражает момент выпуска хотфикса

### Устаревшая схема: семантическое версионирование (историческая справка)

Ранее проект использовал **семантическое версионирование (SemVer)** с тегами вида `v1.2.3`:

- **Мажорные релизы** (X.0.0) — Ломающие изменения и крупные функции
- **Минорные релизы** (X.Y.0) — Новые функции и улучшения
- **Патч‑релизы** (X.Y.Z) — Исправления ошибок и патчи безопасности

Эта схема сейчас считается **устаревшей** и сохранена **только в исторических целях**. Существующие семантические теги и релизы остаются на GitHub, но больше не используются для новых релизов.

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
Актуальная версия указана в файле [VERSION](../../VERSION). Формат всегда `YYYY.M.D.N` и должен совпадать с последним тегом `vYYYY.M.D.N` в ветке `main`.

### История версий
Подробную историю версий см. в [журнале изменений](CHANGELOG.md).

### Правила версионирования (датированная схема)

- **Файл VERSION:** `YYYY.M.D.N` (без префикса `v`).
- **Git‑тег:** `vYYYY.M.D.N`.
- **PKG_VERSION:** `YYYY.M.D.N`.
- **PKG_RELEASE:** `1` для каждой новой версии `PKG_VERSION`.

> **Инвариант:** Тег, `VERSION` и `PKG_VERSION` **обязаны совпадать**, а `PKG_RELEASE` должен быть простым целым числом, начинающимся с `1` для каждой новой версии. Dev/CI‑сборки могут добавлять суффикс `-dev` на уровне артефактов, но релизные сборки — нет.

### Устаревшее семантическое версионирование (история)

Ранние релизы использовали [Semantic Versioning 2.0.0](https://semver.org/) с тегами вида `v1.2.3`. Эти теги и релизы по‑прежнему доступны на GitHub, но больше не применяются для новых релизов.

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
