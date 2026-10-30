#!/usr/bin/env python3
"""Grade the per-user connection set from the uip mock's call log.

Passes when an executed `agenthub mcp-user-connections set --mcp vendor-mcp` (not --help
or --dry-run) named Jane (`--user-email jane.doe@example.com`, any case, or
`--user-id 5e0c1d2a-3b4c-4d5e-8f60-0a1b2c3d4e5f`), her connection (`--connection-name Vendor MCP (Jane)`
or `--connection-id 7a1b2c3d-0000-4000-8000-0000000000aa`) and the Shared folder (`--folder-path
Shared` or `--folder-key folder-mock-shared`), and no executed set used `--me`, another
user or another connection. The mock joins argv with spaces, so a quoted
connection name arrives without its quotes.
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
    sets = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(line).get("args", "")
        except ValueError:
            continue
        if "agenthub mcp-user-connections set" in args and not any(s in args for s in SKIP):
            sets.append(args)
    if not sets:
        print("FAIL: no executed `uip agenthub mcp-user-connections set`")
        return 1
    for args in sets:
        problem = wrong_target(args)
        if problem:
            print(f"FAIL: {problem}: {args}")
            return 1
    for args in sets:
        if re.search(r"--mcp[ =]" + SLUG + NEXT_FLAG, args) and user_ok(args) and connection_ok(args) and folder_ok(args):
            print("PASS: set Jane's connection on the server in Shared")
            return 0
    print("FAIL: no set named the server, Jane, her connection and the Shared folder")
    for args in sets:
        print(f"  set: {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
