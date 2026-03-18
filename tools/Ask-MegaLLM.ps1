# Ask-MegaLLM.ps1 - PowerShell wrapper для MegaLLM CLI

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Prompt,
    
    [Parameter(Mandatory=$false)]
    [string]$Model = "mistralai/mistral-nemotron",
    
    [Parameter(Mandatory=$false)]
    [double]$Temperature = 0.7,
    
    [Parameter(Mandatory=$false)]
    [int]$MaxTokens = 2000,
    
    [Parameter(Mandatory=$false)]
    [switch]$Heavy  # Использовать мощную модель Qwen 3.5 397B для сложных задач
)

# Если указан флаг -Heavy, переключиться на мощную модель
if ($Heavy) {
    $Model = "alibaba-qwen3.5-397b"
    Write-Host "Используется мощная модель: $Model (397B параметров)" -ForegroundColor Cyan
}

# Загрузить API ключ из .env
$envFile = Join-Path $PSScriptRoot ".." ".env"
if (Test-Path $envFile) {
    $apiKey = Get-Content $envFile | Select-String "MEGALLM_API_KEY" | ForEach-Object { 
        $_ -replace "MEGALLM_API_KEY=", "" 
    }
    $env:MEGALLM_API_KEY = $apiKey
}

# Вызвать Python скрипт
$pythonScript = Join-Path $PSScriptRoot "megallm_client.py"
python $pythonScript --model $Model --prompt $Prompt --temperature $Temperature --max-tokens $MaxTokens
