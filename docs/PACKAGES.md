# Available OpenWrt Packages

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

## Repository Files
❌ No .ipk files found in repository

**Explanation**: `.ipk` files are intentionally excluded from version control via `.gitignore` to keep the repository clean. Packages are built on-demand via CI/CD or locally using the build script.

### Local Build Information
- **Current Version**: 1.0.3-1 (from `package/openwrt-captive-monitor/Makefile`)
- **Architecture**: all
- **Build Script**: `./scripts/build_ipk.sh`
- **Output Location**: `dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk`
- **Package Size**: 13,250 bytes (local build)
- **Dependencies**: `dnsmasq`, `curl`

### How to Build Locally
```bash
## Build the package
./scripts/build_ipk.sh

## Output will be in:
## dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk
## dist/opkg/all/Packages
## dist/opkg/all/Packages.gz
```

## GitHub Actions Artifacts
✅ Artifacts available

### Latest Build Information
- **Workflow**: "Build OpenWrt packages"
- **Latest Successful Run**: #18941818953 (2025-10-30T13:13:37Z)
- **Branch**: main
- **Status**: ✅ Success
- **Artifact**: `openwrt-captive-monitor_1.0.1-1_all`
- **Size**: 14,496 bytes
- **Created**: 2025-10-30T13:14:14Z
- **Expires**: 2026-01-28T13:13:38Z

### Download Instructions
1. **Via GitHub Web Interface**:
   - Go to: https://github.com/nagual2/openwrt-captive-monitor/actions
   - Click on the "Build OpenWrt packages" workflow
   - Select the latest successful run (Run #18941818953)
   - Download the "openwrt-captive-monitor_1.0.1-1_all" artifact

2. **Via API** (authentication required):
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
        -L https://api.github.com/repos/nagual2/openwrt-captive-monitor/actions/artifacts/4417725839/zip \
        -o openwrt-captive-monitor_1.0.1-1_all.zip
   ```

### Recent Build History
| Run ID | Date | Status | Artifact Size |
|--------|------|--------|---------------|
| 18941818953 | 2025-10-30 13:13:37Z | ✅ Success | 14,496 bytes |
| 18941783175 | 2025-10-30 13:12:21Z | ✅ Success | 14,502 bytes |
| 18925153078 | 2025-10-29 23:38:58Z | ✅ Success | 14,501 bytes |

## GitHub Releases
❌ No package assets in releases

### Available Releases
- **v0.1.0** (2025-10-23T12:26:42Z)
  - ❌ No package assets attached
  - Release notes: Initial release

### Missing Release Assets
- **v0.1.2**: Tag exists but no release created
- **v0.1.0**: Release exists but no package files attached

**Note**: The workflow is configured to publish release assets when tags are pushed, but it appears this hasn't been working or the assets weren't properly attached.

## Package Metadata

### Current Version (1.0.3-1)
```
Package: openwrt-captive-monitor
Version: 1.0.3-1
Architecture: all
Maintainer: OpenWrt Captive Monitor Team
License: MIT
Section: net
Category: Network
Priority: optional
Depends: dnsmasq, curl
Source: https://github.com/nagual2/openwrt-captive-monitor
Installed-Size: 96
Description: Captive portal connectivity monitor and auto-redirect helper
```

### Version History / История версий
| Версия | Дата тега | Статус сборки | Пакет доступен |
|--------|-----------|---------------|----------------|
| 1.0.3 | Текущая | ✅ Доступно через артефакты CI | Да |
| 1.0.1 | 2025-11-01 | ✅ Доступно через артефакты CI | Да |
| 0.1.2 | 2025-10-26 | ❌ CI выполнен, но артефакты не сохранены | Нет |
| 0.1.0 | 2025-10-23 | ❌ Релиз существует, но нет активов | Нет |

## Summary / Итоги
- **Всего найдено .ipk файлов**: 1 (текущая версия через артефакты CI)
- **Последняя версия**: v1.0.3-1
- **Рекомендуемый способ загрузки**: Артефакты GitHub Actions (самые свежие)
- **Статус репозитория**: Пакеты не хранятся (намеренно)
- **Статус релизов**: Нет файлов пакетов в релизах

## How to Download / Как загрузить

### Recommended Method: GitHub Actions Artifacts / Рекомендуемый способ: артефакты GitHub Actions
1. **Latest Version (Recommended) / Последняя версия (рекомендуется)**:
   - URL: https://github.com/nagual2/openwrt-captive-monitor/actions
   - Нажмите на рабочий процесс "Build OpenWrt packages"
   - Выберите последнюю успешную сборку
   - Скачайте артефакт "openwrt-captive-monitor_1.0.1-1_all"

2. **Прямая загрузка** (требуется вход в GitHub):
   ```
   https://api.github.com/repos/nagual2/openwrt-captive-monitor/actions/artifacts/4417725839/zip
   ```

### Alternative Method: Local Build / Альтернативный способ: локальная сборка
```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor
./scripts/build_ipk.sh
## Пакет будет находиться в: dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk
```

### Package Installation on OpenWrt / Установка пакета на OpenWrt
```bash
## Передайте файл .ipk на ваше устройство OpenWrt
scp openwrt-captive-monitor_1.0.3-1_all.ipk root@192.168.1.1:/tmp/

## Установите пакет
opkg install /tmp/openwrt-captive-monitor_1.0.3-1_all.ipk

## Настройте и включите
u set captive-monitor.@monitor[0].enabled='1'
 uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
```

## Troubleshooting / Устранение неполадок

### If GitHub Actions Artifacts Expire / Если срок действия артефактов GitHub Actions истек
Артефакты GitHub Actions истекают через 90 дней. Если ссылки для загрузки не работают:

1. **Запустите новую сборку**:
   ```bash
   # Внесите любое небольшое изменение и отправьте в main
   echo "update" > README.md
   git add README.md
   git commit -m "trigger build"
   git push origin main
   ```

2. **Соберите пакет локально** с помощью инструкций выше

### If Package Installation Fails / Если установка пакета не удалась
- **Проверьте зависимости**: Убедитесь, что установлены `dnsmasq` и `curl`
- **Проверьте архитектуру**: Пакет собран для архитектуры `all`
- **Проверьте версию OpenWrt**: Совместим с современными версиями OpenWrt
- **Проверьте свободное место на диске**: Пакету требуется около 96 КБ установленного пространства

---

*Последнее обновление: 2025-10-30*
*Отчет сгенерирован на основе файлов репозитория, релизов GitHub и артефактов GitHub Actions*
