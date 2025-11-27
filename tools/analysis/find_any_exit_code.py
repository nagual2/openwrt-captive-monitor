
import re

log_file = "failed_job_log_utf8.txt"
try:
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
except UnicodeError:
    with open(log_file, "r", encoding="latin-1") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")

found = False
for i, line in enumerate(lines):
    if "exit code" in line or "Exit code" in line:
        print(f"Line {i}: {line.strip()}")
        # Print context
        for j in range(max(0, i-5), min(len(lines), i+5)):
             print(f"  {j}: {lines[j].strip()}")
        print("-" * 20)
        found = True

if not found:
    print("No exit codes found.")
