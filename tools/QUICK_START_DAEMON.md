# Quick Start: Captive Portal Daemon

## Быстрый старт

### 1. Тестирование (30 секунд)

```bash
cd /mnt/c/Git/openwrt-captive-monitor
bash tools/test_daemon.sh test
```

Ожидаемый результат:
```
✅ Daemon работает стабильно
```

### 2. Запуск daemon

```bash
bash tools/test_daemon.sh start
```

### 3. Проверка статуса

```bash
bash tools/test_daemon.sh status
```

Ожидаемый результат:
```
✅ Daemon запущен (PID: 1234)
```

### 4. Просмотр логов

```bash
# Последние 20 строк
bash tools/test_daemon.sh logs

# Мониторинг в реальном времени
bash tools/test_daemon.sh tail
```

### 5. Остановка daemon

```bash
bash tools/test_daemon.sh stop
```

## Команды управления

| Команда | Описание |
|---------|----------|
| `test` | Тест daemon на 30 секунд |
| `start` | Запустить daemon в фоне |
| `stop` | Остановить daemon |
| `restart` | Перезапустить daemon |
| `status` | Проверить статус daemon |
| `logs` | Показать последние 20 строк лога |
| `tail` | Мониторинг лога в реальном времени |

## Файлы

- **Скрипт**: `tools/captive_portal_selenium2.py`
- **Управление**: `tools/test_daemon.sh`
- **PID**: `/tmp/captive_portal_daemon.pid`
- **Лог**: `/tmp/captive_portal_daemon.log`
- **Куки**: `/tmp/captive_portal_cookies.pkl`

## Отладка

### Запуск в DEBUG режиме

```bash
CAPTIVE_DAEMON_DEBUG=1 python3 tools/captive_portal_selenium2.py
```

### Проверка процессов

```bash
ps aux | grep captive_portal_selenium2
```

### Проверка Chrome

```bash
ps aux | grep chrome
```

## Сравнение с оригинальным скриптом

| Характеристика | Оригинал | Daemon |
|----------------|----------|--------|
| Запуск | Каждую минуту (cron) | Один раз (daemon) |
| Chrome | Запускается каждый раз | Один раз при старте |
| CPU | 15-20% (средняя) | 1-2% (средняя) |
| Память | 0 MB (между запусками) | 40-50 MB (постоянно) |
| Время проверки | 5-10 секунд | 2-3 секунды |

## Рекомендации

- ✅ Используйте daemon на системах с памятью >256 MB
- ✅ Используйте оригинальный скрипт на роутерах с памятью <128 MB
- ✅ Мониторьте логи первые несколько часов после запуска
- ✅ Настройте автозапуск через systemd для production

## Troubleshooting

### Daemon не запускается

```bash
# Проверить Chrome
google-chrome --version

# Проверить Selenium
python3 -c "from selenium import webdriver; print('OK')"

# Запустить в DEBUG режиме
CAPTIVE_DAEMON_DEBUG=1 python3 tools/captive_portal_selenium2.py
```

### Daemon завершается сразу

```bash
# Проверить логи
cat /tmp/captive_portal_daemon.log

# Проверить ошибки
tail -50 /tmp/captive_portal_daemon.log
```

### Высокое потребление памяти

Это нормально. Chrome в headless режиме потребляет ~40-50 MB.

## Следующие шаги

1. Протестируйте daemon в течение нескольких часов
2. Проверьте стабильность работы
3. Настройте автозапуск через systemd (см. README_DAEMON.md)
4. Мигрируйте с cron на daemon (см. DAEMON_CHANGELOG.md)
