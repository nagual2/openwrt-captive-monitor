# Настройка Claude в VS Code

## 📋 Шаги установки

### 1. Установите расширение Claude для VS Code

Откройте командную палитру (`Ctrl+Shift+P`) и выполните:
```
Extensions: Install Extensions
```

Поищите и установите:
- **Claude for VS Code** (от Anthropic)

Или установите через командную строку:
```powershell
code --install-extension anthropic.claude-for-vscode
```

### 2. Получите API ключ Claude

1. Перейдите на [https://console.anthropic.com](https://console.anthropic.com)
2. Создайте аккаунт (или войдите)
3. Перейдите в раздел **API Keys**
4. Создайте новый API ключ
5. Скопируйте его значение

### 3. Настройте переменную окружения

Выполните в PowerShell:
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'your-api-key-here', 'User')
```

Замените `your-api-key-here` на ваш реальный API ключ.

### 4. Перезагрузите VS Code

Закройте и откройте VS Code заново, чтобы переменная окружения была прочитана.

### 5. Проверьте конфигурацию

В PowerShell выполните:
```powershell
$env:ANTHROPIC_API_KEY
```

Должен вывести ваш API ключ (или пусто, если не установлен).

## 🎯 Использование Claude в VS Code

### Открытие Claude Chat
1. Нажмите `Ctrl+Shift+C` или выберите в левой панели иконку Claude
2. Начните диалог с ассистентом

### Контекстное меню
- Выделите код и нажмите `Ctrl+Shift+A` для быстрого вопроса
- Используйте команды: "Объясни", "Отрефакторь", "Исправь ошибку"

### Встроенные команды
```
/explain    - Объяснить код
/refactor   - Рефакторинг
/tests      - Написать тесты
/optimize   - Оптимизация
```

## 🔐 Безопасность API ключа

⚠️ **ВАЖНО:**
- Никогда не коммитьте API ключ в репозиторий
- Не передавайте ключ третьим лицам
- Храните ключ в переменных окружения, а не в исходном коде
- Используйте `.gitignore` для исключения чувствительных файлов

## 📝 Файлы конфигурации

Конфигурация Claude находится в:
- `.vscode/settings.json` - основные настройки
- `.vscode/extensions.json` - рекомендуемые расширения

## 🚀 Дополнительные возможности

### Интеграция с GitHub Copilot
Вы можете использовать оба ассистента одновременно:
- Claude для глубокого анализа и рефакторинга
- GitHub Copilot для быстрого автодополнения

### Keyboard Shortcuts
Добавьте в `.vscode/keybindings.json`:
```json
[
  {
    "key": "ctrl+shift+c",
    "command": "claude.togglePanel"
  },
  {
    "key": "ctrl+shift+a",
    "command": "claude.quickQuestion"
  }
]
```

## 🔧 Решение проблем

### Claude не подключается
1. Проверьте API ключ: `$env:ANTHROPIC_API_KEY`
2. Убедитесь, что расширение установлено: `code --list-extensions | grep anthropic`
3. Перезагрузите VS Code
4. Проверьте интернет-соединение

### Ошибка аутентификации
- Убедитесь, что ключ скопирован полностью
- Проверьте срок действия ключа в консоли API
- Создайте новый ключ при необходимости

### Медленная работа
- Проверьте качество интернет-соединения
- Сократите размер контекста (выделяйте меньше кода)
- Используйте более специфичные запросы

## 📚 Полезные ресурсы

- [Claude Documentation](https://docs.anthropic.com)
- [VS Code Extension Docs](https://code.visualstudio.com/api)
- [API Keys Management](https://console.anthropic.com/account/keys)

## ✅ Проверка настройки

Выполните команду для проверки:
```powershell
# Проверка переменной окружения
$env:ANTHROPIC_API_KEY | Write-Host

# Проверка установленных расширений
code --list-extensions | Select-String anthropic

# Проверка конфига VS Code
Get-Content .vscode/settings.json | Select-String anthropic
```

---

Успешной работы с Claude! 🎉
