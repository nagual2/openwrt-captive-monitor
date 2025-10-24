# Branch & Pull Request Audit — 2025-10-24

This document captures the state of branches and open pull requests in the `nagual2/openwrt-captive-monitor` repository and proposes the workflow changes requested in the ticket.

## Snapshot

- **Default branch:** `main` (`c2c6e39` – "docs(audit): update audit, backlog, and test plan for OpenWrt 24.x/filogic (#17)")
- **Tags:** `v0.1.0` currently points at `8e8a3f21` (pre-audit state). Later release tags reference branches listed below.
- **Observation:** All open PR heads are currently **1 commit behind `main` and conflict when merged** (tested locally with `git merge --no-commit`). A consistent rebase strategy is needed before any of them can land.
- **Recommended branching model:** Trunk-based (`main` + short-lived `feature/*`, `fix/*`, `chore/*`, `docs/*`). GitFlow is not advised unless long-term maintenance branches become unavoidable (see §“Branching strategy recommendation”).
- **CI coverage:** A consolidated `Lint` workflow (shfmt + ShellCheck) is now provided in `.github/workflows/shellcheck.yml`. Enable it as a required status check on `main` (see §“Branch protection & CI requirements”).

---

## Remote branch inventory

Priority legend: **P0** = unblock immediately, **P1** = address soon, **P2** = nice to clean up when convenient.

| Branch | Last commit (UTC) | Δ vs `main` (ahead/behind) | Linked PR | Notes | Recommended action | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| `origin/restore/feat-captive-intercept-dns-http-redirect` | `68a99f2` (2025-10-22) | +2 / −1 | #1 | Restores captive portal detection & LAN intercept logic; minimal divergence | Rebase onto `main`, rerun lint/tests, merge first to recover core functionality | P0 |
| `origin/restore/feature-openwrt-captive-monitor-opkg` | `92d8bd7` (2025-10-22) | +5 / −1 | #2 | Packaging fixes (`opkg` launcher, Makefile env) | Rebase after #1 lands, validate on router / SDK, merge | P0 |
| `origin/feat-ci-shellcheck-ipk-sdk-matrix` | `5a90e34` (2025-10-22) | +11 / −1 | #6 | Adds CI for ShellCheck + OpenWrt SDK builds | Fold into new `Lint` workflow & modernise matrix before merging; requires rebase | P1 |
| `origin/audit-merge-ci-release-v0-1-1` | `9a55b78` (2025-10-23) | +20 / −1 | #8 | Mass rebases for CI + release automation towards v0.1.1 | Re-evaluate after #1/#2; break into smaller PRs or cherry-pick critical fixes | P1 |
| `origin/release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish` | `dcecbaa` (2025-10-23) | +23 / −1 | #11 | Release packaging fixes | After CI stabilises, keep as tagged release or merge into `main` post-rebase | P1 |
| `origin/ci-openwrt-stabilize-ipk-noninteractive-term-artifacts` | `785f1dc` (2025-10-23) | +25 / −1 | #12 | Normalises `.ipk` build artifacts | Rebase/split (depends on #6/#11). Consider merging once CI jobs green | P1 |
| `origin/fix-openwrt-ipk-build-gha-noninteractive-sdk-arch-feed-artifacts` | `9661a7e` (2025-10-23) | +27 / −1 | #13 | Further CI fixes for SDK matrix | Needs rebase and deduplication with #12 | P1 |
| `origin/release-v0.1.1-ipk-ci-fix-opkg-feed-ath79-ramips` | `cba442f` (2025-10-24) | +29 / −1 | #14 | Adds multi-arch packaging improvements | Tag once validated, or merge after prior CI branches | P1 |
| `origin/restore-missing-changes-rebase-main` | `6dbf114` (2025-10-24) | +29 / −1 | #15 | Attempts to restore lost commits while rebasing onto `main` | Coordinate with maintainers: evaluate if superseded by #1/#2 + CI branches | P1 |
| `origin/audit-openwrt-captive-monitor-plan` | `850ff2a` (2025-10-24) | +30 / −1 | #16 | Documentation backlog/audit plan | Rebase onto latest docs (or supersede with #17 already merged into `main`) | P2 |
| `origin/audit/captive-monitor-openwrt24-filogic` | `c4cf5ba` (2025-10-24) | +31 / −1 | #17 | Follow-up audit docs | Determine if content belongs on `main`; if so, rebase and merge; else archive | P2 |
| `origin/feat-captive-intercept-dns-http-redirect` | `8e8a3f2` (2025-10-23) | +14 / −1 | (closed merge of #6) | Points at already merged commit (`v0.1.0`); stale duplicate | Delete after confirming tags/releases refer to `v0.1.0`; enable auto-delete-on-merge | P2 |
| `origin/feat/shellcheck-ci-openwrt-ash-fixes` | `8e8a3f2` (2025-10-23) | +14 / −1 | (duplicate of above) | Stale branch left after merging #6 | Delete post-confirmation | P2 |
| `origin/feature/captive-redirect-nft-ipv6-iptables-compat-idempotent` | `8e8a3f2` (2025-10-23) | +14 / −1 | (legacy) | Old feature branch already merged | Delete post-confirmation | P2 |
| `origin/feature/openwrt-captive-monitor-opkg` | `8e8a3f2` (2025-10-23) | +14 / −1 | (legacy) | Old packaging branch; functionality preserved via tags | Delete or archive | P2 |
| `origin/release-v0.1.0-pr-review-build-ipk-opkg-feed` | `8e8a3f2` (2025-10-23) | +14 / −1 | (legacy) | Release branch duplicating tag `v0.1.0` | Replace with annotated tag only; delete branch | P2 |
| `origin/restore-branches-reopen-prs-rebase-release-v0.1.0` | `053c661` (2025-10-23) | +20 / −1 | #10 | Reopens older release PR | Decide whether to keep for historical context or close in favour of new plan | P2 |

---

## Open pull request backlog

All PRs were fetched via `git fetch origin refs/pull/*/head`. Attempting to merge each head into `origin/main` results in conflicts; every PR needs a rebase.

| PR | Title (last commit) | Head branch | Δ vs `main` (ahead/behind) | Commits | Mergeability | Recommended action | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1 | `feat(captive-intercept): implement robust captive portal detection and HTTP+DNS intercept for LAN clients` (`68a99f2`, 2025-10-22) | `restore/feat-captive-intercept-dns-http-redirect` | +2 / −1 | 2 | Conflicts | Rebase on `main`, rerun lint + router smoke test, merge first to restore baseline functionality | P0 |
| #2 | `fix(openwrt-captive-monitor): launcher and Makefile env fixes` (`92d8bd7`, 2025-10-22) | `restore/feature-openwrt-captive-monitor-opkg` | +5 / −1 | 5 | Conflicts | Rebase after #1, validate packaging, merge | P0 |
| #3 | `ci(shellcheck): add ShellCheck CI, warnings fixed, safe POSIX, badge` (`a44202d`, 2025-10-22) | Fork branch (no origin ref) | +7 / −1 | 7 | Conflicts | Coordinate with author; much of this is superseded by new `Lint` workflow—extract remaining fixes into new PR | P1 |
| #4 | `feat(captive): add nftables + IPv6 support with idempotence and dual-stack` (`97bfac3`, 2025-10-22) | Fork branch | +9 / −1 | 9 | Conflicts | Large feature delta—needs rebase and incremental review after #1/#2 land | P1 |
| #5 | `feat(release): automate .ipk packaging, opkg feed, and release docs` (`f9a5d4a`, 2025-10-22) | Fork branch | +11 / −1 | 11 | Conflicts | Split into smaller PRs (automation vs docs). Rebase + ensure alignment with modern CI | P1 |
| #6 | `ci(openwrt): add GitHub Actions for ShellCheck and OpenWrt SDK builds` (`5a90e34`, 2025-10-22) | `feat-ci-shellcheck-ipk-sdk-matrix` | +11 / −1 | 11 | Conflicts | Superseded by updated `Lint` workflow. Cherry-pick remaining useful steps; close original PR afterwards | P1 |
| #7 | `ci: drop python3-distutils on ubuntu-24.04 runner` (`2a2abe8`, 2025-10-23) | Fork branch | +15 / −1 | 15 | Conflicts | Fold into CI consolidation (#8/#12/#13) post-rebase | P1 |
| #8 | `ci(openwrt-build): sync/rebase all CI and packaging, bump v0.1.1, fix Ubuntu-24.04 compatibility` (`9a55b78`, 2025-10-23) | `audit-merge-ci-release-v0-1-1` | +20 / −1 | 20 | Conflicts | Break apart into focused PRs after trunk is healthy; close superseded pieces | P1 |
| #9 | `ci(workflow): fix OpenWrt .ipk build by setting config target and defconfig` (`4cc560d`, 2025-10-23) | Fork branch | +20 / −1 | 20 | Conflicts | Duplicate of #8/#12; re-evaluate after consolidation | P1 |
| #10 | `docs(release): add CHANGELOG and release notes link for v0.1.0` (`053c661`, 2025-10-23) | `restore-branches-reopen-prs-rebase-release-v0.1.0` | +20 / −1 | 20 | Conflicts | Migrate relevant docs into current audit (#17). Close once merged or superseded | P2 |
| #11 | `ci(build): fix CI .ipk build, opkg feed, and release workflow for v0.1.1` (`dcecbaa`, 2025-10-23) | `release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish` | +23 / −1 | 23 | Conflicts | Requires rebase after CI consolidation (#6/#12/#13). Keep as release PR until then | P1 |
| #12 | `ci(openwrt): stabilize .ipk build by ensuring non-interactive SDK config and normalized artifacts` (`785f1dc`, 2025-10-23) | `ci-openwrt-stabilize-ipk-noninteractive-term-artifacts` | +25 / −1 | 25 | Conflicts | Rebase, possibly merge with #13; ensure smaller review units | P1 |
| #13 | `ci(openwrt-build): fix .ipk build matrix in GitHub Actions, non-interactive SDK config, arch feed, and artifacts` (`9661a7e`, 2025-10-23) | `fix-openwrt-ipk-build-gha-noninteractive-sdk-arch-feed-artifacts` | +27 / −1 | 27 | Conflicts | Overlaps with #12; extract reusable pieces, close duplicates | P1 |
| #14 | `ci(workflows): fix SDK .ipk CI, matrix feed artifact capture, and update docs` (`cba442f`, 2025-10-24) | `release-v0.1.1-ipk-ci-fix-opkg-feed-ath79-ramips` | +29 / −1 | 29 | Conflicts | Superseded by `main` merges (#20 @a4b5365, #21 @88aaec5); workflows/docs already landed. Close PR and prune branch. | P1 |
| #15 | `ci(workflows): restore reliable OpenWrt package CI and doc clarity` (`6dbf114`, 2025-10-24) | `restore-missing-changes-rebase-main` | +29 / −1 | 29 | Conflicts | Evaluate overlap with #11/#14; may be obsolete once earlier branches merge | P1 |
| #16 | `docs(audit): add audit summary, backlog, and test plan for openwrt-captive-monitor` (`850ff2a`, 2025-10-24) | `audit-openwrt-captive-monitor-plan` | +30 / −1 | 30 | Conflicts | Replace with #17 (already on `main`), or squash into markdown living docs | P2 |
| #17 | `docs(audit): update audit, backlog, and test plan for OpenWrt 24.x/filogic` (`c4cf5ba`, 2025-10-24) | `audit/captive-monitor-openwrt24-filogic` | +31 / −1 | 31 | Conflicts | Determine whether additional audit info belongs in repo or wiki; rebase vs. close | P2 |

---

## Cleanup checklist

Use this as a working log while tidying the backlog. Adjust priorities if new information surfaces.

### Immediate (P0)
- [ ] Rebase PR #1 (`restore/feat-captive-intercept-dns-http-redirect`) onto `main`, resolve conflicts, run `Lint`, and smoke-test on a captive portal.
- [ ] Rebase PR #2 (`restore/feature-openwrt-captive-monitor-opkg`) after #1 merges; verify packaging on OpenWrt 22.03/23.05.

### High priority (P1)
- [ ] Consolidate CI fixes (#6, #7, #8, #9, #11, #12, #13, #15) into a sequenced set of smaller PRs that each pass `Lint` and the SDK build workflow (PR #14 closed as superseded).
- [ ] Work with contributors whose branches live on forks (PRs #3, #4, #5, #7, #9) to rebase and reopen with the new branching conventions.
- [ ] After CI hardening, decide which release branches (#11) should remain as long-lived support vs. being replaced with annotated tags (PR #14 closed as superseded).

### When convenient (P2)
- [ ] Delete stale branches that already landed (`feat-captive-intercept-dns-http-redirect`, `feat/shellcheck-ci-openwrt-ash-fixes`, `feature/*`, `release-v0.1.0-pr-review-build-ipk-opkg-feed`) once tags exist.
- [ ] Migrate audit documentation from PRs #16 & #17 into the repository wiki or docs tree, then close the PRs.
- [ ] Enable “Automatically delete head branches” in repository settings.

---

## Branching strategy recommendation

- **Adopt trunk-based development**: everyone branches off `main`, keeps branches short-lived, and rebases before merge. This minimises merge conflicts (a current pain point) and keeps the production branch deployable at all times.
- **GitFlow comparison**: GitFlow introduces `develop`, release, and hotfix branches. For this repository, those long-lived branches were the source of divergence—the existing backlog mirrors multiple release branches that all conflict today. Unless you are shipping simultaneous maintenance releases, GitFlow adds more ceremony than value. If LTS support becomes necessary, treat it as an exception: create a short-lived release branch from the tag, apply the fix, publish, and merge back to `main` immediately.
- **Naming conventions**: enforce `feature/*`, `fix/*`, `chore/*`, and `docs/*` (mirrored in the PR template and CONTRIBUTING guide). CI-specific work can use `chore/ci-*` so it is obvious what is inside.

---

## Default branch rename plan (if ever needed)

The default branch is already `main`, so no immediate action is required. If another environment still uses `master`, follow this plan:

1. Rename the local branch: `git branch -m master main`.
2. Push the new branch and update the upstream: `git push origin main` and `git push origin --delete master` (only after confirming all automation points at `main`).
3. Update protected branch rules, GitHub Pages settings, and CI workflows to point to `main`.
4. Communicate the change to contributors and update documentation (`README`, `CONTRIBUTING`, release scripts, etc.).
5. Add a fallback script for forks that still fetch `master` (e.g. `git remote set-head origin -a`).

---

## Branch protection & CI requirements

Repository administrators should enforce the following on `main`:

1. **Enable branch protection** with:
   - Require pull-request reviews (≥1 approval) and dismiss stale reviews on new pushes.
   - Restrict force pushes and direct pushes to maintainers only.
   - Require linear history (squash or rebase merges).
2. **Require status checks**:
   - `Lint` (new shfmt + ShellCheck workflow in `.github/workflows/shellcheck.yml`).
   - OpenWrt packaging workflows when relevant (`openwrt-build.yml`, once green again).
3. **Automatically delete head branches** after merge (toggle in Settings → General → Pull Requests).
4. **Set merge strategy** to squash-by-default. Allow rebase merges for multi-commit PRs only if reviewers agree.

Once these protections are active, document the policy in `CONTRIBUTING.md` (already updated) so contributors know what to expect.

---

## Next steps for maintainers

- Share this audit with active contributors and agree on ownership for the P0/P1 tasks.
- Close superseded PRs once their changes are merged in smaller, rebased form.
- Keep `BRANCHES_PR_AUDIT.md` up to date after the backlog is addressed or move the analytics into an issue pinned in the repository.
