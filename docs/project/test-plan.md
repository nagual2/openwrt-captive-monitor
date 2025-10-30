# Test Plan

Comprehensive testing strategy and procedures for **openwrt-captive-monitor**.

## 🎯 Testing Objectives

Ensure the service:
- ✅ Detects captive portals accurately and reliably
- ✅ Intercepts traffic correctly when needed
- ✅ Cleans up properly after authentication
- ✅ Performs well across different OpenWrt versions and hardware
- ✅ Maintains security and doesn't compromise user privacy
- ✅ Handles edge cases and error conditions gracefully

---

## 🧪 Test Environments

### 1. Development Environment

**Setup:**
- Local development machine with BusyBox
- Mock network tools (ip, iptables, dnsmasq)
- Automated test suite with `bats`

**Purpose:**
- Unit testing of individual functions
- Integration testing of core logic
- CI/CD pipeline validation

### 2. Emulation Environment

**Setup:**
- OpenWrt SDK or container
- Full OpenWrt userspace
- Network simulation tools

**Purpose:**
- Realistic testing without hardware
- Multiple OpenWrt version testing
- Automated regression testing

### 3. Hardware Environment

**Setup:**
- Physical OpenWrt routers
- Real network connections
- Actual client devices

**Purpose:**
- End-to-end validation
- Performance testing
- User experience verification

---

## 📋 Test Categories

### 1. Unit Tests

#### Configuration Tests
```bash
#!/usr/bin/env bats
@test "UCI configuration loading" {
    # Test configuration parsing
    # Test default values
    # Test environment variable overrides
    # Test command-line argument parsing
}

@test "Configuration validation" {
    # Test invalid configuration detection
    # Test missing required parameters
    # Test configuration file corruption handling
}
```

#### Network Detection Tests
```bash
@test "WiFi interface detection" {
    # Test automatic interface discovery
    # Test manual interface specification
    # Test interface state validation
}

@test "Network configuration detection" {
    # Test LAN interface detection
    # Test IP address discovery
    # Test IPv6 support detection
}
```

#### Connectivity Tests
```bash
@test "Gateway connectivity checking" {
    # Test ping gateway functionality
    # Test ARP table validation
    # Test route table validation
}

@test "Internet connectivity checking" {
    # Test external ping functionality
    # Test HTTP probe functionality
    # Test DNS resolution testing
}
```

### 2. Integration Tests

#### Service Lifecycle Tests
```bash
@test "Service startup and shutdown" {
    # Test normal startup sequence
    # Test graceful shutdown
    # Test signal handling (SIGTERM, SIGINT)
}

@test "Configuration reloading" {
    # Test runtime configuration changes
    # Test UCI configuration updates
    # Test environment variable changes
}
```

#### Firewall Integration Tests
```bash
@test "iptables backend integration" {
    # Test rule creation and deletion
    # Test chain management
    # Test rule ordering and priorities
}

@test "nftables backend integration" {
    # Test table and chain creation
    # Test rule management
    # Test backend auto-detection
}
```

#### DNS Integration Tests
```bash
@test "dnsmasq integration" {
    # Test drop-in configuration creation
    # Test dnsmasq reload
    # Test DNS override functionality
}
```

### 3. System Tests

#### Captive Portal Detection Tests
```bash
@test "HTTP redirect detection" {
    # Test 302 redirect detection
    # Test Location header extraction
    # Test multiple URL detection
}

@test "Captive portal URL extraction" {
    # Test URL parsing from various responses
    # Test URL validation
    # Test edge cases (malformed URLs)
}
```

#### Traffic Interception Tests
```bash
@test "DNS hijacking functionality" {
    # Test DNS override file creation
    # Test domain resolution redirection
    # Test selective domain preservation
}

@test "HTTP redirection functionality" {
    # Test firewall rule creation
    # Test HTTP server startup
    # Test client redirection flow
}
```

#### Cleanup Tests
```bash
@test "Automatic cleanup after authentication" {
    # Test internet restoration detection
    # Test firewall rule cleanup
    # Test DNS override removal
    # Test HTTP server shutdown
}
```

---

## 🌐 Network Scenario Tests

### 1. Normal Internet Connection

**Test Steps:**
1. Connect router to network with working internet
2. Enable captive monitor service
3. Monitor service behavior

**Expected Results:**
- Service detects working internet
- No captive portal rules created
- Normal traffic flow preserved
- Minimal resource usage

**Validation Commands:**
```bash
# Check service logs
logread | grep captive-monitor

# Verify no interception rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n 2>/dev/null || echo "No rules (expected)"

# Test internet connectivity
ping -c 2 8.8.8.8
curl -I http://example.com
```

### 2. Captive Portal Scenario

**Test Steps:**
1. Connect router to network with captive portal
2. Enable captive monitor service
3. Connect client device and attempt to access internet
4. Authenticate through captive portal
5. Verify cleanup

**Expected Results:**
- Service detects captive portal
- DNS queries redirected to router
- HTTP requests redirected to portal
- Cleanup after authentication

**Validation Commands:**
```bash
# Check DNS interception
nslookup google.com  # Should return router IP

# Check firewall rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

# Test HTTP redirection
curl -I http://google.com  # Should redirect to portal

# Verify cleanup after authentication
# (repeat checks after authentication)
```

### 3. Network Disconnection/Reconnection

**Test Steps:**
1. Start with working internet connection
2. Disconnect WAN connection
3. Reconnect WAN connection
4. Monitor service behavior throughout

**Expected Results:**
- Service detects connection loss
- WiFi restart triggered (if configured)
- Service detects connection restoration
- Normal operation resumes

### 4. Multiple Interface Scenarios

**Test Steps:**
1. Configure multiple network interfaces
2. Test service with different interface configurations
3. Verify interface-specific behavior

**Expected Results:**
- Correct interface detection
- Proper interface-specific rule creation
- Isolation between interfaces

---

## 🔧 Performance Tests

### 1. Resource Usage Tests

**Metrics to Monitor:**
- CPU usage percentage
- Memory consumption (RSS, VMS)
- Disk I/O (log files, temporary files)
- Network overhead

**Test Procedure:**
```bash
# Baseline measurement
ps aux | grep openwrt_captive_monitor
free -h
df -h

# Long-running test (24 hours)
/usr/sbin/openwrt_captive_monitor --monitor &
SERVICE_PID=$!

# Monitor resources every 5 minutes
while kill -0 $SERVICE_PID; do
    echo "$(date): $(ps -o pid,pcpu,pmem,cmd -p $SERVICE_PID)"
    sleep 300
done
```

### 2. Scalability Tests

**Test Scenarios:**
- Multiple concurrent clients (10, 50, 100)
- High-frequency DNS queries
- Simultaneous HTTP requests
- Long-running operation (48+ hours)

**Validation:**
- Service remains responsive
- No memory leaks
- Consistent performance

### 3. Stress Tests

**Test Conditions:**
- Rapid network state changes
- Frequent captive portal detection/cleanup cycles
- Configuration changes during operation
- Resource exhaustion scenarios

---

## 🛡️ Security Tests

### 1. Traffic Isolation Tests

**Test Objectives:**
- Verify HTTPS traffic is never intercepted
- Ensure DNS queries only redirected locally
- Confirm no packet content inspection
- Validate rule isolation

**Test Procedure:**
```bash
# Test HTTPS traffic
curl -I https://google.com  # Should not be intercepted

# Test DNS queries
tcpdump -i any port 53 -n  # Monitor DNS traffic

# Test firewall rules
iptables -L -n -v  # Verify rule scope
```

### 2. Privilege Escalation Tests

**Test Areas:**
- File system access restrictions
- Network interface access validation
- Process permission checks
- Configuration file security

### 3. Data Privacy Tests

**Verification:**
- No user data logging
- No traffic content storage
- Minimal metadata collection
- Secure temporary file handling

---

## 🐛 Edge Case Tests

### 1. Configuration Edge Cases

**Test Scenarios:**
- Empty configuration files
- Corrupted UCI configuration
- Invalid interface names
- Out-of-range parameter values

### 2. Network Edge Cases

**Test Scenarios:**
- No gateway available
- DNS server unavailable
- Interface with no IP address
- IPv6-only networks

### 3. System Edge Cases

**Test Scenarios:**
- Low memory conditions
- Full disk conditions
- Missing dependencies
- Permission denied errors

---

## 📱 Device Compatibility Tests

### 1. OpenWrt Version Testing

**Target Versions:**
- OpenWrt 21.02 (LTS)
- OpenWrt 22.03 (LTS)
- OpenWrt 23.05 (stable)
- OpenWrt 24.10 (development)

### 2. Hardware Platform Testing

**Target Architectures:**
- mips_24kc (common routers)
- aarch64_cortex-a53 (newer routers)
- x86_64 (virtual/PC)
- arm_cortex-a7 (older routers)

### 3. Client Device Testing

**Test Devices:**
- Windows 10/11 laptops
- macOS laptops
- Android phones/tablets
- iOS phones/tablets
- Linux devices

---

## 🔄 Regression Tests

### 1. Automated Regression Suite

**Test Categories:**
- All unit tests
- Core integration tests
- Critical system tests
- Performance benchmarks

**Execution:**
```bash
# Run full regression suite
./scripts/run-regression-tests.sh

# Generate report
./scripts/generate-test-report.sh
```

### 2. Manual Regression Checklist

**Areas to Verify:**
- Basic functionality still works
- No new bugs introduced
- Performance not degraded
- Security not compromised

---

## 📊 Test Automation

### 1. CI/CD Pipeline Tests

**GitHub Actions Workflow:**
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y busybox shellcheck bats
      - name: Run unit tests
        run: bats tests/unit/
      - name: Run integration tests
        run: bats tests/integration/
      - name: Run shellcheck
        run: shellcheck scripts/*.sh package/*/files/usr/sbin/*
      - name: Test package build
        run: scripts/build_ipk.sh --arch all
```

### 2. Automated Test Scripts

**Test Runner:**
```bash
#!/bin/bash
# run-tests.sh - Comprehensive test runner

set -e

echo "Running test suite..."

# Unit tests
echo "Running unit tests..."
bats tests/unit/

# Integration tests
echo "Running integration tests..."
bats tests/integration/

# System tests (if in container/emulation)
if [ -n "$TEST_ENVIRONMENT" ]; then
    echo "Running system tests..."
    bats tests/system/
fi

# Package validation
echo "Validating package..."
scripts/validate-package.sh

echo "All tests passed!"
```

### 3. Test Data Management

**Test Fixtures:**
- Sample configuration files
- Mock network responses
- Simulated captive portal pages
- Test network topologies

**Test Utilities:**
- Mock service scripts
- Network simulation tools
- Test harness helpers
- Result validation functions

---

## 📋 Test Documentation

### 1. Test Case Documentation

Each test case should include:
- **Objective**: What is being tested
- **Prerequisites**: Required setup
- **Procedure**: Step-by-step instructions
- **Expected Results**: What should happen
- **Validation**: How to verify success

### 2. Test Environment Setup

**Development Environment:**
```bash
# Setup development test environment
./scripts/setup-dev-env.sh

# Run tests
./scripts/run-tests.sh
```

**Emulation Environment:**
```bash
# Setup OpenWrt emulation
docker run -it openwrtorg/rootfs:x86-64

# Install test package
opkg install openwrt-captive-monitor_*.ipk

# Run tests
./scripts/run-system-tests.sh
```

---

## 📈 Test Metrics and Reporting

### 1. Coverage Metrics

- **Code Coverage**: Percentage of code tested
- **Feature Coverage**: Percentage of features tested
- **Scenario Coverage**: Percentage of use cases tested

### 2. Quality Metrics

- **Test Pass Rate**: Percentage of tests passing
- **Bug Detection Rate**: Number of bugs found
- **Regression Rate**: Number of regressions introduced

### 3. Performance Metrics

- **Resource Usage**: CPU, memory, disk usage
- **Response Times**: Detection and cleanup times
- **Throughput**: Clients supported simultaneously

### 4. Reporting

**Daily Reports:**
- Automated test results
- Coverage statistics
- Performance benchmarks

**Release Reports:**
- Full test suite results
- Compatibility matrix
- Performance comparison

---

## 🚨 Test Failure Procedures

### 1. Immediate Actions

- **Stop the build/release process**
- **Document the failure**
- **Notify the development team**
- **Preserve test environment for analysis**

### 2. Root Cause Analysis

- **Examine test logs**
- **Reproduce the failure**
- **Identify the root cause**
- **Determine fix scope**

### 3. Resolution Process

- **Implement the fix**
- **Verify the fix**
- **Update tests if needed**
- **Re-run the test suite**

### 4. Prevention Measures

- **Update test cases**
- **Add regression tests**
- **Improve documentation**
- **Review development processes**

This comprehensive test plan ensures the reliability, security, and performance of openwrt-captive-monitor across diverse environments and use cases.