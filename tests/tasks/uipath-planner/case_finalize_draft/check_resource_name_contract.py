import re
from pathlib import Path


EXPECTED = {
    "Screen Resume": "CandidateResumeScreeningPhase0ProbeQ91",
    "Prepare Debrief Summary": "CandidateDebriefSummaryPhase0ProbeQ91",
}


text = Path("sdd.md").read_text(encoding="utf-8")

assert "**Resolved Resource:** <UNRESOLVED>" not in text, (
    "a runnable task lost its concrete intended resource name"
)

for task_name, resource_name in EXPECTED.items():
    task_match = re.search(
        rf"^##### Task .*?: {re.escape(task_name)}(?: \([^\n]*\))?\n"
        rf"(?P<body>.*?)(?=^---$|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert task_match, f'missing task block for "{task_name}"'
    task_body = task_match.group("body")
    assert f"**Resolved Resource:** {resource_name}" in task_body, (
        f'"{task_name}" did not preserve intended resource name {resource_name}'
    )
    assert "**Folder Path:** <UNRESOLVED>" in task_body, (
        f'"{task_name}" must keep its unresolved folder explicit'
    )
    assert "**Resource Identity:** <UNRESOLVED>" in task_body, (
        f'"{task_name}" must keep its unresolved identity explicit'
    )

agents_match = re.search(
    r"^### Agents\n(?P<body>.*?)(?=^### |\Z)",
    text,
    re.MULTILINE | re.DOTALL,
)
assert agents_match, "Section 4 omitted the Agents rollup"
agents_body = agents_match.group("body")

for task_name, resource_name in EXPECTED.items():
    # Grade the contract, not the exact column layout: the row exists, folder and
    # identity are <UNRESOLVED>, and Used By Tasks references the task. Tolerant of a
    # "(t02)"-style task-id suffix and of pipe-free content in the Inputs -> Outputs cell.
    row = re.search(
        rf"^\|\s*{re.escape(resource_name)}\s*\|(?P<rest>.*)$",
        agents_body,
        re.MULTILINE,
    )
    assert row, f"Section 4 Agents rollup is missing a row for {resource_name}"
    cells = [c.strip() for c in row.group("rest").rstrip().rstrip("|").split("|")]
    # After the name cell: Folder | Resource ID | Inputs -> Outputs | Used By Tasks
    assert len(cells) >= 4, (
        f"{resource_name} Section 4 row has too few columns: {cells}"
    )
    folder, resource_id, used_by = cells[0], cells[1], cells[-1]
    assert folder == "<UNRESOLVED>", (
        f"{resource_name} Section 4 folder must be <UNRESOLVED>, got {folder!r}"
    )
    assert resource_id == "<UNRESOLVED>", (
        f"{resource_name} Section 4 resource id must be <UNRESOLVED>, got {resource_id!r}"
    )
    assert task_name in used_by, (
        f'{resource_name} Section 4 "Used By Tasks" ({used_by!r}) does not reference "{task_name}"'
    )
