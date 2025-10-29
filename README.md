# openwrt-captive-monitor

[![Package Build](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml/badge.svg?branch=main&label=Package%20Build)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml?query=branch%3Amain)
[![Tests](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/shellcheck.yml/badge.svg?branch=main&label=Tests)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/shellcheck.yml?query=branch%3Amain)

The **Build OpenWrt packages** workflow provisions the packaging toolchain, runs the BusyBox test harness, builds the `.ipk`, validates the generated `Packages`/`Packages.gz`, and uploads them as artifacts. Tagged builds automatically attach the same files to the GitHub release. **BusyBox lint and test** installs BusyBox, runs `shfmt`, and executes `tests/run.sh` for every push to `main` and pull request targeting `main`.

A lightweight OpenWrt helper that monitors WAN connectivity, detects captive portals, and temporarily intercepts LAN DNS/HTTP traffic so clients can authenticate. Once internet access is restored, the helper automatically cleans up dnsmasq overrides, HTTP redirects, and NAT rules.

**Runtime dependencies:** `dnsmasq`, `curl` (installed automatically via `opkg`).

## Release notes

- [v0.1.3](docs/releases/v0.1.3.md) – package build verification, refreshed release documentation, and end-to-end installation guidance.
- See [CHANGELOG.md](CHANGELOG.md) for highlights of each release.

## Repository layout

- `package/openwrt-captive-monitor/` – OpenWrt package definition, init script, executable, config defaults, and `uci-defaults` helper.
- `docs/openwrt_captive_monitor_README.md` – extended guide that covers troubleshooting, manual deployment, and advanced usage scenarios.

## Download prebuilt packages

Grab the latest `.ipk` from the [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) page:

```bash
wget https://github.com/nagual2/openwrt-captive-monitor/releases/download/v0.1.3/openwrt-captive-monitor_0.1.3-1_all.ipk
```

Replace `v0.1.3` with the desired tag if you need an older version. Each release also includes refreshed `Packages` and `Packages.gz` indexes so the artifacts can be served directly as a custom opkg feed.

## Build with the OpenWrt SDK / Buildroot

1. Download and extract the OpenWrt SDK that matches your target (e.g. `openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz`).
2. Copy this repository into the SDK (for example as `package/openwrt-captive-monitor`).
3. From the SDK root, update the build metadata and compile the package:
   ```bash
   make package/openwrt-captive-monitor/compile V=s
   ```
4. The resulting `.ipk` will be available under `bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk`.

> Tip: you can also integrate the repository as a custom feed; add it to `feeds.conf`, run `./scripts/feeds update -a` and `./scripts/feeds install openwrt-captive-monitor`, then build as shown above.

### Continuous integration

Two GitHub Actions workflows keep the project healthy:

- **Build OpenWrt packages** (`.github/workflows/openwrt-build.yml`) compiles `.ipk` artifacts for supported targets and publishes release assets on tagged builds.
- **BusyBox lint and test** (`.github/workflows/shellcheck.yml`) provisions BusyBox, runs `shfmt`, and executes `tests/run.sh` on every push and pull request targeting `main`.

The badges at the top of this document surface the latest package build and test status for the `main` branch.

For local builds you can still use [`scripts/build_ipk.sh`](scripts/build_ipk.sh) to assemble packages without going through GitHub Actions.

### Quick local packaging (.ipk + opkg feed)

If you only need the shell wrapper without compiling against the full SDK, the helper script below assembles an `.ipk` together with a ready-to-serve opkg feed:

```bash
scripts/build_ipk.sh --arch mips_24kc
```

Install the packaging prerequisites once per workstation or CI runner—`binutils`, `busybox`, `gzip`, `pigz`, `tar`, and `xz-utils` are sufficient for the helper to succeed. On Debian/Ubuntu systems:

```bash
sudo apt-get update
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils
```

The script now fails fast with a descriptive error if any required utility is missing.

- `--arch` controls the architecture tag that ends up in the filename (defaults to the `PKG_ARCH` defined in the package Makefile, currently `all`).
- Artifacts are written to `dist/opkg/<arch>/` alongside refreshed `Packages` and `Packages.gz` indexes, so the directory can be pushed as-is to GitHub Pages or any static host.
- The helper now aborts with a descriptive error if the `.ipk`, `Packages`, or `Packages.gz` files fail to materialise and prints a short summary of the generated feed when it succeeds.
- Use `scripts/build_ipk.sh --help` for additional knobs such as redirecting the output via `--feed-root`.
- Run `busybox sh tests/run.sh` after building if you need to regenerate the packaging validation locally.
- The detailed release/runbook lives in [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md).

#### Manual fallback when CI is unavailable

1. Install the prerequisites shown above.
2. Run `scripts/build_ipk.sh` with the desired `--arch` (and optionally `--feed-root`).
3. Upload `dist/opkg/<arch>/{openwrt-captive-monitor_*.ipk,Packages,Packages.gz}` to the GitHub Release or your static feed host.

## Run tests

Install BusyBox if it is not already present, then execute the ash harness:

```bash
sudo apt-get install -y busybox
busybox sh tests/run.sh
```

## Installing the generated package

1. **Download or build the `.ipk`:**
   - GitHub Releases (prebuilt for the `all` architecture):
     ```bash
     wget https://github.com/nagual2/openwrt-captive-monitor/releases/download/v0.1.3/openwrt-captive-monitor_0.1.3-1_all.ipk
     ```
   - Or build locally from the repository root:
     ```bash
     scripts/build_ipk.sh --arch all
     ```
     Adjust `--arch` if you need architecture-specific naming.
2. **Copy the package to the router** (replace the filename with the actual artifact):
   ```bash
   scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
   ```
3. **Install with opkg:**
   ```bash
   ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
   ```
4. **Enable and start the service when you are ready** (the package keeps it disabled by default):
   ```bash
   uci set captive-monitor.config.enabled='1'
   uci commit captive-monitor
   /etc/init.d/captive-monitor enable
   /etc/init.d/captive-monitor start
   ```
5. On removal, opkg automatically stops the service: `opkg remove openwrt-captive-monitor`.

## Configuration overview

The package stores its defaults in `/etc/config/captive-monitor`. Key options include:

```uci
config captive_monitor 'config'
    option enabled '0'
    option mode 'monitor'                   # monitor (default) or oneshot
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
    option monitor_interval '60'
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
    option enable_syslog '1'
```

Environment variables and CLI flags remain supported for ad-hoc runs; refer to the detailed documentation in `docs/` for advanced scenarios and troubleshooting tips.

## Contributing

Community contributions are welcome. Please review [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, linting, and review expectations before opening a pull request.
