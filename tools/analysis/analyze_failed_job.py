
import re

log_file = "failed_job_log.txt"
try:
    with open(log_file, "r", encoding="utf-16le") as f:
        lines = f.readlines()
except UnicodeError:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")

found_error = False
for i, line in enumerate(lines):
    if any(x in line for x in ["##[error]", "Error:", "FAILED", "make: ***"]):
        print(f"Line {i}: {line.strip()}")
        # Print context
        for j in range(max(0, i-10), min(len(lines), i+20)):
             print(f"  {j}: {lines[j].strip()}")
        print("-" * 20)
        found_error = True
        if i > 10000: # Limit output
            break

if not found_error:
    print("No common error markers found.")
