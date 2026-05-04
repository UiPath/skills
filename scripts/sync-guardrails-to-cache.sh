#!/bin/bash
# Copies guardrails skill files from the local repo into:
#   1. The Claude plugin cache (latest version, auto-detected)
#   2. The active marketplaces path (what Claude loads at runtime)

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
GUARDRAILS_SRC="$REPO_ROOT/skills/uipath-agents/references/lowcode/capabilities/guardrails"
CACHE_BASE="$HOME/.claude/plugins/cache/uipath-marketplace/uipath"
MARKETPLACE_DEST="$HOME/.claude/plugins/marketplaces/uipath-marketplace/skills/uipath-agents/references/lowcode/capabilities/guardrails"

if [[ ! -d "$GUARDRAILS_SRC" ]]; then
    echo "ERROR: guardrails source not found at $GUARDRAILS_SRC" >&2
    exit 1
fi

if [[ ! -d "$CACHE_BASE" ]]; then
    echo "ERROR: cache base not found at $CACHE_BASE" >&2
    exit 1
fi

# Detect the latest version by sorting version folders (semver-aware via sort -V)
VERSION=$(ls "$CACHE_BASE" | sort -V | tail -1)

if [[ -z "$VERSION" ]]; then
    echo "ERROR: no version directories found under $CACHE_BASE" >&2
    exit 1
fi

CACHE_DEST="$CACHE_BASE/$VERSION/skills/uipath-agents/references/lowcode/capabilities/guardrails"

echo "Detected version: $VERSION"
echo "Source:           $GUARDRAILS_SRC"

mkdir -p "$CACHE_DEST"
cp -r "$GUARDRAILS_SRC/." "$CACHE_DEST/"
echo "Synced to cache:       $CACHE_DEST"

mkdir -p "$MARKETPLACE_DEST"
cp -r "$GUARDRAILS_SRC/." "$MARKETPLACE_DEST/"
echo "Synced to marketplace: $MARKETPLACE_DEST"

echo "Done — guardrails synced to cache v$VERSION and active marketplace"
