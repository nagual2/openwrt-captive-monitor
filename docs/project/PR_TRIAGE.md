# PR_TRIAGE — 2025-10-24

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


## Context
- Working branch: `triage-3-failing-prs-check-main-close-or-fix-ci-add-pr-triage-md`
- Base commit on `main`: `88aaec5` ("Merge pull request #21 from nagual2/triage-2-prs-rebase-ci-fixes-openwrt24")
- Commands used:
  - `git fetch origin feat-ci-shellcheck-ipk-sdk-matrix release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish ci-openwrt-stabilize-ipk-noninteractive-term-artifacts`
  - `git diff origin/main..origin/<branch>`
  - `GIT_PAGER=cat git show <commit> --stat`
- Reference CI dashboards for confirmation that `main` is green:
  - Lint: <https://github.com/nagual2/openwrt-captive-monitor/actions?query=workflow%3ALint+branch%3Amain>
  - openwrt-build: <https://github.com/nagual2/openwrt-captive-monitor/actions?query=workflow%3Aopenwrt-build+branch%3Amain>

## Summary
Third triage pass focuses on the three remaining failing CI/release PRs (#6, #11, #12). All heads were created before the audit merge (PR #21), revert BusyBox/procd fixes, and duplicate tooling that already lives on `main`. None of the branches contain unique commits that still need to be rescued; each should be closed with a short explanation that points to the superseding work on trunk.

## PR #6 — `ci(openwrt): add GitHub Actions for ShellCheck and OpenWrt SDK .ipk builds`
- PR: <https://github.com/nagual2/openwrt-captive-monitor/pull/6>
- Head: `feat-ci-shellcheck-ipk-sdk-matrix@5a90e34`
- Compare: <https://github.com/nagual2/openwrt-captive-monitor/compare/main...feat-ci-shellcheck-ipk-sdk-matrix>
- Diff summary: `31 files changed, 176 insertions(+), 1489 deletions(-)` — the branch deletes `.editorconfig`, issue/PR templates, the audited package layout, and replaces the consolidated `Lint` job with an older ShellCheck-only workflow.
- Findings:
  - The branch is based on the pre-audit tree and removes BusyBox compatibility changes, procd shutdown fixes, and the modernised CI configuration.
  - `main` already provides ShellCheck + shfmt coverage and a working SDK build matrix via commit `a4b5365` (PR #20, "ci(main): repair and modernize all CI pipelines"), validated after the rebase merge in `88aaec5` (PR #21).
  - Rebasing would reintroduce the deleted files and fail today’s `Lint` / `openwrt-build` jobs because the workflows no longer match the repository structure.
- **Decision:** Close PR #6 as superseded. Leave a closure comment referencing commits `a4b5365` and `88aaec5` and link to this triage note so contributors know where the functionality moved.

## PR #11 — `ci(build): fix CI .ipk build, opkg feed, and release workflow for v0.1.1`
- PR: <https://github.com/nagual2/openwrt-captive-monitor/pull/11>
- Head: `release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish@dcecbaa`
- Compare: <https://github.com/nagual2/openwrt-captive-monitor/compare/main...release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish>
- Diff summary: `29 files changed, 198 insertions(+), 1076 deletions(-)` — rewinds the repo to the pre-audit layout and reverts the POSIX-safe packaging scripts.
- Findings:
  - The non-interactive SDK setup and deterministic `Packages` index logic already ship on `main` via PR #21 alongside the follow-up CI hardening in `a4b5365`.
  - The head drops `.github/workflows/Lint`, the refreshed docs, and the modern `scripts/build_ipk.sh`, so merging or rebasing would undo the audited release tooling and keep CI red.
  - There are no commits left to salvage once the audit merge is in place; continuing with this branch only delays green builds.
- **Decision:** Close PR #11 as obsolete. Reference commits `a4b5365` and `88aaec5` in the closure note and delete the head branch after maintainers confirm.

## PR #12 — `ci(openwrt): stabilize .ipk build by ensuring non-interactive SDK config and normalized artifacts`
- PR: <https://github.com/nagual2/openwrt-captive-monitor/pull/12>
- Head: `ci-openwrt-stabilize-ipk-noninteractive-term-artifacts@785f1dc`
- Compare: <https://github.com/nagual2/openwrt-captive-monitor/compare/main...ci-openwrt-stabilize-ipk-noninteractive-term-artifacts>
- Diff summary: `29 files changed, 198 insertions(+), 1069 deletions(-)` — same rollback of audited files plus an outdated workflow matrix.
- Findings:
  - Contains the same history as PR #11 (plus intermediate commits); every change already landed on `main` through `a4b5365` and `88aaec5`.
  - Rebasing would still conflict on every audited file and reintroduce lint failures (ShellCheck + shfmt) addressed in the current tree.
  - No unique fixes remain to port; any future CI improvements should begin from `main` instead of resurrecting this branch.
- **Decision:** Close PR #12 as superseded by the modern CI/release stack. Leave a closure comment summarising these findings and request branch deletion.

## Validation
- No new source changes were needed; triage was performed with `git diff`/`git show` only.
- Current `main` workflows to cite in closure comments:
  - Lint — <https://github.com/nagual2/openwrt-captive-monitor/actions?query=workflow%3ALint+branch%3Amain>
  - openwrt-build — <https://github.com/nagual2/openwrt-captive-monitor/actions?query=workflow%3Aopenwrt-build+branch%3Amain>

## Next steps
1. Post closure comments on PRs #6, #11, and #12 referencing this analysis and the superseding commits (`a4b5365`, `88aaec5`).
2. Delete the branches `feat-ci-shellcheck-ipk-sdk-matrix`, `release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish`, and `ci-openwrt-stabilize-ipk-noninteractive-term-artifacts` once maintainers confirm.
3. Keep future CI/release fixes on fresh branches rebased onto `main` to avoid resurrecting pre-audit history.

---

### Appendix — prior triage notes (PRs #1 and #2)

#### PR #1 — `feat(captive-intercept): implement robust captive portal detection and HTTP+DNS intercept for LAN clients`
- Original head: `restore/feat-captive-intercept-dns-http-redirect@68a99f2` (+2 / −1 vs old `main`).
- Problem statement:
  - Rebased state deleted the new repo structure (package layout, CI, docs) and broke linting.
  - Captive DNS lookup relied on `resolveip -s`, which BusyBox 1.36 (OpenWrt 24.x) does not implement, so portal detection failed before firewall rules activated.
  - Service cleanup depended on manual kills; procd never terminated the monitor, leaving nft/iptables rules behind.
- Fixes applied in the replacement branch (`triage-2-prs-rebase-ci-fixes-openwrt24` → PR #21):
  - Rebased functionality onto the packaging-first layout already on `main` (thin launchers + `/usr/sbin/openwrt_captive_monitor`).
  - Replaced BusyBox-incompatible `resolveip -s` calls with portable `nslookup` fallbacks, keeping IPv4/IPv6 detection intact.
  - Extended the procd init script to export LAN IPv6, DNS/captive lists, and firewall backend hints so the intercept logic receives the expected configuration.
  - Added deterministic shutdown (`procd_kill`) and reload triggers for `firewall`/`dnsmasq` to guarantee nft/iptables cleanup during service stops or firewall reloads.
- Outcome: logic now runs on OpenWrt 24.x with fw4/nftables, passes lint, and supersedes the legacy PR.

#### PR #2 — `fix(openwrt-captive-monitor): launcher and Makefile env fixes`
- Original head: `restore/feature-openwrt-captive-monitor-opkg@92d8bd7` (+5 / −1 vs old `main`).
- Problem statement:
  - Branch was missing the reconstructed package skeleton and CI metadata that landed after the audit.
  - UCI schema did not expose the LAN/firewall knobs required by the service, so defaults could not be overridden without editing the script by hand.
- Fixes applied in the replacement branch (`triage-2-prs-rebase-ci-fixes-openwrt24` → PR #21):
  - Preserved the audited packaging layout while wiring the missing `lan_interface`, `lan_ip`, `lan_ipv6`, and `firewall_backend` options into both `/etc/config/captive-monitor` and the `uci-defaults` seed.
  - Ensured these options propagate to the runtime via procd environment variables, matching the behaviour the PR attempted to implement.
  - Updated the user-facing README snippet so downstream operators see the new knobs immediately after installing the package.
- Outcome: packaging and configuration changes are synced with current `main`, linted, and ready for downstream consumption.
