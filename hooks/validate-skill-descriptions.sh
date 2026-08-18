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
# Claude Code truncates `description` + `when_to_use` together at this many
# characters. Reported as a warning rather than enforced: three skills already
# ship over it, and failing them here would break PRs that only touch their
# own SKILL.md. The number is what matters — it is invisible otherwise.
COMBINED_LIMIT=1536
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

  # when_to_use is optional; missing means a combined total equal to len
  wtu=$(sed -n 's/^when_to_use: "\(.*\)"$/\1/p' "$file" | head -1)
  if [ -z "$wtu" ]; then
    wtu=$(sed -n 's/^when_to_use: \(.*\)$/\1/p' "$file" | head -1)
  fi
  combined=$((len + ${#wtu}))

  if [ "$len" -gt "$LIMIT" ]; then
    echo "❌ $file: description exceeds $LIMIT characters ($len chars)"
    FAILED=1
  else
    echo "✓ $file: $len chars (description + when_to_use: $combined)"
  fi

  if [ "$combined" -gt "$COMBINED_LIMIT" ]; then
    echo "⚠️  $file: description + when_to_use is $combined chars, over the $COMBINED_LIMIT Claude Code shows. The tail is truncated in the skill listing."
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
