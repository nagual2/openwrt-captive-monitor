#!/usr/bin/env pwsh
# Monitor build progress

$processId = 5
$lastLines = 30

Write-Host "=== Monitoring Build Process (Process ID: $processId) ===" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring (build will continue)" -ForegroundColor Yellow
Write-Host ""

$iteration = 0
while ($true) {
    $iteration++
    Clear-Host
    
    Write-Host "=== Build Monitor - Iteration $iteration ===" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor White
    Write-Host ""
    
    # Get process output
    try {
        $output = docker ps --filter "ancestor=ubuntu:24.04" --format "{{.ID}}: {{.Status}}"
        if ($output) {
            Write-Host "Active Docker containers:" -ForegroundColor Green
            Write-Host $output
            Write-Host ""
        }
    } catch {
        # Ignore errors
    }
    
    Write-Host "Recent output:" -ForegroundColor Yellow
    Write-Host "----------------------------------------"
    
    # Show last lines from log file if it exists
    if (Test-Path "build.log") {
        Get-Content "build.log" -Tail $lastLines
    } else {
        Write-Host "No log file yet..." -ForegroundColor Gray
    }
    
    Write-Host "----------------------------------------"
    Write-Host ""
    Write-Host "Refreshing in 10 seconds..." -ForegroundColor Gray
    
    Start-Sleep -Seconds 10
}
