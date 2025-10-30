## Summary
<!-- Provide a concise overview that reviewers can skim quickly. -->

## Type of Change
<!-- Mark all that apply. This helps with changelog generation. -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] 🚀 New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🛠️ Maintenance/CI/refactoring (no user-facing changes)
- [ ] 🔧 Configuration or packaging change

## Testing Evidence
<!-- Provide evidence that your changes work as intended. -->
- [ ] **Local linting passed**: `shfmt -d . && shellcheck openwrt_captive_monitor.sh`
- [ ] **Package build tested**: `./scripts/build_ipk.sh` (if packaging files changed)
- [ ] **Manual/hardware validation**: Describe what you tested and the results
- [ ] **Edge cases considered**: Document any edge cases you tested or considered

### Test Details
<!-- Paste relevant test output or describe your testing methodology. -->
```
# Example test output or commands run
```

## Breaking Changes & Migration
<!-- If this is a breaking change, explain the impact and migration path. -->
- [ ] This change contains breaking changes
- [ ] Migration guide provided (if applicable)
- [ ] Backwards compatibility considered

### Breaking Change Details
<!-- Describe what breaks and how users should migrate. -->

## Release Note
<!-- Write a brief release note in the style of the existing changelog. -->
<!-- Example: "Fixed WiFi recovery failing on certain router models by adding timeout handling." -->

```markdown
<!-- Your release note here -->
```

## Reviewer Checklist
<!-- Help reviewers by confirming you've completed these items. -->
- [ ] **Code follows project style**: Consistent with existing codebase
- [ ] **Commits are atomic**: Each commit represents one logical change
- [ ] **Branch is up-to-date**: Rebased on latest `main` branch
- [ ] **Title uses Conventional Commit**: `type(scope): description` format
- [ ] **Documentation updated**: If user-facing changes were made
- [ ] **Tests updated**: If functionality was added or changed
- [ ] **No sensitive data**: Logs and examples are sanitized

## Areas for Review Focus
<!-- Optional: highlight specific areas where you'd like focused feedback. -->
- **Code correctness**: 
- **Security implications**: 
- **Performance impact**: 
- **User experience**: 
- **Documentation clarity**: 

## Additional Context
<!-- Any other information that would help reviewers understand this change. -->
