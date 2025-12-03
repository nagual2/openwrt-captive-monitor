#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Проверка конфигурации OpenRouter

.DESCRIPTION
    Скрипт проверяет все аспекты интеграции OpenRouter

.EXAMPLE
    .\check-openrouter-setup.ps1
#>

$errors = @()
$warnings = @()
$success = @()

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   OpenRouter Setup Verification                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка API ключа
Write-Host "1️⃣  Проверка OpenRouter API ключа..." -ForegroundColor Yellow
$apiKey = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
if ($apiKey) {
  $masked = $apiKey.Substring(0, [Math]::Min(15, $apiKey.Length)) + "..."
  Write-Host "   ✅ API ключ найден: $masked" -ForegroundColor Green
  $success += "API key configured"

  if ($apiKey -notmatch '^sk-or') {
    $warnings += "API key does not start with 'sk-or' prefix"
    Write-Host "   ⚠️  Предупреждение: ключ не начинается с 'sk-or'" -ForegroundColor Yellow
  }
}
else {
  $errors += "OPENROUTER_API_KEY not set"
  Write-Host "   ❌ API ключ не установлен" -ForegroundColor Red
  Write-Host "      Выполните: .\setup-openrouter.ps1" -ForegroundColor Gray
}
Write-Host ""

# 2. Проверка конфигурационного файла
Write-Host "2️⃣  Проверка конфигурационного файла..." -ForegroundColor Yellow
$configPath = ".\.vscode\openrouter-config.json"
if (Test-Path $configPath) {
  Write-Host "   ✅ Файл openrouter-config.json найден" -ForegroundColor Green

  try {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json -ErrorAction Stop
    $success += "Config file valid"

    # Проверить структуру
    if ($config.openrouter) {
      Write-Host "   ✅ Структура конфигурации валидна" -ForegroundColor Green

      # Подсчитать модели
      $models = $config.openrouter.models | Get-Member -MemberType NoteProperty
      $modelCount = $models.Count
      Write-Host "   ✅ Найдено $modelCount моделей" -ForegroundColor Green
      $success += "$modelCount models configured"

      # Проверить рекомендуемые модели
      $recommended = 0
      $config.openrouter.models | Get-Member -MemberType NoteProperty | ForEach-Object {
        if ($config.openrouter.models.$($_.Name).recommended -eq $true) {
          $recommended++
        }
      }
      Write-Host "   ✅ Найдено $recommended рекомендуемых моделей" -ForegroundColor Green

    }
    else {
      $warnings += "openrouter section not found in config"
      Write-Host "   ⚠️  Раздел 'openrouter' не найден" -ForegroundColor Yellow
    }
  }
  catch {
    $errors += "Config file is not valid JSON"
    Write-Host "   ❌ Ошибка при чтении конфига: $_" -ForegroundColor Red
  }
}
else {
  $errors += "openrouter-config.json not found"
  Write-Host "   ❌ Файл openrouter-config.json не найден в .vscode/" -ForegroundColor Red
}
Write-Host ""

# 3. Проверка наличия скриптов
Write-Host "3️⃣  Проверка скриптов установки..." -ForegroundColor Yellow
$setupScript = ".\setup-openrouter.ps1"
if (Test-Path $setupScript) {
  Write-Host "   ✅ setup-openrouter.ps1 найден" -ForegroundColor Green
  $success += "Setup script exists"
}
else {
  Write-Host "   ❌ setup-openrouter.ps1 не найден" -ForegroundColor Red
  $errors += "Missing setup-openrouter.ps1"
}
Write-Host ""

# 4. Проверка документации
Write-Host "4️⃣  Проверка документации..." -ForegroundColor Yellow
$docPath = ".\.vscode\OPENROUTER_SETUP.md"
if (Test-Path $docPath) {
  Write-Host "   ✅ OPENROUTER_SETUP.md найден" -ForegroundColor Green
  $success += "Documentation exists"
}
else {
  Write-Host "   ❌ OPENROUTER_SETUP.md не найден" -ForegroundColor Red
  $errors += "Missing OPENROUTER_SETUP.md"
}
Write-Host ""

# 5. Проверка интернет соединения (опционально)
Write-Host "5️⃣  Проверка соединения с OpenRouter..." -ForegroundColor Yellow
try {
  $response = Invoke-WebRequest -Uri "https://openrouter.ai/api/v1/models" `
    -Method GET `
    -TimeoutSec 5 `
    -ErrorAction Stop

  if ($response.StatusCode -eq 200) {
    Write-Host "   ✅ Соединение с OpenRouter установлено" -ForegroundColor Green
    $success += "OpenRouter API reachable"
  }
}
catch {
  $warnings += "Could not reach OpenRouter API"
  Write-Host "   ⚠️  Не удалось достичь OpenRouter API (проверьте интернет)" -ForegroundColor Yellow
}
Write-Host ""

# 6. Проверка API ключа валидности (если есть интернет)
if ($apiKey -and $success -contains "OpenRouter API reachable") {
  Write-Host "6️⃣  Проверка валидности API ключа..." -ForegroundColor Yellow
  try {
    $headers = @{
      "Authorization" = "Bearer $apiKey"
      "Content-Type"  = "application/json"
    }

    $response = Invoke-WebRequest -Uri "https://openrouter.ai/api/v1/models" `
      -Method GET `
      -Headers $headers `
      -TimeoutSec 5 `
      -ErrorAction Stop

    if ($response.StatusCode -eq 200) {
      Write-Host "   ✅ API ключ валиден" -ForegroundColor Green
      $success += "API key valid"
    }
  }
  catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
      $errors += "API key is invalid or expired"
      Write-Host "   ❌ API ключ невалиден или истёк" -ForegroundColor Red
    }
    else {
      $warnings += "Could not validate API key"
      Write-Host "   ⚠️  Не удалось проверить API ключ: $_" -ForegroundColor Yellow
    }
  }
}
else {
  Write-Host "6️⃣  Проверка валидности API ключа пропущена (нет интернета)" -ForegroundColor Yellow
}
Write-Host ""

# Финальный отчет
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║             ИТОГОВЫЙ ОТЧЕТ                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($success.Count -gt 0) {
  Write-Host "✅ Успешно:" -ForegroundColor Green
  foreach ($msg in $success) {
    Write-Host "   • $msg" -ForegroundColor Green
  }
  Write-Host ""
}

if ($warnings.Count -gt 0) {
  Write-Host "⚠️  Предупреждения:" -ForegroundColor Yellow
  foreach ($msg in $warnings) {
    Write-Host "   • $msg" -ForegroundColor Yellow
  }
  Write-Host ""
}

if ($errors.Count -gt 0) {
  Write-Host "❌ Ошибки:" -ForegroundColor Red
  foreach ($msg in $errors) {
    Write-Host "   • $msg" -ForegroundColor Red
  }
  Write-Host ""
}

Write-Host "📊 Статистика:" -ForegroundColor Cyan
Write-Host "   ✅ Успешно: $($success.Count)" -ForegroundColor Green
Write-Host "   ⚠️  Предупреждения: $($warnings.Count)" -ForegroundColor Yellow
Write-Host "   ❌ Ошибки: $($errors.Count)" -ForegroundColor Red
Write-Host ""

# Показать рекомендуемые действия
if ($errors.Count -gt 0) {
  Write-Host "🔧 Действия для исправления:" -ForegroundColor Red

  if ($errors -contains "OPENROUTER_API_KEY not set") {
    Write-Host "   1. Выполните: .\setup-openrouter.ps1" -ForegroundColor Yellow
  }

  if ($errors -contains "openrouter-config.json not found") {
    Write-Host "   2. Создайте файл: .vscode\openrouter-config.json" -ForegroundColor Yellow
  }

  if ($errors -contains "Config file is not valid JSON") {
    Write-Host "   3. Проверьте синтаксис JSON в конфиге" -ForegroundColor Yellow
  }

  if ($errors -contains "API key is invalid or expired") {
    Write-Host "   4. Получите новый API ключ на https://openrouter.ai/keys" -ForegroundColor Yellow
    Write-Host "   5. Выполните: .\setup-openrouter.ps1" -ForegroundColor Yellow
  }
  Write-Host ""
}

# Итоговый статус
if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
  Write-Host "🎉 Все проверки пройдены успешно!" -ForegroundColor Green
  Write-Host ""
  Write-Host "Вы готовы использовать OpenRouter с этими моделями:" -ForegroundColor Cyan

  if (Test-Path $configPath) {
    try {
      $config = Get-Content $configPath -Raw | ConvertFrom-Json
      $config.openrouter.models | Get-Member -MemberType NoteProperty | ForEach-Object {
        $model = $config.openrouter.models.$($_.Name)
        if ($model.recommended) {
          Write-Host "   ⭐ $($model.name) ($($model.id))" -ForegroundColor Green
        }
      }
    }
    catch {}
  }

  exit 0
}
elseif ($errors.Count -eq 0) {
  Write-Host "⚙️  Конфигурация почти готова (только предупреждения)" -ForegroundColor Yellow
  exit 0
}
else {
  Write-Host "🔴 Необходимы исправления перед использованием" -ForegroundColor Red
  exit 1
}
