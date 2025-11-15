#!/bin/bash

# Demonstration script for Windows-incompatible artifact detection
# This script shows how to detection logic works with sample artifact names

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Import detection function directly (without running main script)
has_windows_incompatible_chars() {
    local name="$1"
    # Check for common Windows-incompatible characters
    if [[ "$name" == *":"* ]] || [[ "$name" == *"*"* ]] || [[ "$name" == *"?"* ]] || [[ "$name" == *"<"* ]] || \
       [[ "$name" == *">"* ]] || [[ "$name" == *"|"* ]] || [[ "$name" == *";"* ]] || \
       [[ "$name" == *","* ]] || [[ "$name" == *"."* ]] || [[ "$name" == *"!"* ]] || [[ "$name" == *"@"* ]] || \
       [[ "$name" == *"#"* ]] || [[ "$name" == *"%"* ]] || [[ "$name" == *"^"* ]] || \
       [[ "$name" == *"&"* ]] || [[ "$name" == *"+"* ]] || [[ "$name" == *"="* ]] || \
       [[ "$name" == *"("* ]] || [[ "$name" == *")"* ]] || [[ "$name" == *"["* ]] || \
       [[ "$name" == *"]"* ]] || [[ "$name" == *"{"* ]] || [[ "$name" == *"}"* ]]; then
        return 0
    else
        return 1
    fi
}

echo -e "${BLUE}=== Windows-Incompatible Artifact Detection Demo ===${NC}"
echo ""

# Sample artifact names that might exist in repository
sample_artifacts=(
    # Current artifacts from workflows
    "test-results"                    # From ci.yml (contains .)
    "ipk-package"                     # From build-simple.yml (compatible)
    "openwrt-package-build-v1.2.3"    # From tag-build-release.yml (contains .)
    
    # Examples of problematic artifacts
    "artifact:name"                   # Contains :
    "build(v1.2.3)"                  # Contains ()
    "package@latest"                  # Contains @
    "release#1"                      # Contains #
    "test-results-2023-12-01"         # Contains .
    "build[debug]"                    # Contains []
    "deploy-staging|prod"             # Contains |
    "version=1.0.0"                  # Contains =
    "temp&build"                      # Contains &
    "backup+old"                     # Contains +
    "config~backup"                   # Contains ~
    "exclamation!mark"                # Contains !
    "percent%sign"                    # Contains %
    "caret^symbol"                    # Contains ^
    "dollar-amount"                   # Contains $
    "less<than"                       # Contains <
    "greater>than"                    # Contains >
    "semicolon;test"                  # Contains ;
    "comma,separated"                 # Contains ,
    "wildcard*test"                   # Contains *
    "question?mark"                   # Contains ?
    
    # Compatible examples
    "build-v1-2-3"                   # Compatible
    "package_latest"                  # Compatible
    "release-1"                       # Compatible
    "test_results"                    # Compatible
    "artifact_name"                   # Compatible
    "simple-artifact"                 # Compatible
)

echo -e "${YELLOW}Analyzing sample artifact names...${NC}"
echo ""

compatible_count=0
incompatible_count=0

for artifact in "${sample_artifacts[@]}"; do
    if has_windows_incompatible_chars "$artifact"; then
        echo -e "${RED}🚫 INCOMPATIBLE: ${artifact}${NC}"
        incompatible_count=$((incompatible_count + 1))
    else
        echo -e "${GREEN}✓ COMPATIBLE: ${artifact}${NC}"
        compatible_count=$((compatible_count + 1))
    fi
done

echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "Total artifacts analyzed: $((compatible_count + incompatible_count))"
echo -e "${GREEN}Compatible artifacts: ${compatible_count}${NC}"
echo -e "${RED}Windows-incompatible artifacts: ${incompatible_count}${NC}"

if [ $incompatible_count -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}The incompatible artifacts above would be deleted by cleanup script.${NC}"
    echo -e "${YELLOW}Note: The dot (.) character is included as problematic per ticket requirements.${NC}"
    echo -e "${YELLOW}Run './scripts/delete-windows-incompatible-artifacts.sh --dry-run' to check real artifacts.${NC}"
else
    echo ""
    echo -e "${GREEN}All sample artifacts are Windows-compatible!${NC}"
fi

echo ""
echo -e "${BLUE}=== Windows Filename Restrictions ===${NC}"
echo "Windows does not allow these characters in filenames:"
echo "- Punctuation: : * ? \" < > | ; , . ! @ # \$ % ^ & + = ~ \` ' \\"
echo "- Brackets: ( ) [ ] { }"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Test with real artifacts:"
echo "   ./scripts/delete-windows-incompatible-artifacts.sh --dry-run"
echo ""
echo "2. Execute cleanup (if safe):"
echo "   ./scripts/delete-windows-incompatible-artifacts.sh --execute"
echo ""
echo "3. Or use GitHub Actions workflow:"
echo "   Navigate to: Actions → 'Delete Windows-Incompatible Artifacts' → 'Run workflow'"