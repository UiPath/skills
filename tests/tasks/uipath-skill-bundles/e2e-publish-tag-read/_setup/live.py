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
  intact     Version 1 is the seed byte for byte; the newest version's README.md and
             refund-skill/instructions.md equal the seed byte for byte (the second publish
             changed nothing it was not asked to), and its invoice-skill/instructions.md is the
             seed's plus the rule. The seed is read from the protected reference copy.
  cleanup    Best effort: deletes the scratch bundle, and only a name of the generated
             `sb-e2e-<12 hex>` shape (the name file is agent-writable). Never fails.

Exit codes: 0 pass, 1 fail.
"""
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

FOLDER = "Shared"
NAME_FILE = Path("bundle-name.txt")
NAME_SHAPE = re.compile(r"^sb-e2e-[0-9a-f]{12}$")
# The protected reference copy of the seed, beside this script; the agent's ./seed may have changed.
SEED = Path(__file__).resolve().parent.parent / "seed"
INVOICE = "invoice-skill/instructions.md"
SEED_FILES = ("README.md", INVOICE, "refund-skill/instructions.md")
UNTOUCHED = tuple(p for p in SEED_FILES if p != INVOICE)
RULE = "more than 2%"


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
    value = NAME_FILE.read_text().strip()
    if not NAME_SHAPE.match(value):
        raise SystemExit(f"FAIL: {NAME_FILE} holds {value!r}, not a name preflight generated")
    return value


def seed(path):
    return (SEED / path).read_text(encoding="utf-8")


def preview(content, raw, n):
    """What a failure message shows: the file content, or the CLI output when there is none."""
    return (content if content is not None else raw)[:n]


def read_file(bundle, path, version):
    _, env, raw = uip("or", "skill-bundles", "file", bundle, "--folder-path", FOLDER, "--path", path, "--version", version)
    return (env["Data"].get("Content") if ok(env) else None), raw


def latest(bundle):
    _, env, raw = uip("or", "skill-bundles", "versions", bundle, "--folder-path", FOLDER)
    if not ok(env):
        raise SystemExit(f"FAIL: versions refused: {raw[:300]}")
    rows = env.get("Data") or []
    return max((r.get("Version", 0) for r in rows), default=0), len(rows)


def preflight():
    code, _, raw = uip("or", "skill-bundles", "--help")
    if code != 0:
        print(f"FAIL: this uip has no `or skill-bundles` (needs a prerelease build with UiPath/cli#6015): {raw[:300]}")
        return 1
    _, env, raw = uip("or", "skill-bundles", "list", "--folder-path", FOLDER, "--limit", "1")
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
    _, env, raw = uip("or", "skill-bundles", "tags", "list", bundle, "--folder-path", FOLDER)
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
    for path in SEED_FILES:
        content, raw = read_file(bundle, path, "1")
        if content != seed(path):
            problems.append(f"v1 {path} is not the seed file: {preview(content, raw, 160)!r}")
    for path in UNTOUCHED:
        content, raw = read_file(bundle, path, "latest")
        if content != seed(path):
            problems.append(f"newest {path} differs from the seed it was never meant to change: {preview(content, raw, 160)!r}")
    newest, raw = read_file(bundle, INVOICE, "latest")
    base = seed(INVOICE).splitlines()
    lines = (newest or "").splitlines()
    if lines[:len(base)] != base or not any(RULE in line for line in lines[len(base):]):
        problems.append(f"newest {INVOICE} is not the seed plus the rule: {preview(newest, raw, 200)!r}")
    if problems:
        print("FAIL: " + "; ".join(problems))
        return 1
    print("ok: v1 is the seed; the newest version kept the untouched files byte for byte and adds the rule")
    return 0


def cleanup():
    # Only ever a scratch bundle this run generated: the file is agent-writable.
    value = NAME_FILE.read_text().strip() if NAME_FILE.exists() else ""
    if NAME_SHAPE.match(value):
        uip("or", "skill-bundles", "delete", value, "--folder-path", FOLDER, "--yes")
    return 0


MODES = {"preflight": preflight, "versions": versions, "stable": stable, "intact": intact, "cleanup": cleanup}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in MODES:
        print(f"usage: live.py {'|'.join(MODES)}")
        sys.exit(1)
    sys.exit(MODES[mode]())
