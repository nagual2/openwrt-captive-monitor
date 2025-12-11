# Manual Release Workflow

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

## Overview

The Manual Release workflow provides maintainers with full control over when and how releases are created. This workflow replaced the automatic release-on-push system to prevent unintended releases and give better control over versioning.

## Accessing the Workflow

1. Navigate to the repository on GitHub
2. Click on the **Actions** tab
3. Select **Manual Release** from the workflow list
4. Click **Run workflow** button

## Workflow Parameters

The Manual Release workflow accepts three optional parameters:

### 1. Custom Version

- **Parameter name**: `version`
- **Type**: String
- **Required**: No
- **Default**: Auto-generated based on current date

**Description**: Specify a custom version for the release in the format `YYYY.M.D.N` (without the `v` prefix).

**Examples**:
- `2025.11.27.1` - First release on November 27, 2025
- `2025.11.27.2` - Second release on the same day
- `2025.12.1.1` - First release on December 1, 2025

**Auto-generation**: If left empty, the workflow will automatically generate a version based on:
- Current year, month, and day
- Sequential number for releases on the same day (starting from 1)

**Validation**: The workflow checks if the tag already exists and will fail if it does.

### 2. Release Notes

- **Parameter name**: `release_notes`
- **Type**: String (multi-line)
- **Required**: No
- **Default**: Auto-generated from git commits

**Description**: Provide custom release notes to describe what's included in this release.

**Auto-generation**: If left empty, the workflow will automatically generate release notes containing:
- Release version and timestamp
- List of commits since the previous release
- Commit messages in chronological order

**Best practices**:
- Highlight major features or bug fixes
- Include breaking changes if any
- Reference related issues or PRs
- Keep it concise and user-focused

**Example**:
```markdown
## What's New

- Added support for nftables backend
- Improved captive portal detection
- Improved error handling in monitor mode

## Bug Fixes

- Fixed issue #123: Service fails to start on OpenWrt 23.05
- Resolved memory leak in continuous monitoring mode

## Breaking Changes

None
```

### 3. Pre-release Flag

- **Parameter name**: `prerelease`
- **Type**: Boolean (checkbox)
- **Required**: No
- **Default**: `false`

**Description**: Mark this release as a pre-release (beta, RC, etc.).

**Effects**:
- Release will be marked with a "Pre-release" badge on GitHub
- Will not be marked as "Latest" release
- Users can opt-in to pre-releases if they want to test new features

**When to use**:
- Testing new features before stable release
- Release candidates (RC)
- Beta versions
- Experimental builds

## Workflow Steps

When you run the Manual Release workflow, it performs the following steps:

### 1. Version Determination

- Uses custom version if provided
- Otherwise, generates version from current date
- Checks if tag already exists
- Finds previous release tag for release notes

### 2. Metadata Update

- Updates `VERSION` file with new version
- Updates `PKG_VERSION` in `package/openwrt-captive-monitor/Makefile`
- Sets `PKG_RELEASE` to `1`
- Verifies changes were made correctly

### 3. Git Operations

- Configures git with bot credentials
- Stages version changes
- Creates commit with message: `chore: bump version to X.Y.Z.N`
- Pushes commit to `main` branch
- Creates annotated git tag
- Pushes tag to remote

### 4. Package Build

- Sets up opkg-utils
- Builds universal package (`arch=all`)
- Validates package structure
- Verifies version in package matches expected version
- Stages artifacts for release

### 5. Release Creation

- Generates or uses custom release notes
- Creates GitHub Release
- Uploads `.ipk` package file
- Uploads `SHA256SUMS` file
- Marks as latest or pre-release based on flag

## Version Format

All releases follow the date-based version format:

**Format**: `vYYYY.M.D.N`

Where:
- `YYYY` - Four-digit year (e.g., 2025)
- `M` - Month without leading zero (1-12)
- `D` - Day without leading zero (1-31)
- `N` - Sequential number for releases on the same day (starting from 1)

**Examples**:
- `v2025.11.27.1` - First release on November 27, 2025
- `v2025.11.27.2` - Second release on the same day
- `v2025.12.1.1` - First release on December 1, 2025

**File versions** (without `v` prefix):
- `VERSION` file: `2025.11.27.1`
- `PKG_VERSION` in Makefile: `2025.11.27.1`
- `PKG_RELEASE` in Makefile: `1`

## Usage Examples

### Example 1: Standard Release with Auto-generated Version

1. Go to Actions → Manual Release
2. Click "Run workflow"
3. Leave all fields empty
4. Click "Run workflow"

**Result**: Creates a release with auto-generated version (e.g., `v2025.11.27.1`) and automatic release notes.

### Example 2: Release with Custom Notes

1. Go to Actions → Manual Release
2. Click "Run workflow"
3. Leave version empty
4. Enter custom release notes:
   ```
   ## New Features
   - Added nftables support
   - Improved captive portal detection
   
   ## Bug Fixes
   - Fixed memory leak in monitor mode
   ```
5. Click "Run workflow"

**Result**: Creates a release with auto-generated version but custom release notes.

### Example 3: Pre-release with Custom Version

1. Go to Actions → Manual Release
2. Click "Run workflow"
3. Enter custom version: `2025.12.1.1`
4. Enter release notes describing beta features
5. Check "Mark as pre-release"
6. Click "Run workflow"

**Result**: Creates a pre-release with version `v2025.12.1.1` and custom notes.

### Example 4: Hotfix Release

1. Ensure hotfix is merged to `main`
2. Go to Actions → Manual Release
3. Click "Run workflow"
4. Enter version with incremented sequence number (e.g., `2025.11.27.2`)
5. Enter release notes describing the fix
6. Click "Run workflow"

**Result**: Creates a hotfix release on the same day as a previous release.

## Troubleshooting

### Error: Tag already exists

**Cause**: The version tag you specified (or auto-generated) already exists in the repository.

**Solution**:
- If using custom version, increment the sequence number (e.g., change `2025.11.27.1` to `2025.11.27.2`)
- If using auto-generation, the workflow should handle this automatically
- Check existing tags: `git tag -l "v2025.11.27.*"`

### Error: No metadata changes detected

**Cause**: The `VERSION` file and Makefile already contain the target version.

**Solution**:
- Verify you're not trying to re-release an existing version
- Check if a previous workflow run partially completed
- Manually verify `VERSION` file and Makefile content

### Error: Package validation failed

**Cause**: The built package doesn't meet validation requirements.

**Solution**:
- Check the workflow logs for specific validation errors
- Verify package structure is correct
- Ensure all required files are present in the package

### Error: Failed to create GitHub Release

**Cause**: GitHub API error or permission issue.

**Solution**:
- Check if the tag was created successfully
- Verify workflow has `contents: write` permission
- Check GitHub status page for API issues
- If tag exists but release doesn't, create release manually from the tag

## Best Practices

### When to Create a Release

✅ **Do create a release when**:
- Merging a significant feature
- Fixing critical bugs
- Reaching a milestone
- Preparing for user testing (pre-release)

❌ **Don't create a release for**:
- Every commit to main
- Work-in-progress features
- Documentation-only changes
- CI/CD configuration updates

### Release Notes Guidelines

1. **Be user-focused**: Describe changes from user perspective
2. **Categorize changes**: Use sections like "New Features", "Bug Fixes", "Breaking Changes"
3. **Reference issues**: Link to relevant GitHub issues or PRs
4. **Keep it concise**: Users should quickly understand what changed
5. **Highlight breaking changes**: Make them prominent and clear

### Version Numbering

1. **Use auto-generation** for most releases
2. **Use custom version** only when:
   - Creating multiple releases on the same day
   - Creating a hotfix for a specific date
   - Following a specific version scheme for compatibility

### Pre-releases

1. **Use pre-releases** for:
   - Beta testing new features
   - Release candidates
   - Experimental builds
2. **Don't use pre-releases** for:
   - Stable production releases
   - Hotfixes for production issues

## Security Considerations

- The workflow uses `github-actions[bot]` for git operations
- Requires `contents: write` permission
- Only maintainers with write access can trigger the workflow
- All operations are logged and auditable
- Package checksums (SHA256SUMS) are automatically generated

## Related Documentation

- [Release Process](RELEASE_PROCESS.md) - Historical semantic versioning process
- [Auto Version Tag](AUTO_VERSION_TAG.md) - Automatic version tagging (deprecated)
- [Contributing Guide](../contributing/CONTRIBUTING.md) - How to contribute to the project
- [Workflow File](.github/workflows/manual-release.yml) - Workflow source code

---

## Русский

---

## 🌐 Язык

[English](#manual-release-workflow) | **Русский**

---

## Обзор

Workflow Manual Release предоставляет мейнтейнерам полный контроль над тем, когда и как создаются релизы. Этот workflow заменил систему автоматического релиза при push, чтобы предотвратить непреднамеренные релизы и обеспечить лучший контроль над версионированием.

## Доступ к Workflow

1. Перейдите в репозиторий на GitHub
2. Нажмите на вкладку **Actions**
3. Выберите **Manual Release** из списка workflow
4. Нажмите кнопку **Run workflow**

## Параметры Workflow

Workflow Manual Release принимает три опциональных параметра:

### 1. Пользовательская версия

- **Имя параметра**: `version`
- **Тип**: Строка
- **Обязательный**: Нет
- **По умолчанию**: Автогенерация на основе текущей даты

**Описание**: Укажите пользовательскую версию для релиза в формате `YYYY.M.D.N` (без префикса `v`).

**Примеры**:
- `2025.11.27.1` - Первый релиз 27 ноября 2025
- `2025.11.27.2` - Второй релиз в тот же день
- `2025.12.1.1` - Первый релиз 1 декабря 2025

**Автогенерация**: Если оставить пустым, workflow автоматически сгенерирует версию на основе:
- Текущего года, месяца и дня
- Порядкового номера для релизов в один день (начиная с 1)

**Валидация**: Workflow проверяет, существует ли уже тег, и завершится с ошибкой, если существует.

### 2. Примечания к релизу

- **Имя параметра**: `release_notes`
- **Тип**: Строка (многострочная)
- **Обязательный**: Нет
- **По умолчанию**: Автогенерация из git коммитов

**Описание**: Предоставьте пользовательские примечания к релизу, описывающие что включено в этот релиз.

**Автогенерация**: Если оставить пустым, workflow автоматически сгенерирует примечания, содержащие:
- Версию релиза и временную метку
- Список коммитов с предыдущего релиза
- Сообщения коммитов в хронологическом порядке

**Лучшие практики**:
- Выделите основные функции или исправления ошибок
- Включите критические изменения, если есть
- Ссылайтесь на связанные issues или PR
- Будьте краткими и ориентированными на пользователя

**Пример**:
```markdown
## Что нового

- Добавлена поддержка nftables backend
- Улучшено обнаружение captive portal
- Улучшена обработка ошибок в режиме монитора

## Исправления ошибок

- Исправлена проблема #123: Сервис не запускается на OpenWrt 23.05
- Устранена утечка памяти в режиме непрерывного мониторинга

## Критические изменения

Нет
```

### 3. Флаг предварительного релиза

- **Имя параметра**: `prerelease`
- **Тип**: Boolean (чекбокс)
- **Обязательный**: Нет
- **По умолчанию**: `false`

**Описание**: Пометить этот релиз как предварительный (beta, RC и т.д.).

**Эффекты**:
- Релиз будет помечен значком "Pre-release" на GitHub
- Не будет помечен как "Latest" релиз
- Пользователи могут выбрать предварительные релизы, если хотят протестировать новые функции

**Когда использовать**:
- Тестирование новых функций перед стабильным релизом
- Кандидаты на релиз (RC)
- Бета-версии
- Экспериментальные сборки

## Шаги Workflow

Когда вы запускаете workflow Manual Release, он выполняет следующие шаги:

### 1. Определение версии

- Использует пользовательскую версию, если указана
- Иначе генерирует версию из текущей даты
- Проверяет, существует ли уже тег
- Находит предыдущий тег релиза для примечаний

### 2. Обновление метаданных

- Обновляет файл `VERSION` новой версией
- Обновляет `PKG_VERSION` в `package/openwrt-captive-monitor/Makefile`
- Устанавливает `PKG_RELEASE` в `1`
- Проверяет, что изменения сделаны корректно

### 3. Git операции

- Настраивает git с учетными данными бота
- Добавляет изменения версии в stage
- Создает коммит с сообщением: `chore: bump version to X.Y.Z.N`
- Отправляет коммит в ветку `main`
- Создает аннотированный git тег
- Отправляет тег на удаленный сервер

### 4. Сборка пакета

- Настраивает opkg-utils
- Собирает универсальный пакет (`arch=all`)
- Валидирует структуру пакета
- Проверяет, что версия в пакете соответствует ожидаемой
- Подготавливает артефакты для релиза

### 5. Создание релиза

- Генерирует или использует пользовательские примечания
- Создает GitHub Release
- Загружает файл пакета `.ipk`
- Загружает файл `SHA256SUMS`
- Помечает как latest или pre-release на основе флага

## Формат версии

Все релизы следуют формату версии на основе даты:

**Формат**: `vYYYY.M.D.N`

Где:
- `YYYY` - Четырехзначный год (например, 2025)
- `M` - Месяц без ведущего нуля (1-12)
- `D` - День без ведущего нуля (1-31)
- `N` - Порядковый номер для релизов в один день (начиная с 1)

**Примеры**:
- `v2025.11.27.1` - Первый релиз 27 ноября 2025
- `v2025.11.27.2` - Второй релиз в тот же день
- `v2025.12.1.1` - Первый релиз 1 декабря 2025

**Версии в файлах** (без префикса `v`):
- Файл `VERSION`: `2025.11.27.1`
- `PKG_VERSION` в Makefile: `2025.11.27.1`
- `PKG_RELEASE` в Makefile: `1`

## Примеры использования

### Пример 1: Стандартный релиз с автогенерацией версии

1. Перейдите в Actions → Manual Release
2. Нажмите "Run workflow"
3. Оставьте все поля пустыми
4. Нажмите "Run workflow"

**Результат**: Создается релиз с автогенерированной версией (например, `v2025.11.27.1`) и автоматическими примечаниями.

### Пример 2: Релиз с пользовательскими примечаниями

1. Перейдите в Actions → Manual Release
2. Нажмите "Run workflow"
3. Оставьте версию пустой
4. Введите пользовательские примечания:
   ```
   ## Новые функции
   - Добавлена поддержка nftables
   - Улучшено обнаружение captive portal
   
   ## Исправления ошибок
   - Исправлена утечка памяти в режиме монитора
   ```
5. Нажмите "Run workflow"

**Результат**: Создается релиз с автогенерированной версией, но пользовательскими примечаниями.

### Пример 3: Предварительный релиз с пользовательской версией

1. Перейдите в Actions → Manual Release
2. Нажмите "Run workflow"
3. Введите пользовательскую версию: `2025.12.1.1`
4. Введите примечания, описывающие бета-функции
5. Отметьте "Mark as pre-release"
6. Нажмите "Run workflow"

**Результат**: Создается предварительный релиз с версией `v2025.12.1.1` и пользовательскими примечаниями.

### Пример 4: Hotfix релиз

1. Убедитесь, что hotfix слит в `main`
2. Перейдите в Actions → Manual Release
3. Нажмите "Run workflow"
4. Введите версию с увеличенным порядковым номером (например, `2025.11.27.2`)
5. Введите примечания, описывающие исправление
6. Нажмите "Run workflow"

**Результат**: Создается hotfix релиз в тот же день, что и предыдущий релиз.

## Устранение неполадок

### Ошибка: Tag already exists

**Причина**: Тег версии, который вы указали (или автогенерированный), уже существует в репозитории.

**Решение**:
- Если используете пользовательскую версию, увеличьте порядковый номер (например, измените `2025.11.27.1` на `2025.11.27.2`)
- Если используете автогенерацию, workflow должен обработать это автоматически
- Проверьте существующие теги: `git tag -l "v2025.11.27.*"`

### Ошибка: No metadata changes detected

**Причина**: Файл `VERSION` и Makefile уже содержат целевую версию.

**Решение**:
- Проверьте, что вы не пытаетесь повторно выпустить существующую версию
- Проверьте, не завершился ли предыдущий запуск workflow частично
- Вручную проверьте содержимое файла `VERSION` и Makefile

### Ошибка: Package validation failed

**Причина**: Собранный пакет не соответствует требованиям валидации.

**Решение**:
- Проверьте логи workflow на наличие конкретных ошибок валидации
- Проверьте, что структура пакета корректна
- Убедитесь, что все необходимые файлы присутствуют в пакете

### Ошибка: Failed to create GitHub Release

**Причина**: Ошибка GitHub API или проблема с правами доступа.

**Решение**:
- Проверьте, был ли тег создан успешно
- Проверьте, что workflow имеет разрешение `contents: write`
- Проверьте страницу статуса GitHub на наличие проблем с API
- Если тег существует, но релиза нет, создайте релиз вручную из тега

## Лучшие практики

### Когда создавать релиз

✅ **Создавайте релиз когда**:
- Сливаете значительную функцию
- Исправляете критические ошибки
- Достигаете вехи
- Готовитесь к пользовательскому тестированию (предварительный релиз)

❌ **Не создавайте релиз для**:
- Каждого коммита в main
- Незавершенных функций
- Изменений только в документации
- Обновлений конфигурации CI/CD

### Рекомендации по примечаниям к релизу

1. **Ориентируйтесь на пользователя**: Описывайте изменения с точки зрения пользователя
2. **Категоризируйте изменения**: Используйте разделы вроде "Новые функции", "Исправления ошибок", "Критические изменения"
3. **Ссылайтесь на issues**: Ссылайтесь на соответствующие GitHub issues или PR
4. **Будьте краткими**: Пользователи должны быстро понять, что изменилось
5. **Выделяйте критические изменения**: Сделайте их заметными и понятными

### Нумерация версий

1. **Используйте автогенерацию** для большинства релизов
2. **Используйте пользовательскую версию** только когда:
   - Создаете несколько релизов в один день
   - Создаете hotfix для конкретной даты
   - Следуете определенной схеме версионирования для совместимости

### Предварительные релизы

1. **Используйте предварительные релизы** для:
   - Бета-тестирования новых функций
   - Кандидатов на релиз
   - Экспериментальных сборок
2. **Не используйте предварительные релизы** для:
   - Стабильных продакшн релизов
   - Hotfix'ов для продакшн проблем

## Соображения безопасности

- Workflow использует `github-actions[bot]` для git операций
- Требует разрешение `contents: write`
- Только мейнтейнеры с правами записи могут запускать workflow
- Все операции логируются и проверяемы
- Контрольные суммы пакетов (SHA256SUMS) генерируются автоматически

## Связанная документация

- [Процесс релиза](RELEASE_PROCESS.md) - Исторический процесс семантического версионирования
- [Auto Version Tag](AUTO_VERSION_TAG.md) - Автоматическое создание тегов версий (устарело)
- [Руководство по вкладу](../contributing/CONTRIBUTING.md) - Как внести вклад в проект
- [Файл Workflow](.github/workflows/manual-release.yml) - Исходный код workflow
