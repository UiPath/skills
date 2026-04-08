#!/bin/bash
# Validate skill description lengths
# Enforces 250-character limit on all SKILL.md descriptions
# (Claude Code truncates non-bundled skill descriptions at 250 chars in the system prompt)
#
# Usage:
#   validate-skill-descriptions.sh [file1 file2 ...]
# If no files specified, checks staged files (for pre-commit hook)

set -e

LIMIT=250
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
  echo "Claude Code truncates plugin skill descriptions at 250 chars in the system prompt."
  echo "Edit the 'description' field in SKILL.md frontmatter and try again."
  exit 1
fi

exit 0
