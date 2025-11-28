# Паттерны версионирования

## Датированное авто-версионирование

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

### Инварианты версионирования

**Проверяются в tag-build-release.yml:**

```bash
# 1. VERSION файл соответствует тегу
TAG_VERSION=${GITHUB_REF#refs/tags/v}  # Убрать префикс v
FILE_VERSION=$(cat VERSION)

if [ "$TAG_VERSION" != "$FILE_VERSION" ]; then
  echo "ERROR: Version mismatch"
  echo "Tag: v$TAG_VERSION"
  echo "VERSION file: $FILE_VERSION"
  exit 1
fi

# 2. PKG_VERSION соответствует VERSION
PKG_VERSION=$(grep "^PKG_VERSION:=" package/*/Makefile | cut -d'=' -f2)

if [ "$PKG_VERSION" != "$FILE_VERSION" ]; then
  echo "ERROR: PKG_VERSION mismatch"
  echo "Expected: $FILE_VERSION"
  echo "Actual: $PKG_VERSION"
  exit 1
fi

# 3. PKG_RELEASE равен 1
PKG_RELEASE=$(grep "^PKG_RELEASE:=" package/*/Makefile | cut -d'=' -f2)

if [ "$PKG_RELEASE" != "1" ]; then
  echo "ERROR: PKG_RELEASE must be 1 for new version"
  echo "Actual: $PKG_RELEASE"
  exit 1
fi
```

### Скрипт обновления версии

```bash
#!/bin/bash
# scripts/update-version-metadata.sh

set -euo pipefail

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 2025.1.15.1"
    exit 1
fi

echo "Updating version to $NEW_VERSION"

# Обновить VERSION файл
echo "$NEW_VERSION" > VERSION

# Обновить PKG_VERSION в Makefile
sed -i "s/^PKG_VERSION:=.*/PKG_VERSION:=${NEW_VERSION}/" \
  package/openwrt-captive-monitor/Makefile

# Установить PKG_RELEASE в 1
sed -i "s/^PKG_RELEASE:=.*/PKG_RELEASE:=1/" \
  package/openwrt-captive-monitor/Makefile

echo "✅ Updated version metadata:"
echo "  VERSION: $NEW_VERSION"
echo "  PKG_VERSION: $NEW_VERSION"
echo "  PKG_RELEASE: 1"
```

### Скрипт валидации версии

```bash
#!/bin/bash
# scripts/validate-version-metadata.sh

set -euo pipefail

echo "=== Validating version metadata ==="

# Получить версии
VERSION=$(cat VERSION)
PKG_VERSION=$(grep "^PKG_VERSION:=" package/openwrt-captive-monitor/Makefile | cut -d'=' -f2)
PKG_RELEASE=$(grep "^PKG_RELEASE:=" package/openwrt-captive-monitor/Makefile | cut -d'=' -f2)

echo "VERSION file: $VERSION"
echo "PKG_VERSION: $PKG_VERSION"
echo "PKG_RELEASE: $PKG_RELEASE"

# Проверка соответствия
errors=0

if [ "$VERSION" != "$PKG_VERSION" ]; then
    echo "❌ ERROR: VERSION and PKG_VERSION mismatch"
    errors=$((errors + 1))
fi

if [ "$PKG_RELEASE" != "1" ]; then
    echo "❌ ERROR: PKG_RELEASE should be 1"
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    echo "✅ Version metadata is valid"
    exit 0
else
    echo "❌ Found $errors error(s)"
    exit 1
fi
```

## Conventional Commits (опционально)

Хотя датированное версионирование не требует Conventional Commits, они полезны для changelog:

### Формат

```
type: description

[optional body]

[optional footer]
```

### Типы коммитов

- `feat:` - новая функциональность
- `fix:` - исправление ошибки
- `docs:` - изменения в документации
- `ci:` - изменения в CI/CD
- `refactor:` - рефакторинг кода
- `test:` - добавление/изменение тестов
- `chore:` - рутинные задачи
- `perf:` - улучшение производительности
- `style:` - форматирование кода

### Примеры

```bash
# Новая функциональность
git commit -m "feat: add support for nftables backend"

# Исправление ошибки
git commit -m "fix: resolve captive portal detection on IPv6"

# Документация
git commit -m "docs: update installation instructions for Windows"

# CI/CD
git commit -m "ci: optimize Docker image build process"

# Рефакторинг
git commit -m "refactor: simplify retry logic in download script"

# Тесты
git commit -m "test: add property-based tests for version validation"

# С телом коммита
git commit -m "feat: add parallel build support

- Implement controlPwshProcess integration
- Add monitoring for parallel builds
- Update documentation"

# Breaking change
git commit -m "feat!: change configuration file format

BREAKING CHANGE: Configuration file now uses YAML instead of UCI"
```

### Интеграция с changelog

```bash
# Генерация changelog из коммитов
git log --oneline --no-merges v2025.1.15.1..HEAD | \
  grep -E "^[a-f0-9]+ (feat|fix|docs|ci|refactor|test|chore|perf|style):" | \
  sed 's/^[a-f0-9]* /- /'
```

## Преимущества датированного версионирования

### Для разработчиков

1. **Простота** - не нужно решать major/minor/patch
2. **Автоматизация** - каждый merge создаёт релиз
3. **Отсутствие конфликтов** - нет merge conflicts в VERSION
4. **Гибкость** - любой коммит может стать релизом

### Для пользователей

1. **Прозрачность** - версия показывает дату релиза
2. **Предсказуемость** - одинаковый формат всегда
3. **Трассируемость** - легко найти релиз по дате
4. **Понятность** - не нужно знать SemVer

### Для CI/CD

1. **Автоматизация** - полностью автоматический процесс
2. **Надежность** - нет ручных ошибок в версионировании
3. **Скорость** - быстрое создание релизов
4. **Консистентность** - единообразный процесс

## Когда использовать

### Подходит для

- ✅ Приложений (не библиотек)
- ✅ Continuous deployment
- ✅ Проектов, где важна дата релиза
- ✅ Внутренних инструментов
- ✅ CLI утилит
- ✅ Системных сервисов

### Не подходит для

- ❌ Публичных библиотек с API
- ❌ Проектов, требующих SemVer
- ❌ Когда нужна совместимость версий
- ❌ Когда пользователи полагаются на major/minor/patch
- ❌ Пакетов в npm, PyPI, RubyGems и т.д.

## Миграция с SemVer

### Процесс миграции

1. **Отключить Release Please:**
   ```bash
   mv .github/workflows/release-please.yml .github/workflows/release-please.yml.disabled
   ```

2. **Создать auto-version workflow:**
   - Скопировать `.github/workflows/auto-version-tag.yml`
   - Настроить под свой проект

3. **Обновить документацию:**
   - Объяснить новый формат версий
   - Обновить примеры в README
   - Создать migration guide

4. **Первый релиз:**
   ```bash
   # Создать первый датированный тег вручную
   bash scripts/update-version-metadata.sh 2025.1.15.1
   git add VERSION package/*/Makefile
   git commit -m "chore: migrate to date-based versioning"
   git tag v2025.1.15.1
   git push origin main --tags
   ```

5. **Проверить автоматизацию:**
   - Сделать тестовый коммит в main
   - Проверить создание тега
   - Проверить создание релиза

### Сохранение старых тегов

Старые SemVer теги остаются доступными:
- `v1.0.0`, `v1.1.0`, `v1.2.3` и т.д.
- Пользователи могут продолжать использовать их
- Новые релизы используют датированный формат

## Troubleshooting

### Проблема: Тег уже существует

**Симптом:**
```
fatal: tag 'v2025.1.15.1' already exists
```

**Причина:**
- Workflow запущен дважды
- Тег создан вручную

**Решение:**
- Workflow автоматически пропустит создание тега
- Или удалить тег и пересоздать:
  ```bash
  git tag -d v2025.1.15.1
  git push origin :refs/tags/v2025.1.15.1
  ```

### Проблема: VERSION не соответствует тегу

**Симптом:**
```
ERROR: Version mismatch
Tag: v2025.1.15.1
VERSION file: 2025.1.15.2
```

**Причина:**
- VERSION файл изменен вручную
- Коммит с обновлением VERSION не создан

**Решение:**
```bash
# Обновить VERSION файл
bash scripts/update-version-metadata.sh 2025.1.15.1

# Создать коммит
git add VERSION package/*/Makefile
git commit -m "chore: fix version metadata"
git push
```

### Проблема: PKG_RELEASE не равен 1

**Симптом:**
```
ERROR: PKG_RELEASE must be 1 for new version
Actual: 2
```

**Причина:**
- PKG_RELEASE не сброшен при новой версии

**Решение:**
```bash
# Обновить PKG_RELEASE
sed -i "s/^PKG_RELEASE:=.*/PKG_RELEASE:=1/" package/*/Makefile

# Создать коммит
git add package/*/Makefile
git commit -m "chore: reset PKG_RELEASE to 1"
git push
```
