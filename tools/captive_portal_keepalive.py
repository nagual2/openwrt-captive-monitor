#!/usr/bin/env python3
"""
Keep-alive скрипт для поддержания авторизации на captive порталах.

Выполняет периодические запросы для предотвращения сброса авторизации.
Предназначен для запуска через cron на роутере OpenWrt.

Автор: OpenWrt Captive Monitor Project
Версия: 1.0.0
"""

import sys
import os
import argparse
import requests
import time
import json
from datetime import datetime


class CaptiveKeepAlive:
    """Класс для поддержания авторизации на captive порталах."""

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()

        # Устанавливаем User-Agent как обычный браузер
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

    def check_internet_connectivity(self):
        """Проверяет доступность интернета."""
        test_urls = [
            'http://www.google.com/generate_204',
            'http://detectportal.firefox.com/success.txt',
            'http://connectivitycheck.gstatic.com/generate_204'
        ]

        for url in test_urls:
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 204 or 'success' in response.text.lower():
                    return True
            except:
                continue

        return False

    def send_keepalive_request(self, portal_url):
        """Отправляет keep-alive запрос к порталу."""
        try:
            # Простой GET запрос к порталу
            response = self.session.get(portal_url, timeout=self.timeout)

            # Проверяем, что получили ответ
            if response.status_code in [200, 204, 302]:
                return True

            return False

        except Exception as e:
            print(f"Ошибка keep-alive запроса: {e}", file=sys.stderr)
            return False

    def run_keepalive_cycle(self, portal_url, check_interval=600):
        """Выполняет один цикл keep-alive проверки."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Сначала проверяем интернет
        if self.check_internet_connectivity():
            print(f"[{timestamp}] ✅ Интернет доступен")

            # Отправляем keep-alive запрос для поддержания сессии
            if self.send_keepalive_request(portal_url):
                print(f"[{timestamp}] ✅ Keep-alive запрос успешен")
                return True
            else:
                print(f"[{timestamp}] ⚠️ Keep-alive запрос не удался")
                return False
        else:
            print(f"[{timestamp}] ❌ Интернет недоступен")
            return False

    def get_portal_from_env(self):
        """Получает URL портала из переменных окружения."""
        portal_url = os.environ.get('CAPTIVE_PORTAL_URL')
        if not portal_url:
            # Пробуем получить из UCI конфигурации через системный вызов
            try:
                import subprocess
                result = subprocess.run(['uci', '-q', 'get', 'captive-monitor.@auth[0].portal_url'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    portal_url = result.stdout.strip()
            except:
                pass

        return portal_url


def main():
    parser = argparse.ArgumentParser(description="Keep-alive для captive порталов")
    parser.add_argument("--portal-url", help="URL captive портала")
    parser.add_argument("--timeout", type=int, default=10, help="Таймаут запросов")
    parser.add_argument("--daemon", action="store_true", help="Режим демона (бесконечный цикл)")
    parser.add_argument("--interval", type=int, default=600, help="Интервал проверки в секундах (по умолчанию 10 минут)")
    parser.add_argument("--quiet", action="store_true", help="Тихий режим (только ошибки)")

    args = parser.parse_args()

    # Создаем keep-alive объект
    keepalive = CaptiveKeepAlive(args.timeout)

    # Определяем URL портала
    portal_url = args.portal_url
    if not portal_url:
        portal_url = keepalive.get_portal_from_env()

    if not portal_url:
        print("Не указан URL портала. Используйте --portal-url или установите CAPTIVE_PORTAL_URL", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Keep-alive для портала: {portal_url}")
        print(f"Интервал проверки: {args.interval} секунд")

    if args.daemon:
        # Режим демона - бесконечный цикл
        if not args.quiet:
            print("Запуск в режиме демона...")

        while True:
            try:
                success = keepalive.run_keepalive_cycle(portal_url, args.interval)

                # Спим до следующей проверки
                time.sleep(args.interval)

            except KeyboardInterrupt:
                if not args.quiet:
                    print("\nОстановка keep-alive демона")
                break
            except Exception as e:
                print(f"Ошибка в цикле keep-alive: {e}", file=sys.stderr)
                time.sleep(60)  # Ждем минуту перед повтором при ошибке
    else:
        # Однократная проверка
        success = keepalive.run_keepalive_cycle(portal_url, args.interval)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
