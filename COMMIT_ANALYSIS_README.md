# Commit Analysis Tools

This directory contains tools and documentation for analyzing the git commit history of the `nagual2/openwrt-captive-monitor` repository.

## Files

### Scripts
- **`analyze-150-commits.sh`** - Main analysis script that fetches and categorizes commits

### Reports
- **`COMMIT_ANALYSIS_REPORT.md`** - Detailed analysis report with comprehensive categorization
- **`ANALYSIS_SUMMARY.md`** - Quick summary with key insights
- **`commit-analysis.txt`** - Raw output from the latest analysis run

## Quick Start

### Run the Analysis
```bash
./analyze-150-commits.sh
```

### With GitHub Token (Recommended for Higher Rate Limits)
```bash
GITHUB_TOKEN=your_github_token_here ./analyze-150-commits.sh
```

### Save Output to File
```bash
./analyze-150-commits.sh > commit-analysis.txt 2>&1
```

## Categorization Logic

### Part 1: Script Changes (45 commits)
Commits that modified:
- Shell scripts and executable code
- Package build and deployment logic
- OpenWrt package configurations
- CI/CD integration with scripts
- Business logic for monitoring and detection

**Keywords matched:** `script`, `.sh`, `.lua`, `.js`, `src/`, `bin/`, `lib/`, `captive`, `monitor`, `detection`, `interception`, `handler`, `chain`, `dns`, `http`, `proxy`, `firewall`, `iptables`, `nftables`, `procd`, `uci`

### Part 2: Other Changes (46 commits)
Commits that modified:
- GitHub Actions workflows
- Build and dependency configuration
- Documentation and README files
- Release management and versioning
- Project metadata and licensing

**Keywords matched:** `workflow`, `github`, `action`, `ci`, `cd`, `makefile`, `config`, `readme`, `doc`, `build`, `test`, `lint`, `format`, `license`, `changelog`, `bump`, `release`, `version`

## Statistics from Latest Run

| Category | Commits | Percentage |
|----------|---------|-----------|
| Script Changes | 45 | 45% |
| Other Changes | 46 | 46% |
| Uncategorized | 9 | 9% |
| **Total** | **100** | **100%** |

## Uncategorized Commits

9 commits don't clearly fit either category due to:
- Vague commit messages
- Non-English commit text
- Generic merge commits
- File removal without context

Examples: "Remove", "Merge", "Обновление версии" (Russian for "Version update")

## API Information

- **API:** GitHub REST API v3
- **Endpoint:** `https://api.github.com/repos/nagual2/openwrt-captive-monitor/commits`
- **Parameters:** `per_page=150`
- **Rate Limits:**
  - **Unauthenticated:** 60 requests/hour
  - **Authenticated:** 5000 requests/hour
- **Note:** GitHub API returns maximum 100 commits per page; pagination is needed for more

## Technical Details

### Dependencies
- `bash` - Shell interpreter
- `curl` - HTTP client for GitHub API
- `jq` - JSON query processor
- `git` - Version control (for remote URL parsing)

### How It Works
1. Fetches commit data from GitHub API as JSON
2. Uses `jq` to parse and filter commits
3. Applies regex patterns on commit messages
4. Categorizes into two groups
5. Generates statistics
6. Outputs results in human-readable format

### Script Permissions
```bash
chmod +x analyze-150-commits.sh
```

## Usage Examples

### Generate Fresh Analysis
```bash
./analyze-150-commits.sh | tee fresh-analysis.txt
```

### Compare Two Analysis Runs
```bash
# Run 1
./analyze-150-commits.sh > analysis-run1.txt

# Run 2  
./analyze-150-commits.sh > analysis-run2.txt

# Compare
diff -u analysis-run1.txt analysis-run2.txt
```

### Extract Just Statistics
```bash
./analyze-150-commits.sh | grep -A 10 "📊 STATISTICS"
```

### Extract Specific Category
```bash
./analyze-150-commits.sh | grep -A 50 "PART 1:"
./analyze-150-commits.sh | grep -A 50 "PART 2:"
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Analyze commits
  run: |
    ./analyze-150-commits.sh
    
- name: Upload analysis
  uses: actions/upload-artifact@v3
  with:
    name: commit-analysis
    path: commit-analysis.txt
```

## Extending the Analysis

### Add Custom Keywords
Edit the `SCRIPT_KEYWORDS` and `OTHER_KEYWORDS` variables in `analyze-150-commits.sh`:

```bash
SCRIPT_KEYWORDS="script|[.]sh|your_keyword_here"
OTHER_KEYWORDS="workflow|github|your_keyword_here"
```

### Fetch More Commits (Pagination)
To analyze more than 100 commits, modify the script to implement pagination:

```bash
for page in {1..3}; do
  curl -s "...&page=$page" | jq '.[]' >> all_commits.json
done
```

### Filter by Date Range
Use GitHub API's date filtering:

```bash
curl -s "...&since=2025-11-01&until=2025-11-12"
```

## Troubleshooting

### "jq: command not found"
Install jq:
```bash
sudo apt-get install jq
```

### "Error fetching commits from GitHub API"
- Check internet connection
- Verify repository name
- Check GitHub API status
- Add authentication with GITHUB_TOKEN

### Empty Results
- Verify you're in a git repository
- Ensure GitHub token has correct permissions
- Check API rate limit (GitHub CLI: `gh api rate_limit`)

## Recommendations

1. **Improve Commit Messages:** Use conventional commit format for better categorization
2. **Run Regularly:** Execute before releases to understand commit trends
3. **Monitor Ratio:** Track script vs infrastructure changes ratio over time
4. **Extend Analysis:** Add file change analysis in addition to message analysis
5. **Archive Results:** Save results over time to detect trends

## Further Reading

- [COMMIT_ANALYSIS_REPORT.md](COMMIT_ANALYSIS_REPORT.md) - Detailed analysis
- [ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md) - Quick summary
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [jq Manual](https://stedolan.github.io/jq/manual/)

---

*Last Updated: 2025-11-12*
*Repository: nagual2/openwrt-captive-monitor*
