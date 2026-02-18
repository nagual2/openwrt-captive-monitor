#!/usr/bin/env python3
import os
import re
import sys
import json

def tokenize(x):
    return [t for t in re.split(r"\W+", x.lower()) if t]

def score(entry, qtokens):
    s = 0.0
    for t in qtokens:
        tf = entry["terms"].get(t, 0)
        idf = entry.get("idf", {}).get(t, 1.0)
        s += tf * idf
    return s

def main():
    if len(sys.argv) < 2:
        print("query required")
        sys.exit(1)
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    path = os.path.join(base, ".cache", "snippets.json")
    if not os.path.exists(path):
        print("index missing")
        sys.exit(2)
    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)
    q = " ".join(sys.argv[1:])
    qtokens = tokenize(q)
    scored = []
    for e in entries:
        s = score(e, qtokens)
        if s > 0:
            scored.append((s, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    for s, e in scored[:10]:
        print(f"{e['file']}:{e['start']}-{e['end']} {s:.2f}")

if __name__ == "__main__":
    main()

