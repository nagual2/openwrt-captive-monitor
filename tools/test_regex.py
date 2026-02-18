import re

tag = '<script src="/admon/js/720678202f7bd7e00e65e423086018c973f5.js?c=default&amp;a=0">'

p = r"<script[^>]*src=['\"]([^'\"\\s]+)"
m = re.search(p, tag, flags=re.IGNORECASE)
if m:
    print(f"Matched content: '{m.group(1)}'")
else:
    print("No match")
