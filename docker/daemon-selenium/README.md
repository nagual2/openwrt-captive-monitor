# Captive Portal Daemon (Selenium/Chrome version)

Этот Docker-образ предназначен для запуска daemon-версии авторизации на captive портале с использованием Selenium и Chromium.

## Особенности
- Базируется на Debian 12 (bookworm).
- Содержит Chromium и ChromeDriver.
- Поддерживает сохранение cookies в файл для последующих проверок.
- Автоматически проверяет состояние сети и авторизуется при необходимости.
- Оптимизирован для работы на Windows (Docker Desktop) и в Debian-системах.

## Быстрый старт на Windows

1. Убедитесь, что установлен Docker Desktop.
2. Откройте PowerShell в этой директории.
3. Соберите образ:
   ```powershell
   .\manage.ps1 build
   ```
4. Запустите daemon:
   ```powershell
   .\manage.ps1 start
   ```
5. Проверьте статус и логи:
   ```powershell
   .\manage.ps1 status
   .\manage.ps1 logs
   ```

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|-----------------------|
| `CHECK_INTERVAL` | Интервал между проверками (сек) | `60` |
| `TZ` | Часовой пояс | `Europe/Berlin` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `COOKIES_FILE` | Путь к файлу куков внутри контейнера | `/var/lib/captive-portal/cookies.pkl` |

## Структура файлов

- `Dockerfile` - инструкция по сборке образа на базе Debian.
- `docker-compose.yml` - для удобного запуска через docker-compose.
- `manage.ps1` - скрипт управления для Windows/PowerShell.
- `logs/` - директория с логами (монтируется в контейнер).
- `data/` - директория с cookies (монтируется в контейнер).

## Сборка DEB пакета

Для сборки полноценного Debian пакета (`.deb`), содержащего этот Docker-образ:
1. Используйте скрипт `scripts/build_deb_docker.sh` из корня проекта.
2. Пакет будет создан в директории `dist/deb-docker/`.
