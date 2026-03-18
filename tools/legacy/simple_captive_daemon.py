#!/usr/bin/env python3
"""
Простой daemon для проверки captive portal без Selenium.
Работает только с HTTP запросами.
"""

import time
import logging
import sys
import signal
from datetime import datetime

try:
    import requests
except ImportError:
    print("requests не установлен: apk add python3-requests")
    sys.exit(1)

# Настройки
CHECK_INTERVAL = 60  # секунд
CHECK_URL = "http://www.msftconnecttest.com/redirect"
LOG_FILE = "/var/log/captive_daemon.log"

shutdown_flag = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    global shutdown_flag
    logger.info(f"Получен сигнал {signum}, завершение...")
    shutdown_flag = True


def check_internet():
    """Проверка доступа в интернет через msftconnecttest."""
    try:
        logger.info(f"Проверка {CHECK_URL}")
        response = requests.get(CHECK_URL, timeout=10, allow_redirects=True)
        final_url = response.url.lower()
        
        logger.info(f"Финальный URL: {final_url}")
        
        if "msn.com" in final_url or "microsoft.com" in final_url:
            logger.info("✅ Интернет доступен")
            return "authorized"
        elif "conn4.com" in final_url:
            logger.warning("⚠️  Обнаружен captive portal conn4.com")
            return "portal"
        else:
            logger.warning(f"⚠️  Неожиданный редирект: {final_url}")
            return "unknown"
            
    except requests.exceptions.Timeout:
        logger.error("❌ Таймаут при проверке")
        return "timeout"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return "error"
    except Exception as e:
        logger.error(f"❌ Ошибка: {type(e).__name__}: {e}")
        return "error"


def main():
    global shutdown_flag
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=== Captive Portal Daemon запущен ===")
    logger.info(f"Интервал проверки: {CHECK_INTERVAL} секунд")
    logger.info(f"Лог файл: {LOG_FILE}")
    
    check_count = 0
    
    while not shutdown_flag:
        check_count += 1
        logger.info(f"=== Проверка #{check_count} ({datetime.now().strftime('%H:%M:%S')}) ===")
        
        status = check_internet()
        
        if status == "portal":
            logger.warning("Требуется авторизация на портале")
            logger.info("Для авторизации используйте: /usr/sbin/auth_conn4.sh")
        
        # Ожидание следующей проверки
        remaining = CHECK_INTERVAL
        while remaining > 0 and not shutdown_flag:
            sleep_time = min(5, remaining)
            time.sleep(sleep_time)
            remaining -= sleep_time
    
    logger.info("=== Daemon остановлен ===")


if __name__ == "__main__":
    main()
