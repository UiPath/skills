#!/usr/bin/env python3
"""Fail when the agent re-logged in: bare `uip login` (any flags) or `uip login refresh`.

Read-only `login status` / `login which` / `login profiles list` / `login tenant list` pass,
and so does any `--help` render. The record_cli log keeps the raw argv, while the CLI strips
its global options (cli packages/cli/src/utils/globalOptions.ts `stripGlobalOptions`) before
parsing the command. So strip them here too, in both `--flag value` and `--flag=value` forms,
wherever they appear, and only then identify the login operation.
"""
import json
import sys
from pathlib import Path

LOG = Path("cli_mocks/calls.jsonl")
GLOBAL_VALUE_FLAGS = {"--output", "--output-filter", "--log-level", "--log-file", "--profile"}
GLOBAL_SWITCHES = {"--json", "--interactive", "--no-interactive"}
HELP = {"--help", "-h"}
LOGIN_SUBCOMMANDS = {"profiles", "refresh", "status", "tenant", "which"}
RELOGIN = {None, "refresh"}


def strip_globals(argv: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in GLOBAL_VALUE_FLAGS:
            i += 2
            continue
        if tok in GLOBAL_SWITCHES or any(tok.startswith(f"{flag}=") for flag in GLOBAL_VALUE_FLAGS):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def login_operation(argv: list[str]) -> tuple[bool, str | None]:
    """(is a login call, its subcommand or None for bare login)."""
    args = strip_globals(argv)
    if not args or args[0] != "login":
        return False, None
    sub = next((tok for tok in args[1:] if tok in LOGIN_SUBCOMMANDS), None)
    return True, sub


def main() -> int:
    rows = []
    if LOG.exists():
        rows = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]
    bad = []
    for row in rows:
        argv = row.get("argv", [])
        if row.get("tool", "uip") != "uip" or HELP & set(argv):
            continue
        is_login, sub = login_operation(argv)
        if is_login and sub in RELOGIN:
            bad.append(argv)
    if bad:
        print(f"re-login calls: {bad}")
        return 1
    print("no re-login")
    return 0


if __name__ == "__main__":
    sys.exit(main())
