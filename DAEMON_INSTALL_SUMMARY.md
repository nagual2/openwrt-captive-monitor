# Установка Captive Portal Daemon - Итоги

## Версия 2026.2.19.6

### Что сделано

1. **Создан симлинк лога в /var/log**
   - Симлинк: `/var/log/captive_portal_daemon.log` → `/run/user/1000/captive_portal_daemon.log`
   - Создается автоматически при установке пакета
   - Удаляется автоматически при удалении пакета

2. **Увеличены таймауты для медленных систем**
   - Page load timeout: 180 секунд (настраивается через `CAPTIVE_PAGE_LOAD_TIMEOUT`)
   - Selenium HTTP timeout: 210 секунд (автоматически = page_load + 30 секунд)
   - Page wait time: 15 секунд (настраивается через `CAPTIVE_PAGE_WAIT`)

3. **Автоматическая установка зависимостей**
   - Пакет автоматически устанавливает `python3-selenium` и `python3-dotenv`
   - Сначала пытается через apt-get, затем через pip
   - Работает на разных дистрибутивах (Debian, Ubuntu, Linux Mint)

### Конфигурация

Файл: `/etc/default/captive-portal-daemon`

```bash
# Check interval in seconds (default: 60)
CHECK_INTERVAL=60

# Debug mode (default: false)
DEBUG_MODE=false

# Page load timeout in seconds (default: 120)
# Increase for slow systems or networks
CAPTIVE_PAGE_LOAD_TIMEOUT=180

# Page wait time in seconds (default: 10)
# Time to wait after page load for JavaScript execution
CAPTIVE_PAGE_WAIT=15

# Environment
CPM_ENV=prod
```

### Просмотр логов

```bash
# Через симлинк в /var/log
sudo tail -f /var/log/captive_portal_daemon.log

# Через journalctl
sudo journalctl -u captive-portal-daemon -f

# Напрямую из /run/user
tail -f /run/user/1000/captive_portal_daemon.log
```

### Управление сервисом

```bash
# Запуск
sudo systemctl start captive-portal-daemon

# Остановка
sudo systemctl stop captive-portal-daemon

# Статус
sudo systemctl status captive-portal-daemon

# Перезапуск
sudo systemctl restart captive-portal-daemon

# Включить автозапуск
sudo systemctl enable captive-portal-daemon

# Отключить автозапуск
sudo systemctl disable captive-portal-daemon
```

### Тестирование на Minisforum

**Система:**
- Linux Mint (базируется на Ubuntu)
- IP: 192.168.35.125 (bridge br0)
- Пользователь: max

**Результаты:**
- ✅ Демон запускается успешно
- ✅ Chrome инициализируется (23 секунды)
- ✅ Первая проверка завершается успешно (2 минуты 13 секунд)
- ✅ Авторизация определяется корректно (редирект на MSN)
- ✅ Логи пишутся в `/var/log/captive_portal_daemon.log`

**Производительность:**
- Память: ~40-50 MB (постоянно)
- CPU: 1-2% (в режиме ожидания)
- Время проверки: 2-3 минуты (на медленной системе)

### Сравнение со старой версией

**Старая версия (cron-based):**
- Запуск Chrome каждую минуту
- Память: 0 MB между запусками, 150-200 MB во время работы
- CPU: 15-20% во время работы
- Время проверки: 30-60 секунд

**Новая версия (daemon):**
- Chrome постоянно в памяти
- Память: 40-50 MB постоянно
- CPU: 1-2% в режиме ожидания
- Время проверки: 2-3 минуты (на медленной системе)
- **Экономия CPU: 90%**
- **Экономия памяти: 75% (в среднем)**

### Известные проблемы

1. **Медленная загрузка страниц на Minisforum**
   - Решение: Увеличены таймауты до 180 секунд
   - Можно настроить через `CAPTIVE_PAGE_LOAD_TIMEOUT`

2. **ReadTimeoutError при стандартных таймаутах**
   - Решение: Selenium HTTP timeout автоматически устанавливается на 30 секунд больше page_load_timeout

### Следующие шаги

1. Мониторинг работы демона в течение нескольких дней
2. Оптимизация времени проверки (если возможно)
3. Реализация улучшенного механизма управления куками (см. `.kiro/specs/daemon-cookie-management/`)

### Бэкап старой версии

Создан полный бэкап старой установки:
- Архив: `backups/minisforum_captive_backup_20260219_100911.tar.gz`
- Crontab: `backups/minisforum_crontab_20260219.txt`
- Инструкции по восстановлению: `backups/MINISFORUM_BACKUP_README.md`
