#!/usr/bin/env python3
"""Check the Slack group-DM multiselect flow.

Passes (exit 0) when any .flow file in the workspace has:
  1. a Slack connector node (type contains 'slack'), and
  2. a 'users' multiselect field on that node with exactly 3 entries.

The 'users' value counts whether it is a native JSON array
(["U1","U2","U3"]) or a flow expression string wrapping an array literal
(e.g. "=js:(['U1','U2','U3'])") — both are valid ways to populate a
multiselect field in a .flow.

Name-agnostic: the prompt does not fix a project name, so every .flow file
selected by the shared same-ground discovery helper is checked.
"""
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.flow_check import find_flow_files  # noqa: E402


def parse_users(value):
    """Normalize a 'users' field value to a list of entries, else None.

    Accepts a native list, or a string holding an array literal such as a
    "=js:(['U1','U2','U3'])" expression.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        match = re.search(r"\[.*\]", value, re.DOTALL)
        if not match:
            return None
        literal = match.group(0)
        try:
            parsed = ast.literal_eval(literal)
        except (ValueError, SyntaxError):
            parsed = None
        if isinstance(parsed, (list, tuple)):
            return list(parsed)
        # Fallback: count quoted string entries inside the brackets.
        entries = re.findall(r"""['"]([^'"]+)['"]""", literal)
        return entries or None
    return None


def is_users_key(key):
    """True for the 'users' multiselect key in any of its encodings.

    Accepts the bare name and array-notation variants a .flow may emit:
    'users', 'users[*]', 'users[]', 'users[0]'.
    """
    return isinstance(key, str) and re.fullmatch(r"users(\[.*\])?", key) is not None


def find_users(obj):
    """Recursively find a 'users' key holding a parseable multiselect value."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if is_users_key(key):
                users = parse_users(value)
                if users is not None:
                    return users
            found = find_users(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_users(item)
            if found is not None:
                return found
    return None


def check_flow(path, expected_count):
    """Return None on pass, else a failure reason."""
    try:
        flow = json.load(open(path))
    except (json.JSONDecodeError, OSError) as exc:
        return f"not valid JSON: {exc}"

    slack_nodes = [
        n for n in flow.get("nodes", [])
        if "slack" in (n.get("type") or "").lower()
    ]
    if not slack_nodes:
        return "no Slack connector node"

    for node in slack_nodes:
        users = find_users(node.get("inputs", {}))
        if users is None:
            continue
        if expected_count == "populated" and users:
            print(f"OK: {path} — node '{node['id']}' users={users}")
            return None
        if isinstance(expected_count, int) and len(users) == expected_count:
            print(f"OK: {path} — node '{node['id']}' users={users}")
            return None
        return f"users field has {len(users)} entries, expected {expected_count}: {users}"
    return "Slack node has no 'users' multiselect field"


def main():
    expected_count = (
        "populated"
        if len(sys.argv) > 1 and sys.argv[1] == "populated"
        else int(sys.argv[1]) if len(sys.argv) > 1 else 3
    )
    flows = find_flow_files()

    reasons = []
    for path in flows:
        reason = check_flow(path, expected_count)
        if reason is None:
            sys.exit(0)
        reasons.append(f"{path}: {reason}")
    sys.exit("; ".join(reasons))


if __name__ == "__main__":
    main()
