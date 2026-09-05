#!/usr/bin/env python3
"""Locate a task's agent / flow project files under either on-disk layout.

Two authoring surfaces leave two trees in the sandbox:

- CLI (``uip solution init`` + ``uip agent init`` / ``uip maestro flow init``):
  ``<Solution>/<Project>/agent.json``, ``<Solution>/<Project>/<Project>.flow``,
  plus a ``<Solution>/<Solution>.uipx`` manifest listing the projects.
- Studio Web (the ``studioweb`` skill flavor; the agent authors in-product and
  the studioweb-stdio bridge mirrors the store into the sandbox): the open
  Studio Web solution — named by the host, not by the task — as
  ``<OpenSolution>/<OpenSolution>.uipx`` plus ``<OpenSolution>/<Project>/...``
  (bridge >= 0.0.1-alpha.15), or the flat ``<Project>/agent.json``,
  ``<Project>/new.flow`` with no ``.uipx`` at all (older bridges).

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
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-agents/_shared/project_files.py \\
        locate IPSol IPAgent agent.json            # prints the resolved path
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-agents/_shared/project_files.py \\
        assert-json IPSol IPAgent agent.json 'metadata.isConversational=true' \\
        'settings.engine="conversational-v1"' 'length(inputSchema.properties)=0'

``registered`` keeps the CLI check strict — when ``<Solution>.uipx`` exists its
``Projects[]`` is what is asserted. Under the Studio Web layout the manifest is
named after the open Studio Web solution, so a lone differently-named ``.uipx``
stands in for ``<Solution>.uipx``; with no ``.uipx`` anywhere the exported
``project.uiproj`` manifests are counted instead, since there registration is
implicit in the active solution.

``assert-json`` replaces a ``json_check`` criterion whose ``path`` would have to
name one layout: each ``EXPR=JSON`` pair is a dotted path (or ``length(path)``)
compared for equality against a JSON literal.
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
    uipx_paths = _walk(f"**/{solution}.uipx") or _walk("**/*.uipx")
    if len(uipx_paths) == 1:
        # Either the task's own manifest or, under Studio Web, the one the bridge
        # exports for the open solution (named by the host, not by the task).
        return _manifest_error(uipx_paths[0], min_projects, max_projects, project_type)
    if uipx_paths:
        return f"no {solution}.uipx found (other solution manifests exist: {', '.join(uipx_paths)})"
    # Studio Web layout without a manifest (older bridges): the exported projects
    # belong to the active solution by construction.
    manifests = _walk("**/project.uiproj")
    error = _count_error(len(manifests), min_projects, max_projects, f"the sandbox root (no {solution}.uipx)")
    if error:
        return error
    if project_type is not None and not any(_manifest_type(m) == project_type for m in manifests):
        return f"no exported project.uiproj declares ProjectType {project_type!r}"
    return None


def _manifest_error(
    uipx_path: str, min_projects: int, max_projects: int | None, project_type: str | None
) -> str | None:
    try:
        with open(uipx_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return f"{uipx_path} is not readable JSON: {exc}"
    projects = manifest.get("Projects") if isinstance(manifest, dict) else None
    if not isinstance(projects, list):
        return f"{uipx_path} has no Projects[] list"
    error = _count_error(len(projects), min_projects, max_projects, uipx_path)
    if error:
        return error
    if project_type is not None:
        first = projects[0].get("Type") if projects and isinstance(projects[0], dict) else None
        if first != project_type:
            return f"{uipx_path} Projects[0].Type is {first!r}; expected {project_type!r}"
    return None


def json_assertion_error(document: object, expression: str, expected_json: str) -> str | None:
    """None when ``expression`` evaluates to the JSON literal ``expected_json``.

    ``expression`` is a dotted path (``metadata.isConversational``) or
    ``length(<dotted path>)``; a missing segment evaluates to ``null`` so the
    mismatch is reported instead of raising.
    """
    try:
        expected = json.loads(expected_json)
    except json.JSONDecodeError as exc:
        return f"{expression}: expected value {expected_json!r} is not JSON ({exc})"
    actual = _evaluate(document, expression)
    if actual == expected and type(actual) is type(expected):
        return None
    return f"{expression}: expected {json.dumps(expected)}, got {json.dumps(actual)}"


def _evaluate(document: object, expression: str) -> object:
    if expression.startswith("length(") and expression.endswith(")"):
        value = _evaluate(document, expression[len("length(") : -1])
        return len(value) if isinstance(value, (list, dict, str)) else None
    current = document
    for segment in expression.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
    return current


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
    if len(argv) == 4 and argv[0] in ("exists", "locate"):
        path = find_project_file(argv[1], argv[2], argv[3])
        if path.exists():
            shown = path.relative_to(os.getcwd()) if path.is_absolute() else path
            print(shown if argv[0] == "locate" else f"OK: {shown}")
            return 0
        print(f"FAIL: Missing {argv[1]}/{argv[2]}/{argv[3]} (looked under {path.parent})", file=sys.stderr)
        return 1
    if len(argv) >= 5 and argv[0] == "assert-json":
        return _assert_json(argv[1], argv[2], argv[3], argv[4:])
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
    print(
        f"usage: project_files.py exists|locate SOLUTION PROJECT RELATIVE_PATH | {_REGISTERED_USAGE} | "
        f"{_ASSERT_JSON_USAGE}",
        file=sys.stderr,
    )
    return 2


def _assert_json(solution: str, project: str, relative: str, assertions: list[str]) -> int:
    path = find_project_file(solution, project, relative)
    if not path.exists():
        print(f"FAIL: Missing {solution}/{project}/{relative} (looked under {path.parent})", file=sys.stderr)
        return 1
    try:
        with open(path, encoding="utf-8") as f:
            document = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"FAIL: {path} is not readable JSON: {exc}", file=sys.stderr)
        return 1
    failures = []
    for assertion in assertions:
        expression, separator, expected_json = assertion.partition("=")
        if not separator:
            print(f"usage: {_ASSERT_JSON_USAGE} (bad assertion {assertion!r})", file=sys.stderr)
            return 2
        error = json_assertion_error(document, expression, expected_json)
        if error:
            failures.append(error)
    if failures:
        print("FAIL: " + "; ".join(failures), file=sys.stderr)
        return 1
    print(f"OK: {path} satisfies {len(assertions)} assertion(s)")
    return 0


_REGISTERED_USAGE = "registered SOLUTION [--min-projects N] [--max-projects N] [--project-type T]"
_ASSERT_JSON_USAGE = "assert-json SOLUTION PROJECT RELATIVE_PATH EXPR=JSON [EXPR=JSON ...]"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
