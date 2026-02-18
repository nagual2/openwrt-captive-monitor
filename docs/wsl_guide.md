# WSL

## Основные

- Нативно запускаем Git, GH CLI, работу с файлами.
- Для работы в Trae используем расширение `Open Remote - WSL` (jeanp413) для подключения к Linux‑окружению.
- WSL используем для ВСЕХ скриптов (Python, Shell), SSH на роутеры, make, сетевых утилит.
- SSH к dev/prod‑роутерам через `wsl ssh`, хосты задаём в `/etc/hosts`:
  - `192.168.1.1 dev-openwrt`
  - `192.168.x.x prod-openwrt`

## Дополнительные

- Для Chrome headless и Selenium ориентируемся на `docs/captive-portal-wsl-selenium.md`.

