# Git Workflow через WSL1

## Обзор

Этот документ описывает использование скрипта `scripts/git-wsl.sh` для работы с Git через WSL1 (Windows Subsystem for Linux) из Windows окружения.

## Мотивация

### Проблемы работы с Git в Windows

1. **Проблемы с путями**: Различия между Windows (`C:\`) и Linux (`/mnt/c/`) путями
2. **Кодировка**: Проблемы с кириллицей в commit messages
3. **Line endings**: Различия CRLF vs LF
4. **Производительность**: Git в WSL работает быстрее чем Git for Windows

### Решение

Единый скрипт для работы с Git через WSL1 с автоматической конвертацией путей и валидацией commit messages.

## Установка

### Требования

1. **WSL1**: Windows Subsystem for Linux версии 1
2. **Git в WSL**: Установленный Git внутри WSL
3. **GitHub CLI (опционально)**: Для работы с pull requests

### Установка WSL1

```powershell
# В PowerShell с правами администратора
wsl --install
```

### Установка Git в WSL

```bash
# В WSL терминале
sudo apt-get update
sudo apt-get install git
```

### Установка GitHub CLI в WSL

```bash
# В WSL терминале
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Аутентификация
gh auth login
```

## Использование

### Базовые команды

#### Создание ветки

```bash
# Создать ветку от main
./scripts/git-wsl.sh create-branch feature/optimize-build

# Создать ветку от другой ветки
./scripts/git-wsl.sh create-branch feature/new-feature develop
```

#### Создание коммита

```bash
# Простой коммит
./scripts/git-wsl.sh commit "Add Docker SDK optimization"

# Коммит с указанием файлов
./scripts/git-wsl.sh commit "Update CI workflow" ".github/workflows/ci.yml"

# Коммит со ссылкой на issue
./scripts/git-wsl.sh commit "Fix build error #123"
# Результат: "Fix build error (#123)"
```

#### Создание Pull Request

```bash
# Простой PR
./scripts/git-wsl.sh create-pr "Optimize build with Docker SDK"

# PR с описанием
./scripts/git-wsl.sh create-pr "Optimize build with Docker SDK" "This PR adds Docker SDK images to speed up builds"

# PR в другую ветку
./scripts/git-wsl.sh create-pr "Add new feature" "Feature description" develop
```

#### Мерж Pull Request

```bash
# Squash merge (по умолчанию)
./scripts/git-wsl.sh merge-pr 123

# Merge commit
./scripts/git-wsl.sh merge-pr 123 merge

# Rebase merge
./scripts/git-wsl.sh merge-pr 123 rebase
```

#### Push изменений

```bash
# Push текущей ветки
./scripts/git-wsl.sh push

# Push конкретной ветки
./scripts/git-wsl.sh push feature/optimize-build

# Force push (с защитой)
./scripts/git-wsl.sh push feature/optimize-build true
```

#### Статус репозитория

```bash
./scripts/git-wsl.sh status
```

### Продвинутое использование

#### Debug режим

```bash
# Включить детальное логирование
DEBUG=1 ./scripts/git-wsl.sh create-branch feature/test
```

#### Автоматизация workflow

```bash
#!/bin/bash
# Пример автоматизированного workflow

# 1. Создать ветку
./scripts/git-wsl.sh create-branch feature/optimize-build

# 2. Внести изменения
# ... редактирование файлов ...

# 3. Создать коммит
./scripts/git-wsl.sh commit "Add Docker SDK images for faster builds"

# 4. Push изменений
./scripts/git-wsl.sh push

# 5. Создать PR
./scripts/git-wsl.sh create-pr "Optimize CI build with Docker SDK" "This PR reduces build time from 5 to 2 minutes"
```

## Функции скрипта

### check_wsl()

Проверяет доступность WSL1.

```bash
if ! check_wsl; then
    echo "WSL not available"
    exit 1
fi
```

### convert_path()

Конвертирует Windows пути в Linux пути.

```bash
# Windows -> Linux
convert_path "C:\Users\Admin\project"
# Результат: /mnt/c/Users/Admin/project

# Уже Linux путь
convert_path "/mnt/c/Users/Admin/project"
# Результат: /mnt/c/Users/Admin/project
```

### wsl_exec()

Выполняет команду в WSL1.

```bash
wsl_exec "ls -la"
wsl_exec "git status"
```

### wsl_git()

Выполняет git команду в WSL1.

```bash
wsl_git "status"
wsl_git "log --oneline -5"
```

### format_issue_ref()

Форматирует ссылки на issues в commit messages.

```bash
format_issue_ref "Fix bug #123"
# Результат: "Fix bug (#123)"

format_issue_ref "Close 456"
# Результат: "Close (#456)"
```

**Поддерживаемые ключевые слова:**
- fix, fixes
- close, closes
- resolve, resolves
- ref, refs
- see

## Валидация commit messages

### Правила

1. **Только английский язык**: Commit messages должны быть на английском
2. **Формат ссылок на issues**: Автоматическое форматирование `#123` → `(#123)`
3. **Conventional Commits**: Рекомендуется использовать формат

### Примеры правильных commit messages

```bash
# Хорошо
./scripts/git-wsl.sh commit "feat: Add Docker SDK optimization"
./scripts/git-wsl.sh commit "fix: Resolve build error (#123)"
./scripts/git-wsl.sh commit "docs: Update README with new workflow"
./scripts/git-wsl.sh commit "refactor: Simplify CI configuration"

# Плохо (будет отклонено)
./scripts/git-wsl.sh commit "Добавил оптимизацию"  # Кириллица
./scripts/git-wsl.sh commit "修复错误"              # Не английский
```

### Conventional Commits формат

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Типы:**
- `feat`: Новая функциональность
- `fix`: Исправление бага
- `docs`: Изменения в документации
- `style`: Форматирование, отступы
- `refactor`: Рефакторинг кода
- `test`: Добавление тестов
- `chore`: Обновление зависимостей, конфигурации

## Конвертация путей

### Windows → Linux

| Windows путь | Linux путь (WSL) |
|--------------|------------------|
| `C:\Users\Admin` | `/mnt/c/Users/Admin` |
| `D:\Projects\repo` | `/mnt/d/Projects/repo` |
| `C:\Program Files` | `/mnt/c/Program Files` |

### Обработка пробелов

Скрипт корректно обрабатывает пути с пробелами:

```bash
convert_path "C:\Program Files\Git"
# Результат: /mnt/c/Program Files/Git
```

### Обработка обратных слешей

```bash
convert_path "C:\Users\Admin\Documents\project"
# Результат: /mnt/c/Users/Admin/Documents/project
```

## Troubleshooting

### WSL не найден

**Проблема**: `WSL (wsl.exe) not found`

**Решение:**
1. Установите WSL: `wsl --install`
2. Перезагрузите компьютер
3. Проверьте: `wsl --version`

### Git не найден в WSL

**Проблема**: `git: command not found`

**Решение:**
```bash
# В WSL терминале
sudo apt-get update
sudo apt-get install git
```

### GitHub CLI не найден

**Проблема**: `GitHub CLI (gh) not found in WSL`

**Решение:**
```bash
# В WSL терминале
sudo apt install gh
gh auth login
```

### Ошибка аутентификации GitHub

**Проблема**: `authentication failed`

**Решение:**
```bash
# В WSL терминале
gh auth login
# Следуйте инструкциям для аутентификации
```

### Commit message с кириллицей

**Проблема**: `Commit message contains non-ASCII characters`

**Решение:**
- Используйте только английский язык в commit messages
- Переведите сообщение на английский
- Используйте транслитерацию если необходимо

### Проблемы с путями

**Проблема**: Неправильная конвертация путей

**Решение:**
1. Используйте абсолютные пути
2. Проверьте формат пути (Windows vs Linux)
3. Включите debug режим: `DEBUG=1 ./scripts/git-wsl.sh ...`

### Permission denied

**Проблема**: `Permission denied` при выполнении скрипта

**Решение:**
```bash
# Сделать скрипт исполняемым
chmod +x scripts/git-wsl.sh
```

## Интеграция с IDE

### Visual Studio Code

Добавьте задачи в `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Git WSL: Create Branch",
      "type": "shell",
      "command": "./scripts/git-wsl.sh",
      "args": ["create-branch", "${input:branchName}"],
      "problemMatcher": []
    },
    {
      "label": "Git WSL: Commit",
      "type": "shell",
      "command": "./scripts/git-wsl.sh",
      "args": ["commit", "${input:commitMessage}"],
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "branchName",
      "type": "promptString",
      "description": "Branch name"
    },
    {
      "id": "commitMessage",
      "type": "promptString",
      "description": "Commit message"
    }
  ]
}
```

### PowerShell алиасы

Добавьте в `$PROFILE`:

```powershell
# Git WSL алиасы
function Git-WSL-Branch { bash scripts/git-wsl.sh create-branch $args }
function Git-WSL-Commit { bash scripts/git-wsl.sh commit $args }
function Git-WSL-PR { bash scripts/git-wsl.sh create-pr $args }
function Git-WSL-Push { bash scripts/git-wsl.sh push $args }

Set-Alias gwb Git-WSL-Branch
Set-Alias gwc Git-WSL-Commit
Set-Alias gwpr Git-WSL-PR
Set-Alias gwp Git-WSL-Push
```

Использование:

```powershell
gwb feature/new-feature
gwc "Add new feature"
gwpr "Add new feature" "Description"
gwp
```

## Лучшие практики

1. **Всегда используйте английский**: Commit messages только на английском
2. **Conventional Commits**: Следуйте формату для единообразия
3. **Ссылки на issues**: Всегда ссылайтесь на issues в commit messages
4. **Атомарные коммиты**: Один коммит = одно логическое изменение
5. **Описательные PR**: Подробно описывайте изменения в PR
6. **Squash merge**: Используйте squash для чистой истории

## Примеры workflow

### Feature разработка

```bash
# 1. Создать feature ветку
./scripts/git-wsl.sh create-branch feature/docker-sdk-optimization

# 2. Внести изменения
# ... редактирование файлов ...

# 3. Коммиты по мере разработки
./scripts/git-wsl.sh commit "feat: Add Dockerfile for SDK images"
./scripts/git-wsl.sh commit "feat: Add build workflow for SDK images"
./scripts/git-wsl.sh commit "docs: Add documentation for Docker SDK"

# 4. Push изменений
./scripts/git-wsl.sh push

# 5. Создать PR
./scripts/git-wsl.sh create-pr "Optimize CI with Docker SDK images" "This PR adds pre-built Docker SDK images to reduce build time from 5 to 2 minutes"

# 6. После review - мерж
./scripts/git-wsl.sh merge-pr 123 squash
```

### Hotfix workflow

```bash
# 1. Создать hotfix ветку от main
./scripts/git-wsl.sh create-branch hotfix/fix-build-error main

# 2. Исправить проблему
# ... редактирование файлов ...

# 3. Коммит с ссылкой на issue
./scripts/git-wsl.sh commit "fix: Resolve SDK download timeout (#456)"

# 4. Push и создать PR
./scripts/git-wsl.sh push
./scripts/git-wsl.sh create-pr "Fix SDK download timeout" "Fixes #456"

# 5. Быстрый мерж
./scripts/git-wsl.sh merge-pr 124 squash
```

## Ссылки

- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [GitHub CLI](https://cli.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
