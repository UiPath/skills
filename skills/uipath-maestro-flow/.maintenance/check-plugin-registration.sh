#!/bin/bash
# Verify every plugin folder is registered in the index files that route agents
# to it. check-plugin-pairs.sh proves the files exist; check-orphans.sh proves
# something links them. Neither catches the real failure: a plugin linked from
# one index but missing from the node-type tables an agent actually reads when
# it is choosing a node, so the node stays undiscoverable.
#
# Usage: bash .maintenance/check-plugin-registration.sh
# Output: MISSING lines per gap, then a summary. Non-zero exit if any gap.
#
# A plugin counts as registered in a file when that file references
# `plugins/<name>/` anywhere outside a fenced code block.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

PLUGINS_DIR="$ROOT/references/author/references/plugins"

if [ ! -d "$PLUGINS_DIR" ]; then
  echo "ERROR: plugins directory not found at $PLUGINS_DIR" >&2
  exit 2
fi

# Every plugin must appear in all three: the capability's task table, the
# planning node-type tables, and the impl routing table.
INDEX_FILES_ALL=(
  "references/author/CAPABILITY.md"
  "references/author/references/planning-arch.md"
  "references/author/references/planning-impl.md"
)

# Plugins whose agent node carries its definition in an `agent.json` inside the
# flow project additionally owe a row in the brownfield task table and in the
# prompt-token table — both enumerate that family by node type, so a new member
# is silently absent until it is added. Keep this list in step with the plugins
# that document an inline `agent.json`.
INLINE_AGENT_PLUGINS=(
  "inline-agent"
  "voice"
)
INDEX_FILES_INLINE_AGENT=(
  "references/author/references/brownfield.md"
  "references/shared/node-output-wiring.md"
)

# Gaps that predate this checker, reported as KNOWN_GAP instead of failing the
# build so the gate lands green and the debt stays visible. Each entry is
# `<index-file>|<plugin>`. Delete the entry — do not add to this list — once the
# owning team adds the row. Owners are in the repo CODEOWNERS.
#
#   summarize, batch-transform -> missing from the planning-impl routing table
#   while present in CAPABILITY.md and planning-arch.md (context-grounding team)
KNOWN_GAPS=(
  "references/author/references/planning-impl.md|summarize"
  "references/author/references/planning-impl.md|batch-transform"
)

# References outside fenced code blocks only — a type named in an example is not
# a routing entry.
references_plugin() {
  local file="$1"
  local plugin="$2"
  [ -f "$file" ] || return 1
  /usr/bin/awk -v needle="plugins/$plugin/" '
    /^```/ { fenced = !fenced; next }
    !fenced && index($0, needle) { found = 1; exit }
    END { exit !found }
  ' "$file"
}

in_list() {
  local needle="$1"; shift
  local item
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

failures=0
known=0
checked=0

while IFS= read -r plugin_dir; do
  [ -z "$plugin_dir" ] && continue
  plugin=$(/usr/bin/basename "$plugin_dir")
  checked=$((checked + 1))

  required=("${INDEX_FILES_ALL[@]}")
  if in_list "$plugin" "${INLINE_AGENT_PLUGINS[@]}"; then
    required+=("${INDEX_FILES_INLINE_AGENT[@]}")
  fi

  for index_file in "${required[@]}"; do
    references_plugin "$ROOT/$index_file" "$plugin" && continue
    if in_list "$index_file|$plugin" "${KNOWN_GAPS[@]}"; then
      echo "KNOWN_GAP  $index_file  ->  no row routing to plugins/$plugin/"
      known=$((known + 1))
    else
      echo "MISSING  $index_file  ->  no row routing to plugins/$plugin/"
      failures=$((failures + 1))
    fi
  done
done < <(/usr/bin/find "$PLUGINS_DIR" -mindepth 1 -maxdepth 1 -type d | /usr/bin/sort)

echo ""
echo "plugins_checked=$checked missing_rows=$failures known_gaps=$known"

[ "$failures" -gt 0 ] && exit 1
exit 0
