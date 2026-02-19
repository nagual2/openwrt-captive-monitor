#!/usr/bin/env python3
"""
Daemon для авторизации на captive портале conn4.com
Запускается один раз и висит в памяти, проверяя портал каждую минуту
Chrome/Selenium остаются в памяти для быстрых проверок
"""

import sys
import os
import time
import logging
import fcntl
import pickle
import json
import signal
from datetime import datetime

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
# Для root используем /var/log, для пользователя - /run/user или /tmp
if os.geteuid() == 0:
    # Root - используем /var/log
    RUNTIME_DIR = "/var/log"
    LOG_FILE = "/var/log/captive_portal_daemon.log"
    PID_FILE = "/var/run/captive_portal_daemon.pid"
    COOKIES_FILE = "/var/lib/captive_portal_cookies.pkl"
    
    # Создаем директорию для куков если не существует
    os.makedirs("/var/lib", exist_ok=True)
else:
    # Обычный пользователь
    RUNTIME_DIR = f"/run/user/{os.getuid()}"
    if not os.path.exists(RUNTIME_DIR):
        RUNTIME_DIR = "/tmp"
    
    LOG_FILE = os.path.join(RUNTIME_DIR, "captive_portal_daemon.log")
    PID_FILE = os.path.join(RUNTIME_DIR, "captive_portal_daemon.pid")
    COOKIES_FILE = os.path.join(RUNTIME_DIR, "captive_portal_cookies.pkl")

# Интервал проверки (секунды)
CHECK_INTERVAL = 60  # 1 минута

# Флаг для graceful shutdown
shutdown_flag = False

# Настройка логирования
# Проверяем переменную окружения для режима отладки
DEBUG_MODE = os.environ.get('CAPTIVE_DAEMON_DEBUG', '0') == '1'

handlers = [logging.FileHandler(LOG_FILE, mode='a')]
if DEBUG_MODE:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global shutdown_flag
    logger.info(f"Received signal {signum}, shutting down...")
    shutdown_flag = True


class SingleInstanceLock:
    """Блокировка для предотвращения множественного запуска daemon"""
    
    def __init__(self, lock_file, pid_file):
        self.lock_file = lock_file
        self.pid_file = pid_file
        self.fp = None
    
    def __enter__(self):
        try:
            self.fp = open(self.lock_file, 'w')
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Записываем PID
            pid = os.getpid()
            self.fp.write(str(pid))
            self.fp.flush()
            
            # Также сохраняем в отдельный PID файл
            with open(self.pid_file, 'w') as pf:
                pf.write(str(pid))
            
            return self
        except IOError:
            logger.error("Daemon уже запущен")
            sys.exit(1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp:
            try:
                fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
                self.fp.close()
                os.remove(self.lock_file)
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
            except:
                pass


class CaptivePortalDaemon:
    """Daemon для постоянного мониторинга captive портала"""

    def __init__(self):
        self.driver = None
        self.chrome_initialized = False
        self.last_check_time = 0
        self.check_count = 0

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
        """Настройка Chrome WebDriver (один раз при запуске)"""
        if self.chrome_initialized:
            logger.debug("Chrome уже инициализирован")
            return True
        
        logger.info("Инициализация Chrome...")

        try:
            options = Options()
            options.add_argument("--headless=new")  # Новый headless режим
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
            chrome_found = False
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    logger.info(f"Chrome binary: {path}")
                    chrome_found = True
                    break
            
            if not chrome_found:
                logger.error("Chrome binary не найден")
                return False

            # Используем Selenium Manager (автоматически скачает chromedriver)
            logger.info("Используем Selenium Manager для автоматической настройки chromedriver")
            service = Service()

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(60)  # Увеличено с 30 до 60 секунд для WSL
            self.chrome_initialized = True
            logger.info("✅ Chrome инициализирован")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Chrome: {e}")
            self.chrome_initialized = False
            return False

    def is_chrome_alive(self) -> bool:
        """Проверка что Chrome процесс жив."""
        try:
            # Пытаемся получить текущий URL - если Chrome жив, это сработает
            _ = self.driver.current_url
            return True
        except Exception:
            return False
    
    def restart_chrome(self):
        """Перезапуск Chrome при падении."""
        logger.warning("🔄 Chrome упал, перезапускаем...")
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.driver = None
            self.chrome_initialized = False
            
            # Пауза перед перезапуском
            time.sleep(2)
            
            # Перезапускаем
            if self.setup_chrome():
                logger.info("✅ Chrome перезапущен успешно")
                return True
            else:
                logger.error("❌ Не удалось перезапустить Chrome")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка перезапуска Chrome: {e}")
            return False
    
    def check_portal_lightweight(self):
        """Легковесная проверка портала без полной загрузки страницы"""
        if not self.driver:
            return None
        
        # Проверяем что Chrome жив
        if not self.is_chrome_alive():
            logger.warning("⚠️  Chrome не отвечает, перезапускаем...")
            if not self.restart_chrome():
                return None
        
        try:
            # Быстрая проверка через msftconnecttest
            logger.info("Проверка: http://www.msftconnecttest.com/redirect")
            self.driver.get("http://www.msftconnecttest.com/redirect")
            time.sleep(5)  # Увеличено с 2 до 5 секунд для WSL
            
            current_url = self.driver.current_url
            logger.info(f"Текущий URL: {current_url}")
            
            # Уже авторизованы
            if "msn.com" in current_url.lower() or "microsoft.com" in current_url.lower():
                logger.info("✅ Уже авторизованы! (редирект на MSN)")
                return False  # Портал не обнаружен
            
            # Портал обнаружен
            if "conn4.com" in current_url.lower():
                logger.warning(f"⚠️  Обнаружен портал: {current_url}")
                return True  # Портал обнаружен
            
            # Неожиданный редирект
            logger.warning(f"⚠️  Неожиданный редирект: {current_url}")
            return None  # Неопределенное состояние
        
        except Exception as e:
            logger.warning(f"Ошибка легковесной проверки: {type(e).__name__}")
            logger.warning("⚠️  Пытаемся перезапустить Chrome...")
            if self.restart_chrome():
                return None  # Попробуем на следующей итерации
            else:
                return None
    
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

    def run_check(self):
        """Одна итерация проверки портала"""
        self.check_count += 1
        self.last_check_time = time.time()
        
        logger.info(f"=== Проверка #{self.check_count} ({datetime.now().strftime('%H:%M:%S')}) ===")
        
        try:
            # Убеждаемся что Chrome инициализирован
            if not self.chrome_initialized:
                if not self.setup_chrome():
                    logger.error("❌ Не удалось инициализировать Chrome")
                    return False
            
            # Легковесная проверка портала
            portal_detected = self.check_portal_lightweight()
            
            if portal_detected is None:
                logger.warning("⚠️  Неопределенное состояние, пропускаем проверку")
                return False
            
            if not portal_detected:
                # ✅ Уже авторизованы
                logger.info("✅ Авторизация активна")
                
                # Периодически обновляем куки (каждые 10 проверок)
                if self.check_count % 10 == 0:
                    logger.info("Обновление куков...")
                    cookies_loaded = self.load_cookies()
                    if cookies_loaded:
                        keepalive_result = self.send_keepalive()
                        if keepalive_result is None:
                            logger.error("❌ Критическая ошибка keepalive")
                            return False
                
                return True
            
            # ❌ Портал обнаружен - нужна полная авторизация
            logger.warning("⚠️  Портал обнаружен, требуется авторизация")
            
            # Удаляем старые куки
            if os.path.exists(COOKIES_FILE):
                logger.info("Удаление старых куков...")
                os.remove(COOKIES_FILE)
            
            # Отметка чекбоксов
            self.click_checkboxes()
            
            # Клик по кнопке подключения
            if self.click_connect_button():
                logger.info("✅ Авторизация завершена успешно")
                return True
            else:
                logger.error("❌ Не удалось авторизоваться")
                return False
        
        except Exception as e:
            logger.error(f"❌ Ошибка проверки: {type(e).__name__}: {e}")
            return False
    
    def run_daemon(self):
        """Основной цикл daemon"""
        global shutdown_flag
        
        logger.info("=== Запуск daemon ===")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Интервал проверки: {CHECK_INTERVAL} секунд")
        
        # Инициализация Chrome при старте
        if not self.setup_chrome():
            logger.error("❌ Не удалось инициализировать Chrome при старте")
            return False
        
        # Первая проверка сразу
        self.run_check()
        
        # Основной цикл
        while not shutdown_flag:
            try:
                # Ждем до следующей проверки
                time_to_wait = CHECK_INTERVAL - (time.time() - self.last_check_time)
                
                if time_to_wait > 0:
                    logger.debug(f"Ожидание {int(time_to_wait)} секунд до следующей проверки...")
                    
                    # Спим небольшими интервалами для быстрого реагирования на shutdown
                    while time_to_wait > 0 and not shutdown_flag:
                        sleep_time = min(5, time_to_wait)
                        time.sleep(sleep_time)
                        time_to_wait -= sleep_time
                
                if shutdown_flag:
                    break
                
                # Выполняем проверку
                self.run_check()
            
            except KeyboardInterrupt:
                logger.info("Получен Ctrl+C, завершение...")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {type(e).__name__}: {e}")
                time.sleep(10)  # Пауза перед повтором при ошибке
        
        logger.info("=== Завершение daemon ===")
        return True
    
    def cleanup(self):
        """Очистка ресурсов"""
        logger.info("Очистка ресурсов...")
        
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome закрыт")
            except:
                pass
        
        # Принудительная очистка процессов
        try:
            import subprocess
            subprocess.run(['pkill', '-9', '-f', 'chromedriver'], 
                          stderr=subprocess.DEVNULL, check=False)
            subprocess.run(['pkill', '-9', '-f', 'google-chrome.*headless'], 
                          stderr=subprocess.DEVNULL, check=False)
        except:
            pass
    


def main():
    """Точка входа daemon"""
    global shutdown_flag
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Проверка единственного экземпляра
    try:
        # Проверяем существующий PID
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Проверяем жив ли процесс
            try:
                os.kill(old_pid, 0)  # Не убивает, просто проверяет
                logger.error(f"Daemon уже запущен (PID: {old_pid})")
                sys.exit(1)
            except OSError:
                # Процесс не существует, удаляем старый PID файл
                logger.info(f"Удаление старого PID файла (процесс {old_pid} не существует)")
                os.remove(PID_FILE)
        
        # Создаем PID файл
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
            daemon.cleanup()
            
            # Удаляем PID файл
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        
        logger.info("=== Daemon остановлен ===")
        sys.exit(0 if success else 1)
    
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
