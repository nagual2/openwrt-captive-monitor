# Автоматическая очистка Docker-образов

## Обзор

Этот документ описывает систему автоматической очистки старых Docker-образов SDK из GitHub Container Registry (GHCR) для предотвращения переполнения хранилища.

## Мотивация

### Проблема

- Docker-образы SDK занимают ~1.5GB каждый
- 8 архитектур × множество версий = большой объем хранилища
- Старые образы редко используются но занимают место
- GHCR имеет лимиты на хранилище

### Решение

Автоматическая очистка старых и неиспользуемых образов с защитой активных версий.

## Правила очистки

### 1. Удаление старых образов (90 дней)

Образы старше 90 дней автоматически удаляются.

**Исключения:**
- Образы с тегом `latest`
- Активно используемые образы

### 2. Удаление неиспользуемых образов (30 дней)

Образы, которые не использовались (не было pulls) в течение 30 дней, удаляются.

**Определение "использования":**
- Дата последнего обновления (`updated_at`)
- Включает pulls и другие операции с образом

### 3. Ограничение версий (10 последних)

Для каждой архитектуры сохраняются только последние 10 версий.

**Логика:**
- Образы сортируются по дате создания (новые → старые)
- Первые 10 сохраняются
- Остальные удаляются

### 4. Защита образов с тегом `latest`

Образы с тегом `*-latest` никогда не удаляются.

**Примеры защищенных тегов:**
- `23.05.5-x86-64-latest`
- `23.05.5-ath79-generic-latest`

### 5. Защита образов без тегов

Образы без тегов (untagged) удаляются немедленно.

## Конфигурация

### Переменные окружения

```yaml
env:
  IMAGE_RETENTION_DAYS: 90        # Максимальный возраст образа
  UNUSED_IMAGE_DAYS: 30           # Период неиспользования
  MAX_VERSIONS_PER_ARCH: 10       # Максимум версий на архитектуру
```

### Расписание

```yaml
on:
  schedule:
    - cron: '0 3 * * *'  # Каждый день в 3:00 UTC
```

### Ручной запуск

Workflow можно запустить вручную через GitHub Actions UI:
1. Перейти в Actions → Cleanup Artifacts and Runs
2. Нажать "Run workflow"
3. Выбрать ветку (обычно `main`)

## Алгоритм работы

### Шаг 1: Получение списка образов

```javascript
const { data: versions } = await github.rest.packages.getAllPackageVersionsForPackageOwnedByUser({
  package_type: 'container',
  package_name: 'openwrt-sdk',
  username: owner,
  per_page: 100
});
```

### Шаг 2: Группировка по архитектурам

Образы группируются по архитектуре на основе тегов:

```
23.05.5-x86-64-abc12345 → архитектура: x86-64
23.05.5-ath79-generic-def67890 → архитектура: ath79-generic
```

### Шаг 3: Применение правил

Для каждого образа проверяются правила в порядке:

1. **Проверка тега `latest`** → Пропустить (защищен)
2. **Проверка возраста** → Удалить если > 90 дней
3. **Проверка использования** → Удалить если не использовался > 30 дней
4. **Проверка позиции** → Удалить если позиция > 10

### Шаг 4: Удаление образов

```javascript
await github.rest.packages.deletePackageVersionForUser({
  package_type: 'container',
  package_name: 'openwrt-sdk',
  username: owner,
  package_version_id: image.id
});
```

## Примеры

### Пример 1: Нормальная очистка

**Состояние:**
- Архитектура `x86-64` имеет 15 версий
- Все версии моложе 90 дней
- Все версии использовались недавно

**Результат:**
- Сохранены: 10 последних версий + `latest`
- Удалены: 5 самых старых версий

### Пример 2: Очистка старых образов

**Состояние:**
- Архитектура `ath79-generic` имеет 8 версий
- 3 версии старше 90 дней
- Остальные 5 версий актуальны

**Результат:**
- Сохранены: 5 актуальных версий + `latest`
- Удалены: 3 старых версии

### Пример 3: Очистка неиспользуемых образов

**Состояние:**
- Архитектура `ramips-mt76x8` имеет 12 версий
- 4 версии не использовались 35 дней
- Остальные 8 версий активны

**Результат:**
- Сохранены: 8 активных версий + `latest`
- Удалены: 4 неиспользуемых версии

## Мониторинг

### GitHub Actions Summary

После каждого запуска создается summary с метриками:

| Метрика | Значение |
|---------|----------|
| Total images found | 120 |
| Images deleted | 35 |
| Images failed | 0 |
| Retention days | 90 |
| Unused days threshold | 30 |
| Max versions per arch | 10 |

### Логи

Детальные логи доступны в GitHub Actions:

```
Processing architecture: x86-64 (15 images)
  Image 12345 kept (age: 5.2d, unused: 2.1d, position: 1)
  Image 12346 kept (age: 10.5d, unused: 5.3d, position: 2)
  ...
  Image 12355 exceeds max versions (position 11 > 10)

=== Deletion Summary ===
Total images to delete: 5
✓ Deleted image 12355 (exceeds max 10 versions): 23.05.5-x86-64-old123
✓ Deleted image 12356 (exceeds max 10 versions): 23.05.5-x86-64-old456
...

=== Final Results ===
Successfully deleted: 5
Failed to delete: 0
Total processed: 120
```

## Расчет экономии хранилища

### Без очистки

```
8 архитектур × 1.5GB × 20 версий = 240GB
```

### С очисткой

```
8 архитектур × 1.5GB × 10 версий = 120GB
Экономия: 120GB (50%)
```

### Реальный пример

При активной разработке (1 сборка в день):

| Период | Без очистки | С очисткой | Экономия |
|--------|-------------|------------|----------|
| 1 месяц | 360GB | 120GB | 240GB (67%) |
| 3 месяца | 1080GB | 120GB | 960GB (89%) |
| 6 месяцев | 2160GB | 120GB | 2040GB (94%) |

## Безопасность

### Защищенные образы

Следующие образы **никогда** не удаляются:

1. **Latest теги**: `*-latest`
2. **Активные образы**: Используемые в последние 30 дней
3. **Недавние образы**: Моложе 90 дней (если в пределах топ-10)

### Права доступа

Workflow требует права:

```yaml
permissions:
  packages: write  # Для удаления образов
  contents: read   # Для чтения репозитория
```

## Troubleshooting

### Образы не удаляются

**Проблема**: Workflow выполняется, но образы остаются

**Возможные причины:**
1. Образы имеют тег `latest`
2. Образы моложе 90 дней и в топ-10
3. Образы использовались в последние 30 дней

**Решение:**
- Проверьте логи workflow
- Убедитесь что образы соответствуют критериям удаления

### Ошибка доступа

**Проблема**: `Error: Resource not accessible by integration`

**Решение:**
1. Проверьте права workflow: `packages: write`
2. Убедитесь что `GITHUB_TOKEN` имеет доступ к packages
3. Проверьте настройки репозитория: Settings → Actions → General → Workflow permissions

### Удалены нужные образы

**Проблема**: Случайно удалены важные образы

**Решение:**
1. Пересоберите образы через `build-sdk-images.yml`
2. Используйте `force_rebuild: true` для принудительной сборки
3. Настройте более длительный retention period

### Слишком много образов удаляется

**Проблема**: Очистка слишком агрессивная

**Решение:**
Увеличьте параметры в workflow:

```yaml
env:
  IMAGE_RETENTION_DAYS: 180      # Было: 90
  UNUSED_IMAGE_DAYS: 60          # Было: 30
  MAX_VERSIONS_PER_ARCH: 20      # Было: 10
```

## Настройка под свои нужды

### Изменение retention period

Для более длительного хранения образов:

```yaml
env:
  IMAGE_RETENTION_DAYS: 180  # 6 месяцев вместо 3
```

### Изменение количества версий

Для хранения большего количества версий:

```yaml
env:
  MAX_VERSIONS_PER_ARCH: 20  # 20 версий вместо 10
```

### Отключение очистки неиспользуемых образов

Закомментируйте проверку в скрипте:

```javascript
// Rule 2: Delete if unused for too long
// if (unusedInDays > unusedDays) {
//   ...
// }
```

### Добавление дополнительных защищенных тегов

Модифицируйте проверку тегов:

```javascript
const hasProtectedTag = tags.some(tag => 
  tag.endsWith('-latest') || 
  tag.includes('-stable') ||
  tag.includes('-production')
);
```

## Интеграция с мониторингом

### Slack уведомления

Добавьте шаг для отправки уведомлений:

```yaml
- name: Send Slack notification
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Docker cleanup completed: ${{ steps.cleanup.outputs.deleted }} images deleted"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Prometheus метрики

Экспортируйте метрики для мониторинга:

```yaml
- name: Export metrics
  run: |
    echo "docker_images_deleted{repo=\"${{ github.repository }}\"} $DELETED_COUNT" > metrics.txt
    # Push to Pushgateway
```

## Лучшие практики

1. **Регулярный мониторинг**: Проверяйте логи cleanup workflow еженедельно
2. **Тестирование**: Тестируйте изменения на тестовом репозитории
3. **Документирование**: Документируйте изменения в retention policy
4. **Резервное копирование**: Сохраняйте важные образы в другом registry
5. **Постепенное внедрение**: Начните с консервативных параметров

## Ссылки

- [GitHub Packages API](https://docs.github.com/en/rest/packages)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Image Cleanup Best Practices](https://docs.docker.com/registry/garbage-collection/)
