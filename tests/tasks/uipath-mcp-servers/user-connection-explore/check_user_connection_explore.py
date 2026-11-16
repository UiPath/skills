#!/usr/bin/env python3
"""Grade exploring a user's personal workspace to set their connection, from the uip mock's call log.

Passes when, in order:
  1. an executed `or folders explore` named Jane's workspace (`--owner jane.doe@example.com` or her
     user id, or the workspace `jane.doe@example.com's workspace` or its key `folder-mock-jane-ws`),
  2. an executed `agenthub mcp-user-connections set --mcp vendor-mcp` after it named Jane
     (`--user-email` or `--user-id`), her connection (`--connection-name Vendor MCP (Jane)` or
     `--connection-id`) and the Shared folder,
  3. an executed `or folders stop-exploring` after that set named Jane's workspace,
and no executed explore named another workspace, and no executed set used `--me`, another user or
another connection. `--help` and `--dry-run` calls are skipped. The mock joins argv with spaces, so
a quoted name arrives without its quotes.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "vendor-mcp"
JANE_EMAIL = "jane.doe@example.com"
JANE_ID = "5e0c1d2a-3b4c-4d5e-8f60-0a1b2c3d4e5f"
JANE_CONN = "7a1b2c3d-0000-4000-8000-0000000000aa"
JANE_CONN_NAME = "Vendor MCP (Jane)"
JANE_WORKSPACE = "jane.doe@example.com's workspace"
JANE_WORKSPACE_KEY = "folder-mock-jane-ws"
FOLDER_KEY = "folder-mock-shared"
SKIP = ("--help", "--dry-run")
NEXT_FLAG = r"(?=\s--|\s*$)"


def user_ok(args: str) -> bool:
    email = re.search(r"--user-email[ =]['\"]?" + re.escape(JANE_EMAIL) + r"['\"]?" + NEXT_FLAG, args, re.I)
    user_id = re.search(r"--user-id[ =]" + JANE_ID + NEXT_FLAG, args, re.I)
    return bool(email or user_id)


def connection_ok(args: str) -> bool:
    name = re.search(r"--connection-name[ =]['\"]?" + re.escape(JANE_CONN_NAME) + r"['\"]?" + NEXT_FLAG, args, re.I)
    conn_id = re.search(r"--connection-id[ =]" + JANE_CONN + NEXT_FLAG, args, re.I)
    return bool(name or conn_id)


def folder_ok(args: str) -> bool:
    path = re.search(r"--folder-path[ =]['\"]?Shared['\"]?" + NEXT_FLAG, args)
    key = re.search(r"--folder-key[ =]" + FOLDER_KEY + NEXT_FLAG, args)
    return bool(path or key)


def set_ok(args: str) -> bool:
    return bool(re.search(r"--mcp[ =]" + SLUG + NEXT_FLAG, args)) and user_ok(args) and connection_ok(args) and folder_ok(args)


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


def workspace_of(args: str, verb: str) -> str:
    """What an explore / stop-exploring call named: its `--owner` value, else the workspace positional."""
    owner = re.search(r"--owner[ =]['\"]?([^'\"\s]+)['\"]?" + NEXT_FLAG, args)
    if owner:
        return owner.group(1)
    rest = args.split(f"or folders {verb}", 1)[1]
    rest = re.split(r"\s--", rest, maxsplit=1)[0]
    return rest.strip().strip("'\"")


def names_jane(target: str) -> bool:
    """Jane's workspace by name or key, or Jane as its owner by email or user id."""
    return target.lower() in (JANE_WORKSPACE.lower(), JANE_WORKSPACE_KEY, JANE_EMAIL, JANE_ID)


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    calls = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(line).get("args", "")
        except ValueError:
            continue
        if not any(s in args for s in SKIP):
            calls.append(args)

    explored_at = stop_at = set_at = None
    for i, args in enumerate(calls):
        if "or folders explore" in args:
            workspace = workspace_of(args, "explore")
            if not names_jane(workspace):
                print(f"FAIL: explored a workspace other than Jane's: {args}")
                return 1
            if explored_at is None:
                explored_at = i
        elif "agenthub mcp-user-connections set" in args:
            problem = wrong_target(args)
            if problem:
                print(f"FAIL: {problem}: {args}")
                return 1
            if explored_at is not None and set_at is None and set_ok(args):
                set_at = i
        elif "or folders stop-exploring" in args:
            if set_at is not None and stop_at is None and names_jane(workspace_of(args, "stop-exploring")):
                stop_at = i

    if explored_at is None:
        print("FAIL: no executed `uip or folders explore` of Jane's workspace")
        return 1
    if set_at is None:
        print("FAIL: no set after exploring named the server, Jane, her connection and the Shared folder")
        for args in calls:
            if "mcp-user-connections set" in args:
                print(f"  set: {args}")
        return 1
    if stop_at is None:
        print("FAIL: Jane's workspace was left explored: no `uip or folders stop-exploring` after the set")
        return 1
    print("PASS: explored Jane's workspace, set her connection in Shared, then stopped exploring")
    return 0


if __name__ == "__main__":
    sys.exit(main())
