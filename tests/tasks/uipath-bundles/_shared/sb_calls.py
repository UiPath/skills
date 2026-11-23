"""Read the `uip` call log the way the CLI reads argv, for the skill-bundle graders.

Global options (cli utils/globalOptions.ts) are stripped wherever they appear. Commander then
parses the command's own options in every spelling (`--opt v`, `--opt=v`, `-o v`, `-ov`); the
last occurrence wins. Both command spellings, `skill-bundles` and its alias `skill-bundle`,
count, and `--help` renders are ignored.

A grader passes `options` ({verb: ({long option taking a value: short alias or None}, {switch})})
and, for nested verbs such as `tags set`, the `prefix` before the verb (("tags",)). Each call
comes back as (verb, positionals, {long option: last value}).

Exit codes from `main`: 0 pass, 1 fail, 2 the log cannot be read.
"""
import json
import sys
from pathlib import Path

LOG = Path("cli_mocks/calls.jsonl")
GROUPS = ("skill-bundles", "skill-bundle")
GLOBAL_VALUE = {"--output", "--output-filter", "--log-level", "--log-file", "--profile"}
GLOBAL_SWITCH = {"--json", "--interactive", "--no-interactive"}
HELP = {"--help", "-h"}


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


def parse(args, values, switches):
    """(positionals, {long option: last value}) the way Commander reads these options."""
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


def calls(options, prefix=()):
    """Every non-help `or skill-bundles <prefix> <verb>` call in log order."""
    if not LOG.exists():
        raise ValueError(f"{LOG} is missing: the uip recorder wrote no log")
    head = 2 + len(prefix)
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
        if (len(args) > head and args[0] == "or" and args[1] in GROUPS
                and tuple(args[2:head]) == tuple(prefix) and args[head] in options):
            pos, opts = parse(args[head + 1:], *options[args[head]])
            out.append((args[head], pos, opts))
    return out


def main(script, checks, options, prefix=()):
    """Run the check named by argv[1] over the parsed log; print problems; return the exit code."""
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in checks:
        print(f"usage: {script} {'|'.join(checks)}")
        return 2
    try:
        log = calls(options, prefix)
    except ValueError as exc:
        print(f"cannot check: {exc}")
        return 2
    problems = checks[mode](log)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"{mode}: ok")
    return 0
