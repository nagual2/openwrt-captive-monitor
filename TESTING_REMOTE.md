# Testing OpenWrt Captive Monitor on Remote Server

## 🚀 Быстрый старт тестирования

Если у вас есть Linux сервер с OpenWrt или Debian, вот как протестировать проект:

### Шаг 1: Подготовка

```bash
# Клонируйте репозиторий
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Сделайте скрипты исполняемыми
chmod +x test_captive_monitor.sh
chmod +x test_captive_scenarios.sh
```

### Шаг 2: Автоматическое тестирование

```bash
# Запустите полный тест (сборка + установка + тесты)
./test_captive_monitor.sh

# Или только сборка
./test_captive_monitor.sh --build-only

# Или только тестирование (если пакет уже установлен)
./test_captive_monitor.sh --test-only
```

### Шаг 3: Ручные тесты сценариев

```bash
# Настройка тестового окружения
./test_captive_scenarios.sh setup

# Тест с рабочим интернетом
./test_captive_scenarios.sh working

# Тест с симуляцией captive portal
./test_captive_scenarios.sh captive

# Тест в offline режиме
./test_captive_scenarios.sh offline

# Очистка
./test_captive_scenarios.sh cleanup
```

## 📋 Подробные инструкции по тестированию

### 1. Сборка пакета

#### На OpenWrt:
```bash
# Вариант 1: Через SDK (если есть)
cp -r package/openwrt-captive-monitor /opt/openwrt-sdk/package/
cd /opt/openwrt-sdk
make package/openwrt-captive-monitor/compile V=s

# Вариант 2: Через build_ipk.sh
cd /path/to/openwrt-captive-monitor
./scripts/build_ipk.sh --arch mips_24kc
```

#### На Debian/Ubuntu:
```bash
# Установите зависимости
sudo apt update
sudo apt install build-essential make curl wget xz-utils

# Скачайте OpenWrt SDK
wget https://downloads.openwrt.org/releases/23.05.3/targets/ath79/generic/openwrt-sdk-23.05.3-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz

# Соберите пакет
cp -r package/openwrt-captive-monitor openwrt-sdk-*/package/
cd openwrt-sdk-*
make package/openwrt-captive-monitor/compile V=s
```

### 2. Установка и настройка

#### На OpenWrt:
```bash
# Установите пакет
opkg install openwrt-captive-monitor_*.ipk

# Проверьте установку
opkg list-installed | grep captive-monitor

# Настройте сервис
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

# Запустите сервис
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
```

#### На Debian (для тестирования скриптов):
```bash
# Распакуйте пакет для анализа
mkdir /tmp/captive-test
cd /tmp/captive-test
ar x /path/to/openwrt-captive-monitor_*.ipk
tar -xf data.tar.gz

# Проверьте синтаксис
bash -n usr/sbin/openwrt_captive_monitor
```

### 3. Тестирование функциональности

#### Базовые тесты:
```bash
# Тест синтаксиса
bash -n package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor

# Тест сборки
./scripts/build_ipk.sh --help

# Проверка зависимостей
for dep in curl nft iptables dnsmasq; do
    if command -v "$dep" >/dev/null 2>&1; then
        echo "✅ $dep - доступен"
    else
        echo "❌ $dep - отсутствует"
    fi
done
```

#### Тестирование captive portal detection:
```bash
# Создайте тестовую страницу captive portal
mkdir -p /tmp/test_portal
echo '<html><head><meta http-equiv="refresh" content="0; url=https://example.com/login"></head><body><h1>Portal Login</h1></body></html>' > /tmp/test_portal/index.html

# Запустите тестовый сервер
python3 -m http.server 8080 -d /tmp/test_portal &
SERVER_PID=$!

# Протестируйте detection
curl -v http://connectivitycheck.gstatic.com/generate_204

# Остановите сервер
kill $SERVER_PID
```

#### Тестирование firewall rules:
```bash
# Проверьте nftables (если доступно)
nft list ruleset | grep -i captive || echo "No captive rules"

# Проверьте iptables (если доступно)
iptables-save | grep -i captive || echo "No captive rules"
```

### 4. Проверка конфигурации

#### UCI настройки (OpenWrt):
```bash
# Покажите текущую конфигурацию
uci show captive-monitor

# Тестируйте различные настройки
uci set captive-monitor.config.mode='oneshot'
uci set captive-monitor.config.monitor_interval='30'
uci commit captive-monitor
/etc/init.d/captive-monitor reload
```

#### Environment variables (любой Linux):
```bash
# Тестируйте с переменными окружения
MONITOR_INTERVAL=30 WIFI_INTERFACE=eth0 ./openwrt_captive_monitor.sh --oneshot

# Проверьте логи
logread | grep captive-monitor
tail -f /var/log/messages | grep captive-monitor
```

### 5. Stress testing

```bash
# Мониторинг в течение времени
timeout 300 ./openwrt_captive_monitor.sh --monitor &
MONITOR_PID=$!

# Следите за ресурсами
watch -n 5 'ps aux | grep captive-monitor'
watch -n 5 'nft list ruleset | grep -c captive_monitor || echo "0 rules"'

# Остановите
kill $MONITOR_PID
```

### 6. Проверка cleanup

```bash
# Запустите сервис
/etc/init.d/captive-monitor start

# Проверьте созданные правила
nft list ruleset | grep captive_monitor || echo "No rules found"

# Остановите сервис
/etc/init.d/captive-monitor stop

# Проверьте очистку
nft list ruleset | grep captive_monitor && echo "Rules not cleaned!" || echo "✅ Cleanup successful"
```

## 🔍 Валидация результатов

### Ожидаемые результаты:

1. **Рабочий интернет**: Нет firewall правил, сервис не активирует captive mode
2. **Captive portal**: Создаются firewall правила, запускается HTTP сервер
3. **Offline**: Попытки перезапуска WiFi, активация captive mode
4. **Cleanup**: Все правила и процессы корректно удаляются

### Проверка артефактов:
```bash
# Проверьте созданные файлы
ls -la /tmp/dnsmasq.d/captive_intercept.conf 2>/dev/null || echo "No DNS config"
ls -la /tmp/captive_httpd/ 2>/dev/null || echo "No HTTP server"

# Проверьте firewall
nft list ruleset | grep -A 5 -B 5 captive_monitor || echo "No NFT rules"
iptables-save | grep -i captive || echo "No IPT rules"

# Проверьте процессы
ps aux | grep -E "(captive|dnsmasq|httpd)" | grep -v grep
```

## 🚨 Troubleshooting

### Если тесты не проходят:

1. **Проверьте зависимости**:
   ```bash
   opkg list-installed | grep -E "(curl|dnsmasq|nft|iptables)"
   ```

2. **Проверьте синтаксис**:
   ```bash
   bash -n /usr/sbin/openwrt_captive_monitor
   ```

3. **Проверьте логи**:
   ```bash
   logread | tail -50 | grep captive
   dmesg | tail -20
   ```

4. **Проверьте права**:
   ```bash
   ls -la /usr/sbin/openwrt_captive_monitor
   ```

5. **Тестируйте по частям**:
   ```bash
   # Только сборка
   ./test_captive_monitor.sh --build-only

   # Только установка
   ./test_captive_monitor.sh --install-only

   # Только тесты
   ./test_captive_monitor.sh --test-only
   ```

## 📊 Сбор результатов

После тестирования соберите:
```bash
# Системная информация
uname -a
cat /etc/os-release

# Установленные пакеты
opkg list-installed 2>/dev/null || dpkg -l

# Firewall состояние
nft list ruleset 2>/dev/null || iptables-save

# Логи
logread 2>/dev/null | grep captive || journalctl -u captive-monitor 2>/dev/null || echo "No logs found"

# Процессы
ps aux | grep captive
```

**Сохраните эти данные для анализа!** 📋
