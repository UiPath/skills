#!/usr/bin/env python3
"""Verify the digitize lifecycle e2e against the tenant.

Takes the runId the agent saved in run.json, reads that run back with the CLI,
and requires a succeeded one-page digitization whose text is the fixture's.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

FOLDER = "Shared"
EXPECTED_TEXT = ("INV-2041", "Northwind Traders")


def fail(msg: str) -> NoReturn:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def saved_run_id() -> str:
    path = Path.cwd() / "run.json"
    if not path.exists():
        fail("run.json not found")
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"run.json is not valid JSON: {exc}")
    run = blob.get("Data", blob) if isinstance(blob, dict) else None
    run_id = run.get("runId") if isinstance(run, dict) else None
    if not isinstance(run_id, str) or not run_id:
        fail("run.json has no runId")
    return run_id


def read_run(run_id: str) -> dict:
    proc = subprocess.run(
        ["uip", "documents", "runs", "get", run_id, "--folder-path", FOLDER, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        fail(f"runs get printed no JSON (exit {proc.returncode}): {proc.stderr.strip()[:300]}")
    if envelope.get("Result") != "Success" or not isinstance(envelope.get("Data"), dict):
        fail(f"runs get answered {envelope.get('Result')}: {envelope.get('Message')}")
    return envelope["Data"]


def require_text(text: str, source: str) -> None:
    for token in EXPECTED_TEXT:
        if token not in text:
            fail(f"{source} does not contain {token!r}")


def main() -> None:
    run = read_run(saved_run_id())
    if run.get("capability") != "digitize" or run.get("status") != "succeeded":
        fail(f"run is {run.get('capability')}/{run.get('status')}, expected digitize/succeeded")
    result = run.get("result") or {}
    if result.get("pageCount") != 1:
        fail(f"pageCount is {result.get('pageCount')}, expected 1")
    require_text(result.get("markdown") or "", "the run's markdown")

    page = Path.cwd() / "page1.md"
    if not page.exists():
        fail("page1.md not found")
    require_text(page.read_text(encoding="utf-8"), "page1.md")
    print("OK: the run succeeded on the tenant and page1.md holds its text")


if __name__ == "__main__":
    main()
