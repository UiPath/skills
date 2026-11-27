#!/usr/bin/env python3
"""Verify the digitize lifecycle e2e against the tenant.

Takes the RunId the agent saved in run.json, reads that run back with the CLI,
and requires a succeeded one-page digitization whose text is the fixture's and
a page1.md identical to the page-1 markdown the service returns for that run.
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
    run_id = run.get("RunId") if isinstance(run, dict) else None
    if not isinstance(run_id, str) or not run_id:
        fail("run.json has no RunId")
    return run_id


def uip_data(*args: str) -> dict:
    command = " ".join(args[:2])
    proc = subprocess.run(
        ["uip", "documents", *args, "--folder-path", FOLDER, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        fail(f"{command} printed no JSON (exit {proc.returncode}): {proc.stderr.strip()[:300]}")
    if envelope.get("Result") != "Success" or not isinstance(envelope.get("Data"), dict):
        fail(f"{command} answered {envelope.get('Result')}: {envelope.get('Message')}")
    return envelope["Data"]


def normalized(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def require_text(text: str, source: str) -> None:
    for token in EXPECTED_TEXT:
        if token not in text:
            fail(f"{source} does not contain {token!r}")


def main() -> None:
    run_id = saved_run_id()
    run = uip_data("runs", "get", run_id)
    if run.get("Capability") != "Digitize" or run.get("Status") != "Succeeded":
        fail(f"run is {run.get('Capability')}/{run.get('Status')}, expected Digitize/Succeeded")
    result = run.get("Result") or {}
    if result.get("PageCount") != 1:
        fail(f"PageCount is {result.get('PageCount')}, expected 1")
    require_text(result.get("Markdown") or "", "the run's markdown")

    page = Path.cwd() / "page1.md"
    if not page.exists():
        fail("page1.md not found")
    expected = uip_data("pages", "get", "1", "--run-id", run_id, "--format", "markdown").get("Content")
    if not isinstance(expected, str) or not expected.strip():
        fail("pages get returned no markdown for page 1")
    if normalized(page.read_text(encoding="utf-8")) != normalized(expected):
        fail("page1.md differs from the page-1 markdown the service returns for the run")
    print("OK: the run succeeded on the tenant and page1.md is its page 1")


if __name__ == "__main__":
    main()
