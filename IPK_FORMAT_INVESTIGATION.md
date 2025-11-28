# Исследование проблемы "Malformed package file"

**Дата:** 28 ноября 2025  
**Проблема:** opkg install выдает ошибку "Malformed package file"  
**Статус:** ✅ РЕШЕНО

## Краткое резюме

OpenWrt 23.05+ использует **tar.gz формат** для .ipk пакетов, а не **ar формат** (Debian binary package format 2.0).

Наши скрипты создавали пакеты в ar формате, что приводило к ошибке при установке через opkg.

## Детальное исследование

### 1. Симптомы

```bash
root@OpenWrt:~# opkg install /tmp/openwrt-captive-monitor_2025.11.28.2-1_all.ipk
Collected errors:
 * pkg_init_from_file: Malformed package file /tmp/openwrt-captive-monitor_2025.11.28.2-1_all.ipk.
```

### 2. Анализ формата пакетов

**Наш пакет (неправильный):**
```bash
$ file openwrt-captive-monitor_2025.11.28.2-1_all.ipk
openwrt-captive-monitor_2025.11.28.2-1_all.ipk: Debian binary package (format 2.0), with control.tar.gz, data compression gz

$ ar t openwrt-captive-monitor_2025.11.28.2-1_all.ipk
debian-binary
control.tar.gz
data.tar.gz
```

**Официальный пакет OpenWrt (правильный):**
```bash
$ file curl_8.7.1-r1_x86_64.ipk
curl_8.7.1-r1_x86_64.ipk: gzip compressed data, from Unix, original size modulo 2^32 71680

$ tar -tzf curl_8.7.1-r1_x86_64.ipk
./debian-binary
./data.tar.gz
./control.tar.gz
```

### 3. Ключевое различие

| Формат | Наш пакет (старый) | Официальный OpenWrt |
|--------|---------------------|---------------------|
| Тип архива | **ar** (Debian format) | **tar.gz** |
| Команда создания | `ar r package.ipk debian-binary control.tar.gz data.tar.gz` | `tar czf package.ipk ./debian-binary ./data.tar.gz ./control.tar.gz` |
| Распознавание file | "Debian binary package" | "gzip compressed data" |
| Работает в opkg | ❌ Malformed package | ✅ Работает |

### 4. История форматов IPK

**Старый формат (до OpenWrt 21.x):**
- Использовал ar архив (как Debian .deb пакеты)
- Формат: `ar r package.ipk debian-binary control.tar.gz data.tar.gz`

**Новый формат (OpenWrt 22.x+):**
- Использует tar.gz архив
- Формат: `tar czf package.ipk ./debian-binary ./data.tar.gz ./control.tar.gz`
- Причина изменения: упрощение, меньше зависимостей (не нужен ar)

### 5. Почему ar не работает

OpenWrt 23.05.3 использует opkg версии `d038e5b6d155784575f62a66a8bb7e874173e92e (2022-02-24)`, которая ожидает tar.gz формат.

При попытке прочитать ar архив, opkg не может распарсить его структуру и выдает "Malformed package file".

## Решение

### Изменения в scripts/build_ipk_simple.sh

**Было:**
```bash
# Create final .ipk (which is an ar archive)
output_ipk="$output_dir/${pkg_name}_${full_version}_${pkg_arch}.ipk"
(cd "$build_dir" && ar r "$output_ipk" debian-binary control.tar.gz data.tar.gz)
```

**Стало:**
```bash
# Create final .ipk (which is a tar.gz archive containing debian-binary, data.tar.gz, control.tar.gz)
# OpenWrt 23.05+ uses tar.gz format instead of ar format
output_ipk="$output_dir/${pkg_name}_${full_version}_${pkg_arch}.ipk"
(cd "$build_dir" && tar czf "$output_ipk" ./debian-binary ./data.tar.gz ./control.tar.gz)
```

### Изменения в .github/workflows/tag-build-release.yml

1. **Исправлен дублирующийся `fi`** в шаге "Validate IPK version metadata"
2. **Исправлен glob pattern** в sha256sum: `./*.ipk` → `*.ipk`

## Тестирование

### Тест 1: Формат пакета

```bash
$ file dist/opkg/all/openwrt-captive-monitor_2025.11.28.3-1_all.ipk
dist/opkg/all/openwrt-captive-monitor_2025.11.28.3-1_all.ipk: gzip compressed data, from Unix, original size modulo 2^32 20480

$ tar -tzf dist/opkg/all/openwrt-captive-monitor_2025.11.28.3-1_all.ipk
./debian-binary
./data.tar.gz
./control.tar.gz
```

✅ Формат правильный - tar.gz

### Тест 2: Установка через opkg

```bash
root@OpenWrt:~# opkg install /tmp/test-new.ipk
Installing openwrt-captive-monitor (2025.11.28.3-1) to root...
Configuring openwrt-captive-monitor.
```

✅ Установка успешна!

### Тест 3: Проверка установленных файлов

```bash
root@OpenWrt:~# opkg list-installed | grep captive
openwrt-captive-monitor - 2025.11.28.3-1

root@OpenWrt:~# ls -la /usr/sbin/openwrt_captive_monitor /etc/init.d/captive-monitor /etc/config/captive-monitor
-rwxrwxrwx    1 1000     1000           532 Nov 28 13:43 /etc/config/captive-monitor
-rwxr-xr-x    1 1000     1000          3239 Nov 28 13:44 /etc/init.d/captive-monitor
-rwxr-xr-x    1 1000     1000         47906 Nov 28 19:35 /usr/sbin/openwrt_captive_monitor
```

✅ Все файлы установлены

### Тест 4: Удаление через opkg

```bash
root@OpenWrt:~# opkg remove openwrt-captive-monitor
Removing package openwrt-captive-monitor from root...
Not deleting modified conffile /etc/config/captive-monitor.

root@OpenWrt:~# ls -la /usr/sbin/openwrt_captive_monitor /etc/init.d/captive-monitor
ls: /usr/sbin/openwrt_captive_monitor: No such file or directory
ls: /etc/init.d/captive-monitor: No such file or directory
```

✅ Удаление успешно (конфиг сохранен, как и должно быть)

## Совместимость

### Поддерживаемые версии OpenWrt

| Версия | Формат IPK | Статус |
|--------|------------|--------|
| 19.07 и старше | ar | ⚠️ Не поддерживается новым форматом |
| 21.02 | ar → tar.gz (переходный) | ⚠️ Требует тестирования |
| 22.03 | tar.gz | ✅ Поддерживается |
| 23.05 | tar.gz | ✅ Протестировано |
| 24.10 | tar.gz | ✅ Должно работать |

### Обратная совместимость

Пакеты в tar.gz формате **не будут работать** на OpenWrt 19.07 и старше.

Если требуется поддержка старых версий, нужно:
1. Определять версию OpenWrt
2. Создавать пакеты в соответствующем формате
3. Или предоставлять два варианта пакетов

## Дополнительные находки

### Проблема с enable

Init скрипт не создает симлинки при выполнении `enable`:

```bash
root@OpenWrt:~# /etc/init.d/captive-monitor enable
root@OpenWrt:~# ls -la /etc/rc.d/*captive*
ls: /etc/rc.d/*captive*: No such file or directory
```

**Причина:** Неизвестна, требует дополнительного исследования.

**Обходное решение:** Создавать симлинки в postinst скрипте:
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

## Выводы

1. ✅ **Проблема решена** - пакеты теперь устанавливаются через opkg
2. ✅ **Формат правильный** - tar.gz вместо ar
3. ✅ **Протестировано** - на реальном OpenWrt 23.05.3 устройстве
4. ⚠️ **Требует доработки** - автоматическое создание симлинков при enable
5. ⚠️ **Требует тестирования** - на других версиях OpenWrt (21.02, 22.03, 24.10)

## Рекомендации

### Для разработчиков

1. Всегда используйте tar.gz формат для OpenWrt 22.03+
2. Тестируйте пакеты на реальных устройствах, а не только в SDK
3. Проверяйте формат пакета через `file` команду перед публикацией

### Для CI/CD

1. Добавить проверку формата пакета в валидационные скрипты
2. Добавить smoke test установки на реальном устройстве (если возможно)
3. Документировать поддерживаемые версии OpenWrt

### Для документации

1. Обновить README с информацией о поддерживаемых версиях
2. Добавить troubleshooting секцию для проблем с установкой
3. Документировать формат пакетов и причины выбора

## Ссылки

- [OpenWrt opkg documentation](https://openwrt.org/docs/guide-user/additional-software/opkg)
- [IPK package format](https://openwrt.org/docs/guide-developer/packages)
- [opkg source code](https://git.openwrt.org/project/opkg-lede.git)
