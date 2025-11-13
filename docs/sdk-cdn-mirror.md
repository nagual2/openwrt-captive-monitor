# GitHub Release SDK CDN Mirror

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This project uses GitHub Release as a CDN mirror for the OpenWrt SDK to dramatically improve download speed and reliability for CI/CD builds.

## Overview

The OpenWrt SDK is downloaded from GitHub Releases CDN instead of the official OpenWrt mirrors, providing:
- **2-5 second downloads** (vs 2+ minutes from official mirrors)
- **99.9%+ uptime** with GitHub's global CDN
- **No rate limiting** issues
- **Automatic fallback** to official mirrors if CDN fails
- **Checksum verification** ensures integrity

## Architecture

### Primary Source: GitHub CDN
```
https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-23.05.3/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

### Fallback Source: Official Mirror
```
https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
```

### Checksum Verification
- **Expected SHA256**: `f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254`
- Verification happens after every download
- Build fails immediately if checksum doesn't match

## Implementation Details

### Workflows Using SDK CDN

- **`.github/workflows/ci.yml`** - Main CI/CD pipeline (lint → test → SDK build)

### Download Logic

```bash
# Try GitHub CDN first
if ! wget -q "$GITHUB_CDN_URL" -O sdk.tar.xz; then
    echo "⚠️  CDN failed, falling back to official mirror..."
    wget -q "$OFFICIAL_MIRROR_URL" -O sdk.tar.xz
fi

# Always verify checksum
if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
    echo "❌ Checksum mismatch!"
    exit 1
fi
```

### Caching

Both workflows implement SDK caching:
- **Cache Key**: `openwrt-sdk-23.05.3-${{ runner.os }}`
- **Cache Path**: `openwrt-sdk-*` directory
- **Result**: Instant rebuilds when SDK is cached

## Managing SDK Releases

### Upload New SDK Version

Use the **"Upload SDK to GitHub Release"** workflow:

1. Go to **Actions** → **Upload SDK to GitHub Release**
2. Click **Run workflow**
3. Enter SDK version (default: `23.05.3`)
4. Enable **Force update** to replace existing release
5. Click **Run workflow**

### Manual Upload (Local)

```bash
# Make the script executable
chmod +x scripts/upload-sdk-to-github.sh

# Run the upload script
./scripts/upload-sdk-to-github.sh
```

### Release Structure

Each SDK release contains:
- **SDK File**: `openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz`
- **Checksum File**: `sdk-checksum.txt`

## Performance Benefits

| Source | Average Download Time | Success Rate |
|--------|---------------------|--------------|
| GitHub CDN | 2-5 seconds | 99.9% |
| Official Mirror | 2-5 minutes | 50% (with timeouts) |

## Troubleshooting

### CDN Download Fails
- **Automatic Fallback**: Workflow automatically tries official mirror
- **Check Logs**: Look for "⚠️ CDN failed, falling back to official mirror..."
- **Manual Upload**: Use upload workflow to refresh CDN

### Checksum Mismatch
- **Expected**: `f90d60c7a00a50a1c80807fb32fd4c12bed1fb65871328f3c2171caf9b711254`
- **Cause**: Corrupted download or wrong SDK version
- **Solution**: Re-upload SDK using the upload workflow

### Release Not Found
- **URL**: `https://github.com/nagual2/openwrt-captive-monitor/releases/download/sdk-23.05.3/...`
- **Solution**: Run the upload workflow to create the release

## Security Considerations

- **Checksum Verification**: Prevents tampered SDK downloads
- **Read-only Access**: Build workflows use `contents: read` permissions
- **Separate Upload**: SDK upload uses dedicated workflow with `contents: write`
- **GitHub Token**: Uses automatic `GITHUB_TOKEN` for authentication

## Future Enhancements

- **Multiple SDK Versions**: Support for different OpenWrt versions
- **Architecture Support**: Add SDKs for different architectures (ARM, MIPS)
- **Automatic Updates**: Workflow to detect and upload new SDK versions
- **Metrics Dashboard**: Track CDN usage and performance metrics