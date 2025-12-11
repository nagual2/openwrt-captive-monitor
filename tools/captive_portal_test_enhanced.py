#!/usr/bin/env python3
"""
Улучшенный скрипт для тестирования и авторизации на captive portal.
Специально адаптирован для работы с conn4.com порталом.
"""

import subprocess
import time
import sys
import os
import re
import json

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

def detect_captive_portal():
    """Обнаружение captive portal"""
    log("Обнаружение captive portal...")

    test_urls = [
        "http://connectivitycheck.gstatic.com/generate_204",
        "http://clients3.google.com/generate_204",
        "http://www.msftconnecttest.com/redirect",
        "http://www.google.com/"
    ]

    portal_info = None

    for url in test_urls:
        try:
            log(f"Тестирование: {url}")

            # Получаем полный ответ с заголовками
            result = subprocess.run([
                'curl', '-s', '-i', '--max-time', '10', url
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                response = result.stdout

                # Разделяем заголовки и тело
                if '\r\n\r\n' in response:
                    headers, body = response.split('\r\n\r\n', 1)
                elif '\n\n' in response:
                    headers, body = response.split('\n\n', 1)
                else:
                    headers = response
                    body = ""

                # Анализируем ответ
                portal_info = analyze_response(url, headers, body)
                if portal_info:
                    break

        except subprocess.TimeoutExpired:
            log(f"⏰ Таймаут для {url}")
        except Exception as e:
            log(f"❌ Ошибка для {url}: {e}")

    return portal_info

def analyze_response(url, headers, body):
    """Анализ HTTP ответа для обнаружения captive portal"""

    # Ищем статус код
    status_match = re.search(r'HTTP/[\d.]+\s+(\d+)', headers)
    status_code = status_match.group(1) if status_match else "unknown"

    log(f"Статус код: {status_code}")

    # Ищем Location заголовок
    location_match = re.search(r'location:\s*(.+)', headers, re.IGNORECASE)
    location = location_match.group(1).strip() if location_match else None

    if location:
        log(f"Location: {location}")

    # Проверяем признаки captive portal
    if status_code == "302" and location and "conn4.com" in location:
        log(f"🚨 CAPTIVE PORTAL обнаружен: {location}")
        return {
            'detected': True,
            'portal_url': location,
            'original_url': url,
            'status_code': status_code,
            'method': 'redirect'
        }

    # Проверяем meta refresh в HTML
    if body and 'meta' in body.lower() and 'refresh' in body.lower():
        refresh_match = re.search(r'content=["\'][^"\']*url=([^"\']*)["\']', body, re.IGNORECASE)
        if refresh_match:
            refresh_url = refresh_match.group(1)
            if "conn4.com" in refresh_url:
                log(f"🚨 CAPTIVE PORTAL обнаружен через meta refresh: {refresh_url}")
                return {
                    'detected': True,
                    'portal_url': refresh_url,
                    'original_url': url,
                    'status_code': status_code,
                    'method': 'meta_refresh'
                }

    # Проверяем ожидаемые ответы
    if "generate_204" in url:
        if status_code == "204" and not body.strip():
            log("✅ Интернет доступен (204 No Content)")
        else:
            log(f"⚠️ Неожиданный ответ для {url}: {status_code}")
            if body.strip():
                log(f"Тело ответа: {body[:200]}...")

    return None

def get_portal_page(portal_url):
    """Получение страницы captive portal"""
    log(f"Получение страницы captive portal: {portal_url}")

    try:
        result = subprocess.run([
            'curl', '-s', '--max-time', '15', portal_url
        ], capture_output=True, text=True, timeout=20)

        if result.returncode == 0:
            html_content = result.stdout

            # Сохраняем в файл
            with open('captive_portal_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            log("📄 Страница портала сохранена в captive_portal_page.html")

            return html_content

    except Exception as e:
        log(f"❌ Ошибка получения страницы портала: {e}")

    return None

def analyze_portal_page(html_content):
    """Анализ страницы captive portal"""
    log("Анализ страницы captive portal...")

    if not html_content:
        return None

    analysis = {
        'forms': [],
        'buttons': [],
        'inputs': [],
        'links': [],
        'auth_methods': []
    }

    # Ищем формы
    form_matches = re.finditer(r'<form[^>]*>(.*?)</form>', html_content, re.DOTALL | re.IGNORECASE)
    for form_match in form_matches:
        form_html = form_match.group(0)

        # Извлекаем action
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        action = action_match.group(1) if action_match else ""

        # Извлекаем method
        method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        method = method_match.group(1) if method_match else "GET"

        analysis['forms'].append({
            'action': action,
            'method': method.upper(),
            'html': form_html[:200] + "..." if len(form_html) > 200 else form_html
        })

        log(f"📝 Найдена форма: {method.upper()} {action}")

    # Ищем кнопки
    button_matches = re.finditer(r'<(?:button|input)[^>]*(?:type=["\'](?:button|submit)["\']|>.*?</button>)', html_content, re.IGNORECASE)
    for button_match in button_matches:
        button_html = button_match.group(0)

        # Извлекаем текст кнопки
        text_match = re.search(r'>([^<]+)<', button_html)
        text = text_match.group(1).strip() if text_match else ""

        # Извлекаем value
        value_match = re.search(r'value=["\']([^"\']*)["\']', button_html, re.IGNORECASE)
        value = value_match.group(1) if value_match else ""

        button_text = text or value
        if button_text:
            analysis['buttons'].append(button_text)
            log(f"🔘 Найдена кнопка: '{button_text}'")

    # Ищем поля ввода
    input_matches = re.finditer(r'<input[^>]*>', html_content, re.IGNORECASE)
    for input_match in input_matches:
        input_html = input_match.group(0)

        # Извлекаем тип
        type_match = re.search(r'type=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
        input_type = type_match.group(1) if type_match else "text"

        # Извлекаем имя
        name_match = re.search(r'name=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
        name = name_match.group(1) if name_match else ""

        if input_type.lower() in ['text', 'password', 'email', 'checkbox', 'submit']:
            analysis['inputs'].append({
                'type': input_type,
                'name': name
            })
            log(f"📝 Найдено поле: {input_type} '{name}'")

    # Определяем методы авторизации
    button_texts = [btn.lower() for btn in analysis['buttons']]

    if any(keyword in ' '.join(button_texts) for keyword in ['connect', 'continue', 'access']):
        analysis['auth_methods'].append('simple_connect')
        log("🔓 Обнаружен метод: простое подключение")

    if any(inp['type'].lower() in ['text', 'password', 'email'] for inp in analysis['inputs']):
        analysis['auth_methods'].append('credentials')
        log("🔐 Обнаружен метод: авторизация по учетным данным")

    if any(inp['type'].lower() == 'checkbox' for inp in analysis['inputs']):
        analysis['auth_methods'].append('terms_acceptance')
        log("☑️ Обнаружен метод: принятие условий")

    return analysis

def attempt_authentication(portal_info, analysis):
    """Попытка авторизации на captive portal"""
    log("Начало попытки авторизации...")

    if not analysis or not analysis['auth_methods']:
        log("❌ Не найдены методы авторизации")
        return False

    # Пробуем методы по приоритету
    for method in analysis['auth_methods']:
        log(f"Попытка метода: {method}")

        if method == 'simple_connect':
            if try_simple_connect(analysis):
                return True

        elif method == 'terms_acceptance':
            if try_terms_acceptance(analysis):
                return True

        elif method == 'credentials':
            log("⚠️ Требуются учетные данные (пропускаем)")

    return False

def try_simple_connect(analysis):
    """Попытка простого подключения"""
    log("Попытка простого подключения...")

    if not analysis['forms']:
        log("❌ Не найдены формы для отправки")
        return False

    # Берем первую форму
    form = analysis['forms'][0]
    action_url = form['action']
    method = form['method']

    if not action_url:
        log("❌ Не найден action URL формы")
        return False

    log(f"Отправка {method} запроса к: {action_url}")

    try:
        if method == 'POST':
            # Простой POST без данных
            result = subprocess.run([
                'curl', '-s', '-X', 'POST', '--max-time', '15',
                '--write-out', '%{http_code}|%{url_effective}',
                '--output', '/dev/null', action_url
            ], capture_output=True, text=True, timeout=20)
        else:
            # GET запрос
            result = subprocess.run([
                'curl', '-s', '--max-time', '15',
                '--write-out', '%{http_code}|%{url_effective}',
                '--output', '/dev/null', action_url
            ], capture_output=True, text=True, timeout=20)

        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 2:
                status_code = parts[0]
                final_url = parts[1]

                log(f"Результат: {status_code}, URL: {final_url}")

                # Проверяем успех
                if status_code.startswith('2') or status_code.startswith('3'):
                    log("✅ Запрос принят, проверяем интернет...")
                    time.sleep(5)
                    return check_internet_access()

    except Exception as e:
        log(f"❌ Ошибка отправки запроса: {e}")

    return False

def try_terms_acceptance(analysis):
    """Попытка принятия условий"""
    log("Попытка принятия условий...")

    # Ищем чекбоксы и формы
    checkboxes = [inp for inp in analysis['inputs'] if inp['type'].lower() == 'checkbox']

    if not checkboxes or not analysis['forms']:
        log("❌ Не найдены чекбоксы или формы")
        return False

    form = analysis['forms'][0]
    action_url = form['action']

    # Формируем данные для отправки
    form_data = []
    for checkbox in checkboxes:
        if checkbox['name']:
            form_data.extend(['-d', f"{checkbox['name']}=on"])

    if not form_data:
        log("❌ Не найдены данные для отправки")
        return False

    log(f"Отправка формы с принятием условий к: {action_url}")

    try:
        cmd = ['curl', '-s', '-X', 'POST', '--max-time', '15'] + form_data + [
            '--write-out', '%{http_code}|%{url_effective}',
            '--output', '/dev/null', action_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 2:
                status_code = parts[0]
                final_url = parts[1]

                log(f"Результат: {status_code}, URL: {final_url}")

                if status_code.startswith('2') or status_code.startswith('3'):
                    log("✅ Форма отправлена, проверяем интернет...")
                    time.sleep(5)
                    return check_internet_access()

    except Exception as e:
        log(f"❌ Ошибка отправки формы: {e}")

    return False

def check_internet_access():
    """Проверка доступности интернета"""
    log("Проверка доступности интернета...")

    test_urls = [
        "http://www.google.com",
        "http://connectivitycheck.gstatic.com/generate_204"
    ]

    for url in test_urls:
        try:
            result = subprocess.run([
                'curl', '-s', '--max-time', '10',
                '--write-out', '%{http_code}',
                '--output', '/dev/null', url
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                status_code = result.stdout.strip()
                log(f"Тест {url}: {status_code}")

                if status_code.startswith('2'):
                    log("🎉 АВТОРИЗАЦИЯ УСПЕШНА! Интернет доступен!")
                    return True

        except Exception as e:
            log(f"❌ Ошибка проверки {url}: {e}")

    log("❌ Интернет по-прежнему недоступен")
    return False

def main():
    log("=" * 70)
    log("УЛУЧШЕННОЕ ТЕСТИРОВАНИЕ CAPTIVE PORTAL")
    log("=" * 70)

    router_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.1"

    try:
        # 1. Настройка маршрутизации
        if not setup_routing(router_ip):
            return 1

        # 2. Обнаружение captive portal
        portal_info = detect_captive_portal()

        if not portal_info or not portal_info['detected']:
            log("✅ Captive portal не обнаружен - интернет доступен")
            return 0

        # 3. Получение страницы портала
        html_content = get_portal_page(portal_info['portal_url'])

        # 4. Анализ страницы
        analysis = analyze_portal_page(html_content)

        # 5. Попытка авторизации
        if attempt_authentication(portal_info, analysis):
            log("🎉 Авторизация завершена успешно!")
            return 0
        else:
            log("❌ Авторизация не удалась")
            return 1

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
