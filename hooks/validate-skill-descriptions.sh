#!/bin/bash
# Validate skill description lengths
# Enforces two limits on every SKILL.md frontmatter:
#   - `description` alone must be ≤ 1024 characters (repo cap, keeps descriptions focused).
#   - `description` + `when_to_use` must fit in 1,536 characters combined. Claude Code
#     renders them as "<description> - <when_to_use>" in the skill listing and truncates
#     past that point (https://code.claude.com/docs/en/skills.md), so anything beyond it —
#     including `→` redirects — is silently dropped and never reaches the model.
#
# Usage:
#   validate-skill-descriptions.sh [file1 file2 ...]
# If no files specified, checks staged files (for pre-commit hook)

set -e

# The listing cap is measured in characters, not bytes. Force a UTF-8 locale so
# `${#var}` counts `→` and `—` as one character on CI, macOS, and Git Bash alike
# (in a C/POSIX locale bash counts bytes and over-reports by 2 per such char).
export LC_ALL=C.UTF-8

LIMIT=1024
LISTING_LIMIT=1536
SEPARATOR_LEN=3   # the " - " Claude Code inserts between the two fields
FAILED=0

# Determine which files to check
if [ "$#" -eq 0 ]; then
  # Pre-commit mode: check staged SKILL.md files
  FILES=$(git diff --cached --name-only --diff-filter=ACM | grep 'skills/.*/SKILL\.md$' || true)
else
  # Explicit mode: use provided files
  FILES="$@"
fi

# Extract a single-line frontmatter field, with or without surrounding quotes.
extract_field() {
  local field=$1 file=$2 value
  value=$(sed -n "s/^${field}: \"\(.*\)\"$/\1/p" "$file" | head -1)
  if [ -z "$value" ]; then
    value=$(sed -n "s/^${field}: \(.*\)$/\1/p" "$file" | head -1)
  fi
  printf '%s' "$value"
}

for file in $FILES; do
  if [ ! -f "$file" ]; then
    continue
  fi

  desc=$(extract_field description "$file")
  wtu=$(extract_field when_to_use "$file")

  len=${#desc}
  if [ -n "$wtu" ]; then
    listing_len=$((len + SEPARATOR_LEN + ${#wtu}))
  else
    listing_len=$len
  fi

  ok=1
  if [ "$len" -gt "$LIMIT" ]; then
    echo "❌ $file: description exceeds $LIMIT characters ($len chars)"
    FAILED=1
    ok=0
  fi
  if [ "$listing_len" -gt "$LISTING_LIMIT" ]; then
    echo "❌ $file: description + when_to_use exceeds the $LISTING_LIMIT-character listing cap ($listing_len chars; the last $((listing_len - LISTING_LIMIT)) would be truncated)"
    FAILED=1
    ok=0
  fi
  if [ "$ok" -eq 1 ]; then
    if [ -n "$wtu" ]; then
      echo "✓ $file: $len chars (listing: $listing_len chars)"
    else
      echo "✓ $file: $len chars"
    fi
  fi
done

if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "Skill description validation failed."
  echo "  - 'description' must be ≤ $LIMIT characters (repo cap)."
  echo "  - 'description' + 'when_to_use' must be ≤ $LISTING_LIMIT characters combined:"
  echo "    Claude Code truncates the skill listing there and drops the rest, including → redirects."
  echo "Edit the frontmatter in SKILL.md and try again."
  exit 1
fi

exit 0
