#!/usr/bin/env python3
"""Count GitHub Actions usage of the ghcr.io/openwrt/sdk container.

This utility talks to the GitHub REST API to analyse workflow runs for a
repository and compute how often the upstream OpenWrt SDK image
``ghcr.io/openwrt/sdk`` is used in GitHub Actions.

The script is intentionally implemented with the Python standard library only
so it can be run in minimal environments (e.g. CI, local clones) without
additional dependencies.

Methodology (high level):

* List all workflows in the repository
* For each workflow, page through all workflow runs
* For each run, determine which workflow file revision was used
  (via ``head_sha`` and ``path``)
* Fetch that workflow YAML from either the local git clone (preferred) or the
  GitHub contents API as a fallback
* Perform a light‐weight textual parse of the YAML to determine which jobs in
  that revision used the upstream OpenWrt SDK image, either by:

  - running directly in a job container whose image is
    ``ghcr.io/openwrt/sdk:*``; or
  - invoking ``openwrt/gh-action-sdk@…`` in a step (the action’s documented
    default container is ``ghcr.io/openwrt/sdk``).

* For each workflow run, list all jobs via the API and match their runtime job
  names against the set of job name patterns that are known (from the YAML) to
  use the image
* Aggregate statistics:

  - number of workflow **runs** where at least one job used the image
  - number of **jobs** that used the image
  - per‑workflow and per‑month breakdowns

The detection logic intentionally focuses on **actual builds that ran inside
an SDK container**, not on helper steps that merely validate that the image
exists (for example, ``scripts/validate-sdk-image.sh`` which only performs
registry HEAD requests).

Usage example (from the repository root):

.. code-block:: bash

   # Requires a GitHub token with at least "repo" scope and admin rights
   # to the repository in order to download workflow logs when needed.
   # The token is only used for GitHub API calls; all build logic stays local.

   export GITHUB_TOKEN="<your-token>"
   python tools/analysis/count_ghcr_openwrt_sdk_usage.py \
     --repo nagual2/openwrt-captive-monitor \
     --output docs/ci/GHCR_OPENWRT_SDK_USAGE.md

For large repositories the script may take several minutes to run because it
has to walk all historical workflow runs and jobs. It honours GitHub API
pagination and rate limits and will sleep when the limit is exhausted instead
of failing abruptly.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


API_BASE = "https://api.github.com"
DEFAULT_IMAGE_SUBSTRING = "ghcr.io/openwrt/sdk"
DEFAULT_SDK_ACTION_SUBSTRING = "openwrt/gh-action-sdk@"


@dataclass
class JobPattern:
    """Description of a job definition that uses the SDK image.

    This is derived statically from a particular revision of a workflow YAML
    file. At runtime we match this pattern against the concrete job names
    returned by the GitHub Actions API.
    """

    job_id: str
    name_template: str
    name_regex: re.Pattern
    uses_sdk_action: bool
    uses_container_image: bool

    def matches(self, job_name: str) -> bool:
        """Return True if the runtime job name matches this pattern."""

        return bool(self.name_regex.match(job_name))


@dataclass
class RunUsage:
    """Aggregated usage counters for a single workflow run."""

    run_id: int
    workflow_path: str
    created_at: _dt.datetime
    jobs_using_sdk: int


class GitHubClient:
    """Minimal GitHub REST API client with rate‑limit handling.

    The client only implements the GET operations needed by this analysis
    script and relies on ``urllib`` from the standard library.
    """

    def __init__(self, token: Optional[str] = None, rate_limit_safety: int = 5) -> None:
        self._token = token
        self._rate_limit_safety = rate_limit_safety
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "openwrt-captive-monitor/ghcr-sdk-usage-analyzer",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._headers = headers

    # --- low-level request helpers -------------------------------------------------

    def _build_url(self, path: str, params: Optional[Dict[str, str]] = None) -> str:
        if not path.startswith("/"):
            raise ValueError(f"API path must start with '/': {path!r}")
        url = f"{API_BASE}{path}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        return url

    def _handle_rate_limit(self, headers: Dict[str, str]) -> None:
        """Sleep if the rate limit has been exhausted.

        This keeps the script robust when used with a token that shares rate
        limits across multiple processes.
        """

        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        limit = headers.get("X-RateLimit-Limit")
        if remaining is None or reset is None or limit is None:
            return

        try:
            remaining_i = int(remaining)
            reset_epoch = int(reset)
            limit_i = int(limit)
        except ValueError:
            return

        if remaining_i > self._rate_limit_safety:
            return

        now = int(time.time())
        sleep_for = max(0, reset_epoch - now + 1)
        if sleep_for <= 0:
            return

        print(
            f"[rate-limit] remaining={remaining_i} limit={limit_i}, "
            f"sleeping {sleep_for}s until reset",
            file=sys.stderr,
        )
        time.sleep(sleep_for)

    def get_json(self, path: str, params: Optional[Dict[str, str]] = None) -> dict:
        """Perform a GET request and parse the JSON body."""

        url = self._build_url(path, params)
        req = urllib.request.Request(url, headers=self._headers, method="GET")
        while True:
            try:
                with urllib.request.urlopen(req) as resp:  # type: ignore[call-arg]
                    body = resp.read()
                    headers = {k: v for k, v in resp.headers.items()}
            except urllib.error.HTTPError as exc:  # pragma: no cover - network edge
                # Handle rate-limit errors explicitly; re-raise everything else.
                if exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0":
                    self._handle_rate_limit(dict(exc.headers.items()))
                    # After sleeping, retry the request.
                    continue
                raise

            self._handle_rate_limit(headers)

            if not body:
                return {}

            return json.loads(body.decode("utf-8"))

    def get_bytes(self, path: str, params: Optional[Dict[str, str]] = None) -> bytes:
        """Perform a GET request and return the raw response body as bytes."""

        url = self._build_url(path, params)
        req = urllib.request.Request(url, headers=self._headers, method="GET")
        while True:
            try:
                with urllib.request.urlopen(req) as resp:  # type: ignore[call-arg]
                    body = resp.read()
                    headers = {k: v for k, v in resp.headers.items()}
            except urllib.error.HTTPError as exc:  # pragma: no cover - network edge
                if exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0":
                    self._handle_rate_limit(dict(exc.headers.items()))
                    continue
                raise

            self._handle_rate_limit(headers)
            return body

    # --- high-level API helpers ----------------------------------------------------

    def list_workflows(self, owner: str, repo: str) -> List[dict]:
        """Return the list of workflows for the repository.

        The GitHub API already returns all workflows for this endpoint in a
        single page for the repository in this project, but the code is written
        generically in case more workflows are added in the future.
        """

        workflows: List[dict] = []
        page = 1
        per_page = 100
        while True:
            data = self.get_json(
                f"/repos/{owner}/{repo}/actions/workflows",
                {"page": str(page), "per_page": str(per_page)},
            )
            wf_chunk = data.get("workflows", []) or []
            workflows.extend(wf_chunk)
            if len(wf_chunk) < per_page:
                break
            page += 1
        return workflows

    def iter_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int,
    ) -> Iterable[dict]:
        """Yield all workflow runs for the given workflow id.

        This helper transparently follows pagination using ``per_page=100``.
        """

        page = 1
        per_page = 100
        while True:
            data = self.get_json(
                f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
                {"page": str(page), "per_page": str(per_page)},
            )
            runs = data.get("workflow_runs", []) or []
            if not runs:
                break
            for run in runs:
                yield run
            if len(runs) < per_page:
                break
            page += 1

    def list_jobs_for_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> List[dict]:
        """Return all jobs for a workflow run (with pagination)."""

        page = 1
        per_page = 100
        jobs: List[dict] = []
        while True:
            data = self.get_json(
                f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
                {"page": str(page), "per_page": str(per_page)},
            )
            chunk = data.get("jobs", []) or []
            jobs.extend(chunk)
            if len(chunk) < per_page:
                break
            page += 1
        return jobs

    def get_workflow_contents(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> Optional[str]:
        """Fetch a workflow file at a specific ref via the contents API.

        This is used as a fallback when the local git history does not contain
        the commit referenced by a workflow run. The contents API returns the
        file body as base64-encoded text.
        """

        try:
            data = self.get_json(
                f"/repos/{owner}/{repo}/contents/{path}",
                {"ref": ref},
            )
        except urllib.error.HTTPError as exc:  # pragma: no cover - network edge
            # 404 or permission errors are treated as "no contents available".
            print(
                f"[warn] failed to fetch {path!r} at {ref[:8]} via contents API: {exc}",
                file=sys.stderr,
            )
            return None

        if not isinstance(data, dict):
            return None

        if data.get("type") != "file":
            return None

        content = data.get("content")
        encoding = data.get("encoding", "base64")
        if not content:
            return ""

        if encoding != "base64":  # pragma: no cover - extremely unlikely
            print(
                f"[warn] unexpected encoding for {path!r} at {ref[:8]}: {encoding}",
                file=sys.stderr,
            )
        try:
            raw = base64.b64decode(content)
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"[warn] failed to decode base64 content for {path!r} at {ref[:8]}: {exc}",
                file=sys.stderr,
            )
            return None

        return raw.decode("utf-8", errors="replace")


def template_to_regex(template: str) -> re.Pattern:
    """Convert a job ``name:`` template into a regex for runtime names.

    The GitHub Actions UI expands expressions like ``${{ matrix.sdk_target }}``
    inside the job ``name`` field. We do not re‑implement the full expression
    engine here; instead we treat such expressions as wildcards.

    Example::

        "Build with OpenWrt SDK (${{ matrix.sdk_target }})" ->
        r"^Build with OpenWrt SDK \(.*\)$"

    This is sufficient to match concrete job names like
    ``"Build with OpenWrt SDK (x86/64)"``.
    """

    # Escape literal text and replace "${{ ... }}" segments with ".*".
    pattern_parts: List[str] = []
    pos = 0
    for match in re.finditer(r"\$\{\{[^}]+\}\}", template):
        start, end = match.span()
        if start > pos:
            pattern_parts.append(re.escape(template[pos:start]))
        pattern_parts.append(".*")
        pos = end
    if pos < len(template):
        pattern_parts.append(re.escape(template[pos:]))
    pattern = "".join(pattern_parts)
    # Anchor at both ends for stricter matching, case‑insensitive.
    return re.compile(f"^{pattern}$", re.IGNORECASE)


def parse_workflow_for_container_jobs(
    workflow_text: str,
    image_substring: str = DEFAULT_IMAGE_SUBSTRING,
    sdk_action_substring: str = DEFAULT_SDK_ACTION_SUBSTRING,
) -> List[JobPattern]:
    """Parse a workflow YAML and return job patterns that use the SDK image.

    This is a deliberately minimal, line‑oriented parser tailored to the
    structure of this repository's workflows. It does **not** attempt to be a
    general YAML parser; instead it relies on indentation and a few key fields
    (``jobs``, ``name``, ``container``, and ``uses``).

    A job is considered to use the SDK image if either of the following holds:

    * the job defines a top‑level ``container:`` block whose image contains
      ``ghcr.io/openwrt/sdk``; or
    * the job contains a step whose ``uses:`` line references
      ``openwrt/gh-action-sdk@`` (which in turn runs inside
      ``ghcr.io/openwrt/sdk``).

    Jobs that merely reference the image string inside helper scripts or
    environment variables (for example, in calls to ``validate-sdk-image.sh``)
    are **not** treated as container usage, because they do not execute inside
    the image.
    """

    lines = workflow_text.splitlines()

    in_jobs = False
    current_job_id: Optional[str] = None
    current_job_name: Optional[str] = None
    current_uses_sdk_action = False
    current_uses_container = False
    in_container_block = False
    container_indent: Optional[int] = None

    patterns: List[JobPattern] = []

    def flush_current_job() -> None:
        """Persist the currently tracked job into ``patterns`` if relevant."""

        nonlocal current_job_id, current_job_name
        nonlocal current_uses_sdk_action, current_uses_container

        if current_job_id is None:
            return
        if not (current_uses_sdk_action or current_uses_container):
            return

        name_template = current_job_name or current_job_id
        regex = template_to_regex(name_template)
        patterns.append(
            JobPattern(
                job_id=current_job_id,
                name_template=name_template,
                name_regex=regex,
                uses_sdk_action=current_uses_sdk_action,
                uses_container_image=current_uses_container,
            )
        )

    for raw in lines:
        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        # Detect the start of the jobs: section.
        if not in_jobs:
            if indent == 0 and stripped.startswith("jobs:"):
                in_jobs = True
            continue

        # A non-empty, non-comment top‑level key marks the end of the jobs
        # section. Flush the current job and stop scanning.
        if indent == 0 and stripped and not stripped.startswith("#"):
            flush_current_job()
            break

        # Detect a new job id at two spaces of indentation, e.g.::
        #
        #   jobs:
        #     build-dev-package:
        m_job = re.match(r"^(\s{2})([A-Za-z0-9_-]+):\s*$", raw)
        if m_job:
            flush_current_job()
            current_job_id = m_job.group(2)
            current_job_name = None
            current_uses_sdk_action = False
            current_uses_container = False
            in_container_block = False
            container_indent = None
            continue

        # Ignore any lines until we have seen at least one job id.
        if current_job_id is None:
            continue

        # Track when we are inside a job's ``container:`` block so that we can
        # distinguish it from arbitrary uses of the image string elsewhere.
        if re.match(r"^\s{4}container:\s*", raw):
            in_container_block = True
            container_indent = 4
            if image_substring in raw:
                current_uses_container = True
            continue

        if in_container_block:
            if indent <= (container_indent or 0):
                in_container_block = False
            else:
                if image_substring in raw:
                    current_uses_container = True
            # Regardless of whether we are still in the block, continue to the
            # next line.
            # noqa: SIM102  (we keep the explicit branch for clarity)
            continue

        # Capture the job's human‑readable ``name`` if present. This is what
        # appears in the GitHub UI and the jobs API.
        m_name = re.match(r"^\s{4}name:\s*(.+?)\s*$", raw)
        if m_name:
            name_val = m_name.group(1).strip()
            if (name_val.startswith("\"") and name_val.endswith("\"")) or (
                name_val.startswith("'") and name_val.endswith("'")
            ):
                name_val = name_val[1:-1]
            current_job_name = name_val
            continue

        # Detect uses of the openwrt/gh-action-sdk composite action in any
        # step. We do not care which particular step it is as long as the job
        # invokes the action at all.
        if sdk_action_substring in stripped:
            current_uses_sdk_action = True
            continue

    # Flush the final job if applicable.
    flush_current_job()
    return patterns


def parse_iso_date(s: str) -> _dt.datetime:
    """Parse a simple ISO‑8601 date string (YYYY-MM-DD).

    GitHub timestamps are already in UTC ("...Z" suffix). For date filters we
    operate in UTC as well.
    """

    try:
        return _dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=_dt.timezone.utc)
    except ValueError as exc:  # pragma: no cover - defensive
        raise argparse.ArgumentTypeError(str(exc)) from exc


def month_bucket(dt: _dt.datetime) -> str:
    """Return a ``YYYY-MM`` month bucket for a datetime value."""

    return f"{dt.year:04d}-{dt.month:02d}"


def load_workflow_revision(
    owner: str,
    repo: str,
    client: GitHubClient,
    sha: str,
    path: str,
    cache: Dict[Tuple[str, str], Optional[List[JobPattern]]],
) -> Optional[List[JobPattern]]:
    """Return job patterns for a particular ``(sha, path)`` pair.

    The function first tries to read the workflow from the local git clone
    using ``git show``. If that fails (for example because the clone is
    shallow), it falls back to the GitHub contents API.
    """

    cache_key = (sha, path)
    if cache_key in cache:
        return cache[cache_key]

    # Try local git history first; this avoids unnecessary API calls when the
    # repository clone already contains the commit.
    workflow_text: Optional[str] = None
    try:
        from subprocess import CalledProcessError, run  # imported lazily

        result = run(
            ["git", "show", f"{sha}:{path}"],
            check=True,
            capture_output=True,
            text=True,
        )
        workflow_text = result.stdout
    except Exception:  # pragma: no cover - if git is missing or commit unknown
        workflow_text = None

    if workflow_text is None:
        # Fallback path: use the contents API.
        workflow_text = client.get_workflow_contents(owner, repo, path, sha)

    if workflow_text is None:
        print(
            f"[warn] could not load workflow {path!r} at {sha[:8]} – "
            "treating as having no SDK jobs",
            file=sys.stderr,
        )
        cache[cache_key] = None
        return None

    patterns = parse_workflow_for_container_jobs(workflow_text)
    cache[cache_key] = patterns
    return patterns


def analyse_repository(
    owner: str,
    repo: str,
    client: GitHubClient,
    *,
    workflow_filters: Optional[Sequence[str]] = None,
    max_runs: Optional[int] = None,
    start_date: Optional[_dt.datetime] = None,
    end_date: Optional[_dt.datetime] = None,
) -> Tuple[List[RunUsage], Dict[str, dict]]:
    """Walk the repository's workflows and collect usage statistics.

    Returns a tuple of:

    * a list of per‑run usage records (``RunUsage``), and
    * a dictionary with per‑workflow metadata that can be fed directly into
      report generation.
    """

    workflows = client.list_workflows(owner, repo)

    # Optional filter by workflow name or path (substring match, case‑insensitive).
    def workflow_is_selected(w: dict) -> bool:
        if not workflow_filters:
            return True
        name = (w.get("name") or "").lower()
        path = (w.get("path") or "").lower()
        for f in workflow_filters:
            f_low = f.lower()
            if f_low in name or f_low in path:
                return True
        return False

    selected_workflows = [w for w in workflows if workflow_is_selected(w)]
    if not selected_workflows:
        raise SystemExit("No workflows matched the provided filters.")

    print(
        f"Analysing {len(selected_workflows)} workflows out of "
        f"{len(workflows)} total...",
        file=sys.stderr,
    )

    per_workflow_meta: Dict[str, dict] = {}
    run_usages: List[RunUsage] = []

    patterns_cache: Dict[Tuple[str, str], Optional[List[JobPattern]]] = {}

    scanned_runs = 0

    for wf in selected_workflows:
        wf_id = int(wf["id"])
        wf_name = wf.get("name") or "(unnamed)"
        wf_path = wf.get("path") or "(unknown path)"

        print(f"\n[workflow] {wf_name} ({wf_path})", file=sys.stderr)

        workflow_runs_with_usage = 0
        workflow_jobs_with_usage = 0

        for run in client.iter_workflow_runs(owner, repo, wf_id):
            if max_runs is not None and scanned_runs >= max_runs:
                break

            run_id = int(run["id"])
            created_str = run.get("created_at") or run.get("run_started_at")
            if not created_str:
                # Fall back to updated_at as a last resort.
                created_str = run.get("updated_at") or "1970-01-01T00:00:00Z"
            created_at = _dt.datetime.strptime(
                created_str, "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=_dt.timezone.utc)

            if start_date and created_at < start_date:
                continue
            if end_date and created_at >= end_date:
                continue

            scanned_runs += 1

            head_sha = run.get("head_sha") or ""
            run_path = run.get("path") or wf_path

            patterns = load_workflow_revision(
                owner,
                repo,
                client,
                head_sha,
                run_path,
                patterns_cache,
            )
            if not patterns:
                # This workflow revision did not define any SDK-using jobs.
                continue

            jobs = client.list_jobs_for_run(owner, repo, run_id)

            jobs_using_sdk = [
                job
                for job in jobs
                if any(p.matches(job.get("name") or "") for p in patterns)
            ]

            if not jobs_using_sdk:
                continue

            workflow_runs_with_usage += 1
            workflow_jobs_with_usage += len(jobs_using_sdk)

            run_usages.append(
                RunUsage(
                    run_id=run_id,
                    workflow_path=run_path,
                    created_at=created_at,
                    jobs_using_sdk=len(jobs_using_sdk),
                )
            )

        per_workflow_meta[wf_path] = {
            "workflow_id": wf_id,
            "name": wf_name,
            "path": wf_path,
            "runs_with_usage": workflow_runs_with_usage,
            "jobs_with_usage": workflow_jobs_with_usage,
        }

    return run_usages, per_workflow_meta


def build_aggregates(
    run_usages: Sequence[RunUsage],
    per_workflow_meta: Dict[str, dict],
) -> Dict[str, object]:
    """Compute top‑level and breakdown statistics from raw run data."""

    runs_with_usage = {ru.run_id for ru in run_usages}
    total_runs_with_usage = len(runs_with_usage)
    total_jobs_with_usage = sum(ru.jobs_using_sdk for ru in run_usages)

    runs_by_month: Counter[str] = Counter()
    jobs_by_month: Counter[str] = Counter()
    for ru in run_usages:
        bucket = month_bucket(ru.created_at)
        runs_by_month[bucket] += 1
        jobs_by_month[bucket] += ru.jobs_using_sdk

    # Per-workflow breakdown is mostly prepared already in per_workflow_meta.
    per_workflow = dict(per_workflow_meta)

    return {
        "total_runs_with_usage": total_runs_with_usage,
        "total_jobs_with_usage": total_jobs_with_usage,
        "runs_by_month": dict(sorted(runs_by_month.items())),
        "jobs_by_month": dict(sorted(jobs_by_month.items())),
        "per_workflow": per_workflow,
    }


def render_markdown_report(
    owner: str,
    repo: str,
    image_substring: str,
    sdk_action_substring: str,
    aggregates: Dict[str, object],
) -> str:
    """Render a human‑readable Markdown report from the statistics."""

    total_runs = aggregates["total_runs_with_usage"]
    total_jobs = aggregates["total_jobs_with_usage"]
    runs_by_month = aggregates["runs_by_month"]  # type: ignore[assignment]
    jobs_by_month = aggregates["jobs_by_month"]  # type: ignore[assignment]
    per_workflow = aggregates["per_workflow"]  # type: ignore[assignment]

    lines: List[str] = []
    lines.append("# GHCR OpenWrt SDK Usage Report")
    lines.append("")
    lines.append(f"Repository: `{owner}/{repo}`")
    lines.append("")
    lines.append("This report was generated by ``tools/analysis/"
                 "count_ghcr_openwrt_sdk_usage.py``.")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("- **Container image considered**: ``%s``" % image_substring)
    lines.append(
        "- **SDK action considered**: steps using ``%s`` are treated as running "
        "inside that image" % sdk_action_substring
    )
    lines.append("")
    lines.append(
        "- **Workflow runs with at least one job using the image**: "
        f"**{total_runs}**"
    )
    lines.append(
        "- **Jobs that used the image**: **%s**" % total_jobs
    )
    lines.append("")

    lines.append("## Breakdown by Workflow")
    lines.append("")
    lines.append("| Workflow file | Workflow name | Runs using image | Jobs using image |")
    lines.append("|--------------|--------------|-----------------|-----------------|")

    for wf_path, meta in sorted(per_workflow.items()):
        runs = meta.get("runs_with_usage", 0)
        jobs = meta.get("jobs_with_usage", 0)
        if runs == 0 and jobs == 0:
            continue
        name = meta.get("name", "")
        lines.append(
            f"| `{wf_path}` | {name} | {runs} | {jobs} |"
        )

    if not any(meta.get("runs_with_usage") or meta.get("jobs_with_usage") for meta in per_workflow.values()):
        lines.append("_No workflows with detected usage of the image were found._")

    lines.append("")
    lines.append("## Breakdown by Month")
    lines.append("")
    if runs_by_month:
        lines.append("| Month (UTC) | Runs using image | Jobs using image |")
        lines.append("|-------------|-----------------|-----------------|")
        for month in sorted(runs_by_month.keys()):
            r = runs_by_month[month]
            j = jobs_by_month.get(month, 0)
            lines.append(f"| {month} | {r} | {j} |")
    else:
        lines.append("_No runs matched the filters used for this report._")

    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("The counting logic is implemented directly in the "
                 "``count_ghcr_openwrt_sdk_usage.py`` script and can be "
                 "re‑run at any time. In short:")
    lines.append("")
    lines.append("1. **Discovery of workflows and runs**")
    lines.append("   - ``GET /repos/{owner}/{repo}/actions/workflows`` to list workflows.")
    lines.append(
        "   - ``GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs`` "
        "with pagination (``per_page=100``) to traverse all runs."
    )
    lines.append("2. **Job enumeration per run**")
    lines.append(
        "   - ``GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs`` to list "
        "jobs and their runtime names."
    )
    lines.append("3. **Workflow revision inspection**")
    lines.append(
        "   - For each run, resolve the workflow file used via ``head_sha`` and "
        "``path`` and load that revision either from the local git history "
        "(``git show <sha>:<path>``) or, if missing, via the GitHub contents "
        "API (``GET /repos/{owner}/{repo}/contents/{path}?ref=<sha>``)."
    )
    lines.append("   - A minimal line‑oriented parser scans the YAML for jobs that either:")
    lines.append(
        f"     - define a top‑level ``container:`` image containing "
        f"``{image_substring}``; or"
    )
    lines.append(
        f"     - contain a step whose ``uses:`` line references "
        f"``{sdk_action_substring}``."
    )
    lines.append("4. **Job and run matching**")
    lines.append(
        "   - For each job definition that uses the image, its ``name:`` "
        "template is converted into a regular expression that treats "
        "expression segments like ``${{ matrix.* }}`` as wildcards."
    )
    lines.append(
        "   - Runtime jobs returned by the API are matched against these "
        "patterns to identify which jobs in each run actually used the image."
    )
    lines.append("5. **Counting rules**")
    lines.append(
        "   - A **workflow run** is counted once if **any** of its jobs used "
        "the image."
    )
    lines.append(
        "   - A **job** is counted once per execution if its runtime name "
        "matches a job definition that uses the image. Matrix jobs therefore "
        "contribute one count per expanded job."
    )
    lines.append(
        "   - Steps that only probe the image's existence via registry HTTP "
        "requests but do not run inside the container are intentionally **not** "
        "counted."
    )

    lines.append("")
    lines.append(
        "To regenerate this report after new workflow runs have completed, "
        "re‑run the script and overwrite this file using the ``--output`` flag."
    )

    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count GitHub Actions jobs and runs that used the "
            "ghcr.io/openwrt/sdk image in a repository."
        )
    )

    parser.add_argument(
        "--repo",
        default="nagual2/openwrt-captive-monitor",
        help="Repository in the form 'owner/name' (default: %(default)s)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help=(
            "GitHub token to use for API requests. If omitted, the script "
            "uses the GITHUB_TOKEN environment variable or unauthenticated "
            "requests (subject to strict rate limits)."
        ),
    )
    parser.add_argument(
        "--image-substring",
        default=DEFAULT_IMAGE_SUBSTRING,
        help=(
            "Substring that identifies the SDK container image inside "
            "workflow files (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--sdk-action-substring",
        default=DEFAULT_SDK_ACTION_SUBSTRING,
        help=(
            "Substring that identifies steps invoking the OpenWrt SDK "
            "action (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--workflow",
        dest="workflows",
        action="append",
        help=(
            "Optional workflow name or path substring to restrict analysis. "
            "Can be passed multiple times. If omitted, all workflows are "
            "considered."
        ),
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help=(
            "Optional limit on the number of workflow runs to scan. This is "
            "primarily intended for testing the script in environments with "
            "very low rate limits."
        ),
    )
    parser.add_argument(
        "--start-date",
        type=parse_iso_date,
        help="Only consider workflow runs created on/after this date (UTC, YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=parse_iso_date,
        help="Only consider workflow runs created before this date (UTC, YYYY-MM-DD).",
    )
    parser.add_argument(
        "--output",
        help=(
            "If set, write a Markdown report to the given path. The summary "
            "statistics are always printed to stdout regardless."
        ),
    )

    args = parser.parse_args(argv)

    try:
        owner, repo = args.repo.split("/", 1)
    except ValueError:
        raise SystemExit("--repo must be in the form 'owner/name'")

    client = GitHubClient(token=args.token)

    run_usages, per_workflow_meta = analyse_repository(
        owner=owner,
        repo=repo,
        client=client,
        workflow_filters=args.workflows,
        max_runs=args.max_runs,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    aggregates = build_aggregates(run_usages, per_workflow_meta)

    # Print a concise summary to stdout for quick inspection.
    print(
        json.dumps(
            {
                "total_runs_with_usage": aggregates["total_runs_with_usage"],
                "total_jobs_with_usage": aggregates["total_jobs_with_usage"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    if args.output:
        report = render_markdown_report(
            owner,
            repo,
            args.image_substring,
            args.sdk_action_substring,
            aggregates,
        )
        output_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Markdown report written to {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
