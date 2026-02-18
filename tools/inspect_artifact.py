import json
import sys
from html.parser import HTMLParser

class SimpleFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current_form = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "form":
            self.current_form = {
                "action": attrs_dict.get("action"),
                "method": attrs_dict.get("method", "GET").upper(),
                "inputs": []
            }
            self.forms.append(self.current_form)
        elif tag in ("input", "textarea", "select", "button") and self.current_form is not None:
            self.current_form["inputs"].append({
                "tag": tag,
                "name": attrs_dict.get("name"),
                "value": attrs_dict.get("value"),
                "type": attrs_dict.get("type"),
                "id": attrs_dict.get("id")
            })

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None

def analyze_artifact(path):
    print(f"Analyzing: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        html = data.get("page_html", "")
        if not html:
            print("No page_html found in artifact")
            return

        parser = SimpleFormParser()
        parser.feed(html)
        
        print(f"Found {len(parser.forms)} forms:")
        for i, form in enumerate(parser.forms):
            print(f"\nForm #{i+1}:")
            print(f"  Action: {form['action']}")
            print(f"  Method: {form['method']}")
            print("  Inputs:")
            for inp in form['inputs']:
                name = inp.get("name", "N/A")
                val = inp.get("value", "N/A")
                typ = inp.get("type", "N/A")
                print(f"    - [{inp['tag']}] name='{name}' value='{val}' type='{typ}'")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_artifact.py <path_to_json>")
        sys.exit(1)
    analyze_artifact(sys.argv[1])
