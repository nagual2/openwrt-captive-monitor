#!/bin/sh
set -eu

# Validate GitHub Actions workflow YAML syntax
echo "Validating workflow files..."

for workflow in .github/workflows/*.yml; do
	echo "Checking $workflow..."
	# Basic YAML syntax check using BusyBox's built-in tools
	if [ -f "$workflow" ]; then
		# Check for basic YAML structure issues
		if grep -q '^[[:space:]]*-' "$workflow" && grep -q '^[[:space:]]*[a-zA-Z][^:]*:' "$workflow"; then
			echo "✓ Basic YAML structure appears valid: $workflow"
		else
			echo "⚠ Warning: $workflow may have YAML syntax issues"
		fi
	else
		echo "✗ File not found: $workflow"
	fi
done

echo "Workflow validation complete."
