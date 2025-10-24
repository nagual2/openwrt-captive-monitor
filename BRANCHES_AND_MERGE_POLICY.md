# Branches & Merge Policy

_Last updated: 2025-10-24 by the `chore-trunk-merge-order-finish-2-prs-cleanup` maintenance pass._

This document captures the current trunk strategy, the agreed merge order for the two highest-priority pull requests, and the hygiene rules that keep the history linear and reviewable. It is the operational companion to `CONTRIBUTING.md` and replaces ad-hoc notes that previously lived across issues and comments.

---

## 1. Trunk status

| Item | Status |
| --- | --- |
| Default branch | `main` (`444b128a` at time of writing) |
| CI workflows pointing at trunk | ✅ `.github/workflows/shellcheck.yml` and `.github/workflows/openwrt-build.yml` trigger on `push`/`pull_request` for `main` |
| Default branch rename required? | No – repository already uses `main`. See Appendix A for the fallback checklist if `master` ever reappears. |

### Actions for repository admins

Although the local repository is configured correctly, a few tasks require GitHub admin access:

1. Confirm `main` is set as the **default branch** under _Settings → Branches_.
2. If any legacy automation still points at `master`, follow the rename checklist in Appendix A.
3. Ensure both workflows above are marked as **required status checks** once branch protection (section 4) is in place.

---

## 2. Merge plan for the two priority PRs

Two pull requests are blocking trunk health. They must merge in order, because the packaging fixes in PR #2 depend on the captive portal recovery restored by PR #1.

| Merge order | PR | Head branch | Purpose | Required actions before merge |
| --- | --- | --- | --- | --- |
| 1 | #1 `feat(captive-intercept): implement robust captive portal detection and HTTP+DNS intercept for LAN clients` | `restore/feat-captive-intercept-dns-http-redirect` | Restores captive portal detection and LAN DNS/HTTP intercept logic lost during earlier rebases. | Rebase onto latest `main`, resolve shell conflicts, rerun `Lint`, smoke-test captive portal recovery. |
| 2 | #2 `fix(openwrt-captive-monitor): launcher and Makefile env fixes` | `restore/feature-openwrt-captive-monitor-opkg` | Fixes launcher script and Makefile environment issues so packages install cleanly via `opkg`. | Rebase on top of post-merge `main`, validate IPK build on OpenWrt 22.03/23.05, rerun `Lint`. |

### Step-by-step playbook

#### PR #1 – Captive intercept restoration

1. Update and rebase:
   ```bash
   git fetch origin
   git checkout restore/feat-captive-intercept-dns-http-redirect
   git rebase origin/main
   ```
2. Resolve conflicts (expect `openwrt_captive_monitor.sh`, `init.d/captive-monitor`, and package scripts). Keep the logic from PR #1 while preserving logging tweaks already on `main`.
3. Re-run formatting and linting locally:
   ```bash
   shfmt -w openwrt_captive_monitor.sh init.d/captive-monitor \
         package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
         package/openwrt-captive-monitor/files/etc/init.d/captive-monitor
   shellcheck openwrt_captive_monitor.sh init.d/captive-monitor \
              package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor
   ```
4. Smoke test on a router or QEMU instance behind a captive portal. Verify:
   - `oneshot` mode detects the portal and launches the intercept.
   - HTTP requests are redirected to the captive login page.
   - Normal connectivity resumes (DNS restored) after authentication.
5. Push the rebased branch (`git push --force-with-lease`) and wait for GitHub Actions to mark the **Lint** workflow green.
6. Request at least one reviewer approval, then **squash-merge**.

#### PR #2 – Packaging fixes

_Blocks on: PR #1 merged to `main`._

1. Once #1 is on `main`, rebase:
   ```bash
   git fetch origin
   git checkout restore/feature-openwrt-captive-monitor-opkg
   git rebase origin/main
   ```
2. Resolve overlaps in `Makefile`, launcher scripts, and packaging metadata. Ensure the environment variables introduced in #2 remain compatible with the code restored by #1.
3. Repeat linting:
   ```bash
   shfmt -w scripts/build_ipk.sh package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor
   shellcheck scripts/build_ipk.sh package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor
   ```
4. Validate the package locally:
   ```bash
   ./scripts/build_ipk.sh
   scp bin/packages/*/base/openwrt-captive-monitor_*.ipk root@<router>:/tmp/
   ssh root@<router> \
     'opkg install /tmp/openwrt-captive-monitor_*.ipk && /etc/init.d/captive-monitor restart'
   ```
   Test both OpenWrt 22.03 and 23.05 if possible.
5. Push with `--force-with-lease`, confirm both **Lint** and **openwrt-build** workflows are green, gather reviewer approval, then squash-merge.

### Evidence of work still pending

The local clone does not include the head branches for PRs #1 and #2, and this environment lacks push/merge permissions. The instructions above are therefore recorded as an execution plan for repository maintainers. Update this document once both PRs are merged (include commit hashes and test evidence).

---

## 3. Branch hygiene

Follow this cleanup immediately after the two PRs land:

1. **Delete merged branches** (locally and on origin):
   - `restore/feat-captive-intercept-dns-http-redirect`
   - `restore/feature-openwrt-captive-monitor-opkg`
2. **Enable automatic branch deletion on merge** (Settings → General → Pull Requests).
3. **Review stale branches (>60 days without activity):**

| Branch | Last commit | Linked PR | Action |
| --- | --- | --- | --- |
| `feat-captive-intercept-dns-http-redirect` | 2025-10-23 | (legacy) | Already merged into `v0.1.0`. Delete. |
| `feat/shellcheck-ci-openwrt-ash-fixes` | 2025-10-23 | (legacy) | Superseded by `Lint` workflow. Delete. |
| `feature/openwrt-captive-monitor-opkg` | 2025-10-23 | (legacy) | Historical duplicate; delete after tagging. |
| `release-v0.1.0-pr-review-build-ipk-opkg-feed` | 2025-10-23 | (legacy) | Preserve only the tag. Delete branch. |
| `restore-branches-reopen-prs-rebase-release-v0.1.0` | 2025-10-23 | PR #10 | Close PR in favour of newer docs, then delete. |
| Remaining `audit/*` branches | 2025-10-24 | PRs #16/#17 | Merge relevant docs into `docs/` or the wiki, close PRs, delete branches. |

Record branch deletions in the team change log or release notes if other integrators still track them.

---

## 4. Branch protection & CI rules

Request a repository admin to configure the following rules for `main` (Settings → Branches → Add rule):

1. **Restrictions**
   - ✅ Require a pull request before merging.
   - ✅ Require approvals: minimum 1.
   - ✅ Dismiss stale pull request approvals when new commits are pushed.
   - ✅ Restrict who can push (maintainers only) and disallow force pushes.
   - ✅ Require linear history; set **squash merge** as the default (disable merge commits).
2. **Status checks**
   - `Lint` (shellcheck + shfmt).
   - `openwrt-build` (fails fast if the IPK packaging pipeline regresses).
3. **Branch management**
   - Enable **Automatically delete head branches** once the PR is merged.

Document any exceptions (e.g., emergency hotfixes) in `CONTRIBUTING.md` so contributors know the escalation path.

---

## 5. Branch naming & workflow expectations

- Branch from `main` and keep topic branches short-lived.
- Allowed prefixes: `feature/…`, `fix/…`, `chore/…`, `docs/…`, `hotfix/…` (for urgent production repairs only).
- Rebase interactively (`git rebase -i origin/main`) before opening or updating a pull request; avoid merge commits.
- Use [Conventional Commit](https://www.conventionalcommits.org/) style titles so release automation can parse changelog categories.
- Update the PR checklist (see `.github/PULL_REQUEST_TEMPLATE.md`) to confirm `Lint` and `openwrt-build` have passed where applicable.

---

## 6. Outstanding actions requiring elevated permissions

| Task | Owner | Notes |
| --- | --- | --- |
| Merge PR #1 then PR #2 per the playbook | Maintainer with write access | Requires fetching contributor branches or creating replacements from maintainer forks. |
| Delete merged/stale branches | Maintainer | Use Settings → Branches or `git push origin --delete <branch>` |
| Enable branch protection and required status checks | Repository admin | See section 4. |
| Enable automatic branch deletion | Repository admin | Settings → General → Pull Requests. |

Update this section (or remove it) once each item is completed.

---

## Appendix A – Default branch rename checklist (reference)

If `master` reappears or the default branch needs to change, follow these steps:

1. `git branch -m master main`
2. `git push origin main`
3. Update default branch in GitHub settings, then delete `master` (`git push origin --delete master`).
4. Audit CI workflows, badges, and deployment scripts for hardcoded branch names.
5. Notify contributors; update documentation and scripts accordingly.

---

## Appendix B – CI workflow triggers

- `.github/workflows/shellcheck.yml` monitors `push` and `pull_request` events for `main` and `feature/*` branches.
- `.github/workflows/openwrt-build.yml` monitors the same events and also publishes release artifacts when tags matching `v*` are pushed.

No further changes are required unless the repository introduces additional long-lived branches.
