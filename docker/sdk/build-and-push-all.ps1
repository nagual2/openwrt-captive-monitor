#!/usr/bin/env pwsh
# PowerShell script to build and push all OpenWrt SDK Docker images
# This script builds all 8 architectures locally and pushes them to GHCR

param(
    [string]$OpenwrtVersion = "23.05.5",
    [string]$Registry = "ghcr.io/nagual2",
    [switch]$SkipBuild,
    [switch]$PushOnly,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-Usage {
    Write-Host @"
Usage: .\build-and-push-all.ps1 [OPTIONS]

Build and push all OpenWrt SDK Docker images to GHCR

OPTIONS:
    -OpenwrtVersion VERSION    OpenWrt version (default: 23.05.5)
    -Registry REGISTRY         Container registry (default: ghcr.io/nagual2)
    -SkipBuild                 Skip building, only push existing images
    -PushOnly                  Only push images, don't build
    -Help                      Show this help message

EXAMPLES:
    # Build and push all images
    .\build-and-push-all.ps1

    # Build with custom version
    .\build-and-push-all.ps1 -OpenwrtVersion 23.05.4

    # Only push existing images
    .\build-and-push-all.ps1 -PushOnly

PREREQUISITES:
    - Docker Desktop must be running
    - You must be logged in to GHCR: docker login ghcr.io
    - Git must be available for commit SHA

"@
    exit 0
}

if ($Help) {
    Show-Usage
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

Write-ColorOutput "=== OpenWrt SDK Docker Images Build Script ===" "Cyan"
Write-ColorOutput "OpenWrt Version: $OpenwrtVersion" "White"
Write-ColorOutput "Registry: $Registry" "White"
Write-ColorOutput "Total architectures: $($architectures.Count)" "White"
Write-ColorOutput ""

# Check Docker
Write-ColorOutput "Checking Docker..." "Yellow"
try {
    $dockerVersion = docker --version
    Write-ColorOutput "Docker found: $dockerVersion" "Green"
} catch {
    Write-ColorOutput "ERROR: Docker not found or not running" "Red"
    exit 1
}

# Check GHCR login
Write-ColorOutput "Checking GHCR authentication..." "Yellow"
$loginCheck = docker login ghcr.io --password-stdin 2>&1
if ($LASTEXITCODE -ne 0 -and $loginCheck -notmatch "already logged in") {
    Write-ColorOutput "WARNING: Not logged in to GHCR. Attempting to use existing credentials..." "Yellow"
}

# Get commit SHA
try {
    $shortSha = git rev-parse --short=8 HEAD
    Write-ColorOutput "Commit SHA: $shortSha" "Green"
} catch {
    $shortSha = "local"
    Write-ColorOutput "WARNING: Could not get git SHA, using 'local'" "Yellow"
}

Write-ColorOutput ""

$successCount = 0
$failedCount = 0
$skippedCount = 0
$failedArchs = @()

foreach ($arch in $architectures) {
    $target = $arch.target
    $subtarget = $arch.subtarget
    $slug = $arch.slug
    
    $imageTag = "${Registry}/openwrt-sdk:${OpenwrtVersion}-${slug}-latest"
    $imageTagSha = "${Registry}/openwrt-sdk:${OpenwrtVersion}-${slug}-${shortSha}"
    
    Write-ColorOutput "================================================" "Cyan"
    Write-ColorOutput "Processing: $target/$subtarget ($slug)" "Cyan"
    Write-ColorOutput "================================================" "Cyan"
    
    if (-not $PushOnly -and -not $SkipBuild) {
        Write-ColorOutput "Building image..." "Yellow"
        
        $buildStart = Get-Date
        
        try {
            docker build `
                --build-arg UBUNTU_VERSION=24.04 `
                --build-arg OPENWRT_VERSION=$OpenwrtVersion `
                --build-arg SDK_TARGET=$target `
                --build-arg SDK_SUBTARGET=$subtarget `
                --tag $imageTag `
                --tag $imageTagSha `
                --file docker/sdk/Dockerfile `
                .
            
            if ($LASTEXITCODE -ne 0) {
                throw "Docker build failed with exit code $LASTEXITCODE"
            }
            
            $buildEnd = Get-Date
            $buildDuration = ($buildEnd - $buildStart).TotalMinutes
            
            Write-ColorOutput "Build completed in $([math]::Round($buildDuration, 2)) minutes" "Green"
            
            # Check image size
            $imageSize = docker images $imageTag --format "{{.Size}}"
            Write-ColorOutput "Image size: $imageSize" "White"
            
            # Validate image
            Write-ColorOutput "Validating image..." "Yellow"
            docker run --rm $imageTag test -d /opt/openwrt-sdk
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "Image validation passed" "Green"
            } else {
                Write-ColorOutput "WARNING: Image validation failed" "Yellow"
            }
            
        } catch {
            Write-ColorOutput "ERROR: Build failed for $slug" "Red"
            Write-ColorOutput "Error: $_" "Red"
            $failedCount++
            $failedArchs += $slug
            continue
        }
    } else {
        Write-ColorOutput "Skipping build (using existing image)" "Yellow"
        
        # Check if image exists
        $imageExists = docker images $imageTag --format "{{.Repository}}:{{.Tag}}"
        if (-not $imageExists) {
            Write-ColorOutput "WARNING: Image $imageTag not found locally" "Yellow"
            $skippedCount++
            continue
        }
    }
    
    # Push image
    Write-ColorOutput "Pushing image to registry..." "Yellow"
    
    try {
        docker push $imageTag
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to push $imageTag"
        }
        
        docker push $imageTagSha
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to push $imageTagSha"
        }
        
        Write-ColorOutput "Successfully pushed $slug" "Green"
        $successCount++
        
    } catch {
        Write-ColorOutput "ERROR: Push failed for $slug" "Red"
        Write-ColorOutput "Error: $_" "Red"
        $failedCount++
        $failedArchs += $slug
    }
    
    Write-ColorOutput ""
}

# Summary
Write-ColorOutput "================================================" "Cyan"
Write-ColorOutput "Build and Push Summary" "Cyan"
Write-ColorOutput "================================================" "Cyan"
Write-ColorOutput "Total architectures: $($architectures.Count)" "White"
Write-ColorOutput "Successful: $successCount" "Green"
Write-ColorOutput "Failed: $failedCount" "Red"
Write-ColorOutput "Skipped: $skippedCount" "Yellow"

if ($failedCount -gt 0) {
    Write-ColorOutput ""
    Write-ColorOutput "Failed architectures:" "Red"
    foreach ($arch in $failedArchs) {
        Write-ColorOutput "  - $arch" "Red"
    }
    exit 1
}

Write-ColorOutput ""
Write-ColorOutput "All images processed successfully!" "Green"
exit 0
