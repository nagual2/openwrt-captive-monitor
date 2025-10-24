# Release & Feed Publication Checklist

This checklist documents the flow we used for the `v0.1.1` release and can be
repeated for subsequent versions.

## 1. Triage and code verification

1. Review every open pull request/feature branch and rebase it onto `main` if
   required.
2. Validate the changes on a real OpenWrt target:
   - Copy the branch build to the device.
   - Run `opkg remove openwrt-captive-monitor` when upgrading from a previous
     snapshot.
   - Install the new `.ipk`, enable the service and check the syslog for
     warnings.
3. Once validated, merge the branch into `main` (fast-forward preferred) and
   push.

## 2. Build the release artifacts

The GitHub Actions workflow **Build OpenWrt packages** produces release-ready
builds for each supported target (`ath79-generic`, `ramips-mt7621`). It pulls the
matching OpenWrt SDK, runs feed installation plus `defconfig`, and uploads the
following artifacts per matrix entry:

- `openwrt-captive-monitor_<version>_<arch>.ipk`
- `Packages_<target>.gz` (with the plain `Packages` and `Packages.manifest`
  variants)

Download the artifacts from the workflow run or rely on the tag-triggered
release job to attach them automatically.

### Option A – quick packager

When the repository only ships shell scripts (no native binaries) the helper
below generates the `.ipk` plus a ready-to-serve opkg feed in one go:

```bash
scripts/build_ipk.sh --arch mips_24kc          # pick the same arch as target
```

- The command reads `PKG_VERSION`/`PKG_RELEASE` from
  `package/openwrt-captive-monitor/Makefile`.
- Outputs land under `dist/opkg/<arch>/` and include `Packages` + `Packages.gz`
  alongside the generated `.ipk`.
- Use `--feed-root` to point to a different destination if you keep release
  artifacts in a separate repo.

### Option B – official OpenWrt SDK/Buildroot

1. Download the OpenWrt SDK matching your target (e.g.
   `openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz`).
2. Copy this repository into `package/openwrt-captive-monitor/` within the SDK.
3. From the SDK root execute:
   ```bash
   make package/openwrt-captive-monitor/compile V=s
   ```
4. Collect the resulting `.ipk` from
   `bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk` and
   copy it into your feed folder.

## 3. Smoke test the package on OpenWrt

1. Transfer the new `.ipk` to the router:
   ```bash
   scp dist/opkg/<arch>/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
   ```
2. Install via opkg and verify start/stop:
   ```bash
   ssh root@192.168.1.1 <<'EOSSH'
   opkg install /tmp/openwrt-captive-monitor_*.ipk
   uci set captive-monitor.config.enabled='1'
   uci commit captive-monitor
   /etc/init.d/captive-monitor enable
   /etc/init.d/captive-monitor start
   logread | tail -50 | grep captive-monitor
   /etc/init.d/captive-monitor stop
   opkg remove openwrt-captive-monitor
   EOSSH
   ```
3. Ensure cleanup removed NAT/DNS overrides and the service stops cleanly.

## 4. Tag and publish the release

1. Update the changelog (if required) and tag `v0.1.x`:
   ```bash
   git tag -a v0.1.1 -m "openwrt-captive-monitor v0.1.1"
   git push origin v0.1.1
   ```

   - The generated `.ipk` for each architecture.
   - The per-target indexes: `Packages_<target>`, `Packages_<target>.gz`, and
     `Packages_<target>.manifest` (or a zipped copy of the feed directory).

## 5. Host the opkg feed

1. Publish the contents of `dist/opkg/` on a static host (GitHub Pages works
   well):
   ```bash
   git checkout --orphan gh-pages
   rm -rf *
   cp -r ../dist/opkg/* .
   git add .
   git commit -m "Publish feed for v0.1.1"
   git push -f origin gh-pages
   ```
2. Record the feed URL, e.g.
   `https://<user>.github.io/openwrt-captive-monitor/mips_24kc/Packages`.
3. Clients can then add the feed on OpenWrt:
   ```bash
   echo 'src/gz captive_monitor https://<user>.github.io/openwrt-captive-monitor/mips_24kc' >> /etc/opkg/customfeeds.conf
   opkg update
   opkg install openwrt-captive-monitor
   ```

## 6. Post-release verification

- Run `opkg update && opkg install openwrt-captive-monitor` on a clean router
  using the hosted feed URL.
- Confirm that removal (`opkg remove openwrt-captive-monitor`) restores the
  pre-release state.
- Monitor `logread -f | grep captive-monitor` for at least one full portal
  sign-in flow.

Following the checklist ensures that pull requests reach `main`, binaries are
attached to the release, `.ipk` installation works end-to-end, and the opkg feed
remains consumable via HTTP.
