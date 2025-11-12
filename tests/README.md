# Test Suite for OpenWrt Captive Monitor

This directory contains the test suite for the OpenWrt Captive Monitor project.

## Overview

The test suite validates:

- Core functionality of the captive monitor script (command-line parsing, mode switching, DNS/HTTP redirects, cleanup)
- Package building with `build_ipk.sh` (standard and release modes, custom architectures)
- Error handling and edge cases

## Running Tests

### Quick Start

```bash
# From repository root
make test

# Or run directly
sh tests/run.sh
```

### With BusyBox

If BusyBox is available, tests will run with `busybox ash` for better OpenWrt compatibility:

```bash
busybox ash tests/run.sh
```

## Test Structure

### Main Test Runner

- `run.sh` - Main test runner with assertion helpers and test orchestration

### Mocks

All mock implementations are in `tests/mocks/`:

- **Core Utilities**: `busybox`, `sleep`, `logger`, `id`, `uci`, `ubus`
- **Network Tools**: `curl`, `ping`, `host`, `nslookup`, `ip`, `route`
- **Firewall**: `iptables`, `ip6tables`, `_iptables_mock.sh`
- **Services**: `dnsmasq`, `wifi`, `ifup`, `ifdown`
- **Build Tools**: `opkg-build`, `opkg-make-index`
- **Helpers**: `_lib.sh` - Common mock utilities

### Test Cases

1. **test_opts_parsing** - Validates command-line argument parsing
2. **test_mode_switch** - Tests oneshot vs monitor mode behavior
3. **test_dns_redirect_stubs** - Validates DNS/HTTP redirect setup
4. **test_cleanup** - Ensures proper cleanup of redirects and configuration
5. **test_build_ipk_package** - Tests complete package build process
6. **test_build_ipk_detects_archiver_failure** - Tests error handling in build
7. **test_build_ipk_release_mode** - Validates release mode output and metadata
8. **test_build_ipk_custom_arch** - Tests custom architecture handling
9. **test_build_ipk_help** - Validates help text completeness

## Mock Implementations

### opkg-build

Mock implementation of OpenWrt's `opkg-build` tool. Creates `.ipk` packages using the standard format:

- Creates `ar` archive with `debian-binary`, `control.tar.gz`, and `data.tar.gz`
- Parses control file for package metadata (name, version, architecture)
- Handles `-c` flag for separate control directory

**Usage**: `opkg-build -c <control-dir> <data-dir> <output-dir>`

### opkg-make-index

Mock implementation of OpenWrt's `opkg-make-index` tool. Generates package indexes:

- Scans directory for `.ipk` files
- Extracts control information from each package
- Adds checksums (MD5, SHA256) and file sizes
- Outputs Packages index format

**Usage**: `opkg-make-index [-a <arch>] <package-dir>`

## Environment Variables

Tests use environment variables for configuration:

### Monitor Script Tests

- `INTERNET_CHECK_RETRIES` - Number of connectivity check retries
- `PING_SERVERS` - Servers to ping for connectivity checks
- `MOCK_PING_FAIL_COUNT` - Number of ping failures to simulate
- `MOCK_CURL_HTTP_CODE` - HTTP status code to return from curl
- `MOCK_SLEEP_FAST` - Skip sleep delays in monitor mode
- `REQUESTED_FIREWALL_BACKEND` - Force firewall backend (iptables/nftables)

### Build Tests

- `TEST_LOG` - Path to command log file
- `TEST_STATE_DIR` - Directory for mock state files
- `PATH` - Modified to include mock directory first

## Output

Test output shows:

```
Running test suite...
Running test_opts_parsing...
PASS test_opts_parsing

Running test_mode_switch...
PASS test_mode_switch

...

All tests passed (9/9)
```

## Test Artifacts

Tests create temporary files in `tests/_out/`:

- `commands.log` - Log of mock commands executed
- `output.txt` - Script output capture
- `state/` - Mock state files
- `feed*/` - Package build artifacts for validation

These are cleaned up before each test run.

## CI/CD Integration

Tests are integrated into the CI pipeline:

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run tests
      run: make test
```

## Writing New Tests

To add a new test:

1. Create test function following naming convention `test_<name>`
2. Use assertion helpers:
   - `assert_eq <expected> <actual> [message]`
   - `assert_contains <needle> <haystack> [message]`
   - `assert_status <expected> <command...>`
3. Add test to `main()` function with `run_test test_<name>`
4. Run tests to verify: `make test`

Example:

```sh
test_my_feature() {
    # Setup
    test_file="$OUT_DIR/test.txt"
    echo "hello" > "$test_file"
    
    # Execute
    result=$(cat "$test_file")
    
    # Assert
    assert_eq "hello" "$result" "Should read test file"
    
    return 0
}
```

## Debugging

To debug test failures:

1. Check test output for specific assertion failures
2. Inspect `tests/_out/commands.log` for mock command invocations
3. Review `tests/_out/output.txt` for script output
4. Run individual test functions by modifying `main()` temporarily
5. Add verbose flags to scripts being tested

## Mock Development

When adding new mocks:

1. Create executable script in `tests/mocks/`
2. Source `_lib.sh` for common utilities:
   - `mock_log <command> <args...>` - Log command invocation
   - `mock_state_file <name>` - Get path to state file
3. Implement behavior based on environment variables
4. Test mock with actual test cases

## Compatibility

Tests are compatible with:

- POSIX shell (`sh`)
- BusyBox ash (OpenWrt default)
- Bash
- Dash

The test suite avoids bash-specific features to maintain OpenWrt compatibility.

## References

- [OpenWrt Testing Guide](https://openwrt.org/docs/guide-developer/testing)
- [BusyBox Ash](https://www.busybox.net/downloads/BusyBox.html)
- [POSIX Shell Scripting](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
