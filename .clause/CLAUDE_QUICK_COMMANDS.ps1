#!/usr/bin/env pwsh
# Claude Setup - Quick Commands

# ╔════════════════════════════════════════════════════════════════╗
# ║           Claude для VS Code - Быстрые команды               ║
# ╚════════════════════════════════════════════════════════════════╝

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1️⃣ УСТАНОВИТЬ CLAUDE
# Выполните эту команду после получения API ключа:
#
# .\setup-claude.ps1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 2️⃣ ПРОВЕРИТЬ КОНФИГУРАЦИЮ
# Убедитесь что всё установлено правильно:
#
# .\check-claude-setup.ps1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 3️⃣ ПРОВЕРИТЬ API КЛЮЧ
# Убедитесь что ключ установлен в переменной окружения:
#
# $env:ANTHROPIC_API_KEY

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 4️⃣ УСТАНОВИТЬ РАСШИРЕНИЕ CLAUDE (вручную)
# Если нужно установить расширение Claude для VS Code:
#
# code --install-extension anthropic.claude-for-vscode

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 5️⃣ ПОКАЗАТЬ ВСЕ УСТАНОВЛЕННЫЕ РАСШИРЕНИЯ
# Проверить что Claude расширение установлено:
#
# code --list-extensions | Select-String anthropic

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 6️⃣ ПЕРЕЗАГРУЗИТЬ VS CODE
# Закройте и откройте VS Code заново, чтобы загрузить переменные окружения

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 7️⃣ ОТКРЫТЬ CLAUDE В VS CODE
# После перезагрузки, используйте:
#
# Ctrl+Shift+C         Открыть Claude Chat
# Ctrl+Shift+A         Быстрый вопрос
# Ctrl+Shift+R         Рефакторинг

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 8️⃣ ПРОЧИТАТЬ ДОКУМЕНТАЦИЮ
# Полная информация доступна в файлах:
#
# .vscode/CLAUDE_README.md       - Quick Start
# .vscode/CLAUDE_SETUP.md        - Подробная инструкция
# .vscode/CLAUDE_TIPS.md         - Советы и примеры
# .vscode/CLAUDE_VISUAL_GUIDE.md - Визуальный гайд

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 🆘 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

# Проблема: Claude не открывается
# Решение:
# 1. Перезагрузите VS Code
# 2. Проверьте API ключ: $env:ANTHROPIC_API_KEY
# 3. Выполните: .\check-claude-setup.ps1

# Проблема: "Authentication failed"
# Решение:
# 1. Проверьте что API ключ правильный
# 2. Получите новый ключ на https://console.anthropic.com/keys
# 3. Выполните: .\setup-claude.ps1

# Проблема: Расширение не установлено
# Решение:
# 1. Выполните: code --install-extension anthropic.claude-for-vscode
# 2. Закройте и откройте VS Code
# 3. Проверьте: code --list-extensions | Select-String anthropic

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Claude VS Code - Быстрые команды                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 УСТАНОВКА:" -ForegroundColor Yellow
Write-Host "   1. Получить API ключ: https://console.anthropic.com/keys" -ForegroundColor White
Write-Host "   2. Выполнить: .\setup-claude.ps1" -ForegroundColor White
Write-Host "   3. Перезагрузить VS Code" -ForegroundColor White
Write-Host ""
Write-Host "✅ ПРОВЕРКА:" -ForegroundColor Yellow
Write-Host "   .\check-claude-setup.ps1" -ForegroundColor White
Write-Host ""
Write-Host "📚 ДОКУМЕНТАЦИЯ:" -ForegroundColor Yellow
Write-Host "   .vscode/CLAUDE_README.md - начните отсюда!" -ForegroundColor White
Write-Host ""
Write-Host "⌨️ КОМАНДНЫЕ КЛАВИШИ:" -ForegroundColor Yellow
Write-Host "   Ctrl+Shift+C - Claude Chat" -ForegroundColor White
Write-Host "   Ctrl+Shift+A - Быстрый вопрос" -ForegroundColor White
Write-Host ""
