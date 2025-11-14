#!/bin/bash

# Verification script for CodeQL SARIF generation fix
# This script checks that the CodeQL workflow is properly configured

echo "=== CodeQL Configuration Verification ==="

# Check 1: Verify codeql.yml exists and has correct structure
echo "1. Checking codeql.yml workflow file..."
if [ ! -f ".github/workflows/codeql.yml" ]; then
    echo "❌ ERROR: .github/workflows/codeql.yml not found"
    exit 1
fi

# Check 2: Verify language is set to shell only
echo "2. Checking language configuration..."
if grep -q "language: \['shell'\]" .github/workflows/codeql.yml; then
    echo "✅ Language correctly set to shell only"
else
    echo "❌ ERROR: Language not correctly configured"
    exit 1
fi

# Check 3: Verify upload: false is removed from analyze step
echo "3. Checking analyze step configuration..."
if grep -q "upload: false" .github/workflows/codeql.yml; then
    echo "❌ ERROR: upload: false still present in analyze step"
    exit 1
else
    echo "✅ upload: false removed from analyze step"
fi

# Check 4: Verify separate upload-sarif step is removed
echo "4. Checking for separate upload-sarif step..."
if grep -q "upload-sarif" .github/workflows/codeql.yml; then
    echo "❌ ERROR: Separate upload-sarif step still present"
    exit 1
else
    echo "✅ Separate upload-sarif step removed"
fi

# Check 5: Verify diagnostic steps are added
echo "5. Checking diagnostic steps..."
if grep -q "Debug - List shell files before analysis" .github/workflows/codeql.yml; then
    echo "✅ Shell files diagnostic step added"
else
    echo "❌ ERROR: Shell files diagnostic step missing"
    exit 1
fi

if grep -q "Debug - Check CodeQL database" .github/workflows/codeql.yml; then
    echo "✅ CodeQL database diagnostic step added"
else
    echo "❌ ERROR: CodeQL database diagnostic step missing"
    exit 1
fi

if grep -q "Debug - Verify SARIF generation" .github/workflows/codeql.yml; then
    echo "✅ SARIF verification diagnostic step added"
else
    echo "❌ ERROR: SARIF verification diagnostic step missing"
    exit 1
fi

# Check 6: Verify paths-ignore includes appropriate patterns
echo "6. Checking paths-ignore configuration..."
if grep -q "'\*.yml'" .github/workflows/codeql.yml && grep -q "'\*.yaml'" .github/workflows/codeql.yml; then
    echo "✅ YAML files excluded from analysis"
else
    echo "❌ ERROR: YAML files not properly excluded"
    exit 1
fi

# Check 7: Count shell scripts (excluding .github directory)
echo "7. Counting shell scripts for analysis..."
shell_count=$(find . -name "*.sh" -type f | grep -v ".github" | wc -l)
if [ "$shell_count" -gt 0 ]; then
    echo "✅ Found $shell_count shell scripts for analysis"
else
    echo "❌ ERROR: No shell scripts found for analysis"
    exit 1
fi

# Check 8: Verify analyze@v4 is being used
echo "8. Checking CodeQL action versions..."
if grep -q "github/codeql-action/analyze@v4" .github/workflows/codeql.yml; then
    echo "✅ Using CodeQL analyze action v4"
else
    echo "❌ ERROR: Not using CodeQL analyze action v4"
    exit 1
fi

echo ""
echo "=== Summary ==="
echo "✅ All CodeQL configuration checks passed"
echo "✅ Workflow should now generate SARIF files correctly"
echo "✅ Diagnostic steps will help troubleshoot any remaining issues"
echo ""
echo "Next steps:"
echo "1. Commit and push these changes"
echo "2. Run the workflow to verify SARIF generation"
echo "3. Check the diagnostic output in the workflow logs"
echo "4. Verify SARIF files appear in the Security tab"