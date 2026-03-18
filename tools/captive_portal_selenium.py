#!/usr/bin/env python3
"""
Авторизация на captive портале conn4.com.
Запускается по cron каждую минуту.

Логика:
1. Проверяем msftconnecttest.com/redirect
2. Редирект на msn.com → авторизованы:
   - Файл куков есть → keepalive (заходим на портал с куками, обновляем файл)
   - Файла куков нет → ничего не делаем
3. Редирект на conn4.com → портал:
   - Сохраняем куки со страницы портала
   - Отмечаем чекбоксы, жмём кнопку Connect
   - После успешной авторизации обновляем куки
"""

import fcntl
import logging
import os
import pickle
import subprocess
import sys
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("selenium не установлен: pip3 install selenium")
    sys.exit(1)

RUNTIME_DIR = f"/run/user/{os.getuid()}"
if not os.path.exists(RUNTIME_DIR):
    RUNTIME_DIR = "/tmp"

LOG_FILE = os.path.join(RUNTIME_DIR, "captive_portal_auth.log")
LOCK_FILE = os.path.join(RUNTIME_DIR, "captive_portal_auth.lock")
COOKIES_FILE = os.path.join(RUNTIME_DIR, "captive_portal_cookies.pkl")

PORTAL_URL = "https://1096.rdr.conn4.com/"
CHECK_URL = "http://www.msftconnecttest.com/redirect"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode="a")],
)
logger = logging.getLogger(__name__)


class SingleInstanceLock:
    """Блокировка для предотвращения множественного запуска."""

    def __init__(self, lock_file: str) -> None:
        self.lock_file = lock_file
        self.fp = None

    def __enter__(self) -> "SingleInstanceLock":
        try:
            self.fp = open(self.lock_file, "w")
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            return self
        except IOError:
            logger.info("Скрипт уже запущен, выход")
            sys.exit(0)

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self.fp:
            try:
                fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
                self.fp.close()
                os.remove(self.lock_file)
            except Exception:
                pass


def _kill_chrome() -> None:
    for pat in ("chromedriver", "google-chrome.*headless"):
        subprocess.run(["pkill", "-9", "-f", pat], stderr=subprocess.DEVNULL, check=False)


def _make_driver() -> webdriver.Chrome | None:
    try:
        opts = Options()
        for arg in (
            "--headless", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--window-size=1920,1080",
        ):
            opts.add_argument(arg)
        opts.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )
        for p in ("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
                   "/usr/bin/chromium-browser", "/usr/bin/chromium"):
            if os.path.exists(p):
                opts.binary_location = p
                break
        svc = None
        for p in ("/usr/local/bin/chromedriver", "/usr/bin/chromedriver"):
            if os.path.exists(p) and os.access(p, os.X_OK):
                svc = Service(p)
                break
        if svc is None:
            svc = Service()
        driver = webdriver.Chrome(service=svc, options=opts)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error("Ошибка создания Chrome: %s", e)
        return None


def _save_cookies(driver: webdriver.Chrome) -> bool:
    cookies = [c for c in driver.get_cookies() if "conn4.com" in c.get("domain", "")]
    if not cookies:
        logger.info("Куки conn4.com не найдены на странице")
        return False
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(cookies, f)
    logger.info("Куки сохранены (%d шт.)", len(cookies))
    return True


def _load_cookies(driver: webdriver.Chrome) -> bool:
    if not os.path.exists(COOKIES_FILE):
        return False
    try:
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        driver.get(PORTAL_URL)
        time.sleep(2)
        for c in cookies:
            try:
                driver.add_cookie(c)
            except Exception:
                pass
        logger.info("Куки загружены из файла (%d шт.)", len(cookies))
        return True
    except Exception as e:
        logger.error("Ошибка загрузки куков: %s", e)
        try:
            os.remove(COOKIES_FILE)
        except OSError:
            pass
        return False


def _check_redirect(driver: webdriver.Chrome) -> str | None:
    for attempt in range(1, 4):
        try:
            logger.info("Проверка %s (попытка %d/3)", CHECK_URL, attempt)
            driver.get(CHECK_URL)
            time.sleep(5)
            url = driver.current_url.lower()
            logger.info("URL: %s", url)
            if "msn.com" in url or "microsoft.com" in url:
                return "authorized"
            if "conn4.com" in url:
                return "portal"
            logger.info("Неожиданный URL: %s", url)
            return None
        except TimeoutException:
            logger.warning("Таймаут (попытка %d/3)", attempt)
            if attempt < 3:
                time.sleep(3)
        except Exception as e:
            logger.error("Ошибка: %s (попытка %d/3)", type(e).__name__, attempt)
            if attempt < 3:
                time.sleep(3)
    return None


def _do_keepalive(driver: webdriver.Chrome) -> None:
    logger.info("Keepalive: загрузка куков и обновление сессии...")
    _load_cookies(driver)
    driver.get(PORTAL_URL)
    time.sleep(3)
    _save_cookies(driver)
    logger.info("Keepalive выполнен")


def _switch_to_content_iframe(driver: webdriver.Chrome) -> None:
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                body = driver.find_element(By.TAG_NAME, "body").text
                if body:
                    logger.info("Переключились на iframe %d", i + 1)
                    return
            except Exception:
                driver.switch_to.default_content()
    except Exception:
        pass


def _click_checkboxes(driver: webdriver.Chrome) -> None:
    try:
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        if not checkboxes:
            logger.info("Чекбоксы не найдены")
            return
        logger.info("Найдено чекбоксов: %d", len(checkboxes))
        for i, cb in enumerate(checkboxes):
            try:
                if not cb.is_selected():
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", cb
                    )
                    time.sleep(0.5)
                    try:
                        cb.click()
                    except Exception:
                        driver.execute_script(
                            "arguments[0].checked=true;"
                            "arguments[0].dispatchEvent(new Event('change'));", cb,
                        )
                    logger.info("Чекбокс %d отмечен", i + 1)
            except Exception as e:
                logger.warning("Ошибка чекбокса %d: %s", i + 1, e)
        time.sleep(1)
    except Exception as e:
        logger.error("Ошибка обработки чекбоксов: %s", e)


def _click_connect_button(driver: webdriver.Chrome) -> bool:
    logger.info("Поиск кнопки подключения...")
    time.sleep(3)

    selectors = [
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'get free wi-fi')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'free wi-fi')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
        "//button[@type='submit']",
        "//input[@type='submit']",
        "//button[contains(@class,'btn')]",
        "//button[contains(@class,'button')]",
        "//button",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for el in elements:
                if el.is_displayed() and el.is_enabled():
                    text = (
                        el.text.strip()
                        or el.get_attribute("value")
                        or el.get_attribute("id")
                        or "button"
                    )
                    logger.info("Найдена кнопка: '%s'", text)
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", el
                    )
                    time.sleep(0.5)
                    try:
                        el.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", el)
                    logger.info("Кнопка '%s' нажата", text)
                    time.sleep(8)

                    new_url = driver.current_url
                    logger.info("URL после клика: %s", new_url)
                    if "conn4.com" not in new_url.lower():
                        logger.info("Авторизация успешна")
                        driver.switch_to.default_content()
                        try:
                            driver.get(PORTAL_URL)
                            time.sleep(3)
                            _save_cookies(driver)
                        except Exception:
                            pass
                        return True
        except Exception:
            continue

    logger.warning("Кнопка подключения не найдена")
    return False


def _do_authorize(driver: webdriver.Chrome) -> bool:
    _save_cookies(driver)
    _switch_to_content_iframe(driver)
    _click_checkboxes(driver)
    return _click_connect_button(driver)


def main() -> None:
    with SingleInstanceLock(LOCK_FILE):
        logger.info("=== Проверка captive портала ===")

        driver = _make_driver()
        if not driver:
            sys.exit(1)

        try:
            result = _check_redirect(driver)

            if result == "authorized":
                if os.path.exists(COOKIES_FILE):
                    _do_keepalive(driver)
                else:
                    logger.info("Авторизованы, куков нет — пропуск")

            elif result == "portal":
                logger.warning("Портал обнаружен, авторизация...")
                if _do_authorize(driver):
                    logger.info("Авторизация завершена успешно")
                else:
                    logger.error("Не удалось авторизоваться")
                    sys.exit(1)

            else:
                logger.warning("Не удалось определить состояние сети")
                sys.exit(1)

        except Exception as e:
            logger.error("Ошибка: %s: %s", type(e).__name__, e)
            sys.exit(1)
        finally:
            try:
                driver.quit()
            except Exception:
                pass
            _kill_chrome()

        logger.info("=== Проверка завершена ===")


if __name__ == "__main__":
    main()
