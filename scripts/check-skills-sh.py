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

--baseline-ref scopes the exit code to drift THIS change introduces. The check
reads the whole tree, so drift already on the base branch otherwise fails every
unrelated PR that touches any skills/*/SKILL.md. That is not hypothetical: when
uipath-process-mining landed ungrouped on 2026-08-04 (#2252), the next 48 hours
produced 65 failures across ~20 unrelated branches until an unrelated PR (#2498)
happened to add the entry. With --baseline-ref, findings that also reproduce at
the baseline are reported as warnings and do not fail the run; only new findings
exit 1. Whole-tree visibility is kept — the blast radius is not.

Outputs:
  - Default: one finding per line, human-readable; exit 1 if any.
  - --json : newline-delimited JSON for downstream tooling.

Usage:
    python3 scripts/check-skills-sh.py
    python3 scripts/check-skills-sh.py --json
    python3 scripts/check-skills-sh.py --fix
    python3 scripts/check-skills-sh.py --baseline-ref origin/main
"""

import argparse
import json
import os
import subprocess
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


def finding(kind, key, subject, error):
    """One finding.

    `key` and `error` are for display. `kind` and `subject` are the identity
    used to decide whether the same drift exists at the baseline, so neither
    may embed anything that unrelated edits can change — no list indices, and
    no grouping titles for findings that are really about a skill name.
    """
    return {"kind": kind, "key": key, "subject": subject, "error": error}


def check_schema(manifest):
    """Structural findings. Returns (findings, groupings, usable) — `groupings`
    is the subset safe to reason about downstream, and `usable` is False when
    the groupings key itself is unusable, so the caller can skip the coverage
    check rather than report every skill on disk as ungrouped."""
    findings = []

    if not isinstance(manifest, dict):
        return ([finding("top-level-type", MANIFEST_PATH.name, MANIFEST_PATH.name,
                         "top level must be a JSON object")], [], False)

    for key in sorted(set(manifest) - TOP_LEVEL_KEYS):
        findings.append(finding("unknown-top-level-key", key, key,
                                f"unknown top-level key — expected one of "
                                f"{sorted(TOP_LEVEL_KEYS)}"))

    schema = manifest.get("$schema")
    if schema is not None and schema != SCHEMA_URL:
        findings.append(finding("schema-url", "$schema", "$schema",
                                f"expected {SCHEMA_URL!r}, got {schema!r}"))

    not_grouped = manifest.get("notGrouped")
    if not_grouped is not None and not_grouped not in NOT_GROUPED_VALUES:
        findings.append(finding("not-grouped-value", "notGrouped", "notGrouped",
                                f"must be one of {sorted(NOT_GROUPED_VALUES)}, "
                                f"got {not_grouped!r}"))

    groupings = manifest.get("groupings")
    if not isinstance(groupings, list) or not groupings:
        findings.append(finding("groupings-missing", "groupings", "groupings",
                                "required, and must be a non-empty list"))
        return (findings, [], False)
    if len(groupings) > MAX_GROUPINGS:
        findings.append(finding("groupings-count", "groupings", "groupings",
                                f"at most {MAX_GROUPINGS} groupings, got {len(groupings)}"))

    valid = []
    for index, group in enumerate(groupings):
        # `key` is for display and carries the index so a reader can find the
        # entry. `subject` is the identity used for baseline comparison and
        # must NOT carry the index — inserting a grouping at the top shifts
        # every index and would re-attribute untouched drift as new.
        where = f"groupings[{index}]"
        if not isinstance(group, dict):
            findings.append(finding("group-type", where, where, "must be an object"))
            continue

        title = group.get("title")
        titled = isinstance(title, str) and 1 <= len(title) <= MAX_TITLE
        # An invalid title leaves nothing stabler than the index to key on;
        # that finding is by definition about the entry the author just touched.
        subject = title if titled else where
        if not titled:
            findings.append(finding("group-title", where, subject,
                                    f"`title` is required and must be 1-{MAX_TITLE} characters"))
        else:
            where = f"groupings[{index}] {title!r}"

        description = group.get("description")
        if description is not None and (not isinstance(description, str)
                                        or len(description) > MAX_DESCRIPTION):
            findings.append(finding("group-description", where, subject,
                                    f"`description` must be a string of at most "
                                    f"{MAX_DESCRIPTION} characters"))

        skills = group.get("skills")
        if not isinstance(skills, list) or not skills:
            findings.append(finding("group-skills-missing", where, subject,
                                    "`skills` is required and must be non-empty"))
            continue
        if len(skills) > MAX_SKILLS_PER_GROUP:
            findings.append(finding("group-skills-count", where, subject,
                                    f"at most {MAX_SKILLS_PER_GROUP} skills, "
                                    f"got {len(skills)}"))
        for name in skills:
            if not isinstance(name, str) or not 1 <= len(name) <= MAX_SKILL_NAME:
                # Keyed on the offending entry, not the grouping: moving a bad
                # entry between groupings is the same pre-existing drift.
                findings.append(finding("skill-entry", where, repr(name),
                                        f"skill entry {name!r} must be a string of "
                                        f"1-{MAX_SKILL_NAME} characters"))
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
                # The message names both groupings for the reader, but identity
                # is the skill alone: retitling a grouping, or moving the
                # duplicate elsewhere, is not new drift.
                findings.append(finding("duplicate-grouping", name, name,
                                        f"listed in more than one grouping "
                                        f"({seen[name]!r} and {title!r})"))
            else:
                seen[name] = title

    for name in sorted(set(seen) - on_disk):
        findings.append(finding("grouped-not-on-disk", name, name,
                                "grouped but no skills/<name>/SKILL.md exists — the skill was "
                                "renamed or removed. Run --fix to drop it."))

    for name in sorted(on_disk - set(seen)):
        findings.append(finding("ungrouped", name, name,
                                "exists on disk but is in no grouping — it would render "
                                "ungrouped on skills.sh. Add it to the right section by hand "
                                "(placement is an editorial call, so --fix will not guess)."))

    return findings


def validate(manifest, on_disk):
    schema_findings, groupings, usable = check_schema(manifest)
    if not usable:
        # `groupings` is absent or malformed — reporting all 24 skills as
        # ungrouped would bury the one finding that matters.
        return schema_findings
    return schema_findings + check_coverage(groupings, on_disk)


# --- baseline comparison ----------------------------------------------------


def _git(*args):
    """Run git in the repo. Returns stdout, or None if the command failed."""
    try:
        result = subprocess.run(("git", "-C", str(REPO_ROOT)) + args,
                                capture_output=True, text=True, check=False)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def baseline_state(ref):
    """The manifest and skill set as of `ref`. Returns (manifest, on_disk) or
    None when the ref is unreadable — a shallow clone, a missing base, or a
    branch that predates skills.sh.json. Callers fall back to strict
    whole-tree validation rather than silently passing."""
    raw = _git("show", f"{ref}:{MANIFEST_PATH.name}")
    if raw is None:
        return None
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError:
        # A baseline that does not even parse cannot establish "pre-existing".
        return None

    listing = _git("ls-tree", "-r", "--name-only", ref, "--", SKILLS_DIR.name)
    if listing is None:
        return None
    on_disk = {parts[1] for parts in
               (line.split("/") for line in listing.splitlines())
               if len(parts) == 3 and parts[0] == SKILLS_DIR.name and parts[2] == "SKILL.md"}
    return (manifest, on_disk)


def identity(item):
    """What makes two findings 'the same drift' across two commits.

    Deliberately NOT the formatted message: it embeds grouping titles and list
    indices, so a retitle or an insertion would re-attribute untouched drift to
    the PR and block it.
    """
    return (item["kind"], item["subject"])


def split_by_baseline(findings, baseline):
    """Partition findings into (new, preexisting) using the baseline state."""
    baseline_manifest, baseline_on_disk = baseline
    already = {identity(f) for f in validate(baseline_manifest, baseline_on_disk)}
    new, preexisting = [], []
    for item in findings:
        (preexisting if identity(item) in already else new).append(item)
    return (new, preexisting)


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
    parser.add_argument("--baseline-ref", metavar="REF",
                        help="Git ref to treat as the baseline (e.g. origin/main). Findings "
                             "that also reproduce at REF are warnings, not failures, so "
                             "drift already on the base branch does not fail this change.")
    args = parser.parse_args()

    manifest = load_manifest()
    on_disk = skills_on_disk()

    if args.fix:
        return fix(manifest, on_disk)

    findings = validate(manifest, on_disk)
    preexisting = []

    if args.baseline_ref:
        baseline = baseline_state(args.baseline_ref)
        if baseline is None:
            # Fail closed: without a readable baseline every finding stays
            # blocking, which is the pre---baseline-ref behaviour.
            print(f"Warning: cannot read baseline {args.baseline_ref!r} — treating every "
                  f"finding as new.", file=sys.stderr)
        else:
            findings, preexisting = split_by_baseline(findings, baseline)

    if args.json:
        for item in findings:
            print(json.dumps({**item, "preexisting": False}))
        for item in preexisting:
            print(json.dumps({**item, "preexisting": True}))
        return 1 if findings else 0

    annotate = os.environ.get("GITHUB_ACTIONS") == "true"

    if preexisting:
        print(f"{len(preexisting)} pre-existing finding(s) — already present at "
              f"{args.baseline_ref}, not caused by this change:\n")
        for item in preexisting:
            prefix = "::warning::" if annotate else "  "
            print(f"{prefix}{item['key']}: {item['error']}")
        print()

    if not findings:
        sections = len(manifest.get("groupings", []))
        print(f"OK — {len(on_disk)} skills grouped across {sections} section(s).")
        if preexisting:
            print("Pre-existing drift above still needs a fix — see CONTRIBUTING.md "
                  "§ Register the skills.sh Grouping.")
        return 0

    print(f"{len(findings)} finding(s):\n")
    for item in findings:
        prefix = "::error::" if annotate else "  "
        print(f"{prefix}{item['key']}: {item['error']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
