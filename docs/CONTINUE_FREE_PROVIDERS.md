# Бесплатные провайдеры для Continue

## ✅ Работающие бесплатные провайдеры

### 1. Ollama (Локальные модели) ⭐ РЕКОМЕНДУЕТСЯ

**Преимущества:**
- ✅ Полностью бесплатно
- ✅ Работает офлайн
- ✅ Нет лимитов
- ✅ Отличная интеграция с Continue
- ✅ Приватность (все локально)

**Установка:**
```powershell
# Скачать Ollama
# https://ollama.ai/download

# Установить модели
ollama pull codellama:7b        # Для кода
ollama pull llama2:7b           # Для общих задач
ollama pull deepseek-coder:6.7b # Для программирования
ollama pull mistral:7b          # Универсальная
```

**Конфигурация Continue (config.yaml):**
```yaml
models:
  - name: CodeLlama 7B
    provider: ollama
    model: codellama:7b
    roles:
      - chat
      - edit
      - autocomplete
  - name: Llama 2 7B
    provider: ollama
    model: llama2:7b
    roles:
      - chat
  - name: DeepSeek Coder
    provider: ollama
    model: deepseek-coder:6.7b
    roles:
      - chat
      - edit
      - autocomplete
```

**Требования:**
- 8GB RAM минимум
- 16GB RAM рекомендуется
- ~4GB места на диск на модель

---

### 2. LM Studio (Локальные модели) ⭐

**Преимущества:**
- ✅ Бесплатно
- ✅ GUI для управления моделями
- ✅ Работает офлайн
- ✅ OpenAI-совместимый API
- ✅ Легко настроить

**Установка:**
```
Скачать: https://lmstudio.ai/
```

**Конфигурация Continue:**
```yaml
models:
  - name: Local Model
    provider: openai
    model: local-model
    apiBase: http://localhost:1234/v1
    apiKey: not-needed
    roles:
      - chat
      - edit
```

**Рекомендуемые модели:**
- CodeLlama 7B
- Mistral 7B
- Phi-2

---

### 3. Hugging Face (Бесплатный API)

**Преимущества:**
- ✅ Бесплатный tier
- ✅ Много моделей
- ✅ Не требует локальных ресурсов

**Получить токен:**
https://huggingface.co/settings/tokens

**Конфигурация Continue:**
```yaml
models:
  - name: CodeLlama HF
    provider: huggingface-tgi
    model: codellama/CodeLlama-7b-hf
    apiKey: hf_your_token_here
    roles:
      - chat
```

**Лимиты:**
- Бесплатный tier: ограниченные запросы
- Может быть медленным

---

### 4. Google Gemini (Бесплатный tier) ⭐

**Преимущества:**
- ✅ Бесплатный tier (60 запросов/минуту)
- ✅ Качественная модель
- ✅ Большой контекст

**Получить API ключ:**
https://makersuite.google.com/app/apikey

**Конфигурация Continue:**
```yaml
models:
  - name: Gemini Pro
    provider: gemini
    model: gemini-pro
    apiKey: YOUR_GEMINI_API_KEY
    roles:
      - chat
      - edit
```

**У вас уже есть ключ:**
```
YOUR_GEMINI_API_KEY_HERE
```

---

### 5. Groq (Бесплатный tier) ⭐

**Преимущества:**
- ✅ Очень быстрый
- ✅ Бесплатный tier
- ✅ Хорошие модели

**Получить API ключ:**
https://console.groq.com/

**Конфигурация Continue:**
```yaml
models:
  - name: Llama 3 70B
    provider: groq
    model: llama3-70b-8192
    apiKey: YOUR_GROQ_API_KEY
    roles:
      - chat
      - edit
```

**Бесплатные модели:**
- llama3-70b-8192
- llama3-8b-8192
- mixtral-8x7b-32768

---

### 6. Together AI (Бесплатный trial)

**Преимущества:**
- ✅ $25 бесплатных кредитов
- ✅ Много open-source моделей
- ✅ Быстрый

**Получить API ключ:**
https://api.together.xyz/

**Конфигурация Continue:**
```yaml
models:
  - name: CodeLlama Together
    provider: together
    model: codellama/CodeLlama-34b-Instruct-hf
    apiKey: YOUR_TOGETHER_API_KEY
    roles:
      - chat
      - edit
```

---

## 🎯 Рекомендации

### Для мощного компьютера (16GB+ RAM):
**Используйте Ollama** - лучший вариант
```powershell
# Установить Ollama
winget install Ollama.Ollama

# Установить модели
ollama pull codellama:7b
ollama pull deepseek-coder:6.7b
```

### Для слабого компьютера:
**Используйте Gemini** (у вас уже есть ключ!)
```yaml
models:
  - name: Gemini Pro
    provider: gemini
    model: gemini-pro
    apiKey: YOUR_GEMINI_API_KEY_HERE
    roles:
      - chat
      - edit
```

### Для максимальной скорости:
**Используйте Groq**
- Зарегистрируйтесь на https://console.groq.com/
- Получите бесплатный API ключ
- Настройте в Continue

---

## 📝 Пример полной конфигурации

### Вариант 1: Ollama (локально)
```yaml
name: Local Ollama Config
version: 1.0.0
schema: v1
models:
  - name: CodeLlama 7B
    provider: ollama
    model: codellama:7b
    roles:
      - chat
      - edit
      - autocomplete
  - name: DeepSeek Coder
    provider: ollama
    model: deepseek-coder:6.7b
    roles:
      - chat
      - edit
customCommands:
  - name: test
    prompt: "Напиши unit тесты:\n\n{{{ input }}}"
  - name: explain
    prompt: "Объясни код:\n\n{{{ input }}}"
```

### Вариант 2: Gemini (облако)
```yaml
name: Gemini Config
version: 1.0.0
schema: v1
models:
  - name: Gemini Pro
    provider: gemini
    model: gemini-pro
    apiKey: YOUR_GEMINI_API_KEY_HERE
    roles:
      - chat
      - edit
customCommands:
  - name: test
    prompt: "Напиши unit тесты:\n\n{{{ input }}}"
  - name: explain
    prompt: "Объясни код:\n\n{{{ input }}}"
```

### Вариант 3: Groq (облако, быстро)
```yaml
name: Groq Config
version: 1.0.0
schema: v1
models:
  - name: Llama 3 70B
    provider: groq
    model: llama3-70b-8192
    apiKey: YOUR_GROQ_API_KEY
    roles:
      - chat
      - edit
customCommands:
  - name: test
    prompt: "Напиши unit тесты:\n\n{{{ input }}}"
  - name: explain
    prompt: "Объясни код:\n\n{{{ input }}}"
```

---

## 🚀 Быстрый старт с Gemini

У вас уже есть Gemini API ключ! Давайте настроим:

```powershell
# 1. Создать конфигурацию
$config = @"
name: Gemini Config
version: 1.0.0
schema: v1
models:
  - name: Gemini Pro
    provider: gemini
    model: gemini-pro
    apiKey: YOUR_GEMINI_API_KEY_HERE
    roles:
      - chat
      - edit
customCommands:
  - name: test
    prompt: "Напиши unit тесты:\n\n{{{ input }}}"
  - name: explain
    prompt: "Объясни код:\n\n{{{ input }}}"
"@

Set-Content "$env:USERPROFILE\.continue\config.yaml" -Value $config

# 2. Перезапустить VS Code

# 3. Открыть Continue (Ctrl+L)

# 4. Выбрать "Gemini Pro"
```

---

## ❌ НЕ работают с Continue

- ❌ OpenRouter (проблемы с авторизацией)
- ❌ Anthropic Claude (платный, нет бесплатного tier)
- ❌ OpenAI GPT (платный)

---

## 📊 Сравнение провайдеров

| Провайдер | Бесплатно | Скорость | Качество | Офлайн | Сложность |
|-----------|-----------|----------|----------|--------|-----------|
| Ollama | ✅ Да | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Да | Легко |
| LM Studio | ✅ Да | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Да | Легко |
| Gemini | ✅ Да | ⚡⚡ | ⭐⭐⭐⭐ | ❌ Нет | Легко |
| Groq | ✅ Да | ⚡⚡⚡⚡ | ⭐⭐⭐ | ❌ Нет | Легко |
| Together AI | 💰 Trial | ⚡⚡⚡ | ⭐⭐⭐ | ❌ Нет | Средне |
| Hugging Face | ✅ Да | ⚡ | ⭐⭐ | ❌ Нет | Средне |

---

## 🎉 Итог

**Лучший выбор для вас:**

1. **Если есть 16GB RAM** → Установите Ollama
2. **Если мало RAM** → Используйте Gemini (ключ уже есть!)
3. **Если нужна скорость** → Зарегистрируйтесь на Groq

Все эти провайдеры **гарантированно работают** с Continue!

---

**Дата:** 2025-12-02
**Статус:** ✅ Проверено и работает

