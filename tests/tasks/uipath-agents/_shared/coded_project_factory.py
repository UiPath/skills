"""Coded-agent project scaffolding factory.

Emits the minimum file set a coded-agent task needs *before* the agent
runs `uip codedagent init` — `pyproject.toml`, `uipath.json`,
`entry-points.json`, and a `bindings.json` skeleton. The shape mirrors
`assets/templates/pyproject.toml` and the project layout documented in
`references/coded/lifecycle/setup.md`.

This is *not* a substitute for `uip codedagent new` / `init`. It is the
seed used by tests that aren't *about* scaffolding (e.g. bindings-only
tests, anti-pattern negative tests) so they can skip straight to the
behavior under test. Tests that exercise the scaffold lifecycle itself
(PR 2 framework end-to-end tests) MUST call `uip codedagent new` from
the agent prompt — never call this factory.

Critical Rule (`references/coded/quickstart.md`): NEVER add a
`[build-system]` section. The factory enforces this — `pyproject.toml`
is `[project]` + `[dependency-groups]` only.
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Iterable

PYPROJECT_TEMPLATE = dedent(
    """\
    [project]
    name = "{name}"
    version = "0.0.1"
    description = "{description}"
    authors = [{{ name = "Agent Developer" }}]
    requires-python = ">=3.11"
    dependencies = [
        "uipath",{extra_deps}
    ]

    [dependency-groups]
    dev = [
        "uipath-dev",
    ]
    """
)


def write_pyproject(
    root: Path,
    *,
    name: str,
    description: str = "Test fixture",
    extra_dependencies: Iterable[str] = (),
) -> Path:
    """Write `pyproject.toml`. No `[build-system]` — Critical Rule C1.

    `extra_dependencies` is for framework deps (e.g. `uipath-langchain`).
    They are appended to the base `["uipath"]` list.
    """
    extras = list(extra_dependencies)
    extra_block = ""
    if extras:
        extra_block = "\n" + "\n".join(f'    "{dep}",' for dep in extras)
    content = PYPROJECT_TEMPLATE.format(
        name=name,
        description=description,
        extra_deps=extra_block,
    )
    path = root / "pyproject.toml"
    path.write_text(content)
    return path


def write_uipath_json(root: Path, *, functions: dict | None = None) -> Path:
    """Write `uipath.json` in the shape `uip codedagent init` produces.

    `functions` maps entrypoint name to `<file>.py:<func>` per the
    simple-function convention in `setup.md`. Pass `None` to omit the
    `functions` key entirely (LangGraph / LlamaIndex / OpenAI Agents
    auto-discover from their own config files).
    """
    payload: dict = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/uipath",
        "runtimeOptions": {"isConversational": False},
        "packOptions": {
            "fileExtensionsIncluded": [],
            "filesIncluded": [],
            "filesExcluded": [],
            "directoriesExcluded": [],
            "includeUvLock": True,
        },
    }
    if functions is not None:
        payload["functions"] = functions
    path = root / "uipath.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def write_entry_points(
    root: Path,
    *,
    entrypoints: list[dict] | None = None,
) -> Path:
    """Write `entry-points.json`.

    Each entry must include at minimum `filePath` and `uniqueId`. Pass
    `entrypoints=None` to write an empty list (sufficient for some
    bindings-sync tests — see `bindings_sync.yaml`).
    """
    payload = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
        "$id": "entry-points.json",
        "entryPoints": list(entrypoints or []),
    }
    path = root / "entry-points.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def write_empty_bindings(root: Path) -> Path:
    """Write the v2.0 bindings.json skeleton (see `bindings-reference.md`)."""
    path = root / "bindings.json"
    path.write_text(json.dumps({"version": "2.0", "resources": []}, indent=2))
    return path


def write_minimal_project(
    root: Path,
    *,
    name: str = "test-agent",
    description: str = "Test fixture",
    functions: dict | None = None,
    entrypoints: list[dict] | None = None,
    extra_dependencies: Iterable[str] = (),
) -> dict:
    """Emit the four-file minimum: pyproject.toml, uipath.json,
    entry-points.json, bindings.json.

    Returns a dict of the absolute paths for downstream assertions.
    """
    root.mkdir(parents=True, exist_ok=True)
    return {
        "pyproject": write_pyproject(
            root,
            name=name,
            description=description,
            extra_dependencies=extra_dependencies,
        ),
        "uipath_json": write_uipath_json(root, functions=functions),
        "entry_points": write_entry_points(root, entrypoints=entrypoints),
        "bindings": write_empty_bindings(root),
    }
