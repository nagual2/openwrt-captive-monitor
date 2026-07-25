#!/usr/bin/env python3
"""
Dual-channel captive portal authorization for conn4.com
- Checks both WAN channels alternately
- SOCKS proxy for traffic management
- Optimized for TrueNAS-dev environment
"""

import sys
import os
import time
import logging
import fcntl
import pickle
import json
import subprocess
import socket
import socks  # PySocks library
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conn4_auth_lib import WbsTokenBuilder

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium")
    sys.exit(1)

try:
    import socks as pysocks
except ImportError:
    print("❌ PySocks не установлен!")
    print("Установите: pip3 install pysocks")
    sys.exit(1)

# Paths
RUNTIME_DIR = os.environ.get("RUNTIME_DIR", f"/run/user/{os.getuid()}")
if not os.path.exists(RUNTIME_DIR):
    RUNTIME_DIR = "/tmp"

LOG_FILE = os.environ.get("LOG_FILE", os.path.join(RUNTIME_DIR, "captive_dual.log"))
LOCK_FILE = os.environ.get("LOCK_FILE", os.path.join(RUNTIME_DIR, "captive_dual.lock"))
COOKIES_FILE = os.environ.get("COOKIES_FILE", os.path.join(RUNTIME_DIR, "captive_dual_cookies.pkl"))
COOKIES_META_FILE = os.environ.get("COOKIES_META_FILE", os.path.join(RUNTIME_DIR, "captive_dual_cookies_meta.json"))

# Cookie TTL settings (seconds)
COOKIE_TTL = 3600  # 1 hour
COOKIE_REFRESH_BEFORE = 300  # 5 minutes before expiration

# Dual SOCKS configuration
SOCKS_CONFIG = {
    "primary": {
        "name": "primary",
        "host": "192.168.35.1",  # OpenWrt LAN IP
        "port": 11080,
        "wan_iface": "phy1-sta0",
        "check_url": "http://www.msftconnecttest.com/connecttest.txt",
    },
    "secondary": {
        "name": "secondary", 
        "host": "192.168.35.1",  # OpenWrt LAN IP
        "port": 11081,
        "wan_iface": "wan",
        "check_url": "http://www.msftconnecttest.com/connecttest.txt",
    }
}

# Logging setup with custom formatter
class ChannelFormatter(logging.Formatter):
    """Formatter that handles missing channel attribute"""
    def format(self, record):
        if not hasattr(record, 'channel'):
            record.channel = 'system'
        return super().format(record)

# Setup logging
handler_file = logging.FileHandler(LOG_FILE, mode='a')
handler_stream = logging.StreamHandler(sys.stdout)
formatter = ChannelFormatter('%(asctime)s - %(levelname)s - [%(channel)s] %(message)s')
handler_file.setFormatter(formatter)
handler_stream.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler_file)
logger.addHandler(handler_stream)


class ChannelFilter(logging.Filter):
    """Filter to add channel context to log records"""
    def __init__(self, channel="unknown"):
        super().__init__()
        self.channel = channel
    
    def filter(self, record):
        record.channel = self.channel
        return True


class SingleInstanceLock:
    """Lock to prevent multiple script instances"""
    
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.fp = None
    
    def __enter__(self):
        try:
            self.fp = open(self.lock_file, 'w')
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            return self
        except IOError:
            logger.info("Script already running, exiting")
            sys.exit(0)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp:
            try:
                fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
                self.fp.close()
                os.remove(self.lock_file)
            except:
                pass


class ChannelChecker:
    """Checks internet connectivity via SOCKS proxies on OpenWrt"""
    
    @staticmethod
    def check_channel(channel_name: str, socks_config: Dict) -> Tuple[bool, str]:
        """Check if channel has internet access via SOCKS proxy"""
        proxy_host = socks_config["host"]
        proxy_port = socks_config["port"]
        wan_iface = socks_config["wan_iface"]
        check_url = socks_config["check_url"]
        
        try:
            # Create socket with SOCKS proxy
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
            sock.settimeout(10)
            
            # Parse URL
            from urllib.parse import urlparse
            parsed = urlparse(check_url)
            host = parsed.netloc or parsed.path
            path = parsed.path if parsed.netloc else "/"
            port = 80
            
            # Connect and send HTTP request
            sock.connect((host, port))
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"
            sock.send(request.encode())
            
            # Receive response
            response = b""
            sock.settimeout(5)
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
            except socket.timeout:
                pass
            
            sock.close()
            
            response_text = response.decode('utf-8', errors='ignore')
            
            # Check response
            if "Microsoft Connect Test" in response_text:
                return True, "Direct internet OK"
            if "msn.com" in response_text.lower() or "location:" in response_text.lower():
                return True, "Already authorized (redirect to MSN)"
            if "conn4.com" in response_text.lower():
                return False, "Captive portal (conn4.com)"
            
            # Check for any redirect (captive portal)
            if "location:" in response_text.lower():
                return False, "Redirect detected (captive portal)"
            
            return False, f"Unknown response: {response_text[:50]}"
            
        except socket.timeout:
            return False, "Connection timeout via SOCKS"
        except Exception as e:
            return False, f"SOCKS error ({wan_iface}): {str(e)[:50]}"
    
    @staticmethod
    def check_gateway_reachable(socks_config: Dict) -> bool:
        """Check if we can reach anything via SOCKS proxy"""
        proxy_host = socks_config["host"]
        proxy_port = socks_config["port"]
        
        try:
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
            sock.settimeout(5)
            sock.connect(("8.8.8.8", 53))  # DNS server
            sock.close()
            return True
        except:
            return False


class CookieManager:
    """Manages cookies for both channels"""
    
    def __init__(self, cookies_file: str, meta_file: str):
        self.cookies_file = cookies_file
        self.meta_file = meta_file
        self.cookies = {}
        self.meta = {}
        self._load()
    
    def _load(self):
        """Load cookies from files"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    self.cookies = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            self.cookies = {}
        
        try:
            if os.path.exists(self.meta_file):
                with open(self.meta_file, 'r') as f:
                    self.meta = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load meta: {e}")
            self.meta = {}
    
    def save(self):
        """Save cookies to files"""
        try:
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(self.cookies, f)
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
        
        try:
            with open(self.meta_file, 'w') as f:
                json.dump(self.meta, f)
        except Exception as e:
            logger.error(f"Failed to save meta: {e}")
    
    def get_channel_cookies(self, channel: str) -> Optional[Dict]:
        """Get cookies for specific channel"""
        return self.cookies.get(channel)
    
    def set_channel_cookies(self, channel: str, cookies: Dict, site_id: str = None):
        """Set cookies for specific channel"""
        self.cookies[channel] = cookies
        self.meta[channel] = {
            "updated": datetime.utcnow().isoformat(),
            "site_id": site_id,
            "ttl": COOKIE_TTL
        }
        self.save()
    
    def is_valid(self, channel: str) -> bool:
        """Check if cookies for channel are still valid"""
        if channel not in self.meta:
            return False
        
        try:
            updated = datetime.fromisoformat(self.meta[channel]["updated"])
            expires = updated + timedelta(seconds=COOKIE_TTL)
            return datetime.utcnow() < (expires - timedelta(seconds=COOKIE_REFRESH_BEFORE))
        except:
            return False


class DualAuthManager:
    """Manages authorization for both channels via SOCKS proxies"""
    
    def __init__(self):
        self.cookie_manager = CookieManager(COOKIES_FILE, COOKIES_META_FILE)
        self.checker = ChannelChecker()
        
    def authorize_channel(self, channel_name: str, socks_config: Dict) -> bool:
        """Authorize on captive portal for specific channel via SOCKS"""
        logger.info(f"Starting authorization for {channel_name} via SOCKS {socks_config['host']}:{socks_config['port']}")
        
        # Check if SOCKS proxy is reachable
        if not self.checker.check_gateway_reachable(socks_config):
            logger.error(f"SOCKS proxy {socks_config['host']}:{socks_config['port']} not reachable")
            return False
        
        # Check if already authorized
        connected, status = self.checker.check_channel(channel_name, socks_config)
        if connected:
            logger.info(f"{channel_name} already authorized: {status}")
            return True
        
        logger.info(f"{channel_name} needs authorization: {status}")
        
        # Try to authorize using Selenium via SOCKS
        try:
            return self._authorize_with_selenium(channel_name, socks_config)
        except Exception as e:
            logger.error(f"Selenium authorization failed for {channel_name}: {e}")
            return False
    
    def _authorize_with_selenium(self, channel_name: str, socks_config: Dict) -> bool:
        """Use Selenium to authorize via SOCKS proxy"""
        proxy_host = socks_config["host"]
        proxy_port = socks_config["port"]
        wan_iface = socks_config["wan_iface"]
        
        logger.info(f"Starting Chrome for {channel_name} via SOCKS {proxy_host}:{proxy_port}")
        
        # Chrome options with SOCKS proxy
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--proxy-server=socks5://{proxy_host}:{proxy_port}')
        
        # ChromeDriver service
        service = Service()
        
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            
            # Navigate to captive portal detection
            driver.get("http://neverssl.com")
            
            # Wait for redirect to portal
            wait = WebDriverWait(driver, 30)
            
            # Check if we're on conn4 portal
            if "conn4.com" in driver.current_url:
                logger.info(f"Detected conn4 portal for {channel_name}")
                
                # Look for connect button
                try:
                    connect_btn = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Connect') or contains(text(), 'Подключить')]"))
                    )
                    connect_btn.click()
                    logger.info(f"Clicked connect button for {channel_name}")
                    
                    # Wait for authorization
                    time.sleep(5)
                    
                    # Check if authorized
                    connected, status = self.checker.check_channel(channel_name, socks_config)
                    if connected:
                        logger.info(f"{channel_name} authorization successful")
                        
                        # Save cookies
                        cookies = driver.get_cookies()
                        self.cookie_manager.set_channel_cookies(channel_name, cookies)
                        
                        return True
                    else:
                        logger.error(f"{channel_name} authorization failed: {status}")
                        return False
                        
                except TimeoutException:
                    logger.error(f"Connect button not found for {channel_name}")
                    return False
            else:
                # Already have internet
                logger.info(f"{channel_name} already has internet access")
                return True
                
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def run_cycle(self):
        """Run authorization check cycle for both channels via SOCKS"""
        results = {}
        
        for channel_name, socks_config in SOCKS_CONFIG.items():
            # Add channel filter to logger
            channel_filter = ChannelFilter(channel_name)
            logger.addFilter(channel_filter)
            
            try:
                # Check current status
                connected, status = self.checker.check_channel(channel_name, socks_config)
                
                if not connected:
                    # Try to authorize
                    success = self.authorize_channel(channel_name, socks_config)
                    results[channel_name] = success
                else:
                    logger.info(f"{channel_name} already connected: {status}")
                    results[channel_name] = True
                    
            finally:
                logger.removeFilter(channel_filter)
        
        return results


def main():
    """Main entry point"""
    parser = None
    try:
        import argparse
        parser = argparse.ArgumentParser(description='Dual-channel captive portal authorization via SOCKS')
        parser.add_argument('--check-only', action='store_true',
                          help='Only check connectivity via SOCKS, do not authorize')
        parser.add_argument('--daemon', action='store_true',
                          help='Run as daemon with periodic checks')
        parser.add_argument('--interval', type=int, default=60,
                          help='Check interval in seconds (default: 60)')
        parser.add_argument('--channel', choices=['primary', 'secondary', 'all'], default='all',
                          help='Which channel to check (default: all)')
        args = parser.parse_args()
    except:
        args = None
    
    with SingleInstanceLock(LOCK_FILE):
        manager = DualAuthManager()
        
        # Run authorization cycle
        if args and args.check_only:
            # Check specific channel or all
            if args.channel == 'all':
                for channel_name, socks_config in SOCKS_CONFIG.items():
                    connected, status = manager.checker.check_channel(channel_name, socks_config)
                    print(f"{channel_name}: {'✓' if connected else '✗'} {status}")
            else:
                socks_config = SOCKS_CONFIG.get(args.channel)
                if socks_config:
                    connected, status = manager.checker.check_channel(args.channel, socks_config)
                    print(f"{args.channel}: {'✓' if connected else '✗'} {status}")
                else:
                    print(f"Channel {args.channel} not configured")
                    sys.exit(1)
            return
        
        if args and args.daemon:
            # Add default channel filter for main logger
            default_filter = ChannelFilter("main")
            logger.addFilter(default_filter)
            
            logger.info(f"Starting daemon mode, interval: {args.interval}s")
            while True:
                results = manager.run_cycle()
                logger.info(f"Cycle complete: {results}")
                time.sleep(args.interval)
        else:
            # Single run
            results = manager.run_cycle()
            logger.info(f"Authorization complete: {results}")
            # Exit with error if any channel failed
            if not all(results.values()):
                sys.exit(1)


if __name__ == "__main__":
    main()
