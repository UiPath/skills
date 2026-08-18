#!/usr/bin/env python3

import json
import re
from pathlib import Path


ROOT = Path.cwd()
PROJECT = ROOT / "SupportSol" / "SupportAgent"
REPORT = ROOT / "_review_report.md"
CANARIES = (
    "GENERATED_ONLY_CANARY_ALPHA_9F3C",
    "GENERATED_ONLY_CANARY_BETA_7D2A",
)
REFRESH_MANAGED_TOKENS = (
    ".agent-builder",
    ".local/build",
    "entry-points.json",
    "legacyrequest",
    "legacyresponse",
)
FINDING_SECTION_PREFIXES = (
    "critical findings",
    "warnings",
    "improvement opportunities",
)
HEADING = re.compile(r"^#{2,4}\s+(.+?)\s*$")
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


def mentions_refresh_managed(line: str) -> bool:
    lowered = line.lower()
    return any(token in lowered for token in REFRESH_MANAGED_TOKENS)


def defect_sections(report: str):
    heading = ""
    lines: list[str] = []
    for line in report.splitlines():
        match = HEADING.match(line)
        if not match:
            lines.append(line)
            continue
        if heading.lower().startswith(FINDING_SECTION_PREFIXES):
            yield heading, lines
        heading, lines = match.group(1), []
    if heading.lower().startswith(FINDING_SECTION_PREFIXES):
        yield heading, lines


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
    summary_grade = re.search(
        r"(?m)^\s*-\s+\*\*Agent Grade:\*\*\s+([ABCDF])(?:\s|$)", report
    )
    if not summary_grade:
        fail("report does not include a valid Summary Agent Grade")
    final_grade = re.search(
        r"(?m)^\*\*Final grade: ([ABCDF])\*\*\Z", report.rstrip()
    )
    if not final_grade:
        fail("report does not end with '**Final grade: <A-F>**'")
    if summary_grade.group(1) != final_grade.group(1):
        fail("Summary Agent Grade and final grade do not match")
    surfaced_canaries = [canary for canary in CANARIES if canary in report]
    if surfaced_canaries:
        fail(f"report surfaced generated-only canaries: {surfaced_canaries}")
    for heading, lines in defect_sections(report):
        cited = [line.strip() for line in lines if mentions_refresh_managed(line)]
        if cited:
            fail(
                f"report files refresh-managed state as a defect under "
                f"'{heading}': {cited[:2]}"
            )


def main() -> None:
    check_derived_state()
    check_report()
    print("PASS: refreshed derived state, report boundary, and grade footer are valid")


if __name__ == "__main__":
    main()
