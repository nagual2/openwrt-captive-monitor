import json
import sys

path = r"/mnt/c/git/openwrt-captive-monitor/mcp_artifacts/conn4_selenium/20260117_215328_2449/conn4_master.json"

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    events = data.get("network", [])
    print(f"Total events: {len(events)}")
    for e in events:
        req = e.get("request", {})
        url = req.get("url", "")
        # print(url)
        if "login/free" in url or "create-session" in url:
            print(f"FOUND: {url}")
            print(f"Method: {req.get('method')}")
            print(f"PostData: {req.get('postData')}")
            
except Exception as e:
    print(e)
