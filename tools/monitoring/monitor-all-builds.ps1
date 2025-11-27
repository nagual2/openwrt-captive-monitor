# Monitor all builds progress
param(
    [int]$ProcessId = 9,
    [int]$CheckIntervalSeconds = 120
)

Write-Host "=== Monitoring Build Process ===" -ForegroundColor Cyan
Write-Host "Process ID: $ProcessId" -ForegroundColor Yellow
Write-Host "Check interval: $CheckIntervalSeconds seconds" -ForegroundColor Yellow
Write-Host "Started at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

$architectures = @(
    "x86-64",
    "ath79-generic",
    "ramips-mt76x8",
    "mediatek-filogic",
    "ipq40xx-generic",
    "ipq806x-generic",
    "bcm27xx-bcm2711",
    "rockchip-armv8"
)

$iteration = 0
$maxIterations = 240  # 8 hours max

while ($iteration -lt $maxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] Check #$iteration" -ForegroundColor Cyan
    
    # Check if process is still running
    try {
        $output = kiro getProcessOutput --processId $ProcessId --lines 100 2>&1 | Out-String
        
        # Parse current architecture
        if ($output -match "Processing: ([^/]+)/([^\s]+) \(([^)]+)\)") {
            $currentArch = $matches[3]
            Write-Host "  Current: $currentArch" -ForegroundColor Green
        }
        
        # Parse build time
        if ($output -match "Building (\d+\.\d+)s") {
            $buildTime = [math]::Round([double]$matches[1] / 60, 1)
            Write-Host "  Build time: $buildTime minutes" -ForegroundColor Yellow
        }
        
        # Parse push progress
        if ($output -match "Pushing\s+(\d+\.?\d*[KMG]?B)/(\d+\.?\d*[KMG]?B)") {
            Write-Host "  Pushing: $($matches[1]) / $($matches[2])" -ForegroundColor Magenta
        }
        
        # Check for completion
        if ($output -match "Build completed in ([\d\.]+) minutes") {
            Write-Host "  ✅ Completed in $($matches[1]) minutes" -ForegroundColor Green
        }
        
        if ($output -match "Successfully pushed") {
            Write-Host "  ✅ Successfully pushed to registry" -ForegroundColor Green
        }
        
        # Check for errors
        if ($output -match "ERROR:") {
            Write-Host "  ❌ ERROR detected!" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "  Process completed or not found" -ForegroundColor Yellow
        break
    }
    
    # Check local images
    Write-Host ""
    Write-Host "  Local images:" -ForegroundColor Cyan
    $images = docker images ghcr.io/nagual2/openwrt-sdk --format "{{.Tag}}" 2>&1 | 
              Select-String "23.05.5-.*-latest" | 
              ForEach-Object { $_.ToString() -replace "23.05.5-", "" -replace "-latest", "" }
    
    foreach ($arch in $architectures) {
        if ($images -contains $arch) {
            Write-Host "    ✅ $arch" -ForegroundColor Green
        } else {
            Write-Host "    ⏳ $arch" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "  Progress: $($images.Count) / $($architectures.Count) architectures" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Next check in $CheckIntervalSeconds seconds..." -ForegroundColor Gray
    Write-Host "  " + ("=" * 60)
    Write-Host ""
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}

Write-Host "=== Monitoring Complete ===" -ForegroundColor Cyan
