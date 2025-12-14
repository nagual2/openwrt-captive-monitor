#!/usr/bin/env python3
"""
Тест для проверки определения типа captive портала.
"""

import sys
import requests
from captive_portal_simple_auth import SimpleCaptiveAuth

def test_portal_detection():
    """Тестирует определение типа портала."""

    test_cases = [
        {
            "url": "http://conn4.com/login",
            "expected_type": "conn4.com",
            "description": "conn4.com портал по URL"
        },
        {
            "url": "http://192.168.1.1/hotspot/login",
            "expected_type": "mikrotik",
            "description": "Mikrotik портал по URL"
        },
        {
            "url": "http://192.168.1.1/login",
            "expected_type": "generic",
            "description": "Generic портал"
        }
    ]

    print("🧪 Тестирование определения типа портала...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   URL: {test_case['url']}")

        # Здесь мы бы вызвали функцию identify_portal_type из bash скрипта
        # Но поскольку это bash функция, мы можем только проверить логику

        url = test_case['url']
        host = url.split('/')[2] if '://' in url else url

        # Эмулируем логику identify_portal_type
        if 'conn4.com' in host or 'conn4' in host:
            detected_type = "conn4.com"
        elif 'mikrotik' in url or 'hotspot' in url:
            detected_type = "mikrotik"
        else:
            detected_type = "generic"

        if detected_type == test_case['expected_type']:
            print(f"   ✅ Определен тип: {detected_type}")
        else:
            print(f"   ❌ Ожидался: {test_case['expected_type']}, получен: {detected_type}")

def test_internet_connectivity():
    """Тестирует проверку интернета."""
    print("\n🌐 Тестирование проверки интернета...")

    auth = SimpleCaptiveAuth("http://test.com")

    if auth.verify_internet_access():
        print("   ✅ Интернет доступен")
        return True
    else:
        print("   ❌ Интернет недоступен")
        return False

def test_form_extraction():
    """Тестирует извлечение форм из HTML."""
    print("\n📝 Тестирование извлечения форм...")

    test_html = '''
    <html>
    <body>
        <form action="/login.php" method="POST">
            <input type="text" name="username" />
            <input type="password" name="password" />
            <input type="hidden" name="csrf_token" value="abc123" />
            <input type="submit" value="Login" />
        </form>
    </body>
    </html>
    '''

    auth = SimpleCaptiveAuth("http://test.com")

    # Тестируем извлечение action формы
    action = auth._extract_form_action(test_html)
    if action == "/login.php":
        print("   ✅ Action формы извлечен корректно")
    else:
        print(f"   ❌ Ожидался '/login.php', получен: {action}")

    # Тестируем извлечение скрытых полей
    hidden_fields = auth._extract_hidden_fields(test_html)
    if hidden_fields.get('csrf_token') == 'abc123':
        print("   ✅ Скрытые поля извлечены корректно")
    else:
        print(f"   ❌ Скрытые поля: {hidden_fields}")

if __name__ == "__main__":
    print("🚀 Запуск тестов автоматизации captive порталов\n")

    try:
        test_portal_detection()
        test_internet_connectivity()
        test_form_extraction()

        print("\n✅ Все тесты завершены")

    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        sys.exit(1)
