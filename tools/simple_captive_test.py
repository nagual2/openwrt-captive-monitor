#!/usr/bin/env python3
"""
Простой скрипт для тестирования captive portal через WSL с принудительной маршрутизацией.
"""

import subprocess
import time
import sys
import os

def log(message, level="INFO"):
    """Простое логирование"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def setup_routing(router_ip="192.168.1.1"):
    """Настройка маршрутизации через роутер"""
    log(f"Настройка маршрутизации через {router_ip}")

    try:
        # Настраиваем DNS
        dns_config = f"""nameserver {router_ip}
nameserver 8.8.8.8
nameserver 1.1.1.1
"""

        # Сохраняем оригинальный resolv.conf
        subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], check=True)

        # Устанавливаем новый resolv.conf
        with open('/tmp/resolv.conf.temp', 'w') as f:
            f.write(dns_config)
        subprocess.run(['sudo', 'cp', '/tmp/resolv.conf.temp', '/etc/resolv.conf'], check=True)

        log("✅ DNS настроен через роутер")
        return True

    except Exception as e:
        log(f"❌ Ошибка настройки маршрутизации: {e}", "ERROR")
        return False

def restore_routing():
    """Восстановление оригинальной конфигурации"""
    try:
        if os.path.exists('/etc/resolv.conf.backup'):
            subprocess.run(['sudo', 'cp', '/etc/resolv.conf.backup', '/etc/resolv.conf'])
            subprocess.run(['sudo', 'rm', '/etc/resolv.conf.backup'])
        log("✅ Конфигурация восстановлена")
    except Exception as e:
        log(f"❌ Ошибка восстановления: {e}", "ERROR")

def test_captive_portal():
    """Тестирование captive portal с помощью curl"""
    log("Тестирование captive portal...")

    test_urls = [
        "http://www.msftconnecttest.com/redirect",
        "http://connectivitycheck.gstatic.com/generate_204",
        "http://clients3.google.com/generate_204",
        "http://www.google.com/"
    ]

    captive_detected = False

    for url in test_urls:
        try:
            log(f"Тестирование: {url}")

            # Используем curl для тестирования
            result = subprocess.run([
                'curl', '-s', '-L', '--max-time', '10',
                '--write-out', '%{http_code}|%{url_effective}',
                '--output', '/dev/null', url
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) >= 2:
                    status_code = parts[0]
                    final_url = parts[1]

                    log(f"Статус: {status_code}, Финальный URL: {final_url}")

                    # Проверяем признаки captive portal
                    if final_url != url and ('conn4.com' in final_url or 'portal' in final_url.lower()):
                        log(f"🚨 CAPTIVE PORTAL обнаружен: {final_url}")
                        captive_detected = True

                        # Попробуем получить содержимое портала
                        get_portal_content(final_url)
                        break
                    elif status_code == '204' and 'generate_204' in url:
                        log("✅ Интернет доступен (204 ответ)")
                    elif status_code.startswith('2'):
                        log("✅ HTTP запрос успешен")

        except subprocess.TimeoutExpired:
            log(f"⏰ Таймаут для {url}")
        except Exception as e:
            log(f"❌ Ошибка для {url}: {e}")

    return captive_detected

def get_portal_content(portal_url):
    """Получение содержимого captive portal"""
    log(f"Анализ captive portal: {portal_url}")

    try:
        # Получаем HTML содержимое
        result = subprocess.run([
            'curl', '-s', '--max-time', '10', portal_url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            html_content = result.stdout

            # Сохраняем в файл для анализа
            with open('captive_portal_content.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            log("📄 Содержимое портала сохранено в captive_portal_content.html")

            # Простой анализ содержимого
            analyze_portal_content(html_content)

    except Exception as e:
        log(f"❌ Ошибка получения содержимого портала: {e}")

def analyze_portal_content(html_content):
    """Простой анализ содержимого портала"""
    log("Анализ содержимого captive portal...")

    html_lower = html_content.lower()

    # Ищем формы
    if '<form' in html_lower:
        log("📝 Найдены формы на странице")

    # Ищем кнопки подключения
    connect_keywords = ['connect', 'continue', 'access', 'agree', 'accept']
    found_buttons = []

    for keyword in connect_keywords:
        if keyword in html_lower:
            found_buttons.append(keyword)

    if found_buttons:
        log(f"🔘 Найдены ключевые слова: {', '.join(found_buttons)}")

    # Ищем поля ввода
    if 'type="text"' in html_lower or 'type="password"' in html_lower:
        log("🔐 Найдены поля для ввода учетных данных")

    # Ищем чекбоксы согласия
    if 'type="checkbox"' in html_lower and ('terms' in html_lower or 'agree' in html_lower):
        log("☑️ Найдены чекбоксы согласия с условиями")

def simulate_portal_auth():
    """Симуляция авторизации на портале"""
    log("Попытка авторизации на captive portal...")

    # Читаем сохраненное содержимое портала
    try:
        with open('captive_portal_content.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Ищем action формы
        import re
        form_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html_content, re.IGNORECASE)

        if form_match:
            action_url = form_match.group(1)
            log(f"Найдена форма с action: {action_url}")

            # Попробуем отправить простой POST запрос
            try_simple_post(action_url)

    except FileNotFoundError:
        log("❌ Файл с содержимым портала не найден")
    except Exception as e:
        log(f"❌ Ошибка анализа портала: {e}")

def try_simple_post(action_url):
    """Попытка простой POST авторизации"""
    log(f"Попытка POST запроса к: {action_url}")

    try:
        # Простой POST запрос без данных (для порталов с кнопкой "Connect")
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', '--max-time', '10',
            '--write-out', '%{http_code}|%{url_effective}',
            '--output', '/dev/null', action_url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 2:
                status_code = parts[0]
                final_url = parts[1]

                log(f"POST результат: {status_code}, URL: {final_url}")

                # Проверяем, сработала ли авторизация
                if status_code.startswith('2') or status_code.startswith('3'):
                    log("✅ POST запрос принят, проверяем интернет...")

                    # Проверяем доступность интернета
                    time.sleep(5)
                    check_internet_access()

    except Exception as e:
        log(f"❌ Ошибка POST запроса: {e}")

def check_internet_access():
    """Проверка доступности интернета после авторизации"""
    log("Проверка доступности интернета...")

    try:
        result = subprocess.run([
            'curl', '-s', '--max-time', '5',
            '--write-out', '%{http_code}',
            '--output', '/dev/null',
            'http://www.google.com'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            status_code = result.stdout.strip()
            if status_code.startswith('2'):
                log("🎉 АВТОРИЗАЦИЯ УСПЕШНА! Интернет доступен!")
                return True
            else:
                log(f"❌ Интернет недоступен (код: {status_code})")
        else:
            log("❌ Не удалось проверить доступность интернета")

    except Exception as e:
        log(f"❌ Ошибка проверки интернета: {e}")

    return False

def main():
    log("=" * 60)
    log("ТЕСТИРОВАНИЕ CAPTIVE PORTAL (Простая версия)")
    log("=" * 60)

    router_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.1"

    try:
        # 1. Настройка маршрутизации
        if not setup_routing(router_ip):
            return 1

        # 2. Тестирование captive portal
        captive_detected = test_captive_portal()

        if captive_detected:
            # 3. Попытка авторизации
            simulate_portal_auth()
        else:
            log("✅ Captive portal не обнаружен - интернет доступен")

        return 0

    except KeyboardInterrupt:
        log("\n⚠️ Прервано пользователем")
        return 1
    except Exception as e:
        log(f"❌ Критическая ошибка: {e}")
        return 1
    finally:
        restore_routing()

if __name__ == "__main__":
    sys.exit(main())
