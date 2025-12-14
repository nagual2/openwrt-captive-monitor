#!/usr/bin/env python3
"""
Запуск Chrome с проксированием всего трафика через dev роутер
"""

import subprocess
import sys
import os
import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class ChromeRouterProxy:
    def __init__(self, router_ip="192.168.1.1", router_port=8080):
        self.router_ip = router_ip
        self.router_port = router_port
        self.driver = None

    def setup_router_proxy(self):
        """Настройка роутера как HTTP прокси"""
        print(f"[INFO] Настройка прокси через роутер {self.router_ip}:{self.router_port}")

        # Проверяем доступность роутера
        try:
            import requests
            response = requests.get(f"http://{self.router_ip}", timeout=5)
            print(f"[INFO] ✅ Роутер {self.router_ip} доступен")
            return True
        except Exception as e:
            print(f"[ERROR] ❌ Роутер недоступен: {e}")
            return False

    def launch_chrome_with_proxy(self, headless=False, gui_mode=False):
        """Запуск Chrome с проксированием через роутер"""
        system = platform.system()
        print(f"[INFO] Запуск Chrome на {system} с проксированием...")

        if gui_mode:
            # Запуск обычного Chrome с прокси настройками
            return self.launch_chrome_gui()
        else:
            # Запуск через Selenium
            return self.launch_chrome_selenium(headless)

    def launch_chrome_gui(self):
        """Запуск обычного Chrome с GUI и прокси"""
        system = platform.system()

        chrome_args = [
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            f"--proxy-server=http://{self.router_ip}:{self.router_port}",
            f"--host-resolver-rules=MAP * {self.router_ip}",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--user-data-dir=/tmp/chrome_dev_profile"
        ]

        if system == "Windows":
            chrome_locations = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
        else:
            chrome_locations = [
                "/usr/bin/google-chrome",
                "/opt/google/chrome/google-chrome"
            ]

        chrome_binary = None
        for location in chrome_locations:
            if os.path.exists(location):
                chrome_binary = location
                break

        if not chrome_binary:
            print("[ERROR] Chrome не найден")
            return False

        try:
            print(f"[INFO] Запуск Chrome: {chrome_binary}")
            print(f"[INFO] Прокси: http://{self.router_ip}:{self.router_port}")

            cmd = [chrome_binary] + chrome_args + ["http://connectivitycheck.gstatic.com/generate_204"]

            if system == "Windows":
                subprocess.Popen(cmd, shell=False)
            else:
                subprocess.Popen(cmd)

            print("[INFO] ✅ Chrome запущен с проксированием")
            print("[INFO] Откройте http://connectivitycheck.gstatic.com/generate_204 для тестирования")
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка запуска Chrome: {e}")
            return False

    def launch_chrome_selenium(self, headless=False):
        """Запуск Chrome через Selenium с проксированием"""
        system = platform.system()

        try:
            options = Options()

            if headless:
                options.add_argument("--headless")

            # Основные настройки
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")

            # КЛЮЧЕВЫЕ НАСТРОЙКИ ПРОКСИ
            options.add_argument(f"--proxy-server=http://{self.router_ip}:{self.router_port}")
            options.add_argument(f"--host-resolver-rules=MAP * {self.router_ip}")

            print(f"[INFO] Настроен прокси: http://{self.router_ip}:{self.router_port}")

            # WSL специфичные настройки
            if system == "Linux" and "Microsoft" in platform.release():
                print("[INFO] Настройки для WSL...")
                options.add_argument("--single-process")
                options.add_argument("--disable-software-rasterizer")
                options.add_argument("--disable-background-networking")

            # Поиск Chrome
            if system == "Windows":
                chrome_locations = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
            else:
                chrome_locations = [
                    "/usr/bin/google-chrome",
                    "/opt/google/chrome/google-chrome"
                ]

            chrome_binary = None
            for location in chrome_locations:
                if os.path.exists(location):
                    chrome_binary = location
                    break

            if chrome_binary:
                options.binary_location = chrome_binary
                print(f"[INFO] Chrome: {chrome_binary}")

            # ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except:
                service = Service()

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)

            print("[INFO] ✅ Chrome Selenium запущен с проксированием")
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка Selenium: {e}")
            return False

    def test_captive_portal(self):
        """Тестирование captive портала через прокси"""
        if not self.driver:
            print("[ERROR] Chrome не запущен")
            return False

        test_urls = [
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://www.google.com",
            "http://www.msftconnecttest.com/connecttest.txt"
        ]

        for url in test_urls:
            try:
                print(f"[INFO] Тестирую: {url}")
                self.driver.get(url)
                time.sleep(3)

                current_url = self.driver.current_url
                title = self.driver.title
                content = self.driver.page_source[:200]

                print(f"[INFO] URL: {current_url}")
                print(f"[INFO] Title: {title}")
                print(f"[INFO] Content: {content}...")

                if current_url != url:
                    print(f"[INFO] 🚨 РЕДИРЕКТ: {url} -> {current_url}")

                print("-" * 50)

            except Exception as e:
                print(f"[ERROR] Ошибка с {url}: {e}")

        return True

    def interactive_mode(self):
        """Интерактивный режим для ручного тестирования"""
        if not self.driver:
            print("[ERROR] Chrome не запущен")
            return

        print("\n" + "=" * 60)
        print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("=" * 60)
        print("Команды:")
        print("  url <адрес>  - открыть URL")
        print("  test         - тест captive портала")
        print("  quit         - выход")
        print("=" * 60)

        while True:
            try:
                cmd = input("\n> ").strip().lower()

                if cmd == "quit" or cmd == "q":
                    break
                elif cmd == "test":
                    self.test_captive_portal()
                elif cmd.startswith("url "):
                    url = cmd[4:].strip()
                    if not url.startswith("http"):
                        url = "http://" + url

                    print(f"[INFO] Открываю: {url}")
                    self.driver.get(url)
                    time.sleep(2)

                    print(f"[INFO] Текущий URL: {self.driver.current_url}")
                    print(f"[INFO] Заголовок: {self.driver.title}")
                elif cmd == "help" or cmd == "h":
                    print("Команды: url <адрес>, test, quit")
                else:
                    print("Неизвестная команда. Введите 'help' для справки")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] Ошибка: {e}")

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                print("[INFO] Chrome закрыт")
            except:
                pass

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Chrome с проксированием через роутер')
    parser.add_argument('--router-ip', default='192.168.1.1', help='IP роутера')
    parser.add_argument('--router-port', type=int, default=8080, help='Порт прокси роутера')
    parser.add_argument('--headless', action='store_true', help='Headless режим')
    parser.add_argument('--gui', action='store_true', help='Запуск обычного Chrome с GUI')
    parser.add_argument('--test', action='store_true', help='Автоматический тест')
    parser.add_argument('--interactive', action='store_true', help='Интерактивный режим')

    args = parser.parse_args()

    proxy = ChromeRouterProxy(router_ip=args.router_ip, router_port=args.router_port)

    try:
        if not proxy.setup_router_proxy():
            print("[ERROR] Не удалось настроить прокси")
            return 1

        if args.gui:
            # Запуск обычного Chrome
            success = proxy.launch_chrome_gui()
            if success:
                print("[INFO] Chrome запущен. Нажмите Enter для завершения...")
                input()
            return 0 if success else 1
        else:
            # Запуск через Selenium
            if not proxy.launch_chrome_selenium(headless=args.headless):
                return 1

            if args.test:
                proxy.test_captive_portal()
            elif args.interactive:
                proxy.interactive_mode()
            else:
                print("[INFO] Chrome запущен. Используйте --test или --interactive")
                time.sleep(5)

        return 0

    except KeyboardInterrupt:
        print("\n[INFO] Прервано пользователем")
        return 130
    except Exception as e:
        print(f"[ERROR] Критическая ошибка: {e}")
        return 1
    finally:
        proxy.cleanup()

if __name__ == "__main__":
    sys.exit(main())
