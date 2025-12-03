
log_file = "failed_job_log_utf8.txt"
try:
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
except UnicodeError:
    with open(log_file, "r", encoding="latin-1") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("--- Last 200 lines ---")
for line in lines[-200:]:
    print(line.strip())
