#!/usr/bin/env python3 -u
"""
Daemon для авторизации на captive портале conn4.com.

Логика:
1. Каждые CHECK_INTERVAL секунд проверяем msftconnecttest.com/redirect
2. Редирект на msn.com → авторизованы:
   - Файл куков есть → keepalive (заходим на портал с куками, обновляем файл)
   - Файла куков нет → ничего не делаем
3. Редирект на conn4.com → портал:
   - Сохраняем куки со страницы портала
   - Отмечаем чекбоксы, жмём кнопку Connect
   - После успешной авторизации обновляем куки
"""

import os
import pickle
import signal
import subprocess
import sys
import time
import logging
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("selenium не установлен: pip3 install selenium")
    sys.exit(1)

# Пути
if os.geteuid() == 0:
    LOG_FILE = os.environ.get("LOG_FILE", "/var/log/captive_portal_daemon.log")
    PID_FILE = os.environ.get("PID_FILE", "/var/run/captive_portal_daemon.pid")
    COOKIES_FILE = os.environ.get("COOKIES_FILE", "/var/lib/captive_portal_cookies.pkl")
else:
    _rd = f"/run/user/{os.getuid()}"
    if not os.path.exists(_rd):
        _rd = "/tmp"
    LOG_FILE = os.environ.get("LOG_FILE", os.path.join(_rd, "captive_portal_daemon.log"))
    PID_FILE = os.environ.get("PID_FILE", os.path.join(_rd, "captive_portal_daemon.pid"))
    COOKIES_FILE = os.environ.get("COOKIES_FILE", os.path.join(_rd, "captive_portal_cookies.pkl"))

CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))
PORTAL_URL = "https://1096.rdr.conn4.com/"
CHECK_URL = "http://www.msftconnecttest.com/redirect"

shutdown_flag = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)
logger = logging.getLogger(__name__)


def signal_handler(signum: int, frame: object) -> None:
    global shutdown_flag
    logger.info("Получен сигнал %d, завершение...", signum)
    shutdown_flag = True


def _kill_chrome() -> None:
    """Убить все процессы chrome/chromedriver."""
    for pat in ("chromedriver", "google-chrome.*headless"):
        subprocess.run(
            ["pkill", "-9", "-f", pat],
            stderr=subprocess.DEVNULL,
            check=False,
        )


def _make_driver() -> webdriver.Chrome | None:
    """Создать headless Chrome WebDriver."""
    try:
        opts = Options()
        for arg in (
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
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
    """Сохранить куки conn4.com в файл. Возвращает True если сохранены."""
    cookies = [c for c in driver.get_cookies() if "conn4.com" in c.get("domain", "")]
    if not cookies:
        logger.info("Куки conn4.com не найдены на странице")
        return False
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(cookies, f)
    logger.info("Куки сохранены (%d шт.)", len(cookies))
    return True


def _load_cookies(driver: webdriver.Chrome) -> bool:
    """Загрузить куки из файла в браузер. Возвращает True если загружены."""
    if not os.path.exists(COOKIES_FILE):
        return False
    try:
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        # Нужно быть на домене conn4.com чтобы добавить куки
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
    """Проверить msftconnecttest redirect.

    Возвращает:
        "authorized" — редирект на msn/microsoft
        "portal"     — редирект на conn4.com
        None         — ошибка или неизвестный результат
    """
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
            logger.error("Ошибка проверки: %s (попытка %d/3)", type(e).__name__, attempt)
            if attempt < 3:
                time.sleep(3)
    return None


def _do_keepalive(driver: webdriver.Chrome) -> None:
    """Keepalive: загрузить куки, зайти на портал, обновить куки в файле."""
    logger.info("Keepalive: загрузка куков и обновление сессии...")
    _load_cookies(driver)
    driver.get(PORTAL_URL)
    time.sleep(3)
    _save_cookies(driver)
    logger.info("Keepalive выполнен")


def _do_authorize(driver: webdriver.Chrome) -> bool:
    """Полная авторизация: чекбоксы + кнопка Connect.

    Предполагается что driver уже на странице портала conn4.com.
    Возвращает True при успехе.
    """
    # Сохраняем куки портала ДО авторизации (куки страницы портала)
    _save_cookies(driver)

    # Переключаемся в iframe если есть
    _switch_to_content_iframe(driver)

    # Чекбоксы
    _click_checkboxes(driver)

    # Кнопка Connect
    return _click_connect_button(driver)


def _switch_to_content_iframe(driver: webdriver.Chrome) -> None:
    """Переключиться на iframe с контентом портала."""
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
    """Отметить все чекбоксы на странице."""
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
                            "arguments[0].dispatchEvent(new Event('change'));",
                            cb,
                        )
                    logger.info("Чекбокс %d отмечен", i + 1)
            except Exception as e:
                logger.warning("Ошибка чекбокса %d: %s", i + 1, e)
        time.sleep(1)
    except Exception as e:
        logger.error("Ошибка обработки чекбоксов: %s", e)


def _click_connect_button(driver: webdriver.Chrome) -> bool:
    """Найти и нажать кнопку подключения. Возвращает True при успехе."""
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
                        # Сохраняем куки ПОСЛЕ успешной авторизации
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


class CaptivePortalDaemon:
    """Основной daemon."""

    def __init__(self) -> None:
        self.check_count = 0

    def run_check(self) -> None:
        """Одна итерация проверки."""
        self.check_count += 1
        logger.info(
            "=== Проверка #%d (%s) ===",
            self.check_count,
            datetime.now().strftime("%H:%M:%S"),
        )

        driver = _make_driver()
        if not driver:
            logger.error("Не удалось создать Chrome")
            return

        try:
            result = _check_redirect(driver)

            if result == "authorized":
                # Уже авторизованы
                if os.path.exists(COOKIES_FILE):
                    # Файл куков есть → keepalive
                    _do_keepalive(driver)
                else:
                    # Куков нет → ничего не делаем
                    logger.info("Авторизованы, куков нет — пропуск")

            elif result == "portal":
                # Портал обнаружен → авторизация
                logger.warning("Портал обнаружен, авторизация...")
                if _do_authorize(driver):
                    logger.info("Авторизация завершена успешно")
                else:
                    logger.error("Не удалось авторизоваться")

            else:
                logger.warning("Не удалось определить состояние сети")

        except Exception as e:
            logger.error("Ошибка проверки: %s: %s", type(e).__name__, e)
        finally:
            try:
                driver.quit()
            except Exception:
                pass
            _kill_chrome()

    def run(self) -> None:
        """Основной цикл."""
        global shutdown_flag
        logger.info("=== Daemon запущен (PID %d, интервал %ds) ===", os.getpid(), CHECK_INTERVAL)

        self.run_check()

        while not shutdown_flag:
            remaining = CHECK_INTERVAL
            while remaining > 0 and not shutdown_flag:
                s = min(5, remaining)
                time.sleep(s)
                remaining -= s
            if shutdown_flag:
                break
            self.run_check()

        logger.info("=== Daemon остановлен ===")


def main() -> None:
    global shutdown_flag
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # PID файл
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            logger.error("Daemon уже запущен (PID %d)", old_pid)
            sys.exit(1)
        except (OSError, ValueError):
            os.remove(PID_FILE)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        CaptivePortalDaemon().run()
    finally:
        try:
            os.remove(PID_FILE)
        except OSError:
            pass


if __name__ == "__main__":
    main()
