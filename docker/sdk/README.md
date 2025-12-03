# OpenWrt SDK Docker Images

This directory contains the Dockerfile for building OpenWrt SDK images used in the CI/CD pipeline.

## Overview

The Docker images provide pre-configured OpenWrt SDK environments for building packages across multiple architectures. Using these images significantly reduces build times by eliminating the need to download and extract the SDK on every build.

## Architecture

The Dockerfile uses a multi-stage build approach:

1. **Stage 1 (sdk-downloader)**: Downloads and extracts the OpenWrt SDK
2. **Stage 2 (final)**: Creates the final image with build dependencies and the extracted SDK

This approach minimizes the final image size by excluding download artifacts and temporary files.

## Supported Architectures

The following OpenWrt target architectures are supported:

- `x86/64` - x86_64 architecture
- `ath79/generic` - Atheros AR71xx/AR724x/AR913x
- `ramips/mt76x8` - MediaTek MT76x8
- `mediatek/filogic` - MediaTek Filogic
- `ipq40xx/generic` - Qualcomm IPQ40xx
- `ipq806x/generic` - Qualcomm IPQ806x
- `bcm27xx/bcm2711` - Raspberry Pi 4
- `rockchip/armv8` - Rockchip ARM64

## Building Images

Images are automatically built by the GitHub Actions workflow `.github/workflows/build-sdk-images.yml`.

### Manual Build

To build an image manually:

```bash
docker build \
  --build-arg OPENWRT_VERSION=23.05.5 \
  --build-arg SDK_TARGET=x86 \
  --build-arg SDK_SUBTARGET=64 \
  -t ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest \
  -f docker/sdk/Dockerfile \
  .
```

### Build Arguments

- `UBUNTU_VERSION`: Base Ubuntu version (default: 24.04)
- `OPENWRT_VERSION`: OpenWrt release version (e.g., 23.05.5)
- `SDK_TARGET`: Target architecture (e.g., x86)
- `SDK_SUBTARGET`: Target subtarget (e.g., 64)

## Image Tags

Images are tagged with the following format:

- `{version}-{target}-{subtarget}-latest` - Latest build for this architecture
- `{version}-{target}-{subtarget}-{sha}` - Specific commit SHA

Example: `23.05.5-x86-64-latest`, `23.05.5-x86-64-abc12345`

## Image Contents

Each image contains:

- Ubuntu 24.04 base
- OpenWrt SDK pre-extracted in `/opt/openwrt-sdk`
- Build dependencies (gcc, make, python3, etc.)
- Non-root `builder` user (UID 1000)

## Usage in CI/CD

The images are used in GitHub Actions workflows via the `container:` directive:

```yaml
jobs:
  build:
    runs-on: ubuntu-24.04
    container:
      image: ghcr.io/nagual2/openwrt-sdk:23.05.5-x86-64-latest
    steps:
      - name: Build package
        run: |
          cd /opt/openwrt-sdk
          # Build commands here
```

## Image Size

Target image size: < 2GB per architecture

The multi-stage build and cleanup steps ensure minimal image size by:
- Removing package manager caches
- Excluding download artifacts
- Removing temporary files
- Using `--no-install-recommends` for apt packages

## Maintenance

Images are automatically cleaned up by the cleanup workflow:
- Images older than 90 days are deleted
- Only the last 10 versions per architecture are kept
- Images tagged as `latest` are protected
- Images used in active workflows are protected

## Troubleshooting

### Image too large

If the image exceeds 2GB, check:
- Temporary files in `/tmp` and `/var/tmp`
- Package manager caches in `/var/lib/apt/lists`
- Unnecessary build artifacts

### SDK not found

Ensure the SDK URL is correct for the OpenWrt version and target architecture. Check the OpenWrt downloads page: https://downloads.openwrt.org/releases/

### Build failures

Check the GitHub Actions logs for detailed error messages. Common issues:
- Network timeouts during SDK download
- Insufficient disk space
- Missing build dependencies
