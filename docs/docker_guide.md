# Docker

## Основные

- Docker используем для OpenWrt SDK и изолированных тестов.
- Проверка и очистка: `docker images`, `docker ps`, `docker system prune -a`.
- Сборка SDK: `docker build -t openwrt-sdk:local .`.

## Дополнительные

- Следи за размером образов и чисти кэш в том же `RUN`.
- Для логов и диагностики используй `docker logs` и официальную документацию.
