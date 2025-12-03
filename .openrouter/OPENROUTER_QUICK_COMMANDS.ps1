#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Быстрые команды для работы с OpenRouter

.DESCRIPTION
    Набор функций для быстрого тестирования и переключения моделей OpenRouter
#>

# Загрузить API ключ
function Load-OpenRouterKey {
    $env:OPENROUTER_API_KEY = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
    if ($env:OPENROUTER_API_KEY) {
        Write-Host "✅ API ключ загружен" -ForegroundColor Green
    } else {
        Write-Host "❌ API ключ не найден. Выполните: .\setup-openrouter.ps1" -ForegroundColor Red
    }
}

# Быстрый тест модели
function Test-Model {
    param(
        [string]$ModelId = "x-ai/grok-4.1-fast:free",
        [string]$Message = "Привет! Как дела?"
    )

    if (-not $env:OPENROUTER_API_KEY) {
        Load-OpenRouterKey
    }

    $headers = @{
        "Authorization" = "Bearer $env:OPENROUTER_API_KEY"
        "Content-Type" = "application/json"
        "HTTP-Referer" = "https://localhost"
        "X-Title" = "OpenWrt Captive Monitor"
    }

    $body = @{
        model = $ModelId
        messages = @(@{
            role = "user"
            content = $Message
        })
        temperature = 0.7
        max_tokens = 200
    } | ConvertTo-Json -Depth 3

    try {
        Write-Host "🧪 Тестирование модели: $ModelId" -ForegroundColor Cyan
        $response = Invoke-WebRequest -Uri "https://openrouter.ai/api/v1/chat/completions" -Method POST -Headers $headers -Body $body -TimeoutSec 30
        $result = ($response.Content | ConvertFrom-Json).choices[0].message.content
        Write-Host "✅ Ответ: $result" -ForegroundColor Green
    } catch {
        Write-Host "❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Показать доступные бесплатные модели
function Show-FreeModels {
    Write-Host "🆓 Доступные бесплатные модели:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Общие задачи:" -ForegroundColor Yellow
    Write-Host "  • x-ai/grok-4.1-fast:free          - Grok 4.1 Fast (рекомендуется)" -ForegroundColor Green
    Write-Host "  • amazon/nova-2-lite-v1:free       - Amazon Nova 2 Lite" -ForegroundColor White
    Write-Host "  • arcee-ai/trinity-mini:free        - Trinity Mini" -ForegroundColor White
    Write-Host ""
    Write-Host "Программирование:" -ForegroundColor Yellow
    Write-Host "  • kwaipilot/kat-coder-pro:free     - KAT-Coder-Pro" -ForegroundColor White
    Write-Host ""
    Write-Host "Анализ и рассуждения:" -ForegroundColor Yellow
    Write-Host "  • allenai/olmo-3-32b-think:free    - Olmo 3 32B Think" -ForegroundColor White
    Write-Host ""
}

# Быстрые алиасы
function Test-Grok { Test-Model -ModelId "x-ai/grok-4.1-fast:free" -Message $args[0] }
function Test-Nova { Test-Model -ModelId "amazon/nova-2-lite-v1:free" -Message $args[0] }
function Test-Coder { Test-Model -ModelId "kwaipilot/kat-coder-pro:free" -Message $args[0] }

# Экспорт функций
Export-ModuleMember -Function Load-OpenRouterKey, Test-Model, Show-FreeModels, Test-Grok, Test-Nova, Test-Coder

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   OpenRouter Quick Commands загружены                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Доступные команды:" -ForegroundColor Yellow
Write-Host "  Load-OpenRouterKey    - Загрузить API ключ" -ForegroundColor White
Write-Host "  Show-FreeModels       - Показать бесплатные модели" -ForegroundColor White
Write-Host "  Test-Model            - Тестировать любую модель" -ForegroundColor White
Write-Host "  Test-Grok 'вопрос'    - Быстрый тест Grok" -ForegroundColor Green
Write-Host "  Test-Nova 'вопрос'    - Быстрый тест Nova" -ForegroundColor White
Write-Host "  Test-Coder 'вопрос'   - Быстрый тест Coder" -ForegroundColor White
Write-Host ""
Write-Host "Примеры:" -ForegroundColor Cyan
Write-Host "  Test-Grok 'Объясни что такое OpenWrt'" -ForegroundColor Gray
Write-Host "  Test-Coder 'Напиши bash функцию для проверки сети'" -ForegroundColor Gray
Write-Host ""
