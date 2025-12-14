# WSL Routing Manager - PowerShell обертка
# Управление маршрутизацией WSL через dev сервер для отладки

param(
    [Parameter(Position=0)]
    [ValidateSet("enable", "disable", "status", "reset", "test", "help")]
    [string]$Command = "status"
)

# Цвета для вывода
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param($Message, $Color = $Reset)
    Write-Host "$Color$Message$Reset"
}

function Write-Info {
    param($Message)
    Write-ColorOutput "[INFO] $Message" $Blue
}

function Write-Success {
    param($Message)
    Write-ColorOutput "[SUCCESS] $Message" $Green
}

function Write-Warning {
    param($Message)
    Write-ColorOutput "[WARNING] $Message" $Yellow
}

function Write-Error {
    param($Message)
    Write-ColorOutput "[ERROR] $Message" $Red
}

# Проверить, что WSL доступен
try {
    $wslVersion = wsl --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "WSL не установлен или не доступен"
    }
} catch {
    Write-Error "WSL не доступен: $_"
    Write-Info "Убедитесь, что WSL 2 установлен и запущен"
    exit 1
}

# Проверить, что скрипт существует
$scriptPath = "tools/wsl_routing_manager.sh"
if (-not (Test-Path $scriptPath)) {
    Write-Error "Скрипт $scriptPath не найден"
    exit 1
}

# Показать справку
if ($Command -eq "help") {
    Write-Info "WSL Routing Manager - управление маршрутизацией через dev сервер"
    Write-Host ""
    Write-Host "Использование: .\tools\wsl_routing_manager.ps1 [команда]"
    Write-Host ""
    Write-Host "Команды:"
    Write-Host "  enable    - Включить маршрутизацию через dev сервер (192.168.1.1)"
    Write-Host "  disable   - Отключить маршрутизацию через dev сервер"
    Write-Host "  status    - Показать текущий статус маршрутизации"
    Write-Host "  reset     - Сбросить маршрутизацию к WSL по умолчанию"
    Write-Host "  test      - Протестировать подключение"
    Write-Host "  help      - Показать эту справку"
    Write-Host ""
    Write-Host "Примеры:"
    Write-Host "  .\tools\wsl_routing_manager.ps1 enable     # Включить маршрутизацию через dev"
    Write-Host "  .\tools\wsl_routing_manager.ps1 status     # Проверить состояние"
    Write-Host "  .\tools\wsl_routing_manager.ps1 test       # Протестировать подключение"
    Write-Host "  .\tools\wsl_routing_manager.ps1 disable    # Вернуться к обычной маршрутизации"
    Write-Host ""
    Write-Warning "ВНИМАНИЕ: Требуются права sudo в WSL для изменения маршрутов"
    Write-Info "Выполните в WSL: sudo -v (для кэширования пароля)"
    exit 0
}

# Предупреждение для команд, изменяющих маршрутизацию
if ($Command -in @("enable", "disable", "reset")) {
    Write-Warning "Команда '$Command' изменит маршрутизацию WSL"

    if ($Command -eq "enable") {
        Write-Info "Весь интернет трафик из WSL будет идти через dev сервер (192.168.1.1)"
        Write-Info "Это полезно для отладки captive portal detection"
    } elseif ($Command -eq "disable") {
        Write-Info "Маршрутизация будет восстановлена к предыдущему состоянию"
    } elseif ($Command -eq "reset") {
        Write-Info "Маршрутизация будет сброшена к WSL по умолчанию"
    }

    $confirmation = Read-Host "Продолжить? (y/N)"
    if ($confirmation -notmatch '^[Yy]') {
        Write-Info "Операция отменена"
        exit 0
    }
}

# Выполнить команду в WSL
Write-Info "Выполняем команду '$Command' в WSL..."

try {
    wsl bash $scriptPath $Command
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Success "Команда '$Command' выполнена успешно"

        # Дополнительные советы
        switch ($Command) {
            "enable" {
                Write-Host ""
                Write-Info "Маршрутизация через dev сервер включена!"
                Write-Info "Теперь можно тестировать captive portal detection:"
                Write-Host "  wsl ssh root@dev-openwrt 'logread -f | grep captive'"
                Write-Host "  wsl curl -v http://detectportal.firefox.com/canonical.html"
            }
            "disable" {
                Write-Host ""
                Write-Info "Обычная маршрутизация восстановлена"
                Write-Info "WSL снова использует стандартный шлюз"
            }
            "reset" {
                Write-Host ""
                Write-Info "Маршрутизация сброшена к WSL по умолчанию"
            }
        }
    } else {
        Write-Error "Команда '$Command' завершилась с ошибкой (код: $exitCode)"

        if ($exitCode -eq 1) {
            Write-Host ""
            Write-Warning "Возможные причины:"
            Write-Host "  - Нет прав sudo в WSL (выполните: wsl sudo -v)"
            Write-Host "  - Dev сервер недоступен (проверьте подключение)"
            Write-Host "  - Проблемы с сетевой конфигурацией"
            Write-Host ""
            Write-Info "Для диагностики выполните:"
            Write-Host "  .\tools\wsl_routing_manager.ps1 status"
            Write-Host "  .\tools\wsl_routing_manager.ps1 test"
        }
    }
} catch {
    Write-Error "Ошибка выполнения WSL команды: $_"
    exit 1
}

exit $exitCode
