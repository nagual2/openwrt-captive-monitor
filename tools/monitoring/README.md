# Monitoring Tools

This directory contains PowerShell scripts for monitoring GitHub Actions workflows and builds.

## Available Tools

### Build Monitoring

- **monitor-build.ps1** - Monitors a single build workflow
- **monitor-build-detailed.ps1** - Detailed monitoring with step-by-step output
- **monitor-all-builds.ps1** - Monitors all active builds simultaneously
- **build-arch.ps1** - Architecture-specific build monitoring

## Usage

### Monitor a Single Build

```powershell
.\tools\monitoring\monitor-build.ps1 -RunId <run-id>
```

### Monitor All Active Builds

```powershell
.\tools\monitoring\monitor-all-builds.ps1
```

### Detailed Build Monitoring

```powershell
.\tools\monitoring\monitor-build-detailed.ps1 -RunId <run-id> -Verbose
```

## Requirements

- PowerShell 5.1+ or PowerShell Core 7+
- GitHub CLI (`gh`) installed and authenticated
- Windows or cross-platform PowerShell

## Features

- Real-time build status updates
- Step-by-step progress tracking
- Error detection and highlighting
- Multi-build parallel monitoring
- Automatic refresh intervals

## Related Documentation

- [GitHub Actions Workflows](../../.github/workflows/)
- [CI Documentation](../../docs/ci/)
- [Common Commands](../../.kiro/steering/common-commands.md)
