#!/usr/bin/env python3
"""Grade changing a header and the description of vendor-agent while keeping its masked key.

The stored agent has the headers `X-Api-Key: ****` (a secret, masked by `get`) and `X-Region: eu`.
Passes when, in the uip mock's call log (`--help`, `--dry-run` and `--print-schema` calls skipped):
- every remote-a2a-agent write names the Shared folder (`--folder-path Shared` or `--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`);
- no update re-sent the card or changed the connection or Relay (`--agent-card-json`, `--agent-card-url`,
  `--connection-id`, `--clear-connection`, `--use-relay`, `--no-use-relay`, or those fields in a payload);
- every successful update that sent headers kept the key as `X-Api-Key=****`, spelled as stored
  (`--header` replaces every stored header, so leaving it out deletes the key);
- a successful update sent `X-Api-Key=****` and `X-Region=us` together, and a successful update set the
  description to "Vendor pricing agent, US region" (the same update or another).
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "vendor-agent"
DESCRIPTION = "Vendor pricing agent, US region"
FOLDER_KEY = "0f0f0f0f-0000-4000-8000-0000000000f1"
SKIP = ("--help", "--dry-run", "--print-schema")
NEXT_FLAG = r"(?=\s--|\s*$)"
WRITE = re.compile(r"agenthub\s+remote-a2a-agent\s+(create|update|delete|refresh-card)\b")
UNASKED = ("--agent-card-json", "--agent-card-url", "--connection-id", "--clear-connection",
           "--use-relay", "--no-use-relay")
UNASKED_FIELDS = ("agentCardJson", "agentCardUrl", "connectionId", "clearConnectionId", "useRelay")


def folder_ok(args: str) -> bool:
    # The value ends at the next space: the slug may follow it, as in `update --folder-path Shared vendor-agent`.
    return bool(re.search(r"--folder-path[ =]['\"]?Shared['\"]?(?=\s|$)", args)
                or re.search(r"--folder-key[ =]" + FOLDER_KEY + r"(?=\s|$)", args))

def names_slug(args: str, verb: str) -> bool:
    """Whether `remote-a2a-agent <verb>` names SLUG as a positional, before or after its flags."""
    m = re.search(r"remote-a2a-agent\s+" + verb + r"\b(.*)", args)
    return bool(m) and re.search(r"(?:^|\s)" + re.escape(SLUG) + r"(?=\s|$)", m.group(1)) is not None


def headers(args: str) -> dict[str, str] | None:
    """The headers an update sends, by name; None when it sends none."""
    found = {m.group(1): m.group(2).strip("'\"") for m in re.finditer(
        r"--header[ =]['\"]?([^=\s]+)=(.*?)" + NEXT_FLAG, args)}
    if "--body" in args:
        found.update({m.group(1): m.group(2) for m in re.finditer(r"(X-Api-Key|X-Region):([^\"\\\s]*)", args)})
    return found or None


def description(args: str) -> str | None:
    m = re.search(r"--description[ =]['\"]?(.*?)['\"]?" + NEXT_FLAG, args)
    if m:
        return m.group(1)
    m = re.search(r"\"description\"\s*:\s*\"([^\"]*)\"", args)
    return m.group(1) if m else None


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

    updates = []
    for verb, args, code in writes:
        if not folder_ok(args):
            print(f"FAIL: a {verb} without the Shared folder: {args}")
            return 1
        unasked = [flag for flag in UNASKED if re.search(re.escape(flag) + r"(?=[\s=]|$)", args)]
        if "--body" in args:
            unasked += [field for field in UNASKED_FIELDS if f'"{field}"' in args]
        if unasked:
            print(f"FAIL: the update also sent {', '.join(unasked)}; only the region and description were asked for: {args}")
            return 1
        if verb == "update" and code == 0 and names_slug(args, "update"):
            updates.append(args)

    region = desc = False
    for args in updates:
        sent = headers(args)
        if sent is not None:
            if sent.get("X-Api-Key") != "****":
                print(f"FAIL: an update sent headers without keeping X-Api-Key=**** (got {sent.get('X-Api-Key')!r}): {args}")
                return 1
            region = region or sent.get("X-Region") == "us"
        value = description(args)
        desc = desc or (value is not None and value.strip().lower() == DESCRIPTION.lower())

    if region and desc:
        print("PASS: region and description changed, masked key kept")
        return 0
    missing = [name for name, ok in (("X-Region=us with X-Api-Key=****", region), (f"--description {DESCRIPTION}", desc)) if not ok]
    print(f"FAIL: no successful update of {SLUG} sent {' or '.join(missing)}")
    for verb, args, code in writes:
        print(f"  {verb} (exit {code}): {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
