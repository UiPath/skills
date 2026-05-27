#!/usr/bin/env python3
"""
Validate skill lifecycle status against the manifest at assets/skill-status.json
(the single source of truth) and generate the status table in README.md.

Checks (default mode):
  1. Bijection   — every skills/<name>/ has a manifest entry and vice versa.
  2. Legal status — each skill's status is one of the canonical values.
  3. Frontmatter guard — SKILL.md description must not carry a status tag
     like [PREVIEW]/[BETA] (status lives only in the manifest).
  4. No stale body markers — SKILL.md body must not carry a
     `> **Preview**` / `> **Status:**` callout (status lives only in the manifest).

README generation:
  --write-readme  regenerate the status table between the markers
                  `<!-- BEGIN GENERATED SKILL STATUS -->` / `<!-- END ... -->`.
  --check-readme  fail if the table is out of date (CI uses this).

Outputs:
  - Default: one finding per line, human-readable; exit 1 if any.
  - --json : newline-delimited JSON for downstream tooling.

Usage:
    python3 scripts/check-skill-status.py
    python3 scripts/check-skill-status.py --json
    python3 scripts/check-skill-status.py --write-readme
    python3 scripts/check-skill-status.py --check-readme
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "assets" / "skill-status.json"
SKILLS_DIR = REPO_ROOT / "skills"
README_PATH = REPO_ROOT / "README.md"

# Canonical display order for the README legend.
STATUS_ORDER = ["ga", "public-preview", "private-preview", "in-development"]

# A status tag wrongly embedded in the frontmatter description.
FM_TAG_RE = re.compile(r"\[(?:preview|beta|alpha|ga|deprecated|experimental)\]", re.I)
# A stale status callout in the body — anchored on the status keyword so
# non-status opening blockquotes (e.g. `> **Two entry points.**`) never match.
STALE_BODY_RE = re.compile(r"^>\s*\*\*(?:Status:|Preview\b|Beta\b|Alpha\b)", re.I)

BEGIN_MARKER = "<!-- BEGIN GENERATED SKILL STATUS -->"
END_MARKER = "<!-- END GENERATED SKILL STATUS -->"
BLOCK_RE = re.compile(
    re.escape(BEGIN_MARKER) + r"(.*?)" + re.escape(END_MARKER), re.DOTALL
)


def load_manifest():
    if not MANIFEST_PATH.exists():
        sys.exit(f"Manifest not found at {MANIFEST_PATH}.")
    return json.loads(MANIFEST_PATH.read_text())


def split_frontmatter(text):
    """Return (frontmatter_text, body_text). Empty frontmatter if no fences."""
    if not text.startswith("---"):
        return "", text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return "", text
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:])


def extract_description(frontmatter_text):
    for line in frontmatter_text.splitlines():
        if line.startswith("description:"):
            return line[len("description:"):]
    return ""


def discover_skills():
    return {
        p.name
        for p in SKILLS_DIR.iterdir()
        if p.is_dir() and (p / "SKILL.md").exists()
    }


def validate(manifest):
    """Return a list of findings: {"skill": ..., "error": ...}."""
    findings = []
    valid_statuses = set(manifest.get("statuses", {}))
    entries = manifest.get("skills", {})
    folders = discover_skills()

    for name in sorted(folders | set(entries)):
        if name not in entries:
            findings.append({"skill": name,
                             "error": "no entry in assets/skill-status.json"})
            continue
        if name not in folders:
            findings.append({"skill": name,
                             "error": "manifest entry has no skills/<name>/SKILL.md"})
            continue

        status = entries[name].get("status")
        if status not in valid_statuses:
            findings.append({"skill": name,
                             "error": f"invalid status {status!r} "
                                      f"(expected one of {sorted(valid_statuses)})"})

        text = (SKILLS_DIR / name / "SKILL.md").read_text()
        frontmatter, body = split_frontmatter(text)
        if FM_TAG_RE.search(extract_description(frontmatter)):
            findings.append({"skill": name,
                             "error": "status tag (e.g. [PREVIEW]) in frontmatter "
                                      "description — status belongs only in the manifest"})
        for lineno, line in enumerate(body.splitlines(), start=1):
            if STALE_BODY_RE.match(line):
                findings.append({"skill": name,
                                 "error": f"stale status callout in body: {line.strip()!r} "
                                          "— status belongs only in the manifest"})
                break
    return findings


def build_status_block(manifest):
    """Render the inner content (table + legend) for the README block."""
    statuses = manifest["statuses"]
    entries = manifest["skills"]
    lines = ["| Skill | Status |", "|-------|--------|"]
    for name in sorted(entries):
        label = statuses[entries[name]["status"]]["label"]
        lines.append(f"| `{name}` | {label} |")
    lines.append("")
    lines.append("**Status legend:**")
    for key in STATUS_ORDER:
        if key in statuses:
            lines.append(f"- **{statuses[key]['label']}** — {statuses[key]['meaning']}")
    return "\n".join(lines)


def render_region(manifest):
    """The exact text expected between the BEGIN and END markers."""
    return "\n" + build_status_block(manifest) + "\n"


def write_readme(manifest):
    if not README_PATH.exists():
        sys.exit(f"README not found at {README_PATH}.")
    text = README_PATH.read_text()
    if not BLOCK_RE.search(text):
        sys.exit(f"Marker pair not found in {README_PATH}. Add this block once:\n"
                 f"{BEGIN_MARKER}\n{END_MARKER}")
    new_text = BLOCK_RE.sub(
        lambda m: BEGIN_MARKER + render_region(manifest) + END_MARKER, text
    )
    if new_text != text:
        README_PATH.write_text(new_text)
        print(f"Updated skill status table in {README_PATH.name}.")
    else:
        print(f"{README_PATH.name} skill status table already current.")
    return 0


def check_readme(manifest):
    if not README_PATH.exists():
        sys.exit(f"README not found at {README_PATH}.")
    text = README_PATH.read_text()
    match = BLOCK_RE.search(text)
    if not match:
        print(f"FAIL — marker pair not found in {README_PATH.name}. "
              f"Add {BEGIN_MARKER} / {END_MARKER}.", file=sys.stderr)
        return 1
    if match.group(1) != render_region(manifest):
        print(f"FAIL — skill status table in {README_PATH.name} is out of date. "
              "Run: python3 scripts/check-skill-status.py --write-readme",
              file=sys.stderr)
        return 1
    print(f"OK — {README_PATH.name} skill status table is current.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true",
                        help="Emit newline-delimited JSON instead of text")
    parser.add_argument("--write-readme", action="store_true",
                        help="Regenerate the README status table in place")
    parser.add_argument("--check-readme", action="store_true",
                        help="Fail if the README status table is out of date")
    args = parser.parse_args()

    manifest = load_manifest()

    if args.write_readme:
        return write_readme(manifest)
    if args.check_readme:
        return check_readme(manifest)

    findings = validate(manifest)

    if args.json:
        for f in findings:
            print(json.dumps(f))
        return 1 if findings else 0

    if not findings:
        n = len(manifest.get("skills", {}))
        print(f"OK — {n} skills, manifest valid.")
        return 0

    print(f"{len(findings)} finding(s):\n")
    for f in findings:
        print(f"  {f['skill']}: {f['error']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
