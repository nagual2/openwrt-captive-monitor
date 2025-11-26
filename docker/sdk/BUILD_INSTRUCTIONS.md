# Local Build Instructions for OpenWrt SDK Images

## Prerequisites

1. **Docker Desktop** must be running
2. **Git** must be available
3. **GitHub Personal Access Token** with `write:packages` scope

## Step 1: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "GHCR SDK Images"
4. Select scopes:
   - ✅ `write:packages`
   - ✅ `read:packages`
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

## Step 2: Login to GHCR

### On Windows (PowerShell):
```powershell
# Replace YOUR_TOKEN with your actual token
$env:CR_PAT = "YOUR_TOKEN"
echo $env:CR_PAT | docker login ghcr.io -u nagual2 --password-stdin
```

### On Linux/WSL (Bash):
```bash
# Replace YOUR_TOKEN with your actual token
export CR_PAT=YOUR_TOKEN
echo $CR_PAT | docker login ghcr.io -u nagual2 --password-stdin
```

You should see: `Login Succeeded`

## Step 3: Build and Push All Images

### On Windows (PowerShell):
```powershell
cd C:\git\openwrt-captive-monitor
.\docker\sdk\build-and-push-all.ps1
```

### On Linux/WSL (Bash):
```bash
cd /path/to/openwrt-captive-monitor
bash docker/sdk/build-and-push-all.sh
```

This will:
- Build all 8 SDK images (x86-64, ath79-generic, ramips-mt76x8, mediatek-filogic, ipq40xx-generic, ipq806x-generic, bcm27xx-bcm2711, rockchip-armv8)
- Validate each image
- Push to ghcr.io/nagual2/openwrt-sdk

**Note:** Building all 8 images will take 2-4 hours depending on your machine and network speed.

## Step 4: Build Single Architecture (for testing)

### On Windows (PowerShell):
```powershell
# Build only x86-64 for testing
bash docker/sdk/build-local.sh --target x86 --subtarget 64 --push
```

### On Linux/WSL (Bash):
```bash
# Build only x86-64 for testing
bash docker/sdk/build-local.sh --target x86 --subtarget 64 --push
```

## Troubleshooting

### "unauthorized: authentication required"
- Your token doesn't have `write:packages` scope
- Token expired
- Wrong username (should be `nagual2`)

### "Image size exceeds 2GB limit"
- This is expected with current Dockerfile
- The optimizations in the latest commit should reduce size
- If still too large, we need more aggressive cleanup

### "Docker daemon not running"
- Start Docker Desktop
- Wait for it to fully start (whale icon in system tray)

### Build fails with "download-sdk.sh: not found"
- Make sure you're in the project root directory
- The script path is relative: `docker/sdk/download-sdk.sh`

## Monitoring Progress

The scripts will show:
- Build progress for each architecture
- Image size after build
- Validation results
- Push progress
- Final summary with success/failure counts

## After Successful Push

Once all images are pushed to GHCR:
1. The fix-github-actions spec can proceed (task 4 will be unblocked)
2. CI/CD workflows will use these images
3. Build times should drop from 3-7 minutes to < 3 minutes

## Cleanup

To remove local images after pushing:
```powershell
# Remove all SDK images
docker images | Select-String "openwrt-sdk" | ForEach-Object { docker rmi ($_ -split '\s+')[2] }
```

```bash
# Remove all SDK images
docker images | grep openwrt-sdk | awk '{print $3}' | xargs docker rmi
```
