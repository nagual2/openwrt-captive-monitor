# Design Document: Restore Missing Releases

## Overview

Система для восстановления удалённых релизов проекта, включая исторические семантические версии (v0.1.x, v1.0.x) и отсутствующие датированные релизы (vYYYY.M.D.N). Система состоит из скриптов для восстановления тегов, создания релизов через GitHub API и проверки целостности истории версий.

## Architecture

### Компоненты системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Restore Releases System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  CHANGELOG.md    │      │   Git History    │            │
│  │  Parser          │      │   Analyzer       │            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                         │                        │
│           v                         v                        │
│  ┌──────────────────────────────────────────┐               │
│  │     Release Restoration Engine           │               │
│  │  - Semantic version restoration          │               │
│  │  - Date-based version restoration        │               │
│  │  - Tag recreation                        │               │
│  │  - Changelog generation                  │               │
│  └────────────────┬─────────────────────────┘               │
│                   │                                          │
│                   v                                          │
│  ┌──────────────────────────────────────────┐               │
│  │        GitHub API Client                 │               │
│  │  - Create tags                           │               │
│  │  - Create releases                       │               │
│  │  - Attach release notes                  │               │
│  └────────────────┬─────────────────────────┘               │
│                   │                                          │
│                   v                                          │
│  ┌──────────────────────────────────────────┐               │
│  │     Integrity Validator                  │               │
│  │  - Verify all releases exist             │               │
│  │  - Check changelog consistency           │               │
│  │  - Generate report                       │               │
│  └──────────────────────────────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Процесс восстановления

**Фаза 1: Восстановление семантических релизов**
1. Парсинг CHANGELOG.md для извлечения информации о версиях
2. Определение коммитов для каждой версии (по датам или тегам)
3. Создание тегов в Git
4. Создание GitHub релизов с changelog из CHANGELOG.md

**Фаза 2: Восстановление датированных релизов**
1. Получение списка всех тегов из удалённого репозитория
2. Получение списка существующих релизов
3. Определение тегов без релизов
4. Генерация changelog для каждого тега
5. Создание GitHub релизов

**Фаза 3: Проверка целостности**
1. Проверка наличия всех семантических релизов
2. Проверка наличия релизов для всех тегов
3. Генерация отчёта

## Components and Interfaces

### 1. CHANGELOG Parser

**Назначение:** Извлечение информации о семантических версиях из CHANGELOG.md

**Интерфейс:**
```bash
parse_changelog() {
    # Input: путь к CHANGELOG.md
    # Output: массив версий с описаниями
    
    # Формат вывода:
    # VERSION|DATE|DESCRIPTION
    # v1.0.3|2025-11-XX|Changed: ...\nFixed: ...
}
```

**Реализация:**
- Использует `awk` или `sed` для парсинга markdown
- Извлекает версию, дату и описание изменений
- Обрабатывает оба формата: `## [1.0.3]` и `## v0.1.1`

### 2. Git History Analyzer

**Назначение:** Определение коммитов для каждой версии

**Интерфейс:**
```bash
find_commit_for_version() {
    local version=$1
    local date=$2
    
    # Стратегия поиска:
    # 1. Поиск по сообщению коммита (содержит версию)
    # 2. Поиск по дате (ближайший коммит к дате из CHANGELOG)
    # 3. Поиск по изменениям в VERSION файле
    
    # Output: SHA коммита
}
```

### 3. Release Restoration Engine

**Назначение:** Создание тегов и релизов

**Интерфейс:**
```bash
restore_semantic_release() {
    local version=$1
    local commit_sha=$2
    local changelog=$3
    
    # 1. Создать тег локально
    git tag -a "$version" "$commit_sha" -m "Release $version"
    
    # 2. Push тег
    git push origin "$version"
    
    # 3. Создать релиз через GitHub API
    gh release create "$version" \
        --title "$version - Historical Release" \
        --notes "**Historical Release - Restored from CHANGELOG**\n\n$changelog"
}

restore_dated_release() {
    local tag=$1
    
    # 1. Получить коммит для тега
    local commit_sha=$(git rev-list -n 1 "$tag")
    
    # 2. Генерировать changelog
    local changelog=$(generate_changelog_for_tag "$tag")
    
    # 3. Создать релиз
    gh release create "$tag" \
        --title "$tag - $(date_from_tag $tag)" \
        --notes "**Restored Release**\n\n$changelog"
}
```

### 4. GitHub API Client

**Назначение:** Взаимодействие с GitHub API

**Используемые команды:**
```bash
# Создание релиза
gh release create <tag> --title <title> --notes <notes>

# Проверка существования релиза
gh release view <tag>

# Список релизов
gh release list --limit 100

# Получение тегов
git ls-remote --tags origin
```

### 5. Integrity Validator

**Назначение:** Проверка целостности релизов

**Интерфейс:**
```bash
validate_releases() {
    # 1. Проверить семантические релизы
    local semantic_versions=("v0.1.0" "v0.1.1" "v0.1.2" "v1.0.1" "v1.0.3")
    
    # 2. Проверить датированные релизы
    local all_tags=$(git tag -l "v2025*")
    
    # 3. Сравнить с существующими релизами
    local releases=$(gh release list --limit 100 --json tagName)
    
    # 4. Вывести отчёт
    echo "=== Release Integrity Report ==="
    echo "Semantic releases: X/5"
    echo "Date-based releases: Y/Z"
    echo "Missing releases: ..."
}
```

## Data Models

### Version Information

```bash
# Семантическая версия
SEMANTIC_VERSION={
    "tag": "v1.0.3",
    "date": "2025-11-XX",
    "changelog": "### Changed\n- Updated documentation...",
    "commit_sha": "abc123...",
    "type": "semantic"
}

# Датированная версия
DATED_VERSION={
    "tag": "v2025.11.27.10",
    "date": "2025-11-27",
    "changelog": "Generated from git log",
    "commit_sha": "def456...",
    "type": "dated"
}
```

### Release Metadata

```bash
RELEASE={
    "tag": "v1.0.3",
    "title": "v1.0.3 - Historical Release",
    "body": "**Historical Release - Restored from CHANGELOG**\n\n...",
    "draft": false,
    "prerelease": false
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Semantic release restoration completeness
*For any* semantic version listed in CHANGELOG.md (v0.1.0, v0.1.1, v0.1.2, v1.0.1, v1.0.3), after running the restoration script, a corresponding GitHub release should exist.
**Validates: Requirements 1.1, 1.4**

### Property 2: Changelog preservation for semantic releases
*For any* restored semantic release, the release body should contain the exact changelog text from CHANGELOG.md for that version.
**Validates: Requirements 1.2**

### Property 3: Historical release marking
*For any* restored semantic release, the release title or body should contain the marker "Historical Release - Restored from CHANGELOG".
**Validates: Requirements 1.3**

### Property 4: Dated release restoration completeness
*For any* dated tag (vYYYY.M.D.N) that exists in the remote repository, after running the restoration script, a corresponding GitHub release should exist.
**Validates: Requirements 2.1, 2.4**

### Property 5: Changelog generation for dated releases
*For any* dated release, the changelog should contain commits between the previous tag and the current tag.
**Validates: Requirements 2.2**

### Property 6: Dated release title format
*For any* dated release, the title should match the format "vYYYY.M.D.N - YYYY-MM-DD".
**Validates: Requirements 2.3**

### Property 7: Release restoration marking
*For any* automatically restored release (both semantic and dated), the release body should contain the marker "Restored" to indicate it was created by the restoration script.
**Validates: Requirements 3.4**

### Property 8: Restoration priority ordering
*For any* execution of the restoration script, semantic releases should be restored before dated releases.
**Validates: Requirements 4.1**

### Property 9: Error resilience
*For any* error during restoration of a single release, the script should continue processing remaining releases and report all errors at the end.
**Validates: Requirements 4.5**

### Property 10: Integrity validation completeness
*For any* execution of the integrity validator, it should check all semantic versions from CHANGELOG.md and all dated tags from the repository.
**Validates: Requirements 5.1, 5.2**

### Property 11: Missing release reporting
*For any* missing release detected by the integrity validator, the report should include the release tag and its type (semantic or dated).
**Validates: Requirements 5.3**

### Property 12: Successful validation reporting
*For any* successful integrity validation (all releases present), the report should include counts of semantic and dated releases.
**Validates: Requirements 5.4**

## Error Handling

### Стратегии обработки ошибок

**1. Отсутствие коммита для семантической версии**
- Попытка 1: Поиск по сообщению коммита
- Попытка 2: Поиск по дате из CHANGELOG
- Попытка 3: Поиск по изменениям в VERSION файле
- Fallback: Запросить у пользователя SHA коммита вручную

**2. Ошибка создания тега**
- Проверить, существует ли тег уже
- Если тег существует, продолжить с созданием релиза
- Если ошибка другая, записать в лог и продолжить

**3. Ошибка создания релиза через GitHub API**
- Проверить rate limit GitHub API
- Retry с экспоненциальной задержкой (3 попытки)
- Записать ошибку в лог и продолжить с следующим релизом

**4. Отсутствие прав доступа**
- Проверить наличие GITHUB_TOKEN
- Проверить права токена (workflow scope)
- Вывести понятное сообщение об ошибке

### Логирование

```bash
# Формат лога
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $*"
}
```

## Testing Strategy

### Unit Tests

**Тестируемые компоненты:**
1. CHANGELOG parser - проверка корректного извлечения версий
2. Commit finder - проверка поиска коммитов по различным критериям
3. Changelog generator - проверка генерации changelog для датированных версий
4. Date formatter - проверка форматирования дат из тегов

**Примеры тестов:**
```bash
# Test: CHANGELOG parser extracts all versions
test_changelog_parser() {
    local versions=$(parse_changelog "test_changelog.md")
    assert_contains "$versions" "v0.1.0"
    assert_contains "$versions" "v1.0.3"
}

# Test: Commit finder locates commit by version
test_find_commit_by_version() {
    local sha=$(find_commit_for_version "v1.0.3" "2025-11-XX")
    assert_not_empty "$sha"
}
```

### Property-Based Tests

**Библиотека:** Python + Hypothesis (для тестирования bash скриптов через subprocess)

**Тестируемые свойства:**

**Property 1: Release restoration idempotence**
```python
@given(st.sampled_from(["v0.1.0", "v0.1.1", "v0.1.2", "v1.0.1", "v1.0.3"]))
def test_restore_semantic_release_idempotent(version):
    """
    Property 1: Semantic release restoration completeness
    For any semantic version, restoring it twice should result in the same state
    
    Validates: Requirements 1.1
    """
    # First restoration
    result1 = restore_semantic_release(version)
    
    # Second restoration (should be idempotent)
    result2 = restore_semantic_release(version)
    
    # Both should succeed or both should fail with same error
    assert result1.returncode == result2.returncode
    
    # Release should exist
    release = gh_release_view(version)
    assert release is not None
```

**Property 2: Changelog preservation**
```python
@given(st.sampled_from(["v0.1.0", "v0.1.1", "v0.1.2", "v1.0.1", "v1.0.3"]))
def test_changelog_preserved_in_release(version):
    """
    Property 2: Changelog preservation for semantic releases
    For any semantic version, the release body should contain changelog from CHANGELOG.md
    
    Validates: Requirements 1.2
    """
    # Get expected changelog from CHANGELOG.md
    expected_changelog = parse_changelog_for_version(version)
    
    # Restore release
    restore_semantic_release(version)
    
    # Get actual release body
    release = gh_release_view(version)
    actual_body = release['body']
    
    # Changelog should be present in release body
    assert expected_changelog in actual_body
```

**Property 3: Historical marker presence**
```python
@given(st.sampled_from(["v0.1.0", "v0.1.1", "v0.1.2", "v1.0.1", "v1.0.3"]))
def test_historical_marker_present(version):
    """
    Property 3: Historical release marking
    For any semantic release, it should be marked as historical
    
    Validates: Requirements 1.3
    """
    restore_semantic_release(version)
    
    release = gh_release_view(version)
    body = release['body']
    
    assert "Historical Release - Restored from CHANGELOG" in body
```

**Property 4: Dated release title format**
```python
@given(st.from_regex(r'v2025\.11\.(21|22|27)\.\d+', fullmatch=True))
def test_dated_release_title_format(tag):
    """
    Property 6: Dated release title format
    For any dated tag, the release title should match the format
    
    Validates: Requirements 2.3
    """
    restore_dated_release(tag)
    
    release = gh_release_view(tag)
    title = release['name']
    
    # Extract date from tag (vYYYY.M.D.N -> YYYY-MM-DD)
    expected_date = format_date_from_tag(tag)
    
    assert title == f"{tag} - {expected_date}"
```

**Property 5: Error resilience**
```python
@given(st.lists(st.sampled_from(["v0.1.0", "v0.1.1", "invalid_tag", "v1.0.3"]), min_size=2))
def test_error_resilience(tags):
    """
    Property 9: Error resilience
    For any list of tags (including invalid ones), script should process all and report errors
    
    Validates: Requirements 4.5
    """
    result = restore_releases(tags)
    
    # Script should complete (not crash)
    assert result.returncode == 0 or result.returncode == 1
    
    # Should report errors for invalid tags
    if "invalid_tag" in tags:
        assert "ERROR" in result.stderr or "ERROR" in result.stdout
    
    # Should still process valid tags
    for tag in tags:
        if tag != "invalid_tag":
            release = gh_release_view(tag)
            assert release is not None
```

### Integration Tests

**Сценарий 1: Полное восстановление**
```bash
test_full_restoration() {
    # 1. Удалить все тестовые релизы
    cleanup_test_releases
    
    # 2. Запустить скрипт восстановления
    bash scripts/restore-releases.sh
    
    # 3. Проверить наличие всех релизов
    assert_release_exists "v0.1.0"
    assert_release_exists "v0.1.1"
    assert_release_exists "v0.1.2"
    assert_release_exists "v1.0.1"
    assert_release_exists "v1.0.3"
    assert_release_exists "v2025.11.27.10"
    assert_release_exists "v2025.11.27.11"
    assert_release_exists "v2025.11.27.12"
}
```

**Сценарий 2: Проверка целостности**
```bash
test_integrity_validation() {
    # 1. Восстановить релизы
    bash scripts/restore-releases.sh
    
    # 2. Запустить проверку целостности
    output=$(bash scripts/validate-releases.sh)
    
    # 3. Проверить вывод
    assert_contains "$output" "Semantic releases: 5/5"
    assert_contains "$output" "Date-based releases:"
    assert_contains "$output" "✅ All releases present"
}
```

## Implementation Notes

### Определение коммитов для семантических версий

**Стратегия поиска:**

1. **По сообщению коммита:**
```bash
git log --all --oneline --grep="$version" | head -1
```

2. **По дате из CHANGELOG:**
```bash
# Если в CHANGELOG указана дата 2025-11-XX
git log --all --until="2025-11-30" --since="2025-11-01" --oneline | head -1
```

3. **По изменениям в VERSION файле:**
```bash
git log --all -S"$version" -- VERSION | head -1
```

4. **Ручной ввод:**
```bash
echo "Could not find commit for $version automatically"
echo "Please provide commit SHA manually:"
read commit_sha
```

### Генерация changelog для датированных версий

```bash
generate_changelog_for_tag() {
    local tag=$1
    
    # Найти предыдущий тег
    local prev_tag=$(git describe --tags --abbrev=0 "$tag^" 2>/dev/null)
    
    if [ -z "$prev_tag" ]; then
        # Первый тег, взять все коммиты до него
        git log --oneline "$tag" --format="- %s (%h)"
    else
        # Коммиты между предыдущим и текущим тегом
        git log --oneline "$prev_tag..$tag" --format="- %s (%h)"
    fi
}
```

### Форматирование даты из тега

```bash
date_from_tag() {
    local tag=$1
    # v2025.11.27.10 -> 2025-11-27
    echo "$tag" | sed -E 's/v([0-9]{4})\.([0-9]{1,2})\.([0-9]{1,2})\..*/\1-\2-\3/' | \
        awk -F'-' '{printf "%s-%02d-%02d\n", $1, $2, $3}'
}
```

## Deployment

### Предварительные требования

1. **GitHub CLI (gh):**
```bash
gh --version  # >= 2.0.0
gh auth status  # Должен быть авторизован
```

2. **Git:**
```bash
git --version  # >= 2.0.0
```

3. **Права доступа:**
- `contents: write` - для создания тегов
- `workflow` - для создания релизов

### Запуск восстановления

```bash
# 1. Восстановить все релизы
bash scripts/restore-releases.sh

# 2. Проверить целостность
bash scripts/validate-releases.sh

# 3. Просмотреть отчёт
cat restore-releases.log
```

### Откат

Если нужно удалить восстановленные релизы:

```bash
# Удалить конкретный релиз
gh release delete v0.1.0 --yes

# Удалить тег
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
```

## Security Considerations

1. **GitHub Token:** Скрипт использует `gh` CLI, который требует авторизации. Токен должен иметь минимальные необходимые права.

2. **Валидация входных данных:** Все версии из CHANGELOG.md должны валидироваться перед использованием.

3. **Rate Limiting:** GitHub API имеет лимиты. Скрипт должен обрабатывать ошибки rate limit и делать retry с задержкой.

4. **Audit Log:** Все действия должны логироваться для возможности аудита.
