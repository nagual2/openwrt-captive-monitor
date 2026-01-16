include $(TOPDIR)/rules.mk

PKG_NAME:=openwrt-captive-monitor
# Date-based package version aligned with the latest vYYYY.MM.DD.N git tag and root VERSION file.
PKG_VERSION:=2026.01.16.1
# PKG_RELEASE must remain a small integer
PKG_RELEASE:=1

PKG_LICENSE:=MIT
PKG_LICENSE_FILES:=LICENSE
PKG_MAINTAINER:=OpenWrt Captive Monitor Team <https://github.com/nagual2/openwrt-captive-monitor>
PKG_ARCH:=all

include $(INCLUDE_DIR)/package.mk

# Mark this as a script-only package with no configure/compile steps.
define Build/Prepare
endef

define Build/Configure
endef

define Build/Compile
	# Nothing to compile; all content is installed from the ./files tree
endef

define Package/openwrt-captive-monitor
  SECTION:=net
  CATEGORY:=Network
  SUBMENU:=Captive Portals
  TITLE:=Automatic captive portal authentication script (conn4)
  DEPENDS:=+curl
  URL:=https://github.com/nagual2/openwrt-captive-monitor
endef

define Package/openwrt-captive-monitor/description
 openwrt-captive-monitor provides a script to automatically authenticate
 against Conn4 captive portals (e.g. Leonardo Hotels) and maintain the session
 via cron.
endef

define Package/openwrt-captive-monitor/conffiles
/etc/cron.d/auth_conn4
endef

define Package/openwrt-captive-monitor/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/usr/sbin/auth_conn4.sh $(1)/usr/sbin/auth_conn4.sh
	$(INSTALL_DIR) $(1)/etc/cron.d
	$(INSTALL_DATA) ./files/etc/cron.d/auth_conn4 $(1)/etc/cron.d/auth_conn4
	$(INSTALL_DIR) $(1)/usr/share/licenses/$(PKG_NAME)
	$(INSTALL_DATA) ./LICENSE $(1)/usr/share/licenses/$(PKG_NAME)/LICENSE
endef

define Package/openwrt-captive-monitor/postinst
#!/bin/sh
[ -n "$$IPKG_INSTROOT" ] && exit 0
/etc/init.d/cron restart
exit 0
endef

define Package/openwrt-captive-monitor/prerm
#!/bin/sh
[ -n "$$IPKG_INSTROOT" ] && exit 0
exit 0
endef

$(eval $(call BuildPackage,openwrt-captive-monitor))
