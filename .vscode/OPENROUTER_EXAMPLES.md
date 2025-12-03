# 💻 OpenRouter - Примеры использования

Полная подборка примеров для работы с OpenRouter на разных языках программирования.

## 🗂️ Содержание

1. [Shell / Bash примеры](#shell--bash)
2. [PowerShell примеры](#powershell)
3. [Python примеры](#python)
4. [JavaScript / Node.js примеры](#javascript--nodejs)
5. [cURL примеры](#curl)

---

## Shell / Bash

### Простой запрос к Claude

```bash
#!/bin/bash

API_KEY="$OPENROUTER_API_KEY"
MODEL="anthropic/claude-3.5-sonnet"
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"

# Создать JSON запрос
read -r -d '' PAYLOAD << 'EOF'
{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "Привет! Что ты умеешь делать?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
EOF

# Отправить запрос
curl -s "$ENDPOINT" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | jq '.choices[0].message.content'
```

### Анализ текста с GPT-4o

```bash
#!/bin/bash

API_KEY="$OPENROUTER_API_KEY"
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
TEXT_TO_ANALYZE="$1"

curl -s "$ENDPOINT" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @- << EOF | jq '.choices[0].message'
{
  "model": "openai/gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "Ты специалист по анализу текста. Предоставь полный анализ."
    },
    {
      "role": "user",
      "content": "$TEXT_TO_ANALYZE"
    }
  ],
  "temperature": 0.5,
  "max_tokens": 2048
}
EOF
```

### Генерация кода

```bash
#!/bin/bash

API_KEY="$OPENROUTER_API_KEY"
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
TASK="$1"

curl -s "$ENDPOINT" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "model": "meta-llama/codellama-70b-instruct",
  "messages": [
    {
      "role": "system",
      "content": "Ты опытный программист. Напиши чистый, эффективный код."
    },
    {
      "role": "user",
      "content": "$TASK"
    }
  ],
  "temperature": 0.2,
  "max_tokens": 4096
}
EOF
```

---

## PowerShell

### Базовая функция для запросов

```powershell
function Invoke-OpenRouter {
    param(
        [string]$Model = "anthropic/claude-3.5-sonnet",
        [string]$Message,
        [float]$Temperature = 0.7,
        [int]$MaxTokens = 2048
    )

    $apiKey = $env:OPENROUTER_API_KEY
    if (-not $apiKey) {
        throw "OPENROUTER_API_KEY не установлен"
    }

    $headers = @{
        "Authorization" = "Bearer $apiKey"
        "Content-Type" = "application/json"
    }

    $body = @{
        model = $Model
        messages = @(
            @{
                role = "user"
                content = $Message
            }
        )
        temperature = $Temperature
        max_tokens = $MaxTokens
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest `
            -Uri "https://openrouter.ai/api/v1/chat/completions" `
            -Method POST `
            -Headers $headers `
            -Body $body `
            -ContentType "application/json"

        $content = $response.Content | ConvertFrom-Json
        return $content.choices[0].message.content
    }
    catch {
        Write-Error "Ошибка API: $_"
        return $null
    }
}

# Использование
$answer = Invoke-OpenRouter `
    -Message "Объясни как работает Docker" `
    -Temperature 0.5

Write-Host $answer
```

### Сравнение моделей

```powershell
function Compare-OpenRouterModels {
    param(
        [string]$Question,
        [string[]]$Models = @("anthropic/claude-3.5-sonnet", "openai/gpt-4o", "mistralai/mistral-medium")
    )

    $apiKey = $env:OPENROUTER_API_KEY
    $headers = @{
        "Authorization" = "Bearer $apiKey"
        "Content-Type" = "application/json"
    }

    $results = @{}

    foreach ($model in $Models) {
        Write-Host "Запрос к $model..." -ForegroundColor Yellow

        $body = @{
            model = $model
            messages = @(
                @{
                    role = "user"
                    content = $Question
                }
            )
            temperature = 0.7
            max_tokens = 1024
        } | ConvertTo-Json

        try {
            $response = Invoke-WebRequest `
                -Uri "https://openrouter.ai/api/v1/chat/completions" `
                -Method POST `
                -Headers $headers `
                -Body $body

            $content = $response.Content | ConvertFrom-Json
            $results[$model] = $content.choices[0].message.content

            Write-Host "✅ Получен ответ от $model" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Ошибка: $_" -ForegroundColor Red
            $results[$model] = $null
        }

        Start-Sleep -Seconds 1  # Избежать rate limiting
    }

    return $results
}

# Использование
$comparison = Compare-OpenRouterModels -Question "Что такое машинное обучение?"
$comparison | Format-Table
```

### Анализ файла

```powershell
function Analyze-FileWithOpenRouter {
    param(
        [string]$FilePath,
        [string]$Model = "anthropic/claude-3.5-sonnet"
    )

    $fileContent = Get-Content $FilePath -Raw
    $fileName = (Get-Item $FilePath).Name

    $message = "Анализируй этот файл '$fileName':`n`n$fileContent"

    $apiKey = $env:OPENROUTER_API_KEY
    $headers = @{
        "Authorization" = "Bearer $apiKey"
        "Content-Type" = "application/json"
    }

    $body = @{
        model = $Model
        messages = @(
            @{
                role = "system"
                content = "Ты эксперт по анализу кода и текста. Предоставь детальный анализ."
            },
            @{
                role = "user"
                content = $message
            }
        )
        temperature = 0.3
        max_tokens = 4096
    } | ConvertTo-Json -Depth 10

    try {
        $response = Invoke-WebRequest `
            -Uri "https://openrouter.ai/api/v1/chat/completions" `
            -Method POST `
            -Headers $headers `
            -Body $body

        $content = $response.Content | ConvertFrom-Json
        return $content.choices[0].message.content
    }
    catch {
        Write-Error "Ошибка при анализе файла: $_"
        return $null
    }
}

# Использование
$analysis = Analyze-FileWithOpenRouter -FilePath "openwrt_captive_monitor.sh"
Write-Host $analysis
```

---

## Python

### Базовый пример

```python
import requests
import os

def query_openrouter(message, model="anthropic/claude-3.5-sonnet", temperature=0.7):
    """Отправить запрос к OpenRouter API"""

    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не установлен")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": temperature,
        "max_tokens": 2048
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# Использование
if __name__ == "__main__":
    answer = query_openrouter("Привет! Как дела?")
    print(answer)
```

### Асинхронные запросы

```python
import asyncio
import aiohttp
import os

async def async_query_openrouter(message, model="anthropic/claude-3.5-sonnet"):
    """Асинхронный запрос к OpenRouter"""

    api_key = os.environ.get('OPENROUTER_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 2048
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"API Error: {response.status}")

# Использование - параллельные запросы
async def main():
    tasks = [
        async_query_openrouter("Что такое Python?"),
        async_query_openrouter("Что такое JavaScript?"),
        async_query_openrouter("Что такое Go?")
    ]

    results = await asyncio.gather(*tasks)
    for i, result in enumerate(results):
        print(f"Ответ {i+1}: {result}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### Работа со стриминг ответами

```python
import requests
import os

def stream_openrouter(message, model="anthropic/claude-3.5-sonnet"):
    """Получить ответ в режиме стриминга"""

    api_key = os.environ.get('OPENROUTER_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        stream=True
    )

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    break
                try:
                    import json
                    chunk = json.loads(data)
                    if 'choices' in chunk:
                        content = chunk['choices'][0]['delta'].get('content', '')
                        print(content, end='', flush=True)
                except:
                    pass

# Использование
stream_openrouter("Напиши стихотворение о программировании")
print("\n")
```

---

## JavaScript / Node.js

### Базовый пример с fetch

```javascript
async function queryOpenRouter(message, model = "anthropic/claude-3.5-sonnet") {
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
        throw new Error('OPENROUTER_API_KEY не установлен');
    }

    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            model: model,
            messages: [
                {
                    role: "user",
                    content: message
                }
            ],
            temperature: 0.7,
            max_tokens: 2048
        })
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
}

// Использование
queryOpenRouter("Привет! Как дела?")
    .then(answer => console.log(answer))
    .catch(error => console.error(error));
```

### С использованием axios

```javascript
const axios = require('axios');

async function queryOpenRouterAxios(message, model = "anthropic/claude-3.5-sonnet") {
    const apiKey = process.env.OPENROUTER_API_KEY;

    try {
        const response = await axios.post(
            "https://openrouter.ai/api/v1/chat/completions",
            {
                model: model,
                messages: [
                    {
                        role: "user",
                        content: message
                    }
                ],
                temperature: 0.7,
                max_tokens: 2048
            },
            {
                headers: {
                    "Authorization": `Bearer ${apiKey}`,
                    "Content-Type": "application/json"
                }
            }
        );

        return response.data.choices[0].message.content;
    } catch (error) {
        console.error("API Error:", error.message);
        throw error;
    }
}

// Использование
(async () => {
    try {
        const answer = await queryOpenRouterAxios("Что такое Node.js?");
        console.log(answer);
    } catch (error) {
        console.error(error);
    }
})();
```

---

## cURL

### Простой запрос

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer sk-or-v1-..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [
      {
        "role": "user",
        "content": "Привет!"
      }
    ]
  }'
```

### Сохранение в файл

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Напиши стихотворение"}]
  }' | jq '.choices[0].message.content' > response.txt
```

### С красивым форматированием

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d @- << 'EOF' | jq '.choices[0].message'
{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [
    {
      "role": "system",
      "content": "Ты помощник по программированию"
    },
    {
      "role": "user",
      "content": "Как написать функцию для сортировки массива?"
    }
  ],
  "temperature": 0.5,
  "max_tokens": 1024
}
EOF
```

---

## 📊 Таблица сравнения примеров

| Язык | Простота | Производительность | Рекомендация |
|------|----------|-------------------|--------------|
| Shell/Bash | Низкая | Низкая | Скрипты |
| PowerShell | Средняя | Средняя | Windows |
| Python | Высокая | Средняя | Общее использование |
| JavaScript | Высокая | Средняя | Веб приложения |
| cURL | Низкая | Низкая | Быстрые тесты |

---

## ⚙️ Общие параметры

Все примеры поддерживают эти параметры:

```json
{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [{"role": "user", "content": "..."}],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 2048,
  "top_k": 0,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
```

---

**Дата создания:** 2025-12-02
**Статус:** ✨ Готово к использованию
