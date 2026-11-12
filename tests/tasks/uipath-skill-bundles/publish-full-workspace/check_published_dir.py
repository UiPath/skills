#!/usr/bin/env python3
"""Every `uip or skill-bundles publish` must name a directory holding the whole next version.

`publish` treats `--input` as the complete next version: a base file the directory lacks
is published as a deletion. So each published directory must still hold the files the
bundle already has (README.md, refund-skill/instructions.md) and carry the user's edit to
invoice-skill/instructions.md. Publishing ./changes, which holds only the edited file, fails here.

Exit codes: 0 every publish names a complete directory, 1 one does not or none happened,
2 the log cannot be read.
"""
import json
import sys
from pathlib import Path

LOG = Path("cli_mocks/calls.jsonl")
VERB = ["or", "skill-bundles", "publish"]
ALIAS = ["or", "skill-bundle", "publish"]
GLOBAL_VALUE_OPTIONS = {"--output", "--output-filter", "--log-level", "--log-file", "--profile"}
REQUIRED = ("README.md", "refund-skill/instructions.md", "invoice-skill/instructions.md")
EDIT = "more than 2%"


def strip_globals(argv: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(argv):
        tok = argv[i]
        if tok in GLOBAL_VALUE_OPTIONS:
            i += 2
            continue
        if tok in {"--json", "--interactive", "--no-interactive"} or any(
            tok.startswith(f"{o}=") for o in GLOBAL_VALUE_OPTIONS
        ):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def input_dir(args: list[str]) -> str | None:
    for i, tok in enumerate(args):
        if tok in ("--input", "-i") and i + 1 < len(args):
            return args[i + 1]
        if tok.startswith("--input="):
            return tok.split("=", 1)[1]
    return None


def read_publishes() -> list[list[str]]:
    if not LOG.exists():
        raise ValueError(f"{LOG} is missing: the uip recorder wrote no log")
    calls = []
    for n, line in enumerate(LOG.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{LOG}:{n} is not JSON: {exc}") from exc
        argv = row.get("argv") if isinstance(row, dict) else None
        if not isinstance(argv, list) or not all(isinstance(t, str) for t in argv):
            raise ValueError(f"{LOG}:{n} has no list-of-strings `argv`")
        args = strip_globals(argv)
        if row.get("tool", "uip") == "uip" and args[:3] in (VERB, ALIAS) and not {"--help", "-h"} & set(args):
            calls.append(args)
    return calls


def main() -> int:
    try:
        publishes = read_publishes()
    except ValueError as exc:
        print(f"cannot check: {exc}")
        return 2
    if not publishes:
        print("no publish call")
        return 1
    problems = []
    for args in publishes:
        raw = input_dir(args)
        if raw is None:
            problems.append(f"{args}: no --input")
            continue
        root = Path(raw)
        missing = [p for p in REQUIRED if not (root / p).is_file()]
        if missing:
            problems.append(f"--input {raw} lacks {missing}; they would be published as deletions")
            continue
        if EDIT not in (root / "invoice-skill/instructions.md").read_text(errors="replace"):
            problems.append(f"--input {raw} does not carry the edit to invoice-skill/instructions.md")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"{len(publishes)} publish call(s), each from a complete directory with the edit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
