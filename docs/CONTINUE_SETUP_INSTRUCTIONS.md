# Настройка Continue для OpenRouter

## Проблема
Continue установлен, но нужно правильно настроить API ключ OpenRouter.

## Решение

### Вариант 1: Через интерфейс Continue (Рекомендуется)

1. **Откройте Continue**
   - Нажмите `Ctrl+L` или найдите иконку Continue в боковой панели

2. **Откройте настройки**
   - Нажмите на иконку шестеренки (⚙️) в панели Continue
   - Или нажмите `Ctrl+Shift+P` → "Continue: Open config.json"

3. **Добавьте API ключ**
   - В открывшемся файле `config.json` найдите секцию `models`
   - Для каждой модели замените `"apiKey": ""` на ваш ключ:

   ```json
   "apiKey": "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"
   ```

4. **Сохраните файл**
   - `Ctrl+S`

5. **Перезагрузите Continue**
   - Закройте и откройте панель Continue

### Вариант 2: Автоматическая настройка через скрипт

```powershell
# Запустите этот скрипт
.\setup-continue-api-key.ps1
```

### Вариант 3: Ручное редактирование

1. **Найдите файл конфигурации Continue:**
   - Windows: `%USERPROFILE%\.continue\config.json`
   - Или: `.continue\config.json` в корне проекта

2. **Откройте файл и добавьте API ключ:**

```json
{
  "models": [
    {
      "title": "Grok 4.1 Fast (Free)",
      "provider": "openrouter",
      "model": "x-ai/grok-4.1-fast:free",
      "apiBase": "https://openrouter.ai/api/v1",
      "apiKey": "ВАШ_API_КЛЮЧ_ЗДЕСЬ",
      "contextLength": 8192
    }
  ]
}
```

3. **Сохраните и перезагрузите VS Code**

## Проверка настройки

После настройки:

1. Откройте Continue (`Ctrl+L`)
2. Выберите модель "Grok 4.1 Fast (Free)" из выпадающего списка
3. Напишите тестовое сообщение: "Привет!"
4. Если модель отвечает - настройка успешна ✅

## Troubleshooting

### Модели не отображаются
- Перезагрузите VS Code
- Проверьте что расширение Continue активно
- Откройте настройки Continue и проверьте конфигурацию

### Ошибка авторизации
```powershell
# Проверьте API ключ
$env:OPENROUTER_API_KEY = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
Write-Host $env:OPENROUTER_API_KEY
```

### Continue не запускается
- Переустановите расширение:
  ```powershell
  code --uninstall-extension Continue.continue
  code --install-extension Continue.continue
  ```

## Альтернатива: Использовать скрипты

Если Continue не работает, используйте наши PowerShell скрипты:

```powershell
# Загрузить команды
. .\OPENROUTER_QUICK_COMMANDS.ps1

# Использовать модели
Test-Grok "ваш вопрос"
Test-Coder "напиши код"
```

Эти скрипты работают напрямую через OpenRouter API без расширений.

---

**Ваш API ключ OpenRouter:**
```
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
```

Скопируйте его и вставьте в настройки Continue.
