# Описание Selenium скрипта (captive_portal_wsl_selenium.py)

Скрипт использует Selenium и Headless Chrome для прохождения flow авторизации на портале `conn4.com` через SOCKS-прокси.

## Параметры запуска (CLI)
Запускается без аргументов, настройки берутся из `.env` или переменных окружения.

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
| :--- | :--- | :--- |
| `CPM_ENV` | Окружение: `prod` или `dev` | `dev` |
| `NOJS_SOCKS_PORT` | Порт локального SOCKS-прокси | `10800` |
| `SELENIUM_ACCEPT_LANGUAGE` | Accept-Language для браузера | `en-US,en;q=0.9` |
| `CHROMEDRIVER_PATH` | Путь к бинарному файлу chromedriver | `/usr/bin/chromedriver` |
| `CPM_BLOCK_REDIRECT_HOSTS` | Список хостов для блокировки (через запятую) | `leonardo-hotels.com` |
| `MCP_ARTIFACTS_DIR` | Директория для артефактов | `mcp_artifacts/conn4_selenium` |
| `OPENWRT_SSH_HOST` | Хост роутера для SSH | `prod-openwrt` или `dev-openwrt` |
| `OPENWRT_SSH_USER` | Пользователь SSH | `root` |
| `OPENWRT_SSH_KEY` | Путь к приватному ключу SSH | `None` |

## Основные функции
- **Headless Chrome**: Запускает браузер в WSL с пробросом SOCKS.
- **Инъекции JS**: Внедряет хуки для перехвата событий `localStorage`, `sessionStorage` и `fetch`.
- **Перехват Network**: Использует CDP (Chrome DevTools Protocol) для логирования сетевых запросов.
- **Сбор артефактов**: Сохраняет скриншоты, дампы DOM, логи консоли и сетевые трассы в `mcp_artifacts/conn4_selenium/<timestamp>_<pid>/`.
