# Docker Master Guide 🐳

Единый справочник по использованию Docker в проекте `openwrt-captive-monitor`.

## 1. Captive Portal Daemon (Selenium/Chrome)
Основной контейнер для автоматической авторизации на порталах.

- **Dockerfile:** `docker/daemon-selenium/Dockerfile`
- **Compose:** `docker/daemon-selenium/docker-compose.yml`
- **Управление (Windows):** `.\docker\daemon-selenium\manage.ps1`

### Основные команды
```powershell
.\docker\daemon-selenium\manage.ps1 build    # Сборка образа
.\docker\daemon-selenium\manage.ps1 start    # Запуск
.\docker\daemon-selenium\manage.ps1 logs     # Просмотр логов
```

## 2. OpenWrt SDK & Сборка
Используется для компиляции `.ipk` пакетов и `.deb` образов.

- **Сборка SDK:** `docker build -t openwrt-sdk:local .`
- **Сборка DEB пакета:** `bash scripts/build_deb_docker.sh`

## 3. Обслуживание Docker
Команды для поддержания чистоты инфополя:

- **Статус:** `docker ps -a`
- **Образы:** `docker images`
- **Очистка:** `docker system prune -a` (удаляет все неиспользуемые контейнеры и образы)

## 4. Диагностика
- **Логи контейнера:** `docker logs -f captive-daemon`
- **Вход в контейнер:** `docker exec -it captive-daemon bash`
- **Проверка версии Chrome:** `docker exec captive-daemon chromium --version`

---
*Документация консолидирована для уменьшения ментального шума.*
