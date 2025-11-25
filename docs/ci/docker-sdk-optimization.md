# Docker SDK Optimization для CI/CD

## Обзор

Этот документ описывает оптимизацию CI/CD pipeline через использование предсобранных Docker-образов с OpenWrt SDK вместо кеширования и загрузки SDK при каждой сборке.

## Мотивация

### Проблемы старого подхода

1. **Медленная сборка**: Загрузка и распаковка SDK занимает 2-3 минуты при каждой сборке
2. **Ненадежное кеширование**: GitHub Actions cache может быть вытеснен или поврежден
3. **Дублирование работы**: Каждый workflow загружает и настраивает SDK независимо
4. **Большой размер кеша**: SDK занимает 500MB-1GB в кеше

### Преимущества нового подхода

1. **Быстрая сборка**: SDK уже готов в образе, экономия 2-3 минуты на каждой сборке
2. **Надежность**: Docker-образы в GHCR более стабильны чем cache
3. **Переиспользование**: Один образ используется всеми workflows
4. **Версионирование**: Образы тегируются и можно откатиться к предыдущей версии

## Архитектура

### Компоненты

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions Workflow: build-sdk-images.yml          │
│  Триггеры: push to main, schedule, manual               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Docker Build (Multi-stage)                             │
│  - Stage 1: Download & extract SDK                      │
│  - Stage 2: Install deps & create final image           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  GitHub Container Registry (GHCR)                       │
│  Images: ghcr.io/nagual2/openwrt-sdk:*                  │
│  Tags: {version}-{arch}-latest, {version}-{arch}-{sha}  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  CI/CD Workflows (ci.yml, tag-build-release.yml)        │
│  Use: container: ghcr.io/.../openwrt-sdk:...            │
└─────────────────────────────────────────────────────────┘
```

## Изменения в CI Workflow

### До оптимизации

```yaml
jobs:
  build-pr-package:
    runs-on: ubuntu-24.04
    steps:
      - name: Cache OpenWrt SDK
        uses: actions/cache@v4
        with:
          path: ~/.cache/openwrt-sdk
          key: ${{ runner.os }}-openwrt-sdk-...
      
      - name: Build with OpenWrt SDK
        uses: openwrt/gh-action-sdk@v9
        env:
          ARCH: x86_64-23.05.5
          PACKAGES: openwrt-captive-monitor
```

### После оптимизации

```yaml
jobs:
  build-pr-package:
    runs-on: ubuntu-24.04
    container:
      image: ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Build package with SDK
        run: |
          cd /opt/openwrt-sdk
          make package/openwrt-captive-monitor/compile V=s
```

### Ключевые изменения

1. **Удалено**:
   - Шаг кеширования SDK
   - Использование `openwrt/gh-action-sdk@v9` action
   - Загрузка и распаковка SDK

2. **Добавлено**:
   - `container:` directive с образом из GHCR
   - Прямая работа с SDK в `/opt/openwrt-sdk`
   - Кеширование только feeds (зависимости)
   - Retry логика для pull образа

3. **Оптимизировано**:
   - Упрощена подготовка пакета
   - Прямой вызов `make` вместо обертки
   - Улучшено кеширование зависимостей

## Docker-образы SDK

### Структура образа

```dockerfile
FROM ubuntu:24.04

# Stage 1: Download SDK
RUN curl SDK_URL | tar -xz

# Stage 2: Final image
FROM ubuntu:24.04
COPY --from=stage1 /opt/openwrt-sdk /opt/openwrt-sdk
RUN apt-get install build-essential ...
USER builder
WORKDIR /opt/openwrt-sdk
```

### Теги образов

- `23.05.5-x86-64-latest` - последняя версия для x86_64
- `23.05.5-x86-64-abc12345` - конкретный коммит
- `23.05.5-ath79-generic-latest` - последняя версия для ath79

### Поддерживаемые архитектуры

1. x86/64 (x86_64)
2. ath79/generic
3. ramips/mt76x8
4. mediatek/filogic
5. ipq40xx/generic
6. ipq806x/generic
7. bcm27xx/bcm2711 (Raspberry Pi 4)
8. rockchip/armv8

## Workflow сборки образов

### Триггеры

1. **Push в main**: При изменении `docker/sdk/Dockerfile`
2. **Schedule**: Еженедельно по воскресеньям (обновление базового образа)
3. **Manual**: Через workflow_dispatch с опцией force rebuild

### Процесс сборки

1. Проверка существования образа (пропуск если уже есть)
2. Сборка образа с Docker Buildx
3. Загрузка в GHCR с двумя тегами (latest и SHA)
4. Валидация образа:
   - Проверка наличия SDK
   - Проверка размера (< 2GB)
   - Проверка отсутствия временных файлов

### Параллелизация

- `max-parallel: 4` - одновременная сборка 4 архитектур
- `fail-fast: false` - продолжение при ошибке в одной архитектуре
- Общее время сборки всех 8 образов: ~30-40 минут

## Кеширование

### Feeds кеш

```yaml
- name: Cache feeds dependencies
  uses: actions/cache@v4
  with:
    path: |
      /opt/openwrt-sdk/feeds
      /opt/openwrt-sdk/dl
    key: ${{ runner.os }}-openwrt-feeds-${{ matrix.sdk_slug }}-...
```

Кешируются:
- `feeds/` - установленные feeds
- `dl/` - загруженные исходники зависимостей

### Docker layer cache

```yaml
cache-from: type=registry,ref=${{ steps.meta.outputs.tag_latest }}
cache-to: type=inline
```

Docker использует layer caching для ускорения повторных сборок образов.

## Retry логика

### Pull образа

```yaml
- name: Retry pull SDK image if needed
  if: failure()
  run: |
    MAX_RETRIES=3
    for i in $(seq 1 $MAX_RETRIES); do
      if docker pull "$IMAGE"; then
        exit 0
      fi
      sleep $((RETRY_DELAY * 2))
    done
```

Retry с экспоненциальной задержкой:
- Попытка 1: немедленно
- Попытка 2: через 10 секунд
- Попытка 3: через 20 секунд

## Метрики производительности

### Время сборки

| Этап | До оптимизации | После оптимизации | Экономия |
|------|----------------|-------------------|----------|
| Загрузка SDK | 1-2 мин | 0 мин | 1-2 мин |
| Распаковка SDK | 30-60 сек | 0 сек | 30-60 сек |
| Настройка SDK | 30 сек | 10 сек | 20 сек |
| Сборка пакета | 1-2 мин | 1-2 мин | 0 |
| **Итого** | **3-5 мин** | **1-2 мин** | **2-3 мин** |

### Использование ресурсов

| Ресурс | До | После | Изменение |
|--------|-----|-------|-----------|
| GitHub Actions cache | 500MB-1GB | 50-100MB | -80% |
| GHCR storage | 0 | 1.5GB × 8 = 12GB | +12GB |
| Build time | 3-5 мин | 1-2 мин | -60% |

## Очистка образов

Автоматическая очистка старых образов (будет реализовано в задаче 5):

- Образы старше 90 дней удаляются
- Сохраняются последние 10 версий каждой архитектуры
- Образы с тегом `latest` защищены
- Активно используемые образы защищены

## Troubleshooting

### Образ не найден

**Проблема**: `Error: failed to pull image: not found`

**Решение**:
1. Проверьте что workflow `build-sdk-images.yml` выполнился успешно
2. Проверьте наличие образа в GHCR: https://github.com/nagual2?tab=packages
3. Запустите `build-sdk-images.yml` вручную с force_rebuild

### Ошибка аутентификации

**Проблема**: `Error: failed to authenticate to GHCR`

**Решение**:
1. Убедитесь что `GITHUB_TOKEN` имеет права `packages: read`
2. Проверьте что образ публичный или workflow имеет доступ

### Сборка пакета не работает

**Проблема**: `Error: package not found in SDK`

**Решение**:
1. Проверьте что feeds обновлены: `./scripts/feeds update -a`
2. Проверьте что пакет установлен: `./scripts/feeds install openwrt-captive-monitor`
3. Проверьте путь к пакету в `feeds.conf`

### Образ слишком большой

**Проблема**: Image size exceeds 2GB

**Решение**:
1. Проверьте что временные файлы удалены в Dockerfile
2. Проверьте что apt cache очищен: `rm -rf /var/lib/apt/lists/*`
3. Используйте `--no-install-recommends` для apt packages

## Миграция

### Для существующих workflows

1. Добавьте `container:` directive в job
2. Удалите шаги кеширования SDK
3. Обновите пути к SDK (`/opt/openwrt-sdk`)
4. Добавьте retry логику для pull образа

### Для новых workflows

Используйте шаблон из `ci.yml`:

```yaml
jobs:
  build:
    runs-on: ubuntu-24.04
    container:
      image: ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - uses: actions/checkout@v6
      - name: Build
        run: |
          cd /opt/openwrt-sdk
          # Build commands
```

## Дальнейшие улучшения

1. **Multi-arch образы**: Использование Docker manifest для поддержки нескольких архитектур в одном теге
2. **Incremental builds**: Кеширование промежуточных результатов сборки
3. **Distributed cache**: Использование внешнего cache backend (S3, Azure)
4. **Build matrix optimization**: Динамическое определение архитектур для сборки

## Ссылки

- [Docker SDK Images](../docker-sdk-images.md)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [OpenWrt SDK](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk)
- [GitHub Actions: Running jobs in a container](https://docs.github.com/en/actions/using-jobs/running-jobs-in-a-container)
