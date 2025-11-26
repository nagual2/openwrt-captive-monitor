param(
    [string]$Target,
    [string]$Subtarget,
    [string]$Slug,
    [string]$Version = "23.05.5",
    [string]$Registry = "ghcr.io/nagual2"
)

$shortSha = git rev-parse --short=8 HEAD
$imageTag = "${Registry}/openwrt-sdk:${Version}-${Slug}-latest"
$imageTagSha = "${Registry}/openwrt-sdk:${Version}-${Slug}-${shortSha}"

Write-Host "Building $Slug..." -ForegroundColor Cyan

docker build `
    --build-arg UBUNTU_VERSION=24.04 `
    --build-arg OPENWRT_VERSION=$Version `
    --build-arg SDK_TARGET=$Target `
    --build-arg SDK_SUBTARGET=$Subtarget `
    --tag $imageTag `
    --tag $imageTagSha `
    --file docker/sdk/Dockerfile `
    .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Pushing $Slug..." -ForegroundColor Yellow
    docker push $imageTag
    docker push $imageTagSha
    Write-Host "✅ $Slug completed!" -ForegroundColor Green
} else {
    Write-Host "❌ $Slug failed!" -ForegroundColor Red
    exit 1
}
