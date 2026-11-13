#!/usr/bin/env python3
"""Pass if at least --min recorded `uip df records` calls match a regex.

`_cli_recorder/uip` logs each such call as a JSON line. A call is matched as the
text `uip <argv joined by spaces>` followed by any `--file` or stdin body it
captured, so a command typed in Bash and one run from a script count alike. Like
a Bash `command_executed` check, the exit code is not checked.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def call_text(call):
    parts = ["uip " + " ".join(map(str, call.get("argv") or []))]
    parts += [call[k] for k in ("file_body", "stdin_body") if isinstance(call.get(k), str)]
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--min", type=int, default=1)
    args = parser.parse_args()

    pattern = re.compile(args.pattern)
    matched = 0
    if args.log.is_file():
        for line in args.log.read_text(encoding="utf-8").splitlines():
            try:
                call = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(call, dict) and pattern.search(call_text(call)):
                matched += 1
    if matched < args.min:
        print(f"FAIL: {matched} recorded call(s) match {args.pattern}, need {args.min}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {matched} recorded call(s) match")


if __name__ == "__main__":
    main()
