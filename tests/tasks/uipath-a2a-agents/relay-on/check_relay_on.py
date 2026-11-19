#!/usr/bin/env python3
"""Grade routing vendor-agent through UiPath Relay.

Passes when, in the uip mock's call log (`--help`, `--dry-run` and `--print-schema` calls skipped), every
remote-a2a-agent write names the Shared folder (`--folder-path Shared` or `--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`)
and the last successful `update vendor-agent` that changed Relay passed `--use-relay`, not `--no-use-relay`,
and no successful update of the agent changed anything else (Critical Rule 6): no card, headers, connection,
name, description or activation flag, and no `--file` / `--body` payload, whose omitted description the
service clears.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "vendor-agent"
FOLDER_KEY = "0f0f0f0f-0000-4000-8000-0000000000f1"
SKIP = ("--help", "--dry-run", "--print-schema")
NEXT_FLAG = r"(?=\s--|\s*$)"
WRITE = re.compile(r"agenthub\s+remote-a2a-agent\s+(create|update|delete|refresh-card)\b")
UNASKED = ("--agent-card-url", "--agent-card-json", "--header", "--connection-id", "--clear-connection",
           "--name", "--description", "--is-active", "--file", "--body")


def folder_ok(args: str) -> bool:
    # The value ends at the next space: the slug may follow it, as in `update --folder-path Shared vendor-agent`.
    return bool(re.search(r"--folder-path[ =]['\"]?Shared['\"]?(?=\s|$)", args)
                or re.search(r"--folder-key[ =]" + FOLDER_KEY + r"(?=\s|$)", args))

def names_slug(args: str, verb: str) -> bool:
    """Whether `remote-a2a-agent <verb>` names SLUG as a positional, before or after its flags."""
    m = re.search(r"remote-a2a-agent\s+" + verb + r"\b(.*)", args)
    return bool(m) and re.search(r"(?:^|\s)" + re.escape(SLUG) + r"(?=\s|$)", m.group(1)) is not None


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    relay = None
    writes = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            call = json.loads(line)
        except ValueError:
            continue
        args = call.get("args", "")
        m = WRITE.search(args)
        if not m or any(s in args for s in SKIP):
            continue
        writes.append((m.group(1), args, int(call.get("exit_code", 0))))
        if not folder_ok(args):
            print(f"FAIL: a {m.group(1)} without the Shared folder: {args}")
            return 1
        if (m.group(1) == "update" and int(call.get("exit_code", 0)) == 0
                and names_slug(args, "update")):
            unasked = [flag for flag in UNASKED if re.search(re.escape(flag) + r"(?=[\s=]|$)", args)]
            if unasked:
                print(f"FAIL: an update of {SLUG} also sent {', '.join(unasked)}; only Relay was asked for: {args}")
                return 1
            if re.search(r"--no-use-relay" + NEXT_FLAG, args):
                relay = False
            elif re.search(r"--use-relay" + NEXT_FLAG, args) or re.search(r"\"useRelay\"\s*:\s*true", args):
                relay = True

    if relay:
        print(f"PASS: {SLUG} routes through Relay")
        return 0
    print(f"FAIL: no successful update left {SLUG} with --use-relay")
    for verb, args, code in writes:
        print(f"  {verb} (exit {code}): {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
