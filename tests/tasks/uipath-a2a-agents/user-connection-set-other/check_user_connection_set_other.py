#!/usr/bin/env python3
"""Grade giving Jane her own connection on the remote A2A agent foundry-agent.

Passes when, in the uip mock's call log (`--help` calls skipped):
- a successful `remote-a2a-agent-user-connections set --agent foundry-agent` named Jane
  (`--user-email jane.doe@example.com`, any case, or `--user-id 5e0c1d2a-…`), her connection
  (`--connection-id 7a1b2c3d-…cc` or `--connection-name Foundry (Jane)`) and the Shared folder
  (`--folder-path Shared` or `--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`), after a `--dry-run` of a set on that agent;
- no executed set used `--me`, another user or another connection;
- no `remote-a2a-agent update` changed the agent's own connection (that would change it for every user).
The mock joins argv with spaces, so a quoted connection name arrives without its quotes.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "foundry-agent"
JANE_EMAIL = "jane.doe@example.com"
JANE_ID = "5e0c1d2a-3b4c-4d5e-8f60-0a1b2c3d4e5f"
JANE_CONN = "7a1b2c3d-0000-4000-8000-0000000000cc"
JANE_CONN_NAME = "Foundry (Jane)"
FOLDER_KEY = "0f0f0f0f-0000-4000-8000-0000000000f1"
NEXT_FLAG = r"(?=\s--|\s*$)"
SET = re.compile(r"agenthub\s+remote-a2a-agent-user-connections\s+set\b")


def folder_ok(args: str) -> bool:
    # The value ends at the next space: the slug may follow it, as in `update --folder-path Shared vendor-agent`.
    return bool(re.search(r"--folder-path[ =]['\"]?Shared['\"]?(?=\s|$)", args)
                or re.search(r"--folder-key[ =]" + FOLDER_KEY + r"(?=\s|$)", args))


def user_ok(args: str) -> bool:
    return bool(re.search(r"--user-email[ =]['\"]?" + re.escape(JANE_EMAIL) + r"['\"]?" + NEXT_FLAG, args, re.I)
                or re.search(r"--user-id[ =]" + JANE_ID + NEXT_FLAG, args, re.I))


def connection_ok(args: str) -> bool:
    return bool(re.search(r"--connection-name[ =]['\"]?" + re.escape(JANE_CONN_NAME) + r"['\"]?" + NEXT_FLAG, args, re.I)
                or re.search(r"--connection-id[ =]" + JANE_CONN + NEXT_FLAG, args, re.I))


def agent_ok(args: str) -> bool:
    return bool(re.search(r"--agent[ =]" + SLUG + NEXT_FLAG, args))


def wrong_target(args: str) -> str | None:
    if re.search(r"--me" + NEXT_FLAG, args):
        return "--me sets the caller's own connection, not Jane's"
    for flag in ("--user-email", "--user-id"):
        if flag in args and not user_ok(args):
            return f"{flag} names another user"
    for flag in ("--connection-name", "--connection-id"):
        if flag in args and not connection_ok(args):
            return f"{flag} names another connection"
    return None


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    calls = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            call = json.loads(line)
        except ValueError:
            continue
        args = call.get("args", "")
        if "--help" not in args:
            calls.append((args, int(call.get("exit_code", 0))))

    for args, _ in calls:
        if re.search(r"agenthub\s+remote-a2a-agent\s+update\b", args) and "--dry-run" not in args and "--connection-id" in args:
            print(f"FAIL: the agent's own connection was changed, for every user: {args}")
            return 1

    dry_run_seen = False
    for args, code in calls:
        if not SET.search(args):
            continue
        if "--dry-run" in args:
            dry_run_seen = dry_run_seen or agent_ok(args)
            continue
        problem = wrong_target(args)
        if problem:
            print(f"FAIL: {problem}: {args}")
            return 1
        if not folder_ok(args):
            print(f"FAIL: a set without the Shared folder: {args}")
            return 1
        if code == 0 and agent_ok(args) and user_ok(args) and connection_ok(args):
            if not dry_run_seen:
                print(f"FAIL: the set ran without a --dry-run first: {args}")
                return 1
            print("PASS: set Jane's connection on foundry-agent in Shared, after a dry-run")
            return 0
    print("FAIL: no successful set named foundry-agent, Jane and her connection")
    for args, code in calls:
        if SET.search(args):
            print(f"  set (exit {code}): {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
