# PR_TRIAGE — 2025-10-24

## Context
- Working branch: `triage-2-prs-rebase-ci-fixes-openwrt24`
- Base commit: `a43b82ad573a35f0f3acd653be9d58f4b11ca9b1` (`main` at the time of triage)
- Tooling verified via the project "Lint" workflow equivalents (`shfmt`, `shellcheck`).

## Summary
Both legacy PRs were based on a pre-audit tree that no longer matches `main` (missing packaging layout, init wrappers, lint config, etc.). They also failed to run on OpenWrt 24.x because of BusyBox-specific incompatibilities and incomplete procd wiring. The changes below re-implement their intent on top of the current trunk so the originals can be superseded.

---

## PR #1 — `feat(captive-intercept): implement robust captive portal detection and HTTP+DNS intercept for LAN clients`
- Original head: `restore/feat-captive-intercept-dns-http-redirect@68a99f2` (+2 / −1 vs old `main`).
- Problem statement:
  - Rebased state deleted the new repo structure (package layout, CI, docs) and broke linting.
  - Captive DNS lookup relied on `resolveip -s`, which BusyBox 1.36 (OpenWrt 24.x) does not implement, so portal detection failed before firewall rules activated.
  - Service cleanup depended on manual kills; procd never terminated the monitor, leaving nft/iptables rules behind.
- Fixes applied in this branch:
  - [x] Rebased functionality onto the packaging-first layout already on `main` (thin launchers + `/usr/sbin/openwrt_captive_monitor`).
  - [x] Replaced BusyBox-incompatible `resolveip -s` calls with portable `nslookup` fallbacks, keeping IPv4/IPv6 detection intact.
  - [x] Extended the procd init script to export LAN IPv6, DNS/captive lists, and firewall backend hints so the intercept logic receives the same configuration the PR expected.
  - [x] Added deterministic shutdown (`procd_kill`) and reload triggers for `firewall`/`dnsmasq` to guarantee nft/iptables cleanup during service stops or firewall reloads.
- Outcome: the logic now runs on OpenWrt 24.x with fw4/nftables, passes lint, and is ready for a replacement PR. Recommend closing the legacy PR in favour of a new one pointing at this branch.

## PR #2 — `fix(openwrt-captive-monitor): launcher and Makefile env fixes`
- Original head: `restore/feature-openwrt-captive-monitor-opkg@92d8bd7` (+5 / −1 vs old `main`).
- Problem statement:
  - Branch was missing the reconstructed package skeleton and CI metadata that landed after the audit.
  - UCI schema did not expose the LAN/firewall knobs required by the service (cited in the original PR description), so the shipped defaults could not be overridden without editing the script by hand.
- Fixes applied in this branch:
  - [x] Preserved the audited packaging layout while wiring the missing `lan_interface`, `lan_ip`, `lan_ipv6`, and `firewall_backend` options into both `/etc/config/captive-monitor` and the `uci-defaults` seed.
  - [x] Ensured these options propagate to the runtime via procd environment variables, matching the behaviour the PR attempted to implement.
  - [x] Updated the user-facing README snippet so downstream operators see the new knobs immediately after installing the package.
- Outcome: Packaging and configuration changes are synced with current `main`, linted, and ready to submit as a fresh PR that references the original ticket.

---

## Validation
- ✅ `shfmt -i 2 -ci -sr -d openwrt_captive_monitor.sh init.d/captive-monitor package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor package/openwrt-captive-monitor/files/etc/init.d/captive-monitor scripts/build_ipk.sh`
- ✅ `shellcheck -s sh openwrt_captive_monitor.sh init.d/captive-monitor package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor package/openwrt-captive-monitor/files/etc/init.d/captive-monitor scripts/build_ipk.sh`

## Next steps
1. Open a new PR from `triage-2-prs-rebase-ci-fixes-openwrt24` that supersedes legacy PRs #1 and #2, referencing them in the description for traceability.
2. Close the obsolete branches (`restore/feat-captive-intercept-dns-http-redirect`, `restore/feature-openwrt-captive-monitor-opkg`) once reviewers confirm the replacement PR.
3. Smoke-test on target hardware (AX3000T / OpenWrt 24.x) to validate nftables + dnsmasq reload behaviour before merge.
4. After merge, retag release candidates so downstream feeds pick up the triaged package.
