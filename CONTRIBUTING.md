# Contributing to openwrt-captive-monitor

Thanks for taking the time to contribute! This project keeps OpenWrt routers online by recovering from captive portals and flaky uplinks, so changes need to be safe, reviewable, and well documented.

The repository follows a **trunk-based** workflow centred on the `main` branch. Short-lived topic branches, small pull requests, and fast feedback from CI keep releases predictable.

---

## 1. Branching model

1. Start from the latest `main` and keep your branch up to date by rebasing before opening a pull request.
2. Use descriptive branch prefixes:
   - `feature/<short-description>` for new capabilities
   - `fix/<short-description>` for bug fixes or regressions
   - `chore/<short-description>` for tooling, CI, or maintenance work
   - `docs/<short-description>` for documentation-only updates
   - `hotfix/<short-description>` for urgent production fixes that must land ahead of the regular release cadence
   Refer to [`BRANCHES_AND_MERGE_POLICY.md`](./BRANCHES_AND_MERGE_POLICY.md) for the latest merge sequencing, branch protection checklist, and cleanup tasks.
3. Prefer incremental pull requests (aim for < ~300 lines of net change). Split large efforts into multiple PRs that can be reviewed independently.
4. Avoid long-lived release branches. If you need to ship a hotfix, branch from the appropriate tag, cherry-pick the fix, release, and merge the change back into `main` immediately afterwards.

### Why trunk-based over GitFlow?

Trunk-based development keeps the integration surface small, which is important for shell tooling that is hard to test exhaustively. GitFlow introduces long-running `develop` and release branches that often diverge and amplify merge conflicts. Unless you are maintaining multiple historical versions in parallel, GitFlow’s additional ceremony rarely pays off here. If the project eventually needs LTS maintenance, treat it as an exception: cut a release branch, backport critical changes, and retire the branch after support ends.

---

## 2. Local development workflow

1. Clone the repository and install the linting dependencies:
   ```bash
   git clone https://github.com/nagual2/openwrt-captive-monitor.git
   cd openwrt-captive-monitor
   sudo apt-get update && sudo apt-get install -y shellcheck shfmt
   ```
2. Create a topic branch following the naming rules above.
3. Make your changes and keep commits focused. Conventional Commit prefixes (`feat(wifi): …`, `fix(ci): …`, etc.) match the existing history and feed changelog automation.
4. Before pushing:
   ```bash
   shfmt -w openwrt_captive_monitor.sh init.d/captive-monitor \
         package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
         package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
         package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor \
         scripts/build_ipk.sh

   shellcheck openwrt_captive_monitor.sh init.d/captive-monitor \
              package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
              package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
              package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor \
              scripts/build_ipk.sh
   ```
5. Run any additional smoke tests that apply (e.g. running the script in `oneshot` mode, packaging via `scripts/build_ipk.sh`, or deploying to a test router).
6. Rebase on top of the latest `main` and resolve conflicts locally before opening the PR.

> Tip: use `git rebase --onto` if you need to drop unrelated commits that slipped into older branches. Keeping branches short-lived eliminates most painful rebases.

---

## 3. Pull request expectations

- Fill out the PR template. It captures the summary, testing evidence, and review checklist all in one place.
- Link the relevant issue or explain the motivation in the summary so that reviewers have context.
- Request at least one reviewer (see [`CODEOWNERS`](./.github/CODEOWNERS)) and wait for an approval before merging. Self-approval is reserved for docs-only or CI-only changes with no risk.
- Ensure the **Lint** workflow (shfmt + ShellCheck) passes. Additional workflows (packaging, release automation) may run depending on the files you touched.
- Squash-and-merge is the default. If a branch contains several independently useful commits, mention it explicitly in the PR so the reviewer can choose "Rebase and merge" instead.

---

## 4. Branch protection & automation

Repository administrators should keep the following settings enabled on `main`:

- ✅ Require pull request reviews before merging (minimum 1 approval).
- ✅ Require status checks to pass before merging and select:
  - `Lint` (shellcheck + shfmt)
  - `openwrt-build` (OpenWrt SDK packaging matrix)
  - Any additional packaging or release workflows relevant to the change
- ✅ Dismiss stale approvals when new commits are pushed.
- ✅ Restrict who can push directly to `main` (typically only maintainers). Everyone else should go through PRs.
- ✅ Automatically delete branches after a pull request is merged.

These checks keep the branch healthy and ensure contributors get feedback quickly.

---

## 5. Issue triage & support

- Use the issue templates to provide reproducible bug reports and well-scoped feature requests.
- Security problems should go through the private disclosure channel listed in `SECURITY.md` or the repository security policy page.
- Tag issues with `good first issue` when they have a clear scope and minimal risk so newcomers can help.

---

## 6. Releases

1. Update `CHANGELOG.md` and docs under `docs/` as needed.
2. Tag the release from `main` (e.g. `git tag -a v0.1.2 -m "v0.1.2"`).
3. Push the tag to trigger the packaging workflow.
4. Publish the generated `.ipk` artifacts and update release notes.

If a regression requires a hotfix, branch from the affected tag, apply the fix, build/test, release, and cherry-pick the change back into `main` immediately.

---

## 7. Getting help

- Discussions: open a GitHub Discussion or issue with the `question` label.
- Real-world testing: share reproducible steps and logs in the PR or issue so maintainers can validate on similar hardware.
- Documentation updates: if anything in this guide is unclear, submit a PR – meta-contributions are welcome!

Thanks again for helping keep captive portal recovery on OpenWrt routers robust and user friendly.
