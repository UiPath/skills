#!/usr/bin/env python3
"""Grade the publish-full-workspace task from the `uip` call log.

Modes:
  publish  Every `publish` names finance-skills (or its key), folder Shared, and an --input directory that
           holds the whole next version: the files the bundle already has (README.md,
           refund-skill/instructions.md) and the user's edit to invoice-skill/instructions.md.
           `publish` treats --input as the complete next version, so a base file the directory
           lacks is a deletion. At least one publish must happen.
  status   An offline `status` inspected the published directory before its first publish.

argv is read the way the CLI reads it: global options (cli utils/globalOptions.ts) are
stripped wherever they appear; then Commander parses the command's own options in every
spelling (`--opt v`, `--opt=v`, `-o v`, `-ov`), the last occurrence winning. Both command
spellings, `skill-bundles` and its alias `skill-bundle`, count. The recorder logs no
working directory, so a relative --input resolves from the task root, where the task tells
the agent to run `uip`.

Exit codes: 0 pass, 1 fail, 2 the log cannot be read.
"""
import json
import sys
from pathlib import Path

LOG = Path("cli_mocks/calls.jsonl")
BUNDLES = {"finance-skills", "5e6f7a8b-0000-0000-0000-000000000004"}
FOLDER = "Shared"
REQUIRED = ("README.md", "refund-skill/instructions.md", "invoice-skill/instructions.md")
EDIT = "more than 2%"

GLOBAL_VALUE = {"--output", "--output-filter", "--log-level", "--log-file", "--profile"}
GLOBAL_SWITCH = {"--json", "--interactive", "--no-interactive"}
HELP = {"--help", "-h"}
# The command's own options: long name -> short alias, and which take a value.
OPTIONS = {
    "publish": ({"--tenant": "-t", "--folder-path": None, "--folder-key": None,
                 "--input": "-i", "--message": "-m", "--base-version": None},
                {"--include-hidden"}),
    "status": ({"--input": "-i"}, {"--include-hidden"}),
}


def strip_globals(argv):
    out, i = [], 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--":
            out.extend(argv[i:])
            break
        if tok in GLOBAL_VALUE:
            i += 2
            continue
        if tok in GLOBAL_SWITCH or any(tok.startswith(f"{o}=") for o in GLOBAL_VALUE):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def parse(args, verb):
    """(positionals, {long option: last value}) the way Commander reads `verb`'s options."""
    values, switches = OPTIONS[verb]
    short = {s: name for name, s in values.items() if s}
    pos, opts, i = [], {}, 0
    while i < len(args):
        tok = args[i]
        if tok == "--":
            pos.extend(args[i + 1:])
            break
        if tok.startswith("--"):
            name, eq, val = tok.partition("=")
            if name in values:
                if eq:
                    opts[name] = val
                elif i + 1 < len(args):
                    opts[name] = args[i + 1]
                    i += 1
            elif name in switches:
                opts[name] = True
        elif tok.startswith("-") and len(tok) > 1:
            name = short.get(tok[:2])
            if name and len(tok) > 2:
                opts[name] = tok[2:]
            elif name and i + 1 < len(args):
                opts[name] = args[i + 1]
                i += 1
        else:
            pos.append(tok)
        i += 1
    return pos, opts


def calls():
    """Every non-help skill-bundle call in log order, as (verb, positionals, options)."""
    if not LOG.exists():
        raise ValueError(f"{LOG} is missing: the uip recorder wrote no log")
    out = []
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
        if row.get("tool", "uip") != "uip" or HELP & set(argv):
            continue
        args = strip_globals(argv)
        if len(args) >= 3 and args[0] == "or" and args[1] in ("skill-bundles", "skill-bundle") and args[2] in OPTIONS:
            pos, opts = parse(args[3:], args[2])
            out.append((args[2], pos, opts))
    return out


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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("publish", "status"):
        print("usage: check_published_dir.py publish|status")
        return 2
    try:
        log = calls()
    except ValueError as exc:
        print(f"cannot check: {exc}")
        return 2
    problems = check_publish(log) if mode == "publish" else check_status(log)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"{mode}: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
