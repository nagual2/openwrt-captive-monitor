# Быстрая настройка среды разработки (Quick Dev Setup)

Этот документ содержит перечень необходимых инструментов и расширений для быстрого развертывания рабочего окружения проекта `openwrt-captive-monitor`.

---

## 1. Системные требования (System Requirements)

### Базовое окружение (Core Environment)
*   **Операционная система:** Windows 10/11 (Build 19044+) или Linux.
*   **WSL 2:** Версия 2.6.2.0 или выше (Kernel 6.6+).
*   **Терминал:** PowerShell 7+ или Windows Terminal.

### Установленное ПО (Installed Software)

#### 1. Python & Библиотеки
*   **Python:** 3.12.10 (рекомендуется 3.10+)
*   **Основные зависимости (Core Dependencies):**
    *   `pyserial` (3.5) — Взаимодействие с последовательным портом.
    *   `PyYAML` (6.0.3) — Работа с YAML конфигурациями.
    *   `Jinja2` (3.1.6) — Шаблонизация.
    *   `requests` (2.32.5) — HTTP запросы.
    *   `python-dotenv` (1.2.1) — Управление переменными окружения.
    *   `yamllint` (1.37.1) — Линтинг YAML файлов.
    *   `git-filter-repo` (2.47.0) — Продвинутая работа с историей Git.

*   **Тестирование и автоматизация (Testing & Automation):**
    *   `pytest` (9.0.1) — Фреймворк для тестирования.
    *   `selenium` (4.39.0) — Браузерная автоматизация.
    *   `webdriver-manager` (4.0.2) — Управление драйверами браузеров.
    *   `hypothesis` (6.148.3) — Property-based тестирование.

*   **AI и ML (AI/ML Stack):**
    *   `torch` (2.9.1), `torchaudio`, `torchvision` (CPU versions).
    *   `transformers` (4.57.3), `tokenizers`.
    *   `google-genai` (1.52.0), `huggingface-hub`.
    *   `numpy` (2.3.5), `pillow`, `networkx`.

#### 2. Инфраструктура
*   **Docker:** Docker Desktop или Docker Engine (для Linux).
    *   *Примечание:* В Windows среде убедитесь, что Docker Desktop запущен и интеграция с WSL включена.
*   **Git:** Версия 2.30+.
*   **Bun:** Среда выполнения JS (для MCP сервера).

---

## 2. Среда разработки (IDE)

Рекомендуется использовать **VS Code** или **Trae IDE**.

### Обязательные расширения (Essential Extensions)

Для автоматической установки можно использовать команду:
```bash
code --install-extension ms-vscode-remote.vscode-remote-extensionpack
code --install-extension ms-python.python
code --install-extension ms-azuretools.vscode-docker
code --install-extension eamodio.gitlens
code --install-extension timonwong.shellcheck
code --install-extension foxundermoon.shell-format
code --install-extension editorconfig.editorconfig
```

#### Полный список по категориям:

**Удаленная разработка (Remote Development):**
*   `ms-vscode-remote.remote-wsl` — Работа в WSL.
*   `ms-vscode-remote.remote-ssh` — Подключение к удаленным серверам (OpenWrt роутерам).
*   `ms-vscode-remote.remote-containers` — Разработка в контейнерах.

**Языки и синтаксис:**
*   **Python:**
    *   `ms-python.python`
    *   `ms-python.vscode-pylance`
*   **Shell / Bash:**
    *   `timonwong.shellcheck` — Линтер для скриптов.
    *   `foxundermoon.shell-format` — Форматирование sh-файлов.
*   **PowerShell:**
    *   `ms-vscode.powershell` — Для скриптов автоматизации на Windows.
*   **Конфигурация:**
    *   `redhat.vscode-yaml` — Подсветка YAML (GitHub Actions).
    *   `editorconfig.editorconfig` — Поддержка единого стиля кодирования.

**Инструменты:**
*   **Docker:** `ms-azuretools.vscode-docker` — Управление контейнерами.
*   **Git:** `eamodio.gitlens`, `donjayamanne.githistory` — Улучшенная работа с историей.
*   **Markdown:** `yzhang.markdown-all-in-one`, `davidanson.vscode-markdownlint` — Документация.

**AI Ассистенты (Опционально):**
*   `continue.continue` — Локальный/облачный AI ассистент.
*   `github.copilot` — GitHub Copilot.

---

## 3. Настройка MCP Сервера (Model Context Protocol)

Для работы интеллектуальных функций Trae/VS Code с контекстом проекта используется `ultrascript-tools`.

1.  Убедитесь, что **Bun** установлен (см. раздел 1).
2.  Проверьте конфигурацию в `.trae/mcp.json` (или глобальном конфиге Claude/Continue):

```json
{
  "mcpServers": {
    "ultrascript-tools": {
      "command": "bun",
      "args": [
        "C:\\path\\to\\ultrascript-tools-mcp\\dist\\index.js",
        "C:\\path\\to\\project\\root"
      ],
      "disabled": false
    }
  }
}
```

---

## 4. Быстрый старт (Quick Start)

1.  Клонируйте репозиторий:
    ```bash
    git clone https://github.com/nagual2/openwrt-captive-monitor.git
    cd openwrt-captive-monitor
    ```
2.  Откройте проект в VS Code / Trae:
    ```bash
    code .
    ```
3.  (Опционально) Установите рекомендуемые расширения, если VS Code предложит это сделать (на основе `.vscode/extensions.json` при наличии).
4.  Проверьте окружение:
    ```bash
    # Проверка Python
    python --version
    
    # Проверка Docker
    docker --version
    
    # Проверка работы скриптов
    ./scripts/test-lib-utilities.sh
    ```
