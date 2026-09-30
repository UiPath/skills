#!/bin/bash
# Verify this skill never pins a .flow version as authoritative in prose, and
# never hardcodes the top-level .flow `version` literal.
# Usage: bash .maintenance/check-versions.sh [file1.md ...]
# Output: BAD lines per violation, then "lines_checked=N violations=M" summary.
#
# Rationale: the .flow top-level `version` and node `typeVersion` are owned by
# `uip maestro flow init` / `uip maestro flow registry get`. Hardcoding them in
# docs rots silently when the CLI/registry advances (e.g. core.action.http.v2
# 2.0 -> 2.1, core.trigger.scheduled 1.0 -> 1.1, top-level 1.1 -> 1.2). The rule
# is: reference the live command, never pin the number as "current"/"required".
#
# Two violation classes (both high-confidence — chosen to NOT re-flag the many
# legitimate illustrative `"typeVersion": "1.0"` JSON examples that are governed
# by an adjacent registry-sourcing note):
#
#   1. PROSE-PIN  — prose that states a version as current or mandatory, e.g.
#      `currently "1.1"`, `the registry currently emits "1.0"`, `must be "2.0"`,
#      `use version "1.0"`. These claims go stale.
#   2. TOPLEVEL   — a hardcoded top-level `.flow` `"version": "x.y"` literal.
#      Top-level version must always be the `uip maestro flow init` placeholder
#      (e.g. `"<version from \`uip maestro flow init\`>"`), never a number.
#
# Explicitly NOT flagged:
#   - `"typeVersion": "x.y"` literals in node JSON examples (legitimate when
#     paired with a sourcing note; too many true-illustrative cases to flag).
#   - `bindings_v2.json` `"version": "2.0"` — a fixed schema constant, not a
#     .flow version. Distinguished by the surrounding `"resources"` key.
#
# Skipping: add `<!-- version-check-skip -->` anywhere on a line to suppress it
# (e.g. a historical/version-comparison note that documents an old literal on
# purpose). For table rows, place the marker inside a cell.
#
# Scans SKILL.md + references/**/*.md. Skips .maintenance/ and root scratch
# files (PLAN.md, PR_BODY.md). Exits non-zero if any violation is found.

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on PATH" >&2
  exit 2
fi

FILES=("$@")
if [ "${#FILES[@]}" -eq 0 ]; then
  while IFS= read -r f; do
    FILES+=("$f")
  done < <({ [ -f SKILL.md ] && echo "./SKILL.md"; /usr/bin/find ./references -type f -name '*.md' 2>/dev/null; } | /usr/bin/sort)
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  echo ""
  echo "lines_checked=0 violations=0"
  exit 0
fi

python3 - "${FILES[@]}" <<'PY'
import re, sys

files = sys.argv[1:]

SKIP_MARKER = "<!-- version-check-skip -->"

# A quoted version literal: "1.0", "1.1", "2.0", "1.0.0", etc.
VER = r'"\d+\.\d+(?:\.\d+)?"'

# Class 1 — PROSE-PIN: a version literal stated as current / mandatory.
# Two sub-patterns (note: docs wrap versions in backticks, e.g. `"1.1"`, so the
# gap class must NOT exclude backticks):
#   (a) a pinning verb followed within a short window by a version literal —
#       `currently "1.1"`, `the registry currently emits "1.0"`, `must be "2.0"`.
#   (b) an inline assignment of a version field to a literal in prose —
#       `typeVersion: "2.0"`, `version: "1.1"` (the original http/impl.md:27 bug
#       had no pin-verb — it just stated `typeVersion: "2.0"`).
PROSE_PIN_VERB = re.compile(
    r'(currently|current\b|must be|use version|emits|emit|is currently|as of)'
    r'[^\n]{0,40}?' + VER,
    re.IGNORECASE,
)
PROSE_PIN_ASSIGN = re.compile(
    r'(typeVersion|version)\s*[:=]\s*' + VER,
    re.IGNORECASE,
)

def prose_pin(line):
    return PROSE_PIN_VERB.search(line) or PROSE_PIN_ASSIGN.search(line)

# Class 2 — TOPLEVEL: a hardcoded top-level `.flow` `"version": "x.y"`.
# Only the .flow document's OWN top-level version is in scope — NOT
# `definitions[].version` (node manifest versions), NOT eval-file `version`,
# NOT `bindings_v2.json` `version`, NOT `connectorDetail.configuration.version`.
# We identify a true top-level .flow version by its sibling keys: a real .flow
# object has `"nodes"` and `"edges"` (and usually `"name"`) within a few lines.
# Definitions entries instead carry `"nodeType"`; bindings_v2 carries
# `"resources"`; eval files carry `"evaluatorRefs"` / `"evaluatorTypeId"` /
# `"evaluations"`. Presence of any of those disqualifies the match.
TOPLEVEL = re.compile(r'"version"\s*:\s*' + VER)

_FLOW_SIBLINGS = ('"nodes"', '"edges"')
_DISQUALIFY = ('"nodeType"', '"resources"', '"evaluatorRefs"',
               '"evaluatorTypeId"', '"evaluations"', '"connectorDetail"')

def is_flow_toplevel_version(lines, idx):
    # Look at a window around the `"version"` line for the discriminating keys,
    # bounded to the current fenced block so it never bleeds into an adjacent
    # JSON example (e.g. a following `definitions` entry with `"nodeType"`).
    lo = idx - 1
    while lo >= 0 and not lines[lo].strip().startswith("```"):
        lo -= 1
    lo += 1
    hi = idx + 1
    while hi < len(lines) and not lines[hi].strip().startswith("```"):
        hi += 1
    window = "\n".join(lines[lo:hi])
    if any(k in window for k in _DISQUALIFY):
        return False
    return all(k in window for k in _FLOW_SIBLINGS)

lines_checked = 0
violations = 0

for path in files:
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        continue

    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Track fenced code blocks so PROSE-PIN only fires on real prose.
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        lines_checked += 1
        if SKIP_MARKER in line:
            continue

        # Class 1: prose only (outside fences).
        if not in_fence and prose_pin(line):
            print(f"BAD  {path}:{i+1}  PROSE-PIN — version stated as current/required; reference `registry get`/`flow init` instead")
            print(f"       {stripped[:140]}")
            violations += 1
            continue

        # Class 2: top-level `.flow` "version" literal — JSON examples only,
        # and only when the surrounding object is a genuine .flow document.
        if in_fence and TOPLEVEL.search(line) and is_flow_toplevel_version(lines, i):
            print(f"BAD  {path}:{i+1}  TOPLEVEL — hardcoded top-level `.flow` `version` literal; use the `uip maestro flow init` placeholder")
            print(f"       {stripped[:140]}")
            violations += 1

print()
print(f"lines_checked={lines_checked} violations={violations}")
sys.exit(1 if violations else 0)
PY
