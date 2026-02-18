import json
import os
import sys

def get_cookies_from_artifact(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cookies = data.get('cookies', [])
            return {c.get('name') for c in cookies if c.get('name')}
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_cookies.py <path_to_selenium_json> <path_to_nojs_json>")
        sys.exit(1)

    sel_path = sys.argv[1]
    nojs_path = sys.argv[2]

    sel_cookies = get_cookies_from_artifact(sel_path)
    nojs_cookies = get_cookies_from_artifact(nojs_path)

    if sel_cookies is None or nojs_cookies is None:
        print("Could not load cookies from one or both files.")
        sys.exit(1)

    print(f"Selenium cookies ({len(sel_cookies)}): {sorted(list(sel_cookies))}")
    print(f"NoJS cookies ({len(nojs_cookies)}): {sorted(list(nojs_cookies))}")

    if sel_cookies == nojs_cookies:
        print("\n✅ Cookie sets are IDENTICAL.")
    else:
        only_sel = sel_cookies - nojs_cookies
        only_nojs = nojs_cookies - sel_cookies
        print("\n❌ Cookie sets DIFFERENT.")
        if only_sel:
            print(f"Only in Selenium: {only_sel}")
        if only_nojs:
            print(f"Only in NoJS: {only_nojs}")

if __name__ == "__main__":
    main()
