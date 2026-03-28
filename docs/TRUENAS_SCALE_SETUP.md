# Установка на TrueNAS SCALE (Minisforum и др.)

TrueNAS SCALE 24.10+ (Electric Eel / Fangtooth) перешел с Kubernetes на **Docker Compose** для приложений (Apps) и **Incus** для виртуализации (Instances/VM). Чтобы запустить Captive Portal Daemon на современных версиях TrueNAS SCALE, следуйте этой инструкции.

## Способ 1: Docker App (Рекомендуемый для 24.10+)

1. Перейдите в **Apps** -> **Discover Apps** -> **Custom App**.
2. **Application Name**: `captive-daemon`
3. **Container Settings**:
   - **Image**: `captive-portal-daemon:latest` (Вам нужно сначала собрать образ локально или использовать готовый, если он запушен в Docker Hub).
   - **Environment Variables**:
     - `CHECK_INTERVAL`: `60`
     - `TZ`: `Europe/Moscow` (ваш часовой пояс)
     - `LOG_LEVEL`: `INFO`
4. **Networking**:
   - Поставьте галочку **Host Network**. Это критически важно для обнаружения captive портала.
5. **Storage**:
   - Добавьте **Host Path Volumes**:
     - **Host Path**: `/mnt/pool/apps/captive-daemon/data` -> **Mount Path**: `/var/lib/captive-portal`
     - **Host Path**: `/mnt/pool/apps/captive-daemon/logs` -> **Mount Path**: `/var/log`
   - Убедитесь, что у пользователя `apps` (UID 568) или `root` (если контейнер запущен от root) есть права на запись в эти папки.
6. **Resources**:
   - Ограничение памяти: минимум `512Mi`, рекомендуется `1Gi` (Selenium + Chromium потребляют много ресурсов).

## Способ 2: Docker Compose (через CLI)

Если вы предпочитаете использовать `docker-compose` напрямую через SSH (доступно в некоторых версиях SCALE):

1. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/ваше-имя/openwrt-captive-monitor.git
   cd openwrt-captive-monitor/docker/daemon-selenium
   ```
2. Соберите образ:
   ```bash
   docker build -t captive-portal-daemon:latest ../.. -f Dockerfile
   ```
3. Запустите:
   ```bash
   docker-compose up -d
   ```

## Возможные проблемы на TrueNAS SCALE

1. **Ошибка ZFS Permissions**: Если контейнер не может писать логи, проверьте ACL на папках данных. В TrueNAS SCALE лучше всего выставлять "Generic" или "Unix" права для папок, монтируемых в Docker.
2. **Host Network**: Без этой опции контейнер будет находиться за NAT и может не увидеть редирект на captive портал провайдера.
3. **Объем памяти**: Если Chromium падает с ошибкой "Out of memory", увеличьте лимит до 1ГБ.
4. **Shared Memory**: В версиях 24.10+ (Docker) параметр `--shm-size=1g` крайне важен. В Custom App это настраивается через `Extra Args`.

## Решение проблем с Middleware (TimeoutError / Incus)

Если вы видите ошибки типа `asyncio.TimeoutError` или `middlewared.plugins.virt.global.recover`, это означает, что внутренняя служба управления TrueNAS (Middleware) не может связаться с бэкендом виртуализации **Incus**. 

На TrueNAS 25.04 (Fangtooth) Incus управляет и VM, и LXC контейнерами (Instances). При нехватке памяти демон `incusd` может зависнуть, что блокирует весь интерфейс приложений и виртуализации.

**Как оживить систему (через SSH):**

1. **Проверьте состояние демона Incus:**
   ```bash
   sudo systemctl status incus
   ```
2. **Перезапустите Middleware и Incus:**
   ```bash
   sudo systemctl restart middlewared
   sudo systemctl restart incus
   ```
3. **Если Incus не отвечает на сигналы:**
   ```bash
   sudo killall -9 incusd
   sudo systemctl start incus
   ```
4. **Проверьте статус контейнеров (Instances):**
   ```bash
   incus list
   ```
5. **Проверьте статус Docker-приложений (Apps):**
   ```bash
   docker ps
   ```

## Как проверить логи
```bash
# Через CLI
docker logs captive-daemon
# Или через UI TrueNAS (кнопка Logs у приложения)
```
