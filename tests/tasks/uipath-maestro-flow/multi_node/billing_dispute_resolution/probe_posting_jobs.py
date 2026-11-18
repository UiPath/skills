#!/usr/bin/env python3
"""Advisory probe: did the posting leave an Orchestrator job on the tenant?

FinancialPostingFunction writes no record of its own, so the only trace a
posting could leave on the tenant is its job. Nothing has yet proven that an
API workflow called from a `flow debug` run creates a job, or in which folder,
so this criterion is advisory: it prints what it finds so a run can settle that.

It reads the time window the effects check left for the same case
(`.grading/posting_window_<case>.json`), lists FinancialPostingFunction jobs
created in that window across all folders, and keeps those whose input cites
the disputed invoice. The tenant is shared and other tasks post the same
invoice, so a job in the window is evidence, not proof, that THIS run made it.

  overcharge       passes when at least one such job is Successful.
  no-discrepancy   passes when there is none.

Usage: probe_posting_jobs.py overcharge|no-discrepancy
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

PROCESS = "FinancialPostingFunction"
WINDOW_FILE = ".grading/posting_window_{case}.json"
CASES = ("overcharge", "no-discrepancy")
# The job record can land a little after the debug run returns.
SLACK = timedelta(seconds=60)


def _get(d, *keys):
    for k in keys:
        for kk, v in (d or {}).items():
            if kk.lower() == k.lower():
                return v
    return None


def _parse_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def list_jobs(created_after):
    cmd = ["uip", "or", "jobs", "list", "--all-folders", "--process-name", PROCESS,
           "--created-after", created_after, "--all-fields", "--output", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    try:
        envelope = json.loads(r.stdout)
    except ValueError:
        sys.exit(f"FAIL: `{' '.join(cmd)}` gave no JSON (exit {r.returncode}): {r.stderr.strip()[:300]}")
    data = _get(envelope, "Data")
    if isinstance(data, dict):
        data = _get(data, "items", "value", "jobs") or []
    if not isinstance(data, list):
        sys.exit(f"FAIL: unexpected jobs list shape: {str(envelope)[:300]}")
    return data


def jobs_in_window(jobs, window):
    start = _parse_time(window["startedAt"])
    end = _parse_time(window["endedAt"]) + SLACK
    kept = []
    for job in jobs:
        created = _parse_time(_get(job, "CreationTime", "creationTime", "StartTime"))
        inputs = json.dumps(_get(job, "InputArguments", "inputArguments") or "")
        if created and start <= created <= end and window["invoice"] in inputs:
            kept.append(job)
    return kept


def verdict(case, matched):
    successful = [j for j in matched if str(_get(j, "State")).lower() == "successful"]
    if case == "overcharge" and not successful:
        return f"FAIL: no Successful {PROCESS} job for the invoice during the overcharge run"
    if case == "no-discrepancy" and matched:
        return f"FAIL: {len(matched)} {PROCESS} job(s) for the invoice during a run that must not post"
    return None


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit(f"usage: probe_posting_jobs.py {'|'.join(CASES)}")
    case = sys.argv[1]
    try:
        with open(WINDOW_FILE.format(case=case)) as f:
            window = json.load(f)
    except OSError:
        sys.exit(f"FAIL: no debug window for {case}: the effects check did not finish its debug run")

    jobs = list_jobs(window["startedAt"])
    print(f"{len(jobs)} {PROCESS} job(s) created since {window['startedAt']} (debug jobKey {window.get('jobKey')})")
    for job in jobs[:10]:
        print("  ", json.dumps({k: _get(job, k) for k in (
            "Key", "State", "CreationTime", "OrganizationUnitFullyQualifiedName",
            "InputArguments", "ParentOperationId", "Source")}))
    if jobs:
        print(f"fields on a job: {sorted(jobs[0])}")

    matched = jobs_in_window(jobs, window)
    print(f"{len(matched)} job(s) in the debug window citing {window['invoice']}")
    failure = verdict(case, matched)
    if failure:
        sys.exit(failure)
    print(f"OK: {case}: the tenant's job record matches")


if __name__ == "__main__":
    main()
