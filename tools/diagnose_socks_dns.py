#!/usr/bin/env python3
"""
SOCKS & DNS Diagnostic Tool
===========================
Tests SOCKS5 proxy stability and DNS resolution modes (Local vs Remote).
Designed to investigate "connection drops after a few requests" issues.
"""

import argparse
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_request(url, proxy_url, timeout=10):
    """Performs a single request and returns (success, status_code/error, duration)."""
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    start_time = time.time()
    try:
        response = requests.get(url, proxies=proxies, timeout=timeout)
        duration = time.time() - start_time
        return True, response.status_code, duration
    except Exception as e:
        duration = time.time() - start_time
        return False, str(e), duration

def run_stress_test(url, proxy_url, count, delay):
    """Runs a sequence of requests to test stability."""
    logger.info("--- Starting Stability Test ---")
    logger.info(f"Target: {url}")
    logger.info(f"Proxy:  {proxy_url}")
    logger.info(f"Count:  {count}")
    
    success_count = 0
    
    for i in range(1, count + 1):
        success, result, duration = test_request(url, proxy_url)
        
        status_str = "OK" if success else "FAIL"
        color = "\033[92m" if success else "\033[91m"
        reset = "\033[0m"
        
        logger.info(f"Req #{i:02d}: {color}{status_str}{reset} | Time: {duration:.2f}s | Result: {result}")
        
        if success:
            success_count += 1
            
        if i < count:
            time.sleep(delay)
            
    success_rate = (success_count / count) * 100
    logger.info(f"--- Test Completed: {success_count}/{count} passed ({success_rate:.1f}%) ---")
    return success_count == count

def check_dns_modes(base_proxy, target_host="www.google.com"):
    """
    Compares Local DNS (socks5://) vs Remote DNS (socks5h://).
    base_proxy: e.g. "127.0.0.1:10800"
    """
    logger.info(f"\n--- DNS Mode Comparison (Target: {target_host}) ---")
    
    # 1. Local DNS (socks5://)
    # This requires the local machine to resolve the hostname, then ask SOCKS to connect to IP.
    local_proxy = f"socks5://{base_proxy}"
    logger.info(f"Testing LOCAL DNS resolution (via {local_proxy})...")
    # Note: If local DNS fails to resolve, requests might throw an error before even hitting the proxy,
    # or the proxy might receive an IP.
    success_local, res_local, time_local = test_request(f"http://{target_host}", local_proxy)
    if success_local:
        logger.info(f"  [Local DNS] -> SUCCESS ({time_local:.2f}s) - Local resolver is working.")
    else:
        logger.info(f"  [Local DNS] -> FAILED ({time_local:.2f}s) - {res_local}")

    # 2. Remote DNS (socks5h://)
    # This sends the hostname to the SOCKS server to resolve.
    remote_proxy = f"socks5h://{base_proxy}"
    logger.info(f"Testing REMOTE DNS resolution (via {remote_proxy})...")
    success_remote, res_remote, time_remote = test_request(f"http://{target_host}", remote_proxy)
    if success_remote:
        logger.info(f"  [Remote DNS] -> SUCCESS ({time_remote:.2f}s) - Proxy DNS is working.")
    else:
        logger.info(f"  [Remote DNS] -> FAILED ({time_remote:.2f}s) - {res_remote}")
        
    # Diagnosis
    if success_local and not success_remote:
        logger.warning("DIAGNOSIS: Local DNS works, but Remote DNS failed. The SOCKS server cannot resolve domains.")
    elif not success_local and success_remote:
        logger.info("DIAGNOSIS: Remote DNS works, Local DNS failed. Use socks5h:// to bypass local DNS issues.")
    elif not success_local and not success_remote:
        logger.error("DIAGNOSIS: Both modes failed. Likely a connectivity or proxy issue, not just DNS.")
    else:
        logger.info("DIAGNOSIS: Both DNS modes are working correctly.")

def main():
    parser = argparse.ArgumentParser(description="Diagnose SOCKS5 proxy and DNS stability.")
    parser.add_argument("--proxy", default="127.0.0.1:10800", help="SOCKS proxy address (host:port), default: 127.0.0.1:10800")
    parser.add_argument("--url", default="http://connectivitycheck.gstatic.com/generate_204", help="Target URL for stability test")
    parser.add_argument("--count", type=int, default=20, help="Number of requests for stability test")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument("--dns-target", default="www.google.com", help="Hostname to test for DNS mode comparison")
    
    args = parser.parse_args()
    
    # Clean proxy string if user added protocol
    proxy_addr = args.proxy.replace("socks5://", "").replace("socks5h://", "")
    
    # 1. Quick DNS Mode Check
    check_dns_modes(proxy_addr, args.dns_target)
    
    print("\n")
    
    # 2. Stability Test (using Remote DNS by default as it's safer for SOCKS)
    # Using socks5h to rule out local DNS issues during stability test, 
    # unless the user wants to test specifically local dns (not implemented as flag here for simplicity)
    proxy_url = f"socks5h://{proxy_addr}"
    run_stress_test(args.url, proxy_url, args.count, args.delay)

if __name__ == "__main__":
    main()
