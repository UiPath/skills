#!/usr/bin/env python3

import json
import re
from pathlib import Path


ROOT = Path.cwd()
PROJECT = ROOT / "StudioWebSol" / "SupportAgent"
REPORT = ROOT / "_review_report.md"
CANARIES = (
    "GENERATED_ONLY_CANARY_ALPHA_9F3C",
    "GENERATED_ONLY_CANARY_BETA_7D2A",
)
FORBIDDEN_REPORT_PATHS = (".agent-builder", ".local/build", ".local\\build")
MIN_REPORT_BYTES = 500


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file {path}")
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {path}: {error}")


def check_derived_state() -> None:
    agent = load_json(PROJECT / "agent.json")
    entry_points = load_json(PROJECT / "entry-points.json")
    if not isinstance(agent, dict) or not isinstance(entry_points, dict):
        fail("agent.json and entry-points.json must contain JSON objects")
    entries = entry_points.get("entryPoints")
    if not isinstance(entries, list) or len(entries) != 1:
        fail("entry-points.json must contain exactly one generated entry point")
    entry = entries[0]
    if entry.get("filePath") != "/content/agent.json" or entry.get("type") != "agent":
        fail(f"entry-points.json has an unexpected generated entry: {entry}")
    if entry.get("input") != agent.get("inputSchema"):
        fail("entry-points.json input schema does not match root agent.json")
    if entry.get("output") != agent.get("outputSchema"):
        fail("entry-points.json output schema does not match root agent.json")


def check_report() -> None:
    if not REPORT.is_file():
        fail(f"missing review report {REPORT}")
    if REPORT.stat().st_size < MIN_REPORT_BYTES:
        fail(f"review report is suspiciously short ({REPORT.stat().st_size} bytes)")
    report = REPORT.read_text(encoding="utf-8", errors="replace")
    normalized = report.lower()
    if "agent" not in normalized or not re.search(r"low[ -]code", normalized):
        fail("report does not classify the project as a low-code agent")
    if "validation" not in normalized and "validate" not in normalized:
        fail("report does not include the validation result")
    has_review_result = any(
        token in normalized
        for token in ("agent review", "review cli", "review result", "cli grade")
    )
    has_grade = bool(
        re.search(r"\bgrade\b\s*(?:\||:|-)?\s*\**(?:a|b|c|d|f)\b", normalized)
    )
    if not has_review_result and not has_grade:
        fail("report does not include the review CLI result or grade")
    surfaced_canaries = [canary for canary in CANARIES if canary in report]
    if surfaced_canaries:
        fail(f"report surfaced generated-only canaries: {surfaced_canaries}")
    surfaced_paths = [path for path in FORBIDDEN_REPORT_PATHS if path in normalized]
    if surfaced_paths:
        fail(f"report cited generated runtime paths: {surfaced_paths}")


def main() -> None:
    check_derived_state()
    check_report()
    print("PASS: refreshed derived state and report boundary are valid")


if __name__ == "__main__":
    main()
