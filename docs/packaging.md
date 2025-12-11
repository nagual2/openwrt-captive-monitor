# Packaging and Distribution Guide

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---


This guide covers the complete workflow for building, packaging, and distributing the OpenWrt Captive Monitor package.

## Overview

The project uses OpenWrt's native packaging system with custom tooling to simplify local builds and release automation. The packaging structure follows OpenWrt conventions and supports both development and production workflows.

## Package Structure

```
package/
├── Makefile.template           # Template for new packages
└── openwrt-captive-monitor/    # Main package definition
    ├── Makefile                # OpenWrt package metadata
    └── files/                  # Package payload
        ├── etc/
        │   ├── config/
        │   ├── init.d/
        │   └── uci-defaults/
        └── usr/
            └── sbin/
```

## Local Development Builds

### Prerequisites

To build the .ipk package locally, install the required tools:

```bash
# On Ubuntu 24.04+ (Noble) and newer:
# Install host deps and opkg-utils from OpenWrt upstream
sudo apt-get update
sudo apt-get install -y --no-install-recommends gawk tar gzip xz-utils zstd coreutils findutils file make rsync git

git clone --depth=1 https://git.openwrt.org/project/opkg-utils.git tools/opkg-utils
sudo install -m0755 tools/opkg-utils/opkg-build /usr/local/bin/opkg-build
sudo install -m0755 tools/opkg-utils/opkg-unbuild /usr/local/bin/opkg-unbuild
sudo install -m0755 tools/opkg-utils/opkg-make-index /usr/local/bin/opkg-make-index

# Or simply use the helper script in this repo:
sh ./scripts/setup-opkg-utils.sh

# On older Ubuntu/Debian releases where opkg-utils is still available in apt:
# sudo apt-get install -y opkg-utils gzip coreutils tar

# opkg-utils provides:
#   - opkg-build: Creates .ipk package files
#   - opkg-make-index: Generates package indexes
# Other tools:
#   - gzip: Compression for package index
#   - coreutils: Provides md5sum, sha256sum, stat for checksums
#   - tar: Archive tool for package data
```

### Quick Build

```bash
## Build package using defaults
./scripts/build_ipk.sh

## Output: dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk
```

### Custom Builds

```bash
## Override maintainer information
./scripts/build_ipk.sh \
  --maintainer "Your Name" \
  --maintainer-email "your.email@example.com"

## Use custom SPDX license identifier
./scripts/build_ipk.sh --spdx-id "MIT"

## Build for specific architecture
./scripts/build_ipk.sh --arch "mips_24kc"

## Custom output directory
./scripts/build_ipk.sh --feed-root "./my-feed"
```

### Release Mode

Release mode generates publication-ready artifacts with checksums and metadata:

```bash
./scripts/build_ipk.sh --release-mode
```

Release mode provides:
- Detailed checksum tables (MD5, SHA256)
- JSON metadata for automation
- Feed setup instructions
- Semantic version-based naming

## Package Metadata

### OpenWrt Makefile Fields

| Field | Value | Description |
|-------|-------|-------------|
| `PKG_NAME` | `openwrt-captive-monitor` | Package identifier |
| `PKG_VERSION` | `1.0.3` | Semantic version |
| `PKG_RELEASE` | `1` | Package release number |
| `PKG_LICENSE` | `MIT` | SPDX license identifier |
| `PKG_LICENSE_FILES` | `LICENSE` | License file reference |
| `PKG_MAINTAINER` | `OpenWrt Captive Monitor Team` | Maintainer contact |
| `PKG_SOURCE_URL` | GitHub repository URL | Source location |
| `PKG_SOURCE_PROTO` | `git` | Source protocol |
| `PKG_SOURCE_VERSION` | `v$(PKG_VERSION)` | Source version tag |

### Package Definition Fields

| Field | Value | Description |
|-------|-------|-------------|
| `SECTION` | `net` | Package section |
| `CATEGORY` | `Network` | OpenWrt category |
| `SUBMENU` | `Captive Portals` | Submenu classification |
| `TITLE` | Package title | Short description |
| `DEPENDS` | `+dnsmasq +curl` | Required packages |
| `URL` | GitHub repository URL | Project homepage |

## CI/CD Integration

### GitHub Actions Workflow

The project includes automated validation and packaging via GitHub Actions:

```yaml
## .github/workflows/ci.yml
- Runs linting and tests
- Builds the package with the OpenWrt SDK
- Uploads `.ipk` and feed metadata
- Attaches release assets on tag pushes
```

### Build Output

| Artifact | Description |
|----------|-------------|
| `.ipk` | Installable OpenWrt package |
| `Packages` | Feed index |
| `Packages.gz` | Compressed feed index |
| `build.log` | Verbose SDK build log |

## Release Workflow

### 1. Version Bump

Update version in `package/openwrt-captive-monitor/Makefile`:

```makefile
PKG_VERSION:=1.0.2
PKG_RELEASE:=1
```

### 2. Build Release Artifacts

```bash
## Build with release mode
./scripts/build_ipk.sh --release-mode

## This creates:
## - dist/opkg/all/openwrt-captive-monitor_1.0.2-1_all.ipk
## - dist/opkg/all/Packages
## - dist/opkg/all/Packages.gz
## - dist/opkg/all/release-metadata.json
```

### 3. Tag and Push

```bash
git tag -a v1.0.2 -m "Release v1.0.2"
git push origin v1.0.2
```

### 4. GitHub Release

1. Go to GitHub Releases page
2. Create new release from tag `v1.0.2`
3. Upload artifacts from `dist/opkg/all/`
4. Use release metadata for description

## Custom OPKG Feed

### Local Feed Setup

1. **Create feed directory structure**:
   ```bash
   mkdir -p /path/to/feed/all
   cp dist/opkg/all/* /path/to/feed/all/
   ```

2. **Configure OpenWrt device**:
   ```bash
   # Add to /etc/opkg/customfeeds.conf
   echo "src/gz captive-monitor file:///path/to/feed" >> /etc/opkg/customfeeds.conf
   
   # Update package lists
   opkg update
   
   # Install package
   opkg install openwrt-captive-monitor
   ```

### GitHub Pages Feed

1. **Create `gh-pages` branch**:
   ```bash
   git checkout --orphan gh-pages
   git reset --hard
   ```

2. **Add package files**:
   ```bash
   mkdir -p all
   cp dist/opkg/all/* all/
   git add all/
   git commit -m "Add package v1.0.2"
   git push origin gh-pages
   ```

3. **Configure devices**:
   ```bash
   echo "src/gz captive-monitor https://username.github.io/openwrt-captive-monitor" >> /etc/opkg/customfeeds.conf
   opkg update
   ```

## Automated Distribution

### Release Script Example

```bash
#!/bin/bash
## release.sh - Automated release script

set -eu

VERSION=${1:-"1.0.2"}
MAINTAINER=${2:-"OpenWrt Captive Monitor Team"}
EMAIL=${3:-"team@example.com"}

## Update version in Makefile
sed -i "s/PKG_VERSION:=.*/PKG_VERSION:=$VERSION/" package/openwrt-captive-monitor/Makefile

## Build release artifacts
./scripts/build_ipk.sh \
  --release-mode \
  --maintainer "$MAINTAINER" \
  --maintainer-email "$EMAIL"

## Create GitHub release
gh release create "v$VERSION" \
  --title "Release v$VERSION" \
  --notes "Automated release v$VERSION" \
  dist/opkg/all/*.ipk \
  dist/opkg/all/Packages* \
  dist/opkg/all/release-metadata.json
```

### CI/CD Release Automation

The GitHub Actions workflow can be extended to:

1. **Auto-create releases** when tags are pushed
2. **Upload artifacts** to GitHub Releases
3. **Update GitHub Pages** feed
4. **Notify downstream systems**

```yaml
## Example release job
- name: Create Release
  if: startsWith(github.ref, 'refs/tags/')
  uses: actions/create-release@v1
  with:
    tag_name: ${{ github.ref }}
    release_name: Release ${{ github.ref }}
    draft: false
    prerelease: false
```

## Package Signing (Optional)

For production feeds, consider package signing:

```bash
## Generate signing key
openssl genrsa -out opkg.key 2048
openssl rsa -in opkg.key -pubout > opkg.pub

## Sign packages
opkg-sign key opkg.key dist/opkg/all/*.ipk

## Update feed with signatures
opkg-make-index -s opkg.pub -p dist/opkg/all/Packages dist/opkg/all/
```

## Quality Assurance

### Package Validation

```bash
## Verify package structure
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk

## Check control file
ar p dist/opkg/all/openwrt-captive-monitor_*.ipk control.tar.gz | tar -Oxz ./control

## Validate dependencies
opkg info ./dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Linting

```bash
## Check OpenWrt package compliance
openwrt-package-lint package/openwrt-captive-monitor/Makefile

## Verify file permissions
find package/openwrt-captive-monitor/files -type f -exec ls -la {} \;
```

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure `dnsmasq` and `curl` are available
2. **Architecture mismatch**: Use correct `--arch` parameter
3. **Permission denied**: Check executable permissions in `files/`
4. **Feed not updating**: Verify `Packages.gz` integrity

### Debug Commands

```bash
## Debug package build
./scripts/build_ipk.sh --arch all 2>&1 | tee build.log

## Test feed locally
python3 -m http.server 8080 --directory dist/opkg/all/
## Then: echo "src/gz test http://localhost:8080" >> /etc/opkg/customfeeds.conf
```

## References

- [OpenWrt Package Development Guide](https://openwrt.org/docs/guide-developer/packages)
- [OPKG Package Manager](https://openwrt.org/docs/techref/opkg)
- [SPDX License List](https://spdx.org/licenses/)
- [GitHub Actions for OpenWrt](https://github.com/openwrt/packages)

---

*Last updated: 2025-10-30*

---

<a name="русский"></a>

# Руководство по упаковке и дистрибуции

---

## 🌐 Language / Язык

[English](#packaging-and-distribution-guide) | **Русский**

---

Это руководство охватывает полный рабочий процесс сборки, упаковки и дистрибуции пакета OpenWrt Captive Monitor.

## Обзор

Проект использует встроенную систему пакетирования OpenWrt с пользовательскими инструментами для упрощения локальных сборок и автоматизации релизов. Структура пакетирования соответствует соглашениям OpenWrt и поддерживает как разработческие, так и продакшн-процессы.

## Структура пакета

```
package/
├── Makefile.template           # Шаблон для новых пакетов
└── openwrt-captive-monitor/    # Основное определение пакета
    ├── Makefile                # Метаданные пакета OpenWrt
    └── files/                  # Содержимое пакета
        ├── etc/
        │   ├── config/
        │   ├── init.d/
        │   └── uci-defaults/
        └── usr/
            └── sbin/
```

## Локальные разработческие сборки

### Предварительные требования

Для сборки .ipk пакета локально установите необходимые инструменты:

```bash
# На Ubuntu 24.04+ (Noble) и новее:
# Установите зависимости хоста и opkg-utils из исходников OpenWrt
sudo apt-get update
sudo apt-get install -y --no-install-recommends gawk tar gzip xz-utils zstd coreutils findutils file make rsync git

git clone --depth=1 https://git.openwrt.org/project/opkg-utils.git tools/opkg-utils
sudo install -m0755 tools/opkg-utils/opkg-build /usr/local/bin/opkg-build
sudo install -m0755 tools/opkg-utils/opkg-unbuild /usr/local/bin/opkg-unbuild
sudo install -m0755 tools/opkg-utils/opkg-make-index /usr/local/bin/opkg-make-index

# Или просто запустите вспомогательный скрипт из этого репозитория:
sh ./scripts/setup-opkg-utils.sh

# На старых Ubuntu/Debian, где opkg-utils доступен в apt:
# sudo apt-get install -y opkg-utils gzip coreutils tar

# opkg-utils предоставляет:
#   - opkg-build: Создает файлы пакета .ipk
#   - opkg-make-index: Генерирует индексы пакетов
# Другие инструменты:
#   - gzip: Сжатие для индекса пакета
#   - coreutils: Предоставляет md5sum, sha256sum, stat для контрольных сумм
#   - tar: Инструмент архива для данных пакета
```

### Быстрая сборка

```bash
## Сборка пакета с настройками по умолчанию
./scripts/build_ipk.sh

## Результат: dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk
```

### Пользовательские сборки

```bash
## Переопределение информации о мейнтейнере
./scripts/build_ipk.sh \
  --maintainer "Ваше Имя" \
  --maintainer-email "your.email@example.com"

## Использование пользовательского идентификатора лицензии SPDX
./scripts/build_ipk.sh --spdx-id "MIT"

## Сборка для конкретной архитектуры
./scripts/build_ipk.sh --arch "mips_24kc"

## Пользовательская выходная директория
./scripts/build_ipk.sh --feed-root "./my-feed"
```

### Режим релиза

Режим релиза генерирует готовые к публикации артефакты с контрольными суммами и метаданными:

```bash
./scripts/build_ipk.sh --release-mode
```

Режим релиза предоставляет:
- Подробные таблицы контрольных сумм (MD5, SHA256)
- JSON метаданные для автоматизации
- Инструкции по настройке фида
- Именование на основе семантического версионирования

## Метаданные пакета

### Поля Makefile OpenWrt

| Поле | Значение | Описание |
|------|----------|----------|
| `PKG_NAME` | `openwrt-captive-monitor` | Идентификатор пакета |
| `PKG_VERSION` | `1.0.3` | Семантическая версия |
| `PKG_RELEASE` | `1` | Номер релиза пакета |
| `PKG_LICENSE` | `MIT` | Идентификатор лицензии SPDX |
| `PKG_LICENSE_FILES` | `LICENSE` | Ссылка на файл лицензии |
| `PKG_MAINTAINER` | `OpenWrt Captive Monitor Team` | Контакт мейнтейнера |
| `PKG_SOURCE_URL` | URL репозитория GitHub | Расположение исходного кода |
| `PKG_SOURCE_PROTO` | `git` | Протокол получения исходного кода |
| `PKG_SOURCE_VERSION` | `v$(PKG_VERSION)` | Тег версии исходного кода |

### Поля определения пакета

| Поле | Значение | Описание |
|------|----------|----------|
| `SECTION` | `net` | Раздел пакета |
| `CATEGORY` | `Network` | Категория OpenWrt |
| `SUBMENU` | `Captive Portals` | Классификация подменю |
| `TITLE` | Название пакета | Краткое описание |
| `DEPENDS` | `+dnsmasq +curl` | Требуемые пакеты |
| `URL` | URL репозитория GitHub | Домашняя страница проекта |

## Интеграция CI/CD

### Workflow GitHub Actions

Проект включает автоматическую валидацию и упаковку через GitHub Actions:

```yaml
## .github/workflows/ci.yml
- Запуск линтинга и тестов
- Сборка пакета с помощью OpenWrt SDK
- Загрузка `.ipk` и метаданных фида
- Прикрепление релизных артефактов при пуше тегов
```

### Результаты сборки

| Артефакт | Описание |
|----------|----------|
| `.ipk` | Устанавливаемый пакет OpenWrt |
| `Packages` | Индекс фида |
| `Packages.gz` | Сжатый индекс фида |
| `build.log` | Подробный лог сборки SDK |

## Процесс релиза

### 1. Обновление версии

Обновите версию в `package/openwrt-captive-monitor/Makefile`:

```makefile
PKG_VERSION:=1.0.2
PKG_RELEASE:=1
```

### 2. Сборка релизных артефактов

```bash
## Сборка в режиме релиза
./scripts/build_ipk.sh --release-mode

## Это создаёт:
## - dist/opkg/all/openwrt-captive-monitor_1.0.2-1_all.ipk
## - dist/opkg/all/Packages
## - dist/opkg/all/Packages.gz
## - dist/opkg/all/release-metadata.json
```

### 3. Создание тега и отправка

```bash
git tag -a v1.0.2 -m "Release v1.0.2"
git push origin v1.0.2
```

### 4. Релиз на GitHub

1. Перейдите на страницу GitHub Releases
2. Создайте новый релиз из тега `v1.0.2`
3. Загрузите артефакты из `dist/opkg/all/`
4. Используйте метаданные релиза для описания

## Пользовательский фид OPKG

### Настройка локального фида

1. **Создайте структуру директорий фида**:
   ```bash
   mkdir -p /path/to/feed/all
   cp dist/opkg/all/* /path/to/feed/all/
   ```

2. **Настройте устройство OpenWrt**:
   ```bash
   # Добавьте в /etc/opkg/customfeeds.conf
   echo "src/gz captive-monitor file:///path/to/feed" >> /etc/opkg/customfeeds.conf
   
   # Обновите списки пакетов
   opkg update
   
   # Установите пакет
   opkg install openwrt-captive-monitor
   ```

### Фид на GitHub Pages

1. **Создайте ветку `gh-pages`**:
   ```bash
   git checkout --orphan gh-pages
   git reset --hard
   ```

2. **Добавьте файлы пакета**:
   ```bash
   mkdir -p all
   cp dist/opkg/all/* all/
   git add all/
   git commit -m "Add package v1.0.2"
   git push origin gh-pages
   ```

3. **Настройте устройства**:
   ```bash
   echo "src/gz captive-monitor https://username.github.io/openwrt-captive-monitor" >> /etc/opkg/customfeeds.conf
   opkg update
   ```

## Автоматизированная дистрибуция

### Пример скрипта релиза

```bash
#!/bin/bash
## release.sh - Автоматизированный скрипт релиза

set -eu

VERSION=${1:-"1.0.2"}
MAINTAINER=${2:-"OpenWrt Captive Monitor Team"}
EMAIL=${3:-"team@example.com"}

## Обновление версии в Makefile
sed -i "s/PKG_VERSION:=.*/PKG_VERSION:=$VERSION/" package/openwrt-captive-monitor/Makefile

## Сборка релизных артефактов
./scripts/build_ipk.sh \
  --release-mode \
  --maintainer "$MAINTAINER" \
  --maintainer-email "$EMAIL"

## Создание релиза на GitHub
gh release create "v$VERSION" \
  --title "Release v$VERSION" \
  --notes "Automated release v$VERSION" \
  dist/opkg/all/*.ipk \
  dist/opkg/all/Packages* \
  dist/opkg/all/release-metadata.json
```

### Автоматизация релизов CI/CD

Workflow GitHub Actions можно расширить для:

1. **Автоматического создания релизов** при пуше тегов
2. **Загрузки артефактов** в GitHub Releases
3. **Обновления фида** на GitHub Pages
4. **Уведомления downstream-систем**

```yaml
## Пример задачи релиза
- name: Create Release
  if: startsWith(github.ref, 'refs/tags/')
  uses: actions/create-release@v1
  with:
    tag_name: ${{ github.ref }}
    release_name: Release ${{ github.ref }}
    draft: false
    prerelease: false
```

## Подписывание пакетов (опционально)

Для продакшн-фидов рассмотрите подписывание пакетов:

```bash
## Генерация ключа подписи
openssl genrsa -out opkg.key 2048
openssl rsa -in opkg.key -pubout > opkg.pub

## Подписывание пакетов
opkg-sign key opkg.key dist/opkg/all/*.ipk

## Обновление фида с подписями
opkg-make-index -s opkg.pub -p dist/opkg/all/Packages dist/opkg/all/
```

## Контроль качества

### Валидация пакета

```bash
## Проверка структуры пакета
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk

## Проверка control-файла
ar p dist/opkg/all/openwrt-captive-monitor_*.ipk control.tar.gz | tar -Oxz ./control

## Валидация зависимостей
opkg info ./dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Линтинг

```bash
## Проверка соответствия пакета OpenWrt
openwrt-package-lint package/openwrt-captive-monitor/Makefile

## Проверка прав доступа к файлам
find package/openwrt-captive-monitor/files -type f -exec ls -la {} \;
```

## Устранение неполадок

### Типичные проблемы

1. **Отсутствующие зависимости**: Убедитесь, что `dnsmasq` и `curl` доступны
2. **Несоответствие архитектуры**: Используйте правильный параметр `--arch`
3. **Отказано в доступе**: Проверьте права на выполнение файлов в `files/`
4. **Фид не обновляется**: Проверьте целостность `Packages.gz`

### Команды отладки

```bash
## Отладка сборки пакета
./scripts/build_ipk.sh --arch all 2>&1 | tee build.log

## Локальное тестирование фида
python3 -m http.server 8080 --directory dist/opkg/all/
## Затем: echo "src/gz test http://localhost:8080" >> /etc/opkg/customfeeds.conf
```

## Ссылки

- [Руководство по разработке пакетов OpenWrt](https://openwrt.org/docs/guide-developer/packages)
- [Менеджер пакетов OPKG](https://openwrt.org/docs/techref/opkg)
- [Список лицензий SPDX](https://spdx.org/licenses/)
- [GitHub Actions для OpenWrt](https://github.com/openwrt/packages)

---

*Последнее обновление: 2025-10-30*
