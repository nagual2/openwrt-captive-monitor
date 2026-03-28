#!/usr/bin/env pwsh
# Управление Captive Portal Daemon (Selenium/Chrome) в Docker под Windows

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'build', 'clean')]
    [string]$Action = 'status'
)

$ContainerName = "captive-daemon"
$ImageName = "captive-portal-daemon:latest"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

# Проверка наличия Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Desktop не найден. Пожалуйста, установите его." -ForegroundColor Red
    exit 1
}

function Start-Daemon {
    Write-Host "🚀 Запуск Captive Portal Daemon (Selenium)..." -ForegroundColor Green
    
    # Создать директории для логов и данных
    $LogDir = Join-Path $PSScriptRoot "logs"
    $DataDir = Join-Path $PSScriptRoot "data"
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
    if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir | Out-Null }
    
    # Проверить, не запущен ли уже
    $existing = docker ps -q --filter "name=$ContainerName"
    if ($existing) {
        Write-Host "⚠️  Контейнер уже запущен" -ForegroundColor Yellow
        return
    }
    
    # Использовать docker-compose если есть, иначе docker run
    if (Test-Path (Join-Path $PSScriptRoot "docker-compose.yml")) {
        docker-compose -f (Join-Path $PSScriptRoot "docker-compose.yml") up -d
    } else {
        docker run -d `
            --name $ContainerName `
            --network host `
            -v "$($LogDir):/var/log" `
            -v "$($DataDir):/var/lib/captive-portal" `
            --shm-size=2g `
            $ImageName
    }
    
    Write-Host "✅ Демон запущен" -ForegroundColor Green
}

function Stop-Daemon {
    Write-Host "🛑 Остановка Captive Portal Daemon..." -ForegroundColor Yellow
    if (Test-Path (Join-Path $PSScriptRoot "docker-compose.yml")) {
        docker-compose -f (Join-Path $PSScriptRoot "docker-compose.yml") down
    } else {
        docker stop $ContainerName 2>$null
        docker rm $ContainerName 2>$null
    }
    Write-Host "✅ Демон остановлен" -ForegroundColor Green
}

function Restart-Daemon {
    Stop-Daemon
    Start-Sleep -Seconds 2
    Start-Daemon
}

function Show-Status {
    Write-Host "📊 Статус Captive Portal Daemon (Selenium)" -ForegroundColor Cyan
    Write-Host ""
    
    $status = docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
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
    
    $LogFile = Join-Path $PSScriptRoot "logs\captive_portal_auth.log"
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 50 -Wait
    } else {
        # Если файл лога ещё не создан, пробуем логи докера
        docker logs --tail 50 -f $ContainerName
    }
}

function Build-Image {
    Write-Host "🔨 Сборка Docker образа (Debian + Selenium)..." -ForegroundColor Cyan
    
    # Засекаем время и размер до сборки
    $startTime = Get-Date
    
    docker build -f (Join-Path $PSScriptRoot "Dockerfile") -t $ImageName $ProjectRoot
    
    # Проверка размера образа
    $imageSize = docker images --filter "reference=$ImageName" --format "{{.Size}}"
    $duration = (Get-Date) - $startTime
    
    Write-Host "✅ Образ собран: $ImageName" -ForegroundColor Green
    Write-Host "📊 Размер образа: $imageSize" -ForegroundColor Cyan
    Write-Host "⏱️ Время сборки: $($duration.TotalSeconds.ToString("F1")) сек" -ForegroundColor Gray
    
    # Проверка лимита в 2ГБ (согласно спецификации docker-windows-optimization)
    if ($imageSize -like "*GB*") {
        $sizeValue = [double]($imageSize -replace "GB", "").Trim()
        if ($sizeValue -gt 2.0) {
            Write-Host "⚠️ ВНИМАНИЕ: Размер образа ($imageSize) превышает лимит 2GB!" -ForegroundColor Yellow
        }
    }
}

function Clean-All {
    Write-Host "🧹 Очистка..." -ForegroundColor Yellow
    Stop-Daemon
    docker rmi $ImageName 2>$null
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
