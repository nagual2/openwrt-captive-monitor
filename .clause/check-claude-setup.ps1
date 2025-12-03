#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Проверка конфигурации Claude в VS Code

.DESCRIPTION
    Скрипт проверяет все аспекты интеграции Claude

.EXAMPLE
    .\check-claude-setup.ps1
#>

param(
  [switch]$Verbose = $false
)

$errors = @()
$warnings = @()
$success = @()

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Claude Setup Verification Script    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка API ключа
Write-Host "1️⃣  Проверка API ключа..." -ForegroundColor Yellow
$apiKey = [System.Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'User')
if ($apiKey) {
  $masked = $apiKey.Substring(0, [Math]::Min(10, $apiKey.Length)) + "..."
  Write-Host "   ✅ API ключ найден: $masked" -ForegroundColor Green
  $success += "API key configured"

  if ($apiKey -notmatch '^sk-') {
    $warnings += "API key does not match expected format (should start with 'sk-')"
    Write-Host "   ⚠️  Предупреждение: ключ не похож на Claude API ключ" -ForegroundColor Yellow
  }
}
else {
  $errors += "ANTHROPIC_API_KEY not set"
  Write-Host "   ❌ API ключ не установлен" -ForegroundColor Red
  Write-Host "      Выполните: [System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'your-key', 'User')" -ForegroundColor Gray
}
Write-Host ""

# 2. Проверка VS Code конфига
Write-Host "2️⃣  Проверка конфигурации VS Code..." -ForegroundColor Yellow
$settingsPath = ".\.vscode\settings.json"
if (Test-Path $settingsPath) {
  Write-Host "   ✅ Файл settings.json найден" -ForegroundColor Green
  $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
  if ($settings) {
    if ($settings.PSObject.Properties | Where-Object Name -eq "anthropic") {
      Write-Host "   ✅ Claude конфигурация присутствует в settings.json" -ForegroundColor Green
      $success += "Settings configured"
    }
    else {
      $warnings += "Claude configuration not found in settings.json"
      Write-Host "   ⚠️  Claude конфигурация не найдена в settings.json" -ForegroundColor Yellow
    }
  }
  else {
    $errors += "Could not parse settings.json"
    Write-Host "   ❌ Невозможно парсить settings.json" -ForegroundColor Red
  }
}
else {
  $errors += "settings.json not found"
  Write-Host "   ❌ Файл settings.json не найден в .vscode/" -ForegroundColor Red
}
Write-Host ""

# 3. Проверка extensions.json
Write-Host "3️⃣  Проверка расширений..." -ForegroundColor Yellow
$extensionsPath = ".\.vscode\extensions.json"
if (Test-Path $extensionsPath) {
  Write-Host "   ✅ Файл extensions.json найден" -ForegroundColor Green
  $extensions = Get-Content $extensionsPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
  if ($extensions.recommendations -contains "anthropic.claude-for-vscode") {
    Write-Host "   ✅ Claude расширение в рекомендациях" -ForegroundColor Green
    $success += "Extensions configured"
  }
  else {
    $warnings += "Claude extension not in recommendations"
    Write-Host "   ⚠️  Claude не в списке рекомендаций расширений" -ForegroundColor Yellow
  }
}
else {
  Write-Host "   ⚠️  Файл extensions.json не найден" -ForegroundColor Yellow
}
Write-Host ""

# 4. Проверка установленного расширения
Write-Host "4️⃣  Проверка установленных расширений VS Code..." -ForegroundColor Yellow
$installed = code --list-extensions 2>&1 | Select-String -Pattern "anthropic" -ErrorAction SilentlyContinue
if ($installed) {
  Write-Host "   ✅ Расширение Claude установлено в VS Code" -ForegroundColor Green
  $success += "Claude extension installed"
}
else {
  Write-Host "   ⚠️  Расширение Claude не установлено" -ForegroundColor Yellow
  Write-Host "      Установите: code --install-extension anthropic.claude-for-vscode" -ForegroundColor Gray
}
Write-Host ""

# 5. Проверка конфигурационных файлов
Write-Host "5️⃣  Проверка конфигурационных файлов..." -ForegroundColor Yellow
$files = @(
  ".\.vscode\claude-config.json",
  ".\.vscode\CLAUDE_SETUP.md",
  ".\.vscode\CLAUDE_TIPS.md",
  ".\.vscode\CLAUDE_README.md",
  ".\.vscode\CLAUDE_VISUAL_GUIDE.md"
)

$foundFiles = 0
foreach ($file in $files) {
  if (Test-Path $file) {
    Write-Host "   ✅ $file" -ForegroundColor Green
    $foundFiles++
  }
  else {
    Write-Host "   ❌ $file" -ForegroundColor Red
    $errors += "Missing $file"
  }
}
$success += "$foundFiles documentation files found"
Write-Host ""

# 6. Проверка скрипта настройки
Write-Host "6️⃣  Проверка скриптов..." -ForegroundColor Yellow
if (Test-Path ".\setup-claude.ps1") {
  Write-Host "   ✅ setup-claude.ps1 найден" -ForegroundColor Green
  $success += "Setup script exists"
}
else {
  Write-Host "   ❌ setup-claude.ps1 не найден" -ForegroundColor Red
  $errors += "Missing setup-claude.ps1"
}
Write-Host ""

# 7. Проверка в PowerShell профиле
Write-Host "7️⃣  Проверка PowerShell профиля..." -ForegroundColor Yellow
$profile = ".\Microsoft.PowerShell_profile.ps1"
if (Test-Path $profile) {
  $profileContent = Get-Content $profile -Raw
  if ($profileContent -match "ANTHROPIC_API_KEY") {
    Write-Host "   ✅ Claude конфигурация в PowerShell профиле" -ForegroundColor Green
    $success += "PowerShell profile updated"
  }
  else {
    $warnings += "Claude configuration not found in PowerShell profile"
    Write-Host "   ⚠️  Claude конфигурация не найдена в профиле" -ForegroundColor Yellow
  }
}
else {
  Write-Host "   ⚠️  PowerShell профиль не найден" -ForegroundColor Yellow
}
Write-Host ""

# Финальный отчет
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          ИТОГОВЫЙ ОТЧЕТ               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
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

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
  Write-Host "🎉 Все конфигурация правильно установлена!" -ForegroundColor Green
  Write-Host ""
  Write-Host "Следующие шаги:" -ForegroundColor Cyan
  Write-Host "1. Перезагрузите VS Code" -ForegroundColor White
  Write-Host "2. Откройте Claude панель (Ctrl+Shift+C)" -ForegroundColor White
  Write-Host "3. Начните использовать Claude!" -ForegroundColor White
  exit 0
}
elseif ($errors.Count -eq 0) {
  Write-Host "⚙️  Конфигурация почти готова" -ForegroundColor Yellow
  Write-Host "   Адресуйте предупреждения выше и перезагрузите VS Code" -ForegroundColor Gray
  exit 0
}
else {
  Write-Host "🔧 Необходимы исправления" -ForegroundColor Red
  Write-Host "   Выполните следующие шаги:" -ForegroundColor Gray
  Write-Host "   1. Прочитайте .vscode/CLAUDE_SETUP.md" -ForegroundColor Gray
  Write-Host "   2. Выполните .\setup-claude.ps1" -ForegroundColor Gray
  Write-Host "   3. Снова запустите этот скрипт" -ForegroundColor Gray
  exit 1
}
