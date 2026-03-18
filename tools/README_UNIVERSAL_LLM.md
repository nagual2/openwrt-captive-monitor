# Universal LLM CLI Client

Универсальный консольный клиент для доступа к MegaLLM и Z.AI через единый интерфейс.

## Установка

API ключи настраиваются в `.env`:
```bash
MEGALLM_API_KEY=sk-mega-...
ZAI_API_KEY=your-zai-key
```

## Использование

### Python CLI

#### Z.AI (бесплатные модели)
```bash
# Бесплатная модель GLM-4.7-Flash
python tools/universal_llm_client.py --provider zai --prompt "Your question"

# Мощная модель GLM-5 (платная)
python tools/universal_llm_client.py --provider zai --model glm-5 --prompt "Complex question"

# Vision модель (бесплатная)
python tools/universal_llm_client.py --provider zai --model glm-4.6v-flash --prompt "Describe this image"
```

#### MegaLLM (платные модели)
```bash
# Mistral Nemotron
python tools/universal_llm_client.py --provider megallm --prompt "Your question"

# Qwen 3.5 397B (мощная)
python tools/universal_llm_client.py --provider megallm --model alibaba-qwen3.5-397b --prompt "Complex question"
```

#### Список моделей
```bash
python tools/universal_llm_client.py --provider zai --list-models
python tools/universal_llm_client.py --provider megallm --list-models
```

### PowerShell обертка

#### Быстрый старт (Z.AI бесплатно)
```powershell
.\tools\Ask-LLM.ps1 "What is 2+2?"
```

#### Выбор провайдера
```powershell
# Z.AI (по умолчанию, бесплатно)
.\tools\Ask-LLM.ps1 "Explain async/await" -Provider zai

# MegaLLM (платно)
.\tools\Ask-LLM.ps1 "Explain async/await" -Provider megallm
```

#### Мощные модели
```powershell
# Z.AI GLM-5 (платно: $1/$3.2)
.\tools\Ask-LLM.ps1 "Design system architecture" -Heavy

# MegaLLM Qwen 3.5 397B (платно: $3/$15)
.\tools\Ask-LLM.ps1 "Design system architecture" -Provider megallm -Heavy
```

#### Ручной выбор модели
```powershell
.\tools\Ask-LLM.ps1 "Code review" -Provider zai -Model "glm-4.5-flash"
```

## Доступные модели

### Z.AI (бесплатные)
- **glm-4.7-flash** - быстрая текстовая модель (FREE)
- **glm-4.5-flash** - предыдущая версия (FREE)
- **glm-4.6v-flash** - vision модель (FREE)

### Z.AI (платные)
- **glm-5** - $1 input / $3.2 output (128K контекст)
- **glm-5-code** - $1.2 input / $5 output (специализация на коде)
- **glm-4.7** - $0.6 input / $2.2 output
- **glm-4.6** - $0.6 input / $2.2 output

### MegaLLM (платные)
- **mistralai/mistral-nemotron** - $1/$1 (128K контекст)
- **alibaba-qwen3.5-397b** - $3/$15 (131K контекст, 397B параметров)

## Расчет стоимости

### Z.AI бесплатные модели
- **Стоимость:** $0
- **Ограничения:** Нет (по данным документации)

### Z.AI GLM-5
- 1M input tokens = $1
- 1M output tokens = $3.2
- Средний запрос: ~500 input + ~500 output = $0.0021

### MegaLLM Mistral Nemotron
- 1M input tokens = $1
- 1M output tokens = $1
- Средний запрос: ~500 input + ~500 output = $0.001

### MegaLLM Qwen 3.5 397B
- 1M input tokens = $3
- 1M output tokens = $15
- Средний запрос: ~500 input + ~500 output = $0.009

## Рекомендации

1. **Для обычных задач:** Z.AI GLM-4.7-Flash (бесплатно)
2. **Для кода:** Z.AI GLM-5-Code или MegaLLM Mistral
3. **Для сложных задач:** MegaLLM Qwen 3.5 397B
4. **Для работы с изображениями:** Z.AI GLM-4.6V-Flash (бесплатно)

## Получение API ключей

### Z.AI
1. Зайти на https://chat.z.ai/
2. Зарегистрироваться
3. Перейти в настройки API
4. Создать новый API ключ
5. Добавить в `.env`: `ZAI_API_KEY=your-key`

### MegaLLM
1. Зайти на https://megallm.io/dashboard/overview
2. Получить API ключ
3. Добавить в `.env`: `MEGALLM_API_KEY=sk-mega-...`

## Интеграция с Kiro

Я (Ри) могу вызывать этот скрипт через `executePwsh`:

```javascript
executePwsh({
  command: `.\tools\Ask-LLM.ps1 "Your question" -Provider zai`
})
```
