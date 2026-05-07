#!/bin/bash
# Validate SKILL.md frontmatter against the canonical SKILL contract.
# See CONTRIBUTING.md#canonical-skillmd-contract and .claude/rules/skill-structure.md.
#
# Enforced rules (non-zero exit on failure):
#   1. `name` field is present
#   2. `name` matches the parent folder name exactly
#   3. `description` field is present
#   4. `description` ≤ 1024 characters
#
# Warning (non-fatal):
#   - Combined `description` + `when_to_use` > 1500 chars (Claude Code truncates
#     the skill listing at 1,536 chars: https://code.claude.com/docs/en/skills.md)
#
# The script keeps its historical filename so the pre-commit hook and CI workflow
# do not need to change. Despite the name, it now validates the full canonical
# contract, not only description length.
#
# Usage:
#   validate-skill-descriptions.sh [file1 file2 ...]
# If no files are specified, checks staged SKILL.md files (pre-commit mode).

set -e

LIMIT=1024
COMBINED_WARN=1500
FAILED=0

# Determine which files to check
if [ "$#" -eq 0 ]; then
  # Pre-commit mode: check staged SKILL.md files
  FILES=$(git diff --cached --name-only --diff-filter=ACM | grep 'skills/.*/SKILL\.md$' || true)
else
  # Explicit mode: use provided files
  FILES="$@"
fi

# Extract a top-level frontmatter scalar field. Handles both quoted ("...")
# and unquoted forms; returns the value without surrounding double quotes.
extract_field() {
  local file="$1"
  local field="$2"
  awk -v f="$field" '
    /^---$/ { c++; if (c == 2) exit; next }
    c == 1 && $0 ~ "^"f": " {
      sub("^"f": *", "")
      # Strip a single pair of surrounding double quotes if present
      if (substr($0, 1, 1) == "\"" && substr($0, length($0), 1) == "\"") {
        $0 = substr($0, 2, length($0) - 2)
      }
      print
      exit
    }
  ' "$file"
}

for file in $FILES; do
  if [ ! -f "$file" ]; then
    continue
  fi

  # Defensive: only validate files that look like skill SKILL.md
  case "$file" in
    *skills/*/SKILL.md) ;;
    *)
      echo "↷ $file: not a skill SKILL.md, skipping"
      continue
      ;;
  esac

  folder_name=$(basename "$(dirname "$file")")
  name=$(extract_field "$file" "name")
  desc=$(extract_field "$file" "description")
  wtu=$(extract_field "$file" "when_to_use")

  file_failed=0

  # Required: name present
  if [ -z "$name" ]; then
    echo "❌ $file: missing 'name' field in frontmatter"
    file_failed=1
  elif [ "$name" != "$folder_name" ]; then
    # Required: name matches folder
    echo "❌ $file: name '$name' does not match parent folder '$folder_name'"
    file_failed=1
  fi

  # Required: description present
  if [ -z "$desc" ]; then
    echo "❌ $file: missing 'description' field in frontmatter"
    file_failed=1
  else
    desc_len=${#desc}
    if [ "$desc_len" -gt "$LIMIT" ]; then
      echo "❌ $file: description exceeds $LIMIT characters ($desc_len chars)"
      file_failed=1
    fi

    # Warning: combined description + when_to_use length
    if [ -n "$wtu" ]; then
      combined_len=$((desc_len + ${#wtu}))
      if [ "$combined_len" -gt "$COMBINED_WARN" ]; then
        echo "⚠ $file: description + when_to_use is $combined_len chars (Claude Code truncates at 1,536)"
      fi
    fi
  fi

  if [ "$file_failed" -eq 0 ]; then
    echo "✓ $file: name='$name', description=${#desc} chars$( [ -n "$wtu" ] && echo ", when_to_use=${#wtu} chars" )"
  else
    FAILED=1
  fi
done

if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "Skill frontmatter validation failed. See:"
  echo "  - CONTRIBUTING.md#canonical-skillmd-contract"
  echo "  - .claude/rules/skill-structure.md"
  echo "Edit the offending SKILL.md frontmatter and try again."
  exit 1
fi

exit 0
