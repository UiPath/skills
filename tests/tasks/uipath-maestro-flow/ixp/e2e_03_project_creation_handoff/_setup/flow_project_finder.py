"""Standalone copy of `_shared/flow_check.py`'s Flow-project-directory lookup.

handoff.py (pre_run/post_run tooling, staged into the sandbox via
sandbox.template_sources) cannot import `_shared.flow_check`: `_shared/` holds
the grading suite's answer scripts and is never mounted into the agent's
sandbox. This module carries only the pure directory-discovery logic —
`find_project_dir` plus its private helpers — copied verbatim from
`_shared/flow_check.py` (`_find_project` and friends). It has no access to,
and shares no state with, any check_*.py's scoring logic.

Keep in sync by inspection if `_shared/flow_check.py`'s discovery heuristic
changes (see `_shared/test_flow_check_discovery.py`) — there is no import
relationship enforcing it.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

_HUSK_MAX_NODES = 1


def _rglob_pruned(pattern: str) -> list[str]:
    """``glob.glob(pattern, recursive=True)`` from the CWD, but never descending
    into ``node_modules`` (the preview workspace symlinks the baked SDK tree
    there, and ``glob`` follows directory symlinks under ``**``)."""
    if "**" not in pattern:
        return sorted(glob.glob(pattern, recursive=True))
    prefix, _, suffix = pattern.partition("**")
    root = prefix.rstrip("/") or "."
    suffix = suffix.lstrip("/")
    matches: list[str] = []
    for dirpath, dirnames, _ in os.walk(root, followlinks=True):
        dirnames[:] = [d for d in dirnames if d != "node_modules"]
        matches.extend(glob.glob(os.path.join(glob.escape(dirpath), suffix)))
    if root == ".":
        matches = [m[2:] if m.startswith("./") else m for m in matches]
    return sorted(set(matches))


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _is_flow_project(path: str) -> bool:
    """Return True iff ``path`` is a ``project.uiproj`` declaring a Flow project.

    Returns False (rather than raising) for unreadable / malformed manifests
    so a single bad sibling cannot mask a legitimate Flow project.
    """
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("ProjectType") == "Flow"


def _flow_file_node_count(path: str) -> int | None:
    """Return one Flow file's node count, or ``None`` when unreadable."""
    try:
        with open(path, encoding="utf-8") as f:
            flow = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    nodes = flow.get("nodes") if isinstance(flow, dict) else None
    return len(nodes) if isinstance(nodes, list) else None


def _flow_node_count(project_dir: str) -> int | None:
    """Total ``nodes`` declared across every ``.flow`` under ``project_dir``.

    ``None`` means unknown — no ``.flow``, or one that will not parse. Unknown is
    never read as a husk.
    """
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        return None
    total = 0
    for path in flows:
        count = _flow_file_node_count(path)
        if count is None:
            return None
        total += count
    return total


def _dedupe_flow_projects(project_uiprojs: list[str]) -> list[str]:
    """Collapse projects whose relative Flow files are byte-for-byte equal.

    Missing or unreadable Flow files stay distinct so project-scoped debug never
    guesses across candidates whose equivalence cannot be proved.
    """
    by_content: dict[tuple[tuple[str, str], ...] | tuple[str, str], str] = {}
    for project_uiproj in project_uiprojs:
        project_dir = os.path.dirname(project_uiproj)
        flows = sorted(
            glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
        )
        fingerprints: list[tuple[str, str]] = []
        try:
            for path in flows:
                with open(path, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                fingerprints.append((os.path.relpath(path, project_dir), digest))
        except OSError:
            fingerprints = []

        key: tuple[tuple[str, str], ...] | tuple[str, str]
        if fingerprints:
            key = tuple(fingerprints)
        else:
            key = ("unknown", project_uiproj)
        by_content.setdefault(key, project_uiproj)
    return sorted(by_content.values())


def _describe_candidate(project_uiproj: str, node_count: int | None) -> str:
    project_dir = os.path.dirname(project_uiproj)
    if node_count is None:
        return f"{project_dir} (node count unknown — .flow missing or unreadable)"
    return f"{project_dir} ({node_count} node{'' if node_count == 1 else 's'})"


def _split_off_scaffold_husks(
    counts: list[tuple[str, int | None]],
) -> tuple[str | None, list[tuple[str, int | None]]]:
    """Separate the one project carrying real work from abandoned init husks.

    `uip maestro flow init` run outside a solution auto-scaffolds a duplicate
    `<Project>Solution/` holding a trigger-only project (cli#2470). An agent that
    then rebuilds in the right solution leaves two `project.uiproj` files, one of
    which is dead weight — a configuration this checker used to refuse outright.

    Returns ``(selected, husks)`` only when exactly one candidate has a known
    node count above the husk ceiling and every other candidate has a known
    count at or below it. Any unknown count (missing / unreadable / malformed
    ``.flow``) makes the split ambiguous, so the caller keeps refusing.
    """
    substantive = [(p, n) for p, n in counts if n is None or n > _HUSK_MAX_NODES]
    husks = [(p, n) for p, n in counts if n is not None and n <= _HUSK_MAX_NODES]
    if len(substantive) != 1 or substantive[0][1] is None:
        return None, []
    return substantive[0][0], husks


def _find_project(pattern: str) -> str:
    """Locate the *Flow* project directory matching ``pattern``.

    Tasks that legitimately ship multi-project solutions (a Flow project
    plus a sibling agent / sub-flow / RPA project) produce more than one
    ``project.uiproj`` under the solution root. The Flow project is the one
    with ``"ProjectType": "Flow"`` in its manifest; sibling resource projects
    declare ``"ProjectType": "Agent"`` / ``"Coded"`` / ``"Process"``.

    Two Flow projects can also mean byte-identical copies, or one build plus one
    abandoned scaffold — see :func:`_dedupe_flow_projects` and
    :func:`_split_off_scaffold_husks`. Anything else stays a refusal.
    """
    candidates = _rglob_pruned(pattern)
    if not candidates:
        _fail(f"No project.uiproj found matching {pattern}")
    flow_projects = [p for p in candidates if _is_flow_project(p)]
    if not flow_projects:
        joined = "\n  - ".join(candidates)
        _fail(
            f"No Flow project.uiproj found matching {pattern} — "
            f'candidates exist but none declare ProjectType="Flow":\n  - {joined}'
        )
    if len(flow_projects) > 1:
        original_count = len(flow_projects)
        flow_projects = _dedupe_flow_projects(flow_projects)
        if len(flow_projects) == 1:
            print(
                "note: ignoring "
                f"{original_count - 1} byte-identical Flow project duplicate(s)"
            )
            return os.path.dirname(flow_projects[0])

        counts = [(p, _flow_node_count(os.path.dirname(p))) for p in flow_projects]
        selected, husks = _split_off_scaffold_husks(counts)
        if selected is not None:
            listed = ", ".join(_describe_candidate(p, n) for p, n in husks)
            print(f"note: ignoring {len(husks)} abandoned scaffold(s): {listed}")
            return os.path.dirname(selected)
        joined = "\n  - ".join(_describe_candidate(p, n) for p, n in counts)
        _fail(
            f"Multiple Flow projects match {pattern!r} — refusing to guess:\n  - {joined}"
        )
    return os.path.dirname(flow_projects[0])


def find_project_dir(pattern: str = "**/project.uiproj") -> str:
    return _find_project(pattern)
