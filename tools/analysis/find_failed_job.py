
import subprocess
import json

run_id = "19572285294"
cmd = ["gh", "api", f"repos/nagual2/openwrt-captive-monitor/actions/runs/{run_id}/jobs", "--paginate"]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    
    failed_jobs = []
    for job in data.get("jobs", []):
        if job["conclusion"] == "failure":
            failed_jobs.append(job)
            
    if failed_jobs:
        print(f"Found {len(failed_jobs)} failed jobs:")
        for job in failed_jobs:
            print(f"Job ID: {job['id']}")
            print(f"Name: {job['name']}")
            print(f"URL: {job['html_url']}")
            print("-" * 20)
    else:
        print("No failed jobs found in API response.")
        
except subprocess.CalledProcessError as e:
    print(f"Error running gh api: {e}")
    print(e.stderr)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
