# Отчет о тестировании релиза v2025.11.28.5

**Дата:** 28 ноября 2025  
**Релиз:** v2025.11.28.5  
**Тестовая среда:** OpenWrt 23.05.3 x86/64 @ 192.168.35.127

## Резюме

✅ **Установка через opkg:** Успешно  
✅ **Формат пакета:** Правильный (tar.gz)  
✅ **Файлы установлены:** Все файлы на месте  
✅ **Конфигурация UCI:** Работает  
✅ **Ручной запуск скрипта:** Работает корректно  
✅ **Удаление через opkg:** Работает  
⚠️ **Запуск через procd/init:** Не работает (требует дополнительного исследования)

## Детали тестирования

### 1. Скачивание и установка

```bash
# Скачивание с GitHub
$ curl -L -o /tmp/openwrt-captive-monitor_2025.11.28.5-1_all.ipk \
  https://github.com/nagual2/openwrt-captive-monitor/releases/download/v2025.11.28.5/openwrt-captive-monitor_2025.11.28.5-1_all.ipk

# Копирование на роутер
$ scp /tmp/openwrt-captive-monitor_2025.11.28.5-1_all.ipk root@192.168.35.127:/tmp/

# Установка
root@OpenWrt:~# opkg install /tmp/openwrt-captive-monitor_2025.11.28.5-1_all.ipk
Installing openwrt-captive-monitor (2025.11.28.5-1) to root...
Configuring openwrt-captive-monitor.
```

✅ **Установка успешна!**

### 2. Проверка формата пакета

```bash
root@OpenWrt:~# file /tmp/openwrt-captive-monitor_2025.11.28.5-1_all.ipk
/tmp/openwrt-captive-monitor_2025.11.28.5-1_all.ipk: gzip compressed data, from Unix, original size modulo 2^32 20480

root@OpenWrt:~# tar -tzf /tmp/openwrt-captive-monitor_2025.11.28.5-1_all.ipk
./debian-binary
./data.tar.gz
./control.tar.gz
```

✅ **Формат правильный (tar.gz)**

### 3. Проверка установленных файлов

```bash
root@OpenWrt:~# opkg list-installed | grep captive
openwrt-captive-monitor - 2025.11.28.5-1

root@OpenWrt:~# ls -la /usr/sbin/openwrt_captive_monitor /etc/init.d/captive-monitor /etc/config/captive-monitor
-rwxrwxrwx    1 root     root           420 Nov 28 22:00 /etc/config/captive-monitor
-rwxr-xr-x    1 1001     1001          3239 Nov 28 23:31 /etc/init.d/captive-monitor
-rwxr-xr-x    1 1001     1001         47904 Nov 28 23:31 /usr/sbin/openwrt_captive_monitor
```

✅ **Все файлы установлены**

### 4. Тестирование ручного запуска

```bash
root@OpenWrt:~# /usr/sbin/openwrt_captive_monitor --monitor > /tmp/manual-test.log 2>&1 &
root@OpenWrt:~# sleep 65
root@OpenWrt:~# ps | grep openwrt_captive
26724 root      1428 S    {openwrt_captive} /bin/sh /usr/sbin/openwrt_captive_monitor --monitor

root@OpenWrt:~# tail -10 /tmp/manual-test.log
[INFO] Запуск в режиме мониторинга (интервал: 60с)
[INFO] === Проверка подключения ===
[INFO] Интернет доступен по ICMP (сервер: 1.1.1.1)
[INFO] Следующая проверка через 60с
[INFO] === Проверка подключения ===
[INFO] Интернет доступен по ICMP (сервер: 1.1.1.1)
[INFO] Следующая проверка через 60с
```

✅ **Скрипт работает корректно при ручном запуске**
- Процесс остается активным
- Выполняет проверки каждые 60 секунд
- Логирование работает

### 5. Проблема с запуском через procd

```bash
root@OpenWrt:~# /etc/init.d/captive-monitor start
root@OpenWrt:~# ps | grep openwrt_captive
# Нет процесса

root@OpenWrt:~# ubus call service list | grep captive-monitor
# Сервис не зарегистрирован в procd
```

⚠️ **Сервис не запускается через init скрипт**

**Возможные причины:**
1. Проблема с procd_open_instance/procd_close_instance
2. Проблема с правами доступа
3. Проблема с переменными окружения
4. Проблема с путями при запуске через procd

### 6. Удаление пакета

```bash
root@OpenWrt:~# opkg remove openwrt-captive-monitor
Removing package openwrt-captive-monitor from root...
Not deleting modified conffile /etc/config/captive-monitor.

root@OpenWrt:~# ls /usr/sbin/openwrt_captive_monitor
ls: /usr/sbin/openwrt_captive_monitor: No such file or directory
```

✅ **Удаление работает корректно**

## Изменения в v2025.11.28.5

### Исправление формата IPK (v2025.11.28.4)

- Изменен формат с `ar` на `tar.gz`
- Пакеты теперь устанавливаются через opkg
- Исправлены workflow для CI/CD

### Исправление monitor mode (v2025.11.28.5)

- Удален `set -e` из скрипта
- Добавлен комментарий о явной обработке ошибок
- Скрипт больше не завершается преждевременно

## Выводы

### Что работает

1. ✅ **Установка через opkg** - основная цель достигнута
2. ✅ **Формат пакета** - соответствует OpenWrt 23.05+
3. ✅ **Функциональность скрипта** - работает при ручном запуске
4. ✅ **Конфигурация UCI** - загружается и применяется
5. ✅ **Удаление пакета** - работает корректно

### Что требует доработки

1. ⚠️ **Запуск через procd** - сервис не регистрируется в procd
   - Приоритет: Средний
   - Обходное решение: Ручной запуск работает
   - Требуется: Дополнительное исследование init скрипта

2. ⚠️ **Автозапуск (enable)** - не создает симлинки автоматически
   - Приоритет: Низкий
   - Обходное решение: Создание симлинков вручную

## Рекомендации

### Для пользователей

**Установка:**
```bash
# Скачать пакет
wget https://github.com/nagual2/openwrt-captive-monitor/releases/download/v2025.11.28.5/openwrt-captive-monitor_2025.11.28.5-1_all.ipk

# Установить
opkg install openwrt-captive-monitor_2025.11.28.5-1_all.ipk

# Настроить
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

# Запустить вручную (временное решение)
/usr/sbin/openwrt_captive_monitor --monitor &
```

### Для разработчиков

1. Исследовать проблему с procd:
   - Проверить вызовы procd_open_instance/procd_close_instance
   - Добавить debug логирование в init скрипт
   - Протестировать на чистой установке OpenWrt

2. Добавить автоматические тесты:
   - Smoke test установки на реальном устройстве
   - Проверка запуска через procd
   - Проверка автозапуска

3. Улучшить документацию:
   - Добавить troubleshooting секцию
   - Документировать известные проблемы
   - Добавить примеры ручного запуска

## Статус релиза

**v2025.11.28.5: Частично готов к использованию**

- ✅ Пакет устанавливается через opkg
- ✅ Функциональность работает
- ⚠️ Требуется ручной запуск (procd не работает)

**Рекомендация:** Использовать для тестирования и разработки. Для production требуется исправление проблемы с procd.
