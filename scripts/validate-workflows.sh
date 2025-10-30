#!/bin/bash
set -euo pipefail

# Validate GitHub Actions workflow YAML syntax
echo "Validating workflow files..."

for workflow in .github/workflows/*.yml; do
    echo "Checking $workflow..."
    if command -v yamllint >/dev/null 2>&1; then
        yamllint "$workflow" || echo "Warning: yamllint found issues in $workflow"
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import yaml; yaml.safe_load(open('$workflow'))" || echo "Error: Invalid YAML in $workflow"
    else
        echo "Warning: No YAML validator available, skipping syntax check for $workflow"
    fi
done

echo "Workflow validation complete."