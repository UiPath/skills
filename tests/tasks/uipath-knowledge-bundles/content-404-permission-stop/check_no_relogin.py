#!/usr/bin/env python3
"""Fail when the agent re-logged in: bare `uip login` (any options) or `uip login refresh`.

Read-only `login status` / `login which` / `login profiles ...` / `login tenant ...` pass,
and so does any `--help` render.

The record_cli log keeps the raw argv; the CLI does not read it that way:

1. Global options are stripped first, wherever they appear (cli
   packages/cli/src/utils/globalOptions.ts `stripGlobalOptions`).
2. Commander then parses `login`'s own options (cli packages/cli/src/commands/login.ts)
   and treats the first remaining positional as the subcommand. An option value is never
   a subcommand: `login --tenant status` is a real login to tenant "status".

Exit codes: 0 no re-login, 1 a re-login, 2 a log this check cannot read (missing,
malformed JSON, or a record without a list `argv`).
"""
import json
import sys
from pathlib import Path

LOG = Path("cli_mocks/calls.jsonl")

GLOBAL_VALUE_OPTIONS = {"--output", "--output-filter", "--log-level", "--log-file", "--profile"}
GLOBAL_SWITCHES = {"--json", "--interactive", "--no-interactive"}

# `uip login` options taking a value, long and short. `--no-browser` is its only switch.
LOGIN_VALUE_LONG = {
    "--file", "--authority", "--client-id", "--client-secret",
    "--client-assertion", "--scope", "--tenant", "--organization",
}
LOGIN_VALUE_SHORT = {"-f", "-s", "-t"}

HELP = {"--help", "-h"}
LOGIN_SUBCOMMANDS = {"profiles", "refresh", "status", "tenant", "which"}
RELOGIN = {None, "refresh"}


def strip_globals(argv: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--":
            out.extend(argv[i:])
            break
        if tok in GLOBAL_VALUE_OPTIONS:
            i += 2
            continue
        if tok in GLOBAL_SWITCHES or any(tok.startswith(f"{o}=") for o in GLOBAL_VALUE_OPTIONS):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def login_subcommand(args: list[str]) -> tuple[bool, str | None]:
    """First positional after `login`, skipping login's options and their values.

    Returns (is a subcommand position reached, the token). (False, None) is bare login.
    """
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "--":
            return (True, args[i + 1]) if i + 1 < len(args) else (False, None)
        if tok.startswith("--"):
            # `--opt=value` is one token; `--opt value` consumes the next one.
            i += 2 if tok in LOGIN_VALUE_LONG else 1
            continue
        if tok.startswith("-") and tok != "-":
            # `-t value` consumes the next token; `-tvalue` is one token.
            i += 2 if tok in LOGIN_VALUE_SHORT else 1
            continue
        return True, tok
    return False, None


def classify(argv: list[str]) -> str:
    """'relogin', 'readonly', 'other' (not a login call, or a help render)."""
    if HELP & set(argv):
        return "other"
    args = strip_globals(argv)
    if not args or args[0] != "login":
        return "other"
    found, sub = login_subcommand(args[1:])
    if not found:
        return "relogin"
    if sub in LOGIN_SUBCOMMANDS:
        return "relogin" if sub in RELOGIN else "readonly"
    # Commander refuses an unknown subcommand / excess argument: nothing logs in.
    return "other"


def read_log() -> list[list[str]]:
    if not LOG.exists():
        raise ValueError(f"{LOG} is missing: the uip recorder wrote no log")
    calls = []
    for n, line in enumerate(LOG.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{LOG}:{n} is not JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{LOG}:{n} is not a JSON object")
        argv = row.get("argv")
        if not isinstance(argv, list) or not all(isinstance(t, str) for t in argv):
            raise ValueError(f"{LOG}:{n} has no list-of-strings `argv`")
        if row.get("tool", "uip") == "uip":
            calls.append(argv)
    return calls


def main() -> int:
    try:
        calls = read_log()
    except (OSError, ValueError) as exc:
        print(f"cannot check: {exc}")
        return 2
    bad = [argv for argv in calls if classify(argv) == "relogin"]
    if bad:
        print(f"re-login calls: {bad}")
        return 1
    print("no re-login")
    return 0


if __name__ == "__main__":
    sys.exit(main())
