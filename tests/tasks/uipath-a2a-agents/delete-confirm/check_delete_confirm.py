#!/usr/bin/env python3
"""Grade deleting vendor-agent with `--yes`.

Passes when, in the uip mock's call log (`--help` and `--dry-run` calls skipped), exactly one
`remote-a2a-agent delete` ran with `--yes`, on vendor-agent, in the Shared folder (`--folder-path Shared` or
`--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`), and no delete named another agent. A delete without `--yes` is refused
(`confirmation_required`) and is allowed. Whether the agent confirmed with the user first is graded by the
task's llm_judge.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "vendor-agent"
FOLDER_KEY = "0f0f0f0f-0000-4000-8000-0000000000f1"
SKIP = ("--help", "--dry-run")
NEXT_FLAG = r"(?=\s--|\s*$)"
DELETE = re.compile(r"agenthub\s+remote-a2a-agent\s+delete\b(.*)")
VALUE_FLAGS = {"--folder-path", "--folder-key", "--output", "--output-filter", "--log-level", "--log-file",
               "--profile", "--tenant", "--login-validity"}


def delete_target(rest: str) -> str | None:
    """The delete's slug: its first positional, skipping flags and the values they take."""
    tokens = iter(rest.split())
    for token in tokens:
        if token.startswith("-"):
            if token.split("=", 1)[0] in VALUE_FLAGS and "=" not in token:
                next(tokens, None)
            continue
        return token.strip("'\"")
    return None


def folder_ok(args: str) -> bool:
    # The value ends at the next space: the slug may follow it, as in `update --folder-path Shared vendor-agent`.
    return bool(re.search(r"--folder-path[ =]['\"]?Shared['\"]?(?=\s|$)", args)
                or re.search(r"--folder-key[ =]" + FOLDER_KEY + r"(?=\s|$)", args))


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    confirmed = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(line).get("args", "")
        except ValueError:
            continue
        m = DELETE.search(args)
        if not m or any(s in args for s in SKIP):
            continue
        target = delete_target(m.group(1))
        if target != SLUG:
            print(f"FAIL: a delete of another agent, {target}: {args}")
            return 1
        if not folder_ok(args):
            print(f"FAIL: a delete without the Shared folder: {args}")
            return 1
        if re.search(r"(--yes|\s-y)(?=\s|$)", args):
            confirmed.append(args)
    if len(confirmed) == 1:
        print(f"PASS: {SLUG} deleted once, with --yes")
        return 0
    print(f"FAIL: {len(confirmed)} deletes of {SLUG} with --yes, expected exactly one")
    return 1


if __name__ == "__main__":
    sys.exit(main())
