#!/usr/bin/env python3
"""
Оптимизированная авторизация на captive портале conn4.com
- Проверка срока жизни cookies перед запуском Chrome
- Легкая проверка подключения через curl
- Запуск Chrome только когда действительно нужно
"""

import sys
import os
import time
import logging
import fcntl
import pickle
import json
import subprocess
from datetime import datetime, timedelta

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

# Пути
RUNTIME_DIR = os.environ.get("RUNTIME_DIR", f"/run/user/{os.getuid()}")
if not os.path.exists(RUNTIME_DIR):
    RUNTIME_DIR = "/tmp"

LOG_FILE = os.environ.get("LOG_FILE", os.path.join(RUNTIME_DIR, "captive_portal_auth.log"))
LOCK_FILE = os.environ.get("LOCK_FILE", os.path.join(RUNTIME_DIR, "captive_portal_auth.lock"))
COOKIES_FILE = os.environ.get("COOKIES_FILE", os.path.join(RUNTIME_DIR, "captive_portal_cookies.pkl"))
COOKIES_META_FILE = os.environ.get("COOKIES_META_FILE", os.path.join(RUNTIME_DIR, "captive_portal_cookies_meta.json"))

# Настройки времени жизни cookies (в секундах)
COOKIE_TTL = 3600  # 1 час - время жизни cookies
COOKIE_REFRESH_BEFORE = 300  # 5 минут - обновлять за 5 мин до истечения

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


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


def check_internet_lightweight():
    """Легкая проверка подключения без Chrome (через curl)"""
    try:
        logger.info("Легкая проверка подключения (curl)...")
        # Используем -I для получения только заголовков и -w для финального URL
        result = subprocess.run(
            ['curl', '-s', '-I', '-L', '-m', '5', '-w', '%{url_effective}',
             'http://www.msftconnecttest.com/redirect'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Финальный URL будет в последней строке после заголовков
        lines = result.stdout.strip().split('\n')
        final_url = lines[-1] if lines else ""
        
        logger.info(f"curl финальный URL: {final_url}")
        
        # Если редирект на msn.com или microsoft.com - авторизованы
        if "msn.com" in final_url.lower() or "microsoft.com" in final_url.lower():
            logger.info("✅ Подключение активно (curl)")
            return True
        # Если редирект на conn4.com - captive portal
        elif "conn4.com" in final_url.lower():
            logger.info("⚠️  Обнаружен captive portal (curl)")
            return False
        else:
            # Неожиданный результат - нужна проверка через Chrome
            logger.info(f"⚠️  Неожиданный URL, требуется проверка (curl)")
            return False
    except Exception as e:
        logger.warning(f"Ошибка curl проверки: {e}")
        return False


def get_cookie_metadata():
    """Получить метаданные cookies"""
    if not os.path.exists(COOKIES_META_FILE):
        return None
    
    try:
        with open(COOKIES_META_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения метаданных: {e}")
        return None


def save_cookie_metadata(created_at=None, ttl=COOKIE_TTL):
    """Сохранить метаданные cookies"""
    try:
        metadata = {
            'created_at': created_at or time.time(),
            'ttl': ttl,
            'expires_at': (created_at or time.time()) + ttl
        }
        with open(COOKIES_META_FILE, 'w') as f:
            json.dump(metadata, f)
        logger.info(f"Метаданные cookies сохранены (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Ошибка сохранения метаданных: {e}")


def are_cookies_valid():
    """Проверить валидность cookies по времени"""
    metadata = get_cookie_metadata()
    
    if not metadata:
        logger.info("Метаданные cookies не найдены")
        return False
    
    if not os.path.exists(COOKIES_FILE):
        logger.info("Файл cookies не найден")
        return False
    
    now = time.time()
    expires_at = metadata.get('expires_at', 0)
    refresh_at = expires_at - COOKIE_REFRESH_BEFORE
    
    age = now - metadata.get('created_at', 0)
    time_until_expiry = expires_at - now
    
    logger.info(f"Cookies: возраст {int(age/60)}м, истекают через {int(time_until_expiry/60)}м")
    
    # Если до истечения меньше COOKIE_REFRESH_BEFORE - нужно обновить
    if now >= refresh_at:
        logger.info("⚠️  Cookies скоро истекут, требуется обновление")
        return False
    
    logger.info("✅ Cookies валидны")
    return True


class CaptivePortalAuth:
    """Оптимизированная авторизация на captive портале"""

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
            
            # Сохраняем метаданные
            save_cookie_metadata()
            
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
            
            metadata = get_cookie_metadata()
            if metadata:
                age = int((time.time() - metadata.get('created_at', 0)) / 60)
                logger.info(f"Файл куков найден (возраст: {age} мин, {len(cookies)} шт.)")
            
            # Переходим на портал для загрузки куков
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
            # Удаляем поврежденные файлы
            try:
                os.remove(COOKIES_FILE)
                os.remove(COOKIES_META_FILE)
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
            
            # Проверяем авторизацию
            logger.info("Проверка активности сессии...")
            self.driver.get("http://www.msftconnecttest.com/redirect")
            time.sleep(3)
            
            current_url = self.driver.current_url
            logger.info(f"URL после проверки: {current_url}")
            
            if "msn.com" in current_url.lower() or "microsoft.com" in current_url.lower():
                logger.info("✅ Keepalive успешен, сессия активна")
                return True
            elif "conn4.com" in current_url.lower():
                logger.warning(f"⚠️  Keepalive не удался, требуется новая авторизация")
                return False
            else:
                logger.warning(f"⚠️  Неожиданный URL после keepalive: {current_url}")
                return False
        
        except TimeoutException:
            logger.error(f"❌ Ошибка keepalive: таймаут при обращении к порталу")
            return None
        
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"❌ Ошибка keepalive: {error_type}")
            return None

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
                service = Service()
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
                logger.info(f"Проверка: http://www.msftconnecttest.com/redirect (попытка {attempt}/{max_retries})")
                self.driver.get("http://www.msftconnecttest.com/redirect")
                time.sleep(5)
                
                current_url = self.driver.current_url
                logger.info(f"Текущий URL: {current_url}")

                if "msn.com" in current_url.lower() or "microsoft.com" in current_url.lower():
                    logger.info("✅ Уже авторизованы! (редирект на MSN)")
                    return False

                if "conn4.com" in current_url.lower():
                    logger.info(f"⚠️  Обнаружен портал: {current_url}")
                    return True

                logger.info(f"⚠️  Неожиданный редирект: {current_url}")
                return False

            except TimeoutException as e:
                logger.warning(f"⚠️  Таймаут при проверке портала (попытка {attempt}/{max_retries})")
                if attempt < max_retries:
                    logger.info(f"Повторная попытка через 3 секунды...")
                    time.sleep(3)
                    continue
                else:
                    logger.error(f"❌ Портал не ответил после {max_retries} попыток")
                    return False
            
            except Exception as e:
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
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                logger.info(f"Найдено iframe: {len(iframes)}")
                
                for i, iframe in enumerate(iframes):
                    try:
                        self.driver.switch_to.frame(iframe)
                        logger.info(f"Переключились на iframe {i+1}")
                        
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if body_text:
                            logger.info(f"Контент в iframe {i+1}: {body_text[:100]}")
                            break
                    except:
                        self.driver.switch_to.default_content()
                        continue
            except Exception as e:
                logger.warning(f"Ошибка переключения на iframe: {e}")
            
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            if not checkboxes:
                logger.info("Чекбоксы не найдены")
                return

            logger.info(f"Найдено чекбоксов: {len(checkboxes)}")

            for i, checkbox in enumerate(checkboxes):
                try:
                    if not checkbox.is_selected():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", 
                            checkbox
                        )
                        time.sleep(0.5)
                        
                        try:
                            checkbox.click()
                            logger.info(f"✅ Чекбокс {i+1} отмечен")
                        except:
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

        time.sleep(3)

        selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free wi-fi')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(@class, 'btn')]",
            "//button[contains(@class, 'button')]",
            "//button"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.strip() or element.get_attribute("value") or element.get_attribute("id") or "Кнопка"
                        logger.info(f"Найдена кнопка: '{text}' (selector: {selector[:50]}...)")

                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", 
                            element
                        )
                        time.sleep(0.5)

                        self.driver.switch_to.default_content()
                        self.save_cookies()
                        
                        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                        if iframes:
                            self.driver.switch_to.frame(iframes[0])
                        
                        try:
                            element.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", element)
                        
                        logger.info(f"✅ Кнопка '{text}' нажата")
                        time.sleep(8)

                        new_url = self.driver.current_url
                        logger.info(f"URL после клика: {new_url}")

                        if "conn4.com" not in new_url.lower():
                            logger.info("✅ Авторизация успешна!")
                            return True

            except Exception as e:
                logger.debug(f"Селектор {selector[:50]}: {e}")
                continue

        logger.warning("Кнопка подключения не найдена")
        
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"Всего кнопок на странице: {len(all_buttons)}")
            for i, btn in enumerate(all_buttons[:5]):
                try:
                    logger.info(f"  Кнопка {i+1}: text='{btn.text[:50]}' class='{btn.get_attribute('class')}'")
                except:
                    pass
        except:
            pass
        
        return False

    def authenticate(self):
        """Основной процесс авторизации с оптимизацией"""
        try:
            # 1. Настройка Chrome
            if not self.setup_chrome():
                return False

            # 2. Проверка портала
            portal_detected = self.detect_portal()
            
            if not portal_detected:
                logger.info("Авторизация активна")
                
                cookies_loaded = self.load_cookies()
                
                if cookies_loaded:
                    logger.info("Отправка keepalive для обновления куков...")
                    keepalive_result = self.send_keepalive()
                    
                    if keepalive_result is None:
                        logger.error("❌ Критическая ошибка keepalive, завершение скрипта")
                        return False
                else:
                    logger.info("Сохранение куков с портала...")
                    try:
                        self.driver.get("https://1096.rdr.conn4.com/")
                        time.sleep(3)
                        self.save_cookies()
                    except Exception as e:
                        logger.warning(f"Не удалось сохранить куки: {e}")
                
                return True

            logger.info("⚠️  Требуется полная авторизация")
            
            if os.path.exists(COOKIES_FILE):
                logger.info("Удаление старых куков...")
                os.remove(COOKIES_FILE)
            if os.path.exists(COOKIES_META_FILE):
                os.remove(COOKIES_META_FILE)

            self.click_checkboxes()

            if self.click_connect_button():
                logger.info("✅ Авторизация завершена успешно")
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
                
                try:
                    import subprocess
                    subprocess.run(['pkill', '-9', '-f', 'chromedriver'], 
                                   stderr=subprocess.DEVNULL, check=False)
                    subprocess.run(['pkill', '-9', '-f', 'google-chrome.*headless'], 
                                   stderr=subprocess.DEVNULL, check=False)
                except:
                    pass


import signal

# Флаг для graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    global shutdown_flag
    logger.info(f"Получен сигнал {signum}, завершение...")
    shutdown_flag = True

def run_check_cycle():
    """Одна итерация проверки"""
    logger.info("=== Проверка captive портала (оптимизированная) ===")
    
    # 1. Легкая проверка подключения (без Chrome)
    if check_internet_lightweight():
        # 2. Проверка валидности cookies
        if are_cookies_valid():
            logger.info("✅ Cookies валидны, Chrome не требуется")
            logger.info("=== Проверка завершена (быстрый путь) ===")
            return True
        else:
            logger.info("⚠️  Cookies требуют обновления, запуск Chrome...")
    else:
        logger.info("⚠️  Подключение неактивно, запуск Chrome...")
    
    # 3. Полная проверка с Chrome (только если нужно)
    auth = CaptivePortalAuth()
    success = auth.authenticate()
    
    if success:
        logger.info("=== Проверка завершена успешно ===")
    else:
        logger.error("=== Проверка завершена с ошибкой ===")
    return success

def main():
    """Точка входа с оптимизацией"""
    global shutdown_flag
    
    # Регистрация сигналов для daemon режима
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Интервал проверки (из окружения или 60 сек)
    check_interval = int(os.environ.get("CHECK_INTERVAL", "60"))
    daemon_mode = os.environ.get("DAEMON_MODE", "true").lower() == "true"

    with SingleInstanceLock(LOCK_FILE):
        if daemon_mode:
            logger.info(f"Запуск в режиме DAEMON (интервал {check_interval}с)")
            while not shutdown_flag:
                run_check_cycle()
                
                # Ожидание с проверкой флага
                remaining = check_interval
                while remaining > 0 and not shutdown_flag:
                    sleep_time = min(5, remaining)
                    time.sleep(sleep_time)
                    remaining -= sleep_time
            logger.info("Daemon остановлен")
        else:
            success = run_check_cycle()
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
