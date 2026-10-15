#!/usr/bin/env python3
"""Grade the remote-server create from the uip mock's call log.

Passes when an executed `mcp create remote` (not --help, --print-schema or
--dry-run) sent the target URL and an Authorization header whose whole value
is the asset reference, either as flags (`--uri`, `--header`) or as a
camelCase `--file` / `--body` payload (`uri`, a `headers` line). A
`Bearer %ASSETS/...%` value fails: the service sends it literally.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
URL = "https://mock.api.example.com"
ASSET = "%ASSETS/SLACK_BOT_TOKEN%"
SKIP = ("--help", "--print-schema", "--dry-run")


def flags_ok(args: str) -> bool:
    uri = re.search(r"--uri[ =]https://mock\.api\.example\.com/?(\s|$)", args)
    header = re.search(
        r"--header[ =]authorization=%ASSETS/SLACK_BOT_TOKEN%(\s|$)", args, re.I
    )
    return bool(uri and header)


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
    if str(payload.get("uri", "")).rstrip("/") != URL:
        return False
    for line in str(payload.get("headers") or "").splitlines():
        name, sep, value = line.partition(":")
        if sep and name.strip().lower() == "authorization" and value.strip() == ASSET:
            return True
    return False


def main() -> int:
    if not CALL_LOG.exists():
        print(f"no call log at {CALL_LOG}")
        return 1
    creates = []
    for raw in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(raw).get("args", "")
        except ValueError:
            continue
        if "mcp create remote" in args and not any(flag in args for flag in SKIP):
            creates.append(args)
    if not creates:
        print("no executed `mcp create remote` call")
        return 1
    for args in creates:
        if re.search(r"bearer\s+%ASSETS", args, re.I):
            continue
        if flags_ok(args) or payload_ok(payload_of(args)):
            print("ok:", args)
            return 0
    print("no create sent the URL with an Authorization header of exactly " + ASSET)
    for args in creates:
        print("  saw:", args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
