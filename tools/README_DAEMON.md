# Captive Portal Daemon

## Описание

`captive_portal_selenium2.py` - это daemon версия скрипта авторизации на captive портале.

### Отличия от оригинального скрипта

| Характеристика | Оригинал (selenium.py) | Daemon (selenium2.py) |
|----------------|------------------------|----------------------|
| Режим работы | Запускается каждую минуту через cron | Запускается один раз и висит в памяти |
| Chrome/Selenium | Запускается и закрывается каждый раз | Инициализируется один раз при старте |
| Нагрузка на CPU | Высокая (постоянные запуски) | Низкая (только проверки) |
| Потребление памяти | Низкое (работает 5-10 секунд) | ~40-50 MB (постоянно) |
| Время проверки | 5-10 секунд (с инициализацией) | 2-3 секунды (без инициализации) |

### Преимущества daemon режима

1. **Меньше нагрузка на CPU** - Chrome запускается один раз, а не каждую минуту
2. **Быстрее проверки** - нет overhead на инициализацию Chrome/Selenium
3. **Меньше износ eMMC** - меньше операций записи логов
4. **Graceful shutdown** - корректная остановка по сигналу SIGTERM

## Установка зависимостей

```bash
# В WSL или Linux
pip3 install selenium
```

## Использование

### Запуск daemon

```bash
# Запуск в фоне
python3 tools/captive_portal_selenium2.py &

# Или через тестовый скрипт
bash tools/test_daemon.sh start
```

### Остановка daemon

```bash
# Через тестовый скрипт
bash tools/test_daemon.sh stop

# Или вручную
kill -TERM $(cat /tmp/captive_portal_daemon.pid)
```

### Проверка статуса

```bash
bash tools/test_daemon.sh status
```

### Просмотр логов

```bash
# Последние 20 строк
bash tools/test_daemon.sh logs

# Мониторинг в реальном времени
bash tools/test_daemon.sh tail
```

### Тестирование

```bash
# Тест на 30 секунд
bash tools/test_daemon.sh test
```

## Конфигурация

### Переменные окружения

- `CAPTIVE_DAEMON_DEBUG=1` - включить вывод в stdout (для отладки)

### Файлы

- **PID файл**: `/run/user/<uid>/captive_portal_daemon.pid` или `/tmp/captive_portal_daemon.pid`
- **Лог файл**: `/run/user/<uid>/captive_portal_daemon.log` или `/tmp/captive_portal_daemon.log`
- **Куки**: `/run/user/<uid>/captive_portal_cookies.pkl` или `/tmp/captive_portal_cookies.pkl`

### Интервал проверки

По умолчанию: 60 секунд (1 минута)

Изменить в коде:
```python
CHECK_INTERVAL = 60  # секунды
```

## Интеграция с systemd

Создайте systemd unit файл:

```ini
# /etc/systemd/system/captive-portal-daemon.service
[Unit]
Description=Captive Portal Authentication Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=your-user
ExecStart=/usr/bin/python3 /path/to/captive_portal_selenium2.py
Restart=on-failure
RestartSec=10
StandardOutput=null
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl daemon-reload
sudo systemctl enable captive-portal-daemon
sudo systemctl start captive-portal-daemon
sudo systemctl status captive-portal-daemon
```

## Мониторинг

### Проверка работы daemon

```bash
# Проверить процесс
ps aux | grep captive_portal_selenium2

# Проверить PID файл
cat /tmp/captive_portal_daemon.pid

# Проверить логи
tail -f /tmp/captive_portal_daemon.log
```

### Типичные сообщения в логе

```
=== Captive Portal Daemon ===
PID: 1234
=== Запуск daemon ===
Интервал проверки: 60 секунд
Инициализация Chrome...
✅ Chrome инициализирован
=== Проверка #1 (12:34:56) ===
✅ Авторизация активна
```

## Troubleshooting

### Daemon не запускается

1. Проверьте что Chrome установлен:
   ```bash
   google-chrome --version
   ```

2. Проверьте что Selenium установлен:
   ```bash
   python3 -c "from selenium import webdriver; print('OK')"
   ```

3. Проверьте логи:
   ```bash
   cat /tmp/captive_portal_daemon.log
   ```

### Daemon завершается сразу после запуска

1. Запустите в DEBUG режиме:
   ```bash
   CAPTIVE_DAEMON_DEBUG=1 python3 tools/captive_portal_selenium2.py
   ```

2. Проверьте ошибки в логе

### Высокое потребление памяти

Chrome в headless режиме потребляет ~40-50 MB. Это нормально.

Если потребление растет со временем:
1. Перезапустите daemon
2. Проверьте версию Chrome и Selenium

### Daemon не реагирует на SIGTERM

Принудительная остановка:
```bash
kill -9 $(cat /tmp/captive_portal_daemon.pid)
```

## Сравнение производительности

### Тест: 10 проверок портала

**Оригинальный скрипт (cron каждую минуту):**
- Время: 10 минут
- Запусков Chrome: 10
- Средняя нагрузка CPU: 15-20% (пики при запуске)
- Потребление памяти: 0 MB (между запусками)

**Daemon:**
- Время: 10 минут
- Запусков Chrome: 1
- Средняя нагрузка CPU: 1-2% (только проверки)
- Потребление памяти: 40-50 MB (постоянно)

## Рекомендации

1. **Для роутеров с ограниченной памятью (<128 MB)** - используйте оригинальный скрипт через cron
2. **Для роутеров с достаточной памятью (>256 MB)** - используйте daemon для меньшей нагрузки на CPU
3. **Для тестирования** - используйте daemon с DEBUG режимом

## Миграция с cron на daemon

1. Остановите cron задачу:
   ```bash
   crontab -e
   # Закомментируйте строку с captive_portal_selenium.py
   ```

2. Запустите daemon:
   ```bash
   bash tools/test_daemon.sh start
   ```

3. Проверьте работу:
   ```bash
   bash tools/test_daemon.sh status
   bash tools/test_daemon.sh logs
   ```

4. Настройте автозапуск через systemd (см. выше)
