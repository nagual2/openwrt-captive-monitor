#!/bin/bash

# Fix line endings and permissions for all shell scripts
find . -type f -name "*.sh" -not -path "*/mocks/*" -not -path "*/\.*" | while read -r file; do
    echo "Fixing $file"
    # Convert Windows line endings to Unix
    dos2unix "$file" 2> /dev/null || sed -i 's/\r$//' "$file"
    # Ensure executable permissions
    chmod +x "$file"
    # Ensure shebang is present
    if ! head -n 1 "$file" | grep -q '^#!'; then
        echo "Adding shebang to $file"
        sed -i '1i#!/bin/sh' "$file"
    fi
done

# Run shellcheck on all scripts
echo "Running shellcheck..."
find . -type f -name "*.sh" -not -path "*/mocks/*" -not -path "*/\.*" -exec shellcheck {} \;

echo "Running shfmt..."
find . -type f -name "*.sh" -not -path "*/mocks/*" -not -path "*/\.*" -exec shfmt -w -i 4 -ci -sr {} \;
