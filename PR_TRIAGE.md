# PR_TRIAGE — 2025-10-24

## Context
- Working branch: `triage/fix-last-failing-pr-openwrt-captive-monitor`
- Base commit: `88aaec5eeaf1a68d716c6746bedbfb7c3aeb5f2b` (`main` as of 2025-10-24)
- Tooling verified locally: `shfmt -i 4 -ci -sr -ln=posix` (per `.shfmt.conf`) and `shellcheck -s sh`
- Prior triage for PRs #1 and #2 (see sections below) landed via PR #21 (`triage-2-prs-rebase-ci-fixes-openwrt24`).

## Summary
Both legacy PRs were based on a pre-audit tree that no longer matches `main` (missing packaging layout, init wrappers, lint config, etc.). They also failed to run on OpenWrt 24.x because of BusyBox-specific incompatibilities and incomplete procd wiring. The changes below re-implement their intent on top of the current trunk so the originals can be superseded, and the resulting branch landed on `main` as PR #21.

This pass additionally evaluates PR #14 from the release/CI backlog. Its head predates the audit tree, removes the modern tooling/docs that now exist on `main`, and duplicates workflow fixes already merged via PRs #20 and #21, so closure is recommended instead of a rebase.

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

## PR #14 — `ci(workflows): fix SDK .ipk CI, matrix feed artifact capture, and update docs`
- Original head: `release-v0.1.1-ipk-ci-fix-opkg-feed-ath79-ramips@cba442f` (+29 / −1 vs pre-audit `main`).
- Findings:
  - Branch predates the audit restructure and drops `.editorconfig`, `.github/` templates, procd packaging refactors, and lint config that now live on `main`.
  - Workflow/doc changes proposed here already exist on `main` via PR #20 (`ci/fix-main-openwrt-captive-monitor@a4b5365`) and PR #21 (`triage-2-prs-rebase-ci-fixes-openwrt24@88aaec5`).
  - Rebasing would reintroduce obsolete shell code (missing BusyBox 1.36 fixes, quoting, procd cleanup) and fail the current lint gate.
- Decision / Outcome:
  - Close PR #14 as superseded; no changes need to be ported.
  - Leave the modern workflow/docs on `main`, which already publish per-target `Packages_<target>` indexes and `.ipk` artifacts.

---

## Validation
- ✅ `shfmt -i 4 -ci -sr -ln=posix -d openwrt_captive_monitor.sh init.d/captive-monitor package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor package/openwrt-captive-monitor/files/etc/init.d/captive-monitor scripts/build_ipk.sh`
- ✅ `shellcheck -s sh openwrt_captive_monitor.sh init.d/captive-monitor package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor package/openwrt-captive-monitor/files/etc/init.d/captive-monitor scripts/build_ipk.sh` (only SC3040 warnings remain on the guarded `set -o pipefail` check)

## Next steps
1. Post a closure comment on PR #14 summarising that its workflow/doc fixes already live on `main` (PRs #20/#21) and link back to this triage. Close the PR and delete `release-v0.1.1-ipk-ci-fix-opkg-feed-ath79-ramips`.
2. Keep consolidating the remaining CI backlog (#6, #8, #9, #11, #12, #13, #15) into rebased, reviewable chunks that pass the current `Lint` + OpenWrt build workflows.
3. Share the new workflow guidance (README + RELEASE_CHECKLIST) with release owners so they rely on the updated artifact structure going forward.
