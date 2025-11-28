# Известные проблемы

**Дата:** 28 ноября 2025  
**Версия:** v2025.11.28.5

## Критичные проблемы

### ❌ Сервис не запускается через procd/init скрипт

**Статус:** Не решено  
**Приоритет:** Высокий  
**Затронутые версии:** Все версии

#### Описание

При запуске через `/etc/init.d/captive-monitor start` сервис не регистрируется в procd и процесс не запускается.

```bash
root@OpenWrt:~# /etc/init.d/captive-monitor start
root@OpenWrt:~# ps | grep openwrt_captive
# Нет процесса

root@OpenWrt:~# ubus call service list | grep captive-monitor
# Сервис не найден в procd
```

#### Симптомы

1. Команда `start` выполняется без ошибок, но процесс не запускается
2. Сервис не регистрируется в procd (не виден через `ubus call service list`)
3. Нет логов об ошибках в syslog
4. `status` команда не возвращает информацию

#### Что работает

- ✅ Ручной запуск скрипта работает корректно:
  ```bash
  /usr/sbin/openwrt_captive_monitor --monitor &
  ```
- ✅ Скрипт выполняет проверки каждые 60 секунд
- ✅ Логирование работает при ручном запуске

#### Что не работает

- ❌ Запуск через `/etc/init.d/captive-monitor start`
- ❌ Регистрация в procd
- ❌ Автоматический respawn при падении
- ❌ Управление через `service` команду

#### Возможные причины

1. **Проблема с procd_open_instance/procd_close_instance**
   - Init скрипт может неправильно вызывать procd функции
   - Возможно, не все параметры установлены корректно

2. **Проблема с переменными окружения**
   - procd может не передавать переменные окружения в процесс
   - Скрипт может зависеть от переменных, которые не установлены

3. **Проблема с правами доступа**
   - Возможно, procd запускает процесс с неправильными правами
   - Файлы могут иметь неправильные права (UID 1001 вместо root)

4. **Проблема с путями**
   - procd может использовать другой PATH
   - Скрипт может не находить необходимые команды

5. **Проблема с load_uci_config**
   - Функция может возвращать ошибку при запуске через procd
   - UCI может быть недоступен в момент запуска

#### Попытки исправления

1. ✅ Удален `set -eu` из скрипта (v2025.11.28.5)
   - Результат: Не помогло
   - Ручной запуск работает, procd - нет

2. ✅ Удален `set -e` полностью
   - Результат: Не помогло
   - Проблема не в обработке ошибок

#### Обходное решение

**Временное решение для пользователей:**

```bash
# 1. Установить пакет
opkg install openwrt-captive-monitor_2025.11.28.5-1_all.ipk

# 2. Настроить конфигурацию
uci set captive-monitor.config.enabled='1'
uci set captive-monitor.config.monitor_interval='60'
uci commit captive-monitor

# 3. Запустить вручную
/usr/sbin/openwrt_captive_monitor --monitor > /dev/null 2>&1 &

# 4. Проверить что работает
ps | grep openwrt_captive
logread | grep captive-monitor
```

**Автозапуск через rc.local:**

```bash
# Добавить в /etc/rc.local перед 'exit 0'
/usr/sbin/openwrt_captive_monitor --monitor > /dev/null 2>&1 &
```

#### Следующие шаги для исправления

1. **Добавить debug логирование в init скрипт**
   ```bash
   logger -t captive-monitor-debug "Starting service..."
   logger -t captive-monitor-debug "procd_open_instance called"
   logger -t captive-monitor-debug "Command: $SCRIPT_PATH $mode_arg"
   ```

2. **Проверить вызовы procd функций**
   - Убедиться что все функции вызываются в правильном порядке
   - Проверить что procd_close_instance вызывается

3. **Протестировать минимальный init скрипт**
   ```bash
   start_service() {
       procd_open_instance
       procd_set_param command /usr/sbin/openwrt_captive_monitor --monitor
       procd_set_param stdout 1
       procd_set_param stderr 1
       procd_close_instance
   }
   ```

4. **Сравнить с рабочим init скриптом**
   - Взять init скрипт от другого пакета, который работает
   - Адаптировать под наш случай

5. **Проверить на чистой установке OpenWrt**
   - Возможно, проблема специфична для тестовой среды
   - Протестировать на свежей VM с OpenWrt

## Некритичные проблемы

### ⚠️ Enable не создает симлинки автоматически

**Статус:** Не решено  
**Приоритет:** Низкий

#### Описание

Команда `/etc/init.d/captive-monitor enable` не создает симлинки в `/etc/rc.d/` автоматически.

```bash
root@OpenWrt:~# /etc/init.d/captive-monitor enable
root@OpenWrt:~# ls /etc/rc.d/*captive*
ls: /etc/rc.d/*captive*: No such file or directory
```

#### Обходное решение

Создать симлинки вручную:
```bash
ln -sf ../init.d/captive-monitor /etc/rc.d/S99captive-monitor
ln -sf ../init.d/captive-monitor /etc/rc.d/K10captive-monitor
```

Или добавить в postinst скрипт:
```bash
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor enable
    # Fallback если enable не сработал
    if [ ! -L /etc/rc.d/S99captive-monitor ]; then
        ln -sf ../init.d/captive-monitor /etc/rc.d/S99captive-monitor
        ln -sf ../init.d/captive-monitor /etc/rc.d/K10captive-monitor
    fi
fi
```

### ⚠️ Файлы имеют UID 1001 вместо root

**Статус:** Косметическая проблема  
**Приоритет:** Очень низкий

#### Описание

После установки некоторые файлы имеют UID 1001 вместо 0 (root):

```bash
-rwxr-xr-x    1 1001     1001          3239 Nov 28 23:31 /etc/init.d/captive-monitor
-rwxr-xr-x    1 1001     1001         47904 Nov 28 23:31 /usr/sbin/openwrt_captive_monitor
```

#### Влияние

Не влияет на функциональность, так как файлы исполняемые для всех (0755).

#### Причина

Файлы собираются в Docker контейнере с UID 1001 (builder user).

#### Решение

Добавить в build скрипт:
```bash
# Установить правильного владельца перед созданием архива
chown -R root:root "$data_dir"
```

## Решенные проблемы

### ✅ Malformed package file (решено в v2025.11.28.4)

**Проблема:** opkg выдавал ошибку "Malformed package file"  
**Причина:** Неправильный формат пакета (ar вместо tar.gz)  
**Решение:** Изменен формат в build_ipk_simple.sh  
**Статус:** ✅ Решено

### ✅ CI/CD workflow failures (решено в v2025.11.28.4)

**Проблема:** Workflow падали с ошибками sha256sum и артефактов  
**Причина:** Неправильный glob pattern и структура артефактов  
**Решение:** Исправлены workflows  
**Статус:** ✅ Решено

### ✅ Скрипт завершается после первой проверки (попытка в v2025.11.28.5)

**Проблема:** Скрипт запускался, но сразу завершался  
**Причина:** Предполагалось что `set -e` вызывает преждевременный выход  
**Решение:** Удален `set -e` из скрипта  
**Статус:** ⚠️ Не помогло - проблема оказалась в procd, а не в скрипте

## Рекомендации

### Для пользователей

1. **Используйте ручной запуск** до исправления проблемы с procd
2. **Добавьте в rc.local** для автозапуска при загрузке
3. **Мониторьте процесс** через `ps` и логи через `logread`

### Для разработчиков

1. **Приоритет #1:** Исправить запуск через procd
2. **Добавить debug логирование** в init скрипт
3. **Создать минимальный тестовый init скрипт** для изоляции проблемы
4. **Протестировать на разных версиях OpenWrt** (21.02, 22.03, 23.05, 24.10)
5. **Добавить автоматические тесты** для проверки запуска через procd

## Статистика

**Всего проблем:** 3  
**Критичных:** 1  
**Некритичных:** 2  
**Решенных:** 2  

**Процент готовности:** 70%  
- ✅ Установка через opkg: 100%
- ✅ Функциональность: 100%
- ❌ Запуск через procd: 0%
- ⚠️ Автозапуск: 50% (работает через rc.local)

## Контакты

**GitHub Issues:** https://github.com/nagual2/openwrt-captive-monitor/issues  
**Документация:** См. TEST_REPORT.md, IPK_FORMAT_INVESTIGATION.md

---

**Последнее обновление:** 28 ноября 2025, 23:35 UTC
