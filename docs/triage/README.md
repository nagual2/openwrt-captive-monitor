# Triage & Audit Reports

This directory contains PR queue audit reports and triage artifacts for the `openwrt-captive-monitor` repository.

## Current Status

📊 **Latest Audit:** No current audit reports available

**Summary:** ✅ **0 open PRs** - Queue clean, all tests passing

## Files in This Directory

### Templates and Label Management

- **[TEMPLATES_AND_LABELS.md](./TEMPLATES_AND_LABELS.md)** - Guide to modernized issue/PR templates and label taxonomy
  - GitHub Issue Forms usage and triage processes
  - PR template structure and review checklist
  - Label taxonomy and synchronization workflow
  - Best practices for issue and PR triage

### Audit Reports

- No current audit reports available. Previous reports have been archived as part of repository cleanup.

### API Snapshots

- **pr-status-20251030T123851Z.json** - GitHub API response snapshot
  - Captured during 2025-10-30 audit
  - Shows empty PR queue at audit time

## Related Documentation

For historical context and prior triage work, see:

- **[../project/BRANCHES_PR_AUDIT.md](../project/BRANCHES_PR_AUDIT.md)** - Original branch & PR inventory (2025-10-24)
   - Documents 17 PRs that existed before comprehensive triage
   - Provides cleanup checklist and branching strategy

- **[../project/PR_TRIAGE.md](../project/PR_TRIAGE.md)** - Detailed triage analysis (2025-10-24)
   - Explains closure rationale for PRs #6, #11, #12
   - Documents prior triage of PRs #1-#2

- CI health tracking information has been archived as part of repository cleanup

## Audit Process

PR queue audits follow this process:

1. **Query GitHub API** for open pull requests
2. **Analyze each PR** for conflicts, CI status, merge readiness
3. **Run baseline tests** on main branch
4. **Document findings** in audit report
5. **Capture API snapshot** for historical record

## When to Run Next Audit

- **Frequency:** Monthly or when PR count exceeds 5
- **Trigger:** After major merges or releases
- **Process:** Follow `docs/RELEASE_CHECKLIST.md` guidelines

## Contributing

When conducting PR triage:

1. Review existing audit reports in this directory
2. Follow trunk-based workflow from `BRANCHES_AND_MERGE_POLICY.md`
3. Document closure rationale for declined PRs
4. Archive audit reports after completion

---

**Last updated:** 2025-10-30
