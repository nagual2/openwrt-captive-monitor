# Analysis Tools

This directory contains Python utilities for analyzing CI/CD logs and debugging build failures.

## Available Tools

### Log Analysis

- **analyze_failed_job.py** - Analyzes failed GitHub Actions job logs
- **analyze_log.py** - General log file analyzer
- **check_corruption.py** - Checks for corrupted files or data

### Error Detection

- **find_exit_code.py** - Finds exit codes in log files
- **find_any_exit_code.py** - Searches for any exit code patterns
- **find_failed_job.py** - Identifies failed jobs in CI logs
- **find_artifact_error.py** - Detects artifact-related errors
- **find_feed_log.py** - Extracts feed-related log entries
- **find_make_error.py** - Finds make/build errors in logs
- **find_make_error_utf8.py** - UTF-8 version of make error finder

### Log Utilities

- **print_tail.py** - Prints the tail of log files
- **print_tail_utf8.py** - UTF-8 version of tail printer

## Usage

Most tools accept a log file as input:

```bash
python tools/analysis/analyze_failed_job.py <log-file>
python tools/analysis/find_make_error.py <log-file>
```

## Requirements

- Python 3.10+
- Standard library only (no external dependencies)

## Related Documentation

- [CI Troubleshooting Guide](../../docs/ci/CI_STATUS_REPORT.md)
- [GitHub Actions Diagnostics](../../docs/ci/GITHUB_ACTIONS_WORKFLOWS_AUDIT.md)
