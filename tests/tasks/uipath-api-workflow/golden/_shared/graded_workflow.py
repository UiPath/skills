#!/usr/bin/env python3
import argparse
import importlib
import sys
from pathlib import Path

GOLDEN = Path(__file__).resolve().parents[1]
GRADERS = {
    "jira_release_notes": "check_release_notes",
    "salesforce_expiring_contracts": "check_contracts",
    "vat_check": "check_vat",
}

sys.path.insert(0, str(GOLDEN / "_shared"))
from golden_connectors import workflow_paths  # noqa: E402


def shown(path):
    return f"./{path.relative_to(Path.cwd().resolve()).as_posix()}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print the Workflow.json a golden scenario's grader grades.")
    parser.add_argument("scenario", choices=sorted(GRADERS))
    parser.add_argument("--single", action="store_true",
                        help="list every project, marking the graded one; exit 1 unless there is exactly one")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(GOLDEN / args.scenario))
    chosen = importlib.import_module(GRADERS[args.scenario]).pick_workflow()
    if chosen is None:
        print("no Workflow.json inside a project folder", file=sys.stderr)
        return 1
    if not args.single:
        print(shown(chosen))
        return 0
    paths = workflow_paths()
    for path in paths:
        print(shown(path) + ("  (graded)" if path == chosen else ""))
    return 0 if len(paths) == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
