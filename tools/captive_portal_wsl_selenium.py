#!/usr/bin/env python3
"""
Консолидированный скрипт авторизации на captive порталах через WSL
================================================================

Единый скрипт на Selenium для автоматической авторизации на captive порталах.
Работает только через WSL с принудительной маршрутизацией через роутер 192.168.1.1.

Возможности:
- Принудительная маршрутизация через роутер 192.168.1.1
- Автоматическое обнаружение captive порталов
- Поддержка различных типов авторизации (простое подключение, формы, условия)
- Работа с Chrome в headless режиме
- Автоматическое восстановление сетевых настроек

Использование:
    # Базовый запуск (headless режим)
    wsl python3 tools/captive_portal_wsl_selenium.py

    # С отображением браузера для отладки
    wsl python3 tools/captive_portal_wsl_selenium.py --show-browser

    # С учетными данными
    wsl python3 tools/captive_portal_wsl_selenium.py --username "user" --password "pass"

    # Отладочный режим
    wsl python3 tools/captive_portal_wsl_selenium.py --debug

Требования:
    - WSL 2
    - Python 3.6+
    - selenium (pip install selenium)
    - webdriver-manager (pip install webdriver-manager)
    - Google Chrome в WSL
    - sudo права для настройки сети

Автор: OpenWrt Captive Monitor Project
Лицензия: MIT
"""

import time
import sys
import os
import argparse
import logging
import subprocess
import platform
from urllib.parse import urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium webdriver-manager")
    sys.exit(1)

# Проверяем, что мы в WSL
is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("❌ Этот скрипт должен запускаться только в WSL!")
    print("Используйте: wsl python3 tools/captive_portal_wsl_selenium.py")
    sys.exit(1)

class CaptivePortalWSLSelenium:
    """Консолидированный авторизатор captive порталов для WSL с Selenium"""

    def __init__(self, router_ip="192.168.1.1", timeout=30, headless=True):
        self.router_ip = router_ip
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self.portal_url = None
        self.added_routes = []

        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def setup_network_routing(self):
        """Настройка принудительной маршрутизации через роутер"""
        self.logger.info(f"Настройка принудительной маршрутизации через {self.router_ip}")

        try:
            # Проверяем права sudo
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
            if result.returncode != 0:
                self.logger.error("❌ Требуются права sudo для настройки маршрутизации")
                self.logger.info("Выполните: sudo visudo и добавьте строку:")
                self.logger.info(f"{os.getenv('USER')} ALL=(ALL) NOPASSWD: /sbin/ip, /bin/cp, /usr/bin/tee")
                return False

            # Настраиваем DNS через роутер
            dns_config = f"""# Временная настройка для captive portal через WSL
nameserver {self.router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

            # Сохраняем оригинальный resolv.conf
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)

            # Устанавливаем новый resolv.conf
            temp_file = os.path.expanduser('~/resolv.conf.temp')
            with open(temp_file, 'w') as f:
                f.write(dns_config)
            subprocess.run(['sudo', 'cp', temp_file, '/etc/resolv.conf'], check=True)
            os.remove(temp_file)

            # Добавляем маршруты для тестовых хостов через роутер
            test_hosts = [
                "www.msftconnecttest.com",
                "connectivitycheck.gstatic.com",
                "clients3.google.com",
                "www.google.com",
                "detectportal.firefox.com"
            ]

            for host in test_hosts:
                try:
                    # Разрешаем IP через DNS роутера
                    result = subprocess.run(['dig', f'@{self.router_ip}', host, 'A', '+short'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        ip = result.stdout.strip().split('\n')[0]
                        if ip and '.' in ip and not ip.startswith(';'):
                            # Добавляем маршрут
                            cmd = ['sudo', 'ip', 'route', 'add', ip, 'via', self.router_ip]
                            result = subprocess.run(cmd, capture_output=True, text=True)

                            if result.returncode == 0:
                                self.logger.info(f"✅ Маршрут добавлен: {host} ({ip}) via {self.router_ip}")
                                self.added_routes.append(ip)
                            elif "File exists" in result.stderr:
                                self.logger.debug(f"ℹ️ Маршрут уже существует: {host} ({ip})")

                except Exception as e:
                    self.logger.debug(f"Ошибка добавления маршрута для {host}: {e}")

            self.logger.info("✅ Принудительная маршрутизация через роутер настроена")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки маршрутизации: {e}")
            return False

    def restore_network_routing(self):
        """Восстановление оригинальной сетевой конфигурации"""
        self.logger.info("Восстановление сетевой конфигурации")

        try:
            # Восстанавливаем resolv.conf
            if os.path.exists('/etc/resolv.conf.backup'):
                subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup', '/etc/resolv.conf'],
                             capture_output=True)
                subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup'], capture_output=True)

            # Удаляем добавленные маршруты
            for ip in self.added_routes:
                try:
                    cmd = ['sudo', 'ip', 'route', 'del', ip, 'via', self.router_ip]
                    subprocess.run(cmd, capture_output=True)
                except Exception:
                    pass

            self.logger.info("✅ Сетевая конфигурация восстановлена")

        except Exception as e:
            self.logger.error(f"❌ Ошибка восстановления конфигурации: {e}")

    def setup_chrome_driver(self):
        """Настройка Chrome WebDriver для WSL"""
        self.logger.info("Настройка Chrome WebDriver для WSL...")

        try:
            # Проверяем наличие Chrome
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium"
            ]

            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break

            if not chrome_binary:
                self.logger.error("❌ Chrome не найден в WSL")
                self.logger.info("Установите: sudo apt update && sudo apt install google-chrome-stable")
                return False

            # Настройка Chrome опций
            options = Options()

            if self.headless:
                options.add_argument("--headless=new")

            # Настройки для WSL
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--window-size=1920,1080")
            # НЕ используем single-process в WSL - это может вызывать проблемы

            # КЛЮЧЕВАЯ НАСТРОЙКА: Принудительная маршрутизация через роутер
            options.add_argument(f"--host-resolver-rules=MAP * {self.router_ip}")

            # User-Agent
            options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Установка бинарного файла Chrome
            options.binary_location = chrome_binary

            # Настройка ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.logger.info("ChromeDriver установлен через webdriver-manager")
            except Exception as e:
                self.logger.warning(f"Ошибка webdriver-manager: {e}")
                # Пробуем системный chromedriver
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    service = Service(result.stdout.strip())
                    self.logger.info(f"Используем системный chromedriver: {result.stdout.strip()}")
                else:
                    service = Service()
                    self.logger.warning("Используем ChromeDriver по умолчанию")

            # Создание драйвера
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)

            self.logger.info("✅ Chrome WebDriver настроен успешно с принудительной маршрутизацией")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки Chrome WebDriver: {e}")
            return False
    def detect_captive_portal(self):
        """Обнаружение captive portal через принудительную маршрутизацию"""
        self.logger.info("Обнаружение captive portal через роутер...")

        test_urls = [
            "http://www.msftconnecttest.com/redirect",
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://clients3.google.com/generate_204",
            "http://detectportal.firefox.com/canonical.html",
            "http://www.google.com/"
        ]

        for url in test_urls:
            try:
                self.logger.info(f"Тестирование URL: {url}")
                self.driver.get(url)

                # Ждем загрузки страницы
                time.sleep(5)

                current_url = self.driver.current_url
                page_title = self.driver.title

                self.logger.info(f"Текущий URL: {current_url}")
                self.logger.info(f"Заголовок страницы: {page_title}")

                # Проверяем, произошел ли редирект на captive portal
                if self.is_captive_portal_page(current_url, page_title):
                    self.portal_url = current_url
                    self.logger.info(f"🚨 Captive portal обнаружен: {current_url}")
                    return True

            except TimeoutException:
                self.logger.warning(f"⏰ Таймаут при загрузке {url}")
                continue
            except Exception as e:
                self.logger.error(f"❌ Ошибка при тестировании {url}: {e}")
                continue

        self.logger.info("✅ Captive portal не обнаружен - интернет доступен")
        return False

    def is_captive_portal_page(self, url, title):
        """Определение, является ли страница captive portal"""
        # Проверяем домен
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # Известные домены captive portal
        captive_domains = [
            'conn4.com', 'rdr.conn4.com', 'captive.apple.com',
            'connectivitycheck.android.com', 'login.microsoftonline.com',
            'portal', 'hotspot', 'wifi', 'guest', 'auth', 'phc.prontonetworks.com'
        ]

        for captive_domain in captive_domains:
            if captive_domain in domain:
                return True

        # Проверяем заголовок страницы
        title_lower = title.lower()
        captive_keywords = [
            'login', 'sign in', 'authentication', 'portal', 'hotspot',
            'wifi', 'internet access', 'terms', 'agreement', 'welcome',
            'connect', 'access'
        ]

        for keyword in captive_keywords:
            if keyword in title_lower:
                return True

        # Проверяем содержимое страницы
        try:
            page_source = self.driver.page_source.lower()

            # Ищем формы входа
            if any(keyword in page_source for keyword in ['login', 'password', 'username', 'email']):
                return True

            # Ищем кнопки подключения
            if any(keyword in page_source for keyword in ['connect', 'access', 'continue', 'agree', 'submit']):
                return True

        except Exception:
            pass

        return False

    def authenticate_portal(self, username=None, password=None):
        """Автоматическая авторизация на captive portal"""
        if not self.portal_url:
            self.logger.error("❌ URL captive portal не определен")
            return False

        self.logger.info(f"Начало авторизации на: {self.portal_url}")

        try:
            # Переходим на портал (если еще не там)
            if self.driver.current_url != self.portal_url:
                self.driver.get(self.portal_url)
                time.sleep(3)

            # Сохраняем скриншот портала для отладки
            self.save_screenshot("captive_portal_page.png")

            # Анализируем тип портала и выполняем авторизацию
            return self._perform_authentication(username, password)

        except Exception as e:
            self.logger.error(f"❌ Ошибка авторизации: {e}")
            return False

    def _perform_authentication(self, username=None, password=None):
        """Выполнение авторизации в зависимости от типа портала"""

        # 1. Попробуем найти простую кнопку "Connect" или "Continue"
        if self._try_simple_connect():
            return True

        # 2. Попробуем авторизацию с учетными данными (если предоставлены)
        if username and password and self._try_credentials_auth(username, password):
            return True

        # 3. Попробуем принять условия использования
        if self._try_terms_acceptance():
            return True

        # 4. Попробуем специфичную авторизацию для известных порталов
        if self._try_known_portal_auth():
            return True

        self.logger.warning("⚠️ Не удалось определить метод авторизации")
        self.save_screenshot("auth_failed_analysis.png")
        self._debug_page_info()

        return False

    def _try_simple_connect(self):
        """Попытка простого подключения через кнопку"""
        self.logger.info("Попытка простого подключения...")

        # Возможные селекторы кнопок подключения
        connect_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'access')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
            "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "#connect", "#continue", "#access", "#agree",
            ".connect-btn", ".continue-btn", ".access-btn", ".agree-btn"
        ]

        for selector in connect_selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                elif selector.startswith("#"):
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, selector[1:]))
                    )
                elif selector.startswith("."):
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, selector[1:]))
                    )
                else:
                    continue

                self.logger.info(f"Найдена кнопка подключения: {selector}")
                element.click()

                # Ждем перенаправления или изменения страницы
                time.sleep(10)

                # Проверяем, прошла ли авторизация
                if self._check_authentication_success():
                    self.logger.info("✅ Простое подключение успешно")
                    return True

            except TimeoutException:
                continue
            except Exception as e:
                self.logger.debug(f"Ошибка с селектором {selector}: {e}")
                continue

        return False

    def _try_credentials_auth(self, username, password):
        """Попытка авторизации с учетными данными"""
        self.logger.info("Попытка авторизации с учетными данными...")

        try:
            # Ищем поля ввода
            username_field = None
            password_field = None

            # Возможные селекторы для полей ввода
            username_selectors = [
                "input[name='username']", "input[name='user']", "input[name='login']",
                "input[name='email']", "input[name='userId']", "input[name='roomNumber']",
                "input[type='text']", "#username", "#user", "#login", "#userId", "#roomNumber"
            ]

            password_selectors = [
                "input[name='password']", "input[name='accessCode']", "input[name='pass']",
                "input[type='password']", "#password", "#accessCode", "#pass"
            ]

            # Ищем поле username
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            # Ищем поле password
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if username_field and password_field:
                self.logger.info("Найдены поля для ввода учетных данных")

                username_field.clear()
                username_field.send_keys(username)

                password_field.clear()
                password_field.send_keys(password)

                # Ищем кнопку отправки
                submit_selectors = [
                    "input[type='submit']", "button[type='submit']", "input[name='Submit22']",
                    "//button[contains(text(), 'Login')]", "//button[contains(text(), 'Sign In')]",
                    "//button[contains(text(), 'Submit')]", "//input[@value='Submit']"
                ]

                for selector in submit_selectors:
                    try:
                        if selector.startswith("//"):
                            submit_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                        submit_button.click()
                        time.sleep(10)

                        if self._check_authentication_success():
                            self.logger.info("✅ Авторизация с учетными данными успешна")
                            return True
                        break

                    except NoSuchElementException:
                        continue

        except Exception as e:
            self.logger.error(f"Ошибка авторизации с учетными данными: {e}")

        return False
    def _try_terms_acceptance(self):
        """Попытка принятия условий использования"""
        self.logger.info("Попытка принятия условий использования...")

        try:
            # Ищем чекбоксы согласия
            checkbox_selectors = [
                "input[type='checkbox']",
                "//input[@type='checkbox'][contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//input[@type='checkbox'][contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'terms')]",
                "//input[@type='checkbox'][contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"
            ]

            checkboxes_found = False
            for selector in checkbox_selectors:
                try:
                    if selector.startswith("//"):
                        checkboxes = self.driver.find_elements(By.XPATH, selector)
                    else:
                        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for checkbox in checkboxes:
                        if checkbox.is_displayed() and not checkbox.is_selected():
                            checkbox.click()
                            checkboxes_found = True
                            self.logger.info("Отмечен чекбокс согласия")

                except Exception:
                    continue

            # Ищем кнопку принятия условий
            accept_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]",
                "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]"
            ]

            for selector in accept_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    time.sleep(10)

                    if self._check_authentication_success():
                        self.logger.info("✅ Принятие условий успешно")
                        return True

                except TimeoutException:
                    continue

        except Exception as e:
            self.logger.error(f"Ошибка принятия условий: {e}")

        return False

    def _try_known_portal_auth(self):
        """Попытка авторизации для известных порталов"""
        current_url = self.driver.current_url

        # Специфичная обработка для phc.prontonetworks.com
        if "phc.prontonetworks.com" in current_url:
            return self._try_pronto_networks_auth()

        # Специфичная обработка для conn4.com
        if "conn4.com" in current_url:
            return self._try_conn4_auth()

        return False

    def _try_pronto_networks_auth(self):
        """Авторизация для phc.prontonetworks.com портала"""
        self.logger.info("Попытка авторизации на phc.prontonetworks.com...")

        try:
            # Ищем кнопку "Accept/Agree" или "Connect"
            button_selectors = [
                "//button[contains(text(),'Agree')]",
                "//button[contains(text(),'Accept')]",
                "//button[contains(text(),'Connect')]",
                "//input[@type='submit'][@value='Agree']",
                "//input[@type='submit'][@value='Accept']",
                "//input[@type='submit'][@value='Connect']"
            ]

            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.logger.info(f"Найдена кнопка: {selector}")
                    button.click()
                    time.sleep(10)

                    if self._check_authentication_success():
                        self.logger.info("✅ Авторизация на phc.prontonetworks.com успешна")
                        return True

                except TimeoutException:
                    continue

        except Exception as e:
            self.logger.error(f"Ошибка авторизации phc.prontonetworks.com: {e}")

        return False

    def _try_conn4_auth(self):
        """Авторизация для conn4.com портала"""
        self.logger.info("Попытка авторизации на conn4.com...")

        try:
            # conn4.com обычно требует простого нажатия кнопки
            connect_selectors = [
                "//button[contains(text(),'Connect')]",
                "//button[contains(text(),'Continue')]",
                "//input[@type='submit']",
                "//a[contains(@href,'connect')]"
            ]

            for selector in connect_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    time.sleep(10)

                    if self._check_authentication_success():
                        self.logger.info("✅ Авторизация на conn4.com успешна")
                        return True

                except TimeoutException:
                    continue

        except Exception as e:
            self.logger.error(f"Ошибка авторизации conn4.com: {e}")

        return False

    def _check_authentication_success(self):
        """Проверка успешности авторизации"""
        try:
            # Проверяем доступность интернета
            test_urls = [
                "http://www.google.com",
                "http://connectivitycheck.gstatic.com/generate_204"
            ]

            for test_url in test_urls:
                try:
                    self.driver.get(test_url)
                    time.sleep(5)

                    current_url = self.driver.current_url

                    # Если мы попали на Google или другой внешний сайт, значит интернет доступен
                    if ("google.com" in current_url.lower() and "conn4.com" not in current_url.lower()) or \
                       ("gstatic.com" in current_url.lower()):
                        self.logger.info(f"✅ Интернет доступен: {current_url}")
                        return True

                except Exception:
                    continue

            # Проверяем наличие сообщений об успехе на текущей странице
            try:
                page_source = self.driver.page_source.lower()
                success_indicators = [
                    "success", "connected", "welcome", "internet access",
                    "you are now connected", "connection established"
                ]

                for indicator in success_indicators:
                    if indicator in page_source:
                        return True
            except Exception:
                pass

        except Exception as e:
            self.logger.debug(f"Ошибка проверки авторизации: {e}")

        return False

    def _debug_page_info(self):
        """Вывод отладочной информации о странице"""
        try:
            self.logger.info("=== ОТЛАДОЧНАЯ ИНФОРМАЦИЯ О СТРАНИЦЕ ===")
            self.logger.info(f"URL: {self.driver.current_url}")
            self.logger.info(f"Заголовок: {self.driver.title}")

            # Ищем все кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.logger.info(f"Найдено кнопок: {len(buttons)}")
            for i, button in enumerate(buttons[:5]):  # Показываем первые 5
                try:
                    text = button.text.strip()
                    if text:
                        self.logger.info(f"  Кнопка {i+1}: '{text}'")
                except:
                    pass

            # Ищем все ссылки
            links = self.driver.find_elements(By.TAG_NAME, "a")
            self.logger.info(f"Найдено ссылок: {len(links)}")
            for i, link in enumerate(links[:5]):  # Показываем первые 5
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href")
                    if text:
                        self.logger.info(f"  Ссылка {i+1}: '{text}' -> {href}")
                except:
                    pass

            # Ищем все формы
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.logger.info(f"Найдено форм: {len(forms)}")

        except Exception as e:
            self.logger.error(f"Ошибка получения отладочной информации: {e}")

    def save_screenshot(self, filename):
        """Сохранение скриншота для отладки"""
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"Скриншот сохранен: {filename}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения скриншота: {e}")

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome WebDriver закрыт")
            except Exception:
                pass

        # Восстанавливаем сетевую конфигурацию
        self.restore_network_routing()

    def run_full_authentication(self, username=None, password=None):
        """Полный процесс обнаружения и авторизации captive portal"""
        self.logger.info("=" * 70)
        self.logger.info("АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ CAPTIVE PORTAL ЧЕРЕЗ WSL")
        self.logger.info("=" * 70)

        try:
            # 1. Настройка принудительной маршрутизации
            if not self.setup_network_routing():
                return False

            # 2. Настройка Chrome WebDriver
            if not self.setup_chrome_driver():
                return False

            # 3. Обнаружение captive portal
            if not self.detect_captive_portal():
                self.logger.info("✅ Captive portal не обнаружен - интернет доступен")
                return True

            # 4. Попытка авторизации
            auth_success = self.authenticate_portal(username, password)

            if auth_success:
                self.logger.info("🎉 АВТОРИЗАЦИЯ НА CAPTIVE PORTAL УСПЕШНА!")
                self.save_screenshot("auth_success_final.png")
            else:
                self.logger.warning("❌ Авторизация не удалась")
                self.save_screenshot("auth_failed_final.png")

            return auth_success

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            return False
        finally:
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description='Консолидированный авторизатор captive порталов для WSL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # Базовый запуск (headless)
  %(prog)s --show-browser                     # С отображением браузера
  %(prog)s --username "user" --password "pass" # С учетными данными
  %(prog)s --debug                            # Отладочный режим

Требования:
  - WSL 2
  - Google Chrome в WSL
  - sudo права для настройки сети
  - pip install selenium webdriver-manager
        """
    )

    parser.add_argument('--router-ip', default='192.168.1.1',
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Таймаут операций в секундах (по умолчанию: 30)')
    parser.add_argument('--username', help='Имя пользователя для авторизации')
    parser.add_argument('--password', help='Пароль для авторизации')
    parser.add_argument('--show-browser', action='store_true',
                       help='Показать браузер (отключить headless режим)')
    parser.add_argument('--debug', action='store_true',
                       help='Включить отладочный режим')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Создание и запуск авторизатора
    authenticator = CaptivePortalWSLSelenium(
        router_ip=args.router_ip,
        timeout=args.timeout,
        headless=not args.show_browser
    )

    try:
        success = authenticator.run_full_authentication(
            username=args.username,
            password=args.password
        )
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        authenticator.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
