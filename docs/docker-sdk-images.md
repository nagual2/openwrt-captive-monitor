# Docker SDK Images для OpenWrt

## Обзор

Этот документ описывает систему Docker-образов SDK для ускорения сборки пакетов OpenWrt в CI/CD pipeline.

## Что это?

Docker-образы SDK - это предсобранные контейнеры, содержащие:
- OpenWrt SDK для конкретной архитектуры
- Все необходимые build dependencies
- Настроенное окружение для сборки

## Зачем это нужно?

### Проблемы без Docker-образов

- ⏱️ Загрузка SDK занимает 1-2 минуты при каждой сборке
- 📦 Распаковка SDK занимает 30-60 секунд
- 💾 Кеш GitHub Actions ненадежен (может быть вытеснен)
- 🔄 Каждый workflow загружает SDK независимо

### Преимущества Docker-образов

- ⚡ SDK уже готов в образе - экономия 2-3 минуты
- 🎯 Надежное хранение в GHCR
- 🔄 Переиспользование между workflows
- 📌 Версионирование и откат к предыдущим версиям

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│  Dockerfile (multi-stage)                               │
│  ├─ Stage 1: Download & extract SDK                     │
│  └─ Stage 2: Install deps & create final image          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions: build-sdk-images.yml                   │
│  ├─ Build images for 8 architectures                    │
│  ├─ Validate size & contents                            │
│  └─ Push to GHCR with tags                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  GitHub Container Registry (GHCR)                       │
│  └─ ghcr.io/nagual2/openwrt-sdk:*                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  CI/CD Workflows                                        │
│  ├─ ci.yml (PR builds)                                  │
│  └─ tag-build-release.yml (Release builds)              │
└─────────────────────────────────────────────────────────┘
```

## Поддерживаемые архитектуры

| Архитектура | SDK Slug | Описание |
|-------------|----------|----------|
| x86/64 | x86-64 | x86_64 архитектура |
| ath79/generic | ath79-generic | Atheros AR71xx/AR724x/AR913x |
| ramips/mt76x8 | ramips-mt76x8 | MediaTek MT76x8 |
| mediatek/filogic | mediatek-filogic | MediaTek Filogic |
| ipq40xx/generic | ipq40xx-generic | Qualcomm IPQ40xx |
| ipq806x/generic | ipq806x-generic | Qualcomm IPQ806x |
| bcm27xx/bcm2711 | bcm27xx-bcm2711 | Raspberry Pi 4 |
| rockchip/armv8 | rockchip-armv8 | Rockchip ARM64 |

## Теги образов

### Формат тегов

```
ghcr.io/{owner}/openwrt-sdk:{version}-{arch}-{tag}
```

### Примеры

- `ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest` - Последняя версия для x86_64
- `ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-abc12345` - Конкретный коммит
- `ghcr.io/nagual2/openwrt-sdk:23.05.5-ath79-generic-latest` - Последняя версия для ath79

### Стратегия тегирования

- **latest**: Последняя собранная версия для архитектуры
- **{sha}**: Конкретный коммит (8 символов)

## Использование

### В GitHub Actions

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
      
      - name: Build package
        run: |
          cd /opt/openwrt-sdk
          echo "src-link local ${{ github.workspace }}/package" >> feeds.conf
          ./scripts/feeds update -a
          ./scripts/feeds install openwrt-captive-monitor
          make defconfig
          make package/openwrt-captive-monitor/compile V=s
```

### Локально

```bash
# Pull образа
docker pull ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest

# Запуск контейнера
docker run -it --rm \
  -v $(pwd):/workspace \
  ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest \
  bash

# Внутри контейнера
cd /opt/openwrt-sdk
# ... build commands ...
```

### Сборка локально

```bash
# Используя скрипт
./docker/sdk/build-local.sh --target x86 --subtarget 64

# Вручную
docker build \
  --build-arg OPENWRT_VERSION=23.05.5 \
  --build-arg SDK_TARGET=x86 \
  --build-arg SDK_SUBTARGET=64 \
  -t my-sdk:latest \
  -f docker/sdk/Dockerfile \
  .
```

## Структура образа

### Директории

```
/opt/openwrt-sdk/          # SDK root
├── Makefile               # Main Makefile
├── scripts/               # Build scripts
│   └── feeds              # Feeds management
├── include/               # Build system includes
├── package/               # Package definitions
├── feeds/                 # Installed feeds
├── bin/                   # Build output
└── dl/                    # Downloaded sources
```

### Пользователи

- **root**: Для системных операций
- **builder** (UID 1000): Для сборки пакетов

### Переменные окружения

```bash
OPENWRT_VERSION=23.05.5
SDK_TARGET=x86
SDK_SUBTARGET=64
PATH=/opt/openwrt-sdk/staging_dir/host/bin:$PATH
```

## Сборка образов

### Автоматическая сборка

Образы автоматически собираются workflow `.github/workflows/build-sdk-images.yml`:

**Триггеры:**
- Push в main с изменениями в `docker/sdk/Dockerfile`
- Еженедельно по воскресеньям (обновление базового образа)
- Ручной запуск через workflow_dispatch

**Процесс:**
1. Проверка существования образа (пропуск если есть)
2. Сборка образа с Docker Buildx
3. Валидация размера (< 2GB)
4. Валидация содержимого (SDK, tools, cleanup)
5. Push в GHCR с двумя тегами

### Ручная сборка

```bash
# Запуск workflow вручную
gh workflow run build-sdk-images.yml

# С принудительной пересборкой
gh workflow run build-sdk-images.yml -f force_rebuild=true
```

## Валидация образов

### Проверка размера

```bash
./scripts/validate-docker-image-size.sh \
  ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest \
  2048  # Max size in MB
```

### Проверка содержимого

```bash
./scripts/validate-docker-image-contents.sh \
  ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest
```

**Проверки:**
- ✅ SDK directory exists
- ✅ Required SDK files present
- ✅ Build tools available
- ⚠️ No temporary files
- ⚠️ APT cache cleaned

## Оптимизация размера

### Multi-stage build

```dockerfile
# Stage 1: Download SDK
FROM ubuntu:24.04 AS sdk-downloader
RUN curl SDK_URL | tar -xz

# Stage 2: Final image
FROM ubuntu:24.04
COPY --from=sdk-downloader /opt/openwrt-sdk /opt/openwrt-sdk
```

### Очистка

```dockerfile
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /var/tmp/*
```

### Результаты

- Без оптимизации: ~2.5GB
- С оптимизацией: ~1.5GB
- Экономия: ~40%

## Обслуживание

### Очистка старых образов

Автоматическая очистка через `.github/workflows/cleanup.yml`:

**Правила:**
- Образы старше 90 дней удаляются
- Сохраняются последние 10 версий на архитектуру
- Образы с тегом `latest` защищены
- Активно используемые образы защищены

### Обновление базового образа

```bash
# Запустить еженедельную пересборку вручную
gh workflow run build-sdk-images.yml -f force_rebuild=true
```

### Обновление OpenWrt версии

1. Обновить `OPENWRT_VERSION` в Dockerfile
2. Обновить matrix в workflows
3. Commit и push изменений
4. Образы пересоберутся автоматически

## Troubleshooting

### Образ не найден

**Проблема**: `Error: failed to pull image`

**Решение:**
1. Проверьте наличие образа: `docker pull ghcr.io/nagual2/openwrt-sdk:...`
2. Проверьте права доступа к GHCR
3. Запустите сборку образов вручную

### Образ слишком большой

**Проблема**: Image size exceeds 2GB

**Решение:**
1. Проверьте Dockerfile на лишние файлы
2. Убедитесь что временные файлы удалены
3. Проверьте что APT cache очищен
4. Используйте `--no-install-recommends`

### SDK не работает

**Проблема**: Build fails in container

**Решение:**
1. Проверьте что SDK directory exists: `docker run --rm IMAGE test -d /opt/openwrt-sdk`
2. Проверьте права доступа: `docker run --rm IMAGE ls -la /opt/openwrt-sdk`
3. Запустите валидацию: `./scripts/validate-docker-image-contents.sh IMAGE`

### Медленная сборка

**Проблема**: Build still takes long time

**Решение:**
1. Проверьте что используется образ из GHCR, а не локальная сборка
2. Проверьте кеширование feeds
3. Используйте `max-parallel` для ограничения параллельных сборок

## Метрики

### Время сборки

| Этап | Без Docker | С Docker | Экономия |
|------|------------|----------|----------|
| Pull/Download SDK | 1-2 мин | 30 сек | 1-1.5 мин |
| Extract SDK | 30-60 сек | 0 сек | 30-60 сек |
| Setup SDK | 30 сек | 10 сек | 20 сек |
| Build package | 1-2 мин | 1-2 мин | 0 |
| **Total** | **3-5 мин** | **1.5-2.5 мин** | **2-2.5 мин** |

### Использование хранилища

- Размер одного образа: ~1.5GB
- Количество архитектур: 8
- Версий на архитектуру: ~10
- **Итого**: ~120GB в GHCR

## Лучшие практики

1. **Используйте latest теги** для CI/CD
2. **Используйте SHA теги** для воспроизводимых сборок
3. **Регулярно обновляйте** базовые образы
4. **Мониторьте размер** образов
5. **Очищайте старые** версии

## Ссылки

- [Dockerfile](../docker/sdk/Dockerfile)
- [Build workflow](../.github/workflows/build-sdk-images.yml)
- [Validation scripts](../scripts/)
- [CI optimization docs](ci/docker-sdk-optimization.md)
- [Cleanup docs](ci/docker-image-cleanup.md)
