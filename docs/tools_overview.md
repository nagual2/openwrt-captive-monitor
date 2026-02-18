# Инструменты

## Основные

- Captive portal: `captive_portal_wsl_selenium.py`, `test_conn4_portal_nojs.py`.
- Администрирование роутеров и консолей: `serial_console.py`.
- Анализ логов и трасс: утилиты в `tools/analysis/`.

## Дополнительные

- Сборка и CI: скрипты в `scripts/` (например, `build_ipk.sh`, `run_openwrt_vm.sh`).
- Поддерживающие скрипты keepalive: `captive_portal_keepalive.py`.
 - Диагностика сети и HTTP: `mitmproxy`, `HTTPie`, `curl` (WSL, pipx для CLI).
 - Качество Python‑кода: `Ruff` (линтер), `MyPy` (типы) — запуск через WSL.
 - Индексы для экономии контекста: `build_symbol_map.py`, `build_snippet_index.py`, `query_snippets.py` (в `tools/analysis/`).
 - Git/GitHub инструменты: `git`, `gh`, `git-lfs`, `lazygit`, `gitui` — использовать в WSL.
