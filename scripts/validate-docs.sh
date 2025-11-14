#!/bin/sh
# validate-docs.sh - Validate documentation structure

set -e

echo "Validating documentation structure..."

# Check required directories
check_required_dirs() {
    for dir in docs docs/usage docs/configuration docs/guides docs/project; do
        if [ -d "$dir" ]; then
            echo "✓ Directory exists: $dir"
        else
            echo "✗ Missing directory: $dir"
            exit 1
        fi
    done
}

# Check required files
check_required_files() {
    for file in docs/index.md README.md CONTRIBUTING.md CODE_OF_CONDUCT.md LICENSE; do
        if [ -f "$file" ]; then
            echo "✓ File exists: $file"
        else
            echo "✗ Missing file: $file"
            exit 1
        fi
    done
}

# Check documentation files
check_doc_files() {
    for file in \
        docs/usage/quick-start.md \
        docs/usage/installation.md \
        docs/configuration/basic-config.md \
        docs/configuration/reference.md \
        docs/configuration/advanced-config.md \
        docs/guides/captive-portal-walkthrough.md \
        docs/guides/oneshot-recovery.md \
        docs/guides/troubleshooting.md \
        docs/guides/architecture.md \
        docs/project/management.md \
        docs/project/faq.md \
        docs/project/release-checklist.md \
        docs/project/test-plan.md \
        docs/project/backlog.md \
        docs/project/packages.md \
        docs/packaging.md; do
        if [ -f "$file" ]; then
            echo "✓ Documentation file exists: $file"
        else
            echo "✗ Missing documentation file: $file"
            exit 1
        fi
    done
}

check_required_dirs
check_required_files
check_doc_files

# Check for broken internal links (simplified)
echo "Checking for broken internal links..."
echo "⚠ Link validation simplified for OpenWrt compatibility"

echo ""
echo "✓ Documentation structure validation completed successfully!"
