# openwrt-captive-monitor

[![ShellCheck](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/shellcheck.yml/badge.svg)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/shellcheck.yml)

A lightweight OpenWrt helper that monitors WAN connectivity, detects captive portals, and temporarily intercepts LAN DNS/HTTP traffic so clients can authenticate. Once internet access is restored, the helper automatically cleans up dnsmasq overrides, HTTP redirects, and NAT rules.

**Runtime dependencies:** `dnsmasq`, `curl` (installed automatically via `opkg`).

## Release notes

See [CHANGELOG.md](CHANGELOG.md) for highlights of each release.

## Repository layout

- `package/openwrt-captive-monitor/` – OpenWrt package definition, init script, executable, config defaults, and `uci-defaults` helper.
- `docs/openwrt_captive_monitor_README.md` – extended guide that covers troubleshooting, manual deployment, and advanced usage scenarios.

## Build with the OpenWrt SDK / Buildroot

1. Download and extract the OpenWrt SDK that matches your target (e.g. `openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz`).
2. Copy this repository into the SDK (for example as `package/openwrt-captive-monitor`).
3. From the SDK root, update the build metadata and compile the package:
   ```bash
   make package/openwrt-captive-monitor/compile V=s
   ```
4. The resulting `.ipk` will be available under `bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk`.

> Tip: you can also integrate the repository as a custom feed; add it to `feeds.conf`, run `./scripts/feeds update -a` and `./scripts/feeds install openwrt-captive-monitor`, then build as shown above.

### Quick local packaging (.ipk + opkg feed)

If you only need the shell wrapper without compiling against the full SDK, the helper script below assembles an `.ipk` together with a ready-to-serve opkg feed:

```bash
scripts/build_ipk.sh --arch mips_24kc
```

- `--arch` controls the architecture tag that ends up in the filename (defaults to the `PKG_ARCH` defined in the package Makefile, currently `all`).
- Artifacts are written to `dist/opkg/<arch>/` alongside refreshed `Packages` and `Packages.gz` indexes, so the directory can be pushed as-is to GitHub Pages or any static host.
- Use `scripts/build_ipk.sh --help` for additional knobs such as redirecting the output via `--feed-root`.
- The detailed release/runbook lives in [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md).

## Installing the generated package

1. Copy the built package to the router (replace the filename with the actual artifact):
   ```bash
   scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
   ```
2. Install with opkg:
   ```bash
   ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
   ```
3. Enable and start the service when you are ready (the package keeps it disabled by default):
   ```bash
   uci set captive-monitor.config.enabled='1'
   uci commit captive-monitor
   /etc/init.d/captive-monitor enable
   /etc/init.d/captive-monitor start
   ```
4. On removal, opkg automatically stops the service: `opkg remove openwrt-captive-monitor`.

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
