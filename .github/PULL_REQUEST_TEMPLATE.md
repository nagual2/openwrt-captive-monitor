## Summary
<!-- What does this change do? Provide a concise overview that reviewers can skim. -->

## Testing
<!-- Describe how you validated the change. Paste command output when possible. -->
- [ ] `shfmt -d …` (or `shfmt -w` before committing)
- [ ] `shellcheck …`
- [ ] `./scripts/build_ipk.sh` (required when packaging is touched)
- [ ] Manual / hardware validation (detail what you tested):

## Trunk readiness
- [ ] Rebased on the latest `main` (`git fetch origin && git rebase origin/main`)
- [ ] Branch name follows `feature/*`, `fix/*`, `chore/*`, `docs/*`, or `hotfix/*`
- [ ] Title uses Conventional Commit style (e.g. `feat(wifi): ...`)
- [ ] `Lint` workflow is green (shfmt + ShellCheck)
- [ ] `openwrt-build` workflow is green (if build/packaging files changed)
- [ ] Docs / tests updated or marked not applicable

## Additional context
<!-- Optional: call out areas where you would like focused feedback or potential follow-up work. -->
