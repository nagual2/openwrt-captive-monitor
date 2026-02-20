# Команды мониторинга Captive Portal Daemon (из PowerShell)

## Просмотр логов

```powershell
# Последние 20 строк
wsl tail -20 /run/user/1000/captive_portal_daemon.log

# Последние 10 строк
wsl tail -10 /run/user/1000/captive_portal_daemon.log

# Мониторинг в реальном времени (Ctrl+C для выхода)
wsl tail -f /run/user/1000/captive_portal_daemon.log

# Весь лог
wsl cat /run/user/1000/captive_portal_daemon.log
```

## Статус daemon

```powershell
# Статус service
wsl sudo systemctl status captive-portal-daemon --no-pager

# Краткий статус
wsl bash -c "sudo systemctl is-active captive-portal-daemon"

# Проверка процесса
wsl bash -c "ps aux | grep captive-portal-daemon | grep -v grep"
```

## Управление daemon

```powershell
# Остановка
wsl sudo systemctl stop captive-portal-daemon

# Запуск
wsl sudo systemctl start captive-portal-daemon

# Перезапуск
wsl sudo systemctl restart captive-portal-daemon

# Статус после команды
wsl sudo systemctl status captive-portal-daemon --no-pager
```

## Systemd журнал

```powershell
# Последние 30 строк
wsl sudo journalctl -u captive-portal-daemon --no-pager -n 30

# Последние 50 строк
wsl sudo journalctl -u captive-portal-daemon --no-pager -n 50

# Мониторинг в реальном времени
wsl sudo journalctl -u captive-portal-daemon -f
```

## Быстрые проверки

```powershell
# Показать последние 5 строк лога
wsl tail -5 /run/user/1000/captive_portal_daemon.log

# Показать статус и последние логи
wsl sudo systemctl status captive-portal-daemon --no-pager; wsl tail -5 /run/user/1000/captive_portal_daemon.log

# Проверить что daemon работает
wsl bash -c "sudo systemctl is-active captive-portal-daemon && echo 'Daemon работает' || echo 'Daemon остановлен'"
```

## Проверка ресурсов

```powershell
# Использование памяти
wsl bash -c "ps aux | grep captive-portal-daemon | grep -v grep | awk '{print \$6}'"

# Количество процессов Chrome
wsl bash -c "ps aux | grep chrome | grep -v grep | wc -l"

# PID daemon
wsl cat /run/user/1000/captive_portal_daemon.pid
```

## Текущее состояние (2026-02-19 09:04)

```
✅ Daemon работает
✅ Chrome инициализирован
✅ Проверка #1 завершена успешно (авторизация активна)
✅ Проверка #2 началась

Время проверки: ~1.5 минуты (нормально для WSL)
Интервал: 60 секунд между проверками
Память: ~255 MB
```

## Удаление пакета (если нужно)

```powershell
# Остановка и удаление
wsl sudo systemctl stop captive-portal-daemon
wsl sudo dpkg -r openwrt-captive-monitor

# Полная очистка (включая конфигурацию)
wsl sudo dpkg --purge openwrt-captive-monitor
```
