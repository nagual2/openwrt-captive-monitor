# GHCR OpenWrt SDK Usage Report (Template)

Repository: `nagual2/openwrt-captive-monitor`

> **Note**
> This document describes the methodology and tooling for counting
> `ghcr.io/openwrt/sdk` usage in this repository's GitHub Actions workflows.
> The actual numeric results are **intended to be generated automatically** by
> the analysis script once it is run with suitable GitHub credentials.
>
> From the development environment used for this change it is not possible to
> safely query the full Actions history (API rate limits and missing
> repository-admin credentials for log access), so the real numbers are **not
> embedded** here. Repository maintainers should re‑run the script as
> described below to obtain an up‑to‑date report.

---

## 1. Purpose

The goal of this report is to provide a reproducible way to answer the
question:

> **How many times was the upstream OpenWrt SDK container image
> `ghcr.io/openwrt/sdk` used in GitHub Actions for this repository?**

Two primary metrics are tracked:

1. **Workflow runs using the image**  
   Number of workflow **runs** where at least one job used the image.
2. **Jobs using the image**  
   Number of individual **jobs** that used the image (matrix expansions are
   counted per job instance).

In addition, the analysis produces:

- a **per‑workflow breakdown** (workflow file → runs / jobs using the image),
- a **per‑month breakdown** based on `run.created_at`.

---

## 2. What counts as "using the image"

For the purposes of this analysis a job is considered to **use** the
`ghcr.io/openwrt/sdk` image if **either** of the following is true:

1. The job runs directly in a container based on the image:

   ```yaml
   jobs:
     build-packages:
       container:
         image: ghcr.io/openwrt/sdk:x86_64-23.05.3
         # ...
   ```

2. The job invokes the OpenWrt SDK GitHub Action which, under the hood, runs
   inside the same image:

   ```yaml
   - name: Build with OpenWrt SDK
     uses: openwrt/gh-action-sdk@v9
     env:
       CONTAINER: ghcr.io/openwrt/sdk:${{ matrix.sdk_slug }}-${{ matrix.openwrt_version }}
       # ...
   ```

Jobs/steps that **only validate** the existence of the image via HTTP or Docker
commands (for example, the `scripts/validate-sdk-image.sh` script which issues
registry `HEAD` requests) are **not** counted as container usage, because the
GitHub Actions job itself does not run inside the container.

---

## 3. Tooling

The repository now contains a dedicated analysis script:

- **Script:** `tools/analysis/count_ghcr_openwrt_sdk_usage.py`  
  Standard-library-only Python tool that talks to the GitHub REST API and uses
  the local git history to map workflow runs back to the exact workflow YAML
  revision that was executed.

High‑level behaviour:

1. **Workflow discovery**  
   `GET /repos/{owner}/{repo}/actions/workflows` to enumerate workflows.
2. **Run enumeration**  
   For each workflow, `GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs`
   (with `per_page=100`) to walk all historical workflow runs.
3. **Job enumeration per run**  
   `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs` to list jobs and
   their runtime names.
4. **Workflow revision inspection**  
   For each run, the script determines which workflow file revision was used
   based on `head_sha` and `path` and loads that YAML via either:

   - `git show <head_sha>:<path>` from the local clone, or
   - `GET /repos/{owner}/{repo}/contents/{path}?ref=<head_sha>` as a fallback.

5. **Static detection of SDK-using jobs**  
   A minimal, line‑oriented parser scans the workflow YAML for jobs that:

   - define a top‑level `container:` block whose image contains
     `ghcr.io/openwrt/sdk`, or
   - contain a step whose `uses:` line references `openwrt/gh-action-sdk@`.

6. **Matching runtime jobs**  
   For each such job definition, the `name:` template is converted into a
   regular expression where expression segments like `${{ matrix.sdk_target }}`
   are treated as wildcards. Runtime job names from the API are matched against
   these patterns; any matches are considered jobs that used the image.

7. **Counting rules**  
   - A **workflow run** is counted once if **any** of its jobs used the image.  
   - A **job** is counted once per execution when its runtime name matches a
     job definition that uses the image (matrix jobs contribute one count per
     expanded job).

The script is careful to honour GitHub API pagination and core rate limits and
will pause when close to exhaustion.

---

## 4. How to generate the report

Run the script from the repository root with a GitHub token that has at least
`repo` scope and **admin access** to the repository (required for complete
access to workflow metadata):

```bash
# From the repository root
export GITHUB_TOKEN="<your-token>"

python tools/analysis/count_ghcr_openwrt_sdk_usage.py \
  --repo nagual2/openwrt-captive-monitor \
  --output docs/ci/GHCR_OPENWRT_SDK_USAGE.md
```

The script will:

- print a concise JSON summary to stdout:

  ```json
  {
    "total_runs_with_usage": 123,
    "total_jobs_with_usage": 456
  }
  ```

- overwrite this Markdown file with a fully populated report including:
  - the overall totals,
  - per‑workflow breakdown, and
  - per‑month breakdown.

You can optionally restrict the analysis to a subset of workflows or a time
window, for example only the main CI workflow in 2025:

```bash
python tools/analysis/count_ghcr_openwrt_sdk_usage.py \
  --repo nagual2/openwrt-captive-monitor \
  --workflow ci.yml \
  --start-date 2025-01-01 \
  --end-date 2026-01-01 \
  --output docs/ci/GHCR_OPENWRT_SDK_USAGE.md
```

---

## 5. Current status

Because the development environment used to implement this tooling does not
have an admin-scoped GitHub token and is limited to 60 unauthenticated API
calls per hour, it is **not** possible to compute the full historical
statistics here without risking incomplete or biased data.

As a result:

- The totals in this template are intentionally left **blank**.  
- Repository maintainers should run the script with their own token to produce
  the authoritative numbers.

Once the script has been executed successfully, this file will be updated with
concrete values for:

- total workflow runs using `ghcr.io/openwrt/sdk`, and
- total jobs using `ghcr.io/openwrt/sdk`,

as well as workflow-level and time-based breakdowns.
