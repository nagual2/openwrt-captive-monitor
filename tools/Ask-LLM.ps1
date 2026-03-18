# Ask-LLM.ps1 - Универсальная PowerShell обертка для LLM провайдеров

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Prompt,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("zai", "megallm")]
    [string]$Provider = "zai",
    
    [Parameter(Mandatory=$false)]
    [string]$Model,
    
    [Parameter(Mandatory=$false)]
    [double]$Temperature = 0.7,
    
    [Parameter(Mandatory=$false)]
    [int]$MaxTokens = 2000,
    
    [Parameter(Mandatory=$false)]
    [switch]$Heavy  # Использовать мощную модель
)

# Загрузить API ключи из .env
$envFile = Join-Path $PSScriptRoot ".." ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Определить модель
if (-not $Model) {
    if ($Provider -eq "zai") {
        $Model = if ($Heavy) { "glm-5" } else { "glm-4.7-flash" }
    } elseif ($Provider -eq "megallm") {
        $Model = if ($Heavy) { "alibaba-qwen3.5-397b" } else { "mistralai/mistral-nemotron" }
    }
}

# Показать информацию о выборе
if ($Heavy) {
    Write-Host "Используется мощная модель: $Model ($Provider)" -ForegroundColor Cyan
} else {
    Write-Host "Используется модель: $Model ($Provider)" -ForegroundColor Green
}

# Вызвать Python скрипт
$pythonScript = Join-Path $PSScriptRoot "universal_llm_client.py"
python $pythonScript --provider $Provider --model $Model --prompt $Prompt --temperature $Temperature --max-tokens $MaxTokens
