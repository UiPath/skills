#!/usr/bin/env python3
"""Live helper for the skill-bundle e2e task: preflight, grading and cleanup.

Every mode talks to the real tenant through the installed `uip`, in folder Shared, about the
scratch bundle whose name `preflight` writes to ./bundle-name.txt.

  preflight  Fails (exit 1) unless the run can test anything: a `uip` build that has
             `or skill-bundles`, a session, and a tenant whose skill-bundles feature answers
             `list` in Shared. Then writes a fresh scratch name. A failing pre_run aborts the
             evaluation as ERROR, so an unprovisioned tenant can never score.
  versions   The bundle has at least two published versions.
  stable     Tag `stable` exists, is mutable, names the newest version, and that version's
             invoice-skill/instructions.md carries the requested rule.
  intact     The newest version still holds README.md and refund-skill/instructions.md (the
             second publish deleted nothing it was not asked to), and version 1 lacks the rule.
  cleanup    Best effort: deletes the scratch bundle. Never fails.

Exit codes: 0 pass, 1 fail.
"""
import json
import subprocess
import sys
import uuid
from pathlib import Path

FOLDER = "Shared"
NAME_FILE = Path("bundle-name.txt")
RULE = "more than 2%"
INVOICE = "invoice-skill/instructions.md"


def uip(*args, timeout=120):
    """Run `uip <args> --output json`; return (exit code, parsed envelope or None, raw text)."""
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, None, str(exc)
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        envelope = None
    return proc.returncode, envelope, (proc.stdout + proc.stderr).strip()


def ok(envelope):
    return isinstance(envelope, dict) and envelope.get("Result") == "Success"


def name():
    if not NAME_FILE.exists():
        raise SystemExit(f"FAIL: {NAME_FILE} is missing; preflight did not run")
    return NAME_FILE.read_text().strip()


def read_file(bundle, path, version):
    code, env, raw = uip("or", "skill-bundles", "file", bundle, "--folder-path", FOLDER, "--path", path, "--version", version)
    return (env["Data"].get("Content") if ok(env) else None), raw


def latest(bundle):
    code, env, raw = uip("or", "skill-bundles", "versions", bundle, "--folder-path", FOLDER)
    if not ok(env):
        raise SystemExit(f"FAIL: versions refused: {raw[:300]}")
    rows = env.get("Data") or []
    return max((r.get("Version", 0) for r in rows), default=0), len(rows)


def preflight():
    code, _, raw = uip("or", "skill-bundles", "--help")
    if code != 0:
        print(f"FAIL: this uip has no `or skill-bundles` (needs a prerelease build with UiPath/cli#6015): {raw[:300]}")
        return 1
    code, env, raw = uip("or", "skill-bundles", "list", "--folder-path", FOLDER, "--limit", "1")
    if not ok(env):
        print(f"FAIL: skill bundles unavailable in folder {FOLDER} (session, Features.SkillBundles, or permission): {raw[:300]}")
        return 1
    NAME_FILE.write_text(f"sb-e2e-{uuid.uuid4().hex[:12]}\n")
    print(f"ok: scratch bundle {name()}")
    return 0


def versions():
    newest, count = latest(name())
    if count < 2:
        print(f"FAIL: {count} version(s) published; expected the initial one and the edit")
        return 1
    print(f"ok: {count} versions, newest v{newest}")
    return 0


def stable():
    bundle = name()
    newest, _ = latest(bundle)
    code, env, raw = uip("or", "skill-bundles", "tags", "list", bundle, "--folder-path", FOLDER)
    if not ok(env):
        print(f"FAIL: tags list refused: {raw[:300]}")
        return 1
    tag = next((t for t in env.get("Data") or [] if t.get("Name") == "stable"), None)
    if tag is None:
        print("FAIL: no `stable` tag")
        return 1
    if tag.get("Immutable"):
        print("FAIL: `stable` was made immutable, which nobody asked for")
        return 1
    if tag.get("Version") != newest:
        print(f"FAIL: `stable` names v{tag.get('Version')}, newest is v{newest}")
        return 1
    content, raw = read_file(bundle, INVOICE, "stable")
    if content is None or RULE not in content:
        print(f"FAIL: {INVOICE} at `stable` lacks the rule: {(content or raw)[:300]}")
        return 1
    print(f"ok: stable -> v{newest}, carrying the rule")
    return 0


def intact():
    bundle = name()
    problems = []
    for path in ("README.md", "refund-skill/instructions.md"):
        content, raw = read_file(bundle, path, "latest")
        if content is None:
            problems.append(f"{path} missing from the newest version: {raw[:200]}")
    first, raw = read_file(bundle, INVOICE, "1")
    if first is None:
        problems.append(f"{INVOICE} missing from v1: {raw[:200]}")
    elif RULE in first:
        problems.append("v1 already carries the rule: the edit did not go into a later version")
    if problems:
        print("FAIL: " + "; ".join(problems))
        return 1
    print("ok: newest version kept the untouched files; v1 predates the edit")
    return 0


def cleanup():
    if NAME_FILE.exists():
        uip("or", "skill-bundles", "delete", NAME_FILE.read_text().strip(), "--folder-path", FOLDER, "--yes")
    return 0


MODES = {"preflight": preflight, "versions": versions, "stable": stable, "intact": intact, "cleanup": cleanup}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in MODES:
        print(f"usage: live.py {'|'.join(MODES)}")
        sys.exit(1)
    sys.exit(MODES[mode]())
