#!/usr/bin/env python3
"""Grade the publish-full-workspace task from the `uip` call log.

Modes:
  publish  Every `publish` names finance-skills (or its key), folder Shared, and an --input directory that
           holds the whole next version: the files the bundle already has (README.md,
           refund-skill/instructions.md) and the user's edit to invoice-skill/instructions.md.
           `publish` treats --input as the complete next version, so a base file the directory
           lacks is a deletion. At least one publish must happen.
  status   An offline `status` inspected the published directory before its first publish.

argv is read the way the CLI reads it (see _shared/sb_calls.py). The recorder logs no working
directory, so a relative --input resolves from the task root, where the task tells the agent to
run `uip`.

Exit codes: 0 pass, 1 fail, 2 the log cannot be read.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from sb_calls import main  # noqa: E402

BUNDLES = {"finance-skills", "5e6f7a8b-0000-0000-0000-000000000004"}
FOLDER = "Shared"
REQUIRED = ("README.md", "refund-skill/instructions.md", "invoice-skill/instructions.md")
EDIT = "more than 2%"

# The command's own options: long name -> short alias for those taking a value, and switches.
OPTIONS = {
    "publish": ({"--tenant": "-t", "--folder-path": None, "--folder-key": None,
                 "--input": "-i", "--message": "-m", "--base-version": None},
                {"--include-hidden"}),
    "status": ({"--input": "-i"}, {"--include-hidden"}),
}


def resolved(raw):
    return Path(raw).resolve() if raw is not None else Path(".").resolve()


def check_publish(log):
    publishes = [c for c in log if c[0] == "publish"]
    if not publishes:
        return ["no publish call"]
    problems = []
    for _, pos, opts in publishes:
        bundle = pos[0] if pos else None
        if bundle not in BUNDLES:
            problems.append(f"publish targets {bundle!r}, not finance-skills")
            continue
        if opts.get("--folder-path") != FOLDER:
            problems.append(f"publish goes to folder {opts.get('--folder-path')!r}, not {FOLDER}")
            continue
        raw = opts.get("--input")
        if raw is None:
            problems.append("publish has no --input")
            continue
        root = resolved(raw)
        missing = [p for p in REQUIRED if not (root / p).is_file()]
        if missing:
            problems.append(f"--input {raw} lacks {missing}; they would be published as deletions")
        elif EDIT not in (root / "invoice-skill/instructions.md").read_text(errors="replace"):
            problems.append(f"--input {raw} does not carry the edit to invoice-skill/instructions.md")
    return problems


def check_status(log):
    first = next((i for i, c in enumerate(log) if c[0] == "publish"), None)
    if first is None:
        return ["no publish call"]
    target = resolved(log[first][2].get("--input"))
    seen = [resolved(c[2].get("--input")) for c in log[:first] if c[0] == "status"]
    if target not in seen:
        return [f"no status inspected {target} before the first publish (status ran on {[str(p) for p in seen]})"]
    return []


if __name__ == "__main__":
    sys.exit(main("check_published_dir.py", {"publish": check_publish, "status": check_status}, OPTIONS))
