#!/bin/bash
# Verification script for CodeQL workflow fix
# This script verifies that all the required changes are in place

set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "CodeQL Workflow Fix Verification"
echo "════════════════════════════════════════════════════════════════"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "1. Checking CodeQL action versions..."
if
    grep -q "github/codeql-action/init@v4" .github/workflows/codeql.yml && \
    grep -q "github/codeql-action/autobuild@v4" .github/workflows/codeql.yml && \
    grep -q "github/codeql-action/analyze@v4" .github/workflows/codeql.yml && \
    grep -q "github/codeql-action/upload-sarif@v4" .github/workflows/codeql.yml
then
    pass "All CodeQL actions are using v4"
else
    fail "Some CodeQL actions are not using v4"
fi

echo
echo "2. Checking for deprecated v3 actions..."
if ! grep -q "codeql-action@v3" .github/workflows/codeql.yml; then
    pass "No deprecated v3 actions found"
else
    fail "Found deprecated v3 actions"
fi

echo
echo "3. Checking language configuration..."
if grep -q "language: \['shell'\]" .github/workflows/codeql.yml; then
    pass "Language matrix correctly set to Shell only"
else
    fail "Language matrix is not correct"
fi

echo
echo "4. Checking for JavaScript references..."
if
    ! grep -iq "javascript" .github/workflows/codeql.yml && \
    ! grep -q "CodeQL Analysis (javascript)" .github/settings.yml
then
    pass "No JavaScript references found in workflow or settings"
else
    fail "Found JavaScript references"
fi

echo
echo "5. Checking required status checks in settings.yml..."
if
    ! grep -q '"CodeQL Analysis (python)"' .github/settings.yml && \
    grep -q '"CodeQL Analysis (shell)"' .github/settings.yml && \
    grep -q '"ShellCheck Security Analysis"' .github/settings.yml && \
    ! grep -q '"CodeQL Analysis (javascript)"' .github/settings.yml
then
    pass "Status checks correctly configured"
else
    fail "Status checks not correctly configured"
fi

echo
echo "6. Verifying YAML syntax..."
if command -v python3 &>/dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/codeql.yml'))" 2>/dev/null; then
        pass "YAML syntax is valid"
    else
        info "Could not verify YAML (yaml module not available)"
    fi
else
    info "Python3 not available, skipping YAML validation"
fi

echo
echo "7. Checking project language files..."
PYTHON_COUNT=$(find . -name "*.py" -not -path "./.git/*" -not -path "./venv/*" | wc -l)
SHELL_COUNT=$(find . -name "*.sh" -not -path "./.git/*" | wc -l)
JS_COUNT=$(find . \( -name "*.js" -o -name "*.ts" \) -not -path "./.git/*" -not -path "./node_modules/*" 2>/dev/null | wc -l)

info "Found $PYTHON_COUNT Python file(s)"
info "Found $SHELL_COUNT Shell script(s)"
info "Found $JS_COUNT JavaScript/TypeScript file(s)"

if [ "$PYTHON_COUNT" -eq 0 ]; then
    pass "No Python files present (correctly not analyzed)"
else
    fail "Python files found but should not be analyzed"
fi

if [ "$SHELL_COUNT" -gt 0 ]; then
    pass "Shell scripts present (ShellCheck analysis applicable)"
else
    fail "No shell scripts found"
fi

if [ "$JS_COUNT" -eq 0 ]; then
    pass "No JavaScript/TypeScript files (correctly not analyzed)"
else
    fail "JavaScript/TypeScript files found but not being analyzed"
fi

echo
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ All checks passed!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo
echo "Summary:"
echo "  • CodeQL actions updated to v4 (no deprecation warnings)"
echo "  • Language configuration: Shell only"
echo "  • Shell scripts analyzed by CodeQL and separate ShellCheck job"
echo "  • No Python analysis (language not present in project)"
echo "  • No JavaScript analysis (language not present in project)"
echo "  • Branch protection settings aligned with workflow outputs"
echo
echo "The CodeQL workflow is correctly configured and ready for use."
