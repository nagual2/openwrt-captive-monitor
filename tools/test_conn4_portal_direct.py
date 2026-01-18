#!/usr/bin/env python3
"""
Прямое тестирование conn4.com captive portal
============================================

Скрипт для прямого обращения к conn4.com порталу, который мы обнаружили
в curl ответе с роутера.

Использование:
    wsl python3 tools/test_conn4_portal_direct.py
"""

import sys
import os
import time
import logging
from urllib.parse import urlparse, parse_qs

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium webdriver-manager")
    sys.exit(1)

# Проверяем, что мы в WSL
is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("❌ Этот скрипт должен запускаться только в WSL!")
    sys.exit(1)

class Conn4PortalTester:
    def __init__(self):
        self.driver = None

        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def setup_chrome_driver(self):
        """Настройка Chrome WebDriver"""
        self.logger.info("Настройка Chrome WebDriver...")

        try:
            options = Options()
            # Запускаем в видимом режиме для отладки
            # options.add_argument("--headless")  # Отключаем headless для отладки
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            # НЕ отключаем JavaScript - он нужен для conn4.com

            # Используем webdriver-manager
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)

            self.logger.info("✅ Chrome WebDriver настроен")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки Chrome: {e}")
            return False

    def test_conn4_portal(self):
        """Тестирование conn4.com портала"""
        # URL из curl ответа с роутера
        portal_url = "https://1096.rdr.conn4.com/ident?client_ip=10.72.192.213&client_mac=1824301B7A8F&site_id=1096&signature=2b73aa027f1d377f8cd6c3d35ce3cd7684a6283ed1ac3beb6aa8880b225ef0c8&loggedin=0&remembered_mac=0"

        self.logger.info(f"Переход на conn4.com портал...")
        self.logger.info(f"URL: {portal_url}")

        try:
            self.driver.get(portal_url)

            # Ждем загрузки JavaScript контента
            self.logger.info("Ожидание загрузки JavaScript контента...")

            # Ждем пока JavaScript создаст элементы на странице
            for i in range(30):  # Максимум 30 секунд
                time.sleep(1)

                # Проверяем, появились ли элементы
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")

                if len(inputs) > 0 or len(buttons) > 0:
                    self.logger.info(f"JavaScript загрузился за {i+1} секунд - найдено {len(inputs)} inputs и {len(buttons)} buttons")
                    break

                if i % 5 == 0:  # Каждые 5 секунд
                    self.logger.info(f"Ожидание JavaScript... {i+1}/30 сек")

            # Дополнительная пауза для завершения анимаций
            time.sleep(3)

            # Принудительно выполняем JavaScript для инициализации страницы
            try:
                self.driver.execute_script("if (typeof initPage === 'function') { initPage(); }")
                self.driver.execute_script("if (typeof loadContent === 'function') { loadContent(); }")
                self.driver.execute_script("document.dispatchEvent(new Event('DOMContentLoaded'));")
                time.sleep(2)
            except Exception as e:
                self.logger.debug(f"Ошибка выполнения JavaScript: {e}")

            current_url = self.driver.current_url
            page_title = self.driver.title

            self.logger.info(f"Текущий URL: {current_url}")
            self.logger.info(f"Заголовок: {page_title}")

            # Сохраняем скриншот
            self.driver.save_screenshot("conn4_portal_page.png")
            self.logger.info("Скриншот сохранен: conn4_portal_page.png")

            # Анализируем страницу
            self.analyze_page()

            # Пробуем авторизацию
            return self.try_authentication()

        except Exception as e:
            self.logger.error(f"❌ Ошибка доступа к порталу: {e}")
            return False

    def analyze_page(self):
        """Анализ страницы портала"""
        self.logger.info("=== АНАЛИЗ СТРАНИЦЫ ПОРТАЛА ===")

        try:
            # Ждем дополнительно для загрузки динамического контента
            time.sleep(5)

            # Ищем ВСЕ элементы input
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"Найдено всех input элементов: {len(all_inputs)}")

            for i, inp in enumerate(all_inputs):
                inp_type = inp.get_attribute("type") or "text"
                inp_name = inp.get_attribute("name") or ""
                inp_value = inp.get_attribute("value") or ""
                inp_id = inp.get_attribute("id") or ""
                inp_class = inp.get_attribute("class") or ""
                is_visible = inp.is_displayed()
                self.logger.info(f"  Input {i+1}: type='{inp_type}' name='{inp_name}' id='{inp_id}' class='{inp_class}' value='{inp_value}' visible={is_visible}")

            # Ищем ВСЕ кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            submit_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
            button_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='button']")

            all_buttons = buttons + submit_inputs + button_inputs
            self.logger.info(f"Найдено всех кнопок: {len(all_buttons)}")

            for i, btn in enumerate(all_buttons):
                text = btn.text.strip() or btn.get_attribute("value") or ""
                btn_type = btn.get_attribute("type") or ""
                btn_id = btn.get_attribute("id") or ""
                btn_class = btn.get_attribute("class") or ""
                onclick = btn.get_attribute("onclick") or ""
                is_visible = btn.is_displayed()
                is_enabled = btn.is_enabled()
                self.logger.info(f"  Кнопка {i+1}: text='{text}' type='{btn_type}' id='{btn_id}' class='{btn_class}' visible={is_visible} enabled={is_enabled}")
                if onclick:
                    self.logger.info(f"    onclick: {onclick}")

            # Ищем чекбоксы отдельно
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            self.logger.info(f"Найдено чекбоксов: {len(checkboxes)}")

            for i, checkbox in enumerate(checkboxes):
                name = checkbox.get_attribute("name") or ""
                checkbox_id = checkbox.get_attribute("id") or ""
                is_checked = checkbox.is_selected()
                is_visible = checkbox.is_displayed()
                self.logger.info(f"  Чекбокс {i+1}: name='{name}' id='{checkbox_id}' checked={is_checked} visible={is_visible}")

            # Ищем элементы с текстом "Get Free WiFi"
            wifi_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Get Free WiFi')]")
            self.logger.info(f"Найдено элементов с 'Get Free WiFi': {len(wifi_elements)}")

            for i, elem in enumerate(wifi_elements):
                tag = elem.tag_name
                text = elem.text.strip()
                elem_id = elem.get_attribute("id") or ""
                elem_class = elem.get_attribute("class") or ""
                is_visible = elem.is_displayed()
                is_enabled = elem.is_enabled() if hasattr(elem, 'is_enabled') else True
                self.logger.info(f"  WiFi элемент {i+1}: <{tag}> text='{text}' id='{elem_id}' class='{elem_class}' visible={is_visible} enabled={is_enabled}")

            # Ищем формы
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.logger.info(f"Найдено форм: {len(forms)}")

            for i, form in enumerate(forms):
                action = form.get_attribute("action") or ""
                method = form.get_attribute("method") or "GET"
                form_id = form.get_attribute("id") or ""
                self.logger.info(f"  Форма {i+1}: {method} {action} id='{form_id}'")

            # Выводим часть HTML для отладки
            page_source = self.driver.page_source
            self.logger.info(f"Размер HTML: {len(page_source)} символов")

            # Ищем ключевые слова в HTML
            keywords = ['get free wifi', 'checkbox', 'connect', 'continue', 'accept', 'agree', 'submit', 'button', 'input']
            for keyword in keywords:
                count = page_source.lower().count(keyword)
                if count > 0:
                    self.logger.info(f"  Найдено '{keyword}': {count} раз в HTML")

        except Exception as e:
            self.logger.error(f"Ошибка анализа страницы: {e}")

    def try_authentication(self):
        """Попытка авторизации"""
        self.logger.info("=== ПОПЫТКА АВТОРИЗАЦИИ ===")

        try:
            # Сначала ищем и отмечаем чекбоксы (галки)
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

            for i, checkbox in enumerate(checkboxes):
                if checkbox.is_displayed() and not checkbox.is_selected():
                    self.logger.info(f"Отмечаем чекбокс {i+1}")
                    try:
                        checkbox.click()
                        self.logger.info(f"✅ Чекбокс {i+1} отмечен")
                    except Exception as e:
                        self.logger.warning(f"Не удалось отметить чекбокс {i+1}: {e}")

            # Небольшая пауза после отметки чекбоксов
            time.sleep(2)

            # Теперь ищем кнопки для подключения
            connect_selectors = [
                # Поиск по конкретному тексту "Get Free WiFi"
                "//button[contains(text(), 'Get Free WiFi')]",
                "//input[@value='Get Free WiFi']",
                "//*[contains(text(), 'Get Free WiFi')]",

                # Поиск по тексту кнопки (общие варианты)
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wifi')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",

                # Поиск по типу
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//button[@type='button']",

                # Поиск по классам (часто используемые в conn4)
                "//button[contains(@class, 'btn')]",
                "//button[contains(@class, 'button')]",
                "//input[contains(@class, 'btn')]",

                # Поиск любых кликабельных элементов
                "//*[@onclick]",

                # Поиск по ID (если есть стандартные)
                "//button[@id]",
                "//input[@id and @type='submit']"
            ]

            for selector in connect_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.strip() or element.get_attribute("value") or element.get_attribute("id") or "Безымянная кнопка"
                            self.logger.info(f"Найдена кнопка: '{text}' ({selector})")

                            try:
                                element.click()
                                self.logger.info(f"✅ Кнопка '{text}' нажата")

                                time.sleep(10)

                                # Проверяем результат
                                new_url = self.driver.current_url
                                self.logger.info(f"Новый URL после клика: {new_url}")

                                # Сохраняем скриншот результата
                                self.driver.save_screenshot("conn4_after_click.png")
                                self.logger.info("Скриншот после клика: conn4_after_click.png")

                                # Проверяем успех
                                if self.check_success():
                                    return True

                            except Exception as e:
                                self.logger.warning(f"Ошибка клика по кнопке '{text}': {e}")
                                continue

                except Exception as e:
                    self.logger.debug(f"Ошибка с селектором {selector}: {e}")
                    continue

            self.logger.warning("Не найдены кнопки для авторизации")
            return False

        except Exception as e:
            self.logger.error(f"Ошибка авторизации: {e}")
            return False

    def check_success(self):
        """Проверка успешности авторизации"""
        try:
            # Проверяем изменение URL
            current_url = self.driver.current_url

            # Проверяем содержимое страницы
            page_source = self.driver.page_source.lower()

            success_indicators = [
                "success", "connected", "welcome", "internet access",
                "you are now connected", "connection established"
            ]

            for indicator in success_indicators:
                if indicator in page_source:
                    self.logger.info(f"✅ Найден индикатор успеха: {indicator}")
                    return True

            # Проверяем доступность интернета
            self.driver.get("http://www.google.com")
            time.sleep(5)

            final_url = self.driver.current_url
            if "google.com" in final_url and "conn4.com" not in final_url:
                self.logger.info("✅ Доступ к Google - авторизация успешна!")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Ошибка проверки успеха: {e}")
            return False

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome WebDriver закрыт")
            except:
                pass

    def run_test(self):
        """Запуск полного теста"""
        self.logger.info("=" * 60)
        self.logger.info("ТЕСТИРОВАНИЕ CONN4.COM CAPTIVE PORTAL")
        self.logger.info("=" * 60)

        try:
            if not self.setup_chrome_driver():
                return False

            success = self.test_conn4_portal()

            if success:
                self.logger.info("🎉 АВТОРИЗАЦИЯ НА CONN4.COM УСПЕШНА!")
            else:
                self.logger.warning("❌ Авторизация не удалась")

            return success

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            return False
        finally:
            self.cleanup()


def main():
    tester = Conn4PortalTester()

    try:
        success = tester.run_test()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
