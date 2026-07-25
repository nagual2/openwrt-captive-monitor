# Сборка и тестирование dual-socks-proxy для OpenWrt

## Структура пакета

```
package/openwrt-dual-socks/
├── Makefile                              # Makefile для сборки
├── files/
│   ├── dual-socks-proxy.init            # init скрипт (procd)
│   ├── dual-socks-proxy.sh              # wrapper скрипт
│   └── dual-socks-proxy.config          # конфигурация по умолчанию
```

## Требования

- OpenWrt SDK или buildroot
- Linux машина для сборки (или WSL)
- microsocks (устанавливается как зависимость)

## Инструкция по сборке

### 1. Подготовка окружения

```bash
# Установить зависимости для сборки (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y build-essential libncurses5-dev zlib1g-dev gawk git \
    gettext libssl-dev xsltproc zip python3

# Скачать OpenWrt SDK
wget https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
tar -xJf openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
cd openwrt-sdk-*.Linux-x86_64
```

### 2. Добавление пакета

```bash
# Создать директорию пакета
mkdir -p package/dual-socks-proxy/files

# Скопировать файлы из проекта
cp /path/to/dual-socks-proxy.init package/dual-socks-proxy/files/
cp /path/to/dual-socks-proxy.sh package/dual-socks-proxy/files/
cp /path/to/dual-socks-proxy.config package/dual-socks-proxy/files/
cp /path/to/Makefile package/dual-socks-proxy/

# Или создать симлинк
ln -s /path/to/package/openwrt-dual-socks package/dual-socks-proxy
```

### 3. Сборка пакета

```bash
# Обновить фиды
./scripts/feeds update -a
./scripts/feeds install -a

# Выбрать пакет для сборки
make menuconfig
# Выбрать: Network -> dual-socks-proxy (M)

# Собрать пакет
make package/dual-socks-proxy/compile -j$(nproc)

# Результат будет в:
ls bin/packages/*/base/dual-socks-proxy_*.ipk
```

### 4. Установка на OpenWrt

```bash
# Копировать на роутер
scp bin/packages/*/base/dual-socks-proxy_*.ipk root@openwrt:/tmp/

# Установить (напрямую из Windows, без WSL)
ssh root@openwrt
opkg update
opkg install microsocks
opkg install /tmp/dual-socks-proxy_*.ipk
```

## Тестирование на openwrt-dev VM

### 1. Подготовка VM

```bash
# Запустить openwrt-dev в Hyper-V/VirtualBox
# Настроить два сетевых адаптера:
#   - WAN (eth0) - основной интернет
#   - WAN2 (eth1) - второй канал (MikroTik)

# Проверить интерфейсы (напрямую из Windows, без WSL)
ssh root@openwrt-dev ip addr show
```

### 2. Установка тестового пакета

```bash
# Подключиться к VM (напрямую из Windows, без WSL)
ssh root@openwrt-dev

# Установить microsocks (зависимость)
opkg update
opkg install microsocks

# Установить наш пакет
opkg install /tmp/dual-socks-proxy_*.ipk
```

### 3. Конфигурация

```bash
# Проверить/изменить конфиг
uci show dual-socks-proxy

# Изменить порты при необходимости
uci set dual-socks-proxy.main.primary_port='11080'
uci set dual-socks-proxy.main.secondary_port='11081'
uci commit dual-socks-proxy
```

### 4. Запуск и тестирование

```bash
# Запустить сервис
/etc/init.d/dual-socks-proxy start

# Проверить статус
/etc/init.d/dual-socks-proxy status

# Проверить логи
logread -e dual-socks-proxy
tail -f /var/log/dual-socks-proxy.log

# Проверить процессы
ps | grep microsocks

# Проверить порты
netstat -tlnp | grep -E '11080|11081'
```

### 5. Тест SOCKS соединения

```bash
# С основного канала (через openwrt-dev)
curl --socks5 openwrt-dev-ip:11080 http://www.msftconnecttest.com/connecttest.txt

# Со вторичного канала
curl --socks5 openwrt-dev-ip:11081 http://www.msftconnecttest.com/connecttest.txt

# Проверка через разные WAN
# - 11080 должен идти через основной WAN
# - 11081 должен идти через WAN2 (MikroTik)
```

### 6. Нагрузочное тестирование

```bash
# Проверка стабильности (запустить на 10 минут)
timeout 600 sh -c '
    while true; do
        curl --socks5 openwrt-dev-ip:11080 -s -o /dev/null \
            http://www.msftconnecttest.com/connecttest.txt && echo "OK: $(date)"
        sleep 5
    done
'

# Мониторинг ресурсов
# В другом терминале:
top | grep microsocks
free -h
```

### 7. Проверка восстановления после сбоя

```bash
# Убить процесс
killall microsocks

# Проверить, что сервис перезапустился через procd
/etc/init.d/dual-socks-proxy status
ps | grep microsocks
```

### 8. Проверка перезагрузки

```bash
# Перезагрузка роутера
reboot

# После перезагрузки:
/etc/init.d/dual-socks-proxy status
```

## Проверки перед деплоем на прод

### Функциональные тесты

- [ ] Пакет устанавливается без ошибок
- [ ] Сервис запускается автоматически
- [ ] Оба SOCKS прокси доступны на портах 11080 и 11081
- [ ] Трафик маршрутизируется через правильные WAN
- [ ] Сервис перезапускается при падении (procd respawn)
- [ ] Логи пишутся корректно
- [ ] Команда status работает

### Тесты стабильности

- [ ] Нет утечек памяти за 24 часа работы
- [ ] CPU usage < 1% в простое
- [ ] Сервис не подвешивает систему
- [ ] Корректная остановка при `stop`

### Интеграционные тесты

- [ ] Работа с captive-portal-dual контейнером
- [ ] Авторизация на обоих каналах
- [ ] Failover между каналами

## Устранение неполадок

### Сервис не запускается

```bash
# Проверить логи
logread -e dual-socks-proxy

# Проверить зависимости
which microsocks

# Проверить конфиг
uci show dual-socks-proxy

# Запустить вручную для дебага
sh -x /usr/bin/dual-socks-proxy start
```

### Нет соединения через SOCKS

```bash
# Проверить firewall
iptables -L -n | grep 1108

# Проверить интерфейсы
ip addr show

# Проверить маршруты
ip route show

# Тест локально на роутере
curl --socks5 localhost:11080 http://example.com
```

### Высокая нагрузка на CPU

```bash
# Проверить процессы
top -bn1 | head -20

# Проверить соединения
netstat -tn | wc -l
```

## Сборка для разных архитектур

```bash
# Для ARM (Raspberry Pi, etc.)
export ARCH=arm
export CROSS_COMPILE=arm-openwrt-linux-

# Для MIPS (старые роутеры)
export ARCH=mips
export CROSS_COMPILE=mips-openwrt-linux-

# Для x86-64
export ARCH=x86_64
export CROSS_COMPILE=x86_64-openwrt-linux-
```

## Примечания для разработки

- Код должен быть POSIX sh совместим (не bash)
- Избегать fork-бомб
- Проверять все внешние команды
- Обрабатывать ошибки
- Не хранить секреты в скриптах
