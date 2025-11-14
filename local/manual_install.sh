#!/bin/bash

# Configuration (use environment variables)
REMOTE="${SSH_REMOTE:-root@192.168.1.1}"
PACKAGE_NAME="${PACKAGE_NAME:-openwrt-captive-monitor_1.0.1-1_all.ipk}"
LOCAL_PACKAGE="${PACKAGE_PATH:-./dist/opkg/all}/${PACKAGE_NAME}"
REMOTE_TEMP_DIR="/tmp/captive_test_manual"

# Function to execute remote commands
remote_exec() {
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$REMOTE" "$1"
}

# Function to copy files to remote
remote_copy() {
    local src="$1"
    local dst="$2"
    scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$src" "$REMOTE:$dst"
}

echo "[1/5] Preparing remote device..."
remote_exec "uname -a"
remote_exec "which opkg || echo 'opkg not found'"
remote_exec "mkdir -p $REMOTE_TEMP_DIR"

# Copy the package to the device
echo "[2/5] Copying package to device..."
remote_copy "$LOCAL_PACKAGE" "$REMOTE_TEMP_DIR/"

# Verify the package on the remote device
echo "[3/5] Verifying package on remote device..."
remote_exec "file ${REMOTE_TEMP_DIR}/${PACKAGE_NAME}"
remote_exec "ls -la ${REMOTE_TEMP_DIR}/"

# Try to install the package
echo "[4/5] Installing package..."
remote_exec "opkg install --force-overwrite --force-downgrade ${REMOTE_TEMP_DIR}/${PACKAGE_NAME} || echo 'Installation failed'"

# Check if the package was installed
echo "[5/5] Verifying installation..."
remote_exec "opkg list-installed | grep captive-monitor || echo 'Package not installed'"
remote_exec "which captive-monitor || echo 'captive-monitor not in PATH'"
remote_exec "find / -name 'captive-monitor' 2>/dev/null || echo 'captive-monitor not found in system'"

echo "\nInstallation process completed. Check the output above for any errors."
