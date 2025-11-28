# Паттерны работы с Docker

## Оптимизация размера Docker образов

### Целевые метрики

- **Максимальный размер образа:** 2GB (2147483648 bytes)
- **Типичный размер после оптимизации:** ~1.5GB
- **Экономия от оптимизации:** ~40%

### Проверка размера образа

```bash
# Получить размер в байтах
IMAGE_SIZE_BYTES=$(docker inspect "$IMAGE" --format='{{.Size}}')

# Проверить лимит
MAX_SIZE_BYTES=$((2 * 1024 * 1024 * 1024))  # 2GB

if [[ ${IMAGE_SIZE_BYTES} -gt ${MAX_SIZE_BYTES} ]]; then
    echo "ERROR: Image size exceeds 2GB limit"
    echo "Actual: $(numfmt --to=iec-i --suffix=B ${IMAGE_SIZE_BYTES})"
    exit 1
fi

# Человекочитаемый формат
docker inspect "$IMAGE" --format='{{.Size}}' | numfmt --to=iec-i --suffix=B
```

### Multi-stage builds

**Паттерн для минимизации размера:**

```dockerfile
# Stage 1: Downloader - загрузка и распаковка
FROM ubuntu:24.04 AS sdk-downloader

# Установить только необходимые инструменты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        xz-utils && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Загрузить и распаковать SDK
COPY docker/sdk/download-sdk.sh /tmp/
RUN bash /tmp/download-sdk.sh && \
    rm -f /tmp/download-sdk.sh

# Stage 2: Final - финальный образ
FROM ubuntu:24.04 AS final

# Установить build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libncurses-dev \
        python3 \
        git && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Скопировать только SDK из первого stage
COPY --from=sdk-downloader /opt/openwrt-sdk /opt/openwrt-sdk

# Создать non-root пользователя
RUN useradd -m -u 1000 builder && \
    chown -R builder:builder /opt/openwrt-sdk

USER builder
WORKDIR /opt/openwrt-sdk
```

**Преимущества multi-stage:**
- Инструменты для загрузки (curl, xz-utils) не попадают в финальный образ
- Временные файлы остаются в первом stage
- Финальный образ содержит только необходимое

### Объединение RUN команд

**❌ Плохо - создает несколько слоев:**
```dockerfile
RUN apt-get update
RUN apt-get install -y pkg1 pkg2
RUN rm -rf /var/lib/apt/lists/*
```

**✅ Хорошо - один слой с очисткой:**
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends pkg1 pkg2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

**Правила объединения:**
- Объединяй связанные команды (установка + очистка)
- Используй `&&` для цепочки команд
- Используй `\` для многострочного формата
- Очищай кеши в том же слое, где они создаются

### Очистка временных файлов

**Обязательная очистка после каждого RUN:**

```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    # Очистка apt кешей
    rm -rf /var/lib/apt/lists/* && \
    # Очистка временных директорий
    rm -rf /tmp/* && \
    rm -rf /var/tmp/*
```

**Удаление архивов после распаковки:**

```dockerfile
# ❌ Плохо - архив остается в образе
RUN tar -xf sdk.tar.xz
RUN rm sdk.tar.xz

# ✅ Хорошо - удаление в том же слое
RUN tar -C /opt/openwrt-sdk --strip-components=1 -xf sdk.tar.xz && \
    rm -f sdk.tar.xz sha256sums
```

### Использование --no-install-recommends

**Всегда используй для apt-get install:**

```dockerfile
# Устанавливает только необходимые пакеты, без рекомендованных
RUN apt-get install -y --no-install-recommends \
    build-essential \
    libncurses-dev \
    python3
```

**Экономия:** 20-30% размера от установленных пакетов

### .dockerignore

**Исключай ненужные файлы из build context:**

```
# .dockerignore
.git
.github
.kiro
docs/
tests/
artifacts/
*.log
*.md
.vscode
.idea
node_modules/
__pycache__/
*.pyc
dist/
build/
```

**Преимущества:**
- Уменьшение размера build context
- Ускорение передачи контекста в Docker daemon
- Предотвращение случайного копирования секретов

### Ускорение загрузки с axel

**Использование axel для параллельной загрузки:**

```bash
# Установка axel
apt-get install -y --no-install-recommends axel

# Загрузка с 32 потоками
axel -n 32 -a -o "$OUTPUT_FILE" "$URL"

# Опции:
# -n 32  : 32 параллельных соединения
# -a     : более компактный прогресс-бар
# -o     : выходной файл
```

**Ускорение:** ~2x по сравнению с curl для больших файлов (> 100MB)

**Важно:** Используй `--progress=plain` в docker build для избежания переполнения логов:

```bash
docker build --progress=plain -t image:tag .
```

## Параллельная сборка Docker образов

### Использование controlPwshProcess

**PowerShell скрипт для параллельной сборки:**

```powershell
# Список архитектур
$architectures = @(
    @{target="x86"; subtarget="64"},
    @{target="ath79"; subtarget="generic"},
    @{target="ramips"; subtarget="mt76x8"}
)

# Запуск параллельных сборок
foreach ($arch in $architectures) {
    $target = $arch.target
    $subtarget = $arch.subtarget
    
    Write-Host "Starting build for $target-$subtarget"
    
    # Запуск через Kiro controlPwshProcess
    kiro controlPwshProcess --action start `
        --command "docker build --build-arg SDK_TARGET=$target --build-arg SDK_SUBTARGET=$subtarget -t sdk:$target-$subtarget ." `
        --path "docker/sdk"
}

# Мониторинг процессов
Write-Host "Monitoring builds..."
kiro listProcesses
```

### Мониторинг параллельных сборок

```powershell
# Получить список процессов
$processes = kiro listProcesses | ConvertFrom-Json

# Проверить статус каждого
foreach ($proc in $processes.processes) {
    Write-Host "Process $($proc.processId): $($proc.status)"
    
    # Получить последние 20 строк вывода
    kiro getProcessOutput --processId $proc.processId --lines 20
}
```

### Ограничение параллелизма

**В GitHub Actions:**

```yaml
jobs:
  build-images:
    strategy:
      matrix:
        arch:
          - {target: x86, subtarget: 64}
          - {target: ath79, subtarget: generic}
          - {target: ramips, subtarget: mt76x8}
      max-parallel: 4  # Ограничение параллельных сборок
      fail-fast: false  # Продолжить при ошибке в одной сборке
```

**Рекомендации:**
- `max-parallel: 4` для GitHub Actions (ограничение ресурсов)
- `max-parallel: 8` для локальной сборки (если достаточно RAM)
- `fail-fast: false` для сборки всех архитектур даже при ошибке

### Агрегация результатов

```yaml
jobs:
  build-images:
    # ... matrix build ...
    
  aggregate-results:
    needs: build-images
    runs-on: ubuntu-24.04
    steps:
      - name: Check all builds succeeded
        run: |
          echo "All builds completed successfully"
      
      - name: List built images
        run: |
          docker images ghcr.io/*/openwrt-sdk --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"
```

## Валидация Docker образов

### Скрипт проверки размера

```bash
#!/bin/bash
# validate-docker-image-size.sh

set -euo pipefail

IMAGE=$1
MAX_SIZE_MB=${2:-2048}  # Default 2GB

echo "=== Validating Docker image size ==="
echo "Image: $IMAGE"
echo "Max size: ${MAX_SIZE_MB}MB"

# Получить размер в байтах
IMAGE_SIZE_BYTES=$(docker inspect "$IMAGE" --format='{{.Size}}')
MAX_SIZE_BYTES=$((MAX_SIZE_MB * 1024 * 1024))

# Человекочитаемый формат
IMAGE_SIZE_HUMAN=$(echo "$IMAGE_SIZE_BYTES" | numfmt --to=iec-i --suffix=B)

echo "Actual size: $IMAGE_SIZE_HUMAN ($IMAGE_SIZE_BYTES bytes)"

# Проверка
if [[ ${IMAGE_SIZE_BYTES} -gt ${MAX_SIZE_BYTES} ]]; then
    echo "❌ ERROR: Image size exceeds limit"
    echo "Limit: ${MAX_SIZE_MB}MB (${MAX_SIZE_BYTES} bytes)"
    exit 1
fi

echo "✅ Image size is within limit"
```

### Скрипт проверки содержимого

```bash
#!/bin/bash
# validate-docker-image-contents.sh

set -euo pipefail

IMAGE=$1

echo "=== Validating Docker image contents ==="
echo "Image: $IMAGE"

# Проверка SDK directory
echo "Checking SDK directory..."
if ! docker run --rm "$IMAGE" test -d /opt/openwrt-sdk; then
    echo "❌ ERROR: SDK directory not found"
    exit 1
fi
echo "✅ SDK directory exists"

# Проверка build tools
echo "Checking build tools..."
for tool in make gcc git python3; do
    if ! docker run --rm "$IMAGE" which "$tool" > /dev/null; then
        echo "❌ ERROR: $tool not found"
        exit 1
    fi
    echo "✅ $tool available"
done

# Проверка прав доступа
echo "Checking permissions..."
if ! docker run --rm "$IMAGE" bash -c "[ -w /opt/openwrt-sdk ]"; then
    echo "❌ ERROR: SDK directory not writable"
    exit 1
fi
echo "✅ SDK directory is writable"

# Проверка отсутствия временных файлов
echo "Checking for temporary files..."
TEMP_FILES=$(docker run --rm "$IMAGE" find /var/lib/apt/lists /tmp /var/tmp -type f 2>/dev/null | wc -l)
if [[ $TEMP_FILES -gt 0 ]]; then
    echo "⚠️  WARNING: Found $TEMP_FILES temporary files"
else
    echo "✅ No temporary files found"
fi

echo "=== Validation complete ==="
```

## Работа с GHCR (GitHub Container Registry)

### Формат тегов

```
ghcr.io/{owner}/{image}:{version}-{target}-{subtarget}-{tag}
```

**Примеры:**
- `ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest`
- `ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-abc12345`

### Стратегия тегирования

**Два тега для каждого образа:**

```bash
# 1. Latest tag (перезаписывается при каждой сборке)
docker tag local-image:latest ghcr.io/owner/image:23.05.5-x86-64-latest

# 2. SHA tag (уникальный для каждого коммита)
SHA=$(git rev-parse --short HEAD)
docker tag local-image:latest ghcr.io/owner/image:23.05.5-x86-64-$SHA

# Push обоих тегов
docker push ghcr.io/owner/image:23.05.5-x86-64-latest
docker push ghcr.io/owner/image:23.05.5-x86-64-$SHA
```

### Аутентификация в GHCR

**В GitHub Actions:**

```yaml
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

**Локально:**

```bash
# Создать Personal Access Token с правами write:packages
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Автоматическая очистка старых образов

**Правила очистки:**
- Образы старше 90 дней удаляются
- Сохраняются последние 10 версий на архитектуру
- Образы с тегом `latest` защищены
- Активно используемые образы защищены

**Workflow для очистки:**

```yaml
name: Cleanup Old Images

on:
  schedule:
    - cron: '0 0 * * 0'  # Еженедельно по воскресеньям
  workflow_dispatch:

jobs:
  cleanup:
    runs-on: ubuntu-24.04
    steps:
      - name: Delete old images
        uses: actions/delete-package-versions@v5
        with:
          package-name: 'openwrt-sdk'
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: false
          token: ${{ secrets.GITHUB_TOKEN }}
```

## WSL2 и Docker Desktop на Windows

### Настройка WSL2

```powershell
# Установить WSL2 как default
wsl --set-default-version 2

# Проверить версию
wsl --list --verbose

# Конвертировать существующий дистрибутив в WSL2
wsl --set-version Ubuntu 2
```

### Docker Desktop интеграция

**Docker Desktop использует собственный WSL дистрибутив:**
- `docker-desktop`
- `docker-desktop-data`

**Остановка других WSL дистрибутивов для освобождения ресурсов:**

```powershell
# Остановить Ubuntu WSL
wsl --terminate Ubuntu

# Проверить запущенные дистрибутивы
wsl --list --running
```

### Проверка интеграции

```powershell
# Проверить Docker из WSL
wsl docker ps

# Проверить Docker из PowerShell
docker ps

# Проверить версию Docker
docker version
```

### File sharing для volume mounts

**Настройка в Docker Desktop:**
1. Settings → Resources → File Sharing
2. Добавить диск C:\ если его нет
3. Apply & Restart

**Проверка монтирования:**

```powershell
# PowerShell
docker run --rm -v ${PWD}:/test alpine ls /test

# CMD
docker run --rm -v %CD%:/test alpine ls /test

# Git Bash
docker run --rm -v "$(pwd):/test" alpine ls /test
```

## Метрики производительности

### Время сборки

**Без Docker SDK образов:**
- Pull/Download SDK: 1-2 мин
- Extract SDK: 30-60 сек
- Setup SDK: 30 сек
- Build package: 1-2 мин
- **Total: 3-5 мин**

**С Docker SDK образами:**
- Pull image: 30 сек
- Setup: 10 сек
- Build package: 1-2 мин
- **Total: 1.5-2.5 мин**

**Экономия: 40-60%**

### Параллельная сборка

- Последовательная сборка 8 архитектур: ~2 часа
- Параллельная сборка 8 архитектур: ~20-30 минут
- **Ускорение: 4-6x**

### Использование хранилища

- Размер одного образа: ~1.5GB
- Количество архитектур: 8
- Версий на архитектуру: ~10
- **Итого: ~120GB в GHCR**
