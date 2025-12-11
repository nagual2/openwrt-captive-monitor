# Инструменты автоматизации Captive Portal

Этот набор инструментов предназначен для автоматического обнаружения, анализа и авторизации на captive порталах в сетях OpenWrt.

## Обзор инструментов

### 🔍 Анализаторы порталов

#### `captive_portal_selenium_analyzer.py`
**Назначение:** Комплексный анализ captive порталов с использованием Selenium WebDriver

**Возможности:**
- Автоматическое обнаружение форм авторизации
- Извлечение всех полей форм и их атрибутов
- Анализ JavaScript логики портала
- Генерация конфигурации для автоматизации
- Поддержка headless режима для серверного использования

**Использование:**
```bash
# Windows (нативно)
python tools/captive_portal_selenium_analyzer.py

# WSL
wsl python3 tools/captive_portal_selenium_analyzer.py

# С параметрами
python tools/captive_portal_selenium_analyzer.py --url "http://192.168.1.1" --headless
```

**Зависимости:**
- selenium
- webdriver-manager
- Firefox browser (для Windows) или firefox-esr (для Linux)

#### `captive_portal_test_enhanced.py`
**Назначение:** Детальный анализ HTML структуры captive порталов без браузера

**Возможности:**
- Быстрый анализ HTML содержимого
- Извлечение параметров форм
- Определение методов отправки данных
- Минимальные системные требования

**Использование:**
```bash
python tools/captive_portal_test_enhanced.py --target 192.168.1.1
```

### 🤖 Автоматизаторы авторизации

#### `captive_portal_final_auth.py`
**Назначение:** Автоматическая авторизация с эмуляцией JavaScript логики

**Возможности:**
- Эмуляция JavaScript кода без браузера
- Автоматическое заполнение форм авторизации
- Поддержка сложных порталов (conn4.com и аналогичных)
- Проверка успешности авторизации

**Использование:**
```bash
# Базовое использование
python tools/captive_portal_final_auth.py

# С параметрами
python tools/captive_portal_final_auth.py --portal-url "http://192.168.1.1" --room "12345" --password "secret"

# Через WSL
wsl python3 tools/captive_portal_final_auth.py --room "12345" --password "secret"
```

**Поддерживаемые порталы:**
- conn4.com (JavaScript-based)
- Простые формы логин/пароль
- Порталы с дополнительными полями

### 🧪 Тестовые инструменты

#### `test_captive_portal.py`
**Назначение:** Комплексное тестирование с принудительной маршрутизацией через роутер

**Возможности:**
- Принудительная маршрутизация трафика через OpenWrt роутер
- Полная эмуляция клиентского окружения
- Детальная диагностика сетевого взаимодействия
- Проверка работы captive portal detection

**Использование:**
```bash
# Тестирование через конкретный роутер
python tools/test_captive_portal.py --router 192.168.1.1 --interface "Wi-Fi"

# С принудительной маршрутизацией
python tools/test_captive_portal.py --force-route --router 192.168.1.1
```

**Требования:**
- Административные права (для изменения маршрутизации)
- Активное подключение к тестируемой сети

#### `simple_captive_test.py`
**Назначение:** Легковесное тестирование доступности captive портала

**Возможности:**
- Быстрая проверка наличия captive портала
- Минимальные зависимости (только requests)
- Подходит для автоматизации и скриптов
- Работает в любом окружении

**Использование:**
```bash
# Простая проверка
python tools/simple_captive_test.py

# Через WSL
wsl python3 tools/simple_captive_test.py

# С конкретным URL
python tools/simple_captive_test.py --test-url "http://detectportal.firefox.com"
```

## Установка зависимостей

### Windows

```powershell
# Установка Python пакетов
pip install selenium webdriver-manager requests beautifulsoup4

# Установка Firefox (если не установлен)
# Скачать с https://www.mozilla.org/firefox/
```

### WSL/Linux

```bash
# Установка системных пакетов
sudo apt update
sudo apt install python3-pip firefox-esr

# Установка Python пакетов
pip3 install selenium webdriver-manager requests beautifulsoup4

# Для headless режима
export DISPLAY=:0  # если нужен GUI
# или используйте --headless флаг
```

## Типичные сценарии использования

### Сценарий 1: Анализ нового captive портала

```bash
# 1. Первичный анализ структуры
python tools/captive_portal_test_enhanced.py --target 192.168.1.1

# 2. Детальный анализ с Selenium
python tools/captive_portal_selenium_analyzer.py --url "http://192.168.1.1" --headless

# 3. Тестирование авторизации
python tools/captive_portal_final_auth.py --portal-url "http://192.168.1.1" --room "test" --password "test"
```

### Сценарий 2: Отладка проблем с авторизацией

```bash
# 1. Проверка доступности портала
python tools/simple_captive_test.py

# 2. Комплексная диагностика
python tools/test_captive_portal.py --router 192.168.1.1 --verbose

# 3. Анализ JavaScript логики
python tools/captive_portal_selenium_analyzer.py --url "http://192.168.1.1" --debug
```

### Сценарий 3: Автоматизация в production

```bash
# В скрипте openwrt-captive-monitor
if detect_captive_portal; then
    # Определить тип портала
    portal_type=$(python3 /usr/sbin/captive_portal_analyzer.py --detect-type)

    # Выполнить авторизацию
    if [ "$portal_type" = "conn4.com" ]; then
        python3 /usr/sbin/captive_portal_final_auth.py \
            --room "$ROOM_NUMBER" \
            --password "$ACCESS_CODE"
    fi
fi
```

## Конфигурация

### Переменные окружения

```bash
# Настройки WebDriver
export WEBDRIVER_HEADLESS=true
export WEBDRIVER_TIMEOUT=30

# Настройки авторизации
export CAPTIVE_ROOM_NUMBER="12345"
export CAPTIVE_ACCESS_CODE="password"
export CAPTIVE_PORTAL_URL="http://192.168.1.1"

# Настройки логирования
export CAPTIVE_LOG_LEVEL="INFO"
export CAPTIVE_LOG_FILE="/var/log/captive-auth.log"
```

### Конфигурационные файлы

Создайте файл `captive_config.json`:

```json
{
  "portal_configs": {
    "conn4.com": {
      "auth_method": "javascript_emulation",
      "form_selector": "form[name='loginForm']",
      "username_field": "username",
      "password_field": "password",
      "submit_function": "submitLogin",
      "success_url_pattern": "success|welcome"
    },
    "simple_form": {
      "auth_method": "direct_post",
      "form_action": "/login",
      "username_field": "user",
      "password_field": "pass"
    }
  },
  "timeouts": {
    "page_load": 30,
    "element_wait": 10,
    "auth_check": 5
  }
}
```

## Troubleshooting

### Проблема: WebDriver не запускается

**Симптомы:** `selenium.common.exceptions.WebDriverException`

**Решение:**
```bash
# Обновить webdriver-manager
pip install --upgrade webdriver-manager

# Проверить установку Firefox
firefox --version  # Windows
firefox-esr --version  # Linux

# Использовать headless режим
python tools/captive_portal_selenium_analyzer.py --headless
```

### Проблема: Авторизация не проходит

**Симптомы:** Скрипт завершается без ошибок, но интернет недоступен

**Диагностика:**
```bash
# Проверить доступность портала
curl -I http://192.168.1.1

# Проверить форму авторизации
python tools/captive_portal_test_enhanced.py --target 192.168.1.1

# Включить детальное логирование
python tools/captive_portal_final_auth.py --debug --verbose
```

### Проблема: Скрипт зависает

**Симптомы:** Скрипт не завершается, нет вывода

**Решение:**
```bash
# Уменьшить таймауты
export WEBDRIVER_TIMEOUT=10

# Использовать простой тестер
python tools/simple_captive_test.py

# Проверить сетевое подключение
ping 8.8.8.8
```

## Интеграция с OpenWrt

### Установка на роутер

```bash
# Скопировать скрипты на роутер
scp tools/captive_portal_final_auth.py root@192.168.1.1:/usr/sbin/
scp tools/simple_captive_test.py root@192.168.1.1:/usr/sbin/

# Установить зависимости (если доступны)
ssh root@192.168.1.1 "opkg update && opkg install python3 python3-pip"
ssh root@192.168.1.1 "pip3 install requests"
```

### UCI конфигурация

```bash
# Настроить параметры авторизации
uci set captive-monitor.@auth[0]=auth
uci set captive-monitor.@auth[0].enabled='1'
uci set captive-monitor.@auth[0].portal_type='conn4.com'
uci set captive-monitor.@auth[0].room_number='12345'
uci set captive-monitor.@auth[0].access_code='password'
uci commit captive-monitor
```

## Разработка и расширение

### Добавление нового типа портала

1. Создайте конфигурацию в `captive_config.json`
2. Добавьте обработчик в `captive_portal_final_auth.py`
3. Протестируйте с помощью анализаторов
4. Обновите документацию

### Создание custom авторизатора

```python
from captive_portal_final_auth import CaptivePortalAuth

class CustomPortalAuth(CaptivePortalAuth):
    def authenticate(self, credentials):
        # Ваша логика авторизации
        pass

    def verify_success(self):
        # Проверка успешности
        pass
```

## Поддержка и обратная связь

При возникновении проблем:

1. Проверьте логи: `tail -f /var/log/captive-auth.log`
2. Запустите диагностику: `python tools/simple_captive_test.py --debug`
3. Создайте issue в GitHub репозитории с детальным описанием проблемы
4. Приложите логи и конфигурацию (без паролей!)

## Лицензия

Все инструменты распространяются под той же лицензией, что и основной проект openwrt-captive-monitor.
