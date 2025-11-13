# Branches & Merge Policy

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


_Last updated: 2025-10-24 on branch `protect-trunk-clean-branches-enforce-ci-pr-rules`._

This document captures the authoritative trunk strategy, CI entry points, and branch protection expectations for **openwrt-captive-monitor**. It replaces the merge-order notes that were tied to the now-completed recovery pull requests and is intended to stay evergreen alongside `CONTRIBUTING.md`.

---

## 1. Trunk & CI status

| Item | Status |
| --- | --- |
| Default branch | `main` (confirmed via `origin/HEAD`) |
| Default branch rename required? | No. See Appendix A if `master` ever reappears. |
| CI workflows covering trunk | ✅ `Lint` (`.github/workflows/shellcheck.yml`) and ✅ `Build OpenWrt packages` (`.github/workflows/openwrt-build.yml`) |
| Trigger coverage | Workflows run on pushes to `main`, `feature/*`, `fix/*`, `chore/*`, `docs/*`, `hotfix/*` and on pull requests targeting `main`. |
| Actions versions | `actions/checkout@v4.1.7`, `actions/upload-artifact@v4.3.3`, `softprops/action-gh-release@v2.4.1` (pinned). |

### 1.1 Workflow summary

| Workflow | Purpose | Key jobs | When it runs |
| --- | --- | --- | --- |
| `Lint` | Shell formatting (`shfmt`) and static analysis (`shellcheck`). | `Shell lint` | `push` to allowed branch prefixes, `pull_request` to `main`. |
| `Build OpenWrt packages` | Builds `.ipk` artifacts for ath79/ramips and publishes releases on tags. | `Build (ath79-generic)`, `Build (ramips-mt7621)`, `release` (tag only). | Same push filters as above, all PRs into `main`, tags `v*`. |

Both workflows currently finish successfully on `main`. Administrators should mark the build jobs listed above as **required status checks** when enabling branch protection (section 3).

---

## 2. Required status checks (GitHub branch protection)

When adding required status checks, select the job names exactly as GitHub reports them:

- `Lint / Shell lint`
- `Build OpenWrt packages / Build (ath79-generic)`
- `Build OpenWrt packages / Build (ramips-mt7621)`

> The `release` job only runs on tag pushes; it should remain optional so hotfix tagging is not blocked.

---

## 3. Branch protection template (admin checklist)

Follow these steps in **Settings → Branches → Add rule**. Repository admin rights are required.

1. **Branch name pattern:** `main`.
2. Enable the following options:
   - Require a pull request before merging.
   - Require approvals: minimum **1** review.
   - Dismiss stale pull request approvals when new commits are pushed.
   - Require status checks to pass before merging (add the three checks from section 2).
   - Require branches to be up to date before merging (ensures PRs are rebased on the current trunk before landing).
   - Require linear history.
   - Restrict who can push to matching branches (limit to maintainers) and disallow force pushes.
3. Save the rule.
4. In **Settings → General → Pull Requests**, configure:
   - Allow squash merging (set as default strategy).
   - Disable merge commits and rebase-merge options (leave only squash enabled).
   - Automatically delete head branches after pull requests are merged.

Document any deliberate exceptions (for example, emergency hotfixes) in `CONTRIBUTING.md`.

---

## 4. Merge & PR workflow summary

Contributors should follow these guardrails (mirrors the PR template):

1. Branch from `main` using the prefixes `feature/`, `fix/`, `chore/`, `docs/`, or `hotfix/`.
2. Rebase onto the latest `origin/main` before opening or updating a PR.
3. Fill in `.github/PULL_REQUEST_TEMPLATE.md`, including:
   - A concise summary of the change.
   - Test evidence (`shfmt`, `shellcheck`, `./scripts/build_ipk.sh`, and any hardware validation when applicable).
   - Confirmation that the `Lint` and `Build OpenWrt packages` workflows are green (or marked not applicable when packaging files are untouched).
4. Obtain at least one approval from the CODEOWNERS list.
5. Use squash merge once checks pass and ensure the final commit message follows Conventional Commit formatting (`feat(...)`, `fix(...)`, etc.).

---

## 5. Branch hygiene report (as of 2025-10-24)

### 5.1 Deleted branches

No local or remote branches were deleted as part of this pass: the workspace has only `main` and the current feature branch, and remote deletions require maintainer privileges.

### 5.2 Stale branches (> 60 days without activity)

None detected. All remote branches show activity within the last 60 days (see inventory below). Re-run the inventory script periodically to identify stale branches once development slows down:

```bash
git for-each-ref --format='%(committerdate:iso8601) %(refname:short)' \
  refs/remotes/origin | grep -v 'origin/HEAD'
```

### 5.3 Inventory & recommendations

| Remote branch | Last commit (UTC) | Recommendation |
| --- | --- | --- |
| `origin/main` | 2025-10-25 00:47 | ✅ Trunk - keep protected. |
| `origin/chore-trunk-merge-order-finish-2-prs-cleanup` | 2025-10-24 22:34 | Docs from previous cleanup; archive content into `main` (done) and then delete remotely. |
| `origin/audit-merge-ci-release-v0-1-1` | 2025-10-23 18:54 | Historical audit branch; confirm notes are captured in docs, then delete. |
| `origin/audit-pr-branching-openwrt-captive-monitor` | 2025-10-24 17:36 | Superseded by this policy; safe to delete after verification. |
| `origin/feat-ci-shellcheck-ipk-sdk-matrix` | 2025-10-22 22:22 | Feature branch integrated into `main`; remove once artifacts are archived. |
| `origin/restore/feat-captive-intercept-dns-http-redirect` | 2025-10-22 15:21 | Historical recovery branch; verify the merged commits exist on `main`, then delete. |
| `origin/restore/feature-openwrt-captive-monitor-opkg` | 2025-10-22 19:04 | Same as above; safe to delete after confirming the diff is on trunk. |
| `origin/release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish` | 2025-10-23 21:40 | Release helper branch; convert to tag notes and delete. |
| `origin/triage-3-failing-prs-check-main-close-or-fix-ci-add-pr-triage-md` | 2025-10-24 21:26 | Triage branch now redundant; integrate any doc updates and delete. |
| `origin/audit/*`, `origin/triage/*`, `origin/restore/*` | 2025-10-22 to 2025-10-24 | Review ownership; if no outstanding PR, remove to keep the branch list lean. |

To delete a remote branch once confirmed safe:

```bash
git push origin --delete <branch>
```

### 5.4 Automatic cleanup guardrail

Ensure **Automatically delete head branches** remains enabled (see section 3) so future topic branches are removed after merge without manual intervention.

---

## Appendix A – Default branch rename playbook

If `master` resurfaces or another rename is required:

1. `git branch -m master main`
2. `git push origin main`
3. In GitHub settings, set `main` as the default branch and delete `master`: `git push origin --delete master`
4. Audit CI, deployment scripts, and documentation for hard-coded branch names.
5. Notify contributors and update tooling/README references.

---

## Appendix B – Workflow trigger matrix (quick reference)

| Workflow | Event | Branch filter |
| --- | --- | --- |
| `Lint` | `push` | `main`, `feature/*`, `fix/*`, `chore/*`, `docs/*`, `hotfix/*` |
| `Lint` | `pull_request` | base: `main` |
| `Build OpenWrt packages` | `push` | `main`, `feature/*`, `fix/*`, `chore/*`, `docs/*`, `hotfix/*`, tags `v*` |
| `Build OpenWrt packages` | `pull_request` | base: `main` |
| `Build OpenWrt packages` | `release` | Tags matching `v*` (publishes artifacts) |

Revisit this table whenever new long-lived branches or workflows are introduced.
