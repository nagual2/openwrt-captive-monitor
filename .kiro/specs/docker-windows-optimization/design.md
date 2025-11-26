# Design Document: Docker Windows Optimization

## Overview

Данный документ описывает оптимизацию Docker образов OpenWrt SDK для эффективной работы на Windows с Docker Desktop. Основные цели:

1. Уменьшение размера образа с 3.55GB до менее 2GB
2. Исправление проверки размера образа в build-local.sh
3. Добавление Windows-специфичной документации
4. Улучшение валидации образов

Текущая реализация уже работает на Windows через Docker Desktop с WSL2 backend, но требует оптимизации размера и улучшения пользовательского опыта.

## Architecture

### Компоненты системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Host System                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Docker Desktop (WSL2)                     │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         OpenWrt SDK Container                    │  │  │
│  │  │  ┌──────────────────────────────────────────┐   │  │  │
│  │  │  │  /opt/openwrt-sdk (extracted SDK)        │   │  │  │
│  │  │  │  - Makefile, scripts, build tools        │   │  │  │
│  │  │  └──────────────────────────────────────────┘   │  │  │
│  │  │  ┌──────────────────────────────────────────┐   │  │  │
│  │  │  │  Build Dependencies                       │   │  │  │
│  │  │  │  - gcc, make, python3, git               │   │  │  │
│  │  │  └──────────────────────────────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Volume Mount: C:\git\project -> /workspace    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Multi-stage Build Process

```
Stage 1: sdk-downloader
├── Base: ubuntu:24.04
├── Install: curl, ca-certificates, xz-utils
├── Download: OpenWrt SDK archive
├── Verify: SHA256 checksum
└── Extract: SDK to /opt/openwrt-sdk

Stage 2: final
├── Base: ubuntu:24.04
├── Install: Build dependencies (gcc, make, etc.)
├── Copy: SDK from stage 1
├── Create: Non-root builder user
└── Cleanup: All temporary files and caches
```

## Components and Interfaces

### 1. Dockerfile

**Ответственность:** Определение структуры Docker образа

**Оптимизации:**
- Объединение RUN команд для уменьшения слоев
- Очистка кэшей в том же слое, где они создаются
- Удаление временных файлов до завершения слоя
- Минимизация установленных пакетов

**Интерфейс (Build Args):**
```dockerfile
ARG UBUNTU_VERSION=24.04
ARG OPENWRT_VERSION=23.05.5
ARG SDK_TARGET=x86
ARG SDK_SUBTARGET=64
```

### 2. download-sdk.sh

**Ответственность:** Загрузка и верификация OpenWrt SDK

**Функции:**
- `determine_musl_suffix()` - определение суффикса для архитектуры
- `download_with_retry()` - загрузка с повторными попытками
- `verify_checksum()` - проверка SHA256
- `list_available_files()` - диагностика доступных файлов

**Интерфейс (Environment Variables):**
```bash
OPENWRT_VERSION  # Версия OpenWrt
SDK_TARGET       # Целевая архитектура
SDK_SUBTARGET    # Подархитектура
```

### 3. build-local.sh

**Ответственность:** Локальная сборка образов для разработчиков

**Функции:**
- `log_info()`, `log_warn()`, `log_error()` - цветной вывод
- `usage()` - справка по использованию
- Парсинг аргументов командной строки
- Сборка образа с docker build
- Валидация размера и содержимого
- Опциональный push в registry

**Интерфейс (CLI):**
```bash
-t, --target TARGET         # SDK target
-s, --subtarget SUBTARGET   # SDK subtarget
-v, --version VERSION       # OpenWrt version
-p, --push                  # Push to registry
```

### 4. Validation Scripts

**validate-docker-image-size.sh:**
- Проверка размера образа в байтах
- Сравнение с лимитом (2GB = 2147483648 bytes)
- Вывод предупреждений при превышении

**validate-docker-image-contents.sh:**
- Проверка наличия /opt/openwrt-sdk
- Проверка build tools (make, gcc, git)
- Проверка прав доступа для builder user
- Проверка переменных окружения

## Data Models

### Docker Image Metadata

```yaml
labels:
  org.opencontainers.image.title: "OpenWrt SDK 23.05.5"
  org.opencontainers.image.description: "OpenWrt SDK for x86/64"
  org.opencontainers.image.version: "23.05.5"
  org.opencontainers.image.source: "https://github.com/nagual2/openwrt-captive-monitor"
  openwrt.version: "23.05.5"
  openwrt.target: "x86"
  openwrt.subtarget: "64"
```

### Image Tags

```
Format: {registry}/{image}:{version}-{target}-{subtarget}-{tag}

Examples:
- ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest
- ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-f6deee98
```

### Build Context

```
.dockerignore excludes:
- .git, .github, .kiro
- docs/, tests/
- artifacts/, build artifacts
- IDE files, logs, temporary files
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Build success on Windows
*For any* valid combination of SDK target and subtarget, building the Docker image on Windows with Docker Desktop should complete successfully without errors
**Validates: Requirements 1.1**

### Property 2: Progress information display
*For any* build execution, the output should contain progress information and final image size in human-readable format
**Validates: Requirements 1.2**

### Property 3: Diagnostic information on failure
*For any* build failure, the system should output diagnostic information including the failure reason and context
**Validates: Requirements 1.3**

### Property 4: Image size compliance
*For any* built Docker image, the size should be less than 2GB (2147483648 bytes)
**Validates: Requirements 2.1**

### Property 5: Temporary files removal
*For any* built Docker image, the following paths should not exist: /var/lib/apt/lists/*, /tmp/*, /var/tmp/*, *.tar.xz in /opt/openwrt-sdk
**Validates: Requirements 2.2, 2.3**

### Property 6: Size parsing accuracy
*For any* Docker image, the build script should correctly parse and report the size in both bytes and human-readable format
**Validates: Requirements 3.1, 3.4**

### Property 7: SDK directory presence
*For any* built Docker image, running `test -d /opt/openwrt-sdk` in a container should return success
**Validates: Requirements 6.1**

### Property 8: Build tools availability
*For any* built Docker image, the commands `make --version`, `gcc --version`, `git --version`, and `python3 --version` should execute successfully in a container
**Validates: Requirements 6.2**

### Property 9: Builder user permissions
*For any* built Docker image, the /opt/openwrt-sdk directory should be owned by the builder user (UID 1000) with read/write permissions
**Validates: Requirements 6.3**

### Property 10: Validation error reporting
*For any* validation failure, the validation script should output a specific error message identifying the missing or incorrect component
**Validates: Requirements 6.4**

## Error Handling

### Build Errors

**SDK Download Failures:**
- Retry logic: 15 attempts with exponential backoff (max 60s)
- Diagnostic output: List available files on server
- Clear error messages with URL and network troubleshooting hints

**Docker Build Failures:**
- Capture and display full build output
- Identify failing layer and command
- Suggest common fixes (disk space, network, permissions)

**Size Validation Failures:**
- Display actual size vs. limit
- Suggest optimization strategies
- Continue build but warn user

### Runtime Errors

**Volume Mount Issues:**
- Document Windows path format: `C:\path` or `/c/path`
- Explain Docker Desktop file sharing settings
- Provide troubleshooting steps for permission errors

**Container Execution Failures:**
- Check Docker Desktop status
- Verify WSL2 integration
- Validate image integrity

## Testing Strategy

### Unit Tests

**Dockerfile Validation:**
- Verify RUN commands are combined appropriately
- Check for cleanup commands in each layer
- Validate --no-install-recommends flag usage
- Confirm .dockerignore excludes unnecessary files

**Script Validation:**
- Test size parsing with known values
- Verify error handling for invalid inputs
- Check output format for progress information

### Integration Tests

**Build Process:**
- Build image for x86/64 architecture
- Verify build completes without errors
- Check final image size < 2GB
- Validate image can run containers

**Volume Mounting:**
- Create test file in Windows workspace
- Mount workspace in container
- Verify file is accessible from container
- Test read/write operations

**Validation Scripts:**
- Run validate-docker-image-size.sh on test image
- Run validate-docker-image-contents.sh on test image
- Verify scripts detect missing components
- Check error messages are specific

### Windows-Specific Tests

**Docker Desktop Integration:**
- Verify build works with WSL2 backend
- Test with different Docker Desktop versions
- Validate path conversion for volume mounts
- Check PowerShell script execution

**Documentation Validation:**
- Verify README contains Windows section
- Check PowerShell command examples are correct
- Validate path format examples
- Ensure WSL/Docker exec instructions are clear

## Implementation Notes

### Size Optimization Strategies

1. **Layer Reduction:**
   - Combine related RUN commands with `&&`
   - Use multi-line format with `\` for readability

2. **Cache Cleanup:**
   ```dockerfile
   RUN apt-get update && \
       apt-get install -y --no-install-recommends pkg1 pkg2 && \
       rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
   ```

3. **SDK Extraction:**
   ```dockerfile
   RUN tar -C /opt/openwrt-sdk --strip-components=1 -xf sdk.tar.xz && \
       rm -f sdk.tar.xz sha256sums
   ```

4. **Build Context:**
   - Comprehensive .dockerignore to exclude unnecessary files
   - Reduces context size and build time

### Windows Path Handling

**PowerShell:**
```powershell
# Use ${PWD} for current directory
docker run -v ${PWD}:/workspace image

# Or use absolute path
docker run -v C:\git\project:/workspace image
```

**CMD:**
```cmd
# Use %CD% for current directory
docker run -v %CD%:/workspace image
```

**Git Bash:**
```bash
# Use $(pwd) with proper escaping
docker run -v "$(pwd):/workspace" image
```

### Validation Implementation

**Size Check Logic:**
```bash
IMAGE_SIZE_BYTES=$(docker inspect "$IMAGE" --format='{{.Size}}')
MAX_SIZE_BYTES=$((2 * 1024 * 1024 * 1024))  # 2GB

if [[ ${IMAGE_SIZE_BYTES} -gt ${MAX_SIZE_BYTES} ]]; then
    echo "ERROR: Image size exceeds 2GB limit"
    exit 1
fi
```

**Contents Check:**
```bash
# Check SDK directory
docker run --rm "$IMAGE" test -d /opt/openwrt-sdk || exit 1

# Check build tools
docker run --rm "$IMAGE" bash -c "make --version && gcc --version" || exit 1

# Check permissions
docker run --rm "$IMAGE" bash -c "[ -w /opt/openwrt-sdk ]" || exit 1
```

## Windows-Specific Documentation

### Setup Requirements

1. **Docker Desktop:**
   - Version 4.0+ with WSL2 backend
   - Enable WSL2 integration in settings
   - Allocate sufficient resources (4GB+ RAM, 2+ CPUs)

2. **WSL2:**
   - Windows 10 version 2004+ or Windows 11
   - WSL2 installed and set as default
   - Ubuntu or other Linux distribution installed

3. **Git:**
   - Git for Windows with proper line ending configuration
   - Recommended: `core.autocrlf=input`

### Building Images on Windows

**Using PowerShell:**
```powershell
# Navigate to project directory
cd C:\git\openwrt-captive-monitor

# Build image using bash script (requires Git Bash or WSL)
bash docker/sdk/build-local.sh --target x86 --subtarget 64

# Or use docker build directly
docker build `
  --build-arg OPENWRT_VERSION=23.05.5 `
  --build-arg SDK_TARGET=x86 `
  --build-arg SDK_SUBTARGET=64 `
  -t openwrt-sdk:local `
  -f docker/sdk/Dockerfile `
  .
```

**Using CMD:**
```cmd
REM Navigate to project directory
cd C:\git\openwrt-captive-monitor

REM Build using docker directly
docker build ^
  --build-arg OPENWRT_VERSION=23.05.5 ^
  --build-arg SDK_TARGET=x86 ^
  --build-arg SDK_SUBTARGET=64 ^
  -t openwrt-sdk:local ^
  -f docker/sdk/Dockerfile ^
  .
```

### Running Containers on Windows

**Mount workspace:**
```powershell
# PowerShell
docker run --rm -v ${PWD}:/workspace openwrt-sdk:local ls /workspace

# CMD
docker run --rm -v %CD%:/workspace openwrt-sdk:local ls /workspace
```

**Interactive shell:**
```powershell
docker run -it --rm openwrt-sdk:local /bin/bash
```

**Build package:**
```powershell
docker run --rm `
  -v ${PWD}:/workspace `
  -w /opt/openwrt-sdk `
  openwrt-sdk:local `
  bash -c "cp -r /workspace/package/openwrt-captive-monitor package/ && make package/openwrt-captive-monitor/compile"
```

### Troubleshooting

**Issue: "Error response from daemon: invalid mount config"**
- Solution: Check path format, use forward slashes or proper escaping
- Example: `C:/git/project` or `C:\git\project` (PowerShell handles both)

**Issue: "Permission denied" when accessing mounted files**
- Solution: Check Docker Desktop file sharing settings
- Enable file sharing for the drive containing your project

**Issue: "No space left on device"**
- Solution: Increase Docker Desktop disk size in settings
- Clean up unused images: `docker system prune -a`

**Issue: Build script fails with "bash: command not found"**
- Solution: Install Git Bash or use WSL to run bash scripts
- Alternative: Use docker build command directly in PowerShell/CMD
