include $(TOPDIR)/rules.mk

PKG_NAME:=dual-socks-proxy
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

PKG_MAINTAINER:=Dwarh-Cruiser <dwarh@example.com>
PKG_LICENSE:=GPL-2.0

include $(INCLUDE_DIR)/package.mk

define Package/dual-socks-proxy
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Dual SOCKS5 Proxy for OpenWrt
  DEPENDS:=+microsocks +uci
  PKGARCH:=all
endef

define Package/dual-socks-proxy/description
  Dual SOCKS5 proxy for routing traffic through two WAN interfaces.
  Provides transparent SOCKS proxies on high ports (11080, 11081)
  for primary and secondary internet connections.
  POSIX sh compatible for all OpenWrt architectures.
endef

define Package/dual-socks-proxy/conffiles
/etc/config/dual-socks-proxy
endef

define Build/Compile
endef

define Package/dual-socks-proxy/install
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/dual-socks-proxy.init $(1)/etc/init.d/dual-socks-proxy
	
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/dual-socks-proxy.config $(1)/etc/config/dual-socks-proxy
	
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) ./files/dual-socks-proxy.sh $(1)/usr/bin/dual-socks-proxy
endef

define Package/dual-socks-proxy/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	echo "Enabling dual-socks-proxy on boot..."
	/etc/init.d/dual-socks-proxy enable
	
	echo ""
	echo "Dual SOCKS Proxy installed successfully!"
	echo ""
	echo "Usage:"
	echo "  /etc/init.d/dual-socks-proxy start   - Start proxies"
	echo "  /etc/init.d/dual-socks-proxy stop    - Stop proxies"
	echo "  /etc/init.d/dual-socks-proxy status  - Check status"
	echo ""
	echo "Configuration:"
	echo "  Edit /etc/config/dual-socks-proxy to change ports/interfaces"
	echo ""
	echo "Dependencies:"
	echo "  opkg update && opkg install microsocks"
	echo ""
fi
exit 0
endef

define Package/dual-socks-proxy/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	/etc/init.d/dual-socks-proxy stop
	/etc/init.d/dual-socks-proxy disable
fi
exit 0
endef

$(eval $(call BuildPackage,dual-socks-proxy))
