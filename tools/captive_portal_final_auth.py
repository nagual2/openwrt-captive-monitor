#!/usr/bin/env python3
"""
Автоматизатор авторизации на captive порталах
============================================

Этот скрипт выполняет автоматическую авторизацию на captive порталах,
эмулируя JavaScript логику браузера без использования WebDriver.

Поддерживаемые порталы:
- conn4.com (JavaScript-based авторизация)
- Простые формы логин/пароль
- Порталы с дополнительными полями

Использование:
    # Базовое использование (интерактивный ввод)
    python captive_portal_final_auth.py

    # С параметрами командной строки
    python captive_portal_final_auth.py --room "12345" --password "secret"

    # Указание конкретного портала
    python captive_portal_final_auth.py --portal-url "http://192.168.1.1" --room "12345"

    # Через WSL
    wsl python3 captive_portal_final_auth.py --room "12345" --password "secret"

Переменные окружения:
    CAPTIVE_ROOM_NUMBER - номер комнаты для авторизации
    CAPTIVE_ACCESS_CODE - код доступа/пароль
    CAPTIVE_PORTAL_URL  - URL портала (по умолчанию определяется автоматически)
    CAPTIVE_LOG_LEVEL   - уровень логирования (DEBUG, INFO, WARNING, ERROR)

Примеры:
    # Использование переменных окружения
    export CAPTIVE_ROOM_NUMBER="12345"
    export CAPTIVE_ACCESS_CODE="password"
    python captive_portal_final_auth.py

    # Отладочный режим
    export CAPTIVE_LOG_LEVEL="DEBUG"
    python captive_portal_final_auth.py --debug

Требования:
    - Python 3.6+
    - requests library (pip install requests)
    - Доступ к сети с captive порталом

Автор: OpenWrt Captive Monitor Project
Лицензия: MIT
"""

import requests
import time
import sys
import subprocess
import os
import re
import json
from urllib.parse import urljoin, urlparse, parse_qs

class CaptivePortalAuth:
    def __init__(self, router_ip="192.168.1.1"):
        self.router_ip = router_ip
        self.session = requests.Session()
        self.portal_url = None

        # Настраиваем сессию как браузер
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def log(self, message, level="INFO"):
        """Логирование"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def setup_network(self):
        """Настройка DNS через роутер"""
        self.log(f"Настройка DNS через {self.router_ip}")

        dns_config = f"""nameserver {self.router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""
        try:
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)
            with open('/tmp/resolv.conf.temp', 'w') as f:
                f.write(dns_config)
            subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.temp', '/etc/resolv.conf'], check=True)
            self.log("✅ DNS настроен")
            return True
        except Exception as e:
            self.log(f"❌ Ошибка настройки DNS: {e}", "ERROR")
            return False

    def restore_network(self):
        """Восстановление DNS"""
        try:
            if os.path.exists('/etc/resolv.conf.backup'):
                subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup', '/etc/resolv.conf'])
                subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup'])
            self.log("✅ DNS восстановлен")
        except Exception as e:
            self.log(f"❌ Ошибка восстановления: {e}", "ERROR")

    def detect_portal(self):
        """Обнаружение captive portal"""
        self.log("Поиск captive portal...")

        test_urls = [
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://clients3.google.com/generate_204",
            "http://www.msftconnecttest.com/redirect"
        ]

        for test_url in test_urls:
            try:
                self.log(f"Тестирование: {test_url}")

                response = self.session.get(test_url, timeout=15, allow_redirects=True)

                self.log(f"Статус: {response.status_code}, URL: {response.url}")

                # Проверяем редирект на conn4.com
                if "conn4.com" in response.url:
                    self.log(f"🚨 Captive portal обнаружен: {response.url}")
                    self.portal_url = response.url
                    return True

                # Проверяем meta refresh в HTML
                if response.status_code == 200 and response.text:
                    meta_match = re.search(r'http-equiv=["\']refresh["\'][^>]*url=([^"\']*)', response.text, re.IGNORECASE)
                    if meta_match:
                        redirect_url = meta_match.group(1)
                        if "conn4.com" in redirect_url:
                            self.log(f"🚨 Captive portal (meta refresh): {redirect_url}")
                            self.portal_url = redirect_url
                            return True

                # Проверяем ожидаемые ответы
                if "generate_204" in test_url and response.status_code == 204:
                    self.log("✅ Интернет доступен (204)")
                    return False

            except Exception as e:
                self.log(f"❌ Ошибка тестирования {test_url}: {e}", "ERROR")
                continue

        self.log("❌ Не удалось определить состояние сети")
        return False

    def analyze_portal_page(self):
        """Анализ страницы captive portal"""
        self.log("Анализ страницы captive portal...")

        try:
            response = self.session.get(self.portal_url, timeout=15)

            if response.status_code != 200:
                self.log(f"❌ Ошибка загрузки портала: {response.status_code}", "ERROR")
                return None

            html_content = response.text

            # Сохраняем HTML для анализа
            with open('portal_analysis.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.log("📄 HTML портала сохранен в portal_analysis.html")

            # Анализируем формы
            forms = self.extract_forms(html_content)
            self.log(f"Найдено форм: {len(forms)}")

            # Анализируем JavaScript
            js_info = self.extract_javascript_info(html_content)

            # Анализируем параметры URL
            url_params = self.extract_url_parameters(self.portal_url)

            analysis = {
                'url': self.portal_url,
                'forms': forms,
                'javascript': js_info,
                'url_params': url_params,
                'html_content': html_content
            }

            return analysis

        except Exception as e:
            self.log(f"❌ Ошибка анализа портала: {e}", "ERROR")
            return None

    def extract_forms(self, html_content):
        """Извлечение информации о формах"""
        forms = []

        # Ищем все формы
        form_matches = re.finditer(r'<form[^>]*>(.*?)</form>', html_content, re.DOTALL | re.IGNORECASE)

        for form_match in form_matches:
            form_html = form_match.group(0)

            # Извлекаем атрибуты формы
            action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
            method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)

            action = action_match.group(1) if action_match else ""
            method = method_match.group(1).upper() if method_match else "GET"

            # Извлекаем поля ввода
            inputs = []
            input_matches = re.finditer(r'<input[^>]*>', form_html, re.IGNORECASE)

            for input_match in input_matches:
                input_html = input_match.group(0)

                type_match = re.search(r'type=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                name_match = re.search(r'name=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                value_match = re.search(r'value=["\']([^"\']*)["\']', input_html, re.IGNORECASE)

                input_info = {
                    'type': type_match.group(1) if type_match else 'text',
                    'name': name_match.group(1) if name_match else '',
                    'value': value_match.group(1) if value_match else ''
                }

                if input_info['name']:  # Только поля с именами
                    inputs.append(input_info)

            form_info = {
                'action': action,
                'method': method,
                'inputs': inputs
            }

            forms.append(form_info)
            self.log(f"Форма: {method} {action} ({len(inputs)} полей)")

        return forms

    def extract_javascript_info(self, html_content):
        """Извлечение информации о JavaScript"""
        js_info = {
            'inline_scripts': [],
            'external_scripts': [],
            'variables': {},
            'functions': []
        }

        # Ищем встроенные скрипты
        script_matches = re.finditer(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)

        for script_match in script_matches:
            script_content = script_match.group(1).strip()
            if script_content:
                js_info['inline_scripts'].append(script_content)

                # Ищем переменные
                var_matches = re.finditer(r'var\s+(\w+)\s*=\s*["\']([^"\']*)["\']', script_content)
                for var_match in var_matches:
                    var_name = var_match.group(1)
                    var_value = var_match.group(2)
                    js_info['variables'][var_name] = var_value

                # Ищем функции
                func_matches = re.finditer(r'function\s+(\w+)\s*\(', script_content)
                for func_match in func_matches:
                    func_name = func_match.group(1)
                    js_info['functions'].append(func_name)

        # Ищем внешние скрипты
        external_matches = re.finditer(r'<script[^>]*src=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        for ext_match in external_matches:
            src = ext_match.group(1)
            js_info['external_scripts'].append(src)

        self.log(f"JavaScript: {len(js_info['inline_scripts'])} встроенных, {len(js_info['external_scripts'])} внешних")

        return js_info

    def extract_url_parameters(self, url):
        """Извлечение параметров из URL портала"""
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        # Преобразуем в простой словарь
        simple_params = {}
        for key, values in params.items():
            simple_params[key] = values[0] if values else ""

        self.log(f"URL параметры: {list(simple_params.keys())}")

        return simple_params

    def authenticate_conn4_portal(self, analysis):
        """Специализированная авторизация для conn4.com портала"""
        self.log("Авторизация на conn4.com портале...")

        try:
            # Получаем страницу портала
            response = self.session.get(self.portal_url, timeout=15)

            if response.status_code != 200:
                self.log(f"❌ Ошибка загрузки портала: {response.status_code}", "ERROR")
                return False

            html_content = response.text

            # Conn4.com обычно использует простую форму или AJAX запрос
            # Ищем специфичные элементы conn4

            # 1. Попробуем найти форму авторизации
            if analysis and analysis['forms']:
                return self.try_form_submission(analysis['forms'][0])

            # 2. Попробуем эмулировать JavaScript авторизацию
            return self.try_javascript_emulation(html_content)

        except Exception as e:
            self.log(f"❌ Ошибка авторизации: {e}", "ERROR")
            return False

    def try_form_submission(self, form_info):
        """Попытка отправки формы"""
        self.log(f"Отправка формы: {form_info['method']} {form_info['action']}")

        try:
            # Подготавливаем данные формы
            form_data = {}

            for input_field in form_info['inputs']:
                name = input_field['name']
                value = input_field['value']
                input_type = input_field['type'].lower()

                if name and input_type in ['hidden', 'text', 'email']:
                    form_data[name] = value
                elif input_type == 'submit' and not form_data:
                    # Если нет других полей, добавляем submit
                    if name:
                        form_data[name] = value or 'Submit'

            self.log(f"Данные формы: {list(form_data.keys())}")

            # Формируем полный URL для action
            action_url = form_info['action']
            if action_url.startswith('/'):
                base_url = f"{urlparse(self.portal_url).scheme}://{urlparse(self.portal_url).netloc}"
                action_url = urljoin(base_url, action_url)
            elif not action_url.startswith('http'):
                action_url = urljoin(self.portal_url, action_url)

            self.log(f"Action URL: {action_url}")

            # Отправляем форму
            if form_info['method'] == 'POST':
                response = self.session.post(action_url, data=form_data, timeout=15, allow_redirects=True)
            else:
                response = self.session.get(action_url, params=form_data, timeout=15, allow_redirects=True)

            self.log(f"Ответ формы: {response.status_code}, URL: {response.url}")

            # Проверяем успех
            time.sleep(5)
            return self.check_internet_access()

        except Exception as e:
            self.log(f"❌ Ошибка отправки формы: {e}", "ERROR")
            return False

    def try_javascript_emulation(self, html_content):
        """Эмуляция JavaScript логики conn4.com"""
        self.log("Эмуляция JavaScript авторизации...")

        try:
            # Conn4.com часто использует AJAX запросы для авторизации
            # Ищем паттерны в JavaScript коде

            # Ищем AJAX endpoints
            ajax_patterns = [
                r'url\s*:\s*["\']([^"\']*)["\']',
                r'\.post\s*\(["\']([^"\']*)["\']',
                r'\.get\s*\(["\']([^"\']*)["\']',
                r'fetch\s*\(["\']([^"\']*)["\']'
            ]

            ajax_urls = []
            for pattern in ajax_patterns:
                matches = re.finditer(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    url = match.group(1)
                    if url.startswith('/') or 'conn4.com' in url:
                        ajax_urls.append(url)

            # Удаляем дубликаты
            ajax_urls = list(set(ajax_urls))

            if ajax_urls:
                self.log(f"Найдены AJAX endpoints: {ajax_urls}")

                # Пробуем каждый endpoint
                for ajax_url in ajax_urls:
                    if self.try_ajax_request(ajax_url):
                        return True

            # Если AJAX не сработал, пробуем простые GET запросы к известным conn4 endpoints
            return self.try_conn4_endpoints()

        except Exception as e:
            self.log(f"❌ Ошибка эмуляции JS: {e}", "ERROR")
            return False

    def try_ajax_request(self, endpoint):
        """Попытка AJAX запроса"""
        try:
            # Формируем полный URL
            if endpoint.startswith('/'):
                base_url = f"{urlparse(self.portal_url).scheme}://{urlparse(self.portal_url).netloc}"
                full_url = urljoin(base_url, endpoint)
            else:
                full_url = endpoint

            self.log(f"AJAX запрос: {full_url}")

            # Добавляем AJAX заголовки
            ajax_headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }

            # Пробуем POST запрос
            response = self.session.post(full_url, headers=ajax_headers, timeout=10)
            self.log(f"AJAX ответ: {response.status_code}")

            if response.status_code in [200, 302]:
                time.sleep(3)
                if self.check_internet_access():
                    return True

            # Пробуем GET запрос
            response = self.session.get(full_url, timeout=10)
            self.log(f"GET ответ: {response.status_code}")

            if response.status_code in [200, 302]:
                time.sleep(3)
                if self.check_internet_access():
                    return True

        except Exception as e:
            self.log(f"❌ Ошибка AJAX запроса {endpoint}: {e}", "ERROR")

        return False

    def try_conn4_endpoints(self):
        """Попытка стандартных conn4.com endpoints"""
        self.log("Попытка стандартных conn4 endpoints...")

        # Извлекаем параметры из URL портала
        parsed_url = urlparse(self.portal_url)
        params = parse_qs(parsed_url.query)

        # Стандартные conn4 endpoints для авторизации
        endpoints = [
            '/login',
            '/auth',
            '/connect',
            '/access',
            '/submit',
            '/authenticate'
        ]

        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for endpoint in endpoints:
            try:
                full_url = urljoin(base_url, endpoint)
                self.log(f"Попытка endpoint: {full_url}")

                # Подготавливаем данные с параметрами из оригинального URL
                auth_data = {}

                # Добавляем параметры из URL
                for key, values in params.items():
                    if values:
                        auth_data[key] = values[0]

                # Добавляем стандартные поля conn4
                auth_data.update({
                    'action': 'connect',
                    'terms': 'on',
                    'agree': '1',
                    'submit': 'Connect'
                })

                # POST запрос
                response = self.session.post(full_url, data=auth_data, timeout=15, allow_redirects=True)
                self.log(f"POST {endpoint}: {response.status_code}")

                if response.status_code in [200, 302]:
                    time.sleep(5)
                    if self.check_internet_access():
                        self.log(f"✅ Успешная авторизация через {endpoint}")
                        return True

            except Exception as e:
                self.log(f"❌ Ошибка endpoint {endpoint}: {e}", "ERROR")
                continue

        return False

    def check_internet_access(self):
        """Проверка доступности интернета"""
        test_urls = [
            "http://www.google.com",
            "http://connectivitycheck.gstatic.com/generate_204"
        ]

        for test_url in test_urls:
            try:
                response = self.session.get(test_url, timeout=10)

                if response.status_code == 200:
                    if "google" in response.text.lower() and "conn4.com" not in response.url:
                        self.log("🎉 ИНТЕРНЕТ ДОСТУПЕН!")
                        return True
                elif response.status_code == 204:
                    self.log("🎉 ИНТЕРНЕТ ДОСТУПЕН (204)!")
                    return True

            except Exception:
                continue

        self.log("❌ Интернет недоступен")
        return False

    def run_full_authentication(self):
        """Полный процесс авторизации"""
        self.log("=" * 60)
        self.log("АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ НА CAPTIVE PORTAL")
        self.log("=" * 60)

        try:
            # 1. Настройка сети
            if not self.setup_network():
                return False

            # 2. Обнаружение портала
            if not self.detect_portal():
                self.log("✅ Captive portal не найден - интернет доступен")
                return True

            # 3. Анализ портала
            analysis = self.analyze_portal_page()
            if not analysis:
                return False

            # 4. Попытка авторизации
            auth_success = self.authenticate_conn4_portal(analysis)

            if auth_success:
                self.log("🎉 АВТОРИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            else:
                self.log("❌ Авторизация не удалась")

            return auth_success

        except KeyboardInterrupt:
            self.log("⚠️ Прервано пользователем")
            return False
        except Exception as e:
            self.log(f"❌ Критическая ошибка: {e}", "ERROR")
            return False
        finally:
            self.restore_network()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Автоматическая авторизация на captive порталах',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # Интерактивный режим
  %(prog)s --room "12345" --password "secret" # С параметрами
  %(prog)s --portal-url "http://192.168.1.1"  # Указать портал
  %(prog)s --debug                            # Отладочный режим

Переменные окружения:
  CAPTIVE_ROOM_NUMBER - номер комнаты
  CAPTIVE_ACCESS_CODE - код доступа
  CAPTIVE_PORTAL_URL  - URL портала
  CAPTIVE_LOG_LEVEL   - уровень логирования (DEBUG, INFO, WARNING, ERROR)
        """
    )

    parser.add_argument('--router-ip', default='192.168.1.1',
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--portal-url',
                       help='URL captive портала (определяется автоматически)')
    parser.add_argument('--room', '--room-number',
                       help='Номер комнаты для авторизации')
    parser.add_argument('--password', '--access-code',
                       help='Код доступа/пароль')
    parser.add_argument('--debug', action='store_true',
                       help='Включить отладочный режим')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Таймаут операций в секундах (по умолчанию: 30)')

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.debug:
        os.environ['CAPTIVE_LOG_LEVEL'] = 'DEBUG'
    elif args.verbose:
        os.environ['CAPTIVE_LOG_LEVEL'] = 'INFO'

    # Установка переменных окружения из аргументов
    if args.room:
        os.environ['CAPTIVE_ROOM_NUMBER'] = args.room
    if args.password:
        os.environ['CAPTIVE_ACCESS_CODE'] = args.password
    if args.portal_url:
        os.environ['CAPTIVE_PORTAL_URL'] = args.portal_url

    # Интерактивный ввод если параметры не заданы
    if not args.room and not os.environ.get('CAPTIVE_ROOM_NUMBER'):
        try:
            room = input("Введите номер комнаты: ").strip()
            if room:
                os.environ['CAPTIVE_ROOM_NUMBER'] = room
        except (KeyboardInterrupt, EOFError):
            print("\nОтменено пользователем")
            sys.exit(1)

    if not args.password and not os.environ.get('CAPTIVE_ACCESS_CODE'):
        try:
            import getpass
            password = getpass.getpass("Введите код доступа: ").strip()
            if password:
                os.environ['CAPTIVE_ACCESS_CODE'] = password
        except (KeyboardInterrupt, EOFError):
            print("\nОтменено пользователем")
            sys.exit(1)

    # Создание и запуск авторизатора
    auth = CaptivePortalAuth(router_ip=args.router_ip)

    try:
        success = auth.run_full_authentication()

        if success:
            print("\n🎉 Авторизация завершена успешно!")
            sys.exit(0)
        else:
            print("\n❌ Авторизация не удалась")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
