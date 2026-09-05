#!/usr/bin/env python3
"""Locate a task's agent / flow project files under either on-disk layout.

Two authoring surfaces leave two trees in the sandbox:

- CLI (``uip solution init`` + ``uip agent init`` / ``uip maestro flow init``):
  ``<Solution>/<Project>/agent.json``, ``<Solution>/<Project>/<Project>.flow``,
  plus a ``<Solution>/<Solution>.uipx`` manifest listing the projects.
- Studio Web (the ``studioweb`` skill flavor; the agent authors in-product and
  the studioweb-stdio bridge mirrors ``/solution/<project>/...`` into the
  sandbox): ``<Project>/agent.json``, ``<Project>/new.flow``, no solution
  directory and no ``.uipx``.

Graders and task YAMLs used to hardcode the CLI shape, so every Studio Web run
failed on paths before a single assertion ran (nightly 13266324). This module
answers "where is project P of solution S" for both shapes, preferring the CLI
path when it exists and falling back to the canonical CLI path when nothing is
found — so a genuine miss still reports the familiar ``Missing <path>``.

Library use (graders)::

    from _shared.project_files import find_project_dir, find_project_file
    ROOT = find_project_dir("IPSol", "IPAgent")
    FLOW = find_project_file("DocsFlowSol", "DocsFlow", "DocsFlow.flow")

Task-YAML use (``run_command`` criteria, cwd = sandbox root)::

    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-agents/_shared/project_files.py \\
        exists IPSol IPAgent agent.json
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-agents/_shared/project_files.py \\
        registered IPSol --min-projects 1 [--project-type Agent]

``registered`` keeps the CLI check strict — when ``<Solution>.uipx`` exists its
``Projects[]`` is what is asserted — and only under the Studio Web layout (no
``.uipx`` anywhere) counts the exported ``<Project>/project.uiproj`` manifests
instead, since there registration is implicit in the active solution.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

_PRUNED = ("/.venv/", "/node_modules/", "/.git/")


def _walk(pattern: str) -> list[str]:
    return sorted(
        p
        for p in glob.glob(pattern, recursive=True)
        if not any(seg in f"/{p.replace(os.sep, '/')}/" for seg in _PRUNED)
    )


def find_project_dir(solution: str, project: str, *, cwd: str | os.PathLike[str] | None = None) -> Path:
    """Directory of ``project``: CLI ``<solution>/<project>``, Studio Web ``<project>``,
    else the unique ``**/<project>/`` holding a project manifest; falls back to the
    canonical CLI path so callers keep their ``Missing <path>`` diagnostics."""
    root = Path(cwd) if cwd is not None else Path(os.getcwd())
    canonical = root / solution / project
    for candidate in (canonical, root / project):
        if candidate.is_dir():
            return candidate
    with _chdir(root):
        hits = {
            os.path.dirname(p)
            for marker in ("project.uiproj", "agent.json")
            for p in _walk(f"**/{project}/{marker}")
        }
    if len(hits) == 1:
        return root / hits.pop()
    return canonical


def find_project_file(
    solution: str, project: str, relative: str, *, cwd: str | os.PathLike[str] | None = None
) -> Path:
    """``relative`` inside :func:`find_project_dir`. A ``.flow`` named after the
    project resolves to the project's lone ``.flow`` when that exact name is
    absent — Studio Web scaffolds the entry point as ``new.flow``."""
    project_dir = find_project_dir(solution, project, cwd=cwd)
    path = project_dir / relative
    if path.exists() or not relative.endswith(".flow") or "/" in relative:
        return path
    flows = sorted(project_dir.glob("*.flow"))
    return flows[0] if len(flows) == 1 else path


def _manifest_type(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return manifest.get("ProjectType") if isinstance(manifest, dict) else None


def _count_error(found: int, min_projects: int, max_projects: int | None, where: str) -> str | None:
    if found < min_projects:
        return f"{where} registers {found} project(s); expected at least {min_projects}"
    if max_projects is not None and found > max_projects:
        return f"{where} registers {found} project(s); expected at most {max_projects}"
    return None


def solution_registration_error(
    solution: str,
    *,
    min_projects: int = 1,
    max_projects: int | None = None,
    project_type: str | None = None,
) -> str | None:
    """None when ``solution`` registers between ``min_projects`` and ``max_projects``
    projects (the first of type ``project_type`` when given); otherwise the failure text."""
    uipx_paths = _walk(f"**/{solution}.uipx")
    if uipx_paths:
        try:
            with open(uipx_paths[0], encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return f"{uipx_paths[0]} is not readable JSON: {exc}"
        projects = manifest.get("Projects") if isinstance(manifest, dict) else None
        if not isinstance(projects, list):
            return f"{uipx_paths[0]} has no Projects[] list"
        error = _count_error(len(projects), min_projects, max_projects, uipx_paths[0])
        if error:
            return error
        if project_type is not None:
            first = projects[0].get("Type") if projects and isinstance(projects[0], dict) else None
            if first != project_type:
                return f"{uipx_paths[0]} Projects[0].Type is {first!r}; expected {project_type!r}"
        return None
    if _walk("**/*.uipx"):
        return f"no {solution}.uipx found (other solution manifests exist: {', '.join(_walk('**/*.uipx'))})"
    # Studio Web layout: projects are exported as <Project>/project.uiproj at the
    # sandbox root and belong to the active solution by construction.
    manifests = sorted(glob.glob("*/project.uiproj"))
    error = _count_error(len(manifests), min_projects, max_projects, f"the sandbox root (no {solution}.uipx)")
    if error:
        return error
    if project_type is not None and not any(_manifest_type(m) == project_type for m in manifests):
        return f"no exported project.uiproj declares ProjectType {project_type!r}"
    return None


class _chdir:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._prev: str | None = None

    def __enter__(self) -> None:
        self._prev = os.getcwd()
        os.chdir(self._path)

    def __exit__(self, *exc: object) -> None:
        assert self._prev is not None
        os.chdir(self._prev)


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[0] == "exists":
        path = find_project_file(argv[1], argv[2], argv[3])
        if path.exists():
            print(f"OK: {path.relative_to(os.getcwd()) if path.is_absolute() else path}")
            return 0
        print(f"FAIL: Missing {argv[1]}/{argv[2]}/{argv[3]} (looked under {path.parent})", file=sys.stderr)
        return 1
    if len(argv) >= 2 and argv[0] == "registered":
        solution, min_projects, max_projects, project_type = argv[1], 1, None, None
        rest = iter(argv[2:])
        try:
            for flag in rest:
                if flag == "--min-projects":
                    min_projects = int(next(rest))
                elif flag == "--max-projects":
                    max_projects = int(next(rest))
                elif flag == "--project-type":
                    project_type = next(rest)
                else:
                    raise ValueError(flag)
        except (StopIteration, ValueError) as exc:
            print(f"usage: {_REGISTERED_USAGE} ({exc})", file=sys.stderr)
            return 2
        error = solution_registration_error(
            solution, min_projects=min_projects, max_projects=max_projects, project_type=project_type
        )
        if error is None:
            print(f"OK: {solution} registers the expected project(s)")
            return 0
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"usage: project_files.py exists SOLUTION PROJECT RELATIVE_PATH | {_REGISTERED_USAGE}", file=sys.stderr)
    return 2


_REGISTERED_USAGE = "registered SOLUTION [--min-projects N] [--max-projects N] [--project-type T]"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
