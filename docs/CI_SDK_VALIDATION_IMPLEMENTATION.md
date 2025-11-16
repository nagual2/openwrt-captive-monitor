# Реализация валидации SDK образов в CI

## Описание проблемы

При неправильной конфигурации OpenWrt SDK версии или целевой архитектуры в матрице CI-конфигурации, сборка может потратить значительное время до момента обнаружения ошибки. Задержка происходит потому, что действие `openwrt/gh-action-sdk@v6` сначала пытается загрузить и запустить Docker образ с несуществующим тегом.

## Решение

Реализована ранняя валидация Docker образа OpenWrt SDK и параметров целевой архитектуры перед запуском собственно сборки в CI. Это позволяет "упасть быстро" (fail-fast) с понятным сообщением об ошибке.

## Компоненты реализации

### 1. Новый валидационный скрипт: `scripts/validate-sdk-image.sh`

**Путь:** `/home/engine/project/scripts/validate-sdk-image.sh`

**Назначение:** Валидация корректности параметров OpenWrt SDK перед запуском сборки.

**Синтаксис:**
```bash
validate-sdk-image.sh <container_image> <sdk_target> <openwrt_version> <sdk_slug>
```

**Пример использования:**
```bash
./scripts/validate-sdk-image.sh \
  "ghcr.io/openwrt/sdk:openwrt-23.05.3-x86-64" \
  "x86/64" \
  "23.05.3" \
  "x86-64"
```

**Функциональность:**

1. **Валидация формата версии OpenWrt:** Проверяет соответствие формату X.Y или X.Y.Z
   - Пример валидных версий: `23.05.3`, `22.03.5`
   - Пример невалидных версий: `invalid`, `23.05`, `v23.05.3`

2. **Валидация формата целевой архитектуры (SDK target):** Проверяет соответствие формату `target/subtarget`
   - Пример валидных целей: `x86/64`, `ar71xx/generic`, `ramips/mt7621`
   - Пример невалидных целей: `x86-64`, `invalid`, `x86`

3. **Валидация формата слага (SDK slug):** Проверяет, что это буквенно-цифровое значение с дефисами
   - Пример валидных слагов: `x86-64`, `ar71xx-generic`, `ramips-mt7621`
   - Пример невалидных слагов: `x86/64`, `invalid.slug`

4. **Проверка соответствия тега контейнера:** Убеждается, что формат Docker образа соответствует параметрам
   - Проверяет, что образ содержит `openwrt-{version}-{slug}`
   - Пример: для версии `23.05.3` и слага `x86-64` образ должен содержать `openwrt-23.05.3-x86-64`

5. **Проверка доступности Docker образа в реестре:** Использует `docker manifest inspect` для проверки наличия образа
   - Выполняет до 3 попыток с интервалом 5 секунд
   - Использует цветной вывод для лучшей читаемости

**Возвращаемые коды:**
- `0`: Успешная валидация
- `1`: Ошибка валидации

**Примеры ошибок:**
```
Error: Invalid OpenWrt version format: invalid (expected: X.Y or X.Y.Z)
Error: Invalid SDK target format: invalid (expected: target/subtarget, e.g., x86/64)
Error: Container image tag mismatch. Expected suffix: openwrt-23.05.3-x86-64, got: ghcr.io/openwrt/sdk:openwrt-22.03.5-x86-64
Error: Docker image not found in registry: ghcr.io/openwrt/sdk:openwrt-23.05.3-x86-64
```

### 2. Изменения в CI-конфигурации: `.github/workflows/ci.yml`

**Новый шаг:** `Validate SDK image and target`

**Расположение:** Между шагами "Prepare package structure for SDK" и "Build with OpenWrt SDK"

**Конфигурация:**
```yaml
- name: Validate SDK image and target
  run: |
    set -euo pipefail
    ./scripts/validate-sdk-image.sh \
      "ghcr.io/openwrt/sdk:openwrt-${{ matrix.openwrt_version }}-${{ matrix.sdk_slug }}" \
      "${{ matrix.sdk_target }}" \
      "${{ matrix.openwrt_version }}" \
      "${{ matrix.sdk_slug }}"
```

**Преимущества:**
- Валидация выполняется на ранней стадии, до попытки загрузки Docker образа
- Четкие и понятные сообщения об ошибках
- Поддержка повторных попыток для проверки доступности образа
- Цветной вывод для лучшей видимости в логах CI

## Примеры ошибок и их значение

### Ошибка: Invalid OpenWrt version format
```
Error: Invalid OpenWrt version format: 23.5 (expected: X.Y or X.Y.Z)
```
**Значение:** Версия OpenWrt не соответствует ожидаемому формату. Необходимо исправить версию в матрице конфигурации.

### Ошибка: Invalid SDK target format
```
Error: Invalid SDK target format: x86-64 (expected: target/subtarget, e.g., x86/64)
```
**Значение:** Формат целевой архитектуры неправильный. Должен быть в виде `target/subtarget`, например `x86/64`.

### Ошибка: Container image tag mismatch
```
Error: Container image tag mismatch. Expected suffix: openwrt-23.05.3-x86-64, got: ghcr.io/openwrt/sdk:openwrt-22.03.5-x86-64
```
**Значение:** Версия в Docker образе не соответствует указанной версии OpenWrt. Проверьте конфигурацию матрицы.

### Ошибка: Docker image not found in registry
```
Error: Docker image not found in registry: ghcr.io/openwrt/sdk:openwrt-23.05.3-x86-64

This usually means:
1. The OpenWrt version (23.05.3) doesn't exist
2. The target/subtarget combination (x86/64 / x86-64) is not supported
3. Network connectivity issue (even after 3 attempts)

Please verify:
- The OpenWrt version is correct
- The target/subtarget combination is valid
- Network connectivity is working
```
**Значение:** Docker образ не найден в реестре. Проверьте:
- Существует ли версия OpenWrt в реестре
- Поддерживается ли комбинация целевой архитектуры
- Доступность сети

## Технические детали

### Использованные технологии
- **Язык:** POSIX shell (совместим с BusyBox ash)
- **Библиотеки:** `scripts/lib/colors.sh` для цветного вывода
- **Инструменты:** `docker manifest inspect` для проверки образов
- **Регулярные выражения:** grep с поддержкой расширенных выражений

### Соблюдение стандартов
- Скрипт использует `set -eu` и условный `set -o pipefail` для надежности
- Следует стилю проекта BusyBox ash совместимости
- Исходит из центральной библиотеки цветов `scripts/lib/colors.sh`
- Соответствует GitHub Actions workflow лучшим практикам

## Тестирование

### Тест 1: Валидные параметры
```bash
./scripts/validate-sdk-image.sh \
  "ghcr.io/openwrt/sdk:openwrt-23.05.3-x86-64" \
  "x86/64" \
  "23.05.3" \
  "x86-64"
```

### Тест 2: Невалидная версия
```bash
./scripts/validate-sdk-image.sh \
  "ghcr.io/openwrt/sdk:openwrt-invalid-x86-64" \
  "x86/64" \
  "invalid" \
  "x86-64"
```
Ожидаемый результат: `Error: Invalid OpenWrt version format: invalid (expected: X.Y or X.Y.Z)`

### Тест 3: Невалидная целевая архитектура
```bash
./scripts/validate-sdk-image.sh \
  "ghcr.io/openwrt/sdk:openwrt-23.05.3-x86-64" \
  "invalid" \
  "23.05.3" \
  "x86-64"
```
Ожидаемый результат: `Error: Invalid SDK target format: invalid (expected: target/subtarget, e.g., x86/64)`

### Тест 4: Несоответствие тега контейнера
```bash
./scripts/validate-sdk-image.sh \
  "ghcr.io/openwrt/sdk:openwrt-22.03.5-x86-64" \
  "x86/64" \
  "23.05.3" \
  "x86-64"
```
Ожидаемый результат: `Error: Container image tag mismatch. Expected suffix: openwrt-23.05.3-x86-64, got: ghcr.io/openwrt/sdk:openwrt-22.03.5-x86-64`

## Установка в CI

Валидационный шаг автоматически выполняется в CI-конфигурации `.github/workflows/ci.yml` и не требует дополнительной настройки при работе с матрицей конфигурации.

### Добавление новой конфигурации в матрицу

При добавлении новой конфигурации в матрицу убедитесь:
1. `openwrt_version` соответствует формату X.Y или X.Y.Z
2. `sdk_target` имеет формат target/subtarget
3. `sdk_slug` соответствует слагу в Docker образе OpenWrt
4. Теги Docker образов соответствуют версиям

**Пример новой конфигурации:**
```yaml
- openwrt_version: '24.01.0'
  sdk_target: 'ath79/generic'
  sdk_slug: 'ath79-generic'
  arch: 'mips_24kc'
```

## Заключение

Реализация валидации SDK образов позволяет:
- **Сократить время сборки** при неправильной конфигурации
- **Улучшить видимость ошибок** через четкие сообщения об ошибках
- **Предотвратить пустые сборки** благодаря ранней валидации
- **Улучшить опыт разработчиков** с быстрой обратной связью

Это особенно полезно при расширении матрицы конфигурации на новые версии OpenWrt или целевые архитектуры.
