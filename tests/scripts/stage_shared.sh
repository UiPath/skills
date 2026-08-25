#!/usr/bin/env bash
# Co-locate each skill group's `_shared/` helper package into every task dir
# whose grader imports it, so `from _shared ...` resolves under coder-eval 0.11+.
#
# Why this exists: coder-eval 0.11 stages $TASK_DIR as an ISOLATED copy of just
# the leaf task folder (/work/task_dir) — the reference anti-cheat deliberately
# no longer exposes the task dir's parent. But ~215 graders import the
# group-level `tests/tasks/<group>/_shared/` package by walking UP out of the
# task dir (`sys.path.insert(0, .../../..)`), which now points at nothing in the
# container -> ModuleNotFoundError.
#
# Fix, with no grader changes: copy the group's `_shared/` INTO the task dir so
# it travels inside the /work/task_dir copy. `python3 $TASK_DIR/check.py` puts
# the script's own dir on sys.path[0], so a co-located `_shared/` is importable
# regardless of the grader's (now-inert) up-walk. A symlink would NOT work —
# coder-eval's copytree ignores symlinks.
#
# Run on the CI checkout BEFORE `coder-eval run`. Idempotent. Ephemeral: it
# mutates the checked-out tree, not the committed repo.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(git -C "$script_dir" rev-parse --show-toplevel)"

manifest=${STAGE_SHARED_MANIFEST:-}
if [ -n "$manifest" ]; then
  : > "$manifest"
fi

count=0
while IFS= read -r f; do
  dir=$(dirname "$f")
  # Never recurse into a _shared package itself.
  case "$dir" in */_shared | */_shared/*) continue ;; esac
  # group = tests/tasks/<group>
  group=$(printf '%s\n' "$f" | sed -E 's#^(tests/tasks/[^/]+)/.*#\1#')
  src="$group/_shared"
  [ -d "$src" ] || continue          # group has no _shared -> nothing to stage
  [ -e "$dir/_shared" ] && continue  # already present (idempotent / hand-authored)
  cp -R "$src" "$dir/_shared"
  if [ -n "$manifest" ]; then
    printf '%s\n' "$PWD/$dir/_shared" >> "$manifest"
  fi
  count=$((count + 1))
done < <(git grep -lE 'from _shared|import _shared' -- 'tests/tasks/**/*.py')

echo "stage_shared: co-located _shared into ${count} task dir(s)"
