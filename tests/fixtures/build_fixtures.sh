#!/usr/bin/env bash
# Build .nupkg fixture binaries from the source dirs under tests/fixtures/.
#
# Idempotent: if a target already exists, skips the rebuild. Pass --force to
# always rebuild.
#
# Currently a STUB: the coded-agent and library scaffolds aren't wired yet
# (see packages/README.md, libraries/README.md). This script's contract is
# documented so it can be filled in once `uip codedagent`/equivalent ships.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

build_stub_package() {
  local src="$SCRIPT_DIR/packages/e2e-stub"
  if [[ ! -d "$src" ]]; then
    echo "[skip] $src not present — coded-agent stub not yet scaffolded; see packages/README.md"
    return 0
  fi
  # TODO: actual packing logic, e.g.:
  #   (cd "$src" && uip codedagent pack --output "$SCRIPT_DIR/packages")
  echo "[todo] stub package build not implemented yet"
}

build_stub_library() {
  local src="$SCRIPT_DIR/libraries/e2e-stub-lib"
  if [[ ! -d "$src" ]]; then
    echo "[skip] $src not present — library stub not yet scaffolded; see libraries/README.md"
    return 0
  fi
  echo "[todo] stub library build not implemented yet"
}

build_stub_package
build_stub_library

echo "[ok] build_fixtures.sh complete (stub — see READMEs for what's still TBD)"
