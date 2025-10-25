## Summary
<!-- Provide a concise overview that reviewers can skim quickly. -->

## Testing
<!-- Paste command output where useful. Mark non-applicable items with N/A. -->
- [ ] `shfmt -d …` (or `shfmt -w` locally before committing)
- [ ] `shellcheck …`
- [ ] `./scripts/build_ipk.sh` (required when packaging is touched)
- [ ] Manual / hardware validation (detail what you tested):

## CI status
- [ ] `Lint / Shell lint` workflow run is green
- [ ] `Build OpenWrt packages / Build (ath79-generic)` is green (if packaging files changed)
- [ ] `Build OpenWrt packages / Build (ramips-mt7621)` is green (if packaging files changed)

## Trunk readiness
- [ ] Rebased on the latest `main` (`git fetch origin && git rebase origin/main`)
- [ ] Branch name follows `feature/*`, `fix/*`, `chore/*`, `docs/*`, or `hotfix/*`
- [ ] Title uses Conventional Commit style (e.g. `feat(wifi): ...`)
- [ ] Docs / tests updated or marked not applicable

## Additional context
<!-- Optional: call out areas where you would like focused feedback or potential follow-up work. -->
