#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Тестирование бесплатных моделей OpenRouter

.DESCRIPTION
    Скрипт тестирует переключение между различными бесплатными моделями OpenRouter

.EXAMPLE
    .\test-openrouter-models.ps1
#>

$apiKey = $env:OPENROUTER_API_KEY
if (-not $apiKey) {
    Write-Host "❌ OPENROUTER_API_KEY не установлен" -ForegroundColor Red
    Write-Host "   Выполните: .\setup-openrouter.ps1" -ForegroundColor Gray
    exit 1
}

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Тестирование бесплатных моделей OpenRouter          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Заголовки с правильной авторизацией
$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
    "HTTP-Referer" = "https://localhost"
    "X-Title" = "OpenWrt Captive Monitor"
}

# Список бесплатных моделей для тестирования
$models = @(
    @{
        id = "amazon/nova-2-lite-v1:free"
        name = "Amazon Nova 2 Lite"
        description = "Новая модель от Amazon"
    },
    @{
        id = "x-ai/grok-4.1-fast:free"
        name = "Grok 4.1 Fast"
        description = "Быстрая модель от xAI"
    },
    @{
        id = "arcee-ai/trinity-mini:free"
        name = "Trinity Mini"
        description = "Компактная модель"
    }
)

$testPrompt = "Привет! Ответь кратко (1-2 предложения) - какая ты модель и что умеешь?"

foreach ($model in $models) {
    Write-Host "🧪 Тестирование: $($model.name)" -ForegroundColor Yellow
    Write-Host "   ID: $($model.id)" -ForegroundColor Gray
    Write-Host "   Описание: $($model.description)" -ForegroundColor Gray

    $body = @{
        model = $model.id
        messages = @(
            @{
                role = "user"
                content = $testPrompt
            }
        )
        temperature = 0.7
        max_tokens = 150
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-WebRequest `
            -Uri "https://openrouter.ai/api/v1/chat/completions" `
            -Method POST `
            -Headers $headers `
            -Body $body `
            -TimeoutSec 30

        $result = ($response.Content | ConvertFrom-Json).choices[0].message.content
        Write-Host "   ✅ Ответ: $result" -ForegroundColor Green

    } catch {
        Write-Host "   ❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red

        # Попробуем получить детали ошибки
        if ($_.Exception.Response) {
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorContent = $reader.ReadToEnd()
                $errorJson = $errorContent | ConvertFrom-Json
                Write-Host "   Детали: $($errorJson.error.message)" -ForegroundColor Yellow
            } catch {
                Write-Host "   HTTP Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
            }
        }
    }

    Write-Host ""
    Start-Sleep -Seconds 1  # Небольшая задержка между запросами
}

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Тестирование завершено                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Советы:" -ForegroundColor Cyan
Write-Host "   • Используйте модели, которые успешно отвечают" -ForegroundColor White
Write-Host "   • Для программирования лучше подходят coding модели" -ForegroundColor White
Write-Host "   • Для быстрых ответов используйте mini/fast модели" -ForegroundColor White
Write-Host ""
