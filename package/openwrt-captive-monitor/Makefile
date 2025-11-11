include $(TOPDIR)/rules.mk

PKG_NAME:=openwrt-captive-monitor
PKG_VERSION:=1.0.6
PKG_RELEASE:=1

PKG_LICENSE:=MIT
PKG_LICENSE_FILES:=LICENSE
PKG_MAINTAINER:=OpenWrt Captive Monitor Team <https://github.com/nagual2/openwrt-captive-monitor>
PKG_ARCH:=all

include $(INCLUDE_DIR)/package.mk

define Package/openwrt-captive-monitor
  SECTION:=net
  CATEGORY:=Network
  SUBMENU:=Captive Portals
  TITLE:=Captive portal connectivity monitor and auto-redirect helper
  DEPENDS:=+dnsmasq +curl +iptables +nftables +busybox
  URL:=https://github.com/nagual2/openwrt-captive-monitor
  MAINTAINER:=OpenWrt Captive Monitor Team
endef

define Package/openwrt-captive-monitor/description
 openwrt-captive-monitor detects captive portals, applies DNS/HTTP redirects so
 authenticated clients can sign in, and restores normal routing once internet
 access is available again.
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
    $(INSTALL_DIR) $(1)/usr/share/licenses/openwrt-captive-monitor
    $(INSTALL_DATA) ./files/LICENSE $(1)/usr/share/licenses/openwrt-captive-monitor/
endef

define Package/openwrt-captive-monitor/postinst
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    if [ -x /etc/uci-defaults/99-captive-monitor ]; then
        /etc/uci-defaults/99-captive-monitor || true
    fi
    /etc/init.d/captive-monitor disable > /dev/null 2>&1 || true
    /etc/init.d/captive-monitor stop > /dev/null 2>&1 || true
fi
exit 0
endef

define Package/openwrt-captive-monitor/prerm
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor disable > /dev/null 2>&1 || true
    /etc/init.d/captive-monitor stop > /dev/null 2>&1 || true
fi
exit 0
endef

define Package/openwrt-captive-monitor/postrm
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor stop > /dev/null 2>&1 || true
fi
exit 0
endef

$(eval $(call BuildPackage,openwrt-captive-monitor))
