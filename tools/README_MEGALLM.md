# MegaLLM CLI Client

Консольный агент для доступа к MegaLLM API через Python.

## Установка

API ключ уже настроен в `.env`:
```bash
MEGALLM_API_KEY=sk-mega-...
```

## Использование

### Базовый запрос (Mistral Nemotron)
```bash
python tools/megallm_client.py --model "mistralai/mistral-nemotron" --prompt "Your question"
```

### Мощная модель для сложных задач (Qwen 3.5 397B)
```bash
python tools/megallm_client.py --model "alibaba-qwen3.5-397b" --prompt "Complex architectural question"
```

### Из stdin
```bash
echo "Your question" | python tools/megallm_client.py --model "mistralai/mistral-nemotron" --stdin
```

### С параметрами
```bash
python tools/megallm_client.py \
  --model "mistralai/mistral-nemotron" \
  --prompt "Explain quantum computing" \
  --temperature 0.5 \
  --max-tokens 500
```

## PowerShell обертка

### Обычный запрос (экономичный)
```powershell
.\tools\Ask-MegaLLM.ps1 "Explain async/await in Python"
```

### Сложная задача (мощная модель)
```powershell
.\tools\Ask-MegaLLM.ps1 "Design distributed system architecture" -Heavy
```

### С параметрами
```powershell
.\tools\Ask-MegaLLM.ps1 "Code review request" -Temperature 0.3 -MaxTokens 1000
```

## Доступные модели (базовый tier)

### Mistral Nemotron (РЕКОМЕНДУЕТСЯ для обычных задач)
- **ID:** `mistralai/mistral-nemotron`
- **Цена:** $1 input / $1 output (per 1M tokens)
- **Контекст:** 128K tokens
- **Плюсы:** Надежный, точный, хорошо для кода, экономичный

### Qwen 3.5 397B (для СЛОЖНЫХ задач)
- **ID:** `alibaba-qwen3.5-397b`
- **Цена:** $3 input / $15 output (per 1M tokens)
- **Контекст:** 131K tokens
- **Параметры:** 397 миллиардов (самая мощная доступная модель)
- **Плюсы:** Максимальная мощность для сложных задач
- **Минусы:** В 15 раз дороже на output

### DeepSeek V3.1 / V3.1 Terminus (НЕ рекомендуется)
- **ID:** `deepseek-ai/deepseek-v3.1` или `deepseek-ai/deepseek-v3.1-terminus`
- **Цена:** $1 input / $1 output (per 1M tokens)
- **Минусы:** Часто ошибается, ненадежный (по отзыву Пилота)

### OpenAI модели (через прокси)
- **gpt-3.5-turbo** - доступен, но устаревший
- **gpt-4o-mini** - доступен, но слабее Mistral Nemotron

## Модели с tier ограничениями (требуют dev/max/enterprise)

### Gemini 2.5 Flash Lite (дешевый)
- **ID:** `gemini-2.5-flash-lite`
- **Цена:** $0.1 input / $0.4 output
- **Tier:** dev, max, enterprise

### Claude Haiku 4.5 (быстрый)
- **ID:** `claude-haiku-4-5-20251001`
- **Цена:** $1 input / $5 output
- **Tier:** dev, max, enterprise

### Llama 4 Maverick 17B (самый дешевый)
- **ID:** `llama-4-maverick-17b`
- **Цена:** $0.12 input / $0.3 output
- **Tier:** dev, max, enterprise

## Расчет стоимости

125 кредитов = $125

**Пример с Mistral Nemotron ($1/$1):**
- 1M input tokens = $1
- 1M output tokens = $1
- Средний запрос: ~500 input + ~500 output = $0.001
- **125 кредитов ≈ 125,000 запросов**

**Пример с Qwen 3.5 397B ($3/$15):**
- 1M input tokens = $3
- 1M output tokens = $15
- Средний запрос: ~500 input + ~500 output = $0.009
- **125 кредитов ≈ 13,888 запросов**

**Рекомендация:** Используй Mistral для обычных задач, Qwen 3.5 397B только для сложных архитектурных решений.

## Интеграция с Kiro

Я (Ри) могу вызывать этот скрипт через `executePwsh`:

```javascript
executePwsh({
  command: `$env:MEGALLM_API_KEY = (Get-Content .env | Select-String "MEGALLM_API_KEY" | ForEach-Object { $_ -replace "MEGALLM_API_KEY=", "" }); python tools/megallm_client.py --model "mistralai/mistral-nemotron" --prompt "Your question"`
})
```

## Проверка баланса

Зайди на https://megallm.io/dashboard/overview для проверки оставшихся кредитов.
