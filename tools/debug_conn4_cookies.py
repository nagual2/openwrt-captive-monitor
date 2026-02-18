#!/usr/bin/env python3
"""
Отладка cookies и редиректов conn4.com (NoJS)
==============================================

Этот скрипт эмулирует поведение браузера (с cookie jar) для прохождения
цепочки редиректов captive portal, корректно обрабатывая cookie-challenge.
"""

import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# URL для проверки
START_URL = "https://1096.rdr.conn4.com/"

# Прокси (SOCKS5)
PROXIES = {
    'http': 'socks5h://127.0.0.1:10800',
    'https': 'socks5h://127.0.0.1:10800'
}

# User-Agent как в скрипте auth_conn4.sh
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def debug_request():
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    session.proxies.update(PROXIES)

    # Настройка повторных попыток
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    logger.info(f"Начинаем запрос к {START_URL}")
    
    try:
        # Делаем запрос с автоматическим следованием по редиректам и обработкой куков
        response = session.get(START_URL, timeout=30, allow_redirects=True)
        
        logger.info(f"Финальный URL: {response.url}")
        logger.info(f"Статус код: {response.status_code}")
        
        logger.info("=== Cookies в сессии ===")
        for cookie in session.cookies:
            logger.info(f"{cookie.name}: {cookie.value} (Domain: {cookie.domain}, Path: {cookie.path})")
            
        logger.info("=== Заголовки ответа ===")
        for k, v in response.headers.items():
            logger.info(f"{k}: {v}")
            
        logger.info("=== Тело ответа (первые 2000 символов) ===")
        print(response.text[:2000])
        
        # Сохраняем полный HTML для анализа
        with open("debug_conn4_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info("Полный ответ сохранен в debug_conn4_response.html")

    except Exception as e:
        logger.error(f"Ошибка запроса: {e}")

if __name__ == "__main__":
    debug_request()
