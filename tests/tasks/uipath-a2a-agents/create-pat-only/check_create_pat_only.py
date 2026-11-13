#!/usr/bin/env python3
"""Grade refusing to attach a Personal Access Token connection to a remote A2A agent.

Passes when no remote-a2a-agent write in the uip mock's call log (`--help`,
`--dry-run` and `--print-schema` calls skipped) sent the PAT connection `7a1b2c3d-…bb` (as `--connection-id`,
or as `connectionId` in a `--body` payload) or ran without the Shared folder (`--folder-path Shared` or
`--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`). A PAT connection has no OAuth token, so Agent Gateway fails the card
fetch and every call with a 502. A run with no uip command at all (the agent refused and explained) has
no log and passes. Whether the answer explains that and offers `--header` with an asset is graded by the
task's llm_judge.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
PAT = "7a1b2c3d-0000-4000-8000-0000000000bb"
FOLDER_KEY = "0f0f0f0f-0000-4000-8000-0000000000f1"
SKIP = ("--help", "--dry-run", "--print-schema")
NEXT_FLAG = r"(?=\s--|\s*$)"
WRITE = re.compile(r"agenthub\s+remote-a2a-agent(?:-user-connections)?\s+(create|update|delete|refresh-card|set)\b")


def folder_ok(args: str) -> bool:
    # The value ends at the next space: the slug may follow it, as in `update --folder-path Shared vendor-agent`.
    return bool(re.search(r"--folder-path[ =]['\"]?Shared['\"]?(?=\s|$)", args)
                or re.search(r"--folder-key[ =]" + FOLDER_KEY + r"(?=\s|$)", args))


def main() -> int:
    writes = []
    lines = CALL_LOG.read_text(encoding="utf-8").splitlines() if CALL_LOG.is_file() else []
    for line in lines:
        try:
            call = json.loads(line)
        except ValueError:
            continue
        args = call.get("args", "")
        m = WRITE.search(args)
        if m and not any(s in args for s in SKIP):
            writes.append((m.group(1), args))

    for verb, args in writes:
        if PAT in args:
            print(f"FAIL: a {verb} sent the Personal Access Token connection {PAT}: {args}")
            return 1
        if not folder_ok(args):
            print(f"FAIL: a {verb} without the Shared folder: {args}")
            return 1
    print(f"PASS: no write attached the PAT connection ({len(writes)} writes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
