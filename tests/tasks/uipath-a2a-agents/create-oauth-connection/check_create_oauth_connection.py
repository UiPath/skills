#!/usr/bin/env python3
"""Grade registering a Foundry-style agent with its OAuth connection, from a card at a non-.well-known path.

Passes when, in the uip mock's call log (`--help`, `--dry-run` and `--print-schema` calls skipped):
- every remote-a2a-agent write names the Shared folder (`--folder-path Shared` or `--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`);
- no write sent the Personal Access Token connection (`7a1b2c3d-…bb`) as `--connection-id` or `connectionId`;
- no create used `--agent-card-json` (Agent Gateway fetches the card with the connection's token);
- a create succeeded with `--slug foundry-agent`, `--agent-card-url <CARD_URL>` and
  `--connection-id 7a1b2c3d-…aa`, the OAuth client credentials connection.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "foundry-agent"
CARD_URL = "https://agent.example.com/api/a2a/agentCard/v1.0"
OAUTH = "7a1b2c3d-0000-4000-8000-0000000000aa"
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
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    writes = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            call = json.loads(line)
        except ValueError:
            continue
        args = call.get("args", "")
        m = WRITE.search(args)
        if m and not any(s in args for s in SKIP):
            writes.append((m.group(1), args, int(call.get("exit_code", 0))))

    for verb, args, _ in writes:
        if not folder_ok(args):
            print(f"FAIL: a {verb} without the Shared folder: {args}")
            return 1
        if PAT in args:
            print(f"FAIL: a {verb} sent the Personal Access Token connection {PAT}: {args}")
            return 1
        if verb == "create" and "--agent-card-json" in args:
            print(f"FAIL: a create from --agent-card-json; the connection authenticates the card URL: {args}")
            return 1

    for verb, args, code in writes:
        if (verb == "create" and code == 0
                and re.search(r"--slug[ =]" + SLUG + NEXT_FLAG, args)
                and re.search(r"--agent-card-url[ =]['\"]?" + re.escape(CARD_URL) + r"['\"]?" + NEXT_FLAG, args)
                and re.search(r"--connection-id[ =]" + OAUTH + NEXT_FLAG, args)):
            print(f"PASS: {SLUG} registered from {CARD_URL} with the OAuth connection")
            return 0
    print(f"FAIL: no successful create of {SLUG} from {CARD_URL} with --connection-id {OAUTH}")
    for verb, args, code in writes:
        print(f"  {verb} (exit {code}): {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
