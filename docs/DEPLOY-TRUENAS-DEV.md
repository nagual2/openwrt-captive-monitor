# Развёртывание captive-portal-dual на TrueNAS-dev (Hyper-V)

## Обзор

Это руководство описывает развёртывание контейнера двухканальной авторизации captive portal на TrueNAS-dev, работающем в Hyper-V.

## Требования

- Виртуальная машина TrueNAS-dev в Hyper-V
- SSH доступ к TrueNAS-dev
- Два сетевых адаптера в Hyper-V:
  - Primary WAN (eth0)
  - Secondary WAN (eth1) — подключён к MikroTik
- Docker установлен на TrueNAS-dev

## Быстрое развёртывание

### 1. Сборка Docker-образа

На Windows-хосте (или TrueNAS-dev, если есть инструменты сборки):

```powershell
# Перейти в директорию проекта
cd C:\Git\openwrt-captive-monitor

# Собрать Docker-образ
docker build -t openwrt-captive-monitor:dual -f docker/Dockerfile.dual .

# Сохранить образ в tar-файл
docker save openwrt-captive-monitor:dual | gzip > captive-portal-dual.tar.gz
```

### 2. Перенос на TrueNAS-dev

```powershell
# Копирование на TrueNAS-dev через SCP
scp captive-portal-dual.tar.gz root@truenas-dev-ip:/root/
```

Или через общую папку, если настроена в Hyper-V.

### 3. Загрузка образа на TrueNAS-dev

Подключиться к TrueNAS-dev по SSH и загрузить образ:

```bash
ssh root@truenas-dev-ip

# Загрузить образ
docker load < captive-portal-dual.tar.gz

# Проверка
docker images | grep dual
```

### 4. Создание директорий данных

```bash
mkdir -p /opt/captive-portal-dual/data
mkdir -p /opt/captive-portal-dual/logs
mkdir -p /opt/captive-portal-dual/config
```

### 5. Создание файла конфигурации

Создать `/opt/captive-portal-dual/config/config.json`:

```json
{
  "primary": {
    "name": "wan",
    "interface": "eth0",
    "gateway": "192.168.1.1",
    "check_url": "http://www.msftconnecttest.com/connecttest.txt",
    "priority": 1
  },
  "secondary": {
    "name": "wan2",
    "interface": "eth1",
    "gateway": "192.168.45.1",
    "check_url": "http://www.msftconnecttest.com/connecttest.txt",
    "priority": 2
  },
  "socks_proxy": {
    "host": "0.0.0.0",
    "port": 1080
  },
  "cookie_ttl": 3600,
  "check_interval": 60
}
```

### 6. Запуск контейнера

```bash
docker run -d \
  --name captive-portal-dual \
  --restart unless-stopped \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --network host \
  -p 1080:1080 \
  -v /opt/captive-portal-dual/data:/tmp \
  -v /opt/captive-portal-dual/logs:/var/log/captive-portal-dual \
  -v /opt/captive-portal-dual/config/config.json:/app/config.json:ro \
  -e CONFIG_FILE=/app/config.json \
  -e PRIMARY_WAN_INTERFACE=eth0 \
  -e SECONDARY_WAN_INTERFACE=eth1 \
  openwrt-captive-monitor:dual
```

### 7. Проверка развёртывания

```bash
# Просмотр логов контейнера
docker logs -f captive-portal-dual

# Проверка SOCKS-прокси
curl -x socks5://localhost:1080 http://www.msftconnecttest.com/connecttest.txt

# Статус контейнера
docker ps | grep captive-portal-dual
```

## Использование Docker Compose

Если на TrueNAS-dev установлен docker-compose:

```bash
# Копирование docker-compose файла
cp docker/docker-compose.dual.yml /opt/captive-portal-dual/docker-compose.yml

# Запуск сервисов
cd /opt/captive-portal-dual
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## Специфика TrueNAS SCALE (Kubernetes)

Для TrueNAS SCALE (использует Kubernetes вместо Docker):

### 1. Создание Dockerfile для TrueNAS SCALE

```dockerfile
FROM ixsystems/truecommand:latest

# Установка дополнительных пакетов
RUN apt-get update && apt-get install -y python3-pip chromium

# Копирование приложения
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt

CMD ["python3", "tools/captive-portal-dual.py", "--daemon"]
```

### 2. Развёртывание через TrueNAS UI

1. Перейти в **Apps** → **Discover** → **Custom App**
2. Загрузить Docker-образ или использовать Docker Hub
3. Настройка:
   - **Container Image**: `openwrt-captive-monitor:dual`
   - **Container Name**: `captive-portal-dual`
   - **Networking**: Host Network
   - **Ports**: 1080 (SOCKS)
   - **Storage**: 
     - Host Path: `/opt/captive-portal-dual/data` → Container: `/tmp`
     - Host Path: `/opt/captive-portal-dual/logs` → Container: `/var/log`

### 3. Развёртывание через CLI (middlewared)

```bash
# Создание custom app через TrueNAS API
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  https://truenas-dev-ip/api/v2.0/chart/release \
  -d '{
    "catalog": "OFFICIAL",
    "item": "custom-app",
    "release_name": "captive-portal-dual",
    "train": "stable",
    "version": "1.0.0",
    "values": {
      "image": {
        "repository": "openwrt-captive-monitor",
        "tag": "dual"
      },
      "networking": {
        "hostNetwork": true
      },
      "service": {
        "main": {
          "ports": [
            {
              "port": 1080,
              "protocol": "tcp"
            }
          ]
        }
      }
    }
  }'
```

## Настройка сети на TrueNAS-dev

### Проверка сетевых интерфейсов

```bash
# Список всех интерфейсов
ip link show

# Проверка имён интерфейсов (Hyper-V обычно показывает eth0, eth1)
ip addr show

# Проверка secondary интерфейса
cat /sys/class/net/eth1/address
```

### Настройка Secondary WAN

Отредактировать `/etc/systemd/network/eth1.network`:

```ini
[Match]
Name=eth1

[Network]
DHCP=yes
LinkLocalAddressing=no

[DHCPv4]
UseDNS=no
UseRoutes=no
UseGateway=no
```

Перезапуск сети:

```bash
systemctl restart systemd-networkd
```

## Использование SOCKS-прокси

После развёртывания используйте SOCKS-прокси для маршрутизации трафика:

### Настройка браузера

Настроить браузер на использование SOCKS5-прокси:
- Хост: `truenas-dev-ip`
- Порт: `1080`

### curl через SOCKS

```bash
curl --socks5 truenas-dev-ip:1080 http://example.com
```

### Конфигурация приложений

Установить переменные окружения:

```bash
export ALL_PROXY=socks5://truenas-dev-ip:1080
export HTTP_PROXY=socks5://truenas-dev-ip:1080
export HTTPS_PROXY=socks5://truenas-dev-ip:1080
```

## Диагностика

### Просмотр логов контейнера

```bash
docker logs captive-portal-dual
docker logs --tail 100 -f captive-portal-dual
```

### Проверка соединения

```bash
# Вход в контейнер
docker exec -it captive-portal-dual /bin/bash

# Тест с primary интерфейса
curl --interface eth0 http://www.msftconnecttest.com/connecttest.txt

# Тест с secondary интерфейса
curl --interface eth1 http://www.msftconnecttest.com/connecttest.txt

# Тест SOCKS-прокси
curl --socks5 localhost:1080 http://www.msftconnecttest.com/connecttest.txt
```

### Проверка сетевой конфигурации

```bash
# Проверка маршрутизации
docker exec captive-portal-dual ip route

# Проверка iptables
docker exec captive-portal-dual iptables -L -n -v

# Проверка конфигурации интерфейсов
docker exec captive-portal-dual ip addr show
```

### Перезапуск контейнера

```bash
docker restart captive-portal-dual

# Или через compose
cd /opt/captive-portal-dual && docker-compose restart
```

## Обновление контейнера

Для обновления до новой версии:

```bash
# Остановка и удаление старого контейнера
docker stop captive-portal-dual
docker rm captive-portal-dual

# Сборка и загрузка нового образа
# ... (повторить шаги сборки и переноса)

# Запуск нового контейнера
docker run -d ... (как в шаге 6)
```

## Резервное копирование и восстановление

### Резервное копирование данных

```bash
tar -czf captive-portal-dual-backup.tar.gz /opt/captive-portal-dual/
```

### Восстановление

```bash
tar -xzf captive-portal-dual-backup.tar.gz -C /
```

## Замечания для среды Hyper-V

- Убедиться, что оба сетевых адаптера подключены в настройках Hyper-V
- Включить MAC address spoofing на secondary адаптере при необходимости
- Настроить Hyper-V virtual switch для доступа к внешней сети
- Проверить Windows Defender Firewall при проблемах соединения
