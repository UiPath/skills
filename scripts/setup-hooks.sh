#!/bin/bash
# Setup git hooks for this repository

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Configure git to use .githooks directory
git config core.hooksPath .githooks

echo "✓ Git hooks configured to use .githooks/"
echo "  Pre-commit validation enabled for skill descriptions"
