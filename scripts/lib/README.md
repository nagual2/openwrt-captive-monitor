# Library Utilities

Эта директория содержит вспомогательные библиотеки для различных операций в проекте.

## Release Restoration Utilities

Утилиты для восстановления удалённых релизов проекта.

### changelog-parser.sh

Парсинг CHANGELOG.md для извлечения информации о семантических версиях.

**Основные функции:**

- `parse_changelog_versions` - извлечь все версии из CHANGELOG
- `get_changelog_for_version <version>` - получить changelog для конкретной версии
- `list_semantic_versions` - список всех семантических версий
- `version_exists_in_changelog <version>` - проверить наличие версии
- `get_version_date <version>` - получить дату версии

**Пример использования:**

```bash
source scripts/lib/changelog-parser.sh

# Получить список версий
versions=$(list_semantic_versions)

# Получить changelog для v1.0.3
changelog=$(get_changelog_for_version "v1.0.3")
```

### commit-finder.sh

Поиск git коммитов для конкретных версий с использованием нескольких стратегий.

**Основные функции:**

- `find_commit_for_version <version> [date_hint]` - найти коммит для версии
- `find_by_existing_tag <version>` - поиск по существующему тегу
- `find_by_commit_message <version>` - поиск по сообщению коммита
- `find_by_version_file <version>` - поиск по изменениям в VERSION файле
- `find_by_date <version> <date>` - поиск по дате
- `get_commit_date <sha>` - получить дату коммита
- `verify_commit_exists <sha>` - проверить существование коммита

**Стратегии поиска (в порядке применения):**

1. Проверка существующего тега
2. Поиск в сообщениях коммитов
3. Поиск изменений в VERSION файле
4. Поиск по дате (если указана)
5. Поиск изменений в Makefile PKG_VERSION

**Пример использования:**

```bash
source scripts/lib/commit-finder.sh

# Найти коммит для v1.0.3
commit=$(find_commit_for_version "v1.0.3")

# Найти коммит с подсказкой по дате
commit=$(find_commit_for_version "v0.1.0" "2024-11-15")
```

### changelog-generator.sh

Генерация changelog из git истории для датированных релизов.

**Основные функции:**

- `generate_changelog_for_tag <tag> [format]` - сгенерировать changelog для тега
- `generate_dated_release_changelog <tag>` - сгенерировать changelog для датированного релиза
- `find_previous_tag <tag>` - найти предыдущий тег
- `list_all_tags` - список всех тегов
- `list_dated_tags` - список датированных тегов (vYYYY.M.D.N)
- `list_semantic_tags` - список семантических тегов (vX.Y.Z)
- `extract_date_from_tag <tag>` - извлечь дату из датированного тега
- `count_commits_between <prev_tag> <current_tag>` - подсчитать коммиты между тегами

**Форматы вывода:**

- `markdown` (по умолчанию) - группировка по типам коммитов (feat, fix, docs, ci)
- `plain` - простой список коммитов

**Пример использования:**

```bash
source scripts/lib/changelog-generator.sh

# Сгенерировать changelog для тега
changelog=$(generate_changelog_for_tag "v2025.11.27.13")

# Сгенерировать полный changelog для датированного релиза
full_changelog=$(generate_dated_release_changelog "v2025.11.27.13")

# Список датированных тегов
dated_tags=$(list_dated_tags)
```

## Other Utilities

### colors.sh

Определения цветов для вывода в терминал.

### timeout-wrapper.sh

Wrapper для выполнения команд с таймаутом.

## Testing

Для тестирования утилит восстановления релизов:

```bash
bash scripts/test-lib-utilities.sh
```

Этот скрипт проверяет все основные функции и выводит результаты тестирования.
