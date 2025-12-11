#!/usr/bin/env python3
"""
Скрипт для автоматической авторизации на captive portal с использованием Selenium.
Работает через тестовый роутер OpenWrt для тестирования функционала captive portal.
"""

import time
import sys
import argparse
import logging
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class CaptivePortalAuthenticator:
    def __init__(self, router_ip="192.168.1.1", timeout=30, headless=True):
        self.router_ip = router_ip
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self.portal_url = None

        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Настройка Chrome WebDriver"""
        self.logger.info("Настройка Chrome WebDriver...")

        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument("--headless")

            # Настройки для работы в ограниченной среде
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            # Отключение изображений для ускорения
            chrome_options.add_argument("--disable-images")

            # Настройка прокси через роутер (если нужно)
            # chrome_options.add_argument(f"--proxy-server=http://{self.router_ip}:8080")

            # Установка и запуск драйвера
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)

            self.logger.info("✅ Chrome WebDriver настроен успешно")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки WebDriver: {e}")
            return False

    def detect_captive_portal(self):
        """Обнаружение captive portal через connectivity check"""
        self.logger.info("Обнаружение captive portal...")

        test_urls = [
            "http://www.msftconnecttest.com/redirect",
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://clients3.google.com/generate_204",
            "http://www.google.com/"
        ]

        for url in test_urls:
            try:
                self.logger.info(f"Тестирование URL: {url}")
                self.driver.get(url)

                # Ждем загрузки страницы
                time.sleep(3)

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
            'portal', 'hotspot', 'wifi', 'guest', 'auth'
        ]

        for captive_domain in captive_domains:
            if captive_domain in domain:
                return True

        # Проверяем заголовок страницы
        title_lower = title.lower()
        captive_keywords = [
            'login', 'sign in', 'authentication', 'portal', 'hotspot',
            'wifi', 'internet access', 'terms', 'agreement', 'welcome'
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
            if any(keyword in page_source for keyword in ['connect', 'access', 'continue', 'agree']):
                return True

        except Exception:
            pass

        return False

    def authenticate_portal(self, credentials=None):
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

            # Анализируем тип портала и выполняем авторизацию
            return self._perform_authentication(credentials)

        except Exception as e:
            self.logger.error(f"❌ Ошибка авторизации: {e}")
            return False

    def _perform_authentication(self, credentials):
        """Выполнение авторизации в зависимости от типа портала"""

        # 1. Попробуем найти простую кнопку "Connect" или "Continue"
        if self._try_simple_connect():
            return True

        # 2. Попробуем авторизацию с учетными данными
        if credentials and self._try_credentials_auth(credentials):
            return True

        # 3. Попробуем принять условия использования
        if self._try_terms_acceptance():
            return True

        # 4. Попробуем социальную авторизацию
        if self._try_social_auth():
            return True

        self.logger.warning("⚠️ Не удалось определить метод авторизации")
        return False

    def _try_simple_connect(self):
        """Попытка простого подключения через кнопку"""
        self.logger.info("Попытка простого подключения...")

        # Возможные селекторы кнопок подключения
        connect_selectors = [
            "//button[contains(text(), 'Connect')]",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'Access')]",
            "//input[@type='submit'][contains(@value, 'Connect')]",
            "//input[@type='submit'][contains(@value, 'Continue')]",
            "//a[contains(text(), 'Connect')]",
            "//a[contains(text(), 'Continue')]",
            "#connect", "#continue", "#access",
            ".connect-btn", ".continue-btn", ".access-btn"
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
                time.sleep(5)

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

    def _try_credentials_auth(self, credentials):
        """Попытка авторизации с учетными данными"""
        self.logger.info("Попытка авторизации с учетными данными...")

        username = credentials.get('username', '')
        password = credentials.get('password', '')

        if not username or not password:
            self.logger.warning("Учетные данные не предоставлены")
            return False

        try:
            # Ищем поля ввода
            username_field = None
            password_field = None

            # Возможные селекторы для полей ввода
            username_selectors = [
                "input[name='username']", "input[name='user']", "input[name='login']",
                "input[name='email']", "input[type='text']", "#username", "#user", "#login"
            ]

            password_selectors = [
                "input[name='password']", "input[type='password']", "#password"
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
                submit_button = None
                submit_selectors = [
                    "input[type='submit']", "button[type='submit']",
                    "//button[contains(text(), 'Login')]",
                    "//button[contains(text(), 'Sign In')]"
                ]

                for selector in submit_selectors:
                    try:
                        if selector.startswith("//"):
                            submit_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue

                if submit_button:
                    submit_button.click()
                    time.sleep(5)

                    if self._check_authentication_success():
                        self.logger.info("✅ Авторизация с учетными данными успешна")
                        return True

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
                "//input[@type='checkbox'][contains(@name, 'agree')]",
                "//input[@type='checkbox'][contains(@name, 'terms')]",
                "//input[@type='checkbox'][contains(@name, 'accept')]"
            ]

            checkboxes_found = False
            for selector in checkbox_selectors:
                try:
                    if selector.startswith("//"):
                        checkboxes = self.driver.find_elements(By.XPATH, selector)
                    else:
                        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for checkbox in checkboxes:
                        if not checkbox.is_selected():
                            checkbox.click()
                            checkboxes_found = True
                            self.logger.info("Отмечен чекбокс согласия")

                except Exception:
                    continue

            # Ищем кнопку принятия условий
            accept_selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//button[contains(text(), 'I Agree')]",
                "//input[@type='submit'][contains(@value, 'Accept')]",
                "//input[@type='submit'][contains(@value, 'Agree')]"
            ]

            for selector in accept_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    time.sleep(5)

                    if self._check_authentication_success():
                        self.logger.info("✅ Принятие условий успешно")
                        return True

                except TimeoutException:
                    continue

        except Exception as e:
            self.logger.error(f"Ошибка принятия условий: {e}")

        return False

    def _try_social_auth(self):
        """Попытка социальной авторизации"""
        self.logger.info("Попытка социальной авторизации...")

        # Ищем кнопки социальных сетей
        social_selectors = [
            "//button[contains(text(), 'Facebook')]",
            "//button[contains(text(), 'Google')]",
            "//a[contains(@href, 'facebook')]",
            "//a[contains(@href, 'google')]",
            ".facebook-btn", ".google-btn", ".social-btn"
        ]

        for selector in social_selectors:
            try:
                if selector.startswith("//"):
                    element = self.driver.find_element(By.XPATH, selector)
                elif selector.startswith("."):
                    element = self.driver.find_element(By.CLASS_NAME, selector[1:])
                else:
                    continue

                self.logger.info(f"Найдена кнопка социальной авторизации: {selector}")
                # Для демонстрации не кликаем по социальным кнопкам
                # element.click()

            except NoSuchElementException:
                continue

        return False

    def _check_authentication_success(self):
        """Проверка успешности авторизации"""
        try:
            # Проверяем изменение URL
            current_url = self.driver.current_url

            # Проверяем доступность интернета
            test_urls = [
                "http://www.google.com",
                "http://connectivitycheck.gstatic.com/generate_204"
            ]

            for test_url in test_urls:
                try:
                    self.driver.get(test_url)
                    time.sleep(3)

                    # Если мы попали на Google или получили 204, значит интернет доступен
                    if "google" in self.driver.current_url.lower() or self.driver.title:
                        return True

                except Exception:
                    continue

            # Проверяем наличие сообщений об успехе
            success_indicators = [
                "success", "connected", "welcome", "internet access",
                "you are now connected", "connection established"
            ]

            page_source = self.driver.page_source.lower()
            for indicator in success_indicators:
                if indicator in page_source:
                    return True

        except Exception as e:
            self.logger.debug(f"Ошибка проверки авторизации: {e}")

        return False

    def save_screenshot(self, filename="captive_portal_screenshot.png"):
        """Сохранение скриншота для отладки"""
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"Скриншот сохранен: {filename}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения скриншота: {e}")

    def get_page_info(self):
        """Получение информации о текущей странице"""
        try:
            info = {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'forms': len(self.driver.find_elements(By.TAG_NAME, "form")),
                'inputs': len(self.driver.find_elements(By.TAG_NAME, "input")),
                'buttons': len(self.driver.find_elements(By.TAG_NAME, "button"))
            }
            return info
        except Exception:
            return {}

    def run_full_test(self, credentials=None, save_screenshots=False):
        """Полный тест обнаружения и авторизации captive portal"""
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО ТЕСТИРОВАНИЯ CAPTIVE PORTAL АВТОРИЗАЦИИ")
        self.logger.info("=" * 60)

        try:
            # 1. Настройка WebDriver
            if not self.setup_driver():
                return False

            # 2. Обнаружение captive portal
            if not self.detect_captive_portal():
                self.logger.info("Captive portal не обнаружен - тестирование завершено")
                return True

            # 3. Сохранение скриншота портала
            if save_screenshots:
                self.save_screenshot("captive_portal_detected.png")

            # 4. Получение информации о странице
            page_info = self.get_page_info()
            self.logger.info(f"Информация о портале: {page_info}")

            # 5. Попытка авторизации
            auth_success = self.authenticate_portal(credentials)

            # 6. Сохранение скриншота результата
            if save_screenshots:
                result_filename = "auth_success.png" if auth_success else "auth_failed.png"
                self.save_screenshot(result_filename)

            if auth_success:
                self.logger.info("✅ АВТОРИЗАЦИЯ НА CAPTIVE PORTAL УСПЕШНА!")
            else:
                self.logger.warning("❌ Авторизация не удалась")

            return auth_success

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            return False

        finally:
            self.cleanup()

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver закрыт")
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description='Автоматическая авторизация на captive portal')
    parser.add_argument('--router', default='192.168.1.1',
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Таймаут операций в секундах (по умолчанию: 30)')
    parser.add_argument('--username', help='Имя пользователя для авторизации')
    parser.add_argument('--password', help='Пароль для авторизации')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Запуск браузера в headless режиме')
    parser.add_argument('--show-browser', action='store_true',
                       help='Показать браузер (отключить headless режим)')
    parser.add_argument('--screenshots', action='store_true',
                       help='Сохранять скриншоты для отладки')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Подготовка учетных данных
    credentials = None
    if args.username and args.password:
        credentials = {
            'username': args.username,
            'password': args.password
        }

    # Создание и запуск аутентификатора
    authenticator = CaptivePortalAuthenticator(
        router_ip=args.router,
        timeout=args.timeout,
        headless=args.headless and not args.show_browser
    )

    try:
        success = authenticator.run_full_test(
            credentials=credentials,
            save_screenshots=args.screenshots
        )
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        authenticator.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
