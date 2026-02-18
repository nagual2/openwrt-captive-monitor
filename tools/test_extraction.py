import json
import sys
from conn4_shared import extract_resource_urls_from_html

def test_extraction(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    html = data.get("page_html", "")
    print(f"HTML len: {len(html)}")
    
    # Print first 500 chars to see head
    print("Head snippet:")
    print(html[:500])
    
    print("\nSearching for 'script':")
    start = 0
    while True:
        idx = html.find("<script", start)
        if idx == -1:
            break
        end = html.find(">", idx)
        print(f"Script tag at {idx}: {html[idx:end+1]}")
        start = idx + 1

    urls = extract_resource_urls_from_html(html, "https://example.com")
    print(f"\nFound {len(urls)} URLs:")
    for u in urls:
        print(f"  {u}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/test_extraction.py <artifact_json>")
        sys.exit(1)
    test_extraction(sys.argv[1])
