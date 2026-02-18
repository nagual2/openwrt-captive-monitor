
import os
import sys
import time
import json
sys.path.append(os.getcwd())
from tools.captive_portal_wsl_selenium import Conn4PortalTester

def get_sel_cookies():
    os.environ["SELENIUM_HEADLESS"] = "1"
    tester = Conn4PortalTester()
    try:
        if not tester.setup_chrome_driver():
            print("Failed to setup driver")
            return
        tester.driver.get('https://1096.rdr.conn4.com/')
        time.sleep(3)
        tester.driver.get('https://1096.rdr.conn4.com/admon-assets/cookie-challenge.php')
        time.sleep(3)
        tester.driver.get('https://1096.rdr.conn4.com/')
        time.sleep(3)
        cookies = tester.driver.get_cookies()
        names = sorted([c['name'] for c in cookies])
        print(f"SELENIUM_COOKIES: {names}")
        
        # Save to a temp file for comparison
        with open("mcp_artifacts/temp_sel_cookies.json", "w") as f:
            json.dump({"cookies": cookies}, f)
            
    finally:
        if tester.driver:
            tester.driver.quit()

if __name__ == "__main__":
    get_sel_cookies()
