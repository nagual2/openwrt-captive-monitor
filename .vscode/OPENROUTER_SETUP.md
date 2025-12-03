# 🌐 OpenRouter - Настройка и использование

OpenRouter предоставляет унифицированный доступ к различным моделям AI от разных провайдеров через один API.

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Установка](#установка)
3. [Доступные модели](#доступные-модели)
4. [Примеры использования](#примеры-использования)
5. [Параметры моделей](#параметры-моделей)
6. [Решение проблем](#решение-проблем)

---

## 🚀 Быстрый старт

### 1. Получить API ключ

1. Перейдите на https://openrouter.ai/keys
2. Создайте новый API ключ (или используйте существующий)
3. Скопируйте ключ (формат: `sk-or-v1-...`)

### 2. Установить ключ

```powershell
.\setup-openrouter.ps1
```

Введите ваш API ключ при запросе.

### 3. Проверить конфигурацию

```powershell
# Проверить что ключ установлен
$env:OPENROUTER_API_KEY

# Показать доступные модели
Get-Content .\.vscode\openrouter-config.json | ConvertFrom-Json | Select-Object -ExpandProperty openrouter
```

---

## 📦 Установка

### Требования

- PowerShell 7+ (pwsh)
- Интернет подключение
- API ключ OpenRouter

### Шаги установки

```powershell
# 1. Выполнить скрипт установки
.\setup-openrouter.ps1

# 2. Ввести API ключ
# (вам будет предложено ввести ключ)

# 3. Перезагрузить PowerShell
# (закрыть и открыть новое окно)
```

### Ручная установка ключа

Если скрипт не работает, установите переменную вручную:

```powershell
[System.Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'User')
```

---

## 🤖 Доступные модели

### Рекомендуемые модели ⭐

#### Claude 3.5 Sonnet (Рекомендуется)
```
ID: anthropic/claude-3.5-sonnet
Провайдер: Anthropic
Стоимость: $3/$15 за миллион токен (вход/выход)
Context: 200K токенов
Использование: Общие задачи, анализ, рефакторинг
```

#### GPT-4o (Рекомендуется)
```
ID: openai/gpt-4o
Провайдер: OpenAI
Стоимость: $5/$15 за миллион токен (вход/выход)
Context: 128K токенов
Использование: Быстрые задачи, кодирование
```

#### Mistral Medium (Рекомендуется)
```
ID: mistralai/mistral-medium
Провайдер: Mistral AI
Стоимость: $2.7/$8.1 за миллион токен (вход/выход)
Context: 32K токенов
Использование: Баланс скорости и качества
```

### Все доступные модели

#### Anthropic
- **Claude 3.5 Sonnet** - `anthropic/claude-3.5-sonnet` ⭐
- **Claude 3 Opus** - `anthropic/claude-3-opus`

#### OpenAI
- **GPT-4 Turbo** - `openai/gpt-4-turbo`
- **GPT-4o** - `openai/gpt-4o` ⭐
- **GPT-3.5 Turbo** - `openai/gpt-3.5-turbo` (дешёвый)

#### Mistral
- **Mistral Large** - `mistralai/mistral-large`
- **Mistral Medium** - `mistralai/mistral-medium` ⭐
- **Mistral Small** - `mistralai/mistral-small` (быстрый)

#### Open Source
- **Llama 2 70B** - `meta-llama/llama-2-70b-chat`
- **Neural Chat 7B** - `intel/neural-chat-7b` (очень дешёвый)

#### Специализированные для кода
- **DeepSeek Coder 33B** - `deepseek/deepseek-coder-33b-instruct`
- **Code Llama 70B** - `meta-llama/codellama-70b-instruct`

---

## 💻 Примеры использования

### Использование с curl

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [
      {
        "role": "user",
        "content": "Привет! Что ты умеешь делать?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 2048
  }'
```

### Использование с PowerShell

```powershell
$apiKey = $env:OPENROUTER_API_KEY
$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$body = @{
    model = "anthropic/claude-3.5-sonnet"
    messages = @(
        @{
            role = "user"
            content = "Объясни как работает машинное обучение"
        }
    )
    temperature = 0.7
    max_tokens = 2048
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "https://openrouter.ai/api/v1/chat/completions" `
    -Method POST `
    -Headers $headers `
    -Body $body

$response.Content | ConvertFrom-Json | Select-Object -ExpandProperty choices
```

### Использование с Python

```python
import requests
import os

api_key = os.environ.get('OPENROUTER_API_KEY')
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [
        {
            "role": "user",
            "content": "Привет! Как дела?"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=data
)

print(response.json()['choices'][0]['message']['content'])
```

---

## ⚙️ Параметры моделей

### Основные параметры

| Параметр | Описание | Пример |
|----------|---------|--------|
| `model` | ID модели | `anthropic/claude-3.5-sonnet` |
| `messages` | Список сообщений | `[{"role": "user", "content": "..."}]` |
| `temperature` | Творчество (0-2) | `0.7` |
| `top_p` | Контроль вариативности | `0.9` |
| `max_tokens` | Максимум выходных токенов | `2048` |

### Предустановленные конфигурации

#### Общие задачи (General)
```json
{
  "temperature": 0.7,
  "top_p": 1,
  "top_k": 0,
  "max_tokens": 2048
}
```

#### Творческие задачи (Creative)
```json
{
  "temperature": 0.9,
  "top_p": 0.95,
  "top_k": 50,
  "max_tokens": 4096
}
```

#### Точные ответы (Precise)
```json
{
  "temperature": 0.3,
  "top_p": 0.9,
  "top_k": 0,
  "max_tokens": 2048
}
```

#### Программирование (Coding)
```json
{
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 0,
  "max_tokens": 4096
}
```

#### Анализ (Analysis)
```json
{
  "temperature": 0.5,
  "top_p": 1,
  "top_k": 0,
  "max_tokens": 3000
}
```

---

## 🎯 Выбор подходящей модели

### Для производительности
- Claude 3.5 Sonnet ⭐
- GPT-4 Turbo
- Mistral Large

### Для скорости
- GPT-3.5 Turbo
- Mistral Small
- Neural Chat 7B

### Для экономии
- GPT-3.5 Turbo (~$0.5-1.5 за 1M токенов)
- Mistral Small (~$0.14-0.42 за 1M токенов)
- Neural Chat 7B (~$0.04 за 1M токенов)

### Для программирования
- Claude 3.5 Sonnet ⭐
- Code Llama 70B
- DeepSeek Coder 33B

### Для анализа текста
- Claude 3 Opus
- GPT-4 Turbo
- Mistral Large

---

## 🔐 Безопасность

### Хранение API ключа

✅ **Правильно:**
- Использовать переменные окружения
- Хранить в .env файле (локально)
- Использовать системные переменные (User scope)

❌ **Неправильно:**
- Коммитить в Git
- Хранить в исходном коде
- Передавать третьим лицам
- Использовать публичные каналы

### Защита ключа

```powershell
# Не выводить ключ в консоль
# Вместо этого используйте:
if ($env:OPENROUTER_API_KEY) {
    Write-Host "API ключ установлен ✅"
}

# Убедитесь что ключ в .gitignore
Add-Content .gitignore ".env"
Add-Content .gitignore "*_key*"
```

---

## 🐛 Решение проблем

### Проблема: "Invalid API key"

**Решение:**
1. Проверьте что ключ начинается с `sk-or`
2. Убедитесь что ключ полностью скопирован
3. Получите новый ключ на https://openrouter.ai/keys

```powershell
# Проверить ключ
$env:OPENROUTER_API_KEY | Write-Host
```

### Проблема: "Model not found"

**Решение:**
1. Проверьте что ID модели правильный
2. Посмотрите доступные модели в конфиге
3. Убедитесь что модель активна на вашем аккаунте

```powershell
# Показать доступные модели
Get-Content .\.vscode\openrouter-config.json | ConvertFrom-Json |
  Select-Object -ExpandProperty openrouter |
  Select-Object -ExpandProperty models
```

### Проблема: "Rate limit exceeded"

**Решение:**
1. Подождите несколько минут
2. Проверьте использование API на https://openrouter.ai/activity
3. Рассмотрите использование более дешёвой модели
4. Увеличьте задержку между запросами

```powershell
# Пример с задержкой
Start-Sleep -Seconds 2
# Отправить запрос
```

### Проблема: "Connection timeout"

**Решение:**
1. Проверьте интернет подключение
2. Убедитесь что URL правильный (`https://openrouter.ai/api/v1`)
3. Увеличьте timeout параметр
4. Попробуйте позже (возможны проблемы на сервере)

---

## 📊 Мониторинг использования

### Проверить статистику

Перейдите на https://openrouter.ai/activity для просмотра:
- Количество использованных токенов
- Стоимость запросов
- История запросов
- Баланс аккаунта

### Управление лимитами

```powershell
# Проверить лимиты в конфиге
$config = Get-Content .\.vscode\openrouter-config.json | ConvertFrom-Json
$config.openrouter.models |
  ForEach-Object {
    [PSCustomObject]@{
      Name = $_.name
      CostInput = $_.costPerMillion.input
      CostOutput = $_.costPerMillion.output
    }
  }
```

---

## 📚 Дополнительные ресурсы

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/docs/models)
- [API Reference](https://openrouter.ai/docs/api-reference)
- [Status Page](https://openrouter.ai/status)

---

## ✅ Статус конфигурации

Проверьте что всё правильно установлено:

```powershell
.\check-openrouter-setup.ps1
```

---

**Дата создания:** 2025-12-02
**Версия:** 1.0
**Статус:** ✨ Готово к использованию
