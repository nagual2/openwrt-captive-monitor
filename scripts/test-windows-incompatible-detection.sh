#!/bin/bash

# Test script for Windows-incompatible character detection
# This script tests the regex pattern used to identify problematic characters

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Windows-incompatible characters pattern (same as in main script)
# Use a character class approach
has_windows_incompatible_chars() {
    local name="$1"
    # Check for any Windows-incompatible characters using a simple loop
    local incompatible=':"*?<>|;,.!@#$%^&+=~`'"'"'\()[]{}'
    
    for (( i=0; i<${#name}; i++ )); do
        local char="${name:$i:1}"
        if [[ "$incompatible" == *"$char"* ]]; then
            return 0
        fi
    done
    
    return 1
}

echo -e "${YELLOW}Testing Windows-Incompatible Character Detection${NC}"
echo ""

# Test cases
test_cases=(
    # Should be detected as incompatible
    "artifact:name" "artifact*name" "artifact?name" 'artifact"name' 
    "artifact<name" "artifact>name" "artifact|name" "artifact;name"
    "artifact,name" "artifact.name" "artifact!name" "artifact@name"
    "artifact#name" "artifact\$name" "artifact%name" "artifact^name"
    "artifact&name" "artifact+name" "artifact=name" "artifact~name"
    "artifact\`name" "artifact'name" "artifact\\name" "artifact(name"
    "artifact)name" "artifact[name" "artifact]name" "artifact{name"
    "artifact}name"
    
    # Should be detected as compatible (no Windows-incompatible chars)
    "artifact-name" "artifact_name" "artifact123" "ArtifactName"
    "artifact-123_name" "simple-artifact" "test_results"
)

echo -e "${YELLOW}Testing incompatible characters:${NC}"
echo ""

incompatible_count=0
compatible_count=0

# Test cases that should be detected as incompatible
for test_name in "artifact:name" "artifact*name" "artifact?name" "artifact\"name" \
    "artifact<name" "artifact>name" "artifact|name" "artifact;name" \
    "artifact,name" "artifact.name" "artifact!name" "artifact@name" \
    "artifact#name" "artifact\$name" "artifact%name" "artifact^name" \
    "artifact&name" "artifact+name" "artifact=name" "artifact~name" \
    "artifact\`name" "artifact'name" "artifact\\\\name" "artifact(name" \
    "artifact)name" "artifact[name" "artifact]name" "artifact{name" \
    "artifact}name"; do
    
    if has_windows_incompatible_chars "$test_name"; then
        echo -e "${GREEN}✓ Correctly detected: ${test_name}${NC}"
        incompatible_count=$((incompatible_count + 1))
    else
        echo -e "${RED}✗ Failed to detect: ${test_name}${NC}"
    fi
done

echo ""
echo -e "${YELLOW}Testing compatible characters (no Windows-incompatible chars):${NC}"
echo ""

# Test cases that should be detected as compatible
for test_name in "artifact-name" "artifact_name" "artifact123" "ArtifactName" \
    "artifact-123_name" "simple-artifact" "test_results"; do
    
    if ! has_windows_incompatible_chars "$test_name"; then
        echo -e "${GREEN}✓ Correctly allowed: ${test_name}${NC}"
        compatible_count=$((compatible_count + 1))
    else
        echo -e "${RED}✗ Incorrectly flagged: ${test_name}${NC}"
    fi
done

echo ""
echo -e "${YELLOW}Test Summary:${NC}"
echo "Incompatible characters detected: $incompatible_count/29"
echo "Compatible characters allowed: $compatible_count/7"

if [ $incompatible_count -eq 29 ] && [ $compatible_count -eq 7 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi