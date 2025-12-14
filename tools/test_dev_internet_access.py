#!/usr/bin/env python3
"""
Быстрое тестирование доступа к интернету через dev роутер
========================================================

Простой скрипт для проверки доступности интернета через dev роутер (192.168.1.1).
Используется для быстрой диагностики перед запуском основных тестов.

Использование:
    # Базовая проверка
    wsl python3 tools/test_dev_internet_access.py

    # С указанием IP роутера
    wsl python3 tools/test_dev_internet_access.py --router 192.168.1.1

    # Подробный режим
    wsl python3 tools/test_dev_internet_access.py --verbose

Автор: OpenWrt Captive Monitor Project
"""

import sys
import os
import argparse
import subprocess
import time
from datetime import datetime

# Проверяем, что мы в WSL
is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("❌ Этот скрипт должен запускаться только в WSL!")
    print("Используйте: wsl python3 tools/test_dev_internet_access.py")
    sys.exit(1)

class DevInternetTester:
    """Тестер доступа к интернету через dev роутер"""

    def __init__(self, router_ip="192.168.1.1", verbose=False):
        self.router_ip = router_ip
        self.verbose = verbose
        self.results = {}

    def log(self, message, level="INFO"):
        """Простое логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def verbose_log(self, message):
        """Логирование в подробном режиме"""
        if self.verbose:
            self.log(message, "DEBUG")

    def test_router_ping(self):
        """Тестирование доступности роутера"""
        self.log(f"Проверка доступности роутера {self.router_ip}...")

        try:
            result = subprocess.run(['ping', '-c', '3', '-W', '2', self.router_ip],
                                  capture_output=True, text=True, timeout=10)

            success = result.returncode == 0

            if success:
                # Извлекаем статистику пинга
                lines = result.stdout.split('\n')
                stats_line = [line for line in lines if 'packet loss' in line]
                if stats_line:
                    self.verbose_log(f"Ping статистика: {stats_line[0].strip()}")

                self.log("✅ Роутер доступен")
            else:
                self.log("❌ Роутер недоступен")
                self.verbose_log(f"Ping ошибка: {result.stderr}")

            self.results['router_ping'] = success
            return success

        except Exception as e:
            self.log(f"❌ Ошибка ping роутера: {e}")
            self.results['router_ping'] = False
            return False

    def setup_dns_via_router(self):
        """Настройка DNS через роутер"""
        self.log("Настройка DNS через роутер...")

        try:
            # Сохраняем оригинальную конфигурацию
            with open('/etc/resolv.conf', 'r') as f:
                original_resolv = f.read()

            # Создаем новую конфигурацию
            dns_config = f"""# Временная настройка для тестирования через dev роутер
nameserver {self.router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

            with open('/tmp/resolv.conf.dev_test', 'w') as f:
                f.write(dns_config)

            # Применяем новую конфигурацию
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup_dev_test'], check=True)
            subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.dev_test', '/etc/resolv.conf'], check=True)

            self.log("✅ DNS настроен через роутер")
            self.results['dns_setup'] = True
            return True

        except Exception as e:
            self.log(f"❌ Ошибка настройки DNS: {e}")
            self.results['dns_setup'] = False
            return False

    def test_dns_resolution(self):
        """Тестирование DNS разрешения"""
        self.log("Тестирование DNS разрешения...")

        test_domains = ['google.com', 'github.com', 'cloudflare.com']
        successful_resolutions = 0

        for domain in test_domains:
            try:
                result = subprocess.run(['nslookup', domain], capture_output=True, text=True, timeout=10)

                success = result.returncode == 0 and 'NXDOMAIN' not in result.stdout

                if success:
                    successful_resolutions += 1
                    self.verbose_log(f"✅ DNS {domain}: успешно")

                    # Извлекаем IP адрес
                    lines = result.stdout.split('\n')
                    address_lines = [line for line in lines if 'Address:' in line and '#' not in line]
                    if address_lines:
                        ip = address_lines[0].split('Address:')[1].strip()
                        self.verbose_log(f"   IP: {ip}")
                else:
                    self.verbose_log(f"❌ DNS {domain}: неудача")

            except Exception as e:
                self.verbose_log(f"❌ DNS {domain}: ошибка {e}")

        dns_success = successful_resolutions > 0
        self.log(f"DNS разрешение: {successful_resolutions}/{len(test_domains)} доменов")

        if dns_success:
            self.log("✅ DNS работает")
        else:
            self.log("❌ DNS не работает")

        self.results['dns_resolution'] = {
            'success': dns_success,
            'resolved_domains': successful_resolutions,
            'total_domains': len(test_domains)
        }

        return dns_success

    def test_http_connectivity(self):
        """Тестирование HTTP подключения"""
        self.log("Тестирование HTTP подключения...")

        test_urls = [
            'http://www.google.com',
            'http://connectivitycheck.gstatic.com/generate_204',
            'http://detectportal.firefox.com/canonical.html',
            'http://www.msftconnecttest.com/connecttest.txt'
        ]

        successful_requests = 0

        for url in test_urls:
            try:
                result = subprocess.run(['curl', '-s', '--max-time', '10', '--write-out', '%{http_code}',
                                       '--output', '/dev/null', url],
                                      capture_output=True, text=True, timeout=15)

                http_code = result.stdout.strip()
                success = result.returncode == 0 and http_code.startswith(('2', '3'))

                if success:
                    successful_requests += 1
                    self.verbose_log(f"✅ HTTP {url}: {http_code}")
                else:
                    self.verbose_log(f"❌ HTTP {url}: {http_code} (код возврата: {result.returncode})")

            except Exception as e:
                self.verbose_log(f"❌ HTTP {url}: ошибка {e}")

        http_success = successful_requests > 0
        self.log(f"HTTP подключение: {successful_requests}/{len(test_urls)} URL доступны")

        if http_success:
            self.log("✅ HTTP подключение работает")
        else:
            self.log("❌ HTTP подключение не работает")

        self.results['http_connectivity'] = {
            'success': http_success,
            'successful_requests': successful_requests,
            'total_requests': len(test_urls)
        }

        return http_success

    def test_captive_portal_detection(self):
        """Тестирование обнаружения captive portal"""
        self.log("Тестирование обнаружения captive portal...")

        # URL-ы для проверки captive portal
        captive_test_urls = [
            'http://connectivitycheck.gstatic.com/generate_204',
            'http://clients3.google.com/generate_204',
            'http://detectportal.firefox.com/canonical.html'
        ]

        captive_detected = False
        redirect_info = {}

        for url in captive_test_urls:
            try:
                # Получаем полный ответ с заголовками
                result = subprocess.run(['curl', '-s', '-i', '--max-time', '10', url],
                                      capture_output=True, text=True, timeout=15)

                if result.returncode == 0:
                    response = result.stdout

                    # Проверяем статус код
                    status_line = response.split('\n')[0] if response else ""

                    # Ищем редиректы
                    if 'HTTP/' in status_line and ('302' in status_line or '301' in status_line):
                        # Ищем Location заголовок
                        lines = response.split('\n')
                        location_line = [line for line in lines if line.lower().startswith('location:')]

                        if location_line:
                            location = location_line[0].split(':', 1)[1].strip()

                            # Проверяем признаки captive portal
                            captive_indicators = ['conn4.com', 'portal', 'captive', 'auth', 'login']
                            if any(indicator in location.lower() for indicator in captive_indicators):
                                captive_detected = True
                                redirect_info[url] = location
                                self.verbose_log(f"🚨 Captive portal обнаружен: {url} -> {location}")
                            else:
                                self.verbose_log(f"↗️ Редирект (не captive): {url} -> {location}")
                        else:
                            self.verbose_log(f"↗️ Редирект без Location: {url}")

                    elif 'HTTP/' in status_line and '204' in status_line:
                        self.verbose_log(f"✅ Прямой доступ: {url} (204 No Content)")

                    elif 'HTTP/' in status_line and '200' in status_line:
                        self.verbose_log(f"✅ Прямой доступ: {url} (200 OK)")

                    else:
                        self.verbose_log(f"❓ Неожиданный ответ: {url} - {status_line}")

            except Exception as e:
                self.verbose_log(f"❌ Ошибка проверки captive portal {url}: {e}")

        if captive_detected:
            self.log("🚨 Captive portal обнаружен!")
            for url, redirect in redirect_info.items():
                self.log(f"   {url} -> {redirect}")
        else:
            self.log("✅ Captive portal не обнаружен - прямой доступ к интернету")

        self.results['captive_portal'] = {
            'detected': captive_detected,
            'redirects': redirect_info
        }

        return not captive_detected  # Успех = отсутствие captive portal

    def restore_dns_config(self):
        """Восстановление оригинальной DNS конфигурации"""
        self.log("Восстановление оригинальной DNS конфигурации...")

        try:
            if os.path.exists('/etc/resolv.conf.backup_dev_test'):
                subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup_dev_test', '/etc/resolv.conf'], check=True)
                subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup_dev_test'], check=True)
                self.log("✅ DNS конфигурация восстановлена")
            else:
                self.log("⚠️ Backup файл DNS не найден")

            # Очищаем временные файлы
            for temp_file in ['/tmp/resolv.conf.dev_test']:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            self.results['dns_restore'] = True
            return True

        except Exception as e:
            self.log(f"❌ Ошибка восстановления DNS: {e}")
            self.results['dns_restore'] = False
            return False

    def run_full_test(self):
        """Запуск полного тестирования"""
        self.log("=" * 60)
        self.log("ТЕСТИРОВАНИЕ ДОСТУПА К ИНТЕРНЕТУ ЧЕРЕЗ DEV РОУТЕР")
        self.log("=" * 60)

        start_time = time.time()

        try:
            # Последовательность тестов
            tests = [
                ("Ping роутера", self.test_router_ping),
                ("Настройка DNS", self.setup_dns_via_router),
                ("DNS разрешение", self.test_dns_resolution),
                ("HTTP подключение", self.test_http_connectivity),
                ("Обнаружение captive portal", self.test_captive_portal_detection)
            ]

            overall_success = True

            for test_name, test_func in tests:
                self.log(f"\n--- {test_name} ---")
                success = test_func()

                if not success:
                    overall_success = False
                    # Продолжаем тестирование даже при неудаче

            # Итоговый отчет
            end_time = time.time()
            duration = end_time - start_time

            self.log("\n" + "=" * 60)
            self.log("ИТОГОВЫЙ ОТЧЕТ")
            self.log("=" * 60)

            for test_name, result in self.results.items():
                if isinstance(result, bool):
                    status = "✅ PASS" if result else "❌ FAIL"
                    self.log(f"{status}: {test_name}")
                elif isinstance(result, dict) and 'success' in result:
                    status = "✅ PASS" if result['success'] else "❌ FAIL"
                    self.log(f"{status}: {test_name}")

            self.log(f"\nВремя выполнения: {duration:.1f} секунд")

            if overall_success:
                self.log("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Интернет доступен через dev роутер.")
            else:
                self.log("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. Проверьте конфигурацию.")

            return overall_success

        finally:
            # Всегда восстанавливаем DNS конфигурацию
            self.restore_dns_config()


def main():
    parser = argparse.ArgumentParser(
        description='Быстрое тестирование доступа к интернету через dev роутер',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                           # Базовая проверка
  %(prog)s --router 192.168.1.1      # С указанием IP роутера
  %(prog)s --verbose                 # Подробный режим

Этот скрипт:
1. Проверяет доступность dev роутера
2. Настраивает DNS через роутер
3. Тестирует DNS разрешение
4. Проверяет HTTP подключение
5. Обнаруживает captive порталы
6. Восстанавливает оригинальную конфигурацию
        """
    )

    parser.add_argument('--router', default='192.168.1.1',
                       help='IP адрес dev роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')

    args = parser.parse_args()

    # Создаем тестер
    tester = DevInternetTester(
        router_ip=args.router,
        verbose=args.verbose
    )

    try:
        # Запускаем тестирование
        success = tester.run_full_test()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        # Пытаемся восстановить DNS
        tester.restore_dns_config()
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        # Пытаемся восстановить DNS
        tester.restore_dns_config()
        sys.exit(1)


if __name__ == "__main__":
    main()
