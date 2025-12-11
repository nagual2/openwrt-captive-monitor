#!/usr/bin/env python3
"""
Анализатор Captive Portal с использованием Selenium WebDriver
===========================================================

Этот инструмент выполняет комплексный анализ captive порталов с использованием
браузерной автоматизации для извлечения форм, JavaScript логики и генерации
конфигурации для последующей автоматизации.

Возможности:
- Автоматическое обнаружение форм авторизации
- Извлечение всех полей форм и их атрибутов
- Анализ JavaScript кода и функций
- Генерация конфигурации для автоматизации
- Поддержка headless режима для серверного использования
- Скриншоты для диагностики

Использование:
    # Базовый анализ с GUI
    python captive_portal_selenium_analyzer.py

    # Headless режим (без GUI)
    python captive_portal_selenium_analyzer.py --headless

    # Анализ конкретного URL
    python captive_portal_selenium_analyzer.py --url "http://192.168.1.1" --headless

    # С сохранением результатов
    python captive_portal_selenium_analyzer.py --output analysis.json

    # Через WSL
    wsl python3 captive_portal_selenium_analyzer.py --headless

Требования:
    - Python 3.6+
    - selenium library (pip install selenium)
    - webdriver-manager (pip install webdriver-manager)
    - Firefox browser (Windows) или firefox-esr (Linux)

Переменные окружения:
    WEBDRIVER_HEADLESS - запуск в headless режиме (true/false)
    WEBDRIVER_TIMEOUT  - таймаут операций в секундах (по умолчанию: 30)
    DISPLAY           - для WSL с GUI (например: :0)

Примеры:
    # Анализ с переменными окружения
    export WEBDRIVER_HEADLESS=true
    export WEBDRIVER_TIMEOUT=60
    python captive_portal_selenium_analyzer.py

    # WSL с GUI поддержкой
    export DISPLAY=:0
    python3 captive_portal_selenium_analyzer.py

Автор: OpenWrt Captive Monitor Project
Лицензия: MIT
"""

import time
import sys
import os
import json
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CaptivePortalAnalyzer:
    def __init__(self, router_ip="192.168.1.1", headless=False):
        self.router_ip = router_ip
        self.headless = headless
        self.driver = None
        self.portal_data = {}

    def setup_network(self):
        """Настройка сети через роутер"""
        print(f"[INFO] Настройка DNS через {self.router_ip}")

        dns_config = f"""nameserver {self.router_ip}
nameserver 8.8.8.8
"""

        try:
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)
            with open('/tmp/resolv.conf.temp', 'w') as f:
                f.write(dns_config)
            subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.temp', '/etc/resolv.conf'], check=True)
            print("[INFO] ✅ DNS настроен")
            return True
        except Exception as e:
            print(f"[ERROR] ❌ Ошибка настройки DNS: {e}")
            return False

    def restore_network(self):
        """Восстановление сети"""
        try:
            if os.path.exists('/etc/resolv.conf.backup'):
                subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup', '/etc/resolv.conf'])
                subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup'])
            print("[INFO] ✅ DNS восстановлен")
        except Exception as e:
            print(f"[ERROR] ❌ Ошибка восстановления: {e}")

    def setup_driver(self):
        """Настройка Firefox WebDriver"""
        print("[INFO] Настройка Firefox...")

        try:
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            self.driver = webdriver.Firefox(options=options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            print("[INFO] ✅ Firefox настроен")
            return True
        except Exception as e:
            print(f"[ERROR] ❌ Ошибка настройки Firefox: {e}")
            return False

    def detect_portal(self):
        """Обнаружение captive portal"""
        print("[INFO] Поиск captive portal...")

        test_url = "http://connectivitycheck.gstatic.com/generate_204"

        try:
            self.driver.get(test_url)
            time.sleep(5)

            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"[INFO] URL: {current_url}")
            print(f"[INFO] Title: {page_title}")

            if "conn4.com" in current_url:
                print("[INFO] 🚨 Captive portal обнаружен!")
                self.portal_data['portal_url'] = current_url
                return True
            else:
                print("[INFO] ✅ Интернет доступен")
                return False

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка обнаружения: {e}")
            return False

    def analyze_portal_page(self):
        """Детальный анализ страницы портала"""
        print("[INFO] Анализ страницы captive portal...")

        try:
            # Сохраняем HTML
            html_content = self.driver.page_source
            with open('portal_page_source.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("[INFO] 📄 HTML сохранен в portal_page_source.html")

            # Анализируем формы
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"[INFO] Найдено форм: {len(forms)}")

            form_data = []
            for i, form in enumerate(forms):
                try:
                    action = form.get_attribute("action") or ""
                    method = form.get_attribute("method") or "GET"

                    # Ищем поля в форме
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    input_data = []

                    for inp in inputs:
                        input_info = {
                            'type': inp.get_attribute("type") or "text",
                            'name': inp.get_attribute("name") or "",
                            'value': inp.get_attribute("value") or "",
                            'id': inp.get_attribute("id") or ""
                        }
                        input_data.append(input_info)

                    form_info = {
                        'index': i,
                        'action': action,
                        'method': method.upper(),
                        'inputs': input_data
                    }
                    form_data.append(form_info)

                    print(f"[INFO] Форма {i}: {method.upper()} {action}")
                    for inp in input_data:
                        print(f"[INFO]   Input: {inp['type']} '{inp['name']}' = '{inp['value']}'")

                except Exception as e:
                    print(f"[ERROR] Ошибка анализа формы {i}: {e}")

            self.portal_data['forms'] = form_data

            # Анализируем JavaScript
            self.analyze_javascript()

            # Анализируем кнопки
            self.analyze_buttons()

            return True

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка анализа страницы: {e}")
            return False

    def analyze_javascript(self):
        """Анализ JavaScript на странице"""
        print("[INFO] Анализ JavaScript...")

        try:
            # Получаем все script теги
            scripts = self.driver.find_elements(By.TAG_NAME, "script")

            js_data = []
            for i, script in enumerate(scripts):
                src = script.get_attribute("src")
                content = script.get_attribute("innerHTML") or ""

                if src:
                    print(f"[INFO] Внешний JS: {src}")
                    js_data.append({'type': 'external', 'src': src})
                elif content.strip():
                    print(f"[INFO] Встроенный JS: {len(content)} символов")
                    js_data.append({'type': 'inline', 'content': content[:200] + "..."})

            self.portal_data['javascript'] = js_data

            # Пытаемся выполнить JavaScript для получения данных
            try:
                # Получаем все глобальные переменные
                global_vars = self.driver.execute_script("""
                    var globals = {};
                    for (var key in window) {
                        if (window.hasOwnProperty(key) && typeof window[key] !== 'function') {
                            try {
                                globals[key] = window[key];
                            } catch(e) {}
                        }
                    }
                    return globals;
                """)

                print(f"[INFO] Найдено глобальных переменных: {len(global_vars)}")
                for key, value in list(global_vars.items())[:10]:  # Показываем первые 10
                    print(f"[INFO]   {key}: {str(value)[:50]}")

                self.portal_data['global_vars'] = global_vars

            except Exception as e:
                print(f"[ERROR] Ошибка выполнения JS: {e}")

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка анализа JavaScript: {e}")

    def analyze_buttons(self):
        """Анализ кнопок и ссылок"""
        print("[INFO] Анализ кнопок...")

        try:
            # Ищем все кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
            links = self.driver.find_elements(By.TAG_NAME, "a")

            button_data = []

            # Анализируем button теги
            for btn in buttons:
                btn_info = {
                    'tag': 'button',
                    'text': btn.text.strip(),
                    'type': btn.get_attribute("type") or "button",
                    'onclick': btn.get_attribute("onclick") or "",
                    'id': btn.get_attribute("id") or "",
                    'class': btn.get_attribute("class") or ""
                }
                button_data.append(btn_info)
                print(f"[INFO] Button: '{btn_info['text']}' onclick='{btn_info['onclick']}'")

            # Анализируем input кнопки
            for inp in inputs:
                btn_info = {
                    'tag': 'input',
                    'text': inp.get_attribute("value") or "",
                    'type': inp.get_attribute("type"),
                    'onclick': inp.get_attribute("onclick") or "",
                    'id': inp.get_attribute("id") or "",
                    'class': inp.get_attribute("class") or ""
                }
                button_data.append(btn_info)
                print(f"[INFO] Input: '{btn_info['text']}' onclick='{btn_info['onclick']}'")

            # Анализируем ссылки с JavaScript
            for link in links:
                href = link.get_attribute("href") or ""
                onclick = link.get_attribute("onclick") or ""
                text = link.text.strip()

                if onclick or "javascript:" in href:
                    btn_info = {
                        'tag': 'a',
                        'text': text,
                        'href': href,
                        'onclick': onclick,
                        'id': link.get_attribute("id") or "",
                        'class': link.get_attribute("class") or ""
                    }
                    button_data.append(btn_info)
                    print(f"[INFO] Link: '{text}' href='{href}' onclick='{onclick}'")

            self.portal_data['buttons'] = button_data

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка анализа кнопок: {e}")

    def try_authentication(self):
        """Попытка авторизации через Selenium"""
        print("[INFO] Попытка авторизации...")

        try:
            # Ищем кнопки подключения
            connect_buttons = []

            for btn_info in self.portal_data.get('buttons', []):
                text = btn_info['text'].lower()
                if any(keyword in text for keyword in ['connect', 'continue', 'access', 'agree', 'start']):
                    connect_buttons.append(btn_info)

            if not connect_buttons:
                print("[ERROR] ❌ Не найдены кнопки подключения")
                return False

            # Пробуем нажать на первую подходящую кнопку
            btn_info = connect_buttons[0]
            print(f"[INFO] Попытка нажать: '{btn_info['text']}'")

            if btn_info['tag'] == 'button':
                element = self.driver.find_element(By.TAG_NAME, "button")
                if btn_info['text']:
                    element = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{btn_info['text']}')]")
            elif btn_info['tag'] == 'input':
                if btn_info['text']:
                    element = self.driver.find_element(By.XPATH, f"//input[@value='{btn_info['text']}']")
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            elif btn_info['tag'] == 'a':
                element = self.driver.find_element(By.XPATH, f"//a[contains(text(), '{btn_info['text']}')]")

            # Нажимаем кнопку
            element.click()
            print("[INFO] ✅ Кнопка нажата")

            # Ждем перенаправления
            time.sleep(10)

            # Проверяем результат
            new_url = self.driver.current_url
            print(f"[INFO] Новый URL: {new_url}")

            # Проверяем доступность интернета
            self.driver.get("http://www.google.com")
            time.sleep(5)

            final_url = self.driver.current_url
            if "google.com" in final_url and "conn4.com" not in final_url:
                print("[INFO] 🎉 АВТОРИЗАЦИЯ УСПЕШНА!")
                return True
            else:
                print("[INFO] ❌ Авторизация не удалась")
                return False

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка авторизации: {e}")
            return False

    def save_analysis_data(self):
        """Сохранение данных анализа для создания Python скрипта"""
        print("[INFO] Сохранение данных анализа...")

        try:
            # Сохраняем все собранные данные
            analysis_data = {
                'portal_url': self.portal_data.get('portal_url', ''),
                'forms': self.portal_data.get('forms', []),
                'buttons': self.portal_data.get('buttons', []),
                'javascript': self.portal_data.get('javascript', []),
                'global_vars': self.portal_data.get('global_vars', {}),
                'timestamp': time.time()
            }

            with open('portal_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)

            print("[INFO] 📄 Анализ сохранен в portal_analysis.json")

            # Создаем шаблон для Python скрипта
            self.generate_python_script_template(analysis_data)

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка сохранения: {e}")

    def generate_python_script_template(self, data):
        """Генерация шаблона Python скрипта на основе анализа"""
        print("[INFO] Генерация Python скрипта...")

        script_template = f'''#!/usr/bin/env python3
"""
Автоматически сгенерированный скрипт авторизации на captive portal.
Основан на анализе портала: {data['portal_url']}
"""

import requests
import time
import sys
import subprocess
import os

class CaptivePortalAuth:
    def __init__(self, router_ip="192.168.1.1"):
        self.router_ip = router_ip
        self.session = requests.Session()
        self.portal_url = "{data['portal_url']}"

    def setup_network(self):
        """Настройка DNS через роутер"""
        dns_config = f"""nameserver {{self.router_ip}}
nameserver 8.8.8.8
"""
        try:
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)
            with open('/tmp/resolv.conf.temp', 'w') as f:
                f.write(dns_config)
            subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.temp', '/etc/resolv.conf'], check=True)
            print("[INFO] ✅ DNS настроен")
            return True
        except Exception as e:
            print(f"[ERROR] ❌ Ошибка настройки DNS: {{e}}")
            return False

    def restore_network(self):
        """Восстановление DNS"""
        try:
            if os.path.exists('/etc/resolv.conf.backup'):
                subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup', '/etc/resolv.conf'])
                subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup'])
            print("[INFO] ✅ DNS восстановлен")
        except Exception as e:
            print(f"[ERROR] ❌ Ошибка восстановления: {{e}}")

    def detect_portal(self):
        """Обнаружение captive portal"""
        test_url = "http://connectivitycheck.gstatic.com/generate_204"

        try:
            response = self.session.get(test_url, timeout=10, allow_redirects=True)

            if "conn4.com" in response.url:
                print(f"[INFO] 🚨 Captive portal: {{response.url}}")
                self.portal_url = response.url
                return True
            elif response.status_code == 204:
                print("[INFO] ✅ Интернет доступен")
                return False
            else:
                print(f"[INFO] Неожиданный ответ: {{response.status_code}}")
                return False

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка обнаружения: {{e}}")
            return False

    def authenticate(self):
        """Авторизация на портале"""
        print("[INFO] Начало авторизации...")

        try:
            # Получаем страницу портала
            response = self.session.get(self.portal_url, timeout=15)

            if response.status_code != 200:
                print(f"[ERROR] Ошибка загрузки портала: {{response.status_code}}")
                return False

            print("[INFO] Страница портала загружена")

            # Анализируем формы (на основе данных Selenium)'''

        # Добавляем информацию о формах из анализа
        if data['forms']:
            form = data['forms'][0]  # Берем первую форму
            script_template += f'''

            # Форма найдена: {form['method']} {form['action']}
            form_action = "{form['action']}"
            form_method = "{form['method']}"

            # Подготавливаем данные формы
            form_data = {{'''

            for inp in form['inputs']:
                if inp['type'] in ['hidden', 'text', 'email']:
                    script_template += f'''
                "{inp['name']}": "{inp['value']}",'''

            script_template += '''
            }

            # Отправляем форму
            if form_method == "POST":
                auth_response = self.session.post(form_action, data=form_data, timeout=15)
            else:
                auth_response = self.session.get(form_action, params=form_data, timeout=15)

            print(f"[INFO] Ответ формы: {auth_response.status_code}")
            '''

        script_template += '''

            # Проверяем успех авторизации
            time.sleep(5)
            return self.check_internet()

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка авторизации: {e}")
            return False

    def check_internet(self):
        """Проверка доступности интернета"""
        try:
            response = self.session.get("http://www.google.com", timeout=10)
            if response.status_code == 200 and "google" in response.text.lower():
                print("[INFO] 🎉 АВТОРИЗАЦИЯ УСПЕШНА!")
                return True
            else:
                print("[INFO] ❌ Интернет недоступен")
                return False
        except Exception as e:
            print(f"[ERROR] ❌ Ошибка проверки: {e}")
            return False

    def run(self):
        """Основной метод"""
        try:
            if not self.setup_network():
                return False

            if not self.detect_portal():
                return True  # Интернет уже доступен

            return self.authenticate()

        finally:
            self.restore_network()

def main():
    auth = CaptivePortalAuth()
    success = auth.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
'''

        with open('captive_portal_auth_generated.py', 'w', encoding='utf-8') as f:
            f.write(script_template)

        print("[INFO] 📄 Python скрипт создан: captive_portal_auth_generated.py")

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                print("[INFO] Firefox закрыт")
            except:
                pass
        self.restore_network()

    def run_analysis(self):
        """Запуск полного анализа"""
        print("=" * 60)
        print("АНАЛИЗ CAPTIVE PORTAL С SELENIUM")
        print("=" * 60)

        try:
            if not self.setup_network():
                return False

            if not self.setup_driver():
                return False

            if not self.detect_portal():
                print("[INFO] Captive portal не найден")
                return True

            if not self.analyze_portal_page():
                return False

            # Пробуем авторизацию
            auth_success = self.try_authentication()

            # Сохраняем данные анализа
            self.save_analysis_data()

            return auth_success

        except Exception as e:
            print(f"[ERROR] ❌ Критическая ошибка: {e}")
            return False
        finally:
            self.cleanup()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Анализ captive порталов с использованием Selenium WebDriver',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # GUI режим для отладки
  %(prog)s --headless                         # Headless режим
  %(prog)s --url "http://192.168.1.1"         # Анализ конкретного URL
  %(prog)s --output analysis.json             # Сохранить результаты
  %(prog)s --detect-type                      # Только определить тип портала

Переменные окружения:
  WEBDRIVER_HEADLESS - запуск в headless режиме (true/false)
  WEBDRIVER_TIMEOUT  - таймаут операций в секундах
  DISPLAY           - для WSL с GUI поддержкой
        """
    )

    parser.add_argument('--router-ip', default='192.168.1.1',
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--url',
                       help='URL captive портала для анализа')
    parser.add_argument('--headless', action='store_true',
                       help='Запуск в headless режиме (без GUI)')
    parser.add_argument('--output', '-o',
                       help='Файл для сохранения результатов анализа (JSON)')
    parser.add_argument('--detect-type', action='store_true',
                       help='Только определить тип портала и выйти')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Таймаут операций в секундах (по умолчанию: 30)')
    parser.add_argument('--debug', action='store_true',
                       help='Включить отладочный режим')
    parser.add_argument('--screenshot', action='store_true',
                       help='Сделать скриншот портала')

    args = parser.parse_args()

    # Настройка переменных окружения
    if args.headless or os.environ.get('WEBDRIVER_HEADLESS', '').lower() == 'true':
        headless = True
    else:
        headless = False

    if args.timeout:
        os.environ['WEBDRIVER_TIMEOUT'] = str(args.timeout)

    # Создание анализатора
    analyzer = CaptivePortalAnalyzer(router_ip=args.router_ip, headless=headless)

    try:
        if args.detect_type:
            # Только определение типа портала
            print("[INFO] Определение типа captive портала...")
            success = analyzer.setup_network()
            if success:
                portal_url = analyzer.detect_portal()
                if portal_url:
                    portal_type = analyzer.identify_portal_type(portal_url)
                    print(f"[RESULT] Тип портала: {portal_type}")
                    if args.output:
                        result = {"portal_type": portal_type, "portal_url": portal_url}
                        with open(args.output, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        print(f"[INFO] Результат сохранен в {args.output}")
                else:
                    print("[RESULT] Captive portal не обнаружен")
            sys.exit(0 if success else 1)

        # Полный анализ
        success = analyzer.run_analysis()

        # Сохранение результатов
        if success and args.output and analyzer.portal_data:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(analyzer.portal_data, f, indent=2, ensure_ascii=False)
                print(f"[INFO] ✅ Результаты анализа сохранены в {args.output}")
            except Exception as e:
                print(f"[ERROR] ❌ Ошибка сохранения результатов: {e}")

        # Скриншот
        if args.screenshot and analyzer.driver:
            try:
                screenshot_path = f"captive_portal_screenshot_{int(time.time())}.png"
                analyzer.driver.save_screenshot(screenshot_path)
                print(f"[INFO] 📸 Скриншот сохранен: {screenshot_path}")
            except Exception as e:
                print(f"[ERROR] ❌ Ошибка создания скриншота: {e}")

        if success:
            print("\n🎉 Анализ завершен успешно!")
            sys.exit(0)
        else:
            print("\n❌ Анализ не удался")
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
    finally:
        if analyzer:
            analyzer.cleanup()

if __name__ == "__main__":
    main()
