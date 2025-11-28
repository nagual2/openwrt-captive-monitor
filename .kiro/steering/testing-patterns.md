# Паттерны тестирования

## Property-Based Testing (PBT)

### Общие принципы

Property-Based Testing проверяет универсальные свойства системы на большом количестве автоматически сгенерированных входных данных.

**Когда использовать PBT:**
- Парсеры и сериализаторы (round-trip properties)
- Конфигурационные файлы (YAML, JSON)
- Математические функции (коммутативность, ассоциативность)
- Инварианты системы (размер образа, формат версии)

### Выбор библиотек

**Python + Hypothesis:**
- Для тестирования YAML/JSON конфигураций
- Для валидации workflow файлов GitHub Actions
- Для проверки структуры данных

**bats-core:**
- Для тестирования bash скриптов
- Для проверки CLI инструментов
- Для интеграционных тестов shell команд

### Конфигурация PBT тестов

```python
# Python + Hypothesis
from hypothesis import given, strategies as st, assume
import pytest

@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
def test_property(input_data):
    # Минимум 100 итераций (по умолчанию в Hypothesis)
    assume(len(input_data) > 0)  # Фильтрация невалидных данных
    
    result = function_under_test(input_data)
    
    # Проверка универсального свойства
    assert property_holds(result)
```

**Обязательные настройки:**
- Минимум 100 итераций для каждого теста
- Использование `assume()` для фильтрации невалидных входных данных
- Seed для воспроизводимости: `--hypothesis-seed=12345`

### Стратегии генерации данных

**Для текстовых данных:**
```python
# Только ASCII буквы и цифры
st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))

# С ограничением длины
st.text(min_size=1, max_size=100)

# С фильтрацией
st.text().filter(lambda s: len(s) > 0 and s.strip() == s)
```

**Для структурированных данных:**
```python
# Словари с определенными ключами
st.fixed_dictionaries({
    'version': st.text(regex=r'\d+\.\d+\.\d+'),
    'name': st.text(min_size=1)
})

# Списки с ограничениями
st.lists(st.integers(min_value=0), min_size=1, max_size=10)
```

### Типичные свойства для проверки

**Round-trip properties (парсеры/сериализаторы):**
```python
@given(st.text())
def test_parse_roundtrip(data):
    # parse(serialize(data)) == data
    assert parse(serialize(data)) == data
```

**Инварианты (размер, формат):**
```python
@given(st.text())
def test_size_invariant(data):
    result = process(data)
    assert len(result) <= MAX_SIZE
```

**Идемпотентность:**
```python
@given(st.text())
def test_idempotent(data):
    # f(f(x)) == f(x)
    assert process(process(data)) == process(data)
```

### Формат комментариев в тестах

Каждый property-based тест должен содержать комментарий со ссылкой на свойство из design.md:

```python
def test_docker_image_size():
    """
    Property 4: Image size compliance
    For any built Docker image, the size should be less than 2GB
    
    Validates: Requirements 2.1
    Reference: .kiro/specs/docker-windows-optimization/design.md#property-4
    """
    # Test implementation
```

### Отладка PBT тестов

**Воспроизведение ошибки:**
```bash
# Использовать seed из failed теста
pytest test_properties.py --hypothesis-seed=12345

# Увеличить количество примеров
pytest test_properties.py --hypothesis-max-examples=1000

# Verbose режим
pytest test_properties.py --hypothesis-verbosity=verbose
```

**Анализ counterexample:**
```python
# Hypothesis автоматически минимизирует counterexample
# Пример вывода:
# Falsified after 42 tests
# Counterexample: data='abc\x00def'
```

## Стратегия тестирования в спецификациях

### Три типа тестов

**1. Unit тесты**
- Тестируют отдельные функции/компоненты
- Быстрые (< 1 секунды)
- Изолированные (без внешних зависимостей)
- Используют моки для внешних вызовов

**Когда использовать:**
- Тестирование отдельных функций bash скриптов
- Проверка парсинга аргументов
- Валидация форматирования вывода

**Пример:**
```bash
# tests/unit/test_download_sdk.bats
@test "determine_musl_suffix returns correct suffix for x86/64" {
  SDK_TARGET="x86"
  SDK_SUBTARGET="64"
  
  result=$(determine_musl_suffix)
  
  [ "$result" = "_musl" ]
}
```

**2. Property-Based тесты**
- Проверяют универсальные свойства
- Минимум 100 итераций
- Автоматическая генерация входных данных
- Находят edge cases

**Когда использовать:**
- Проверка инвариантов (размер образа, формат версии)
- Валидация конфигурационных файлов
- Тестирование парсеров/сериализаторов

**Пример:**
```python
# tests/properties/test_workflow_concurrency.py
@given(st.sampled_from(workflow_files))
def test_all_workflows_have_concurrency(workflow_file):
    """Property 1: All workflows have concurrency section"""
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)
    
    assert 'concurrency' in workflow
    assert 'group' in workflow['concurrency']
    assert 'cancel-in-progress' in workflow['concurrency']
```

**3. Integration тесты**
- Тестируют полный цикл работы
- Медленные (минуты)
- Используют реальные зависимости
- Проверяют взаимодействие компонентов

**Когда использовать:**
- Тестирование полной сборки Docker образа
- Проверка workflow в GitHub Actions
- Валидация установки пакета на OpenWrt

**Пример:**
```bash
# tests/integration/test_docker_build.bats
@test "Docker image builds successfully for x86/64" {
  docker build \
    --build-arg OPENWRT_VERSION=23.05.5 \
    --build-arg SDK_TARGET=x86 \
    --build-arg SDK_SUBTARGET=64 \
    -t test-sdk:local \
    -f docker/sdk/Dockerfile \
    .
  
  [ $? -eq 0 ]
}
```

### Матрица выбора типа теста

| Что тестируем | Unit | Property-Based | Integration |
|---------------|------|----------------|-------------|
| Отдельная функция | ✅ | ❌ | ❌ |
| Универсальное свойство | ❌ | ✅ | ❌ |
| Конфигурация | ❌ | ✅ | ❌ |
| Полный цикл | ❌ | ❌ | ✅ |
| Edge cases | ⚠️ | ✅ | ❌ |
| Взаимодействие компонентов | ❌ | ❌ | ✅ |

### Checkpoints в спецификациях

**Что такое checkpoint:**
- Специальная задача для валидации прогресса
- Проверяет работоспособность перед переходом к следующему этапу
- Не добавляет новую функциональность, только проверяет существующую

**Когда добавлять checkpoint:**
- После реализации критичной функциональности
- Перед началом следующего крупного этапа
- После изменений, которые могут сломать существующую функциональность

**Примеры checkpoint задач:**

```markdown
## Задачи

### Задача 1: Оптимизация Dockerfile
- Объединить RUN команды
- Добавить очистку кэшей
- _Requirements: 2.1, 2.2_

### Задача 2: Checkpoint - проверка размера образа
- Собрать образ локально
- Проверить размер < 2GB
- Проверить работоспособность SDK
- _Validates: Task 1_

### Задача 3: Добавление валидационных скриптов
- Создать validate-docker-image-size.sh
- Создать validate-docker-image-contents.sh
- _Requirements: 3.1, 6.1_
```

## Act - локальное тестирование GitHub Actions

### Основные команды

**Список workflow:**
```bash
act --list
```

**Dry-run (без выполнения):**
```bash
# Проверить что workflow запустится
act -W .github/workflows/ci.yml --job lint -n

# Проверить все jobs
act -W .github/workflows/ci.yml -n
```

**Запуск workflow:**
```bash
# Запустить конкретный job
act -W .github/workflows/ci.yml --job lint

# Запустить весь workflow
act -W .github/workflows/ci.yml
```

**Запуск с matrix параметром:**
```bash
# Запустить для конкретного значения matrix
act -W .github/workflows/ci.yml --job lint --matrix linter:shellcheck
```

### Полезные опции

**Управление образами:**
```bash
# Не загружать образы (использовать локальные)
act --pull=false

# Переиспользовать контейнеры
act --reuse
```

**Отладка:**
```bash
# Интерактивный режим (остановка при ошибке)
act --interactive

# Максимальная детализация
act --verbose

# Тихий режим (только ошибки)
act --quiet
```

**Переменные окружения и секреты:**
```bash
# Загрузить переменные из файла
act --env-file .env.local

# Загрузить секреты из файла
act --secret-file .secrets

# Установить переменную напрямую
act --env MY_VAR=value
```

### Типичные сценарии использования

**1. Быстрое тестирование изменений:**
```bash
# Dry-run для проверки синтаксиса
act -W .github/workflows/ci.yml --job lint -n

# Реальный запуск
act -W .github/workflows/ci.yml --job lint
```

**2. Отладка проблемного job:**
```bash
# Интерактивный режим с детальным выводом
act -W .github/workflows/ci.yml --job lint --interactive --verbose
```

**3. Тестирование всех линтеров:**
```bash
# Запустить все jobs в matrix
act -W .github/workflows/ci.yml --job lint
```

**4. Тестирование конкретного линтера:**
```bash
# Только shellcheck
act -W .github/workflows/ci.yml --job lint --matrix linter:shellcheck
```

### Ограничения act

**Что НЕ работает в act:**
- Некоторые GitHub-специфичные actions (actions/upload-artifact@v4)
- GitHub API вызовы (создание релизов, комментарии к PR)
- Некоторые контексты (${{ github.event.pull_request }})
- Secrets из GitHub (нужно предоставить локально)

**Что работает:**
- Большинство стандартных actions (checkout, setup-*)
- Docker контейнеры
- Bash скрипты
- Условия (if:)
- Matrix builds

### Когда использовать act vs GitHub Actions

**Используй act когда:**
- Тестируешь изменения в workflow локально
- Отлаживаешь проблемный job
- Хочешь быстро проверить синтаксис
- Разрабатываешь новый workflow

**Используй GitHub Actions когда:**
- Нужны GitHub-специфичные features (artifacts, releases)
- Тестируешь интеграцию с GitHub API
- Проверяешь работу в реальном CI окружении
- Нужны секреты из GitHub

## Интеграция тестов в CI

### Структура тестов в проекте

```
tests/
├── unit/                    # Unit тесты
│   ├── test_download_sdk.bats
│   └── test_version_calc.bats
├── properties/              # Property-based тесты
│   ├── test_workflow_concurrency.py
│   └── test_docker_image_size.py
├── integration/             # Integration тесты
│   ├── test_docker_build.bats
│   └── test_package_build.bats
└── mocks/                   # Моки для unit тестов
    ├── curl
    └── docker
```

### CI workflow для тестов

```yaml
name: Tests

on:
  pull_request:
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
      
      - name: Install bats
        run: |
          sudo apt-get update
          sudo apt-get install -y bats
      
      - name: Run unit tests
        run: bats tests/unit/
  
  property-tests:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install hypothesis pytest pyyaml
      
      - name: Run property-based tests
        run: pytest tests/properties/ -v
  
  integration-tests:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
      
      - name: Run integration tests
        run: bats tests/integration/
```

### Быстрая обратная связь

**Стратегия:**
- Unit тесты запускаются на каждый PR (быстро, < 1 мин)
- Property-based тесты запускаются на каждый PR (средне, 2-3 мин)
- Integration тесты запускаются только на main или по требованию (медленно, 5-10 мин)

**Пример условного запуска:**
```yaml
integration-tests:
  if: github.ref == 'refs/heads/main' || contains(github.event.head_commit.message, '[integration]')
  runs-on: ubuntu-24.04
  # ...
```
