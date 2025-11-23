
import re

log_file = "failed_job_log_utf8.txt"
try:
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
except UnicodeError:
    print("UTF-8 read failed, trying latin-1")
    with open(log_file, "r", encoding="latin-1") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")

found = False
for i, line in enumerate(lines):
    if "make" in line.lower() and ("error" in line.lower() or "***" in line):
        print(f"Line {i}: {line.strip()}")
        # Print context
        for j in range(max(0, i-10), min(len(lines), i+10)):
             print(f"  {j}: {lines[j].strip()}")
        print("-" * 20)
        found = True
        if i > 10000: # Limit output
            break

if not found:
    print("No make errors found.")
