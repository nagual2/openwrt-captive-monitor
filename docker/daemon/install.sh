#!/bin/bash
set -euo pipefail

# Install Captive Portal Daemon via Docker
# Usage: bash docker/daemon/install.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Captive Portal Daemon - Docker Install ==="

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is not installed"
    echo "Install: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Create .env if not exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "Created .env from .env.example"
    echo "Edit $SCRIPT_DIR/.env to configure credentials"
fi

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Build and start
echo "Building Docker image..."
cd "$SCRIPT_DIR"

if docker compose version >/dev/null 2>&1; then
    docker compose build
    docker compose up -d
else
    docker-compose build
    docker-compose up -d
fi

echo ""
echo "=== Installation complete ==="
echo "Check status: docker compose ps"
echo "View logs:    docker compose logs -f"
echo "Stop:         docker compose down"
