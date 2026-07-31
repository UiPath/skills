#!/usr/bin/env python3
"""
Validate skills.sh.json — the display grouping for the repo's page on skills.sh —
against the skills that actually exist under skills/.

skills.sh.json is presentation-only: it never changes what the `skills` CLI
installs. That is exactly why it rots silently — a skill added, renamed, or
removed under skills/ produces no error anywhere, and the public page keeps
showing the old grouping. (As of this script's introduction the live page still
listed 13 skills that had been renamed or retired.) This check makes that drift
a build failure instead of a discovery months later.

Checks:
  1. Parses      — the file is valid JSON with the expected top-level shape.
  2. Schema      — the constraints published at
                   https://skills.sh/schemas/skills.sh.schema.json, enforced
                   locally so CI needs no network: groupings is a non-empty
                   list of at most 50 objects; each has a required `title`
                   (1-120 chars) and a required non-empty `skills` list (at
                   most 500 entries, each 1-120 chars); `description` is
                   optional and at most 500 chars; `notGrouped` is "top" or
                   "bottom".
  3. No duplicates — a skill appears in at most one grouping.
  4. Bijection   — every skills/<name>/ is grouped, and every grouped name
                   exists on disk.

--fix repairs only what is unambiguous: it removes grouped names that no longer
exist on disk (and any grouping left empty as a result). It deliberately does
NOT place newly added skills — which section a skill belongs to is an editorial
judgement, not something a script should guess.

Outputs:
  - Default: one finding per line, human-readable; exit 1 if any.
  - --json : newline-delimited JSON for downstream tooling.

Usage:
    python3 scripts/check-skills-sh.py
    python3 scripts/check-skills-sh.py --json
    python3 scripts/check-skills-sh.py --fix
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills.sh.json"
SKILLS_DIR = REPO_ROOT / "skills"

SCHEMA_URL = "https://skills.sh/schemas/skills.sh.schema.json"
NOT_GROUPED_VALUES = {"top", "bottom"}
TOP_LEVEL_KEYS = {"$schema", "schema", "notGrouped", "groupings"}

MAX_GROUPINGS = 50
MAX_TITLE = 120
MAX_DESCRIPTION = 500
MAX_SKILLS_PER_GROUP = 500
MAX_SKILL_NAME = 120


def load_manifest():
    if not MANIFEST_PATH.exists():
        sys.exit(f"Manifest not found at {MANIFEST_PATH}.")
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"{MANIFEST_PATH.name} is not valid JSON: {exc}")


def skills_on_disk():
    """Skill directory names — a skill is any skills/<name>/SKILL.md."""
    if not SKILLS_DIR.is_dir():
        sys.exit(f"Skills directory not found at {SKILLS_DIR}.")
    return {p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")}


def check_schema(manifest):
    """Structural findings. Returns (findings, groupings, usable) — `groupings`
    is the subset safe to reason about downstream, and `usable` is False when
    the groupings key itself is unusable, so the caller can skip the coverage
    check rather than report every skill on disk as ungrouped."""
    findings = []

    if not isinstance(manifest, dict):
        return ([{"key": MANIFEST_PATH.name, "error": "top level must be a JSON object"}], [], False)

    for key in sorted(set(manifest) - TOP_LEVEL_KEYS):
        findings.append({"key": key,
                         "error": f"unknown top-level key — expected one of {sorted(TOP_LEVEL_KEYS)}"})

    schema = manifest.get("$schema")
    if schema is not None and schema != SCHEMA_URL:
        findings.append({"key": "$schema", "error": f"expected {SCHEMA_URL!r}, got {schema!r}"})

    not_grouped = manifest.get("notGrouped")
    if not_grouped is not None and not_grouped not in NOT_GROUPED_VALUES:
        findings.append({"key": "notGrouped",
                         "error": f"must be one of {sorted(NOT_GROUPED_VALUES)}, got {not_grouped!r}"})

    groupings = manifest.get("groupings")
    if not isinstance(groupings, list) or not groupings:
        findings.append({"key": "groupings", "error": "required, and must be a non-empty list"})
        return (findings, [], False)
    if len(groupings) > MAX_GROUPINGS:
        findings.append({"key": "groupings",
                         "error": f"at most {MAX_GROUPINGS} groupings, got {len(groupings)}"})

    valid = []
    for index, group in enumerate(groupings):
        where = f"groupings[{index}]"
        if not isinstance(group, dict):
            findings.append({"key": where, "error": "must be an object"})
            continue

        title = group.get("title")
        if not isinstance(title, str) or not 1 <= len(title) <= MAX_TITLE:
            findings.append({"key": where,
                             "error": f"`title` is required and must be 1-{MAX_TITLE} characters"})
        else:
            where = f"groupings[{index}] {title!r}"

        description = group.get("description")
        if description is not None and (not isinstance(description, str)
                                        or len(description) > MAX_DESCRIPTION):
            findings.append({"key": where,
                             "error": f"`description` must be a string of at most "
                                      f"{MAX_DESCRIPTION} characters"})

        skills = group.get("skills")
        if not isinstance(skills, list) or not skills:
            findings.append({"key": where, "error": "`skills` is required and must be non-empty"})
            continue
        if len(skills) > MAX_SKILLS_PER_GROUP:
            findings.append({"key": where,
                             "error": f"at most {MAX_SKILLS_PER_GROUP} skills, got {len(skills)}"})
        for name in skills:
            if not isinstance(name, str) or not 1 <= len(name) <= MAX_SKILL_NAME:
                findings.append({"key": where,
                                 "error": f"skill entry {name!r} must be a string of "
                                          f"1-{MAX_SKILL_NAME} characters"})
        valid.append(group)

    return (findings, valid, True)


def check_coverage(groupings, on_disk):
    """Duplicate and bijection findings."""
    findings = []
    seen = {}

    for group in groupings:
        title = group.get("title", "?")
        for name in group.get("skills", []):
            if not isinstance(name, str):
                continue
            if name in seen:
                findings.append({"key": name,
                                 "error": f"listed in more than one grouping "
                                          f"({seen[name]!r} and {title!r})"})
            else:
                seen[name] = title

    for name in sorted(set(seen) - on_disk):
        findings.append({"key": name,
                         "error": "grouped but no skills/<name>/SKILL.md exists — the skill was "
                                  "renamed or removed. Run --fix to drop it."})

    for name in sorted(on_disk - set(seen)):
        findings.append({"key": name,
                         "error": "exists on disk but is in no grouping — it would render "
                                  "ungrouped on skills.sh. Add it to the right section by hand "
                                  "(placement is an editorial call, so --fix will not guess)."})

    return findings


def validate(manifest, on_disk):
    schema_findings, groupings, usable = check_schema(manifest)
    if not usable:
        # `groupings` is absent or malformed — reporting all 24 skills as
        # ungrouped would bury the one finding that matters.
        return schema_findings
    return schema_findings + check_coverage(groupings, on_disk)


def fix(manifest, on_disk):
    """Drop grouped names that no longer exist, and any grouping left empty."""
    groupings = manifest.get("groupings")
    if not isinstance(groupings, list):
        sys.exit(f"Cannot --fix: `groupings` in {MANIFEST_PATH.name} is not a list.")

    removed, dropped_groups, kept = [], [], []
    for group in groupings:
        if not isinstance(group, dict) or not isinstance(group.get("skills"), list):
            kept.append(group)
            continue
        title = group.get("title", "?")
        surviving = [n for n in group["skills"] if not isinstance(n, str) or n in on_disk]
        removed += [f"{n} (was in {title!r})" for n in group["skills"]
                    if isinstance(n, str) and n not in on_disk]
        if surviving:
            group["skills"] = surviving
            kept.append(group)
        else:
            dropped_groups.append(title)

    if not removed:
        print(f"{MANIFEST_PATH.name} has no stale entries to remove.")
    else:
        manifest["groupings"] = kept
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        print(f"Removed {len(removed)} stale entr{'y' if len(removed) == 1 else 'ies'} "
              f"from {MANIFEST_PATH.name}:")
        for entry in removed:
            print(f"  - {entry}")
        for title in dropped_groups:
            print(f"  ! grouping {title!r} dropped — it had no surviving skills")

    # Ungrouped skills are never auto-placed; surface them so --fix isn't
    # mistaken for "the manifest is now correct".
    grouped = {n for g in manifest.get("groupings", []) if isinstance(g, dict)
               for n in g.get("skills", []) if isinstance(n, str)}
    ungrouped = sorted(on_disk - grouped)
    if ungrouped:
        print(f"\n{len(ungrouped)} skill(s) still need a grouping — add by hand:")
        for name in ungrouped:
            print(f"  - {name}")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true",
                        help="Emit newline-delimited JSON instead of text")
    parser.add_argument("--fix", action="store_true",
                        help="Remove grouped names that no longer exist on disk")
    args = parser.parse_args()

    manifest = load_manifest()
    on_disk = skills_on_disk()

    if args.fix:
        return fix(manifest, on_disk)

    findings = validate(manifest, on_disk)

    if args.json:
        for finding in findings:
            print(json.dumps(finding))
        return 1 if findings else 0

    if not findings:
        sections = len(manifest.get("groupings", []))
        print(f"OK — {len(on_disk)} skills grouped across {sections} section(s).")
        return 0

    print(f"{len(findings)} finding(s):\n")
    for finding in findings:
        print(f"  {finding['key']}: {finding['error']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
