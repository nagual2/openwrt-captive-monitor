#!/usr/bin/env pwsh
# Управление Captive Portal Daemon в Docker

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'build', 'clean')]
    [string]$Action = 'status'
)

$ContainerName = "captive-daemon"
$ImageName = "captive-portal-daemon:latest"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Start-Daemon {
    Write-Host "🚀 Запуск Captive Portal Daemon..." -ForegroundColor Green
    
    # Создать директорию для логов
    $LogDir = Join-Path $PSScriptRoot "logs"
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir | Out-Null
    }
    
    # Проверить, не запущен ли уже
    $existing = wsl docker ps -q --filter "name=$ContainerName"
    if ($existing) {
        Write-Host "⚠️  Контейнер уже запущен" -ForegroundColor Yellow
        return
    }
    
    # Запустить контейнер
    wsl bash -c "cd /mnt/c/git/openwrt-captive-monitor/docker/daemon && docker run -d --name $ContainerName --network host -v /mnt/c/git/openwrt-captive-monitor/docker/daemon/logs:/var/log -v /dev/shm:/dev/shm --cap-add=SYS_ADMIN $ImageName"
    
    Write-Host "✅ Демон запущен" -ForegroundColor Green
    Write-Host "Логи: docker\daemon\logs\captive_portal_daemon.log"
}

function Stop-Daemon {
    Write-Host "🛑 Остановка Captive Portal Daemon..." -ForegroundColor Yellow
    wsl docker stop $ContainerName 2>$null
    wsl docker rm $ContainerName 2>$null
    Write-Host "✅ Демон остановлен" -ForegroundColor Green
}

function Restart-Daemon {
    Stop-Daemon
    Start-Sleep -Seconds 2
    Start-Daemon
}

function Show-Status {
    Write-Host "📊 Статус Captive Portal Daemon" -ForegroundColor Cyan
    Write-Host ""
    
    $status = wsl docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    if ($status -match $ContainerName) {
        Write-Host $status
        Write-Host ""
        Write-Host "✅ Демон работает" -ForegroundColor Green
    } else {
        Write-Host "❌ Демон не запущен" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "📋 Логи Captive Portal Daemon (последние 50 строк)" -ForegroundColor Cyan
    Write-Host "Нажмите Ctrl+C для выхода" -ForegroundColor Gray
    Write-Host ""
    
    $LogFile = Join-Path $PSScriptRoot "logs\captive_portal_daemon.log"
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 50 -Wait
    } else {
        Write-Host "❌ Файл логов не найден: $LogFile" -ForegroundColor Red
    }
}

function Build-Image {
    Write-Host "🔨 Сборка Docker образа..." -ForegroundColor Cyan
    wsl bash -c "cd /mnt/c/git/openwrt-captive-monitor && docker build -f docker/daemon/Dockerfile -t $ImageName ."
    Write-Host "✅ Образ собран" -ForegroundColor Green
}

function Clean-All {
    Write-Host "🧹 Очистка..." -ForegroundColor Yellow
    Stop-Daemon
    wsl docker rmi $ImageName 2>$null
    Write-Host "✅ Очистка завершена" -ForegroundColor Green
}

# Выполнить действие
switch ($Action) {
    'start'   { Start-Daemon }
    'stop'    { Stop-Daemon }
    'restart' { Restart-Daemon }
    'status'  { Show-Status }
    'logs'    { Show-Logs }
    'build'   { Build-Image }
    'clean'   { Clean-All }
}
