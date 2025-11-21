include $(TOPDIR)/rules.mk

PKG_NAME:=openwrt-captive-monitor
# Date-based package version aligned with the latest vYYYY.MM.DD.N git tag and root VERSION file.
PKG_VERSION:=2025.11.21.8
# PKG_RELEASE must remain a small integer; do not encode dates here to avoid double-encoding
# the date component (PKG_VERSION already carries the YYYY.M.D.N value).
PKG_RELEASE:=1

PKG_LICENSE:=MIT
PKG_LICENSE_FILES:=LICENSE
PKG_MAINTAINER:=OpenWrt Captive Monitor Team <https://github.com/nagual2/openwrt-captive-monitor>
PKG_ARCH:=all

include $(INCLUDE_DIR)/package.mk

# Mark this as a script-only package with no configure/compile steps.
define Build/Configure
endef

define Build/Compile
	# Nothing to compile; all content is installed from the ./files tree
endef

define Package/openwrt-captive-monitor
  SECTION:=net
  CATEGORY:=Network
  SUBMENU:=Captive Portals
  TITLE:=Captive portal connectivity monitor and auto-redirect helper
  DEPENDS:=+dnsmasq +curl +iptables
  URL:=https://github.com/nagual2/openwrt-captive-monitor
endef

define Package/openwrt-captive-monitor/description
 openwrt-captive-monitor detects captive portals, applies DNS/HTTP redirects so
 authenticated clients can sign in, and restores normal routing once internet
 access is available again.
endef

define Package/openwrt-captive-monitor/conffiles
/etc/config/captive-monitor
endef

define Package/openwrt-captive-monitor/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/usr/sbin/openwrt_captive_monitor $(1)/usr/sbin/openwrt_captive_monitor
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/etc/init.d/captive-monitor $(1)/etc/init.d/captive-monitor
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/etc/config/captive-monitor $(1)/etc/config/captive-monitor
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-captive-monitor $(1)/etc/uci-defaults/99-captive-monitor
	$(INSTALL_DIR) $(1)/usr/share/licenses/$(PKG_NAME)
	$(INSTALL_DATA) ./LICENSE $(1)/usr/share/licenses/$(PKG_NAME)/LICENSE
endef

define Package/openwrt-captive-monitor/postinst
#!/bin/sh
[ -n "$$IPKG_INSTROOT" ] && exit 0
[ -x /etc/uci-defaults/99-captive-monitor ] && /etc/uci-defaults/99-captive-monitor
exit 0
endef

define Package/openwrt-captive-monitor/prerm
#!/bin/sh
[ -n "$$IPKG_INSTROOT" ] && exit 0
/etc/init.d/captive-monitor stop >/dev/null 2>&1
/etc/init.d/captive-monitor disable >/dev/null 2>&1
exit 0
endef

define Package/openwrt-captive-monitor/postrm
#!/bin/sh
[ -n "$$IPKG_INSTROOT" ] && exit 0
rm -f /tmp/dnsmasq.d/captive_intercept.conf
rm -rf /tmp/captive_httpd
exit 0
endef

$(eval $(call BuildPackage,openwrt-captive-monitor))
