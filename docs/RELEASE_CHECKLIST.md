# Release & Feed Publication Checklist

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This checklist documents the flow we used for the `v1.0.1` release (update the
version string whenever you cut the next release) and can be repeated for
subsequent versions.

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

The GitHub Actions workflow **CI** (`.github/workflows/ci.yml`) now:
- Runs linting and formatting checks
- Executes the BusyBox test harness
- Builds package with OpenWrt SDK
- Validates the built `.ipk` file
- Uploads artifacts (`.ipk`, `Packages`, `Packages.gz`)

Every push or pull request targeting `main` produces a verified feed under
`dist/opkg/<arch>/` containing:

- `openwrt-captive-monitor_<version>-<release>_<arch>.ipk`
- `Packages`
- `Packages.gz`

Tag pushes reuse the same workflow to upload the artifacts directly to the
GitHub Release via `softprops/action-gh-release`. Grab the run URL or artifact
log snippet for the release notes to demonstrate successful binary attachment.

### Option A – quick packager

When the repository only ships shell scripts (no native binaries), the helper
below generates the `.ipk` plus a ready-to-serve opkg feed in one go:

```bash
scripts/build_ipk.sh --arch mips_24kc          # pick the same arch as target
```

Install these dependencies before running the helper:
- `binutils`
- `busybox`
- `gzip`
- `pigz`
- `tar`
- `xz-utils`

The helper will abort early with a descriptive error if any tool is missing.

- The command reads `PKG_VERSION`/`PKG_RELEASE` from
  `package/openwrt-captive-monitor/Makefile`.
- Outputs land under `dist/opkg/<arch>/` and include `Packages` + `Packages.gz`
  alongside the generated `.ipk`.
- Use `--feed-root` to point to a different destination if you keep release
  artifacts in a separate repo.
- Run `busybox sh tests/run.sh` after generating artifacts to re-check the
  archive layout and ensure `Packages.gz` matches `Packages`.

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

### Sanity checks

Run the BusyBox test harness (it now validates the `.ipk` layout, control metadata, and that `Packages.gz` matches `Packages`):

```bash
busybox sh tests/run.sh
```

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

1. Update the changelog (if required), regenerate `docs/releases/<version>.md`,
   and make sure the test harness is green (`busybox sh tests/run.sh`).
2. Tag and push the release:
   ```bash
   git tag -a v1.0.1 -m "openwrt-captive-monitor v1.0.1"
   git push origin v1.0.1

   Swap `v1.0.1` for the new version string on future releases.
3. Monitor the **CI** workflow triggered by the tag, ensure the SDK build job succeeds, and confirm the GitHub Release lists:

   - `openwrt-captive-monitor_<version>-<release>_<arch>.ipk`
   - `Packages`
   - `Packages.gz`

   Capture a screenshot of the artifact upload step or copy the workflow run URL into your release notes for traceability. If automation is unavailable, run `scripts/build_ipk.sh` manually (see the README fallback section) and upload the three files above to the release page by hand.

## 5. Host the opkg feed

1. Publish the contents of `dist/opkg/` on a static host (GitHub Pages works
   well):
   ```bash
   git checkout --orphan gh-pages
   rm -rf *
   cp -r ../dist/opkg/* .
   git add .
   git commit -m "Publish feed for v1.0.1"
   git push -f origin gh-pages
   ```
2. Record the feed URL, e.g.:
   ```
   https://<user>.github.io/openwrt-captive-monitor/mips_24kc/Packages
   ```

3. Clients can then add the feed on OpenWrt:
   ```bash
   # Add feed
   echo 'src/gz captive_monitor https://<user>.github.io/openwrt-captive-monitor/mips_24kc' \
        >> /etc/opkg/customfeeds.conf
   ```
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
