#!/usr/bin/env python3
"""Check the Slack group-DM multiselect flow.

Passes (exit 0) when any .flow file in the workspace has:
  1. a Slack connector node (type contains 'slack'), and
  2. a 'users' multiselect field on that node with exactly 3 entries.

Name-agnostic: the prompt does not fix a project name, so every .flow file
is checked ('**' glob skips dot-dirs, so .uipath/.skills flows are ignored).
"""
import glob
import json
import sys


def find_users_list(obj):
    """Recursively find a 'users' key holding a list."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "users" and isinstance(value, list):
                return value
            found = find_users_list(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_users_list(item)
            if found is not None:
                return found
    return None


def check_flow(path):
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
        users = find_users_list(node.get("inputs", {}))
        if users is None:
            continue
        if len(users) == 3:
            print(f"OK: {path} — node '{node['id']}' users={users}")
            return None
        return f"users field has {len(users)} entries, expected 3: {users}"
    return "Slack node has no 'users' multiselect field"


def main():
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        sys.exit("no .flow file found")

    reasons = []
    for path in flows:
        reason = check_flow(path)
        if reason is None:
            sys.exit(0)
        reasons.append(f"{path}: {reason}")
    sys.exit("; ".join(reasons))


if __name__ == "__main__":
    main()
