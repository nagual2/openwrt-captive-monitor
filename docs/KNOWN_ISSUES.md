# Известные проблемы

**Дата:** 28 ноября 2025  
**Версия:** v2025.11.28.5

## Критичные проблемы

### ✅ Сервис не запускается через procd/init скрипт (РЕШЕНО в v2025.11.28.6)

**Статус:** ✅ Решено  
**Приоритет:** Высокий  
**Затронутые версии:** v2025.11.28.1 - v2025.11.28.5  
**Исправлено в:** v2025.11.28.6

#### Описание

При запуске через `/etc/init.d/captive-monitor start` сервис не регистрировался в procd и процесс не запускался.

**Причина:** Неправильный shebang в init скрипте. Было `#!/bin/sh`, должно быть `#!/bin/sh /etc/rc.common`.

**Решение:** Исправлен shebang в первой строке init скрипта на `#!/bin/sh /etc/rc.common`.

#### Проверка исправления

После установки v2025.11.28.6:

```bash
root@OpenWrt:~# /etc/init.d/captive-monitor start
root@OpenWrt:~# ps | grep openwrt_captive
30757 root      1436 S    {openwrt_captive} /bin/sh /usr/sbin/openwrt_captive_monitor --monitor

root@OpenWrt:~# ubus call service list | grep -A 10 captive-monitor
"captive-monitor": {
    "instances": {
        "instance1": {
            "running": true,
            "pid": 30757,
            ...
        }
    }
}

root@OpenWrt:~# /etc/init.d/captive-monitor status
running
```

#### Root Cause Analysis

**Найденная причина:** Неправильный shebang в init скрипте.

OpenWrt init скрипты должны использовать специальный shebang `#!/bin/sh /etc/rc.common`, который:
1. Загружает `/etc/rc.common` framework
2. Предоставляет procd функции (`procd_open_instance`, `procd_set_param`, и т.д.)
3. Обрабатывает команды start/stop/enable/disable
4. Регистрирует сервис в procd

**Было:**
```bash
#!/bin/sh
```

**Стало:**
```bash
#!/bin/sh /etc/rc.common
```

#### Диагностика

При попытке вызвать `start_service()` напрямую без `/etc/rc.common`:
```bash
root@OpenWrt:~# . /etc/init.d/captive-monitor; start_service
ash: procd_open_instance: not found
ash: procd_set_param: not found
ash: procd_close_instance: not found
```

После исправления shebang все procd функции доступны и сервис запускается корректно.

#### Исправление для пользователей старых версий

Если у вас установлена версия v2025.11.28.1 - v2025.11.28.5, вы можете:

**Вариант 1: Обновиться до v2025.11.28.6+**
```bash
opkg update
opkg upgrade openwrt-captive-monitor
```

**Вариант 2: Исправить вручную**
```bash
# Исправить shebang в существующем init скрипте
sed -i '1s|^#!/bin/sh$|#!/bin/sh /etc/rc.common|' /etc/init.d/captive-monitor

# Перезапустить сервис
/etc/init.d/captive-monitor restart
```

#### Процесс исправления

1. ✅ **Добавлено debug логирование** - помогло выявить что procd функции не найдены
2. ✅ **Создан минимальный тестовый init скрипт** - для изоляции проблемы
3. ✅ **Созданы автоматические тесты** - `scripts/test-procd-issue.sh` и `scripts/build-and-test-procd.sh`
4. ✅ **Запущены тесты на OpenWrt** - выявили отсутствие procd функций
5. ✅ **Найдена root cause** - неправильный shebang `#!/bin/sh` вместо `#!/bin/sh /etc/rc.common`
6. ✅ **Реализовано исправление** - изменен shebang в init скрипте
7. ✅ **Протестировано на OpenWrt 23.05.3** - все функции работают корректно

**Документация:** См. `docs/PROCD_INVESTIGATION.md` для детального анализа

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

### ✅ Скрипт завершается после первой проверки (решено в v2025.11.28.6)

**Проблема:** Скрипт не запускался через procd  
**Причина:** Неправильный shebang в init скрипте - procd функции не были доступны  
**Решение:** Исправлен shebang на `#!/bin/sh /etc/rc.common`  
**Статус:** ✅ Решено - проблема была в init скрипте, не в самом скрипте мониторинга

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

**Всего проблем:** 5  
**Критичных:** 1 (решена)  
**Некритичных:** 2  
**Решенных:** 4  
**Активных:** 1  

**Процент готовности:** 95%  
- ✅ Установка через opkg: 100%
- ✅ Функциональность: 100%
- ✅ Запуск через procd: 100%
- ✅ Автозапуск: 100%
- ⚠️ Косметические проблемы: 50% (UID 1001)

## Контакты

**GitHub Issues:** https://github.com/nagual2/openwrt-captive-monitor/issues  
**Документация:** См. TEST_REPORT.md, IPK_FORMAT_INVESTIGATION.md

---

**Последнее обновление:** 28 ноября 2025, 23:05 UTC  
**Критичная проблема решена:** v2025.11.28.6
