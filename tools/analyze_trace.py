import json
import sys

path = r"/mnt/c/git/openwrt-captive-monitor/mcp_artifacts/conn4_selenium/20260117_215328_2449/conn4_session_storage_trace.json"

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data:
        if item.get("type") == "xhr":
            print(f"XHR: {item.get('url')}")
        if item.get("type") == "xhr" and "login/free" in item.get("url", ""):
            print("FOUND login/free:")
            print(json.dumps(item, indent=2))
            
            body = item.get("body", "")
            print("\nBODY:")
            print(body)
            
            if item.get("parsed"):
                print("\nPARSED:")
                print(json.dumps(item["parsed"], indent=2))
                
except Exception as e:
    print(e)
