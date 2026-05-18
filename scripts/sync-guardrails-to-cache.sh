#!/bin/bash
# Copies guardrails skill files from the local repo into:
#   1. The Claude plugin cache (latest version, auto-detected)
#   2. The active marketplaces path (what Claude loads at runtime)
#
# Syncs SKILL.md and both low-code and coded agent guardrail references.

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
CACHE_BASE="$HOME/.claude/plugins/cache/uipath-marketplace/uipath"

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

echo "Detected version: $VERSION"

sync_dir() {
    local src="$1"
    local rel="$2"   # path relative to skills/uipath-agents/references/

    local cache_dest="$CACHE_BASE/$VERSION/skills/uipath-agents/references/$rel"
    local marketplace_dest="$HOME/.claude/plugins/marketplaces/uipath-marketplace/skills/uipath-agents/references/$rel"

    if [[ ! -d "$src" ]]; then
        echo "ERROR: source not found at $src" >&2
        exit 1
    fi

    echo "Source:           $src"
    mkdir -p "$cache_dest"
    cp -r "$src/." "$cache_dest/"
    echo "Synced to cache:       $cache_dest"

    mkdir -p "$marketplace_dest"
    cp -r "$src/." "$marketplace_dest/"
    echo "Synced to marketplace: $marketplace_dest"
    echo ""
}

# SKILL.md — single file, lives at the skill root
SKILL_MD_SRC="$REPO_ROOT/skills/uipath-agents/SKILL.md"
if [[ ! -f "$SKILL_MD_SRC" ]]; then
    echo "ERROR: SKILL.md not found at $SKILL_MD_SRC" >&2
    exit 1
fi
cp "$SKILL_MD_SRC" "$CACHE_BASE/$VERSION/skills/uipath-agents/SKILL.md"
echo "Source:           $SKILL_MD_SRC"
echo "Synced to cache:       $CACHE_BASE/$VERSION/skills/uipath-agents/SKILL.md"
cp "$SKILL_MD_SRC" "$HOME/.claude/plugins/marketplaces/uipath-marketplace/skills/uipath-agents/SKILL.md"
echo "Synced to marketplace: $HOME/.claude/plugins/marketplaces/uipath-marketplace/skills/uipath-agents/SKILL.md"
echo ""

sync_dir \
    "$REPO_ROOT/skills/uipath-agents/references/lowcode/capabilities/guardrails" \
    "lowcode/capabilities/guardrails"

sync_dir \
    "$REPO_ROOT/skills/uipath-agents/references/coded/capabilities/guardrails" \
    "coded/capabilities/guardrails"

echo "Done — SKILL.md and guardrails synced to cache v$VERSION and active marketplace"
