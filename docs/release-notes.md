# Release Notes

## Docker-based Daemon (2026.2.19)

### Основные изменения

- Миграция на Docker-архитектуру: Python daemon в контейнере с Chrome + Selenium
- Deb-пакет устанавливает Docker-образ и systemd-сервис
- Удалена старая структура (прямая установка Python, NoJS скрипт)

### Daemon режим

- Chrome/Selenium инициализируются один раз и остаются в памяти
- Непрерывный мониторинг с интервалом 60 секунд
- Автоматический перезапуск Chrome при падении
- Graceful shutdown с очисткой ресурсов

### Производительность

- CPU: снижение на ~90% (с 15-20% до 1-2%)
- Быстрые проверки без перезапуска браузера
- Память: ~40-50 MB постоянно

### Документация

- [Docker Quick Start](DAEMON_DOCKER_QUICKSTART.md)
- [Установка deb-пакета](debian-installation.md)
- [Docker Daemon README](../docker/daemon/README.md)
- [Daemon Changelog](../tools/DAEMON_CHANGELOG.md)
