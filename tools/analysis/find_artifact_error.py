
import re

log_file = "failed_job_log_utf8.txt"
try:
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
except UnicodeError:
    with open(log_file, "r", encoding="latin-1") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")

patterns = [
    "error: no .ipk files found",
    "error: no openwrt-captive-monitor package found",
    "Verify package internals",
    "Validate IPK version metadata"
]

for pattern in patterns:
    found = False
    for i, line in enumerate(lines):
        if pattern in line:
            print(f"Found '{pattern}' at line {i}: {line.strip()}")
            # Print context
            for j in range(i, min(len(lines), i+20)):
                 print(f"  {j}: {lines[j].strip()}")
            print("-" * 20)
            found = True
            break
    if not found:
        print(f"Pattern '{pattern}' not found.")
