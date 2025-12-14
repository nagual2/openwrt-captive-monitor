#!/usr/bin/env python3
"""
Тестирование консолидированного скрипта авторизации captive portal
================================================================

Этот скрипт тестирует работу captive_portal_wsl_selenium.py в различных сценариях:
- Проверка доступа к интернету на dev среде
- Тестирование обнаружения captive порталов
- Проверка различных методов авторизации
- Валидация восстановления сетевых настроек

Использование:
    # Полное тестирование
    wsl python3 tools/test_captive_portal_wsl_selenium.py

    # Только проверка интернета
    wsl python3 tools/test_captive_portal_wsl_selenium.py --test internet

    # Тестирование с учетными данными
    wsl python3 tools/test_captive_portal_wsl_selenium.py --username "12345" --password "secret"

    # Отладочный режим
    wsl python3 tools/test_captive_portal_wsl_selenium.py --debug

Требования:
    - WSL 2
    - Доступ к dev роутеру (192.168.1.1)
    - Python 3.6+
    - selenium, webdriver-manager
    - sudo права для настройки сети

Автор: OpenWrt Captive Monitor Project
"""

import sys
import os
import time
import argparse
import logging
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Проверяем, что мы в WSL
is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("❌ Этот скрипт должен запускаться только в WSL!")
    print("Используйте: wsl python3 tools/test_captive_portal_wsl_selenium.py")
    sys.exit(1)

class CaptivePortalTester:
    """Тестер для консолидированного скрипта авторизации captive portal"""

    def __init__(self, dev_router_ip="192.168.1.1", debug=False):
        self.dev_router_ip = dev_router_ip
        self.debug = debug
        self.test_results = {}
        self.start_time = datetime.now()

        # Настройка логирования
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

        # Путь к тестируемому скрипту
        self.script_path = Path(__file__).parent / "captive_portal_wsl_selenium.py"
        if not self.script_path.exists():
            raise FileNotFoundError(f"Скрипт не найден: {self.script_path}")

    def log_test_result(self, test_name, success, details=None):
        """Логирование результата теста"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status}: {test_name}")

        self.test_results[test_name] = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }

        if details and self.debug:
            for key, value in details.items():
                self.logger.debug(f"  {key}: {value}")

    def check_prerequisites(self):
        """Проверка предварительных условий"""
        self.logger.info("=== ПРОВЕРКА ПРЕДВАРИТЕЛЬНЫХ УСЛОВИЙ ===")

        # Проверка доступности dev роутера
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', self.dev_router_ip],
                                  capture_output=True, text=True, timeout=5)
            router_available = result.returncode == 0
            self.log_test_result("Dev router accessibility", router_available,
                               {'router_ip': self.dev_router_ip, 'ping_result': result.returncode})
        except Exception as e:
            self.log_test_result("Dev router accessibility", False, {'error': str(e)})
            return False

        # Проверка sudo прав
        try:
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
            sudo_available = result.returncode == 0
            self.log_test_result("Sudo privileges", sudo_available)
        except Exception as e:
            self.log_test_result("Sudo privileges", False, {'error': str(e)})
            if not sudo_available:
                self.logger.error("Настройте sudo: wsl bash tools/setup_wsl_sudo.sh")
                return False

        # Проверка Python зависимостей
        try:
            import selenium
            from webdriver_manager.chrome import ChromeDriverManager
            self.log_test_result("Python dependencies", True,
                               {'selenium_version': selenium.__version__})
        except ImportError as e:
            self.log_test_result("Python dependencies", False, {'error': str(e)})
            self.logger.error("Установите зависимости: pip3 install selenium webdriver-manager")
            return False

        # Проверка Chrome
        chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
                       "/usr/bin/chromium-browser", "/usr/bin/chromium"]
        chrome_found = any(os.path.exists(path) for path in chrome_paths)
        self.log_test_result("Chrome browser", chrome_found)

        if not chrome_found:
            self.logger.error("Установите Chrome: sudo apt install google-chrome-stable")
            return False

        return router_available and sudo_available and chrome_found

    def test_internet_connectivity_dev(self):
        """Тестирование доступа к интернету через dev роутер"""
        self.logger.info("=== ТЕСТИРОВАНИЕ ДОСТУПА К ИНТЕРНЕТУ ЧЕРЕЗ DEV ===")

        # Сохраняем текущую конфигурацию DNS
        original_resolv = None
        try:
            with open('/etc/resolv.conf', 'r') as f:
                original_resolv = f.read()
        except Exception as e:
            self.log_test_result("Save original DNS config", False, {'error': str(e)})
            return False

        try:
            # Настраиваем DNS через dev роутер
            dns_config = f"""# Временная настройка для тестирования
nameserver {self.dev_router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

            with open('/tmp/resolv.conf.test', 'w') as f:
                f.write(dns_config)

            subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.test', '/etc/resolv.conf'], check=True)
            self.log_test_result("Configure DNS via dev router", True)

            # Тестируем DNS разрешение
            test_hosts = ['google.com', 'github.com', 'cloudflare.com']
            dns_results = {}

            for host in test_hosts:
                try:
                    result = subprocess.run(['nslookup', host], capture_output=True, text=True, timeout=10)
                    dns_success = result.returncode == 0 and 'NXDOMAIN' not in result.stdout
                    dns_results[host] = dns_success

                    if self.debug:
                        self.logger.debug(f"DNS lookup {host}: {'SUCCESS' if dns_success else 'FAILED'}")

                except Exception as e:
                    dns_results[host] = False
                    if self.debug:
                        self.logger.debug(f"DNS lookup {host} error: {e}")

            dns_overall = any(dns_results.values())
            self.log_test_result("DNS resolution via dev router", dns_overall, dns_results)

            # Тестируем HTTP доступность
            test_urls = [
                'http://www.google.com',
                'http://connectivitycheck.gstatic.com/generate_204',
                'http://detectportal.firefox.com/canonical.html'
            ]

            http_results = {}
            for url in test_urls:
                try:
                    result = subprocess.run(['curl', '-s', '--max-time', '10', '--write-out', '%{http_code}',
                                           '--output', '/dev/null', url],
                                          capture_output=True, text=True, timeout=15)

                    http_code = result.stdout.strip()
                    http_success = result.returncode == 0 and http_code.startswith(('2', '3'))
                    http_results[url] = {'code': http_code, 'success': http_success}

                    if self.debug:
                        self.logger.debug(f"HTTP test {url}: {http_code} ({'SUCCESS' if http_success else 'FAILED'})")

                except Exception as e:
                    http_results[url] = {'error': str(e), 'success': False}

            http_overall = any(result['success'] for result in http_results.values())
            self.log_test_result("HTTP connectivity via dev router", http_overall, http_results)

            return dns_overall and http_overall

        except Exception as e:
            self.log_test_result("Internet connectivity test", False, {'error': str(e)})
            return False

        finally:
            # Восстанавливаем оригинальную конфигурацию DNS
            if original_resolv:
                try:
                    with open('/tmp/resolv.conf.original', 'w') as f:
                        f.write(original_resolv)
                    subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.original', '/etc/resolv.conf'], check=True)
                    self.log_test_result("Restore original DNS config", True)
                except Exception as e:
                    self.logger.error(f"Ошибка восстановления DNS: {e}")

    def test_script_help(self):
        """Тестирование вывода справки скрипта"""
        self.logger.info("=== ТЕСТИРОВАНИЕ СПРАВКИ СКРИПТА ===")

        try:
            result = subprocess.run(['python3', str(self.script_path), '--help'],
                                  capture_output=True, text=True, timeout=10)

            help_success = result.returncode == 0 and 'usage:' in result.stdout
            help_details = {
                'return_code': result.returncode,
                'has_usage': 'usage:' in result.stdout,
                'has_examples': 'Примеры использования:' in result.stdout,
                'output_length': len(result.stdout)
            }

            self.log_test_result("Script help output", help_success, help_details)
            return help_success

        except Exception as e:
            self.log_test_result("Script help output", False, {'error': str(e)})
            return False

    def test_script_basic_run(self):
        """Тестирование базового запуска скрипта"""
        self.logger.info("=== ТЕСТИРОВАНИЕ БАЗОВОГО ЗАПУСКА ===")

        try:
            # Запускаем скрипт с коротким таймаутом для быстрого тестирования
            cmd = ['python3', str(self.script_path), '--timeout', '10', '--debug']

            self.logger.info(f"Запуск команды: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            # Анализируем вывод
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')

            analysis = {
                'return_code': result.returncode,
                'has_network_setup': any('маршрутизации' in line for line in output_lines),
                'has_chrome_setup': any('Chrome' in line for line in output_lines),
                'has_portal_detection': any('portal' in line.lower() for line in output_lines),
                'has_cleanup': any('восстановлен' in line for line in output_lines),
                'output_lines': len([line for line in output_lines if line.strip()])
            }

            # Скрипт может завершиться с кодом 0 (интернет доступен) или 1 (авторизация не удалась)
            # Оба варианта считаются успешным выполнением теста
            basic_success = result.returncode in [0, 1] and analysis['has_network_setup']

            self.log_test_result("Script basic execution", basic_success, analysis)

            if self.debug:
                self.logger.debug("=== ВЫВОД СКРИПТА ===")
                for line in output_lines[:20]:  # Показываем первые 20 строк
                    if line.strip():
                        self.logger.debug(line)
                if len(output_lines) > 20:
                    self.logger.debug(f"... и еще {len(output_lines) - 20} строк")

            return basic_success

        except subprocess.TimeoutExpired:
            self.log_test_result("Script basic execution", False, {'error': 'Timeout after 60 seconds'})
            return False
        except Exception as e:
            self.log_test_result("Script basic execution", False, {'error': str(e)})
            return False

    def test_script_with_credentials(self, username=None, password=None):
        """Тестирование скрипта с учетными данными"""
        if not username or not password:
            self.logger.info("Пропуск тестирования с учетными данными (не предоставлены)")
            return True

        self.logger.info("=== ТЕСТИРОВАНИЕ С УЧЕТНЫМИ ДАННЫМИ ===")

        try:
            cmd = ['python3', str(self.script_path),
                   '--username', username, '--password', password,
                   '--timeout', '15', '--debug']

            self.logger.info(f"Запуск с учетными данными: username={username}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

            output_lines = result.stdout.split('\n') + result.stderr.split('\n')

            analysis = {
                'return_code': result.returncode,
                'has_credentials_usage': any('учетными данными' in line for line in output_lines),
                'has_auth_attempt': any('авторизац' in line.lower() for line in output_lines),
                'has_success_check': any('интернет' in line.lower() for line in output_lines)
            }

            # Успех если скрипт выполнился и попытался использовать учетные данные
            creds_success = result.returncode in [0, 1] and (
                analysis['has_credentials_usage'] or analysis['has_auth_attempt']
            )

            self.log_test_result("Script with credentials", creds_success, analysis)
            return creds_success

        except subprocess.TimeoutExpired:
            self.log_test_result("Script with credentials", False, {'error': 'Timeout after 90 seconds'})
            return False
        except Exception as e:
            self.log_test_result("Script with credentials", False, {'error': str(e)})
            return False

    def test_network_cleanup(self):
        """Тестирование очистки сетевых настроек"""
        self.logger.info("=== ТЕСТИРОВАНИЕ ОЧИСТКИ СЕТЕВЫХ НАСТРОЕК ===")

        try:
            # Сохраняем текущую конфигурацию
            with open('/etc/resolv.conf', 'r') as f:
                original_resolv = f.read()

            # Запускаем скрипт и прерываем его
            cmd = ['python3', str(self.script_path), '--timeout', '5']

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Ждем немного, затем прерываем
            time.sleep(8)
            process.terminate()

            # Ждем завершения
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()

            # Проверяем, что конфигурация восстановлена
            time.sleep(2)

            with open('/etc/resolv.conf', 'r') as f:
                current_resolv = f.read()

            # Проверяем, что нет временных настроек
            cleanup_success = (
                'Временная настройка для captive portal' not in current_resolv and
                not os.path.exists('/etc/resolv.conf.backup')
            )

            cleanup_details = {
                'original_length': len(original_resolv),
                'current_length': len(current_resolv),
                'has_temp_config': 'Временная настройка' in current_resolv,
                'has_backup_file': os.path.exists('/etc/resolv.conf.backup')
            }

            self.log_test_result("Network cleanup after interruption", cleanup_success, cleanup_details)
            return cleanup_success

        except Exception as e:
            self.log_test_result("Network cleanup after interruption", False, {'error': str(e)})
            return False

    def test_chrome_availability(self):
        """Тестирование доступности Chrome и WebDriver"""
        self.logger.info("=== ТЕСТИРОВАНИЕ CHROME И WEBDRIVER ===")

        try:
            # Проверяем Chrome
            chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]
            chrome_path = None

            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break

            if not chrome_path:
                self.log_test_result("Chrome binary", False, {'checked_paths': chrome_paths})
                return False

            # Проверяем версию Chrome
            result = subprocess.run([chrome_path, '--version'], capture_output=True, text=True, timeout=10)
            chrome_version = result.stdout.strip() if result.returncode == 0 else "Unknown"

            self.log_test_result("Chrome binary", True, {'path': chrome_path, 'version': chrome_version})

            # Проверяем WebDriver Manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                webdriver_success = os.path.exists(driver_path)

                self.log_test_result("WebDriver Manager", webdriver_success, {'driver_path': driver_path})

            except Exception as e:
                self.log_test_result("WebDriver Manager", False, {'error': str(e)})
                webdriver_success = False

            return webdriver_success

        except Exception as e:
            self.log_test_result("Chrome and WebDriver test", False, {'error': str(e)})
            return False

    def generate_test_report(self):
        """Генерация отчета о тестировании"""
        self.logger.info("=== ГЕНЕРАЦИЯ ОТЧЕТА ТЕСТИРОВАНИЯ ===")

        end_time = datetime.now()
        duration = end_time - self.start_time

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests

        report = {
            'test_session': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'dev_router_ip': self.dev_router_ip
            },
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'test_results': self.test_results
        }

        # Сохраняем отчет
        report_file = f"captive_portal_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Выводим краткий отчет
        self.logger.info("=" * 60)
        self.logger.info("ОТЧЕТ О ТЕСТИРОВАНИИ")
        self.logger.info("=" * 60)
        self.logger.info(f"Всего тестов: {total_tests}")
        self.logger.info(f"Успешно: {passed_tests}")
        self.logger.info(f"Неудачно: {failed_tests}")
        self.logger.info(f"Процент успеха: {report['summary']['success_rate']:.1f}%")
        self.logger.info(f"Длительность: {duration.total_seconds():.1f} секунд")
        self.logger.info(f"Отчет сохранен: {report_file}")

        if failed_tests > 0:
            self.logger.info("\nНеудачные тесты:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    self.logger.info(f"  ❌ {test_name}")
                    if 'error' in result.get('details', {}):
                        self.logger.info(f"     Ошибка: {result['details']['error']}")

        return report

    def run_all_tests(self, username=None, password=None, test_filter=None):
        """Запуск всех тестов"""
        self.logger.info("=" * 70)
        self.logger.info("ТЕСТИРОВАНИЕ CAPTIVE PORTAL WSL SELENIUM SCRIPT")
        self.logger.info("=" * 70)

        # Определяем какие тесты запускать
        all_tests = [
            ('prerequisites', self.check_prerequisites),
            ('internet', self.test_internet_connectivity_dev),
            ('help', self.test_script_help),
            ('chrome', self.test_chrome_availability),
            ('basic_run', self.test_script_basic_run),
            ('credentials', lambda: self.test_script_with_credentials(username, password)),
            ('cleanup', self.test_network_cleanup)
        ]

        # Фильтруем тесты если указан фильтр
        if test_filter:
            all_tests = [(name, func) for name, func in all_tests if name == test_filter]
            if not all_tests:
                self.logger.error(f"Неизвестный тест: {test_filter}")
                return False

        # Запускаем тесты
        overall_success = True

        for test_name, test_func in all_tests:
            try:
                self.logger.info(f"\n--- Запуск теста: {test_name} ---")
                success = test_func()
                if not success:
                    overall_success = False

            except Exception as e:
                self.logger.error(f"Критическая ошибка в тесте {test_name}: {e}")
                self.log_test_result(test_name, False, {'critical_error': str(e)})
                overall_success = False

        # Генерируем отчет
        report = self.generate_test_report()

        return overall_success


def main():
    parser = argparse.ArgumentParser(
        description='Тестирование консолидированного скрипта авторизации captive portal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # Полное тестирование
  %(prog)s --test internet                    # Только проверка интернета
  %(prog)s --username "12345" --password "secret" # С учетными данными
  %(prog)s --debug                            # Отладочный режим

Доступные тесты для --test:
  prerequisites  - проверка предварительных условий
  internet      - проверка доступа к интернету через dev
  help          - тестирование справки скрипта
  chrome        - проверка Chrome и WebDriver
  basic_run     - базовый запуск скрипта
  credentials   - тестирование с учетными данными
  cleanup       - проверка очистки сетевых настроек
        """
    )

    parser.add_argument('--dev-router', default='192.168.1.1',
                       help='IP адрес dev роутера (по умолчанию: 192.168.1.1)')
    parser.add_argument('--username', help='Имя пользователя для тестирования авторизации')
    parser.add_argument('--password', help='Пароль для тестирования авторизации')
    parser.add_argument('--test', choices=['prerequisites', 'internet', 'help', 'chrome',
                                          'basic_run', 'credentials', 'cleanup'],
                       help='Запустить только указанный тест')
    parser.add_argument('--debug', action='store_true',
                       help='Включить отладочный режим')

    args = parser.parse_args()

    # Создаем тестер
    tester = CaptivePortalTester(
        dev_router_ip=args.dev_router,
        debug=args.debug
    )

    try:
        # Запускаем тесты
        success = tester.run_all_tests(
            username=args.username,
            password=args.password,
            test_filter=args.test
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
