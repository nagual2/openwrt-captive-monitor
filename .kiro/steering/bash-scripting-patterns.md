# Паттерны bash скриптов

## Обязательные флаги безопасности

### set -euo pipefail

**Всегда начинай bash скрипты с:**

```bash
#!/bin/bash
set -euo pipefail
```

**Что делают флаги:**
- `set -e` - завершить скрипт при любой ошибке (exit code != 0)
- `set -u` - ошибка при использовании неопределенных переменных
- `set -o pipefail` - ошибка в любой части pipeline

**Пример:**
```bash
#!/bin/bash
set -euo pipefail

# Скрипт завершится при ошибке
curl -fsSL https://example.com/file.tar.gz | tar -xz

# Скрипт завершится при использовании неопределенной переменной
echo "Version: $VERSION"

# Скрипт завершится при ошибке в любой части pipeline
cat file.txt | grep pattern | wc -l
```

## Валидация входных параметров

### Проверка обязательных параметров

```bash
#!/bin/bash
set -euo pipefail

# Проверка наличия параметров
if [ $# -lt 2 ]; then
    echo "Usage: $0 <target> <subtarget>"
    exit 1
fi

TARGET=$1
SUBTARGET=$2

# Проверка значений
if [ -z "$TARGET" ] || [ -z "$SUBTARGET" ]; then
    echo "ERROR: Target and subtarget cannot be empty"
    exit 1
fi
```

### Проверка переменных окружения

```bash
# Проверка обязательных переменных
: "${OPENWRT_VERSION:?ERROR: OPENWRT_VERSION is not set}"
: "${SDK_TARGET:?ERROR: SDK_TARGET is not set}"

# Или с дефолтными значениями
OPENWRT_VERSION=${OPENWRT_VERSION:-23.05.5}
SDK_TARGET=${SDK_TARGET:-x86}
```

## Обработка ошибок

### Trap для cleanup

```bash
#!/bin/bash
set -euo pipefail

# Временные файлы
TEMP_DIR=$(mktemp -d)

# Cleanup функция
cleanup() {
    local exit_code=$?
    echo "Cleaning up..."
    rm -rf "$TEMP_DIR"
    exit $exit_code
}

# Вызвать cleanup при выходе
trap cleanup EXIT INT TERM

# Основная логика
echo "Working in $TEMP_DIR"
# ... работа с временными файлами ...
```

### Понятные сообщения об ошибках

```bash
error() {
    echo "ERROR: $*" >&2
    exit 1
}

warn() {
    echo "WARNING: $*" >&2
}

info() {
    echo "INFO: $*"
}

# Использование
[ -f "$CONFIG_FILE" ] || error "Config file not found: $CONFIG_FILE"
[ -d "$SDK_DIR" ] || warn "SDK directory does not exist: $SDK_DIR"
info "Starting build process..."
```

### Exit codes

```bash
# Стандартные exit codes
EXIT_SUCCESS=0
EXIT_GENERAL_ERROR=1
EXIT_INVALID_ARGS=2
EXIT_FILE_NOT_FOUND=3
EXIT_NETWORK_ERROR=4

# Использование
if ! curl -fsSL "$URL" -o "$OUTPUT"; then
    echo "ERROR: Failed to download file"
    exit $EXIT_NETWORK_ERROR
fi
```

## Retry логика для сетевых операций

### Экспоненциальная задержка

```bash
retry_with_backoff() {
    local max_retries=15
    local retry_count=0
    local wait_time=1
    
    while [ $retry_count -lt $max_retries ]; do
        if "$@"; then
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        wait_time=$((2 ** retry_count))
        [ $wait_time -gt 60 ] && wait_time=60  # Max 60 секунд
        
        echo "Retry $retry_count/$max_retries after ${wait_time}s..."
        sleep $wait_time
    done
    
    echo "ERROR: Failed after $max_retries attempts"
    return 1
}

# Использование
retry_with_backoff curl -fsSL "$URL" -o "$OUTPUT"
```

### Полный пример с retry

```bash
download_with_retry() {
    local url=$1
    local output=$2
    local max_retries=15
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -fsSL "$url" -o "$output"; then
            echo "Download successful"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        wait_time=$((2 ** retry_count))
        [ $wait_time -gt 60 ] && wait_time=60
        
        echo "Retry $retry_count/$max_retries after ${wait_time}s..."
        sleep $wait_time
    done
    
    echo "ERROR: Failed to download after $max_retries attempts"
    echo "URL: $url"
    return 1
}
```

## Curl опции для надежной загрузки

### Рекомендуемые опции

```bash
curl \
  -f \                      # Fail on HTTP errors (4xx, 5xx)
  -s \                      # Silent mode (no progress bar)
  -S \                      # Show errors even in silent mode
  -L \                      # Follow redirects
  --retry 15 \              # Retry up to 15 times
  --retry-delay 10 \        # Wait 10s between retries
  --retry-all-errors \      # Retry on all errors, not just transient
  --max-time 3600 \         # Maximum time for operation (1 hour)
  --connect-timeout 60 \    # Connection timeout (60s)
  --speed-limit 1000 \      # Minimum speed (1KB/s)
  --speed-time 30 \         # Time to maintain minimum speed (30s)
  -C - \                    # Continue interrupted download
  -o "$output" \            # Output file
  "$url"
```

### Проверка HTTP статуса

```bash
# Получить HTTP статус код
http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")

if [ "$http_code" -eq 200 ]; then
    echo "URL is accessible"
elif [ "$http_code" -eq 404 ]; then
    echo "ERROR: File not found (404)"
    exit 1
else
    echo "ERROR: HTTP $http_code"
    exit 1
fi
```

## Диагностика ошибок загрузки SDK

### При ошибке 404

```bash
download_sdk() {
    local url=$1
    local output=$2
    local base_url=$(dirname "$url")
    
    if ! curl -fsSL "$url" -o "$output"; then
        local exit_code=$?
        
        if [ $exit_code -eq 22 ]; then  # HTTP 404
            echo "ERROR: SDK file not found"
            echo "URL: $url"
            echo ""
            echo "Available SDK files in directory:"
            curl -fsSL "${base_url}/" | grep -o 'href="[^"]*sdk[^"]*"' | cut -d'"' -f2 | sort
            echo ""
            echo "SHA256 sums:"
            curl -fsSL "${base_url}/sha256sums" | grep sdk || echo "No sha256sums found"
        else
            echo "ERROR: Failed to download SDK (exit code: $exit_code)"
            echo "URL: $url"
        fi
        
        return 1
    fi
    
    return 0
}
```

### Маппинг архитектур на MUSL суффиксы

```bash
determine_musl_suffix() {
    local target=$1
    
    case "$target" in
        ipq40xx|ipq806x)
            echo "_musl_eabi"
            ;;
        *)
            echo "_musl"
            ;;
    esac
}

# Использование
SDK_TARGET="x86"
MUSL_SUFFIX=$(determine_musl_suffix "$SDK_TARGET")
echo "MUSL suffix for $SDK_TARGET: $MUSL_SUFFIX"
```

### Формат имени файла SDK

```bash
construct_sdk_filename() {
    local version=$1
    local target=$2
    local subtarget=$3
    local gcc_version=${4:-12.3.0}
    
    local musl_suffix=$(determine_musl_suffix "$target")
    
    echo "openwrt-sdk-${version}-${target}-${subtarget}_gcc-${gcc_version}${musl_suffix}.Linux-x86_64.tar.xz"
}

# Пример
# openwrt-sdk-23.05.5-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
SDK_FILENAME=$(construct_sdk_filename "23.05.5" "x86" "64")
echo "SDK filename: $SDK_FILENAME"
```

## Форматирование и линтинг

### shfmt - форматирование bash скриптов

```bash
# Форматирование одного файла
shfmt -i 2 -ci -sr -w script.sh

# Форматирование всех bash скриптов в директории
shfmt -i 2 -ci -sr -w *.sh

# Опции:
# -i 2  : indent 2 spaces
# -ci   : case indent
# -sr   : space redirects (> file вместо >file)
# -w    : write to file (без -w только проверка)

# Проверка без изменения файлов
shfmt -i 2 -ci -sr -d script.sh
```

### shellcheck - статический анализ

```bash
# Проверка одного файла
shellcheck script.sh

# Проверка всех bash скриптов
shellcheck *.sh

# Игнорировать конкретные правила
shellcheck -e SC2086 -e SC2046 script.sh

# Вывод в формате JSON
shellcheck -f json script.sh

# Типичные правила для игнорирования:
# SC2086 - Double quote to prevent globbing and word splitting
# SC2046 - Quote this to prevent word splitting
# SC2155 - Declare and assign separately to avoid masking return values
```

### Условное форматирование

```bash
# В SDK Docker контейнерах нет git репозитория
# Форматирование может падать, используй условную проверку

format_scripts() {
    if [ -d .git ]; then
        echo "Formatting bash scripts..."
        shfmt -i 2 -ci -sr -w *.sh
    else
        echo "Skipping formatting (not a git repository)"
    fi
}
```

### Интеграция в CI

```yaml
# .github/workflows/ci.yml
jobs:
  lint-bash:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
      
      - name: Install shellcheck and shfmt
        run: |
          sudo apt-get update
          sudo apt-get install -y shellcheck
          go install mvdan.cc/sh/v3/cmd/shfmt@latest
      
      - name: Run shellcheck
        run: shellcheck *.sh scripts/*.sh
      
      - name: Check formatting
        run: shfmt -i 2 -ci -sr -d *.sh scripts/*.sh
```

## Работа с JSON в bash

### jq для парсинга JSON

```bash
# Извлечь значение
version=$(echo "$json" | jq -r '.version')

# Извлечь массив
items=$(echo "$json" | jq -r '.items[]')

# Фильтрация
active_items=$(echo "$json" | jq -r '.items[] | select(.active == true)')

# Создать JSON
json=$(jq -n \
    --arg name "test" \
    --arg version "1.0.0" \
    '{name: $name, version: $version}')
```

### Проверка валидности JSON

```bash
if echo "$json" | jq empty 2>/dev/null; then
    echo "Valid JSON"
else
    echo "Invalid JSON"
    exit 1
fi
```

## Работа с YAML в bash

### yq для парсинга YAML

```bash
# Извлечь значение
version=$(yq eval '.version' config.yaml)

# Изменить значение
yq eval '.version = "2.0.0"' -i config.yaml

# Извлечь массив
items=$(yq eval '.items[]' config.yaml)
```

## Цветной вывод

### ANSI escape codes

```bash
# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
log_info() {
    echo -e "${BLUE}INFO:${NC} $*"
}

log_success() {
    echo -e "${GREEN}SUCCESS:${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}WARNING:${NC} $*"
}

log_error() {
    echo -e "${RED}ERROR:${NC} $*" >&2
}

# Использование
log_info "Starting build process..."
log_success "Build completed successfully"
log_warn "Using default configuration"
log_error "Failed to download file"
```

## Параллельное выполнение

### GNU parallel

```bash
# Установка
sudo apt-get install parallel

# Параллельное выполнение команд
parallel echo "Processing {}" ::: file1 file2 file3

# С количеством параллельных процессов
parallel -j 4 process_file {} ::: *.txt

# Из файла со списком
parallel -j 4 process_file {} :::: files.txt
```

### Bash background jobs

```bash
# Запуск в фоне
process_file file1.txt &
process_file file2.txt &
process_file file3.txt &

# Дождаться завершения всех
wait

# Дождаться конкретного процесса
pid=$!
wait $pid
```