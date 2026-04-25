#!/bin/bash
# Validate skill description lengths
# Enforces a 1024-character limit on all SKILL.md descriptions.
# Claude Code truncates the combined `description` + `when_to_use` at 1,536 chars
# in the skill listing (https://code.claude.com/docs/en/skills.md). 1024 keeps
# us comfortably under that cap while leaving headroom for `when_to_use`.
#
# Usage:
#   validate-skill-descriptions.sh [file1 file2 ...]
# If no files specified, checks staged files (for pre-commit hook)

set -e

LIMIT=1024
FAILED=0

# Determine which files to check
if [ "$#" -eq 0 ]; then
  # Pre-commit mode: check staged SKILL.md files
  FILES=$(git diff --cached --name-only --diff-filter=ACM | grep 'skills/.*/SKILL\.md$' || true)
else
  # Explicit mode: use provided files
  FILES="$@"
fi

for file in $FILES; do
  if [ ! -f "$file" ]; then
    continue
  fi

  # Extract description from frontmatter
  desc=$(sed -n 's/^description: "\(.*\)"$/\1/p' "$file" | head -1)

  # Also handle descriptions without surrounding quotes
  if [ -z "$desc" ]; then
    desc=$(sed -n 's/^description: \(.*\)$/\1/p' "$file" | head -1)
  fi

  len=${#desc}

  if [ "$len" -gt "$LIMIT" ]; then
    echo "❌ $file: description exceeds $LIMIT characters ($len chars)"
    FAILED=1
  else
    echo "✓ $file: $len chars"
  fi
done

if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "Skill description validation failed. Descriptions must be ≤ $LIMIT characters."
  echo "Claude Code truncates description + when_to_use at 1,536 chars in the skill listing;"
  echo "this repo caps at $LIMIT to leave headroom and keep descriptions focused."
  echo "Edit the 'description' field in SKILL.md frontmatter and try again."
  exit 1
fi

exit 0
