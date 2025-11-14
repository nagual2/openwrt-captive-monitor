# Available OpenWrt Packages / Доступные пакеты OpenWrt

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

## Repository Files / Файлы репозитория
❌ No .ipk files found in repository / В репозитории не найдены .ipk файлы

**Explanation**: `.ipk` files are intentionally excluded from version control via `.gitignore` to keep the repository clean. Packages are built on-demand via CI/CD or locally using the build script.
**Пояснение**: Файлы `.ipk` намеренно исключены из системы контроля версий через `.gitignore` для поддержания чистоты репозитория. Пакеты собираются по запросу через CI/CD или локально с использованием скрипта сборки.

### Local Build Information / Информация о локальной сборке
- **Current Version / Текущая версия**: 1.0.3-1 (from `package/openwrt-captive-monitor/Makefile`)
- **Architecture / Архитектура**: all
- **Build Script / Скрипт сборки**: `./scripts/build_ipk.sh`
- **Output Location / Выходной каталог**: `dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk`
- **Package Size / Размер пакета**: 13,250 bytes (local build / локальная сборка)
- **Dependencies / Зависимости**: `dnsmasq`, `curl`

### How to Build Locally / Как собрать локально
```bash
## Build the package / Собрать пакет
./scripts/build_ipk.sh

## Output will be in: / Выходные файлы будут в:
## dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk
## dist/opkg/all/Packages
## dist/opkg/all/Packages.gz
```

## GitHub Actions Artifacts / Артефакты GitHub Actions
✅ Artifacts available / Артефакты доступны

### Latest Build Information / Информация о последней сборке
- **Workflow / Процесс**: "Build OpenWrt packages" / "Сборка пакетов OpenWrt"
- **Latest Successful Run / Последняя успешная сборка**: #18941818953 (2025-10-30T13:13:37Z)
- **Branch / Ветка**: main
- **Status / Статус**: ✅ Success / Успешно
- **Artifact / Артефакт**: `openwrt-captive-monitor_1.0.1-1_all`
- **Size / Размер**: 14,496 bytes
- **Created / Создан**: 2025-10-30T13:14:14Z
- **Expires / Истекает**: 2026-01-28T13:13:38Z

### Download Instructions / Инструкции по загрузке
1. **Via GitHub Web Interface / Через веб-интерфейс GitHub**:
   - Перейдите по адресу: https://github.com/nagual2/openwrt-captive-monitor/actions
   - Нажмите на рабочий процесс "Build OpenWrt packages"
   - Выберите последнюю успешную сборку (Run #18941818953)
   - Скачайте артефакт "openwrt-captive-monitor_1.0.1-1_all"

2. **Via API / Через API** (требуется аутентификация):
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
        -L https://api.github.com/repos/nagual2/openwrt-captive-monitor/actions/artifacts/4417725839/zip \
        -o openwrt-captive-monitor_1.0.1-1_all.zip
   ```

### Recent Build History / История последних сборок
| Run ID | Дата | Статус | Размер артефакта |
|--------|------|--------|-----------------|
| 18941818953 | 2025-10-30 13:13:37Z | ✅ Success | 14,496 bytes |
| 18941783175 | 2025-10-30 13:12:21Z | ✅ Success | 14,502 bytes |
| 18925153078 | 2025-10-29 23:38:58Z | ✅ Success | 14,501 bytes |

## GitHub Releases / Релизы GitHub
❌ No package assets in releases / В релизах нет файлов пакетов

### Available Releases / Доступные релизы
- **v0.1.0** (2025-10-23T12:26:42Z)
  - ❌ No package assets attached / Нет прикрепленных файлов пакетов
  - Release notes / Примечания к выпуску: Initial release / Первый выпуск

### Missing Release Assets / Отсутствующие активы релиза
- **v0.1.2**: Тег существует, но релиз не создан
- **v0.1.0**: Релиз существует, но нет файлов пакетов

**Note / Примечание**: The workflow is configured to publish release assets when tags are pushed, but it appears this hasn't been working or the assets weren't properly attached.
Рабочий процесс настроен на публикацию активов при отправке тегов, но, похоже, это не сработало, или активы не были правильно прикреплены.

## Package Metadata / Метаданные пакета

### Current Version (1.0.3-1) / Текущая версия (1.0.3-1)
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
