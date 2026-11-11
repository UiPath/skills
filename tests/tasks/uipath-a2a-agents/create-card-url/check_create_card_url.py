#!/usr/bin/env python3
"""Grade registering vendor-agent from its card URL with an asset-backed API key header.

Passes when, in the uip mock's call log (`--help`, `--dry-run` and `--print-schema` calls skipped):
- every remote-a2a-agent write names the Shared folder (`--folder-path Shared` or `--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`);
- exactly one create succeeded: `--slug vendor-agent`, `--agent-card-url <CARD_URL>`, no `--agent-card-json`;
- no create carried `--connection-id`;
- a successful create or `update vendor-agent` sent the header `X-API-Key=%ASSETS/VendorKey%` (the name in
  any case), and no write sent that header with another value.

From a CLI login a create from a card URL with a `%ASSETS/...%` header fails with a 403 (the mock answers it
so), so the header is expected on an update after a create without it. The mock joins argv with spaces, so
quotes are gone and a value with a space reaches the log as two words.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "vendor-agent"
CARD_URL = "https://agent.example.com/.well-known/agent-card.json"
HEADER = "X-API-Key"
VALUE = "%ASSETS/VendorKey%"
FOLDER_KEY = "0f0f0f0f-0000-4000-8000-0000000000f1"
SKIP = ("--help", "--dry-run", "--print-schema")
NEXT_FLAG = r"(?=\s--|\s*$)"
WRITE = re.compile(r"agenthub\s+remote-a2a-agent\s+(create|update|delete|refresh-card)\b")


def folder_ok(args: str) -> bool:
    # The value ends at the next space: the slug may follow it, as in `update --folder-path Shared vendor-agent`.
    return bool(re.search(r"--folder-path[ =]['\"]?Shared['\"]?(?=\s|$)", args)
                or re.search(r"--folder-key[ =]" + FOLDER_KEY + r"(?=\s|$)", args))

def names_slug(args: str, verb: str) -> bool:
    """Whether `remote-a2a-agent <verb>` names SLUG as a positional, before or after its flags."""
    m = re.search(r"remote-a2a-agent\s+" + verb + r"\b(.*)", args)
    return bool(m) and re.search(r"(?:^|\s)" + re.escape(SLUG) + r"(?=\s|$)", m.group(1)) is not None


def header_values(args: str) -> list[str]:
    """Values sent for HEADER: by --header flags, or as a `Name:Value` line of a --body payload."""
    values = [m.group(1).strip("'\"") for m in re.finditer(
        r"--header[ =]['\"]?" + re.escape(HEADER) + r"=(.*?)" + NEXT_FLAG, args, re.I)]
    if "--body" in args:
        values += [m.group(1) for m in re.finditer(re.escape(HEADER) + r":([^\"\\\s]*)", args, re.I)]
    return values


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
        if verb == "create" and "--connection-id" in args:
            print(f"FAIL: a create with --connection-id (the agent uses a header): {args}")
            return 1
        if verb == "create" and "--agent-card-json" in args:
            print(f"FAIL: a create from --agent-card-json (the card URL is public): {args}")
            return 1
        wrong = [v for v in header_values(args) if v.lower() != VALUE.lower()]
        if wrong:
            print(f"FAIL: {HEADER} sent as '{wrong[0]}', not exactly {VALUE}: {args}")
            return 1

    creates = [a for v, a, code in writes if v == "create" and code == 0]
    if len(creates) != 1:
        print(f"FAIL: {len(creates)} successful creates, expected exactly one")
        return 1
    create = creates[0]
    if not (re.search(r"--slug[ =]" + SLUG + NEXT_FLAG, create)
            and re.search(r"--agent-card-url[ =]['\"]?" + re.escape(CARD_URL) + r"['\"]?" + NEXT_FLAG, create)):
        print(f"FAIL: the create did not name --slug {SLUG} and --agent-card-url {CARD_URL}: {create}")
        return 1

    targets = [a for v, a, code in writes if code == 0 and (
        v == "create" or (v == "update" and names_slug(a, "update")))]
    if any(VALUE.lower() in (x.lower() for x in header_values(a)) for a in targets):
        print(f"PASS: {SLUG} registered from its card URL with {HEADER}={VALUE}")
        return 0
    print(f"FAIL: no successful create or update of {SLUG} sent {HEADER}={VALUE}")
    for verb, args, code in writes:
        print(f"  {verb} (exit {code}): {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
