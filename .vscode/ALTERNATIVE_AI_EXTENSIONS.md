# Альтернативные AI расширения для работы с OpenRouter

## 1. Continue (Рекомендуется) ⭐

**ID расширения:** `Continue.continue`

### Установка:
```powershell
code --install-extension Continue.continue
```

### Особенности:
- ✅ Полная поддержка OpenRouter
- ✅ Бесплатное и open-source
- ✅ Чат в боковой панели
- ✅ Автодополнение кода
- ✅ Кастомные команды
- ✅ Работает с бесплатными моделями

### Конфигурация:
Файл: `.vscode/continue-config.json` (уже создан)

### Использование:
1. Установите расширение
2. Откройте боковую панель Continue (Ctrl+L)
3. Выберите модель из списка
4. Начните чат

---

## 2. Cline (бывший Claude Dev)

**ID расширения:** `saoudrizwan.claude-dev`

### Установка:
```powershell
code --install-extension saoudrizwan.claude-dev
```

### Особенности:
- ✅ Поддержка OpenRouter через API
- ✅ Автономное выполнение задач
- ✅ Работа с файлами
- ✅ Терминал интеграция

### Конфигурация:
```json
{
  "cline.apiProvider": "openrouter",
  "cline.openRouterApiKey": "${OPENROUTER_API_KEY}",
  "cline.openRouterModel": "x-ai/grok-4.1-fast:free"
}
```

---

## 3. Cody (от Sourcegraph)

**ID расширения:** `sourcegraph.cody-ai`

### Установка:
```powershell
code --install-extension sourcegraph.cody-ai
```

### Особенности:
- ✅ Поддержка кастомных LLM
- ✅ Контекст всего проекта
- ✅ Автодополнение
- ⚠️ Требует настройку для OpenRouter

### Конфигурация:
```json
{
  "cody.customConfiguration": {
    "provider": "openrouter",
    "apiKey": "${OPENROUTER_API_KEY}",
    "endpoint": "https://openrouter.ai/api/v1"
  }
}
```

---

## 4. Twinny

**ID расширения:** `rjmacarthy.twinny`

### Установка:
```powershell
code --install-extension rjmacarthy.twinny
```

### Особенности:
- ✅ Легковесное
- ✅ Поддержка OpenRouter
- ✅ Автодополнение
- ✅ Чат

### Конфигурация:
```json
{
  "twinny.apiProvider": "openrouter",
  "twinny.apiKey": "${OPENROUTER_API_KEY}",
  "twinny.apiHostname": "https://openrouter.ai/api/v1",
  "twinny.chatModelName": "x-ai/grok-4.1-fast:free"
}
```

---

## 5. Privy (Privacy-focused)

**ID расширения:** `srikanth.privy`

### Установка:
```powershell
code --install-extension srikanth.privy
```

### Особенности:
- ✅ Фокус на приватность
- ✅ Поддержка множества провайдеров
- ✅ Локальное хранение истории

---

## Сравнительная таблица

| Расширение | OpenRouter | Бесплатно | Чат | Автодополнение | Сложность |
|------------|-----------|-----------|-----|----------------|-----------|
| Continue   | ✅ Да     | ✅ Да     | ✅  | ✅             | Легко     |
| Cline      | ✅ Да     | ✅ Да     | ✅  | ❌             | Средне    |
| Cody       | ⚠️ Настройка | ✅ Да  | ✅  | ✅             | Сложно    |
| Twinny     | ✅ Да     | ✅ Да     | ✅  | ✅             | Легко     |
| Privy      | ✅ Да     | ✅ Да     | ✅  | ❌             | Легко     |

---

## Рекомендация

**Для начала используйте Continue:**

1. Самое простое в настройке
2. Отличная поддержка OpenRouter
3. Активное сообщество
4. Регулярные обновления

**Установка и настройка Continue:**

```powershell
# 1. Установить расширение
code --install-extension Continue.continue

# 2. Конфигурация уже создана в .vscode/continue-config.json

# 3. Перезагрузить VS Code
# Ctrl+Shift+P -> "Developer: Reload Window"

# 4. Открыть Continue
# Ctrl+L или иконка в боковой панели

# 5. Выбрать модель "Grok 4.1 Fast (Free)"

# 6. Начать чат!
```

---

## Быстрая установка всех расширений

```powershell
# Установить все рекомендуемые расширения
code --install-extension Continue.continue
code --install-extension saoudrizwan.claude-dev
code --install-extension rjmacarthy.twinny

Write-Host "✅ Расширения установлены!" -ForegroundColor Green
Write-Host "Перезагрузите VS Code для применения изменений" -ForegroundColor Yellow
```

---

## Troubleshooting

### Continue не видит модели:
1. Проверьте `.vscode/continue-config.json`
2. Убедитесь что `OPENROUTER_API_KEY` установлен
3. Перезагрузите VS Code

### Ошибка авторизации:
```powershell
# Проверить API ключ
$env:OPENROUTER_API_KEY = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
Write-Host $env:OPENROUTER_API_KEY
```

### Модели не отвечают:
```powershell
# Протестировать API
.\test-openrouter-models.ps1
```

---

**Дата создания:** 2025-12-02
**Статус:** Готово к использованию
