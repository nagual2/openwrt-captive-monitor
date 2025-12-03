# VS Code Configuration

Настройки VS Code для проекта OpenWrt Captive Monitor.

## 🤖 Claude AI Integration

Полная интеграция Claude (Anthropic) в VS Code!

**Быстрый старт:**
- Читайте [./CLAUDE_README.md](./CLAUDE_README.md) (Quick Start)
- Выполните `.\setup-claude.ps1` для установки API ключа
- Используйте `Ctrl+Shift+C` для открытия Claude Chat

**Документация:**
- [CLAUDE_README.md](./CLAUDE_README.md) - Quick Start (3 мин)
- [CLAUDE_SETUP.md](./CLAUDE_SETUP.md) - Подробная установка (10 мин)
- [CLAUDE_TIPS.md](./CLAUDE_TIPS.md) - Советы и примеры (15 мин)
- [CLAUDE_VISUAL_GUIDE.md](./CLAUDE_VISUAL_GUIDE.md) - Визуальный гайд (10 мин)

**Основные команды:**
- `Ctrl+Shift+C` - Открыть Claude Chat
- `Ctrl+Shift+A` - Быстрый вопрос
- `/refactor` - Рефакторинг кода
- `/tests` - Написать тесты

---

## Установленные файлы

### settings.json
Основные настройки редактора:
- Автоформатирование при сохранении
- Настройки для Markdown, YAML, JSON, Shell
- Интеграция с Git
- Настройки терминала (PowerShell Core по умолчанию)
- Исключения для поиска и файлового наблюдателя
- Доверенные команды для Kiro Agent

### extensions.json
Рекомендуемые расширения:
- **GitHub**: Pull Requests, GitLens
- **Docker**: Docker extension
- **Shell**: ShellCheck, Shell Format
- **YAML**: RedHat YAML
- **Markdown**: All in One, MarkdownLint
- **Remote**: Remote-SSH
- **Utilities**: EditorConfig, Spell Checker (EN/RU)

Установить все: `Ctrl+Shift+P` → "Extensions: Show Recommended Extensions"

### tasks.json
Быстрые задачи (запуск через `Ctrl+Shift+P` → "Tasks: Run Task"):
- **Git**: Status, Create Feature Branch
- **GitHub**: List Workflows, List Runs, PR Status
- **Docker**: List Images, System Info
- **OpenWrt**: Connect to Router, Check Status
- **Tests**: Run Unit Tests, ShellCheck
- **Act**: List Workflows
- **Project**: Show Version

### launch.json
Конфигурации отладки:
- Debug Bash Script (требует расширение bashdb)

### Code Snippets

#### Markdown (markdown.code-snippets)
- `ears` - EARS format requirement
- `property` - Correctness property
- `task` - Task item
- `commit` - Conventional commit message

#### PowerShell (powershell.code-snippets)
- `git-feature` - Git feature branch workflow
- `docker-sdk` - Build OpenWrt SDK Docker image
- `gh-run` - Run GitHub workflow
- `ssh-openwrt` - SSH to OpenWrt test router
- `try-catch` - PowerShell error handling

#### Bash (shellscript.code-snippets)
- `bash-header` - Script header with safety flags
- `bash-error` - Error handling functions
- `bash-cleanup` - Cleanup with trap
- `bash-retry` - Retry with exponential backoff
- `curl-download` - Reliable curl download
- `bash-validate` - Parameter validation

## Использование

### Быстрые команды

**Открыть Command Palette**: `Ctrl+Shift+P`

**Запустить задачу**: `Ctrl+Shift+P` → "Tasks: Run Task"

**Создать feature branch**:
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Выбрать "Git: Create Feature Branch"
3. Ввести имя ветки (без префикса `feature/`)

### Snippets

В Markdown файле начните печатать:
- `ears` → Enter → заполните EARS requirement
- `property` → Enter → заполните correctness property
- `task` → Enter → заполните task item

В PowerShell файле:
- `git-feature` → Enter → полный workflow для feature branch
- `docker-sdk` → Enter → команда сборки Docker образа

В Bash файле:
- `bash-header` → Enter → заголовок скрипта с флагами безопасности
- `bash-retry` → Enter → функция retry с backoff

### Terminal

По умолчанию используется **PowerShell Core (pwsh)**.

Переключить профиль терминала: кликнуть на `+` рядом с терминалом → выбрать профиль.

Доступные профили:
- PowerShell Core (pwsh) - по умолчанию
- WSL - для Linux команд

### Remote-SSH

Подключение к OpenWrt тестовому роутеру:
1. `Ctrl+Shift+P` → "Remote-SSH: Connect to Host..."
2. Выбрать `openwrt-test` или `openwrt`
3. VS Code откроет новое окно с подключением к роутеру

Или через задачу:
- `Ctrl+Shift+P` → "Tasks: Run Task" → "OpenWrt: Connect to Test Router"

## Troubleshooting

### Расширения не установлены
`Ctrl+Shift+P` → "Extensions: Show Recommended Extensions" → "Install All"

### Terminal не использует PowerShell Core
Проверьте что PowerShell 7 установлен: `C:\Program Files\PowerShell\7\pwsh.exe`

### SSH не работает
Проверьте SSH config: `C:\Users\Администратор\.ssh\config`

### Snippets не работают
Убедитесь что открыт файл правильного типа (Markdown, PowerShell, Shell Script)

## Дополнительные настройки

### Добавить свои snippets
Создайте файл `.vscode/{language}.code-snippets` или используйте:
`Ctrl+Shift+P` → "Preferences: Configure User Snippets"

### Изменить настройки
Отредактируйте `.vscode/settings.json` или используйте:
`Ctrl+,` → Settings UI

### Добавить задачи
Отредактируйте `.vscode/tasks.json`
