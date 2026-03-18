# OpenWrt Captive Monitor - Developer Convenience Makefile
# This is NOT the OpenWrt package Makefile. For package building, see:
# - package/openwrt-captive-monitor/Makefile (OpenWrt SDK builds)
# - scripts/build_deb_docker.sh (Docker-based deb package)

.PHONY: help test lint docker-build docker-run docker-stop clean

help:
	@echo "OpenWrt Captive Monitor - Developer Tools"
	@echo ""
	@echo "Available targets:"
	@echo "  help         - Show this help message"
	@echo "  test         - Run test suite"
	@echo "  lint         - Run shellcheck on shell scripts"
	@echo "  docker-build - Build Docker daemon image"
	@echo "  docker-run   - Run Docker daemon container"
	@echo "  docker-stop  - Stop Docker daemon container"
	@echo "  deb          - Build Docker-based deb package"
	@echo "  clean        - Clean build artifacts"
	@echo ""
	@echo "See README.md and docs/ for detailed documentation."

test:
	@echo "Running test suite..."
	@if command -v busybox >/dev/null 2>&1; then \
		busybox ash tests/run.sh; \
	else \
		sh tests/run.sh; \
	fi

lint:
	@command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck is required"; exit 1; }
	@echo "Running shellcheck..."
	@shellcheck package/openwrt-captive-monitor/files/usr/sbin/auth_conn4.sh
	@shellcheck scripts/*.sh
	@echo "Shellcheck passed!"

docker-build:
	@echo "Building Docker daemon image..."
	docker build -f docker/daemon/Dockerfile -t captive-portal-daemon:latest .
	@echo "Done. Image: captive-portal-daemon:latest"

docker-run:
	@echo "Starting Docker daemon..."
	docker run -d \
		--name captive-daemon \
		--network host \
		--restart unless-stopped \
		-v /var/log/captive-daemon:/var/log \
		-v /dev/shm:/dev/shm \
		-e CHECK_INTERVAL=60 \
		captive-portal-daemon:latest
	@echo "Daemon started. Logs: docker logs captive-daemon -f"

docker-stop:
	@echo "Stopping Docker daemon..."
	-docker stop captive-daemon
	-docker rm captive-daemon
	@echo "Daemon stopped."

deb:
	@echo "Building Docker-based deb package..."
	bash scripts/build_deb_docker.sh

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/
	@rm -rf tmp/
	@rm -rf .tmp/
	@rm -f *.log
	@echo "Clean completed!"
