#!/bin/bash
set -e
set -u
set -o pipefail

# Download OpenWrt SDK with enhanced error handling and diagnostics
# This script is called from Dockerfile during build
#
# Requirements:
# - OPENWRT_VERSION: OpenWrt version (e.g., "23.05.5")
# - SDK_TARGET: Target architecture (e.g., "x86", "ath79")
# - SDK_SUBTARGET: Target subarchitecture (e.g., "64", "generic")

echo "=== OpenWrt SDK Download Script ==="
echo "OpenWrt Version: ${OPENWRT_VERSION}"
echo "Target: ${SDK_TARGET}"
echo "Subtarget: ${SDK_SUBTARGET}"

# Function: Determine MUSL suffix based on architecture
# Returns: _musl, _musl_eabi, or empty string
determine_musl_suffix() {
    local target="$1"

    case "${target}" in
        ipq40xx | ipq806x)
            echo "_musl_eabi"
            ;;
        x86 | ath79 | ramips | mediatek | bcm27xx | rockchip)
            echo "_musl"
            ;;
        *)
            # Default to _musl for unknown architectures
            echo "_musl"
            ;;
    esac
}

# Function: List available SDK files on server for diagnostics
# Parameters: $1 - base URL
list_available_files() {
    local base_url="$1"
    echo ""
    echo "=== Available SDK files on server ==="
    echo "Fetching file list from: ${base_url}"

    if curl -s "${base_url}" | grep -oP 'openwrt-sdk-[^"]+\.tar\.xz' | sort; then
        echo "=== End of available files ==="
    else
        echo "Failed to retrieve file list from server"
    fi
    echo ""
}

# Function: Download file with retry and exponential backoff
# Parameters: $1 - URL, $2 - output file, $3 - max attempts
download_with_retry() {
    local url="$1"
    local output="$2"
    local max_attempts="${3:-15}"
    local attempt=1

    echo "Downloading: ${url}"
    echo "Output file: ${output}"

    while [ ${attempt} -le ${max_attempts} ]; do
        echo "Attempt ${attempt}/${max_attempts}..."

        # Use -C - to continue interrupted downloads
        if curl -fL -C - --retry 3 --retry-delay 5 --retry-all-errors \
            --max-time 3600 --connect-timeout 60 \
            --speed-limit 1000 --speed-time 30 \
            -o "${output}" "${url}"; then
            echo "Download successful!"
            return 0
        fi

        local exit_code=$?
        echo "Download failed with exit code: ${exit_code}"

        if [ ${attempt} -lt ${max_attempts} ]; then
            # Exponential backoff: 2^attempt seconds
            local delay=1
            local i=0
            while [ ${i} -lt ${attempt} ]; do
                delay=$((delay * 2))
                i=$((i + 1))
            done
            # Cap delay at 60 seconds
            if [ ${delay} -gt 60 ]; then
                delay=60
            fi
            echo "Retrying after ${delay} seconds..."
            sleep ${delay}
        else
            echo "ERROR: All ${max_attempts} download attempts exhausted"
            return 1
        fi

        attempt=$((attempt + 1))
    done

    return 1
}

# Function: Verify checksum of downloaded file
# Parameters: $1 - SDK file, $2 - checksums file
verify_checksum() {
    local sdk_file="$1"
    local checksums_file="$2"

    echo "Verifying checksum for: ${sdk_file}"

    if ! grep "${sdk_file}" "${checksums_file}" > /dev/null 2>&1; then
        echo "ERROR: Checksum not found in ${checksums_file}"
        echo "Expected file: ${sdk_file}"
        return 1
    fi

    local expected_sum
    local actual_sum
    expected_sum=$(grep "${sdk_file}" "${checksums_file}" | awk '{print $1}')
    actual_sum=$(sha256sum "${sdk_file}" | awk '{print $1}')

    echo "Expected SHA256: ${expected_sum}"
    echo "Actual SHA256:   ${actual_sum}"

    if [ "${expected_sum}" = "${actual_sum}" ]; then
        echo "Checksum verification: PASSED"
        return 0
    else
        echo "ERROR: Checksum verification FAILED"
        echo "The downloaded file is corrupted or tampered with"
        rm -f "${sdk_file}"
        return 1
    fi
}

# Determine MUSL suffix for the target architecture
MUSL_SUFFIX=$(determine_musl_suffix "${SDK_TARGET}")
echo "MUSL Suffix: ${MUSL_SUFFIX}"

# Construct SDK filename and URLs
SDK_FILE="openwrt-sdk-${OPENWRT_VERSION}-${SDK_TARGET}-${SDK_SUBTARGET}_gcc-12.3.0${MUSL_SUFFIX}.Linux-x86_64.tar.xz"
BASE_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/${SDK_TARGET}/${SDK_SUBTARGET}"
SDK_URL="${BASE_URL}/${SDK_FILE}"
SHA256_URL="${BASE_URL}/sha256sums"

echo "SDK File: ${SDK_FILE}"
echo "Full SDK URL: ${SDK_URL}"

# Download SDK with retry logic
echo ""
echo "=== Downloading SDK ==="
if ! download_with_retry "${SDK_URL}" "${SDK_FILE}" 15; then
    echo ""
    echo "ERROR: Failed to download SDK after all retry attempts"
    echo "URL: ${SDK_URL}"

    # Try to list available files for diagnostics
    list_available_files "${BASE_URL}/"

    echo "Please verify:"
    echo "  1. OpenWrt version is correct: ${OPENWRT_VERSION}"
    echo "  2. Target architecture is correct: ${SDK_TARGET}/${SDK_SUBTARGET}"
    echo "  3. Network connectivity to downloads.openwrt.org"
    exit 1
fi

echo ""
echo "SDK downloaded successfully"
ls -lh "${SDK_FILE}"

# Download checksums
echo ""
echo "=== Downloading checksums ==="
if ! download_with_retry "${SHA256_URL}" "sha256sums" 5; then
    echo "ERROR: Failed to download checksums"
    echo "URL: ${SHA256_URL}"
    exit 1
fi

# Verify checksum
echo ""
echo "=== Verifying checksum ==="
if ! verify_checksum "${SDK_FILE}" "sha256sums"; then
    echo "ERROR: Checksum verification failed"
    exit 1
fi

echo ""
echo "=== SDK Download Complete ==="
