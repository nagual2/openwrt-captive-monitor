# OpenWRT Captive Portal Monitor

## 📋 Описание

Автоматический скрипт для OpenWRT, который:
- ✅ Проверяет доступность интернета
- 🔄 Перезагружает WiFi при отсутствии связи
- 🌐 **DNS Spoofing**: Все DNS запросы возвращают адрес шлюза (через dnsmasq)
- 🔀 **DNS Redirect**: Перехватывает DNS запросы (TCP/UDP 53) и направляет на локальный DNS
- 🔀 **HTTP/HTTPS Redirect**: Редиректит веб-трафик на captive portal шлюза
- ⏳ Ожидает восстановления интернета
- ✨ Автоматически убирает все редиректы после авторизации
- ⚡ Минимальное TTL для DNS записей (0 секунд)

## 🚀 Установка

### 1. Копирование скрипта

```bash
# Скопировать на OpenWRT роутер
scp openwrt_captive_monitor.sh root@192.168.1.1:/usr/bin/

# Сделать исполняемым
ssh root@192.168.1.1 "chmod +x /usr/bin/openwrt_captive_monitor.sh"
```

### 2. Настройка автозапуска (init.d)

Создайте файл `/etc/init.d/captive-monitor`:

```bash
#!/bin/sh /etc/rc.common

START=99
STOP=10

USE_PROCD=1

start_service() {
    procd_open_instance
    procd_set_param command /usr/bin/openwrt_captive_monitor.sh --monitor
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
```

Активация сервиса:

```bash
chmod +x /etc/init.d/captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
```

### 3. Настройка через cron (альтернатива)

Добавьте в `/etc/crontabs/root`:

```bash
# Проверка каждые 2 минуты
*/2 * * * * /usr/bin/openwrt_captive_monitor.sh --oneshot
```

Перезапустите cron:

```bash
/etc/init.d/cron restart
```

## ⚙️ Конфигурация

### Переменные окружения

```bash
export WIFI_INTERFACE="phy1-sta0"     # Физический интерфейс
export WIFI_LOGICAL="wwan"            # Логический интерфейс OpenWRT
export MONITOR_INTERVAL=60            # Интервал проверки (секунды)
```

### Параметры командной строки

```bash
# Однократная проверка
openwrt_captive_monitor.sh --oneshot

# Постоянный мониторинг
openwrt_captive_monitor.sh --monitor

# Кастомные параметры
openwrt_captive_monitor.sh --monitor \
  --interface wlan0 \
  --logical wan \
  --interval 30
```

### Редактирование настроек в скрипте

Откройте скрипт и измените секцию КОНФИГУРАЦИЯ:

```bash
# Сетевые интерфейсы
WIFI_INTERFACE="${WIFI_INTERFACE:-phy1-sta0}"
WIFI_LOGICAL="${WIFI_LOGICAL:-wwan}"

# Серверы для проверки интернета
PING_SERVERS="1.1.1.1 8.8.8.8 9.9.9.9"

# Параметры проверки
GATEWAY_CHECK_RETRIES=3
INTERNET_CHECK_RETRIES=3
MAX_WAIT_TIME=90

# Интервал мониторинга
MONITOR_INTERVAL=60
```

## 📖 Использование

### Режимы работы

#### 1. Oneshot (однократная проверка)

```bash
openwrt_captive_monitor.sh --oneshot
```

Выполняет:
1. Проверку интернета
2. Перезапуск WiFi (если нужно)
3. Установку редиректа (если нужно)
4. Ожидание восстановления
5. Выход

#### 2. Monitor (постоянный мониторинг)

```bash
openwrt_captive_monitor.sh --monitor
```

Выполняет проверку в бесконечном цикле с заданным интервалом.

### Примеры

```bash
# Проверка с логированием
openwrt_captive_monitor.sh --oneshot 2>&1 | tee /tmp/captive.log

# Мониторинг в фоне
openwrt_captive_monitor.sh --monitor &

# Мониторинг с кастомным интервалом
openwrt_captive_monitor.sh --monitor --interval 30

# Проверка конкретного интерфейса
openwrt_captive_monitor.sh --oneshot --interface wlan0 --logical wan
```

## 🔍 Диагностика

### Проверка логов

```bash
# Системные логи
logread | grep captive-monitor

# Последние 50 записей
logread | grep captive-monitor | tail -50

# Мониторинг в реальном времени
logread -f | grep captive-monitor
```

### Проверка состояния

```bash
# Проверка интерфейса
ip link show phy1-sta0
ip addr show phy1-sta0

# Проверка шлюза
ip route show dev phy1-sta0

# Проверка правил iptables
iptables -t nat -L CAPTIVE_REDIRECT -n -v
iptables -t nat -L CAPTIVE_DNS_REDIRECT -n -v

# Проверка всех редиректов
iptables -t nat -L PREROUTING -n -v | grep CAPTIVE
```

### Проверка DNS spoofing

```bash
# Проверка конфигурации dnsmasq
cat /tmp/dnsmasq.d/captive-portal.conf

# Проверка работы DNS
nslookup google.com
nslookup example.com

# Должны возвращать IP шлюза, если captive mode активен
```

### Ручное тестирование

```bash
# Проверка ping
ping -c 1 -W 2 8.8.8.8

# Проверка шлюза
GATEWAY=$(ip route show dev phy1-sta0 | grep default | awk '{print $3}')
ping -c 1 -W 2 $GATEWAY

# Проверка DNS
nslookup google.com
dig google.com
```

## 🛠️ Устранение неполадок

### Проблема: Скрипт не запускается

```bash
# Проверка прав
ls -la /usr/bin/openwrt_captive_monitor.sh

# Должно быть: -rwxr-xr-x
chmod +x /usr/bin/openwrt_captive_monitor.sh

# Проверка shebang
head -1 /usr/bin/openwrt_captive_monitor.sh
# Должно быть: #!/bin/sh
```

### Проблема: WiFi не перезапускается

```bash
# Проверка существования интерфейса
ip link show phy1-sta0

# Проверка логического интерфейса
ifstatus wwan

# Ручной перезапуск
ifdown wwan && sleep 2 && ifup wwan
```

### Проблема: Редирект не работает

```bash
# Проверка модулей iptables
lsmod | grep iptable_nat
lsmod | grep nf_nat

# Загрузка модулей (если нужно)
modprobe iptable_nat
modprobe nf_nat

# Проверка правил
iptables -t nat -L -n -v

# Ручная установка полного captive режима
GATEWAY=$(ip route | grep default | awk '{print $3}')
ROUTER_IP=$(ip -4 addr show dev phy1-sta0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)

# DNS Spoofing
mkdir -p /tmp/dnsmasq.d
cat > /tmp/dnsmasq.d/captive-portal.conf <<EOF
address=/#/$GATEWAY
local-ttl=0
min-cache-ttl=0
max-cache-ttl=0
no-negcache
EOF
/etc/init.d/dnsmasq restart

# DNS Redirect
iptables -t nat -A PREROUTING -i phy1-sta0 -p udp --dport 53 \
  -j DNAT --to-destination $ROUTER_IP:53
iptables -t nat -A PREROUTING -i phy1-sta0 -p tcp --dport 53 \
  -j DNAT --to-destination $ROUTER_IP:53

# HTTP/HTTPS Redirect
iptables -t nat -A PREROUTING -i phy1-sta0 -p tcp --dport 80 \
  -j DNAT --to-destination $GATEWAY:80
iptables -t nat -A PREROUTING -i phy1-sta0 -p tcp --dport 443 \
  -j DNAT --to-destination $GATEWAY:80
```

### Проблема: DNS не резолвится

```bash
# Проверка dnsmasq
/etc/init.d/dnsmasq status

# Перезапуск dnsmasq
/etc/init.d/dnsmasq restart

# Проверка конфигурации
cat /tmp/dnsmasq.d/captive-portal.conf

# Проверка DNS запросов
nslookup google.com
dig google.com

# Проверка логов dnsmasq
logread | grep dnsmasq
```

### Проблема: Интернет не восстанавливается

```bash
# Проверка DNS
cat /etc/resolv.conf

# Проверка маршрутов
ip route show

# Проверка firewall
iptables -L -n -v

# Проверка connectivity check URLs
curl -I http://connectivitycheck.gstatic.com/generate_204
curl -I http://captive.apple.com/hotspot-detect.html
```

## 🔗 Интеграция с существующим проектом

Скрипт можно интегрировать с вашим Python проектом:

```bash
# Вызов из Python
import subprocess

result = subprocess.run(
    ['/usr/bin/openwrt_captive_monitor.sh', '--oneshot'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Интернет доступен")
else:
    print("Требуется авторизация")
    # Запустить ваш Python скрипт авторизации
    subprocess.run(['python3', '/path/to/main.py'])
```

## 📚 Готовые решения на GitHub

### Для OpenWRT:

1. **uspot** - https://github.com/f00b4r0/uspot
   - Полноценный captive portal для OpenWRT
   - 38 звезд, активная разработка

2. **apfree-wifidog** - https://github.com/liudf0716/apfree-wifidog
   - High-performance captive portal
   - 899 звезд, C, libevent
   - Поддержка OpenWRT

3. **lua-captive-portal** - https://github.com/ptkoz/lua-captive-portal
   - Captive portal на Lua для OpenWRT
   - Token authentication

### Для автоматической авторизации:

1. **CaptivePortalAutologin** (Android) - https://github.com/jsparber/CaptivePortalAutologin
   - Сохраняет процедуру логина и воспроизводит
   - 61 звезда

2. **NetworkAutoLogin** (iOS) - https://github.com/tyilo/NetworkAutoLogin
   - Автоматический логин на iOS
   - 134 звезды

3. **AutoFi** (Tasker) - https://github.com/harsgak/AutoFi
   - Auto-login assistant для WiFi captive portal

### Скрипты для конкретных порталов:

- https://github.com/ael-code/sapienza_wireless_cpal - Sapienza wireless
- https://github.com/cipherswami/autologin-iitk - IITK firewall auth
- https://github.com/samvid25/Captive-Portal-Auto-Login - Python скрипт

## 🔐 Безопасность

⚠️ **Важно:**

1. Скрипт требует прав root
2. Редирект трафика может быть небезопасен в публичных сетях
3. Используйте VPN после авторизации для защиты трафика
4. Не храните пароли в скрипте

## 📝 Лицензия

MIT License - свободное использование

## 🤝 Вклад

Приветствуются pull requests и issue reports!

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `logread | grep captive-monitor`
2. Запустите в debug режиме: `sh -x /usr/bin/openwrt_captive_monitor.sh --oneshot`
3. Проверьте конфигурацию сети: `ifconfig`, `ip route`

---

**Автор:** Kombai AI Assistant  
**Дата:** 2024