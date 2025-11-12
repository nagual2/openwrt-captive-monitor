# OpenWrt Captive Monitor - Developer Convenience Makefile
# This is NOT the OpenWrt package Makefile. For package building, see:
# - package/openwrt-captive-monitor/Makefile (OpenWrt SDK builds)
# - scripts/build_ipk.sh (standalone builds without SDK)

.PHONY: help test lint format check clean

help:
	@echo "OpenWrt Captive Monitor - Developer Tools"
	@echo ""
	@echo "Available targets:"
	@echo "  help      - Show this help message"
	@echo "  test      - Run test suite"
	@echo "  lint      - Run all linters (shell, markdown)"
	@echo "  format    - Format shell scripts with shfmt"
	@echo "  check     - Run format check without modifying files"
	@echo "  clean     - Clean build artifacts and temporary files"
	@echo ""
	@echo "Package building:"
	@echo "  scripts/build_ipk.sh               - Build IPK package (standalone)"
	@echo "  make -C <sdk-dir> package/.../compile - Build with OpenWrt SDK"
	@echo ""
	@echo "See README.md and docs/ for detailed documentation."

test:
	@echo "Running test suite..."
	@busybox ash tests/run.sh

lint: lint-shell lint-markdown

lint-shell:
	@command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck is required"; exit 1; }
	@echo "Running shellcheck..."
	@shellcheck package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor
	@shellcheck package/openwrt-captive-monitor/files/etc/init.d/captive-monitor
	@shellcheck package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor
	@shellcheck scripts/*.sh
	@shellcheck tests/run.sh
	@echo "Shellcheck passed!"

lint-markdown:
	@command -v markdownlint >/dev/null 2>&1 || { echo "markdownlint is not installed; skipping"; exit 0; }
	@echo "Running markdownlint..."
	@markdownlint .
	@echo "Markdown lint completed!"

format:
	@command -v shfmt >/dev/null 2>&1 || { echo "shfmt is required"; exit 1; }
	@echo "Formatting shell scripts..."
	@shfmt -w -s -i 4 -ci -sr .
	@echo "Format completed!"

check:
	@command -v shfmt >/dev/null 2>&1 || { echo "shfmt is required"; exit 1; }
	@echo "Checking shell script formatting..."
	@shfmt -d -s -i 4 -ci -sr .
	@echo "Format check completed!"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/
	@rm -rf tmp/
	@rm -rf .tmp/
	@rm -f *.log
	@echo "Clean completed!"
