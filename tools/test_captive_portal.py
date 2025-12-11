#!/usr/bin/env python3
"""
Скрипт для тестирования captive portal функционала через роутер OpenWrt.
Принудительно направляет ВСЕ запросы (DNS и HTTP) через указанный роутер.
Должен запускаться в WSL с правами sudo для управления маршрутизацией.
"""

import socket
import requests
import time
import sys
import argparse
import subprocess
import os
import tempfile
import json
from urllib.parse import urlparse

class CaptivePortalTester:
    def __init__(self, router_ip="192.168.1.1", timeout=10):
        self.router_ip = router_ip
        self.timeout = timeout
        self.test_urls = [
            "http://www.msftconnecttest.com/redirect",
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://clients3.google.com/generate_204",
            "http://www.google.com/generate_204"
        ]
        self.test_hosts = [
            "www.msftconnecttest.com",
            "connectivitycheck.gstatic.com",
            "clients3.google.com",
            "www.google.com",
            "google.com",
            "8.8.8.8",
            "1.1.1.1"
        ]
        self.added_routes = []
        self.original_resolv_conf = None

    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def check_root_privileges(self):
        """Проверка прав sudo для управления маршрутизацией"""
        if os.geteuid() != 0:
            self.log("❌ Скрипт должен запускаться с правами sudo для управления маршрутизацией", "ERROR")
            self.log("Запустите: sudo python3 tools/test_captive_portal.py", "ERROR")
            return False
        return True

    def setup_dns_through_router(self):
        """Настройка DNS через роутер"""
        self.log(f"Настройка DNS через роутер {self.router_ip}")

        try:
            # Сохраняем оригинальный resolv.conf
            with open('/etc/resolv.conf', 'r') as f:
                self.original_resolv_conf = f.read()

            # Создаем новый resolv.conf с DNS через роутер
            new_resolv_conf = f"""# Временная настройка для тестирования captive portal
nameserver {self.router_ip}
# Резервные DNS (если роутер не отвечает)
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

            with open('/etc/resolv.conf', 'w') as f:
                f.write(new_resolv_conf)

            self.log("✅ DNS настроен через роутер")
            return True

        except Exception as e:
            self.log(f"❌ Ошибка настройки DNS: {e}", "ERROR")
            return False

    def restore_dns(self):
        """Восстановление оригинальных DNS настроек"""
        if self.original_resolv_conf:
            try:
                with open('/etc/resolv.conf', 'w') as f:
                    f.write(self.original_resolv_conf)
                self.log("✅ DNS настройки восстановлены")
            except Exception as e:
                self.log(f"❌ Ошибка восстановления DNS: {e}", "ERROR")

    def add_route_through_router(self, destination):
        """Добавление маршрута через роутер для конкретного хоста"""
        try:
            # Проверяем, является ли destination IP адресом
            try:
                socket.inet_aton(destination)
                target = destination
            except socket.error:
                # Это hostname, нужно разрешить через DNS
                try:
                    target = socket.gethostbyname(destination)
                    self.log(f"DNS разрешение: {destination} -> {target}")
                except socket.gaierror as e:
                    self.log(f"❌ Не удалось разрешить {destination}: {e}", "ERROR")
                    return False

            # Добавляем маршрут через роутер
            cmd = ["ip", "route", "add", target, "via", self.router_ip]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.log(f"✅ Маршрут добавлен: {target} via {self.router_ip}")
                self.added_routes.append(target)
                return True
            else:
                # Проверяем, не существует ли уже маршрут
                if "File exists" in result.stderr:
                    self.log(f"ℹ️ Маршрут уже существует: {target}")
                    return True
                else:
                    self.log(f"❌ Ошибка добавления маршрута для {target}: {result.stderr}", "ERROR")
                    return False

        except Exception as e:
            self.log(f"❌ Неожиданная ошибка при добавлении маршрута для {destination}: {e}", "ERROR")
            return False

    def remove_added_routes(self):
        """Удаление всех добавленных маршрутов"""
        for target in self.added_routes:
            try:
                cmd = ["ip", "route", "del", target, "via", self.router_ip]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log(f"✅ Маршрут удален: {target}")
                else:
                    self.log(f"⚠️ Не удалось удалить маршрут {target}: {result.stderr}", "WARN")
            except Exception as e:
                self.log(f"❌ Ошибка удаления маршрута {target}: {e}", "ERROR")
        self.added_routes.clear()

    def test_dns_resolution(self, hostname):
        """Тестирование DNS разрешения через роутер"""
        self.log(f"Тестирование DNS для {hostname}")

        try:
            start_time = time.time()

            # Используем dig для явного DNS запроса через роутер
            cmd = ["dig", f"@{self.router_ip}", hostname, "A", "+short", "+time=5"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)

            resolve_time = time.time() - start_time

            if result.returncode == 0 and result.stdout.strip():
                ip_addresses = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                if ip_addresses:
                    ip = ip_addresses[0]
                    self.log(f"✅ DNS успешно: {hostname} -> {ip} ({resolve_time:.3f}s)")
                    return ip

            # Fallback на системный резолвер
            try:
                ip = socket.gethostbyname(hostname)
                self.log(f"✅ DNS (fallback): {hostname} -> {ip} ({resolve_time:.3f}s)")
                return ip
            except socket.gaierror:
                pass

            self.log(f"❌ DNS не удалось разрешить {hostname}", "ERROR")
            return None

        except subprocess.TimeoutExpired:
            self.log(f"❌ DNS таймаут для {hostname}", "ERROR")
            return None
        except Exception as e:
            self.log(f"❌ DNS ошибка для {hostname}: {e}", "ERROR")
            return None

    def test_http_request(self, url):
        """Тестирование HTTP запроса через роутер"""
        self.log(f"Тестирование HTTP запроса: {url}")

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            # Добавляем маршрут для этого хоста через роутер
            if not self.add_route_through_router(hostname):
                self.log(f"⚠️ Не удалось добавить маршрут для {hostname}, продолжаем", "WARN")

            # Выполняем HTTP запрос
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            start_time = time.time()
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False
            )
            request_time = time.time() - start_time

            # Анализируем ответ
            result = self.analyze_http_response(url, response, request_time)
            return response, result

        except requests.exceptions.Timeout:
            self.log(f"❌ HTTP таймаут для {url}", "ERROR")
            return None, "timeout"
        except requests.exceptions.ConnectionError as e:
            self.log(f"❌ HTTP ошибка подключения для {url}: {e}", "ERROR")
            return None, "connection_error"
        except Exception as e:
            self.log(f"❌ HTTP неожиданная ошибка для {url}: {e}", "ERROR")
            return None, "error"

    def analyze_http_response(self, url, response, request_time):
        """Анализ HTTP ответа для определения captive portal"""
        status = response.status_code
        content_length = len(response.content)

        self.log(f"📊 HTTP ответ: {status} ({request_time:.3f}s, {content_length} bytes)")

        # Показываем заголовки для анализа
        if 'Location' in response.headers:
            location = response.headers['Location']
            self.log(f"🔄 Редирект на: {location}")

        if 'Content-Type' in response.headers:
            content_type = response.headers['Content-Type']
            self.log(f"📄 Content-Type: {content_type}")

        # Анализируем статус код
        if status == 200:
            if "generate_204" in url:
                if content_length == 0:
                    self.log(f"✅ Интернет доступен (пустой 204 ответ)")
                    return "internet_ok"
                else:
                    self.log(f"🚨 CAPTIVE PORTAL: ожидался пустой ответ, получен контент ({content_length} bytes)", "WARN")
                    # Показываем первые 200 символов контента
                    content_preview = response.text[:200].replace('\n', ' ').replace('\r', '')
                    self.log(f"📄 Контент: {content_preview}...")
                    return "captive_portal"
            else:
                self.log(f"✅ HTTP запрос успешен")
                return "http_ok"

        elif status in [301, 302, 303, 307, 308]:
            if 'Location' in response.headers:
                location = response.headers['Location']
                if self.is_captive_portal_redirect(url, location):
                    return "captive_portal"
            self.log(f"🔄 HTTP редирект ({status})")
            return "redirect"

        elif status == 204:
            if content_length == 0:
                self.log(f"✅ Интернет доступен (204 No Content)")
                return "internet_ok"
            else:
                self.log(f"🚨 CAPTIVE PORTAL: 204 с контентом", "WARN")
                return "captive_portal"

        else:
            self.log(f"❓ Неожиданный статус: {status}")
            return "unknown"

    def is_captive_portal_redirect(self, original_url, redirect_url):
        """Определяет, является ли редирект признаком captive portal"""
        original_domain = urlparse(original_url).netloc
        redirect_domain = urlparse(redirect_url).netloc

        if original_domain != redirect_domain:
            self.log(f"🚨 CAPTIVE PORTAL: Редирект на другой домен ({original_domain} -> {redirect_domain})", "WARN")
            return True

        captive_patterns = [
            'login', 'auth', 'portal', 'captive', 'wifi',
            'hotspot', 'guest', 'welcome', 'terms', 'signin'
        ]

        redirect_lower = redirect_url.lower()
        for pattern in captive_patterns:
            if pattern in redirect_lower:
                self.log(f"🚨 CAPTIVE PORTAL: Обнаружен паттерн '{pattern}' в URL", "WARN")
                return True

        return False

    def test_ping_connectivity(self):
        """Тестирование ICMP ping через роутер"""
        self.log("Тестирование ICMP ping")

        test_hosts = ["8.8.8.8", "1.1.1.1", "google.com"]

        for host in test_hosts:
            # Добавляем маршрут через роутер
            self.add_route_through_router(host)

            try:
                # Используем ping с принудительным интерфейсом
                cmd = ["ping", "-c", "3", "-W", "3", host]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

                if result.returncode == 0:
                    self.log(f"✅ PING успешен: {host}")
                    return True
                else:
                    self.log(f"❌ PING неудачен: {host}")

            except subprocess.TimeoutExpired:
                self.log(f"❌ PING таймаут: {host}")
            except Exception as e:
                self.log(f"❌ PING ошибка для {host}: {e}")

        return False

    def show_network_info(self):
        """Показать информацию о сетевой конфигурации"""
        self.log("📊 СЕТЕВАЯ КОНФИГУРАЦИЯ")

        try:
            # Показать маршруты
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log("🛣️ Таблица маршрутизации:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        self.log(f"   {line}")

            # Показать DNS
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    dns_config = f.read().strip()
                self.log("🌐 DNS конфигурация:")
                for line in dns_config.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        self.log(f"   {line}")
            except:
                pass

        except Exception as e:
            self.log(f"❌ Ошибка получения сетевой информации: {e}")

    def cleanup(self):
        """Очистка всех изменений"""
        self.log("🧹 Очистка конфигурации")
        self.remove_added_routes()
        self.restore_dns()

    def run_full_test(self):
        """Запуск полного теста captive portal"""
        self.log("=" * 70)
        self.log("НАЧАЛО ТЕСТИРОВАНИЯ CAPTIVE PORTAL")
        self.log(f"Роутер: {self.router_ip}")
        self.log("=" * 70)

        # Проверяем права
        if not self.check_root_privileges():
            return None

        try:
            # Показываем текущую конфигурацию
            self.show_network_info()

            # Настраиваем DNS через роутер
            if not self.setup_dns_through_router():
                return None

            results = {}

            # 1. Тестируем ICMP ping
            self.log("\n1️⃣ ТЕСТИРОВАНИЕ ICMP PING")
            results['ping'] = self.test_ping_connectivity()

            # 2. Тестируем DNS разрешение
            self.log("\n2️⃣ ТЕСТИРОВАНИЕ DNS РАЗРЕШЕНИЯ")
            results['dns_tests'] = []
            for host in self.test_hosts:
                ip = self.test_dns_resolution(host)
                results['dns_tests'].append({
                    'hostname': host,
                    'success': ip is not None,
                    'ip': ip
                })
                time.sleep(0.5)

            # 3. Тестируем HTTP запросы
            self.log("\n3️⃣ ТЕСТИРОВАНИЕ HTTP ЗАПРОСОВ")
            results['http_tests'] = []

            for url in self.test_urls:
                self.log(f"\n--- Тестирование {url} ---")
                response, result = self.test_http_request(url)
                results['http_tests'].append({
                    'url': url,
                    'success': response is not None,
                    'result': result,
                    'response': response
                })
                time.sleep(1)

            # 4. Анализ результатов
            self.log("\n4️⃣ АНАЛИЗ РЕЗУЛЬТАТОВ")
            self.analyze_results(results)

            return results

        finally:
            # Всегда очищаем конфигурацию
            self.cleanup()

    def analyze_results(self, results):
        """Анализ результатов тестирования"""
        self.log("=" * 70)

        # Анализ ping
        if results['ping']:
            self.log("✅ ICMP: Работает")
        else:
            self.log("❌ ICMP: Заблокирован")

        # Анализ DNS
        successful_dns = sum(1 for test in results['dns_tests'] if test['success'])
        total_dns = len(results['dns_tests'])
        self.log(f"🌐 DNS: {successful_dns}/{total_dns} запросов успешны")

        # Анализ HTTP
        successful_http = sum(1 for test in results['http_tests'] if test['success'])
        total_http = len(results['http_tests'])
        captive_detected = any(test['result'] == 'captive_portal' for test in results['http_tests'] if test['success'])

        self.log(f"📊 HTTP: {successful_http}/{total_http} запросов успешны")

        # Общий вывод
        if captive_detected:
            self.log("🚨 CAPTIVE PORTAL ОБНАРУЖЕН!")
        elif not results['ping'] and successful_http > 0:
            self.log("🚨 ВЕРОЯТЕН CAPTIVE PORTAL: ICMP заблокирован, но HTTP работает")
        elif results['ping'] and successful_http == total_http:
            self.log("✅ ИНТЕРНЕТ ДОСТУПЕН: ICMP и HTTP работают нормально")
        elif not results['ping'] and successful_http == 0:
            self.log("❌ ИНТЕРНЕТ НЕДОСТУПЕН: ICMP и HTTP заблокированы")
        else:
            self.log("❓ НЕОПРЕДЕЛЕННОЕ СОСТОЯНИЕ: Смешанные результаты")

        self.log("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Тестирование captive portal через OpenWrt роутер')
    parser.add_argument('--router', default='192.168.1.1',
                       help='IP адрес роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Таймаут запросов в секундах (по умолчанию: 10)')
    parser.add_argument('--url',
                       help='Тестировать конкретный URL вместо полного теста')
    parser.add_argument('--dns-only', action='store_true',
                       help='Тестировать только DNS разрешение')

    args = parser.parse_args()

    tester = CaptivePortalTester(router_ip=args.router, timeout=args.timeout)

    try:
        if args.dns_only:
            # Только DNS тестирование
            if not tester.check_root_privileges():
                sys.exit(1)
            tester.setup_dns_through_router()
            for host in tester.test_hosts:
                tester.test_dns_resolution(host)
                time.sleep(0.5)
        elif args.url:
            # Тестируем конкретный URL
            if not tester.check_root_privileges():
                sys.exit(1)
            tester.setup_dns_through_router()
            response, result = tester.test_http_request(args.url)
        else:
            # Полное тестирование
            results = tester.run_full_test()
    except KeyboardInterrupt:
        tester.log("\n⚠️ Прервано пользователем")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Неожиданная ошибка: {e}", "ERROR")
        tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
