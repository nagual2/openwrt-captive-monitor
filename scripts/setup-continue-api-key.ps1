#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Автоматическая настройка API ключа для Continue

.DESCRIPTION
    Скрипт автоматически добавляет OpenRouter API ключ в конфигурацию Continue

.EXAMPLE
    .\setup-continue-api-key.ps1
#>

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Настройка Continue API ключа                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Получить API ключ
$apiKey = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')

if (-not $apiKey) {
    Write-Host "❌ OPENROUTER_API_KEY не установлен" -ForegroundColor Red
    Write-Host "   Выполните: .\setup-openrouter.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ API ключ найден: $($apiKey.Substring(0,15))..." -ForegroundColor Green
Write-Host ""

# Пути к конфигурации Continue
$configPaths = @(
    ".\.continue\config.json",
    "$env:USERPROFILE\.continue\config.json"
)

$updated = $false

foreach ($configPath in $configPaths) {
    if (Test-Path $configPath) {
        Write-Host "📝 Обновление конфигурации: $configPath" -ForegroundColor Cyan

        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json

            # Обновить API ключи для всех моделей
            if ($config.models) {
                foreach ($model in $config.models) {
                    $model.apiKey = $apiKey
                }
            }

            # Обновить для автодополнения
            if ($config.tabAutocompleteModel) {
                $config.tabAutocompleteModel.apiKey = $apiKey
            }

            # Сохранить обновленную конфигурацию
            $config | ConvertTo-Json -Depth 10 | Set-Content $configPath

            Write-Host "   ✅ Конфигурация обновлена" -ForegroundColor Green
            $updated = $true

        } catch {
            Write-Host "   ❌ Ошибка обновления: $_" -ForegroundColor Red
        }

        Write-Host ""
    }
}

if (-not $updated) {
    Write-Host "⚠️  Конфигурация Continue не найдена" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Создайте конфигурацию вручную:" -ForegroundColor Cyan
    Write-Host "1. Откройте Continue (Ctrl+L)" -ForegroundColor White
    Write-Host "2. Нажмите на шестеренку (⚙️)" -ForegroundColor White
    Write-Host "3. Добавьте модели OpenRouter" -ForegroundColor White
    Write-Host "4. Используйте API ключ: $apiKey" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Итоговая информация
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Настройка завершена успешно                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Перезагрузите VS Code (Ctrl+Shift+P -> Reload Window)" -ForegroundColor White
Write-Host "2. Откройте Continue (Ctrl+L)" -ForegroundColor White
Write-Host "3. Выберите модель 'Grok 4.1 Fast (Free)'" -ForegroundColor White
Write-Host "4. Напишите тестовое сообщение: 'Привет!'" -ForegroundColor White
Write-Host ""

Write-Host "🆓 Доступные модели:" -ForegroundColor Cyan
Write-Host "  • Grok 4.1 Fast (Free) - общие задачи" -ForegroundColor Green
Write-Host "  • KAT-Coder-Pro (Free) - программирование" -ForegroundColor Green
Write-Host "  • Olmo 3 32B Think (Free) - анализ" -ForegroundColor Green
Write-Host ""

Write-Host "📖 Документация: CONTINUE_SETUP_INSTRUCTIONS.md" -ForegroundColor Gray
Write-Host ""
