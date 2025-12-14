#!/usr/bin/env python3
"""
Тест captive портала через dev роутер без Selenium.
Использует requests для проверки перенаправлений.
"""

import requests
import sys
import time
import subprocess
import os

class CaptivePortalTester:
    def __init__(self, router_ip="192.168.1.1"):
        self.router_ip = router_ip
        self.session = requests.Session()

        # Настраиваем прокси через роутер если нужно
        # self.session.proxies = {'http': f'http://{router_ip}:8080'}

        # User-Agent как обычный браузер
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def test_router_connectivity(self):
        """Проверка доступности роутера"""
        print(f"[INFO] Проверка доступности роутера {self.router_ip}...")

        try:
            response = self.session.get(f"http://{self.router_ip}", timeout=10)
            print(f"[INFO] ✅ Роутер доступен: {response.status_code}")
            return True
        except Exception as e:
            print(f"[ERROR] ❌ Роутер недоступен: {e}")
            return False

    def test_captive_portal_detection(self):
        """Тестирование обнаружения captive портала"""
        print("[INFO] Тестирование обнаружения captive портала...")

        test_urls = [
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://detectportal.firefox.com/success.txt",
            "http://www.google.com/generate_204"
        ]

        for url in test_urls:
            print(f"[INFO] Тестирование URL: {url}")

            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)

                print(f"[INFO]   Статус: {response.status_code}")
                print(f"[INFO]   Финальный URL: {response.url}")
                print(f"[INFO]   Размер ответа: {len(response.content)} байт")

                # Проверяем признаки captive портала
                if response.url != url:
                    print(f"[INFO] 🚨 Обнаружено перенаправление!")

                    if "conn4.com" in response.url:
                        print(f"[INFO] 🎯 Обнаружен conn4.com портал: {response.url}")
                        return response.url
                    elif any(keyword in response.url.lower() for keyword in ['login', 'auth', 'portal', 'captive']):
                        print(f"[INFO] 🎯 Обнаружен captive портал: {response.url}")
                        return response.url
                    else:
                        print(f"[INFO] ⚠️ Неизвестное перенаправление: {response.url}")

                elif response.status_code == 204:
                    print(f"[INFO] ✅ Интернет доступен (204)")
                elif "success" in response.text.lower():
                    print(f"[INFO] ✅ Интернет доступен (success)")
                else:
                    print(f"[INFO] ⚠️ Неожиданный ответ")
                    print(f"[INFO]   Содержимое: {response.text[:200]}...")

            except Exception as e:
                print(f"[ERROR] ❌ Ошибка запроса к {url}: {e}")

        print("[INFO] ✅ Captive портал не обнаружен")
        return None

    def analyze_portal_page(self, portal_url):
        """Анализ страницы captive портала"""
        print(f"[INFO] Анализ страницы портала: {portal_url}")

        try:
            response = self.session.get(portal_url, timeout=15)

            if response.status_code != 200:
                print(f"[ERROR] ❌ Ошибка загрузки портала: {response.status_code}")
                return False

            html_content = response.text
            print(f"[INFO] ✅ Страница загружена: {len(html_content)} символов")

            # Сохраняем HTML для анализа
            with open('portal_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("[INFO] 📄 HTML сохранен в portal_page.html")

            # Простой анализ содержимого
            self.analyze_html_content(html_content)

            return True

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка анализа портала: {e}")
            return False

    def analyze_html_content(self, html):
        """Простой анализ HTML содержимого"""
        print("[INFO] Анализ HTML содержимого...")

        # Ищем формы
        import re

        forms = re.findall(r'<form[^>]*>(.*?)</form>', html, re.DOTALL | re.IGNORECASE)
        print(f"[INFO] Найдено форм: {len(forms)}")

        for i, form in enumerate(forms):
            print(f"[INFO] Форма {i+1}:")

            # Ищем action
            action_match = re.search(r'action=["\']([^"\']*)["\']', form, re.IGNORECASE)
            if action_match:
                print(f"[INFO]   Action: {action_match.group(1)}")

            # Ищем method
            method_match = re.search(r'method=["\']([^"\']*)["\']', form, re.IGNORECASE)
            method = method_match.group(1) if method_match else "GET"
            print(f"[INFO]   Method: {method}")

            # Ищем input поля
            inputs = re.findall(r'<input[^>]*>', form, re.IGNORECASE)
            print(f"[INFO]   Input полей: {len(inputs)}")

            for inp in inputs:
                name_match = re.search(r'name=["\']([^"\']*)["\']', inp, re.IGNORECASE)
                type_match = re.search(r'type=["\']([^"\']*)["\']', inp, re.IGNORECASE)
                value_match = re.search(r'value=["\']([^"\']*)["\']', inp, re.IGNORECASE)

                name = name_match.group(1) if name_match else "unnamed"
                input_type = type_match.group(1) if type_match else "text"
                value = value_match.group(1) if value_match else ""

                print(f"[INFO]     {input_type}: {name} = '{value}'")

        # Ищем JavaScript
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        print(f"[INFO] Найдено script блоков: {len(scripts)}")

        # Ищем кнопки
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.DOTALL | re.IGNORECASE)
        submit_inputs = re.findall(r'<input[^>]*type=["\']submit["\'][^>]*>', html, re.IGNORECASE)

        print(f"[INFO] Найдено кнопок: {len(buttons)}")
        print(f"[INFO] Найдено submit кнопок: {len(submit_inputs)}")

        for i, button in enumerate(buttons):
            button_text = re.sub(r'<[^>]*>', '', button).strip()
            print(f"[INFO]   Button {i+1}: '{button_text}'")

    def test_simple_auth_attempt(self, portal_url):
        """Простая попытка авторизации"""
        print(f"[INFO] Попытка простой авторизации на {portal_url}")

        try:
            # Получаем страницу портала
            response = self.session.get(portal_url, timeout=15)

            if response.status_code != 200:
                print(f"[ERROR] ❌ Ошибка загрузки: {response.status_code}")
                return False

            # Пробуем найти простые кнопки подключения
            html = response.text.lower()

            if 'conn4.com' in portal_url.lower():
                print("[INFO] Обнаружен conn4.com портал - требуются roomNumber и accessCode")
                return False

            # Ищем простые формы или кнопки
            if 'connect' in html or 'continue' in html or 'agree' in html:
                print("[INFO] Найдены кнопки подключения, но требуется Selenium для клика")
                return False

            print("[INFO] ⚠️ Простая авторизация невозможна без дополнительных данных")
            return False

        except Exception as e:
            print(f"[ERROR] ❌ Ошибка авторизации: {e}")
            return False

    def run_full_test(self):
        """Полный тест captive портала"""
        print("=" * 60)
        print("ТЕСТ CAPTIVE ПОРТАЛА ЧЕРЕЗ DEV РОУТЕР")
        print("=" * 60)

        # 1. Проверяем роутер
        if not self.test_router_connectivity():
            return False

        # 2. Ищем captive портал
        portal_url = self.test_captive_portal_detection()

        if not portal_url:
            print("[INFO] ✅ Captive портал не обнаружен - интернет доступен")
            return True

        # 3. Анализируем портал
        if not self.analyze_portal_page(portal_url):
            return False

        # 4. Пробуем простую авторизацию
        auth_success = self.test_simple_auth_attempt(portal_url)

        if auth_success:
            print("[INFO] 🎉 Авторизация успешна!")
        else:
            print("[INFO] ⚠️ Требуется ручная авторизация или Selenium")

        return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Тест captive портала через роутер")
    parser.add_argument("--router-ip", default="192.168.1.1", help="IP роутера")
    parser.add_argument("--timeout", type=int, default=10, help="Таймаут запросов")

    args = parser.parse_args()

    tester = CaptivePortalTester(router_ip=args.router_ip)

    try:
        success = tester.run_full_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
