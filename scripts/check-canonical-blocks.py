#!/usr/bin/env python3
"""
Verify canonical blocks embedded in skill docs against their source of truth
at assets/canonical-blocks/<block-id>.md.

Skills are self-contained — each keeps its own physical copy of shared
boilerplate — but every copy wrapped in marker comments must stay
byte-identical (after newline normalization and trimming of leading/trailing
blank lines) to the canonical file:

    <!-- BEGIN CANONICAL: <block-id> -->
    ...body...
    <!-- END CANONICAL: <block-id> -->

Checks (default mode):
  1. Drift      — marked body differs from assets/canonical-blocks/<block-id>.md
                  (finding includes a unified diff snippet).
  2. Unknown id — markers reference a block-id with no canonical file.
  3. Marker sanity — BEGIN without END, END without BEGIN, id mismatch.
  4. Orphan     — canonical file with no occurrence under skills/ (warning).

Fix tool:
  --write  rewrite every occurrence's body from the canonical file.
  --list   print block-id -> occurrence count + paths.

Outputs:
  - Default: one finding per line, human-readable; exit 1 if any.
  - --json : newline-delimited JSON for downstream tooling.

Usage:
    python3 scripts/check-canonical-blocks.py
    python3 scripts/check-canonical-blocks.py --json
    python3 scripts/check-canonical-blocks.py --list
    python3 scripts/check-canonical-blocks.py --write
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "assets" / "canonical-blocks"
SKILLS_DIR = REPO_ROOT / "skills"

BEGIN_RE = re.compile(r"^\s*<!--\s*BEGIN CANONICAL:\s*([A-Za-z0-9._-]+)\s*-->\s*$")
END_RE = re.compile(r"^\s*<!--\s*END CANONICAL:\s*([A-Za-z0-9._-]+)\s*-->\s*$")

MAX_DIFF_LINES = 30


def rel(path):
    return path.relative_to(REPO_ROOT).as_posix()


def to_lines(text):
    """Normalize line endings to \\n and split into lines."""
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def normalize(text):
    """Normalize line endings and strip leading/trailing blank lines."""
    lines = to_lines(text)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def load_canonical():
    """Return {block_id: normalized body} from assets/canonical-blocks/."""
    if not CANONICAL_DIR.exists():
        sys.exit(f"Canonical blocks directory not found at {CANONICAL_DIR}.")
    return {
        p.stem: normalize(p.read_text(encoding="utf-8"))
        for p in sorted(CANONICAL_DIR.glob("*.md"))
    }


def scan_file(path):
    """Parse one markdown file.

    Returns (occurrences, findings). Each occurrence is a dict with the
    file path, block id, marker line indexes (0-based, exclusive of the
    markers themselves), and the raw body between the markers.
    """
    lines = to_lines(path.read_text(encoding="utf-8"))
    occurrences, findings = [], []
    i = 0
    while i < len(lines):
        end_match = END_RE.match(lines[i])
        if end_match:
            findings.append({"file": rel(path), "block": end_match.group(1),
                             "severity": "error",
                             "error": f"END marker without matching BEGIN (line {i + 1})"})
            i += 1
            continue
        begin_match = BEGIN_RE.match(lines[i])
        if not begin_match:
            i += 1
            continue

        block_id = begin_match.group(1)
        j = i + 1
        end_idx = None
        while j < len(lines):
            if BEGIN_RE.match(lines[j]):
                break  # nested BEGIN — outer block is unterminated
            inner_end = END_RE.match(lines[j])
            if inner_end:
                if inner_end.group(1) != block_id:
                    findings.append({"file": rel(path), "block": block_id,
                                     "severity": "error",
                                     "error": f"BEGIN '{block_id}' (line {i + 1}) closed by "
                                              f"END '{inner_end.group(1)}' (line {j + 1})"})
                end_idx = j
                break
            j += 1

        if end_idx is None:
            findings.append({"file": rel(path), "block": block_id,
                             "severity": "error",
                             "error": f"BEGIN marker without matching END (line {i + 1})"})
            i = j
            continue

        occurrences.append({"path": path, "block": block_id,
                            "body_start": i + 1, "body_end": end_idx,
                            "body": "\n".join(lines[i + 1:end_idx])})
        i = end_idx + 1
    return occurrences, findings


def scan_skills():
    """Scan skills/**/*.md. Returns (occurrences, findings)."""
    occurrences, findings = [], []
    for path in sorted(SKILLS_DIR.rglob("*.md")):
        occ, fnd = scan_file(path)
        occurrences.extend(occ)
        findings.extend(fnd)
    return occurrences, findings


def diff_snippet(canonical_body, actual_body, block_id, file_rel):
    diff = list(difflib.unified_diff(
        canonical_body.split("\n"), normalize(actual_body).split("\n"),
        fromfile=f"assets/canonical-blocks/{block_id}.md", tofile=file_rel,
        lineterm=""))
    if len(diff) > MAX_DIFF_LINES:
        diff = diff[:MAX_DIFF_LINES] + [f"... ({len(diff) - MAX_DIFF_LINES} more diff lines)"]
    return "\n".join(diff)


def validate(canonical, occurrences, findings):
    """Append drift / unknown-id / orphan findings. Returns findings."""
    for occ in occurrences:
        file_rel = rel(occ["path"])
        if occ["block"] not in canonical:
            findings.append({"file": file_rel, "block": occ["block"],
                             "severity": "error",
                             "error": f"unknown block-id '{occ['block']}' — no file "
                                      f"assets/canonical-blocks/{occ['block']}.md"})
            continue
        if normalize(occ["body"]) != canonical[occ["block"]]:
            findings.append({"file": file_rel, "block": occ["block"],
                             "severity": "error",
                             "error": "body drifted from canonical source — run: "
                                      "python3 scripts/check-canonical-blocks.py --write",
                             "diff": diff_snippet(canonical[occ["block"]], occ["body"],
                                                  occ["block"], file_rel)})

    used = {occ["block"] for occ in occurrences}
    for block_id in canonical:
        if block_id not in used:
            findings.append({"file": f"assets/canonical-blocks/{block_id}.md",
                             "block": block_id, "severity": "warning",
                             "error": "orphaned canonical file — no occurrence under skills/"})
    return findings


def write_blocks(canonical, occurrences):
    """Rewrite every known occurrence's body from its canonical file."""
    by_file = {}
    for occ in occurrences:
        if occ["block"] in canonical:
            by_file.setdefault(occ["path"], []).append(occ)

    updated = 0
    for path, occs in by_file.items():
        lines = to_lines(path.read_text(encoding="utf-8"))
        # Replace bottom-up so earlier indexes stay valid.
        changed = False
        for occ in sorted(occs, key=lambda o: o["body_start"], reverse=True):
            new_body = canonical[occ["block"]].split("\n")
            if lines[occ["body_start"]:occ["body_end"]] != new_body:
                lines[occ["body_start"]:occ["body_end"]] = new_body
                changed = True
        if changed:
            path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
            updated += 1
            print(f"Updated {rel(path)}")
    print(f"{updated} file(s) updated, {sum(len(v) for v in by_file.values())} occurrence(s) stamped.")
    return updated


def list_blocks(canonical, occurrences):
    by_block = {block_id: [] for block_id in canonical}
    for occ in occurrences:
        by_block.setdefault(occ["block"], []).append(rel(occ["path"]))
    for block_id in sorted(by_block):
        paths = by_block[block_id]
        marker = "" if block_id in canonical else "  [UNKNOWN — no canonical file]"
        print(f"{block_id} — {len(paths)} occurrence(s){marker}")
        for p in sorted(paths):
            print(f"  {p}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true",
                        help="Emit newline-delimited JSON instead of text")
    parser.add_argument("--write", action="store_true",
                        help="Rewrite every occurrence's body from its canonical file")
    parser.add_argument("--list", action="store_true",
                        help="Print block-id -> occurrence count + paths")
    args = parser.parse_args()

    canonical = load_canonical()
    occurrences, findings = scan_skills()

    if args.list:
        return list_blocks(canonical, occurrences)

    if args.write:
        write_blocks(canonical, occurrences)
        # Re-scan so marker-sanity and unknown-id findings still fail the run.
        occurrences, findings = scan_skills()

    findings = validate(canonical, occurrences, findings)

    if args.json:
        for f in findings:
            print(json.dumps(f))
        return 1 if findings else 0

    if not findings:
        print(f"OK — {len(canonical)} canonical block(s), "
              f"{len(occurrences)} occurrence(s) verified.")
        return 0

    print(f"{len(findings)} finding(s):\n")
    for f in findings:
        print(f"  [{f['severity']}] {f['file']} ({f['block']}): {f['error']}")
        if f.get("diff"):
            for line in f["diff"].split("\n"):
                print(f"      {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
