#!/usr/bin/env python3
"""Pass if a recorded `uip df records <verb>` call matches a regex.

Reads the `uip` calls recorded by `_cli_recorder/uip`, so a command typed in
Bash and one run from a script the agent wrote count alike. Each call of the
given verb is matched as the text `uip <argv joined by spaces>`, followed on
new lines by any `--file` or stdin body the recorder captured. The pattern is
searched anywhere in that text, as a Bash-only `command_executed` criterion
searches the command text. Like that criterion, the call's exit
code is not checked.

Exit 0 on pass, 1 with a reason on failure.
"""

import argparse
import json
import re
import sys
from pathlib import Path

MAX_TEXT_CHARS = 20_000


def call_text(call: dict) -> str:
    parts = ["uip " + " ".join(str(arg) for arg in call.get("argv") or [])]
    for key in ("file_body", "stdin_body"):
        if isinstance(call.get(key), str):
            parts.append(call[key])
    return "\n".join(parts)[:MAX_TEXT_CHARS]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--verb", required=True, help="records subcommand, e.g. insert")
    parser.add_argument("--pattern", required=True)
    args = parser.parse_args()

    if not args.log.is_file():
        print(f"FAIL: no recorded uip calls at {args.log}", file=sys.stderr)
        sys.exit(1)
    pattern = re.compile(args.pattern)
    verb = ["df", "records", args.verb]
    seen = matched = 0
    for line in args.log.read_text(encoding="utf-8").splitlines():
        try:
            call = json.loads(line)
        except json.JSONDecodeError:
            continue
        argv = call.get("argv") if isinstance(call, dict) else None
        if not isinstance(argv, list) or not any(argv[i:i + 3] == verb for i in range(len(argv))):
            continue
        seen += 1
        if pattern.search(call_text(call)):
            matched += 1
    if matched == 0:
        print(f"FAIL: {seen} recorded `records {args.verb}` call(s), none match {args.pattern}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {matched} of {seen} recorded `records {args.verb}` call(s) match")


if __name__ == "__main__":
    main()
