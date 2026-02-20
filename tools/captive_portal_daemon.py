#!/usr/bin/env python3 -u
"""
Daemon для авторизации на captive портале conn4.com
Основан на рабочем скрипте captive_portal_selenium.py (Minisforum)
Полная логика: детекция портала, авторизация, keepalive сессии
"""

import sys
import os
import time
import logging
import pickle
import signal
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium")
    sys.exit(1)

# Пути для root (Docker) и обычного пользователя
if os.geteuid() == 0:
    LOG_FILE = "/var/log/captive_portal_daemon.log"
    PID_FILE = "/var/run/captive_portal_daemon.pid"
    COOKIES_FILE = "/var/lib/captive_portal_cookies.pkl"
    os.makedirs("/var/lib", exist_ok=True)
else:
    RUNTIME_DIR = f"/run/user/{os.getuid()}"
    if not os.path.exists(RUNTIME_DIR):
        RUNTIME_DIR = "/tmp"
    LOG_FILE = os.path.join(RUNTIME_DIR, "captive_portal_daemon.log")
    PID_FILE = os.path.join(RUNTIME_DIR, "captive_portal_daemon.pid")
    COOKIES_FILE = os.path.join(RUNTIME_DIR, "captive_portal_cookies.pkl")

CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '60'))
shutdown_flag = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler(sys.stdout),
    ],
    force=True
)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    global shutdown_flag
    logger.info(f"Получен сигнал {signum}, завершение...")
    shutdown_flag = True


class CaptivePortalDaemon:
    """Daemon с полной логикой авторизации и keepalive (как на Minisforum)"""

    def __init__(self):
        self.driver = None
        self.check_count = 0

    def save_cookies(self):
        """Сохранение куков портала conn4.com в файл"""
        if not self.driver:
            return
        try:
            cookies = self.driver.get_cookies()
            portal_cookies = [c for c in cookies if 'conn4.com' in c.get('domain', '')]
            if not portal_cookies:
                logger.info("Куки портала не найдены для сохранения")
                return
            with open(COOKIES_FILE, 'wb') as f:
                pickle.dump(portal_cookies, f)
            logger.info(f"✅ Куки портала сохранены ({len(portal_cookies)} шт.)")
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
            file_age = time.time() - os.path.getmtime(COOKIES_FILE)
            logger.info(f"Файл куков найден (возраст: {int(file_age/60)} мин, {len(cookies)} шт.)")
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
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"Не удалось загрузить cookie {cookie.get('name')}: {e}")
                logger.info("✅ Куки загружены в браузер")
                return True
            else:
                logger.warning("Домен портала не найден в куках")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки куков: {e}")
            try:
                os.remove(COOKIES_FILE)
            except Exception:
                pass
            return False

    def send_keepalive(self):
        """Отправка keepalive для обновления куков на сервере"""
        try:
            logger.info("Отправка keepalive для обновления сессии...")
            self.driver.get("https://1096.rdr.conn4.com/")
            time.sleep(2)
            self.save_cookies()

            logger.info("Проверка активности сессии...")
            self.driver.get("http://www.msftconnecttest.com/redirect")
            time.sleep(3)
            current_url = self.driver.current_url
            logger.info(f"URL после проверки: {current_url}")

            if "msn.com" in current_url.lower() or "microsoft.com" in current_url.lower():
                logger.info("✅ Keepalive успешен, сессия активна")
                return True
            elif "conn4.com" in current_url.lower():
                logger.warning("⚠️  Keepalive не удался, требуется новая авторизация")
                return False
            else:
                logger.warning(f"⚠️  Неожиданный URL после keepalive: {current_url}")
                return False
        except TimeoutException:
            logger.error("❌ Ошибка keepalive: таймаут при обращении к порталу")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка keepalive: {type(e).__name__}")
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
            options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2
            })
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
            service = None
            driver_paths = ["/usr/local/bin/chromedriver", "/usr/bin/chromedriver"]
            for path in driver_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    try:
                        import subprocess
                        result = subprocess.run([path, '--version'],
                                                capture_output=True, timeout=5)
                        if result.returncode == 0:
                            service = Service(path)
                            logger.info(f"ChromeDriver: {path}")
                            break
                    except Exception:
                        pass
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
            if shutdown_flag:
                return False
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
            except TimeoutException:
                logger.warning(f"⚠️  Таймаут при проверке портала (попытка {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(3)
                    continue
                else:
                    logger.error(f"❌ Портал не ответил после {max_retries} попыток")
                    return False
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f"❌ Ошибка проверки портала (попытка {attempt}/{max_retries}): {error_type}")
                if attempt < max_retries:
                    time.sleep(3)
                    continue
                else:
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
                    except Exception:
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
                            "arguments[0].scrollIntoView({block: 'center'});", checkbox)
                        time.sleep(0.5)
                        try:
                            checkbox.click()
                            logger.info(f"✅ Чекбокс {i+1} отмечен")
                        except Exception:
                            self.driver.execute_script(
                                "arguments[0].checked = true; "
                                "arguments[0].dispatchEvent(new Event('change'));", checkbox)
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
                            "arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        self.driver.switch_to.default_content()
                        self.save_cookies()
                        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                        if iframes:
                            self.driver.switch_to.frame(iframes[0])
                        try:
                            element.click()
                        except Exception:
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
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def _cleanup_chrome(self):
        """Закрытие Chrome и очистка процессов"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome закрыт")
            except Exception:
                pass
            self.driver = None
        try:
            import subprocess
            subprocess.run(['pkill', '-9', '-f', 'chromedriver'],
                           stderr=subprocess.DEVNULL, check=False)
            subprocess.run(['pkill', '-9', '-f', 'google-chrome.*headless'],
                           stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass

    def run_check(self):
        """Одна итерация проверки — полная логика как в рабочем скрипте"""
        self.check_count += 1
        logger.info(f"=== Проверка #{self.check_count} ({datetime.now().strftime('%H:%M:%S')}) ===")

        try:
            if not self.setup_chrome():
                logger.error("❌ Не удалось инициализировать Chrome")
                return False

            # Проверяем портал
            portal_detected = self.detect_portal()

            if not portal_detected:
                # ✅ Уже авторизованы — делаем keepalive
                logger.info("Авторизация активна")

                cookies_loaded = self.load_cookies()
                if cookies_loaded:
                    logger.info("Отправка keepalive для обновления куков...")
                    keepalive_result = self.send_keepalive()
                    if keepalive_result is None:
                        logger.error("❌ Критическая ошибка keepalive")
                    elif not keepalive_result:
                        logger.warning("⚠️  Сессия истекла, будет переавторизация на следующей проверке")
                else:
                    # Куков нет — сохраняем текущие с портала
                    logger.info("Сохранение куков с портала...")
                    try:
                        self.driver.get("https://1096.rdr.conn4.com/")
                        time.sleep(3)
                        self.save_cookies()
                    except Exception as e:
                        logger.warning(f"Не удалось сохранить куки: {e}")
                return True

            # ❌ Портал обнаружен — нужна полная авторизация
            logger.warning("⚠️  Портал обнаружен, требуется авторизация")

            if os.path.exists(COOKIES_FILE):
                logger.info("Удаление старых куков...")
                os.remove(COOKIES_FILE)

            self.click_checkboxes()

            if self.click_connect_button():
                logger.info("✅ Авторизация завершена успешно")
                return True
            else:
                logger.error("❌ Не удалось авторизоваться")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка проверки: {type(e).__name__}: {e}")
            return False
        finally:
            self._cleanup_chrome()

    def run_daemon(self):
        """Основной цикл daemon"""
        global shutdown_flag

        logger.info("=== Запуск daemon ===")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Интервал проверки: {CHECK_INTERVAL} секунд")

        self.run_check()

        while not shutdown_flag:
            try:
                logger.info(f"Ожидание {CHECK_INTERVAL} секунд до следующей проверки...")
                remaining = CHECK_INTERVAL
                while remaining > 0 and not shutdown_flag:
                    sleep_time = min(5, remaining)
                    time.sleep(sleep_time)
                    remaining -= sleep_time
                if shutdown_flag:
                    break
                self.run_check()
            except KeyboardInterrupt:
                logger.info("Получен Ctrl+C, завершение...")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {type(e).__name__}: {e}")
                time.sleep(10)

        logger.info("=== Завершение daemon ===")
        return True


def main():
    global shutdown_flag
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)
                logger.error(f"Daemon уже запущен (PID: {old_pid})")
                sys.exit(1)
            except OSError:
                logger.info(f"Удаление старого PID файла (процесс {old_pid} не существует)")
                os.remove(PID_FILE)

        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        logger.info("=== Captive Portal Daemon ===")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Log: {LOG_FILE}")

        daemon = CaptivePortalDaemon()
        try:
            success = daemon.run_daemon()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {type(e).__name__}: {e}")
            success = False
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

        logger.info("=== Daemon остановлен ===")
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
