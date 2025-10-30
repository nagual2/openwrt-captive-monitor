# Last Green CI Audit

**Last successful run:**
- **Workflow:** CI (Consolidated)
- **Run ID:** PENDING — [view run](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml)
- **Commit:** CURRENT — CI consolidation and release automation upgrade (2025-01-30)
- **Audit range:** `Previous commit..current consolidation`

## New CI Pipeline Structure

### Primary Workflows

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - **Lint Jobs**: Parallel matrix execution of shfmt, shellcheck
   - **Test Job**: BusyBox ash test harness execution
   - **Triggers**: Push to all branches, PR to main, manual dispatch
   - **Artifacts**: Test results uploaded with 7-day retention

2. **Build Workflow** (`.github/workflows/openwrt-build.yml`)
   - **Matrix Builds**: generic, x86-64, armvirt-64, mips_24kc targets
   - **Dependencies**: Requires CI workflow completion
   - **Concurrency**: Enabled with automatic cancellation
   - **Release Job**: Dedicated job for tag-triggered releases

3. **Release Workflow** (`.github/workflows/release-please.yml`)
   - **Automated**: Semantic versioning and changelog generation
   - **Version Management**: Automatic package Makefile updates
   - **Integration**: Works with GitHub releases and tags

### Required Status Checks

For branch protection, enable these required checks:
- `lint (shfmt)`
- `lint (shellcheck)` 
- `test`
- `build (generic)` (or specific target as needed)

### Maintenance Automation

- **Dependabot**: Weekly updates for GitHub Actions dependencies
- **Auto-merge**: Configure for Dependabot PRs after CI passes
- **Release Process**: Fully automated through conventional commits

## Previous Audit History

## Changes Since Last Green Run (chronological)

1. **6e9e72e — fix(dns): replace resolveip usage with nslookup/host-based DNS resolution and timeout** — Shell scripts; swapped resolveip calls for nslookup/host wrappers with timeouts to improve IPv4/IPv6 captive portal detection stability.
2. **444b128 — Merge pull request #24 from nagual2/continue-previous-task** — Merge; no additional changes beyond integrating 6e9e72e.
3. **ce3776d — chore(repo): establish trunk, merge policy, and branch hygiene for maintainability (#26)** — Documentation (.github/PULL_REQUEST_TEMPLATE.md, BRANCHES_AND_MERGE_POLICY.md, CONTRIBUTING.md); formalized contribution and review policies.
4. **07fa174 — feat(health-check): add HTTP/HTTPS probes and exponential backoff to connectivity checks (#25)** — Shell script & docs; added HTTP/HTTPS captive portal probes with exponential backoff logic.
5. **fe78ae9 — chore(repo): enforce trunk protection, improve CI hygiene, and document merge rules (#27)** — CI workflows & docs; tightened workflow requirements and updated merge guidelines.
6. **185dbf7 — docs(setup): add branch protection setup instructions** — Documentation; created BRANCH_PROTECTION_SETUP.md.
7. **d9ae7a4 — docs(build): add Windows build instructions** — Documentation; introduced BUILD_WINDOWS.md guide.
8. **7dacbd5 — feat(testing): add comprehensive testing suite for remote servers** — Tests & docs; added remote testing scripts (test_captive_monitor.sh, test_captive_scenarios.sh) plus TESTING_REMOTE.md.
9. **86e3645 — fix(shellcheck): fix ash compatibility and workflow file patterns** — CI workflow, init scripts, uci-defaults, build/test scripts; adjusted shellcheck targeting and ensured BusyBox ash compatibility.
10. **16d459a — fix(shellcheck): improve workflow file detection and POSIX compatibility** — CI workflow and main script; refined file discovery and POSIX adjustments.
11. **0f7a7bb — fix(shellcheck): add comprehensive ash compatibility annotations** — Shell script; expanded shellcheck annotations for ash.
12. **0616788 — fix(shellcheck): comprehensive ash compatibility fixes** — CI workflow, init/uci scripts, service script, build script, tests; broad ash compatibility updates.
13. **008cba3 — fix(shellcheck): add comprehensive disable annotations and simplify workflow** — CI workflow, shell/init/build/test scripts; streamlined shellcheck configuration with scoped disables.
14. **df81fc4 — fix(shellcheck): clean up excessive disable annotations** — Shell/init/build/test scripts; reduced redundant shellcheck suppressions while keeping ash compliance.
15. **7f10c76 — docs: add comprehensive project commit report** — Documentation; introduced PROJECT_COMMIT_REPORT.md.
16. **b473c54 — chore(release): bump version to v0.1.2** — CHANGELOG & package Makefile; version bump artifacts.
17. **95b39d3 — fix(ci): resolve shell compatibility issues in GitHub Actions** — CI workflows, build script, tests; adjusted job steps for ash-compatible execution.
18. **9c3b7d5 — fix(ci): resolve YAML syntax errors and simplify workflow scripts** — CI workflows; cleaned workflow structure and syntax.
19. **92e2802 — refactor(tests): deep refactor and cleanup of test suite** — CI workflow, tests, and docs; replaced remote test harness with slimmed-down checks, removed large documentation set.
20. **96c5fbe — fix(ci): resolve OpenWrt SDK version and dependency issues** — CI workflow & CHANGELOG; corrected SDK version handling.
21. **5c66326 — fix(build): improve OpenWrt SDK package compilation process** — CI workflow; refined SDK build steps.
22. **faf23e2 — fix(shell): resolve POSIX shell compatibility issues** — Main script and tests; removed non-POSIX constructs.
23. **1ab308f — fix(openwrt): convert tests to pure OpenWrt validation** — CI workflow, configs, service script, tests; aligned tests with OpenWrt environment and updated lint configurations.
24. **5b8c756 — fix(sdk): improve OpenWrt SDK package build process** — CI workflow and package Makefile; build pipeline improvements.
25. **53372c1 — fix(sdk): use OpenWrt feeds system for package building** — CI workflow; switched package builds to use feeds.
26. **1ab45c3 — fix(shell): fix POSIX shell compatibility in test scripts** — Service/init/build/test scripts; additional ash compatibility fixes.
27. **3feb8b8 — fix(shellcheck): fix sh -n syntax validation commands** — CI workflow, config, tests; corrected validation invocation.
28. **04cb8d8 — fix(shfmt): remove -filename option from shfmt config** — CI workflow & shfmt config; adjusted formatter invocation.
29. **a4cf30d — feat(minimal): remove complex testing, keep only essential linting** — CI workflow, shellcheck config, shfmt config, tests; pared test suite down to lint-style checks.
30. **e6fd6e0 — fix(ci): correct OpenWrt build workflow to ensure package build dir context** — CI workflow; fixed working directory usage for package builds.
31. **fe7031f — Merge pull request #28 from nagual2/fix-gh-actions-tests-openwrt** — Merge; no additional files beyond PR content.
32. **c2916d0 — ci(shfmt): reformat shell scripts to comply with shfmt rules** — Shell script; formatting-only changes (shfmt) to openwrt_captive_monitor.
33. **581bf18 — Merge pull request #29 from nagual2/ci-shfmt-fix-openwrt-captive-monitor** — Merge; no further file modifications.
34. **4fccdcc — test(openwrt-ash): add minimal POSIX BusyBox ash test harness and mocks** — CI workflows, README, .gitignore, main script, tests/mocks, tests/run.sh; introduced ash-based mock framework and runner.
35. **a8cec07 — Merge pull request #30 from nagual2/tests-openwrt-ash-minimal-harness** — Merge; no additional files beyond PR content.

## Likely Breakpoints

- **6e9e72e — DNS resolution overhaul** modifying core connectivity logic in `openwrt_captive_monitor`.
- **7dacbd5 — Remote testing suite introduction** that greatly expanded test scripts and documentation.
- **95b39d3 — CI shell compatibility fixes** touching workflows, build scripts, and tests.
- **92e2802 — Major test-suite rewrite** that removed extensive documentation and reimplemented tests in a minimal form.
- **4fccdcc — Ash test harness & mocks** adding significant new test infrastructure and editing core scripts.
