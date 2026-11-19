#!/usr/bin/env python3
"""Grade fixing a remote A2A agent registration that fails with a 502 from a PAT connection.

The user's `create --connection-id 7a1b2c3d-…bb` (a Personal Access Token Agent 2 Agent connection)
fails with `HTTP 502: Received HTML …`, whatever the CLI's Instructions say about retrying. Passes when,
in the uip mock's call log (`--help`, `--dry-run` and `--print-schema` calls skipped):
- at most one create ran with the PAT connection (a retry does not help), and no update set it;
- every remote-a2a-agent write names the Shared folder (`--folder-path Shared` or `--folder-key 0f0f0f0f-0000-4000-8000-0000000000f1`);
- any Authorization header sent is exactly `%ASSETS/VendorToken%` (the asset holds `Bearer <token>`);
- either no agent was created (the agent stopped to ask about the connection's type), or vendor-agent was
  created and a successful create or update sent `Authorization=%ASSETS/VendorToken%`.
Whether the answer names the non-OAuth connection as the cause is graded by the task's llm_judge.
"""

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks/.calls.jsonl")
SLUG = "vendor-agent"
PAT = "7a1b2c3d-0000-4000-8000-0000000000bb"
VALUE = "%ASSETS/VendorToken%"
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


def authorization(args: str) -> list[str]:
    return [m.group(1).strip("'\"") for m in re.finditer(
        r"--header[ =]['\"]?Authorization=(.*?)" + NEXT_FLAG, args, re.I)]


def main() -> int:
    writes = []
    if CALL_LOG.is_file():
        for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
            try:
                call = json.loads(line)
            except ValueError:
                continue
            args = call.get("args", "")
            m = WRITE.search(args)
            if m and not any(s in args for s in SKIP):
                writes.append((m.group(1), args, int(call.get("exit_code", 0))))

    pat_creates = 0
    for verb, args, _ in writes:
        if not folder_ok(args):
            print(f"FAIL: a {verb} without the Shared folder: {args}")
            return 1
        if PAT in args:
            if verb != "create":
                print(f"FAIL: a {verb} set the Personal Access Token connection: {args}")
                return 1
            pat_creates += 1
        wrong = [v for v in authorization(args) if v.lower() != VALUE.lower()]
        if wrong:
            print(f"FAIL: Authorization sent as '{wrong[0]}', not exactly {VALUE}: {args}")
            return 1
    if pat_creates > 1:
        print(f"FAIL: the create with the PAT connection ran {pat_creates} times; retrying does not help")
        return 1

    created = [a for v, a, code in writes if v == "create" and code == 0]
    if not created:
        print("PASS: no agent registered; the PAT connection was not retried")
        return 0
    targets = [a for v, a, code in writes if code == 0 and (
        v == "create" or (v == "update" and names_slug(a, "update")))]
    if any(VALUE.lower() in (x.lower() for x in authorization(a)) for a in targets):
        print(f"PASS: {SLUG} registered with Authorization={VALUE} instead of the PAT connection")
        return 0
    print(f"FAIL: {SLUG} was registered, but no create or update sent Authorization={VALUE}")
    for verb, args, code in writes:
        print(f"  {verb} (exit {code}): {args}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
