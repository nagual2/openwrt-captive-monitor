# Monitor build progress with detailed analysis
param(
    [int]$ProcessId = 7,
    [int]$IntervalSeconds = 60,
    [int]$MaxIterations = 120
)

$iteration = 0
$lastStatus = ""

Write-Host "=== Build Monitor Started ===" -ForegroundColor Cyan
Write-Host "Process ID: $ProcessId" -ForegroundColor Yellow
Write-Host "Check interval: $IntervalSeconds seconds" -ForegroundColor Yellow
Write-Host "Max iterations: $MaxIterations" -ForegroundColor Yellow
Write-Host ""

while ($iteration -lt $MaxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] Iteration $iteration/$MaxIterations" -ForegroundColor Cyan
    
    # Get process output
    $output = kiro getProcessOutput --processId $ProcessId --lines 50 2>&1 | Out-String
    
    # Parse current status
    if ($output -match "Building (\d+\.\d+)s") {
        $buildTime = $matches[1]
        Write-Host "  Build time: $buildTime seconds" -ForegroundColor Green
    }
    
    if ($output -match "Pushing\s+(\d+\.?\d*[KMG]?B)/(\d+\.?\d*[KMG]?B)") {
        $current = $matches[1]
        $total = $matches[2]
        Write-Host "  Pushing: $current / $total" -ForegroundColor Yellow
    }
    
    if ($output -match "FINISHED") {
        Write-Host "  Status: Build FINISHED" -ForegroundColor Green
    }
    
    if ($output -match "Build completed in ([\d\.]+) minutes") {
        $minutes = $matches[1]
        Write-Host "  Completed in: $minutes minutes" -ForegroundColor Green
    }
    
    if ($output -match "Successfully pushed") {
        Write-Host "  Status: Successfully pushed to registry" -ForegroundColor Green
    }
    
    if ($output -match "Building.*\((\d+)/(\d+)\)") {
        $current = $matches[1]
        $total = $matches[2]
        Write-Host "  Architecture: $current / $total" -ForegroundColor Magenta
    }
    
    # Check if process is still running
    $processes = kiro listProcesses 2>&1 | Out-String
    if ($processes -notmatch "processId.*$ProcessId") {
        Write-Host ""
        Write-Host "=== Process $ProcessId has completed ===" -ForegroundColor Green
        break
    }
    
    Write-Host ""
    Start-Sleep -Seconds $IntervalSeconds
}

if ($iteration -ge $MaxIterations) {
    Write-Host "=== Monitor reached maximum iterations ===" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Monitor Stopped ===" -ForegroundColor Cyan
