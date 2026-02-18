# Тестирование Captive Portal

## Основные

- NoJS: `wsl python3 tools/test_conn4_portal_nojs.py`.
- Selenium: `wsl python3 tools/captive_portal_wsl_selenium.py`.
- Обязательно: рабочий SOCKS‑прокси, проверка `/_time`, маршруты к `conn4.com`.

## Дополнительные

- Подробные сценарии и чек‑листы: `docs/captive-portal-testing.md`.
