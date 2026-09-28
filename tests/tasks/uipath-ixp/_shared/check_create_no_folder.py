"""Grade that every recorded `uip ixp projects create` call passed no folder.

`cli_called` matches `positional` as a PREFIX, so `positional: ["test project"]`
also accepts `create "test project" ./docs`. This checks the complement: after
the name, only flags may follow. Reads the `record_cli` log, whose argv is a
list, so a quoted name with a space stays one argument.

Exit 0: at least one create call, none with a second positional.
Exit 1: no create call, or one passed a folder.
"""

import json
import sys
from pathlib import Path

LOG = Path("cli_mocks/calls.jsonl")
VERB = ["ixp", "projects", "create"]
# Flags of `projects create` that take a value, per `uip ixp projects create --help`.
VALUE_FLAGS = {"-d", "--description", "--output", "--output-filter", "--log-level", "--log-file", "--profile"}


def extra_positionals(args: list[str]) -> list[str]:
    """Positionals after the verb, minus the first (the project name)."""
    positionals: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        index += 1
        if token == "--":
            positionals.extend(args[index:])
            break
        if token.startswith("-") and token != "-":
            if "=" not in token and token in VALUE_FLAGS:
                index += 1
            continue
        positionals.append(token)
    return positionals[1:]


def main() -> int:
    if not LOG.exists():
        print(f"FAIL: {LOG} not found - no uip call was recorded")
        return 1
    creates = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        argv = record.get("argv") or []
        if record.get("tool") == "uip" and argv[: len(VERB)] == VERB:
            creates.append(argv)
    if not creates:
        print("FAIL: no `uip ixp projects create` call was recorded")
        return 1
    for argv in creates:
        extra = extra_positionals(argv[len(VERB) :])
        if extra:
            print(f"FAIL: `{' '.join(argv)}` passes a folder argument {extra!r} - not an empty project")
            return 1
    print(f"OK: {len(creates)} create call(s), none with a folder argument")
    return 0


if __name__ == "__main__":
    sys.exit(main())
