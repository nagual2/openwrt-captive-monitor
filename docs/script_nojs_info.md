# Описание NoJS скрипта (test_conn4_portal_nojs.py)

Скрипт эмулирует работу браузера для авторизации на портале `conn4.com` через HTTP-запросы и SOCKS-прокси.

## Параметры запуска (CLI)
Скрипт принимает позиционные аргументы в конструкторе, но чаще всего управляется через переменные окружения.

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
| :--- | :--- | :--- |
| `CPM_ENV` | Окружение: `prod` или `dev` | `dev` |
| `PORTAL_URL` | Прямая ссылка на портал (если известна) | `None` (автодетект) |
| `NOJS_SOCKS_PORT` | Порт локального SOCKS-прокси | `10800` |
| `NOJS_CLIENT_IP` | Подмена IP клиента в запросах | `None` |
| `NOJS_CLIENT_MAC` | Подмена MAC-адреса клиента | `None` |
| `NOJS_USER_AGENT` | User-Agent браузера | Chrome 131 (Windows) |
| `NOJS_DISABLE_SSH` | Отключить автоматический запуск SSH туннеля (`1`) | `None` |
| `NOJS_ACCEPT_LANGUAGE` | Заголовок Accept-Language | `en-US,en;q=0.9` |
| `MCP_ARTIFACTS_DIR` | Путь к директории для сохранения логов и артефактов | `mcp_artifacts/conn4_nojs` |
| `OPENWRT_SSH_HOST` | Хост роутера для SSH | `prod-openwrt` или `dev-openwrt` |
| `OPENWRT_SSH_USER` | Пользователь SSH | `root` |
| `OPENWRT_SSH_KEY` | Путь к приватному ключу SSH | `None` |

## Основные функции
- **Автоматический SOCKS**: Поднимает `ssh -D` туннель к роутеру.
- **Сбор артефактов**: Сохраняет каждый HTTP-ответ, токены и куки в `mcp_artifacts/conn4_nojs/<timestamp>_<pid>/`.
- **WBS API**: Взаимодействует с API портала для получения параметров сессии.
