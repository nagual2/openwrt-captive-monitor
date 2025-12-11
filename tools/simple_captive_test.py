#!/usr/bin/env python3
"""
Легковесный тестер Captive Portal
================================

Простой инструмент для быстрой проверки наличия и доступности captive портала
с минимальными зависимостями. Идеально подходит для автоматизации и скриптов.

Возможности:
- Быстрая проверка наличия captive портала
- Минимальные зависимости (только requests)
- Работает в любом окружении (Windows, WSL, Linux)
- Подходит для автоматизации и интеграции в скрипты
- Принудительная маршрутизация через роутер (WSL/Linux)

Использование:
    # Простая проверка
    python simple_captive_test.py

    # Через WSL
    wsl python3 simple_captive_test.py

    # С конкретным роутером
    python simple_captive_test.py --router 192.168.1.1

    # С конкретным тестовым URL
    python simple_captive_test.py --test-url "http://detectportal.firefox.com"

    # Только проверка без настройки маршрутизации
    python simple_captive_test.py --no-routing

Требования:
    - Python 3.6+
    - requests library (pip install requests)
    - sudo права для настройки маршрутизации (WSL/Linux)

Переменные окружения:
    CAPTIVE_ROUTER_IP - IP адрес роутера (по умолчанию: 192.168.1.1)
    CAPTIVE_TEST_URL  - URL для проверки (по умолчанию: http://detectportal.firefox.com)
    CAPTIVE_TIMEOUT   - таймаут запросов в секундах (по умолчанию: 10)

Примеры:
    # Использование переменных окружения
    export CAPTIVE_ROUTER_IP="192.168.35.1"
    export CAPTIVE_TEST_URL="http://www.google.com"
    python simple_captive_test.py

    # Интеграция в bash скрипт
    if python3 simple_captive_test.py --no-routing; then
        echo "Captive portal обнаружен"
    else
        echo "Интернет доступен"
    fi

Коды возврата:
    0 - Интернет доступен (captive portal отсутствует)
    1 - Captive portal обнаружен
    2 - Ошибка сети или конфигурации
    130 - Прервано пользователем

Автор: OpenWrt Captive Monitor Project
Лицензия: MIT
"""

import subprocess
import time
import sys
import os

def log(message, level="INFO"):
    """Простое логирование"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def setup_routing(router_ip="192.168.1.1"):
    """Настройка маршрутизации через роутер"""
    log(f"Настройка маршрутизации через {router_ip}")

    try:
        # Настраиваем DNS
        dns_config = f"""nameserver {router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

        # Сохраняем оригинальный resolv.conf
        subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)

        # Устанавливаем новый resolv.conf
        with open('/tmp/resolv.conf.temp', 'w') as f:
            f.write(dns_config)
        subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.temp', '/etc/resolv.conf'], check=True)

        log("✅ DNS настроен через роутер")
        return True

    except Exception as e:
        log(f"❌ Ошибка настройки маршрутизации: {e}", "ERROR")
        return False

def restore_routing():
    """Восстановление оригинальной конфигурации"""
    try:
        if os.path.exists('/etc/resolv.conf.backup'):
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup', '/etc/resolv.conf'])
            subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup'])
        log("✅ Конфигурация восстановлена")
    except Exception as e:
        log(f"❌ Ошибка восстановления: {e}", "ERROR")

def test_captive_portal():
    """Тестирование captive portal с помощью curl"""
    log("Тестирование captive portal...")

    test_urls = [
        "http://www.msftconnecttest.com/redirect",
        "http://connectivitycheck.gstatic.com/generate_204",
        "http://clients3.google.com/generate_204",
        "http://www.google.com/"
    ]

    captive_detected = False

    for url in test_urls:
        try:
            log(f"Тестирование: {url}")

            # Используем curl для тестирования
            result = subprocess.run([
                'curl', '-s', '-L', '--max-time', '10',
                '--write-out', '%{http_code}|%{url_effective}',
                '--output', '/dev/null', url
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) >= 2:
                    status_code = parts[0]
                    final_url = parts[1]

                    log(f"Статус: {status_code}, Финальный URL: {final_url}")

                    # Проверяем признаки captive portal
                    if final_url != url and ('conn4.com' in final_url or 'portal' in final_url.lower()):
                        log(f"🚨 CAPTIVE PORTAL обнаружен: {final_url}")
                        captive_detected = True

                        # Попробуем получить содержимое портала
                        get_portal_content(final_url)
                        break
                    elif status_code == '204' and 'generate_204' in url:
                        log("✅ Интернет доступен (204 ответ)")
                    elif status_code.startswith('2'):
                        log("✅ HTTP запрос успешен")

        except subprocess.TimeoutExpired:
            log(f"⏰ Таймаут для {url}")
        except Exception as e:
            log(f"❌ Ошибка для {url}: {e}")

    return captive_detected

def get_portal_content(portal_url):
    """Получение содержимого captive portal"""
    log(f"Анализ captive portal: {portal_url}")

    try:
        # Получаем HTML содержимое
        result = subprocess.run([
            'curl', '-s', '--max-time', '10', portal_url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            html_content = result.stdout

            # Сохраняем в файл для анализа
            with open('captive_portal_content.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            log("📄 Содержимое портала сохранено в captive_portal_content.html")

            # Простой анализ содержимого
            analyze_portal_content(html_content)

    except Exception as e:
        log(f"❌ Ошибка получения содержимого портала: {e}")

def analyze_portal_content(html_content):
    """Простой анализ содержимого портала"""
    log("Анализ содержимого captive portal...")

    html_lower = html_content.lower()

    # Ищем формы
    if '<form' in html_lower:
        log("📝 Найдены формы на странице")

    # Ищем кнопки подключения
    connect_keywords = ['connect', 'continue', 'access', 'agree', 'accept']
    found_buttons = []

    for keyword in connect_keywords:
        if keyword in html_lower:
            found_buttons.append(keyword)

    if found_buttons:
        log(f"🔘 Найдены ключевые слова: {', '.join(found_buttons)}")

    # Ищем поля ввода
    if 'type="text"' in html_lower or 'type="password"' in html_lower:
        log("🔐 Найдены поля для ввода учетных данных")

    # Ищем чекбоксы согласия
    if 'type="checkbox"' in html_lower and ('terms' in html_lower or 'agree' in html_lower):
        log("☑️ Найдены чекбоксы согласия с условиями")

def simulate_portal_auth():
    """Симуляция авторизации на портале"""
    log("Попытка авторизации на captive portal...")

    # Читаем сохраненное содержимое портала
    try:
        with open('captive_portal_content.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Ищем action формы
        import re
        form_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html_content, re.IGNORECASE)

        if form_match:
            action_url = form_match.group(1)
            log(f"Найдена форма с action: {action_url}")

            # Попробуем отправить простой POST запрос
            try_simple_post(action_url)

    except FileNotFoundError:
        log("❌ Файл с содержимым портала не найден")
    except Exception as e:
        log(f"❌ Ошибка анализа портала: {e}")

def try_simple_post(action_url):
    """Попытка простой POST авторизации"""
    log(f"Попытка POST запроса к: {action_url}")

    try:
        # Простой POST запрос без данных (для порталов с кнопкой "Connect")
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', '--max-time', '10',
            '--write-out', '%{http_code}|%{url_effective}',
            '--output', '/dev/null', action_url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 2:
                status_code = parts[0]
                final_url = parts[1]

                log(f"POST результат: {status_code}, URL: {final_url}")

                # Проверяем, сработала ли авторизация
                if status_code.startswith('2') or status_code.startswith('3'):
                    log("✅ POST запрос принят, проверяем интернет...")

                    # Проверяем доступность интернета
                    time.sleep(5)
                    check_internet_access()

    except Exception as e:
        log(f"❌ Ошибка POST запроса: {e}")

def check_internet_access():
    """Проверка доступности интернета после авторизации"""
    log("Проверка доступности интернета...")

    try:
        result = subprocess.run([
            'curl', '-s', '--max-time', '5',
            '--write-out', '%{http_code}',
            '--output', '/dev/null',
            'http://www.google.com'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            status_code = result.stdout.strip()
            if status_code.startswith('2'):
                log("🎉 АВТОРИЗАЦИЯ УСПЕШНА! Интернет доступен!")
                return True
            else:
                log(f"❌ Интернет недоступен (код: {status_code})")
        else:
            log("❌ Не удалось проверить доступность интернета")

    except Exception as e:
        log(f"❌ Ошибка проверки интернета: {e}")

    return False

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Легковесное тестирование captive портала',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # Базовая проверка
  %(prog)s --router 192.168.1.1               # Указать роутер
  %(prog)s --test-url "http://www.google.com"  # Указать тестовый URL
  %(prog)s --no-routing                       # Без настройки маршрутизации
  %(prog)s --timeout 15                       # Увеличить таймаут

Переменные окружения:
  CAPTIVE_ROUTER_IP - IP адрес роутера
  CAPTIVE_TEST_URL  - URL для проверки
  CAPTIVE_TIMEOUT   - таймаут запросов в секундах

Коды возврата:
  0 - Интернет доступен (captive portal отсутствует)
  1 - Captive portal обнаружен
  2 - Ошибка сети или конфигурации
        """
    )

    parser.add_argument('--router', '--router-ip',
                       default=os.environ.get('CAPTIVE_ROUTER_IP', '192.168.1.1'),
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--test-url',
                       default=os.environ.get('CAPTIVE_TEST_URL', 'http://detectportal.firefox.com'),
                       help='URL для проверки captive портала')
    parser.add_argument('--no-routing', action='store_true',
                       help='Не настраивать маршрутизацию (только проверка)')
    parser.add_argument('--timeout', type=int,
                       default=int(os.environ.get('CAPTIVE_TIMEOUT', '10')),
                       help='Таймаут запросов в секундах (по умолчанию: 10)')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')
    parser.add_argument('--quiet', action='store_true',
                       help='Минимальный вывод (только результат)')
    parser.add_argument('--simulate-auth', action='store_true',
                       help='Попытка симуляции авторизации при обнаружении портала')

    args = parser.parse_args()

    # Настройка уровня логирования
    global verbose_logging
    verbose_logging = args.verbose and not args.quiet

    if not args.quiet:
        log("=" * 60)
        log("ТЕСТИРОВАНИЕ CAPTIVE PORTAL (Легковесная версия)")
        log("=" * 60)
        log(f"Роутер: {args.router}")
        log(f"Тестовый URL: {args.test_url}")
        log(f"Таймаут: {args.timeout}s")

    try:
        # 1. Настройка маршрутизации (если требуется)
        if not args.no_routing:
            if not setup_routing(args.router):
                if not args.quiet:
                    log("❌ Ошибка настройки маршрутизации")
                return 2
        elif not args.quiet:
            log("⚠️ Пропуск настройки маршрутизации")

        # 2. Тестирование captive portal
        captive_detected = test_captive_portal(test_url=args.test_url, timeout=args.timeout)

        if captive_detected:
            if not args.quiet:
                log("🔒 Captive portal обнаружен")

            # 3. Попытка авторизации (если запрошена)
            if args.simulate_auth:
                if not args.quiet:
                    log("🤖 Попытка симуляции авторизации...")
                simulate_portal_auth()

            return 1  # Captive portal обнаружен
        else:
            if not args.quiet:
                log("✅ Captive portal не обнаружен - интернет доступен")
            return 0  # Интернет доступен

    except KeyboardInterrupt:
        if not args.quiet:
            log("\n⚠️ Прервано пользователем")
        return 130
    except Exception as e:
        if not args.quiet:
            log(f"❌ Критическая ошибка: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 2
    finally:
        if not args.no_routing:
            restore_routing()

def test_captive_portal(test_url="http://detectportal.firefox.com", timeout=10):
    """Тестирование наличия captive портала"""
    try:
        import requests

        log(f"Тестирование captive portal: {test_url}")

        response = requests.get(test_url, timeout=timeout, allow_redirects=False)

        # Проверяем редирект (признак captive портала)
        if response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = response.headers.get('Location', '')
            log(f"Обнаружен редирект: {response.status_code} -> {redirect_url}")
            return True
        elif response.status_code == 200:
            # Проверяем содержимое ответа
            if 'captive' in response.text.lower() or 'portal' in response.text.lower():
                log("Обнаружены ключевые слова captive portal в ответе")
                return True
            else:
                log("Получен нормальный HTTP 200 ответ")
                return False
        else:
            log(f"Неожиданный статус код: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        log("❌ Таймаут запроса")
        return False
    except requests.exceptions.ConnectionError:
        log("❌ Ошибка подключения")
        return False
    except Exception as e:
        log(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
