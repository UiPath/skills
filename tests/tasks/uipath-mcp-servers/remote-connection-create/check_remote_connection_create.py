#!/usr/bin/env python3
"""Grade the remote-server create from the uip mock's call log.

Passes when an executed `mcp create remote` (not --help, --print-schema or
--dry-run) sent the target URI and the id of the enabled "Mock MCP OAuth"
connection, either as flags (`--uri`, `--connection-id`) or as a camelCase
`--file` / `--body` payload (`uri`, `connectionId`), and no executed create
sent the id of the failed "Mock MCP OAuth (old)" connection.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
URI = "https://mcp.mock.example.com/mcp"
CONNECTION = "6f3c2a10-4b7e-4c1d-9a2e-0d5b8c7e1a01"
OLD_CONNECTION = "6f3c2a10-4b7e-4c1d-9a2e-0d5b8c7e1a02"
SKIP = ("--help", "--print-schema", "--dry-run")


def flags_ok(args: str) -> bool:
    uri = re.search(r"--uri[ =]" + re.escape(URI) + r"/?(\s|$)", args)
    connection = re.search(r"--connection-id[ =]" + CONNECTION + r"(\s|$)", args, re.I)
    return bool(uri and connection)


def payload_of(args: str):
    file_match = re.search(r"--file[ =](\S+)", args)
    if file_match:
        try:
            return json.loads(Path(file_match.group(1)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    body_at = args.find("--body")
    if body_at != -1:
        rest = args[body_at + len("--body"):].lstrip(" =")
        try:
            return json.JSONDecoder().raw_decode(rest)[0]
        except ValueError:
            return None
    return None


def payload_ok(payload) -> bool:
    if not isinstance(payload, dict):
        return False
    if str(payload.get("uri", "")).rstrip("/") != URI:
        return False
    return str(payload.get("connectionId", "")).lower() == CONNECTION


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    creates = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(line).get("args", "")
        except ValueError:
            continue
        if "agenthub mcp create remote" in args and not any(s in args for s in SKIP):
            creates.append(args)
    if not creates:
        print("FAIL: no executed `uip agenthub mcp create remote`")
        return 1
    for args in creates:
        payload = payload_of(args)
        sent = args + " " + (json.dumps(payload) if payload is not None else "")
        if OLD_CONNECTION in sent.lower():
            print(f"FAIL: a create used the failed '(old)' connection: {args}")
            return 1
    if any(flags_ok(a) or payload_ok(payload_of(a)) for a in creates):
        print("PASS: create sent the URI and the enabled connection's id")
        return 0
    print("FAIL: no create sent both the URI and the enabled connection's id")
    for args in creates:
        print(f"  create: {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
