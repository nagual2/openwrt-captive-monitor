# Документация OpenWrt Captive Monitor

## Архитектура

Проект использует Docker-контейнер с Chrome + Selenium для автоматической авторизации на captive порталах. Установка на целевую машину через deb-пакет.

## Документы

### Установка и использование

- [Установка deb-пакета](debian-installation.md) — установка Docker-образа через deb-пакет
- [Docker Quick Start](DAEMON_DOCKER_QUICKSTART.md) — быстрый старт с Docker
- [Docker Daemon README](../docker/daemon/README.md) — полная документация Docker-образа

### Разработка

- [Команды](commands_cheatsheet.md) — часто используемые команды
- [Docker Guide](docker_guide.md) — работа с Docker
- [Troubleshooting](troubleshooting.md) — решение проблем
- [Release Notes](release-notes.md) — история релизов

### Дизайн

- [Cookie Proposal](DAEMON_COOKIE_PROPOSAL.md) — предложение по улучшению управления куками
- [Daemon Changelog](../tools/DAEMON_CHANGELOG.md) — история изменений daemon-версии
