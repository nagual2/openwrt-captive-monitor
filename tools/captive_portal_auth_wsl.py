#!/usr/bin/env python3
"""
Скрипт для автоматической авторизации на captive portal через WSL.
Использует Firefox в WSL с принудительной маршрутизацией через роутер.
"""

import time
import sys
import argparse
import logging
import subprocess
import os
from urllib.parse import urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.firefox.service import Service
    from selenium.webdriver.firefox.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium")
    sys.exit(1)

# Проверяем, что мы в WSL (опционально)
is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("⚠️ Рекомендуется запускать в WSL для корректной маршрутизации")

class CaptivePortalAuthenticatorWSL:
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

    def setup_network_routing(self):
        """Настройка принудительной маршрутизации через роутер"""
        self.logger.info(f"Настройка маршрутизации через роутер {self.router_ip}")

        try:
            # Проверяем права sudo
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
            if result.returncode != 0:
                self.logger.error("❌ Требуются права sudo для настройки маршрутизации")
                return False

            # Настраиваем DNS через роутер
            dns_config = f"""# Временная настройка для тестирования captive portal
nameserver {self.router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

            # Сохраняем оригинальный resolv.conf
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)

            # Устанавливаем новый resolv.conf
            with open('/tmp/resolv.conf.temp', 'w') as f:
                f.write(dns_config)
            subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.temp', '/etc/resolv.conf'], check=True)

            # Добавляем маршруты для тестовых хостов через роутер
            test_hosts = [
                "www.msftconnecttest.com",
                "connectivitycheck.gstatic.com",
                "clients3.google.com",
                "www.google.com",
                "8.8.8.8",
                "1.1.1.1"
            ]

            self.added_routes = []
            for host in test_hosts:
                try:
                    # Разрешаем IP через DNS
                    if not host.replace('.', '').isdigit():  # Если это не IP
                        result = subprocess.run(['dig', f'@{self.router_ip}', host, 'A', '+short'],
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0 and result.stdout.strip():
                            ip = result.stdout.strip().split('\n')[0]
                            if ip and '.' in ip:
                                host = ip

                    # Добавляем маршрут
                    cmd = ['sudo', 'ip', 'route', 'add', host, 'via', self.router_ip]
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        self.logger.info(f"✅ Маршрут добавлен: {host} via {self.router_ip}")
                        self.added_routes.append(host)
                    elif "File exists" in result.stderr:
                        self.logger.info(f"ℹ️ Маршрут уже существует: {host}")

                except Exception as e:
                    self.logger.debug(f"Ошибка добавления маршрута для {host}: {e}")

            self.logger.info("✅ Сетевая маршрутизация настроена")
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
            if hasattr(self, 'added_routes'):
                for host in self.added_routes:
                    try:
                        cmd = ['sudo', 'ip', 'route', 'del', host, 'via', self.router_ip]
                        subprocess.run(cmd, capture_output=True)
                    except Exception:
                        pass

            self.logger.info("✅ Сетевая конфигурация восстановлена")

        except Exception as e:
            self.logger.error(f"❌ Ошибка восстановления конфигурации: {e}")

    def setup_driver(self):
        """Настройка Firefox WebDriver в WSL"""
        self.logger.info("Настройка Firefox WebDriver...")

        try:
            # Проверяем наличие Firefox
            result = subprocess.run(['which', 'firefox'], capture_output=True)
            if result.returncode != 0:
                self.logger.error("❌ Firefox не установлен в WSL")
                self.logger.info("Установите: sudo apt update && sudo apt install firefox")
                return False

            # Настройка Firefox опций
            firefox_options = Options()

            if self.headless:
                firefox_options.add_argument("--headless")

            # Настройки для работы в WSL
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            firefox_options.add_argument("--disable-gpu")

            # Настройка профиля Firefox
            firefox_options.set_preference("network.proxy.type", 0)  # Прямое подключение
            firefox_options.set_preference("network.dns.disableIPv6", True)
            firefox_options.set_preference("permissions.default.image", 2)  # Блокировать изображения

            # Установка переменных окружения для WSL
            os.environ['DISPLAY'] = ':0'

            # Создание драйвера
            self.driver = webdriver.Firefox(options=firefox_options)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)

            self.logger.info("✅ Firefox WebDriver настроен успешно")
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

    def authenticate_portal(self):
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

            # Сохраняем скриншот портала
            self.save_screenshot("captive_portal_page.png")

            # Анализируем тип портала и выполняем авторизацию
            return self._perform_authentication()

        except Exception as e:
            self.logger.error(f"❌ Ошибка авторизации: {e}")
            return False

    def _perform_authentication(self):
        """Выполнение авторизации в зависимости от типа портала"""

        # 1. Попробуем найти простую кнопку "Connect" или "Continue"
        if self._try_simple_connect():
            return True

        # 2. Попробуем принять условия использования
        if self._try_terms_acceptance():
            return True

        self.logger.warning("⚠️ Не удалось определить метод авторизации")

        # Сохраняем скриншот для анализа
        self.save_screenshot("auth_failed_analysis.png")

        # Выводим информацию о странице для отладки
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
            "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
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
                    if ("google" in current_url.lower() and "conn4.com" not in current_url.lower()) or \
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

    def run_full_test(self):
        """Полный тест обнаружения и авторизации captive portal"""
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО ТЕСТИРОВАНИЯ CAPTIVE PORTAL АВТОРИЗАЦИИ (WSL)")
        self.logger.info("=" * 60)

        try:
            # 1. Настройка сетевой маршрутизации
            if not self.setup_network_routing():
                return False

            # 2. Настройка WebDriver
            if not self.setup_driver():
                return False

            # 3. Обнаружение captive portal
            if not self.detect_captive_portal():
                self.logger.info("Captive portal не обнаружен - тестирование завершено")
                return True

            # 4. Попытка авторизации
            auth_success = self.authenticate_portal()

            if auth_success:
                self.logger.info("✅ АВТОРИЗАЦИЯ НА CAPTIVE PORTAL УСПЕШНА!")
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

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver закрыт")
            except Exception:
                pass

        # Восстанавливаем сетевую конфигурацию
        self.restore_network_routing()

def main():
    parser = argparse.ArgumentParser(description='Автоматическая авторизация на captive portal в WSL')
    parser.add_argument('--router', default='192.168.1.1',
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Таймаут операций в секундах (по умолчанию: 30)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Запуск браузера в headless режиме')
    parser.add_argument('--show-browser', action='store_true',
                       help='Показать браузер (отключить headless режим)')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Создание и запуск аутентификатора
    authenticator = CaptivePortalAuthenticatorWSL(
        router_ip=args.router,
        timeout=args.timeout,
        headless=args.headless and not args.show_browser
    )

    try:
        success = authenticator.run_full_test()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        authenticator.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
