#!/bin/sh
set -eu

TEST_DIR=$(cd "$(dirname "$0")" 2> /dev/null && pwd)
REPO_ROOT=$(cd "$TEST_DIR/.." 2> /dev/null && pwd)
SCRIPT="$REPO_ROOT/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor"
MOCK_DIR="$TEST_DIR/mocks"
OUT_DIR="$TEST_DIR/_out"
STATE_DIR="$OUT_DIR/state"
TEST_LOG="$OUT_DIR/commands.log"
BASE_PATH=${PATH_OVERRIDE:-/usr/bin:/bin}
BUSYBOX_CANDIDATE=${BUSYBOX:-busybox}
REAL_BUSYBOX_PATH=$(PATH="$BASE_PATH" command -v "$BUSYBOX_CANDIDATE" 2> /dev/null || true)
HAS_REAL_BUSYBOX=0
if [ -n "$REAL_BUSYBOX_PATH" ] && [ -x "$REAL_BUSYBOX_PATH" ]; then
    HAS_REAL_BUSYBOX=1
else
    REAL_BUSYBOX_PATH=""
fi
SYSTEM_SHELL=$(PATH="$BASE_PATH" command -v sh 2> /dev/null || printf '/bin/sh')
case "$SYSTEM_SHELL" in
    */*) ;;
    *)
        SYSTEM_SHELL="/bin/sh"
        ;;
esac
REAL_SLEEP_BIN=$(PATH="$BASE_PATH" command -v sleep 2> /dev/null || printf '/bin/sleep')
DNSMASQ_MOCK="$MOCK_DIR/dnsmasq"
DNSMASQ_CONF="/tmp/dnsmasq.d/captive_intercept.conf"
HTTPD_ROOT="/tmp/captive_httpd"
HTTPD_PIDFILE="/tmp/captive_httpd.pid"

TOTAL_TESTS=0
PASSED_TESTS=0
LAST_STATUS=0
LAST_OUTPUT=""

reset_logs() {
    rm -rf "$OUT_DIR"
    mkdir -p "$STATE_DIR"
    : > "$TEST_LOG"
    rm -f "$DNSMASQ_CONF"
    rm -rf "${DNSMASQ_CONF%/*}"
    rm -rf "$HTTPD_ROOT"
    rm -f "$HTTPD_PIDFILE"
}

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

assert_eq() {
    expected="$1"
    actual="$2"
    message=${3:-"Expected '$expected' got '$actual'"}
    if [ "$expected" != "$actual" ]; then
        fail "$message"
    fi
}

assert_contains() {
    needle="$1"
    haystack="$2"
    message=${3:-"Expected to find '$needle'"}
    case "$haystack" in
        *"$needle"*) ;;
        *)
            fail "$message"
            ;;
    esac
}

assert_status() {
    expected="$1"
    shift
    if "$@"; then
        status=0
    else
        status=$?
    fi
    if [ "$status" -ne "$expected" ]; then
        fail "Expected exit status $expected, got $status"
    fi
}

parse_make_var() {
    key="$1"
    awk -F':=' -v key="$key" '
        $1 == key {
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
            gsub(/\r/, "", $2)
            print $2
            exit
        }
    ' "$REPO_ROOT/package/openwrt-captive-monitor/Makefile"
}

run_with_env() {
    outfile="$OUT_DIR/output.txt"
    rm -f "$outfile"
    (
        set -eu
        export PATH="$MOCK_DIR:$BASE_PATH"
        export TEST_LOG="$TEST_LOG"
        export TEST_STATE_DIR="$STATE_DIR"
        export REAL_SLEEP_BIN="$REAL_SLEEP_BIN"
        if [ "$HAS_REAL_BUSYBOX" = "1" ]; then
            export REAL_BUSYBOX_BIN="$REAL_BUSYBOX_PATH"
        else
            unset REAL_BUSYBOX_BIN
        fi
        export DNSMASQ_SERVICE="$DNSMASQ_MOCK"
        mkdir -p "$STATE_DIR"
        while [ "$#" -gt 0 ]; do
            case "$1" in
                --)
                    shift
                    break
                    ;;
                *=*)
                    var=${1%%=*}
                    value=${1#*=}
                    export "$var=$value"
                    shift
                    ;;
                *)
                    break
                    ;;
            esac
        done
        use_real_busybox="$HAS_REAL_BUSYBOX"
        if [ "$use_real_busybox" = "1" ]; then
            if [ "${MOCK_SLEEP_FAST:-}" = "1" ] || [ "${MOCK_SLEEP_TERMINATE:-}" = "1" ]; then
                use_real_busybox=0
            fi
        fi
        if [ "$use_real_busybox" = "1" ]; then
            runner="$REAL_BUSYBOX_PATH"
            set -- sh "$SCRIPT" "$@"
        else
            runner="$SYSTEM_SHELL"
            set -- "$SCRIPT" "$@"
        fi
        "$runner" "$@" > "$outfile" 2>&1
    )
    status=$?
    LAST_STATUS=$status
    if [ -f "$outfile" ]; then
        LAST_OUTPUT=$(cat "$outfile" 2> /dev/null || printf '')
    else
        LAST_OUTPUT=""
    fi
    return "$status"
}

run_test() {
    name="$1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    printf 'Running %s...\n' "$name"
    reset_logs
    if "$name"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        printf 'PASS %s\n\n' "$name"
    else
        fail "Test $name failed"
    fi
}

test_opts_parsing() {
    assert_status 0 run_with_env -- --help
    assert_contains "Использование" "$LAST_OUTPUT" "--help should print usage"

    assert_status 1 run_with_env -- --unknown
    assert_contains "Неизвестная опция" "$LAST_OUTPUT" "Unknown option should be reported"
    assert_contains "Использование" "$LAST_OUTPUT" "Usage should be shown for unknown option"

    assert_status 0 run_with_env \
        "INTERNET_CHECK_RETRIES=1" \
        "PING_SERVERS=1.1.1.1" \
        "MOCK_PING_FAIL_COUNT=1" \
        "PING_SUCCESS_HOSTS=1.1.1.1 192.168.1.1" \
        "MOCK_CURL_HTTP_CODE=000" \
        "MOCK_CURL_CAPTIVE=fail" \
        "MOCK_IFUP_STATUS=1" \
        "MOCK_SLEEP_FAST=1" \
        "REQUESTED_FIREWALL_BACKEND=iptables" \
        -- -o -i custom0 -t 7
    log_content=$(cat "$TEST_LOG" 2> /dev/null || printf '')
    assert_contains "ip link set dev custom0 down" "$log_content" "Custom interface should be used when restarting WiFi"
    return 0
}

test_mode_switch() {
    assert_status 0 run_with_env \
        "INTERNET_CHECK_RETRIES=1" \
        "PING_SERVERS=1.1.1.1" \
        "PING_SUCCESS_HOSTS=1.1.1.1" \
        "REQUESTED_FIREWALL_BACKEND=iptables" \
        -- -o
    assert_contains "Запуск в режиме однократной проверки" "$LAST_OUTPUT" "Oneshot mode should log startup"

    assert_status 0 run_with_env \
        "INTERNET_CHECK_RETRIES=1" \
        "PING_SERVERS=1.1.1.1" \
        "PING_SUCCESS_HOSTS=1.1.1.1" \
        "MOCK_SLEEP_FAST=1" \
        "MOCK_SLEEP_TERMINATE=1" \
        "REQUESTED_FIREWALL_BACKEND=iptables" \
        -- -m -t 5
    assert_contains "Запуск в режиме мониторинга" "$LAST_OUTPUT" "Monitor mode should log startup"
    assert_contains "Следующая проверка через 5с" "$LAST_OUTPUT" "Monitor mode should respect custom interval"
    return 0
}

test_dns_redirect_stubs() {
    assert_status 0 run_with_env \
        "INTERNET_CHECK_RETRIES=1" \
        "PING_SERVERS=1.1.1.1" \
        "MOCK_PING_FAIL_COUNT=1" \
        "PING_SUCCESS_HOSTS=1.1.1.1" \
        "INTERNET_HTTP_PROBES=" \
        "MOCK_CURL_HTTP_CODE=000" \
        "MOCK_CURL_CAPTIVE=success" \
        "MOCK_CURL_CAPTIVE_URL=http://captive.test/login" \
        "CAPTIVE_CHECK_URLS=http://captive.test/status" \
        "MOCK_NSLOOKUP_IPV4=10.10.10.10" \
        "MOCK_SLEEP_FAST=1" \
        "REQUESTED_FIREWALL_BACKEND=iptables" \
        -- -o
    log_content=$(cat "$TEST_LOG" 2> /dev/null || printf '')
    assert_contains "dnsmasq reload" "$log_content" "dnsmasq reload should be invoked"
    assert_contains "iptables -t nat -A CAPTIVE_HTTP_REDIRECT" "$log_content" "HTTP redirect rule should be added"
    assert_contains "iptables -t nat -A CAPTIVE_DNS_REDIRECT" "$log_content" "DNS redirect chain should be populated"
    return 0
}

test_cleanup() {
    assert_status 0 run_with_env \
        "INTERNET_CHECK_RETRIES=1" \
        "PING_SERVERS=1.1.1.1" \
        "MOCK_PING_FAIL_COUNT=1" \
        "PING_SUCCESS_HOSTS=1.1.1.1" \
        "INTERNET_HTTP_PROBES=" \
        "MOCK_CURL_HTTP_CODE=000" \
        "MOCK_CURL_CAPTIVE=success" \
        "MOCK_CURL_CAPTIVE_URL=http://captive.test/login" \
        "CAPTIVE_CHECK_URLS=http://captive.test/status" \
        "MOCK_NSLOOKUP_IPV4=10.10.10.10" \
        "MOCK_SLEEP_FAST=1" \
        "REQUESTED_FIREWALL_BACKEND=iptables" \
        -- -o
    log_content=$(cat "$TEST_LOG" 2> /dev/null || printf '')
    assert_contains "iptables -t nat -F CAPTIVE_HTTP_REDIRECT" "$log_content" "Cleanup should flush NAT chain"
    assert_contains "iptables -t nat -X CAPTIVE_HTTP_REDIRECT" "$log_content" "Cleanup should delete NAT chain"
    if [ -f "$DNSMASQ_CONF" ]; then
        fail "dnsmasq intercept configuration should be removed"
    fi
    return 0
}

test_build_ipk_package() {
    feed_dir="$OUT_DIR/feed"
    arch="all_test"
    mkdir -p "$feed_dir"
    build_log="$OUT_DIR/build_ipk.log"
    if ! "$REPO_ROOT/scripts/build_ipk.sh" --feed-root "$feed_dir" --arch "$arch" > "$build_log" 2>&1; then
        cat "$build_log" >&2 2> /dev/null || true
        fail "build_ipk.sh failed"
    fi
    ipk_file=$(find "$feed_dir/$arch" -maxdepth 1 -type f -name '*.ipk' | head -n1)
    [ -n "$ipk_file" ] || fail "No .ipk produced under $feed_dir/$arch"
    data_listing=$(ar p "$ipk_file" data.tar.gz | tar -tzf -)
    assert_contains "usr/sbin/openwrt_captive_monitor" "$data_listing" "Executable missing from package payload"
    assert_contains "etc/init.d/captive-monitor" "$data_listing" "Init script missing from package payload"
    assert_contains "etc/uci-defaults/99-captive-monitor" "$data_listing" "uci-defaults missing from package payload"
    assert_contains "etc/config/captive-monitor" "$data_listing" "Config file missing from package payload"
    tmp_control_dir=$(mktemp -d)
    ar p "$ipk_file" control.tar.gz | tar -C "$tmp_control_dir" -xz
    control_contents=$(cat "$tmp_control_dir/control" 2> /dev/null || printf '')
    rm -rf "$tmp_control_dir"
    pkg_version=$(parse_make_var "PKG_VERSION")
    pkg_release=$(parse_make_var "PKG_RELEASE")
    assert_contains "Package: openwrt-captive-monitor" "$control_contents" "control file missing package name"
    assert_contains "Version: ${pkg_version}-${pkg_release}" "$control_contents" "control file missing version string"
    assert_contains "Depends: dnsmasq, curl" "$control_contents" "control file missing dependencies"
    packages_index="$feed_dir/$arch/Packages"
    packages_body=$(cat "$packages_index" 2> /dev/null || printf '')
    assert_contains "Package: openwrt-captive-monitor" "$packages_body" "Packages index missing package entry"
    assert_contains "Filename: $(basename "$ipk_file")" "$packages_body" "Packages index missing filename entry"
    packages_gz="$feed_dir/$arch/Packages.gz"
    [ -f "$packages_gz" ] || fail "Packages.gz missing under $feed_dir/$arch"
    if ! gzip -t "$packages_gz" > /dev/null 2>&1; then
        fail "Packages.gz integrity check failed"
    fi
    packages_gz_body=$(gzip -cd "$packages_gz" 2> /dev/null || printf '')
    [ -n "$packages_gz_body" ] || fail "Packages.gz decompressed to empty content"
    if [ "$packages_body" != "$packages_gz_body" ]; then
        fail "Packages.gz content differs from Packages"
    fi
    return 0
}

test_build_ipk_detects_archiver_failure() {
    feed_dir="$OUT_DIR/feed_missing"
    arch="all_fail"
    mkdir -p "$feed_dir"
    mock_bin="$OUT_DIR/mock-bin"
    mkdir -p "$mock_bin"
    cat <<'EOF' > "$mock_bin/ar"
#!/bin/sh
exit 0
EOF
    chmod +x "$mock_bin/ar"
    build_log="$OUT_DIR/build_ipk_missing.log"
    if PATH="$mock_bin:$PATH" "$REPO_ROOT/scripts/build_ipk.sh" --feed-root "$feed_dir" --arch "$arch" > "$build_log" 2>&1; then
        cat "$build_log" >&2 2> /dev/null || true
        fail "build_ipk.sh succeeded even though ar produced no archive"
    fi
    log_contents=$(cat "$build_log" 2> /dev/null || printf '')
    assert_contains "error: expected package archive" "$log_contents" "build_ipk.sh should detect missing archive"
    return 0
}

main() {
    run_test test_opts_parsing
    run_test test_mode_switch
    run_test test_dns_redirect_stubs
    run_test test_cleanup
    run_test test_build_ipk_package
    run_test test_build_ipk_detects_archiver_failure
    printf 'All tests passed (%d/%d)\n' "$PASSED_TESTS" "$TOTAL_TESTS"
}

main
