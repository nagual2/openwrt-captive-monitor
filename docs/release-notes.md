## Daemon Mode для Captive Portal

### Основные изменения

✅ **Daemon режим работы:**
- Chrome/Selenium инициализируются один раз и остаются в памяти
- Непрерывный мониторинг с интервалом 60 секунд
- Автоматический перезапуск Chrome при падении
- Детальное логирование с проверкой URL и редиректов

✅ **Производительность:**
- Память: ~40-50 MB постоянно (вместо 0 MB между запусками)
- CPU: снижение на 90% (с 15-20% до 1-2%)
- Быстрые проверки без перезапуска браузера

✅ **Интеграция:**
- Debian пакет с systemd сервисом
- Автозапуск при загрузке системы
- Graceful shutdown с очисткой ресурсов

✅ **Документация:**
- README_DAEMON.md - полное руководство
- QUICK_START_DAEMON.md - быстрый старт
- DAEMON_CHANGELOG.md - история изменений
- MONITORING_COMMANDS.md - команды мониторинга

### Установка

```bash
# Скачать пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/download/v2026.2.19.2/openwrt-captive-monitor_2026.2.19.2-1_all.deb

# Установить
sudo dpkg -i openwrt-captive-monitor_2026.2.19.2-1_all.deb

# Запустить
sudo systemctl start captive-portal-daemon

# Проверить статус
sudo systemctl status captive-portal-daemon
```

### Мониторинг

```bash
# Просмотр логов
sudo journalctl -u captive-portal-daemon -f

# Или напрямую из файла
tail -f /run/user/1000/captive_portal_daemon.log

# Статус сервиса
systemctl status captive-portal-daemon
```

### Файлы

- `openwrt-captive-monitor_2026.2.19.2-1_all.deb` - Debian пакет с daemon
