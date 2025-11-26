# Паттерны работы со спецификациями

## Общие принципы

При работе со спецификациями в этом проекте следуй этим принципам:

### 1. Структура спецификаций

Каждая спецификация находится в `.kiro/specs/{feature-name}/` и содержит:
- `requirements.md` - требования в формате EARS с acceptance criteria
- `design.md` - детальный дизайн с correctness properties
- `tasks.md` - список задач для имплементации

### 2. Формат требований (EARS)

Все требования должны следовать одному из EARS паттернов:
- **Ubiquitous**: THE {system} SHALL {response}
- **Event-driven**: WHEN {trigger}, THE {system} SHALL {response}
- **State-driven**: WHILE {condition}, THE {system} SHALL {response}
- **Unwanted event**: IF {condition}, THEN THE {system} SHALL {response}
- **Optional feature**: WHERE {option}, THE {system} SHALL {response}

**Пример для Docker образов:**
```
WHEN the Docker image is built THEN the system SHALL produce an image smaller than 2GB
```

### 3. Correctness Properties

Каждое свойство корректности должно:
- Начинаться с "For any" (универсальная квантификация)
- Быть тестируемым через Property-Based Testing
- Ссылаться на конкретный acceptance criteria из requirements
- Использовать формат: **Validates: Requirements X.Y**

**Пример:**
```
Property 1: Image size compliance
*For any* built Docker image, the size should be less than 2GB (2147483648 bytes)
**Validates: Requirements 2.1**
```

## Типичные сценарии

### Сценарий 1: Оптимизация Docker образов

**Типичные требования:**
- Уменьшение размера образа
- Валидация содержимого образа
- Документация для Windows пользователей
- Оптимизация слоев и кэширования

**Типичные свойства корректности:**
- Размер образа < лимита
- Наличие необходимых файлов/директорий
- Корректные права доступа
- Работоспособность build tools

**Типичные задачи:**
1. Анализ текущего размера и слоев
2. Оптимизация Dockerfile (объединение RUN команд)
3. Добавление .dockerignore
4. Создание валидационных скриптов
5. Обновление документации

### Сценарий 2: Исправление CI/CD проблем

**Типичные требования:**
- Успешное выполнение workflow
- Корректная обработка ошибок
- Детальная диагностика при сбоях
- Retry логика для сетевых операций

**Типичные свойства корректности:**
- Workflow завершается успешно для валидных входных данных
- Ошибки содержат достаточно информации для диагностики
- Retry логика работает при временных сбоях
- Артефакты создаются корректно

**Типичные задачи:**
1. Анализ логов failed jobs
2. Идентификация root cause
3. Исправление скриптов/workflow
4. Добавление error handling
5. Тестирование в CI окружении

### Сценарий 3: Оптимизация сборки OpenWrt пакетов

**Типичные требования:**
- Ускорение времени сборки
- Кэширование зависимостей
- Параллельная сборка для разных архитектур
- Валидация собранных пакетов

**Типичные свойства корректности:**
- Собранный пакет содержит все необходимые файлы
- Версия в пакете соответствует VERSION файлу
- Пакет устанавливается без ошибок
- Сервис запускается после установки

**Типичные задачи:**
1. Профилирование текущего процесса сборки
2. Внедрение кэширования (Docker layers, GitHub Actions cache)
3. Оптимизация зависимостей
4. Параллелизация сборки
5. Добавление валидационных тестов

## Частые ошибки и как их избежать

### 1. Слишком общие требования

❌ **Плохо:**
```
The system SHALL work correctly
```

✅ **Хорошо:**
```
WHEN the Docker image is built THEN the system SHALL verify presence of the SDK directory
```

### 2. Свойства без универсальной квантификации

❌ **Плохо:**
```
Property 1: The image should be small
```

✅ **Хорошо:**
```
Property 1: Image size compliance
*For any* built Docker image, the size should be less than 2GB
```

### 3. Задачи без ссылок на требования

❌ **Плохо:**
```
- [ ] 1. Optimize Dockerfile
```

✅ **Хорошо:**
```
- [ ] 1. Optimize Dockerfile to reduce image size
  - Combine RUN commands to reduce layers
  - Clean up apt caches in the same layer
  - _Requirements: 2.1, 2.2_
```

### 4. Отсутствие edge cases в тестировании

При работе с парсерами, сериализаторами, сетевыми операциями всегда добавляй:
- Round-trip properties для парсеров/сериализаторов
- Retry логику для сетевых операций
- Валидацию входных данных
- Обработку пустых/некорректных входов

## Специфика проекта

### Docker и OpenWrt SDK

**Важные ограничения:**
- Размер образа должен быть < 2GB
- Образ должен работать на Windows с Docker Desktop
- SDK должен быть полностью функциональным
- Пути должны быть корректными для Windows монтирования

**Типичные оптимизации:**
```dockerfile
# Объединение команд для уменьшения слоев
RUN apt-get update && \
    apt-get install -y --no-install-recommends pkg1 pkg2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Multi-stage build для минимизации размера
FROM ubuntu:24.04 AS downloader
# ... загрузка и распаковка SDK ...

FROM ubuntu:24.04 AS final
COPY --from=downloader /opt/openwrt-sdk /opt/openwrt-sdk
```

### GitHub Actions

**Важные практики:**
- Всегда указывай `--ref branch-name` при запуске workflow
- Используй `cancel-old-workflows` для отмены старых запусков
- Добавляй timeout для долгих операций
- Кэшируй зависимости где возможно

**Пример:**
```yaml
- name: Build with timeout
  timeout-minutes: 30
  run: |
    make package/compile
```

### Bash скрипты

**Важные практики:**
- Используй `set -euo pipefail` для строгой обработки ошибок
- Добавляй retry логику для сетевых операций
- Валидируй входные параметры
- Выводи понятные сообщения об ошибках

**Пример retry логики:**
```bash
retry_count=0
max_retries=15
while [ $retry_count -lt $max_retries ]; do
  if curl -fsSL "$url" -o "$output"; then
    break
  fi
  retry_count=$((retry_count + 1))
  sleep $((2 ** retry_count))
done
```

## Чеклист перед началом работы

Перед началом работы над новой спецификацией:

1. ✅ Изучи существующие спецификации в `.kiro/specs/`
2. ✅ Проверь связанные документы в `docs/`
3. ✅ Посмотри на текущие GitHub Actions workflows
4. ✅ Изучи структуру проекта и ключевые файлы
5. ✅ Определи, какие компоненты будут затронуты
6. ✅ Проверь, есть ли похожие задачи в других спецификациях

## Чеклист после завершения спецификации

После завершения работы над спецификацией:

1. ✅ Все требования следуют EARS формату
2. ✅ Все свойства корректности имеют "For any" и ссылки на requirements
3. ✅ Все задачи имеют ссылки на requirements
4. ✅ Добавлены property-based тесты для ключевых свойств
5. ✅ Добавлены unit тесты для edge cases
6. ✅ Обновлена документация
7. ✅ Проверена работа на Windows (если применимо)
8. ✅ Добавлены валидационные скрипты (если применимо)
