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
#
# Still load-bearing after the 2026-09 host-path-removal migration (test:
# d61fa9d52): that migration moved most graders to $REFERENCE_DIR (whose
# staged root already contains _shared/, so those graders no longer need this
# script), but ~70 graders still do `from _shared import ...` / `import _shared`
# by walking up out of their own task dir rather than through $REFERENCE_DIR —
# this script is what makes that resolve in CI. It is CI-only: `tests/Makefile`
# never calls it, so those same graders resolve `_shared` in CI (this script
# ran first) but NOT under a local `make all`/`make smoke` run. Retiring this
# script requires repointing all ~70 to $REFERENCE_DIR-relative imports first.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(git -C "$script_dir" rev-parse --show-toplevel)"

manifest=${STAGE_SHARED_MANIFEST:-}
if [ -n "$manifest" ]; then
  : > "$manifest"
fi

search_root=${STAGE_SHARED_ROOT:-tests/tasks}
# Compare resolved paths so `tests/tasks/../../etc` cannot pass the guard.
resolved_root=$(realpath -m -- "$search_root")
tasks_root=$(realpath -m -- "$PWD/tests/tasks")
case "$resolved_root" in
  "$tasks_root" | "$tasks_root"/*) ;;
  *)
    echo "stage_shared: STAGE_SHARED_ROOT must be under tests/tasks: $search_root" >&2
    exit 2
    ;;
esac
search_root=${resolved_root#"$PWD"/}

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
done < <(git grep -lE 'from _shared|import _shared' -- "$search_root/**/*.py")

# Pass 2: graders that put a `_shared` DIR itself on sys.path and then import
# its modules bare (e.g. `sys.path.insert(0, .../"..", "_shared")` followed by
# `from grader_common import ...`). Co-locating the _shared DIR does not help
# those — the bare module must be importable, and only the script's own dir is
# reliably on sys.path. Copy the nearest ancestor _shared's top-level *.py
# files NEXT TO the grader, where sys.path[0] already points. Nearest matters:
# e.g. tests/tasks/uipath-review/rpa/_shared (grader_common) must win over the
# group-level tests/tasks/uipath-review/_shared (scaffold helpers).
count2=0
while IFS= read -r f; do
  dir=$(dirname "$f")
  case "$dir" in */_shared | */_shared/*) continue ;; esac
  probe=$dir src=""
  while [[ "$probe" == tests/tasks/* ]]; do
    if [ -d "$probe/_shared" ]; then src="$probe/_shared"; break; fi
    probe=$(dirname "$probe")
  done
  [ -n "$src" ] || continue
  copied=0
  for py in "$src"/*.py; do
    [ -e "$py" ] || continue
    base=$(basename "$py")
    [ -e "$dir/$base" ] && continue
    cp "$py" "$dir/$base"
    copied=1
  done
  [ "$copied" -eq 1 ] && count2=$((count2 + 1))
done < <(git grep -lE 'sys\.path\.insert\(.*_shared' -- 'tests/tasks/**/*.py' \
           | { xargs grep -LE 'from _shared|import _shared' || true; })

echo "stage_shared: co-located _shared into ${count} task dir(s), module files into ${count2}"
