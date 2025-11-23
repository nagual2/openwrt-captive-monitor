
import re

log_file = "ci_log.txt"
try:
    with open(log_file, "r", encoding="utf-16le") as f:
        lines = f.readlines()
except UnicodeError:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")

start_line = 2020
found = False
for i in range(start_line, len(lines)):
    line = lines[i]
    if any(x in line for x in ["##[error]", "Error:", "FAILED", "exited with code"]):
        print(f"Line {i}: {line.strip()}")
        # Print context
        for j in range(max(start_line, i-10), min(len(lines), i+20)):
             print(f"  {j}: {lines[j].strip()}")
        print("-" * 20)
        found = True
        if i > start_line + 5000: # Limit search scope
            break

if not found:
    print("No errors found in Test job section.")
