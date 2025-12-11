# Design Document

## Overview

Переход от автоматического создания релизов при каждом коммите в main на ручной процесс, где разработчик явно инициирует создание релиза через GitHub Actions workflow_dispatch. Это обеспечит больший контроль над версионированием и уменьшит количество избыточных релизов.

## Architecture

### Текущая архитектура

```
Push to main → auto-version-tag.yml → Create tag → tag-build-release.yml → Build with SDK → Publish release
```

### Новая архитектура

```
Manual trigger → manual-release.yml → Update VERSION → Commit → Create tag → Build without SDK → Publish release
```

## Components and Interfaces

### 1. Manual Release Workflow (manual-release.yml)

**Входные параметры:**
- `version` (optional): Кастомная версия в формате YYYY.M.D.N
- `release_notes` (optional): Описание релиза
- `prerelease` (optional): Отметить как pre-release

**Выходные данные:**
- Обновленный VERSION файл
- Обновленный Makefile
- Git тег
- GitHub Release с прикрепленным .ipk пакетом

### 2. Version Management Module

**Функции:**
- `generate_version()`: Генерирует версию на основе текущей даты
- `update_version_file()`: Обновляет VERSION файл
- `update_makefile()`: Обновляет PKG_VERSION в Makefile
- `create_version_commit()`: Создает коммит с обновлениями версии

### 3. Build Module

**Функции:**
- `build_package()`: Собирает универсальный пакет без SDK
- `validate_package()`: Проверяет корректность пакета
- `stage_artifacts()`: Подготавливает артефакты для публикации

### 4. Release Module

**Функции:**
- `create_github_release()`: Создает релиз на GitHub
- `upload_assets()`: Загружает пакет и SHA256SUMS
- `generate_release_notes()`: Генерирует автоматические release notes

## Data Models

### Version Format

```
YYYY.M.D.N
где:
- YYYY: год (4 цифры)
- M: месяц (1-2 цифры)
- D: день (1-2 цифры)
- N: порядковый номер релиза за день (начинается с 1)
```

### Release Metadata

```yaml
tag: v2025.11.27.1
version: 2025.11.27.1
commit_sha: abc123def
release_notes: "Manual release with bug fixes"
prerelease: false
assets:
  - openwrt-captive-monitor_2025.11.27.1-1_all.ipk
  - SHA256SUMS
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Version uniqueness

*For any* manual release execution, the generated version tag should not already exist in the repository
**Validates: Requirements 1.1**

### Property 2: Version file consistency

*For any* release, the VERSION file content should match the PKG_VERSION in Makefile
**Validates: Requirements 2.1, 2.2**

### Property 3: Commit before tag

*For any* release, the version update commit should be created before the tag is created
**Validates: Requirements 2.3, 2.4**

### Property 4: No automatic releases

*For any* push to main branch (without manual trigger), no release workflow should be automatically triggered
**Validates: Requirements 3.1**

### Property 5: Package architecture

*For any* built package, the architecture field should be "all"
**Validates: Requirements 4.3**

### Property 6: Release asset presence

*For any* published release, it should contain at least one .ipk file and SHA256SUMS file
**Validates: Requirements 4.4**

## Error Handling

### Version Conflicts

**Scenario:** Тег с такой версией уже существует

**Handling:**
1. Проверить существование тега перед созданием
2. Если тег существует, инкрементировать порядковый номер N
3. Повторить проверку до нахождения свободной версии

### Build Failures

**Scenario:** Сборка пакета завершилась с ошибкой

**Handling:**
1. Не создавать коммит и тег
2. Вывести детальные логи ошибки
3. Откатить любые частичные изменения
4. Завершить workflow с ошибкой

### Git Push Failures

**Scenario:** Не удалось запушить коммит или тег

**Handling:**
1. Повторить попытку с exponential backoff (3 попытки)
2. Если все попытки неудачны, вывести ошибку
3. Не создавать GitHub Release без успешного push

### Release Creation Failures

**Scenario:** Не удалось создать GitHub Release

**Handling:**
1. Тег и коммит уже созданы, не откатывать
2. Вывести ошибку с инструкциями для ручного создания релиза
3. Сохранить артефакты для ручной загрузки

## Testing Strategy

### Unit Tests

1. **Version generation tests**
   - Тест генерации версии для текущей даты
   - Тест инкремента порядкового номера
   - Тест парсинга кастомной версии

2. **File update tests**
   - Тест обновления VERSION файла
   - Тест обновления Makefile
   - Тест корректности regex замены

3. **Package build tests**
   - Тест успешной сборки пакета
   - Тест валидации пакета
   - Тест создания SHA256SUMS

### Property-Based Tests

Использовать Hypothesis (Python) для property-based тестирования:

1. **Property 1 test**: Генерировать случайные даты и проверять уникальность версий
2. **Property 2 test**: Генерировать случайные версии и проверять консистентность файлов
3. **Property 5 test**: Проверять arch=all для всех собранных пакетов

### Integration Tests

1. **End-to-end release test**
   - Запустить workflow в тестовом окружении
   - Проверить создание коммита, тега и релиза
   - Проверить наличие артефактов

2. **Rollback test**
   - Симулировать ошибку на разных этапах
   - Проверить корректность отката изменений

## Implementation Notes

### Отключение auto-version-tag workflow

Удалить или закомментировать trigger `push` в `.github/workflows/auto-version-tag.yml`:

```yaml
on:
  # push:  # DISABLED - use manual-release.yml instead
  #   branches:
  #     - main
  workflow_dispatch:  # Keep for manual testing
```

### Использование Simple Release Build

Вместо `tag-build-release.yml` (который использует SDK), использовать логику из `simple-release.yml`:

```yaml
- name: Build package
  run: |
    chmod +x ./scripts/build_ipk.sh
    ./scripts/build_ipk.sh --arch all
```

### Git операции в workflow

```yaml
- name: Configure git
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"

- name: Commit and push
  run: |
    git add VERSION package/openwrt-captive-monitor/Makefile
    git commit -m "chore: bump version to $VERSION"
    git push origin main
    git tag "v$VERSION"
    git push origin "v$VERSION"
```

## Migration Plan

1. **Phase 1: Создание manual-release workflow**
   - Создать новый workflow файл
   - Протестировать на feature ветке
   - Убедиться что все работает корректно

2. **Phase 2: Отключение auto-version**
   - Закомментировать push trigger в auto-version-tag.yml
   - Задокументировать изменение в README
   - Обновить CONTRIBUTING.md с новым процессом

3. **Phase 3: Очистка**
   - Удалить неиспользуемые workflows (tag-build-release.yml)
   - Обновить документацию
   - Создать первый ручной релиз для проверки

## Documentation Updates

### README.md

Добавить секцию "Creating a Release":

```markdown
## Creating a Release

To create a new release:

1. Go to Actions → Manual Release
2. Click "Run workflow"
3. (Optional) Specify custom version or release notes
4. Click "Run workflow"

The workflow will:
- Generate a new version tag
- Update VERSION and Makefile
- Build the package
- Create a GitHub release with the package attached
```

### CONTRIBUTING.md

Обновить секцию о релизах:

```markdown
## Release Process

Releases are created manually by maintainers:

1. Ensure all changes are merged to main
2. Run the "Manual Release" workflow
3. The workflow will automatically:
   - Bump the version
   - Build the package
   - Create a GitHub release

Do not create tags manually - use the workflow.
```
