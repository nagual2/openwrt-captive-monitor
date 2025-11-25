# Документ проектирования

## Обзор

Данный документ описывает техническое решение для автоматической отмены старых запущенных GitHub Actions workflow при мерже в main или запуске новой сборки. Решение основано на встроенном механизме GitHub Actions `concurrency` с настройкой `cancel-in-progress`.

### Текущее состояние

Анализ существующих workflow показал:

**Workflow с настроенным concurrency (7 из 10):**
- `auto-version-tag.yml` - cancel-in-progress: false
- `build-sdk-images.yml` - cancel-in-progress: false  
- `ci.yml` - cancel-in-progress: условно (false для main, true для PR)
- `release-please.yml` - cancel-in-progress: false
- `sdk-simple-build.yml` - cancel-in-progress: true
- `security-scanning.yml` - cancel-in-progress: true
- `tag-build-release.yml` - cancel-in-progress: false

**Workflow БЕЗ concurrency (3 из 10):**
- `build-simple.yml` - триггеры: tags, workflow_dispatch
- `cleanup.yml` - триггеры: schedule, workflow_dispatch
- `upload-sdk-to-release.yml` - триггер: workflow_dispatch

### Цели проектирования

1. Добавить concurrency настройки в оставшиеся 3 workflow
2. Стандартизировать формат concurrency groups во всех workflow
3. Добавить документирующие комментарии для каждой concurrency секции
4. Обеспечить правильную политику отмены для разных типов workflow

## Архитектура

### Механизм Concurrency в GitHub Actions

GitHub Actions предоставляет встроенный механизм управления параллельным выполнением через секцию `concurrency`:

```yaml
concurrency:
  group: <unique-group-identifier>
  cancel-in-progress: <true|false>
```

**Параметры:**
- `group` - уникальный идентификатор группы workflow, которые не должны выполняться одновременно
- `cancel-in-progress` - флаг автоматической отмены предыдущих запусков в той же группе

**Поведение:**
- Когда новый workflow запускается, GitHub проверяет его concurrency group
- Если в этой группе уже выполняется workflow и `cancel-in-progress: true`, старый workflow отменяется
- Если `cancel-in-progress: false`, новый workflow ждет завершения предыдущего

### Стратегия группировки

Для обеспечения правильной изоляции используется следующая формула для concurrency group:

```yaml
group: ${{ github.workflow }}-${{ github.ref }}
```

**Компоненты:**
- `github.workflow` - имя workflow (уникально для каждого файла)
- `github.ref` - полная ссылка на ветку/тег/PR

**Преимущества:**
- Изоляция между разными workflow
- Изоляция между разными ветками/PR
- Workflow для main не отменяют workflow для PR и наоборот


## Компоненты и интерфейсы

### Матрица политик отмены

| Workflow | Триггеры | cancel-in-progress | Обоснование |
|----------|----------|-------------------|-------------|
| ci.yml | push (main), pull_request | условно | Уже настроено. Отменяет для PR, сохраняет для main |
| sdk-simple-build.yml | push (main), pull_request | true | Уже настроено. Быстрая обратная связь для PR |
| security-scanning.yml | push, pull_request, schedule | true | Уже настроено. Отменяет устаревшие сканирования |
| build-sdk-images.yml | push (main), workflow_dispatch, schedule | false | Уже настроено. Долгие сборки образов не отменяются |
| tag-build-release.yml | push (tags) | false | Уже настроено. Релизные сборки критичны |
| release-please.yml | push (main), workflow_dispatch | false | Уже настроено. Создание релизов не отменяется |
| auto-version-tag.yml | push (main) | false | Уже настроено. Версионирование не отменяется |
| **build-simple.yml** | push (tags), workflow_dispatch | **false** | Нужно добавить. Релизные сборки |
| **cleanup.yml** | schedule, workflow_dispatch | **false** | Нужно добавить. Очистка должна завершиться |
| **upload-sdk-to-release.yml** | workflow_dispatch | **false** | Нужно добавить. Загрузка SDK критична |

### Правила выбора политики

**cancel-in-progress: true** - использовать когда:
- Workflow запускается часто (при каждом коммите в PR)
- Результаты предыдущего запуска становятся неактуальными
- Workflow выполняется быстро (< 10 минут)
- Примеры: lint, test, security scanning для PR

**cancel-in-progress: false** - использовать когда:
- Workflow создает критичные артефакты (релизы, Docker образы)
- Workflow выполняется долго (> 10 минут)
- Workflow запускается по тегам или schedule
- Workflow изменяет состояние (создает релизы, теги, загружает артефакты)
- Примеры: release builds, Docker image builds, cleanup, version tagging

## Модели данных

### Структура concurrency секции

```yaml
# Concurrency control: <краткое описание политики>
# - Group: <объяснение формулы группы>
# - Cancel policy: <объяснение значения cancel-in-progress>
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: <true|false|expression>
```

### Примеры для разных сценариев

#### 1. Workflow для PR с отменой

```yaml
# Concurrency control: Cancel previous runs for the same PR to save resources
# - Group: Isolated per workflow and branch/PR
# - Cancel policy: true for PRs to get fast feedback on latest changes
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

#### 2. Workflow для релизов без отмены

```yaml
# Concurrency control: Never cancel release builds to ensure all artifacts are created
# - Group: Isolated per workflow and tag
# - Cancel policy: false to guarantee completion of release builds
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false
```

#### 3. Условная отмена (main vs PR)

```yaml
# Concurrency control: Cancel for PRs, preserve for main branch
# - Group: Isolated per workflow and branch/PR
# - Cancel policy: true for PRs (fast feedback), false for main (preserve history)
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```


## Свойства корректности

*Свойство - это характеристика или поведение, которое должно выполняться во всех допустимых выполнениях системы - по сути, формальное утверждение о том, что система должна делать. Свойства служат мостом между человекочитаемыми спецификациями и машинно-проверяемыми гарантиями корректности.*

### Свойство 1: Все workflow имеют concurrency секцию

*Для любого* workflow файла в `.github/workflows/`, файл должен содержать секцию `concurrency` с определенными `group` и `cancel-in-progress`

**Проверяет: Требования 3.1**

### Свойство 2: Concurrency group использует стандартный формат

*Для любого* workflow файла, concurrency group должен соответствовать формату `${{ github.workflow }}-${{ github.ref }}`

**Проверяет: Требования 3.2**

### Свойство 3: Релизные workflow не отменяются

*Для любого* workflow с триггером `push: tags:`, значение `cancel-in-progress` должно быть `false`

**Проверяет: Требования 4.1**

### Свойство 4: PR workflow отменяются

*Для любого* workflow с триггером `pull_request`, значение `cancel-in-progress` должно быть `true` или условным выражением, возвращающим `true` для PR

**Проверяет: Требования 6.1**

### Свойство 5: Критичные workflow не отменяются

*Для любого* workflow из списка критичных (`build-sdk-images`, `release-please`, `tag-build-release`, `build-simple`, `cleanup`, `upload-sdk-to-release`), значение `cancel-in-progress` должно быть `false`

**Проверяет: Требования 5.1, 8.1**

### Свойство 6: Concurrency секции документированы

*Для любого* workflow файла, перед секцией `concurrency` должен быть комментарий, объясняющий политику отмены

**Проверяет: Требования 10.1, 10.2, 10.3**

## Обработка ошибок

### Сценарии ошибок

1. **Неправильный формат concurrency group**
   - Обнаружение: Статический анализ YAML файлов
   - Обработка: Тесты должны провалиться, указав на неправильный формат
   - Восстановление: Исправить формат группы в workflow файле

2. **Отсутствие concurrency секции**
   - Обнаружение: Проверка наличия секции во всех workflow
   - Обработка: Тест должен провалиться, указав на отсутствующий файл
   - Восстановление: Добавить concurrency секцию

3. **Неправильная политика отмены для критичных workflow**
   - Обнаружение: Проверка значения cancel-in-progress для релизных workflow
   - Обработка: Тест должен провалиться с объяснением риска
   - Восстановление: Изменить cancel-in-progress на false

4. **Отсутствие документации**
   - Обнаружение: Проверка наличия комментариев перед concurrency
   - Обработка: Тест должен провалиться, указав на недокументированный workflow
   - Восстановление: Добавить объясняющие комментарии

### Граничные случаи

1. **Workflow с несколькими триггерами**
   - Решение: Использовать условное выражение для cancel-in-progress
   - Пример: `${{ github.ref != 'refs/heads/main' }}` для push и pull_request

2. **Workflow только с workflow_dispatch**
   - Решение: cancel-in-progress: false
   - Обоснование: Каждый ручной запуск должен выполниться

3. **Workflow с schedule триггером**
   - Решение: cancel-in-progress: false
   - Обоснование: Запланированные задачи должны завершиться


## Стратегия тестирования

### Unit тесты

Не применимы, так как мы не пишем исполняемый код, а конфигурируем YAML файлы.

### Property-Based тесты

Будут использоваться для проверки корректности конфигурации всех workflow файлов.

**Библиотека:** Для тестирования YAML конфигурации будем использовать комбинацию:
- **Python** с библиотекой **Hypothesis** для property-based testing
- **PyYAML** для парсинга YAML файлов
- **pytest** как test runner

**Обоснование выбора:**
- Python хорошо подходит для работы с YAML
- Hypothesis - зрелая библиотека для PBT в Python
- Легко интегрируется в CI/CD pipeline

**Конфигурация:**
- Каждый property-based тест будет запускаться минимум 100 итераций
- Тесты будут проверять все workflow файлы в `.github/workflows/`
- Каждый тест будет помечен комментарием с ссылкой на свойство из design.md

### Интеграционные тесты

Интеграционные тесты не требуются, так как:
- Поведение concurrency полностью контролируется GitHub Actions
- Мы можем проверить корректность конфигурации статически
- Реальное поведение можно наблюдать в GitHub Actions UI после деплоя

### Стратегия валидации

1. **Статическая валидация YAML**
   - Проверка синтаксиса YAML
   - Проверка наличия обязательных полей
   - Проверка типов значений

2. **Property-based валидация**
   - Проверка всех 6 свойств корректности
   - Автоматическое обнаружение всех workflow файлов
   - Генерация отчета о соответствии

3. **Ручная валидация**
   - Проверка в GitHub Actions UI после деплоя
   - Тестирование реального поведения отмены
   - Проверка логов отмененных workflow

## Зависимости

### Внешние зависимости

- **GitHub Actions Platform** - предоставляет механизм concurrency
- **Python 3.8+** - для запуска property-based тестов
- **PyYAML** - для парсинга workflow файлов
- **Hypothesis** - для property-based testing
- **pytest** - для запуска тестов

### Внутренние зависимости

- Все workflow файлы в `.github/workflows/`
- Существующая CI/CD инфраструктура
- Документация проекта

## Риски и ограничения

### Риски

1. **Случайная отмена критичных workflow**
   - Вероятность: Низкая
   - Воздействие: Высокое
   - Митигация: Property-based тесты проверяют политику для критичных workflow

2. **Неправильная изоляция между PR**
   - Вероятность: Низкая
   - Воздействие: Среднее
   - Митигация: Тесты проверяют формат concurrency group

### Ограничения

1. **Платформенные ограничения**
   - Поведение concurrency полностью контролируется GitHub Actions
   - Мы не можем изменить логику отмены, только настроить её
   - Нет способа протестировать реальное поведение без деплоя

2. **Ограничения тестирования**
   - Property-based тесты проверяют только конфигурацию, не поведение
   - Реальное поведение можно проверить только в GitHub Actions
   - Нет способа автоматически тестировать UI и логи

3. **Обратная совместимость**
   - Изменения не влияют на существующую функциональность
   - Все workflow продолжат работать как раньше
   - Добавление concurrency только улучшает управление ресурсами
