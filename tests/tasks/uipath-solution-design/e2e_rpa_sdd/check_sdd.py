"""Validate the generated SDD for structural completeness and content quality.

Exit 0 if all checks pass, exit 1 with diagnostic output on failure.
"""

import re
import sys
from pathlib import Path

SDD_FILE = "employee-onboarding-data-entry-sdd.md"

# Required sections from the RPA SDD template (## N. Title format)
REQUIRED_SECTIONS = [
    "Process Overview",
    "Process Map",
    "Detailed Process Steps",
    "Business Rules",
    "Data Definitions",
    "Exception Handling",
    "Error Handling",
    "Application Inventory",
    "Credentials",
    "Project Structure",
    "Implementation Mode",
    "Testing Strategy",
    "Implementation Plan",
]

# Minimum expected items in key tables
MIN_PROCESS_STEPS = 5
MIN_BUSINESS_EXCEPTIONS = 2
MIN_SYSTEM_ERRORS = 2
MIN_APPLICATIONS = 4
MIN_CREDENTIALS = 3
MIN_IMPLEMENTATION_TASKS = 3

# Content markers that should appear
EXPECTED_MARKERS = [
    "Employee Onboarding Data Entry",
    "Workday",
    "Active Directory",
    "SharePoint",
]


def load_sdd() -> str:
    path = Path(SDD_FILE)
    if not path.exists():
        print(f"FAIL: {SDD_FILE} not found")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def check_sections(content: str) -> list[str]:
    """Verify required sections exist as headings."""
    failures = []
    for section in REQUIRED_SECTIONS:
        # Match ## N. Section or # N. Section (with optional number)
        pattern = rf"^#{1,3}\s+(\d+\.\s+)?{re.escape(section)}"
        if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            failures.append(f"Missing section: {section}")
    return failures


def check_line_count(content: str) -> list[str]:
    """SDD should be between 100 and 1200 lines."""
    lines = content.strip().split("\n")
    if len(lines) < 100:
        return [f"SDD too short: {len(lines)} lines (minimum 100)"]
    if len(lines) > 1200:
        return [f"SDD too long: {len(lines)} lines (maximum 1200)"]
    return []


def count_table_rows(content: str, section_pattern: str) -> int:
    """Count data rows in the first markdown table after a section heading."""
    match = re.search(section_pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return 0

    after_heading = content[match.end() :]
    rows = 0
    in_table = False
    for line in after_heading.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            # Skip header separator row (|---|---|)
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                in_table = True
                continue
            if in_table:
                rows += 1
        elif in_table and not stripped.startswith("|"):
            break  # End of table
    return rows


def check_table_minimums(content: str) -> list[str]:
    """Verify key tables have enough rows."""
    failures = []

    steps = count_table_rows(content, r"^#{1,3}\s+.*(?:Step Summary|Detailed Process Steps)")
    if steps < MIN_PROCESS_STEPS:
        failures.append(
            f"Process steps table has {steps} rows (minimum {MIN_PROCESS_STEPS})"
        )

    exceptions = count_table_rows(content, r"^#{1,3}\s+.*Exception Handling")
    if exceptions < MIN_BUSINESS_EXCEPTIONS:
        failures.append(
            f"Exception table has {exceptions} rows (minimum {MIN_BUSINESS_EXCEPTIONS})"
        )

    errors = count_table_rows(content, r"^#{1,3}\s+.*Error Handling")
    if errors < MIN_SYSTEM_ERRORS:
        failures.append(
            f"Error table has {errors} rows (minimum {MIN_SYSTEM_ERRORS})"
        )

    apps = count_table_rows(content, r"^#{1,3}\s+.*Application Inventory")
    if apps < MIN_APPLICATIONS:
        failures.append(
            f"Application inventory has {apps} rows (minimum {MIN_APPLICATIONS})"
        )

    creds = count_table_rows(content, r"^#{1,3}\s+.*Credentials")
    if creds < MIN_CREDENTIALS:
        failures.append(
            f"Credentials table has {creds} rows (minimum {MIN_CREDENTIALS})"
        )

    return failures


def check_implementation_plan(content: str) -> list[str]:
    """Verify the implementation plan has enough tasks with structure."""
    failures = []

    task_pattern = r"^#{1,4}\s+Task\s+\d+"
    tasks = re.findall(task_pattern, content, re.MULTILINE)
    if len(tasks) < MIN_IMPLEMENTATION_TASKS:
        failures.append(
            f"Implementation plan has {len(tasks)} tasks (minimum {MIN_IMPLEMENTATION_TASKS})"
        )

    if "Dependencies:" not in content and "**Dependencies:**" not in content:
        failures.append("Implementation tasks missing 'Dependencies:' field")

    if "References:" not in content and "**References:**" not in content:
        failures.append("Implementation tasks missing 'References:' field")

    return failures


def check_content_markers(content: str) -> list[str]:
    """Verify key PDD data carried through to SDD."""
    failures = []
    for marker in EXPECTED_MARKERS:
        if marker.lower() not in content.lower():
            failures.append(f"Missing expected content: {marker}")
    return failures


def check_no_unfilled_placeholders(content: str) -> list[str]:
    """Check for leftover template placeholders like <PROCESS_NAME>."""
    # Match <UPPER_SNAKE_CASE> but not HTML tags or mermaid syntax
    placeholders = re.findall(r"<[A-Z][A-Z_]{3,}>", content)
    if placeholders:
        unique = list(set(placeholders))[:5]
        return [f"Unfilled template placeholders found: {', '.join(unique)}"]
    return []


def check_mermaid_diagram(content: str) -> list[str]:
    """Verify at least one mermaid diagram exists."""
    if "```mermaid" not in content:
        return ["No mermaid diagram found (Process Map section should have one)"]
    return []


def check_workflow_inventory(content: str) -> list[str]:
    """Verify the workflow inventory has entries."""
    rows = count_table_rows(content, r"^#{1,4}\s+.*Workflow Inventory")
    if rows < 3:
        return [f"Workflow inventory has {rows} rows (minimum 3)"]
    return []


def main():
    content = load_sdd()
    all_failures = []

    all_failures.extend(check_sections(content))
    all_failures.extend(check_line_count(content))
    all_failures.extend(check_table_minimums(content))
    all_failures.extend(check_implementation_plan(content))
    all_failures.extend(check_content_markers(content))
    all_failures.extend(check_no_unfilled_placeholders(content))
    all_failures.extend(check_mermaid_diagram(content))
    all_failures.extend(check_workflow_inventory(content))

    if all_failures:
        print(f"FAIL: {len(all_failures)} check(s) failed:")
        for f in all_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("PASS: All SDD structure checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
