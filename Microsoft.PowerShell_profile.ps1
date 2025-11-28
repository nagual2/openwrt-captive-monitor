# ==================================================
# PowerShell Profile - Оптимизированный для разработки
# ==================================================

# ============================================
# ПОЛЕЗНЫЕ ФУНКЦИИ (АКТИВНЫ)
# ============================================

# Функция для безопасного выполнения команд с таймаутом
function Invoke-WithTimeout {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,
        [int]$TimeoutSeconds = 30
    )
    
    $job = Start-Job -ScriptBlock {
        param($cmd)
        Invoke-Expression $cmd
    } -ArgumentList $Command
    
    $completed = Wait-Job -Job $job -Timeout $TimeoutSeconds
    
    if ($completed) {
        Receive-Job -Job $job
        Remove-Job -Job $job
    } else {
        Write-Host "⚠️  Command timed out after $TimeoutSeconds seconds" -ForegroundColor Yellow
        Stop-Job -Job $job
        Remove-Job -Job $job
    }
}

# Функция для очистки WSL и Docker
function Stop-DevEnvironment {
    Write-Host "Stopping Docker containers..." -ForegroundColor Yellow
    docker stop $(docker ps -q) 2>$null
    
    Write-Host "Shutting down WSL..." -ForegroundColor Yellow
    wsl --shutdown
    
    Write-Host "✅ Development environment stopped" -ForegroundColor Green
}

Set-Alias cleanup-dev Stop-DevEnvironment

# Функция для безопасного выполнения bash скриптов
function Invoke-BashSafe {
    param(
        [string]$Script,
        [int]$Timeout = 30
    )
    
    $env:GIT_PAGER = "cat"
    $env:PAGER = "cat"
    
    $command = "wsl bash -c 'export GIT_PAGER=cat; export PAGER=cat; bash $Script'"
    Invoke-WithTimeout -Command $command -TimeoutSeconds $Timeout
}

# Git алиасы
function gst { git --no-pager status }
function gco { param($branch) git checkout $branch }
function gcb { param($branch) git checkout -b $branch }
function gp { git push origin $(git branch --show-current) }
function gl { git --no-pager log --oneline --graph --decorate -10 }
function gd { git --no-pager diff }
function gds { git --no-pager diff --staged }

# Docker алиасы
function dps { docker ps }
function di { docker images }
function dclean { docker system prune -a -f }
function dstop { docker stop $(docker ps -q) }

# GitHub CLI алиасы
function ghw { gh workflow list }
function ghr { gh run list --limit 10 }
function ghp { gh pr status }

# WSL алиасы
function wslbash { param($script) wsl bash $script }

# Отключить пейджер для git глобально
$env:GIT_PAGER = "cat"
$env:PAGER = "cat"

# Универсальная функция для всех операций с файлами
function Invoke-FileOperation {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet('Check', 'Read', 'Write', 'Copy', 'Move', 'Delete', 'List')]
        [string]$Operation,
        
        [Parameter(Mandatory=$true)]
        [string]$Path,
        
        [string]$Destination,
        [string]$Content
    )
    
    switch ($Operation) {
        'Check'  { Test-Path $Path }
        'Read'   { Get-Content $Path -Raw }
        'Write'  { Set-Content -Path $Path -Value $Content }
        'Copy'   { Copy-Item -Path $Path -Destination $Destination -Force }
        'Move'   { Move-Item -Path $Path -Destination $Destination -Force }
        'Delete' { Remove-Item -Path $Path -Force -Recurse }
        'List'   { Get-ChildItem -Path $Path }
    }
}

# Короткие алиасы
Set-Alias fop Invoke-FileOperation
Set-Alias file Invoke-FileOperation

# ============================================
# ЗАКОММЕНТИРОВАННЫЕ ФУНКЦИИ (МОГУТ МЕШАТЬ)
# ============================================

<#
# ВНИМАНИЕ: Эти функции переопределяют Invoke-Expression
# Это может ломать нормальную работу PowerShell и Kiro
# Раскомментируй только если точно знаешь что делаешь

# 1. Авто-исправление команд ИИ с таймаутом
function Invoke-SafeAI {
    param([string]$Command)

    Write-Host "[AI GUARD] Обнаружена команда ИИ..." -ForegroundColor Yellow
    
    # Исправляем типичные ошибки ИИ
    $fixedCmd = $Command -replace 'python -c "', 'python -c "' `
                        -replace 'from a pachlib', 'from pathlib' `
                        -replace 'import readhead', 'import re' `
                        -replace 'Pach\(', 'Path(' `
                        -replace 'protal_', 'portal_' `
                        -replace 'error = ', 'errors=' `
                        -replace 'namespace\.', 're.' `
                        -replace 't''name=', 'r''name=' `
                        -replace '""', '"' `
                        -replace "''", "'"

    # Всегда завершаем кавычки
    if ($fixedCmd -match 'python -c "' -and -not $fixedCmd.EndsWith('"')) {
        $fixedCmd += '"'
    }

    Write-Host "[AI GUARD] Исправленная команда: $fixedCmd" -ForegroundColor Green
    
    # Создаем временный файл для надежности
    $tempFile = "$env:TEMP\ai_safe_script.py"

    if ($fixedCmd -match 'python -c "(.*)"') {
        $pythonCode = $Matches[1] -replace '\\"', '"'
        try {
            [System.IO.File]::WriteAllText($tempFile, $pythonCode, [System.Text.Encoding]::UTF8)
            
            # Запуск с таймаутом
            $process = Start-Process python -ArgumentList $tempFile -PassThru -NoNewWindow -Wait -Timeout 15
            $output = Get-Content $tempFile -ErrorAction SilentlyContinue
            Remove-Item $tempFile -ErrorAction SilentlyContinue
            
            return $output
        }
        catch {
            Remove-Item $tempFile -ErrorAction SilentlyContinue
            Write-Host "[AI GUARD] Ошибка: $($_.Exception.Message)" -ForegroundColor Red
            return "AI_COMMAND_FAILED"
        }
    }
}

# 2. Автоматический перехват всех Python команд
# ВНИМАНИЕ: Это переопределяет стандартный Invoke-Expression!
function Invoke-Expression {
    param([string]$Command)

    # Перехватываем только опасные команды ИИ
    if ($Command -match 'python -c' -and (
        $Command -match 'pachlib|readhead|protal|t''name=|namespace\.|error = ' -or
        $Command -match 'r"name' -or
        ($Command -match 'python -c "' -and -not $Command.EndsWith('"'))
    )) {
        return Invoke-SafeAI $Command
    }
    else {
        # Обычные команды выполняем как есть
        & Microsoft.PowerShell.Utility\Invoke-Expression $Command
    }
}

# 3. Алиасы для удобства
Set-Alias pyai Invoke-SafeAI
Set-Alias fixai Invoke-SafeAI

# 4. Функция принудительного исправления кода ИИ
function Repair-AICode {
    param([string]$Code)

    $fixes = @{
        'from a pachlib' = 'from pathlib'
        'pachlib' = 'pathlib'
        'import readhead' = 'import re'
        'Pach' = 'Path'
        'protal_' = 'portal_'
        'error = ' = 'errors='
        'namespace\.' = 're.'
        't''name=' = 'r''name='
        'r"name' = 'r"name'
        '""' = '"'
        "encoding='utf-8'" = 'encoding="utf-8"'
        "errors='ignore'" = 'errors="ignore"'
    }

    $fixed = $Code
    foreach ($key in $fixes.Keys) {
        $fixed = $fixed -replace $key, $fixes[$key]
    }

    return $fixed
}

# 5. Монитор зависших процессов Python
# ВНИМАНИЕ: Убивает все Python процессы старше 30 секунд!
function Start-AIWatchdog {
    while ($true) {
        $pythonProcs = Get-Process python -ErrorAction SilentlyContinue
        foreach ($proc in $pythonProcs) {
            $runningTime = (Get-Date) - $proc.StartTime
            if ($runningTime.TotalSeconds -gt 30) {
                Write-Host "[WATCHDOG] Убит зависший Python процесс: $($proc.Id)" -ForegroundColor Red
                $proc.Kill()
            }
        }
        Start-Sleep 10
    }
}

# 6. Быстрое исправление последней команды
function Fix-LastCommand {
    $lastCmd = Get-History -Count 1
    if ($lastCmd.CommandLine -match 'python -c') {
        $fixed = Repair-AICode $lastCmd.CommandLine
        Write-Host "Исправленная команда:" -ForegroundColor Green
        Write-Host $fixed -ForegroundColor Yellow
        return $fixed
    }
}

Set-Alias flc Fix-LastCommand

# 8. Автозапуск watchdog в фоне
# ВНИМАНИЕ: Это запускает фоновый процесс который убивает Python!
Start-Job -ScriptBlock ${function:Start-AIWatchdog} | Out-Null
#>

# ============================================
# ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ
# ============================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "PowerShell Profile Loaded" -ForegroundColor Green
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  cleanup-dev     - Stop WSL and Docker" -ForegroundColor White
Write-Host "  gst, gco, gp    - Git shortcuts" -ForegroundColor White
Write-Host "  dps, di, dclean - Docker shortcuts" -ForegroundColor White
Write-Host "  ghw, ghr, ghp   - GitHub CLI shortcuts" -ForegroundColor White
Write-Host "=========================================" -ForegroundColor Cyan
