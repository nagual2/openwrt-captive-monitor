# Issue & PR Templates and Label Management

This guide explains the modernized issue and PR templates, label taxonomy, and triage processes for the
`openwrt-captive-monitor` repository.

## Overview

The repository uses GitHub Issue Forms and structured PR templates to ensure consistent, high-quality contributions.
Labels are managed manually to maintain consistency across all issues and pull requests.

## Issue Templates

### Available Issue Forms

1. **🐛 Bug Report** (`bug.yml`)
   - Use for: Reporting problems and unexpected behavior
   - Auto-applied labels: `bug`
   - Required fields: Summary, Environment, Steps to reproduce, Expected/Actual behavior
   - Acceptance criteria: Search existing issues, provide reproduction steps, sanitize logs

2. **🚀 Feature Request** (`feature.yml`)
   - Use for: Suggesting new functionality or improvements
   - Auto-applied labels: `enhancement`
   - Required fields: Summary, Motivation, Proposed solution
   - Optional: Implementation scope, alternatives considered

3. **💬 Support Question** (`support.yml`)
   - Use for: Getting help with installation, configuration, and troubleshooting
   - Auto-applied labels: `question`
   - Required fields: Category, Environment, Question
   - Pre-requisites: Check documentation, SUPPORT.md, and existing issues

4. **📚 Documentation Issue** (`docs.yml`)
   - Use for: Reporting problems or suggesting improvements to documentation
   - Auto-applied labels: `documentation`
   - Required fields: Issue type, Documentation type, Issue description
   - Helps maintain accurate and helpful documentation

### Issue Triage Process

1. **Initial Tiage** (within 24 hours)
   - Apply `status/needs-triage` to new issues
   - Verify correct template usage and required fields
   - Add appropriate component labels (`component/wifi`, `component/dns`, etc.)
   - Set priority label (`priority/low`, `priority/medium`, `priority/high`, `priority/critical`)
   - Remove `status/needs-triage` and add `status/ready-for-review` if actionable

2. **Information Gathering**
   - Use `status/needs-more-info` for incomplete reports
   - Request additional details with specific questions
   - Close after 7 days of no response with `status/wontfix`

3. **Duplicate Management**
   - Mark duplicates with `status/duplicate`
   - Link to original issue
   - Close duplicate after confirming overlap

## Pull Request Template

### Structure

The PR template is organized into clear sections to help contributors and reviewers:

1. **Summary**: Quick overview for reviewers
2. **Type of Change**: Categorizes the PR for changelog generation
3. **Testing Evidence**: Demonstrates that changes work correctly
4. **Breaking Changes & Migration**: Documents any breaking changes
5. **Release Note**: Drafts the changelog entry
6. **Reviewer Checklist**: Confirms readiness for review
7. **Areas for Review Focus**: Highlights specific concerns

### PR Triage Process

1. **Initial Review** (within 48 hours)
   - Verify PR template is properly completed
   - Check branch name follows conventions (`feature/*`, `fix/*`, etc.)
   - Confirm title uses Conventional Commit format
   - Add appropriate size label (`size/XS` through `size/XXL`)
   - Apply component labels based on changed files

2. **Review Assignment**
   - Add `status/review-requested` when ready for detailed review
   - Assign appropriate reviewers based on components
   - Set `status/ready-for-review` for initial automated checks

3. **Review Process**
   - Validate all checklist items are completed
   - Ensure testing evidence is sufficient
   - Verify breaking changes are properly documented
   - Check release note quality and accuracy

## Label Taxonomy

### Priority Labels
- `priority/critical` - Immediate attention required (security, production outages)
- `priority/high` - Important issues affecting core functionality
- `priority/medium` - Standard priority for most issues and features
- `priority/low` - Nice-to-have improvements, minor issues

### Type Labels
- `bug` - Something isn't working as expected
- `enhancement` - New feature or improvement request
- `question` - Support questions and clarifications
- `documentation` - Documentation improvements and fixes
- `maintenance` - Refactoring, cleanup, technical debt

### Status Labels
- `status/needs-triage` - Awaiting initial triage
- `status/ready-for-review` - Ready for community review
- `status/review-requested` - Specific review requested
- `status/needs-more-info` - Awaiting additional information
- `status/blocked` - Blocked by dependencies or other issues
- `status/wontfix` - Will not be implemented
- `status/duplicate` - Duplicate of existing issue

### Component Labels
- `component/wifi` - WiFi recovery and management
- `component/dns` - DNS handling and redirection
- `component/networking` - Network connectivity and routing
- `component/packaging` - OpenWrt packaging and build system
- `component/ci` - CI/CD workflows and automation
- `component/configuration` - UCI configuration and settings
- `component/logging` - Logging and diagnostics

### Size Labels (PRs only)
- `size/XS` - 0-9 lines changed
- `size/S` - 10-29 lines changed
- `size/M` - 30-99 lines changed
- `size/L` - 100-499 lines changed
- `size/XL` - 500-999 lines changed
- `size/XXL` - 1000+ lines changed

### Special Labels
- `good-first-issue` - Suitable for newcomers
- `help-wanted` - Community assistance needed
- `security` - Security-related issues
- `dependencies` - Dependency updates
- `release-blocker` - Blocks next release
- `release-candidate` - Ready for next release

## Triage Best Practices

### For Issue Triage

1. **Respond promptly** - Acknowledge new issues within 24 hours
2. **Be specific** - Ask targeted questions when more info is needed
3. **Use consistent labeling** - Follow the taxonomy strictly
4. **Document decisions** - Explain why issues are marked `wontfix` or `duplicate`
5. **Encourage contributions** - Use `good-first-issue` and `help-wanted` strategically

### For PR Triage

1. **Check template completion** - Ensure all sections are filled out
2. **Verify CI status** - All automated checks must pass
3. **Review size labels** - Encourage smaller PRs when possible
4. **Focus on security** - Pay special attention to `security` labeled changes
5. **Maintain quality** - Don't merge without proper review and testing

### Label Combinations

Common label combinations to understand:

- `bug` + `priority/critical` + `component/wifi` = Critical WiFi bug
- `enhancement` + `priority/medium` + `help-wanted` = Community feature request
- `documentation` + `good-first-issue` = Beginner-friendly documentation task
- `status/blocked` + `dependencies` = Blocked by external dependency

## Automation and Workflows

### Issue Form Automation

Issue forms automatically:
- Apply base labels (`bug`, `enhancement`, `question`, `documentation`)
- Validate required fields
- Guide contributors through structured reporting

### PR Template Integration

The PR template integrates with:
- Conventional Commit titles for changelog automation
- Size labeling for release planning
- Component labels for reviewer assignment
- Release note drafting for CHANGELOG.md

## Contributing to Templates

To improve the templates and label system:

1. **Edit issue forms** - Modify `.github/ISSUE_TEMPLATE/*.yml` files
2. **Update PR template** - Edit `.github/PULL_REQUEST_TEMPLATE.md`
3. **Manage labels** - Use GitHub's label management interface
4. **Test changes** - Use draft PRs to verify template rendering
5. **Update documentation** - Keep this guide current

## Resources

- [GitHub Issue Forms
documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [Conventional Commits specification](https://www.conventionalcommits.org/)
- [Project contribution guidelines](../../CONTRIBUTING.md)

---

**Last updated:** 2025-10-30  
**Maintained by:** Repository maintainers and community contributors
