# Настройка бесплатных моделей в Kiro

## Статус: ✅ Настроено

### Доступные бесплатные модели OpenRouter:

1. **Grok 4.1 Fast (Free)** - рекомендуется
   - ID: `x-ai/grok-4.1-fast:free`
   - Использование: Общие задачи, быстрые ответы
   - Context: 8K токенов

2. **KAT-Coder-Pro (Free)**
   - ID: `kwaipilot/kat-coder-pro:free`
   - Использование: Программирование, код
   - Context: 16K токенов

3. **Olmo 3 32B Think (Free)**
   - ID: `allenai/olmo-3-32b-think:free`
   - Использование: Анализ, рассуждения
   - Context: 32K токенов

## Конфигурация

### Файлы настроек:

- `.kiro/settings/mcp.json` - MCP конфигурация для OpenRouter
- `.kiro/settings/models.json` - Детальные настройки моделей
- `.vscode/settings.json` - Интеграция с Kiro IDE

### API ключ:

```bash
# Проверить ключ
$env:OPENROUTER_API_KEY

# Установить ключ
.\setup-openrouter.ps1
```

## Использование в Kiro

### Через меню моделей:

1. Откройте выпадающее меню моделей в чате Kiro
2. Найдите секцию "OpenRouter"
3. Выберите одну из бесплатных моделей

### Через команды:

```powershell
# Загрузить быстрые команды
. .\OPENROUTER_QUICK_COMMANDS.ps1

# Тестировать модели
Test-Grok "ваш вопрос"
Test-Coder "напиши код"
```

## Troubleshooting

### Модели не отображаются в меню:

1. **Перезагрузите Kiro** - F5 или перезапустите IDE
2. **Проверьте API ключ**:
   ```powershell
   .\check-openrouter-setup.ps1
   ```
3. **Проверьте переменную окружения**:
   ```powershell
   $env:OPENROUTER_API_KEY = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
   ```

### Модели не работают:

1. **Проверьте соединение**:
   ```powershell
   .\test-openrouter-models.ps1
   ```
2. **Проверьте логи Kiro** в консоли разработчика

## Дополнительная информация

- Документация OpenRouter: https://openrouter.ai/docs
- Список всех бесплатных моделей: https://openrouter.ai/models?free=true
- Получить API ключ: https://openrouter.ai/keys

## Обновление списка моделей

Чтобы добавить новые бесплатные модели:

1. Отредактируйте `.kiro/settings/models.json`
2. Добавьте модель в `.kiro/settings/mcp.json`
3. Обновите список в `.vscode/settings.json`
4. Перезагрузите Kiro

---

**Последнее обновление:** 2025-12-02
**Статус:** Настроено и протестировано
