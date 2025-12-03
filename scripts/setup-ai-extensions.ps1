#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Установка AI расширений с поддержкой OpenRouter

.DESCRIPTION
    Скрипт устанавливает рекомендуемые AI расширения для работы с бесплатными моделями OpenRouter

.EXAMPLE
    .\setup-ai-extensions.ps1
    .\setup-ai-extensions.ps1 -All
#>

param(
    [switch]$All = $false
)

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Установка AI расширений для OpenRouter             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Проверка API ключа
$apiKey = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
if (-not $apiKey) {
    Write-Host "⚠️  OPENROUTER_API_KEY не установлен" -ForegroundColor Yellow
    Write-Host "   Выполните: .\setup-openrouter.ps1" -ForegroundColor Gray
    Write-Host ""
}

# Список расширений
$extensions = @(
    @{
        id = "Continue.continue"
        name = "Continue"
        recommended = $true
        description = "Лучшее для OpenRouter - чат, автодополнение, кастомные команды"
    },
    @{
        id = "saoudrizwan.claude-dev"
        name = "Cline"
        recommended = $false
        description = "Автономное выполнение задач, работа с файлами"
    },
    @{
        id = "rjmacarthy.twinny"
        name = "Twinny"
        recommended = $false
        description = "Легковесное расширение с чатом и автодополнением"
    }
)

# Установка расширений
$installed = @()
$failed = @()

foreach ($ext in $extensions) {
    if (-not $All -and -not $ext.recommended) {
        continue
    }

    Write-Host "📦 Установка: $($ext.name)" -ForegroundColor Yellow
    Write-Host "   $($ext.description)" -ForegroundColor Gray

    code --install-extension $ext.id 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Установлено" -ForegroundColor Green
        $installed += $ext.name
    } else {
        Write-Host "   ❌ Ошибка установки" -ForegroundColor Red
        $failed += $ext.name
    }
    Write-Host ""
}

# Итоговый отчет
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Установка завершена                                 ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

if ($installed.Count -gt 0) {
    Write-Host "✅ Установлено расширений: $($installed.Count)" -ForegroundColor Green
    foreach ($name in $installed) {
        Write-Host "   • $name" -ForegroundColor Green
    }
    Write-Host ""
}

if ($failed.Count -gt 0) {
    Write-Host "❌ Не удалось установить: $($failed.Count)" -ForegroundColor Red
    foreach ($name in $failed) {
        Write-Host "   • $name" -ForegroundColor Red
    }
    Write-Host ""
}

# Следующие шаги
Write-Host "📋 Следующие шаги:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Перезагрузите VS Code" -ForegroundColor White
Write-Host "   Ctrl+Shift+P -> 'Developer: Reload Window'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Откройте Continue" -ForegroundColor White
Write-Host "   Нажмите Ctrl+L или найдите иконку в боковой панели" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Выберите модель" -ForegroundColor White
Write-Host "   • Grok 4.1 Fast (Free) - для общих задач" -ForegroundColor Gray
Write-Host "   • KAT-Coder-Pro (Free) - для программирования" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Начните чат!" -ForegroundColor White
Write-Host "   Все бесплатные модели OpenRouter готовы к использованию" -ForegroundColor Gray
Write-Host ""

Write-Host "📖 Документация:" -ForegroundColor Yellow
Write-Host "   .vscode/ALTERNATIVE_AI_EXTENSIONS.md" -ForegroundColor Gray
Write-Host "   .vscode/continue-config.json" -ForegroundColor Gray
Write-Host ""

Write-Host "🔧 Дополнительные команды:" -ForegroundColor Yellow
Write-Host "   .\setup-ai-extensions.ps1 -All    # Установить все расширения" -ForegroundColor Gray
Write-Host "   .\check-openrouter-setup.ps1      # Проверить настройки" -ForegroundColor Gray
Write-Host "   .\test-openrouter-models.ps1      # Протестировать модели" -ForegroundColor Gray
Write-Host ""
