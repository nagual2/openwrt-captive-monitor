#!/usr/bin/env python3
"""
Минимальная авторизация на captive портале conn4.com
Только функционал авторизации, без отладки и артефактов
Запускается по cron каждую минуту, проверяет что не запущен
"""

import sys
import os
import time
import logging
import fcntl
import pickle
import json

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium")
    sys.exit(1)

# Используем tmpfs для логов и куков (экономия eMMC)
RUNTIME_DIR = f"/run/user/{os.getuid()}"
if not os.path.exists(RUNTIME_DIR):
    RUNTIME_DIR = "/tmp"

LOG_FILE = os.path.join(RUNTIME_DIR, "captive_portal_auth.log")
LOCK_FILE = os.path.join(RUNTIME_DIR, "captive_portal_auth.lock")
COOKIES_FILE = os.path.join(RUNTIME_DIR, "captive_portal_cookies.pkl")

# Настройка логирования (один handler - только файл)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Файл блокировки для предотвращения множественного запуска
LOCK_FILE = '/tmp/captive_portal_auth.lock'


class SingleInstanceLock:
    """Блокировка для предотвращения множественного запуска"""
    
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.fp = None
    
    def __enter__(self):
        try:
            self.fp = open(self.lock_file, 'w')
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            return self
        except IOError:
            logger.info("Скрипт уже запущен, выход")
            sys.exit(0)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp:
            try:
                fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
                self.fp.close()
                os.remove(self.lock_file)
            except:
                pass


class CaptivePortalAuth:
    """Минимальная авторизация на captive портале"""

    def __init__(self):
        self.driver = None

    def save_cookies(self):
        """Сохранение куков портала conn4.com в файл"""
        if not self.driver:
            return
        
        try:
            cookies = self.driver.get_cookies()
            
            # Фильтруем только куки портала conn4.com
            portal_cookies = [c for c in cookies if 'conn4.com' in c.get('domain', '')]
            
            if not portal_cookies:
                logger.info("Куки портала не найдены для сохранения")
                return
            
            # Сохраняем в pickle
            with open(COOKIES_FILE, 'wb') as f:
                pickle.dump(portal_cookies, f)
            
            logger.info(f"✅ Куки портала сохранены ({len(portal_cookies)} шт.)")
            
            # Логируем важные куки
            for cookie in portal_cookies:
                if 'session' in cookie.get('name', '').lower() or 'PHPSESSID' in cookie.get('name', ''):
                    logger.info(f"  Cookie: {cookie['name']}={cookie['value'][:20]}...")
        
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения куков: {e}")

    def load_cookies(self):
        """Загрузка куков портала из файла"""
        if not os.path.exists(COOKIES_FILE):
            logger.info("Файл куков не найден")
            return False
        
        try:
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            
            # Проверяем возраст файла куков
            file_age = time.time() - os.path.getmtime(COOKIES_FILE)
            logger.info(f"Файл куков найден (возраст: {int(file_age/60)} мин, {len(cookies)} шт.)")
            
            # Переходим на портал для загрузки куков
            # Selenium требует быть на том же домене
            portal_domain = None
            for cookie in cookies:
                domain = cookie.get('domain', '').lstrip('.')
                if 'conn4.com' in domain:
                    portal_domain = domain
                    break
            
            if portal_domain:
                logger.info(f"Переход на портал для загрузки куков: {portal_domain}")
                self.driver.get(f"https://{portal_domain}")
                time.sleep(2)
                
                # Загружаем куки
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"Не удалось загрузить cookie {cookie.get('name')}: {e}")
                
                logger.info(f"✅ Куки загружены в браузер")
                return True
            else:
                logger.warning("Домен портала не найден в куках")
                return False
        
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки куков: {e}")
            # Удаляем поврежденный файл
            try:
                os.remove(COOKIES_FILE)
            except:
                pass
            return False

    def send_keepalive(self):
        """Отправка keepalive для обновления куков на сервере"""
        try:
            logger.info("Отправка keepalive для обновления сессии...")
            
            # Переходим на портал для обновления сессии
            self.driver.get("https://1096.rdr.conn4.com/")
            time.sleep(2)
            
            # Сохраняем куки СРАЗУ после загрузки портала
            self.save_cookies()
            
            # Проверяем авторизацию через msftconnecttest (как в detect_portal)
            logger.info("Проверка активности сессии...")
            self.driver.get("http://www.msftconnecttest.com/redirect")
            time.sleep(3)
            
            current_url = self.driver.current_url
            logger.info(f"URL после проверки: {current_url}")
            
            # Если редирект на msn.com - сессия активна
            if "msn.com" in current_url.lower() or "microsoft.com" in current_url.lower():
                logger.info("✅ Keepalive успешен, сессия активна")
                return True
            # Если редирект на портал - сессия истекла
            elif "conn4.com" in current_url.lower():
                logger.warning(f"⚠️  Keepalive не удался, требуется новая авторизация")
                return False
            else:
                logger.warning(f"⚠️  Неожиданный URL после keepalive: {current_url}")
                return False
        
        except TimeoutException:
            # Таймаут - портал не отвечает, завершаем скрипт
            logger.error(f"❌ Ошибка keepalive: таймаут при обращении к порталу")
            return None  # Специальное значение для завершения скрипта
        
        except Exception as e:
            # Другие ошибки - логируем только тип без stacktrace
            error_type = type(e).__name__
            logger.error(f"❌ Ошибка keepalive: {error_type}")
            return None  # Специальное значение для завершения скрипта

    def setup_chrome(self):
        """Настройка Chrome WebDriver"""
        logger.info("Настройка Chrome...")

        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Отключаем изображения для ускорения
            options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2
            })

            # Ищем Chrome binary
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium"
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    logger.info(f"Chrome binary: {path}")
                    break

            # Ищем chromedriver
            driver_paths = [
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver"
            ]
            service = None
            for path in driver_paths:
                if os.path.exists(path):
                    service = Service(path)
                    logger.info(f"ChromeDriver: {path}")
                    break
            
            if not service:
                service = Service()  # Selenium Manager
                logger.info("Используем Selenium Manager для chromedriver")

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Chrome настроен")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка настройки Chrome: {e}")
            return False

    def detect_portal(self):
        """Обнаружение captive портала с retry логикой"""
        logger.info("Проверка авторизации...")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Проверяем редирект с msftconnecttest
                logger.info(f"Проверка: http://www.msftconnecttest.com/redirect (попытка {attempt}/{max_retries})")
                self.driver.get("http://www.msftconnecttest.com/redirect")
                time.sleep(5)
                
                current_url = self.driver.current_url
                logger.info(f"Текущий URL: {current_url}")

                # Проверка на уже авторизованное состояние (редирект на msn.com)
                if "msn.com" in current_url.lower() or "microsoft.com" in current_url.lower():
                    logger.info("✅ Уже авторизованы! (редирект на MSN)")
                    return False

                # Проверка на captive portal (редирект на conn4.com)
                if "conn4.com" in current_url.lower():
                    logger.info(f"⚠️  Обнаружен портал: {current_url}")
                    return True

                # Если редирект на другой сайт (не conn4 и не msn)
                logger.info(f"⚠️  Неожиданный редирект: {current_url}")
                return False

            except TimeoutException as e:
                # Логируем только краткое сообщение без stacktrace
                logger.warning(f"⚠️  Таймаут при проверке портала (попытка {attempt}/{max_retries})")
                if attempt < max_retries:
                    logger.info(f"Повторная попытка через 3 секунды...")
                    time.sleep(3)
                    continue
                else:
                    logger.error(f"❌ Портал не ответил после {max_retries} попыток")
                    return False
            
            except Exception as e:
                # Логируем только тип ошибки без stacktrace
                error_type = type(e).__name__
                logger.error(f"❌ Ошибка проверки портала (попытка {attempt}/{max_retries}): {error_type}")
                if attempt < max_retries:
                    logger.info(f"Повторная попытка через 3 секунды...")
                    time.sleep(3)
                    continue
                else:
                    logger.error(f"❌ Не удалось проверить портал после {max_retries} попыток")
                    return False
        
        return False

    def click_checkboxes(self):
        """Отметка всех чекбоксов"""
        logger.info("Поиск чекбоксов...")

        try:
            # Сначала пробуем переключиться на iframe
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                logger.info(f"Найдено iframe: {len(iframes)}")
                
                for i, iframe in enumerate(iframes):
                    try:
                        self.driver.switch_to.frame(iframe)
                        logger.info(f"Переключились на iframe {i+1}")
                        
                        # Проверяем наличие контента
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if body_text:
                            logger.info(f"Контент в iframe {i+1}: {body_text[:100]}")
                            break
                    except:
                        self.driver.switch_to.default_content()
                        continue
            except Exception as e:
                logger.warning(f"Ошибка переключения на iframe: {e}")
            
            # Ищем все чекбоксы
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            if not checkboxes:
                logger.info("Чекбоксы не найдены")
                return

            logger.info(f"Найдено чекбоксов: {len(checkboxes)}")

            # Отмечаем все чекбоксы
            for i, checkbox in enumerate(checkboxes):
                try:
                    if not checkbox.is_selected():
                        # Прокручиваем к чекбоксу
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", 
                            checkbox
                        )
                        time.sleep(0.5)
                        
                        # Пробуем кликнуть
                        try:
                            checkbox.click()
                            logger.info(f"✅ Чекбокс {i+1} отмечен")
                        except:
                            # Если не получилось, используем JavaScript
                            self.driver.execute_script(
                                "arguments[0].checked = true; "
                                "arguments[0].dispatchEvent(new Event('change'));", 
                                checkbox
                            )
                            logger.info(f"✅ Чекбокс {i+1} отмечен через JS")
                except Exception as e:
                    logger.warning(f"Ошибка отметки чекбокса {i+1}: {e}")

            time.sleep(1)

        except Exception as e:
            logger.error(f"Ошибка обработки чекбоксов: {e}")

    def click_connect_button(self):
        """Поиск и клик по кнопке подключения"""
        logger.info("Поиск кнопки подключения...")

        # Ждём загрузки страницы
        time.sleep(3)

        # Список селекторов для поиска кнопки
        selectors = [
            # По тексту
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free wi-fi')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
            # По типу
            "//button[@type='submit']",
            "//input[@type='submit']",
            # По классу
            "//button[contains(@class, 'btn')]",
            "//button[contains(@class, 'button')]",
            # Любые кнопки
            "//button"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.strip() or element.get_attribute("value") or element.get_attribute("id") or "Кнопка"
                        logger.info(f"Найдена кнопка: '{text}' (selector: {selector[:50]}...)")

                        # Прокручиваем к кнопке
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", 
                            element
                        )
                        time.sleep(0.5)

                        # Выходим из iframe перед сохранением куков
                        self.driver.switch_to.default_content()
                        
                        # Сохраняем куки портала ПЕРЕД кликом
                        # (пока браузер еще на conn4.com)
                        self.save_cookies()
                        
                        # Возвращаемся в iframe для клика
                        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                        if iframes:
                            self.driver.switch_to.frame(iframes[0])
                        
                        # Кликаем
                        try:
                            element.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", element)
                        
                        logger.info(f"✅ Кнопка '{text}' нажата")
                        time.sleep(8)  # Увеличено время ожидания

                        # Проверяем результат
                        new_url = self.driver.current_url
                        logger.info(f"URL после клика: {new_url}")

                        # Проверка успеха
                        if "conn4.com" not in new_url.lower():
                            logger.info("✅ Авторизация успешна!")
                            return True

            except Exception as e:
                logger.debug(f"Селектор {selector[:50]}: {e}")
                continue

        logger.warning("Кнопка подключения не найдена")
        
        # Выводим список всех найденных элементов для отладки
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"Всего кнопок на странице: {len(all_buttons)}")
            for i, btn in enumerate(all_buttons[:5]):  # Первые 5
                try:
                    logger.info(f"  Кнопка {i+1}: text='{btn.text[:50]}' class='{btn.get_attribute('class')}'")
                except:
                    pass
        except:
            pass
        
        return False

    def authenticate(self):
        """Основной процесс авторизации с поддержкой куков"""
        try:
            # 1. Настройка Chrome
            if not self.setup_chrome():
                return False

            # 2. Проверка портала БЕЗ куков (чистая проверка)
            portal_detected = self.detect_portal()
            
            if not portal_detected:
                # ✅ Уже авторизованы
                logger.info("Авторизация активна")
                
                # Загружаем куки из файла (если есть)
                cookies_loaded = self.load_cookies()
                
                if cookies_loaded:
                    # Отправляем keepalive для обновления куков
                    logger.info("Отправка keepalive для обновления куков...")
                    keepalive_result = self.send_keepalive()
                    
                    # Если keepalive вернул None - критическая ошибка, завершаем
                    if keepalive_result is None:
                        logger.error("❌ Критическая ошибка keepalive, завершение скрипта")
                        return False
                else:
                    # Куков нет - сохраняем текущие с портала
                    logger.info("Сохранение куков с портала...")
                    try:
                        self.driver.get("https://1096.rdr.conn4.com/")
                        time.sleep(3)
                        self.save_cookies()
                    except Exception as e:
                        logger.warning(f"Не удалось сохранить куки: {e}")
                
                return True

            # 3. ❌ Портал обнаружен - нужна полная авторизация
            logger.info("⚠️  Требуется полная авторизация")
            
            # Удаляем старые куки
            if os.path.exists(COOKIES_FILE):
                logger.info("Удаление старых куков...")
                os.remove(COOKIES_FILE)

            # 4. Отметка чекбоксов
            self.click_checkboxes()

            # 5. Клик по кнопке подключения (куки сохраняются внутри)
            if self.click_connect_button():
                logger.info("✅ Авторизация завершена успешно")
                # Куки уже сохранены в click_connect_button()
                return True
            else:
                logger.error("❌ Не удалось авторизоваться")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка авторизации: {e}")
            return False

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                
                # Принудительная очистка дочерних процессов
                try:
                    import subprocess
                    import signal
                    
                    # Убиваем все chromedriver процессы текущего пользователя
                    subprocess.run(['pkill', '-9', '-f', 'chromedriver'], 
                                   stderr=subprocess.DEVNULL, check=False)
                    
                    # Убиваем все headless chrome процессы текущего пользователя
                    subprocess.run(['pkill', '-9', '-f', 'google-chrome.*headless'], 
                                   stderr=subprocess.DEVNULL, check=False)
                except:
                    pass


def main():
    """Точка входа"""
    # Проверка единственного экземпляра
    with SingleInstanceLock(LOCK_FILE):
        logger.info("=== Проверка captive портала ===")
        
        auth = CaptivePortalAuth()
        success = auth.authenticate()
        
        if success:
            logger.info("=== Проверка завершена успешно ===")
        else:
            logger.error("=== Проверка завершена с ошибкой ===")
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
