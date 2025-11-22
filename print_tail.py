
log_file = "failed_job_log.txt"
try:
    with open(log_file, "r", encoding="utf-16le") as f:
        lines = f.readlines()
except UnicodeError:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("--- Last 100 lines ---")
for line in lines[-100:]:
    print(line.strip())
