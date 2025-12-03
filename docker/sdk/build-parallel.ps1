#!/usr/bin/env pwsh
# Parallel build script for all OpenWrt SDK architectures
# Builds all 8 architectures simultaneously using background jobs

param(
    [string]$OpenwrtVersion = "23.05.5",
    [string]$Registry = "ghcr.io/nagual2",
    [int]$MaxParallel = 8,
    [switch]$Help
)

$ErrorActionPreference = "Continue"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

if ($Help) {
    Write-Host @"
Usage: .\build-parallel.ps1 [OPTIONS]

Build all OpenWrt SDK Docker images in parallel

OPTIONS:
    -OpenwrtVersion VERSION    OpenWrt version (default: 23.05.5)
    -Registry REGISTRY         Container registry (default: ghcr.io/nagual2)
    -MaxParallel N            Max parallel builds (default: 8)
    -Help                      Show this help

EXAMPLES:
    # Build all architectures in parallel
    .\build-parallel.ps1

    # Build with 4 parallel jobs
    .\build-parallel.ps1 -MaxParallel 4
"@
    exit 0
}

# Define all architectures
$architectures = @(
    @{ target = "x86"; subtarget = "64"; slug = "x86-64" },
    @{ target = "ath79"; subtarget = "generic"; slug = "ath79-generic" },
    @{ target = "ramips"; subtarget = "mt76x8"; slug = "ramips-mt76x8" },
    @{ target = "mediatek"; subtarget = "filogic"; slug = "mediatek-filogic" },
    @{ target = "ipq40xx"; subtarget = "generic"; slug = "ipq40xx-generic" },
    @{ target = "ipq806x"; subtarget = "generic"; slug = "ipq806x-generic" },
    @{ target = "bcm27xx"; subtarget = "bcm2711"; slug = "bcm27xx-bcm2711" },
    @{ target = "rockchip"; subtarget = "armv8"; slug = "rockchip-armv8" }
)

Write-ColorOutput "=== Parallel OpenWrt SDK Build ===" "Cyan"
Write-ColorOutput "OpenWrt Version: $OpenwrtVersion" "White"
Write-ColorOutput "Registry: $Registry" "White"
Write-ColorOutput "Architectures: $($architectures.Count)" "White"
Write-ColorOutput "Max Parallel: $MaxParallel" "White"
Write-ColorOutput ""

# Get commit SHA
try {
    $shortSha = git rev-parse --short=8 HEAD
    Write-ColorOutput "Commit SHA: $shortSha" "Green"
} catch {
    $shortSha = "local"
    Write-ColorOutput "WARNING: Could not get git SHA, using 'local'" "Yellow"
}

Write-ColorOutput ""
Write-ColorOutput "Starting parallel builds..." "Yellow"
Write-ColorOutput ""

# Create jobs for each architecture
$jobs = @()
foreach ($arch in $architectures) {
    $target = $arch.target
    $subtarget = $arch.subtarget
    $slug = $arch.slug
    
    $imageTag = "${Registry}/openwrt-sdk:${OpenwrtVersion}-${slug}-latest"
    $imageTagSha = "${Registry}/openwrt-sdk:${OpenwrtVersion}-${slug}-${shortSha}"
    
    Write-ColorOutput "Queuing: $slug" "Cyan"
    
    # Create background job for this architecture
    $job = Start-Job -ScriptBlock {
        param($target, $subtarget, $slug, $imageTag, $imageTagSha, $version)
        
        $result = @{
            slug = $slug
            success = $false
            error = $null
            buildTime = 0
            imageSize = $null
        }
        
        $startTime = Get-Date
        
        try {
            # Build image
            docker build `
                --build-arg UBUNTU_VERSION=24.04 `
                --build-arg OPENWRT_VERSION=$version `
                --build-arg SDK_TARGET=$target `
                --build-arg SDK_SUBTARGET=$subtarget `
                --tag $imageTag `
                --tag $imageTagSha `
                --file docker/sdk/Dockerfile `
                .
            
            if ($LASTEXITCODE -ne 0) {
                throw "Docker build failed with exit code $LASTEXITCODE"
            }
            
            # Get image size
            $result.imageSize = docker images $imageTag --format "{{.Size}}"
            
            # Validate image
            docker run --rm $imageTag test -d /opt/openwrt-sdk 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Image validation failed"
            }
            
            # Push image
            docker push $imageTag 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to push $imageTag"
            }
            
            docker push $imageTagSha 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to push $imageTagSha"
            }
            
            $result.success = $true
            
        } catch {
            $result.error = $_.Exception.Message
        }
        
        $endTime = Get-Date
        $result.buildTime = ($endTime - $startTime).TotalMinutes
        
        return $result
        
    } -ArgumentList $target, $subtarget, $slug, $imageTag, $imageTagSha, $OpenwrtVersion
    
    $jobs += @{
        Job = $job
        Slug = $slug
        StartTime = Get-Date
    }
    
    # Throttle if we hit max parallel
    while ((Get-Job -State Running).Count -ge $MaxParallel) {
        Start-Sleep -Seconds 5
    }
}

Write-ColorOutput ""
Write-ColorOutput "All builds queued. Waiting for completion..." "Yellow"
Write-ColorOutput ""

# Monitor progress
$completed = 0
$total = $jobs.Count

while ($completed -lt $total) {
    Start-Sleep -Seconds 10
    
    $running = (Get-Job -State Running).Count
    $completedJobs = (Get-Job -State Completed).Count
    
    if ($completedJobs -ne $completed) {
        $completed = $completedJobs
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-ColorOutput "[$timestamp] Progress: $completed/$total completed, $running running" "Cyan"
    }
}

Write-ColorOutput ""
Write-ColorOutput "All builds finished. Collecting results..." "Yellow"
Write-ColorOutput ""

# Collect results
$results = @()
$successCount = 0
$failedCount = 0

foreach ($jobInfo in $jobs) {
    $result = Receive-Job -Job $jobInfo.Job -Wait
    $results += $result
    
    if ($result.success) {
        $successCount++
        Write-ColorOutput "✅ $($result.slug) - $([math]::Round($result.buildTime, 2)) min - $($result.imageSize)" "Green"
    } else {
        $failedCount++
        Write-ColorOutput "❌ $($result.slug) - Failed: $($result.error)" "Red"
    }
    
    Remove-Job -Job $jobInfo.Job
}

# Summary
Write-ColorOutput ""
Write-ColorOutput "================================================" "Cyan"
Write-ColorOutput "Build Summary" "Cyan"
Write-ColorOutput "================================================" "Cyan"
Write-ColorOutput "Total: $total" "White"
Write-ColorOutput "Successful: $successCount" "Green"
Write-ColorOutput "Failed: $failedCount" "Red"

if ($failedCount -gt 0) {
    Write-ColorOutput ""
    Write-ColorOutput "Failed architectures:" "Red"
    foreach ($result in $results) {
        if (-not $result.success) {
            Write-ColorOutput "  - $($result.slug): $($result.error)" "Red"
        }
    }
    exit 1
}

Write-ColorOutput ""
Write-ColorOutput "All images built and pushed successfully!" "Green"
exit 0
