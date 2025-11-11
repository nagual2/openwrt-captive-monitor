# OpenWrt Captive Monitor Package Makefile
# This Makefile provides integration with OpenWrt build system

# Package metadata
PKG_NAME := openwrt-captive-monitor
PKG_VERSION := $(shell cat VERSION 2>/dev/null || echo "1.0.6")
PKG_RELEASE := 1
PKG_LICENSE := MIT
PKG_LICENSE_FILES := LICENSE
PKG_MAINTAINER := OpenWrt Captive Monitor Team <https://github.com/nagual2/openwrt-captive-monitor>
PKG_ARCH := all

# Build system integration
TOPDIR ?= $(CURDIR)

# Only include OpenWrt build system files if we're in an OpenWrt environment
ifneq ($(wildcard $(TOPDIR)/rules.mk),)
include $(TOPDIR)/rules.mk
# Only include package.mk if INCLUDE_DIR is defined (OpenWrt environment)
ifdef INCLUDE_DIR
include $(INCLUDE_DIR)/package.mk
OPENWRT_ENV := 1
else
OPENWRT_ENV := 0
endif
else
OPENWRT_ENV := 0
endif

# Package definition
define Package/openwrt-captive-monitor
  SECTION := net
  CATEGORY := Network
  SUBMENU := Captive Portals
  TITLE := Captive portal connectivity monitor and auto-redirect helper
  DEPENDS := +dnsmasq +curl
  URL := https://github.com/nagual2/openwrt-captive-monitor
  MAINTAINER := $(PKG_MAINTAINER)
endef

# Package description
define Package/openwrt-captive-monitor/description
 openwrt-captive-monitor detects captive portals, applies DNS/HTTP redirects so
 authenticated clients can sign in, and restores normal routing once internet
 access is available again.
endef

# Build preparation
define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) ./package/openwrt-captive-monitor/files/* $(PKG_BUILD_DIR)/
endef

# Build compilation (no compilation needed for shell scripts)
define Build/Compile
	# No compilation needed - this is a shell script package
	# Ensure proper permissions on executable files
	chmod 0755 $(PKG_BUILD_DIR)/usr/sbin/openwrt_captive_monitor || true
	chmod 0755 $(PKG_BUILD_DIR)/etc/init.d/captive-monitor || true
	chmod 0755 $(PKG_BUILD_DIR)/etc/uci-defaults/99-captive-monitor || true
endef

# Package installation
define Package/openwrt-captive-monitor/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/usr/sbin/openwrt_captive_monitor $(1)/usr/sbin/
	
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/init.d/captive-monitor $(1)/etc/init.d/captive-monitor
	
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/etc/config/captive-monitor $(1)/etc/config/captive-monitor
	
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/uci-defaults/99-captive-monitor $(1)/etc/uci-defaults/99-captive-monitor
	
	$(INSTALL_DIR) $(1)/usr/share/licenses/openwrt-captive-monitor
	$(INSTALL_DATA) ./LICENSE $(1)/usr/share/licenses/openwrt-captive-monitor/
endef

# Post-installation script
define Package/openwrt-captive-monitor/postinst
#!/bin/sh
if [ -z "$$IPKG_INSTROOT" ]; then
	if [ -x /etc/uci-defaults/99-captive-monitor ]; then
		/etc/uci-defaults/99-captive-monitor || true
	fi
	/etc/init.d/captive-monitor disable >/dev/null 2>&1 || true
	/etc/init.d/captive-monitor stop >/dev/null 2>&1 || true
fi
exit 0
endef

# Pre-removal script
define Package/openwrt-captive-monitor/prerm
#!/bin/sh
if [ -z "$$IPKG_INSTROOT" ]; then
	/etc/init.d/captive-monitor disable >/dev/null 2>&1 || true
	/etc/init.d/captive-monitor stop >/dev/null 2>&1 || true
fi
exit 0
endef

# Post-removal script
define Package/openwrt-captive-monitor/postrm
#!/bin/sh
if [ -z "$$IPKG_INSTROOT" ]; then
	/etc/init.d/captive-monitor stop >/dev/null 2>&1 || true
fi
exit 0
endef

# Build the package (only in OpenWrt environment)
ifeq ($(OPENWRT_ENV),1)
$(eval $(call BuildPackage,openwrt-captive-monitor))
endif

# Helper targets for development
.PHONY: clean-build distclean help

clean-build:
	rm -rf $(PKG_BUILD_DIR)
	rm -rf bin/*
	rm -rf tmp/*

distclean: clean-build
	rm -rf dl/
	rm -rf feeds/
	rm -rf staging_dir/
	rm -rf build_dir/
	rm -rf toolchain/

help:
	@echo "OpenWrt Captive Monitor Package Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  clean-build    - Clean build artifacts"
	@echo "  distclean      - Clean all build files and caches"
	@echo "  help           - Show this help message"
	@echo ""
	@echo "Package variables:"
	@echo "  PKG_NAME      = $(PKG_NAME)"
	@echo "  PKG_VERSION   = $(PKG_VERSION)"
	@echo "  PKG_RELEASE   = $(PKG_RELEASE)"
	@echo "  PKG_ARCH      = $(PKG_ARCH)"
	@echo ""
	@echo "OpenWrt integration targets (use within OpenWrt SDK):"
	@echo "  package/$(PKG_NAME)/compile    - Compile the package"
	@echo "  package/$(PKG_NAME)/install    - Install the package"
	@echo "  package/$(PKG_NAME)/clean       - Clean package build"