#!/usr/bin/env python3
import os
import re
import json
from collections import defaultdict

def tokenize(text):
    return [t for t in re.split(r"\W+", text.lower()) if t]

def scan_blocks(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    blocks = []
    starts = []
    for i, line in enumerate(lines):
        if re.match(r"\s*(def|class)\s+\w+", line):
            starts.append(i)
    if not starts:
        return blocks
    for idx, s in enumerate(starts):
        e = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        blocks.append((s + 1, e))
    return blocks

def tfidf(corpus_terms):
    df = defaultdict(int)
    for terms in corpus_terms:
        for k in set(terms.keys()):
            df[k] += 1
    n = len(corpus_terms)
    idf = {k: 1.0 + (n / (1 + v)) for k, v in df.items()}
    return idf

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    targets = [
        os.path.join(base, "tools"),
        os.path.join(base, "package"),
        os.path.join(base, "scripts"),
    ]
    entries = []
    corpus_terms = []
    for root in targets:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".py"):
                    fp = os.path.join(dirpath, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except Exception:
                        continue
                    blocks = scan_blocks(fp)
                    if not blocks:
                        terms = defaultdict(int)
                        for t in tokenize(content):
                            terms[t] += 1
                        entries.append({"file": fp.replace("\\", "/"), "start": 1, "end": 1, "terms": terms})
                        corpus_terms.append(terms)
                        continue
                    for s, e in blocks:
                        text = "".join(content.splitlines(True)[s - 1 : e])
                        terms = defaultdict(int)
                        for t in tokenize(text):
                            terms[t] += 1
                        entries.append({"file": fp.replace("\\", "/"), "start": s, "end": e, "terms": terms})
                        corpus_terms.append(terms)
    idf = tfidf(corpus_terms)
    for ent in entries:
        ent["idf"] = {k: idf.get(k, 1.0) for k in ent["terms"].keys()}
    out_dir = os.path.join(base, ".cache")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "snippets.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)
    print(out_path)

if __name__ == "__main__":
    main()

