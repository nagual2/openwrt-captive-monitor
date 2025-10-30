#!/bin/bash
# validate-docs.sh - Validate documentation structure

set -e

echo "Validating documentation structure..."

# Check required directories
REQUIRED_DIRS=(
    "docs"
    "docs/usage"
    "docs/configuration"
    "docs/guides"
    "docs/project"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ Directory exists: $dir"
    else
        echo "✗ Missing directory: $dir"
        exit 1
    fi
done

# Check required files
REQUIRED_FILES=(
    "docs/index.md"
    "mkdocs.yml"
    "README.md"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "LICENSE"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ File exists: $file"
    else
        echo "✗ Missing file: $file"
        exit 1
    fi
done

# Check documentation files
DOC_FILES=(
    "docs/usage/quick-start.md"
    "docs/usage/installation.md"
    "docs/configuration/basic-config.md"
    "docs/configuration/reference.md"
    "docs/configuration/advanced-config.md"
    "docs/guides/captive-portal-walkthrough.md"
    "docs/guides/oneshot-recovery.md"
    "docs/guides/troubleshooting.md"
    "docs/guides/architecture.md"
    "docs/project/management.md"
    "docs/project/faq.md"
    "docs/project/release-checklist.md"
    "docs/project/test-plan.md"
    "docs/project/backlog.md"
    "docs/project/packages.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ Documentation file exists: $file"
    else
        echo "✗ Missing documentation file: $file"
        exit 1
    fi
done

# Check mkdocs.yml syntax
if command -v python3 >/dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('mkdocs.yml'))" 2>/dev/null; then
        echo "✓ mkdocs.yml syntax is valid"
    else
        echo "✗ mkdocs.yml has syntax errors"
        exit 1
    fi
else
    echo "⚠ Python3 not available, skipping mkdocs.yml validation"
fi

# Check for broken internal links
echo "Checking for broken internal links..."
if command -v find >/dev/null && command -v grep >/dev/null; then
    BROKEN_LINKS=0
    
    # Find all markdown files and check for broken internal links
    find docs -name "*.md" -exec grep -H '\[.*\](.*\.md)' {} \; | while read line; do
        file=$(echo "$line" | cut -d: -f1)
        links=$(echo "$line" | grep -o '\[.*\]([^)]*\.md)' | sed 's/.*](\(.*\))/\1/')
        
        for link in $links; do
            if [[ "$link" == http* ]]; then
                continue  # Skip external links
            fi
            
            # Convert relative links to absolute paths
            if [[ "$link" == /* ]]; then
                target="$link"
            else
                target="$(dirname "$file")/$link"
            fi
            
            # Normalize path
            target=$(realpath -m "$target" 2>/dev/null || echo "$target")
            
            if [ ! -f "$target" ] && [ ! -d "$target" ]; then
                echo "✗ Broken link: $file -> $link (target: $target)"
                BROKEN_LINKS=$((BROKEN_LINKS + 1))
            fi
        done
    done
    
    if [ $BROKEN_LINKS -eq 0 ]; then
        echo "✓ No broken internal links found"
    else
        echo "✗ Found $BROKEN_LINKS broken internal links"
        exit 1
    fi
else
    echo "⚠ find/grep not available, skipping link validation"
fi

echo ""
echo "✓ Documentation structure validation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Install MkDocs dependencies: pip install -r requirements.txt"
echo "2. Build documentation: mkdocs build"
echo "3. Serve locally: mkdocs serve"
echo "4. Deploy to GitHub Pages when ready"