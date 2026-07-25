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
| `CHECK_INTERVAL` | Baseline interval between checks (sec); doubles on failure up to 60 | `5` |
| `REFRESH_INTERVAL` | Min seconds between Chrome keepalives when cookies are valid | `1800` |
| `PING_TARGETS` | Comma-separated ICMP hosts for the hot-path check | `1.1.1.1,8.8.8.8` |
| `PING_TIMEOUT` | Seconds for `ping -W` per probe | `1` |
| `TZ` | Timezone | `Europe/Berlin` |
| `LOG_LEVEL` | Log level | `INFO` |
| `COOKIES_FILE` | Cookie file path inside the container | `/var/lib/captive-portal/cookies.pkl` |

## Структура файлов

- `Dockerfile` - инструкция по сборке образа на базе Debian.
- `docker-compose.yml` - для удобного запуска через docker-compose.
- `manage.ps1` - скрипт управления для Windows/PowerShell.
- `logs/` - директория с логами (монтируется в контейнер).
- `data/` - директория с cookies (монтируется в контейнер).

## Особенности для Windows (Docker Desktop)

1. **WSL2 Backend**: Рекомендуется использовать WSL2 для лучшей производительности.
2. **Память**: Chromium требует минимум 512MB RAM. В `docker-compose.yml` установлено ограничение 1GB. Если ваша система имеет мало памяти, проверьте лимиты в настройках Docker Desktop.
3. **Shared Memory**: Параметр `shm_size: 1gb` обязателен для стабильной работы Chromium в Docker под Windows.
4. **Volume Mounts**: Пути в Windows монтируются через WSL2 автоматически. Логи и данные будут доступны в папках `logs/` и `data/` текущей директории.

## Устранение неполадок на Windows

- **Ошибка "Out of memory"**: Убедитесь, что лимит в `docker-compose.yml` не превышает доступную память в WSL2.
- **Chrome не стартует**: Проверьте логи (`.\manage.ps1 logs`). Если Chromium падает с ошибкой библиотек, убедитесь, что образ собран без ошибок.
- **Проблемы с путями**: Если вы используете PowerShell, используйте `.\manage.ps1` для управления, он автоматически определяет пути.

## Сборка и оптимизация

Для сборки полноценного Debian пакета (`.deb`), содержащего этот Docker-образ:
1. Используйте скрипт `scripts/build_deb_docker.sh` из корня проекта.
2. Пакет будет создан в директории `dist/deb-docker/`.
