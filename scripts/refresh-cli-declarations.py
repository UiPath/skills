#!/usr/bin/env python3
"""Refresh the snapshots of CLI declarations that skills restate, and report drift.

Several skills restate something the `uip` CLI declares: the case task types,
and later the rule types per scope and the browser bundle's command list. Each
restatement is checked against a committed snapshot of the declaration by a
test, so a hand-kept copy cannot drift from the snapshot unnoticed. What this
script closes is the other gap: the snapshot drifting from the CLI between
manual refreshes (MST-16782).

For every entry in DECLARATIONS it reads the declaration from the installed
CLI, compares the part a copy must match (not volatile fields such as schema
versions), and when that part moved: writes the snapshot, regenerates anything
generated from it, runs the declaration's tests, and records which hand-kept
copies now fail. The report is markdown, meant to be a PR body.

    python3 scripts/refresh-cli-declarations.py --report out.md   # refresh all, write the report
    python3 scripts/refresh-cli-declarations.py --check           # report only, write nothing

Exit: 0 when it ran (changed or not; `changed=true|false` goes to $GITHUB_OUTPUT
when set), 1 when a declaration could not be read from the CLI. A missing
command is a broken refresh, never drift: nothing is written for it.

Add a declaration by appending to DECLARATIONS: a module exposing `from_cli()`,
`load()` and the significant-part function, its snapshot path, the generators to
re-run, and the tests that hold its hand-kept copies.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Declaration:
    name: str  # shown in the PR title and body
    command: str  # the CLI command that declares it, for the report
    module: Path  # exposes from_cli(), load() and `significant`
    significant: str  # name of the function giving the part a copy must match
    snapshot: Path
    generators: tuple[tuple[str, ...], ...] = ()  # argv lists re-run after a refresh
    tests: tuple[str, ...] = ()  # pytest paths holding the hand-kept copies
    copies: tuple[str, ...] = ()  # hand-kept files, named in the report
    notes: tuple[Path, str] | None = None  # (module, function(data) -> lines): new lines reported, never failed


CASE_SHARED = REPO / "tests" / "tasks" / "uipath-maestro-case" / "_shared"

DECLARATIONS: tuple[Declaration, ...] = (
    Declaration(
        name="case task types",
        command="uip maestro case task-types list --output json",
        module=CASE_SHARED / "task_types.py",
        significant="lists",
        snapshot=CASE_SHARED / "task_types.json",
        generators=((sys.executable, str(CASE_SHARED / "task_types.py"), "--write-guide"),),
        tests=(str(CASE_SHARED / "test_task_types.py"),),
        copies=(
            "skills/uipath-planner/references/case/case-design-layers-guide.md (§ Task types table and count)",
            "skills/uipath-planner/references/case/case-sdd-conformance-checklist.md (item 8 count, item 6 detail markers)",
            "tests/tasks/uipath-maestro-case/_shared/sdd_check.py (TASK_TYPES, TASK_DETAIL_MARKERS)",
            "tests/tasks/uipath-planner/_shared/sdd_check.py (TASK_TYPES, TASK_DETAIL_MARKERS)",
        ),
    ),
    Declaration(
        name="case rule types per slot",
        command="uip maestro case rule-types list --output json",
        module=CASE_SHARED / "rule_types.py",
        significant="scopes",
        snapshot=CASE_SHARED / "rule_types.json",
        tests=(str(CASE_SHARED / "test_rule_types.py"),),
        copies=(
            "skills/uipath-planner/references/case/case-design-layers-guide.md (§ Lifecycle gates: Legal WHEN rules and Marks complete)",
            "tests/tasks/uipath-maestro-case/_shared/sdd_check.py (STAGE_ENTRY, TASK_ENTRY, … gate sets)",
            "tests/tasks/uipath-planner/_shared/sdd_check.py (STAGE_ENTRY, TASK_ENTRY, … gate sets)",
        ),
        notes=(CASE_SHARED / "rule_types.py", "unused"),
    ),
)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def list_diff(old: dict, new: dict) -> list[str]:
    """One line per list: what entries were added and removed."""
    lines = []
    for key in sorted(set(old) | set(new)):
        before = {json.dumps(x, sort_keys=True) for x in old.get(key) or []}
        after = {json.dumps(x, sort_keys=True) for x in new.get(key) or []}
        added = sorted(after - before)
        removed = sorted(before - after)
        if added or removed:
            parts = []
            if added:
                parts.append("added " + ", ".join(f"`{a}`" for a in added))
            if removed:
                parts.append("removed " + ", ".join(f"`{r}`" for r in removed))
            lines.append(f"- `{key}`: " + "; ".join(parts))
    return lines


def failing_tests(paths: tuple[str, ...]) -> tuple[bool, list[str]]:
    """Run the declaration's tests; return (passed, failing test ids)."""
    if not paths:
        return True, []
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rfE", "--no-header", *paths],
        capture_output=True, text=True, cwd=REPO,
    )
    failed = re.findall(r"^(?:FAILED|ERROR) (\S+)", result.stdout, re.M)
    return result.returncode == 0, [f.replace(str(REPO) + os.sep, "") for f in failed]


def refresh(decl: Declaration, write: bool) -> dict:
    """Refresh one declaration. Returns a result dict for the report."""
    module = load_module(decl.module)
    live = module.from_cli()
    if live is None:
        return {"decl": decl, "error": f"`{decl.command}` is not available in the installed CLI"}
    significant = getattr(module, decl.significant)
    old = module.load()
    try:
        moved = significant(live)
    except (KeyError, TypeError) as e:  # the CLI dropped or reshaped a part a copy restates
        return {"decl": decl, "error": f"`{decl.command}` no longer has the shape the snapshot records ({type(e).__name__}: {e})"}
    if significant(old) == moved:
        return {"decl": decl, "changed": False}
    result = {"decl": decl, "changed": True, "diff": list_diff(significant(old), significant(live))}
    if write:
        payload = json.loads(decl.snapshot.read_text())
        payload["Data"] = live
        decl.snapshot.write_text(json.dumps(payload, indent=2) + "\n")
        for argv in decl.generators:
            gen = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
            if gen.returncode != 0:
                sys.exit(f"generator {' '.join(argv)} failed:\n{gen.stdout}{gen.stderr}")
        result["passed"], result["failing"] = failing_tests(decl.tests)
    if decl.notes:
        # Only what this move added: the standing policy gaps would repeat in every PR.
        # A notes failure is reported, never raised, so it cannot cost the run its report.
        try:
            notes_of = getattr(load_module(decl.notes[0]), decl.notes[1])
            before = set(notes_of(old))
            result["notes"] = [line for line in notes_of(live) if line not in before]
        except Exception as e:  # noqa: BLE001
            result["notes"] = [f"- notes unavailable: {type(e).__name__}: {e}"]
    return result


def report(results: list[dict], cli_version: str) -> str:
    changed = [r for r in results if r.get("changed")]
    names = ", ".join(r["decl"].name for r in changed) or "nothing"
    out = [f"Automated refresh of CLI declaration snapshots against `@uipath/cli@{cli_version}`. Moved: {names}.", ""]
    for r in changed:
        d = r["decl"]
        out += [f"## {d.name}", "", f"Declared by `{d.command}`; snapshot `{rel(d.snapshot)}`.", "", "What moved:", *r["diff"], ""]
        if r.get("passed"):
            out += ["Every hand-kept copy still matches: the tests pass. This PR only updates the snapshot (and anything generated from it).", ""]
        elif "passed" in r:
            out += ["**These hand-kept copies no longer match**, so the tests below fail until they are updated in this PR:", ""]
            out += [f"- {c}" for c in d.copies] + ["", "Failing tests:", *[f"- `{t}`" for t in r["failing"]], ""]
        if r.get("notes"):
            out += ["Allowed by the CLI but not by the skills (policy, so nothing fails; widen a copy only on purpose):", *r["notes"], ""]
    for r in results:
        if r.get("error"):
            out += [f"**Could not read {r['decl'].name}:** {r['error']}. Nothing was written for it.", ""]
    if any("passed" in r and not r["passed"] for r in changed):
        out += ["Do not merge with failing tests: update each named copy to the new declaration, or, if the CLI change is wrong, fix it there and close this PR."]
    return "\n".join(out).rstrip() + "\n"


def cli_version() -> str:
    try:
        out = subprocess.run(["uip", "--version"], capture_output=True, text=True, timeout=60).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"
    raw = (out.strip().split() or ["unknown"])[-1]
    return re.sub(r"[^A-Za-z0-9._-]", "_", raw)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--report", type=Path, help="write the markdown report here")
    parser.add_argument("--check", action="store_true", help="compare only; write no snapshot")
    args = parser.parse_args(argv)

    results = [refresh(d, write=not args.check) for d in DECLARATIONS]
    changed = any(r.get("changed") for r in results)
    if args.report:
        args.report.write_text(report(results, cli_version()))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    for r in results:
        state = "ERROR" if r.get("error") else ("moved" if r.get("changed") else "current")
        print(f"{r['decl'].name}: {state}" + (f" — {r['error']}" if r.get("error") else ""))
    return 1 if any(r.get("error") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
