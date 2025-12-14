# Консолидированный авторизатор captive порталов для WSL

## Обзор

`captive_portal_wsl_selenium.py` - единый скрипт на Selenium для автоматической авторизации на captive порталах через WSL с принудительной маршрутизацией через роутер 192.168.1.1.

## Возможности

- ✅ Принудительная маршрутизация через роутер 192.168.1.1
- ✅ Автоматическое обнаружение captive порталов
- ✅ Поддержка различных типов авторизации:
  - Простое подключение (кнопка Connect/Continue)
  - Авторизация по учетным данным (username/password)
  - Принятие условий использования (чекбоксы)
  - Специфичная обработка известных порталов (phc.prontonetworks.com, conn4.com)
- ✅ Работа с Chrome в headless режиме
- ✅ Автоматическое восстановление сетевых настроек
- ✅ Отладочные скриншоты и логирование

## Требования

### Системные требования
- WSL 2
- Google Chrome в WSL
- sudo права для настройки сети

### Python зависимости
```bash
pip3 install selenium webdriver-manager
```

### Установка Chrome в WSL
```bash
# Обновление пакетов
sudo apt update

# Установка Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable
```

### Настройка sudo без пароля
```bash
# Запустить скрипт настройки
wsl bash tools/setup_wsl_sudo.sh

# Или настроить вручную
sudo visudo
# Добавить строку:
# username ALL=(ALL) NOPASSWD: /sbin/ip, /bin/cp, /usr/bin/tee
```

## Использование

### Базовые команды

```bash
# Базовый запуск (headless режим)
wsl python3 tools/captive_portal_wsl_selenium.py

# С отображением браузера для отладки
wsl python3 tools/captive_portal_wsl_selenium.py --show-browser

# С учетными данными
wsl python3 tools/captive_portal_wsl_selenium.py --username "12345" --password "secret"

# Отладочный режим с подробными логами
wsl python3 tools/captive_portal_wsl_selenium.py --debug --verbose
```

### Параметры командной строки

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--router-ip` | IP адрес роутера | 192.168.1.1 |
| `--timeout` | Таймаут операций (сек) | 30 |
| `--username` | Имя пользователя | - |
| `--password` | Пароль | - |
| `--show-browser` | Показать браузер | false (headless) |
| `--debug` | Отладочный режим | false |
| `--verbose` | Подробный вывод | false |

## Принцип работы

### 1. Настройка принудительной маршрутизации
- Изменяет `/etc/resolv.conf` для использования DNS роутера
- Добавляет маршруты для тестовых хостов через роутер
- Все сетевые запросы идут только через 192.168.1.1

### 2. Обнаружение captive portal
Тестирует URL-адреса:
- `http://www.msftconnecttest.com/redirect`
- `http://connectivitycheck.gstatic.com/generate_204`
- `http://clients3.google.com/generate_204`
- `http://detectportal.firefox.com/canonical.html`
- `http://www.google.com/`

### 3. Авторизация
Пробует методы в порядке приоритета:
1. **Простое подключение** - поиск кнопок Connect/Continue/Access
2. **Учетные данные** - заполнение форм username/password (если предоставлены)
3. **Принятие условий** - отметка чекбоксов и нажатие Accept/Agree
4. **Известные порталы** - специфичная обработка для phc.prontonetworks.com и conn4.com

### 4. Проверка успеха
- Попытка доступа к google.com
- Проверка connectivity check endpoints
- Анализ содержимого страниц на признаки успеха

### 5. Восстановление настроек
- Восстановление оригинального `/etc/resolv.conf`
- Удаление добавленных маршрутов
- Закрытие Chrome WebDriver

## Поддерживаемые порталы

### Автоматически обнаруживаемые домены
- `conn4.com`, `rdr.conn4.com`
- `phc.prontonetworks.com`
- `captive.apple.com`
- `connectivitycheck.android.com`
- Любые домены содержащие: portal, hotspot, wifi, guest, auth

### Специфичная обработка
- **phc.prontonetworks.com** - поиск кнопок Agree/Accept/Connect
- **conn4.com** - простое нажатие Connect/Continue

## Отладка

### Логи
Скрипт выводит подробные логи с временными метками:
```
[12:34:56] INFO: Настройка принудительной маршрутизации через 192.168.1.1
[12:34:57] INFO: ✅ Маршрут добавлен: www.google.com (142.250.185.4) via 192.168.1.1
[12:34:58] INFO: Тестирование URL: http://connectivitycheck.gstatic.com/generate_204
[12:35:03] INFO: 🚨 Captive portal обнаружен: http://phc.prontonetworks.com/...
```

### Скриншоты
При отладке создаются скриншоты:
- `captive_portal_page.png` - страница портала
- `auth_success_final.png` - успешная авторизация
- `auth_failed_final.png` - неудачная авторизация
- `auth_failed_analysis.png` - анализ при ошибке

### Отладочная информация
В режиме `--debug` выводится:
- Найденные кнопки и ссылки
- Формы на странице
- URL и заголовки страниц
- Детали ошибок

## Устранение неполадок

### Chrome не найден
```bash
# Установить Chrome
sudo apt update
sudo apt install google-chrome-stable

# Проверить установку
which google-chrome
```

### Нет прав sudo
```bash
# Настроить sudo без пароля
sudo visudo
# Добавить: username ALL=(ALL) NOPASSWD: /sbin/ip, /bin/cp, /usr/bin/tee
```

### Selenium ошибки
```bash
# Переустановить зависимости
pip3 uninstall selenium webdriver-manager
pip3 install selenium webdriver-manager

# Очистить кэш webdriver-manager
rm -rf ~/.wdm
```

### Проблемы с сетью
```bash
# Проверить доступность роутера
ping 192.168.1.1

# Проверить DNS
nslookup google.com 192.168.1.1

# Восстановить сеть вручную (если скрипт завис)
sudo cp /etc/resolv.conf.backup /etc/resolv.conf 2>/dev/null || true
```

## Интеграция с другими скриптами

### Использование в bash скриптах
```bash
#!/bin/bash
# Запуск авторизации
if wsl python3 tools/captive_portal_wsl_selenium.py --username "$USER" --password "$PASS"; then
    echo "✅ Авторизация успешна"
else
    echo "❌ Авторизация не удалась"
    exit 1
fi
```

### Использование с переменными окружения
```bash
export CAPTIVE_USERNAME="12345"
export CAPTIVE_PASSWORD="secret"
wsl python3 tools/captive_portal_wsl_selenium.py --username "$CAPTIVE_USERNAME" --password "$CAPTIVE_PASSWORD"
```

## Безопасность

- ✅ Скрипт работает только в WSL (проверка при запуске)
- ✅ Автоматическое восстановление сетевых настроек
- ✅ Минимальные права sudo (только для ip, cp, tee)
- ✅ Headless режим по умолчанию (без GUI)
- ⚠️ Учетные данные передаются через аргументы командной строки (видны в ps)

## Ограничения

- Работает только в WSL 2
- Требует установки Chrome в WSL
- Требует sudo права для настройки сети
- Не поддерживает сложные JavaScript-based порталы
- Учетные данные видны в процессах (используйте переменные окружения)
