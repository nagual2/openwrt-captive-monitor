# 🤖 Claude в VS Code - Полная настройка

Успешно настроена интеграция Claude (Anthropic) в ваш VS Code для проекта OpenWrt Captive Monitor!

## 📋 Что было сделано

✅ Обновлена конфигурация VS Code
- Добавлена поддержка Claude API в `.vscode/settings.json`
- Обновлены рекомендации расширений в `.vscode/extensions.json`
- Создана специальная конфигурация Claude в `.vscode/claude-config.json`

✅ Настроена переменная окружения
- Добавлена инструкция в `Microsoft.PowerShell_profile.ps1`
- Создан скрипт автоматической настройки `setup-claude.ps1`

✅ Подготовлена документация
- `CLAUDE_SETUP.md` - Подробная инструкция по установке
- `CLAUDE_TIPS.md` - Советы и примеры использования
- Этот файл - Quick Start руководство

## 🚀 Быстрый старт (3 шага)

### Шаг 1: Получить API ключ
1. Перейдите на [https://console.anthropic.com/keys](https://console.anthropic.com/keys)
2. Создайте новый API ключ
3. Скопируйте его

### Шаг 2: Установить ключ
Откройте PowerShell и выполните:
```powershell
.\setup-claude.ps1
```

Или вручную установите переменную:
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-...', 'User')
```

### Шаг 3: Перезагрузить VS Code
- Закройте VS Code полностью
- Откройте VS Code заново

## ✨ Основные команды

| Команда | Описание |
|---------|---------|
| `Ctrl+Shift+C` | Открыть Claude Chat |
| `Ctrl+Shift+A` | Быстрый вопрос |
| `Ctrl+Shift+R` | Рефакторинг кода |
| `/explain` | Объяснить код |
| `/refactor` | Рефакторинг |
| `/tests` | Написать тесты |
| `/optimize` | Оптимизация |

## 📂 Структура файлов конфигурации

```
.vscode/
├── settings.json          # Основные настройки VS Code с Claude
├── extensions.json        # Рекомендации расширений
├── claude-config.json     # Специфичная конфигурация Claude
├── CLAUDE_SETUP.md        # Инструкция по установке
├── CLAUDE_TIPS.md         # Советы и примеры
└── README.md             # Этот файл
```

## 🔐 Безопасность

- ✅ API ключ хранится в переменной окружения (User scope)
- ✅ Не коммитится в репозиторий
- ✅ Не видно в исходном коде
- ⚠️ Никогда не передавайте ключ третьим лицам

Проверить что ключ НЕ в .gitignore:
```powershell
# Проверьте .gitignore - ANTHROPIC_API_KEY там не должен быть!
# Он должен быть в переменных окружения
```

## 🎯 Частые вопросы

### Q: Claude не подключается?
**A:**
1. Проверьте API ключ: `$env:ANTHROPIC_API_KEY`
2. Перезагрузите VS Code
3. Убедитесь что расширение установлено: `code --list-extensions | grep anthropic`

### Q: Как получить новый API ключ?
**A:** Перейдите на [console.anthropic.com/keys](https://console.anthropic.com/keys) и создайте новый

### Q: Какая модель используется?
**A:** `claude-3-5-sonnet-20241022` - оптимальный баланс скорости и качества

### Q: Могу ли я использовать другую модель?
**A:** Да, отредактируйте `"modelId"` в `.vscode/claude-config.json`

## 🔗 Документация

- **Установка & Конфигурация:** [CLAUDE_SETUP.md](./.vscode/CLAUDE_SETUP.md)
- **Советы & Примеры:** [CLAUDE_TIPS.md](./.vscode/CLAUDE_TIPS.md)
- **Claude Documentation:** https://docs.anthropic.com
- **VS Code Extensions:** https://marketplace.visualstudio.com

## 🌟 Рекомендуемые расширения

Кроме Claude, в проект добавлены:
- **GitHub Copilot** - Для быстрого автодополнения (дополняет Claude)
- **GitLens** - Для анализа Git истории
- **ShellCheck** - Для проверки shell скриптов
- **YAML** - Для редактирования конфигов
- **Docker** - Для работы с Docker

## 💡 Лучшие практики

1. **Включайте контекст** - Спрашивайте про OpenWrt, procd, shell, и т.д.
2. **Используйте @файл** - `@openwrt_captive_monitor.sh "как сделать...?"`
3. **Просите примеры** - "Дай пример реального кода"
4. **Проверяйте код** - Всегда проверяйте сгенерированный код
5. **Уточняйте ошибки** - "Почему эта строка выдает ошибку?"

## 📈 Next Steps

1. ✅ Выполните `setup-claude.ps1` для установки API ключа
2. ✅ Перезагрузите VS Code
3. ✅ Откройте файл и спросите Claude: "Объясни что делает этот файл"
4. ✅ Попробуйте `/refactor` на выделенном коде
5. ✅ Используйте `Ctrl+Shift+C` для основной панели Chat

## 🆘 Помощь

Если столкнулись с проблемой:
1. Прочитайте [CLAUDE_SETUP.md](./.vscode/CLAUDE_SETUP.md) - раздел "Решение проблем"
2. Проверьте что API ключ правильный и активный
3. Убедитесь что VS Code полностью перезагружен
4. Проверьте логи: VS Code > Help > Toggle Developer Tools

## 📞 Контакты & Ресурсы

- **Anthropic Claude:** https://www.anthropic.com/
- **VS Code API:** https://code.visualstudio.com/api
- **OpenWrt Documentation:** https://openwrt.org/

---

**Статус:** ✅ Настройка завершена успешно!

Начните работать с Claude в VS Code прямо сейчас! 🚀
