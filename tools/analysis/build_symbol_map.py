#!/usr/bin/env python3
import os
import re
import json
import sys

def scan_dir(root):
    result = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.py'):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for idx, line in enumerate(lines, start=1):
                    m = re.match(r"\s*(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
                    if m:
                        name = m.group(2)
                        key = name
                        result.setdefault(key, []).append({
                            'file': fp.replace('\\', '/'),
                            'line': idx
                        })
    return result

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    targets = [
        os.path.join(base, 'tools'),
        os.path.join(base, 'package'),
        os.path.join(base, 'scripts')
    ]
    symbols = {}
    for t in targets:
        if os.path.isdir(t):
            m = scan_dir(t)
            for k, v in m.items():
                symbols.setdefault(k, []).extend(v)
    out_dir = os.path.join(base, '.cache')
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        pass
    out_path = os.path.join(out_dir, 'symbols.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(symbols, f, ensure_ascii=False, indent=2)
    print(out_path)

if __name__ == '__main__':
    main()

