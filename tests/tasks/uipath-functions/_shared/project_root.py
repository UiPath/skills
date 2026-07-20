"""Resolve the on-disk project root for a coded-agent test.

The skill's `references/coded/lifecycle/setup.md` teaches `mkdir
<PROJECT_NAME> && cd <PROJECT_NAME>` as the canonical scaffolding
step, but in practice agents sometimes work directly in the
sandbox cwd (no subdir) — especially when the prompt doesn't
emphasise the mkdir step. To stay durable across both behaviours
without flipping check scripts every time, this helper finds the
project root by looking for `pyproject.toml`:

  1. If `<cwd>/pyproject.toml` exists → return `<cwd>` (flat layout).
  2. Else if `<cwd>/<default_subdir>/pyproject.toml` exists →
     return that subdir.
  3. Else fall back to `<cwd>/<default_subdir>` so downstream
     checks surface a clear "Missing <expected file>" diagnostic
     against the canonical layout.
"""

from __future__ import annotations

import os
from pathlib import Path


def find_project_root(default_subdir: str) -> Path:
    cwd = Path(os.getcwd())
    if (cwd / "pyproject.toml").is_file():
        return cwd
    nested = cwd / default_subdir
    if (nested / "pyproject.toml").is_file():
        return nested
    return nested
